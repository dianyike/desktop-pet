"""
配置管理模組
處理應用程序設置的保存和讀取
"""
import json
import os
from pathlib import Path
from loguru import logger


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config_path = Path(config_file)
        self.default_config = {
            'pet_size': 150,
            'reminder_interval': 30,  # 分鐘
            'reminder_enabled': False,
            'idle_enabled': True,
            'sound_enabled': True,
            'font_color': '#FFFFFF',
            'border_color': '#000000',
            'reminder_messages': [
                "該休息一下眼睛了！",
                "記得保持良好的坐姿哦～",
                "喝點水，保持水分！",
                "起來走動走動吧！",
                "深呼吸，放松一下～",
                "記得活動手腕和頸部！"
            ]
        }
        self.config = self.load_config()
    
    def load_config(self):
        """載入配置"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合並預設配置，確保所有欄位都存在
                    merged_config = self.default_config.copy()
                    merged_config.update(config)
                    logger.info(f"配置文件載入成功: {self.config_path}")
                    return merged_config
            else:
                logger.info("配置文件不存在，使用預設配置")
                return self.default_config.copy()
        except Exception as e:
            logger.error(f"載入配置文件失敗: {e}，使用預設配置")
            return self.default_config.copy()
    
    def save_config(self):
        """保存配置"""
        try:
            # 確保配置目錄存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info(f"配置文件保存成功: {self.config_path}")
            logger.debug(f"保存的配置內容: {self.config}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失敗: {e}")
            return False
    
    def get(self, key, default=None):
        """獲取配置值"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """設置配置值"""
        self.config[key] = value
    
    def update(self, updates):
        """批量更新配置"""
        self.config.update(updates)
    
    def reset_to_default(self):
        """重置為預設配置"""
        self.config = self.default_config.copy()
        logger.info("配置已重置為預設值")


# 全局配置管理器實例
config_manager = ConfigManager() 