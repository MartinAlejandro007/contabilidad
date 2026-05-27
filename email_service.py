"""
email_service.py - Servicio de envío de correos electrónicos.

Configura SMTP para enviar facturas (XML + PDF) a los clientes.
Soporta Gmail, Outlook y otros proveedores SMTP.
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional

from database import obtener_config, obtener_factura


class EmailService:
    """Servicio de envío de correos para facturas electrónicas."""

    def __init__(self, smtp_server: str = None, smtp_port: int = None,
                 email: str = None, password: str = None):
        """
        Inicializa el servicio de email.

        Si no se proporcionan credenciales, las toma de la configuración.
        """
        config = obtener_toda_config()

        self.smtp_server = smtp_server or config.get("email_smtp", "smtp.gmail.com")
        self.smtp_port = int(smtp_port or config.get("email_puerto", "587"))
        self.email = email or config.get("email_emisor", "")
        self.password = password or config.get("email_password", "")

    def enviar_factura(self, factura_id: int, destinatario: str,
                       asunto: str = None, mensaje_extra: str = "") -> bool:
        """
        Envía una factura por correo electrónico con XML y PDF adjuntos.

        Args:
            factura_id: ID de la factura en la base de datos
            destinatario: Correo del cliente
            asunto: Asunto del correo (por defecto: "Factura Electrónica")
            mensaje_extra: Mensaje adicional en el cuerpo del correo

        Returns:
            True si se envió correctamente, False en caso contrario
        """
        factura = obtener_factura(factura_id)
        if not factura:
            raise ValueError(f"Factura {factura_id} no encontrada")

        if not destinatario:
            raise ValueError("El destinatario no tiene correo electrónico configurado")

        config = obtener_toda_config()

        if asunto is None:
            asunto = f"Factura Electrónica Nro {factura['secuencial']}"

        # Construir el mensaje
        msg = MIMEMultipart()
        msg["From"] = self.email
        msg["To"] = destinatario
        msg["Subject"] = asunto

        # Cuerpo del mensaje
        cuerpo = f"""
Estimado(a) cliente,

Adjunto encontrará su factura electrónica Nro {factura['secuencial']}
emitida por {config.get('razon_social', 'nuestro negocio')}.

Clave de Acceso: {factura.get('clave_acceso', '')}

{mensaje_extra}

Gracias por su preferencia.

--
{config.get('razon_social', '')}
{config.get('direccion_matriz', '')}
        """.strip()

        msg.attach(MIMEText(cuerpo, "plain", "utf-8"))

        # Adjuntar XML
        xml_path = factura.get("xml_path", "")
        if xml_path and os.path.exists(xml_path):
            self._adjuntar_archivo(msg, xml_path)

        # Adjuntar PDF
        pdf_path = factura.get("pdf_path", "")
        if pdf_path and os.path.exists(pdf_path):
            self._adjuntar_archivo(msg, pdf_path)

        # Enviar
        return self._enviar_mensaje(msg)

    def enviar_correo_simple(self, destinatario: str, asunto: str,
                             cuerpo: str, adjuntos: list = None) -> bool:
        """
        Envía un correo simple con opcionales adjuntos.

        Args:
            destinatario: Correo del destinatario
            asunto: Asunto del correo
            cuerpo: Cuerpo del mensaje
            adjuntos: Lista de rutas de archivos a adjuntar

        Returns:
            True si se envió correctamente
        """
        msg = MIMEMultipart()
        msg["From"] = self.email
        msg["To"] = destinatario
        msg["Subject"] = asunto

        msg.attach(MIMEText(cuerpo, "plain", "utf-8"))

        if adjuntos:
            for ruta in adjuntos:
                if os.path.exists(ruta):
                    self._adjuntar_archivo(msg, ruta)

        return self._enviar_mensaje(msg)

    def _adjuntar_archivo(self, msg: MIMEMultipart, ruta: str):
        """Adjunta un archivo al mensaje MIME."""
        nombre_archivo = os.path.basename(ruta)

        with open(ruta, "rb") as f:
            adjunto = MIMEBase("application", "octet-stream")
            adjunto.set_payload(f.read())
            encoders.encode_base64(adjunto)
            adjunto.add_header(
                "Content-Disposition",
                f'attachment; filename="{nombre_archivo}"',
            )
            msg.attach(adjunto)

    def _enviar_mensaje(self, msg: MIMEMultipart) -> bool:
        """Envía el mensaje a través de SMTP."""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            return True
        except smtplib.SMTPAuthenticationError:
            raise RuntimeError(
                "Error de autenticación SMTP. Verifique el correo y la contraseña. "
                "Para Gmail, use una 'Contraseña de aplicación'."
            )
        except smtplib.SMTPException as e:
            raise RuntimeError(f"Error al enviar correo: {e}")


def obtener_toda_config() -> dict:
    """Importa y retorna la configuración desde database."""
    from database import obtener_toda_config as _get_config
    return _get_config()
