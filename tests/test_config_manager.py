#!/usr/bin/env python3
"""测试配置管理器"""

import os
import json
import tempfile
import pytest

from app.core.config_manager import ConfigManager


@pytest.fixture
def temp_config_dir():
    """创建临时配置目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def config_manager(temp_config_dir):
    """创建配置管理器实例"""
    return ConfigManager(config_root=temp_config_dir)


def test_set_and_get_string(config_manager):
    """测试字符串配置"""
    config_manager.set("test.string", "hello")
    assert config_manager.get("test.string") == "hello"


def test_set_and_get_int(config_manager):
    """测试整数配置"""
    config_manager.set("test.int", 42)
    assert config_manager.get("test.int") == 42


def test_set_and_get_bool(config_manager):
    """测试布尔配置"""
    config_manager.set("test.bool", True)
    assert config_manager.get("test.bool") is True


def test_set_and_get_nested(config_manager):
    """测试嵌套配置"""
    config_manager.set("ui.theme.primary", "#6366F1")
    assert config_manager.get("ui.theme.primary") == "#6366F1"


def test_get_with_default(config_manager):
    """测试默认值"""
    assert config_manager.get("nonexistent", "default") == "default"
    assert config_manager.get("nonexistent", default=123) == 123


def test_delete_key(config_manager):
    """测试删除配置"""
    config_manager.set("to.delete", "value")
    config_manager.delete("to.delete")
    assert config_manager.get("to.delete") is None


def test_save_and_load(config_manager):
    """测试保存和加载"""
    config_manager.set("app.name", "ClipFlowCut")
    config_manager.set("app.version", "3.0.0")
    config_manager.save()
    
    # 创建新的管理器实例并加载
    new_manager = ConfigManager(config_root=config_manager.config_root)
    new_manager.load()
    
    assert new_manager.get("app.name") == "ClipFlowCut"
    assert new_manager.get("app.version") == "3.0.0"


def test_reset(config_manager):
    """测试重置配置"""
    config_manager.set("test.key", "value")
    config_manager.reset()
    
    assert config_manager.get("test.key") is None
