#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Editor Settings Page
Editor and workspace configuration settings
"""

import os
from typing import List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox, QGroupBox,
    QPushButton, QColorDialog, QFontDialog, QSlider, QTabWidget,
    QTextEdit, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QFont, QPalette

from ...settings_dialog import SettingsBasePage
from ...components.base_component import BaseComponent


class EditorSettingsPage(SettingsBasePage):
    """Editor and workspace settings"""

    def __init__(self, config_manager, parent=None):
        super().__init__(config_manager, parent)

    def setup_ui(self):
        super().setup_ui()

        # Create tabs for different editor settings
        tabs = QTabWidget()
        self.content_layout.addWidget(tabs)

        # Interface tab
        interface_tab = QWidget()
        interface_layout = QVBoxLayout(interface_tab)
        self.setup_interface_settings(interface_layout)
        tabs.addTab(interface_tab, "Interface")

        # Timeline tab
        timeline_tab = QWidget()
        timeline_layout = QVBoxLayout(timeline_tab)
        self.setup_timeline_settings(timeline_layout)
        tabs.addTab(timeline_tab, "Timeline")

        # Shortcuts tab
        shortcuts_tab = QWidget()
        shortcuts_layout = QVBoxLayout(shortcuts_tab)
        self.setup_shortcuts_settings(shortcuts_layout)
        tabs.addTab(shortcuts_tab, "Shortcuts")

    def setup_interface_settings(self, layout):
        """Setup interface settings"""
        # Window settings
        window_group = QGroupBox("Window")
        window_layout = QVBoxLayout()

        # Startup behavior
        startup_layout = QHBoxLayout()
        startup_label = QLabel("Startup Mode:")
        self.startup_combo = QComboBox()
        self.startup_combo.addItems([
            "Show Welcome Screen",
            "Open Last Project",
            "Create New Project",
            "Show Blank Workspace"
        ])
        startup_layout.addWidget(startup_label)
        startup_layout.addWidget(self.startup_combo)
        startup_layout.addStretch()
        window_layout.addLayout(startup_layout)

        # Window state
        self.remember_window_check = QCheckBox("Remember window position and size")
        self.remember_tabs_check = QCheckBox("Remember open tabs")
        window_layout.addWidget(self.remember_window_check)
        window_layout.addWidget(self.remember_tabs_check)

        window_group.setLayout(window_layout)
        layout.addWidget(window_group)

        # Editor settings
        editor_group = QGroupBox("Editor")
        editor_layout = QVBoxLayout()

        # Auto-save behavior
        autosave_layout = QHBoxLayout()
        self.editor_autosave_check = QCheckBox("Auto-save editor state")
        self.editor_autosave_interval = QSpinBox()
        self.editor_autosave_interval.setRange(1, 30)
        self.editor_autosave_interval.setSuffix(" seconds")
        autosave_layout.addWidget(self.editor_autosave_check)
        autosave_layout.addWidget(self.editor_autosave_interval)
        autosave_layout.addStretch()
        editor_layout.addLayout(autosave_layout)

        # Undo levels
        undo_layout = QHBoxLayout()
        undo_label = QLabel("Undo Levels:")
        self.undo_spin = QSpinBox()
        self.undo_spin.setRange(10, 1000)
        undo_layout.addWidget(undo_label)
        undo_layout.addWidget(self.undo_spin)
        undo_layout.addStretch()
        editor_layout.addLayout(undo_layout)

        # Smooth scrolling
        self.smooth_scroll_check = QCheckBox("Enable smooth scrolling")
        self.animation_check = QCheckBox("Enable interface animations")
        editor_layout.addWidget(self.smooth_scroll_check)
        editor_layout.addWidget(self.animation_check)

        editor_group.setLayout(editor_layout)
        layout.addWidget(editor_group)

        # UI scaling
        scaling_group = QGroupBox("Interface Scaling")
        scaling_layout = QVBoxLayout()

        # Scale factor
        scale_layout = QHBoxLayout()
        scale_label = QLabel("UI Scale:")
        self.scale_combo = QComboBox()
        self.scale_combo.addItems([
            "100% (Normal)",
            "125%",
            "150%",
            "175%",
            "200%"
        ])
        scale_layout.addWidget(scale_label)
        scale_layout.addWidget(self.scale_combo)
        scale_layout.addStretch()
        scaling_layout.addLayout(scale_layout)

        # Font size
        font_layout = QHBoxLayout()
        font_label = QLabel("Font Size:")
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 24)
        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_spin)
        font_layout.addStretch()
        scaling_layout.addLayout(font_layout)

        scaling_group.setLayout(scaling_layout)
        layout.addWidget(scaling_group)

        layout.addStretch()

    def setup_timeline_settings(self, layout):
        """Setup timeline settings"""
        # Timeline display
        display_group = QGroupBox("Timeline Display")
        display_layout = QVBoxLayout()

        # Track height
        track_layout = QHBoxLayout()
        track_label = QLabel("Default Track Height:")
        self.track_height_spin = QSpinBox()
        self.track_height_spin.setRange(20, 200)
        self.track_height_spin.setSuffix(" px")
        track_layout.addWidget(track_label)
        track_layout.addWidget(self.track_height_spin)
        track_layout.addStretch()
        display_layout.addLayout(track_layout)

        # Time format
        time_layout = QHBoxLayout()
        time_label = QLabel("Time Display:")
        self.time_format_combo = QComboBox()
        self.time_format_combo.addItems([
            "HH:MM:SS:FF",
            "HH:MM:SS.mmm",
            "Frames",
            "Seconds"
        ])
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.time_format_combo)
        time_layout.addStretch()
        display_layout.addLayout(time_layout)

        # Thumbnail settings
        self.thumbnails_check = QCheckBox("Show thumbnails on timeline")
        self.waveforms_check = QCheckBox("Show audio waveforms")
        self.keyframes_check = QCheckBox("Show keyframe indicators")
        display_layout.addWidget(self.thumbnails_check)
        display_layout.addWidget(self.waveforms_check)
        display_layout.addWidget(self.keyframes_check)

        display_group.setLayout(display_layout)
        layout.addWidget(display_group)

        # Timeline behavior
        behavior_group = QGroupBox("Timeline Behavior")
        behavior_layout = QVBoxLayout()

        # Snapping
        self.snap_check = QCheckBox("Enable snapping")
        self.snap_threshold_spin = QSpinBox()
        self.snap_threshold_spin.setRange(1, 100)
        self.snap_threshold_spin.setSuffix(" frames")
        snap_layout = QHBoxLayout()
        snap_layout.addWidget(self.snap_check)
        snap_layout.addWidget(self.snap_threshold_spin)
        snap_layout.addStretch()
        behavior_layout.addLayout(snap_layout)

        # Ripple editing
        self.ripple_check = QCheckBox("Enable ripple editing by default")
        self.link_check = QCheckBox("Link clips by default")
        behavior_layout.addWidget(self.ripple_check)
        behavior_layout.addWidget(self.link_check)

        # Zoom behavior
        zoom_layout = QHBoxLayout()
        zoom_label = QLabel("Zoom Sensitivity:")
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(1, 100)
        zoom_layout.addWidget(zoom_label)
        zoom_layout.addWidget(self.zoom_slider)
        behavior_layout.addLayout(zoom_layout)

        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)

        layout.addStretch()

    def setup_shortcuts_settings(self, layout):
        """Setup keyboard shortcuts settings"""
        # Shortcuts table would go here
        # This is a simplified version

        shortcuts_group = QGroupBox("Keyboard Shortcuts")
        shortcuts_layout = QVBoxLayout()

        info_label = QLabel("Keyboard shortcuts configuration will be implemented in a future update.")
        shortcuts_layout.addWidget(info_label)

        # Preset shortcuts
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Shortcut Preset:")
        self.shortcuts_preset_combo = QComboBox()
        self.shortcuts_preset_combo.addItems([
            "Default",
            "Professional",
            "Premiere Pro Style",
            "Final Cut Pro Style"
        ])
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.shortcuts_preset_combo)
        preset_layout.addStretch()
        shortcuts_layout.addLayout(preset_layout)

        shortcuts_group.setLayout(shortcuts_layout)
        layout.addWidget(shortcuts_group)
        layout.addStretch()

    def load_settings(self):
        """Load editor settings"""
        config = self.config_manager.get_config()
        editor_config = config.get("editor", {})

        # Interface settings
        interface_config = editor_config.get("interface", {})
        self.startup_combo.setCurrentText(interface_config.get("startup_mode", "Show Welcome Screen"))
        self.remember_window_check.setChecked(interface_config.get("remember_window", True))
        self.remember_tabs_check.setChecked(interface_config.get("remember_tabs", True))

        # Editor settings
        editor_settings = editor_config.get("editor_settings", {})
        self.editor_autosave_check.setChecked(editor_settings.get("autosave", True))
        self.editor_autosave_interval.setValue(editor_settings.get("autosave_interval", 10))
        self.undo_spin.setValue(editor_settings.get("undo_levels", 100))
        self.smooth_scroll_check.setChecked(editor_settings.get("smooth_scrolling", True))
        self.animation_check.setChecked(editor_settings.get("animations", True))

        # UI scaling
        scaling_config = editor_config.get("scaling", {})
        scale_value = scaling_config.get("scale_factor", 100)
        self.scale_combo.setCurrentText(f"{scale_value}%")
        self.font_spin.setValue(scaling_config.get("font_size", 12))

        # Timeline settings
        timeline_config = editor_config.get("timeline", {})
        self.track_height_spin.setValue(timeline_config.get("track_height", 80))
        self.time_format_combo.setCurrentText(timeline_config.get("time_format", "HH:MM:SS:FF"))
        self.thumbnails_check.setChecked(timeline_config.get("show_thumbnails", True))
        self.waveforms_check.setChecked(timeline_config.get("show_waveforms", True))
        self.keyframes_check.setChecked(timeline_config.get("show_keyframes", True))

        # Timeline behavior
        behavior_config = timeline_config.get("behavior", {})
        self.snap_check.setChecked(behavior_config.get("snapping", True))
        self.snap_threshold_spin.setValue(behavior_config.get("snap_threshold", 10))
        self.ripple_check.setChecked(behavior_config.get("ripple_editing", False))
        self.link_check.setChecked(behavior_config.get("link_clips", False))
        self.zoom_slider.setValue(behavior_config.get("zoom_sensitivity", 50))

    def save_settings(self):
        """Save editor settings"""
        config = self.config_manager.get_config()

        # Ensure editor section exists
        if "editor" not in config:
            config["editor"] = {}

        # Interface settings
        config["editor"]["interface"] = {
            "startup_mode": self.startup_combo.currentText(),
            "remember_window": self.remember_window_check.isChecked(),
            "remember_tabs": self.remember_tabs_check.isChecked()
        }

        # Editor settings
        config["editor"]["editor_settings"] = {
            "autosave": self.editor_autosave_check.isChecked(),
            "autosave_interval": self.editor_autosave_interval.value(),
            "undo_levels": self.undo_spin.value(),
            "smooth_scrolling": self.smooth_scroll_check.isChecked(),
            "animations": self.animation_check.isChecked()
        }

        # UI scaling
        scale_text = self.scale_combo.currentText()
        scale_value = int(scale_text.replace("%", ""))
        config["editor"]["scaling"] = {
            "scale_factor": scale_value,
            "font_size": self.font_spin.value()
        }

        # Timeline settings
        config["editor"]["timeline"] = {
            "track_height": self.track_height_spin.value(),
            "time_format": self.time_format_combo.currentText(),
            "show_thumbnails": self.thumbnails_check.isChecked(),
            "show_waveforms": self.waveforms_check.isChecked(),
            "show_keyframes": self.keyframes_check.isChecked(),
            "behavior": {
                "snapping": self.snap_check.isChecked(),
                "snap_threshold": self.snap_threshold_spin.value(),
                "ripple_editing": self.ripple_check.isChecked(),
                "link_clips": self.link_check.isChecked(),
                "zoom_sensitivity": self.zoom_slider.value()
            }
        }

        self.config_manager.save_config(config)

    def validate_settings(self) -> List[str]:
        """Validate editor settings"""
        errors = []

        # Validate track height
        if self.track_height_spin.value() < 20:
            errors.append("Track height must be at least 20 pixels")

        # Validate font size
        if self.font_spin.value() < 8:
            errors.append("Font size must be at least 8 points")

        return errors