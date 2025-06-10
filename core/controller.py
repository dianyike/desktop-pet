"""
桌面寵物核心控制器
整合所有模組功能，作為應用程序的中央協調器
"""
from PySide6.QtCore import QObject, Signal, QTimer, QPoint
from PySide6.QtWidgets import QApplication
from .animator import AnimationController, AnimationState
from .events import EventHandler
from utils.config import config_manager
from loguru import logger
import pygame
import os


class PetController(QObject):
    """桌面寵物核心控制器"""
    
    # 狀態變化信號
    state_changed = Signal(str)
    notification_triggered = Signal(str)
    reminder_message = Signal(str)  # 提醒消息信號
    feeding_finished = Signal()     # 餵食完成信號
    
    def __init__(self, assets_path="assets"):
        super().__init__()
        
        self.assets_path = assets_path
        
        # 初始化子模組
        self.animation_controller = AnimationController(assets_path)
        self.event_handler = EventHandler()
        
        # 音效初始化
        self._init_audio()
        
        # 雙擊計數和餵食狀態
        self.click_count = 0
        self.click_reset_timer = QTimer()
        self.click_reset_timer.setSingleShot(True)
        self.click_reset_timer.timeout.connect(self._reset_click_count)
        self.is_feeding = False
        
        # 睡眠機制定時器
        self.sleepy_timer = QTimer()
        self.sleepy_timer.setSingleShot(True)
        self.sleepy_timer.timeout.connect(self._start_sleepy)
        
        self.sleep_timer = QTimer()
        self.sleep_timer.setSingleShot(True)
        self.sleep_timer.timeout.connect(self._start_sleep)
        
        # 從配置載入設置
        self._load_settings()
        
        # 定時提醒
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self._on_reminder)
        self.current_reminder_index = 0
        
        # 狀態管理
        self.current_state = AnimationState.IDLE
        self.is_interaction_mode = False
        
        # 連接事件信號
        self._connect_signals()
        
        # 啟動初始動畫和睡眠計時
        self.animation_controller.switch_to_state(AnimationState.IDLE)
        self.animation_controller.start_animation()
        self._start_sleep_timers()
        
        logger.info("桌面寵物控制器初始化完成")
    
    def _init_audio(self):
        """初始化音效系統"""
        try:
            pygame.mixer.init()
            self.sound_effects = {}
            
            # 載入音效文件
            meow_sound_path = os.path.join(self.assets_path, "meow.wav")
            if os.path.exists(meow_sound_path):
                self.sound_effects['meow'] = pygame.mixer.Sound(meow_sound_path)
                logger.info("meow音效載入成功")
            else:
                logger.warning(f"音效文件不存在: {meow_sound_path}")
                
        except Exception as e:
            logger.error(f"音效初始化失敗: {e}")
            self.sound_effects = {}
    
    def _connect_signals(self):
        """連接各模組的信號"""
        # 事件處理器信號連接
        self.event_handler.click_detected.connect(self._on_click)
        self.event_handler.drag_started.connect(self._on_drag_start)
        self.event_handler.drag_moved.connect(self._on_drag_move)
        self.event_handler.drag_finished.connect(self._on_drag_finish)
        self.event_handler.double_click.connect(self._on_double_click)
        self.event_handler.right_click.connect(self._on_right_click)
        self.event_handler.hover_enter.connect(self._on_hover_enter)
        self.event_handler.hover_leave.connect(self._on_hover_leave)
        self.event_handler.idle_timeout.connect(self._on_idle)
        
        # 動畫控制器信號連接
        self.animation_controller.animation_changed.connect(self._on_animation_changed)
    
    def _on_click(self, position: QPoint):
        """處理點擊事件"""
        logger.info(f"寵物被點擊: {position}")
        
        # 重置睡眠定時器
        self._reset_sleep_timers()
        
        # 如果正在餵食，忽略點擊
        if self.is_feeding:
            return
        
        # 點擊計數
        self.click_count += 1
        
        # 重置點擊計數定時器
        self.click_reset_timer.stop()
        self.click_reset_timer.start(1000)  # 1秒內有效
        
        # 檢查是否雙擊
        if self.click_count >= 2:
            self._play_sound('meow')
            self._show_notification("喵～ 你點了我兩次！")
            self.click_count = 0
            self.click_reset_timer.stop()
        
        # 切換到點擊動畫
        self.animation_controller.switch_to_state(AnimationState.CLICK)
        self.animation_controller.start_animation()
        
        # 2秒後返回閒置狀態
        QTimer.singleShot(2000, lambda: self._return_to_idle())
    
    def _on_drag_start(self, position: QPoint):
        """處理拖拽開始事件"""
        logger.info(f"開始拖拽寵物: {position}")
        
        # 重置睡眠定時器
        self._reset_sleep_timers()
        
        # 切換到移動動畫
        self.animation_controller.switch_to_state(AnimationState.MOVE)
        self.animation_controller.start_animation()
        
        self.is_interaction_mode = True
    
    def _on_drag_move(self, position: QPoint):
        """處理拖拽移動事件"""
        # 這裡主要由主視窗處理位置更新
        pass
    
    def _on_drag_finish(self, position: QPoint):
        """處理拖拽結束事件"""
        logger.info(f"拖拽結束: {position}")
        
        self.is_interaction_mode = False
        
        # 延遲返回閒置狀態並重啟睡眠計時
        QTimer.singleShot(1000, lambda: self._return_to_idle())
    
    def _on_double_click(self, position: QPoint):
        """處理雙擊事件"""
        logger.info(f"寵物被雙擊: {position}")
        
        # 雙擊觸發特殊動畫或功能
        self._show_notification("你雙擊了我！好開心～")
    
    def _on_right_click(self, position: QPoint):
        """處理右鍵點擊事件"""
        logger.info(f"右鍵點擊寵物: {position}")
        
        # 右鍵可以觸發菜單或特殊功能
        self._show_notification("右鍵功能菜單（待實現）")
    
    def _on_hover_enter(self):
        """處理鼠標懸停進入事件"""
        logger.info("鼠標懸停在寵物上")
        
        # 可以顯示一些提示信息
        pass
    
    def _on_hover_leave(self):
        """處理鼠標懸停離開事件"""
        logger.info("鼠標離開寵物")
        pass
    
    def _on_idle(self):
        """處理閒置超時事件"""
        logger.info("檢測到用戶閒置")
        
        if not self.is_interaction_mode:
            # 閒置時可以播放特殊動畫或提醒
            self._show_notification("我在這裡等你哦～")
    
    def _on_animation_changed(self, animation_name: str):
        """處理動畫變化事件"""
        logger.info(f"動畫已切換到: {animation_name}")
        self.state_changed.emit(animation_name)
    
    def _return_to_idle(self):
        """返回閒置狀態"""
        if not self.is_interaction_mode and not self.is_feeding:
            self.animation_controller.switch_to_state(AnimationState.IDLE)
            self.animation_controller.start_animation()
            self._start_sleep_timers()
    
    def _reset_click_count(self):
        """重置點擊計數"""
        self.click_count = 0
    
    def _start_sleep_timers(self):
        """啟動睡眠相關定時器"""
        if not self.is_interaction_mode and not self.is_feeding:
            self.sleepy_timer.stop()
            self.sleep_timer.stop()
            self.sleepy_timer.start(15000)  # 15秒後打哈欠
    
    def _reset_sleep_timers(self):
        """重置睡眠定時器"""
        self.sleepy_timer.stop()
        self.sleep_timer.stop()
        if not self.is_interaction_mode and not self.is_feeding:
            self._start_sleep_timers()
    
    def _start_sleepy(self):
        """開始打哈欠"""
        if not self.is_interaction_mode and not self.is_feeding:
            self.animation_controller.switch_to_state(AnimationState.SLEEPY)
            self.animation_controller.start_animation()
            # 打哈欠2秒後回到idle，然後再啟動sleep計時
            QTimer.singleShot(2000, self._return_to_idle_from_sleepy)
    
    def _return_to_idle_from_sleepy(self):
        """從打哈欠回到idle狀態"""
        if not self.is_interaction_mode and not self.is_feeding:
            self.animation_controller.switch_to_state(AnimationState.IDLE)
            self.animation_controller.start_animation()
            # 再15秒後睡覺
            self.sleep_timer.start(15000)
    
    def _start_sleep(self):
        """開始睡覺"""
        if not self.is_interaction_mode and not self.is_feeding:
            self.animation_controller.switch_to_state(AnimationState.SLEEP)
            self.animation_controller.start_animation()
    
    def feed_pet(self):
        """餵食寵物"""
        logger.info("開始餵食寵物")
        
        # 停止所有定時器
        self._reset_sleep_timers()
        
        # 設置餵食狀態
        self.is_feeding = True
        
        # 切換到餵食動畫
        self.animation_controller.switch_to_state(AnimationState.EAT)
        self.animation_controller.start_animation()
        
        # 3秒後結束餵食
        QTimer.singleShot(3000, self._finish_feeding)
        
        self._show_notification("好好吃～謝謝你的餵食！")
    
    def _finish_feeding(self):
        """結束餵食"""
        self.is_feeding = False
        self.feeding_finished.emit()
        self._return_to_idle()
        logger.info("餵食完成")
    
    def _play_sound(self, sound_name: str):
        """播放音效"""
        if not self.sound_enabled:
            return
            
        if sound_name in self.sound_effects:
            try:
                self.sound_effects[sound_name].play()
                logger.debug(f"播放音效: {sound_name}")
            except Exception as e:
                logger.error(f"播放音效失敗: {e}")
    
    def _show_notification(self, message: str):
        """顯示通知"""
        self.notification_triggered.emit(message)
        logger.info(f"通知: {message}")
    
    def _on_reminder(self):
        """定時提醒回調"""
        message = self.reminder_messages[self.current_reminder_index]
        self.current_reminder_index = (self.current_reminder_index + 1) % len(self.reminder_messages)
        
        # 發送提醒消息信號（顯示在主窗口上）
        self.reminder_message.emit(message)
        
        # 也發送系統通知
        self._show_notification(message)
        
        logger.info(f"定時提醒: {message}")
    
    def start_reminders(self):
        """開始定時提醒"""
        self.reminder_timer.start(self.reminder_interval)
        logger.info(f"定時提醒已啟動，間隔: {self.reminder_interval/1000/60}分鐘")
    
    def stop_reminders(self):
        """停止定時提醒"""
        self.reminder_timer.stop()
        logger.info("定時提醒已停止")
    
    def set_reminder_interval(self, minutes: int):
        """設置提醒間隔"""
        self.reminder_interval = minutes * 60 * 1000
        if self.reminder_timer.isActive():
            self.reminder_timer.stop()
            self.reminder_timer.start(self.reminder_interval)
        logger.info(f"提醒間隔已設置為: {minutes}分鐘")
    
    def get_current_movie(self):
        """獲取當前動畫對象"""
        return self.animation_controller.get_current_movie()
    
    def get_event_handler(self):
        """獲取事件處理器"""
        return self.event_handler
    
    def set_pet_size(self, width: int, height: int):
        """設置寵物大小"""
        from PySide6.QtCore import QSize
        size = QSize(width, height)
        self.animation_controller.set_animation_size(size)
        logger.info(f"寵物大小已設置為: {width}x{height}")
    
    def cleanup(self):
        """清理資源"""
        self.reminder_timer.stop()
        self.animation_controller.cleanup()
        self.event_handler.cleanup()
        
        # 清理音效資源
        if hasattr(pygame.mixer, 'quit'):
            pygame.mixer.quit()
            
        logger.info("控制器資源已清理")
    
    def set_sound_enabled(self, enabled: bool):
        """設置音效開關"""
        self.sound_enabled = enabled
        logger.info(f"音效{'開啟' if enabled else '關閉'}")
    
    def is_sound_enabled(self) -> bool:
        """檢查音效是否開啟"""
        return self.sound_enabled
    
    def _load_settings(self):
        """從配置載入設置"""
        self.reminder_interval = config_manager.get('reminder_interval', 30) * 60 * 1000  # 轉換為毫秒
        self.reminder_messages = config_manager.get('reminder_messages', [
            "該休息一下眼睛了！",
            "記得保持良好的坐姿哦～",
            "喝點水，保持水分！",
            "起來走動走動吧！",
            "深呼吸，放松一下～",
            "記得活動手腕和頸部！"
        ])
        self.sound_enabled = config_manager.get('sound_enabled', True)
        logger.info(f"設置已載入 - 提醒間隔: {self.reminder_interval/1000/60}分鐘, 音效: {self.sound_enabled}")
    
    def save_settings(self):
        """保存當前設置到配置文件"""
        config_manager.update({
            'reminder_interval': self.reminder_interval // (60 * 1000),  # 轉換為分鐘
            'reminder_enabled': self.reminder_timer.isActive(),
            'sound_enabled': self.sound_enabled,
            'reminder_messages': self.reminder_messages
        })
        config_manager.save_config()
        logger.info("設置已保存到配置文件")
