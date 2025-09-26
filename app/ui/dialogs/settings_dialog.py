#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Settings Dialog
Main settings management interface for CineAIStudio
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QTabWidget,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QSlider, QGroupBox,
    QScrollArea, QSplitter, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QFileDialog, QDialogButtonBox, QProgressBar,
    QFrame, QStackedWidget, QToolBar, QToolButton, QMenu,
    QSystemTrayIcon, QApplication
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QTimer, QSize, QPoint, QSettings, QThread,
    pyqtSlot, QUrl, QMimeData
)
from PyQt6.QtGui import (
    QIcon, QFont, QPixmap, QPainter, QColor, QPalette,
    QAction, QKeySequence, QCursor
)

from app.core.config_manager import ConfigManager
from app.core.application_config import ThemeConfig
from app.core.project_settings_manager import ProjectSettingsManager
from app.core.secure_key_manager import get_secure_key_manager
from app.ui.theme.theme_manager import ThemeManager

# Import settings pages
from .settings_pages.editor_settings import EditorSettingsPage
from .settings_pages.ai_settings import AISettingsPage
from .settings_pages.export_settings import ExportSettingsPage
from .settings_pages.themes_settings import ThemesSettingsPage
from .settings_pages.advanced_settings import AdvancedSettingsPage


class SettingsCategory(Enum):
    """Settings categories"""
    GENERAL = "general"
    EDITOR = "editor"
    AI_SERVICES = "ai_services"
    EXPORT = "export"
    PERFORMANCE = "performance"
    THEMES = "themes"
    ADVANCED = "advanced"


@dataclass
class SettingsPageInfo:
    """Settings page information"""
    category: SettingsCategory
    title: str
    icon: str
    description: str
    widget_class: Optional[type] = None


class SettingsBasePage(QWidget):
    """Base class for settings pages"""

    settings_changed = pyqtSignal(str, object)
    settings_applied = pyqtSignal()
    settings_reset = pyqtSignal()

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Setup UI components"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # Add scroll area for content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(10)

        self.scroll_area.setWidget(self.content_widget)
        self.layout.addWidget(self.scroll_area)

    def load_settings(self):
        """Load settings from config manager"""
        pass

    def save_settings(self):
        """Save settings to config manager"""
        # Override in subclasses
        pass

    def reset_settings(self):
        """Reset settings to defaults"""
        pass

    def apply_settings(self):
        """Apply settings changes"""
        self.save_settings()
        self.settings_applied.emit()

    def validate_settings(self) -> List[str]:
        """Validate settings and return list of errors"""
        return []


