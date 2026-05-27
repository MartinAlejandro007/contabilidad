"""
gui.py - Interfaz grafica moderna del sistema de contabilidad.

Diseno profesional con CustomTkinter:
- Dashboard con tarjetas de resumen
- POS interactivo con tarjetas de productos y carrito visual
- Barra de estado inferior
- Dialogos modernos
"""

import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime
from typing import Optional

from database import (
    init_db, buscar_productos, obtener_producto, obtener_todos_productos,
    crear_producto, actualizar_producto, ajustar_stock,
    buscar_clientes, obtener_cliente, obtener_todos_clientes,
    crear_cliente, obtener_precios_caja, crear_precio_caja,
    crear_factura, obtener_siguiente_secuencial, obtener_todas_facturas,
    obtener_factura, actualizar_estado_factura,
    registrar_movimiento_caja, obtener_resumen_caja,
    obtener_config, guardar_config, obtener_toda_config,
)
from utils import validar_identificacion
from sri_xml import generar_xml_factura, guardar_xml, generar_pdf_factura
from email_service import EmailService

COLORS = {
    "primary": "#2563eb", "primary_dark": "#1d4ed8", "primary_light": "#dbeafe",
    "secondary": "#7c3aed", "success": "#059669", "success_light": "#d1fae5",
    "warning": "#d97706", "warning_light": "#fef3c7", "danger": "#dc2626",
    "danger_light": "#fee2e2", "dark": "#1e293b", "gray_700": "#334155",
    "gray_600": "#475569", "gray_500": "#64748b", "gray_400": "#94a3b8",
    "gray_300": "#cbd5e1", "gray_200": "#e2e8f0", "gray_100": "#f1f5f9",
    "gray_50": "#f8fafc", "white": "#ffffff", "sidebar_bg": "#0f172a",
    "sidebar_hover": "#1e293b", "sidebar_active": "#2563eb",
    "card_border": "#e2e8f0",
}

