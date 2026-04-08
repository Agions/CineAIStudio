#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Narrafiilm 主窗口 — 薄壳架构
只负责导航路由，不处理具体页面逻辑
"""

import os

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QStatusBar, QFrame, QLabel, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ...core.application import Application
from ...core.logger import Logger


class NarrafiilmWindow(QMainWindow):
    """
    Narrafiilm 主窗口

    架构：薄壳设计
    - 左侧导航（80px）：Logo + 导航图标
    - 右侧内容区：页面堆叠，由页面自己管理
    """

    status_updated = Signal(str)

    def __init__(self, application: Application):
        super().__init__()
        self.application = application
        self.logger = application.get_service_by_name("logger") or Logger("NarrafiilmWindow")

        self.setWindowTitle("Narrafiilm — AI First-Person Video Narrator")
        self.resize(1280, 800)
        self.setMinimumSize(900, 600)

        # 加载品牌 QSS
        qss_path = os.path.join(os.path.dirname(__file__), "../theme/narrafiilm.qss")
        if os.path.exists(qss_path):
            self.setStyleSheet(open(qss_path).read())

        self._pages = {}
        self._current_page = None

        self._init_ui()
        self._load_pages()
        self._navigate_to("creator")
        self.logger.info("Narrafiilm 主窗口初始化完成")

    # ====================================================================
    # UI 初始化
    # ====================================================================

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧导航
        self.left_panel = QFrame()
        self.left_panel.setObjectName("left_panel")
        self.left_panel.setFixedWidth(80)
        self._build_nav()
        main_layout.addWidget(self.left_panel)

        # 右侧页面堆叠
        self.page_stack = QStackedWidget()
        main_layout.addWidget(self.page_stack, 1)

        # 状态栏
        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(26)
        self.status_bar.setStyleSheet("color: #3A5070; font-size: 11px;")
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def _build_nav(self):
        """构建左侧导航"""
        layout = QVBoxLayout(self.left_panel)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(8)

        # Logo
        logo_container = QWidget()
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(2)

        logo_icon = QLabel("🎬")
        logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_icon.setStyleSheet("font-size: 26px; padding: 4px;")
        logo_layout.addWidget(logo_icon)

        logo_text = QLabel("NARR")
        logo_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_text.setStyleSheet(
            "color: #0A84FF; font-size: 9px; font-weight: 800; letter-spacing: 0.15em;"
        )
        logo_layout.addWidget(logo_text)

        layout.addWidget(logo_container)
        layout.addSpacing(24)

        # 导航按钮
        self.nav_buttons = {}

        nav_items = [
            ("creator", "🏠", "创作台"),
            ("settings", "⚙️", "设置"),
        ]

        for page_id, icon, tip in nav_items:
            btn = QPushButton(icon)
            btn.setObjectName("nav_icon_btn")
            btn.setFixedSize(48, 48)
            btn.setToolTip(tip)
            btn.setCheckable(True)
            btn.setStyleSheet(self._nav_btn_style())
            btn.clicked.connect(lambda _, p=page_id: self._navigate_to(p))
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
            self.nav_buttons[page_id] = btn

        layout.addStretch()

        # 版本
        ver = QLabel("v3.2")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet("color: #2A3A50; font-size: 10px; font-weight: 600;")
        layout.addWidget(ver, alignment=Qt.AlignmentFlag.AlignCenter)

    @staticmethod
    def _nav_btn_style() -> str:
        return (
            "QPushButton { background: transparent; border: none; border-radius: 12px; "
            "font-size: 20px; padding: 0px; } "
            "QPushButton:hover { background: #111827; } "
            "QPushButton:checked { background: #0F1D32; }"
        )

    # ====================================================================
    # 页面加载
    # ====================================================================

    def _load_pages(self):
        """惰性加载所有页面"""
        # 创作台页
        from .pages.creation_wizard_page import CreationWizardPage
        creator = CreationWizardPage("creator", "创作台", self.application)
        creator.create_content()
        creator.page_activated.connect(self._on_page_activated)
        self.page_stack.addWidget(creator)
        self._pages["creator"] = creator

        # 设置页
        from .pages.settings_page import SettingsPage
        settings = SettingsPage("settings", "设置", self.application)
        settings.create_content()
        settings.page_activated.connect(self._on_page_activated)
        self.page_stack.addWidget(settings)
        self._pages["settings"] = settings

    def _navigate_to(self, page_id: str):
        """导航到指定页面"""
        if page_id not in self._pages:
            return

        # 更新按钮状态
        for pid, btn in self.nav_buttons.items():
            btn.setChecked(pid == page_id)

        # 切换页面
        page = self._pages[page_id]
        self.page_stack.setCurrentWidget(page)
        page.activate()
        self._current_page = page_id

    def _on_page_activated(self):
        """页面激活回调"""
        pass

    # ====================================================================
    # 状态栏
    # ====================================================================

    def show_status(self, msg: str):
        self.status_bar.showMessage(msg)


# 别名：兼容旧代码
MainWindow = NarrafiilmWindow

