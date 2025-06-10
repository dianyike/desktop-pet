"""
桌面寵物通知工具
提供跨平台的桌面通知和提醒功能
"""
from PySide6.QtWidgets import QSystemTrayIcon, QApplication
from PySide6.QtCore import QObject, Signal, QTimer
from loguru import logger
import platform
import subprocess
import os
from datetime import datetime, timedelta
from enum import Enum


class NotificationType(Enum):
    """通知類型枚舉"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    REMINDER = "reminder"


class NotificationPriority(Enum):
    """通知優先級"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class CrossPlatformNotifier(QObject):
    """跨平台通知器"""
    
    notification_clicked = Signal(str)  # 通知被點擊
    notification_shown = Signal(str)    # 通知已顯示
    
    def __init__(self, app_name="桌面寵物"):
        super().__init__()
        self.app_name = app_name
        self.platform = platform.system().lower()
        self.tray_icon = None
        
        logger.info(f"通知器初始化完成 - 平台: {self.platform}")
    
    def set_tray_icon(self, tray_icon: QSystemTrayIcon):
        """設置系統托盤圖標"""
        self.tray_icon = tray_icon
    
    def show_notification(self, title: str, message: str, 
                         notification_type: NotificationType = NotificationType.INFO,
                         duration: int = 5000):
        """顯示通知"""
        try:
            if self._use_qt_notification():
                self._show_qt_notification(title, message, notification_type, duration)
            else:
                self._show_native_notification(title, message, notification_type, duration)
            
            self.notification_shown.emit(message)
            logger.info(f"通知已顯示: {title} - {message}")
            
        except Exception as e:
            logger.error(f"顯示通知失敗: {e}")
    
    def _use_qt_notification(self) -> bool:
        """判斷是否使用Qt通知"""
        return (self.tray_icon is not None and 
                self.tray_icon.isVisible() and 
                QSystemTrayIcon.supportsMessages())
    
    def _show_qt_notification(self, title: str, message: str, 
                             notification_type: NotificationType, duration: int):
        """顯示Qt系統托盤通知"""
        icon_type = self._get_qt_icon_type(notification_type)
        self.tray_icon.showMessage(title, message, icon_type, duration)
    
    def _get_qt_icon_type(self, notification_type: NotificationType):
        """獲取Qt通知圖標類型"""
        type_map = {
            NotificationType.INFO: QSystemTrayIcon.MessageIcon.Information,
            NotificationType.WARNING: QSystemTrayIcon.MessageIcon.Warning,
            NotificationType.ERROR: QSystemTrayIcon.MessageIcon.Critical,
            NotificationType.REMINDER: QSystemTrayIcon.MessageIcon.Information
        }
        return type_map.get(notification_type, QSystemTrayIcon.MessageIcon.Information)
    
    def _show_native_notification(self, title: str, message: str,
                                 notification_type: NotificationType, duration: int):
        """顯示原生系統通知"""
        if self.platform == "windows":
            self._show_windows_notification(title, message, duration)
        elif self.platform == "darwin":  # macOS
            self._show_macos_notification(title, message, duration)
        elif self.platform == "linux":
            self._show_linux_notification(title, message, duration)
        else:
            logger.warning(f"不支持的平台: {self.platform}")
    
    def _show_windows_notification(self, title: str, message: str, duration: int):
        """Windows原生通知"""
        try:
            import win10toast
            toaster = win10toast.ToastNotifier()
            toaster.show_toast(
                title,
                message,
                duration=duration // 1000,  # 轉換為秒
                threaded=True
            )
        except ImportError:
            # 備用方案：使用PowerShell
            self._show_windows_powershell_notification(title, message)
    
    def _show_windows_powershell_notification(self, title: str, message: str):
        """使用PowerShell顯示Windows通知"""
        script = f'''
        Add-Type -AssemblyName System.Windows.Forms
        $balloon = New-Object System.Windows.Forms.NotifyIcon
        $balloon.Icon = [System.Drawing.SystemIcons]::Information
        $balloon.BalloonTipIcon = "Info"
        $balloon.BalloonTipText = "{message}"
        $balloon.BalloonTipTitle = "{title}"
        $balloon.Visible = $true
        $balloon.ShowBalloonTip(5000)
        '''
        try:
            subprocess.run(["powershell", "-Command", script], 
                          capture_output=True, text=True, timeout=10)
        except Exception as e:
            logger.error(f"PowerShell通知失敗: {e}")
    
    def _show_macos_notification(self, title: str, message: str, duration: int):
        """macOS原生通知"""
        script = f'''
        display notification "{message}" with title "{title}" sound name "default"
        '''
        try:
            subprocess.run(["osascript", "-e", script], 
                          capture_output=True, text=True, timeout=10)
        except Exception as e:
            logger.error(f"macOS通知失敗: {e}")
    
    def _show_linux_notification(self, title: str, message: str, duration: int):
        """Linux原生通知"""
        try:
            subprocess.run([
                "notify-send", 
                title, 
                message, 
                f"--expire-time={duration}"
            ], capture_output=True, text=True, timeout=10)
        except Exception as e:
            logger.error(f"Linux通知失敗: {e}")


