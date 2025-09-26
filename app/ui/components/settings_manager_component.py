#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Settings Manager Component
Central settings management component for CineAIStudio
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QFrame, QMenu, QAction, QSystemTrayIcon,
    QMessageBox, QToolBar, QToolButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt6.QtGui import QIcon, QAction, QKeySequence

from ..dialogs.settings_dialog import SettingsDialog
from app.core.config_manager import ConfigManager
from app.core.theme_manager import ThemeManager


class SettingsAction(Enum):
    """Settings actions"""
    OPEN_DIALOG = "open_dialog"
    RESET_SETTINGS = "reset_settings"
    BACKUP_SETTINGS = "backup_settings"
    RESTORE_SETTINGS = "restore_settings"
    EXPORT_SETTINGS = "export_settings"
    IMPORT_SETTINGS = "import_settings"


@dataclass
class SettingsPreset:
    """Settings preset configuration"""
    name: str
    description: str
    category: str
    config: Dict[str, Any]
    icon: Optional[str] = None


class SettingsManagerComponent(QWidget):
    """Settings manager component"""

    settings_changed = pyqtSignal(str, object)
    preset_applied = pyqtSignal(str)
    settings_reset = pyqtSignal()

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.theme_manager = ThemeManager()
        self.settings_dialog = None
        self.presets = []
        self.action_callbacks = {}

        self.setup_ui()
        self.load_presets()
        self.setup_connections()

    def setup_ui(self):
        """Setup settings manager UI"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Create toolbar
        self.toolbar = QToolBar()
        self.toolbar.setOrientation(Qt.Orientation.Horizontal)
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(24, 24))

        # Add toolbar actions
        self.setup_toolbar_actions()

        self.layout.addWidget(self.toolbar)

    def setup_toolbar_actions(self):
        """Setup toolbar actions"""
        # Settings dialog action
        settings_action = QAction("Settings", self)
        settings_action.setIcon(self.get_icon("settings"))
        settings_action.setToolTip("Open Settings")
        settings_action.triggered.connect(self.open_settings_dialog)
        self.toolbar.addAction(settings_action)

        # Presets menu
        presets_menu = QMenu("Presets", self)
        self.presets_action = QAction("Presets", self)
        self.presets_action.setIcon(self.get_icon("presets"))
        self.presets_action.setToolTip("Settings Presets")
        self.presets_action.setMenu(presets_menu)
        self.toolbar.addAction(self.presets_action)

        # Separator
        self.toolbar.addSeparator()

        # Quick settings dropdown
        self.quick_settings_combo = QComboBox()
        self.quick_settings_combo.setMaximumWidth(200)
        self.quick_settings_combo.setToolTip("Quick Settings")
        self.quick_settings_combo.addItems([
            "Default Profile",
            "High Performance",
            "Quality Mode",
            "Mobile Optimized"
        ])
        self.quick_settings_combo.currentTextChanged.connect(self.apply_quick_settings)
        self.toolbar.addWidget(self.quick_settings_combo)

        # Theme switcher
        self.theme_combo = QComboBox()
        self.theme_combo.setMaximumWidth(150)
        self.theme_combo.setToolTip("Theme")
        self.theme_combo.addItems(["Dark", "Light", "System"])
        self.theme_combo.currentTextChanged.connect(self.apply_theme)
        self.toolbar.addWidget(self.theme_combo)

        # Separator
        self.toolbar.addSeparator()

        # Advanced actions
        backup_action = QAction("Backup", self)
        backup_action.setIcon(self.get_icon("backup"))
        backup_action.setToolTip("Backup Settings")
        backup_action.triggered.connect(self.backup_settings)
        self.toolbar.addAction(backup_action)

        reset_action = QAction("Reset", self)
        reset_action.setIcon(self.get_icon("reset"))
        reset_action.setToolTip("Reset Settings")
        reset_action.triggered.connect(self.reset_settings)
        self.toolbar.addAction(reset_action)

    def setup_connections(self):
        """Setup signal connections"""
        self.theme_manager.theme_changed.connect(self.on_theme_changed)

    def load_presets(self):
        """Load settings presets"""
        # Built-in presets
        self.presets = [
            SettingsPreset(
                "High Performance",
                "Optimized for maximum performance",
                "Performance",
                {
                    "performance": {
                        "hardware": {"gpu_enabled": True, "memory_limit": 8192},
                        "processing": {"threads": 0, "cache_size": 2048}
                    }
                }
            ),
            SettingsPreset(
                "Quality Mode",
                "Highest quality output",
                "Quality",
                {
                    "export": {
                        "quality": {
                            "resolution": "Source (Keep Original)",
                            "quality_preset": "Slow"
                        }
                    }
                }
            ),
            SettingsPreset(
                "Mobile Optimized",
                "Optimized for mobile devices",
                "Mobile",
                {
                    "export": {
                        "quality": {
                            "resolution": "1280x720 (HD)",
                            "quality_preset": "Fast"
                        }
                    }
                }
            ),
            SettingsPreset(
                "Developer",
                "Development environment settings",
                "Development",
                {
                    "advanced": {
                        "developer": {
                            "development_mode": True,
                            "debug_menu": True
                        }
                    }
                }
            )
        ]

        # Load custom presets from config
        config = self.config_manager.get_config()
        custom_presets = config.get("settings_presets", [])
        for preset_data in custom_presets:
            self.presets.append(SettingsPreset(**preset_data))

        # Update presets menu
        self.update_presets_menu()

    def update_presets_menu(self):
        """Update presets menu"""
        presets_menu = self.presets_action.menu()
        presets_menu.clear()

        # Add built-in presets by category
        categories = {}
        for preset in self.presets:
            if preset.category not in categories:
                categories[preset.category] = []
            categories[preset.category].append(preset)

        for category, category_presets in categories.items():
            if len(categories) > 1:
                category_menu = presets_menu.addMenu(category)
            else:
                category_menu = presets_menu

            for preset in category_presets:
                action = QAction(preset.name, self)
                action.setToolTip(preset.description)
                action.triggered.connect(lambda checked, p=preset: self.apply_preset(p))
                category_menu.addAction(action)

        # Add separator and custom actions
        if len(categories) > 1:
            presets_menu.addSeparator()

        save_action = QAction("Save Current as Preset...", self)
        save_action.triggered.connect(self.save_current_as_preset)
        presets_menu.addAction(save_action)

        import_action = QAction("Import Preset...", self)
        import_action.triggered.connect(self.import_preset)
        presets_menu.addAction(import_action)

    def open_settings_dialog(self):
        """Open settings dialog"""
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(self.config_manager, self)
            self.settings_dialog.settings_applied.connect(self.on_settings_applied)
            self.settings_dialog.settings_reset.connect(self.on_settings_reset)

        self.settings_dialog.show()
        self.settings_dialog.raise_()
        self.settings_dialog.activateWindow()

    def apply_preset(self, preset: SettingsPreset):
        """Apply settings preset"""
        try:
            # Get current config
            config = self.config_manager.get_config()

            # Apply preset configuration
            self.merge_config(config, preset.config)

            # Save updated config
            self.config_manager.save_config(config)

            # Emit signal
            self.preset_applied.emit(preset.name)

            # Show feedback
            QMessageBox.information(
                self,
                "Preset Applied",
                f"Settings preset '{preset.name}' has been applied successfully."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to apply preset: {str(e)}"
            )

    def apply_quick_settings(self, profile_name: str):
        """Apply quick settings profile"""
        profile_configs = {
            "Default Profile": {},
            "High Performance": {
                "performance": {
                    "hardware": {"gpu_enabled": True, "memory_limit": 8192},
                    "processing": {"performance_mode": "Speed"}
                }
            },
            "Quality Mode": {
                "export": {
                    "quality": {"quality_preset": "Very Slow"},
                    "presets": {"smart_optimization": True}
                }
            },
            "Mobile Optimized": {
                "export": {
                    "quality": {"resolution": "1280x720 (HD)"},
                    "presets": {"smart_optimization": True}
                },
                "performance": {
                    "hardware": {"gpu_enabled": False}
                }
            }
        }

        if profile_name in profile_configs:
            config = self.config_manager.get_config()
            profile_config = profile_configs[profile_name]

            self.merge_config(config, profile_config)
            self.config_manager.save_config(config)

            self.settings_changed.emit("quick_settings", profile_name)

    def apply_theme(self, theme_name: str):
        """Apply theme"""
        theme_colors = {
            "Dark": self.theme_manager.get_dark_theme_colors(),
            "Light": self.theme_manager.get_light_theme_colors(),
            "System": None  # Use system theme
        }

        if theme_name in theme_colors:
            colors = theme_colors[theme_name]
            if colors:
                self.theme_manager.apply_theme(theme_name, colors)
            else:
                self.theme_manager.apply_system_theme()

            # Save theme preference
            config = self.config_manager.get_config()
            if "themes" not in config:
                config["themes"] = {}
            config["themes"]["current_theme"] = theme_name
            self.config_manager.save_config(config)

    def backup_settings(self):
        """Backup settings to file"""
        file_path, _ = self.get_save_file(
            "Backup Settings",
            "cineai-studio-settings-backup.json",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                config = self.config_manager.get_config()
                backup_data = {
                    "version": "1.0",
                    "timestamp": self.get_timestamp(),
                    "config": config
                }

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)

                QMessageBox.information(
                    self,
                    "Backup Complete",
                    f"Settings have been backed up to:\n{file_path}"
                )

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Backup Failed",
                    f"Failed to backup settings: {str(e)}"
                )

    def reset_settings(self):
        """Reset settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to their default values?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Reset config to defaults
                default_config = self.config_manager.get_default_config()
                self.config_manager.save_config(default_config)

                # Reload UI components
                self.reload_ui()

                # Emit signal
                self.settings_reset.emit()

                QMessageBox.information(
                    self,
                    "Settings Reset",
                    "All settings have been reset to their default values."
                )

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Reset Failed",
                    f"Failed to reset settings: {str(e)}"
                )

    def save_current_as_preset(self):
        """Save current settings as preset"""
        # This would open a dialog to name and describe the preset
        # For now, just show a placeholder message
        QMessageBox.information(
            self,
            "Save Preset",
            "Save preset functionality will be implemented in a future update."
        )

    def import_preset(self):
        """Import preset from file"""
        file_path, _ = self.get_open_file(
            "Import Preset",
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    preset_data = json.load(f)

                # Validate preset data
                if "name" in preset_data and "config" in preset_data:
                    preset = SettingsPreset(
                        preset_data["name"],
                        preset_data.get("description", ""),
                        preset_data.get("category", "Imported"),
                        preset_data["config"]
                    )

                    self.presets.append(preset)
                    self.update_presets_menu()

                    # Save to config
                    config = self.config_manager.get_config()
                    if "settings_presets" not in config:
                        config["settings_presets"] = []

                    config["settings_presets"].append({
                        "name": preset.name,
                        "description": preset.description,
                        "category": preset.category,
                        "config": preset.config
                    })

                    self.config_manager.save_config(config)

                    QMessageBox.information(
                        self,
                        "Import Complete",
                        f"Preset '{preset.name}' has been imported successfully."
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Invalid Format",
                        "The selected file is not a valid settings preset."
                    )

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Import Failed",
                    f"Failed to import preset: {str(e)}"
                )

    def merge_config(self, base_config: Dict[str, Any], new_config: Dict[str, Any]):
        """Merge new configuration into base configuration"""
        for key, value in new_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self.merge_config(base_config[key], value)
            else:
                base_config[key] = value

    def reload_ui(self):
        """Reload UI components with new settings"""
        # Reload theme
        theme_name = self.theme_combo.currentText()
        self.apply_theme(theme_name)

        # Reload quick settings
        quick_settings = self.quick_settings_combo.currentText()
        self.apply_quick_settings(quick_settings)

    def on_settings_applied(self):
        """Handle settings applied from dialog"""
        self.settings_changed.emit("dialog_applied", None)
        self.reload_ui()

    def on_settings_reset(self):
        """Handle settings reset from dialog"""
        self.settings_reset.emit()
        self.reload_ui()

    def on_theme_changed(self, theme_name: str):
        """Handle theme change"""
        # Update theme combo
        index = self.theme_combo.findText(theme_name, Qt.MatchFlag.MatchExactly)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

    def register_action_callback(self, action: SettingsAction, callback: Callable):
        """Register callback for settings action"""
        self.action_callbacks[action] = callback

    def execute_action(self, action: SettingsAction, *args, **kwargs):
        """Execute settings action"""
        if action in self.action_callbacks:
            self.action_callbacks[action](*args, **kwargs)

    def get_icon(self, name: str) -> QIcon:
        """Get icon by name (placeholder implementation)"""
        # In a real implementation, this would load actual icon files
        return QIcon()

    def get_save_file(self, title: str, default: str, file_filter: str) -> tuple:
        """Get save file path (placeholder)"""
        # In a real implementation, this would use QFileDialog
        return (default, "")

    def get_open_file(self, title: str, default: str, file_filter: str) -> tuple:
        """Get open file path (placeholder)"""
        # In a real implementation, this would use QFileDialog
        return (default, "")

    def get_timestamp(self) -> str:
        """Get current timestamp string"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get specific setting value"""
        config = self.config_manager.get_config()
        keys = key.split('.')
        value = config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set_setting(self, key: str, value: Any):
        """Set specific setting value"""
        config = self.config_manager.get_config()
        keys = key.split('.')
        current = config

        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Set the value
        current[keys[-1]] = value

        # Save config
        self.config_manager.save_config(config)

        # Emit signal
        self.settings_changed.emit(key, value)