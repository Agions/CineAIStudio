#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlow 图标管理器
提供统一的图标加载和管理功能
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize


class IconManager:
    """图标管理器"""

    def __init__(self, icon_dir: Optional[str] = None):
        self.icon_dir = Path(icon_dir or "resources/icons")
        self._icon_cache: Dict[str, QIcon] = {}
        self._current_theme = "light"

    def get_icon(self, icon_name: str, size: int = 24, theme: Optional[str] = None) -> QIcon:
        """获取图标"""
        if theme is None:
            theme = self._current_theme

        cache_key = f"{icon_name}_{size}_{theme}"
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]

        icon = self._load_icon(icon_name, size, theme)
        self._icon_cache[cache_key] = icon
        return icon

    def _load_icon(self, icon_name: str, size: int, theme: str) -> QIcon:
        """加载图标"""
        # 检查QApplication是否存在
        from PyQt6.QtWidgets import QApplication
        if not QApplication.instance():
            # 如果QApplication不存在，返回一个空图标
            return QIcon()

        # 尝试按主题加载
        if theme != "light":
            themed_path = self.icon_dir / theme / str(size) / f"{icon_name}.png"
            if themed_path.exists():
                return QIcon(str(themed_path))

        # 默认路径
        default_path = self.icon_dir / str(size) / f"{icon_name}.png"
        if default_path.exists():
            return QIcon(str(default_path))

        # 尝试其他尺寸
        for alt_size in [32, 48, 64, 24, 16]:
            alt_path = self.icon_dir / str(alt_size) / f"{icon_name}.png"
            if alt_path.exists():
                icon = QIcon(str(alt_path))
                # 调整尺寸
                return self._resize_icon(icon, QSize(size, size))

        # 返回空图标
        return QIcon()

    def _resize_icon(self, icon: QIcon, size: QSize) -> QIcon:
        """调整图标尺寸"""
        # 创建新图标并添加调整尺寸后的pixmap
        new_icon = QIcon()
        for mode in [QIcon.Mode.Normal, QIcon.Mode.Disabled, QIcon.Mode.Active, QIcon.Mode.Selected]:
            for state in [QIcon.State.On, QIcon.State.Off]:
                pixmap = icon.pixmap(size, mode, state)
                new_icon.addPixmap(pixmap, mode, state)
        return new_icon

    def get_multi_size_icon(self, icon_name: str, theme: Optional[str] = None) -> QIcon:
        """获取多尺寸图标"""
        if theme is None:
            theme = self._current_theme

        cache_key = f"{icon_name}_multi_{theme}"
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]

        icon = QIcon()
        sizes = [16, 24, 32, 48, 64, 128, 256]

        for size in sizes:
            size_icon = self.get_icon(icon_name, size, theme)
            if not size_icon.isNull():
                pixmap = size_icon.pixmap(QSize(size, size))
                icon.addPixmap(pixmap)

        self._icon_cache[cache_key] = icon
        return icon

    def set_theme(self, theme: str):
        """设置主题"""
        if theme in ["light", "dark", "high_contrast"]:
            self._current_theme = theme
            self._icon_cache.clear()  # 清除缓存

    def get_available_icons(self) -> Dict[str, Any]:
        """获取可用图标列表"""
        icons = {}

        # 扫描图标目录
        for size_dir in self.icon_dir.iterdir():
            if size_dir.is_dir() and size_dir.name.isdigit():
                size = int(size_dir.name)
                icons[size] = []

                for icon_file in size_dir.glob("*.png"):
                    icons[size].append(icon_file.stem)

        return icons

    def clear_cache(self):
        """清除图标缓存"""
        self._icon_cache.clear()

    def get_app_icon(self) -> QIcon:
        """获取应用图标"""
        return self.get_multi_size_icon("app_icon")


# 全局图标管理器实例
_icon_manager: Optional[IconManager] = None


def get_icon_manager(icon_dir: Optional[str] = None) -> IconManager:
    """获取全局图标管理器"""
    global _icon_manager
    if _icon_manager is None:
        _icon_manager = IconManager(icon_dir)
    return _icon_manager


def init_icon_manager(icon_dir: str) -> IconManager:
    """初始化图标管理器"""
    global _icon_manager
    _icon_manager = IconManager(icon_dir)
    return _icon_manager


# 便捷函数
def get_icon(icon_name: str, size: int = 24, theme: Optional[str] = None) -> QIcon:
    """获取图标的便捷函数"""
    manager = get_icon_manager()
    return manager.get_icon(icon_name, size, theme)


def get_multi_size_icon(icon_name: str, theme: Optional[str] = None) -> QIcon:
    """获取多尺寸图标的便捷函数"""
    manager = get_icon_manager()
    return manager.get_multi_size_icon(icon_name, theme)


def set_icon_theme(theme: str):
    """设置图标主题的便捷函数"""
    manager = get_icon_manager()
    manager.set_theme(theme)