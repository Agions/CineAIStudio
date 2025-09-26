#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI配置管理页面
提供国产AI模型的配置、测试和管理功能
"""

import json
import webbrowser
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QPushButton, QLabel, QFrame, QSpacerItem,
    QSizePolicy, QGroupBox, QStackedWidget, QSplitter,
    QTabWidget, QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QRadioButton, QButtonGroup,
    QFileDialog, QColorDialog, QFontDialog, QMessageBox,
    QSlider, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QListWidget, QListWidgetItem, QProgressBar,
    QFormLayout, QToolButton, QDialog, QDialogButtonBox,
    QSystemTrayIcon, QMenu, QApplication, QStyle
)
from PyQt6.QtCore import (
    Qt, QSize, QTimer, pyqtSignal, QPoint, QRect, QSettings,
    QMimeData, QUrl, QEvent, QRectF, QThread, pyqtSlot
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QFont, QPalette, QColor, QCursor,
    QPainter, QPen, QBrush, QPainterPath, QFontDatabase,
    QDesktopServices, QRegularExpression
)

from ...core.config_manager import ConfigManager
from ...core.logger import Logger
from ...core.icon_manager import get_icon
from ...core.application import Application
from ...services.ai_service_manager import AIServiceManager
from ...services.base_ai_service import ModelStatus, ModelCapability
from ...services.chinese_ai_services import ChineseAIServiceFactory
from ...utils.error_handler import handle_exception
from .base_page import BasePage


class ModelConfigState(Enum):
    """模型配置状态"""
    NOT_CONFIGURED = "not_configured"
    CONFIGURING = "configuring"
    CONFIGURED = "configured"
    ERROR = "error"
    TESTING = "testing"


@dataclass
class ServiceUIState:
    """服务UI状态"""
    service_name: str
    provider_name: str
    is_expanded: bool = False
    is_configured: bool = False
    is_testing: bool = False
    last_error: str = ""


class ModelConfigWidget(QWidget):
    """模型配置部件"""

    config_changed = pyqtSignal(str, str, object)
    test_requested = pyqtSignal(str, str)
    remove_requested = pyqtSignal(str, str)

    def __init__(self, service_name: str, model_id: str, model_info: Dict[str, Any]):
        super().__init__()
        self.service_name = service_name
        self.model_id = model_id
        self.model_info = model_info
        self.config_state = ModelConfigState.NOT_CONFIGURED
        self.is_testing = False

        self._init_ui()
        self._setup_connections()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 模型信息区域
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 6px;
            }
        """)
        info_layout = QHBoxLayout(info_frame)

        # 模型名称和版本
        model_info_layout = QVBoxLayout()
        model_name_label = QLabel(self.model_info.get("name", self.model_id))
        model_name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        model_info_layout.addWidget(model_name_label)

        model_version_label = QLabel(f"版本: {self.model_info.get('version', 'N/A')}")
        model_version_label.setStyleSheet("color: #888888; font-size: 12px;")
        model_info_layout.addWidget(model_version_label)

        info_layout.addLayout(model_info_layout)
        info_layout.addStretch()

        # 状态指示器
        self.status_label = QLabel("未配置")
        self.status_label.setStyleSheet("color: #ff4d4f; font-size: 12px;")
        self.status_icon = QLabel()
        self.status_icon.setFixedSize(16, 16)
        self._update_status_icon(ModelConfigState.NOT_CONFIGURED)

        status_layout = QHBoxLayout()
        status_layout.addWidget(self.status_icon)
        status_layout.addWidget(self.status_label)
        info_layout.addLayout(status_layout)

        layout.addWidget(info_frame)

        # 配置区域
        self.config_frame = QFrame()
        self.config_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.config_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #404040;
                border-radius: 6px;
            }
        """)
        config_layout = QFormLayout(self.config_frame)

        # API密钥输入
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText(f"请输入{self.service_name}的API密钥")
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        config_layout.addRow("API密钥:", self.api_key_edit)

        # 密钥提示
        key_hint_label = QLabel(self._get_key_hint())
        key_hint_label.setStyleSheet("color: #888888; font-size: 11px;")
        key_hint_label.setWordWrap(True)
        config_layout.addRow("", key_hint_label)

        layout.addWidget(self.config_frame)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.configure_btn = QPushButton("配置")
        self.configure_btn.setFixedSize(80, 32)
        self.configure_btn.clicked.connect(self._on_configure_clicked)

        self.test_btn = QPushButton("测试")
        self.test_btn.setFixedSize(80, 32)
        self.test_btn.clicked.connect(self._on_test_clicked)
        self.test_btn.setEnabled(False)

        self.remove_btn = QPushButton("移除")
        self.remove_btn.setFixedSize(80, 32)
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        self.remove_btn.setEnabled(False)

        button_layout.addWidget(self.configure_btn)
        button_layout.addWidget(self.test_btn)
        button_layout.addWidget(self.remove_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # 测试结果区域
        self.test_result_label = QLabel()
        self.test_result_label.setStyleSheet("color: #888888; font-size: 12px;")
        self.test_result_label.setWordWrap(True)
        self.test_result_label.hide()
        layout.addWidget(self.test_result_label)

    def _get_key_hint(self) -> str:
        """获取密钥提示"""
        hints = {
            "wenxin": "格式: client_id|client_secret",
            "spark": "格式: api_key|api_secret",
            "qwen": "直接输入API Key",
            "glm": "直接输入API Key",
            "baichuan": "直接输入API Key",
            "moonshot": "直接输入API Key"
        }
        return hints.get(self.service_name, "请输入API密钥")

    def _setup_connections(self):
        """设置信号连接"""
        self.api_key_edit.textChanged.connect(self._on_api_key_changed)

    def _on_api_key_changed(self, text: str):
        """API密钥变化处理"""
        has_key = bool(text.strip())
        self.configure_btn.setEnabled(has_key)
        self.test_btn.setEnabled(self.config_state == ModelConfigState.CONFIGURED)

    def _on_configure_clicked(self):
        """配置按钮点击处理"""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(self, "提示", "请输入API密钥")
            return

        self.config_state = ModelConfigState.CONFIGURING
        self._update_status()
        self.configure_btn.setEnabled(False)

        # 发送配置请求
        self.config_changed.emit(self.service_name, self.model_id, api_key)

    def _on_test_clicked(self):
        """测试按钮点击处理"""
        if self.config_state != ModelConfigState.CONFIGURED:
            return

        self.is_testing = True
        self._update_status()
        self.test_btn.setEnabled(False)

        # 发送测试请求
        self.test_requested.emit(self.service_name, self.model_id)

    def _on_remove_clicked(self):
        """移除按钮点击处理"""
        reply = QMessageBox.question(
            self,
            "确认移除",
            f"确定要移除 {self.model_info.get('name', self.model_id)} 的配置吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.remove_requested.emit(self.service_name, self.model_id)

    def _update_status(self):
        """更新状态显示"""
        if self.is_testing:
            self.status_label.setText("测试中...")
            self._update_status_icon(ModelConfigState.TESTING)
        elif self.config_state == ModelConfigState.CONFIGURING:
            self.status_label.setText("配置中...")
            self._update_status_icon(ModelConfigState.CONFIGURING)
        elif self.config_state == ModelConfigState.CONFIGURED:
            self.status_label.setText("已配置")
            self._update_status_icon(ModelConfigState.CONFIGURED)
            self.test_btn.setEnabled(True)
            self.remove_btn.setEnabled(True)
        elif self.config_state == ModelConfigState.ERROR:
            self.status_label.setText("配置失败")
            self._update_status_icon(ModelConfigState.ERROR)
        else:
            self.status_label.setText("未配置")
            self._update_status_icon(ModelConfigState.NOT_CONFIGURED)

    def _update_status_icon(self, state: ModelConfigState):
        """更新状态图标"""
        icon_colors = {
            ModelConfigState.NOT_CONFIGURED: "#888888",
            ModelConfigState.CONFIGURING: "#faad14",
            ModelConfigState.CONFIGURED: "#52c41a",
            ModelConfigState.ERROR: "#ff4d4f",
            ModelConfigState.TESTING: "#1890ff"
        }

        color = icon_colors.get(state, "#888888")
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor("transparent"))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(color), 2))
        painter.setBrush(QBrush(QColor(color)))
        painter.drawEllipse(2, 2, 12, 12)
        painter.end()

        self.status_icon.setPixmap(pixmap)

    def set_config_state(self, state: ModelConfigState, error_message: str = ""):
        """设置配置状态"""
        self.config_state = state
        self.is_testing = False
        self._update_status()

        if state == ModelConfigState.CONFIGURED:
            self.configure_btn.setEnabled(True)
            self.test_btn.setEnabled(True)
            self.remove_btn.setEnabled(True)
        elif state == ModelConfigState.ERROR:
            self.configure_btn.setEnabled(True)
            self.test_btn.setEnabled(False)
            self.remove_btn.setEnabled(False)
            if error_message:
                QMessageBox.warning(self, "配置失败", error_message)

    def set_test_result(self, success: bool, message: str = ""):
        """设置测试结果"""
        self.is_testing = False
        self._update_status()

        if success:
            self.test_result_label.setText("✅ 连接测试成功")
            self.test_result_label.setStyleSheet("color: #52c41a; font-size: 12px;")
            QMessageBox.information(self, "测试成功", "连接测试成功！")
        else:
            self.test_result_label.setText(f"❌ 连接测试失败: {message}")
            self.test_result_label.setStyleSheet("color: #ff4d4f; font-size: 12px;")
            QMessageBox.warning(self, "测试失败", f"连接测试失败: {message}")

        self.test_result_label.show()
        self.test_btn.setEnabled(True)


class ServicePanel(QWidget):
    """服务面板"""

    def __init__(self, service_name: str, service_info: Dict[str, Any]):
        super().__init__()
        self.service_name = service_name
        self.service_info = service_info
        self.model_widgets: Dict[str, ModelConfigWidget] = {}
        self.is_expanded = False

        self._init_ui()
        self._load_models()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 服务标题栏
        self.header_frame = QFrame()
        self.header_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.header_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 6px;
            }
        """)
        self.header_frame.mousePressEvent = self._on_header_clicked

        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(10, 10, 10, 10)

        # 服务图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(32, 32)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_service_icon()

        # 服务信息
        info_layout = QVBoxLayout()

        self.service_name_label = QLabel(self.service_info.get("name", self.service_name))
        self.service_name_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #ffffff;")
        info_layout.addWidget(self.service_name_label)

        self.service_desc_label = QLabel(self.service_info.get("description", ""))
        self.service_desc_label.setStyleSheet("color: #888888; font-size: 12px;")
        self.service_desc_label.setWordWrap(True)
        info_layout.addWidget(self.service_desc_label)

        header_layout.addLayout(info_layout)
        header_layout.addStretch()

        # 展开/收起按钮
        self.expand_btn = QToolButton()
        self.expand_btn.setFixedSize(24, 24)
        self.expand_btn.setIcon(get_icon("chevron_right", 16))
        self.expand_btn.setStyleSheet("""
            QToolButton {
                border: none;
                background-color: transparent;
            }
            QToolButton:hover {
                background-color: #404040;
            }
        """)
        self.expand_btn.clicked.connect(self._toggle_expanded)
        header_layout.addWidget(self.expand_btn)

        layout.addWidget(self.header_frame)

        # 模型配置区域
        self.models_container = QWidget()
        self.models_container.hide()
        models_layout = QVBoxLayout(self.models_container)
        models_layout.setContentsMargins(0, 0, 0, 0)
        models_layout.setSpacing(8)

        layout.addWidget(self.models_container)

    def _set_service_icon(self):
        """设置服务图标"""
        # 这里可以根据不同的服务设置不同的图标
        icon_name = f"{self.service_name}"
        icon = get_icon(icon_name, 32)
        if icon:
            self.icon_label.setPixmap(icon.pixmap(32, 32))
        else:
            # 使用默认图标
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor("transparent"))
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor("#1890ff"), 2))
            painter.setBrush(QBrush(QColor("#1890ff")))
            painter.drawEllipse(6, 6, 20, 20)
            painter.end()
            self.icon_label.setPixmap(pixmap)

    def _load_models(self):
        """加载模型"""
        try:
            # 创建服务实例获取模型信息
            service = ChineseAIServiceFactory.create_service(self.service_name)
            if service:
                models = service.get_available_models()
                for model_id in models:
                    model_info = service.get_model_info(model_id)
                    if model_info:
                        self._add_model_widget(model_id, model_info.__dict__)

        except Exception as e:
            print(f"加载模型失败: {e}")

    def _add_model_widget(self, model_id: str, model_info: Dict[str, Any]):
        """添加模型配置部件"""
        model_widget = ModelConfigWidget(self.service_name, model_id, model_info)
        model_widget.config_changed.connect(self._on_model_config_changed)
        model_widget.test_requested.connect(self._on_model_test_requested)
        model_widget.remove_requested.connect(self._on_model_remove_requested)

        self.model_widgets[model_id] = model_widget
        self.models_container.layout().addWidget(model_widget)

    def _toggle_expanded(self):
        """切换展开/收起状态"""
        self.is_expanded = not self.is_expanded
        self.models_container.setVisible(self.is_expanded)

        # 更新按钮图标
        if self.is_expanded:
            self.expand_btn.setIcon(get_icon("chevron_down", 16))
        else:
            self.expand_btn.setIcon(get_icon("chevron_right", 16))

    def _on_header_clicked(self, event):
        """标题栏点击处理"""
        self._toggle_expanded()

    def _on_model_config_changed(self, service_name: str, model_id: str, api_key: str):
        """模型配置变化处理"""
        # 转发信号
        if hasattr(self.parent(), 'model_config_changed'):
            self.parent().model_config_changed.emit(service_name, model_id, api_key)

    def _on_model_test_requested(self, service_name: str, model_id: str):
        """模型测试请求处理"""
        # 转发信号
        if hasattr(self.parent(), 'model_test_requested'):
            self.parent().model_test_requested.emit(service_name, model_id)

    def _on_model_remove_requested(self, service_name: str, model_id: str):
        """模型移除请求处理"""
        # 转发信号
        if hasattr(self.parent(), 'model_remove_requested'):
            self.parent().model_remove_requested.emit(service_name, model_id)

    def set_model_config_state(self, model_id: str, state: ModelConfigState, error_message: str = ""):
        """设置模型配置状态"""
        if model_id in self.model_widgets:
            self.model_widgets[model_id].set_config_state(state, error_message)

    def set_model_test_result(self, model_id: str, success: bool, message: str = ""):
        """设置模型测试结果"""
        if model_id in self.model_widgets:
            self.model_widgets[model_id].set_test_result(success, message)


