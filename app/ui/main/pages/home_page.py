#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlowCut 首页 - 模板选择式设计
简洁、美观、以创作流程为核心
"""

from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QScrollArea, QSizePolicy, QSpacerItem, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QCursor

from .base_page import BasePage


class TemplateCard(QFrame):
    """模板卡片 - 精美设计"""
    clicked = pyqtSignal(str)  # template_id

    def __init__(self, template_id: str, icon: str, title: str,
                 description: str, parent=None):
        super().__init__(parent)
        self._template_id = template_id
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedSize(240, 200)
        self.setObjectName("templateCard")
        self.setStyleSheet("""
            #templateCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1E1E1E, stop:1 #1A1A1A);
                border: 1px solid #333;
                border-radius: 14px;
            }
            #templateCard:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #252525, stop:1 #202020);
                border-color: #2962FF;
                border-width: 2px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(12)

        # 图标容器 - 带背景
        icon_container = QFrame()
        icon_container.setFixedSize(64, 64)
        icon_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2962FF, stop:1 #448AFF);
                border-radius: 12px;
            }
        """)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("", 32))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(icon_label)
        
        layout.addWidget(icon_container)
        layout.addSpacing(4)

        # 标题
        title_label = QLabel(title)
        title_label.setFont(QFont("", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title_label)

        # 描述
        desc_label = QLabel(description)
        desc_label.setFont(QFont("", 12))
        desc_label.setStyleSheet("color: #999; line-height: 1.4;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addStretch()
        
        # 底部提示
        hint_label = QLabel("点击开始 →")
        hint_label.setFont(QFont("", 11))
        hint_label.setStyleSheet("color: #666;")
        layout.addWidget(hint_label)

    def mousePressEvent(self, event):
        self.clicked.emit(self._template_id)
        super().mousePressEvent(event)


class RecentProjectItem(QFrame):
    """最近项目条目 - 优化设计"""
    clicked = pyqtSignal(str)

    def __init__(self, name: str, path: str, date: str = "", parent=None):
        super().__init__(parent)
        self._path = path
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(56)
        self.setStyleSheet("""
            QFrame {
                background: #1A1A1A;
                border: 1px solid #2A2A2A;
                border-radius: 10px;
                padding: 8px 16px;
            }
            QFrame:hover {
                background: #242424;
                border-color: #2962FF;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(16)

        # 图标
        icon = QLabel("📄")
        icon.setFont(QFont("", 20))
        layout.addWidget(icon)

        # 项目信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        name_label = QLabel(name)
        name_label.setFont(QFont("", 14, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #FFFFFF;")
        info_layout.addWidget(name_label)
        
        # 路径显示（简化）
        from pathlib import Path
        path_label = QLabel(str(Path(path).parent.name))
        path_label.setStyleSheet("color: #666; font-size: 12px;")
        info_layout.addWidget(path_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()

        # 日期标签
        if date:
            date_label = QLabel(date)
            date_label.setFont(QFont("", 12))
            date_label.setStyleSheet("color: #888;")
            layout.addWidget(date_label)
        
        # 箭头图标
        arrow = QLabel("→")
        arrow.setFont(QFont("", 16))
        arrow.setStyleSheet("color: #666;")
        layout.addWidget(arrow)

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
        """标题区 - 优化设计"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 主标题
        title = QLabel("欢迎使用 ClipFlowCut")
        title.setFont(QFont("", 32, QFont.Weight.Bold))
        title.setStyleSheet("""
            color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #FFFFFF, stop:1 #CCCCCC);
        """)
        layout.addWidget(title)

        # 副标题
        subtitle = QLabel("AI 驱动的专业视频创作工具")
        subtitle.setFont(QFont("", 18))
        subtitle.setStyleSheet("color: #999;")
        layout.addWidget(subtitle)
        
        # 分隔线
        layout.addSpacing(8)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 transparent, stop:0.5 #333, stop:1 transparent); max-height: 1px;")
        layout.addWidget(separator)

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
        layout.setSpacing(12)

        header_row = QHBoxLayout()
        label = QLabel("最近项目")
        label.setFont(QFont("", 16, QFont.Weight.Bold))
        label.setStyleSheet("color: #FFFFFF;")
        header_row.addWidget(label)
        header_row.addStretch()

        # 查看全部按钮
        view_all_btn = QPushButton("查看全部 →")
        view_all_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #2962FF;
                border: none;
                font-size: 14px;
                font-weight: 600;
                padding: 4px 8px;
            }
            QPushButton:hover {
                color: #448AFF;
                text-decoration: underline;
            }
        """)
        view_all_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        view_all_btn.clicked.connect(self._on_view_all_projects)
        header_row.addWidget(view_all_btn)
        layout.addLayout(header_row)

        # 最近项目列表
        recent = self._get_recent_projects()
        if recent:
            for name, path, date in recent[:5]:
                item = RecentProjectItem(name, path, date)
                item.clicked.connect(self._on_open_recent)
                layout.addWidget(item)
        else:
            # 空状态 - 更精美的设计
            empty_container = QFrame()
            empty_container.setStyleSheet("""
                QFrame {
                    background: #1A1A1A;
                    border: 2px dashed #333;
                    border-radius: 12px;
                    padding: 40px;
                }
            """)
            empty_layout = QVBoxLayout(empty_container)
            empty_layout.setSpacing(12)
            empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            empty_icon = QLabel("📂")
            empty_icon.setFont(QFont("", 48))
            empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_icon)
            
            empty_text = QLabel("还没有项目")
            empty_text.setFont(QFont("", 16, QFont.Weight.Bold))
            empty_text.setStyleSheet("color: #888;")
            empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_text)
            
            empty_hint = QLabel("选择上方的模板开始创作吧 ✨")
            empty_hint.setStyleSheet("color: #666; font-size: 14px;")
            empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(empty_hint)
            
            layout.addWidget(empty_container)

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
        self.logger.info(f"打开最近项目: {path}")
        self.project_opened.emit(path)
        
        # 切换到项目编辑页面
        if hasattr(self, 'application'):
            main_window = self.application.get_service_by_name("main_window")
            if main_window and hasattr(main_window, 'switch_to_page'):
                from app.ui.main.main_window import PageType
                main_window.switch_to_page(PageType.VIDEO_EDITOR)
    
    def _on_view_all_projects(self):
        """查看全部项目"""
        self.logger.info("切换到项目管理页面")
        if hasattr(self, 'application'):
            main_window = self.application.get_service_by_name("main_window")
            if main_window and hasattr(main_window, 'switch_to_page'):
                from app.ui.main.main_window import PageType
                main_window.switch_to_page(PageType.PROJECTS)

    def on_activated(self) -> None:
        """页面激活"""
        # 刷新最近项目列表
        self._load_recent_projects()
        self._load_templates()

    def on_deactivated(self) -> None:
        """页面停用"""
        # 保存页面状态
        self._save_page_state()
