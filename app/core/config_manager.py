#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单配置管理器
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """简化配置管理器"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(
            os.path.expanduser("~"), ".cineai-studio", "config.json"
        )
        self._config: Dict[str, Any] = self._load_default_config()
        self._ensure_config_dir()
        self.load()

    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            "window": {
                "width": 1200,
                "height": 800,
                "x": 100,
                "y": 100,
                "maximized": False,
                "fullscreen": False
            },
            "theme": {
                "name": "dark_modern",
                "mode": "dark",
                "primary_color": "#2196F3",
                "font_size": 12
            },
            "editor": {
                "auto_save": True,
                "auto_save_interval": 300,
                "backup_enabled": True,
                "recent_files": []
            },
            "ai": {
                "default_model": "openai",
                "max_tokens": 2000,
                "temperature": 0.7
            }
        }

    def _ensure_config_dir(self) -> None:
        """确保配置目录存在"""
        config_dir = Path(self.config_path).parent
        config_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> None:
        """加载配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self._config.update(loaded_config)
            except (json.JSONDecodeError, IOError):
                pass

    def save(self) -> None:
        """保存配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except IOError:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def get_value(self, key: str, default: Any = None) -> Any:
        """获取配置值（别名）"""
        return self.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()

    def reset(self) -> None:
        """重置为默认配置"""
        self._config = self._load_default_config()
        self.save()

    def set_value(self, key: str, value: Any) -> None:
        """设置配置值（别名）"""
        self.set(key, value)

    def add_watcher(self, callback) -> None:
        """添加配置变更监听器（简化版）"""
        # 简化实现，不实现真正的监听功能
        pass

    def get_settings(self) -> Dict[str, Any]:
        """获取所有设置（别名）"""
        return self.get_all()

    def update_settings(self, settings: Dict[str, Any]) -> None:
        """更新设置（别名）"""
        self._config.update(settings)
        self.save()