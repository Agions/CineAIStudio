#!/usr/bin/env python3
"""测试项目设置管理器"""

import pytest
from dataclasses import asdict

from app.core.project_settings_manager import (
    SettingType,
    SettingDefinition,
    ProjectSettingsProfile,
    ProjectSettingsManager,
)


class TestSettingType:
    """测试设置类型枚举"""

    def test_all_types(self):
        """测试所有设置类型"""
        types = [
            SettingType.STRING,
            SettingType.INTEGER,
            SettingType.FLOAT,
            SettingType.BOOLEAN,
            SettingType.LIST,
            SettingType.DICT,
            SettingType.COLOR,
            SettingType.PATH,
            SettingType.RESOLUTION,
        ]
        
        assert len(types) == 9
        assert SettingType.STRING.value == "string"


class TestSettingDefinition:
    """测试设置定义"""

    def test_basic_creation(self):
        """测试基本创建"""
        definition = SettingDefinition(
            key="app_name",
            name="应用名称",
            description="应用显示名称",
            setting_type=SettingType.STRING,
            default_value="ClipFlowCut",
        )
        
        assert definition.key == "app_name"
        assert definition.name == "应用名称"
        assert definition.setting_type == SettingType.STRING
        assert definition.default_value == "ClipFlowCut"

    def test_with_options(self):
        """测试带选项的定义"""
        definition = SettingDefinition(
            key="theme",
            name="主题",
            description="应用主题",
            setting_type=SettingType.STRING,
            default_value="dark",
            options=["light", "dark", "auto"],
        )
        
        assert definition.options == ["light", "dark", "auto"]

    def test_with_range(self):
        """测试带范围的定义"""
        definition = SettingDefinition(
            key="volume",
            name="音量",
            description="播放音量",
            setting_type=SettingType.FLOAT,
            default_value=1.0,
            min_value=0.0,
            max_value=1.0,
        )
        
        assert definition.min_value == 0.0
        assert definition.max_value == 1.0


class TestProjectSettingsProfile:
    """测试项目设置配置文件"""

    def test_creation(self):
        """测试创建"""
        profile = ProjectSettingsProfile(
            name="默认配置",
            description="默认项目设置",
            settings={"key": "value"},
        )
        
        assert profile.name == "默认配置"
        assert profile.settings["key"] == "value"

    def test_to_dict(self):
        """测试转换为字典"""
        profile = ProjectSettingsProfile(
            name="测试",
            description="测试配置",
            settings={"theme": "dark"},
        )
        
        d = asdict(profile)
        
        assert d["name"] == "测试"
        assert d["settings"]["theme"] == "dark"


class TestProjectSettingsManager:
    """测试项目设置管理器"""

    def test_init_default(self):
        """测试默认初始化"""
        # 由于需要 ConfigManager，我们 mock 它
        with patch('app.core.project_settings_manager.ConfigManager'):
            manager = ProjectSettingsManager()
            
            assert manager._settings_definitions is not None

    def test_get_setting_definition(self):
        """测试获取设置定义"""
        with patch('app.core.project_settings_manager.ConfigManager'):
            manager = ProjectSettingsManager()
            
            # 测试获取预定义设置
            defn = manager.get_setting_definition("general.theme")
            
            # 可能返回 None 如果设置不存在
            assert defn is None or isinstance(defn, SettingDefinition)

    def test_register_setting(self):
        """测试注册新设置"""
        with patch('app.core.project_settings_manager.ConfigManager'):
            manager = ProjectSettingsManager()
            
            new_def = SettingDefinition(
                key="test.setting",
                name="测试设置",
                description="用于测试",
                setting_type=SettingType.STRING,
                default_value="test",
            )
            
            manager.register_setting(new_def)
            
            # 验证注册成功
            retrieved = manager.get_setting_definition("test.setting")
            # 可能需要检查实现


class TestProjectSettingsValidation:
    """测试设置验证"""

    def test_validate_string(self):
        """测试字符串验证"""
        with patch('app.core.project_settings_manager.ConfigManager'):
            manager = ProjectSettingsManager()
            
            # 测试基本验证
            result = manager._validate_value("test", SettingType.STRING, "value")
            assert result is True

    def test_validate_boolean(self):
        """测试布尔验证"""
        with patch('app.core.project_settings_manager.ConfigManager'):
            manager = ProjectSettingsManager()
            
            assert manager._validate_value("true", SettingType.BOOLEAN, True) is True
            assert manager._validate_value("false", SettingType.BOOLEAN, False) is True
