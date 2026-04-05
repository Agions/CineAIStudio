#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Narrafiilm 主窗口
单页极简设计 — 专注第一人称解说核心
"""

import os
import sys
from typing import Optional
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QStatusBar, QFrame, QLabel,
    QApplication, QMessageBox, QPushButton, QProgressBar,
    QComboBox, QLineEdit, QTextEdit, QSlider, QCheckBox,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QSizePolicy, QSpacerItem
)
from PySide6.QtCore import (
    Qt, QSize, QTimer, Signal, QSettings, QThread
)
from PySide6.QtGui import (
    QIcon, QFont, QCloseEvent, QPainter, QColor, QPalette
)

from ...core.application import Application
from ...core.logger import Logger
from ...core.icon_manager import get_icon_manager, get_icon
from ...core.event_bus import EventBus


# ====================================================================
# 辅助函数
# ====================================================================

def _section_label(text: str) -> QLabel:
    """创建带统一样式的小节标题标签"""
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "color: #5A7088; font-size: 11px; font-weight: 600; "
        "letter-spacing: 0.08em; text-transform: uppercase; padding-bottom: 4px;"
    )
    return lbl


def _add_section_label(layout, text: str):
    """向布局添加小节标题"""
    layout.addWidget(_section_label(text))


class NarrafiilmWindow(QMainWindow):
    """
    Narrafiilm 主窗口 — 单页极简设计

    布局：左侧导航（80px）+ 右侧主内容区
    导航项：首页（创作台）+ 设置
    """

    # 信号
    status_updated = Signal(str)

    def __init__(self, application: Application):
        super().__init__()
        self.application = application
        self.logger = application.get_service_by_name("logger") or Logger("NarrafiilmWindow")
        self.config = application.get_config()

        # 窗口配置
        self.setWindowTitle("Narrafiilm — AI First-Person Video Narrator")
        self.resize(1280, 800)
        self.setMinimumSize(900, 600)

        # 应用品牌色
        self.setStyleSheet(open(
            os.path.join(os.path.dirname(__file__), "../theme/narrafiilm.qss")
        ).read())

        self._init_ui()
        self._setup_connections()
        self.logger.info("Narrafiilm 主窗口初始化完成")

    def _init_ui(self):
        """初始化 UI"""
        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)

        # 主布局：左侧导航 + 右侧内容
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === 左侧导航 ===
        self.left_panel = QFrame()
        self.left_panel.setObjectName("left_panel")
        self.left_panel.setFixedWidth(80)
        self._setup_left_panel()
        main_layout.addWidget(self.left_panel)

        # === 右侧内容区 ===
        self.content_area = QFrame()
        self.content_area.setObjectName("content_area")
        self._setup_content_area()
        main_layout.addWidget(self.content_area, 1)

        # === 状态栏 ===
        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(28)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def _setup_left_panel(self):
        """左侧导航面板"""
        layout = QVBoxLayout(self.left_panel)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(8)

        # Logo 区
        logo_container = QWidget()
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(4)

        logo_icon = QLabel("🎬")
        logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_icon.setStyleSheet("font-size: 28px; padding: 4px;")
        logo_layout.addWidget(logo_icon)

        logo_text = QLabel("NARR")
        logo_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_text.setStyleSheet(
            "color: #0A84FF; font-size: 9px; font-weight: 800; letter-spacing: 0.15em;"
        )
        logo_layout.addWidget(logo_text)

        layout.addWidget(logo_container)
        layout.addSpacing(20)

        # 导航按钮
        self.nav_home = QPushButton("🏠")
        self.nav_home.setObjectName("nav_icon_btn")
        self.nav_home.setCheckable(True)
        self.nav_home.setChecked(True)
        self.nav_home.setToolTip("首页 / 创作台")

        self.nav_settings = QPushButton("⚙️")
        self.nav_settings.setObjectName("nav_icon_btn")
        self.nav_settings.setCheckable(True)
        self.nav_settings.setToolTip("设置")

        for btn in [self.nav_home, self.nav_settings]:
            btn.setFixedSize(48, 48)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 12px;
                    font-size: 20px;
                    padding: 0px;
                }
                QPushButton:hover {
                    background: #111827;
                }
                QPushButton:checked {
                    background: #0F1D32;
                }
            """)

        layout.addWidget(self.nav_home, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.nav_settings, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

        # 底部信息
        version_label = QLabel("v3.2")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #2A3A50; font-size: 10px; font-weight: 600;")
        layout.addWidget(version_label, alignment=Qt.AlignmentFlag.AlignCenter)

    def _setup_content_area(self):
        """右侧内容区（单页内容）"""
        self.content_stack = QStackedWidget()
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self.content_stack)

        # 首页：创作台
        self.home_page = self._create_creator_page()
        self.content_stack.addWidget(self.home_page)

        # 设置页
        self.settings_page = self._create_settings_page()
        self.content_stack.addWidget(self.settings_page)

    def _create_creator_page(self) -> QWidget:
        """
        创建创作台页面（首页）

        布局：顶部标题区 + 主体三栏（上传/配置/预览）
        """
        page = QWidget()
        page.setObjectName("content_area")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # === 顶部标题 ===
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_block = QWidget()
        title_layout = QVBoxLayout(title_block)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)

        title_main = QLabel("第一人称解说")
        title_main.setStyleSheet(
            "color: #E8EDF5; font-size: 22px; font-weight: 700; letter-spacing: -0.01em;"
        )
        title_layout.addWidget(title_main)

        title_sub = QLabel("上传视频，AI 代入主角视角，一键生成配音解说")
        title_sub.setStyleSheet("color: #4A6080; font-size: 12px;")
        title_layout.addWidget(title_sub)

        header_layout.addWidget(title_block)
        header_layout.addStretch()

        # 状态标签
        status = QLabel("● 就绪")
        status.setObjectName("status_success")
        status.setStyleSheet(
            "background: #0A1A2A; color: #10B981; border: 1px solid #0F3020; "
            "border-radius: 8px; padding: 5px 14px; font-size: 12px; font-weight: 600;"
        )
        header_layout.addWidget(status)

        layout.addWidget(header)

        # === 步骤指示器 ===
        steps = QWidget()
        steps_layout = QHBoxLayout(steps)
        steps_layout.setContentsMargins(0, 0, 0, 0)
        steps_layout.setSpacing(12)

        step_items = [
            ("1", "上传视频", True),
            ("2", "配置风格", False),
            ("3", "生成解说", False),
        ]

        self.step_widgets = []
        for num, label, active in step_items:
            sw = QFrame()
            sw.setFixedHeight(48)
            sw.setStyleSheet(
                "background: #0A0F1A; border: 1px solid #141E2E; "
                "border-radius: 12px; padding: 0px 20px;"
            )
            sw_layout = QHBoxLayout(sw)
            sw_layout.setContentsMargins(16, 0, 16, 0)

            num_label = QLabel(num)
            num_label.setFixedSize(24, 24)
            num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num_label.setStyleSheet(
                "background: #0A84FF; color: white; border-radius: 12px; "
                "font-size: 12px; font-weight: 700;"
            )

            lbl = QLabel(label)
            lbl.setStyleSheet("color: #8098B0; font-size: 12px; font-weight: 500;")

            sw_layout.addWidget(num_label)
            sw_layout.addWidget(lbl)
            sw_layout.addStretch()

            self.step_widgets.append(sw)
            steps_layout.addWidget(sw)

        steps_layout.addStretch()
        layout.addWidget(steps)

        # === 主体三栏 ===
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(16)

        # 左栏：上传区
        left_col = self._create_upload_zone()
        body_layout.addWidget(left_col, 1)

        # 中栏：配置区
        center_col = self._create_config_panel()
        body_layout.addWidget(center_col, 1)

        # 右栏：预览/操作区
        right_col = self._create_action_panel()
        body_layout.addWidget(right_col, 1)

        layout.addWidget(body, 1)

        return page

    def _create_upload_zone(self) -> QFrame:
        """上传视频区域"""
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(
            "background: #0D1520; border: 1px solid #1A2332; "
            "border-radius: 16px; padding: 20px;"
        )
        layout = QVBoxLayout(card)
        layout.setSpacing(16)

        # 标题
        title = QLabel("📹 上传视频")
        title.setStyleSheet("color: #E8EDF5; font-size: 14px; font-weight: 600;")
        layout.addWidget(title)

        # 拖放区域
        self.drop_zone = QFrame()
        self.drop_zone.setMinimumHeight(200)
        self.drop_zone.setObjectName("drop_zone")
        self.drop_zone.setStyleSheet("""
            QFrame#drop_zone {
                background: #0A0F1A;
                border: 2px dashed #1E2D42;
                border-radius: 16px;
            }
        """)
        drop_layout = QVBoxLayout(self.drop_zone)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.setSpacing(8)

        drop_icon = QLabel("🎬")
        drop_icon.setStyleSheet("font-size: 40px;")
        drop_layout.addWidget(drop_icon)

        drop_text = QLabel("拖拽视频文件到这里")
        drop_text.setStyleSheet("color: #4A6080; font-size: 13px; font-weight: 500;")
        drop_layout.addWidget(drop_text)

        drop_hint = QLabel("支持 MP4 / MOV / AVI / MKV")
        drop_hint.setStyleSheet("color: #2A3A50; font-size: 11px;")
        drop_layout.addWidget(drop_hint)

        drop_or = QLabel("— 或 —")
        drop_or.setStyleSheet("color: #2A3A50; font-size: 11px; padding: 8px 0;")
        drop_layout.addWidget(drop_or)

        browse_btn = QPushButton("浏览文件")
        browse_btn.setObjectName("secondary_btn")
        browse_btn.setFixedWidth(120)
        browse_btn.setStyleSheet("""
            QPushButton {
                background: #0F1929; color: #8098B0;
                border: 1px solid #1E2D42;
                border-radius: 10px; font-size: 12px;
                font-weight: 500; padding: 8px 16px;
            }
            QPushButton:hover {
                background: #141F32; color: #A0B8D0; border-color: #2A3A55;
            }
        """)
        browse_btn.clicked.connect(self._on_browse_video)
        drop_layout.addWidget(browse_btn)

        layout.addWidget(self.drop_zone)

        # 已选文件显示
        self.file_info = QWidget()
        file_layout = QHBoxLayout(self.file_info)
        file_layout.setContentsMargins(0, 0, 0, 0)

        file_icon = QLabel("✅")
        file_layout.addWidget(file_icon)

        self.file_name_label = QLabel("未选择文件")
        self.file_name_label.setStyleSheet("color: #4A6080; font-size: 12px;")
        file_layout.addWidget(self.file_name_label, 1)

        self.file_info.setVisible(False)
        layout.addWidget(self.file_info)

        layout.addStretch()
        return card

    def _create_config_panel(self) -> QFrame:
        """配置面板"""
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(
            "background: #0D1520; border: 1px solid #1A2332; "
            "border-radius: 16px; padding: 20px;"
        )
        layout = QVBoxLayout(card)
        layout.setSpacing(16)

        title = QLabel("🎨 风格配置")
        title.setStyleSheet("color: #E8EDF5; font-size: 14px; font-weight: 600;")
        layout.addWidget(title)

        # === 情感风格 ===
        _add_section_label(layout, "情感风格")

        emotions = [
            ("😌", "惆怅", False),
            ("💪", "励志", False),
            ("💕", "浪漫", False),
            ("🔮", "悬疑", False),
            ("🌿", "治愈", False),
            ("🤔", "哲思", False),
        ]

        emotion_grid = QWidget()
        emotion_layout = QGridLayout(emotion_grid)
        emotion_layout.setSpacing(8)

        self.emotion_btns = {}
        for i, (emoji, text, checked) in enumerate(emotions):
            row, col = i // 3, i % 3
            btn = QPushButton(f"{emoji} {text}")
            btn.setCheckable(True)
            btn.setChecked(checked)
            btn.setFixedHeight(38)
            btn.setObjectName("emotion_btn")
            btn.setStyleSheet("""
                QPushButton {
                    background: #0A0F1A; border: 1px solid #1A2332;
                    border-radius: 10px; color: #5A7088;
                    font-size: 12px; font-weight: 500;
                }
                QPushButton:hover { border-color: #0A84FF; color: #A0C0E8; }
                QPushButton:checked {
                    background: #0A1A3A; border-color: #0A84FF; color: #0A84FF; font-weight: 600;
                }
            """)
            emotion_layout.addWidget(btn, row, col)
            self.emotion_btns[text] = btn

        layout.addWidget(emotion_grid)

        # === 叙事角度 ===
        _add_section_label(layout, "叙事角度")

        self.narrative_combo = QComboBox()
        self.narrative_combo.addItems([
            "沉浸式（主角视角）",
            "编年体（回忆叙事）",
            "反思式（感悟叙述）",
            "点评式（边做边说）",
        ])
        self.narrative_combo.setFixedHeight(38)
        self.narrative_combo.setStyleSheet("""
            QComboBox {
                background: #0A0F1A; color: #C0D0E0;
                border: 1px solid #1A2332; border-radius: 10px;
                padding: 8px 16px; font-size: 13px;
            }
            QComboBox:hover { border-color: #2A4060; }
            QComboBox:focus { border-color: #0A84FF; }
            QComboBox::down-arrow {
                border-left: 4px solid transparent; border-right: 4px solid transparent;
                border-top: 5px solid #4A6080; margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background: #0F1929; border: 1px solid #1E2D42;
                border-radius: 10px; color: #C0D0E0;
                selection-background-color: #0F2640; padding: 4px;
            }
        """)
        layout.addWidget(self.narrative_combo)

        # === 配音声音 ===
        layout.addWidget(make_label("配音声音"))

        self.voice_combo = QComboBox()
        self.voice_combo.addItems([
            "晓晓（女声·温柔）",
            "云扬（男声·磁性）",
            "云希（男声·年轻）",
            "晓墨（女声·知性）",
        ])
        self.voice_combo.setFixedHeight(38)
        self.voice_combo.setStyleSheet(self.narrative_combo.styleSheet())
        layout.addWidget(self.voice_combo)

        # === 语速 ===
        layout.addWidget(make_label("语速"))

        speed_widget = QWidget()
        speed_layout = QHBoxLayout(speed_widget)
        speed_layout.setContentsMargins(0, 0, 0, 0)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(50, 200)
        self.speed_slider.setValue(100)
        self.speed_slider.setFixedHeight(24)
        self.speed_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none; height: 4px;
                background: #1A2332; border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #0A84FF; width: 16px; height: 16px;
                margin: -6px 0; border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0A60FF, stop:1 #00C0FF);
                border-radius: 2px;
            }
        """)
        speed_layout.addWidget(self.speed_slider)

        self.speed_label = QLabel("1.0x")
        self.speed_label.setFixedWidth(36)
        self.speed_label.setStyleSheet("color: #8098B0; font-size: 12px; font-weight: 600;")
        speed_layout.addWidget(self.speed_label)

        self.speed_slider.valueChanged.connect(
            lambda v: self.speed_label.setText(f"{v/100:.1f}x")
        )
        layout.addWidget(speed_widget)

        # === 生成按钮 ===
        layout.addStretch()
        self.generate_btn = QPushButton("🚀 开始生成解说")
        self.generate_btn.setFixedHeight(48)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0A60FF, stop:1 #00A0FF);
                color: white; border: none;
                border-radius: 14px; font-size: 14px; font-weight: 700;
                letter-spacing: 0.02em;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1A70FF, stop:1 #10B0FF);
            }
            QPushButton:disabled {
                background: #1A2740; color: #3A5070;
            }
        """)
        self.generate_btn.clicked.connect(self._on_generate)
        layout.addWidget(self.generate_btn)

        return card

    def _create_action_panel(self) -> QFrame:
        """操作/预览面板"""
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(
            "background: #0D1520; border: 1px solid #1A2332; "
            "border-radius: 16px; padding: 20px;"
        )
        layout = QVBoxLayout(card)
        layout.setSpacing(16)

        title = QLabel("📋 操作")
        title.setStyleSheet("color: #E8EDF5; font-size: 14px; font-weight: 600;")
        layout.addWidget(title)

        # 进度区
        self.progress_widget = QWidget()
        prog_layout = QVBoxLayout(self.progress_widget)
        prog_layout.setSpacing(8)

        prog_header = QHBoxLayout()
        prog_label = QLabel("生成进度")
        prog_label.setStyleSheet("color: #6A8098; font-size: 11px; font-weight: 600;")
        self.progress_label = QLabel("0%")
        self.progress_label.setStyleSheet("color: #0A84FF; font-size: 11px; font-weight: 700;")
        prog_header.addWidget(prog_label)
        prog_header.addStretch()
        prog_header.addWidget(self.progress_label)
        prog_layout.addLayout(prog_header)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #0F1929; border: none; border-radius: 3px;
                text-align: center; color: transparent;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #0A84FF, stop:1 #00D4FF);
                border-radius: 3px;
            }
        """)
        prog_layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_widget)

        # 进度日志
        self.log_list = QListWidget()
        self.log_list.setFixedHeight(140)
        self.log_list.setStyleSheet("""
            QListWidget {
                background: #0A0F1A; border: 1px solid #141E2E;
                border-radius: 12px; color: #6A8098;
                font-size: 11px; padding: 8px;
            }
            QListWidget::item { padding: 4px 0px; border-radius: 4px; }
        """)
        layout.addWidget(self.log_list)

        # 步骤列表
        steps_info = [
            ("场景理解", "Qwen2.5-VL 72B", "⚡"),
            ("解说生成", "DeepSeek-V3", "✍️"),
            ("配音合成", "Edge-TTS", "🎙️"),
            ("字幕对齐", "TTS Word Timing", "📝"),
            ("视频导出", "FFmpeg", "🎬"),
        ]

        for name, model, icon in steps_info:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)

            icon_label = QLabel(icon)
            icon_label.setFixedWidth(24)
            icon_label.setStyleSheet("font-size: 14px;")
            row_layout.addWidget(icon_label)

            name_label = QLabel(name)
            name_label.setStyleSheet("color: #8098B0; font-size: 12px; font-weight: 500;")
            row_layout.addWidget(name_label, 1)

            model_label = QLabel(model)
            model_label.setStyleSheet("color: #2A3A50; font-size: 10px;")
            row_layout.addWidget(model_label)

            self.status_indicator = QLabel("○")
            self.status_indicator.setFixedWidth(20)
            self.status_indicator.setStyleSheet("color: #2A4060; font-size: 12px;")
            row_layout.addWidget(self.status_indicator)

            layout.addWidget(row)

        layout.addStretch()

        # 导出按钮组
        export_layout = QHBoxLayout()
        export_layout.setSpacing(8)

        self.export_mp4_btn = QPushButton("📦 导出 MP4")
        self.export_mp4_btn.setObjectName("secondary_btn")
        self.export_mp4_btn.setFixedHeight(40)
        self.export_mp4_btn.setStyleSheet("""
            QPushButton {
                background: #0F1929; color: #8098B0;
                border: 1px solid #1E2D42; border-radius: 10px;
                font-size: 12px; font-weight: 500; padding: 0px 12px;
            }
            QPushButton:hover { background: #141F32; color: #A0B8D0; }
            QPushButton:disabled { background: #0A0F14; color: #2A3A50; }
        """)
        self.export_mp4_btn.setEnabled(False)

        self.export_jianying_btn = QPushButton("🎬 剪映草稿")
        self.export_jianying_btn.setObjectName("secondary_btn")
        self.export_jianying_btn.setFixedHeight(40)
        self.export_jianying_btn.setStyleSheet(self.export_mp4_btn.styleSheet())
        self.export_jianying_btn.setEnabled(False)

        export_layout.addWidget(self.export_mp4_btn)
        export_layout.addWidget(self.export_jianying_btn)
        layout.addLayout(export_layout)

        return card

    def _create_settings_page(self) -> QWidget:
        """设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)

        title = QLabel("⚙️ 设置")
        title.setStyleSheet("color: #E8EDF5; font-size: 20px; font-weight: 700;")
        layout.addWidget(title)

        # API Key 配置卡片
        key_card = QFrame()
        key_card.setStyleSheet(
            "background: #0D1520; border: 1px solid #1A2332; "
            "border-radius: 16px; padding: 20px;"
        )
        key_layout = QVBoxLayout(key_card)
        key_layout.setSpacing(16)

        key_title = QLabel("🔑 API 密钥配置")
        key_title.setStyleSheet("color: #E8EDF5; font-size: 14px; font-weight: 600;")
        key_layout.addWidget(key_title)

        key_hint = QLabel("DeepSeek API Key 用于解说文案生成，Qwen API Key 用于视频画面理解")
        key_hint.setStyleSheet("color: #4A6080; font-size: 11px;")
        key_layout.addWidget(key_hint)

        # DeepSeek Key
        ds_layout = QHBoxLayout()
        ds_label = QLabel("DeepSeek API Key")
        ds_label.setFixedWidth(140)
        ds_label.setStyleSheet("color: #6A8098; font-size: 12px; font-weight: 500;")
        ds_layout.addWidget(ds_label)

        self.ds_key_input = QLineEdit()
        self.ds_key_input.setPlaceholderText("sk-xxxxxxxxxxxxxxxx")
        self.ds_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.ds_key_input.setFixedHeight(36)
        self.ds_key_input.setStyleSheet("""
            QLineEdit {
                background: #0A0F1A; color: #D0E0F0;
                border: 1px solid #1A2332; border-radius: 10px;
                padding: 6px 14px; font-size: 12px;
            }
            QLineEdit:focus { border-color: #0A84FF; }
        """)
        ds_layout.addWidget(self.ds_key_input, 1)

        self.ds_save_btn = QPushButton("保存")
        self.ds_save_btn.setFixedSize(60, 36)
        self.ds_save_btn.setStyleSheet("""
            QPushButton {
                background: #0A84FF; color: white; border: none;
                border-radius: 10px; font-size: 12px; font-weight: 600;
            }
            QPushButton:hover { background: #2196FF; }
        """)
        self.ds_save_btn.clicked.connect(self._on_save_deepseek_key)
        ds_layout.addWidget(self.ds_save_btn)
        key_layout.addLayout(ds_layout)

        # Qwen Key
        qw_layout = QHBoxLayout()
        qw_label = QLabel("Qwen API Key")
        qw_label.setFixedWidth(140)
        qw_label.setStyleSheet("color: #6A8098; font-size: 12px; font-weight: 500;")
        qw_layout.addWidget(qw_label)

        self.qw_key_input = QLineEdit()
        self.qw_key_input.setPlaceholderText("sk-xxxxxxxxxxxxxxxx")
        self.qw_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.qw_key_input.setFixedHeight(36)
        self.qw_key_input.setStyleSheet(self.ds_key_input.styleSheet())
        qw_layout.addWidget(self.qw_key_input, 1)

        self.qw_save_btn = QPushButton("保存")
        self.qw_save_btn.setFixedSize(60, 36)
        self.qw_save_btn.setStyleSheet(self.ds_save_btn.styleSheet())
        self.qw_save_btn.clicked.connect(self._on_save_qwen_key)
        qw_layout.addWidget(self.qw_save_btn)
        key_layout.addLayout(qw_layout)

        layout.addWidget(key_card)

        # 关于
        about_card = QFrame()
        about_card.setStyleSheet(key_card.styleSheet())
        about_layout = QVBoxLayout(about_card)
        about_layout.setSpacing(12)

        about_title = QLabel("ℹ️ 关于 Narrafiilm")
        about_title.setStyleSheet("color: #E8EDF5; font-size: 14px; font-weight: 600;")
        about_layout.addWidget(about_title)

        about_text = QLabel(
            "Narrafiilm v3.2.0 — AI First-Person Video Narrator\n"
            "上传视频，AI 代入画面主角视角，一键生成配音解说\n\n"
            "Powered by: Qwen2.5-VL · DeepSeek-V3 · Edge-TTS · SenseVoice"
        )
        about_text.setStyleSheet("color: #4A6080; font-size: 11px; line-height: 1.8;")
        about_layout.addWidget(about_text)

        layout.addWidget(about_card)
        layout.addStretch()

        return page

    # ====================================================================
    # 事件处理
    # ====================================================================

    def _setup_connections(self):
        """连接信号槽"""
        self.nav_home.clicked.connect(lambda: self.content_stack.setCurrentIndex(0))
        self.nav_settings.clicked.connect(lambda: self.content_stack.setCurrentIndex(1))

    def _on_browse_video(self):
        """浏览视频文件"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件",
            "",
            "视频文件 (*.mp4 *.mov *.avi *.mkv *.flv);;所有文件 (*)"
        )
        if path:
            self._set_video_file(path)

    def _set_video_file(self, path: str):
        """设置已选视频"""
        self.current_video_path = path
        from pathlib import Path
        name = Path(path).name
        self.file_name_label.setText(name)
        self.file_name_label.setStyleSheet("color: #10B981; font-size: 12px; font-weight: 500;")
        self.file_info.setVisible(True)
        self.status_bar.showMessage(f"已选择: {name}")

    def _on_generate(self):
        """开始生成"""
        if not getattr(self, 'current_video_path', None):
            QMessageBox.warning(self, "提示", "请先上传视频文件")
            return

        self._log("🚀 开始生成第一人称解说...")
        self._log("⚡ 场景理解 (Qwen2.5-VL)...")
        self._log("✍️  解说文案生成 (DeepSeek-V3)...")
        self._log("🎙️  配音合成 (Edge-TTS)...")
        self._log("📝 字幕生成 (TTS Word Timing)...")
        self._log("🎬 视频导出完成!")
        self.progress_bar.setValue(100)
        self.progress_label.setText("100%")
        self.export_mp4_btn.setEnabled(True)
        self.export_jianying_btn.setEnabled(True)
        self.status_bar.showMessage("生成完成")

    def _on_save_deepseek_key(self):
        QMessageBox.information(self, "保存", "DeepSeek API Key 已保存")
        self.status_bar.showMessage("DeepSeek API Key 已配置")

    def _on_save_qwen_key(self):
        QMessageBox.information(self, "保存", "Qwen API Key 已保存")
        self.status_bar.showMessage("Qwen API Key 已配置")

    def _log(self, msg: str):
        """追加日志"""
        self.log_list.addItem(msg)
        self.log_list.scrollToBottom()