class ReminderScheduler(QObject):
    """提醒調度器"""
    
    reminder_triggered = Signal(str, str)  # title, message
    
    def __init__(self):
        super().__init__()
        self.reminders = {}  # 存儲提醒任務
        self.active_timers = {}  # 活動的定時器
        
        # 預設提醒消息
        self.default_reminders = {
            "hydration": {
                "title": "💧 補水提醒",
                "messages": [
                    "該喝水了！保持身體水分充足很重要哦～",
                    "別忘了喝水！你已經專注工作很久了",
                    "來杯水吧！讓大腦保持清醒"
                ],
                "interval": 30,  # 分鐘
                "current_index": 0
            },
            "posture": {
                "title": "🪑 姿勢提醒",
                "messages": [
                    "檢查一下坐姿！記得保持脊椎挺直",
                    "調整一下坐姿，預防頸椎問題",
                    "坐姿端正，身體更健康！"
                ],
                "interval": 45,
                "current_index": 0
            },
            "rest": {
                "title": "😴 休息提醒",
                "messages": [
                    "該休息一下眼睛了！看看遠方放鬆一下",
                    "工作辛苦了！起來走動走動吧",
                    "休息是為了走更長的路，放鬆一下吧！"
                ],
                "interval": 60,
                "current_index": 0
            },
            "exercise": {
                "title": "🏃 運動提醒",
                "messages": [
                    "起來活動活動筋骨吧！",
                    "簡單的伸展運動對身體很有好處",
                    "運動一下，保持活力！"
                ],
                "interval": 90,
                "current_index": 0
            }
        }
        
        logger.info("提醒調度器初始化完成")
    
    def add_reminder(self, name: str, title: str, messages: list, 
                    interval_minutes: int, auto_start: bool = False):
        """添加自定義提醒"""
        self.reminders[name] = {
            "title": title,
            "messages": messages,
            "interval": interval_minutes,
            "current_index": 0
        }
        
        if auto_start:
            self.start_reminder(name)
        
        logger.info(f"添加提醒: {name}, 間隔: {interval_minutes}分鐘")
    
    def start_reminder(self, name: str):
        """開始指定提醒"""
        if name in self.reminders:
            self.stop_reminder(name)  # 先停止現有的
            
            reminder = self.reminders[name]
            interval_ms = reminder["interval"] * 60 * 1000
            
            timer = QTimer()
            timer.timeout.connect(lambda: self._trigger_reminder(name))
            timer.start(interval_ms)
            
            self.active_timers[name] = timer
            logger.info(f"提醒已啟動: {name}")
        else:
            logger.error(f"提醒不存在: {name}")
    
    def stop_reminder(self, name: str):
        """停止指定提醒"""
        if name in self.active_timers:
            self.active_timers[name].stop()
            del self.active_timers[name]
            logger.info(f"提醒已停止: {name}")
    
    def start_all_default_reminders(self):
        """啟動所有預設提醒"""
        self.reminders.update(self.default_reminders)
        for name in self.default_reminders.keys():
            self.start_reminder(name)
        logger.info("所有預設提醒已啟動")
    
    def stop_all_reminders(self):
        """停止所有提醒"""
        for name in list(self.active_timers.keys()):
            self.stop_reminder(name)
        logger.info("所有提醒已停止")
    
    def _trigger_reminder(self, name: str):
        """觸發提醒"""
        if name in self.reminders:
            reminder = self.reminders[name]
            messages = reminder["messages"]
            current_index = reminder["current_index"]
            
            title = reminder["title"]
            message = messages[current_index]
            
            # 更新消息索引
            reminder["current_index"] = (current_index + 1) % len(messages)
            
            self.reminder_triggered.emit(title, message)
            logger.info(f"提醒觸發: {name} - {message}")
    
    def set_reminder_interval(self, name: str, interval_minutes: int):
        """設置提醒間隔"""
        if name in self.reminders:
            self.reminders[name]["interval"] = interval_minutes
            
            # 如果提醒正在運行，重新啟動
            if name in self.active_timers:
                self.start_reminder(name)
            
            logger.info(f"提醒間隔已更新: {name} = {interval_minutes}分鐘")
    
    def get_active_reminders(self) -> list:
        """獲取活動中的提醒列表"""
        return list(self.active_timers.keys())
    
    def cleanup(self):
        """清理資源"""
        self.stop_all_reminders()
        logger.info("提醒調度器資源已清理")


