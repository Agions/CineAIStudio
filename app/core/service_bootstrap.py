#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI-EditX 服务引导程序
简化服务系统的使用，提供高级API
"""

from typing import Optional, Dict, Any, List, Type, TypeVar
from contextlib import contextmanager
import threading

from .service_registry import (
    ServiceRegistry, ServiceDefinition, ServiceLifetime,
    ServiceLifecycleHook, ServiceError, ServiceNotFoundError
)
from .service_config import (
    register_core_services, register_all_services,
    SERVICE_CONFIG_DEFAULTS, validate_dependencies
)
from .logger import Logger
from .event_bus import EventBus


T = TypeVar('T')


class ServiceBootstrap:
    """服务引导程序"""

    def __init__(self):
        self._registry: Optional[ServiceRegistry] = None
        self._logger: Optional[Logger] = None
        self._event_bus: Optional[EventBus] = None
        self._initialized = False
        self._lock = threading.RLock()

    def initialize(self, config: Optional[Dict[str, Any]] = None,
                  auto_register_all: bool = False) -> None:
        """初始化服务系统"""
        with self._lock:
            if self._initialized:
                return

            # 创建基础服务
            temp_logger = Logger("ServiceBootstrap")
            temp_event_bus = EventBus()

            # 创建注册表
            self._registry = ServiceRegistry(temp_logger, temp_event_bus)

            # 设置配置
            if config is None:
                config = SERVICE_CONFIG_DEFAULTS.copy()
            else:
                # 合并默认配置
                merged_config = SERVICE_CONFIG_DEFAULTS.copy()
                merged_config.update(config)
                config = merged_config

            self._registry.set_config(config)

            # 注册核心服务
            register_core_services(self._registry)

            # 注册所有服务（可选）
            if auto_register_all:
                register_all_services(self._registry)

            # 验证依赖
            errors = validate_dependencies()
            if errors:
                raise ServiceError(f"Service dependency validation failed: {errors}")

            # 初始化核心服务
            core_services = ["logger", "event_bus"]
            for service_name in core_services:
                self._registry.start_service(service_name)

            # 获取核心服务引用
            self._logger = self._registry.get("logger")
            self._event_bus = self._registry.get("event_bus")

            self._initialized = True
            self._logger.info("Service system initialized successfully")

    def register_service(self, name: str, service_type: Type[T],
                         factory: Optional[callable] = None,
                         lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
                         dependencies: Optional[List[str]] = None,
                         auto_start: bool = False,
                         priority: int = 0) -> 'ServiceBootstrap':
        """注册服务（链式调用）"""
        self._ensure_initialized()

        from .service_registry import ServiceDependency
        deps = []
        if dependencies:
            deps = [ServiceDependency(dep) for dep in dependencies]

        definition = ServiceDefinition(
            name=name,
            service_type=service_type,
            factory=factory,
            lifetime=lifetime,
            dependencies=deps,
            auto_start=auto_start,
            priority=priority
        )

        self._registry.register(definition)
        return self

    def register_singleton(self, name: str, service_type: Type[T],
                          factory: Optional[callable] = None,
                          dependencies: Optional[List[str]] = None,
                          auto_start: bool = False) -> 'ServiceBootstrap':
        """注册单例服务（链式调用）"""
        return self.register_service(
            name, service_type, factory,
            ServiceLifetime.SINGLETON, dependencies, auto_start
        )

    def register_transient(self, name: str, service_type: Type[T],
                          factory: Optional[callable] = None,
                          dependencies: Optional[List[str]] = None) -> 'ServiceBootstrap':
        """注册瞬态服务（链式调用）"""
        return self.register_service(
            name, service_type, factory,
            ServiceLifetime.TRANSIENT, dependencies, False
        )

    def get(self, service_name: str) -> Any:
        """获取服务实例"""
        self._ensure_initialized()
        return self._registry.get(service_name)

    def get_typed(self, service_name: str, service_type: Type[T]) -> T:
        """获取指定类型的服务实例"""
        service = self.get(service_name)
        if not isinstance(service, service_type):
            raise ServiceError(
                f"Service {service_name} is not of type {service_type.__name__}"
            )
        return service

    def start_service(self, service_name: str, timeout: float = 30.0) -> bool:
        """启动服务"""
        self._ensure_initialized()
        return self._registry.start_service(service_name, timeout)

    def start_all_services(self, timeout: float = 60.0) -> Dict[str, bool]:
        """启动所有自动启动的服务"""
        self._ensure_initialized()
        return self._registry.start_all_services(timeout)

    def stop_service(self, service_name: str, timeout: float = 30.0) -> bool:
        """停止服务"""
        self._ensure_initialized()
        return self._registry.stop_service(service_name, timeout)

    def stop_all_services(self, timeout: float = 60.0) -> Dict[str, bool]:
        """停止所有服务"""
        self._ensure_initialized()
        return self._registry.stop_all_services(timeout)

    def health_check(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """服务健康检查"""
        self._ensure_initialized()
        return self._registry.health_check(service_name)

    def add_hook(self, hook: ServiceLifecycleHook) -> 'ServiceBootstrap':
        """添加生命周期钩子（链式调用）"""
        self._ensure_initialized()
        self._registry.add_hook(hook)
        return self

    def get_service_info(self, service_name: str) -> Optional[Dict[str, Any]]:
        """获取服务信息"""
        self._ensure_initialized()
        return self._registry.get_service_info(service_name)

    def get_all_services_info(self) -> Dict[str, Any]:
        """获取所有服务信息"""
        self._ensure_initialized()
        return self._registry.get_all_services_info()

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        self._ensure_initialized()
        return self._registry.get_statistics()

    @contextmanager
    def scope(self, scope_name: str):
        """创建服务作用域上下文"""
        self._ensure_initialized()
        # 作用域开始
        yield self._registry
        # 作用域结束，清理作用域内的服务实例
        if hasattr(self._registry, '_scoped_instances'):
            if scope_name in self._registry._scoped_instances:
                del self._registry._scoped_instances[scope_name]

    def cleanup(self) -> None:
        """清理资源"""
        if self._registry:
            self._registry.cleanup()
            self._registry = None
        self._logger = None
        self._event_bus = None
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """确保已初始化"""
        if not self._initialized:
            raise ServiceError("Service system not initialized. Call initialize() first.")

    @property
    def logger(self) -> Logger:
        """获取日志服务"""
        if not self._logger:
            raise ServiceError("Logger service not available")
        return self._logger

    @property
    def event_bus(self) -> EventBus:
        """获取事件总线服务"""
        if not self._event_bus:
            raise ServiceError("Event bus service not available")
        return self._event_bus


# 全局服务引导实例
_bootstrap_instance = ServiceBootstrap()
_bootstrap_lock = threading.Lock()


def initialize_services(config: Optional[Dict[str, Any]] = None,
                        auto_register_all: bool = False) -> ServiceBootstrap:
    """初始化全局服务系统"""
    global _bootstrap_instance
    with _bootstrap_lock:
        _bootstrap_instance.initialize(config, auto_register_all)
        return _bootstrap_instance


def get_service(service_name: str) -> Any:
    """获取全局服务实例"""
    return _bootstrap_instance.get(service_name)


def get_typed_service(service_name: str, service_type: Type[T]) -> T:
    """获取指定类型的全局服务实例"""
    return _bootstrap_instance.get_typed(service_name, service_type)


def register_service(name: str, service_type: Type[T],
                    factory: Optional[callable] = None,
                    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
                    dependencies: Optional[List[str]] = None,
                    auto_start: bool = False) -> None:
    """注册全局服务"""
    _bootstrap_instance.register_service(
        name, service_type, factory, lifetime, dependencies, auto_start
    )


def start_all_services(timeout: float = 60.0) -> Dict[str, bool]:
    """启动所有全局服务"""
    return _bootstrap_instance.start_all_services(timeout)


def stop_all_services(timeout: float = 60.0) -> Dict[str, bool]:
    """停止所有全局服务"""
    return _bootstrap_instance.stop_all_services(timeout)


def cleanup_services() -> None:
    """清理全局服务系统"""
    _bootstrap_instance.cleanup()


class ServiceAccessor:
    """服务访问器 - 简化服务获取"""

    def __init__(self, bootstrap: Optional[ServiceBootstrap] = None):
        self._bootstrap = bootstrap or _bootstrap_instance

    def __getattr__(self, service_name: str) -> Any:
        """通过属性访问服务"""
        try:
            return self._bootstrap.get(service_name)
        except ServiceNotFoundError:
            raise AttributeError(f"Service '{service_name}' not found")

    def get(self, service_name: str) -> Any:
        """获取服务实例"""
        return self._bootstrap.get(service_name)

    def get_typed(self, service_name: str, service_type: Type[T]) -> T:
        """获取指定类型的服务实例"""
        return self._bootstrap.get_typed(service_name, service_type)


# 全局服务访问器
services = ServiceAccessor()


# 便捷装饰器
def service_method(service_name: str):
    """服务方法装饰器 - 自动注入服务依赖"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            service = get_service(service_name)
            return func(service, *args, **kwargs)
        return wrapper
    return decorator


