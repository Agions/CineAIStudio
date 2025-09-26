#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Settings System Test
Comprehensive test suite for the settings management system
"""

import sys
import os
import json
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_config_manager_basic():
    """Test basic config manager functionality"""
    print("Testing ConfigManager basic functionality...")

    try:
        from app.core.config_manager import ConfigManager

        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_config_path = f.name

        # Test config manager creation
        config_manager = ConfigManager(config_path=temp_config_path)
        print("✓ ConfigManager created successfully")

        # Test default config
        default_config = config_manager.get_default_config()
        assert isinstance(default_config, dict)
        print("✓ Default config retrieved")

        # Test get config
        config = config_manager.get_config()
        assert isinstance(config, dict)
        print("✓ Config retrieved")

        # Test save config
        test_value = {"test_key": "test_value"}
        config["test_section"] = test_value
        config_manager.save_config(config)
        print("✓ Config saved")

        # Test load config
        loaded_config = config_manager.get_config()
        assert loaded_config.get("test_section") == test_value
        print("✓ Config loaded correctly")

        # Cleanup
        os.unlink(temp_config_path)
        return True

    except Exception as e:
        print(f"✗ ConfigManager test failed: {e}")
        return False


def test_settings_dialog_creation():
    """Test settings dialog creation"""
    print("Testing SettingsDialog creation...")

    try:
        # Mock required dependencies
        with patch('app.ui.dialogs.settings_dialog.get_secure_key_manager') as mock_key_manager, \
             patch('app.ui.dialogs.settings_dialog.ThemeManager') as mock_theme_manager:

            mock_key_manager.return_value = Mock()
            mock_theme_manager.return_value = Mock()

            from app.ui.dialogs.settings_dialog import SettingsDialog
            from app.core.config_manager import ConfigManager

            # Create temporary config file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                temp_config_path = f.name

            config_manager = ConfigManager(config_path=temp_config_path)

            # Test dialog creation (without showing)
            dialog = SettingsDialog(config_manager)
            assert dialog is not None
            print("✓ SettingsDialog created successfully")

            # Test dialog properties
            assert dialog.windowTitle() == "Settings"
            assert dialog.isModal()
            print("✓ Dialog properties correct")

            # Cleanup
            dialog.deleteLater()
            os.unlink(temp_config_path)
            return True

    except Exception as e:
        print(f"✗ SettingsDialog test failed: {e}")
        return False


def test_settings_pages():
    """Test individual settings pages"""
    print("Testing settings pages...")

    try:
        from app.core.config_manager import ConfigManager

        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_config_path = f.name

        config_manager = ConfigManager(config_path=temp_config_path)

        # Test general settings page
        from app.ui.dialogs.settings_pages.general_settings import GeneralSettingsPage
        general_page = GeneralSettingsPage(config_manager)
        assert general_page is not None
        print("✓ GeneralSettingsPage created")

        # Test performance settings page
        from app.ui.dialogs.settings_pages.performance_settings import PerformanceSettingsPage
        performance_page = PerformanceSettingsPage(config_manager)
        assert performance_page is not None
        print("✓ PerformanceSettingsPage created")

        # Test AI settings page
        with patch('app.ui.dialogs.settings_pages.ai_settings.get_secure_key_manager') as mock_key, \
             patch('app.ui.dialogs.settings_pages.ai_settings.AIServiceManager') as mock_ai_manager:

            mock_key.return_value = Mock()
            mock_ai_manager.return_value = Mock()

            from app.ui.dialogs.settings_pages.ai_settings import AISettingsPage
            ai_page = AISettingsPage(config_manager)
            assert ai_page is not None
            print("✓ AISettingsPage created")

        # Test export settings page
        from app.ui.dialogs.settings_pages.export_settings import ExportSettingsPage
        export_page = ExportSettingsPage(config_manager)
        assert export_page is not None
        print("✓ ExportSettingsPage created")

        # Test themes settings page
        with patch('app.ui.dialogs.settings_pages.themes_settings.ThemeManager') as mock_theme:
            mock_theme.return_value = Mock()

            from app.ui.dialogs.settings_pages.themes_settings import ThemesSettingsPage
            themes_page = ThemesSettingsPage(config_manager)
            assert themes_page is not None
            print("✓ ThemesSettingsPage created")

        # Test advanced settings page
        from app.ui.dialogs.settings_pages.advanced_settings import AdvancedSettingsPage
        advanced_page = AdvancedSettingsPage(config_manager)
        assert advanced_page is not None
        print("✓ AdvancedSettingsPage created")

        # Cleanup
        for page in [general_page, performance_page, export_page, advanced_page]:
            page.deleteLater()

        if 'ai_page' in locals():
            ai_page.deleteLater()
        if 'themes_page' in locals():
            themes_page.deleteLater()

        os.unlink(temp_config_path)
        return True

    except Exception as e:
        print(f"✗ Settings pages test failed: {e}")
        return False


def test_settings_manager_component():
    """Test settings manager component"""
    print("Testing SettingsManagerComponent...")

    try:
        with patch('app.ui.components.settings_manager_component.ThemeManager') as mock_theme:
            mock_theme.return_value = Mock()

            from app.ui.components.settings_manager_component import SettingsManagerComponent
            from app.core.config_manager import ConfigManager

            # Create temporary config file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                temp_config_path = f.name

            config_manager = ConfigManager(config_path=temp_config_path)

            # Test component creation
            settings_manager = SettingsManagerComponent(config_manager)
            assert settings_manager is not None
            print("✓ SettingsManagerComponent created")

            # Test toolbar creation
            assert settings_manager.toolbar is not None
            print("✓ Toolbar created")

            # Test presets loading
            assert len(settings_manager.presets) > 0
            print("✓ Presets loaded successfully")

            # Test quick settings
            assert settings_manager.quick_settings_combo.count() > 0
            print("✓ Quick settings populated")

            # Test theme combo
            assert settings_manager.theme_combo.count() > 0
            print("✓ Theme combo populated")

            # Test setting getter/setter
            settings_manager.set_setting("test.nested.key", "test_value")
            value = settings_manager.get_setting("test.nested.key")
            assert value == "test_value"
            print("✓ Setting getter/setter working")

            # Cleanup
            settings_manager.deleteLater()
            os.unlink(temp_config_path)
            return True

    except Exception as e:
        print(f"✗ SettingsManagerComponent test failed: {e}")
        return False


def test_settings_validation():
    """Test settings validation"""
    print("Testing settings validation...")

    try:
        from app.core.config_manager import ConfigManager

        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_config_path = f.name

        config_manager = ConfigManager(config_path=temp_config_path)

        # Test general settings validation
        from app.ui.dialogs.settings_pages.general_settings import GeneralSettingsPage
        general_page = GeneralSettingsPage(config_manager)

        # Test invalid paths
        general_page.work_dir_edit.setText("/nonexistent/path")
        general_page.temp_dir_edit.setText("/another/nonexistent/path")

        errors = general_page.validate_settings()
        assert len(errors) > 0
        assert any("directory does not exist" in error for error in errors)
        print("✓ General settings validation working")

        # Test performance settings validation
        from app.ui.dialogs.settings_pages.performance_settings import PerformanceSettingsPage
        performance_page = PerformanceSettingsPage(config_manager)

        # Test invalid memory limits
        performance_page.mem_limit_spin.setValue(100)  # Too low
        errors = performance_page.validate_settings()
        assert len(errors) > 0
        print("✓ Performance settings validation working")

        # Test advanced settings validation
        from app.ui.dialogs.settings_pages.advanced_settings import AdvancedSettingsPage
        advanced_page = AdvancedSettingsPage(config_manager)

        # Test invalid values
        advanced_page.mem_limit_spin.setValue(100)  # Too low
        advanced_page.thread_pool_spin.setValue(0)  # Too low
        errors = advanced_page.validate_settings()
        assert len(errors) > 0
        print("✓ Advanced settings validation working")

        # Cleanup
        general_page.deleteLater()
        performance_page.deleteLater()
        advanced_page.deleteLater()
        os.unlink(temp_config_path)
        return True

    except Exception as e:
        print(f"✗ Settings validation test failed: {e}")
        return False


def test_settings_persistence():
    """Test settings persistence"""
    print("Testing settings persistence...")

    try:
        from app.core.config_manager import ConfigManager

        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_config_path = f.name

        config_manager = ConfigManager(config_path=temp_config_path)

        # Test general settings save/load
        from app.ui.dialogs.settings_pages.general_settings import GeneralSettingsPage
        general_page = GeneralSettingsPage(config_manager)

        # Set some values
        general_page.lang_combo.setCurrentText("中文")
        general_page.autosave_check.setChecked(True)
        general_page.autosave_interval.setValue(10)
        general_page.work_dir_edit.setText("/test/path")

        # Save settings
        general_page.save_settings()

        # Create new page and load settings
        new_page = GeneralSettingsPage(config_manager)
        new_page.load_settings()

        # Verify values
        assert new_page.lang_combo.currentText() == "中文"
        assert new_page.autosave_check.isChecked() == True
        assert new_page.autosave_interval.value() == 10
        assert new_page.work_dir_edit.text() == "/test/path"
        print("✓ General settings persistence working")

        # Test performance settings persistence
        from app.ui.dialogs.settings_pages.performance_settings import PerformanceSettingsPage
        performance_page = PerformanceSettingsPage(config_manager)

        # Set some values
        performance_page.gpu_check.setChecked(True)
        performance_page.gpu_backend_combo.setCurrentText("CUDA")
        performance_page.mem_limit_spin.setValue(8192)

        # Save settings
        performance_page.save_settings()

        # Create new page and load settings
        new_perf_page = PerformanceSettingsPage(config_manager)
        new_perf_page.load_settings()

        # Verify values
        assert new_perf_page.gpu_check.isChecked() == True
        assert new_perf_page.gpu_backend_combo.currentText() == "CUDA"
        assert new_perf_page.mem_limit_spin.value() == 8192
        print("✓ Performance settings persistence working")

        # Cleanup
        general_page.deleteLater()
        new_page.deleteLater()
        performance_page.deleteLater()
        new_perf_page.deleteLater()
        os.unlink(temp_config_path)
        return True

    except Exception as e:
        print(f"✗ Settings persistence test failed: {e}")
        return False


def test_settings_integration():
    """Test settings integration with other systems"""
    print("Testing settings integration...")

    try:
        # Test theme manager integration
        with patch('app.core.theme_manager.ThemeManager') as mock_theme_class:
            mock_theme = Mock()
            mock_theme_class.return_value = mock_theme

            from app.core.theme_manager import ThemeManager
            theme_manager = ThemeManager()

            # Test theme application
            colors = {"background": "#1e1e1e", "text": "#ffffff"}
            theme_manager.apply_theme("Dark", colors)
            print("✓ Theme manager integration working")

        # Test secure key manager integration
        with patch('app.core.secure_key_manager.keyring') as mock_keyring:
            mock_keyring.get_password.return_value = "test_api_key"
            mock_keyring.set_password.return_value = True

            from app.core.secure_key_manager import get_secure_key_manager
            key_manager = get_secure_key_manager()

            # Test API key operations
            api_key = key_manager.get_api_key("test_service")
            assert api_key == "test_api_key"
            print("✓ Secure key manager integration working")

        # Test AI service manager integration
        with patch('app.services.ai_service_manager.get_secure_key_manager') as mock_key, \
             patch('app.services.ai_service_manager.BaseAIService') as mock_base:

            mock_key.return_value = Mock()
            mock_base.return_value = Mock()

            from app.services.ai_service_manager import AIServiceManager
            ai_manager = AIServiceManager()

            # Test manager creation
            assert ai_manager is not None
            print("✓ AI service manager integration working")

        return True

    except Exception as e:
        print(f"✗ Settings integration test failed: {e}")
        return False


def main():
    """Run all settings system tests"""
    print("CineAIStudio Settings System Test Suite")
    print("=" * 50)

    tests = [
        test_config_manager_basic,
        test_settings_dialog_creation,
        test_settings_pages,
        test_settings_manager_component,
        test_settings_validation,
        test_settings_persistence,
        test_settings_integration
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

    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All settings system tests passed!")
        return True
    else:
        print("✗ Some settings system tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)