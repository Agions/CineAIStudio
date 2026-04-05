"""
Narrafiilm UI 模块

提供 PySide6 图形界面组件
"""

from .main.main_window import NarrafiilmWindow
from .main.main_window import NarrafiilmWindow as MainWindow

__all__ = [
    "MainWindow",
    "NarrafiilmWindow",
]
