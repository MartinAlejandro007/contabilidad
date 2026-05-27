"""
database.py - Gestión de base de datos SQLite para el sistema de contabilidad.

Maneja la creación del esquema, operaciones CRUD para clientes, productos,
precios de caja, facturas y detalles de factura, así como el control de caja.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "contabilidad.db")


def get_db_path() -> str:
    """Retorna la ruta absoluta de la base de datos."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return DB_PATH


def get_connection() -> sqlite3.Connection:
    """Obtiene una conexión con la base de datos."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Inicializa la base de datos creando todas las tablas necesarias."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identificacion TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            direccion TEXT,
            telefono TEXT,
            correo TEXT,
            tipo_contribuyente TEXT DEFAULT 'consumidor_final',
            fecha_creacion TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            precio_base REAL NOT NULL DEFAULT 0,
            stock INTEGER NOT NULL DEFAULT 0,
            iva REAL NOT NULL DEFAULT 15.0,
            activo INTEGER NOT NULL DEFAULT 1,
            fecha_creacion TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS precios_cajas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            tamano TEXT NOT NULL,
            precio_fijo REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
            UNIQUE(producto_id, tamano)
        );

        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clave_acceso TEXT UNIQUE,
            secuencial TEXT NOT NULL,
            cliente_id INTEGER,
            fecha TEXT DEFAULT (datetime('now','localtime')),
            subtotal_sin_iva REAL NOT NULL DEFAULT 0,
            subtotal_iva_0 REAL NOT NULL DEFAULT 0,
            subtotal_iva_15 REAL NOT NULL DEFAULT 0,
            iva REAL NOT NULL DEFAULT 0,
            total REAL NOT NULL DEFAULT 0,
            estado_sri TEXT DEFAULT 'pendiente',
            tipo_comprobante TEXT DEFAULT 'factura',
            xml_path TEXT,
            pdf_path TEXT,
            observaciones TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        );

        CREATE TABLE IF NOT EXISTS detalles_factura (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            factura_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad REAL NOT NULL,
            tipo_empaque TEXT NOT NULL DEFAULT 'unidad',
            precio_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            iva REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (factura_id) REFERENCES facturas(id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        );

        CREATE TABLE IF NOT EXISTS caja (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            tipo TEXT NOT NULL,
            monto REAL NOT NULL DEFAULT 0,
            descripcion TEXT,
            metodo_pago TEXT DEFAULT 'efectivo',
            usuario TEXT DEFAULT 'admin',
            fecha_registro TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT
        );

        CREATE TABLE IF NOT EXISTS secuenciales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_comprobante TEXT NOT NULL DEFAULT '001',
            establecimiento TEXT NOT NULL DEFAULT '001',
            punto_emision TEXT NOT NULL DEFAULT '001',
            siguiente_secuencial INTEGER NOT NULL DEFAULT 1
        );
    """)

    # Insertar configuración por defecto si no existe
    defaults = [
        ("razon_social", "Recuerdos y Artesanías"),
        ("ruc", "0000000000001"),
        ("nombre_comercial", "Recuerdos Mamá"),
        ("direccion_matriz", "Dirección del negocio"),
        ("contribuyente_especial", ""),
        ("obligado_contabilidad", "NO"),
        ("ambiente", "1"),
        ("email_emisor", ""),
        ("email_password", ""),
        ("email_smtp", "smtp.gmail.com"),
        ("email_puerto", "587"),
        ("secuencia_actual", "001001000000001"),
    ]
    for clave, valor in defaults:
        cursor.execute(
            "INSERT OR IGNORE INTO configuracion (clave, valor) VALUES (?, ?)",
            (clave, valor),
        )

    # Insertar secuencial por defecto
    cursor.execute(
        "INSERT OR IGNORE INTO secuenciales (tipo_comprobante, establecimiento, punto_emision, siguiente_secuencial) VALUES (?, ?, ?, ?)",
        ("001", "001", "001", 1),
    )

    # Insertar cliente consumidor final por defecto
    cursor.execute(
        "INSERT OR IGNORE INTO clientes (identificacion, nombre, tipo_contribuyente) VALUES (?, ?, ?)",
        ("9999999999999", "Consumidor Final", "consumidor_final"),
    )

    # Insertar productos demo si no existen
    productos_demo = [
        ("1542", "Recuerdo Bautizo", 5.50, 50, 15.0),
        ("2187", "Recuerdo Cumpleaños", 4.75, 30, 15.0),
        ("3093", "Recuerdo Primera Comunion", 7.00, 40, 15.0),
    ]
    for codigo, nombre, precio, stock, iva in productos_demo:
        cursor.execute(
            "INSERT OR IGNORE INTO productos (codigo, nombre, precio_base, stock, iva) VALUES (?, ?, ?, ?, ?)",
            (codigo, nombre, precio, stock, iva),
        )

    conn.commit()
    conn.close()


