"""
桌面寵物核心模組
包含動畫控制、事件處理和核心控制器
"""

from .animator import AnimationController, AnimationState
from .events import EventHandler, EventType
from .controller import PetController

__all__ = [
    'AnimationController',
    'AnimationState', 
    'EventHandler',
    'EventType',
    'PetController'
] 