class AIConfigPage(BasePage):
    """AI配置管理页面"""

    # 信号定义
    model_config_changed = pyqtSignal(str, str, object)  # 模型配置变化
    model_test_requested = pyqtSignal(str, str)  # 模型测试请求
    model_remove_requested = pyqtSignal(str, str)  # 模型移除请求

    def __init__(self, application: Application):
        super().__init__("ai_config", "AI配置", application)
        self.application = application
        self.logger = application.get_service(Logger)
        self.config_manager = application.get_service_by_name("config_manager")
        self.ai_service_manager = None

        # 获取AI服务管理器
        self._get_ai_service_manager()

        self.service_panels: Dict[str, ServicePanel] = {}
        self._init_ui()
        self._setup_connections()

    def _get_ai_service_manager(self):
        """获取AI服务管理器"""
        try:
            self.ai_service_manager = self.application.get_service_by_name("ai_service_manager")
            if not self.ai_service_manager:
                self.logger.warning("AI服务管理器未注册")
        except Exception as e:
            self.logger.error(f"获取AI服务管理器失败: {e}")

    def _init_ui(self):
        """初始化UI"""
        # 设置布局
        self.set_main_layout_margins(20, 20, 20, 20)
        self.set_main_layout_spacing(20)

        # 标题
        title_label = QLabel("国产AI模型配置")
        title_font = QFont("Arial", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.add_widget_to_main_layout(title_label)

        # 描述
        desc_label = QLabel("配置和管理国产AI模型，支持文心一言、讯飞星火、通义千问、智谱AI、百川AI、月之暗面等")
        desc_label.setStyleSheet("color: #888888; font-size: 14px;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        self.add_widget_to_main_layout(desc_label)

        # 统计信息
        stats_frame = QFrame()
        stats_frame.setFrameShape(QFrame.Shape.StyledPanel)
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 6px;
            }
        """)
        stats_layout = QHBoxLayout(stats_frame)

        # 服务状态统计
        self.service_stats_label = QLabel("服务: 0/0")
        self.service_stats_label.setStyleSheet("color: #888888; font-size: 12px;")
        stats_layout.addWidget(self.service_stats_label)

        stats_layout.addWidget(QLabel(" | "))

        # 模型状态统计
        self.model_stats_label = QLabel("模型: 0/0")
        self.model_stats_label.setStyleSheet("color: #888888; font-size: 12px;")
        stats_layout.addWidget(self.model_stats_label)

        stats_layout.addWidget(QLabel(" | "))

        # 总请求数
        self.request_stats_label = QLabel("总请求: 0")
        self.request_stats_label.setStyleSheet("color: #888888; font-size: 12px;")
        stats_layout.addWidget(self.request_stats_label)

        stats_layout.addWidget(QLabel(" | "))

        # 总成本
        self.cost_stats_label = QLabel("总成本: ¥0.00")
        self.cost_stats_label.setStyleSheet("color: #888888; font-size: 12px;")
        stats_layout.addWidget(self.cost_stats_label)

        stats_layout.addStretch()

        # 刷新按钮
        refresh_btn = QPushButton(get_icon("refresh", 16), "刷新")
        refresh_btn.setFixedSize(80, 24)
        refresh_btn.clicked.connect(self._refresh_stats)
        stats_layout.addWidget(refresh_btn)

        self.add_widget_to_main_layout(stats_frame)

        # 服务面板容器
        self.services_container = QWidget()
        services_layout = QVBoxLayout(self.services_container)
        services_layout.setContentsMargins(0, 0, 0, 0)
        services_layout.setSpacing(10)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.services_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarNever)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)

        self.add_widget_to_main_layout(scroll_area)

        # 加载服务面板
        self._load_service_panels()

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # 全部测试按钮
        test_all_btn = QPushButton("全部测试")
        test_all_btn.setFixedSize(100, 32)
        test_all_btn.clicked.connect(self._test_all_models)
        button_layout.addWidget(test_all_btn)

        # 应用设置按钮
        apply_btn = QPushButton("应用设置")
        apply_btn.setFixedSize(100, 32)
        apply_btn.clicked.connect(self._apply_settings)
        button_layout.addWidget(apply_btn)

        self.add_layout_to_main_layout(button_layout)

        # 添加弹簧
        self.add_widget_to_main_layout(QWidget())

    def _setup_connections(self):
        """设置信号连接"""
        # 连接AI服务管理器信号
        if self.ai_service_manager:
            self.ai_service_manager.model_configured.connect(self._on_model_configured)
            self.ai_service_manager.configuration_error.connect(self._on_configuration_error)
            self.ai_service_manager.service_status_changed.connect(self._on_service_status_changed)
            self.ai_service_manager.stats_updated.connect(self._on_stats_updated)

        # 连接页面信号
        self.model_config_changed.connect(self._on_model_config_changed)
        self.model_test_requested.connect(self._on_model_test_requested)
        self.model_remove_requested.connect(self._on_model_remove_requested)

    def _load_service_panels(self):
        """加载服务面板"""
        try:
            services = ChineseAIServiceFactory.get_available_services()
            for service_name in services:
                service_info = ChineseAIServiceFactory.get_service_info(service_name)
                if service_info:
                    panel = ServicePanel(service_name, service_info)
                    panel.model_config_changed.connect(self._on_model_config_changed)
                    panel.model_test_requested.connect(self._on_model_test_requested)
                    panel.model_remove_requested.connect(self._on_model_remove_requested)

                    self.service_panels[service_name] = panel
                    self.services_container.layout().addWidget(panel)

            self._update_stats()

        except Exception as e:
            self.logger.error(f"加载服务面板失败: {e}")

    def _on_model_config_changed(self, service_name: str, model_id: str, api_key: str):
        """模型配置变化处理"""
        if self.ai_service_manager:
            success = self.ai_service_manager.configure_model(service_name, model_id, api_key)
            if success:
                self.service_panels[service_name].set_model_config_state(model_id, ModelConfigState.CONFIGURED)
            else:
                self.service_panels[service_name].set_model_config_state(model_id, ModelConfigState.ERROR, "配置失败")

    def _on_model_test_requested(self, service_name: str, model_id: str):
        """模型测试请求处理"""
        if self.ai_service_manager:
            success = self.ai_service_manager.test_connection(service_name, model_id)
            self.service_panels[service_name].set_model_test_result(model_id, success)

    def _on_model_remove_requested(self, service_name: str, model_id: str):
        """模型移除请求处理"""
        # 这里可以实现移除配置的逻辑
        if hasattr(self.ai_service_manager, 'remove_model_config'):
            self.ai_service_manager.remove_model_config(service_name, model_id)
        self.service_panels[service_name].set_model_config_state(model_id, ModelConfigState.NOT_CONFIGURED)

    def _on_model_configured(self, service_name: str, model_id: str, model_info: object):
        """模型配置完成处理"""
        if service_name in self.service_panels:
            self.service_panels[service_name].set_model_config_state(model_id, ModelConfigState.CONFIGURED)
        self._update_stats()

    def _on_configuration_error(self, service_name: str, error_message: str):
        """配置错误处理"""
        QMessageBox.warning(self, "配置错误", f"{service_name}: {error_message}")

    def _on_service_status_changed(self, service_name: str, status: str):
        """服务状态变化处理"""
        self._update_stats()

    def _on_stats_updated(self, stats: object):
        """统计数据更新处理"""
        self._update_stats()

    def _update_stats(self):
        """更新统计信息"""
        try:
            if self.ai_service_manager:
                summary = self.ai_service_manager.get_summary()

                # 更新服务统计
                self.service_stats_label.setText(f"服务: {summary['active_services']}/{summary['total_services']}")

                # 更新模型统计
                configured_count = sum(len(models) for models in summary['configured_models'].values())
                available_count = sum(len(models) for models in self.ai_service_manager.get_available_models().values())
                self.model_stats_label.setText(f"模型: {configured_count}/{available_count}")

                # 更新请求统计
                self.request_stats_label.setText(f"总请求: {summary['total_requests']}")

                # 更新成本统计
                self.cost_stats_label.setText(f"总成本: ¥{summary['total_cost']:.2f}")

        except Exception as e:
            self.logger.error(f"更新统计失败: {e}")

    def _refresh_stats(self):
        """刷新统计"""
        self._update_stats()

    def _test_all_models(self):
        """测试所有模型"""
        if not self.ai_service_manager:
            return

        configured_models = self.ai_service_manager.get_configured_models()
        total_tests = sum(len(models) for models in configured_models.values())

        if total_tests == 0:
            QMessageBox.information(self, "提示", "没有配置的模型")
            return

        # 创建进度对话框
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle("测试连接")
        progress_dialog.setFixedSize(400, 150)

        layout = QVBoxLayout(progress_dialog)

        label = QLabel("正在测试所有模型连接...")
        layout.addWidget(label)

        progress_bar = QProgressBar()
        progress_bar.setRange(0, total_tests)
        layout.addWidget(progress_bar)

        # 执行测试
        current_test = 0
        for service_name, models in configured_models.items():
            for model_id in models:
                success = self.ai_service_manager.test_connection(service_name, model_id)
                self.service_panels[service_name].set_model_test_result(model_id, success)

                current_test += 1
                progress_bar.setValue(current_test)

                # 更新UI
                QApplication.processEvents()

        progress_dialog.accept()
        QMessageBox.information(self, "测试完成", f"已完成 {total_tests} 个模型的连接测试")

    def _apply_settings(self):
        """应用设置"""
        QMessageBox.information(self, "设置已保存", "AI配置已保存并应用")

    def initialize(self) -> bool:
        """初始化页面"""
        try:
            self.logger.info("AI配置页面初始化开始")

            # 检查AI服务管理器
            if not self.ai_service_manager:
                self.logger.warning("AI服务管理器未初始化")
                return False

            # 加载已配置的模型状态
            self._load_configured_models()

            self.logger.info("AI配置页面初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"AI配置页面初始化失败: {e}")
            return False

    def create_content(self) -> None:
        """创建页面内容"""
        # 内容已在_init_ui中创建
        pass

    def _load_configured_models(self):
        """加载已配置的模型"""
        try:
            if self.ai_service_manager:
                configured_models = self.ai_service_manager.get_configured_models()
                for service_name, models in configured_models.items():
                    if service_name in self.service_panels:
                        for model_id in models:
                            self.service_panels[service_name].set_model_config_state(model_id, ModelConfigState.CONFIGURED)
        except Exception as e:
            self.logger.error(f"加载已配置模型失败: {e}")

    def activate(self) -> None:
        """激活页面"""
        super().activate()
        self._update_stats()

    def refresh(self):
        """刷新页面"""
        self._update_stats()
        self._load_configured_models()

    def get_page_help_url(self) -> str:
        """获取页面帮助URL"""
        return "https://github.com/agions/wiki/AI-Config-Help"