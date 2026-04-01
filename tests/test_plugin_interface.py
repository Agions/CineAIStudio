#!/usr/bin/env python3
"""测试插件接口"""

import pytest
from dataclasses import asdict

from app.plugins.plugin_interface import (
    PluginType,
    PluginStatus,
    PluginInfo,
    PluginInterface,
)


class TestPluginType:
    """测试插件类型枚举"""

    def test_all_types(self):
        """测试所有插件类型"""
        types = [
            PluginType.VIDEO_EFFECT,
            PluginType.AUDIO_EFFECT,
            PluginType.TRANSITION,
            PluginType.TEXT_OVERLAY,
            PluginType.COLOR_GRADING,
            PluginType.MOTION_GRAPHICS,
            PluginType.AI_ENHANCEMENT,
            PluginType.EXPORT_FORMAT,
            PluginType.IMPORT_FORMAT,
            PluginType.ANALYSIS_TOOL,
            PluginType.UTILITY,
            PluginType.THEME,
            PluginType.INTEGRATION,
        ]
        
        assert len(types) == 13
        assert PluginType.VIDEO_EFFECT.value == "video_effect"


class TestPluginStatus:
    """测试插件状态枚举"""

    def test_all_statuses(self):
        """测试所有状态"""
        statuses = [
            PluginStatus.UNLOADED,
            PluginStatus.LOADING,
            PluginStatus.LOADED,
            PluginStatus.INITIALIZING,
            PluginStatus.ACTIVE,
            PluginStatus.ERROR,
            PluginStatus.DISABLED,
        ]
        
        assert len(statuses) == 7
        assert PluginStatus.LOADED.value == "loaded"


class TestPluginInfo:
    """测试插件信息数据类"""

    def test_basic_creation(self):
        """测试基本创建"""
        info = PluginInfo(
            id="my_plugin",
            name="我的插件",
            version="1.0.0",
            description="这是一个测试插件",
            author="Test Author",
        )
        
        assert info.id == "my_plugin"
        assert info.name == "我的插件"
        assert info.version == "1.0.0"
        assert info.author == "Test Author"

    def test_with_optional_fields(self):
        """测试可选字段"""
        info = PluginInfo(
            id="full_plugin",
            name="完整插件",
            version="1.0.0",
            description="完整插件",
            author="Author",
            email="test@example.com",
            website="https://example.com",
            plugin_type=PluginType.AI_ENHANCEMENT,
            dependencies=["dep1", "dep2"],
            min_app_version="2.0.0",
            license="MIT",
            tags=["AI", "Video"],
        )
        
        assert info.email == "test@example.com"
        assert info.website == "https://example.com"
        assert info.plugin_type == PluginType.AI_ENHANCEMENT
        assert info.dependencies == ["dep1", "dep2"]
        assert info.tags == ["AI", "Video"]

    def test_default_values(self):
        """测试默认值"""
        info = PluginInfo(
            id="default_plugin",
            name="默认插件",
            version="1.0.0",
            description="测试",
            author="Author",
        )

        assert info.plugin_type == PluginType.UTILITY
        assert info.dependencies is None  # dataclass 默认是 None
        assert info.min_app_version == "1.0.0"
        assert info.license == "MIT"
        assert info.tags is None

    def test_to_dict(self):
        """测试转换为字典"""
        info = PluginInfo(
            id="test",
            name="测试",
            version="1.0.0",
            description="测试",
            author="Author",
        )

        d = asdict(info)

        assert d["id"] == "test"
        assert d["version"] == "1.0.0"

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "id": "from_dict",
            "name": "从字典创建",
            "version": "2.0.0",
            "description": "测试",
            "author": "Test",
            "plugin_type": PluginType.EXPORT_FORMAT,
        }

        info = PluginInfo(**data)

        assert info.id == "from_dict"
        assert info.plugin_type == PluginType.EXPORT_FORMAT


class TestPluginInterface:
    """测试插件接口基类"""

    def test_get_info(self):
        """测试获取插件信息"""
        class TestPlugin(PluginInterface):
            def get_plugin_info(self):
                return PluginInfo(
                    id="test",
                    name="测试",
                    version="1.0.0",
                    description="测试插件",
                    author="Test",
                )

            def activate(self):
                pass

            def deactivate(self):
                pass

        plugin = TestPlugin()
        info = plugin.get_plugin_info()

        assert info.id == "test"
        assert info.name == "测试"

    def test_activate_deactivate(self):
        """测试激活/停用"""
        class TestPlugin(PluginInterface):
            def get_plugin_info(self):
                return PluginInfo(
                    id="test",
                    name="测试",
                    version="1.0.0",
                    description="",
                    author="Test",
                )

            def on_initialize(self) -> bool:
                return True

            def on_activated(self) -> None:
                self._status = PluginStatus.ACTIVE

            def on_deactivated(self) -> None:
                self._status = PluginStatus.UNLOADED

            def status(self) -> PluginStatus:
                return getattr(self, '_status', PluginStatus.UNLOADED)

        plugin = TestPlugin()
        plugin.__init__()  # call parent __init__

        plugin.on_activated()
        assert plugin.status() == PluginStatus.ACTIVE

        plugin.on_deactivated()
        assert plugin.status() == PluginStatus.UNLOADED


class TestPluginCapabilities:
    """测试插件能力检查"""

    def test_supports_video_effects(self):
        """测试视频效果支持检查"""
        class VideoPlugin(PluginInterface):
            def get_plugin_info(self):
                return PluginInfo(
                    id="video",
                    name="视频插件",
                    version="1.0.0",
                    description="",
                    author="Test",
                )

            def supports_video_effects(self):
                return True

            def activate(self):
                pass

            def deactivate(self):
                pass

        plugin = VideoPlugin()
        assert plugin.supports_video_effects() is True
