# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# Prepare datas - include data directory if it exists
datas = []
if os.path.exists('data'):
    datas.append(('data', 'data'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'lxml',
        'lxml.etree',
        'lxml._elementpath',
        'reportlab',
        'reportlab.lib',
        'reportlab.lib.colors',
        'reportlab.lib.pagesizes',
        'reportlab.lib.styles',
        'reportlab.lib.units',
        'reportlab.lib.enums',
        'reportlab.platypus',
        'reportlab.platypus.tables',
        'reportlab.platypus.paragraph',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'customtkinter',
        'customtkinter.windows',
        'customtkinter.windows.ctk_tk',
        'customtkinter.windows.ctk_input_dialog',
        'customtkinter.windows.widgets',
        'customtkinter.windows.widgets.core_widget_classes',
        'customtkinter.windows.widgets.core_rendering',
        'tkinter',
        'tkinter.messagebox',
        'tkinter.ttk',
        'smtplib',
        'email.mime.multipart',
        'email.mime.text',
        'email.mime.base',
        'email.encoders',
        'xml.etree.ElementTree',
        'xml.dom.minidom',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'scipy', 'pandas', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Contabilidad',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
