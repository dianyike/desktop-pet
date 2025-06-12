#!/usr/bin/env python3
"""
桌面寵物Windows可執行文件打包腳本
使用PyInstaller創建獨立的exe文件
"""
import os
import sys
import subprocess
import shutil
import locale

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
        ('config.json', '.'),
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
    icon='assets/idle.gif',  # 使用idle.gif作為圖標
)
'''
    
    with open('desktop_pet.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ 創建PyInstaller規格文件: desktop_pet.spec")

def build_executable():
    """構建可執行文件"""
    print("🔨 開始構建Windows可執行文件...")
    
    # 設置環境變量，強制使用UTF-8編碼
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    # 運行PyInstaller
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        'desktop_pet.spec'
    ]
    
    try:
        # 獲取系統編碼
        system_encoding = locale.getpreferredencoding()
        print(f"🔤 系統編碼: {system_encoding}")
        
        # 使用系統編碼運行subprocess
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True,
            encoding=system_encoding,
            errors='replace',  # 替換無法解碼的字符
            env=env
        )
        
        if result.returncode == 0:
            print("✅ 構建成功！")
            print("📁 可執行文件位置: dist/DesktopPet.exe")
            
            # 檢查文件是否存在
            exe_path = "dist/DesktopPet.exe"
            if os.path.exists(exe_path):
                size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
                print(f"📊 文件大小: {size:.1f} MB")
            
            # 顯示構建輸出（如果有警告）
            if result.stderr.strip():
                print("⚠️ 構建警告:")
                print(result.stderr[:1000] + "..." if len(result.stderr) > 1000 else result.stderr)
            
            return True
        else:
            print("❌ 構建失敗！")
            print(f"❌ 錯誤代碼: {result.returncode}")
            
            if result.stdout:
                print("📝 標準輸出:")
                print(result.stdout[:2000] + "..." if len(result.stdout) > 2000 else result.stdout)
                
            if result.stderr:
                print("❌ 錯誤輸出:")
                print(result.stderr[:2000] + "..." if len(result.stderr) > 2000 else result.stderr)
            
            return False
            
    except UnicodeDecodeError as e:
        print(f"❌ 編碼錯誤: {e}")
        print("🔧 嘗試使用不同的編碼...")
        
        # 嘗試使用GB2312編碼（Windows中文系統）
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                encoding='gb2312',
                errors='replace',
                env=env
            )
            
            if result.returncode == 0:
                print("✅ 使用GB2312編碼構建成功！")
                return True
            else:
                print("❌ 即使使用GB2312編碼也構建失敗")
                return False
                
        except Exception as e2:
            print(f"❌ GB2312編碼也失敗: {e2}")
            return False
            
    except Exception as e:
        print(f"❌ 構建過程出錯: {e}")
        print("🔧 嘗試手動運行以下命令:")
        print(f"   {' '.join(cmd)}")
        return False

def copy_required_files():
    """複製必要的文件到dist目錄"""
    print("📁 複製必要文件...")
    
    # 確保dist目錄存在
    if not os.path.exists('dist'):
        os.makedirs('dist')
    
    # 複製配置文件
    if os.path.exists('config.json'):
        shutil.copy2('config.json', 'dist/')
        print("✅ 複製 config.json")
    
    # 複製assets目錄（如果PyInstaller沒有正確處理）
    if os.path.exists('assets') and not os.path.exists('dist/assets'):
        shutil.copytree('assets', 'dist/assets')
        print("✅ 複製 assets 目錄")
    
    # 創建logs目錄
    logs_dir = 'dist/logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        print("✅ 創建 logs 目錄")

def create_installer_info():
    """創建安裝說明文件"""
    info_content = """# 桌面寵物 - Windows可執行文件

## 📦 文件說明
- `DesktopPet.exe`: 桌面寵物主程序
- `assets/`: 動畫和音效資源文件夾
- `config.json`: 配置文件
- `logs/`: 日誌文件夾

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

版本: v1.1.0
"""
    
    os.makedirs('dist', exist_ok=True)
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
    
    # 檢查必要文件
    required_files = ['main.py', 'assets', 'core', 'ui', 'utils']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ 缺少必要文件: {missing_files}")
        return 1
    
    # 創建規格文件
    create_spec_file()
    
    # 構建可執行文件
    if build_executable():
        # 複製必要文件
        copy_required_files()
        
        # 創建說明文件
        create_installer_info()
        
        print("\n🎉 打包完成！")
        print("📁 輸出目錄: dist/")
        print("🚀 可執行文件: dist/DesktopPet.exe")
        print("\n💡 提示:")
        print("   - 將整個dist文件夾分發給用戶")
        print("   - 或者創建安裝包包含dist文件夾內容")
        print("   - 可執行文件已包含所有依賴，無需安裝Python")
        
        return 0
    else:
        print("\n🔧 如果問題持續，請嘗試:")
        print("   1. 更新PyInstaller: pip install --upgrade pyinstaller")
        print("   2. 清理緩存: python -m PyInstaller --clean desktop_pet.spec")
        print("   3. 檢查Python版本兼容性")
        
        return 1

if __name__ == "__main__":
    sys.exit(main()) 