#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
现代化导航栏
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QFrame,
    QLabel,
    QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPainter, QColor


class ModernNavigationBar(QWidget):
    """
    现代化侧边导航栏

    特点:
    - 玻璃拟态效果
    - 渐变激活状态
    - 平滑过渡动画
    - 可折叠
    """

    nav_item_clicked = pyqtSignal(str)  # 导航项点击信号

    def __init__(
        self,
        items: list = None,
        parent: QWidget = None,
        width: int = 240,
        collapsible: bool = False,
    ):
        super().__init__(parent)
        self.items = items or [
            {"id": "home", "text": "首页", "icon": "🏠"},
            {"id": "projects", "text": "项目", "icon": "📁"},
            {"id": "ai", "text": "AI 生成", "icon": "🤖"},
            {"id": "editor", "text": "编辑器", "icon": "✏️"},
            {"id": "export", "text": "导出", "icon": "📤"},
            {"id": "settings", "text": "设置", "icon": "⚙️"},
        ]
        self.nav_width = width
        self.collapsible = collapsible
        self.collapsed = False
        self.active_item_id = "home"

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Logo区域
        self.logo_area = QWidget()
        self.logo_area.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 212, 255, 0.1),
                    stop:1 rgba(139, 92, 246, 0.1));
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        """)

        logo_layout = QHBoxLayout()
        logo_layout.setContentsMargins(20, 20, 20, 20)
        self.logo_area.setLayout(logo_layout)

        logo_label = QLabel("CineFlow")
        logo_label.setStyleSheet("""
            font-size: 24px;
            font-weight: 700;
            background: transparent;
        """)
        logo_layout.addWidget(logo_label)

        if self.collapsible:
            self.collapse_btn = QPushButton("◀")
            self.collapse_btn.setFixedSize(24, 24)
            self.collapse_btn.clicked.connect(self._toggle_collapse)
            logo_layout.addStretch()
            logo_layout.addWidget(self.collapse_btn)

        layout.addWidget(self.logo_area)

        # 导航菜单区域
        self.nav_menu = QWidget()
        nav_layout = QVBoxLayout()
        nav_layout.setContentsMargins(12, 16, 12, 16)
        nav_layout.setSpacing(4)
        self.nav_menu.setLayout(nav_layout)

        # 创建导航项
        self.nav_items = {}
        for item in self.items:
            btn = self._create_nav_item(item)
            self.nav_items[item["id"]] = btn
            nav_layout.addWidget(btn)

        layout.addWidget(self.nav_menu)

        # 底部区域
        self.bottom_area = QWidget()
        self.bottom_area.setStyleSheet("""
            background: rgba(0, 0, 0, 0.2);
            border-top: 1px solid rgba(255, 255, 255, 0.08);
        """)

        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(20, 12, 20, 12)
        self.bottom_area.setLayout(bottom_layout)

        # 用户头像（简化）
        user_label = QLabel("👤")
        user_label.setStyleSheet("""
            font-size: 24px;
            background: transparent;
        """)
        bottom_layout.addWidget(user_label)

        layout.addWidget(self.bottom_area)

        layout.addStretch()

    def _create_nav_item(self, item: dict) -> QPushButton:
        """创建导航项"""
        btn = QPushButton(f"{item['icon']}  {item['text']}")
        btn.setProperty("nav_id", item["id"])
        btn.setProperty("is_nav_item", True)

        btn.setCursor(Qt.CursorShape.PointingHandCard)
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #9CA3AF;
                border: none;
                border-radius: 8px;
                padding: 10px 12px;
                text-align: left;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.05);
                color: #D1D5DB;
            }
            QPushButton[active="true"] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 212, 255, 0.2),
                    stop:1 rgba(139, 92, 246, 0.2));
                color: #F9FAFB;
            }
        """)

        btn.clicked.connect(lambda: self._on_item_clicked(item["id"]))

        return btn

    def _apply_style(self):
        """应用样式"""
        self.setFixedWidth(self.nav_width)
        self.setStyleSheet("""
            ModernNavigationBar {
                background: rgba(10, 14, 20, 0.95);
                border-right: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)

    def _on_item_clicked(self, item_id: str):
        """导航项点击事件"""
        self.set_active_item(item_id)
        self.nav_item_clicked.emit(item_id)

    def set_active_item(self, item_id: str):
        """设置激活项"""
        self.active_item_id = item_id

        for id_text, btn in self.nav_items.items():
            if id_text == item_id:
                btn.setProperty("active", "true")
            else:
                btn.setProperty("active", "")

            # 重新应用样式
            # PyQt6需要手动刷新
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _toggle_collapse(self):
        """切换折叠状态"""
        self.collapsed = not self.collapsed

        if self.collapsed:
            self.setFixedWidth(64)
            self.collapse_btn.setText("▶")
            # 隐藏文本，只显示图标
            for btn in self.nav_items.values():
                btn.setText(btn.text().split()[0])  # 只保留emoji
            self.logo_area.findChild(QLabel).setText("CF")
        else:
            self.setFixedWidth(self.nav_width)
            self.collapse_btn.setText("◀")
            # 显示完整文本
            for item, btn in zip(self.items, self.nav_items.values()):
                btn.setText(f"{item['icon']}  {item['text']}")
            self.logo_area.findChild(QLabel).setText("CineFlow")


class ModernTopBar(QWidget):
    """
    现代化顶部栏

    用于显示页面标题、搜索、操作按钮等
    """

    def __init__(self, title: str = "", parent: QWidget = None):
        super().__init__(parent)
        self.page_title = title
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)
        self.setLayout(layout)

        # 标题
        self.title_label = QLabel(self.page_title)
        self.title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: 600;
            color: #F9FAFB;
        """)
        layout.addWidget(self.title_label)

        layout.addStretch()

        # 右侧操作区（可添加）
        pass

    def set_title(self, title: str):
        """设置标题"""
        self.title_label.setText(title)


class ModernStatusBar(QWidget):
    """
    现代化状态栏

    显示状态信息、提示等
    """

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setSpacing(16)
        self.setLayout(layout)

        # 左侧状态
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("""
            font-size: 12px;
            color: #9CA3AF;
        """)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # 右侧信息（版本等）
        version_label = QLabel("CineFlow v3.0")
        version_label.setStyleSheet("""
            font-size: 12px;
            color: #6B7280;
        """)
        layout.addWidget(version_label)

    def set_status(self, text: str):
        """设置状态文本"""
        self.status_label.setText(text)