# ==================== CLIENTES ====================

def crear_cliente(identificacion: str, nombre: str, direccion: str = "",
                  telefono: str = "", correo: str = "",
                  tipo_contribuyente: str = "consumidor_final") -> int:
    """Crea un nuevo cliente. Retorna el ID."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO clientes (identificacion, nombre, direccion, telefono, correo, tipo_contribuyente)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (identificacion, nombre, direccion, telefono, correo, tipo_contribuyente),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError(f"Ya existe un cliente con identificación {identificacion}")
    finally:
        conn.close()


def obtener_cliente(identificacion: str) -> Optional[dict]:
    """Busca un cliente por su RUC o cédula."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes WHERE identificacion = ?", (identificacion,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def buscar_clientes(termino: str) -> list:
    """Busca clientes por identificación o nombre (búsqueda parcial)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM clientes WHERE identificacion LIKE ? OR nombre LIKE ? ORDER BY nombre",
        (f"%{termino}%", f"%{termino}%"),
    )
    resultados = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return resultados


def obtener_todos_clientes() -> list:
    """Retorna todos los clientes."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes ORDER BY nombre")
    resultados = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return resultados


def actualizar_cliente(cliente_id: int, **kwargs) -> bool:
    """Actualiza campos de un cliente."""
    campos = ", ".join(f"{k} = ?" for k in kwargs.keys())
    valores = list(kwargs.values()) + [cliente_id]
    conn = get_connection()
    try:
        conn.execute(f"UPDATE clientes SET {campos} WHERE id = ?", valores)
        conn.commit()
        return True
    finally:
        conn.close()


# ==================== PRODUCTOS ====================

def crear_producto(codigo: str, nombre: str, precio_base: float,
                   stock: int = 0, iva: float = 15.0) -> int:
    """Crea un nuevo producto. Retorna el ID."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO productos (codigo, nombre, precio_base, stock, iva)
               VALUES (?, ?, ?, ?, ?)""",
            (codigo, nombre, precio_base, stock, iva),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError(f"Ya existe un producto con código {codigo}")
    finally:
        conn.close()


def obtener_producto(codigo: str = None, producto_id: int = None) -> Optional[dict]:
    """Busca un producto por código o ID."""
    conn = get_connection()
    cursor = conn.cursor()
    if codigo:
        cursor.execute("SELECT * FROM productos WHERE codigo = ?", (codigo,))
    elif producto_id:
        cursor.execute("SELECT * FROM productos WHERE id = ?", (producto_id,))
    else:
        conn.close()
        return None
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def buscar_productos(termino: str) -> list:
    """Busca productos por código o nombre."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM productos WHERE activo = 1 AND (codigo LIKE ? OR nombre LIKE ?) ORDER BY nombre",
        (f"%{termino}%", f"%{termino}%"),
    )
    resultados = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return resultados


def obtener_todos_productos() -> list:
    """Retorna todos los productos activos."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos WHERE activo = 1 ORDER BY nombre")
    resultados = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return resultados


def actualizar_producto(producto_id: int, **kwargs) -> bool:
    """Actualiza campos de un producto."""
    campos = ", ".join(f"{k} = ?" for k in kwargs.keys())
    valores = list(kwargs.values()) + [producto_id]
    conn = get_connection()
    try:
        conn.execute(f"UPDATE productos SET {campos} WHERE id = ?", valores)
        conn.commit()
        return True
    finally:
        conn.close()


def ajustar_stock(producto_id: int, cantidad: int) -> bool:
    """Ajusta el stock de un producto (positivo para agregar, negativo para restar)."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE productos SET stock = stock + ? WHERE id = ?",
            (cantidad, producto_id),
        )
        conn.commit()
        return True
    finally:
        conn.close()


# ==================== PRECIOS DE CAJAS ====================

def crear_precio_caja(producto_id: int, tamano: str, precio_fijo: float) -> int:
    """Crea o actualiza un precio de caja para un producto."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO precios_cajas (producto_id, tamano, precio_fijo)
               VALUES (?, ?, ?)
               ON CONFLICT(producto_id, tamano) DO UPDATE SET precio_fijo = excluded.precio_fijo""",
            (producto_id, tamano, precio_fijo),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def obtener_precios_caja(producto_id: int) -> list:
    """Obtiene todos los precios de caja para un producto."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM precios_cajas WHERE producto_id = ?",
        (producto_id,),
    )
    resultados = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return resultados


