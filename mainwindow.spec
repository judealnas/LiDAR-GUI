# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['mainwindow.py'],
             pathex=['/home/jude/Projects/LiDAR-GUI',\
                '/home/jude/Projects/LiDAR-GUI/TcpControl',\
                '/home/jude/Projects/LiDAR-GUI/LidarPlot'
             ],
             binaries=[],
             datas=[('/home/jude/Projects/LiDAR-GUI/TcpControl/Ui_TcpControl.ui','.')],
             hiddenimports=['/home/jude/Projects/LiDAR-GUI/TcpControl/LedIndicatorWidget'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='mainwindow',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False )
