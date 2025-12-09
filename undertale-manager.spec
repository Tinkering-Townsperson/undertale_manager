# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for UNDERTALE Manager.

Usage:
    poetry run pyinstaller undertale-manager.spec

This will create a standalone executable in the dist/ folder.
"""

import sys
from pathlib import Path

# Get the project root directory
project_root = Path.cwd()
src_dir = project_root / 'src'

a = Analysis(
    [str(src_dir / 'undertale_manager' / '__main__.py')],
    pathex=[str(src_dir)],
    binaries=[],
    datas=[
        # Include the CSS file for Textual TUI
        (str(src_dir / 'undertale_manager' / 'undertale_manager.tcss'), 'undertale_manager'),
        # Include the ids.py module (contains room data)
        (str(src_dir / 'undertale_manager' / 'ids.py'), 'undertale_manager'),
    ],
    hiddenimports=[
        'undertale_manager',
        'undertale_manager.ids',
        'undertale_manager.tui',
        'textual',
        'textual.app',
        'textual.widgets',
        'textual.containers',
        'textual.screen',
    ],
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
    name='undertale-manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console window for TUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Uncomment and set icon if you have one:
    # icon='icon.ico',
)

# Alternative: Create a folder distribution instead of a single file
# Uncomment the section below and comment out the EXE section above
# to create a folder distribution (faster startup, larger size)

"""
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='undertale-manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='undertale-manager',
)
"""
