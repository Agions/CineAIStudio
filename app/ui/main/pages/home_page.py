#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineFlow AI 首页 - 模板选择式设计
简洁、美观、以创作流程为核心
"""

from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QScrollArea, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QCursor

from .base_page import BasePage


class TemplateCard(QFrame):
    """模板卡片"""
    clicked = pyqtSignal(str)  # template_id

    def __init__(self, template_id: str, icon: str, title: str,
                 description: str, parent=None):
        super().__init__(parent)
        self._template_id = template_id
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedSize(220, 180)
        self.setObjectName("templateCard")
        self.setStyleSheet("""
            #templateCard {
                background: #1E1E1E;
                border: 1px solid #333;
                border-radius: 12px;
                padding: 20px;
            }
            #templateCard:hover {
                background: #252525;
                border-color: #2962FF;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(8)

        # 图标
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("", 36))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(icon_label)

        layout.addSpacerItem(QSpacerItem(0, 8, QSizePolicy.Policy.Minimum,
                                          QSizePolicy.Policy.Fixed))

        # 标题
        title_label = QLabel(title)
        title_label.setFont(QFont("", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title_label)

        # 描述
        desc_label = QLabel(description)
        desc_label.setFont(QFont("", 12))
        desc_label.setStyleSheet("color: #888;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addStretch()

    def mousePressEvent(self, event):
        self.clicked.emit(self._template_id)
        super().mousePressEvent(event)


class RecentProjectItem(QFrame):
    """最近项目条目"""
    clicked = pyqtSignal(str)

    def __init__(self, name: str, path: str, date: str = "", parent=None):
        super().__init__(parent)
        self._path = path
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(48)
        self.setStyleSheet("""
            QFrame {
                background: transparent;
                border-radius: 8px;
                padding: 4px 12px;
            }
            QFrame:hover {
                background: #1E1E1E;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(12)

        icon = QLabel("📄")
        icon.setFont(QFont("", 16))
        layout.addWidget(icon)

        name_label = QLabel(name)
        name_label.setStyleSheet("color: #DDD; font-size: 14px;")
        layout.addWidget(name_label)

        layout.addStretch()

        if date:
            date_label = QLabel(date)
            date_label.setStyleSheet("color: #666; font-size: 12px;")
            layout.addWidget(date_label)

    def mousePressEvent(self, event):
        self.clicked.emit(self._path)
        super().mousePressEvent(event)


class HomePage(BasePage):
    """首页 - 模板选择式设计"""

    # 信号
    template_selected = pyqtSignal(str)   # template_id
    project_opened = pyqtSignal(str)      # project_path

    TEMPLATES = [
        ("movie_commentary", "🎬", "电影解说",
         "AI 分析画面 → 生成解说 → 配音"),
        ("music_mashup", "🎵", "音乐混剪",
         "多段素材 → 节拍匹配 → 转场"),
        ("emotional_monologue", "🎭", "情感独白",
         "画面情感 → 第一人称独白"),
        ("short_drama_clip", "📺", "短剧切片",
         "识别高能片段 → 切片字幕"),
        ("product_promo", "🛍️", "产品推广",
         "卖点提取 → 推广文案配音"),
        ("custom", "➕", "自定义",
         "从零开始，自由创作"),
    ]

    def __init__(self, application):
        super().__init__("home", "首页", application)
        self.logger = application.get_service(type(application.logger))

    def initialize(self) -> bool:
        try:
            self.logger.info("初始化首页页面")
            return True
        except Exception as e:
            self.logger.error(f"初始化首页失败: {e}")
            return False

    def create_content(self) -> None:
        """创建首页内容"""
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: #121212; }")

        content = QWidget()
        content.setStyleSheet("background: #121212;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(48, 40, 48, 40)
        layout.setSpacing(0)

        # ── 标题区 ──
        header = self._create_header()
        layout.addWidget(header)
        layout.addSpacing(32)

        # ── 模板网格 ──
        templates_label = QLabel("选择创作模板")
        templates_label.setFont(QFont("", 14, QFont.Weight.Bold))
        templates_label.setStyleSheet("color: #888; margin-bottom: 4px;")
        layout.addWidget(templates_label)
        layout.addSpacing(16)

        grid = self._create_template_grid()
        layout.addLayout(grid)
        layout.addSpacing(40)

        # ── 分隔线 ──
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #333;")
        layout.addWidget(line)
        layout.addSpacing(24)

        # ── 最近项目 ──
        recent_section = self._create_recent_section()
        layout.addWidget(recent_section)

        layout.addStretch()

        scroll.setWidget(content)
        self.main_layout.addWidget(scroll)

    def _create_header(self) -> QWidget:
        """标题区"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel("🎬 CineFlow AI")
        title.setFont(QFont("", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)

        subtitle = QLabel("选一个模板，开始你的创作")
        subtitle.setFont(QFont("", 16))
        subtitle.setStyleSheet("color: #888;")
        layout.addWidget(subtitle)

        return widget

    def _create_template_grid(self) -> QGridLayout:
        """模板卡片网格"""
        grid = QGridLayout()
        grid.setSpacing(16)

        for i, (tid, icon, title, desc) in enumerate(self.TEMPLATES):
            card = TemplateCard(tid, icon, title, desc)
            card.clicked.connect(self._on_template_clicked)
            row = i // 3
            col = i % 3
            grid.addWidget(card, row, col)

        return grid

    def _create_recent_section(self) -> QWidget:
        """最近项目区"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        header_row = QHBoxLayout()
        label = QLabel("最近项目")
        label.setFont(QFont("", 14, QFont.Weight.Bold))
        label.setStyleSheet("color: #888;")
        header_row.addWidget(label)
        header_row.addStretch()

        # 查看全部按钮
        view_all = QLabel("查看全部 →")
        view_all.setStyleSheet("color: #2962FF; font-size: 13px;")
        view_all.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        header_row.addWidget(view_all)
        layout.addLayout(header_row)

        # 最近项目列表
        recent = self._get_recent_projects()
        if recent:
            for name, path, date in recent[:5]:
                item = RecentProjectItem(name, path, date)
                item.clicked.connect(self._on_open_recent)
                layout.addWidget(item)
        else:
            empty = QLabel("还没有项目，选个模板开始吧 ✨")
            empty.setStyleSheet("color: #555; font-size: 14px; padding: 20px 0;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty)

        return widget

    def _get_recent_projects(self) -> List:
        """获取最近项目"""
        try:
            config_manager = self.application.get_service_by_name("config_manager")
            if config_manager:
                files = config_manager.get_value("recent_files", [])
                if files:
                    from pathlib import Path
                    return [
                        (Path(f).stem, f, "")
                        for f in files[:5]
                        if isinstance(f, str)
                    ]
        except Exception:
            pass
        return []

    def _on_template_clicked(self, template_id: str):
        """模板点击处理"""
        self.logger.info(f"选择模板: {template_id}")
        self.template_selected.emit(template_id)

        # 切换到 AI 视频创作页面
        if hasattr(self, 'application'):
            main_window = self.application.get_service_by_name("main_window")
            if main_window and hasattr(main_window, 'switch_to_page'):
                from app.ui.main.main_window import PageType
                main_window.switch_to_page(PageType.AI_VIDEO_CREATOR)

    def _on_open_recent(self, path: str):
        """打开最近项目"""
        self.project_opened.emit(path)

    def on_activated(self) -> None:
        """页面激活"""
        pass

    def on_deactivated(self) -> None:
        """页面停用"""
        pass
