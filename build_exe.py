#!/usr/bin/env python3
"""
桌面寵物Windows可執行文件打包腳本
使用PyInstaller創建獨立的exe文件
"""
import os
import sys
import subprocess
import shutil

def check_pyinstaller():
    """檢查PyInstaller是否已安裝"""
    try:
        import PyInstaller
        print(f"✅ PyInstaller已安裝，版本: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("❌ PyInstaller未安裝")
        print("請運行: pip install pyinstaller")
        return False

def create_spec_file():
    """創建PyInstaller規格文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('README.md', '.'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui', 
        'PySide6.QtWidgets',
        'pygame',
        'loguru',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DesktopPet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不顯示控制台視窗
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/rest.gif',  # 使用rest.gif作為圖標
)
'''
    
    with open('desktop_pet.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ 創建PyInstaller規格文件: desktop_pet.spec")

def build_executable():
    """構建可執行文件"""
    print("🔨 開始構建Windows可執行文件...")
    
    # 運行PyInstaller
    cmd = [
        'python', '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        'desktop_pet.spec'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 構建成功！")
            print("📁 可執行文件位置: dist/DesktopPet.exe")
            
            # 檢查文件是否存在
            exe_path = "dist/DesktopPet.exe"
            if os.path.exists(exe_path):
                size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
                print(f"📊 文件大小: {size:.1f} MB")
            
            return True
        else:
            print("❌ 構建失敗！")
            print("錯誤信息:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 構建過程出錯: {e}")
        return False

def create_installer_info():
    """創建安裝說明文件"""
    info_content = """# 桌面寵物 - Windows可執行文件

## 📦 文件說明
- `DesktopPet.exe`: 桌面寵物主程序
- `assets/`: 動畫和音效資源文件夾

## 🚀 使用方法
1. 雙擊 `DesktopPet.exe` 啟動程序
2. 寵物會出現在桌面上
3. 左鍵拖拽移動寵物位置
4. 右鍵點擊顯示功能菜單
5. 系統托盤圖標提供更多選項

## ⚙️ 命令行參數
在命令提示符中運行：
- `DesktopPet.exe --debug`: 啟用調試模式
- `DesktopPet.exe --hide`: 啟動時隱藏寵物
- `DesktopPet.exe --start-reminders`: 啟動時開啟定時提醒

## 🔧 功能特性
- 🖼️ 桌面常駐透明視窗
- 🐕 多狀態動畫播放
- 🖱️ 拖拽與點擊互動
- 🔔 智能定時提醒
- 🔊 音效回饋
- 🌙 系統托盤集成

## 📝 系統需求
- Windows 10/11
- 無需額外安裝Python或其他依賴

## 🆘 問題排除
如果程序無法啟動：
1. 確保assets文件夾與exe文件在同一目錄
2. 檢查Windows防火牆設置
3. 以管理員身份運行
4. 查看logs文件夾中的日誌文件

版本: v1.0.0
"""
    
    with open('dist/README_Windows.txt', 'w', encoding='utf-8') as f:
        f.write(info_content)
    
    print("✅ 創建安裝說明: dist/README_Windows.txt")

def main():
    """主函數"""
    print("🐾 桌面寵物Windows打包工具")
    print("=" * 40)
    
    # 檢查PyInstaller
    if not check_pyinstaller():
        return 1
    
    # 創建規格文件
    create_spec_file()
    
    # 構建可執行文件
    if build_executable():
        # 創建說明文件
        create_installer_info()
        
        print("\n🎉 打包完成！")
        print("📁 輸出目錄: dist/")
        print("🚀 可執行文件: dist/DesktopPet.exe")
        print("\n💡 提示:")
        print("   - 將整個dist文件夾分發給用戶")
        print("   - 或者創建安裝包包含dist文件夾內容")
        
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main()) 