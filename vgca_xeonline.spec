# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import (
    collect_submodules,
    collect_data_files,
    collect_dynamic_libs,
)

block_cipher = None

hiddenimports = []

# PyHanko
hiddenimports += collect_submodules("pyhanko")
hiddenimports += collect_submodules("pyhanko_certvalidator")

# PKCS11
hiddenimports += collect_submodules("pkcs11")

# PyMuPDF
hiddenimports += collect_submodules("fitz")

# Pillow
hiddenimports += collect_submodules("PIL")

datas = []

# Thu toàn bộ data của các package
datas += collect_data_files("pyhanko")
datas += collect_data_files("pyhanko_certvalidator")
datas += collect_data_files("fitz")
datas += collect_data_files("PIL")

# Icon ngoài thư mục gốc
datas += [
    ("*.png", "."),
]

binaries = []

# Thu toàn bộ thư viện .so của các package
binaries += collect_dynamic_libs("fitz")
binaries += collect_dynamic_libs("pkcs11")

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="vgca_xeonline",
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="vgca_xeonline",
)