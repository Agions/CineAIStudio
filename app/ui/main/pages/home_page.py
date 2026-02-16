#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineFlow 首页 - macOS 设计系统优化版
使用标准化组件，零内联样式
"""

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon

from .base_page import BasePage
from app.core.icon_manager import get_icon
from app.ui.common.macOS_components import (
    MacCard, MacElevatedCard, MacPrimaryButton, MacSecondaryButton,
    MacIconButton, MacTitleLabel, MacLabel, MacBadge, MacStatLabel,
    MacPageToolbar, MacGrid, MacScrollArea, MacEmptyState,
    create_icon_text_row, create_status_badge_row
)
from app.ui.main.components.quick_ai_config import QuickAIConfigWidget


class HomePage(BasePage):
    """首页页面 - 使用 macOS 设计系统"""

    def __init__(self, application):
        super().__init__("home", "首页", application)
        self.logger = application.get_service(type(application.logger))
        self._setup_refresh_timer()

    def initialize(self) -> bool:
        """初始化页面"""
        try:
            self.logger.info("初始化首页页面")
            return True
        except Exception as e:
            self.logger.error(f"初始化首页失败: {e}")
            return False

    def create_content(self) -> None:
        """创建页面内容 - 使用标准化组件"""
        # 设置页面边距和间距
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 创建滚动容器
        scroll_area = MacScrollArea()
        scroll_content = QWidget()
        scroll_content.setProperty("class", "page-content")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(32, 24, 32, 32)
        scroll_layout.setSpacing(20)

        # 1. 页面工具栏
        toolbar = MacPageToolbar("👋 欢迎使用 CineFlow")
        scroll_layout.addWidget(toolbar)

        # 2. 欢迎卡片
        welcome_card = self._create_welcome_card()
        scroll_layout.addWidget(welcome_card)

        # 3. 内容区域网格（支持响应式）
        content_grid = MacGrid(columns=2, gap=16)

        # 快捷操作卡片
        quick_actions = self._create_quick_actions_card()
        content_grid.add_widget(quick_actions)

        # AI 配置卡片
        ai_config = self._create_ai_config_card()
        content_grid.add_widget(ai_config)

        # 状态卡片
        status_card = self._create_status_card()
        content_grid.add_widget(status_card)

        # 最近项目卡片
        projects_card = self._create_recent_projects_card()
        content_grid.add_widget(projects_card)

        scroll_layout.addWidget(content_grid)
        scroll_layout.addStretch()

        # 设置滚动内容
        scroll_area.setWidget(scroll_content)
        self.main_layout.addWidget(scroll_area)

    def _create_welcome_card(self) -> MacCard:
        """创建欢迎卡片"""
        card = MacElevatedCard()

        # 标题行
        title_row = create_icon_text_row("🌟", "欢迎使用 CineFlow", "title-2xl")
        card.layout().addWidget(title_row)

        # 欢迎文案
        desc = MacLabel(
            "这是一个专业的AI视频编辑器，集成了最新的人工智能技术。 workflows, 提供智能剪辑、画质增强、音频处理等功能。",
            "text-base text-muted"
        )
        desc.setWordWrap(True)
        card.layout().addWidget(desc)

        # 快速开始按钮
        quick_start_layout = QHBoxLayout()
        quick_start_layout.addStretch()

        btn_new = MacPrimaryButton("✨ 新建项目")
        btn_new.clicked.connect(self._on_new_project)
        quick_start_layout.addWidget(btn_new)

        btn_import = MacSecondaryButton("📁 导入素材")
        btn_import.clicked.connect(self._on_open_project)
        quick_start_layout.addWidget(btn_import)

        quick_start_widget = QWidget()
        quick_start_widget.setLayout(quick_start_layout)
        card.layout().addWidget(quick_start_widget)

        return card

    def _create_quick_actions_card(self) -> MacCard:
        """创建快捷操作卡片"""
        card = MacCard()
        card.setProperty("class", "card section-card")

        # 标题
        title = MacTitleLabel("快捷操作", 5)
        card.layout().addWidget(title)

        # 按钮网格
        actions = [
            ("新建项目", "new", self._on_new_project, "✨", "primary"),
            ("打开项目", "open", self._on_open_project, "📂", "secondary"),
            ("AI增强", "ai_enhance", self._on_ai_enhance, "🤖", "primary"),
            ("智能剪辑", "ai_magic", self._on_smart_cut, "✂️", "secondary"),
            ("项目管理", "projects", self._on_projects, "📋", "secondary"),
            ("设置", "settings", self._on_settings, "⚙️", "secondary"),
        ]

        button_grid = QGridLayout()
        button_grid.setSpacing(8)
        button_grid.setContentsMargins(0, 8, 0, 0)

        for i, (text, icon_name, handler, icon, variant) in enumerate(actions):
            row = i // 2
            col = i % 2

            try:
                qicon = get_icon(icon_name, 24)
            except:
                qicon = QIcon()

            if variant == "primary":
                btn = MacPrimaryButton(f"  {text}", qicon)
            else:
                btn = MacSecondaryButton(f"  {text}", qicon)

            btn.setProperty("class", f"button button-{variant} action-btn")
            btn.setMinimumHeight(36)
            btn.setMinimumWidth(140)
            btn.clicked.connect(handler)
            btn.setToolTip(actions[i][3])

            button_grid.addWidget(btn, row, col)

        card.layout().addLayout(button_grid)
        return card

    def _create_ai_config_card(self) -> MacCard:
        """创建AI配置卡片"""
        # 使用现有的 AI 配置组件，包装以符合新样式
        card = MacCard()

        title = MacTitleLabel("⚡ AI 快捷配置", 5)
        card.layout().addWidget(title)

        # 包装现有组件
        self.ai_config_component = QuickAIConfigWidget(self)
        self.ai_config_component.setProperty("class", "ai-config-wrapper")

        card.layout().addWidget(self.ai_config_component)
        return card

    def _create_status_card(self) -> MacCard:
        """创建状态卡片"""
        card = MacCard()

        title = MacTitleLabel("📊 系统状态", 5)
        card.layout().addWidget(title)

        # 状态信息 - 使用统计标签
        status_items = [
            ("AI服务", "🟢 在线", "success"),
            ("存储空间", "💾 充足", "success"),
            ("内存使用", "📊 正常", "primary"),
            ("主题", "🌙 深色模式", "primary"),
        ]

        for label, value, style in status_items:
            # 创建带徽章的行
            row = QWidget()
            row.setProperty("class", "stat-row")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 4, 0, 4)
            row_layout.setSpacing(8)

            # 标签
            label_widget = QLabel(f"{label}:")
            label_widget.setProperty("class", "text-secondary text-bold")
            row_layout.addWidget(label_widget)

            # 徽章或值
            if style in ["success", "primary", "warning", "error"]:
                badge_text = value.split(" ")[-1] if " " in value else value
                badge = MacBadge(badge_text, style)
                badge.setMinimumWidth(80)
                row_layout.addWidget(badge)
            else:
                value_widget = QLabel(value)
                value_widget.setProperty("class", "text-base")
                row_layout.addWidget(value_widget)

            row_layout.addStretch()
            card.layout().addWidget(row)

        return card

    def _create_recent_projects_card(self) -> MacCard:
        """创建最近项目卡片"""
        card = MacCard()

        title = MacTitleLabel("📁 最近项目", 5)
        card.layout().addWidget(title)

        recent_projects = self._get_recent_projects()

        if recent_projects:
            for project in recent_projects[:5]:
                btn = MacSecondaryButton(f"📄 {project}")
                btn.setProperty("class", "button secondary project-item")
                btn.setMinimumHeight(32)
                btn.clicked.connect(lambda checked, p=project: self._on_open_recent_project(p))
                card.layout().addWidget(btn)
        else:
            empty = MacEmptyState(
                icon="📭",
                title="暂无项目",
                description="开始创建您的第一个AI视频编辑项目吧！"
            )
            card.layout().addWidget(empty)

        return card

    def _setup_refresh_timer(self):
        """设置定时刷新"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_status)
        self.refresh_timer.start(30000)

    def _refresh_status(self):
        """刷新状态"""
        try:
            self.logger.debug("刷新状态信息")
        except Exception as e:
            self.logger.error(f"刷新状态失败: {e}")

    def _get_recent_projects(self) -> list:
        """获取最近项目"""
        try:
            config_manager = self.application.get_service_by_name("config_manager")
            if config_manager:
                return config_manager.get_value("recent_files", [])
            return []
        except Exception as e:
            self.logger.error(f"获取最近项目失败: {e}")
            return []

    # 事件处理
    def _on_new_project(self):
        self.logger.info("新建项目")
        from ..main_window import PageType
        main_window = self.window()
        if hasattr(main_window, 'switch_to_page'):
            main_window.switch_to_page(PageType.VIDEO_EDITOR)

    def _on_open_project(self):
        self.logger.info("打开项目")
        from ..main_window import PageType
        main_window = self.window()
        if hasattr(main_window, 'switch_to_page'):
            main_window.switch_to_page(PageType.VIDEO_EDITOR)

    def _on_ai_enhance(self):
        self.logger.info("AI视频增强")
        from ..main_window import PageType
        main_window = self.window()
        if hasattr(main_window, 'switch_to_page'):
            main_window.switch_to_page(PageType.VIDEO_EDITOR)

    def _on_smart_cut(self):
        self.logger.info("智能剪辑")
        from ..main_window import PageType
        main_window = self.window()
        if hasattr(main_window, 'switch_to_page'):
            main_window.switch_to_page(PageType.VIDEO_EDITOR)

    def _on_projects(self):
        self.logger.info("打开项目管理")
        from ..main_window import PageType
        main_window = self.window()
        if hasattr(main_window, 'switch_to_page'):
            main_window.switch_to_page(PageType.PROJECTS)

    def _on_settings(self):
        self.logger.info("打开设置")
        from ..main_window import PageType
        main_window = self.window()
        if hasattr(main_window, 'switch_to_page'):
            main_window.switch_to_page(PageType.SETTINGS)

    def _on_open_recent_project(self, project_path: str):
        self.logger.info(f"打开最近项目: {project_path}")
        # 模拟打开项目
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "打开项目", f"正在打开项目: {project_path}")

    def refresh(self):
        """刷新页面"""
        self._refresh_status()

    def get_page_type(self) -> str:
        return "home"