def obtener_precio_caja(producto_id: int, tamano: str) -> Optional[dict]:
    """Obtiene el precio de un tamaño de caja específico."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM precios_cajas WHERE producto_id = ? AND tamano = ?",
        (producto_id, tamano),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ==================== FACTURAS ====================

def obtener_siguiente_secuencial() -> str:
    """Obtiene el siguiente número secuencial para facturas."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM secuenciales ORDER BY id DESC LIMIT 1")
    seq = cursor.fetchone()
    conn.close()
    if seq:
        return f"{seq['establecimiento']}{seq['punto_emision']}{seq['siguiente_secuencial']:09d}"
    return "001001000000001"


def incrementar_secuencial():
    """Incrementa el contador secuencial después de emitir una factura."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE secuenciales SET siguiente_secuencial = siguiente_secuencial + 1 WHERE id = (SELECT MAX(id) FROM secuenciales)"
        )
        conn.commit()
    finally:
        conn.close()


def crear_factura(cliente_id: int, detalles: list, tipo_comprobante: str = "factura",
                  observaciones: str = "") -> dict:
    """
    Crea una factura completa con sus detalles.

    detalles: lista de dicts con keys:
        producto_id, cantidad, tipo_empaque, precio_unitario, subtotal, iva
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Calcular totales
        subtotal_sin_iva = 0.0
        subtotal_iva_0 = 0.0
        subtotal_iva_15 = 0.0
        total_iva = 0.0

        for d in detalles:
            prod = obtener_producto(producto_id=d["producto_id"])
            iva_prod = prod["iva"] if prod else 15.0
            monto_iva = d["subtotal"] * (iva_prod / 100.0)

            if iva_prod == 0:
                subtotal_iva_0 += d["subtotal"]
            else:
                subtotal_iva_15 += d["subtotal"]
                total_iva += monto_iva

        subtotal_sin_iva = subtotal_iva_0 + subtotal_iva_15
        total = subtotal_sin_iva + total_iva

        # Generar secuencial
        secuencial = obtener_siguiente_secuencial()

        # Generar clave de acceso (se completa después con firma)
        from utils import generar_clave_acceso
        fecha = datetime.now().strftime("%Y%m%d")
        clave_acceso = generar_clave_acceso(
            fecha=fecha,
            tipo_comprobante="01",
            ruc=obtener_config("ruc"),
            ambiente=obtener_config("ambiente"),
            serie=secuencial[:6],
            secuencial=secuencial[6:],
        )

        # Insertar factura
        cursor.execute(
            """INSERT INTO facturas (clave_acceso, secuencial, cliente_id, fecha,
               subtotal_sin_iva, subtotal_iva_0, subtotal_iva_15, iva, total,
               tipo_comprobante, observaciones)
               VALUES (?, ?, ?, datetime('now','localtime'), ?, ?, ?, ?, ?, ?, ?)""",
            (clave_acceso, secuencial, cliente_id, subtotal_sin_iva,
             subtotal_iva_0, subtotal_iva_15, total_iva, total,
             tipo_comprobante, observaciones),
        )
        factura_id = cursor.lastrowid

        # Insertar detalles y ajustar stock
        for d in detalles:
            cursor.execute(
                """INSERT INTO detalles_factura (factura_id, producto_id, cantidad,
                   tipo_empaque, precio_unitario, subtotal, iva)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (factura_id, d["producto_id"], d["cantidad"],
                 d["tipo_empaque"], d["precio_unitario"], d["subtotal"], d["iva"]),
            )
            # Descontar stock
            cursor.execute(
                "UPDATE productos SET stock = stock - ? WHERE id = ?",
                (d["cantidad"], d["producto_id"]),
            )

        # Incrementar secuencial
        cursor.execute(
            "UPDATE secuenciales SET siguiente_secuencial = siguiente_secuencial + 1 WHERE id = (SELECT MAX(id) FROM secuenciales)"
        )

        conn.commit()

        # Retornar datos completos de la factura
        cursor.execute("SELECT * FROM facturas WHERE id = ?", (factura_id,))
        factura = dict(cursor.fetchone())

        cursor.execute(
            "SELECT df.*, p.nombre as producto_nombre, p.codigo as producto_codigo FROM detalles_factura df JOIN productos p ON df.producto_id = p.id WHERE df.factura_id = ?",
            (factura_id,),
        )
        factura["detalles"] = [dict(r) for r in cursor.fetchall()]

        return factura

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def obtener_factura(factura_id: int) -> Optional[dict]:
    """Obtiene una factura con sus detalles."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM facturas WHERE id = ?", (factura_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    factura = dict(row)
    cursor.execute(
        "SELECT df.*, p.nombre as producto_nombre, p.codigo as producto_codigo FROM detalles_factura df JOIN productos p ON df.producto_id = p.id WHERE df.factura_id = ?",
        (factura_id,),
    )
    factura["detalles"] = [dict(r) for r in cursor.fetchall()]

    # Datos del cliente
    cursor.execute(
        "SELECT * FROM clientes WHERE id = ?", (factura["cliente_id"],)
    )
    cliente_row = cursor.fetchone()
    factura["cliente"] = dict(cliente_row) if cliente_row else None

    conn.close()
    return factura


def obtener_todas_facturas(fecha_desde: str = None, fecha_hasta: str = None) -> list:
    """Obtiene todas las facturas, opcionalmente filtradas por fecha."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT f.*, c.nombre as cliente_nombre, c.identificacion as cliente_identificacion
        FROM facturas f
        LEFT JOIN clientes c ON f.cliente_id = c.id
    """
    params = []
    condiciones = []

    if fecha_desde:
        condiciones.append("f.fecha >= ?")
        params.append(fecha_desde)
    if fecha_hasta:
        condiciones.append("f.fecha <= ?")
        params.append(fecha_hasta)

    if condiciones:
        query += " WHERE " + " AND ".join(condiciones)

    query += " ORDER BY f.fecha DESC"

    cursor.execute(query, params)
    resultados = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return resultados


def actualizar_estado_factura(factura_id: int, estado: str, xml_path: str = "", pdf_path: str = ""):
    """Actualiza el estado SRI de una factura."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE facturas SET estado_sri = ?, xml_path = ?, pdf_path = ? WHERE id = ?",
            (estado, xml_path, pdf_path, factura_id),
        )
        conn.commit()
    finally:
        conn.close()


# ==================== CONTROL DE CAJA ====================

def registrar_movimiento_caja(tipo: str, monto: float, descripcion: str = "",
                              metodo_pago: str = "efectivo", usuario: str = "admin"):
    """Registra un movimiento de caja (venta, gasto, apertura, cierre)."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO caja (fecha, tipo, monto, descripcion, metodo_pago, usuario)
               VALUES (date('now','localtime'), ?, ?, ?, ?, ?)""",
            (tipo, monto, descripcion, metodo_pago, usuario),
        )
        conn.commit()
    finally:
        conn.close()


def obtener_resumen_caja(fecha: str = None) -> dict:
    """Obtiene el resumen de caja para una fecha."""
    if not fecha:
        fecha = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COALESCE(SUM(monto), 0) FROM caja WHERE fecha = ? AND tipo = 'venta' AND metodo_pago = 'efectivo'",
        (fecha,),
    )
    efectivo = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COALESCE(SUM(monto), 0) FROM caja WHERE fecha = ? AND tipo = 'venta' AND metodo_pago = 'transferencia'",
        (fecha,),
    )
    transferencia = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COALESCE(SUM(monto), 0) FROM caja WHERE fecha = ? AND tipo = 'gasto'",
        (fecha,),
    )
    gastos = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COALESCE(SUM(monto), 0) FROM caja WHERE fecha = ? AND tipo = 'apertura'",
        (fecha,),
    )
    apertura = cursor.fetchone()[0]

    conn.close()

    return {
        "fecha": fecha,
        "efectivo": round(efectivo, 2),
        "transferencia": round(transferencia, 2),
        "gastos": round(gastos, 2),
        "apertura": round(apertura, 2),
        "total_ventas": round(efectivo + transferencia, 2),
        "total_caja": round(apertura + efectivo + transferencia - gastos, 2),
    }


# ==================== CONFIGURACIÓN ====================

def obtener_config(clave: str) -> str:
    """Obtiene un valor de configuración."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuracion WHERE clave = ?", (clave,))
    row = cursor.fetchone()
    conn.close()
    return row["valor"] if row else ""


def guardar_config(clave: str, valor: str):
    """Guarda un valor de configuración."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO configuracion (clave, valor) VALUES (?, ?) ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor",
            (clave, valor),
        )
        conn.commit()
    finally:
        conn.close()


def obtener_toda_config() -> dict:
    """Obtiene toda la configuración como diccionario."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM configuracion")
    config = {row["clave"]: row["valor"] for row in cursor.fetchall()}
    conn.close()
    return config
