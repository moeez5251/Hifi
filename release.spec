# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['release.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets/Logo.png', 'assets'),
        ('assets/Banner.png', 'assets'),
        ('assets/svgs/home.svg', 'assets/svgs'),
        ('assets/svgs/search.svg', 'assets/svgs'),
        ('assets/svgs/recognize.svg', 'assets/svgs'),
        ('assets/svgs/Artist.svg', 'assets/svgs'),
        ('assets/svgs/replay.svg', 'assets/svgs'),
        ('assets/svgs/playlist.svg', 'assets/svgs'),
        ('assets/svgs/pop.svg', 'assets/svgs'),
        ('assets/svgs/rock.svg', 'assets/svgs'),
        ('assets/svgs/about.svg', 'assets/svgs'),
        ('assets/svgs/more.svg', 'assets/svgs'),
        ('assets/svgs/play.svg', 'assets/svgs'),
        ('assets/svgs/pause.svg', 'assets/svgs'),
        ('assets/svgs/maximize.svg', 'assets/svgs'),
        ('assets/svgs/minimize.svg', 'assets/svgs'),
        ('assets/svgs/close.svg', 'assets/svgs'),
        ('assets/fonts/Poppins-Regular.ttf', 'assets/fonts'),
        ('assets/Moeez.png', 'assets'),
        ('assets/Taha.png', 'assets'),
        ('assets/Haseeb.png', 'assets'),
        ('assets/Fasee.png', 'assets'),
        ('style.css', '.'),
        ('.env', '.'),
        ('components/gradient_label.py', 'components'),
        ('components/recognizer.py', 'components'),
        ('components/clickableimage.py', 'components'),
        ('components/playbar.py', 'components')
    ],
    hiddenimports=[
        'PySide6.QtWidgets',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtSvg',
        'requests',
        'uuid',
        'io',
        'scipy',
        'numpy',
        'dotenv',
        'librosa',
        'pydub'
    ],
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib'],
    noarchive=False,
    optimize=0
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MusicApp',
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
    icon='assets\\Logo.ico'
)