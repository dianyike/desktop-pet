"""
桌面寵物事件處理器
負責處理鼠標、鍵盤和系統事件
"""
from PySide6.QtCore import QObject, Signal, QTimer, QPoint, Qt
from PySide6.QtGui import QMouseEvent, QKeyEvent
from enum import Enum
from loguru import logger
import time


class EventType(Enum):
    """事件類型枚舉"""
    MOUSE_CLICK = "mouse_click"
    MOUSE_DRAG = "mouse_drag"
    MOUSE_RELEASE = "mouse_release"
    MOUSE_ENTER = "mouse_enter"
    MOUSE_LEAVE = "mouse_leave"
    KEY_PRESS = "key_press"
    TIMER_EXPIRED = "timer_expired"
    SYSTEM_IDLE = "system_idle"


class EventHandler(QObject):
    """事件處理器類"""
    
    # 信號定義
    click_detected = Signal(QPoint)      # 點擊事件
    drag_started = Signal(QPoint)        # 拖拽開始
    drag_moved = Signal(QPoint)          # 拖拽移動
    drag_finished = Signal(QPoint)       # 拖拽結束
    double_click = Signal(QPoint)        # 雙擊事件
    right_click = Signal(QPoint)         # 右鍵點擊
    hover_enter = Signal()               # 鼠標懸停進入
    hover_leave = Signal()               # 鼠標懸停離開
    idle_timeout = Signal()              # 閒置超時
    
    def __init__(self):
        super().__init__()
        
        # 拖拽狀態
        self.is_dragging = False
        self.drag_start_position = None
        self.last_position = None
        
        # 點擊檢測
        self.click_threshold = 5  # 像素閾值
        self.double_click_threshold = 300  # 毫秒
        self.last_click_time = 0
        self.last_click_position = None
        
        # 閒置檢測
        self.idle_timer = QTimer()
        self.idle_timer.timeout.connect(self._on_idle_timeout)
        self.idle_timeout_ms = 30000  # 30秒無操作視為閒置
        self.last_activity_time = time.time()
        
        # 懸停檢測
        self.hover_timer = QTimer()
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self._on_hover_timeout)
        self.hover_delay = 500  # 懸停延遲毫秒
        
        logger.info("事件處理器初始化完成")
    
    def handle_mouse_press(self, event: QMouseEvent):
        """處理鼠標按下事件"""
        position = event.globalPosition().toPoint()
        current_time = time.time() * 1000  # 轉換為毫秒
        
        self._update_activity()
        
        if event.button() == Qt.MouseButton.LeftButton:
            # 檢測雙擊
            if (self.last_click_position and 
                self._distance(position, self.last_click_position) < self.click_threshold and
                current_time - self.last_click_time < self.double_click_threshold):
                
                self.double_click.emit(position)
                logger.info(f"雙擊檢測: {position}")
                return
            
            # 記錄點擊信息
            self.last_click_time = current_time
            self.last_click_position = position
            
            # 準備拖拽
            self.drag_start_position = position
            self.last_position = position
            
            self.click_detected.emit(position)
            logger.debug(f"左鍵點擊: {position}")
            
        elif event.button() == Qt.MouseButton.RightButton:
            self.right_click.emit(position)
            logger.info(f"右鍵點擊: {position}")
    
    def handle_mouse_move(self, event: QMouseEvent):
        """處理鼠標移動事件"""
        if not self.drag_start_position:
            return
            
        current_position = event.globalPosition().toPoint()
        self._update_activity()
        
        # 檢查是否開始拖拽
        if not self.is_dragging:
            distance = self._distance(current_position, self.drag_start_position)
            if distance > self.click_threshold:
                self.is_dragging = True
                self.drag_started.emit(self.drag_start_position)
                logger.info(f"拖拽開始: {self.drag_start_position}")
        
        # 拖拽中
        if self.is_dragging:
            self.drag_moved.emit(current_position)
            self.last_position = current_position
            logger.debug(f"拖拽移動: {current_position}")
    
    def handle_mouse_release(self, event: QMouseEvent):
        """處理鼠標釋放事件"""
        if self.is_dragging:
            position = event.globalPosition().toPoint()
            self.drag_finished.emit(position)
            logger.info(f"拖拽結束: {position}")
        
        # 重置拖拽狀態
        self.is_dragging = False
        self.drag_start_position = None
        self.last_position = None
        
        self._update_activity()
    
    def handle_enter_event(self):
        """處理鼠標進入事件"""
        self.hover_timer.start(self.hover_delay)
        self._update_activity()
        logger.debug("鼠標進入區域")
    
    def handle_leave_event(self):
        """處理鼠標離開事件"""
        self.hover_timer.stop()
        self.hover_leave.emit()
        self._update_activity()
        logger.debug("鼠標離開區域")
    
    def _on_hover_timeout(self):
        """懸停超時回調"""
        self.hover_enter.emit()
        logger.info("鼠標懸停檢測")
    
    def handle_key_press(self, event: QKeyEvent):
        """處理鍵盤按鍵事件"""
        key = event.key()
        modifiers = event.modifiers()
        
        self._update_activity()
        
        # 這裡可以根據需要處理特定按鍵
        logger.debug(f"按鍵事件: key={key}, modifiers={modifiers}")
    
    def _distance(self, point1: QPoint, point2: QPoint) -> float:
        """計算兩點間距離"""
        dx = point1.x() - point2.x()
        dy = point1.y() - point2.y()
        return (dx * dx + dy * dy) ** 0.5
    
    def _update_activity(self):
        """更新最後活動時間"""
        self.last_activity_time = time.time()
        
        # 重啟閒置計時器
        if self.idle_timer.isActive():
            self.idle_timer.stop()
        self.idle_timer.start(self.idle_timeout_ms)
    
    def _on_idle_timeout(self):
        """閒置超時回調"""
        self.idle_timeout.emit()
        logger.info("檢測到用戶閒置")
    
    def set_idle_timeout(self, timeout_ms: int):
        """設置閒置超時時間"""
        self.idle_timeout_ms = timeout_ms
        
    def set_click_threshold(self, threshold: int):
        """設置點擊檢測閾值"""
        self.click_threshold = threshold
        
    def set_double_click_threshold(self, threshold: int):
        """設置雙擊檢測閾值"""
        self.double_click_threshold = threshold
    
    def start_idle_detection(self):
        """開始閒置檢測"""
        self.idle_timer.start(self.idle_timeout_ms)
        logger.info("閒置檢測已啟動")
        
    def stop_idle_detection(self):
        """停止閒置檢測"""
        self.idle_timer.stop()
        logger.info("閒置檢測已停止")
    
    def cleanup(self):
        """清理資源"""
        self.idle_timer.stop()
        self.hover_timer.stop()
        logger.info("事件處理器資源已清理")