class GeneralSettingsPage(SettingsBasePage):
    """General application settings page"""

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(config_manager, parent)

    def setup_ui(self):
        super().setup_ui()

        # Application section
        app_group = QGroupBox("Application")
        app_layout = QVBoxLayout()

        # Language selection
        lang_layout = QHBoxLayout()
        lang_label = QLabel("Language:")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English", "中文", "日本語", "한국어"])
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        app_layout.addLayout(lang_layout)

        # Auto-save settings
        autosave_layout = QHBoxLayout()
        self.autosave_check = QCheckBox("Enable auto-save")
        self.autosave_interval = QSpinBox()
        self.autosave_interval.setRange(1, 60)
        self.autosave_interval.setSuffix(" minutes")
        autosave_layout.addWidget(self.autosave_check)
        autosave_layout.addWidget(self.autosave_interval)
        autosave_layout.addStretch()
        app_layout.addLayout(autosave_layout)

        # Backup settings
        backup_layout = QHBoxLayout()
        self.backup_check = QCheckBox("Create backups")
        self.backup_count = QSpinBox()
        self.backup_count.setRange(1, 50)
        self.backup_count.setSuffix(" files")
        backup_layout.addWidget(self.backup_check)
        backup_layout.addWidget(self.backup_count)
        backup_layout.addStretch()
        app_layout.addLayout(backup_layout)

        app_group.setLayout(app_layout)
        self.content_layout.addWidget(app_group)

        # File paths section
        paths_group = QGroupBox("File Paths")
        paths_layout = QVBoxLayout()

        # Working directory
        work_dir_layout = QHBoxLayout()
        work_dir_label = QLabel("Working Directory:")
        self.work_dir_edit = QLineEdit()
        work_dir_browse = QPushButton("Browse...")
        work_dir_layout.addWidget(work_dir_label)
        work_dir_layout.addWidget(self.work_dir_edit)
        work_dir_layout.addWidget(work_dir_browse)
        paths_layout.addLayout(work_dir_layout)

        # Temporary directory
        temp_dir_layout = QHBoxLayout()
        temp_dir_label = QLabel("Temporary Directory:")
        self.temp_dir_edit = QLineEdit()
        temp_dir_browse = QPushButton("Browse...")
        temp_dir_layout.addWidget(temp_dir_label)
        temp_dir_layout.addWidget(self.temp_dir_edit)
        temp_dir_layout.addWidget(temp_dir_browse)
        paths_layout.addLayout(temp_dir_layout)

        paths_group.setLayout(paths_layout)
        self.content_layout.addWidget(paths_group)

        # Add stretch
        self.content_layout.addStretch()

        # Connect signals
        work_dir_browse.clicked.connect(self.browse_work_dir)
        temp_dir_browse.clicked.connect(self.browse_temp_dir)

    def browse_work_dir(self):
        """Browse for working directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Working Directory", self.work_dir_edit.text()
        )
        if directory:
            self.work_dir_edit.setText(directory)

    def browse_temp_dir(self):
        """Browse for temporary directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Temporary Directory", self.temp_dir_edit.text()
        )
        if directory:
            self.temp_dir_edit.setText(directory)

    def load_settings(self):
        """Load general settings"""
        # Language
        lang = self.config_manager.get("general.language", "English")
        self.lang_combo.setCurrentText(lang)

        # Auto-save
        self.autosave_check.setChecked(self.config_manager.get("general.autosave.enabled", True))
        self.autosave_interval.setValue(self.config_manager.get("general.autosave.interval", 5))

        # Backup
        self.backup_check.setChecked(self.config_manager.get("general.backup.enabled", True))
        self.backup_count.setValue(self.config_manager.get("general.backup.max_files", 10))

        # Paths
        self.work_dir_edit.setText(self.config_manager.get("general.paths.working_dir", ""))
        self.temp_dir_edit.setText(self.config_manager.get("general.paths.temp_dir", ""))

    def save_settings(self):
        """Save general settings"""
        # Language
        self.config_manager.set("general.language", self.lang_combo.currentText())

        # Auto-save
        self.config_manager.set("general.autosave.enabled", self.autosave_check.isChecked())
        self.config_manager.set("general.autosave.interval", self.autosave_interval.value())

        # Backup
        self.config_manager.set("general.backup.enabled", self.backup_check.isChecked())
        self.config_manager.set("general.backup.max_files", self.backup_count.value())

        # Paths
        self.config_manager.set("general.paths.working_dir", self.work_dir_edit.text())
        self.config_manager.set("general.paths.temp_dir", self.temp_dir_edit.text())

        self.config_manager.save()

    def validate_settings(self) -> List[str]:
        """Validate general settings"""
        errors = []

        # Validate paths
        work_dir = self.work_dir_edit.text()
        if work_dir and not os.path.exists(work_dir):
            errors.append("Working directory does not exist")

        temp_dir = self.temp_dir_edit.text()
        if temp_dir and not os.path.exists(temp_dir):
            errors.append("Temporary directory does not exist")

        return errors


