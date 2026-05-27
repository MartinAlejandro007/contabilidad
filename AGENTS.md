# Contabilidad - Sistema de Facturación Electrónica (Ecuador - SRI)

Sistema de escritorio para gestión de ventas, inventario y facturación electrónica conforme al SRI Ecuador.

## Stack
- Python 3.8+
- CustomTkinter (GUI)
- SQLite (base de datos)
- ReportLab (generación PDF/RIDE)
- lxml (generación XML)
- SMTP nativo (envío de correos)

## Comandos

```bash
pip install -r requirements.txt
python main.py
```

## Arquitectura de Archivos

| Archivo | Responsabilidad |
|---|---|
| `main.py` | Entry point, verifica dependencias |
| `database.py` | Schema SQLite, CRUD completo, secuenciales, control de caja |
| `utils.py` | Validación RUC/cédula ecuatoriana, clave de acceso 49 dígitos (módulo 11) |
| `sri_xml.py` | Generación XML factura SRI v1.1.0, PDF (RIDE), puentes firma digital y WS SRI |
| `email_service.py` | Envío SMTP de facturas (XML + PDF) |
| `gui.py` | Interfaz CustomTkinter: POS, inventario, caja, historial, configuración |

## Base de Datos

SQLite en `data/contabilidad.db`. Tablas: `clientes`, `productos`, `precios_cajas`, `facturas`, `detalles_factura`, `caja`, `configuracion`, `secuenciales`.

## Flujo de Facturación

1. POS: agregar productos al carrito → seleccionar cliente → "Emitir Factura"
2. Se genera factura en DB con secuencial autoincremental
3. Se genera XML según estructura SRI (infoTributaria, infoFactura, detalles, totales)
4. Se genera PDF (RIDE) con ReportLab
5. Estado: `pendiente` → `generado` → `enviado` (si se envía por email)
6. **Firma digital y envío al SRI**: puentes implementados pero `NotImplementedError`. Requiere certificado `.p12` y librería `signxml`

## Validaciones SRI

- RUC: 13 dígitos, validación módulo 11 (jurídicas) o cédula + 3 dígitos (naturales)
- Cédula: 10 dígitos, validación módulo 10
- Clave acceso: 49 dígitos con dígito verificador módulo 11
- IVA: 15% vigente (configurable por producto, soporta 0% y exento)

## Pendientes para Producción

- Firma digital XAdES-BES (`sri_xml.py:firmar_xml_xades`)
- Web Services SRI recepción/autorización (`sri_xml.py:SRIWebService`)
- Instalar `signxml` y `zeep` para producción
- Configurar certificado digital `.p12` emitido por entidad autorizada

## Convenciones

- Todo el código y comentarios en español
- Los precios de caja se configuran por producto con tamaños: Pequeña, Mediana, Grande
- Consumidor Final usa RUC `9999999999999`
- Ambiente 1 = Pruebas, 2 = Producción (configurable en GUI)
