#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Themes Settings Page
Appearance and theme customization settings
"""

import json
from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QCheckBox, QComboBox, QGroupBox, QPushButton,
    QColorDialog, QFontDialog, QTabWidget, QTreeWidget,
    QTreeWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView,
    QListWidget, QListWidgetItem, QSlider, QTextEdit, QFrame,
    QScrollArea, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt6.QtGui import QColor, QFont, QPalette, QPixmap, QPainter

from ...settings_dialog import SettingsBasePage
from app.core.theme_manager import ThemeManager


class ThemePreviewWidget(QWidget):
    """Theme preview widget"""

    def __init__(self, theme_colors: Dict[str, str], parent=None):
        super().__init__(parent)
        self.theme_colors = theme_colors
        self.setMinimumSize(200, 150)
        self.setMaximumHeight(150)

    def paintEvent(self, event):
        """Paint theme preview"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        bg_color = QColor(self.theme_colors.get("background", "#ffffff"))
        painter.fillRect(self.rect(), bg_color)

        # Sample UI elements
        y_offset = 10

        # Window title bar
        title_height = 30
        title_color = QColor(self.theme_colors.get("titlebar", "#2b2b2b"))
        painter.fillRect(0, y_offset, self.width(), title_height, title_color)

        # Title text
        text_color = QColor(self.theme_colors.get("text", "#000000"))
        painter.setPen(text_color)
        painter.drawText(10, y_offset + 20, "Theme Preview")

        y_offset += title_height + 10

        # Button
        button_width = 80
        button_height = 25
        button_color = QColor(self.theme_colors.get("button", "#0078d4"))
        painter.fillRect(10, y_offset, button_width, button_height, button_color)

        # Button text
        painter.setPen(QColor("#ffffff"))
        painter.drawText(15, y_offset + 17, "Button")

        # Panel
        panel_color = QColor(self.theme_colors.get("panel", "#f0f0f0"))
        panel_width = self.width() - 20
        panel_height = 60
        painter.fillRect(10, y_offset + 35, panel_width, panel_height, panel_color)

        # Panel border
        border_color = QColor(self.theme_colors.get("border", "#cccccc"))
        painter.setPen(border_color)
        painter.drawRect(10, y_offset + 35, panel_width, panel_height)

        # Sample text in panel
        painter.setPen(text_color)
        painter.drawText(15, y_offset + 55, "Sample text content")
        painter.drawText(15, y_offset + 75, "Another line of text")


