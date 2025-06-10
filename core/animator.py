"""
桌面寵物動畫控制器
負責管理動畫播放、狀態切換和動畫效果
"""
from PySide6.QtGui import QMovie
from PySide6.QtCore import QSize, QObject, Signal
import os
from enum import Enum
from loguru import logger


class AnimationState(Enum):
    """動畫狀態枚舉"""
    IDLE = "idle"          # 閒置狀態（原rest）
    MOVE = "move"          # 移動狀態（原drag）
    CLICK = "click"        # 點擊狀態
    EAT = "eat"            # 餵食狀態
    SLEEPY = "sleepy"      # 打哈欠狀態
    SLEEP = "sleep"        # 睡覺狀態


class AnimationController(QObject):
    """動畫控制器類"""
    
    # 信號定義
    animation_changed = Signal(str)  # 動畫切換信號
    animation_finished = Signal()    # 動畫完成信號
    
    def __init__(self, assets_path="assets"):
        super().__init__()
        self.assets_path = assets_path
        self.current_state = AnimationState.IDLE
        self.movies = {}  # 存儲所有動畫對象
        self.current_movie = None
        self.default_size = QSize(150, 150)
        
        self._load_animations()
        
    def _load_animations(self):
        """載入所有動畫文件"""
        animation_files = {
            AnimationState.IDLE: "idle.gif",
            AnimationState.MOVE: "move.gif", 
            AnimationState.CLICK: "dance.gif",  # 使用dance.gif作為點擊動畫
            AnimationState.EAT: "eat.gif",
            AnimationState.SLEEPY: "sleepy.gif",
            AnimationState.SLEEP: "sleep.gif"
        }
        
        for state, filename in animation_files.items():
            file_path = os.path.join(self.assets_path, filename)
            if os.path.exists(file_path):
                movie = QMovie(file_path)
                movie.setScaledSize(self.default_size)
                self.movies[state] = movie
                logger.info(f"載入動畫: {filename}")
            else:
                logger.warning(f"動畫文件不存在: {file_path}")
    
    def set_animation_size(self, size: QSize):
        """設置動畫尺寸"""
        self.default_size = size
        for movie in self.movies.values():
            movie.setScaledSize(size)
            
    def switch_to_state(self, state: AnimationState):
        """切換到指定動畫狀態"""
        if state == self.current_state:
            return
            
        if state in self.movies:
            # 停止當前動畫
            if self.current_movie:
                self.current_movie.stop()
                
            # 切換到新動畫
            self.current_state = state
            self.current_movie = self.movies[state]
            
            # 發送信號
            self.animation_changed.emit(state.value)
            logger.info(f"切換到動畫狀態: {state.value}")
        else:
            logger.error(f"動畫狀態不存在: {state}")
    
    def get_current_movie(self):
        """獲取當前動畫對象"""
        return self.current_movie
    
    def start_animation(self):
        """開始播放當前動畫"""
        if self.current_movie:
            self.current_movie.start()
            
    def stop_animation(self):
        """停止當前動畫"""
        if self.current_movie:
            self.current_movie.stop()
            
    def pause_animation(self):
        """暫停當前動畫"""
        if self.current_movie:
            self.current_movie.setPaused(True)
            
    def resume_animation(self):
        """恢復動畫播放"""
        if self.current_movie:
            self.current_movie.setPaused(False)
    
    def set_animation_speed(self, speed: float):
        """設置動畫播放速度 (1.0為正常速度)"""
        if self.current_movie:
            # PySide6中通過設置frame延遲來控制速度
            original_speed = self.current_movie.speed()
            self.current_movie.setSpeed(int(original_speed * speed))
    
    def get_available_states(self):
        """獲取可用的動畫狀態列表"""
        return list(self.movies.keys())
    
    def is_animation_running(self):
        """檢查動畫是否正在運行"""
        if self.current_movie:
            return self.current_movie.state() == QMovie.State.Running
        return False
    
    def cleanup(self):
        """清理資源"""
        for movie in self.movies.values():
            movie.stop()
        self.movies.clear()
        logger.info("動畫控制器資源已清理")