class PerformanceSettingsPage(SettingsBasePage):
    """Performance and hardware settings page"""

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(config_manager, parent)

    def setup_ui(self):
        super().setup_ui()

        # Hardware acceleration
        hw_group = QGroupBox("Hardware Acceleration")
        hw_layout = QVBoxLayout()

        # GPU acceleration
        self.gpu_check = QCheckBox("Enable GPU acceleration")
        hw_layout.addWidget(self.gpu_check)

        # GPU backend selection
        gpu_backend_layout = QHBoxLayout()
        gpu_backend_label = QLabel("GPU Backend:")
        self.gpu_backend_combo = QComboBox()
        self.gpu_backend_combo.addItems(["Auto", "CUDA", "OpenCL", "Metal", "VAAPI"])
        gpu_backend_layout.addWidget(gpu_backend_label)
        gpu_backend_layout.addWidget(self.gpu_backend_combo)
        gpu_backend_layout.addStretch()
        hw_layout.addLayout(gpu_backend_layout)

        # Memory settings
        mem_layout = QHBoxLayout()
        mem_label = QLabel("GPU Memory Limit:")
        self.mem_limit_spin = QSpinBox()
        self.mem_limit_spin.setRange(512, 16384)
        self.mem_limit_spin.setSuffix(" MB")
        mem_layout.addWidget(mem_label)
        mem_layout.addWidget(self.mem_limit_spin)
        mem_layout.addStretch()
        hw_layout.addLayout(mem_layout)

        hw_group.setLayout(hw_layout)
        self.content_layout.addWidget(hw_group)

        # Processing settings
        proc_group = QGroupBox("Processing")
        proc_layout = QVBoxLayout()

        # Thread count
        threads_layout = QHBoxLayout()
        threads_label = QLabel("Processing Threads:")
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 32)
        self.threads_spin.setSpecialValueText("Auto")
        threads_layout.addWidget(threads_label)
        threads_layout.addWidget(self.threads_spin)
        threads_layout.addStretch()
        proc_layout.addLayout(threads_layout)

        # Cache size
        cache_layout = QHBoxLayout()
        cache_label = QLabel("Cache Size:")
        self.cache_spin = QSpinBox()
        self.cache_spin.setRange(128, 8192)
        self.cache_spin.setSuffix(" MB")
        cache_layout.addWidget(cache_label)
        cache_layout.addWidget(self.cache_spin)
        cache_layout.addStretch()
        proc_layout.addLayout(cache_layout)

        # Performance mode
        perf_layout = QHBoxLayout()
        perf_label = QLabel("Performance Mode:")
        self.perf_combo = QComboBox()
        self.perf_combo.addItems(["Balanced", "Quality", "Speed"])
        perf_layout.addWidget(perf_label)
        perf_layout.addWidget(self.perf_combo)
        perf_layout.addStretch()
        proc_layout.addLayout(perf_layout)

        proc_group.setLayout(proc_layout)
        self.content_layout.addWidget(proc_group)

        # Add stretch
        self.content_layout.addStretch()

    def load_settings(self):
        """Load performance settings"""
        # Hardware acceleration
        self.gpu_check.setChecked(self.config_manager.get("performance.hardware.gpu_enabled", True))
        self.gpu_backend_combo.setCurrentText(self.config_manager.get("performance.hardware.gpu_backend", "Auto"))
        self.mem_limit_spin.setValue(self.config_manager.get("performance.hardware.memory_limit", 4096))

        # Processing
        self.threads_spin.setValue(self.config_manager.get("performance.processing.threads", 0))
        self.cache_spin.setValue(self.config_manager.get("performance.processing.cache_size", 1024))
        self.perf_combo.setCurrentText(self.config_manager.get("performance.processing.performance_mode", "Balanced"))

    def save_settings(self):
        """Save performance settings"""
        # Hardware acceleration
        self.config_manager.set("performance.hardware.gpu_enabled", self.gpu_check.isChecked())
        self.config_manager.set("performance.hardware.gpu_backend", self.gpu_backend_combo.currentText())
        self.config_manager.set("performance.hardware.memory_limit", self.mem_limit_spin.value())

        # Processing
        self.config_manager.set("performance.processing.threads", self.threads_spin.value())
        self.config_manager.set("performance.processing.cache_size", self.cache_spin.value())
        self.config_manager.set("performance.processing.performance_mode", self.perf_combo.currentText())

        self.config_manager.save()


