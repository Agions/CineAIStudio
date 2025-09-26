#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Basic Settings System Test
Simple test to verify core settings functionality
"""

import sys
import os
import json
import tempfile

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_config_manager():
    """Test ConfigManager functionality"""
    print("Testing ConfigManager...")

    try:
        from app.core.config_manager import ConfigManager

        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_config_path = f.name

        # Test config manager creation
        config_manager = ConfigManager(config_path=temp_config_path)
        print("✓ ConfigManager created successfully")

        # Test get and save config
        config = config_manager.get_all()
        assert isinstance(config, dict)
        print("✓ Config retrieved")

        # Test setting and getting values
        config_manager.set("test_section.test_key", "test_value")
        value = config_manager.get("test_section.test_key")
        assert value == "test_value"
        print("✓ Config set/get working")

        # Test saving
        config_manager.save()
        print("✓ Config saved")

        # Test loading by creating new instance
        config_manager2 = ConfigManager(config_path=temp_config_path)
        loaded_value = config_manager2.get("test_section.test_key")
        assert loaded_value == "test_value"
        print("✓ Config persistence working")

        # Cleanup
        os.unlink(temp_config_path)
        return True

    except Exception as e:
        print(f"✗ ConfigManager test failed: {e}")
        return False

def test_settings_dialog_imports():
    """Test settings dialog imports"""
    print("Testing settings dialog imports...")

    try:
        # Test basic imports
        from app.ui.dialogs.settings_dialog import SettingsDialog, SettingsBasePage
        print("✓ Settings dialog imports successful")

        # Test settings pages imports
        from app.ui.dialogs.settings_pages import (
            EditorSettingsPage,
            AISettingsPage,
            ExportSettingsPage,
            ThemesSettingsPage,
            AdvancedSettingsPage
        )
        print("✓ Settings pages imports successful")

        # Test settings manager component import
        from app.ui.components.settings_manager_component import SettingsManagerComponent
        print("✓ Settings manager component import successful")

        return True

    except Exception as e:
        print(f"✗ Settings dialog imports failed: {e}")
        return False

def test_settings_structure():
    """Test settings structure and basic functionality"""
    print("Testing settings structure...")

    try:
        from app.ui.dialogs.settings_dialog import SettingsCategory, SettingsPageInfo

        # Test enum values
        assert SettingsCategory.GENERAL.value == "general"
        assert SettingsCategory.EDITOR.value == "editor"
        assert SettingsCategory.AI_SERVICES.value == "ai_services"
        print("✓ SettingsCategory enum working")

        # Test SettingsPageInfo dataclass
        page_info = SettingsPageInfo(
            SettingsCategory.GENERAL,
            "Test Page",
            "test-icon",
            "Test description"
        )
        assert page_info.category == SettingsCategory.GENERAL
        assert page_info.title == "Test Page"
        print("✓ SettingsPageInfo dataclass working")

        return True

    except Exception as e:
        print(f"✗ Settings structure test failed: {e}")
        return False

def test_theme_manager():
    """Test theme manager functionality"""
    print("Testing theme manager...")

    try:
        from app.core.theme_manager import ThemeManager

        # Test theme manager creation
        theme_manager = ThemeManager()
        print("✓ ThemeManager created successfully")

        # Test theme colors
        dark_colors = theme_manager.get_dark_theme_colors()
        assert isinstance(dark_colors, dict)
        assert "background" in dark_colors
        print("✓ Dark theme colors working")

        light_colors = theme_manager.get_light_theme_colors()
        assert isinstance(light_colors, dict)
        assert "background" in light_colors
        print("✓ Light theme colors working")

        return True

    except Exception as e:
        print(f"✗ Theme manager test failed: {e}")
        return False

def test_file_creation():
    """Test that all settings files were created"""
    print("Testing file creation...")

    required_files = [
        "app/ui/dialogs/settings_dialog.py",
        "app/ui/dialogs/settings_pages/__init__.py",
        "app/ui/dialogs/settings_pages/editor_settings.py",
        "app/ui/dialogs/settings_pages/ai_settings.py",
        "app/ui/dialogs/settings_pages/export_settings.py",
        "app/ui/dialogs/settings_pages/themes_settings.py",
        "app/ui/dialogs/settings_pages/advanced_settings.py",
        "app/ui/components/settings_manager_component.py",
        "tests/test_settings_basic.py"
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False

    print("✓ All required settings files created")
    return True

def main():
    """Run basic settings tests"""
    print("CineAIStudio Basic Settings Test")
    print("=" * 40)

    tests = [
        test_file_creation,
        test_settings_structure,
        test_config_manager,
        test_theme_manager,
        test_settings_dialog_imports
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"✗ {test.__name__} crashed: {e}")
            print()

    print("=" * 40)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All basic settings tests passed!")
        return True
    else:
        print("✗ Some basic settings tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)