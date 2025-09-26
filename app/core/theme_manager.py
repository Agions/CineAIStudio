#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Theme Manager Compatibility Layer
Compatibility interface for settings system
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

try:
    from app.ui.theme.theme_manager import ThemeManager as UIThemeManager
    from app.core.config_manager import ThemeConfig

    # Create default theme config
    default_theme_config = ThemeConfig()

    class ThemeManager(UIThemeManager):
        """Extended theme manager with compatibility methods"""

        def __init__(self, theme_config: Optional[ThemeConfig] = None):
            if theme_config is None:
                theme_config = default_theme_config
            super().__init__(theme_config)

        def get_dark_theme_colors(self) -> Dict[str, str]:
            """Get dark theme colors for settings"""
            return {
                "background": self.colors.background,
                "titlebar": self.colors.surface,
                "text": self.colors.text,
                "button": self.colors.primary,
                "panel": self.colors.card,
                "border": self.colors.border
            }

        def get_light_theme_colors(self) -> Dict[str, str]:
            """Get light theme colors for settings"""
            return {
                "background": "#FFFFFF",
                "titlebar": "#F5F5F5",
                "text": "#000000",
                "button": "#2196F3",
                "panel": "#FFFFFF",
                "border": "#E0E0E0"
            }

        def apply_theme(self, theme_name: str, colors: Dict[str, str]) -> None:
            """Apply theme with custom colors"""
            if theme_name.lower() == "dark":
                self.set_theme_mode("dark")
            elif theme_name.lower() == "light":
                self.set_theme_mode("light")
            else:
                self.set_theme_mode("auto")

        def apply_system_theme(self) -> None:
            """Apply system theme"""
            self.set_theme_mode("auto")

except ImportError:
    # Fallback implementation if UI theme manager is not available
    class ThemeManager:
        """Fallback theme manager implementation"""

        def __init__(self):
            pass

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

        def apply_theme(self, theme_name: str, colors: Dict[str, str]) -> None:
            """Apply theme (placeholder)"""
            pass

        def apply_system_theme(self) -> None:
            """Apply system theme (placeholder)"""
            pass

        def set_theme_mode(self, mode: str) -> None:
            """Set theme mode (placeholder)"""
            pass

        def get_theme_mode(self) -> str:
            """Get theme mode"""
            return "dark"