"""
sri_xml.py - Generación de XML de Factura Electrónica para el SRI Ecuador.

Genera el XML según la estructura oficial vigente del SRI, incluyendo:
- infoTributaria
- infoFactura
- detalles
- totales
- infoAdicional

También genera el PDF (RIDE) usando ReportLab.
"""

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
from typing import Optional

from database import obtener_config, obtener_factura


# ==================== GENERACIÓN DE XML ====================

def generar_xml_factura(factura: dict) -> str:
    """
    Genera el XML de factura electrónica según la estructura del SRI.

    La estructura sigue la ficha técnica oficial:
    https://www.sri.gob.ec/facturacion-electronica
    """
    config = obtener_toda_config()

    # Elemento raíz
    factura_elem = ET.Element("factura")
    factura_elem.set("id", "comprobante")
    factura_elem.set("version", "1.1.0")

    # infoTributaria
    info_tributaria = ET.SubElement(factura_elem, "infoTributaria")
    ET.SubElement(info_tributaria, "ambiente").text = config.get("ambiente", "1")
    ET.SubElement(info_tributaria, "tipoEmision").text = "1"
    ET.SubElement(info_tributaria, "razonSocial").text = config.get("razon_social", "")
    ET.SubElement(info_tributaria, "nombreComercial").text = config.get("nombre_comercial", "")
    ET.SubElement(info_tributaria, "ruc").text = config.get("ruc", "")
    ET.SubElement(info_tributaria, "claveAcceso").text = factura.get("clave_acceso", "")
    ET.SubElement(info_tributaria, "codDoc").text = "01"
    ET.SubElement(info_tributaria, "estab").text = factura["secuencial"][:3]
    ET.SubElement(info_tributaria, "ptoEmi").text = factura["secuencial"][3:6]
    ET.SubElement(info_tributaria, "secuencial").text = factura["secuencial"][6:]
    ET.SubElement(info_tributaria, "dirMatriz").text = config.get("direccion_matriz", "")

    # Contribuyente especial (si aplica)
    if config.get("contribuyente_especial"):
        ET.SubElement(info_tributaria, "contribuyenteEspecial").text = config["contribuyente_especial"]

    ET.SubElement(info_tributaria, "obligadoContabilidad").text = config.get("obligado_contabilidad", "NO")

    # infoFactura
    info_factura = ET.SubElement(factura_elem, "infoFactura")
    ET.SubElement(info_factura, "fechaEmision").text = datetime.now().strftime("%d/%m/%Y")
    ET.SubElement(info_factura, "dirEstablecimiento").text = config.get("direccion_matriz", "")

    # Tipo de identificación del cliente
    cliente = factura.get("cliente", {})
    if cliente:
        tipo_identificacion = _obtener_tipo_identificacion(cliente.get("tipo_contribuyente", "consumidor_final"))
        ET.SubElement(info_factura, "tipoIdentificacionComprador").text = tipo_identificacion
        ET.SubElement(info_factura, "guiasRemision").text = ""
        ET.SubElement(info_factura, "razonSocialComprador").text = cliente.get("nombre", "Consumidor Final")
        ET.SubElement(info_factura, "identificacionComprador").text = cliente.get("identificacion", "9999999999999")
        ET.SubElement(info_factura, "totalSinImpuestos").text = f"{factura['subtotal_sin_iva']:.2f}"

    # Total con descuentos (sin descuentos por ahora)
    ET.SubElement(info_factura, "totalDescuento").text = "0.00"

    # totalesConImpuestos
    totales_impuestos = ET.SubElement(info_factura, "totalesConImpuestos")

    # IVA 0%
    if factura["subtotal_iva_0"] > 0:
        total_impuesto_0 = ET.SubElement(totales_impuestos, "totalImpuesto")
        ET.SubElement(total_impuesto_0, "codigo").text = "2"
        ET.SubElement(total_impuesto_0, "codigoPorcentaje").text = "2"
        ET.SubElement(total_impuesto_0, "baseImponible").text = f"{factura['subtotal_iva_0']:.2f}"
        ET.SubElement(total_impuesto_0, "valor").text = "0.00"

    # IVA 15%
    if factura["subtotal_iva_15"] > 0:
        total_impuesto_15 = ET.SubElement(totales_impuestos, "totalImpuesto")
        ET.SubElement(total_impuesto_15, "codigo").text = "2"
        ET.SubElement(total_impuesto_15, "codigoPorcentaje").text = "3"
        ET.SubElement(total_impuesto_15, "baseImponible").text = f"{factura['subtotal_iva_15']:.2f}"
        ET.SubElement(total_impuesto_15, "valor").text = f"{factura['iva']:.2f}"

    # propina (no aplica)
    ET.SubElement(info_factura, "propina").text = "0.00"

    # Importaciones (no aplica)
    ET.SubElement(info_factura, "importeTotal").text = f"{factura['total']:.2f}"
    ET.SubElement(info_factura, "moneda").text = "DOLAR"

    # pagos
    pagos = ET.SubElement(info_factura, "pagos")
    pago = ET.SubElement(pagos, "pago")
    ET.SubElement(pago, "formaPago").text = "01"
    ET.SubElement(pago, "total").text = f"{factura['total']:.2f}"
    ET.SubElement(pago, "plazo").text = "0"
    ET.SubElement(pago, "unidadTiempo").text = "dias"

    # detalles
    detalles_elem = ET.SubElement(factura_elem, "detalles")

    for d in factura.get("detalles", []):
        detalle = ET.SubElement(detalles_elem, "detalle")
        ET.SubElement(detalle, "codigoPrincipal").text = d.get("producto_codigo", "")
        ET.SubElement(detalle, "codigoAuxiliar").text = ""
        ET.SubElement(detalle, "descripcion").text = f"{d.get('producto_nombre', '')} [{d.get('tipo_empaque', 'unidad')}]"
        ET.SubElement(detalle, "cantidad").text = f"{d['cantidad']:.2f}"
        ET.SubElement(detalle, "precioUnitario").text = f"{d['precio_unitario']:.2f}"
        ET.SubElement(detalle, "descuento").text = "0.00"
        ET.SubElement(detalle, "precioTotalSinImpuesto").text = f"{d['subtotal']:.2f}"

        # Detalles de impuestos por línea
        impuestos_detalle = ET.SubElement(detalle, "impuestos")
        impuesto_detalle = ET.SubElement(impuestos_detalle, "impuesto")
        ET.SubElement(impuesto_detalle, "codigo").text = "2"

        # Determinar código de porcentaje según IVA
        iva_linea = d.get("iva", 15)
        if iva_linea == 0:
            ET.SubElement(impuesto_detalle, "codigoPorcentaje").text = "2"
        elif iva_linea == 15:
            ET.SubElement(impuesto_detalle, "codigoPorcentaje").text = "3"
        else:
            ET.SubElement(impuesto_detalle, "codigoPorcentaje").text = "3"

        ET.SubElement(impuesto_detalle, "tarifa").text = f"{iva_linea:.2f}"
        ET.SubElement(impuesto_detalle, "baseImponible").text = f"{d['subtotal']:.2f}"
        ET.SubElement(impuesto_detalle, "valor").text = f"{d['subtotal'] * (iva_linea / 100):.2f}"

    # infoAdicional
    info_adicional = ET.SubElement(factura_elem, "infoAdicional")
    campo = ET.SubElement(info_adicional, "campoAdicional")
    campo.set("nombre", "email")
    if cliente:
        campo.text = cliente.get("correo", "")
    else:
        campo.text = ""

    # Observaciones
    if factura.get("observaciones"):
        campo_obs = ET.SubElement(info_adicional, "campoAdicional")
        campo_obs.set("nombre", "observaciones")
        campo_obs.text = factura["observaciones"]

    # Convertir a string con formato bonito
    xml_str = ET.tostring(factura_elem, encoding="unicode")
    dom = minidom.parseString(xml_str)
    return dom.toprettyxml(indent="  ", encoding=None)


