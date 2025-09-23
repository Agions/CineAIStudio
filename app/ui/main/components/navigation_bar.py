"""
导航栏组件 - 负责页面切换和导航
"""

from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QFrame, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QPalette


class NavigationButtonStyle:
    """导航按钮样式"""

    def __init__(self):
        self.normal_bg = QColor(45, 45, 45)
        self.hover_bg = QColor(60, 60, 60)
        self.selected_bg = QColor(33, 150, 243)
        self.normal_text = QColor(200, 200, 200)
        self.hover_text = QColor(255, 255, 255)
        self.selected_text = QColor(255, 255, 255)
        self.border_radius = 8
        self.padding = 12
        self.font_size = 14
        self.font_weight = QFont.Weight.Normal


class NavigationButton(QPushButton):
    """导航按钮"""

    def __init__(self, text: str, icon: str = "", style: NavigationButtonStyle = None):
        super().__init__()

        self.text = text
        self.icon = icon
        self.style = style or NavigationButtonStyle()
        self.is_selected = False

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """设置UI"""
        # 设置文本
        if self.icon:
            self.setText(f"{self.icon} {self.text}")
        else:
            self.setText(self.text)

        # 设置字体
        font = QFont("Microsoft YaHei", self.style.font_size)
        font.setWeight(self.style.font_weight)
        self.setFont(font)

        # 设置大小策略
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(50)

        # 设置初始样式
        self._update_style()

    def _connect_signals(self) -> None:
        """连接信号"""
        self.pressed.connect(self._on_pressed)
        self.released.connect(self._on_released)

    def _update_style(self) -> None:
        """更新样式"""
        if self.is_selected:
            bg_color = self.style.selected_bg
            text_color = self.style.selected_text
            font_weight = QFont.Weight.Bold
        else:
            bg_color = self.style.normal_bg
            text_color = self.style.normal_text
            font_weight = QFont.Weight.Normal

        stylesheet = f"""
            QPushButton {{
                background-color: {bg_color.name()};
                color: {text_color.name()};
                border: none;
                border-radius: {self.style.border_radius}px;
                padding: {self.style.padding}px;
                font-weight: {font_weight};
            }}
            QPushButton:hover {{
                background-color: {self.style.hover_bg.name()};
                color: {self.style.hover_text.name()};
            }}
            QPushButton:pressed {{
                background-color: {self.style.selected_bg.name()};
            }}
        """

        self.setStyleSheet(stylesheet)

    def set_selected(self, selected: bool) -> None:
        """设置选中状态"""
        if self.is_selected != selected:
            self.is_selected = selected
            self._update_style()

    def _on_pressed(self) -> None:
        """按下事件"""
        self._update_style()

    def _on_released(self) -> None:
        """释放事件"""
        self._update_style()


@dataclass
class NavigationItem:
    """导航项"""
    id: str
    text: str
    icon: str = ""
    tooltip: str = ""
    enabled: bool = True


