#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI-EditX 服务配置
定义系统服务的配置和依赖关系
"""

from typing import List, Dict, Any
from .service_registry import (
    ServiceDefinition, ServiceDependency, ServiceLifetime,
    ServiceRegistry
)
from .logger import Logger
from .event_bus import EventBus


# 核心服务配置
CORE_SERVICES = [
    ServiceDefinition(
        name="logger",
        service_type=Logger,
        factory=lambda: Logger("AI-EditX"),
        lifetime=ServiceLifetime.SINGLETON,
        auto_start=True,
        priority=-100  # 最高优先级，最先初始化
    ),

    ServiceDefinition(
        name="event_bus",
        service_type=EventBus,
        factory=lambda: EventBus(),
        lifetime=ServiceLifetime.SINGLETON,
        auto_start=True,
        priority=-90,
        dependencies=[
            ServiceDependency("logger")
        ]
    ),
]

# 配置管理服务
CONFIG_SERVICES = [
    ServiceDefinition(
        name="config_manager",
        service_type=object,  # 实际类型应该是 ConfigManager
        lifetime=ServiceLifetime.SINGLETON,
        auto_start=True,
        priority=-80,
        dependencies=[
            ServiceDependency("logger")
        ],
        config_section="config"
    ),
]

# 管理器服务
MANAGER_SERVICES = [
    ServiceDefinition(
        name="icon_manager",
        service_type=object,  # 实际类型应该是 IconManager
        lifetime=ServiceLifetime.SINGLETON,
        auto_start=True,
        priority=-70,
        dependencies=[
            ServiceDependency("logger"),
            ServiceDependency("config_manager")
        ],
        config_section="icons"
    ),

    ServiceDefinition(
        name="project_manager",
        service_type=object,  # 实际类型应该是 ProjectManager
        lifetime=ServiceLifetime.SINGLETON,
        auto_start=False,  # 需要用户交互后才启动
        priority=0,
        dependencies=[
            ServiceDependency("logger"),
            ServiceDependency("config_manager"),
            ServiceDependency("event_bus")
        ],
        config_section="projects"
    ),
]

# AI 服务
AI_SERVICES = [
    ServiceDefinition(
        name="ai_service_manager",
        service_type=object,  # 实际类型应该是 AIServiceManager
        lifetime=ServiceLifetime.SINGLETON,
        auto_start=False,
        priority=10,
        dependencies=[
            ServiceDependency("logger"),
            ServiceDependency("config_manager"),
            ServiceDependency("event_bus")
        ],
        config_section="ai_services"
    ),
]

# 视频服务
VIDEO_SERVICES = [
    ServiceDefinition(
        name="video_service",
        service_type=object,  # 实际类型应该是 VideoService
        lifetime=ServiceLifetime.SINGLETON,
        auto_start=False,
        priority=10,
        dependencies=[
            ServiceDependency("logger"),
            ServiceDependency("config_manager"),
            ServiceDependency("event_bus")
        ],
        config_section="video"
    ),

    ServiceDefinition(
        name="export_service",
        service_type=object,  # 实际类型应该是 ExportService
        lifetime=ServiceLifetime.SINGLETON,
        auto_start=False,
        priority=20,
        dependencies=[
            ServiceDependency("logger"),
            ServiceDependency("video_service"),
            ServiceDependency("config_manager")
        ],
        config_section="export"
    ),
]

# 所有服务配置
ALL_SERVICES = (
    CORE_SERVICES +
    CONFIG_SERVICES +
    MANAGER_SERVICES +
    AI_SERVICES +
    VIDEO_SERVICES
)


def register_core_services(registry: ServiceRegistry) -> None:
    """注册核心服务到注册表"""
    for definition in CORE_SERVICES:
        registry.register(definition)


def register_all_services(registry: ServiceRegistry) -> None:
    """注册所有服务到注册表"""
    for definition in ALL_SERVICES:
        registry.register(definition)


def get_service_dependencies(service_name: str) -> List[str]:
    """获取服务的依赖列表"""
    for definition in ALL_SERVICES:
        if definition.name == service_name:
            return [dep.service_name for dep in definition.dependencies]
    return []


def get_startup_order() -> List[str]:
    """获取服务启动顺序（按优先级排序）"""
    auto_services = [defn for defn in ALL_SERVICES if defn.auto_start]
    auto_services.sort(key=lambda x: x.priority)
    return [defn.name for defn in auto_services]


def validate_dependencies() -> List[str]:
    """验证所有服务的依赖关系"""
    errors = []

    # 创建服务名称映射
    service_names = {defn.name for defn in ALL_SERVICES}

    for definition in ALL_SERVICES:
        for dep in definition.dependencies:
            if dep.required and dep.service_name not in service_names:
                errors.append(
                    f"Service {definition.name} requires {dep.service_name} which is not defined"
                )

    return errors


def get_service_graph() -> Dict[str, List[str]]:
    """获取服务依赖图"""
    graph = {}
    for definition in ALL_SERVICES:
        graph[definition.name] = [dep.service_name for dep in definition.dependencies]
    return graph


# 预定义的服务配置
SERVICE_CONFIG_DEFAULTS = {
    "logger": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file_path": "logs/ai_editx.log",
        "max_file_size": 10 * 1024 * 1024,  # 10MB
        "backup_count": 5
    },

    "event_bus": {
        "max_queue_size": 1000,
        "thread_pool_size": 4,
        "enable_metrics": True
    },

    "config_manager": {
        "config_file": "config/ai_editx.json",
        "auto_save": True,
        "validation": True
    },

    "icons": {
        "theme": "dark",
        "size": 16,
        "fallback_mode": "text"
    },

    "projects": {
        "default_path": "projects",
        "auto_save_interval": 300,  # 5分钟
        "max_recent_projects": 10
    },

    "ai_services": {
        "timeout": 30,
        "retry_attempts": 3,
        "cache_ttl": 3600
    },

    "video": {
        "temp_dir": "temp",
        "cache_enabled": True,
        "gpu_acceleration": True,
        "max_memory_usage": 1024 * 1024 * 1024  # 1GB
    },

    "export": {
        "default_format": "mp4",
        "default_quality": "high",
        "temp_dir": "temp/export",
        "parallel_processing": True
    }
}