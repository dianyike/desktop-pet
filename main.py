"""
桌面寵物主程序入口
整合所有功能模組，提供完整的桌面寵物體驗
"""
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication, Qt
import sys
import os
from loguru import logger
from ui.main_window import DesktopPetWindow


def setup_logging():
    """設置日誌系統"""
    # 創建日誌目錄
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 配置loguru
    logger.remove()  # 移除默認處理器
    
    # 添加文件日誌
    logger.add(
        os.path.join(log_dir, "desktop_pet_{time:YYYY-MM-DD}.log"),
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        encoding="utf-8"
    )
    
    # 添加控制台日誌（僅在調試模式下）
    if "--debug" in sys.argv:
        logger.add(
            sys.stderr,
            level="DEBUG",
            format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | {message}"
        )
    
    logger.info("日誌系統初始化完成")


def setup_application():
    """設置應用程序"""
    # 設置應用程序屬性
    QCoreApplication.setApplicationName("桌面寵物")
    QCoreApplication.setApplicationVersion("1.0.0")
    QCoreApplication.setOrganizationName("Desktop Pet")
    QCoreApplication.setOrganizationDomain("desktop-pet.local")
    
    # 設置高DPI支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # 創建應用程序實例
    app = QApplication(sys.argv)
    
    # 設置應用程序圖標
    assets_path = "assets"
    icon_path = os.path.join(assets_path, "idle.gif")
    if os.path.exists(icon_path):
        from PySide6.QtGui import QIcon, QPixmap
        app.setWindowIcon(QIcon(QPixmap(icon_path)))
    
    # 設置樣式
    app.setStyle("Fusion")  # 使用Fusion樣式以獲得更好的跨平台外觀
    
    logger.info("應用程序設置完成")
    return app


def check_dependencies():
    """檢查必要的依賴和資源"""
    # 檢查資源文件
    assets_path = "assets"
    required_assets = ["idle.gif", "move.gif", "dance.gif", "eat.gif", "sleepy.gif", "sleep.gif", "meow.wav"]
    
    missing_assets = []
    for asset in required_assets:
        asset_path = os.path.join(assets_path, asset)
        if not os.path.exists(asset_path):
            missing_assets.append(asset)
    
    if missing_assets:
        logger.warning(f"缺少資源文件: {missing_assets}")
        return False
    
    logger.info("資源文件檢查完成")
    return True


def main():
    """主函數"""
    try:
        # 設置日誌
        setup_logging()
        logger.info("=== 桌面寵物啟動 ===")
        
        # 檢查依賴
        if not check_dependencies():
            logger.error("依賴檢查失敗，程序退出")
            return 1
        
        # 設置應用程序
        app = setup_application()
        
        # 檢查是否支持系統托盤
        from PySide6.QtWidgets import QSystemTrayIcon
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("系統不支持系統托盤功能")
        
        # 創建主窗口
        logger.info("創建桌面寵物窗口...")
        window = DesktopPetWindow()
        
        # 顯示窗口
        window.show()
        logger.info("桌面寵物窗口已顯示")
        
        # 處理命令行參數
        if "--hide" in sys.argv:
            window.hide()
            logger.info("啟動時隱藏寵物")
        
        if "--start-reminders" in sys.argv:
            window.pet_controller.start_reminders()
            logger.info("啟動時開啟定時提醒")
        
        # 確保程序不會因為關閉主窗口而退出
        app.setQuitOnLastWindowClosed(False)
        
        logger.info("桌面寵物已成功啟動！")
        
        # 運行事件循環
        exit_code = app.exec()
        
        logger.info(f"桌面寵物正常退出，退出碼: {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.exception(f"程序運行出現錯誤: {e}")
        return 1
    finally:
        logger.info("=== 桌面寵物退出 ===")


if __name__ == "__main__":
    # 支持的命令行參數：
    # --debug: 啟用調試模式，顯示詳細日誌
    # --hide: 啟動時隱藏寵物
    # --start-reminders: 啟動時開啟定時提醒
    
    sys.exit(main()) 