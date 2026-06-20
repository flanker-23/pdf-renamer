# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for PDF Renamer
# This spec bundles pdfplumber + pdfminer data files reliably.

from PyInstaller.utils.hooks import collect_all, collect_data_files

# Collect everything from pdfplumber and pdfminer (data files included)
plumber_d, plumber_b, plumber_h = collect_all('pdfplumber')
miner_d,   miner_b,   miner_h   = collect_all('pdfminer')

a = Analysis(
    ['pdf_renamer_gui.py'],
    pathex=[],
    binaries=plumber_b + miner_b,
    datas=plumber_d + miner_d,
    hiddenimports=plumber_h + miner_h + [
        'PyPDF2',
        'pdfplumber',
        'pdfminer',
        'pdfminer.high_level',
        'pdfminer.layout',
        'pdfminer.pdfparser',
        'pdfminer.pdfdocument',
        'pdfminer.pdfpage',
        'pdfminer.pdfinterp',
        'pdfminer.converter',
        'pdfminer.cmapdb',
        'pdfminer.utils',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'PIL'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PDF Renamer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,        # no terminal window — pure GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