class ThemesSettingsPage(SettingsBasePage):
    """Themes and appearance settings"""

    def __init__(self, config_manager, parent=None):
        super().__init__(config_manager, parent)
        self.theme_manager = ThemeManager()
        self.current_theme = {}

    def setup_ui(self):
        super().setup_ui()

        # Create tabs
        tabs = QTabWidget()
        self.content_layout.addWidget(tabs)

        # Theme selection tab
        selection_tab = QWidget()
        selection_layout = QVBoxLayout(selection_tab)
        self.setup_theme_selection(selection_layout)
        tabs.addTab(selection_tab, "Theme Selection")

        # Color customization tab
        colors_tab = QWidget()
        colors_layout = QVBoxLayout(colors_tab)
        self.setup_color_customization(colors_layout)
        tabs.addTab(colors_tab, "Colors")

        # Typography tab
        typography_tab = QWidget()
        typography_layout = QVBoxLayout(typography_tab)
        self.setup_typography_settings(typography_layout)
        tabs.addTab(typography_tab, "Typography")

        # Interface tab
        interface_tab = QWidget()
        interface_layout = QVBoxLayout(interface_tab)
        self.setup_interface_settings(interface_layout)
        tabs.addTab(interface_tab, "Interface")

    def setup_theme_selection(self, layout):
        """Setup theme selection UI"""
        # Theme selection
        selection_group = QGroupBox("Theme Selection")
        selection_layout = QHBoxLayout()

        # Theme list
        themes_list_group = QGroupBox("Available Themes")
        themes_list_layout = QVBoxLayout()

        self.themes_list = QListWidget()
        self.themes_list.setMaximumWidth(200)
        self.populate_themes_list()
        themes_list_layout.addWidget(self.themes_list)

        themes_list_group.setLayout(themes_list_layout)
        selection_layout.addWidget(themes_list_group)

        # Theme preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()

        self.theme_preview = ThemePreviewWidget({})
        preview_layout.addWidget(self.theme_preview)

        # Theme info
        self.theme_info = QTextEdit()
        self.theme_info.setMaximumHeight(80)
        self.theme_info.setReadOnly(True)
        preview_layout.addWidget(self.theme_info)

        preview_group.setLayout(preview_layout)
        selection_layout.addWidget(preview_group, 1)

        selection_group.setLayout(selection_layout)
        layout.addWidget(selection_group)

        # Theme actions
        actions_group = QGroupBox("Theme Actions")
        actions_layout = QHBoxLayout()

        self.apply_theme_btn = QPushButton("Apply Theme")
        self.import_theme_btn = QPushButton("Import")
        self.export_theme_btn = QPushButton("Export")
        self.delete_theme_btn = QPushButton("Delete")
        actions_layout.addWidget(self.apply_theme_btn)
        actions_layout.addWidget(self.import_theme_btn)
        actions_layout.addWidget(self.export_theme_btn)
        actions_layout.addWidget(self.delete_theme_btn)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        # Connect signals
        self.themes_list.currentItemChanged.connect(self.theme_selected)
        self.apply_theme_btn.clicked.connect(self.apply_theme)
        self.import_theme_btn.clicked.connect(self.import_theme)
        self.export_theme_btn.clicked.connect(self.export_theme)
        self.delete_theme_btn.clicked.connect(self.delete_theme)

    def setup_color_customization(self, layout):
        """Setup color customization UI"""
        # Color scheme
        color_scheme_group = QGroupBox("Color Scheme")
        color_scheme_layout = QVBoxLayout()

        # Color categories
        self.color_categories = QTreeWidget()
        self.color_categories.setHeaderLabels(["Color Category", "Current"])
        self.color_categories.setMaximumHeight(200)
        self.populate_color_categories()
        color_scheme_layout.addWidget(self.color_categories)

        # Color picker
        color_picker_layout = QHBoxLayout()
        self.color_preview = QLabel()
        self.color_preview.setMinimumSize(100, 30)
        self.color_preview.setFrameStyle(QFrame.Shape.Box)
        self.color_change_btn = QPushButton("Change Color")
        color_picker_layout.addWidget(QLabel("Selected Color:"))
        color_picker_layout.addWidget(self.color_preview)
        color_picker_layout.addWidget(self.color_change_btn)
        color_picker_layout.addStretch()
        color_scheme_layout.addLayout(color_picker_layout)

        color_scheme_group.setLayout(color_scheme_layout)
        layout.addWidget(color_scheme_group)

        # Advanced color settings
        advanced_group = QGroupBox("Advanced Color Settings")
        advanced_layout = QVBoxLayout()

        # Color temperature
        temp_layout = QHBoxLayout()
        temp_label = QLabel("Color Temperature:")
        self.color_temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.color_temp_slider.setRange(0, 100)
        self.color_temp_slider.setValue(50)
        self.color_temp_label = QLabel("6500K")
        temp_layout.addWidget(temp_label)
        temp_layout.addWidget(self.color_temp_slider)
        temp_layout.addWidget(self.color_temp_label)
        temp_layout.addStretch()
        advanced_layout.addLayout(temp_layout)

        # Contrast
        contrast_layout = QHBoxLayout()
        contrast_label = QLabel("Contrast:")
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(0, 100)
        self.contrast_slider.setValue(50)
        self.contrast_label = QLabel("1.0")
        contrast_layout.addWidget(contrast_label)
        contrast_layout.addWidget(self.contrast_slider)
        contrast_layout.addWidget(self.contrast_label)
        contrast_layout.addStretch()
        advanced_layout.addLayout(contrast_layout)

        # Saturation
        saturation_layout = QHBoxLayout()
        saturation_label = QLabel("Saturation:")
        self.saturation_slider = QSlider(Qt.Orientation.Horizontal)
        self.saturation_slider.setRange(0, 100)
        self.saturation_slider.setValue(50)
        self.saturation_label = QLabel("100%")
        saturation_layout.addWidget(saturation_label)
        saturation_layout.addWidget(self.saturation_slider)
        saturation_layout.addWidget(self.saturation_label)
        saturation_layout.addStretch()
        advanced_layout.addLayout(saturation_layout)

        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)

        # Color presets
        presets_group = QGroupBox("Color Presets")
        presets_layout = QVBoxLayout()

        presets_layout.addWidget(QLabel("Quick color presets:"))
        preset_buttons_layout = QHBoxLayout()

        self.dark_preset_btn = QPushButton("Dark Theme")
        self.light_preset_btn = QPushButton("Light Theme")
        self.blue_preset_btn = QPushButton("Blue Theme")
        self.green_preset_btn = QPushButton("Green Theme")
        self.sepia_preset_btn = QPushButton("Sepia Theme")

        preset_buttons_layout.addWidget(self.dark_preset_btn)
        preset_buttons_layout.addWidget(self.light_preset_btn)
        preset_buttons_layout.addWidget(self.blue_preset_btn)
        preset_buttons_layout.addWidget(self.green_preset_btn)
        preset_buttons_layout.addWidget(self.sepia_preset_btn)

        presets_layout.addLayout(preset_buttons_layout)
        presets_group.setLayout(presets_layout)
        layout.addWidget(presets_group)

        layout.addStretch()

        # Connect signals
        self.color_categories.itemClicked.connect(self.color_category_selected)
        self.color_change_btn.clicked.connect(self.change_color)
        self.color_temp_slider.valueChanged.connect(self.update_color_temp)
        self.contrast_slider.valueChanged.connect(self.update_contrast)
        self.saturation_slider.valueChanged.connect(self.update_saturation)

        # Connect preset buttons
        self.dark_preset_btn.clicked.connect(lambda: self.apply_color_preset("dark"))
        self.light_preset_btn.clicked.connect(lambda: self.apply_color_preset("light"))
        self.blue_preset_btn.clicked.connect(lambda: self.apply_color_preset("blue"))
        self.green_preset_btn.clicked.connect(lambda: self.apply_color_preset("green"))
        self.sepia_preset_btn.clicked.connect(lambda: self.apply_color_preset("sepia"))

    def setup_typography_settings(self, layout):
        """Setup typography settings"""
        # Font settings
        font_group = QGroupBox("Font Settings")
        font_layout = QVBoxLayout()

        # Main font
        main_font_layout = QHBoxLayout()
        main_font_label = QLabel("Main Font:")
        self.main_font_edit = QLineEdit()
        self.main_font_edit.setReadOnly(True)
        self.main_font_btn = QPushButton("Choose Font")
        main_font_layout.addWidget(main_font_label)
        main_font_layout.addWidget(self.main_font_edit)
        main_font_layout.addWidget(self.main_font_btn)
        font_layout.addLayout(main_font_layout)

        # Code font
        code_font_layout = QHBoxLayout()
        code_font_label = QLabel("Code Font:")
        self.code_font_edit = QLineEdit()
        self.code_font_edit.setReadOnly(True)
        self.code_font_btn = QPushButton("Choose Font")
        code_font_layout.addWidget(code_font_label)
        code_font_layout.addWidget(self.code_font_edit)
        code_font_layout.addWidget(self.code_font_btn)
        font_layout.addLayout(code_font_layout)

        # Font sizes
        sizes_layout = QGridLayout()

        sizes_layout.addWidget(QLabel("UI Font Size:"), 0, 0)
        self.ui_font_size_spin = QSpinBox()
        self.ui_font_size_spin.setRange(8, 24)
        sizes_layout.addWidget(self.ui_font_size_spin, 0, 1)

        sizes_layout.addWidget(QLabel("Editor Font Size:"), 1, 0)
        self.editor_font_size_spin = QSpinBox()
        self.editor_font_size_spin.setRange(8, 32)
        sizes_layout.addWidget(self.editor_font_size_spin, 1, 1)

        sizes_layout.addWidget(QLabel("Code Font Size:"), 2, 0)
        self.code_font_size_spin = QSpinBox()
        self.code_font_size_spin.setRange(8, 24)
        sizes_layout.addWidget(self.code_font_size_spin, 2, 1)

        font_layout.addLayout(sizes_layout)

        font_group.setLayout(font_layout)
        layout.addWidget(font_group)

        # Text rendering
        rendering_group = QGroupBox("Text Rendering")
        rendering_layout = QVBoxLayout()

        # Font smoothing
        smoothing_group = QButtonGroup(self)
        self.smoothing_standard_radio = QRadioButton("Standard smoothing")
        self.smoothing_clear_radio = QRadioButton("ClearType")
        self.smoothing_none_radio = QRadioButton("No smoothing")
        smoothing_group.addButton(self.smoothing_standard_radio)
        smoothing_group.addButton(self.smoothing_clear_radio)
        smoothing_group.addButton(self.smoothing_none_radio)
        rendering_layout.addWidget(self.smoothing_standard_radio)
        rendering_layout.addWidget(self.smoothing_clear_radio)
        rendering_layout.addWidget(self.smoothing_none_radio)

        # Font hinting
        self.hinting_check = QCheckBox("Enable font hinting")
        self.kerning_check = QCheckBox("Enable font kerning")
        rendering_layout.addWidget(self.hinting_check)
        rendering_layout.addWidget(self.kerning_check)

        rendering_group.setLayout(rendering_layout)
        layout.addWidget(rendering_group)

        layout.addStretch()

        # Connect signals
        self.main_font_btn.clicked.connect(self.choose_main_font)
        self.code_font_btn.clicked.connect(self.choose_code_font)

    def setup_interface_settings(self, layout):
        """Setup interface settings"""
        # UI scaling
        scaling_group = QGroupBox("Interface Scaling")
        scaling_layout = QVBoxLayout()

        # Scale factor
        scale_layout = QHBoxLayout()
        scale_label = QLabel("Scale Factor:")
        self.scale_combo = QComboBox()
        self.scale_combo.addItems([
            "100% (Normal)",
            "125%",
            "150%",
            "175%",
            "200%",
            "250%",
            "300%"
        ])
        scale_layout.addWidget(scale_label)
        scale_layout.addWidget(self.scale_combo)
        scale_layout.addStretch()
        scaling_layout.addLayout(scale_layout)

        # Custom scale
        custom_scale_layout = QHBoxLayout()
        custom_scale_label = QLabel("Custom Scale:")
        self.custom_scale_spin = QSpinBox()
        self.custom_scale_spin.setRange(50, 500)
        self.custom_scale_spin.setSuffix("%")
        custom_scale_layout.addWidget(custom_scale_label)
        custom_scale_layout.addWidget(self.custom_scale_spin)
        custom_scale_layout.addStretch()
        scaling_layout.addLayout(custom_scale_layout)

        scaling_group.setLayout(scaling_layout)
        layout.addWidget(scaling_group)

        # Animations
        animations_group = QGroupBox("Animations")
        animations_layout = QVBoxLayout()

        self.enable_animations_check = QCheckBox("Enable interface animations")
        self.enable_transitions_check = QCheckBox("Enable smooth transitions")
        self.enable_effects_check = QCheckBox("Enable visual effects")
        animations_layout.addWidget(self.enable_animations_check)
        animations_layout.addWidget(self.enable_transitions_check)
        animations_layout.addWidget(self.enable_effects_check)

        # Animation speed
        speed_layout = QHBoxLayout()
        speed_label = QLabel("Animation Speed:")
        self.animation_speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.animation_speed_slider.setRange(1, 100)
        self.animation_speed_slider.setValue(50)
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.animation_speed_slider)
        speed_layout.addStretch()
        animations_layout.addLayout(speed_layout)

        animations_group.setLayout(animations_layout)
        layout.addWidget(animations_group)

        # Layout options
        layout_group = QGroupBox("Layout Options")
        layout_options_layout = QVBoxLayout()

        self.compact_mode_check = QCheckBox("Use compact mode")
        self.hide_menubar_check = QCheckBox("Auto-hide menu bar")
        self.hide_toolbar_check = QCheckBox("Auto-hide toolbar")
        self.fullscreen_check = QCheckBox("Enable fullscreen mode")
        layout_options_layout.addWidget(self.compact_mode_check)
        layout_options_layout.addWidget(self.hide_menubar_check)
        layout_options_layout.addWidget(self.hide_toolbar_check)
        layout_options_layout.addWidget(self.fullscreen_check)

        layout_group.setLayout(layout_options_layout)
        layout.addWidget(layout_group)

        layout.addStretch()

    def populate_themes_list(self):
        """Populate themes list"""
        # Built-in themes
        built_in_themes = [
            {"name": "Dark Theme", "type": "built-in", "colors": self.get_dark_theme_colors()},
            {"name": "Light Theme", "type": "built-in", "colors": self.get_light_theme_colors()},
            {"name": "Blue Theme", "type": "built-in", "colors": self.get_blue_theme_colors()},
            {"name": "High Contrast", "type": "built-in", "colors": self.get_high_contrast_colors()}
        ]

        # Add themes to list
        for theme in built_in_themes:
            item = QListWidgetItem(theme["name"])
            item.setData(Qt.ItemDataRole.UserRole, theme)
            self.themes_list.addItem(item)

    def populate_color_categories(self):
        """Populate color categories tree"""
        categories = [
            ("Window", [
                ("Background", "#ffffff"),
                ("Title Bar", "#2b2b2b"),
                ("Border", "#cccccc")
            ]),
            ("Text", [
                ("Primary", "#000000"),
                ("Secondary", "#666666"),
                ("Disabled", "#999999")
            ]),
            ("Controls", [
                ("Button", "#0078d4"),
                ("Button Hover", "#106ebe"),
                ("Button Pressed", "#005a9e")
            ]),
            ("Panels", [
                ("Background", "#f0f0f0"),
                ("Alternate", "#e8e8e8"),
                ("Selected", "#0078d4")
            ])
        ]

        for category_name, colors in categories:
            category_item = QTreeWidgetItem(self.color_categories)
            category_item.setText(0, category_name)

            for color_name, color_value in colors:
                color_item = QTreeWidgetItem(category_item)
                color_item.setText(0, color_name)
                color_item.setText(1, color_value)
                color_item.setData(0, Qt.ItemDataRole.UserRole, color_value)

        self.color_categories.expandAll()

    def get_dark_theme_colors(self) -> Dict[str, str]:
        """Get dark theme colors"""
        return {
            "background": "#1e1e1e",
            "titlebar": "#2d2d30",
            "text": "#d4d4d4",
            "button": "#0e639c",
            "panel": "#252526",
            "border": "#3e3e42"
        }

    def get_light_theme_colors(self) -> Dict[str, str]:
        """Get light theme colors"""
        return {
            "background": "#ffffff",
            "titlebar": "#f3f3f3",
            "text": "#000000",
            "button": "#0078d4",
            "panel": "#f0f0f0",
            "border": "#e1e1e1"
        }

    def get_blue_theme_colors(self) -> Dict[str, str]:
        """Get blue theme colors"""
        return {
            "background": "#f0f8ff",
            "titlebar": "#4682b4",
            "text": "#000080",
            "button": "#4169e1",
            "panel": "#e6f3ff",
            "border": "#b0c4de"
        }

    def get_high_contrast_colors(self) -> Dict[str, str]:
        """Get high contrast colors"""
        return {
            "background": "#000000",
            "titlebar": "#ffffff",
            "text": "#ffffff",
            "button": "#ffff00",
            "panel": "#000000",
            "border": "#ffffff"
        }

    def theme_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Handle theme selection"""
        if current:
            theme_data = current.data(Qt.ItemDataRole.UserRole)
            if theme_data:
                self.current_theme = theme_data
                self.update_theme_preview()
                self.update_theme_info()

    def update_theme_preview(self):
        """Update theme preview"""
        colors = self.current_theme.get("colors", {})
        self.theme_preview.theme_colors = colors
        self.theme_preview.update()

    def update_theme_info(self):
        """Update theme information"""
        theme_name = self.current_theme.get("name", "")
        theme_type = self.current_theme.get("type", "")

        info_text = f"<b>{theme_name}</b><br>Type: {theme_type}<br>"
        if theme_type == "built-in":
            info_text += "Built-in theme"
        else:
            info_text += "Custom theme"

        self.theme_info.setHtml(info_text)

    def color_category_selected(self, item: QTreeWidgetItem, column: int):
        """Handle color category selection"""
        if item.parent():  # It's a color item
            color_value = item.data(0, Qt.ItemDataRole.UserRole)
            if color_value:
                self.update_color_preview(color_value)

    def update_color_preview(self, color_value: str):
        """Update color preview"""
        color = QColor(color_value)
        self.color_preview.setStyleSheet(f"background-color: {color_value};")
        self.selected_color = color_value

    def change_color(self):
        """Change selected color"""
        if hasattr(self, 'selected_color'):
            current_color = QColor(self.selected_color)
            color = QColorDialog.getColor(current_color, self)
            if color.isValid():
                new_color_value = color.name()
                self.update_color_preview(new_color_value)
                self.update_current_tree_item(new_color_value)

    def update_current_tree_item(self, color_value: str):
        """Update current tree item with new color"""
        current_item = self.color_categories.currentItem()
        if current_item and current_item.parent():
            current_item.setText(1, color_value)
            current_item.setData(0, Qt.ItemDataRole.UserRole, color_value)

    def apply_color_preset(self, preset_name: str):
        """Apply color preset"""
        preset_colors = {
            "dark": self.get_dark_theme_colors(),
            "light": self.get_light_theme_colors(),
            "blue": self.get_blue_theme_colors(),
            "green": {
                "background": "#f0fff0",
                "titlebar": "#228b22",
                "text": "#006400",
                "button": "#32cd32",
                "panel": "#e8f5e8",
                "border": "#90ee90"
            },
            "sepia": {
                "background": "#f4f1ea",
                "titlebar": "#8b7355",
                "text": "#5c4033",
                "button": "#cd853f",
                "panel": "#faf8f3",
                "border": "#d2b48c"
            }
        }

        if preset_name in preset_colors:
            colors = preset_colors[preset_name]
            self.apply_colors_to_ui(colors)

    def apply_colors_to_ui(self, colors: Dict[str, str]):
        """Apply colors to UI elements"""
        # Update tree items
        for i in range(self.color_categories.topLevelItemCount()):
            category_item = self.color_categories.topLevelItem(i)
            for j in range(category_item.childCount()):
                color_item = category_item.child(j)
                color_name = color_item.text(0).lower().replace(" ", "_")
                if color_name in colors:
                    color_value = colors[color_name]
                    color_item.setText(1, color_value)
                    color_item.setData(0, Qt.ItemDataRole.UserRole, color_value)

        # Update preview
        self.theme_preview.theme_colors = colors
        self.theme_preview.update()

    def update_color_temp(self, value: int):
        """Update color temperature display"""
        temp = 4000 + (value * 40)  # 4000K to 8000K
        self.color_temp_label.setText(f"{temp}K")

    def update_contrast(self, value: int):
        """Update contrast display"""
        contrast = 0.5 + (value / 100.0)  # 0.5 to 1.5
        self.contrast_label.setText(f"{contrast:.1f}")

    def update_saturation(self, value: int):
        """Update saturation display"""
        saturation = (value / 100.0) * 200  # 0% to 200%
        self.saturation_label.setText(f"{saturation:.0f}%")

    def choose_main_font(self):
        """Choose main font"""
        current_font = QFont(self.main_font_edit.text())
        font, ok = QFontDialog.getFont(current_font, self)
        if ok:
            self.main_font_edit.setText(font.family())

    def choose_code_font(self):
        """Choose code font"""
        current_font = QFont(self.code_font_edit.text())
        font, ok = QFontDialog.getFont(current_font, self)
        if ok:
            self.code_font_edit.setText(font.family())

    def apply_theme(self):
        """Apply selected theme"""
        if hasattr(self, 'current_theme') and self.current_theme:
            theme_colors = self.current_theme.get("colors", {})
            # Apply theme through theme manager
            self.theme_manager.apply_theme(self.current_theme["name"], theme_colors)
            # Save to config
            self.save_theme_settings()

    def import_theme(self):
        """Import theme from file"""
        # Implementation for theme import
        pass

    def export_theme(self):
        """Export current theme to file"""
        # Implementation for theme export
        pass

    def delete_theme(self):
        """Delete selected theme"""
        current_item = self.themes_list.currentItem()
        if current_item:
            theme_data = current_item.data(Qt.ItemDataRole.UserRole)
            if theme_data and theme_data.get("type") == "custom":
                reply = self.parent().parent().question(
                    "Delete Theme",
                    "Are you sure you want to delete this theme?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    row = self.themes_list.row(current_item)
                    self.themes_list.takeItem(row)

    def load_settings(self):
        """Load theme settings"""
        config = self.config_manager.get_config()
        theme_config = config.get("themes", {})

        # Current theme
        current_theme = theme_config.get("current_theme", "Dark Theme")
        for i in range(self.themes_list.count()):
            item = self.themes_list.item(i)
            theme_data = item.data(Qt.ItemDataRole.UserRole)
            if theme_data and theme_data.get("name") == current_theme:
                self.themes_list.setCurrentItem(item)
                break

        # UI scaling
        scaling = theme_config.get("scaling", {})
        self.scale_combo.setCurrentText(f"{scaling.get('scale_factor', 100)}%")
        self.custom_scale_spin.setValue(scaling.get("custom_scale", 100))

        # Typography
        typography = theme_config.get("typography", {})
        self.main_font_edit.setText(typography.get("main_font", "Arial"))
        self.code_font_edit.setText(typography.get("code_font", "Consolas"))
        self.ui_font_size_spin.setValue(typography.get("ui_font_size", 12))
        self.editor_font_size_spin.setValue(typography.get("editor_font_size", 14))
        self.code_font_size_spin.setValue(typography.get("code_font_size", 12))

        # Animations
        animations = theme_config.get("animations", {})
        self.enable_animations_check.setChecked(animations.get("enabled", True))
        self.enable_transitions_check.setChecked(animations.get("transitions", True))
        self.enable_effects_check.setChecked(animations.get("effects", True))
        self.animation_speed_slider.setValue(animations.get("speed", 50))

        # Layout
        layout_options = theme_config.get("layout", {})
        self.compact_mode_check.setChecked(layout_options.get("compact_mode", False))
        self.hide_menubar_check.setChecked(layout_options.get("auto_hide_menubar", False))
        self.hide_toolbar_check.setChecked(layout_options.get("auto_hide_toolbar", False))
        self.fullscreen_check.setChecked(layout_options.get("fullscreen_mode", False))

    def save_settings(self):
        """Save theme settings"""
        config = self.config_manager.get_config()

        # Ensure themes section exists
        if "themes" not in config:
            config["themes"] = {}

        # Current theme
        if hasattr(self, 'current_theme') and self.current_theme:
            config["themes"]["current_theme"] = self.current_theme.get("name", "")

        # UI scaling
        scale_text = self.scale_combo.currentText()
        scale_value = int(scale_text.replace("%", ""))
        config["themes"]["scaling"] = {
            "scale_factor": scale_value,
            "custom_scale": self.custom_scale_spin.value()
        }

        # Typography
        config["themes"]["typography"] = {
            "main_font": self.main_font_edit.text(),
            "code_font": self.code_font_edit.text(),
            "ui_font_size": self.ui_font_size_spin.value(),
            "editor_font_size": self.editor_font_size_spin.value(),
            "code_font_size": self.code_font_size_spin.value()
        }

        # Animations
        config["themes"]["animations"] = {
            "enabled": self.enable_animations_check.isChecked(),
            "transitions": self.enable_transitions_check.isChecked(),
            "effects": self.enable_effects_check.isChecked(),
            "speed": self.animation_speed_slider.value()
        }

        # Layout
        config["themes"]["layout"] = {
            "compact_mode": self.compact_mode_check.isChecked(),
            "auto_hide_menubar": self.hide_menubar_check.isChecked(),
            "auto_hide_toolbar": self.hide_toolbar_check.isChecked(),
            "fullscreen_mode": self.fullscreen_check.isChecked()
        }

        self.config_manager.save_config(config)

    def validate_settings(self) -> List[str]:
        """Validate theme settings"""
        errors = []

        # Validate font sizes
        if self.ui_font_size_spin.value() < 8:
            errors.append("UI font size must be at least 8 points")

        if self.editor_font_size_spin.value() < 8:
            errors.append("Editor font size must be at least 8 points")

        if self.code_font_size_spin.value() < 8:
            errors.append("Code font size must be at least 8 points")

        # Validate scaling
        if self.custom_scale_spin.value() < 50 or self.custom_scale_spin.value() > 500:
            errors.append("Custom scale must be between 50% and 500%")

        return errors