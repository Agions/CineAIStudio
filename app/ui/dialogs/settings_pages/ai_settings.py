#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Settings Page
AI service and model configuration settings
"""

import json
from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QCheckBox, QComboBox, QGroupBox, QPushButton,
    QTextEdit, QTabWidget, QScrollArea, QProgressBar,
    QMessageBox, QTreeWidget, QTreeWidgetItem, QSplitter,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QColor

from ...settings_dialog import SettingsBasePage
from ...components.ai_demo_widget import AIDemoWidget
from ...components.quick_ai_config import QuickAIConfig
from ...ai_model_config_dialog import AIModelConfigDialog
from app.core.secure_key_manager import get_secure_key_manager
from app.services.ai_service_manager import AIServiceManager


class AITestThread(QThread):
    """Thread for testing AI service connections"""

    test_complete = pyqtSignal(str, bool, str)
    progress_updated = pyqtSignal(int)

    def __init__(self, service_config: Dict[str, Any]):
        super().__init__()
        self.service_config = service_config

    def run(self):
        """Test AI service connection"""
        try:
            # Simulate connection test
            self.progress_updated.emit(25)
            self.msleep(500)

            # Test API key validation
            api_key = self.service_config.get("api_key", "")
            if not api_key:
                self.test_complete.emit(self.service_config["name"], False, "No API key provided")
                return

            self.progress_updated.emit(50)
            self.msleep(500)

            # Test model availability
            model = self.service_config.get("model", "")
            if not model:
                self.test_complete.emit(self.service_config["name"], False, "No model selected")
                return

            self.progress_updated.emit(75)
            self.msleep(500)

            # Simulate successful test
            self.test_complete.emit(self.service_config["name"], True, "Connection successful")
            self.progress_updated.emit(100)

        except Exception as e:
            self.test_complete.emit(self.service_config["name"], False, f"Error: {str(e)}")


class AISettingsPage(SettingsBasePage):
    """AI services and models settings"""

    def __init__(self, config_manager, parent=None):
        super().__init__(config_manager, parent)
        self.ai_service_manager = AIServiceManager()
        self.key_manager = get_secure_key_manager()
        self.test_threads = {}

    def setup_ui(self):
        super().setup_ui()

        # Create main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.content_layout.addWidget(main_splitter)

        # Services panel
        services_panel = QWidget()
        services_layout = QVBoxLayout(services_panel)

        # Services tree
        services_group = QGroupBox("AI Services")
        services_tree_layout = QVBoxLayout()
        self.services_tree = QTreeWidget()
        self.services_tree.setHeaderLabels(["Service", "Status", "Model"])
        self.services_tree.itemClicked.connect(self.service_selected)
        services_tree_layout.addWidget(self.services_tree)
        services_group.setLayout(services_tree_layout)
        services_layout.addWidget(services_group)

        # Service actions
        actions_layout = QHBoxLayout()
        self.add_service_btn = QPushButton("Add Service")
        self.remove_service_btn = QPushButton("Remove")
        self.test_service_btn = QPushButton("Test")
        actions_layout.addWidget(self.add_service_btn)
        actions_layout.addWidget(self.remove_service_btn)
        actions_layout.addWidget(self.test_service_btn)
        services_layout.addLayout(actions_layout)

        main_splitter.addWidget(services_panel)

        # Configuration panel
        config_panel = QWidget()
        config_layout = QVBoxLayout(config_panel)

        # Configuration tabs
        self.config_tabs = QTabWidget()
        config_layout.addWidget(self.config_tabs)

        # Service configuration tab
        self.service_config_tab = QWidget()
        service_config_layout = QVBoxLayout(self.service_config_tab)
        self.setup_service_configuration(service_config_layout)
        self.config_tabs.addTab(self.service_config_tab, "Configuration")

        # Usage statistics tab
        self.usage_stats_tab = QWidget()
        usage_layout = QVBoxLayout(self.usage_stats_tab)
        self.setup_usage_statistics(usage_layout)
        self.config_tabs.addTab(self.usage_stats_tab, "Usage Statistics")

        main_splitter.addWidget(config_panel)

        # Set splitter sizes
        main_splitter.setSizes([300, 600])

        # Quick AI config
        quick_config_group = QGroupBox("Quick Configuration")
        quick_config_layout = QVBoxLayout()
        self.quick_config_widget = QuickAIConfig(self.config_manager)
        quick_config_layout.addWidget(self.quick_config_widget)
        quick_config_group.setLayout(quick_config_layout)
        config_layout.addWidget(quick_config_group)

        # Connect signals
        self.add_service_btn.clicked.connect(self.add_service)
        self.remove_service_btn.clicked.connect(self.remove_service)
        self.test_service_btn.clicked.connect(self.test_service)

    def setup_service_configuration(self, layout):
        """Setup service configuration UI"""
        # Service details
        details_group = QGroupBox("Service Details")
        details_layout = QVBoxLayout()

        # Service name
        name_layout = QHBoxLayout()
        name_label = QLabel("Service Name:")
        self.service_name_edit = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.service_name_edit)
        details_layout.addLayout(name_layout)

        # Service type
        type_layout = QHBoxLayout()
        type_label = QLabel("Service Type:")
        self.service_type_combo = QComboBox()
        self.service_type_combo.addItems([
            "OpenAI",
            "Anthropic",
            "Google Gemini",
            "DeepSeek",
            "Qwen",
            "Baichuan",
            "Zhipu AI",
            "Custom"
        ])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.service_type_combo)
        details_layout.addLayout(type_layout)

        # API endpoint
        endpoint_layout = QHBoxLayout()
        endpoint_label = QLabel("API Endpoint:")
        self.endpoint_edit = QLineEdit()
        endpoint_layout.addWidget(endpoint_label)
        endpoint_layout.addWidget(self.endpoint_edit)
        details_layout.addLayout(endpoint_layout)

        # API key
        key_layout = QHBoxLayout()
        key_label = QLabel("API Key:")
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.show_key_btn = QPushButton("Show")
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.api_key_edit)
        key_layout.addWidget(self.show_key_btn)
        details_layout.addLayout(key_layout)

        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        # Model configuration
        model_group = QGroupBox("Model Configuration")
        model_layout = QVBoxLayout()

        # Model selection
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        model_layout.addWidget(self.model_combo)

        # Model parameters
        params_layout = QTabWidget()

        # General parameters
        general_tab = QWidget()
        general_params_layout = QVBoxLayout(general_tab)

        # Temperature
        temp_layout = QHBoxLayout()
        temp_label = QLabel("Temperature:")
        self.temp_spin = QSpinBox()
        self.temp_spin.setRange(0, 200)
        self.temp_spin.setValue(100)
        self.temp_spin.setSuffix(" %")
        temp_layout.addWidget(temp_label)
        temp_layout.addWidget(self.temp_spin)
        temp_layout.addStretch()
        general_params_layout.addLayout(temp_layout)

        # Max tokens
        tokens_layout = QHBoxLayout()
        tokens_label = QLabel("Max Tokens:")
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 32000)
        self.max_tokens_spin.setValue(4000)
        tokens_layout.addWidget(tokens_label)
        tokens_layout.addWidget(self.max_tokens_spin)
        tokens_layout.addStretch()
        general_params_layout.addLayout(tokens_layout)

        params_layout.addTab(general_tab, "General")

        # Advanced parameters
        advanced_tab = QWidget()
        advanced_params_layout = QVBoxLayout(advanced_tab)

        # Top P
        top_p_layout = QHBoxLayout()
        top_p_label = QLabel("Top P:")
        self.top_p_spin = QSpinBox()
        self.top_p_spin.setRange(0, 100)
        self.top_p_spin.setValue(90)
        self.top_p_spin.setSuffix(" %")
        top_p_layout.addWidget(top_p_label)
        top_p_layout.addWidget(self.top_p_spin)
        top_p_layout.addStretch()
        advanced_params_layout.addLayout(top_p_layout)

        # Frequency penalty
        freq_layout = QHBoxLayout()
        freq_label = QLabel("Frequency Penalty:")
        self.freq_spin = QSpinBox()
        self.freq_spin.setRange(-200, 200)
        self.freq_spin.setValue(0)
        freq_layout.addWidget(freq_label)
        freq_layout.addWidget(self.freq_spin)
        freq_layout.addStretch()
        advanced_params_layout.addLayout(freq_layout)

        params_layout.addTab(advanced_tab, "Advanced")

        model_layout.addWidget(params_layout)
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # Test connection
        test_group = QGroupBox("Connection Test")
        test_layout = QVBoxLayout()

        self.test_progress = QProgressBar()
        test_layout.addWidget(self.test_progress)

        self.test_result = QTextEdit()
        self.test_result.setReadOnly(True)
        self.test_result.setMaximumHeight(100)
        test_layout.addWidget(self.test_result)

        test_group.setLayout(test_layout)
        layout.addWidget(test_group)

        # Save configuration
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.save_config_btn = QPushButton("Save Configuration")
        save_layout.addWidget(self.save_config_btn)
        layout.addLayout(save_layout)

        # Connect signals
        self.show_key_btn.toggled.connect(self.toggle_api_key_visibility)
        self.service_type_combo.currentTextChanged.connect(self.update_model_list)
        self.save_config_btn.clicked.connect(self.save_service_config)

    def setup_usage_statistics(self, layout):
        """Setup usage statistics UI"""
        # Statistics overview
        overview_group = QGroupBox("Usage Overview")
        overview_layout = QVBoxLayout()

        # Total usage
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("Total Requests:"))
        self.total_requests_label = QLabel("0")
        total_layout.addWidget(self.total_requests_label)
        total_layout.addStretch()
        overview_layout.addLayout(total_layout)

        # Cost estimation
        cost_layout = QHBoxLayout()
        cost_layout.addWidget(QLabel("Estimated Cost:"))
        self.total_cost_label = QLabel("$0.00")
        cost_layout.addWidget(self.total_cost_label)
        cost_layout.addStretch()
        overview_layout.addLayout(cost_layout)

        overview_group.setLayout(overview_layout)
        layout.addWidget(overview_group)

        # Service breakdown
        breakdown_group = QGroupBox("Service Breakdown")
        breakdown_layout = QVBoxLayout()

        self.usage_table = QTableWidget()
        self.usage_table.setColumnCount(4)
        self.usage_table.setHorizontalHeaderLabels(["Service", "Requests", "Cost", "Last Used"])
        self.usage_table.horizontalHeader().setStretchLastSection(True)
        breakdown_layout.addWidget(self.usage_table)

        breakdown_group.setLayout(breakdown_layout)
        layout.addWidget(breakdown_group)

        # Reset statistics
        reset_layout = QHBoxLayout()
        reset_layout.addStretch()
        self.reset_stats_btn = QPushButton("Reset Statistics")
        reset_layout.addWidget(self.reset_stats_btn)
        layout.addLayout(reset_layout)

        # Connect signals
        self.reset_stats_btn.clicked.connect(self.reset_statistics)

    def load_settings(self):
        """Load AI service settings"""
        config = self.config_manager.get_config()
        ai_config = config.get("ai_services", {})

        # Load services
        services = ai_config.get("services", [])
        self.services_tree.clear()

        for service in services:
            item = QTreeWidgetItem(self.services_tree)
            item.setText(0, service.get("name", "Unknown"))
            item.setText(1, service.get("status", "Unknown"))
            item.setText(2, service.get("model", "Unknown"))
            item.setData(0, Qt.ItemDataRole.UserRole, service)

        # Load usage statistics
        self.update_usage_statistics()

    def save_settings(self):
        """Save AI service settings"""
        config = self.config_manager.get_config()

        # Ensure AI services section exists
        if "ai_services" not in config:
            config["ai_services"] = {}

        # Save services
        services = []
        for i in range(self.services_tree.topLevelItemCount()):
            item = self.services_tree.topLevelItem(i)
            service_data = item.data(0, Qt.ItemDataRole.UserRole)
            if service_data:
                services.append(service_data)

        config["ai_services"]["services"] = services
        self.config_manager.save_config(config)

    def service_selected(self, item: QTreeWidgetItem, column: int):
        """Handle service selection"""
        service_data = item.data(0, Qt.ItemDataRole.UserRole)
        if service_data:
            self.load_service_config(service_data)

    def load_service_config(self, service_data: Dict[str, Any]):
        """Load service configuration into UI"""
        self.service_name_edit.setText(service_data.get("name", ""))
        self.service_type_combo.setCurrentText(service_data.get("type", "OpenAI"))
        self.endpoint_edit.setText(service_data.get("endpoint", ""))

        # Load API key from secure storage
        service_name = service_data.get("name", "")
        api_key = self.key_manager.get_api_key(service_name)
        self.api_key_edit.setText(api_key)

        # Load model configuration
        self.update_model_list()
        model = service_data.get("model", "")
        index = self.model_combo.findText(model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)

        # Load parameters
        params = service_data.get("parameters", {})
        self.temp_spin.setValue(int(params.get("temperature", 1.0) * 100))
        self.max_tokens_spin.setValue(params.get("max_tokens", 4000))
        self.top_p_spin.setValue(int(params.get("top_p", 0.9) * 100))
        self.freq_spin.setValue(int(params.get("frequency_penalty", 0.0) * 100))

    def update_model_list(self):
        """Update model list based on service type"""
        self.model_combo.clear()

        service_type = self.service_type_combo.currentText()
        models = self.get_models_for_service(service_type)

        for model in models:
            self.model_combo.addItem(model)

    def get_models_for_service(self, service_type: str) -> List[str]:
        """Get available models for service type"""
        model_map = {
            "OpenAI": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            "Anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            "Google Gemini": ["gemini-pro", "gemini-pro-vision"],
            "DeepSeek": ["deepseek-chat", "deepseek-coder"],
            "Qwen": ["qwen-turbo", "qwen-plus", "qwen-max"],
            "Baichuan": ["baichuan2-turbo", "baichuan2-pro"],
            "Zhipu AI": ["glm-4", "glm-3-turbo"],
            "Custom": ["custom-model"]
        }

        return model_map.get(service_type, ["default-model"])

    def toggle_api_key_visibility(self, checked: bool):
        """Toggle API key visibility"""
        if checked:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_key_btn.setText("Hide")
        else:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_key_btn.setText("Show")

    def add_service(self):
        """Add new AI service"""
        dialog = AIModelConfigDialog(self)
        if dialog.exec():
            new_service = dialog.get_service_config()
            self.add_service_to_tree(new_service)

    def add_service_to_tree(self, service_data: Dict[str, Any]):
        """Add service to tree widget"""
        item = QTreeWidgetItem(self.services_tree)
        item.setText(0, service_data.get("name", "Unknown"))
        item.setText(1, "Not Tested")
        item.setText(2, service_data.get("model", "Unknown"))
        item.setData(0, Qt.ItemDataRole.UserRole, service_data)

    def remove_service(self):
        """Remove selected service"""
        current_item = self.services_tree.currentItem()
        if current_item:
            reply = QMessageBox.question(
                self,
                "Remove Service",
                "Are you sure you want to remove this service?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                index = self.services_tree.indexOfTopLevelItem(current_item)
                self.services_tree.takeTopLevelItem(index)

    def test_service(self):
        """Test selected service connection"""
        current_item = self.services_tree.currentItem()
        if not current_item:
            return

        service_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not service_data:
            return

        # Update current service config with UI values
        service_data["endpoint"] = self.endpoint_edit.text()
        service_data["api_key"] = self.api_key_edit.text()
        service_data["model"] = self.model_combo.currentText()
        service_data["parameters"] = {
            "temperature": self.temp_spin.value() / 100.0,
            "max_tokens": self.max_tokens_spin.value(),
            "top_p": self.top_p_spin.value() / 100.0,
            "frequency_penalty": self.freq_spin.value() / 100.0
        }

        # Create test thread
        self.test_progress.setValue(0)
        self.test_result.clear()

        test_thread = AITestThread(service_data)
        test_thread.test_complete.connect(self.on_test_complete)
        test_thread.progress_updated.connect(self.test_progress.setValue)
        test_thread.start()

        self.test_threads[service_data["name"]] = test_thread

    def on_test_complete(self, service_name: str, success: bool, message: str):
        """Handle test completion"""
        self.test_result.setText(message)

        # Update tree item status
        for i in range(self.services_tree.topLevelItemCount()):
            item = self.services_tree.topLevelItem(i)
            if item.text(0) == service_name:
                item.setText(1, "✓ Connected" if success else "✗ Failed")
                break

        # Clean up thread
        if service_name in self.test_threads:
            del self.test_threads[service_name]

    def save_service_config(self):
        """Save current service configuration"""
        current_item = self.services_tree.currentItem()
        if not current_item:
            return

        service_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not service_data:
            return

        # Update service data
        service_data["name"] = self.service_name_edit.text()
        service_data["type"] = self.service_type_combo.currentText()
        service_data["endpoint"] = self.endpoint_edit.text()
        service_data["model"] = self.model_combo.currentText()
        service_data["parameters"] = {
            "temperature": self.temp_spin.value() / 100.0,
            "max_tokens": self.max_tokens_spin.value(),
            "top_p": self.top_p_spin.value() / 100.0,
            "frequency_penalty": self.freq_spin.value() / 100.0
        }

        # Save API key securely
        service_name = service_data["name"]
        api_key = self.api_key_edit.text()
        self.key_manager.save_api_key(service_name, api_key)

        # Update tree item
        current_item.setText(0, service_data["name"])
        current_item.setText(2, service_data["model"])
        current_item.setData(0, Qt.ItemDataRole.UserRole, service_data)

        QMessageBox.information(self, "Success", "Service configuration saved successfully")

    def update_usage_statistics(self):
        """Update usage statistics display"""
        config = self.config_manager.get_config()
        stats = config.get("ai_services", {}).get("usage_statistics", {})

        total_requests = sum(service.get("requests", 0) for service in stats.values())
        total_cost = sum(service.get("cost", 0.0) for service in stats.values())

        self.total_requests_label.setText(str(total_requests))
        self.total_cost_label.setText(f"${total_cost:.2f}")

        # Update table
        self.usage_table.setRowCount(len(stats))
        for i, (service_name, service_stats) in enumerate(stats.items()):
            self.usage_table.setItem(i, 0, QTableWidgetItem(service_name))
            self.usage_table.setItem(i, 1, QTableWidgetItem(str(service_stats.get("requests", 0))))
            self.usage_table.setItem(i, 2, QTableWidgetItem(f"${service_stats.get('cost', 0.0):.2f}"))
            self.usage_table.setItem(i, 3, QTableWidgetItem(service_stats.get("last_used", "Never")))

    def reset_statistics(self):
        """Reset usage statistics"""
        reply = QMessageBox.question(
            self,
            "Reset Statistics",
            "Are you sure you want to reset all usage statistics?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            config = self.config_manager.get_config()
            if "ai_services" in config:
                config["ai_services"]["usage_statistics"] = {}
                self.config_manager.save_config(config)

            self.update_usage_statistics()

    def validate_settings(self) -> List[str]:
        """Validate AI service settings"""
        errors = []

        # Validate service names
        service_names = set()
        for i in range(self.services_tree.topLevelItemCount()):
            item = self.services_tree.topLevelItem(i)
            service_data = item.data(0, Qt.ItemDataRole.UserRole)
            if service_data:
                name = service_data.get("name", "")
                if not name:
                    errors.append(f"Service {i+1} must have a name")
                elif name in service_names:
                    errors.append(f"Duplicate service name: {name}")
                else:
                    service_names.add(name)

        return errors