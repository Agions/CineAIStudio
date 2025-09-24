#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI模型配置对话框
提供AI模型的配置、测试和管理功能
"""

import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QTextEdit, QTabWidget, QWidget, QFrame, QScrollArea,
    QMessageBox, QProgressBar, QGroupBox, QSplitter, QTreeWidget,
    QTreeWidgetItem, QHeaderView, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QThread, pyqtSlot
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor

from ...core.config_manager import ConfigManager
from ...core.logger import Logger
from ...core.icon_manager import get_icon
from ...services.ai_service_manager import AIServiceManager, ServiceStatus
from ...services.chinese_ai_services import ChineseAIServiceFactory
from ...core.secure_key_manager import get_secure_key_manager


class ModelConfigWorker(QThread):
    """模型配置工作线程"""

    config_complete = pyqtSignal(str, bool, str)
    test_complete = pyqtSignal(str, bool, str)
    progress_update = pyqtSignal(int)

    def __init__(self, ai_service_manager: AIServiceManager):
        super().__init__()
        self.ai_service_manager = ai_service_manager
        self.tasks = []

    def add_config_task(self, service_name: str, model_id: str, api_key: str, **kwargs):
        """添加配置任务"""
        self.tasks.append({
            "type": "config",
            "service_name": service_name,
            "model_id": model_id,
            "api_key": api_key,
            "kwargs": kwargs
        })

    def add_test_task(self, service_name: str, model_id: str):
        """添加测试任务"""
        self.tasks.append({
            "type": "test",
            "service_name": service_name,
            "model_id": model_id
        })

    def run(self):
        """执行任务"""
        for i, task in enumerate(self.tasks):
            try:
                if task["type"] == "config":
                    success = self.ai_service_manager.configure_model(
                        task["service_name"],
                        task["model_id"],
                        task["api_key"],
                        **task["kwargs"]
                    )
                    result_msg = "配置成功" if success else "配置失败"
                    self.config_complete.emit(task["service_name"], success, result_msg)

                elif task["type"] == "test":
                    success = self.ai_service_manager.test_connection(
                        task["service_name"],
                        task["model_id"]
                    )
                    result_msg = "连接测试成功" if success else "连接测试失败"
                    self.test_complete.emit(task["service_name"], success, result_msg)

                self.progress_update.emit(int((i + 1) / len(self.tasks) * 100))

            except Exception as e:
                error_msg = f"任务执行失败: {str(e)}"
                if task["type"] == "config":
                    self.config_complete.emit(task["service_name"], False, error_msg)
                else:
                    self.test_complete.emit(task["service_name"], False, error_msg)

            time.sleep(0.5)  # 避免过于频繁的请求


class AIModelConfigDialog(QDialog):
    """AI模型配置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI模型配置")
        self.setFixedSize(900, 700)
        self.setModal(True)

        # 初始化组件
        self.config_manager = ConfigManager()
        self.logger = Logger("AIModelConfigDialog")
        self.ai_service_manager = AIServiceManager(self.logger)
        self.key_manager = get_secure_key_manager()

        # 工作线程
        self.worker = ModelConfigWorker(self.ai_service_manager)
        self.worker.config_complete.connect(self._on_config_complete)
        self.worker.test_complete.connect(self._on_test_complete)
        self.worker.progress_update.connect(self._on_progress_update)

        # 当前配置
        self.current_service = None
        self.current_model = None

        # 初始化UI
        self._init_ui()
        self._load_configurations()

        # 定时刷新状态
        self._setup_status_timer()

    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title_widget = self._create_title_section()
        layout.addWidget(title_widget)

        # 主要内容区域
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 2)

        # 左侧服务列表
        service_list_widget = self._create_service_list()
        main_splitter.addWidget(service_list_widget)

        # 右侧配置区域
        config_widget = self._create_config_area()
        main_splitter.addWidget(config_widget)

        layout.addWidget(main_splitter)

        # 底部按钮区域
        button_widget = self._create_button_section()
        layout.addWidget(button_widget)

    def _create_title_section(self) -> QWidget:
        """创建标题区域"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 图标和标题
        icon_label = QLabel()
        icon_label.setPixmap(get_icon("ai", 32).pixmap(32, 32))
        layout.addWidget(icon_label)

        title_label = QLabel("AI模型配置")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        layout.addWidget(title_label)

        layout.addStretch()

        # 状态指示
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #52c41a; font-size: 14px;")
        layout.addWidget(self.status_label)

        return widget

    def _create_service_list(self) -> QWidget:
        """创建服务列表"""
        widget = QFrame()
        widget.setFrameShape(QFrame.Shape.Box)
        widget.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 列表标题
        list_title = QLabel("AI服务提供商")
        list_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
        layout.addWidget(list_title)

        # 服务树
        self.service_tree = QTreeWidget()
        self.service_tree.setHeaderLabels(["服务", "状态", "模型"])
        self.service_tree.setColumnWidth(0, 150)
        self.service_tree.setColumnWidth(1, 80)
        self.service_tree.setColumnWidth(2, 100)
        self.service_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #e9ecef;
                border-radius: 4px;
                background-color: white;
            }
            QTreeWidget::item {
                padding: 5px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTreeWidget::item:selected {
                background-color: #e6f7ff;
            }
        """)
        self.service_tree.itemClicked.connect(self._on_service_selected)
        layout.addWidget(self.service_tree)

        return widget

    def _create_config_area(self) -> QWidget:
        """创建配置区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 配置选项卡
        self.config_tabs = QTabWidget()
        self.config_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e9ecef;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #1890ff;
            }
        """)

        # 模型配置选项卡
        model_config_tab = self._create_model_config_tab()
        self.config_tabs.addTab(model_config_tab, "模型配置")

        # 连接测试选项卡
        connection_tab = self._create_connection_tab()
        self.config_tabs.addTab(connection_tab, "连接测试")

        # 使用统计选项卡
        stats_tab = self._create_stats_tab()
        self.config_tabs.addTab(stats_tab, "使用统计")

        layout.addWidget(self.config_tabs)

        return widget

    def _create_model_config_tab(self) -> QWidget:
        """创建模型配置选项卡"""
        widget = QScrollArea()
        widget.setWidgetResizable(True)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 服务信息
        self.service_info_group = QGroupBox("服务信息")
        self.service_info_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #495057;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        service_info_layout = QFormLayout(self.service_info_group)

        self.service_name_label = QLabel()
        service_info_layout.addRow("服务商:", self.service_name_label)

        self.service_desc_label = QLabel()
        self.service_desc_label.setWordWrap(True)
        service_info_layout.addRow("描述:", self.service_desc_label)

        layout.addWidget(self.service_info_group)

        # API配置
        api_config_group = QGroupBox("API配置")
        api_config_group.setStyleSheet(self.service_info_group.styleSheet())
        api_config_layout = QFormLayout(api_config_group)

        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(200)
        api_config_layout.addRow("选择模型:", self.model_combo)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("请输入API密钥")
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        api_config_layout.addRow("API密钥:", self.api_key_edit)

        # API密钥格式提示
        self.api_key_hint = QLabel()
        self.api_key_hint.setStyleSheet("color: #8c8c8c; font-size: 11px;")
        self.api_key_hint.setWordWrap(True)
        api_config_layout.addRow("", self.api_key_hint)

        layout.addWidget(api_config_group)

        # 高级配置
        advanced_group = QGroupBox("高级配置")
        advanced_group.setStyleSheet(self.service_info_group.styleSheet())
        advanced_layout = QFormLayout(advanced_group)

        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 10000)
        self.max_tokens_spin.setValue(2000)
        self.max_tokens_spin.setSuffix(" tokens")
        advanced_layout.addRow("最大令牌数:", self.max_tokens_spin)

        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setValue(0.7)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setDecimals(2)
        advanced_layout.addRow("温度:", self.temp_spin)

        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.0, 1.0)
        self.top_p_spin.setValue(0.9)
        self.top_p_spin.setSingleStep(0.05)
        self.top_p_spin.setDecimals(2)
        advanced_layout.addRow("Top-P:", self.top_p_spin)

        layout.addWidget(advanced_group)

        layout.addStretch()

        widget.setWidget(content_widget)
        return widget

    def _create_connection_tab(self) -> QWidget:
        """创建连接测试选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 测试配置
        test_group = QGroupBox("连接测试")
        test_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #495057;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        test_layout = QVBoxLayout(test_group)

        # 测试模型选择
        model_select_layout = QHBoxLayout()
        model_select_layout.addWidget(QLabel("测试模型:"))
        self.test_model_combo = QComboBox()
        self.test_model_combo.setMinimumWidth(200)
        model_select_layout.addWidget(self.test_model_combo)
        model_select_layout.addStretch()
        test_layout.addLayout(model_select_layout)

        # 测试按钮
        self.test_connection_btn = QPushButton(get_icon("network", 16), "测试连接")
        self.test_connection_btn.setFixedSize(120, 36)
        self.test_connection_btn.clicked.connect(self._test_connection)
        test_layout.addWidget(self.test_connection_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(test_group)

        # 测试结果
        result_group = QGroupBox("测试结果")
        result_group.setStyleSheet(test_group.styleSheet())
        result_layout = QVBoxLayout(result_group)

        self.test_result_text = QTextEdit()
        self.test_result_text.setReadOnly(True)
        self.test_result_text.setMaximumHeight(200)
        self.test_result_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        result_layout.addWidget(self.test_result_text)

        layout.addWidget(result_group)

        # 进度条
        self.test_progress = QProgressBar()
        self.test_progress.setVisible(False)
        layout.addWidget(self.test_progress)

        layout.addStretch()

        return widget

    def _create_stats_tab(self) -> QWidget:
        """创建使用统计选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 统计概览
        overview_group = QGroupBox("使用概览")
        overview_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #495057;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        overview_layout = QFormLayout(overview_group)

        self.total_requests_label = QLabel("0")
        overview_layout.addRow("总请求数:", self.total_requests_label)

        self.success_rate_label = QLabel("0%")
        overview_layout.addRow("成功率:", self.success_rate_label)

        self.total_cost_label = QLabel("¥0.00")
        overview_layout.addRow("总成本:", self.total_cost_label)

        self.avg_response_time_label = QLabel("0ms")
        overview_layout.addRow("平均响应时间:", self.avg_response_time_label)

        layout.addWidget(overview_group)

        # 详细统计
        detail_group = QGroupBox("详细统计")
        detail_group.setStyleSheet(overview_group.styleSheet())
        detail_layout = QVBoxLayout(detail_group)

        self.stats_tree = QTreeWidget()
        self.stats_tree.setHeaderLabels(["服务", "模型", "请求数", "成功率", "成本"])
        self.stats_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #e9ecef;
                border-radius: 4px;
                background-color: white;
            }
        """)
        detail_layout.addWidget(self.stats_tree)

        layout.addWidget(detail_group)

        # 刷新按钮
        refresh_btn = QPushButton(get_icon("refresh", 16), "刷新统计")
        refresh_btn.setFixedSize(120, 36)
        refresh_btn.clicked.connect(self._refresh_stats)
        layout.addWidget(refresh_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

        return widget

    def _create_button_section(self) -> QWidget:
        """创建按钮区域"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addStretch()

        # 应用按钮
        self.apply_btn = QPushButton(get_icon("check", 16), "应用配置")
        self.apply_btn.setFixedSize(100, 36)
        self.apply_btn.clicked.connect(self._apply_config)
        layout.addWidget(self.apply_btn)

        # 测试按钮
        self.test_btn = QPushButton(get_icon("network", 16), "测试连接")
        self.test_btn.setFixedSize(100, 36)
        self.test_btn.clicked.connect(self._test_connection)
        layout.addWidget(self.test_btn)

        # 关闭按钮
        self.close_btn = QPushButton(get_icon("close", 16), "关闭")
        self.close_btn.setFixedSize(100, 36)
        self.close_btn.clicked.connect(self.reject)
        layout.addWidget(self.close_btn)

        return widget

    def _load_configurations(self):
        """加载配置"""
        try:
            # 获取所有服务
            services = ChineseAIServiceFactory.get_available_services()

            # 清空树
            self.service_tree.clear()

            for service_name in services:
                service_info = ChineseAIServiceFactory.get_service_info(service_name)

                # 创建服务项
                service_item = QTreeWidgetItem(self.service_tree)
                service_item.setText(0, service_info["name"])
                service_item.setText(1, "未配置")
                service_item.setData(0, Qt.ItemDataRole.UserRole, service_name)

                # 获取已配置的模型
                configured_models = self.ai_service_manager.get_configured_models().get(service_name, [])
                if configured_models:
                    service_item.setText(1, "已配置")
                    service_item.setText(2, f"{len(configured_models)}个模型")

                    # 添加模型子项
                    for model_id in configured_models:
                        model_item = QTreeWidgetItem(service_item)
                        model_item.setText(0, model_id)
                        model_item.setText(1, "已配置")

                service_item.setExpanded(True)

        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")

    def _on_service_selected(self, item: QTreeWidgetItem, column: int):
        """服务选择处理"""
        try:
            service_name = item.data(0, Qt.ItemDataRole.UserRole)
            if not service_name:
                return

            self.current_service = service_name
            service_info = ChineseAIServiceFactory.get_service_info(service_name)

            # 更新服务信息
            self.service_name_label.setText(service_info["name"])
            self.service_desc_label.setText(service_info["description"])

            # 更新模型列表
            self.model_combo.clear()
            service = ChineseAIServiceFactory.create_service(service_name)
            if service:
                available_models = service.get_available_models()
                self.model_combo.addItems(available_models)

                # 更新测试模型列表
                self.test_model_combo.clear()
                configured_models = self.ai_service_manager.get_configured_models().get(service_name, [])
                self.test_model_combo.addItems(configured_models)

            # 更新API密钥提示
            self._update_api_key_hint(service_name)

            # 加载已保存的配置
            self._load_saved_config(service_name)

        except Exception as e:
            self.logger.error(f"选择服务失败: {e}")

    def _update_api_key_hint(self, service_name: str):
        """更新API密钥提示"""
        hints = {
            "wenxin": "格式: client_id|client_secret (从百度云控制台获取)",
            "spark": "格式: api_key|api_secret (从讯飞开放平台获取)",
            "qwen": "格式: API-KEY (从阿里云DashScope控制台获取)",
            "glm": "格式: API密钥 (从智谱AI开放平台获取)",
            "baichuan": "格式: API密钥 (从百川AI平台获取)",
            "moonshot": "格式: API密钥 (从月之暗面平台获取)"
        }

        self.api_key_hint.setText(hints.get(service_name, "请输入API密钥"))

    def _load_saved_config(self, service_name: str):
        """加载已保存的配置"""
        try:
            configured_models = self.ai_service_manager.get_configured_models().get(service_name, [])
            if configured_models:
                # 加载第一个模型的配置
                model_id = configured_models[0]
                key_data = self.key_manager.get_api_key(f"{service_name}_{model_id}")
                if key_data and "api_key" in key_data:
                    self.api_key_edit.setText(key_data["api_key"])

                    # 设置选中的模型
                    index = self.model_combo.findText(model_id)
                    if index >= 0:
                        self.model_combo.setCurrentIndex(index)

        except Exception as e:
            self.logger.error(f"加载保存配置失败: {e}")

    def _apply_config(self):
        """应用配置"""
        if not self.current_service:
            QMessageBox.warning(self, "警告", "请先选择一个AI服务")
            return

        model_id = self.model_combo.currentText()
        api_key = self.api_key_edit.text().strip()

        if not model_id:
            QMessageBox.warning(self, "警告", "请选择一个模型")
            return

        if not api_key:
            QMessageBox.warning(self, "警告", "请输入API密钥")
            return

        # 添加配置任务到工作线程
        self.worker.tasks.clear()
        self.worker.add_config_task(
            self.current_service,
            model_id,
            api_key,
            max_tokens=self.max_tokens_spin.value(),
            temperature=self.temp_spin.value(),
            top_p=self.top_p_spin.value()
        )

        # 显示进度
        self.status_label.setText("正在配置...")
        self.apply_btn.setEnabled(False)

        # 启动工作线程
        self.worker.start()

    def _test_connection(self):
        """测试连接"""
        if not self.current_service:
            QMessageBox.warning(self, "警告", "请先选择一个AI服务")
            return

        # 确定要测试的模型
        if self.config_tabs.currentIndex() == 1:  # 连接测试选项卡
            model_id = self.test_model_combo.currentText()
        else:
            model_id = self.model_combo.currentText()

        if not model_id:
            QMessageBox.warning(self, "警告", "请选择一个模型进行测试")
            return

        # 添加测试任务到工作线程
        self.worker.tasks.clear()
        self.worker.add_test_task(self.current_service, model_id)

        # 显示进度
        self.status_label.setText("正在测试连接...")
        self.test_btn.setEnabled(False)
        self.test_progress.setVisible(True)
        self.test_result_text.clear()

        # 启动工作线程
        self.worker.start()

    def _on_config_complete(self, service_name: str, success: bool, message: str):
        """配置完成处理"""
        self.status_label.setText("就绪")
        self.apply_btn.setEnabled(True)

        if success:
            QMessageBox.information(self, "配置成功", f"{service_name} 配置成功")
            self._load_configurations()  # 刷新服务列表
        else:
            QMessageBox.warning(self, "配置失败", f"{service_name} 配置失败: {message}")

    def _on_test_complete(self, service_name: str, success: bool, message: str):
        """测试完成处理"""
        self.status_label.setText("就绪")
        self.test_btn.setEnabled(False)
        self.test_progress.setVisible(False)

        # 显示测试结果
        result_text = f"服务: {service_name}\n"
        result_text += f"状态: {'成功' if success else '失败'}\n"
        result_text += f"消息: {message}\n"
        result_text += f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"

        self.test_result_text.setText(result_text)

        if success:
            self.test_result_text.setStyleSheet("color: #52c41a;")
        else:
            self.test_result_text.setStyleSheet("color: #ff4d4f;")

    def _on_progress_update(self, progress: int):
        """进度更新处理"""
        self.test_progress.setValue(progress)

    def _refresh_stats(self):
        """刷新统计信息"""
        try:
            # 获取管理器摘要
            summary = self.ai_service_manager.get_summary()

            # 更新概览
            self.total_requests_label.setText(str(summary.get("total_requests", 0)))
            self.total_cost_label.setText(f"¥{summary.get('total_cost', 0):.2f}")

            # 计算成功率
            total = summary.get("total_requests", 0)
            active = summary.get("active_services", 0)
            success_rate = (active / len(summary.get("service_health", {}))) * 100 if summary.get("service_health") else 0
            self.success_rate_label.setText(f"{success_rate:.1f}%")

            # 更新详细统计
            self.stats_tree.clear()
            for service_name, models in summary.get("configured_models", {}).items():
                service_item = QTreeWidgetItem(self.stats_tree)
                service_item.setText(0, service_name)
                service_item.setText(1, f"{len(models)}个模型")

                for model_id in models:
                    model_item = QTreeWidgetItem(service_item)
                    model_item.setText(0, "")
                    model_item.setText(1, model_id)
                    model_item.setText(2, "0")
                    model_item.setText(3, "100%")
                    model_item.setText(4, "¥0.00")

                service_item.setExpanded(True)

        except Exception as e:
            self.logger.error(f"刷新统计失败: {e}")

    def _setup_status_timer(self):
        """设置状态定时器"""
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_service_status)
        self.status_timer.start(5000)  # 每5秒更新一次

    def _update_service_status(self):
        """更新服务状态"""
        try:
            # 这里可以添加实时状态更新逻辑
            pass
        except Exception as e:
            self.logger.error(f"更新服务状态失败: {e}")

    def closeEvent(self, event):
        """关闭事件处理"""
        try:
            # 清理资源
            if self.worker.isRunning():
                self.worker.terminate()
                self.worker.wait(1000)

            # 保存配置
            self.ai_service_manager.cleanup()

        except Exception as e:
            self.logger.error(f"关闭对话框时出错: {e}")

        super().closeEvent(event)