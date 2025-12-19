#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pytest 配置文件
定义测试夹具和全局测试配置
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, Generator

from app.core.application import Application
from app.core.config_manager import ConfigManager
from app.core.logger import Logger
from app.core.service_container import ServiceContainer
from app.core.event_bus import EventBus


@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """创建临时目录夹具"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_config(temp_dir: Path) -> Dict[str, Any]:
    """模拟配置数据"""
    return {
        "app": {
            "name": "AI-EditX-Test",
            "version": "2.0.0-test",
            "debug": True,
        },
        "ui": {
            "theme": "dark",
            "window": {
                "width": 800,
                "height": 600,
                "min_width": 600,
                "min_height": 400,
            },
        },
        "paths": {
            "projects": str(temp_dir / "projects"),
            "temp": str(temp_dir / "temp"),
            "cache": str(temp_dir / "cache"),
            "logs": str(temp_dir / "logs"),
        },
        "ai_services": {
            "openai": {
                "enabled": False,
                "api_key": "test-key",
                "base_url": "https://api.openai.com/v1",
            }
        },
        "video": {
            "default_fps": 30,
            "max_resolution": "1920x1080",
            "supported_formats": [".mp4", ".avi", ".mov", ".mkv"],
        }
    }


@pytest.fixture
def mock_logger():
    """模拟日志记录器"""
    logger = Mock(spec=Logger)
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.critical = Mock()
    return logger


@pytest.fixture
def mock_event_bus():
    """模拟事件总线"""
    event_bus = Mock(spec=EventBus)
    event_bus.subscribe = Mock()
    event_bus.unsubscribe = Mock()
    event_bus.publish = Mock()
    return event_bus


@pytest.fixture
def mock_service_container(mock_logger, mock_event_bus):
    """模拟服务容器"""
    container = Mock(spec=ServiceContainer)

    # 注册基本服务
    def get_service_side_effect(service_name: str):
        if service_name == "logger":
            return mock_logger
        elif service_name == "event_bus":
            return mock_event_bus
        else:
            return None

    container.get_service = Mock(side_effect=get_service_side_effect)
    container.register_service = Mock()
    container.unregister_service = Mock()

    return container


@pytest.fixture
def test_application(mock_config, mock_service_container):
    """测试应用实例"""
    app = Application()
    app._config = mock_config
    app._service_container = mock_service_container
    app._initialized = True
    return app


@pytest.fixture
def sample_video_data():
    """示例视频数据"""
    return {
        "file_path": "/test/sample.mp4",
        "duration": 60.0,
        "fps": 30,
        "resolution": (1920, 1080),
        "codec": "h264",
        "bitrate": 5000000,
        "size": 50000000,
    }


@pytest.fixture
def sample_project_data():
    """示例项目数据"""
    return {
        "name": "测试项目",
        "description": "这是一个测试项目",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "settings": {
            "resolution": "1920x1080",
            "fps": 30,
            "codec": "h264",
        },
        "media_files": [],
        "timeline": [],
        "effects": [],
    }


# 测试标记
pytest_plugins = []

def pytest_configure(config):
    """pytest 配置钩子"""
    config.addinivalue_line(
        "markers", "unit: 单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试"
    )
    config.addinivalue_line(
        "markers", "ui: UI测试"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试"
    )
    config.addinivalue_line(
        "markers", "gpu: 需要GPU的测试"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试项"""
    for item in items:
        # 为UI测试添加标记
        if "ui" in item.nodeid:
            item.add_marker(pytest.mark.ui)

        # 为GPU相关测试添加标记
        if "video" in item.nodeid and "render" in item.nodeid:
            item.add_marker(pytest.mark.gpu)
            item.add_marker(pytest.mark.slow)