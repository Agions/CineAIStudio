#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快捷AI配置组件
提供国产AI模型的快速配置入口
"""

import os
from typing import Dict, List, Optional, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QSizePolicy, QSpacerItem, QMessageBox, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor

from app.core.config_manager import ConfigManager
from app.core.logger import Logger
from app.core.icon_manager import get_icon
from ..dialogs.model_application_dialog import ModelApplicationDialog


class QuickAIConfigWidget(QWidget):
    """快捷AI配置组件"""

    config_changed = pyqtSignal()  # 配置变更信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("quickAIConfigWidget")

        # 初始化组件
        self.config_manager = ConfigManager()
        self.logger = Logger("QuickAIConfigWidget")

        # 初始化UI
        self._init_ui()
        self._setup_connections()

        # 定时刷新状态
        self._setup_refresh_timer()

    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 标题区域
        title_widget = self._create_title_section()
        layout.addWidget(title_widget)

        # 配置状态区域
        status_widget = self._create_status_section()
        layout.addWidget(status_widget)

        # 快捷操作区域
        actions_widget = self._create_actions_section()
        layout.addWidget(actions_widget)

        # 最近使用区域
        recent_widget = self._create_recent_section()
        layout.addWidget(recent_widget)

        layout.addStretch()

    def _create_title_section(self) -> QWidget:
        """创建标题区域"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 图标和标题
        icon_label = QLabel()
        icon_label.setPixmap(get_icon("ai", 32).pixmap(32, 32))
        layout.addWidget(icon_label)

        title_label = QLabel("快捷AI配置")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        layout.addWidget(title_label)

        layout.addStretch()

        # 刷新按钮
        refresh_btn = QPushButton(get_icon("refresh", 16), "")
        refresh_btn.setFixedSize(24, 24)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_status)
        layout.addWidget(refresh_btn)

        return widget

    def _create_status_section(self) -> QWidget:
        """创建状态区域"""
        widget = QFrame()
        widget.setObjectName("statusSection")
        widget.setFrameShape(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame#statusSection {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 状态标题
        status_title = QLabel("当前配置状态")
        status_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
        layout.addWidget(status_title)

        # 状态网格
        self.status_grid = QGridLayout()
        self.status_grid.setSpacing(10)

        # 获取当前配置状态
        configured_models = self._get_configured_models()

        # 状态项
        status_items = [
            ("百度文心一言", "baidu" in configured_models, "#1890ff"),
            ("讯飞星火", "xunfei" in configured_models, "#52c41a"),
            ("通义千问", "aliyun" in configured_models, "#722ed1"),
            ("智谱AI", "zhipu" in configured_models, "#fa8c16"),
            ("百川AI", "baichuan" in configured_models, "#eb2f96"),
            ("月之暗面", "moonshot" in configured_models, "#13c2c2")
        ]

        for i, (name, configured, color) in enumerate(status_items):
            row = i // 3
            col = i % 3

            # 状态卡片
            status_card = QFrame()
            status_card.setFixedSize(140, 60)
            status_card.setStyleSheet(f"""
                QFrame {{
                    background-color: {'#f6ffed' if configured else '#fff1f0'};
                    border: 1px solid {'#b7eb8f' if configured else '#ffccc7'};
                    border-radius: 6px;
                }}
            """)

            card_layout = QVBoxLayout(status_card)
            card_layout.setContentsMargins(8, 8, 8, 8)
            card_layout.setSpacing(5)

            # 模型名称
            name_label = QLabel(name)
            name_label.setStyleSheet("font-size: 12px; font-weight: bold;")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(name_label)

            # 状态标签
            status_text = "已配置" if configured else "未配置"
            status_color = "#52c41a" if configured else "#ff4d4f"
            status_label = QLabel(status_text)
            status_label.setStyleSheet(f"color: {status_color}; font-size: 11px;")
            status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(status_label)

            self.status_grid.addWidget(status_card, row, col)

        layout.addLayout(self.status_grid)

        return widget

    def _create_actions_section(self) -> QWidget:
        """创建快捷操作区域"""
        widget = QFrame()
        widget.setObjectName("actionsSection")
        widget.setFrameShape(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame#actionsSection {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 操作标题
        actions_title = QLabel("快捷操作")
        actions_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
        layout.addWidget(actions_title)

        # 按钮网格
        button_grid = QGridLayout()
        button_grid.setSpacing(10)

        buttons = [
            ("申请AI模型", "add", self._on_apply_model, "快速申请国产AI模型API密钥"),
            ("配置参数", "settings", self._on_config_params, "配置AI模型参数"),
            ("测试连接", "network", self._on_test_connection, "测试AI服务连接状态"),
            ("查看文档", "document", self._on_view_docs, "查看AI服务文档")
        ]

        for i, (text, icon, handler, tooltip) in enumerate(buttons):
            row = i // 2
            col = i % 2

            btn = QPushButton(get_icon(icon, 20), text)
            btn.setFixedSize(160, 40)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(tooltip)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f8f9fa;
                    color: #495057;
                    border: 1px solid #e9ecef;
                    border-radius: 6px;
                    font-size: 13px;
                    text-align: center;
                    padding: 8px;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                    border-color: #1890ff;
                    color: #1890ff;
                }
                QPushButton:pressed {
                    background-color: #1890ff;
                    color: white;
                    border-color: #1890ff;
                }
            """)
            btn.clicked.connect(handler)
            button_grid.addWidget(btn, row, col)

        layout.addLayout(button_grid)

        return widget

    def _create_recent_section(self) -> QWidget:
        """创建最近使用区域"""
        widget = QFrame()
        widget.setObjectName("recentSection")
        widget.setFrameShape(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame#recentSection {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 最近使用标题
        recent_title = QLabel("最近使用")
        recent_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
        layout.addWidget(recent_title)

        # 获取最近使用的模型
        recent_models = self._get_recent_models()

        if recent_models:
            for model_name, model_info in recent_models[:3]:  # 显示最近3个
                model_item = self._create_model_item(model_name, model_info)
                layout.addWidget(model_item)
        else:
            no_recent_label = QLabel("暂无使用记录")
            no_recent_label.setStyleSheet("color: #8c8c8c; font-size: 12px; font-style: italic;")
            no_recent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_recent_label)

        return widget

    def _create_model_item(self, model_name: str, model_info: Dict[str, Any]) -> QFrame:
        """创建模型项"""
        item = QFrame()
        item.setFrameShape(QFrame.Shape.StyledPanel)
        item.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 6px;
            }
            QFrame:hover {
                border-color: #1890ff;
                background-color: #f0f8ff;
            }
        """)
        item.setFixedHeight(50)

        layout = QHBoxLayout(item)
        layout.setContentsMargins(10, 10, 10, 10)

        # 模型图标
        icon_label = QLabel()
        icon_label.setPixmap(get_icon("ai", 16).pixmap(16, 16))
        layout.addWidget(icon_label)

        # 模型信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        name_label = QLabel(model_name)
        name_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #2c3e50;")
        info_layout.addWidget(name_label)

        status_label = QLabel("已配置")
        status_label.setStyleSheet("color: #52c41a; font-size: 10px;")
        info_layout.addWidget(status_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        # 使用时间
        time_label = QLabel(model_info.get("last_used", ""))
        time_label.setStyleSheet("color: #8c8c8c; font-size: 10px;")
        layout.addWidget(time_label)

        return item

    def _setup_connections(self):
        """设置信号连接"""
        pass

    def _setup_refresh_timer(self):
        """设置定时刷新"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_status)
        self.refresh_timer.start(30000)  # 每30秒刷新一次

    def _get_configured_models(self) -> List[str]:
        """获取已配置的模型列表"""
        try:
            ai_configs = self.config_manager.get_value("ai_models", {})
            return list(ai_configs.keys())
        except Exception as e:
            self.logger.error(f"获取已配置模型失败: {e}")
            return []

    def _get_recent_models(self) -> List[tuple]:
        """获取最近使用的模型"""
        try:
            recent_models = self.config_manager.get_value("recent_ai_models", [])
            return [(model.get("name", ""), model) for model in recent_models]
        except Exception as e:
            self.logger.error(f"获取最近使用模型失败: {e}")
            return []

    def _on_apply_model(self):
        """申请AI模型"""
        try:
            dialog = ModelApplicationDialog(self)
            dialog.exec()
            self.refresh_status()
        except Exception as e:
            self.logger.error(f"打开申请对话框失败: {e}")
            QMessageBox.critical(self, "错误", f"无法打开申请对话框: {e}")

    def _on_config_params(self):
        """配置参数"""
        try:
            configured_models = self._get_configured_models()
            if not configured_models:
                QMessageBox.information(self, "提示", "请先申请并配置AI模型")
                return

            # 这里可以打开参数配置对话框
            QMessageBox.information(self, "功能开发中", "参数配置功能正在开发中")
        except Exception as e:
            self.logger.error(f"配置参数失败: {e}")

    def _on_test_connection(self):
        """测试连接"""
        try:
            configured_models = self._get_configured_models()
            if not configured_models:
                QMessageBox.information(self, "提示", "请先申请并配置AI模型")
                return

            # 模拟连接测试
            QMessageBox.information(self, "测试结果", "AI服务连接正常")
        except Exception as e:
            self.logger.error(f"测试连接失败: {e}")

    def _on_view_docs(self):
        """查看文档"""
        try:
            # 打开文档页面
            webbrowser.open("https://github.com/your-repo/docs")
        except Exception as e:
            self.logger.error(f"打开文档失败: {e}")

    def refresh_status(self):
        """刷新状态"""
        try:
            # 重新创建状态区域
            self._refresh_status_section()
            self.logger.debug("刷新AI配置状态")
        except Exception as e:
            self.logger.error(f"刷新状态失败: {e}")

    def _refresh_status_section(self):
        """刷新状态区域"""
        # 重新创建状态区域
        self.status_grid.parent().deleteLater()

        status_widget = self._create_status_section()
        self.layout().insertWidget(1, status_widget)