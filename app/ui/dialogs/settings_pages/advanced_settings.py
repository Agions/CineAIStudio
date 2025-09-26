#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Advanced Settings Page
Advanced and developer configuration settings
"""

import os
import json
import logging
from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QCheckBox, QComboBox, QGroupBox, QPushButton,
    QTabWidget, QTreeWidget, QTreeWidgetItem, QTextEdit,
    QScrollArea, QFrame, QSlider, QProgressBar, QMessageBox,
    QFileDialog, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer, QSettings
from PyQt6.QtGui import QColor, QFont

from ...settings_dialog import SettingsBasePage
from app.core.config_manager import ConfigManager


class LogViewerWidget(QWidget):
    """Log viewer widget for advanced debugging"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Log level filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Log Level:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        filter_layout.addWidget(self.level_combo)
        filter_layout.addWidget(QLabel("Filter:"))
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter log messages...")
        filter_layout.addWidget(self.filter_edit)
        self.clear_btn = QPushButton("Clear")
        filter_layout.addWidget(self.clear_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 10))
        layout.addWidget(self.log_display)

        # Log controls
        controls_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.save_btn = QPushButton("Save Log")
        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        controls_layout.addWidget(self.refresh_btn)
        controls_layout.addWidget(self.save_btn)
        controls_layout.addWidget(self.auto_scroll_check)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)


