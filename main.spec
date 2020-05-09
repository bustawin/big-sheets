# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['bigsheets/main.py'],
    pathex=['/Users/bustawin/Documents/repos/bigsheet'],
    binaries=[],
    datas=[('bigsheets/adapters/ui/gui/templates', 'adapters/ui/gui/templates')],
    hiddenimports=[
        # Fixes https://github.com/pypa/setuptools/issues/1963#issuecomment-610829709
        "pkg_resources.py2_warn"
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False)
app = BUNDLE(
    exe,
    name='Big Sheets.app',
    icon='assets/app.icns',
    bundle_identifier="com.bustawin.big-sheets",
    info_plist={
        'NSPrincipalClass': 'NSApplication',  # Required for HighDPI monitors
        # Handles opening files. Problem is:
        # https://github.com/pyinstaller/pyinstaller/issues/1309
        'UTExportedTypeDeclarations': [
            {
                'UTTypeIdentifier': 'com.bustawin.big-sheets-workspace',
                'UTTypeReferenceURL': 'http://bustawin.com',
                'UTTypeDescription': 'Big Sheets Workspace file',
                'CFBundleTypeIconFiles': ['assets/app.png'],
                'UTTypeTagSpecification': {
                    'public.filename-extension': ['bsw'],
                    'public.mime-type': 'application/big-sheets-workspace'
                },
                'UTTypeConformsTo': 'public.data',
            }
        ],
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Big Sheets Workspace file',
                'CFBundleTypeRole': 'Editor',
                'CFBundleTypeIconFiles': ['assets/app.png'],
                'LSItemContentTypes': ['com.bustawin.big-sheets-workspace'],
                'LSHandlerRank': 'Owner',
            },
        ],
        'LSEnvironment': {
            'LANG': 'en_US.UTF-8',
            'LC_CTYPE': 'en_US.UTF-8'
        }
    }
)
