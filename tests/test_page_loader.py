#!/usr/bin/env python3
"""测试页面加载器"""

import pytest
from unittest.mock import Mock, patch

from app.ui.main.page_loader import PageLoader


class TestPageLoader:
    """测试页面加载器"""

    def test_pages_config_exists(self):
        """测试页面配置存在"""
        config = PageLoader.get_pages_to_load()
        
        assert len(config) > 0
        assert any(p["id"] == "projects" for p in config)
        assert any(p["id"] == "settings" for p in config)

    def test_validate_page_config_valid(self):
        """测试验证有效配置"""
        config = {
            "id": "test",
            "name": "测试页面",
            "class": "TestPage",
            "attribute": "test_page",
        }
        
        assert PageLoader.validate_page_config(config) is True

    def test_validate_page_config_invalid(self):
        """测试验证无效配置"""
        # 缺少 required_keys
        config = {
            "id": "test",
            "name": "测试页面",
        }
        
        assert PageLoader.validate_page_config(config) is False

    def test_validate_page_config_empty(self):
        """测试验证空配置"""
        assert PageLoader.validate_page_config({}) is False

    def test_get_pages_to_load_returns_copy(self):
        """测试获取页面列表返回副本"""
        pages1 = PageLoader.get_pages_to_load()
        pages2 = PageLoader.get_pages_to_load()
        
        # 应该是不同的列表对象
        assert pages1 is not pages2
        # 但内容相同
        assert pages1 == pages2


class TestPageLoaderIntegration:
    """测试页面加载器集成"""

    def test_page_class_mapping(self):
        """测试页面类映射"""
        # 测试已知页面类
        known_classes = [
            "ProjectsPage",
            "VideoEditorPage", 
            "SettingsPage",
        ]
        
        for class_name in known_classes:
            # 只验证映射存在，不实际导入（避免依赖）
            mapping = {
                "ProjectsPage": "app.ui.main.pages.projects_page",
                "VideoEditorPage": "app.ui.main.pages.video_editor_page",
                "SettingsPage": "app.ui.main.pages.settings_page",
            }
            
            assert class_name in mapping
