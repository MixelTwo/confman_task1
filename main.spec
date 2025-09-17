# -*- mode: python ; coding: utf-8 -*-
import sys
from os import path
site_packages = next(p for p in sys.path if 'site-packages' in p)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[("data", "data"), (path.join(site_packages, "dateparser", "data"), path.join("dateparser", "data"))],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='emulator',
    icon='data/favicon.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
