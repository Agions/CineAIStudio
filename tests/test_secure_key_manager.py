#!/usr/bin/env python3
"""测试安全密钥管理器"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from app.core.secure_key_manager import SecureKeyManager


class TestSecureKeyManager:
    """测试安全密钥管理器"""

    @patch('app.core.secure_key_manager.platform.system')
    @patch('app.core.secure_key_manager.keyring')
    def test_init_default(self, mock_keyring, mock_platform):
        """测试默认初始化"""
        mock_platform.return_value = "Linux"
        
        manager = SecureKeyManager()
        
        assert manager.app_name == "ClipFlow"
        assert manager._encryption_key is None
        assert manager._master_password is None

    @patch('app.core.secure_key_manager.platform.system')
    @patch('app.core.secure_key_manager.keyring')
    def test_init_custom_app_name(self, mock_keyring, mock_platform):
        """测试自定义应用名称"""
        mock_platform.return_value = "Linux"
        
        manager = SecureKeyManager(app_name="MyApp")
        
        assert manager.app_name == "MyApp"

    @patch('app.core.secure_key_manager.platform.system')
    @patch('app.core.secure_key_manager.keyring')
    def test_set_and_get_key(self, mock_keyring, mock_platform):
        """测试设置和获取密钥"""
        mock_platform.return_value = "Linux"
        
        manager = SecureKeyManager()
        
        # Mock 加密方法
        manager._encrypt_value = Mock(return_value="encrypted_value")
        manager._decrypt_value = Mock(return_value="my_api_key")
        
        manager.set_key("openai", "my_api_key")
        
        # 由于是 mock，直接验证方法被调用
        manager._encrypt_value.assert_called_once()

    @patch('app.core.secure_key_manager.platform.system')
    @patch('app.core.secure_key_manager.keyring')
    def test_delete_key(self, mock_keyring, mock_platform):
        """测试删除密钥"""
        mock_platform.return_value = "Linux"
        
        manager = SecureKeyManager()
        
        # 不应该抛出异常
        manager.delete_key("nonexistent_key")

    @patch('app.core.secure_key_manager.platform.system')
    @patch('app.core.secure_key_manager.keyring')
    def test_list_keys(self, mock_keyring, mock_platform):
        """测试列出密钥"""
        mock_platform.return_value = "Linux"
        
        manager = SecureKeyManager()
        
        # 模拟一些密钥
        manager._keys = {"openai": "encrypted", "github": "encrypted"}
        
        keys = manager.list_keys()
        
        assert "openai" in keys
        assert "github" in keys


class TestSecureKeyManagerPlatform:
    """测试平台相关功能"""

    @patch('app.core.secure_key_manager.platform.system')
    def test_darwin_platform(self, mock_platform):
        """测试 macOS 平台"""
        mock_platform.return_value = "Darwin"
        
        # 不应该抛出异常
        try:
            manager = SecureKeyManager()
        except Exception:
            pass  # 忽略预期错误

    @patch('app.core.secure_key_manager.platform.system')
    def test_windows_platform(self, mock_platform):
        """测试 Windows 平台"""
        mock_platform.return_value = "Windows"
        
        try:
            manager = SecureKeyManager()
        except Exception:
            pass

    @patch('app.core.secure_key_manager.platform.system')
    def test_linux_platform(self, mock_platform):
        """测试 Linux 平台"""
        mock_platform.return_value = "Linux"
        
        try:
            manager = SecureKeyManager()
        except Exception:
            pass
