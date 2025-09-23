"""
主题管理器 - 管理应用程序主题
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPalette, QColor

from ...core.config_manager import ThemeConfig


@dataclass
class ThemeColors:
    """主题颜色"""
    primary: str = "#2196F3"
    secondary: str = "#1976D2"
    background: str = "#1E1E1E"
    surface: str = "#2D2D2D"
    card: str = "#2D2D2D"
    text: str = "#FFFFFF"
    text_secondary: str = "#CCCCCC"
    border: str = "#404040"
    divider: str = "#555555"
    error: str = "#F44336"
    warning: str = "#FF9800"
    success: str = "#4CAF50"
    info: str = "#2196F3"


class ThemeManager(QObject):
    """主题管理器"""

    # 信号定义
    theme_changed = pyqtSignal(str)  # 主题模式变更信号

    def __init__(self, theme_config: ThemeConfig):
        super().__init__()

        self.theme_config = theme_config
        self.current_mode = theme_config.mode
        self.colors = ThemeColors()

        # 更新颜色配置
        self._update_colors()

    def _update_colors(self) -> None:
        """更新颜色配置"""
        if self.current_mode == "dark":
            self.colors = ThemeColors(
                primary=self.theme_config.primary_color,
                secondary=self.theme_config.secondary_color,
                background=self.theme_config.background_color,
                surface=self.theme_config.surface_color,
                text=self.theme_config.text_color,
                border="#404040",
                divider="#555555"
            )
        else:
            self.colors = ThemeColors(
                primary=self.theme_config.primary_color,
                secondary=self.theme_config.secondary_color,
                background="#FFFFFF",
                surface="#F5F5F5",
                card="#FFFFFF",
                text="#000000",
                text_secondary="#666666",
                border="#E0E0E0",
                divider="#EEEEEE"
            )

    def set_theme_mode(self, mode: str) -> None:
        """设置主题模式"""
        if mode != self.current_mode:
            self.current_mode = mode
            self._update_colors()
            self.theme_changed.emit(mode)

    def get_theme_mode(self) -> str:
        """获取主题模式"""
        return self.current_mode

    def apply_theme(self, widget) -> None:
        """应用主题到窗口部件"""
        stylesheet = self.get_stylesheet()
        widget.setStyleSheet(stylesheet)

    def get_stylesheet(self) -> str:
        """获取样式表"""
        if self.current_mode == "dark":
            return self._get_dark_stylesheet()
        else:
            return self._get_light_stylesheet()

    def _get_dark_stylesheet(self) -> str:
        """获取深色主题样式表"""
        return f"""
        /* 全局样式 */
        * {{
            color: {self.colors.text};
            background-color: transparent;
        }}

        /* 主窗口 */
        QMainWindow {{
            background-color: {self.colors.background};
            color: {self.colors.text};
        }}

        /* 中央窗口部件 */
        QWidget#central_widget {{
            background-color: {self.colors.background};
        }}

        /* 按钮样式 */
        QPushButton {{
            background-color: {self.colors.primary};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
        }}

        QPushButton:hover {{
            background-color: {self.colors.secondary};
        }}

        QPushButton:pressed {{
            background-color: {self.colors.secondary};
        }}

        QPushButton:disabled {{
            background-color: {self.colors.border};
            color: {self.colors.text_secondary};
        }}

        /* 输入框样式 */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {self.colors.surface};
            color: {self.colors.text};
            border: 1px solid {self.colors.border};
            border-radius: 4px;
            padding: 8px;
        }}

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 1px solid {self.colors.primary};
        }}

        /* 标签样式 */
        QLabel {{
            color: {self.colors.text};
        }}

        /* 菜单栏样式 */
        QMenuBar {{
            background-color: {self.colors.surface};
            color: {self.colors.text};
            border-bottom: 1px solid {self.colors.border};
        }}

        QMenuBar::item:selected {{
            background-color: {self.colors.primary};
        }}

        /* 菜单样式 */
        QMenu {{
            background-color: {self.colors.surface};
            color: {self.colors.text};
            border: 1px solid {self.colors.border};
        }}

        QMenu::item:selected {{
            background-color: {self.colors.primary};
        }}

        /* 工具栏样式 */
        QToolBar {{
            background-color: {self.colors.surface};
            color: {self.colors.text};
            border: 1px solid {self.colors.border};
            spacing: 4px;
        }}

        /* 状态栏样式 */
        QStatusBar {{
            background-color: {self.colors.surface};
            color: {self.colors.text};
            border-top: 1px solid {self.colors.border};
        }}

        /* 滚动条样式 */
        QScrollBar:vertical {{
            background-color: {self.colors.surface};
            width: 12px;
            border: none;
        }}

        QScrollBar::handle:vertical {{
            background-color: {self.colors.border};
            border-radius: 6px;
            min-height: 20px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {self.colors.primary};
        }}

        QScrollBar:horizontal {{
            background-color: {self.colors.surface};
            height: 12px;
            border: none;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {self.colors.border};
            border-radius: 6px;
            min-width: 20px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {self.colors.primary};
        }}

        /* 分割器样式 */
        QSplitter::handle {{
            background-color: {self.colors.border};
        }}

        QSplitter::handle:horizontal {{
            width: 2px;
        }}

        QSplitter::handle:vertical {{
            height: 2px;
        }}

        /* 选项卡样式 */
        QTabWidget::pane {{
            border: 1px solid {self.colors.border};
            background-color: {self.colors.background};
        }}

        QTabBar::tab {{
            background-color: {self.colors.surface};
            color: {self.colors.text};
            padding: 8px 16px;
            border: 1px solid {self.colors.border};
            margin-right: 2px;
        }}

        QTabBar::tab:selected {{
            background-color: {self.colors.primary};
            color: white;
        }}

        /* 列表样式 */
        QListWidget {{
            background-color: {self.colors.surface};
            color: {self.colors.text};
            border: 1px solid {self.colors.border};
            outline: none;
        }}

        QListWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {self.colors.divider};
        }}

        QListWidget::item:selected {{
            background-color: {self.colors.primary};
            color: white;
        }}

        /* 树形视图样式 */
        QTreeWidget {{
            background-color: {self.colors.surface};
            color: {self.colors.text};
            border: 1px solid {self.colors.border};
            outline: none;
        }}

        QTreeWidget::item:selected {{
            background-color: {self.colors.primary};
            color: white;
        }}

        /* 表格样式 */
        QTableWidget {{
            background-color: {self.colors.surface};
            color: {self.colors.text};
            border: 1px solid {self.colors.border};
            gridline-color: {self.colors.divider};
            outline: none;
        }}

        QTableWidget::item:selected {{
            background-color: {self.colors.primary};
            color: white;
        }}

        QHeaderView::section {{
            background-color: {self.colors.card};
            color: {self.colors.text};
            padding: 8px;
            border: 1px solid {self.colors.border};
            font-weight: bold;
        }}

        /* 进度条样式 */
        QProgressBar {{
            background-color: {self.colors.surface};
            color: white;
            border: 1px solid {self.colors.border};
            border-radius: 4px;
            text-align: center;
        }}

        QProgressBar::chunk {{
            background-color: {self.colors.primary};
            border-radius: 3px;
        }}

        /* 滑块样式 */
        QSlider::groove:horizontal {{
            background-color: {self.colors.border};
            height: 6px;
            border-radius: 3px;
        }}

        QSlider::handle:horizontal {{
            background-color: {self.colors.primary};
            border: 2px solid white;
            border-radius: 8px;
            width: 16px;
            height: 16px;
            margin: -5px 0;
        }}

        /* 复选框样式 */
        QCheckBox {{
            color: {self.colors.text};
            spacing: 8px;
        }}

        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {self.colors.border};
            border-radius: 3px;
            background-color: {self.colors.surface};
        }}

        QCheckBox::indicator:checked {{
            background-color: {self.colors.primary};
            border-color: {self.colors.primary};
        }}

        /* 单选按钮样式 */
        QRadioButton {{
            color: {self.colors.text};
            spacing: 8px;
        }}

        QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {self.colors.border};
            border-radius: 9px;
            background-color: {self.colors.surface};
        }}

        QRadioButton::indicator:checked {{
            background-color: {self.colors.primary};
            border-color: {self.colors.primary};
        }}

        /* 组合框样式 */
        QComboBox {{
            background-color: {self.colors.surface};
            color: {self.colors.text};
            border: 1px solid {self.colors.border};
            border-radius: 4px;
            padding: 6px;
            min-width: 100px;
        }}

        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}

        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {self.colors.text};
        }}

        /* 工具提示样式 */
        QToolTip {{
            background-color: {self.colors.card};
            color: {self.colors.text};
            border: 1px solid {self.colors.border};
            padding: 4px;
            border-radius: 4px;
        }}

        /* 对话框样式 */
        QDialog {{
            background-color: {self.colors.background};
            color: {self.colors.text};
        }}

        QMessageBox {{
            background-color: {self.colors.background};
            color: {self.colors.text};
        }}
        """

    def _get_light_stylesheet(self) -> str:
        """获取浅色主题样式表"""
        return f"""
        /* 全局样式 */
        * {{
            color: {self.colors.text};
            background-color: transparent;
        }}

        /* 主窗口 */
        QMainWindow {{
            background-color: {self.colors.background};
            color: {self.colors.text};
        }}

        /* 中央窗口部件 */
        QWidget#central_widget {{
            background-color: {self.colors.background};
        }}

        /* 按钮样式 */
        QPushButton {{
            background-color: {self.colors.primary};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
        }}

        QPushButton:hover {{
            background-color: {self.colors.secondary};
        }}

        QPushButton:pressed {{
            background-color: {self.colors.secondary};
        }}

        QPushButton:disabled {{
            background-color: {self.colors.border};
            color: {self.colors.text_secondary};
        }}

        /* 输入框样式 */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: white;
            color: {self.colors.text};
            border: 1px solid {self.colors.border};
            border-radius: 4px;
            padding: 8px;
        }}

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 1px solid {self.colors.primary};
        }}

        /* 标签样式 */
        QLabel {{
            color: {self.colors.text};
        }}

        /* 菜单栏样式 */
        QMenuBar {{
            background-color: {self.colors.surface};
            color: {self.colors.text};
            border-bottom: 1px solid {self.colors.border};
        }}

        QMenuBar::item:selected {{
            background-color: {self.colors.primary};
        }}

        /* 菜单样式 */
        QMenu {{
            background-color: {self.colors.surface};
            color: {self.colors.text};
            border: 1px solid {self.colors.border};
        }}

        QMenu::item:selected {{
            background-color: {self.colors.primary};
        }}

        /* 工具栏样式 */
        QToolBar {{
            background-color: {self.colors.surface};
            color: {self.colors.text};
            border: 1px solid {self.colors.border};
            spacing: 4px;
        }}

        /* 状态栏样式 */
        QStatusBar {{
            background-color: {self.colors.surface};
            color: {self.colors.text};
            border-top: 1px solid {self.colors.border};
        }}

        /* 滚动条样式 */
        QScrollBar:vertical {{
            background-color: {self.colors.surface};
            width: 12px;
            border: none;
        }}

        QScrollBar::handle:vertical {{
            background-color: {self.colors.border};
            border-radius: 6px;
            min-height: 20px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {self.colors.primary};
        }}

        QScrollBar:horizontal {{
            background-color: {self.colors.surface};
            height: 12px;
            border: none;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {self.colors.border};
            border-radius: 6px;
            min-width: 20px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {self.colors.primary};
        }}

        /* 分割器样式 */
        QSplitter::handle {{
            background-color: {self.colors.border};
        }}

        QSplitter::handle:horizontal {{
            width: 2px;
        }}

        QSplitter::handle:vertical {{
            height: 2px;
        }}

        /* 选项卡样式 */
        QTabWidget::pane {{
            border: 1px solid {self.colors.border};
            background-color: {self.colors.background};
        }}

        QTabBar::tab {{
            background-color: {self.colors.surface};
            color: {self.colors.text};
            padding: 8px 16px;
            border: 1px solid {self.colors.border};
            margin-right: 2px;
        }}

        QTabBar::tab:selected {{
            background-color: {self.colors.primary};
            color: white;
        }}

        /* 列表样式 */
        QListWidget {{
            background-color: white;
            color: {self.colors.text};
            border: 1px solid {self.colors.border};
            outline: none;
        }}

        QListWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {self.colors.divider};
        }}

        QListWidget::item:selected {{
            background-color: {self.colors.primary};
            color: white;
        }}

        /* 工具提示样式 */
        QToolTip {{
            background-color: {self.colors.card};
            color: {self.colors.text};
            border: 1px solid {self.colors.border};
            padding: 4px;
            border-radius: 4px;
        }}
        """

    def get_colors(self) -> ThemeColors:
        """获取主题颜色"""
        return self.colors

    def set_color(self, color_type: str, color: str) -> None:
        """设置主题颜色"""
        if hasattr(self.colors, color_type):
            setattr(self.colors, color_type, color)

    def get_color(self, color_type: str) -> str:
        """获取主题颜色"""
        return getattr(self.colors, color_type, "#000000")