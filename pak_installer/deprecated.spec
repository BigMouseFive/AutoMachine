# -*- mode: python -*-

block_cipher = None


a = Analysis(['..\\deprecated.py'],
             pathex=['../DataManager.py', '../SpiderProcess.py', '../OperateProcess.py', 'D:\\Utils\\AutoMachine\\VisualStudio2013WorkPlatform\\automachine\\pak_installer'],
             binaries=[],
             datas=[],
             hiddenimports=[],
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
          [],
          exclude_binaries=True,
          name='deprecated',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True , icon='lemon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='deprecated')