TAMANO_CAJAS = ["Pequena", "Mediana", "Grande"]


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Recuerdos - Sistema de Facturacion")
        self.geometry("1350x800")
        self.minsize(1100, 650)
        init_db()
        self.carrito = []
        self.panel_actual = None
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self._crear_header()
        self._crear_sidebar()
        self._crear_contenido()
        self._crear_statusbar()
        self._mostrar_panel("dashboard")

    def _crear_header(self):
        self.header = ctk.CTkFrame(self, height=56, fg_color=COLORS["white"], corner_radius=0)
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.header.grid_propagate(False)
        logo_frame = ctk.CTkFrame(self.header, fg_color="transparent", corner_radius=0)
        logo_frame.pack(side="left", padx=20, fill="y")
        ctk.CTkLabel(logo_frame, text="\U0001f9fe", font=ctk.CTkFont(size=24)).pack(side="left")
        ctk.CTkLabel(logo_frame, text="Recuerdos", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLORS["dark"]).pack(side="left", padx=(8, 4))
        ctk.CTkLabel(logo_frame, text="Sistema de Facturacion", font=ctk.CTkFont(size=12), text_color=COLORS["gray_500"]).pack(side="left")
        self.lbl_fecha = ctk.CTkLabel(self.header, text="", font=ctk.CTkFont(size=13), text_color=COLORS["gray_600"])
        self.lbl_fecha.pack(side="right", padx=20)
        self._actualizar_reloj()

    def _actualizar_reloj(self):
        ahora = datetime.now()
        self.lbl_fecha.configure(text=ahora.strftime("%A, %d de %B de %Y  -  %H:%M"))
        self.after(60000, self._actualizar_reloj)

    def _crear_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=COLORS["sidebar_bg"], corner_radius=0)
        self.sidebar.grid(row=1, column=0, sticky="nsew", rowspan=2)
        self.sidebar.grid_propagate(False)
        ctk.CTkFrame(self.sidebar, fg_color="transparent", height=20, corner_radius=0).pack(fill="x", pady=(10, 0))
        self.botones_nav = {}
        botones = [
            ("dashboard", "\U0001f4ca", "Dashboard"),
            ("ventas", "\U0001f6d2", "Punto de Venta"),
            ("inventario", "\U0001f4e6", "Inventario"),
            ("caja", "\U0001f4b0", "Control de Caja"),
            ("facturas", "\U0001f4cb", "Historial"),
            ("config", "\u2699\ufe0f", "Configuracion"),
        ]
        for clave, icono, texto in botones:
            btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", corner_radius=0, height=44)
            btn_frame.pack(fill="x", padx=12, pady=2)
            btn_frame.pack_propagate(False)
            btn = ctk.CTkButton(btn_frame, text=f"  {icono}  {texto}", corner_radius=10, height=38,
                fg_color="transparent", text_color=COLORS["gray_400"], hover_color=COLORS["sidebar_hover"],
                anchor="w", font=ctk.CTkFont(size=14), command=lambda k=clave: self._mostrar_panel(k))
            btn.pack(fill="both", padx=4, pady=2)
            self.botones_nav[clave] = btn

    def _crear_contenido(self):
        self.contenido = ctk.CTkFrame(self, fg_color=COLORS["gray_100"], corner_radius=0)
        self.contenido.grid(row=1, column=1, sticky="nsew")
        self.contenido.grid_columnconfigure(0, weight=1)
        self.contenido.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def _crear_statusbar(self):
        self.statusbar = ctk.CTkFrame(self, height=30, fg_color=COLORS["white"], corner_radius=0)
        self.statusbar.grid(row=2, column=1, sticky="ew")
        self.statusbar.grid_propagate(False)
        self.lbl_status = ctk.CTkLabel(self.statusbar, text="Listo", font=ctk.CTkFont(size=11), text_color=COLORS["gray_500"])
        self.lbl_status.pack(side="left", padx=15)
        self.lbl_secuencial_status = ctk.CTkLabel(self.statusbar, text="", font=ctk.CTkFont(size=11), text_color=COLORS["gray_500"])
        self.lbl_secuencial_status.pack(side="right", padx=15)
        self._actualizar_secuencial_status()

    def _actualizar_secuencial_status(self):
        try:
            seq = obtener_siguiente_secuencial()
            self.lbl_secuencial_status.configure(text=f"Secuencial: {seq}")
        except:
            pass

    def _mostrar_panel(self, panel: str):
        for widget in self.contenido.winfo_children():
            widget.destroy()
        for clave, btn in self.botones_nav.items():
            if clave == panel:
                btn.configure(fg_color=COLORS["sidebar_active"], text_color=COLORS["white"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["gray_400"])
        self.panel_actual = panel
        panels = {"dashboard": self._crear_panel_dashboard, "ventas": self._crear_panel_ventas,
                  "inventario": self._crear_panel_inventario, "caja": self._crear_panel_caja,
                  "facturas": self._crear_panel_facturas, "config": self._crear_panel_config}
        if panel in panels:
            panels[panel]()

    def _set_status(self, msg):
        self.lbl_status.configure(text=msg)

    # ==================== DASHBOARD ====================
    def _crear_panel_dashboard(self):
        for i in range(4):
            self.contenido.grid_columnconfigure(i, weight=1)
        self.contenido.grid_rowconfigure(0, weight=0)
        self.contenido.grid_rowconfigure(1, weight=1)

        hoy = datetime.now().strftime("%Y-%m-%d")
        resumen = obtener_resumen_caja(hoy)
        tarjetas = [
            ("\U0001f4b0 Ventas Hoy", f"${resumen['total_ventas']:.2f}", COLORS["primary"], COLORS["primary_light"]),
            ("\U0001f4c4 Facturas", self._contar_facturas_hoy(), COLORS["secondary"], "#ede9fe"),
            ("\U0001f4e6 Productos", self._contar_productos(), COLORS["success"], COLORS["success_light"]),
            ("\U0001f465 Clientes", self._contar_clientes(), COLORS["warning"], COLORS["warning_light"]),
        ]
        for i, (titulo, valor, color, bg) in enumerate(tarjetas):
            card = ctk.CTkFrame(self.contenido, fg_color=COLORS["white"], corner_radius=16, border_width=1, border_color=COLORS["card_border"])
            card.grid(row=0, column=i, padx=12, pady=(15, 10), sticky="nsew")
            ctk.CTkLabel(card, text=titulo, font=ctk.CTkFont(size=13), text_color=COLORS["gray_500"]).pack(anchor="w", padx=20, pady=(18, 0))
            ctk.CTkLabel(card, text=valor, font=ctk.CTkFont(size=28, weight="bold"), text_color=color).pack(anchor="w", padx=20, pady=(4, 18))

        frame_accesos = ctk.CTkFrame(self.contenido, fg_color=COLORS["white"], corner_radius=16, border_width=1, border_color=COLORS["card_border"])
        frame_accesos.grid(row=1, column=0, columnspan=2, padx=12, pady=10, sticky="nsew")
        ctk.CTkLabel(frame_accesos, text="Accesos Rapidos", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["dark"]).pack(anchor="w", padx=20, pady=(15, 10))
        af = ctk.CTkFrame(frame_accesos, fg_color="transparent")
        af.pack(fill="both", expand=True, padx=20, pady=10)
        ctk.CTkButton(af, text="\U0001f6d2 Nueva Venta", fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"], font=ctk.CTkFont(size=14, weight="bold"), height=45, corner_radius=12, command=lambda: self._mostrar_panel("ventas")).pack(side="left", padx=8, fill="x", expand=True)
        ctk.CTkButton(af, text="\U0001f4e6 Agregar Producto", fg_color=COLORS["success"], hover_color="#047857", font=ctk.CTkFont(size=14, weight="bold"), height=45, corner_radius=12, command=lambda: [self._mostrar_panel("inventario"), self.after(100, self._dialogo_nuevo_producto)]).pack(side="left", padx=8, fill="x", expand=True)
        ctk.CTkButton(af, text="\U0001f4e5 Apertura de Caja", fg_color=COLORS["warning"], hover_color="#b45309", font=ctk.CTkFont(size=14, weight="bold"), height=45, corner_radius=12, command=lambda: [self._mostrar_panel("caja"), self.after(100, self._registrar_apertura)]).pack(side="left", padx=8, fill="x", expand=True)

        frame_ultimas = ctk.CTkFrame(self.contenido, fg_color=COLORS["white"], corner_radius=16, border_width=1, border_color=COLORS["card_border"])
        frame_ultimas.grid(row=1, column=2, columnspan=2, padx=12, pady=10, sticky="nsew")
        ctk.CTkLabel(frame_ultimas, text="Ultimas Ventas", font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["dark"]).pack(anchor="w", padx=20, pady=(15, 10))
        self.tabla_dashboard = ttk.Treeview(frame_ultimas, columns=("secuencial", "cliente", "total", "fecha"), show="headings", height=8)
        self.tabla_dashboard.heading("secuencial", text="Nro")
        self.tabla_dashboard.heading("cliente", text="Cliente")
        self.tabla_dashboard.heading("total", text="Total")
        self.tabla_dashboard.heading("fecha", text="Fecha")
        self.tabla_dashboard.column("secuencial", width=100)
        self.tabla_dashboard.column("cliente", width=150)
        self.tabla_dashboard.column("total", width=80)
        self.tabla_dashboard.column("fecha", width=120)
        self.tabla_dashboard.pack(fill="both", expand=True, padx=20, pady=10)
        self._cargar_ultimas_facturas_dashboard()

    def _contar_facturas_hoy(self):
        try:
            hoy = datetime.now().strftime("%Y-%m-%d")
            return str(len(obtener_todas_facturas(hoy, hoy)))
        except:
            return "0"

    def _contar_productos(self):
        try:
            return str(len(obtener_todos_productos()))
        except:
            return "0"

    def _contar_clientes(self):
        try:
            return str(len(obtener_todos_clientes()))
        except:
            return "0"

    def _cargar_ultimas_facturas_dashboard(self):
        for item in self.tabla_dashboard.get_children():
            self.tabla_dashboard.delete(item)
        try:
            for f in obtener_todas_facturas()[:5]:
                self.tabla_dashboard.insert("", "end", values=(f["secuencial"], f.get("cliente_nombre", "Consumidor Final"), f"${f['total']:.2f}", f["fecha"][:10]))
        except:
            pass

    # ==================== PANEL DE VENTAS (POS) ====================
    def _crear_panel_ventas(self):
        self.contenido.grid_columnconfigure(0, weight=2)
        self.contenido.grid_columnconfigure(1, weight=3)
        self.contenido.grid_columnconfigure(2, weight=2)
        self.contenido.grid_rowconfigure(0, weight=1)

        panel_prod = ctk.CTkFrame(self.contenido, fg_color=COLORS["white"], corner_radius=16, border_width=1, border_color=COLORS["card_border"])
        panel_prod.grid(row=0, column=0, padx=(12, 6), pady=12, sticky="nsew")

        ctk.CTkLabel(panel_prod, text="Productos", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["dark"]).pack(anchor="w", padx=15, pady=(12, 8))

        fb = ctk.CTkFrame(panel_prod, fg_color=COLORS["gray_50"], corner_radius=10)
        fb.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(fb, text="\U0001f50d", font=ctk.CTkFont(size=16)).pack(side="left", padx=(10, 0))
        self.buscar_prod_entry = ctk.CTkEntry(fb, placeholder_text="Buscar por codigo o nombre...", fg_color="transparent", border_width=0, font=ctk.CTkFont(size=13))
        self.buscar_prod_entry.pack(side="left", fill="x", expand=True, padx=(8, 10), pady=8)
        self.buscar_prod_entry.bind("<KeyRelease>", self._buscar_productos_callback)

        self.frame_productos = ctk.CTkScrollableFrame(panel_prod, fg_color="transparent")
        self.frame_productos.pack(fill="both", expand=True, padx=10, pady=5)
        self._cargar_tarjetas_productos()

        panel_carrito = ctk.CTkFrame(self.contenido, fg_color=COLORS["white"], corner_radius=16, border_width=1, border_color=COLORS["card_border"])
        panel_carrito.grid(row=0, column=1, padx=6, pady=12, sticky="nsew")

        hc = ctk.CTkFrame(panel_carrito, fg_color="transparent")
        hc.pack(fill="x", padx=15, pady=(12, 8))
        ctk.CTkLabel(hc, text="Carrito de Compra", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["dark"]).pack(side="left")
        self.lbl_items_count = ctk.CTkLabel(hc, text="(0 items)", font=ctk.CTkFont(size=13), text_color=COLORS["gray_500"])
        self.lbl_items_count.pack(side="right")

        self.tabla_carrito = ttk.Treeview(panel_carrito, columns=("codigo", "nombre", "cant", "tipo", "precio", "subtotal"), show="headings", height=14)
        for col, w in [("codigo", 70), ("nombre", 140), ("cant", 50), ("tipo", 80), ("precio", 75), ("subtotal", 85)]:
            self.tabla_carrito.column(col, width=w)
            self.tabla_carrito.heading(col, text=col.capitalize())
        self.tabla_carrito.heading("cant", text="Cant.")
        self.tabla_carrito.heading("tipo", text="Tipo")
        self.tabla_carrito.heading("precio", text="P. Unit.")
        self.tabla_carrito.heading("subtotal", text="Subtotal")
        scrollbar = ttk.Scrollbar(panel_carrito, orient="vertical", command=self.tabla_carrito.yview)
        self.tabla_carrito.configure(yscrollcommand=scrollbar.set)
        self.tabla_carrito.pack(fill="both", expand=True, padx=15, pady=5)
        scrollbar.place(relx=0.97, rely=0.05, relheight=0.65)

        fbc = ctk.CTkFrame(panel_carrito, fg_color="transparent")
        fbc.pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(fbc, text="X Eliminar", fg_color=COLORS["danger"], hover_color="#b91c1c", height=32, corner_radius=8, font=ctk.CTkFont(size=12), command=self._eliminar_del_carrito).pack(side="right")
        ctk.CTkButton(fbc, text="Vaciar Todo", fg_color=COLORS["gray_500"], hover_color=COLORS["gray_600"], height=32, corner_radius=8, font=ctk.CTkFont(size=12), command=self._vaciar_carrito).pack(side="right", padx=5)

        ctk.CTkFrame(panel_carrito, height=2, fg_color=COLORS["gray_200"], corner_radius=1).pack(fill="x", padx=15, pady=10)

        ft = ctk.CTkFrame(panel_carrito, fg_color="transparent")
        ft.pack(fill="x", padx=15, pady=5)
        self.lbl_subtotal = ctk.CTkLabel(ft, text="Subtotal: $0.00", font=ctk.CTkFont(size=13), text_color=COLORS["gray_600"])
        self.lbl_subtotal.pack(anchor="e")
        self.lbl_iva = ctk.CTkLabel(ft, text="IVA 15%: $0.00", font=ctk.CTkFont(size=13), text_color=COLORS["gray_600"])
        self.lbl_iva.pack(anchor="e", pady=(2, 0))
        ctk.CTkFrame(ft, height=1, fg_color=COLORS["gray_300"]).pack(fill="x", pady=8)
        self.lbl_total = ctk.CTkLabel(ft, text="$0.00", font=ctk.CTkFont(size=26, weight="bold"), text_color=COLORS["primary"])
        self.lbl_total.pack(anchor="e")

        panel_cliente = ctk.CTkFrame(self.contenido, fg_color=COLORS["white"], corner_radius=16, border_width=1, border_color=COLORS["card_border"])
        panel_cliente.grid(row=0, column=2, padx=(6, 12), pady=12, sticky="nsew")

        ctk.CTkLabel(panel_cliente, text="Cliente", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["dark"]).pack(anchor="w", padx=15, pady=(12, 8))

        fr = ctk.CTkFrame(panel_cliente, fg_color=COLORS["gray_50"], corner_radius=10)
        fr.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(fr, text="\U0001faaa", font=ctk.CTkFont(size=14)).pack(side="left", padx=(10, 0))
        self.entry_ruc = ctk.CTkEntry(fr, placeholder_text="RUC o Cedula...", fg_color="transparent", border_width=0, font=ctk.CTkFont(size=13))
        self.entry_ruc.pack(side="left", fill="x", expand=True, padx=(8, 10), pady=8)
        self.entry_ruc.bind("<Return>", self._buscar_cliente_ruc)

        self.lbl_cliente_nombre = ctk.CTkLabel(panel_cliente, text="", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS["primary"])
        self.lbl_cliente_nombre.pack(anchor="w", padx=15, pady=(5, 0))

        ctk.CTkLabel(panel_cliente, text="Correo electronico", font=ctk.CTkFont(size=12), text_color=COLORS["gray_500"]).pack(anchor="w", padx=15, pady=(12, 2))
        fe = ctk.CTkFrame(panel_cliente, fg_color=COLORS["gray_50"], corner_radius=10)
        fe.pack(fill="x", padx=15, pady=2)
        ctk.CTkLabel(fe, text="\u2709\ufe0f", font=ctk.CTkFont(size=14)).pack(side="left", padx=(10, 0))
        self.entry_email = ctk.CTkEntry(fe, placeholder_text="cliente@email.com", fg_color="transparent", border_width=0, font=ctk.CTkFont(size=13))
        self.entry_email.pack(side="left", fill="x", expand=True, padx=(8, 10), pady=8)

        ctk.CTkLabel(panel_cliente, text="Observaciones", font=ctk.CTkFont(size=12), text_color=COLORS["gray_500"]).pack(anchor="w", padx=15, pady=(12, 2))
        self.entry_observaciones = ctk.CTkTextbox(panel_cliente, height=60, corner_radius=10, border_width=1, border_color=COLORS["gray_200"])
        self.entry_observaciones.pack(fill="x", padx=15, pady=2)

        ctk.CTkButton(panel_cliente, text="\U0001f4c4 Emitir Factura Electronica", fg_color=COLORS["success"], hover_color="#047857", font=ctk.CTkFont(size=14, weight="bold"), height=45, corner_radius=12, command=self._emitir_factura).pack(fill="x", padx=15, pady=(12, 6))
        ctk.CTkButton(panel_cliente, text="\U0001f4dd Nota de Venta Interna", fg_color=COLORS["warning"], hover_color="#b45309", font=ctk.CTkFont(size=13, weight="bold"), height=40, corner_radius=12, command=self._emitir_nota_venta).pack(fill="x", padx=15, pady=4)
        ctk.CTkButton(panel_cliente, text="\U0001f504 Nueva Venta", fg_color=COLORS["gray_200"], hover_color=COLORS["gray_300"], text_color=COLORS["dark"], font=ctk.CTkFont(size=13), height=36, corner_radius=12, command=self._nueva_venta).pack(fill="x", padx=15, pady=4)

    def _cargar_tarjetas_productos(self, termino=""):
        for w in self.frame_productos.winfo_children():
            w.destroy()
        productos = buscar_productos(termino) if termino else obtener_todos_productos()
        if not productos:
            ctk.CTkLabel(self.frame_productos, text="No hay productos registrados", text_color=COLORS["gray_400"], font=ctk.CTkFont(size=14)).pack(pady=40)
            return
        for p in productos:
            card = ctk.CTkFrame(self.frame_productos, fg_color=COLORS["gray_50"], corner_radius=10, border_width=0)
            card.pack(fill="x", padx=5, pady=3)
            stock_color = COLORS["success"] if p["stock"] > 10 else (COLORS["warning"] if p["stock"] > 0 else COLORS["danger"])
            stock_text = f"Stock: {p['stock']}"
            ctk.CTkLabel(card, text=p["nombre"], font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["dark"], anchor="w").pack(fill="x", padx=12, pady=(8, 0))
            ctk.CTkLabel(card, text=f"{p['codigo']}  |  ${p['precio_base']:.2f}  |  {stock_text}", font=ctk.CTkFont(size=11), text_color=COLORS["gray_500"], anchor="w").pack(fill="x", padx=12, pady=(0, 2))
            if p["stock"] > 0:
                btn = ctk.CTkButton(card, text="+ Agregar", fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"], height=28, corner_radius=8, font=ctk.CTkFont(size=11), command=lambda prod=p: self._agregar_al_carrito(prod))
                btn.pack(anchor="e", padx=8, pady=4)
            else:
                ctk.CTkLabel(card, text="Sin stock", text_color=COLORS["danger"], font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="e", padx=8, pady=4)

    def _buscar_productos_callback(self, event=None):
        self._cargar_tarjetas_productos(self.buscar_prod_entry.get().strip())

    def _agregar_al_carrito(self, producto):
        if producto["stock"] <= 0:
            messagebox.showwarning("Sin Stock", f"{producto['nombre']} no tiene stock")
            return
        ventana = ctk.CTkToplevel(self)
        ventana.title("Agregar al Carrito")
        ventana.geometry("350x320")
        ventana.transient(self)
        ventana.grab_set()
        ctk.CTkLabel(ventana, text=producto["nombre"], font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS["dark"]).pack(pady=(15, 5))
        ctk.CTkLabel(ventana, text=f"Precio base: ${producto['precio_base']:.2f}", font=ctk.CTkFont(size=13), text_color=COLORS["gray_600"]).pack(pady=2)
        tipo_var = ctk.StringVar(value="unidad")
        tamano_var = ctk.StringVar(value="")
        ctk.CTkRadioButton(ventana, text=f"Por Unidad - ${producto['precio_base']:.2f}", variable=tipo_var, value="unidad").pack(pady=5, anchor="w", padx=30)
        ctk.CTkRadioButton(ventana, text="En Caja", variable=tipo_var, value="caja").pack(anchor="w", padx=30)
        precios_caja = obtener_precios_caja(producto["id"])
        if precios_caja:
            for pc in precios_caja:
                ctk.CTkRadioButton(ventana, text=f"  Caja {pc['tamano']} - ${pc['precio_fijo']:.2f}", variable=tamano_var, value=pc["tamano"]).pack(anchor="w", padx=50)
        ctk.CTkLabel(ventana, text="Cantidad:").pack(pady=(10, 2))
        entry_cantidad = ctk.CTkEntry(ventana, width=100)
        entry_cantidad.insert(0, "1")
        entry_cantidad.pack()
        def confirmar():
            tipo = tipo_var.get()
            cantidad = float(entry_cantidad.get() or 1)
            if tipo == "caja" and not tamano_var.get():
                messagebox.showwarning("Atencion", "Seleccione un tamano de caja")
                return
            if tipo == "unidad":
                precio = producto["precio_base"]
                tipo_empaque = "Unidad"
            else:
                pc = obtener_precio_caja(producto["id"], tamano_var.get())
                precio = pc["precio_fijo"] if pc else producto["precio_base"]
                tipo_empaque = f"Caja {tamano_var.get()}"
            subtotal = round(precio * cantidad, 2)
            iva = round(subtotal * (producto["iva"] / 100), 2)
            self.carrito.append({"producto_id": producto["id"], "codigo": producto["codigo"], "nombre": producto["nombre"], "cantidad": cantidad, "tipo_empaque": tipo_empaque, "precio_unitario": precio, "subtotal": subtotal, "iva": iva})
            self._actualizar_carrito()
            self._set_status(f"Agregado: {producto['nombre']} x{cantidad}")
            ventana.destroy()
        ctk.CTkButton(ventana, text="Agregar al Carrito", fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"], font=ctk.CTkFont(size=13, weight="bold"), height=38, corner_radius=10, command=confirmar).pack(pady=15)

    def _actualizar_carrito(self):
        for item in self.tabla_carrito.get_children():
            self.tabla_carrito.delete(item)
        subtotal_total = sum(i["subtotal"] for i in self.carrito)
        iva_total = sum(i["iva"] for i in self.carrito)
        total = subtotal_total + iva_total
        for item in self.carrito:
            self.tabla_carrito.insert("", "end", values=(item["codigo"], item["nombre"], item["cantidad"], item["tipo_empaque"], f"${item['precio_unitario']:.2f}", f"${item['subtotal']:.2f}"))
        self.lbl_subtotal.configure(text=f"Subtotal: ${subtotal_total:.2f}")
        self.lbl_iva.configure(text=f"IVA 15%: ${iva_total:.2f}")
        self.lbl_total.configure(text=f"${total:.2f}")
        self.lbl_items_count.configure(text=f"({len(self.carrito)} items)")

    def _eliminar_del_carrito(self):
        sel = self.tabla_carrito.selection()
        if not sel:
            messagebox.showinfo("Atencion", "Seleccione un item para eliminar")
            return
        self.carrito.pop(self.tabla_carrito.index(sel[0]))
        self._actualizar_carrito()
        self._set_status("Item eliminado del carrito")

    def _vaciar_carrito(self):
        if self.carrito and messagebox.askyesno("Vaciar Carrito", "Eliminar todos los items?"):
            self.carrito = []
            self._actualizar_carrito()
            self._set_status("Carrito vaciado")

    def _buscar_cliente_ruc(self, event=None):
        ident = self.entry_ruc.get().strip()
        if not ident:
            return
        es_valido, tipo, mensaje = validar_identificacion(ident)
        if not es_valido:
            messagebox.showerror("Error", f"Identificacion invalida: {mensaje}")
            return
        cliente = obtener_cliente(ident)
        if cliente:
            self.lbl_cliente_nombre.configure(text=f"{cliente['nombre']}")
            self.entry_email.delete(0, "end")
            self.entry_email.insert(0, cliente.get("correo", ""))
            self._set_status(f"Cliente: {cliente['nombre']}")
        else:
            if messagebox.askyesno("Cliente Nuevo", f"No se encontro cliente con {ident}.\nDesea crearlo?"):
                self._crear_cliente_nuevo(ident)

    def _crear_cliente_nuevo(self, identificacion):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Nuevo Cliente")
        ventana.geometry("380x320")
        ventana.transient(self)
        ventana.grab_set()
        campos = [("Nombre / Razon Social:", "nombre"), ("Direccion:", "direccion"), ("Telefono:", "telefono"), ("Correo:", "correo")]
        entries = {}
        for i, (label, clave) in enumerate(campos):
            ctk.CTkLabel(ventana, text=label, font=ctk.CTkFont(size=12)).grid(row=i, column=0, padx=15, pady=6, sticky="w")
            entry = ctk.CTkEntry(ventana, corner_radius=8)
            entry.grid(row=i, column=1, padx=10, pady=6, sticky="ew")
            entries[clave] = entry
        def guardar():
            nombre = entries["nombre"].get().strip()
            if not nombre:
                messagebox.showerror("Error", "El nombre es obligatorio")
                return
            try:
                crear_cliente(identificacion=identificacion, nombre=nombre, direccion=entries["direccion"].get().strip(), telefono=entries["telefono"].get().strip(), correo=entries["correo"].get().strip())
                self.lbl_cliente_nombre.configure(text=nombre)
                self.entry_email.delete(0, "end")
                self.entry_email.insert(0, entries["correo"].get().strip())
                messagebox.showinfo("Exito", "Cliente creado correctamente")
                self._set_status(f"Cliente creado: {nombre}")
                ventana.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        ctk.CTkButton(ventana, text="Guardar Cliente", fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"], font=ctk.CTkFont(size=13, weight="bold"), height=38, corner_radius=10, command=guardar).grid(row=4, column=0, columnspan=2, pady=15)

    def _emitir_factura(self):
        if not self.carrito:
            messagebox.showwarning("Atencion", "El carrito esta vacio")
            return
        ident = self.entry_ruc.get().strip() or "9999999999999"
        es_valido, tipo, mensaje = validar_identificacion(ident)
        if not es_valido:
            messagebox.showerror("Error", f"Identificacion invalida: {mensaje}")
            return
        cliente = obtener_cliente(ident) or obtener_cliente("9999999999999")
        cliente_id = cliente["id"] if cliente else 1
        obs = self.entry_observaciones.get("1.0", "end").strip()
        try:
            factura = crear_factura(cliente_id=cliente_id, detalles=self.carrito, tipo_comprobante="factura", observaciones=obs)
            xml_content = generar_xml_factura(factura)
            xml_path = guardar_xml(factura["id"], xml_content)
            pdf_path = generar_pdf_factura(factura)
            actualizar_estado_factura(factura["id"], "generado", xml_path, pdf_path)
            registrar_movimiento_caja(tipo="venta", monto=factura["total"], descripcion=f"Factura {factura['secuencial']}", metodo_pago="efectivo")
            self._actualizar_secuencial_status()
            email_cliente = self.entry_email.get().strip()
            if email_cliente and messagebox.askyesno("Enviar por Correo", "Desea enviar la factura por correo al cliente?"):
                try:
                    EmailService().enviar_factura(factura["id"], email_cliente)
                    actualizar_estado_factura(factura["id"], "enviado", xml_path, pdf_path)
                    messagebox.showinfo("Exito", "Factura enviada por correo")
                except Exception as e:
                    messagebox.showerror("Error Email", f"No se pudo enviar: {e}")
            messagebox.showinfo("Factura Emitida", f"Factura Nro {factura['secuencial']}\nTotal: ${factura['total']:.2f}\nClave: {factura['clave_acceso']}")
            self._set_status(f"Factura {factura['secuencial']} emitida - ${factura['total']:.2f}")
            self._nueva_venta()
        except Exception as e:
            messagebox.showerror("Error", f"Error al emitir factura: {e}")

    def _emitir_nota_venta(self):
        if not self.carrito:
            messagebox.showwarning("Atencion", "El carrito esta vacio")
            return
        total = sum(i["subtotal"] + i["iva"] for i in self.carrito)
        registrar_movimiento_caja(tipo="venta", monto=total, descripcion="Nota de venta interna", metodo_pago="efectivo")
        messagebox.showinfo("Nota de Venta", f"Nota de venta interna emitida\nTotal: ${total:.2f}")
        self._set_status(f"Nota de venta emitida - ${total:.2f}")
        self._nueva_venta()

    def _nueva_venta(self):
        self.carrito = []
        self._actualizar_carrito()
        self.entry_ruc.delete(0, "end")
        self.lbl_cliente_nombre.configure(text="")
        self.entry_email.delete(0, "end")
        self.entry_observaciones.delete("1.0", "end")
        self.buscar_prod_entry.delete(0, "end")
        self._cargar_tarjetas_productos()
        self._set_status("Nueva venta iniciada")

    # ==================== PANEL DE INVENTARIO ====================
    def _crear_panel_inventario(self):
        self.contenido.grid_columnconfigure(0, weight=1)
        self.contenido.grid_rowconfigure(0, weight=1)
        frame = ctk.CTkFrame(self.contenido, fg_color=COLORS["white"], corner_radius=16, border_width=1, border_color=COLORS["card_border"])
        frame.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        tabview = ctk.CTkTabview(frame, corner_radius=12)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)
        self._crear_tab_productos(tabview.add("Productos"))
        self._crear_tab_precios_caja(tabview.add("Precios de Caja"))
        self._crear_tab_clientes(tabview.add("Clientes"))

    def _crear_tab_productos(self, parent):
        fb = ctk.CTkFrame(parent, fg_color="transparent")
        fb.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(fb, text="+ Nuevo Producto", fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"], height=34, corner_radius=8, command=self._dialogo_nuevo_producto).pack(side="left", padx=5)
        ctk.CTkButton(fb, text="Editar", fg_color=COLORS["gray_200"], hover_color=COLORS["gray_300"], text_color=COLORS["dark"], height=34, corner_radius=8, command=self._dialogo_editar_producto).pack(side="left", padx=5)
        ctk.CTkButton(fb, text="Ajustar Stock", fg_color=COLORS["warning"], hover_color="#b45309", height=34, corner_radius=8, command=self._dialogo_ajustar_stock).pack(side="left", padx=5)
        self.tabla_inventario = ttk.Treeview(parent, columns=("id", "codigo", "nombre", "precio", "stock", "iva"), show="headings", height=16)
        for col, w in [("id", 40), ("codigo", 80), ("nombre", 200), ("precio", 80), ("stock", 60), ("iva", 60)]:
            self.tabla_inventario.column(col, width=w)
            self.tabla_inventario.heading(col, text=col.capitalize())
        self.tabla_inventario.heading("precio", text="Precio Base")
        self.tabla_inventario.heading("iva", text="IVA %")
        self.tabla_inventario.pack(fill="both", expand=True, padx=5, pady=5)
        self._cargar_tabla_inventario()

    def _cargar_tabla_inventario(self):
        for item in self.tabla_inventario.get_children():
            self.tabla_inventario.delete(item)
        for p in obtener_todos_productos():
            self.tabla_inventario.insert("", "end", values=(p["id"], p["codigo"], p["nombre"], f"${p['precio_base']:.2f}", p["stock"], f"{p['iva']}%"))

    def _dialogo_nuevo_producto(self):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Nuevo Producto")
        ventana.geometry("380x300")
        ventana.grid_columnconfigure(1, weight=1)
        ventana.transient(self)
        ventana.grab_set()
        campos = [("Codigo:", "codigo"), ("Nombre:", "nombre"), ("Precio Base:", "precio"), ("Stock Inicial:", "stock")]
        entries = {}
        for i, (label, clave) in enumerate(campos):
            ctk.CTkLabel(ventana, text=label, font=ctk.CTkFont(size=12)).grid(row=i, column=0, padx=15, pady=6, sticky="w")
            entry = ctk.CTkEntry(ventana, corner_radius=8)
            entry.grid(row=i, column=1, padx=10, pady=6, sticky="ew")
            entries[clave] = entry
        ctk.CTkLabel(ventana, text="IVA %:", font=ctk.CTkFont(size=12)).grid(row=4, column=0, padx=15, pady=6, sticky="w")
        combo_iva = ctk.CTkComboBox(ventana, values=["0", "15"], corner_radius=8)
        combo_iva.set("15")
        combo_iva.grid(row=4, column=1, padx=10, pady=6, sticky="ew")
        def guardar():
            try:
                crear_producto(codigo=entries["codigo"].get().strip(), nombre=entries["nombre"].get().strip(), precio_base=float(entries["precio"].get() or 0), stock=int(entries["stock"].get() or 0), iva=float(combo_iva.get()))
                messagebox.showinfo("Exito", "Producto creado")
                self._cargar_tabla_inventario()
                self._set_status(f"Producto creado: {entries['nombre'].get()}")
                ventana.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        ctk.CTkButton(ventana, text="Guardar", fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"], font=ctk.CTkFont(size=13, weight="bold"), height=38, corner_radius=10, command=guardar).grid(row=5, column=0, columnspan=2, pady=15)

    def _dialogo_editar_producto(self):
        sel = self.tabla_inventario.selection()
        if not sel:
            messagebox.showinfo("Atencion", "Seleccione un producto")
            return
        val = self.tabla_inventario.item(sel[0])["values"]
        pid = val[0]
        ventana = ctk.CTkToplevel(self)
        ventana.title("Editar Producto")
        ventana.geometry("380x300")
        ventana.transient(self)
        ventana.grab_set()
        campos = [("Codigo:", "codigo", val[1]), ("Nombre:", "nombre", val[2]), ("Precio Base:", "precio", val[3].replace("$", "")), ("Stock:", "stock", val[4])]
        entries = {}
        for i, (label, clave, vi) in enumerate(campos):
            ctk.CTkLabel(ventana, text=label, font=ctk.CTkFont(size=12)).grid(row=i, column=0, padx=15, pady=6, sticky="w")
            entry = ctk.CTkEntry(ventana, corner_radius=8)
            entry.insert(0, str(vi))
            entry.grid(row=i, column=1, padx=10, pady=6, sticky="ew")
            entries[clave] = entry
        ctk.CTkLabel(ventana, text="IVA %:", font=ctk.CTkFont(size=12)).grid(row=4, column=0, padx=15, pady=6, sticky="w")
        combo_iva = ctk.CTkComboBox(ventana, values=["0", "15"], corner_radius=8)
        combo_iva.set(str(val[5]).replace("%", ""))
        combo_iva.grid(row=4, column=1, padx=10, pady=6, sticky="ew")
        def guardar():
            try:
                actualizar_producto(pid, codigo=entries["codigo"].get().strip(), nombre=entries["nombre"].get().strip(), precio_base=float(entries["precio"].get() or 0), stock=int(entries["stock"].get() or 0), iva=float(combo_iva.get()))
                messagebox.showinfo("Exito", "Producto actualizado")
                self._cargar_tabla_inventario()
                ventana.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        ctk.CTkButton(ventana, text="Guardar", fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"], font=ctk.CTkFont(size=13, weight="bold"), height=38, corner_radius=10, command=guardar).grid(row=5, column=0, columnspan=2, pady=15)

    def _dialogo_ajustar_stock(self):
        sel = self.tabla_inventario.selection()
        if not sel:
            messagebox.showinfo("Atencion", "Seleccione un producto")
            return
        val = self.tabla_inventario.item(sel[0])["values"]
        ventana = ctk.CTkToplevel(self)
        ventana.title("Ajustar Stock")
        ventana.geometry("320x200")
        ventana.transient(self)
        ventana.grab_set()
        ctk.CTkLabel(ventana, text=f"Producto: {val[2]}", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        ctk.CTkLabel(ventana, text=f"Stock actual: {val[4]}", font=ctk.CTkFont(size=13), text_color=COLORS["gray_600"]).pack()
        ctk.CTkLabel(ventana, text="Cantidad a agregar (+) o retirar (-):").pack(pady=10)
        entry = ctk.CTkEntry(ventana, width=100, corner_radius=8)
        entry.pack()
        def ajustar():
            try:
                ajustar_stock(val[0], int(entry.get()))
                messagebox.showinfo("Exito", "Stock actualizado")
                self._cargar_tabla_inventario()
                ventana.destroy()
            except ValueError:
                messagebox.showerror("Error", "Ingrese un numero valido")
        ctk.CTkButton(ventana, text="Ajustar", fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"], height=36, corner_radius=10, command=ajustar).pack(pady=12)

    def _crear_tab_precios_caja(self, parent):
        fb = ctk.CTkFrame(parent, fg_color="transparent")
        fb.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(fb, text="Producto:").pack(side="left", padx=5)
        self.combo_producto_caja = ctk.CTkComboBox(fb, width=200, corner_radius=8)
        self.combo_producto_caja.pack(side="left", padx=5)
        ctk.CTkButton(fb, text="Cargar", fg_color=COLORS["primary"], height=32, corner_radius=8, command=self._cargar_precios_caja_tabla).pack(side="left", padx=5)
        productos = obtener_todos_productos()
        self.combo_producto_caja.configure(values=[f"{p['codigo']} - {p['nombre']}" for p in productos])
        self.tabla_precios = ttk.Treeview(parent, columns=("id", "tamano", "precio"), show="headings", height=10)
        for col, w in [("id", 40), ("tamano", 150), ("precio", 100)]:
            self.tabla_precios.column(col, width=w)
            self.tabla_precios.heading(col, text=col.capitalize())
        self.tabla_precios.heading("precio", text="Precio Fijo")
        self.tabla_precios.pack(fill="both", expand=True, padx=5, pady=5)
        ff = ctk.CTkFrame(parent, fg_color="transparent")
        ff.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(ff, text="Tamano:").grid(row=0, column=0, padx=5)
        combo_tamano = ctk.CTkComboBox(ff, values=TAMANO_CAJAS, width=120, corner_radius=8)
        combo_tamano.grid(row=0, column=1, padx=5)
        ctk.CTkLabel(ff, text="Precio:").grid(row=0, column=2, padx=5)
        entry_precio = ctk.CTkEntry(ff, width=80, corner_radius=8)
        entry_precio.grid(row=0, column=3, padx=5)
        def agregar():
            sel = self.combo_producto_caja.get()
            if not sel:
                messagebox.showwarning("Atencion", "Seleccione un producto")
                return
            prod = obtener_producto(codigo=sel.split(" - ")[0])
            if not prod:
                return
            try:
                crear_precio_caja(prod["id"], combo_tamano.get(), float(entry_precio.get()))
                messagebox.showinfo("Exito", "Precio de caja guardado")
                self._cargar_precios_caja_tabla()
            except ValueError:
                messagebox.showerror("Error", "Ingrese un precio valido")
        ctk.CTkButton(ff, text="Guardar", fg_color=COLORS["primary"], height=32, corner_radius=8, command=agregar).grid(row=0, column=4, padx=10)

    def _cargar_precios_caja_tabla(self):
        sel = self.combo_producto_caja.get()
        if not sel:
            return
        prod = obtener_producto(codigo=sel.split(" - ")[0])
        if not prod:
            return
        for item in self.tabla_precios.get_children():
            self.tabla_precios.delete(item)
        for p in obtener_precios_caja(prod["id"]):
            self.tabla_precios.insert("", "end", values=(p["id"], p["tamano"], f"${p['precio_fijo']:.2f}"))

    def _crear_tab_clientes(self, parent):
        fb = ctk.CTkFrame(parent, fg_color="transparent")
        fb.pack(fill="x", padx=5, pady=5)
        ctk.CTkButton(fb, text="+ Nuevo Cliente", fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"], height=34, corner_radius=8, command=self._dialogo_nuevo_cliente_inv).pack(side="left", padx=5)
        entry_buscar = ctk.CTkEntry(fb, width=200, placeholder_text="Nombre o RUC...", corner_radius=8)
        entry_buscar.pack(side="left", padx=5)
        ctk.CTkButton(fb, text="Buscar", fg_color=COLORS["gray_200"], text_color=COLORS["dark"], height=34, corner_radius=8, command=lambda: self._cargar_tabla_clientes(entry_buscar.get().strip())).pack(side="left", padx=5)
        self.tabla_clientes = ttk.Treeview(parent, columns=("id", "identificacion", "nombre", "telefono", "correo"), show="headings", height=15)
        for col, w in [("id", 40), ("identificacion", 120), ("nombre", 200), ("telefono", 100), ("correo", 200)]:
            self.tabla_clientes.column(col, width=w)
            self.tabla_clientes.heading(col, text=col.capitalize())
        self.tabla_clientes.heading("identificacion", text="RUC/Cedula")
        self.tabla_clientes.pack(fill="both", expand=True, padx=5, pady=5)
        self._cargar_tabla_clientes()

    def _cargar_tabla_clientes(self, termino=""):
        for item in self.tabla_clientes.get_children():
            self.tabla_clientes.delete(item)
        clientes = buscar_clientes(termino) if termino else obtener_todos_clientes()
        for c in clientes:
            self.tabla_clientes.insert("", "end", values=(c["id"], c["identificacion"], c["nombre"], c.get("telefono", ""), c.get("correo", "")))

    def _dialogo_nuevo_cliente_inv(self):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Nuevo Cliente")
        ventana.geometry("380x320")
        ventana.transient(self)
        ventana.grab_set()
        campos = [("RUC / Cedula:", "identificacion"), ("Nombre:", "nombre"), ("Direccion:", "direccion"), ("Telefono:", "telefono"), ("Correo:", "correo")]
        entries = {}
        for i, (label, clave) in enumerate(campos):
            ctk.CTkLabel(ventana, text=label, font=ctk.CTkFont(size=12)).grid(row=i, column=0, padx=15, pady=6, sticky="w")
            entry = ctk.CTkEntry(ventana, corner_radius=8)
            entry.grid(row=i, column=1, padx=10, pady=6, sticky="ew")
            entries[clave] = entry
        def guardar():
            ident = entries["identificacion"].get().strip()
            nombre = entries["nombre"].get().strip()
            if not ident or not nombre:
                messagebox.showerror("Error", "Identificacion y nombre son obligatorios")
                return
            es_valido, tipo, mensaje = validar_identificacion(ident)
            if not es_valido:
                messagebox.showerror("Error", f"Identificacion invalida: {mensaje}")
                return
            try:
                crear_cliente(identificacion=ident, nombre=nombre, direccion=entries["direccion"].get().strip(), telefono=entries["telefono"].get().strip(), correo=entries["correo"].get().strip())
                messagebox.showinfo("Exito", "Cliente creado")
                self._cargar_tabla_clientes()
                ventana.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        ctk.CTkButton(ventana, text="Guardar", fg_color=COLORS["primary"], hover_color=COLORS["primary_dark"], font=ctk.CTkFont(size=13, weight="bold"), height=38, corner_radius=10, command=guardar).grid(row=5, column=0, columnspan=2, pady=15)

    # ==================== CONTROL DE CAJA ====================
    def _crear_panel_caja(self):
        self.contenido.grid_columnconfigure(0, weight=1)
        self.contenido.grid_rowconfigure(0, weight=1)
        frame = ctk.CTkFrame(self.contenido, fg_color=COLORS["white"], corner_radius=16, border_width=1, border_color=COLORS["card_border"])
        frame.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        ff = ctk.CTkFrame(frame, fg_color="transparent")
        ff.pack(fill="x", padx=15, pady=12)
        ctk.CTkLabel(ff, text="Fecha:", font=ctk.CTkFont(size=13)).pack(side="left", padx=5)
        entry_fecha = ctk.CTkEntry(ff, width=130, corner_radius=8)
        entry_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        entry_fecha.pack(side="left", padx=5)
        ctk.CTkButton(ff, text="Ver Resumen", fg_color=COLORS["primary"], height=34, corner_radius=8, command=lambda: self._mostrar_resumen_caja(entry_fecha.get())).pack(side="left", padx=10)
        fm = ctk.CTkFrame(frame, fg_color="transparent")
        fm.pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(fm, text="\U0001f4e5 Apertura", fg_color=COLORS["success"], hover_color="#047857", height=38, corner_radius=10, command=self._registrar_apertura).pack(side="left", padx=5)
        ctk.CTkButton(fm, text="\U0001f4b8 Registrar Gasto", fg_color=COLORS["danger"], hover_color="#b91c1c", height=38, corner_radius=10, command=self._registrar_gasto).pack(side="left", padx=5)
        ctk.CTkButton(fm, text="\U0001f4ca Cierre de Caja", fg_color=COLORS["warning"], hover_color="#b45309", height=38, corner_radius=10, command=lambda: self._cierre_caja(entry_fecha.get())).pack(side="left", padx=5)
        self.frame_resumen = ctk.CTkFrame(frame, fg_color="transparent")
        self.frame_resumen.pack(fill="both", expand=True, padx=15, pady=10)
        self._mostrar_resumen_caja(datetime.now().strftime("%Y-%m-%d"))

    def _mostrar_resumen_caja(self, fecha):
        for w in self.frame_resumen.winfo_children():
            w.destroy()
        resumen = obtener_resumen_caja(fecha)
        ctk.CTkLabel(self.frame_resumen, text=f"Resumen de Caja - {fecha}", font=ctk.CTkFont(size=18, weight="bold"), text_color=COLORS["dark"]).pack(anchor="w", pady=(5, 15))
        datos = [("\U0001f4b5 Apertura", f"${resumen['apertura']:.2f}", COLORS["gray_600"]), ("\U0001f4b0 Ventas Efectivo", f"${resumen['efectivo']:.2f}", COLORS["success"]), ("\U0001f3e6 Transferencias", f"${resumen['transferencia']:.2f}", COLORS["primary"]), ("\U0001f4c8 Total Ventas", f"${resumen['total_ventas']:.2f}", COLORS["secondary"]), ("\U0001f4b8 Gastos", f"-${resumen['gastos']:.2f}", COLORS["danger"]), ("\U0001f4b3 Total en Caja", f"${resumen['total_caja']:.2f}", COLORS["dark"])]
        for label, valor, color in datos:
            row = ctk.CTkFrame(self.frame_resumen, fg_color=COLORS["gray_50"], corner_radius=10)
            row.pack(fill="x", padx=10, pady=3)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=14), text_color=COLORS["gray_600"], anchor="w").pack(side="left", fill="x", expand=True, padx=15, pady=10)
            ctk.CTkLabel(row, text=valor, font=ctk.CTkFont(size=16, weight="bold"), text_color=color, anchor="e").pack(side="right", padx=15, pady=10)

    def _registrar_apertura(self):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Apertura de Caja")
        ventana.geometry("320x200")
        ventana.transient(self)
        ventana.grab_set()
        ctk.CTkLabel(ventana, text="Monto inicial en caja:", font=ctk.CTkFont(size=14)).pack(pady=15)
        entry = ctk.CTkEntry(ventana, width=150, corner_radius=8)
        entry.pack()
        def guardar():
            try:
                monto = float(entry.get())
                registrar_movimiento_caja("apertura", monto, "Apertura de caja")
                messagebox.showinfo("Exito", f"Apertura registrada: ${monto:.2f}")
                self._mostrar_resumen_caja(datetime.now().strftime("%Y-%m-%d"))
                ventana.destroy()
            except ValueError:
                messagebox.showerror("Error", "Ingrese un monto valido")
        ctk.CTkButton(ventana, text="Registrar", fg_color=COLORS["success"], hover_color="#047857", height=36, corner_radius=10, command=guardar).pack(pady=15)

    def _registrar_gasto(self):
        ventana = ctk.CTkToplevel(self)
        ventana.title("Registrar Gasto")
        ventana.geometry("360x250")
        ventana.transient(self)
        ventana.grab_set()
        ctk.CTkLabel(ventana, text="Monto:", font=ctk.CTkFont(size=12)).pack(pady=(12, 2))
        entry_monto = ctk.CTkEntry(ventana, corner_radius=8)
        entry_monto.pack(padx=20, fill="x")
        ctk.CTkLabel(ventana, text="Descripcion:", font=ctk.CTkFont(size=12)).pack(pady=(8, 2))
        entry_desc = ctk.CTkEntry(ventana, corner_radius=8)
        entry_desc.pack(padx=20, fill="x")
        ctk.CTkLabel(ventana, text="Metodo de pago:", font=ctk.CTkFont(size=12)).pack(pady=(8, 2))
        combo = ctk.CTkComboBox(ventana, values=["efectivo", "transferencia"], corner_radius=8)
        combo.set("efectivo")
        combo.pack(padx=20, fill="x")
        def guardar():
            try:
                registrar_movimiento_caja("gasto", float(entry_monto.get()), entry_desc.get(), combo.get())
                messagebox.showinfo("Exito", "Gasto registrado")
                self._mostrar_resumen_caja(datetime.now().strftime("%Y-%m-%d"))
                ventana.destroy()
            except ValueError:
                messagebox.showerror("Error", "Ingrese un monto valido")
        ctk.CTkButton(ventana, text="Registrar Gasto", fg_color=COLORS["danger"], hover_color="#b91c1c", height=38, corner_radius=10, command=guardar).pack(pady=15)

    def _cierre_caja(self, fecha):
        resumen = obtener_resumen_caja(fecha)
        registrar_movimiento_caja("cierre", resumen["total_caja"], f"Cierre de caja {fecha}")
        messagebox.showinfo("Cierre de Caja", f"Fecha: {fecha}\nApertura: ${resumen['apertura']:.2f}\nVentas: ${resumen['total_ventas']:.2f}\nGastos: ${resumen['gastos']:.2f}\nTotal en Caja: ${resumen['total_caja']:.2f}")

    # ==================== HISTORIAL DE FACTURAS ====================
    def _crear_panel_facturas(self):
        self.contenido.grid_columnconfigure(0, weight=1)
        self.contenido.grid_rowconfigure(0, weight=1)
        frame = ctk.CTkFrame(self.contenido, fg_color=COLORS["white"], corner_radius=16, border_width=1, border_color=COLORS["card_border"])
        frame.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        ff = ctk.CTkFrame(frame, fg_color="transparent")
        ff.pack(fill="x", padx=15, pady=12)
        ctk.CTkLabel(ff, text="Desde:", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
        entry_desde = ctk.CTkEntry(ff, width=120, corner_radius=8)
        entry_desde.insert(0, datetime.now().strftime("%Y-%m-%d"))
        entry_desde.pack(side="left", padx=5)
        ctk.CTkLabel(ff, text="Hasta:", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
        entry_hasta = ctk.CTkEntry(ff, width=120, corner_radius=8)
        entry_hasta.insert(0, datetime.now().strftime("%Y-%m-%d"))
        entry_hasta.pack(side="left", padx=5)
        ctk.CTkButton(ff, text="Filtrar", fg_color=COLORS["primary"], height=32, corner_radius=8, command=lambda: self._cargar_historial_facturas(entry_desde.get(), entry_hasta.get())).pack(side="left", padx=10)
        self.tabla_facturas = ttk.Treeview(frame, columns=("id", "secuencial", "cliente", "fecha", "total", "estado"), show="headings", height=18)
        for col, w in [("id", 40), ("secuencial", 100), ("cliente", 180), ("fecha", 120), ("total", 80), ("estado", 100)]:
            self.tabla_facturas.column(col, width=w)
            self.tabla_facturas.heading(col, text=col.capitalize())
        self.tabla_facturas.heading("estado", text="Estado SRI")
        self.tabla_facturas.pack(fill="both", expand=True, padx=15, pady=5)
        self.tabla_facturas.bind("<Double-1>", self._ver_detalle_factura)
        fb = ctk.CTkFrame(frame, fg_color="transparent")
        fb.pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(fb, text="Ver XML", fg_color=COLORS["primary"], height=34, corner_radius=8, command=self._ver_xml_factura).pack(side="left", padx=5)
        ctk.CTkButton(fb, text="Ver PDF", fg_color=COLORS["secondary"], height=34, corner_radius=8, command=self._ver_pdf_factura).pack(side="left", padx=5)
        ctk.CTkButton(fb, text="Reenviar Email", fg_color=COLORS["success"], height=34, corner_radius=8, command=self._reenviar_email).pack(side="left", padx=5)
        self._cargar_historial_facturas()

    def _cargar_historial_facturas(self, fd=None, fh=None):
        for item in self.tabla_facturas.get_children():
            self.tabla_facturas.delete(item)
        for f in obtener_todas_facturas(fd, fh):
            self.tabla_facturas.insert("", "end", values=(f["id"], f["secuencial"], f.get("cliente_nombre", "Consumidor Final"), f["fecha"], f"${f['total']:.2f}", f["estado_sri"]))

    def _ver_detalle_factura(self, event=None):
        sel = self.tabla_facturas.selection()
        if not sel:
            return
        fid = self.tabla_facturas.item(sel[0])["values"][0]
        factura = obtener_factura(fid)
        if not factura:
            return
        ventana = ctk.CTkToplevel(self)
        ventana.title(f"Factura {factura['secuencial']}")
        ventana.geometry("600x480")
        ventana.transient(self)
        cliente = factura.get("cliente", {})
        texto = f"Factura Nro: {factura['secuencial']}\nFecha: {factura['fecha']}\nCliente: {cliente.get('nombre', 'N/A')}\nIdentificacion: {cliente.get('identificacion', 'N/A')}\nClave de Acceso: {factura['clave_acceso']}\nEstado: {factura['estado_sri']}\n\nDETALLES:\n"
        for d in factura.get("detalles", []):
            texto += f"  {d['producto_nombre']} x{d['cantidad']} ({d['tipo_empaque']}) - ${d['subtotal']:.2f}\n"
        texto += f"\nSubtotal sin IVA: ${factura['subtotal_sin_iva']:.2f}\nSubtotal IVA 0%: ${factura['subtotal_iva_0']:.2f}\nSubtotal IVA 15%: ${factura['subtotal_iva_15']:.2f}\nIVA: ${factura['iva']:.2f}\nTOTAL: ${factura['total']:.2f}"
        if factura.get("observaciones"):
            texto += f"\n\nObservaciones: {factura['observaciones']}"
        txt = ctk.CTkTextbox(ventana, width=580, height=430, corner_radius=10)
        txt.pack(padx=10, pady=10)
        txt.insert("1.0", texto)
        txt.configure(state="disabled")

    def _ver_xml_factura(self):
        sel = self.tabla_facturas.selection()
        if not sel:
            messagebox.showinfo("Atencion", "Seleccione una factura")
            return
        factura = obtener_factura(self.tabla_facturas.item(sel[0])["values"][0])
        if factura and factura.get("xml_path"):
            import subprocess, platform
            cmd = ["notepad", factura["xml_path"]] if platform.system() == "Windows" else ["xdg-open", factura["xml_path"]]
            subprocess.Popen(cmd)
        else:
            messagebox.showinfo("Info", "No se encontro el XML")

    def _ver_pdf_factura(self):
        sel = self.tabla_facturas.selection()
        if not sel:
            messagebox.showinfo("Atencion", "Seleccione una factura")
            return
        factura = obtener_factura(self.tabla_facturas.item(sel[0])["values"][0])
        if factura and factura.get("pdf_path"):
            import subprocess, platform
            cmd = ["start", factura["pdf_path"]] if platform.system() == "Windows" else ["xdg-open", factura["pdf_path"]]
            subprocess.Popen(cmd, shell=True) if platform.system() == "Windows" else subprocess.Popen(cmd)
        else:
            messagebox.showinfo("Info", "No se encontro el PDF")

    def _reenviar_email(self):
        sel = self.tabla_facturas.selection()
        if not sel:
            messagebox.showinfo("Atencion", "Seleccione una factura")
            return
        factura = obtener_factura(self.tabla_facturas.item(sel[0])["values"][0])
        email = factura.get("cliente", {}).get("correo", "") if factura else ""
        if not email:
            messagebox.showinfo("Atencion", "El cliente no tiene correo registrado")
            return
        if messagebox.askyesno("Reenviar", f"Reenviar factura a {email}?"):
            try:
                EmailService().enviar_factura(factura["id"], email)
                messagebox.showinfo("Exito", "Factura reenviada")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ==================== CONFIGURACION ====================
    def _crear_panel_config(self):
        self.contenido.grid_columnconfigure(0, weight=1)
        self.contenido.grid_rowconfigure(0, weight=1)
        frame = ctk.CTkFrame(self.contenido, fg_color=COLORS["white"], corner_radius=16, border_width=1, border_color=COLORS["card_border"])
        frame.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        ctk.CTkLabel(frame, text="Configuracion del Sistema", font=ctk.CTkFont(size=20, weight="bold"), text_color=COLORS["dark"]).pack(pady=15)
        sf = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        sf.pack(fill="both", expand=True, padx=20, pady=10)
        ctk.CTkLabel(sf, text="Datos del Negocio", font=ctk.CTkFont(size=15, weight="bold"), text_color=COLORS["primary"]).pack(anchor="w", pady=(5, 10))
        config = obtener_toda_config()
        campos_negocio = [("Razon Social:", "razon_social"), ("Nombre Comercial:", "nombre_comercial"), ("RUC:", "ruc"), ("Direccion Matriz:", "direccion_matriz"), ("Nro. Contribuyente Especial:", "contribuyente_especial")]
        self.entries_config = {}
        for label, clave in campos_negocio:
            row = ctk.CTkFrame(sf, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, width=220, font=ctk.CTkFont(size=12), anchor="w").pack(side="left", padx=5)
            entry = ctk.CTkEntry(row, corner_radius=8)
            entry.insert(0, config.get(clave, ""))
            entry.pack(side="left", padx=5, fill="x", expand=True)
            self.entries_config[clave] = entry
        row_amb = ctk.CTkFrame(sf, fg_color="transparent")
        row_amb.pack(fill="x", pady=8)
        ctk.CTkLabel(row_amb, text="Ambiente:", width=220, font=ctk.CTkFont(size=12), anchor="w").pack(side="left", padx=5)
        self.combo_ambiente = ctk.CTkComboBox(row_amb, values=["1 - Pruebas", "2 - Produccion"], width=180, corner_radius=8)
        self.combo_ambiente.set(f"{config.get('ambiente', '1')} - {'Pruebas' if config.get('ambiente') == '1' else 'Produccion'}")
        self.combo_ambiente.pack(side="left", padx=5)
        ctk.CTkLabel(sf, text="Configuracion de Email (SMTP)", font=ctk.CTkFont(size=15, weight="bold"), text_color=COLORS["primary"]).pack(anchor="w", pady=(15, 10))
        campos_email = [("Correo Emisor:", "email_emisor"), ("Contraseña:", "email_password"), ("Servidor SMTP:", "email_smtp"), ("Puerto:", "email_puerto")]
        for label, clave in campos_email:
            row = ctk.CTkFrame(sf, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, width=220, font=ctk.CTkFont(size=12), anchor="w").pack(side="left", padx=5)
            entry = ctk.CTkEntry(row, corner_radius=8, show=clave == "email_password")
            entry.insert(0, config.get(clave, ""))
            entry.pack(side="left", padx=5, fill="x", expand=True)
            self.entries_config[clave] = entry
        nota = ctk.CTkTextbox(sf, height=80, corner_radius=10)
        nota.pack(fill="x", pady=15)
        nota.insert("1.0", "NOTA: Para firma digital XAdES-BES y envio al SRI se requiere:\n1. Certificado digital (.p12) emitido por entidad autorizada\n2. Instalar: pip install signxml zeep\n3. Configurar ruta del certificado en sri_xml.py")
        nota.configure(state="disabled")
        ctk.CTkButton(frame, text="Guardar Configuracion", fg_color=COLORS["success"], hover_color="#047857", font=ctk.CTkFont(size=14, weight="bold"), height=45, corner_radius=12, command=self._guardar_config).pack(pady=15)

    def _guardar_config(self):
        try:
            for clave, entry in self.entries_config.items():
                guardar_config(clave, entry.get().strip())
            guardar_config("ambiente", self.combo_ambiente.get().split(" - ")[0])
            messagebox.showinfo("Exito", "Configuracion guardada correctamente")
            self._set_status("Configuracion actualizada")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {e}")