def service_class(*required_services: str):
    """服务类装饰器 - 自动注入所需服务"""
    def decorator(cls):
        original_init = cls.__init__

        def __init__(self, *args, **kwargs):
            # 注入服务
            for service_name in required_services:
                setattr(self, f"_{service_name}", get_service(service_name))

            original_init(self, *args, **kwargs)

        cls.__init__ = __init__
        return cls
    return decorator


# 环境管理
class ServiceEnvironment:
    """服务环境管理器"""

    def __init__(self):
        self._environments = {}
        self._current_env = None

    def add_environment(self, name: str, config: Dict[str, Any]) -> None:
        """添加环境配置"""
        self._environments[name] = config

    def switch_environment(self, name: str) -> None:
        """切换环境"""
        if name not in self._environments:
            raise ValueError(f"Environment {name} not found")

        # 停止当前服务
        if self._current_env:
            stop_all_services()

        # 切换环境
        self._current_env = name
        config = self._environments[name]

        # 重新初始化服务
        initialize_services(config)

    def get_current_environment(self) -> Optional[str]:
        """获取当前环境"""
        return self._current_env


# 全局环境管理器
environment = ServiceEnvironment()

# 预定义环境
environment.add_environment("development", {
    "logger": {"level": "DEBUG"},
    "debug": True,
    "auto_start_all": False
})

environment.add_environment("production", {
    "logger": {"level": "WARNING"},
    "debug": False,
    "auto_start_all": True
})

environment.add_environment("testing", {
    "logger": {"level": "ERROR"},
    "debug": True,
    "auto_start_all": False
})