class SmartNotificationManager(QObject):
    """智能通知管理器"""
    
    def __init__(self, notifier: CrossPlatformNotifier):
        super().__init__()
        self.notifier = notifier
        self.scheduler = ReminderScheduler()
        
        # 通知歷史
        self.notification_history = []
        self.max_history = 50
        
        # 免打擾模式
        self.do_not_disturb = False
        self.quiet_hours_start = None  # 時間對象
        self.quiet_hours_end = None
        
        # 連接信號
        self.scheduler.reminder_triggered.connect(self._handle_reminder)
        
        logger.info("智能通知管理器初始化完成")
    
    def show_notification(self, title: str, message: str,
                         notification_type: NotificationType = NotificationType.INFO,
                         priority: NotificationPriority = NotificationPriority.NORMAL):
        """顯示智能通知"""
        # 檢查免打擾模式
        if self._is_quiet_time() and priority != NotificationPriority.URGENT:
            logger.info(f"免打擾模式，跳過通知: {title}")
            return
        
        # 記錄通知歷史
        self._add_to_history(title, message, notification_type)
        
        # 顯示通知
        self.notifier.show_notification(title, message, notification_type)
    
    def _handle_reminder(self, title: str, message: str):
        """處理提醒通知"""
        self.show_notification(title, message, NotificationType.REMINDER)
    
    def _is_quiet_time(self) -> bool:
        """檢查是否在免打擾時間內"""
        if self.do_not_disturb:
            return True
        
        if self.quiet_hours_start and self.quiet_hours_end:
            now = datetime.now().time()
            if self.quiet_hours_start <= self.quiet_hours_end:
                return self.quiet_hours_start <= now <= self.quiet_hours_end
            else:  # 跨越午夜
                return now >= self.quiet_hours_start or now <= self.quiet_hours_end
        
        return False
    
    def _add_to_history(self, title: str, message: str, notification_type: NotificationType):
        """添加到通知歷史"""
        entry = {
            "timestamp": datetime.now(),
            "title": title,
            "message": message,
            "type": notification_type.value
        }
        
        self.notification_history.append(entry)
        
        # 限制歷史記錄數量
        if len(self.notification_history) > self.max_history:
            self.notification_history.pop(0)
    
    def set_do_not_disturb(self, enabled: bool):
        """設置免打擾模式"""
        self.do_not_disturb = enabled
        logger.info(f"免打擾模式: {'開啟' if enabled else '關閉'}")
    
    def set_quiet_hours(self, start_hour: int, start_minute: int,
                       end_hour: int, end_minute: int):
        """設置免打擾時間段"""
        from datetime import time
        self.quiet_hours_start = time(start_hour, start_minute)
        self.quiet_hours_end = time(end_hour, end_minute)
        logger.info(f"免打擾時間: {self.quiet_hours_start} - {self.quiet_hours_end}")
    
    def get_notification_history(self, limit: int = 10) -> list:
        """獲取通知歷史"""
        return self.notification_history[-limit:]
    
    def start_default_reminders(self):
        """啟動預設提醒"""
        self.scheduler.start_all_default_reminders()
    
    def stop_all_reminders(self):
        """停止所有提醒"""
        self.scheduler.stop_all_reminders()
    
    def cleanup(self):
        """清理資源"""
        self.scheduler.cleanup()
        logger.info("智能通知管理器資源已清理") 