def _obtener_tipo_identificacion(tipo_contribuyente: str) -> str:
    """
    Retorna el código de tipo de identificación según el SRI.
    04 = RUC, 05 = Cédula, 06 = Pasaporte, 07 = Consumidor Final
    """
    mapeo = {
        "ruc": "04",
        "cedula": "05",
        "pasaporte": "06",
        "consumidor_final": "07",
    }
    return mapeo.get(tipo_contribuyente, "07")


def guardar_xml(factura_id: int, xml_content: str) -> str:
    """Guarda el XML en el sistema de archivos."""
    directorio = os.path.join(os.path.dirname(__file__), "data", "xml")
    os.makedirs(directorio, exist_ok=True)

    factura = obtener_factura(factura_id)
    nombre_archivo = f"factura_{factura['clave_acceso']}.xml"
    ruta = os.path.join(directorio, nombre_archivo)

    with open(ruta, "w", encoding="utf-8") as f:
        f.write(xml_content)

    return ruta


def obtener_toda_config() -> dict:
    """Importa y retorna la configuración desde database."""
    from database import obtener_toda_config as _get_config
    return _get_config()


# ==================== GENERACIÓN DE PDF (RIDE) ====================

def generar_pdf_factura(factura: dict) -> str:
    """
    Genera el PDF representativo de la factura electrónica (RIDE).
    Usa ReportLab para crear un documento con formato profesional.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
        PageBreak
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

    config = obtener_toda_config()
    directorio = os.path.join(os.path.dirname(__file__), "data", "pdf")
    os.makedirs(directorio, exist_ok=True)

    nombre_archivo = f"factura_{factura['clave_acceso']}.pdf"
    ruta = os.path.join(directorio, nombre_archivo)

    doc = SimpleDocTemplate(ruta, pagesize=letter, rightMargin=0.75*inch,
                           leftMargin=0.75*inch, topMargin=0.75*inch,
                           bottomMargin=0.75*inch)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Titulo", fontSize=16, leading=20,
                              spaceAfter=6, textColor=HexColor("#1a5276")))
    styles.add(ParagraphStyle(name="Subtitulo", fontSize=11, leading=14,
                              spaceAfter=4, textColor=HexColor("#2c3e50")))
    styles.add(ParagraphStyle(name="NormalPeq", fontSize=9, leading=12,
                              spaceAfter=2))
    styles.add(ParagraphStyle(name="Derecha", fontSize=9, leading=12,
                              alignment=TA_RIGHT, spaceAfter=2))
    styles.add(ParagraphStyle(name="Centro", fontSize=9, leading=12,
                              alignment=TA_CENTER, spaceAfter=2))
    styles.add(ParagraphStyle(name="Clave", fontSize=7, leading=9,
                              alignment=TA_CENTER, spaceAfter=2,
                              textColor=HexColor("#7f8c8d")))

    elementos = []

    # Encabezado
    elementos.append(Paragraph(config.get("razon_social", "Recuerdos y Artesanías"), styles["Titulo"]))
    elementos.append(Paragraph(config.get("nombre_comercial", ""), styles["Subtitulo"]))
    elementos.append(Paragraph(f"RUC: {config.get('ruc', '')}", styles["NormalPeq"]))
    elementos.append(Paragraph(f"Matriz: {config.get('direccion_matriz', '')}", styles["NormalPeq"]))
    elementos.append(Spacer(1, 10))

    # Datos de la factura
    if config.get("contribuyente_especial"):
        elementos.append(Paragraph(f"Contribuyente Especial Nro: {config['contribuyente_especial']}", styles["NormalPeq"]))

    elementos.append(Paragraph(f"FACTURA Nro: {factura['secuencial']}", styles["Subtitulo"]))
    elementos.append(Paragraph(f"Fecha de Emisión: {factura['fecha']}", styles["NormalPeq"]))
    elementos.append(Spacer(1, 5))

    # Clave de acceso
    elementos.append(Paragraph("CLAVE DE ACCESO:", styles["Centro"]))
    elementos.append(Paragraph(factura.get("clave_acceso", ""), styles["Clave"]))
    elementos.append(Paragraph(f"Ambiente: {'PRUEBAS' if config.get('ambiente') == '1' else 'PRODUCCIÓN'}", styles["Centro"]))
    elementos.append(Spacer(1, 10))

    # Datos del cliente
    cliente = factura.get("cliente", {})
    if cliente:
        elementos.append(Paragraph("DATOS DEL CLIENTE:", styles["Subtitulo"]))
        elementos.append(Paragraph(f"Nombre: {cliente.get('nombre', '')}", styles["NormalPeq"]))
        elementos.append(Paragraph(f"Identificación: {cliente.get('identificacion', '')}", styles["NormalPeq"]))
        elementos.append(Paragraph(f"Dirección: {cliente.get('direccion', '')}", styles["NormalPeq"]))
        if cliente.get("correo"):
            elementos.append(Paragraph(f"Email: {cliente['correo']}", styles["NormalPeq"]))
        elementos.append(Spacer(1, 10))

    # Tabla de detalles
    datos_detalle = [["Código", "Descripción", "Cant.", "P. Unit.", "Subtotal"]]
    for d in factura.get("detalles", []):
        datos_detalle.append([
            d.get("producto_codigo", ""),
            f"{d.get('producto_nombre', '')} [{d.get('tipo_empaque', '')}]",
            f"{d['cantidad']:.2f}",
            f"${d['precio_unitario']:.2f}",
            f"${d['subtotal']:.2f}",
        ])

    tabla_detalle = Table(datos_detalle, colWidths=[1.2*inch, 2.5*inch, 0.8*inch, 1*inch, 1*inch])
    tabla_detalle.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1a5276")),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#ffffff")),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BACKGROUND", (0, 1), (-1, -1), HexColor("#f8f9fa")),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#bdc3c7")),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
    ]))
    elementos.append(tabla_detalle)
    elementos.append(Spacer(1, 10))

    # Totales
    datos_totales = [
        ["Subtotal sin IVA", f"${factura['subtotal_sin_iva']:.2f}"],
        ["Subtotal IVA 0%", f"${factura['subtotal_iva_0']:.2f}"],
        ["Subtotal IVA 15%", f"${factura['subtotal_iva_15']:.2f}"],
        ["IVA", f"${factura['iva']:.2f}"],
        ["TOTAL", f"${factura['total']:.2f}"],
    ]

    tabla_totales = Table(datos_totales, colWidths=[4*inch, 1.5*inch])
    tabla_totales.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, -1), (-1, -1), HexColor("#1a5276")),
        ("TEXTCOLOR", (0, -1), (-1, -1), HexColor("#ffffff")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#bdc3c7")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elementos.append(tabla_totales)

    if factura.get("observaciones"):
        elementos.append(Spacer(1, 10))
        elementos.append(Paragraph("Observaciones:", styles["Subtitulo"]))
        elementos.append(Paragraph(factura["observaciones"], styles["NormalPeq"]))

    doc.build(elementos)
    return ruta


# ==================== PUENTE PARA FIRMA DIGITAL ====================

def firmar_xml_xades(xml_content: str, certificado_path: str, clave_path: str) -> str:
    """
    PUENTE: Firma el XML con firma digital XAdES-BES.

    Para producción, implementar usando:
    - lxml con xmlsec1
    - O la librería 'signxml' de Python
    - O el firmador oficial del SRI

    Args:
        xml_content: Contenido XML sin firmar
        certificado_path: Ruta al archivo .p12 o .pem del certificado
        clave_path: Ruta a la clave privada

    Returns:
        XML firmado como string
    """
    # TODO: Implementar firma XAdES-BES con signxml o xmlsec
    # Ejemplo con signxml:
    # from signxml import XMLSigner
    # from lxml import etree
    # from cryptography.hazmat.primitives.serialization import pkcs12
    #
    # with open(certificado_path, "rb") as f:
    #     p12_data = f.read()
    # private_key, certificate, _ = pkcs12.load_key_and_certificates(
    #     p12_data, b"password_certificado"
    # )
    # signer = XMLSigner(method=signxml.methods.enveloped,
    #                    signature_algorithm="rsa-sha256",
    #                    digest_algorithm="sha256")
    # root = etree.fromstring(xml_content.encode())
    # signed_root = signer.sign(root, key=private_key, cert=[certificate])
    # return etree.tostring(signed_root, encoding="unicode", xml_declaration=True)

    raise NotImplementedError(
        "Firma digital XAdES-BES no implementada. "
        "Configure certificado digital y use la librería 'signxml'."
    )


# ==================== PUENTE PARA WEB SERVICES DEL SRI ====================

class SRIWebService:
    """
    PUENTE: Cliente para los Web Services del SRI.

    Endpoints oficiales:
    - Recepción: https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl
    - Autorización: https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl

    Para pruebas (ambiente 1):
    - Recepción: https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl
    - Autorización: https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl
    """

    URL_RECEPCION_PRODUCCION = "https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl"
    URL_AUTORIZACION_PRODUCCION = "https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl"
    URL_RECEPCION_PRUEBAS = "https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl"
    URL_AUTORIZACION_PRUEBAS = "https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl"

    def __init__(self, ambiente: str = "1"):
        self.ambiente = ambiente
        if ambiente == "2":
            self.url_recepcion = self.URL_RECEPCION_PRODUCCION
            self.url_autorizacion = self.URL_AUTORIZACION_PRODUCCION
        else:
            self.url_recepcion = self.URL_RECEPCION_PRUEBAS
            self.url_autorizacion = self.URL_AUTORIZACION_PRUEBAS

    def enviar_comprobante(self, xml_firmado: str) -> dict:
        """
        Envía el comprobante firmado al SRI para recepción.

        Args:
            xml_firmado: XML firmado en base64

        Returns:
            Dict con estado de la recepción
        """
        # TODO: Implementar con Zeep o SUDS
        # from zeep import Client
        # import base64
        #
        # client = Client(self.url_recepcion)
        # xml_base64 = base64.b64encode(xml_firmado.encode()).decode()
        # respuesta = client.validarComprobante(
        #     tipoComprobante="01",
        #     comprobante=xml_base64
        # )
        # return dict(respuesta)

        raise NotImplementedError(
            "Envío al SRI no implementado. Use la librería 'zeep' para consumir el Web Service."
        )

    def consultar_autorizacion(self, clave_acceso: str) -> dict:
        """
        Consulta el estado de autorización de un comprobante.

        Args:
            clave_acceso: Clave de acceso de 49 dígitos

        Returns:
            Dict con estado de autorización
        """
        # TODO: Implementar con Zeep o SUDS
        # from zeep import Client
        #
        # client = Client(self.url_autorizacion)
        # respuesta = client.autorizacionComprobante(
        #     claveAccesoComprobante=clave_acceso
        # )
        # return dict(respuesta)

        raise NotImplementedError(
            "Consulta de autorización no implementada. Use la librería 'zeep'."
        )
