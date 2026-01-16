# -*- mode: python ; coding: utf-8 -*-


import os
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules, collect_data_files, collect_all

# Collect ALL files for supabase and its actual dependencies (supabase 2.x)
supabase_datas, supabase_binaries, supabase_hiddenimports = collect_all('supabase')
httpx_datas, httpx_binaries, httpx_hiddenimports = collect_all('httpx')
httpcore_datas, httpcore_binaries, httpcore_hiddenimports = collect_all('httpcore')
postgrest_datas, postgrest_binaries, postgrest_hiddenimports = collect_all('postgrest')

# Try to collect supabase-auth (may be named differently)
try:
    auth_datas, auth_binaries, auth_hiddenimports = collect_all('supabase_auth')
except:
    auth_datas, auth_binaries, auth_hiddenimports = [], [], []

try:
    gotrue_datas, gotrue_binaries, gotrue_hiddenimports = collect_all('gotrue')
except:
    gotrue_datas, gotrue_binaries, gotrue_hiddenimports = [], [], []

a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath('.')],
    binaries=[
        ('wajik-anime-api.exe', '.'),
    ] + collect_dynamic_libs('pillow_heif') + supabase_binaries + httpx_binaries + httpcore_binaries + postgrest_binaries + auth_binaries + gotrue_binaries,
    datas=[
        ('app/styles/*.qss', 'app/styles'),
        ('app/styles', 'app/styles'),
    ] + collect_data_files('certifi') + supabase_datas + httpx_datas + httpcore_datas + postgrest_datas + auth_datas + gotrue_datas,
    hiddenimports=[
        # Supabase 2.x dan dependencies
        'supabase',
        'supabase.client',
        'supabase._sync',
        'supabase._sync.client',
        'supabase._async',
        'supabase._async.client',
        'supabase_auth',
        'gotrue',
        'postgrest',
        'realtime',
        'storage3',
        'supafunc',
        # HTTP client
        'httpx',
        'httpx._transports',
        'httpx._transports.default',
        'httpcore',
        'h11',
        'anyio',
        'anyio._backends',
        'anyio._backends._asyncio',
        'sniffio',
        'socksio',
        # Pydantic
        'pydantic',
        'pydantic.fields',
        'pydantic_core',
        # Yarl for URL handling
        'yarl',
        'multidict',
        'idna',
        # PySide6 Qt Framework
        'PySide6.QtCore',
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        # Threading
        'threading',
        'queue',
        'PySide6.QtCore.Signal',
        'PySide6.QtCore.Slot',
        'PySide6.QtCore.QThread',
        'PySide6.QtCore.QTimer',
        # Image processing
        'PIL.Image',
        'PIL.ImageFile',
        'PIL.ImageDraw',
        'pillow_heif',
        # Network & SSL
        'ssl',
        'certifi',
        'urllib3.util.ssl_',
        'hashlib',
        'shutil',
    ] + supabase_hiddenimports + httpx_hiddenimports + httpcore_hiddenimports + postgrest_hiddenimports + auth_hiddenimports + gotrue_hiddenimports + collect_submodules('pydantic') + collect_submodules('anyio') + collect_submodules('h11') + collect_submodules('yarl') + collect_submodules('multidict') + collect_submodules('pillow_heif') + collect_submodules('requests') + collect_submodules('urllib3'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch',
        'torchvision',
        'torchaudio',
        'matplotlib',
        'numpy',
        'pandas',
        'pygame',
        'scipy',
        'sklearn',
        'tensorflow',
        'cv2',
        'OpenCV',
        'notebook',
        'jupyter',
        'IPython',
        'setuptools',
        'pip',
        'wheel',
        'test',
        'tests',
        # 'testing',  # REMOVED - pyparsing.testing needs this
        # 'unittest', # REMOVED - pyparsing.testing needs unittest
        'pytest',
        'tkinter',
    ],
    noarchive=False,
    optimize=2,  # Optimize bytecode
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # --onedir mode for installer
    name='GalaxyStream',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # Windows doesn't have strip command
    upx=True,
    upx_exclude=[],
    console=False,  # Enable console for debugging - set False for production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='galaxystream_icon_fix.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GalaxyStream',
)