class SettingsDialog(QDialog):
    """Main settings dialog"""

    settings_applied = pyqtSignal()
    settings_reset = pyqtSignal()

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.theme_manager = ThemeManager() if hasattr(ThemeManager, '__init__') else None
        self.current_page = None
        self.pages = {}

        self.setup_ui()
        self.setup_pages()
        self.load_all_settings()

    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)

        # Main layout
        main_layout = QHBoxLayout(self)

        # Sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)

        # Content area
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, 1)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.Reset
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_settings)
        buttons.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(self.reset_settings)

        # Add buttons to layout
        button_layout = QVBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(buttons)
        main_layout.addLayout(button_layout)

    def create_sidebar(self) -> QWidget:
        """Create settings sidebar"""
        sidebar = QWidget()
        sidebar.setMaximumWidth(250)
        sidebar.setMinimumWidth(200)

        layout = QVBoxLayout(sidebar)

        # Title
        title = QLabel("Settings")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Search box
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search settings...")
        self.search_edit.textChanged.connect(self.search_settings)
        layout.addWidget(self.search_edit)

        # Categories tree
        self.categories_tree = QTreeWidget()
        self.categories_tree.setHeaderHidden(True)
        self.categories_tree.setAlternatingRowColors(True)
        self.categories_tree.itemClicked.connect(self.category_selected)
        layout.addWidget(self.categories_tree)

        return sidebar

    def setup_pages(self):
        """Setup settings pages"""
        self.page_info = [
            SettingsPageInfo(
                SettingsCategory.GENERAL,
                "General",
                "settings-general",
                "Application settings, language, and file paths",
                GeneralSettingsPage
            ),
            SettingsPageInfo(
                SettingsCategory.EDITOR,
                "Editor",
                "settings-editor",
                "Editor preferences and workspace configuration",
                EditorSettingsPage
            ),
            SettingsPageInfo(
                SettingsCategory.AI_SERVICES,
                "AI Services",
                "settings-ai",
                "AI model configuration and API settings",
                AISettingsPage
            ),
            SettingsPageInfo(
                SettingsCategory.EXPORT,
                "Export",
                "settings-export",
                "Export formats, quality settings, and presets",
                ExportSettingsPage
            ),
            SettingsPageInfo(
                SettingsCategory.PERFORMANCE,
                "Performance",
                "settings-performance",
                "Hardware acceleration and performance optimization",
                PerformanceSettingsPage
            ),
            SettingsPageInfo(
                SettingsCategory.THEMES,
                "Themes",
                "settings-themes",
                "Appearance and theme customization",
                ThemesSettingsPage
            ),
            SettingsPageInfo(
                SettingsCategory.ADVANCED,
                "Advanced",
                "settings-advanced",
                "Advanced settings and developer options",
                AdvancedSettingsPage
            )
        ]

        # Create category items
        self.category_items = {}
        for info in self.page_info:
            item = QTreeWidgetItem([info.title])
            item.setData(0, Qt.ItemDataRole.UserRole, info.category)
            self.categories_tree.addTopLevelItem(item)
            self.category_items[info.category] = item

            # Create page if widget class is available
            if info.widget_class:
                page = info.widget_class(self.config_manager)
                self.pages[info.category] = page
                self.content_stack.addWidget(page)
                page.settings_applied.connect(self.on_settings_applied)

        # Expand all items
        self.categories_tree.expandAll()

    def category_selected(self, item: QTreeWidgetItem, column: int):
        """Handle category selection"""
        category = item.data(0, Qt.ItemDataRole.UserRole)
        if category in self.pages:
            self.content_stack.setCurrentWidget(self.pages[category])
            self.current_page = self.pages[category]

    def search_settings(self, text: str):
        """Search settings"""
        search_text = text.lower()

        # Filter tree items
        for i, item in enumerate(self.categories_tree.findItems("", Qt.MatchFlag.MatchContains | Qt.MatchFlag.MatchRecursive)):
            info = self.page_info[i]
            visible = (search_text == "" or
                      search_text in info.title.lower() or
                      search_text in info.description.lower())
            item.setHidden(not visible)

    def load_all_settings(self):
        """Load all settings"""
        for page in self.pages.values():
            page.load_settings()

    def apply_settings(self):
        """Apply current settings"""
        if self.current_page:
            errors = self.current_page.validate_settings()
            if errors:
                QMessageBox.warning(
                    self,
                    "Settings Validation",
                    "Please fix the following errors:\n\n" + "\n".join(errors)
                )
                return

            self.current_page.apply_settings()
            self.settings_applied.emit()

    def reset_settings(self):
        """Reset current settings"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.current_page:
                self.current_page.reset_settings()
            self.settings_reset.emit()

    def on_settings_applied(self):
        """Handle settings applied signal"""
        # Update any dependent components
        QApplication.processEvents()

    def accept(self):
        """Handle dialog acceptance"""
        # Apply current page settings
        if self.current_page:
            self.apply_settings()

        super().accept()

    def reject(self):
        """Handle dialog rejection"""
        super().reject()