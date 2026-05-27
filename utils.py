"""
utils.py - Utilidades de validación y generación para el SRI Ecuador.

Incluye:
- Validación de RUC (personas naturales y jurídicas)
- Validación de cédula de identidad
- Generación de clave de acceso de 49 dígitos (módulo 11)
- Formateo de números para el SRI
"""

import re
from datetime import datetime


# ==================== VALIDACIÓN DE CÉDULA ====================

def validar_cedula(cedula: str) -> bool:
    """
    Valida una cédula de identidad ecuatoriana (10 dígitos).

    Algoritmo módulo 10 según lo establecido por el Registro Civil del Ecuador.
    """
    cedula = cedula.strip()

    if not cedula.isdigit():
        return False
    if len(cedula) != 10:
        return False

    # Los dos primeros dígitos corresponden a la provincia (01-24)
    provincia = int(cedula[:2])
    if provincia < 1 or provincia > 24:
        return False

    # Tercer dígito debe ser menor a 6 (personas naturales)
    tercer_digito = int(cedula[2])
    if tercer_digito >= 6:
        return False

    # Algoritmo módulo 10
    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    total = 0

    for i in range(9):
        valor = int(cedula[i]) * coeficientes[i]
        if valor > 9:
            valor -= 9
        total += valor

    digito_verificador = (10 - (total % 10)) % 10
    return digito_verificador == int(cedula[9])


# ==================== VALIDACIÓN DE RUC ====================

def validar_ruc(ruc: str) -> bool:
    """
    Valida un RUC ecuatoriano (13 dígit).

    - Personas naturales: primeros 10 dígitos = cédula válida
    - Personas jurídicas: tercer dígito >= 6, dígito verificador módulo 11
    - RUC público (entidades del estado): tercer dígito = 6
    """
    ruc = ruc.strip()

    if not ruc.isdigit():
        return False
    if len(ruc) != 13:
        return False

    # Los dos primeros dígitos deben corresponder a una provincia
    provincia = int(ruc[:2])
    if provincia < 1 or provincia > 30:
        return False

    tercer_digito = int(ruc[2])

    if tercer_digito < 6:
        # Persona natural: validar los primeros 10 dígitos como cédula
        return validar_cedula(ruc[:10])
    elif tercer_digito == 6:
        # Entidad pública: validación especial módulo 11
        return _validar_ruc_publico(ruc)
    else:
        # Persona jurídica: validación módulo 11
        return _validar_ruc_juridico(ruc)


def _validar_ruc_juridico(ruc: str) -> bool:
    """Valida RUC de persona jurídica (módulo 11)."""
    coeficientes = [3, 2, 7, 6, 5, 4, 3, 2, 3, 2, 3, 2]
    total = 0

    for i in range(12):
        total += int(ruc[i]) * coeficientes[i]

    residuo = total % 11
    digito_verificador = 11 - residuo

    if digito_verificador >= 10:
        digito_verificador = 0

    return digito_verificador == int(ruc[12])


def _validar_ruc_publico(ruc: str) -> bool:
    """Valida RUC de entidad pública (módulo 11)."""
    coeficientes = [3, 2, 7, 6, 5, 4, 3, 2, 3, 2, 3, 2]
    total = 0

    for i in range(12):
        total += int(ruc[i]) * coeficientes[i]

    residuo = total % 11
    digito_verificador = 11 - residuo

    if digito_verificador >= 10:
        digito_verificador = 0

    return digito_verificador == int(ruc[12])


# ==================== VALIDACIÓN DE IDENTIFICACIÓN ====================

