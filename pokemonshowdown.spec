# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['tictactoe.py'],
    pathex=[],
    binaries=[],
    datas=[('pause.mp3', '.'), ('unpause.mp3', '.'), ('cash_sound.mp3', '.')],
    hiddenimports=['pynput.keyboard', 'win32gui', 'win32con', 'win32api', 'win32process'],
    hookspath=['hooks'],
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
    name='pokemonshowdown',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['showdown_icon.ico'],
)
