"""
桌面寵物主視窗
提供透明桌面視窗和系統托盤功能
"""
from PySide6.QtWidgets import (QApplication, QLabel, QSystemTrayIcon, 
                               QMenu, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QSlider, QCheckBox, QSpinBox,
                               QMessageBox, QGroupBox, QColorDialog, QDialog,
                               QListWidget, QListWidgetItem, QLineEdit, QTextEdit)
from PySide6.QtGui import QIcon, QPixmap, QAction, QFont, QColor, QPalette
from PySide6.QtCore import Qt, QPoint, QSize, QTimer, QPropertyAnimation, QEasingCurve
import sys
import os
from loguru import logger
from core.controller import PetController
from utils.config import config_manager
import json


class DesktopPetWindow(QLabel):
    """桌面寵物主視窗類"""
    
    def __init__(self, assets_path="assets"):
        super().__init__()
        
        self.assets_path = assets_path
        
        # 載入窗口配置
        self._load_window_config()
        
        # 初始化核心控制器
        self.pet_controller = PetController(assets_path)
        
        # 如果配置中提醒已啟用，則啟動提醒
        from utils.config import config_manager
        if config_manager.get('reminder_enabled', False):
            self.pet_controller.start_reminders()
            logger.info("根據配置自動啟動提醒功能")
        
        # 消息顯示相關
        self._setup_message_display()
        
        # 視窗設置
        self._setup_window()
        
        # 系統托盤設置
        self._setup_system_tray()
        
        # 設置右鍵菜單
        self._setup_context_menu()
        
        # 連接信號
        self._connect_signals()
        
        # 設置動畫顯示
        self._setup_animation_display()
        
        # 拖拽相關
        self.drag_position = None
        
        logger.info("桌面寵物主視窗初始化完成")
    
    def _load_window_config(self):
        """載入窗口配置"""
        from utils.config import config_manager
        
        # 載入字體和邊框顏色
        font_color_str = config_manager.get('font_color', '#FFFFFF')
        border_color_str = config_manager.get('border_color', '#000000')
        
        logger.info(f"載入配置 - 字體顏色: {font_color_str}, 邊框顏色: {border_color_str}")
        
        # 轉換字符串為QColor對象
        if isinstance(font_color_str, str):
            self.message_font_color = QColor(font_color_str)
        else:
            self.message_font_color = QColor(255, 255, 255)  # 預設白色
            
        if isinstance(border_color_str, str):
            self.message_border_color = QColor(border_color_str)
        else:
            self.message_border_color = QColor(0, 0, 0)  # 預設黑色
            
        logger.info(f"窗口配置已載入 - 字體: {self.message_font_color.name()}, 邊框: {self.message_border_color.name()}")
    
    def _save_window_config(self):
        """保存窗口配置"""
        config_manager.update({
            'font_color': self.message_font_color.name(),
            'border_color': self.message_border_color.name()
        })
        config_manager.save_config()
        logger.info("窗口配置已保存")
    
    def _setup_message_display(self):
        """設置消息顯示組件"""
        # 創建消息標籤作為主窗口的子控件
        self.message_label = QLabel(self)
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.hide()  # 初始隱藏
        
        # 設置基本樣式
        self._update_message_style()
        
        logger.debug("消息顯示組件初始化完成")
    
    def _update_message_style(self):
        """更新消息樣式"""
        font_color = self.message_font_color.name()
        border_color = self.message_border_color.name()
        
        self.message_label.setStyleSheet(f"""
            QLabel {{
                color: {font_color};
                background-color: rgba(255, 255, 255, 220);
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 8px;
                font-size: 12px;
                font-weight: bold;
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
            }}
        """)
        
        logger.debug(f"消息樣式已更新 - 字體: {font_color}, 邊框: {border_color}")
    
    def _update_message_position(self):
        """更新消息標籤位置"""
        if not self.message_label:
            return
            
        # 設置消息最大寬度為寵物寬度，避免超出範圍
        pet_width = self.width()
        pet_height = self.height()
        
        # 限制消息寬度不超過寵物寬度
        max_width = pet_width - 20  # 左右各留10像素邊距
        self.message_label.setMaximumWidth(max_width)
        self.message_label.setWordWrap(True)
        
        # 重新調整大小以適應內容
        self.message_label.adjustSize()
        
        # 計算消息位置：寵物內部上方居中
        message_width = self.message_label.width()
        message_height = self.message_label.height()
        
        # 在寵物內部上方顯示，居中對齊
        message_x = (pet_width - message_width) // 2
        message_y = 10  # 距離寵物頂部10像素
        
        # 確保消息不會超出寵物範圍
        if message_x < 5:
            message_x = 5
        if message_y + message_height > pet_height - 10:
            message_y = pet_height - message_height - 10
        
        self.message_label.move(message_x, message_y)
        self.message_label.raise_()  # 確保在最上層
        
        logger.debug(f"消息位置更新: ({message_x}, {message_y}), 大小: {message_width}x{message_height}, 寵物大小: {pet_width}x{pet_height}")
    
    def show_message(self, message: str, duration: int = 5000):
        """顯示消息"""
        if not self.message_label:
            logger.warning("消息標籤不存在，無法顯示消息")
            return
            
        logger.info(f"顯示消息: {message}")
        self.message_label.setText(message)
        
        # 更新消息位置和樣式
        self._update_message_position()
        
        # 顯示消息
        self.message_label.show()
        
        # 設置定時隱藏
        if hasattr(self, 'message_timer'):
            self.message_timer.stop()
        else:
            self.message_timer = QTimer()
            self.message_timer.timeout.connect(self._hide_message)
        
        self.message_timer.start(duration)
        
        logger.debug(f"消息已顯示，將在 {duration}ms 後隱藏")
    
    def _hide_message(self):
        """隱藏消息"""
        if self.message_label:
            self.message_label.hide()
            logger.debug("消息已隱藏")
    
    def _setup_window(self):
        """設置視窗屬性"""
        # 設置無邊框、透明背景、置頂
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        # 設置初始大小和位置
        self.resize(150, 150)
        self.move(500, 300)  # 確保在可見位置
        
        # 設置最小大小
        self.setMinimumSize(50, 50)
        
        # 允許接受拖放事件
        self.setAcceptDrops(True)
        
        # 確保視窗可以接收鼠標事件
        self.setMouseTracking(True)
        
        logger.info("視窗屬性設置完成")
    
    def _setup_system_tray(self):
        """設置系統托盤"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("系統不支持系統托盤")
            return
        
        # 創建托盤圖標
        tray_icon_path = os.path.join(self.assets_path, "idle.gif")
        if os.path.exists(tray_icon_path):
            # 從GIF中提取第一幀作為圖標
            pixmap = QPixmap(tray_icon_path)
            icon = QIcon(pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            # 使用系統默認圖標
            icon = self.style().standardIcon(self.style().SP_ComputerIcon)
        
        self.tray_icon = QSystemTrayIcon(icon, self)
        
        # 創建托盤菜單
        self._create_tray_menu()
        
        # 設置托盤提示
        self.tray_icon.setToolTip("桌面寵物 - 點擊打開菜單")
        
        # 連接托盤信號
        self.tray_icon.activated.connect(self._on_tray_activated)
        
        # 顯示托盤圖標
        self.tray_icon.show()
        
        logger.info("系統托盤設置完成")
    
    def _create_tray_menu(self):
        """創建托盤右鍵菜單"""
        self.tray_menu = QMenu()
        
        # 顯示/隱藏寵物
        self.toggle_action = QAction("隱藏寵物", self)
        self.toggle_action.triggered.connect(self._toggle_visibility)
        self.tray_menu.addAction(self.toggle_action)
        
        self.tray_menu.addSeparator()
        
        # 設置選項
        settings_action = QAction("設置", self)
        settings_action.triggered.connect(self._show_settings)
        self.tray_menu.addAction(settings_action)
        
        # 提醒管理
        reminder_action = QAction("定時提醒", self)
        reminder_action.triggered.connect(self._toggle_reminders)
        self.tray_menu.addAction(reminder_action)
        
        # 音效開關
        self.sound_action = QAction("🔊 關閉音效", self)
        self.sound_action.triggered.connect(self._toggle_sound)
        self.tray_menu.addAction(self.sound_action)
        
        self.tray_menu.addSeparator()
        
        # 關於
        about_action = QAction("關於", self)
        about_action.triggered.connect(self._show_about)
        self.tray_menu.addAction(about_action)
        
        # 退出
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._quit_application)
        self.tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
    
    def _setup_animation_display(self):
        """設置動畫顯示"""
        movie = self.pet_controller.get_current_movie()
        if movie:
            self.setMovie(movie)
            movie.start()
            logger.info("動畫顯示設置完成")
        else:
            logger.warning("無法獲取動畫對象")
            # 設置一個佔位符文本，但不設置背景色
            self.setText("🐾")
            self.setAlignment(Qt.AlignCenter)
            self.setStyleSheet("QLabel { color: white; font-size: 48px; }")
    
    def _connect_signals(self):
        """連接信號"""
        # 控制器信號
        self.pet_controller.state_changed.connect(self._on_state_changed)
        self.pet_controller.notification_triggered.connect(self._show_notification)
        self.pet_controller.reminder_message.connect(self._show_reminder_message)  # 使用專門的提醒消息處理方法
        self.pet_controller.feeding_finished.connect(self._on_feeding_finished)  # 連接餵食完成信號
    
    def _show_reminder_message(self, message: str):
        """顯示提醒消息（較長顯示時間）"""
        self.show_message(message, 10000)  # 顯示10秒
        logger.info(f"顯示提醒消息: {message}")
    
    def _on_state_changed(self, state: str):
        """處理狀態變化"""
        movie = self.pet_controller.get_current_movie()
        if movie:
            self.setMovie(movie)
            movie.start()
            logger.info(f"視窗動畫已切換到: {state}")
        else:
            logger.warning(f"無法獲取 {state} 狀態的動畫對象")
            self.setText("🐾")
            self.setAlignment(Qt.AlignCenter)
    
    def _show_notification(self, message: str):
        """顯示系統通知"""
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.tray_icon.showMessage(
                "桌面寵物", 
                message, 
                QSystemTrayIcon.MessageIcon.Information, 
                3000
            )
    
    def _on_tray_activated(self, reason):
        """處理托盤圖標激活"""
        if reason == QSystemTrayIcon.DoubleClick:
            self._toggle_visibility()
        elif reason == QSystemTrayIcon.Trigger:
            # 單擊顯示寵物位置（閃爍效果）
            if self.isVisible():
                self._flash_pet()
    
    def _toggle_visibility(self):
        """切換寵物顯示/隱藏"""
        if self.isVisible():
            self.hide()
            self.toggle_action.setText("顯示寵物")
            logger.info("寵物已隱藏")
        else:
            self.show()
            self.toggle_action.setText("隱藏寵物")
            logger.info("寵物已顯示")
    
    def _flash_pet(self):
        """閃爍效果指示寵物位置"""
        original_opacity = self.windowOpacity()
        
        def flash_step(step):
            if step < 6:  # 閃爍3次
                opacity = 0.3 if step % 2 == 0 else 1.0
                self.setWindowOpacity(opacity)
                QTimer.singleShot(200, lambda: flash_step(step + 1))
            else:
                self.setWindowOpacity(original_opacity)
        
        flash_step(0)
    
    def _show_settings(self):
        """顯示設置對話框"""
        # 如果設置窗口已存在且還沒關閉，就直接顯示
        if hasattr(self, 'settings_window') and self.settings_window is not None:
            try:
                # 檢查窗口是否還有效
                self.settings_window.show()
                self.settings_window.raise_()
                self.settings_window.activateWindow()
                return
            except RuntimeError:
                # 窗口已被刪除，需要重新創建
                self.settings_window = None
        
        # 創建新的設置窗口
        self.settings_window = SettingsWindow(self.pet_controller, self)
        self.settings_window.show()
        
        logger.info("設置窗口已創建並顯示")
    
    def _toggle_reminders(self):
        """切換定時提醒"""
        if self.pet_controller.reminder_timer.isActive():
            self.pet_controller.stop_reminders()
            self._show_notification("定時提醒已停止")
            logger.info("通過托盤菜單停止定時提醒")
        else:
            self.pet_controller.start_reminders()
            self._show_notification("定時提醒已啟動")
            logger.info("通過托盤菜單啟動定時提醒")
    
    def _show_about(self):
        """顯示關於信息"""
        self._show_notification("桌面寵物 v1.0 - 陪伴你的桌面小夥伴")
    
    def _quit_application(self):
        """退出應用程序"""
        logger.info("正在退出應用程序...")
        self.pet_controller.cleanup()
        QApplication.quit()
    
    # 事件處理方法
    def mousePressEvent(self, event):
        """鼠標按下事件"""
        # 處理事件
        self.pet_controller.get_event_handler().handle_mouse_press(event)
        
        # 記錄拖拽起點
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            logger.debug(f"鼠標按下: {event.globalPosition().toPoint()}")
        
        event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠標移動事件"""
        # 處理事件
        self.pet_controller.get_event_handler().handle_mouse_move(event)
        
        # 處理視窗拖拽
        if (event.buttons() & Qt.LeftButton and 
            self.drag_position is not None):
            new_pos = event.globalPosition().toPoint() - self.drag_position
            self.move(new_pos)
            logger.debug(f"拖拽移動到: {new_pos}")
        
        event.accept()
    
    def mouseReleaseEvent(self, event):
        """鼠標釋放事件"""
        # 處理事件
        self.pet_controller.get_event_handler().handle_mouse_release(event)
        
        # 重置拖拽狀態
        if self.drag_position is not None:
            logger.debug(f"鼠標釋放: {event.globalPosition().toPoint()}")
            self.drag_position = None
        
        event.accept()
    
    def enterEvent(self, event):
        """鼠標進入事件"""
        self.pet_controller.get_event_handler().handle_enter_event()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠標離開事件"""
        self.pet_controller.get_event_handler().handle_leave_event()
        super().leaveEvent(event)
    
    def closeEvent(self, event):
        """視窗關閉事件"""
        # 關閉視窗時隱藏到托盤，而不是真正退出
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            self._quit_application()
            event.accept()

    def _setup_context_menu(self):
        """設置右鍵上下文菜單"""
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
    def _show_context_menu(self, position):
        """顯示右鍵上下文菜單"""
        context_menu = QMenu(self)
        
        # 設置選項
        settings_action = context_menu.addAction("⚙️ 設置")
        settings_action.triggered.connect(self._show_settings)
        
        # 提醒選項
        reminder_action = context_menu.addAction("🔔 切換提醒")
        reminder_action.triggered.connect(self._toggle_reminders)
        
        context_menu.addSeparator()
        
        # 隱藏選項
        hide_action = context_menu.addAction("👁️ 隱藏寵物")
        hide_action.triggered.connect(self.hide)
        
        # 關閉選項
        quit_action = context_menu.addAction("❌ 退出程序")
        quit_action.triggered.connect(self._quit_application)
        
        # 顯示菜單
        context_menu.exec(self.mapToGlobal(position))

    def resizeEvent(self, event):
        """視窗大小改變事件"""
        super().resizeEvent(event)
        self._update_message_position()

    def _on_feeding_finished(self):
        """處理餵食完成"""
        logger.info("餵食動畫播放完成")

    def _toggle_sound(self):
        """切換音效開關"""
        self.pet_controller.set_sound_enabled(not self.pet_controller.is_sound_enabled())
        self._show_notification("音效開關已切換")

class SettingsWindow(QWidget):
    """設置視窗"""
    
    def __init__(self, pet_controller, main_window=None):
        super().__init__()
        self.pet_controller = pet_controller
        self.main_window = main_window
        
        # 保存原始設置用於取消操作
        self.original_settings = self._get_current_settings()
        
        logger.info(f"設置窗口初始化 - 讀取到的配置: {self.original_settings}")
        
        self._setup_ui()
    
    def _get_current_settings(self):
        """獲取當前設置"""
        from utils.config import config_manager
        
        logger.info(f"讀取配置 - 當前配置管理器狀態: {config_manager.config}")
        
        # 從配置文件獲取顏色設置
        font_color_str = config_manager.get('font_color', '#FFFFFF')
        border_color_str = config_manager.get('border_color', '#000000')
        
        logger.info(f"讀取配置 - 字體顏色: {font_color_str}, 邊框顏色: {border_color_str}")
        logger.info(f"讀取配置 - 提醒間隔: {config_manager.get('reminder_interval', 30)}")
        logger.info(f"讀取配置 - 提醒啟用: {config_manager.get('reminder_enabled', False)}")
        
        # 轉換為QColor對象
        font_color = QColor(font_color_str) if isinstance(font_color_str, str) else QColor(255, 255, 255)
        border_color = QColor(border_color_str) if isinstance(border_color_str, str) else QColor(0, 0, 0)
        
        return {
            'pet_size': config_manager.get('pet_size', 150),
            'reminder_interval': config_manager.get('reminder_interval', 30),  # 從配置文件讀取
            'reminder_enabled': config_manager.get('reminder_enabled', False),  # 從配置文件讀取
            'idle_enabled': config_manager.get('idle_enabled', True),
            'font_color': font_color,
            'border_color': border_color,
            'sound_enabled': config_manager.get('sound_enabled', True)  # 從配置文件讀取
        }
    
    def _setup_ui(self):
        """設置用戶界面"""
        self.setWindowTitle("桌面寵物設置")
        self.setFixedSize(400, 450)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        
        layout = QVBoxLayout()
        
        # 基本設置組
        basic_group = QGroupBox("基本設置")
        basic_layout = QVBoxLayout(basic_group)
        
        # 寵物大小設置
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("寵物大小:"))
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(50, 300)
        # 主動設置為配置文件中的值
        self.size_slider.setValue(self.original_settings['pet_size'])
        self.size_label = QLabel(f"{self.original_settings['pet_size']}px")
        self.size_slider.valueChanged.connect(lambda v: self.size_label.setText(f"{v}px"))
        size_layout.addWidget(self.size_slider)
        size_layout.addWidget(self.size_label)
        basic_layout.addLayout(size_layout)
        
        # 音效開關
        self.sound_checkbox = QCheckBox("開啟音效")
        # 主動設置為配置文件中的值
        self.sound_checkbox.setChecked(self.original_settings['sound_enabled'])
        basic_layout.addWidget(self.sound_checkbox)
        
        # 餵食按鈕
        self.feed_button = QPushButton("🍖 餵食寵物")
        self.feed_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 8px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.feed_button.clicked.connect(self._feed_pet)
        basic_layout.addWidget(self.feed_button)
        
        layout.addWidget(basic_group)
        
        # 提醒設置組
        reminder_group = QGroupBox("提醒設置")
        reminder_layout = QVBoxLayout()
        
        # 提醒間隔設置
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("提醒間隔(分鐘):"))
        self.reminder_spin = QSpinBox()
        self.reminder_spin.setRange(1, 120)
        # 主動設置為配置文件中的值
        self.reminder_spin.setValue(self.original_settings['reminder_interval'])
        interval_layout.addWidget(self.reminder_spin)
        reminder_layout.addLayout(interval_layout)
        
        # 開啟定時提醒設置
        self.reminder_checkbox = QCheckBox("開啟定時提醒")
        # 主動設置為配置文件中的值
        self.reminder_checkbox.setChecked(self.original_settings['reminder_enabled'])
        reminder_layout.addWidget(self.reminder_checkbox)
        
        # 自定義提醒消息按鈕
        self.custom_messages_btn = QPushButton("📝 管理提醒消息")
        self.custom_messages_btn.clicked.connect(self._manage_reminder_messages)
        reminder_layout.addWidget(self.custom_messages_btn)
        
        # 閒置檢測設置
        self.idle_checkbox = QCheckBox("開啟閒置檢測")
        # 主動設置為配置文件中的值
        self.idle_checkbox.setChecked(self.original_settings['idle_enabled'])
        reminder_layout.addWidget(self.idle_checkbox)
        
        reminder_group.setLayout(reminder_layout)
        layout.addWidget(reminder_group)
        
        # 外觀設置組
        appearance_group = QGroupBox("消息外觀設置")
        appearance_layout = QVBoxLayout()
        
        # 字體顏色設置
        font_color_layout = QHBoxLayout()
        font_color_layout.addWidget(QLabel("字體顏色:"))
        self.font_color_btn = QPushButton()
        self.font_color_btn.setFixedSize(50, 30)
        # 主動設置為配置文件中的值
        self.font_color = self.original_settings['font_color']
        self.font_color_btn.setStyleSheet(f"background-color: {self.font_color.name()}")
        self.font_color_btn.clicked.connect(self._choose_font_color)
        font_color_layout.addWidget(self.font_color_btn)
        font_color_layout.addStretch()
        appearance_layout.addLayout(font_color_layout)
        
        # 邊框顏色設置
        border_color_layout = QHBoxLayout()
        border_color_layout.addWidget(QLabel("邊框顏色:"))
        self.border_color_btn = QPushButton()
        self.border_color_btn.setFixedSize(50, 30)
        # 主動設置為配置文件中的值
        self.border_color = self.original_settings['border_color']
        self.border_color_btn.setStyleSheet(f"background-color: {self.border_color.name()}")
        self.border_color_btn.clicked.connect(self._choose_border_color)
        border_color_layout.addWidget(self.border_color_btn)
        border_color_layout.addStretch()
        appearance_layout.addLayout(border_color_layout)
        
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)
        
        # 按鈕組
        button_layout = QHBoxLayout()
        
        # 預覽按鈕
        preview_btn = QPushButton("預覽消息")
        preview_btn.clicked.connect(self._preview_message)
        button_layout.addWidget(preview_btn)
        
        button_layout.addStretch()
        
        # 保存按鈕（移到左邊）
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save_settings)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        # 取消按鈕（移到右邊）
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self._cancel_settings)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 記錄UI初始化完成和實際顯示的值
        logger.info(f"UI控件初始化完成:")
        logger.info(f"  - 寵物大小滑塊值: {self.size_slider.value()}")
        logger.info(f"  - 提醒間隔數值: {self.reminder_spin.value()}")
        logger.info(f"  - 提醒啟用checkbox: {self.reminder_checkbox.isChecked()}")
        logger.info(f"  - 閒置檢測checkbox: {self.idle_checkbox.isChecked()}")
        logger.info(f"  - 音效checkbox: {self.sound_checkbox.isChecked()}")
        logger.info(f"  - 字體顏色: {self.font_color.name()}")
        logger.info(f"  - 邊框顏色: {self.border_color.name()}")
    
    def _choose_font_color(self):
        """選擇字體顏色"""
        color = QColorDialog.getColor(self.font_color, self, "選擇字體顏色")
        if color.isValid():
            self.font_color = color
            self.font_color_btn.setStyleSheet(f"background-color: {color.name()}")
    
    def _choose_border_color(self):
        """選擇邊框顏色"""
        color = QColorDialog.getColor(self.border_color, self, "選擇邊框顏色")
        if color.isValid():
            self.border_color = color
            self.border_color_btn.setStyleSheet(f"background-color: {color.name()}")
    
    def _preview_message(self):
        """預覽消息效果"""
        if self.main_window:
            # 臨時應用當前設置
            original_font_color = self.main_window.message_font_color
            original_border_color = self.main_window.message_border_color
            
            self.main_window.message_font_color = self.font_color
            self.main_window.message_border_color = self.border_color
            self.main_window._update_message_style()
            
            # 顯示預覽消息
            self.main_window.show_message("這是消息預覽效果", 3000)
            
            # 恢復原始設置
            QTimer.singleShot(3100, lambda: self._restore_preview_colors(original_font_color, original_border_color))
    
    def _restore_preview_colors(self, original_font_color, original_border_color):
        """恢復預覽前的顏色設置"""
        if self.main_window:
            self.main_window.message_font_color = original_font_color
            self.main_window.message_border_color = original_border_color
            self.main_window._update_message_style()
    
    def _has_changes(self):
        """檢查是否有設置變更"""
        try:
            # 檢查UI組件是否還存在
            if not hasattr(self, 'size_slider') or self.size_slider is None:
                logger.debug("UI組件不存在，返回無變更")
                return False
            if not hasattr(self, 'reminder_spin') or self.reminder_spin is None:
                logger.debug("reminder_spin不存在，返回無變更")
                return False
            if not hasattr(self, 'reminder_checkbox') or self.reminder_checkbox is None:
                logger.debug("reminder_checkbox不存在，返回無變更")
                return False
            if not hasattr(self, 'idle_checkbox') or self.idle_checkbox is None:
                logger.debug("idle_checkbox不存在，返回無變更")
                return False
            if not hasattr(self, 'sound_checkbox') or self.sound_checkbox is None:
                logger.debug("sound_checkbox不存在，返回無變更")
                return False
            
            current = {
                'pet_size': self.size_slider.value(),
                'reminder_interval': self.reminder_spin.value(),
                'reminder_enabled': self.reminder_checkbox.isChecked(),
                'idle_enabled': self.idle_checkbox.isChecked(),
                'font_color': self.font_color.name(),  # 使用顏色名稱字符串
                'border_color': self.border_color.name(),  # 使用顏色名稱字符串
                'sound_enabled': self.sound_checkbox.isChecked()
            }
            
            # 將原始設置中的顏色也轉換為字符串進行比較
            original_font_color = self.original_settings['font_color'].name() if hasattr(self.original_settings['font_color'], 'name') else str(self.original_settings['font_color'])
            original_border_color = self.original_settings['border_color'].name() if hasattr(self.original_settings['border_color'], 'name') else str(self.original_settings['border_color'])
            
            logger.info(f"變更檢測 - 當前UI值: {current}")
            logger.info(f"變更檢測 - 原始設置字體顏色: {original_font_color}, 邊框顏色: {original_border_color}")
            
            has_changes = (current['pet_size'] != self.original_settings['pet_size'] or
                    current['reminder_interval'] != self.original_settings['reminder_interval'] or
                    current['reminder_enabled'] != self.original_settings['reminder_enabled'] or
                    current['idle_enabled'] != self.original_settings['idle_enabled'] or
                    current['font_color'] != original_font_color or
                    current['border_color'] != original_border_color or
                    current['sound_enabled'] != self.original_settings['sound_enabled'])
            
            logger.info(f"變更檢測結果: {has_changes}")
            
            if has_changes:
                logger.info("檢測到的具體變更:")
                if current['pet_size'] != self.original_settings['pet_size']:
                    logger.info(f"  - 寵物大小: {self.original_settings['pet_size']} -> {current['pet_size']}")
                if current['reminder_interval'] != self.original_settings['reminder_interval']:
                    logger.info(f"  - 提醒間隔: {self.original_settings['reminder_interval']} -> {current['reminder_interval']}")
                if current['reminder_enabled'] != self.original_settings['reminder_enabled']:
                    logger.info(f"  - 提醒啟用: {self.original_settings['reminder_enabled']} -> {current['reminder_enabled']}")
                if current['idle_enabled'] != self.original_settings['idle_enabled']:
                    logger.info(f"  - 閒置檢測: {self.original_settings['idle_enabled']} -> {current['idle_enabled']}")
                if current['font_color'] != original_font_color:
                    logger.info(f"  - 字體顏色: {original_font_color} -> {current['font_color']}")
                if current['border_color'] != original_border_color:
                    logger.info(f"  - 邊框顏色: {original_border_color} -> {current['border_color']}")
                if current['sound_enabled'] != self.original_settings['sound_enabled']:
                    logger.info(f"  - 音效啟用: {self.original_settings['sound_enabled']} -> {current['sound_enabled']}")
            
            return has_changes
            
        except RuntimeError:
            # UI組件已被刪除，視為無變更
            logger.debug("UI組件運行時錯誤，返回無變更")
            return False
    
    def _save_settings(self):
        """保存設置"""
        try:
            logger.info("=== 開始保存設置流程 ===")
            
            # 檢查UI組件是否還存在
            if not hasattr(self, 'size_slider') or self.size_slider is None:
                logger.warning("UI組件已被刪除，無法保存設置")
                self.close()
                return
            
            logger.info("UI組件檢查通過")
            
            # 直接保存，不再詢問確認
            logger.info("開始保存設置...")
            
            # 獲取當前UI中的值
            pet_size = self.size_slider.value()
            reminder_interval = self.reminder_spin.value()
            reminder_enabled = self.reminder_checkbox.isChecked()
            idle_enabled = self.idle_checkbox.isChecked()
            sound_enabled = self.sound_checkbox.isChecked()
            font_color_name = self.font_color.name()
            border_color_name = self.border_color.name()
            
            logger.info(f"UI中的值 - 寵物大小: {pet_size}, 提醒間隔: {reminder_interval}分鐘")
            logger.info(f"UI中的值 - 提醒啟用: {reminder_enabled}, 閒置檢測: {idle_enabled}, 音效: {sound_enabled}")
            logger.info(f"UI中的值 - 字體顏色: {font_color_name}, 邊框顏色: {border_color_name}")
            
            # 使用簡單直接的方法保存配置
            settings_path = "config.json"
            settings = {
                "pet_size": pet_size,
                "reminder_interval": reminder_interval,
                "reminder_enabled": reminder_enabled,
                "idle_enabled": idle_enabled,
                "sound_enabled": sound_enabled,
                "font_color": font_color_name,
                "border_color": border_color_name,
                "reminder_messages": [
                    "該休息一下眼睛了！",
                    "記得保持良好的坐姿哦～",
                    "喝點水，保持水分！",
                    "起來走動走動吧！",
                    "深呼吸，放松一下～",
                    "記得活動手腕和頸部！"
                ]
            }
            
            logger.info(f"準備保存的設置: {settings}")
            
            try:
                # 直接保存配置文件
                with open(settings_path, "w", encoding="utf-8") as f:
                    json.dump(settings, f, indent=4, ensure_ascii=False)
                logger.info("配置文件保存成功")
                
                # 驗證保存結果
                if os.path.exists(settings_path):
                    with open(settings_path, "r", encoding="utf-8") as f:
                        saved_data = json.load(f)
                    logger.info(f"驗證保存結果: {saved_data}")
                
                # 同時更新配置管理器
                from utils.config import config_manager
                config_manager.config.update(settings)
                logger.info("配置管理器已同步更新")
                
                # 應用設置到控制器
                self.pet_controller.set_pet_size(pet_size, pet_size)
                logger.info(f"寵物大小已應用: {pet_size}")
                
                self.pet_controller.set_reminder_interval(reminder_interval)
                logger.info(f"提醒間隔已應用: {reminder_interval}分鐘")
                
                if reminder_enabled:
                    self.pet_controller.start_reminders()
                    logger.info("提醒功能已啟動")
                else:
                    self.pet_controller.stop_reminders()
                    logger.info("提醒功能已停止")
                
                if idle_enabled:
                    self.pet_controller.get_event_handler().start_idle_detection()
                    logger.info("閒置檢測已啟動")
                else:
                    self.pet_controller.get_event_handler().stop_idle_detection()
                    logger.info("閒置檢測已停止")
                
                # 設置音效
                self.pet_controller.set_sound_enabled(sound_enabled)
                logger.info(f"音效設置已應用: {sound_enabled}")
                
                # 應用外觀設置到主窗口
                if self.main_window:
                    self.main_window.message_font_color = self.font_color
                    self.main_window.message_border_color = self.border_color
                    self.main_window._update_message_style()
                    logger.info("外觀設置已應用到主窗口")
                
                logger.info("=== 設置保存流程完成 ===")
                self._show_notification("設置已保存")
                
                # 更新原始設置，避免關閉時再次詢問
                self.original_settings = self._get_current_settings()
                
                # 保存成功後自動關閉窗口
                self.close()
                
            except Exception as save_error:
                logger.error(f"保存配置文件時發生錯誤: {save_error}")
                QMessageBox.warning(self, "保存失敗", f"配置文件保存失敗: {save_error}")
                
        except RuntimeError as e:
            logger.error(f"保存設置時發生運行時錯誤: {e}")
        except Exception as e:
            logger.error(f"保存設置時發生未知錯誤: {e}")
            import traceback
            logger.error(f"錯誤堆疊: {traceback.format_exc()}")
    
    def _cancel_settings(self):
        """取消設置"""
        try:
            # 直接關閉窗口，如果有未保存的變更會在 closeEvent 中處理
            self.close()
        except RuntimeError as e:
            logger.error(f"取消設置時發生錯誤: {e}")
            self.close()
    
    def closeEvent(self, event):
        """關閉事件"""
        try:
            if self._has_changes():
                reply = QMessageBox.question(self, "關閉設置", 
                                           "您有未保存的更改，是否要保存？",
                                           QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                                           QMessageBox.Save)
                
                if reply == QMessageBox.Save:
                    self._save_settings()
                    event.accept()
                elif reply == QMessageBox.Discard:
                    event.accept()
                else:
                    event.ignore()
                    return
            else:
                event.accept()
            
            # 清理主窗口中的設置窗口引用
            if self.main_window and hasattr(self.main_window, 'settings_window'):
                self.main_window.settings_window = None
            
            logger.info("設置窗口已關閉並清理引用")
                
        except RuntimeError as e:
            logger.error(f"關閉設置窗口時發生錯誤: {e}")
            event.accept()
            
            # 即使出錯也要清理引用
            if self.main_window and hasattr(self.main_window, 'settings_window'):
                self.main_window.settings_window = None
    
    def _feed_pet(self):
        """處理餵食寵物"""
        self.pet_controller.feed_pet()
        
    def _show_notification(self, message):
        """顯示通知消息"""
        if self.main_window:
            self.main_window.show_message(message)

    def _manage_reminder_messages(self):
        """管理提醒消息"""
        dialog = ReminderMessagesDialog(self.pet_controller, self)
        dialog.exec()


class ReminderMessagesDialog(QDialog):
    """提醒消息管理對話框"""
    
    def __init__(self, pet_controller, parent=None):
        super().__init__(parent)
        self.pet_controller = pet_controller
        self.setWindowTitle("管理提醒消息")
        self.setFixedSize(500, 400)
        
        # 獲取當前消息列表
        self.messages = self.pet_controller.reminder_messages.copy()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """設置UI"""
        layout = QVBoxLayout(self)
        
        # 說明文字
        info_label = QLabel("您可以添加最多5個自定義提醒消息：")
        layout.addWidget(info_label)
        
        # 消息列表
        self.message_list = QListWidget()
        self._update_message_list()
        layout.addWidget(self.message_list)
        
        # 新消息輸入
        input_layout = QVBoxLayout()
        input_layout.addWidget(QLabel("新消息："))
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(80)
        self.message_input.setPlaceholderText("輸入新的提醒消息...")
        input_layout.addWidget(self.message_input)
        layout.addLayout(input_layout)
        
        # 按鈕組
        button_layout = QHBoxLayout()
        
        # 添加按鈕
        add_btn = QPushButton("➕ 添加消息")
        add_btn.clicked.connect(self._add_message)
        button_layout.addWidget(add_btn)
        
        # 刪除按鈕
        delete_btn = QPushButton("🗑️ 刪除選中")
        delete_btn.clicked.connect(self._delete_message)
        button_layout.addWidget(delete_btn)
        
        button_layout.addStretch()
        
        # 保存按鈕
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._save_messages)
        button_layout.addWidget(save_btn)
        
        # 取消按鈕
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _update_message_list(self):
        """更新消息列表"""
        self.message_list.clear()
        for i, message in enumerate(self.messages):
            item = QListWidgetItem(f"{i+1}. {message}")
            self.message_list.addItem(item)
    
    def _add_message(self):
        """添加新消息"""
        message = self.message_input.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "錯誤", "請輸入消息內容！")
            return
        
        if len(self.messages) >= 5:
            QMessageBox.warning(self, "錯誤", "最多只能添加5個消息！")
            return
        
        self.messages.append(message)
        self.message_input.clear()
        self._update_message_list()
    
    def _delete_message(self):
        """刪除選中的消息"""
        current_row = self.message_list.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(self, "確認刪除", 
                                       "確定要刪除這個消息嗎？",
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.No)
            if reply == QMessageBox.Yes:
                del self.messages[current_row]
                self._update_message_list()
        else:
            QMessageBox.warning(self, "錯誤", "請先選擇要刪除的消息！")
    
    def _save_messages(self):
        """保存消息"""
        if not self.messages:
            QMessageBox.warning(self, "錯誤", "至少需要一個提醒消息！")
            return
        
        # 更新控制器中的消息
        self.pet_controller.reminder_messages = self.messages
        self.pet_controller.current_reminder_index = 0
        
        QMessageBox.information(self, "成功", "提醒消息已保存！")
        self.accept()
