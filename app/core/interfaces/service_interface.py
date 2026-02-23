"""
服务基础接口定义

定义所有服务必须实现的基础接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from enum import Enum


class ServiceState(Enum):
    """服务状态枚举"""
    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    STOPPED = "stopped"


class IService(ABC):
    """
    服务基础接口
    
    所有服务类必须实现此接口，以确保一致的生命周期管理。
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """服务名称"""
        pass
    
    @property
    @abstractmethod
    def state(self) -> ServiceState:
        """当前服务状态"""
        pass
    
    @abstractmethod
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        初始化服务
        
        Args:
            config: 服务配置字典
            
        Returns:
            初始化是否成功
        """
        pass
    
    @abstractmethod
    def start(self) -> bool:
        """
        启动服务
        
        Returns:
            启动是否成功
        """
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """停止服务"""
        pass
    
    @abstractmethod
    def destroy(self) -> None:
        """销毁服务，释放资源"""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            服务是否健康
        """
        pass


class IInitializable(ABC):
    """
    可初始化接口
    
    用于需要复杂初始化逻辑的对象。
    """
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        执行初始化
        
        Returns:
            初始化是否成功
        """
        pass
    
    @abstractmethod
    def is_initialized(self) -> bool:
        """
        检查是否已初始化
        
        Returns:
            是否已初始化
        """
        pass


class IConfigurable(ABC):
    """
    可配置接口
    
    用于支持动态配置的对象。
    """
    
    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> None:
        """
        应用配置
        
        Args:
            config: 配置字典
        """
        pass
    
    @abstractmethod
    def get_configuration(self) -> Dict[str, Any]:
        """
        获取当前配置
        
        Returns:
            配置字典
        """
        pass
    
    @abstractmethod
    def validate_configuration(self, config: Dict[str, Any]) -> bool:
        """
        验证配置有效性
        
        Args:
            config: 待验证的配置
            
        Returns:
            配置是否有效
        """
        pass
