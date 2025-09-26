#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Export Settings Page
Export format and quality configuration settings
"""

import os
from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox, QGroupBox,
    QPushButton, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QScrollArea, QFrame, QSlider, QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QColor

from ...settings_dialog import SettingsBasePage
from ...components.export_settings_component import ExportSettingsComponent
from app.export.enhanced_export_formats import EnhancedExportFormat, EnhancedExportPresets


class ExportSettingsPage(SettingsBasePage):
    """Export format and quality settings"""

    def __init__(self, config_manager, parent=None):
        super().__init__(config_manager, parent)

    def setup_ui(self):
        super().setup_ui()

        # Create tabs
        tabs = QTabWidget()
        self.content_layout.addWidget(tabs)

        # Formats tab
        formats_tab = QWidget()
        formats_layout = QVBoxLayout(formats_tab)
        self.setup_formats_settings(formats_layout)
        tabs.addTab(formats_tab, "Formats")

        # Presets tab
        presets_tab = QWidget()
        presets_layout = QVBoxLayout(presets_tab)
        self.setup_presets_settings(presets_layout)
        tabs.addTab(presets_tab, "Presets")

        # Quality tab
        quality_tab = QWidget()
        quality_layout = QVBoxLayout(quality_tab)
        self.setup_quality_settings(quality_layout)
        tabs.addTab(quality_tab, "Quality")

        # Locations tab
        locations_tab = QWidget()
        locations_layout = QVBoxLayout(locations_tab)
        self.setup_locations_settings(locations_layout)
        tabs.addTab(locations_tab, "Locations")

    def setup_formats_settings(self, layout):
        """Setup export formats settings"""
        # Default format
        default_group = QGroupBox("Default Export Format")
        default_layout = QHBoxLayout()

        default_label = QLabel("Default Format:")
        self.default_format_combo = QComboBox()
        self.populate_format_combo(self.default_format_combo)
        default_layout.addWidget(default_label)
        default_layout.addWidget(self.default_format_combo)
        default_layout.addStretch()

        default_group.setLayout(default_layout)
        layout.addWidget(default_group)

        # Format compatibility
        compatibility_group = QGroupBox("Format Compatibility")
        compatibility_layout = QVBoxLayout()

        # Target platforms
        platforms_layout = QHBoxLayout()
        platforms_label = QLabel("Target Platform:")
        self.target_platform_combo = QComboBox()
        self.target_platform_combo.addItems([
            "Universal",
            "YouTube",
            "Vimeo",
            "Instagram",
            "TikTok",
            "Mobile",
            "Web",
            "Broadcast"
        ])
        platforms_layout.addWidget(platforms_label)
        platforms_layout.addWidget(self.target_platform_combo)
        platforms_layout.addStretch()
        compatibility_layout.addLayout(platforms_layout)

        # Compatibility mode
        self.compatibility_check = QCheckBox("Enable maximum compatibility mode")
        self.legacy_codecs_check = QCheckBox("Include legacy codec support")
        compatibility_layout.addWidget(self.compatibility_check)
        compatibility_layout.addWidget(self.legacy_codecs_check)

        compatibility_group.setLayout(compatibility_layout)
        layout.addWidget(compatibility_group)

        # Advanced format settings
        advanced_group = QGroupBox("Advanced Format Settings")
        advanced_layout = QVBoxLayout()

        # Container options
        container_layout = QHBoxLayout()
        container_label = QLabel("Container Options:")
        self.container_options_combo = QComboBox()
        self.container_options_combo.addItems([
            "Auto",
            "MP4",
            "MOV",
            "MKV",
            "WebM",
            "AVI"
        ])
        container_layout.addWidget(container_label)
        container_layout.addWidget(self.container_options_combo)
        container_layout.addStretch()
        advanced_layout.addLayout(container_layout)

        # Metadata handling
        metadata_layout = QHBoxLayout()
        metadata_label = QLabel("Metadata:")
        self.metadata_combo = QComboBox()
        self.metadata_combo.addItems([
            "Include All",
            "Include Basic",
            "Strip All",
            "Custom"
        ])
        metadata_layout.addWidget(metadata_label)
        metadata_layout.addWidget(self.metadata_combo)
        metadata_layout.addStretch()
        advanced_layout.addLayout(metadata_layout)

        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)

        layout.addStretch()

    def setup_presets_settings(self, layout):
        """Setup export presets settings"""
        # Preset management
        preset_group = QGroupBox("Preset Management")
        preset_layout = QVBoxLayout()

        # Default preset
        default_preset_layout = QHBoxLayout()
        default_preset_label = QLabel("Default Preset:")
        self.default_preset_combo = QComboBox()
        self.populate_preset_combo(self.default_preset_combo)
        default_preset_layout.addWidget(default_preset_label)
        default_preset_layout.addWidget(self.default_preset_combo)
        default_preset_layout.addStretch()
        preset_layout.addLayout(default_preset_layout)

        # Custom presets
        custom_presets_group = QGroupBox("Custom Presets")
        custom_presets_layout = QVBoxLayout()

        # Presets list
        self.presets_tree = QTreeWidget()
        self.presets_tree.setHeaderLabels(["Preset Name", "Format", "Quality", "Description"])
        self.presets_tree.setMaximumHeight(200)
        custom_presets_layout.addWidget(self.presets_tree)

        # Preset actions
        preset_actions_layout = QHBoxLayout()
        self.add_preset_btn = QPushButton("Add Preset")
        self.edit_preset_btn = QPushButton("Edit")
        self.delete_preset_btn = QPushButton("Delete")
        preset_actions_layout.addWidget(self.add_preset_btn)
        preset_actions_layout.addWidget(self.edit_preset_btn)
        preset_actions_layout.addWidget(self.delete_preset_btn)
        custom_presets_layout.addLayout(preset_actions_layout)

        custom_presets_group.setLayout(custom_presets_layout)
        preset_layout.addWidget(custom_presets_group)

        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)

        # Smart preset optimization
        smart_group = QGroupBox("Smart Preset Optimization")
        smart_layout = QVBoxLayout()

        self.enable_optimization_check = QCheckBox("Enable smart preset optimization")
        self.auto_select_check = QCheckBox("Auto-select best preset based on content")
        smart_layout.addWidget(self.enable_optimization_check)
        smart_layout.addWidget(self.auto_select_check)

        # Optimization level
        opt_level_layout = QHBoxLayout()
        opt_level_label = QLabel("Optimization Level:")
        self.opt_level_slider = QSlider(Qt.Orientation.Horizontal)
        self.opt_level_slider.setRange(0, 100)
        self.opt_level_slider.setValue(75)
        opt_level_layout.addWidget(opt_level_label)
        opt_level_layout.addWidget(self.opt_level_slider)
        smart_layout.addLayout(opt_level_layout)

        smart_group.setLayout(smart_layout)
        layout.addWidget(smart_group)

        layout.addStretch()

    def setup_quality_settings(self, layout):
        """Setup quality settings"""
        # Video quality
        video_group = QGroupBox("Video Quality")
        video_layout = QVBoxLayout()

        # Resolution
        res_layout = QHBoxLayout()
        res_label = QLabel("Default Resolution:")
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "Source (Keep Original)",
            "3840x2160 (4K)",
            "2560x1440 (2K)",
            "1920x1080 (Full HD)",
            "1280x720 (HD)",
            "854x480 (SD)",
            "640x360 (Low)",
            "Custom"
        ])
        res_layout.addWidget(res_label)
        res_layout.addWidget(self.resolution_combo)
        res_layout.addStretch()
        video_layout.addLayout(res_layout)

        # Frame rate
        fps_layout = QHBoxLayout()
        fps_label = QLabel("Frame Rate:")
        self.fps_combo = QComboBox()
        self.fps_combo.addItems([
            "Source (Keep Original)",
            "60 fps",
            "30 fps",
            "24 fps",
            "25 fps",
            "50 fps",
            "Custom"
        ])
        fps_layout.addWidget(fps_label)
        fps_layout.addWidget(self.fps_combo)
        fps_layout.addStretch()
        video_layout.addLayout(fps_layout)

        # Bitrate control
        bitrate_layout = QHBoxLayout()
        bitrate_label = QLabel("Bitrate Control:")
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems([
            "Variable (VBR)",
            "Constant (CBR)",
            "Constant Quality (CRF)",
            "Average (ABR)"
        ])
        bitrate_layout.addWidget(bitrate_label)
        bitrate_layout.addWidget(self.bitrate_combo)
        bitrate_layout.addStretch()
        video_layout.addLayout(bitrate_layout)

        # Quality preset
        quality_preset_layout = QHBoxLayout()
        quality_preset_label = QLabel("Quality Preset:")
        self.quality_preset_combo = QComboBox()
        self.quality_preset_combo.addItems([
            "Ultra Fast",
            "Super Fast",
            "Very Fast",
            "Faster",
            "Fast",
            "Medium",
            "Slow",
            "Slower",
            "Very Slow"
        ])
        quality_preset_layout.addWidget(quality_preset_label)
        quality_preset_layout.addWidget(self.quality_preset_combo)
        quality_preset_layout.addStretch()
        video_layout.addLayout(quality_preset_layout)

        video_group.setLayout(video_layout)
        layout.addWidget(video_group)

        # Audio quality
        audio_group = QGroupBox("Audio Quality")
        audio_layout = QVBoxLayout()

        # Audio codec
        audio_codec_layout = QHBoxLayout()
        audio_codec_label = QLabel("Audio Codec:")
        self.audio_codec_combo = QComboBox()
        self.audio_codec_combo.addItems([
            "AAC",
            "MP3",
            "Opus",
            "FLAC",
            "PCM",
            "AC3"
        ])
        audio_codec_layout.addWidget(audio_codec_label)
        audio_codec_layout.addWidget(self.audio_codec_combo)
        audio_codec_layout.addStretch()
        audio_layout.addLayout(audio_codec_layout)

        # Sample rate
        sample_rate_layout = QHBoxLayout()
        sample_rate_label = QLabel("Sample Rate:")
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems([
            "48000 Hz",
            "44100 Hz",
            "32000 Hz",
            "24000 Hz",
            "22050 Hz"
        ])
        sample_rate_layout.addWidget(sample_rate_label)
        sample_rate_layout.addWidget(self.sample_rate_combo)
        sample_rate_layout.addStretch()
        audio_layout.addLayout(sample_rate_layout)

        # Audio bitrate
        audio_bitrate_layout = QHBoxLayout()
        audio_bitrate_label = QLabel("Audio Bitrate:")
        self.audio_bitrate_combo = QComboBox()
        self.audio_bitrate_combo.addItems([
            "320 kbps",
            "256 kbps",
            "192 kbps",
            "128 kbps",
            "96 kbps",
            "64 kbps"
        ])
        audio_bitrate_layout.addWidget(audio_bitrate_label)
        audio_bitrate_layout.addWidget(self.audio_bitrate_combo)
        audio_bitrate_layout.addStretch()
        audio_layout.addLayout(audio_bitrate_layout)

        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)

        layout.addStretch()

    def setup_locations_settings(self, layout):
        """Setup export locations settings"""
        # Default export location
        default_location_group = QGroupBox("Default Export Location")
        default_location_layout = QHBoxLayout()

        self.export_location_edit = QLineEdit()
        self.export_location_browse = QPushButton("Browse...")
        default_location_layout.addWidget(self.export_location_edit)
        default_location_layout.addWidget(self.export_location_browse)

        default_location_group.setLayout(default_location_layout)
        layout.addWidget(default_location_group)

        # File naming
        naming_group = QGroupBox("File Naming")
        naming_layout = QVBoxLayout()

        # Naming pattern
        pattern_layout = QHBoxLayout()
        pattern_label = QLabel("Naming Pattern:")
        self.naming_pattern_edit = QLineEdit()
        self.naming_pattern_edit.setPlaceholderText("{project_name}_{date}_{quality}")
        pattern_layout.addWidget(pattern_label)
        pattern_layout.addWidget(self.naming_pattern_edit)
        pattern_layout.addStretch()
        naming_layout.addLayout(pattern_layout)

        # Naming options
        self.include_date_check = QCheckBox("Include date in filename")
        self.include_time_check = QCheckBox("Include time in filename")
        self.include_quality_check = QCheckBox("Include quality indicator")
        self.include_version_check = QCheckBox("Include version number")
        naming_layout.addWidget(self.include_date_check)
        naming_layout.addWidget(self.include_time_check)
        naming_layout.addWidget(self.include_quality_check)
        naming_layout.addWidget(self.include_version_check)

        naming_group.setLayout(naming_layout)
        layout.addWidget(naming_group)

        # Organization
        organization_group = QGroupBox("File Organization")
        organization_layout = QVBoxLayout()

        # Create subfolders
        self.create_subfolders_check = QCheckBox("Create subfolders by project")
        self.date_folders_check = QCheckBox("Create subfolders by date")
        self.quality_folders_check = QCheckBox("Create subfolders by quality")
        organization_layout.addWidget(self.create_subfolders_check)
        organization_layout.addWidget(self.date_folders_check)
        organization_layout.addWidget(self.quality_folders_check)

        # Folder structure
        folder_layout = QHBoxLayout()
        folder_label = QLabel("Custom Folder Structure:")
        self.folder_structure_edit = QLineEdit()
        self.folder_structure_edit.setPlaceholderText("{project}/{year}/{month}")
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_structure_edit)
        folder_layout.addStretch()
        organization_layout.addLayout(folder_layout)

        organization_group.setLayout(organization_layout)
        layout.addWidget(organization_group)

        layout.addStretch()

        # Connect signals
        self.export_location_browse.clicked.connect(self.browse_export_location)

    def populate_format_combo(self, combo: QComboBox):
        """Populate format combo box"""
        formats = [
            "MP4 (H.264)",
            "MP4 (H.265)",
            "MP4 (AV1)",
            "MOV (ProRes)",
            "WebM (VP9)",
            "MKV (H.264)",
            "AVI (XviD)",
            "GIF",
            "Image Sequence"
        ]

        for format_name in formats:
            combo.addItem(format_name)

    def populate_preset_combo(self, combo: QComboBox):
        """Populate preset combo box"""
        presets = [
            "High Quality 4K",
            "High Quality 1080p",
            "Standard Quality 720p",
            "Web Optimized",
            "Mobile Optimized",
            "Social Media",
            "YouTube Upload",
            "Vimeo Upload"
        ]

        for preset_name in presets:
            combo.addItem(preset_name)

    def browse_export_location(self):
        """Browse for export location"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Export Location", self.export_location_edit.text()
        )
        if directory:
            self.export_location_edit.setText(directory)

    def load_settings(self):
        """Load export settings"""
        config = self.config_manager.get_config()
        export_config = config.get("export", {})

        # Formats
        formats_config = export_config.get("formats", {})
        self.default_format_combo.setCurrentText(formats_config.get("default_format", "MP4 (H.264)"))
        self.target_platform_combo.setCurrentText(formats_config.get("target_platform", "Universal"))
        self.compatibility_check.setChecked(formats_config.get("compatibility_mode", False))
        self.legacy_codecs_check.setChecked(formats_config.get("legacy_codecs", False))
        self.container_options_combo.setCurrentText(formats_config.get("container_options", "Auto"))
        self.metadata_combo.setCurrentText(formats_config.get("metadata", "Include All"))

        # Presets
        presets_config = export_config.get("presets", {})
        self.default_preset_combo.setCurrentText(presets_config.get("default_preset", "High Quality 1080p"))
        self.enable_optimization_check.setChecked(presets_config.get("smart_optimization", True))
        self.auto_select_check.setChecked(presets_config.get("auto_select", True))
        self.opt_level_slider.setValue(presets_config.get("optimization_level", 75))

        # Quality
        quality_config = export_config.get("quality", {})
        self.resolution_combo.setCurrentText(quality_config.get("resolution", "Source (Keep Original)"))
        self.fps_combo.setCurrentText(quality_config.get("frame_rate", "Source (Keep Original)"))
        self.bitrate_combo.setCurrentText(quality_config.get("bitrate_control", "Variable (VBR)"))
        self.quality_preset_combo.setCurrentText(quality_config.get("quality_preset", "Medium"))
        self.audio_codec_combo.setCurrentText(quality_config.get("audio_codec", "AAC"))
        self.sample_rate_combo.setCurrentText(quality_config.get("sample_rate", "48000 Hz"))
        self.audio_bitrate_combo.setCurrentText(quality_config.get("audio_bitrate", "192 kbps"))

        # Locations
        locations_config = export_config.get("locations", {})
        self.export_location_edit.setText(locations_config.get("default_location", ""))
        self.naming_pattern_edit.setText(locations_config.get("naming_pattern", "{project_name}_{date}_{quality}"))
        self.include_date_check.setChecked(locations_config.get("include_date", True))
        self.include_time_check.setChecked(locations_config.get("include_time", False))
        self.include_quality_check.setChecked(locations_config.get("include_quality", True))
        self.include_version_check.setChecked(locations_config.get("include_version", False))
        self.create_subfolders_check.setChecked(locations_config.get("create_subfolders", True))
        self.date_folders_check.setChecked(locations_config.get("date_folders", False))
        self.quality_folders_check.setChecked(locations_config.get("quality_folders", False))
        self.folder_structure_edit.setText(locations_config.get("folder_structure", ""))

        # Load custom presets
        self.load_custom_presets()

    def load_custom_presets(self):
        """Load custom presets into tree"""
        config = self.config_manager.get_config()
        custom_presets = config.get("export", {}).get("custom_presets", [])

        self.presets_tree.clear()
        for preset in custom_presets:
            item = QTreeWidgetItem(self.presets_tree)
            item.setText(0, preset.get("name", ""))
            item.setText(1, preset.get("format", ""))
            item.setText(2, preset.get("quality", ""))
            item.setText(3, preset.get("description", ""))
            item.setData(0, Qt.ItemDataRole.UserRole, preset)

    def save_settings(self):
        """Save export settings"""
        config = self.config_manager.get_config()

        # Ensure export section exists
        if "export" not in config:
            config["export"] = {}

        # Formats
        config["export"]["formats"] = {
            "default_format": self.default_format_combo.currentText(),
            "target_platform": self.target_platform_combo.currentText(),
            "compatibility_mode": self.compatibility_check.isChecked(),
            "legacy_codecs": self.legacy_codecs_check.isChecked(),
            "container_options": self.container_options_combo.currentText(),
            "metadata": self.metadata_combo.currentText()
        }

        # Presets
        config["export"]["presets"] = {
            "default_preset": self.default_preset_combo.currentText(),
            "smart_optimization": self.enable_optimization_check.isChecked(),
            "auto_select": self.auto_select_check.isChecked(),
            "optimization_level": self.opt_level_slider.value()
        }

        # Quality
        config["export"]["quality"] = {
            "resolution": self.resolution_combo.currentText(),
            "frame_rate": self.fps_combo.currentText(),
            "bitrate_control": self.bitrate_combo.currentText(),
            "quality_preset": self.quality_preset_combo.currentText(),
            "audio_codec": self.audio_codec_combo.currentText(),
            "sample_rate": self.sample_rate_combo.currentText(),
            "audio_bitrate": self.audio_bitrate_combo.currentText()
        }

        # Locations
        config["export"]["locations"] = {
            "default_location": self.export_location_edit.text(),
            "naming_pattern": self.naming_pattern_edit.text(),
            "include_date": self.include_date_check.isChecked(),
            "include_time": self.include_time_check.isChecked(),
            "include_quality": self.include_quality_check.isChecked(),
            "include_version": self.include_version_check.isChecked(),
            "create_subfolders": self.create_subfolders_check.isChecked(),
            "date_folders": self.date_folders_check.isChecked(),
            "quality_folders": self.quality_folders_check.isChecked(),
            "folder_structure": self.folder_structure_edit.text()
        }

        # Save custom presets
        custom_presets = []
        for i in range(self.presets_tree.topLevelItemCount()):
            item = self.presets_tree.topLevelItem(i)
            preset_data = item.data(0, Qt.ItemDataRole.UserRole)
            if preset_data:
                custom_presets.append(preset_data)

        config["export"]["custom_presets"] = custom_presets

        self.config_manager.save_config(config)

    def validate_settings(self) -> List[str]:
        """Validate export settings"""
        errors = []

        # Validate export location
        export_location = self.export_location_edit.text()
        if export_location and not os.path.exists(os.path.dirname(export_location)):
            errors.append("Export location directory does not exist")

        # Validate naming pattern
        naming_pattern = self.naming_pattern_edit.text()
        if not naming_pattern:
            errors.append("File naming pattern cannot be empty")

        # Validate folder structure
        folder_structure = self.folder_structure_edit.text()
        if folder_structure and not folder_structure.replace("{", "").replace("}", "").replace("/", "").replace("_", "").isalnum():
            errors.append("Folder structure contains invalid characters")

        return errors