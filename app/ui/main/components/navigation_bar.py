"""
导航栏组件 - 负责页面切换和导航
优化为纯 macOS 设计系统风格，移除所有内联样式
"""

from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QFrame, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize


class NavigationButton(QPushButton):
    """导航按钮 - 使用 QSS 类名，支持 macOS 风格"""

    def __init__(self, text: str, icon: str = ""):
        super().__init__()
        self.text = text
        self.icon = icon
        self.is_selected = False

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """设置UI - 仅配置结构，样式由QSS管理"""
        # 设置文本
        if self.icon:
            self.setText(f"{self.icon} {self.text}")
        else:
            self.setText(self.text)

        # 设置大小策略
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(32)  # macOS 导航项标准高度

        # 应用 macOS 样式类
        self.setProperty("class", "nav-item")

        # 启用悬停检测
        self.setAttribute(Qt.WA_Hover, True)

        # 设置鼠标指针
        self.setCursor(Qt.PointingHandCursor)

    def _connect_signals(self) -> None:
        """连接信号"""
        self.pressed.connect(self._on_pressed)
        self.released.connect(self._on_released)

    def _on_pressed(self) -> None:
        """按下事件 - 视觉反馈"""
        self.setProperty("pressed", True)
        self.style().unpolish(self)
        self.style().polish(self)

    def _on_released(self) -> None:
        """释放事件 - 恢复状态"""
        self.setProperty("pressed", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_selected(self, selected: bool) -> None:
        """设置选中状态"""
        if self.is_selected != selected:
            self.is_selected = selected
            if selected:
                self.setProperty("class", "nav-item active")
                self.setCheckable(True)
                self.setChecked(True)
            else:
                self.setProperty("class", "nav-item")
                self.setCheckable(False)
                self.setChecked(False)

            # 刷新样式
            self.style().unpolish(self)
            self.style().polish(self)
            self.update()


@dataclass
class NavigationItem:
    """导航项"""
    id: str
    text: str
    icon: str = ""
    tooltip: str = ""
    enabled: bool = True


class NavigationBar(QWidget):
    """导航栏组件 - macOS 风格"""

    # 信号定义
    page_changed = pyqtSignal(str)  # 页面ID

    def __init__(self, parent=None):
        super().__init__(parent)
        self.buttons = {}
        self.navigation_items = []
        self.current_page_id = None

        self._setup_ui()
        self._setup_layout()

    def _setup_ui(self) -> None:
        """设置UI - macOS 样式"""
        # 设置为导航栏样式
        self.setProperty("class", "nav-sidebar")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(52)  # macOS 顶部栏标准高度

        # 启用样式背景
        self.setAttribute(Qt.WA_StyledBackground, True)

    def _setup_layout(self) -> None:
        """设置布局"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(16)

        # 左侧：Logo和标题
        left_layout = self._create_left_section()
        layout.addLayout(left_layout)

        # 中间：导航按钮
        self.navigation_layout = QHBoxLayout()
        self.navigation_layout.setSpacing(4)
        layout.addLayout(self.navigation_layout)
        layout.addStretch()

        # 右侧：用户信息（简化）
        right_layout = self._create_right_section()
        layout.addLayout(right_layout)

    def _create_left_section(self) -> QHBoxLayout:
        """创建左侧区域 - 应用 macOS 样式"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Logo
        logo_label = QLabel("🎬")
        logo_label.setProperty("class", "app-icon")
        layout.addWidget(logo_label)

        # 标题
        title_label = QLabel("ClipFlowCut")
        title_label.setProperty("class", "app-title")
        layout.addWidget(title_label)

        return layout

    def _create_right_section(self) -> QHBoxLayout:
        """创建右侧区域 - 移除内联样式"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 用户信息标签
        user_label = QLabel("👤 用户")
        user_label.setProperty("class", "nav-user")
        layout.addWidget(user_label)

        # 设置按钮
        settings_btn = QPushButton("⚙️")
        settings_btn.setFixedSize(28, 28)
        settings_btn.setProperty("class", "nav-icon-button")
        settings_btn.setToolTip("设置")
        layout.addWidget(settings_btn)

        return layout

    def add_navigation_item(self, item: NavigationItem) -> None:
        """添加导航项"""
        self.navigation_items.append(item)

        # 创建导航按钮 - 传递父级样式
        button = NavigationButton(item.text, item.icon)
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


# 预定义的导航项
def create_default_navigation_items() -> List[NavigationItem]:
    """创建默认导航项 - 简化版：首页、项目管理、设置"""
    return [
        NavigationItem(
            id="home",
            text="首页",
            icon="🏠",
            tooltip="返回首页"
        ),
        NavigationItem(
            id="projects",
            text="项目管理",
            icon="📁",
            tooltip="项目管理"
        ),
        NavigationItem(
            id="settings",
            text="设置",
            icon="⚙️",
            tooltip="应用设置"
        )
    ]


def create_navigation_bar(items: List[NavigationItem] = None) -> NavigationBar:
    """创建导航栏"""
    nav_bar = NavigationBar()

    if items is None:
        items = create_default_navigation_items()

    for item in items:
        nav_bar.add_navigation_item(item)

    return nav_bar