def validar_identificacion(identificacion: str) -> tuple:
    """
    Valida una identificación (RUC o cédula).

    Retorna: (es_valido: bool, tipo: str, mensaje: str)
    tipo puede ser: 'ruc', 'cedula', 'consumidor_final', 'pasaporte', 'invalido'
    """
    identificacion = identificacion.strip()

    # Consumidor final
    if identificacion == "9999999999999":
        return True, "consumidor_final", "Consumidor Final"

    # Pasaporte (no se valida, solo se acepta)
    if re.match(r'^[A-Z0-9]{3,13}$', identificacion, re.IGNORECASE):
        return True, "pasaporte", "Pasaporte"

    # Cédula (10 dígitos)
    if len(identificacion) == 10:
        if validar_cedula(identificacion):
            return True, "cedula", "Cédula válida"
        return False, "invalido", "Cédula inválida"

    # RUC (13 dígitos)
    if len(identificacion) == 13:
        if validar_ruc(identificacion):
            return True, "ruc", "RUC válido"
        return False, "invalido", "RUC inválido"

    return False, "invalido", "Identificación debe ser de 10 o 13 dígitos"


# ==================== CLAVE DE ACCESO SRI ====================

def generar_clave_acceso(fecha: str, tipo_comprobante: str, ruc: str,
                         ambiente: str, serie: str, secuencial: str,
                         codigo_numerico: str = None) -> str:
    """
    Genera la clave de acceso de 49 dígitos para el SRI.

    Estructura:
    - Fecha (8 dígitos): AAAAMMDD
    - Tipo de comprobante (2 dígitos): 01=Factura, 04=Nota de Crédito, etc.
    - RUC (13 dígitos)
    - Tipo de ambiente (1 dígito): 1=Pruebas, 2=Producción
    - Tipo de emisión (1 dígito): 1=Normal (por ahora)
    - Código numérico (8 dígitos)
    - Tipo de comprobante (repetido, 2 dígitos)
    - Secuencial (9 dígitos)
    - Dígito verificador (1 dígito, módulo 11)

    Total: 49 dígitos
    """
    if codigo_numerico is None:
        import random
        codigo_numerico = f"{random.randint(1, 99999999):08d}"

    fecha_str = fecha.replace("-", "")
    serie_str = str(serie).zfill(6)
    secuencial_str = str(secuencial).zfill(9)

    clave_sin_dv = (
        f"{fecha_str}"
        f"{tipo_comprobante}"
        f"{ruc}"
        f"{ambiente}"
        f"1"
        f"{codigo_numerico}"
        f"{tipo_comprobante}"
        f"{secuencial_str}"
    )

    # Calcular dígito verificador (módulo 11)
    coeficientes = [7, 1, 3, 5, 2, 4, 6, 3, 7, 1, 3, 5, 2, 4, 6,
                    3, 7, 1, 3, 5, 2, 4, 6, 3, 7, 1, 3, 5, 2, 4, 6,
                    3, 7, 1, 3, 5, 2, 4, 6, 3, 7, 1, 3, 5, 2, 4, 6, 3]

    total = 0
    for i, digito in enumerate(clave_sin_dv):
        total += int(digito) * coeficientes[i]

    residuo = total % 11
    if residuo == 0:
        digito_verificador = 1
    elif residuo == 1:
        digito_verificador = 0
    else:
        digito_verificador = 11 - residuo

    return f"{clave_sin_dv}{digito_verificador}"


# ==================== FORMATEO DE NÚMEROS ====================

def formato_sri_decimal(valor: float, decimales: int = 2) -> str:
    """Formatea un número con el formato requerido por el SRI."""
    return f"{valor:.{decimales}f}"


def formato_sri_moneda(valor: float) -> str:
    """Formatea un valor monetario para el SRI (2 decimales)."""
    return formato_sri_decimal(valor, 2)


# ==================== UTILIDADES GENERALES ====================

def obtener_fecha_actual() -> str:
    """Retorna la fecha actual en formato AAAA-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


def obtener_fecha_sri() -> str:
    """Retorna la fecha actual en formato AAAAMMDD para el SRI."""
    return datetime.now().strftime("%Y%m%d")


def obtener_hora_actual() -> str:
    """Retorna la hora actual en formato HH:MM:SS."""
    return datetime.now().strftime("%H:%M:%S")