class NavigationBar(QWidget):
    """导航栏组件"""

    # 信号定义
    page_changed = pyqtSignal(str)  # 页面ID

    def __init__(self, style: NavigationButtonStyle = None):
        super().__init__()

        self.style = style or NavigationButtonStyle()
        self.buttons = {}
        self.navigation_items = []
        self.current_page_id = None

        self._setup_ui()
        self._setup_layout()

    def _setup_ui(self) -> None:
        """设置UI"""
        # 设置窗口部件属性
        self.setObjectName("navigation_bar")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(60)

        # 设置背景色
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        self.setPalette(palette)

    def _setup_layout(self) -> None:
        """设置布局"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)

        # 左侧：Logo和标题
        left_layout = self._create_left_section()
        layout.addLayout(left_layout)

        # 中间：导航按钮
        self.navigation_layout = QHBoxLayout()
        self.navigation_layout.setSpacing(10)
        layout.addLayout(self.navigation_layout)
        layout.addStretch()

        # 右侧：用户信息
        right_layout = self._create_right_section()
        layout.addLayout(right_layout)

    def _create_left_section(self) -> QHBoxLayout:
        """创建左侧区域"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Logo
        logo_label = QLabel("🎬")
        logo_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(logo_label)

        # 标题
        title_label = QLabel("CineAIStudio")
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title_label)

        return layout

    def _create_right_section(self) -> QHBoxLayout:
        """创建右侧区域"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 用户信息
        user_label = QLabel("👤 用户")
        user_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-size: 14px;
            }
        """)
        layout.addWidget(user_label)

        # 设置按钮
        settings_btn = QPushButton("⚙️")
        settings_btn.setFixedSize(30, 30)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #CCCCCC;
                border: none;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: #FFFFFF;
            }
        """)
        settings_btn.setToolTip("设置")
        layout.addWidget(settings_btn)

        return layout

    def add_navigation_item(self, item: NavigationItem) -> None:
        """添加导航项"""
        self.navigation_items.append(item)

        # 创建导航按钮
        button = NavigationButton(item.text, item.icon, self.style)
        button.setEnabled(item.enabled)
        if item.tooltip:
            button.setToolTip(item.tooltip)

        # 连接点击事件
        button.clicked.connect(lambda checked=False, page_id=item.id: self._on_navigation_clicked(page_id))

        # 添加到布局
        self.navigation_layout.addWidget(button)
        self.buttons[item.id] = button

        # 如果是第一个按钮，默认选中
        if len(self.buttons) == 1:
            self.set_current_page(item.id)

    def remove_navigation_item(self, item_id: str) -> None:
        """移除导航项"""
        if item_id in self.buttons:
            button = self.buttons[item_id]
            self.navigation_layout.removeWidget(button)
            button.deleteLater()
            del self.buttons[item_id]

            # 从导航项列表中移除
            self.navigation_items = [item for item in self.navigation_items if item.id != item_id]

            # 如果删除的是当前页面，切换到第一个页面
            if self.current_page_id == item_id and self.navigation_items:
                self.set_current_page(self.navigation_items[0].id)

    def set_current_page(self, page_id: str) -> None:
        """设置当前页面"""
        if page_id == self.current_page_id:
            return

        # 更新按钮状态
        for item_id, button in self.buttons.items():
            button.set_selected(item_id == page_id)

        self.current_page_id = page_id

    def get_current_page(self) -> Optional[str]:
        """获取当前页面"""
        return self.current_page_id

    def set_item_enabled(self, item_id: str, enabled: bool) -> None:
        """设置导航项启用状态"""
        if item_id in self.buttons:
            self.buttons[item_id].setEnabled(enabled)

        # 更新导航项
        for item in self.navigation_items:
            if item.id == item_id:
                item.enabled = enabled
                break

    def get_navigation_items(self) -> List[NavigationItem]:
        """获取所有导航项"""
        return self.navigation_items.copy()

    def _on_navigation_clicked(self, page_id: str) -> None:
        """导航点击处理"""
        self.set_current_page(page_id)
        self.page_changed.emit(page_id)

    def set_style(self, style: NavigationButtonStyle) -> None:
        """设置按钮样式"""
        self.style = style
        for button in self.buttons.values():
            button.style = style
            button._update_style()

    def update_theme(self, is_dark: bool = True) -> None:
        """更新主题"""
        if is_dark:
            bg_color = QColor(30, 30, 30)
            text_color = QColor(255, 255, 255)
        else:
            bg_color = QColor(245, 245, 245)
            text_color = QColor(33, 33, 33)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, bg_color)
        self.setPalette(palette)

        # 更新标题颜色
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if isinstance(item.widget(), QLabel) and item.widget().text() == "CineAIStudio":
                item.widget().setStyleSheet(f"color: {text_color.name()}; font-size: 18px; font-weight: bold;")


# 预定义的导航项
def create_default_navigation_items() -> List[NavigationItem]:
    """创建默认导航项"""
    return [
        NavigationItem(
            id="video_editor",
            text="视频编辑",
            icon="🎬",
            tooltip="专业的视频编辑功能"
        ),
        NavigationItem(
            id="ai_chat",
            text="AI对话",
            icon="🤖",
            tooltip="AI助手对话"
        )
    ]


def create_navigation_bar(items: List[NavigationItem] = None,
                         style: NavigationButtonStyle = None) -> NavigationBar:
    """创建导航栏"""
    nav_bar = NavigationBar(style)

    if items is None:
        items = create_default_navigation_items()

    for item in items:
        nav_bar.add_navigation_item(item)

    return nav_bar