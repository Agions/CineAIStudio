#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快捷AI配置组件
提供国产AI模型的快速配置入口
"""

import os
import webbrowser
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
from app.utils.error_handler import (
    get_global_error_handler, ErrorInfo, ErrorType, ErrorSeverity,
    ErrorContext, RecoveryAction, error_handler_decorator
)
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
        self.error_handler = get_global_error_handler()

        # 初始化UI
        self._init_ui()
        self._setup_connections()

        # 定时刷新状态
        self._setup_refresh_timer()

    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 标题和快速操作区域
        header_widget = self._create_header_section()
        layout.addWidget(header_widget)

        # AI模型状态网格
        models_widget = self._create_models_section()
        layout.addWidget(models_widget)

        # 快捷操作区域
        actions_widget = self._create_actions_section()
        layout.addWidget(actions_widget)

        # 最近使用区域
        recent_widget = self._create_recent_section()
        layout.addWidget(recent_widget)

        layout.addStretch()

    def _create_header_section(self) -> QWidget:
        """创建标题区域"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 12px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # 标题行
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)

        # 图标和标题
        try:
            icon_label = QLabel()
            icon_label.setPixmap(get_icon("ai", 32).pixmap(32, 32))
            title_layout.addWidget(icon_label)
        except:
            title_layout.addSpacing(32)

        title_label = QLabel("AI 配置中心")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # 刷新按钮
        refresh_btn = QPushButton(get_icon("refresh", 16), "")
        refresh_btn.setFixedSize(28, 28)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #b0b0b0;
                border: 1px solid #404040;
                border-radius: 14px;
            }
            QPushButton:hover {
                background-color: #404040;
                color: #ffffff;
                border-color: #1890ff;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_status)
        title_layout.addWidget(refresh_btn)

        layout.addLayout(title_layout)

        # 快速状态概览
        status_overview = self._create_status_overview()
        status_overview.setObjectName("status_overview")
        layout.addWidget(status_overview)

        return widget

    def _create_status_overview(self) -> QWidget:
        """创建状态概览"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        configured_models = self._get_configured_models()
        total_models = 6  # 总共支持的AI模型数量
        configured_count = len(configured_models)

        # 总体状态
        status_widget = QFrame()
        status_widget.setFrameStyle(QFrame.Shape.Box)
        status_widget.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(10)

        # 状态图标
        try:
            status_icon = QLabel()
            if configured_count > 0:
                status_icon.setPixmap(get_icon("success", 16).pixmap(16, 16))
            else:
                status_icon.setPixmap(get_icon("warning", 16).pixmap(16, 16))
            status_layout.addWidget(status_icon)
        except:
            status_layout.addSpacing(16)

        # 状态文本
        if configured_count == 0:
            status_text = "未配置AI模型"
            status_color = "#ff9800"
        elif configured_count == total_models:
            status_text = "所有AI模型已配置"
            status_color = "#4caf50"
        else:
            status_text = f"已配置 {configured_count}/{total_models} 个AI模型"
            status_color = "#2196f3"

        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {status_color}; font-size: 12px; font-weight: bold;")
        status_layout.addWidget(status_label)

        layout.addWidget(status_widget)
        layout.addStretch()

        return widget

    def _create_models_section(self) -> QWidget:
        """创建AI模型状态区域"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 12px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("AI 模型状态")
        title_label.setStyleSheet("""
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
        """)
        layout.addWidget(title_label)

        # 模型网格
        self.models_grid = QGridLayout()
        self.models_grid.setSpacing(12)

        # 获取当前配置状态
        configured_models = self._get_configured_models()

        # AI模型项
        ai_models = [
            ("百度文心一言", "baidu", "#1890ff", "文心一言"),
            ("讯飞星火", "xunfei", "#52c41a", "星火"),
            ("通义千问", "aliyun", "#722ed1", "千问"),
            ("智谱AI", "zhipu", "#fa8c16", "智谱"),
            ("百川AI", "baichuan", "#eb2f96", "百川"),
            ("月之暗面", "moonshot", "#13c2c2", "月之暗面")
        ]

        for i, (full_name, short_name, color, display_name) in enumerate(ai_models):
            row = i // 3
            col = i % 3

            model_card = self._create_model_card(
                display_name, short_name in configured_models, color, short_name
            )
            self.models_grid.addWidget(model_card, row, col)

        layout.addLayout(self.models_grid)

        return widget

    def _create_model_card(self, name: str, configured: bool, color: str, model_key: str) -> QWidget:
        """创建模型卡片"""
        card = QFrame()
        card.setObjectName(f"modelCard_{model_key}")
        card.setFrameStyle(QFrame.Shape.Box)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setFixedSize(160, 80)

        if configured:
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: #1e3a5f;
                    border: 2px solid {color};
                    border-radius: 10px;
                    padding: 10px;
                }}
                QFrame:hover {{
                    background-color: #2a4a7a;
                    border-color: {self._adjust_color(color, 1.2)};
                }}
            """)
        else:
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: #3a2a2a;
                    border: 2px solid #404040;
                    border-radius: 10px;
                    padding: 10px;
                }}
                QFrame:hover {{
                    background-color: #4a3a3a;
                    border-color: {color};
                }}
            """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 模型图标和名称
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        # 状态图标
        try:
            icon_name = "check" if configured else "add"
            icon_label = QLabel()
            icon_label.setPixmap(get_icon(icon_name, 16).pixmap(16, 16))
            header_layout.addWidget(icon_label)
        except:
            header_layout.addSpacing(16)

        # 模型名称
        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            color: {'#ffffff' if configured else '#b0b0b0'};
            font-size: 12px;
            font-weight: bold;
        """)
        header_layout.addWidget(name_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # 状态文本
        status_text = "已配置" if configured else "点击配置"
        status_color = color if configured else "#ff9800"
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"""
            color: {status_color};
            font-size: 10px;
            font-weight: bold;
        """)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)

        # 点击事件
        card.mousePressEvent = lambda event: self._on_model_card_clicked(model_key, configured)

        return card

    def _adjust_color(self, hex_color: str, factor: float) -> str:
        """调整颜色亮度"""
        try:
            # 移除#号
            hex_color = hex_color.lstrip('#')
            # 转换为RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)

            # 调整亮度
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))

            # 转换回十六进制
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return hex_color

    def _on_model_card_clicked(self, model_key: str, configured: bool):
        """处理模型卡片点击事件"""
        try:
            if configured:
                # 已配置的模型，显示配置详情或测试连接
                self._on_test_connection()
            else:
                # 未配置的模型，打开配置对话框
                self._on_apply_model()
        except Exception as e:
            self.logger.error(f"处理模型卡片点击失败: {e}")

    def _create_actions_section(self) -> QWidget:
        """创建快捷操作区域"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 12px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("快捷操作")
        title_label.setStyleSheet("""
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
        """)
        layout.addWidget(title_label)

        # 操作按钮网格
        actions_grid = QGridLayout()
        actions_grid.setSpacing(12)

        buttons = [
            ("申请AI模型", "add", self._on_apply_model, "#1890ff", "快速申请国产AI模型API密钥"),
            ("配置参数", "settings", self._on_config_params, "#52c41a", "配置AI模型参数"),
            ("测试连接", "network", self._on_test_connection, "#722ed1", "测试AI服务连接状态"),
            ("查看文档", "document", self._on_view_docs, "#fa8c16", "查看AI服务文档"),
            ("智能优化", "optimize", self._on_optimize, "#eb2f96", "智能优化AI配置"),
            ("负载均衡", "balance", self._on_balance, "#13c2c2", "AI负载均衡管理")
        ]

        for i, (text, icon, handler, color, tooltip) in enumerate(buttons):
            row = i // 3
            col = i % 2

            btn = self._create_action_button(text, icon, color, handler, tooltip)
            actions_grid.addWidget(btn, row, col)

        layout.addLayout(actions_grid)

        return widget

    def _create_action_button(self, text: str, icon_name: str, color: str, callback, tooltip: str = "") -> QPushButton:
        """创建操作按钮"""
        btn = QPushButton(text)
        btn.setFixedSize(140, 38)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            btn.setToolTip(tooltip)

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
                padding: 8px 12px;
            }}
            QPushButton:hover {{
                background-color: {self._adjust_color(color, 1.1)};
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
            QPushButton:pressed {{
                background-color: {self._adjust_color(color, 0.9)};
            }}
        """)

        try:
            btn.setIcon(get_icon(icon_name, 18))
        except:
            pass

        btn.clicked.connect(callback)
        return btn

    def _create_recent_section(self) -> QWidget:
        """创建最近使用区域"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 12px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("最近使用")
        title_label.setStyleSheet("""
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
        """)
        layout.addWidget(title_label)

        # 获取最近使用的模型
        recent_models = self._get_recent_models()

        if recent_models:
            for model_name, model_info in recent_models[:3]:  # 显示最近3个
                model_item = self._create_model_item(model_name, model_info)
                layout.addWidget(model_item)
        else:
            no_recent_label = QLabel("暂无使用记录")
            no_recent_label.setStyleSheet("color: #b0b0b0; font-size: 12px; font-style: italic;")
            no_recent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_recent_label)

        return widget

    def _create_model_item(self, model_name: str, model_info: Dict[str, Any]) -> QFrame:
        """创建模型项"""
        item = QFrame()
        item.setFrameStyle(QFrame.Shape.Box)
        item.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 12px;
            }
            QFrame:hover {
                background-color: #2a2a2a;
                border-color: #1890ff;
            }
        """)

        layout = QHBoxLayout(item)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 模型图标
        try:
            icon_label = QLabel()
            icon_label.setPixmap(get_icon("ai", 16).pixmap(16, 16))
            layout.addWidget(icon_label)
        except:
            layout.addSpacing(16)

        # 模型信息
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        name_label = QLabel(model_name)
        name_label.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold;")
        info_layout.addWidget(name_label)

        status_label = QLabel("已配置")
        status_label.setStyleSheet("color: #4caf50; font-size: 10px;")
        info_layout.addWidget(status_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        # 使用时间
        time_label = QLabel(model_info.get("last_used", ""))
        time_label.setStyleSheet("color: #b0b0b0; font-size: 10px;")
        layout.addWidget(time_label)

        return item

    def _on_optimize(self):
        """智能优化"""
        try:
            self.logger.info("AI配置智能优化")
            # 实现智能优化逻辑
            QMessageBox.information(self, "智能优化", "AI配置智能优化功能正在开发中...")
        except Exception as e:
            self.logger.error(f"AI配置智能优化失败: {e}")

    def _on_balance(self):
        """负载均衡"""
        try:
            self.logger.info("AI负载均衡管理")
            # 实现负载均衡逻辑
            QMessageBox.information(self, "负载均衡", "AI负载均衡管理功能正在开发中...")
        except Exception as e:
            self.logger.error(f"AI负载均衡管理失败: {e}")

    def _setup_connections(self):
        """设置信号连接"""
        pass

    def _setup_refresh_timer(self):
        """设置定时刷新"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_status)
        self.refresh_timer.start(30000)  # 每30秒刷新一次

    @error_handler_decorator(
        error_type=ErrorType.CONFIG,
        severity=ErrorSeverity.MEDIUM,
        recovery_action=RecoveryAction.RETRY,
        user_message="获取AI模型配置失败"
    )
    def _get_configured_models(self) -> List[str]:
        """获取已配置的模型列表"""
        try:
            ai_configs = self.config_manager.get_value("ai_models", {})
            if not ai_configs:
                self.logger.info("未找到已配置的AI模型")
            return list(ai_configs.keys())
        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.CONFIG,
                severity=ErrorSeverity.MEDIUM,
                message=f"获取已配置模型失败: {e}",
                exception=e,
                context=ErrorContext(
                    component="QuickAIConfigWidget",
                    operation="_get_configured_models",
                    system_state={"config_key": "ai_models"}
                ),
                recovery_action=RecoveryAction.RETRY,
                user_message="无法获取AI模型配置，请检查配置文件"
            )
            self.error_handler.handle_error(error_info)
            return []

    @error_handler_decorator(
        error_type=ErrorType.CONFIG,
        severity=ErrorSeverity.LOW,
        recovery_action=RecoveryAction.NONE,
        user_message="获取最近使用模型失败"
    )
    def _get_recent_models(self) -> List[tuple]:
        """获取最近使用的模型"""
        try:
            recent_models = self.config_manager.get_value("recent_ai_models", [])
            if not recent_models:
                self.logger.info("未找到最近使用的模型记录")
            return [(model.get("name", ""), model) for model in recent_models]
        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.CONFIG,
                severity=ErrorSeverity.LOW,
                message=f"获取最近使用模型失败: {e}",
                exception=e,
                context=ErrorContext(
                    component="QuickAIConfigWidget",
                    operation="_get_recent_models",
                    system_state={"config_key": "recent_ai_models"}
                ),
                recovery_action=RecoveryAction.NONE,
                user_message="无法获取最近使用的模型记录"
            )
            self.error_handler.handle_error(error_info)
            return []

    @error_handler_decorator(
        error_type=ErrorType.UI,
        severity=ErrorSeverity.MEDIUM,
        recovery_action=RecoveryAction.RETRY,
        user_message="打开AI模型申请对话框失败"
    )
    def _on_apply_model(self):
        """申请AI模型"""
        try:
            dialog = ModelApplicationDialog(self)
            if not dialog:
                raise RuntimeError("无法创建模型申请对话框")

            result = dialog.exec()
            self.logger.info(f"模型申请对话框关闭，结果: {result}")
            self.refresh_status()

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.UI,
                severity=ErrorSeverity.MEDIUM,
                message=f"打开申请对话框失败: {e}",
                exception=e,
                context=ErrorContext(
                    component="QuickAIConfigWidget",
                    operation="_on_apply_model",
                    user_action="点击申请AI模型按钮"
                ),
                recovery_action=RecoveryAction.RETRY,
                user_message="无法打开AI模型申请对话框，请重试"
            )
            self.error_handler.handle_error(error_info, show_dialog=True, parent=self)

    @error_handler_decorator(
        error_type=ErrorType.UI,
        severity=ErrorSeverity.MEDIUM,
        recovery_action=RecoveryAction.RETRY,
        user_message="打开AI模型配置对话框失败"
    )
    def _on_config_params(self):
        """配置参数"""
        try:
            from ..dialogs.ai_model_config_dialog import AIModelConfigDialog

            dialog = AIModelConfigDialog(self)
            if not dialog:
                raise RuntimeError("无法创建模型配置对话框")

            result = dialog.exec()
            self.logger.info(f"模型配置对话框关闭，结果: {result}")
            self.refresh_status()
            self.config_changed.emit()

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.UI,
                severity=ErrorSeverity.MEDIUM,
                message=f"配置参数失败: {e}",
                exception=e,
                context=ErrorContext(
                    component="QuickAIConfigWidget",
                    operation="_on_config_params",
                    user_action="点击配置参数按钮"
                ),
                recovery_action=RecoveryAction.RETRY,
                user_message="无法打开AI模型配置对话框，请重试"
            )
            self.error_handler.handle_error(error_info, show_dialog=True, parent=self)

    @error_handler_decorator(
        error_type=ErrorType.AI,
        severity=ErrorSeverity.MEDIUM,
        recovery_action=RecoveryAction.RETRY,
        user_message="AI模型连接测试失败"
    )
    def _on_test_connection(self):
        """测试连接"""
        try:
            from ..dialogs.ai_model_config_dialog import AIModelConfigDialog

            configured_models = self._get_configured_models()
            if not configured_models:
                QMessageBox.information(self, "提示", "请先申请并配置AI模型")
                return

            # 打开配置对话框进行连接测试
            dialog = AIModelConfigDialog(self)
            if not dialog:
                raise RuntimeError("无法创建模型配置对话框")

            dialog.config_tabs.setCurrentIndex(1)  # 切换到连接测试选项卡
            result = dialog.exec()
            self.logger.info(f"连接测试对话框关闭，结果: {result}")
            self.refresh_status()

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.AI,
                severity=ErrorSeverity.MEDIUM,
                message=f"测试连接失败: {e}",
                exception=e,
                context=ErrorContext(
                    component="QuickAIConfigWidget",
                    operation="_on_test_connection",
                    user_action="点击测试连接按钮",
                    system_state={"configured_models": configured_models}
                ),
                recovery_action=RecoveryAction.RETRY,
                user_message="无法进行AI模型连接测试，请检查网络连接和配置"
            )
            self.error_handler.handle_error(error_info, show_dialog=True, parent=self)

    @error_handler_decorator(
        error_type=ErrorType.UI,
        severity=ErrorSeverity.LOW,
        recovery_action=RecoveryAction.NONE,
        user_message="打开帮助文档失败"
    )
    def _on_view_docs(self):
        """查看文档"""
        try:
            import webbrowser
            # 打开本地文档
            doc_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                                 "docs", "AI_SETUP_GUIDE.md")
            if os.path.exists(doc_path):
                webbrowser.open(f"file://{doc_path}")
                self.logger.info(f"已打开本地文档: {doc_path}")
            else:
                # 打开在线文档
                webbrowser.open("https://github.com/agions/docs")
                self.logger.info("已打开在线文档")

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.UI,
                severity=ErrorSeverity.LOW,
                message=f"打开文档失败: {e}",
                exception=e,
                context=ErrorContext(
                    component="QuickAIConfigWidget",
                    operation="_on_view_docs",
                    user_action="点击查看文档按钮"
                ),
                recovery_action=RecoveryAction.NONE,
                user_message="无法打开帮助文档，请手动访问官方网站"
            )
            self.error_handler.handle_error(error_info, show_dialog=False)

    @error_handler_decorator(
        error_type=ErrorType.UI,
        severity=ErrorSeverity.LOW,
        recovery_action=RecoveryAction.NONE,
        user_message="刷新状态失败"
    )
    def refresh_status(self):
        """刷新状态"""
        try:
            # 重新创建状态区域
            self._refresh_status_section()
            self.logger.debug("刷新AI配置状态")
        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.UI,
                severity=ErrorSeverity.LOW,
                message=f"刷新状态失败: {e}",
                exception=e,
                context=ErrorContext(
                    component="QuickAIConfigWidget",
                    operation="refresh_status",
                    user_action="自动刷新状态"
                ),
                recovery_action=RecoveryAction.NONE,
                user_message="状态刷新失败，部分信息可能不是最新的"
            )
            self.error_handler.handle_error(error_info, show_dialog=False)

    def _refresh_status_section(self):
        """刷新状态区域"""
        # 找到状态概览部件并刷新
        try:
            # 查找状态概览部件
            for i in range(self.layout().count()):
                widget = self.layout().itemAt(i).widget()
                if widget and widget.objectName() == "status_overview":
                    widget.deleteLater()
                    break

            # 创建新的状态概览
            status_widget = self._create_status_overview()
            status_widget.setObjectName("status_overview")
            self.layout().insertWidget(1, status_widget)

        except Exception as e:
            self.logger.error(f"Failed to refresh status section: {e}")