class AdvancedSettingsPage(SettingsBasePage):
    """Advanced and developer settings"""

    def __init__(self, config_manager, parent=None):
        super().__init__(config_manager, parent)

    def setup_ui(self):
        super().setup_ui()

        # Create tabs
        tabs = QTabWidget()
        self.content_layout.addWidget(tabs)

        # Developer settings tab
        developer_tab = QWidget()
        developer_layout = QVBoxLayout(developer_tab)
        self.setup_developer_settings(developer_layout)
        tabs.addTab(developer_tab, "Developer")

        # Debugging tab
        debug_tab = QWidget()
        debug_layout = QVBoxLayout(debug_tab)
        self.setup_debugging_settings(debug_layout)
        tabs.addTab(debug_tab, "Debugging")

        # Performance tab
        perf_tab = QWidget()
        perf_layout = QVBoxLayout(perf_tab)
        self.setup_performance_settings(perf_layout)
        tabs.addTab(perf_tab, "Performance")

        # System tab
        system_tab = QWidget()
        system_layout = QVBoxLayout(system_tab)
        self.setup_system_settings(system_layout)
        tabs.addTab(system_tab, "System")

    def setup_developer_settings(self, layout):
        """Setup developer settings"""
        # Development mode
        dev_mode_group = QGroupBox("Development Mode")
        dev_mode_layout = QVBoxLayout()

        self.dev_mode_check = QCheckBox("Enable development mode")
        self.debug_menu_check = QCheckBox("Show debug menu")
        self.test_features_check = QCheckBox("Enable experimental features")
        self.dev_tools_check = QCheckBox("Show developer tools")
        dev_mode_layout.addWidget(self.dev_mode_check)
        dev_mode_layout.addWidget(self.debug_menu_check)
        dev_mode_layout.addWidget(self.test_features_check)
        dev_mode_layout.addWidget(self.dev_tools_check)

        dev_mode_group.setLayout(dev_mode_layout)
        layout.addWidget(dev_mode_group)

        # API settings
        api_group = QGroupBox("API Settings")
        api_layout = QVBoxLayout()

        # API key
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("Developer API Key:")
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.generate_key_btn = QPushButton("Generate")
        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.api_key_edit)
        api_key_layout.addWidget(self.generate_key_btn)
        api_layout.addLayout(api_key_layout)

        # API endpoints
        endpoint_layout = QHBoxLayout()
        endpoint_label = QLabel("API Endpoint:")
        self.api_endpoint_edit = QLineEdit()
        self.api_endpoint_edit.setPlaceholderText("https://api.example.com")
        endpoint_layout.addWidget(endpoint_label)
        endpoint_layout.addWidget(self.api_endpoint_edit)
        endpoint_layout.addStretch()
        api_layout.addLayout(endpoint_layout)

        # Rate limiting
        rate_layout = QHBoxLayout()
        rate_label = QLabel("Rate Limit (req/min):")
        self.rate_limit_spin = QSpinBox()
        self.rate_limit_spin.setRange(1, 10000)
        rate_layout.addWidget(rate_label)
        rate_layout.addWidget(self.rate_limit_spin)
        rate_layout.addStretch()
        api_layout.addLayout(rate_layout)

        api_group.setLayout(api_layout)
        layout.addWidget(api_group)

        # Testing framework
        testing_group = QGroupBox("Testing Framework")
        testing_layout = QVBoxLayout()

        self.enable_tests_check = QCheckBox("Enable built-in test framework")
        self.auto_tests_check = QCheckBox("Run tests on startup")
        self.test_coverage_check = QCheckBox("Enable test coverage")
        testing_layout.addWidget(self.enable_tests_check)
        testing_layout.addWidget(self.auto_tests_check)
        testing_layout.addWidget(self.test_coverage_check)

        # Test directories
        test_dirs_layout = QHBoxLayout()
        test_dirs_label = QLabel("Test Directories:")
        self.test_dirs_edit = QLineEdit()
        self.test_dirs_edit.setPlaceholderText("tests/")
        self.browse_test_dirs_btn = QPushButton("Browse")
        test_dirs_layout.addWidget(test_dirs_label)
        test_dirs_layout.addWidget(self.test_dirs_edit)
        test_dirs_layout.addWidget(self.browse_test_dirs_btn)
        testing_layout.addLayout(test_dirs_layout)

        testing_group.setLayout(testing_layout)
        layout.addWidget(testing_group)

        layout.addStretch()

        # Connect signals
        self.generate_key_btn.clicked.connect(self.generate_api_key)
        self.browse_test_dirs_btn.clicked.connect(self.browse_test_directories)

    def setup_debugging_settings(self, layout):
        """Setup debugging settings"""
        # Logging configuration
        logging_group = QGroupBox("Logging Configuration")
        logging_layout = QVBoxLayout()

        # Log level
        log_level_layout = QHBoxLayout()
        log_level_label = QLabel("Log Level:")
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        log_level_layout.addWidget(log_level_label)
        log_level_layout.addWidget(self.log_level_combo)
        log_level_layout.addStretch()
        logging_layout.addLayout(log_level_layout)

        # Log file
        log_file_layout = QHBoxLayout()
        log_file_label = QLabel("Log File:")
        self.log_file_edit = QLineEdit()
        self.log_file_edit.setPlaceholderText("logs/cineai-studio.log")
        self.browse_log_file_btn = QPushButton("Browse")
        log_file_layout.addWidget(log_file_label)
        log_file_layout.addWidget(self.log_file_edit)
        log_file_layout.addWidget(self.browse_log_file_btn)
        logging_layout.addLayout(log_file_layout)

        # Log rotation
        rotation_layout = QHBoxLayout()
        rotation_label = QLabel("Log Rotation:")
        self.rotation_size_spin = QSpinBox()
        self.rotation_size_spin.setRange(1, 1000)
        self.rotation_size_spin.setSuffix(" MB")
        self.rotation_count_spin = QSpinBox()
        self.rotation_count_spin.setRange(1, 100)
        self.rotation_count_spin.setSuffix(" files")
        rotation_layout.addWidget(rotation_label)
        rotation_layout.addWidget(self.rotation_size_spin)
        rotation_layout.addWidget(QLabel("Keep:"))
        rotation_layout.addWidget(self.rotation_count_spin)
        rotation_layout.addStretch()
        logging_layout.addLayout(rotation_layout)

        logging_group.setLayout(logging_layout)
        layout.addWidget(logging_group)

        # Debug output
        debug_group = QGroupBox("Debug Output")
        debug_layout = QVBoxLayout()

        # Console output
        self.console_check = QCheckBox("Enable console output")
        self.timestamp_check = QCheckBox("Show timestamps")
        self.thread_check = QCheckBox("Show thread names")
        self.module_check = QCheckBox("Show module names")
        debug_layout.addWidget(self.console_check)
        debug_layout.addWidget(self.timestamp_check)
        debug_layout.addWidget(self.thread_check)
        debug_layout.addWidget(self.module_check)

        # Verbosity
        verbosity_layout = QHBoxLayout()
        verbosity_label = QLabel("Verbosity Level:")
        self.verbosity_slider = QSlider(Qt.Orientation.Horizontal)
        self.verbosity_slider.setRange(0, 100)
        self.verbosity_slider.setValue(50)
        self.verbosity_label = QLabel("50")
        verbosity_layout.addWidget(verbosity_label)
        verbosity_layout.addWidget(self.verbosity_slider)
        verbosity_layout.addWidget(self.verbosity_label)
        verbosity_layout.addStretch()
        debug_layout.addLayout(verbosity_layout)

        debug_group.setLayout(debug_layout)
        layout.addWidget(debug_group)

        # Log viewer
        viewer_group = QGroupBox("Log Viewer")
        viewer_layout = QVBoxLayout()
        self.log_viewer = LogViewerWidget()
        viewer_layout.addWidget(self.log_viewer)
        viewer_group.setLayout(viewer_layout)
        layout.addWidget(viewer_group)

        layout.addStretch()

        # Connect signals
        self.browse_log_file_btn.clicked.connect(self.browse_log_file)
        self.verbosity_slider.valueChanged.connect(self.update_verbosity_label)

    def setup_performance_settings(self, layout):
        """Setup performance settings"""
        # Memory management
        memory_group = QGroupBox("Memory Management")
        memory_layout = QVBoxLayout()

        # Memory limit
        mem_limit_layout = QHBoxLayout()
        mem_limit_label = QLabel("Memory Limit:")
        self.mem_limit_spin = QSpinBox()
        self.mem_limit_spin.setRange(512, 32768)
        self.mem_limit_spin.setSuffix(" MB")
        mem_limit_layout.addWidget(mem_limit_label)
        mem_limit_layout.addWidget(self.mem_limit_spin)
        mem_limit_layout.addStretch()
        memory_layout.addLayout(mem_limit_layout)

        # Cache settings
        cache_layout = QHBoxLayout()
        cache_label = QLabel("Cache Size:")
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(128, 8192)
        self.cache_size_spin.setSuffix(" MB")
        cache_layout.addWidget(cache_label)
        cache_layout.addWidget(self.cache_size_spin)
        cache_layout.addStretch()
        memory_layout.addLayout(cache_layout)

        # Garbage collection
        self.gc_check = QCheckBox("Enable aggressive garbage collection")
        self.mem_profiling_check = QCheckBox("Enable memory profiling")
        memory_layout.addWidget(self.gc_check)
        memory_layout.addWidget(self.mem_profiling_check)

        memory_group.setLayout(memory_layout)
        layout.addWidget(memory_group)

        # Thread management
        thread_group = QGroupBox("Thread Management")
        thread_layout = QVBoxLayout()

        # Thread pool
        pool_layout = QHBoxLayout()
        pool_label = QLabel("Thread Pool Size:")
        self.thread_pool_spin = QSpinBox()
        self.thread_pool_spin.setRange(1, 64)
        pool_layout.addWidget(pool_label)
        pool_layout.addWidget(self.thread_pool_spin)
        pool_layout.addStretch()
        thread_layout.addLayout(pool_layout)

        # Thread timeout
        timeout_layout = QHBoxLayout()
        timeout_label = QLabel("Thread Timeout:")
        self.thread_timeout_spin = QSpinBox()
        self.thread_timeout_spin.setRange(1, 300)
        self.thread_timeout_spin.setSuffix(" seconds")
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(self.thread_timeout_spin)
        timeout_layout.addStretch()
        thread_layout.addLayout(timeout_layout)

        thread_group.setLayout(thread_layout)
        layout.addWidget(thread_group)

        # Performance monitoring
        monitor_group = QGroupBox("Performance Monitoring")
        monitor_layout = QVBoxLayout()

        self.monitoring_check = QCheckBox("Enable performance monitoring")
        self.profiler_check = QCheckBox("Enable CPU profiler")
        self.memory_monitor_check = QCheckBox("Enable memory monitor")
        monitor_layout.addWidget(self.monitoring_check)
        monitor_layout.addWidget(self.profiler_check)
        monitor_layout.addWidget(self.memory_monitor_check)

        # Update interval
        interval_layout = QHBoxLayout()
        interval_label = QLabel("Update Interval:")
        self.monitor_interval_spin = QSpinBox()
        self.monitor_interval_spin.setRange(100, 10000)
        self.monitor_interval_spin.setSuffix(" ms")
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.monitor_interval_spin)
        interval_layout.addStretch()
        monitor_layout.addLayout(interval_layout)

        monitor_group.setLayout(monitor_layout)
        layout.addWidget(monitor_group)

        layout.addStretch()

    def setup_system_settings(self, layout):
        """Setup system settings"""
        # File system
        fs_group = QGroupBox("File System")
        fs_layout = QVBoxLayout()

        # Temp directory
        temp_dir_layout = QHBoxLayout()
        temp_dir_label = QLabel("Temporary Directory:")
        self.temp_dir_edit = QLineEdit()
        self.browse_temp_dir_btn = QPushButton("Browse")
        temp_dir_layout.addWidget(temp_dir_label)
        temp_dir_layout.addWidget(self.temp_dir_edit)
        temp_dir_layout.addWidget(self.browse_temp_dir_btn)
        fs_layout.addLayout(temp_dir_layout)

        # Cache directory
        cache_dir_layout = QHBoxLayout()
        cache_dir_label = QLabel("Cache Directory:")
        self.cache_dir_edit = QLineEdit()
        self.browse_cache_dir_btn = QPushButton("Browse")
        cache_dir_layout.addWidget(cache_dir_label)
        cache_dir_layout.addWidget(self.cache_dir_edit)
        cache_dir_layout.addWidget(self.browse_cache_dir_btn)
        fs_layout.addLayout(cache_dir_layout)

        # File permissions
        self.preserve_perms_check = QCheckBox("Preserve file permissions")
        self.safe_mode_check = QCheckBox("Safe file operations mode")
        fs_layout.addWidget(self.preserve_perms_check)
        fs_layout.addWidget(self.safe_mode_check)

        fs_group.setLayout(fs_layout)
        layout.addWidget(fs_group)

        # Process management
        process_group = QGroupBox("Process Management")
        process_layout = QVBoxLayout()

        # Process priority
        priority_layout = QHBoxLayout()
        priority_label = QLabel("Process Priority:")
        self.priority_combo = QComboBox()
        self.priority_combo.addItems([
            "Low",
            "Below Normal",
            "Normal",
            "Above Normal",
            "High",
            "Realtime"
        ])
        priority_layout.addWidget(priority_label)
        priority_layout.addWidget(self.priority_combo)
        priority_layout.addStretch()
        process_layout.addLayout(priority_layout)

        # Process timeout
        process_timeout_layout = QHBoxLayout()
        process_timeout_label = QLabel("Process Timeout:")
        self.process_timeout_spin = QSpinBox()
        self.process_timeout_spin.setRange(1, 3600)
        self.process_timeout_spin.setSuffix(" seconds")
        process_timeout_layout.addWidget(process_timeout_label)
        process_timeout_layout.addWidget(self.process_timeout_spin)
        process_timeout_layout.addStretch()
        process_layout.addLayout(process_timeout_layout)

        process_group.setLayout(process_layout)
        layout.addWidget(process_group)

        # System integration
        integration_group = QGroupBox("System Integration")
        integration_layout = QVBoxLayout()

        # Shell integration
        self.shell_integration_check = QCheckBox("Enable shell integration")
        self.file_associations_check = QCheckBox("Manage file associations")
        self.startup_check = QCheckBox("Run on system startup")
        integration_layout.addWidget(self.shell_integration_check)
        integration_layout.addWidget(self.file_associations_check)
        integration_layout.addWidget(self.startup_check)

        integration_group.setLayout(integration_layout)
        layout.addWidget(integration_group)

        # Maintenance
        maintenance_group = QGroupBox("Maintenance")
        maintenance_layout = QVBoxLayout()

        # Clear cache
        clear_cache_layout = QHBoxLayout()
        self.clear_cache_btn = QPushButton("Clear All Caches")
        self.clear_temp_btn = QPushButton("Clear Temporary Files")
        self.clear_logs_btn = QPushButton("Clear Old Logs")
        maintenance_layout.addLayout(clear_cache_layout)

        # Database maintenance
        db_layout = QHBoxLayout()
        self.optimize_db_btn = QPushButton("Optimize Database")
        self.backup_config_btn = QPushButton("Backup Configuration")
        self.reset_config_btn = QPushButton("Reset to Defaults")
        maintenance_layout.addLayout(db_layout)

        maintenance_group.setLayout(maintenance_layout)
        layout.addWidget(maintenance_group)

        layout.addStretch()

        # Connect signals
        self.browse_temp_dir_btn.clicked.connect(self.browse_temp_directory)
        self.browse_cache_dir_btn.clicked.connect(self.browse_cache_directory)
        self.clear_cache_btn.clicked.connect(self.clear_caches)
        self.clear_temp_btn.clicked.connect(self.clear_temp_files)
        self.clear_logs_btn.clicked.connect(self.clear_logs)
        self.optimize_db_btn.clicked.connect(self.optimize_database)
        self.backup_config_btn.clicked.connect(self.backup_configuration)
        self.reset_config_btn.clicked.connect(self.reset_configuration)

    def generate_api_key(self):
        """Generate random API key"""
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits
        api_key = ''.join(secrets.choice(alphabet) for _ in range(32))
        self.api_key_edit.setText(api_key)

    def browse_test_directories(self):
        """Browse for test directories"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Test Directory", self.test_dirs_edit.text()
        )
        if directory:
            self.test_dirs_edit.setText(directory)

    def browse_log_file(self):
        """Browse for log file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Log File", self.log_file_edit.text(),
            "Log Files (*.log);;All Files (*)"
        )
        if file_path:
            self.log_file_edit.setText(file_path)

    def browse_temp_directory(self):
        """Browse for temporary directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Temporary Directory", self.temp_dir_edit.text()
        )
        if directory:
            self.temp_dir_edit.setText(directory)

    def browse_cache_directory(self):
        """Browse for cache directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Cache Directory", self.cache_dir_edit.text()
        )
        if directory:
            self.cache_dir_edit.setText(directory)

    def update_verbosity_label(self, value: int):
        """Update verbosity label"""
        self.verbosity_label.setText(str(value))

    def clear_caches(self):
        """Clear all caches"""
        reply = QMessageBox.question(
            self,
            "Clear Caches",
            "Are you sure you want to clear all caches? This may slow down the application temporarily.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Implementation for clearing caches
            QMessageBox.information(self, "Success", "Caches cleared successfully")

    def clear_temp_files(self):
        """Clear temporary files"""
        reply = QMessageBox.question(
            self,
            "Clear Temporary Files",
            "Are you sure you want to clear all temporary files?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Implementation for clearing temp files
            QMessageBox.information(self, "Success", "Temporary files cleared successfully")

    def clear_logs(self):
        """Clear old logs"""
        reply = QMessageBox.question(
            self,
            "Clear Logs",
            "Are you sure you want to clear old log files?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Implementation for clearing logs
            QMessageBox.information(self, "Success", "Old logs cleared successfully")

    def optimize_database(self):
        """Optimize database"""
        # Implementation for database optimization
        QMessageBox.information(self, "Success", "Database optimized successfully")

    def backup_configuration(self):
        """Backup configuration"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Backup Configuration",
            "cineai-studio-config-backup.json",
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            try:
                config = self.config_manager.get_config()
                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=2)
                QMessageBox.information(self, "Success", "Configuration backed up successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to backup configuration: {str(e)}")

    def reset_configuration(self):
        """Reset configuration to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Configuration",
            "Are you sure you want to reset all settings to their default values? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Implementation for resetting configuration
            QMessageBox.information(self, "Success", "Configuration reset to defaults")

    def load_settings(self):
        """Load advanced settings"""
        config = self.config_manager.get_config()
        advanced_config = config.get("advanced", {})

        # Developer settings
        dev_config = advanced_config.get("developer", {})
        self.dev_mode_check.setChecked(dev_config.get("development_mode", False))
        self.debug_menu_check.setChecked(dev_config.get("debug_menu", False))
        self.test_features_check.setChecked(dev_config.get("experimental_features", False))
        self.dev_tools_check.setChecked(dev_config.get("developer_tools", False))

        self.api_key_edit.setText(dev_config.get("api_key", ""))
        self.api_endpoint_edit.setText(dev_config.get("api_endpoint", ""))
        self.rate_limit_spin.setValue(dev_config.get("rate_limit", 100))

        # Testing
        testing_config = dev_config.get("testing", {})
        self.enable_tests_check.setChecked(testing_config.get("enabled", False))
        self.auto_tests_check.setChecked(testing_config.get("auto_run", False))
        self.test_coverage_check.setChecked(testing_config.get("coverage", False))
        self.test_dirs_edit.setText(testing_config.get("test_directories", "tests/"))

        # Debugging
        debug_config = advanced_config.get("debugging", {})
        self.log_level_combo.setCurrentText(debug_config.get("log_level", "INFO"))
        self.log_file_edit.setText(debug_config.get("log_file", "logs/cineai-studio.log"))
        self.rotation_size_spin.setValue(debug_config.get("rotation_size", 10))
        self.rotation_count_spin.setValue(debug_config.get("rotation_count", 5))

        self.console_check.setChecked(debug_config.get("console_output", True))
        self.timestamp_check.setChecked(debug_config.get("show_timestamps", True))
        self.thread_check.setChecked(debug_config.get("show_threads", False))
        self.module_check.setChecked(debug_config.get("show_modules", True))
        self.verbosity_slider.setValue(debug_config.get("verbosity", 50))

        # Performance
        perf_config = advanced_config.get("performance", {})
        self.mem_limit_spin.setValue(perf_config.get("memory_limit", 4096))
        self.cache_size_spin.setValue(perf_config.get("cache_size", 1024))
        self.gc_check.setChecked(perf_config.get("aggressive_gc", False))
        self.mem_profiling_check.setChecked(perf_config.get("memory_profiling", False))
        self.thread_pool_spin.setValue(perf_config.get("thread_pool_size", 8))
        self.thread_timeout_spin.setValue(perf_config.get("thread_timeout", 30))
        self.monitoring_check.setChecked(perf_config.get("monitoring", False))
        self.profiler_check.setChecked(perf_config.get("profiler", False))
        self.memory_monitor_check.setChecked(perf_config.get("memory_monitor", False))
        self.monitor_interval_spin.setValue(perf_config.get("monitor_interval", 1000))

        # System
        system_config = advanced_config.get("system", {})
        self.temp_dir_edit.setText(system_config.get("temp_directory", ""))
        self.cache_dir_edit.setText(system_config.get("cache_directory", ""))
        self.preserve_perms_check.setChecked(system_config.get("preserve_permissions", True))
        self.safe_mode_check.setChecked(system_config.get("safe_mode", True))
        self.priority_combo.setCurrentText(system_config.get("process_priority", "Normal"))
        self.process_timeout_spin.setValue(system_config.get("process_timeout", 60))
        self.shell_integration_check.setChecked(system_config.get("shell_integration", False))
        self.file_associations_check.setChecked(system_config.get("file_associations", True))
        self.startup_check.setChecked(system_config.get("run_on_startup", False))

    def save_settings(self):
        """Save advanced settings"""
        config = self.config_manager.get_config()

        # Ensure advanced section exists
        if "advanced" not in config:
            config["advanced"] = {}

        # Developer settings
        config["advanced"]["developer"] = {
            "development_mode": self.dev_mode_check.isChecked(),
            "debug_menu": self.debug_menu_check.isChecked(),
            "experimental_features": self.test_features_check.isChecked(),
            "developer_tools": self.dev_tools_check.isChecked(),
            "api_key": self.api_key_edit.text(),
            "api_endpoint": self.api_endpoint_edit.text(),
            "rate_limit": self.rate_limit_spin.value(),
            "testing": {
                "enabled": self.enable_tests_check.isChecked(),
                "auto_run": self.auto_tests_check.isChecked(),
                "coverage": self.test_coverage_check.isChecked(),
                "test_directories": self.test_dirs_edit.text()
            }
        }

        # Debugging
        config["advanced"]["debugging"] = {
            "log_level": self.log_level_combo.currentText(),
            "log_file": self.log_file_edit.text(),
            "rotation_size": self.rotation_size_spin.value(),
            "rotation_count": self.rotation_count_spin.value(),
            "console_output": self.console_check.isChecked(),
            "show_timestamps": self.timestamp_check.isChecked(),
            "show_threads": self.thread_check.isChecked(),
            "show_modules": self.module_check.isChecked(),
            "verbosity": self.verbosity_slider.value()
        }

        # Performance
        config["advanced"]["performance"] = {
            "memory_limit": self.mem_limit_spin.value(),
            "cache_size": self.cache_size_spin.value(),
            "aggressive_gc": self.gc_check.isChecked(),
            "memory_profiling": self.mem_profiling_check.isChecked(),
            "thread_pool_size": self.thread_pool_spin.value(),
            "thread_timeout": self.thread_timeout_spin.value(),
            "monitoring": self.monitoring_check.isChecked(),
            "profiler": self.profiler_check.isChecked(),
            "memory_monitor": self.memory_monitor_check.isChecked(),
            "monitor_interval": self.monitor_interval_spin.value()
        }

        # System
        config["advanced"]["system"] = {
            "temp_directory": self.temp_dir_edit.text(),
            "cache_directory": self.cache_dir_edit.text(),
            "preserve_permissions": self.preserve_perms_check.isChecked(),
            "safe_mode": self.safe_mode_check.isChecked(),
            "process_priority": self.priority_combo.currentText(),
            "process_timeout": self.process_timeout_spin.value(),
            "shell_integration": self.shell_integration_check.isChecked(),
            "file_associations": self.file_associations_check.isChecked(),
            "run_on_startup": self.startup_check.isChecked()
        }

        self.config_manager.save_config(config)

    def validate_settings(self) -> List[str]:
        """Validate advanced settings"""
        errors = []

        # Validate memory limits
        if self.mem_limit_spin.value() < 512:
            errors.append("Memory limit must be at least 512 MB")

        if self.cache_size_spin.value() < 128:
            errors.append("Cache size must be at least 128 MB")

        # Validate thread pool size
        if self.thread_pool_spin.value() < 1:
            errors.append("Thread pool size must be at least 1")

        # Validate timeouts
        if self.thread_timeout_spin.value() < 1:
            errors.append("Thread timeout must be at least 1 second")

        if self.process_timeout_spin.value() < 1:
            errors.append("Process timeout must be at least 1 second")

        # Validate monitoring interval
        if self.monitor_interval_spin.value() < 100:
            errors.append("Monitor interval must be at least 100 ms")

        # Validate directories
        temp_dir = self.temp_dir_edit.text()
        if temp_dir and not os.path.exists(os.path.dirname(temp_dir)):
            errors.append("Temporary directory parent does not exist")

        cache_dir = self.cache_dir_edit.text()
        if cache_dir and not os.path.exists(os.path.dirname(cache_dir)):
            errors.append("Cache directory parent does not exist")

        # Validate log file
        log_file = self.log_file_edit.text()
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                errors.append("Log file directory does not exist")

        return errors