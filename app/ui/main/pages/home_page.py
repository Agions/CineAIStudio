#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 首页
应用程序主入口页面，提供快捷访问和状态概览
"""

import os
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSizePolicy, QSpacerItem,
    QProgressBar, QGroupBox, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPixmap, QIcon

from .base_page import BasePage
from app.core.icon_manager import get_icon
from app.utils.error_handler import handle_exception
from app.ui.components.quick_ai_config import QuickAIConfigWidget


class HomePage(BasePage):
    """首页页面"""

    def __init__(self, application):
        super().__init__("home", "首页", application)

        self.logger = application.get_service(type(application.logger))
        self.page_title = "首页"

        # 初始化UI
        self._init_ui()

        # 定时刷新状态
        self._setup_refresh_timer()

    def _init_ui(self):
        """初始化用户界面"""
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(25)

        # 标题区域
        title_widget = self._create_title_section()
        self.main_layout.addWidget(title_widget)

        # 欢迎区域
        welcome_widget = self._create_welcome_section()
        self.main_layout.addWidget(welcome_widget)

        # 使用分割器来更好地组织内容
        content_splitter = QSplitter(Qt.Orientation.Vertical)

        # 上部分：快捷操作和状态
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setSpacing(20)

        # 快捷操作区域
        quick_actions_widget = self._create_quick_actions_section()
        top_layout.addWidget(quick_actions_widget, 1)  # 权重1

        # AI快捷配置区域
        ai_config_widget = self._create_ai_config_section()
        top_layout.addWidget(ai_config_widget, 1)  # 权重1

        content_splitter.addWidget(top_widget)

        # 中间部分：系统状态
        status_widget = self._create_status_section()
        content_splitter.addWidget(status_widget)

        # 下部分：最近项目
        recent_widget = self._create_recent_projects_section()
        content_splitter.addWidget(recent_widget)

        # 设置分割器比例
        content_splitter.setSizes([300, 150, 150])
        content_splitter.setCollapsible(0, False)
        content_splitter.setCollapsible(1, True)
        content_splitter.setCollapsible(2, True)

        self.main_layout.addWidget(content_splitter, 1)  # 主要内容区域，权重1

        # 添加弹性空间
        self.main_layout.addStretch()

    def _create_title_section(self) -> QWidget:
        """创建标题区域"""
        widget = QFrame()
        widget.setObjectName("titleSection")
        layout = QVBoxLayout(widget)

        # 主标题
        title_label = QLabel("CineAIStudio")
        title_label.setObjectName("mainTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel#mainTitle {
                font-size: 36px;
                font-weight: bold;
                color: #2196F3;
                margin: 10px;
            }
        """)

        # 副标题
        subtitle_label = QLabel("专业的AI视频编辑器")
        subtitle_label.setObjectName("subTitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel#subTitle {
                font-size: 18px;
                color: #666;
                margin: 5px;
            }
        """)

        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)

        return widget

    def _create_welcome_section(self) -> QWidget:
        """创建欢迎区域"""
        widget = QFrame()
        widget.setObjectName("welcomeSection")
        widget.setFrameShape(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame#welcomeSection {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(20, 15, 20, 15)

        # 欢迎文本
        welcome_text = QLabel(
            "欢迎使用 CineAIStudio v2.0！\n"
            "这里您可以使用AI技术来增强您的视频编辑体验。"
        )
        welcome_text.setWordWrap(True)
        welcome_text.setStyleSheet("""
            QLabel {
                font-size: 15px;
                line-height: 1.6;
                color: #333;
                background: transparent;
            }
        """)

        layout.addWidget(welcome_text)

        return widget

    def _create_quick_actions_section(self) -> QWidget:
        """创建快捷操作区域"""
        widget = QFrame()
        widget.setObjectName("quickActionsSection")
        widget.setStyleSheet("""
            QFrame#quickActionsSection {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = QLabel("快捷操作")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")
        layout.addWidget(title_label)

        # 按钮网格
        button_layout = QGridLayout()
        button_layout.setSpacing(15)

        actions = [
            ("新建项目", "new", self._on_new_project),
            ("打开项目", "open", self._on_open_project),
            ("AI视频增强", "ai_enhance", self._on_ai_enhance),
            ("智能剪辑", "ai_magic", self._on_smart_cut),
            ("设置", "settings", self._on_settings)
        ]

        for i, (text, icon_name, handler) in enumerate(actions):
            row = i // 3
            col = i % 3

            # 安全地获取图标
            try:
                icon = get_icon(icon_name, 32)
            except Exception:
                icon = QIcon()

            btn = QPushButton(icon, text)
            btn.setMinimumSize(140, 80)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f8f9fa;
                    color: #495057;
                    border: 2px solid #e9ecef;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 500;
                    padding: 12px 8px;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                    border-color: #2196F3;
                    color: #2196F3;
                }
                QPushButton:pressed {
                    background-color: #2196F3;
                    color: white;
                    border-color: #2196F3;
                }
            """)
            btn.clicked.connect(handler)

            button_layout.addWidget(btn, row, col)

        self.main_layout.addLayout(button_layout)

        return widget

    def _create_ai_config_section(self) -> QWidget:
        """创建AI快捷配置区域"""
        widget = QFrame()
        widget.setObjectName("aiConfigSection")
        widget.setStyleSheet("""
            QFrame#aiConfigSection {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)

        # 创建快捷AI配置组件
        self.ai_config_component = QuickAIConfigWidget(self)

        return self.ai_config_component

    def _create_status_section(self) -> QWidget:
        """创建状态概览区域"""
        widget = QFrame()
        widget.setObjectName("statusSection")
        widget.setStyleSheet("""
            QFrame#statusSection {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = QLabel("系统状态")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")
        layout.addWidget(title_label)

        # 状态网格
        status_layout = QGridLayout()
        status_layout.setSpacing(10)

        # 状态项
        status_items = [
            ("AI服务", "正常", "#4CAF50"),
            ("存储空间", "充足", "#4CAF50"),
            ("内存使用", "正常", "#4CAF50"),
            ("主题", "深色模式", "#2196F3")
        ]

        for i, (label, value, color) in enumerate(status_items):
            # 标签
            label_widget = QLabel(f"{label}:")
            label_widget.setStyleSheet("font-weight: bold;")
            status_layout.addWidget(label_widget, i, 0)

            # 值
            value_widget = QLabel(value)
            value_widget.setStyleSheet(f"color: {color};")
            status_layout.addWidget(value_widget, i, 1)

        self.main_layout.addLayout(status_layout)

        return widget

    def _create_recent_projects_section(self) -> QWidget:
        """创建最近项目区域"""
        widget = QFrame()
        widget.setObjectName("recentProjectsSection")
        widget.setStyleSheet("""
            QFrame#recentProjectsSection {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = QLabel("最近项目")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")
        layout.addWidget(title_label)

        # 最近项目列表
        recent_projects = self._get_recent_projects()

        if recent_projects:
            for project in recent_projects[:5]:  # 显示最近5个项目
                project_btn = QPushButton(project)
                project_btn.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        padding: 8px;
                        border: 1px solid #ddd;
                        border-radius: 3px;
                        background-color: white;
                    }
                    QPushButton:hover {
                        background-color: #f5f5f5;
                    }
                """)
                project_btn.clicked.connect(lambda checked, p=project: self._on_open_recent_project(p))
                layout.addWidget(project_btn)
        else:
            no_projects_label = QLabel("暂无最近项目")
            no_projects_label.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
            layout.addWidget(no_projects_label)

        return widget

    def _setup_refresh_timer(self):
        """设置定时刷新"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_status)
        self.refresh_timer.start(30000)  # 每30秒刷新一次

    def _refresh_status(self):
        """刷新状态信息"""
        try:
            # 这里可以添加状态刷新逻辑
            self.logger.debug("刷新状态信息")
        except Exception as e:
            self.logger.error(f"刷新状态失败: {e}")

    def _get_recent_projects(self) -> list:
        """获取最近项目列表"""
        try:
            # 从设置管理器获取最近项目
            config_manager = self.application.get_service_by_name("config_manager")
            if config_manager:
                return config_manager.get_value("recent_files", [])
            return []
        except Exception as e:
            self.logger.error(f"获取最近项目失败: {e}")
            return []

    def _on_new_project(self):
        """新建项目"""
        try:
            self.logger.info("新建项目")
            # 切换到视频编辑页面
            self.parent().switch_to_page("video_editor")
        except Exception as e:
            self.logger.error(f"新建项目失败: {e}")

    def _on_open_project(self):
        """打开项目"""
        try:
            self.logger.info("打开项目")
            # 这里应该显示文件选择对话框
            QMessageBox.information(self, "打开项目", "打开项目功能正在开发中...")
        except Exception as e:
            self.logger.error(f"打开项目失败: {e}")

    def _on_ai_enhance(self):
        """AI视频增强"""
        try:
            self.logger.info("AI视频增强")
            # 切换到AI对话页面
            self.parent().switch_to_page("ai_chat")
        except Exception as e:
            self.logger.error(f"AI增强失败: {e}")

    def _on_smart_cut(self):
        """智能剪辑"""
        try:
            self.logger.info("智能剪辑")
            QMessageBox.information(self, "智能剪辑", "智能剪辑功能正在开发中...")
        except Exception as e:
            self.logger.error(f"智能剪辑失败: {e}")

    def _on_settings(self):
        """打开设置"""
        try:
            self.logger.info("打开设置")
            # 切换到设置页面
            self.parent().switch_to_page("settings")
        except Exception as e:
            self.logger.error(f"打开设置失败: {e}")

    def _on_open_recent_project(self, project_path: str):
        """打开最近项目"""
        try:
            self.logger.info(f"打开最近项目: {project_path}")
            # 这里应该加载项目文件
            QMessageBox.information(self, "打开项目", f"正在打开项目: {project_path}")
        except Exception as e:
            self.logger.error(f"打开最近项目失败: {e}")

    def refresh(self):
        """刷新页面"""
        self._refresh_status()

    def get_page_type(self) -> str:
        """获取页面类型"""
        return "home"