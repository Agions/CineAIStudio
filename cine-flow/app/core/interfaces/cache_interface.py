"""
缓存接口定义

定义统一的缓存系统接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import hashlib


class CachePolicy(Enum):
    """缓存策略枚举"""
    LRU = "lru"  # 最近最少使用
    LFU = "lfu"  # 最少使用
    FIFO = "fifo"  # 先进先出
    TTL = "ttl"  # 基于过期时间


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = None
    size_bytes: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    @property
    def age_seconds(self) -> float:
        """获取条目年龄（秒）"""
        return (datetime.now() - self.created_at).total_seconds()


@dataclass
class CacheStats:
    """缓存统计信息"""
    total_entries: int
    total_size_bytes: int
    hit_count: int
    miss_count: int
    eviction_count: int
    hit_rate: float
    avg_entry_size: float
    max_size_bytes: int
    policy: CachePolicy


class ICache(ABC):
    """
    缓存接口
    
    提供统一的缓存操作接口。
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值，不存在则返回None
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None,
            metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            metadata: 元数据
            
        Returns:
            是否设置成功
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        检查键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空缓存"""
        pass
    
    @abstractmethod
    def get_stats(self) -> CacheStats:
        """
        获取缓存统计
        
        Returns:
            统计信息
        """
        pass
    
    @abstractmethod
    def get_entry(self, key: str) -> Optional[CacheEntry]:
        """
        获取完整缓存条目
        
        Args:
            key: 缓存键
            
        Returns:
            缓存条目
        """
        pass
    
    @abstractmethod
    def keys(self, pattern: Optional[str] = None) -> List[str]:
        """
        获取所有键
        
        Args:
            pattern: 匹配模式（通配符）
            
        Returns:
            键列表
        """
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> int:
        """
        清理过期条目
        
        Returns:
            清理的条目数
        """
        pass


class ICacheable(ABC):
    """
    可缓存接口
    
    用于可以缓存的对象。
    """
    
    @abstractmethod
    def get_cache_key(self) -> str:
        """
        获取缓存键
        
        Returns:
            缓存键
        """
        pass
    
    @abstractmethod
    def get_cache_ttl(self) -> Optional[int]:
        """
        获取缓存过期时间
        
        Returns:
            过期时间（秒），None表示永不过期
        """
        pass
    
    @abstractmethod
    def to_cache_value(self) -> Any:
        """
        转换为可缓存的值
        
        Returns:
            可缓存的值
        """
        pass
    
    @classmethod
    @abstractmethod
    def from_cache_value(cls, value: Any) -> 'ICacheable':
        """
        从缓存值创建对象
        
        Args:
            value: 缓存值
            
        Returns:
            对象实例
        """
        pass


def generate_cache_key(*args, **kwargs) -> str:
    """
    生成缓存键
    
    基于参数生成唯一的缓存键。
    
    Args:
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        缓存键
    """
    key_parts = []
    
    for arg in args:
        key_parts.append(str(arg))
    
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}={v}")
    
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


class CacheDecorator:
    """
    缓存装饰器
    
    用于自动缓存函数结果。
    """
    
    def __init__(self, cache: ICache, ttl: Optional[int] = None,
                 key_func: Optional[Callable] = None):
        """
        初始化装饰器
        
        Args:
            cache: 缓存实例
            ttl: 过期时间（秒）
            key_func: 自定义键生成函数
        """
        self.cache = cache
        self.ttl = ttl
        self.key_func = key_func or generate_cache_key
    
    def __call__(self, func: Callable) -> Callable:
        """
        装饰函数
        
        Args:
            func: 要装饰的函数
            
        Returns:
            装饰后的函数
        """
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = self.key_func(func.__name__, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_value = self.cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            self.cache.set(cache_key, result, self.ttl)
            
            return result
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        
        return wrapper
