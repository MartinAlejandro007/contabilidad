#!/usr/bin/env python3
"""
main.py - Entry point for the Accounting and Electronic Invoicing System.

Usage:
    python main.py

Requirements:
    pip install -r requirements.txt

This system provides:
- Point of Sale (POS) with product search and box price management
- Electronic invoicing compliant with SRI Ecuador (XML + PDF/RIDE)
- Daily cash control (open, sales, expenses, close)
- Inventory and customer management
- Invoice email sending
"""

import sys
import os

# Asegurar que el directorio del script esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def verificar_dependencias():
    """Verifica que las dependencias estén instaladas."""
    dependencias = [
        ("customtkinter", "customtkinter"),
        ("reportlab", "reportlab"),
        ("lxml", "lxml"),
    ]

    faltantes = []
    for modulo, pip_name in dependencias:
        try:
            __import__(modulo)
        except ImportError:
            faltantes.append(pip_name)

    if faltantes:
        print("Faltan dependencias. Instálelas con:")
        print(f"  pip install {' '.join(faltantes)}")
        print("\nO ejecute:")
        print("  pip install -r requirements.txt")
        return False
    return True


def main():
    """Función principal de la aplicación."""
    if not verificar_dependencias():
        sys.exit(1)

    # Inicializar base de datos
    from database import init_db
    init_db()

    # Iniciar interfaz gráfica
    from gui import App
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
