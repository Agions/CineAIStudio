"""
缓存管理器

实现统一的缓存系统，支持多种缓存策略。
"""

import os
import json
import pickle
import shutil
from typing import Any, Optional, List, Dict, Callable
from pathlib import Path
from datetime import datetime, timedelta
from collections import OrderedDict
from threading import Lock

from .interfaces.cache_interface import (
    ICache, CacheEntry, CacheStats, CachePolicy,
    generate_cache_key
)


class MemoryCache(ICache):
    """
    内存缓存实现
    
    基于OrderedDict实现LRU缓存。
    """
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100,
                 policy: CachePolicy = CachePolicy.LRU):
        """
        初始化内存缓存
        
        Args:
            max_size: 最大条目数
            max_memory_mb: 最大内存使用（MB）
            policy: 缓存策略
        """
        self._max_size = max_size
        self._max_memory_bytes = max_memory_mb * 1024 * 1024
        self._policy = policy
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        
        # 统计
        self._hit_count = 0
        self._miss_count = 0
        self._eviction_count = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._miss_count += 1
                return None
            
            if entry.is_expired:
                del self._cache[key]
                self._miss_count += 1
                return None
            
            # 更新访问信息
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            
            # LRU策略：移动到末尾
            if self._policy == CachePolicy.LRU:
                self._cache.move_to_end(key)
            
            self._hit_count += 1
            return entry.value
    
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
        try:
            # 估算大小
            size_bytes = len(pickle.dumps(value))
            
            with self._lock:
                # 检查内存限制
                if size_bytes > self._max_memory_bytes:
                    return False
                
                # 计算过期时间
                expires_at = None
                if ttl:
                    expires_at = datetime.now() + timedelta(seconds=ttl)
                
                # 创建条目
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=datetime.now(),
                    expires_at=expires_at,
                    size_bytes=size_bytes,
                    metadata=metadata or {}
                )
                
                # 检查是否需要清理
                self._evict_if_needed(size_bytes)
                
                # 存储
                self._cache[key] = entry
                
                # LRU策略：移动到末尾
                if self._policy == CachePolicy.LRU:
                    self._cache.move_to_end(key)
                
                return True
                
        except Exception as e:
            print(f"缓存设置失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def exists(self, key: str) -> bool:
        """
        检查键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            是否存在
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            if entry.is_expired:
                del self._cache[key]
                return False
            return True
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> CacheStats:
        """
        获取缓存统计
        
        Returns:
            统计信息
        """
        with self._lock:
            total_size = sum(e.size_bytes for e in self._cache.values())
            total_requests = self._hit_count + self._miss_count
            hit_rate = self._hit_count / total_requests if total_requests > 0 else 0
            
            return CacheStats(
                total_entries=len(self._cache),
                total_size_bytes=total_size,
                hit_count=self._hit_count,
                miss_count=self._miss_count,
                eviction_count=self._eviction_count,
                hit_rate=hit_rate,
                avg_entry_size=total_size / len(self._cache) if self._cache else 0,
                max_size_bytes=self._max_memory_bytes,
                policy=self._policy
            )
    
    def get_entry(self, key: str) -> Optional[CacheEntry]:
        """
        获取完整缓存条目
        
        Args:
            key: 缓存键
            
        Returns:
            缓存条目
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry and not entry.is_expired:
                return entry
            return None
    
    def keys(self, pattern: Optional[str] = None) -> List[str]:
        """
        获取所有键
        
        Args:
            pattern: 匹配模式
            
        Returns:
            键列表
        """
        with self._lock:
            keys = list(self._cache.keys())
            
            if pattern:
                import fnmatch
                keys = [k for k in keys if fnmatch.fnmatch(k, pattern)]
            
            return keys
    
    def cleanup_expired(self) -> int:
        """
        清理过期条目
        
        Returns:
            清理的条目数
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    def _evict_if_needed(self, required_bytes: int) -> None:
        """
        如果需要则清理空间
        
        Args:
            required_bytes: 需要的字节数
        """
        current_size = sum(e.size_bytes for e in self._cache.values())
        
        while (len(self._cache) >= self._max_size or 
               current_size + required_bytes > self._max_memory_bytes):
            
            if not self._cache:
                break
            
            # 根据策略选择淘汰项
            if self._policy == CachePolicy.LRU:
                # 移除最久未访问的
                key_to_remove = next(iter(self._cache))
            elif self._policy == CachePolicy.LFU:
                # 移除访问次数最少的
                key_to_remove = min(
                    self._cache.keys(),
                    key=lambda k: self._cache[k].access_count
                )
            else:
                # 默认FIFO
                key_to_remove = next(iter(self._cache))
            
            entry = self._cache.pop(key_to_remove)
            current_size -= entry.size_bytes
            self._eviction_count += 1


class DiskCache(ICache):
    """
    磁盘缓存实现
    
    将缓存持久化到磁盘。
    """
    
    def __init__(self, cache_dir: str, max_size_mb: int = 1000):
        """
        初始化磁盘缓存
        
        Args:
            cache_dir: 缓存目录
            max_size_mb: 最大缓存大小（MB）
        """
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._max_size_bytes = max_size_mb * 1024 * 1024
        self._lock = Lock()
        
        # 统计
        self._hit_count = 0
        self._miss_count = 0
        self._eviction_count = 0
    
    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        # 使用两层目录结构避免单个目录文件过多
        hash_val = hash(key) % 256
        subdir = self._cache_dir / f"{hash_val:02x}"
        subdir.mkdir(exist_ok=True)
        return subdir / f"{key}.cache"
    
    def _get_metadata_path(self, cache_path: Path) -> Path:
        """获取元数据文件路径"""
        return cache_path.with_suffix('.meta')
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        cache_path = self._get_cache_path(key)
        meta_path = self._get_metadata_path(cache_path)
        
        if not cache_path.exists() or not meta_path.exists():
            self._miss_count += 1
            return None
        
        try:
            # 读取元数据
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
            
            # 检查过期
            expires_at = metadata.get('expires_at')
            if expires_at:
                expires = datetime.fromisoformat(expires_at)
                if datetime.now() > expires:
                    self._delete_files(cache_path, meta_path)
                    self._miss_count += 1
                    return None
            
            # 读取缓存值
            with open(cache_path, 'rb') as f:
                value = pickle.load(f)
            
            # 更新访问次数
            metadata['access_count'] = metadata.get('access_count', 0) + 1
            metadata['last_accessed'] = datetime.now().isoformat()
            with open(meta_path, 'w') as f:
                json.dump(metadata, f)
            
            self._hit_count += 1
            return value
            
        except Exception as e:
            print(f"读取缓存失败: {e}")
            self._miss_count += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None,
            metadata: Optional[Dict[str, Any]] = None) -> bool:
        """设置缓存值"""
        try:
            cache_path = self._get_cache_path(key)
            meta_path = self._get_metadata_path(cache_path)
            
            # 序列化值
            data = pickle.dumps(value)
            size_bytes = len(data)
            
            # 检查并清理空间
            self._evict_if_needed(size_bytes)
            
            # 写入缓存文件
            with open(cache_path, 'wb') as f:
                f.write(data)
            
            # 写入元数据
            meta = {
                'key': key,
                'created_at': datetime.now().isoformat(),
                'size_bytes': size_bytes,
                'access_count': 0,
                'metadata': metadata or {}
            }
            
            if ttl:
                meta['expires_at'] = (datetime.now() + timedelta(seconds=ttl)).isoformat()
            
            with open(meta_path, 'w') as f:
                json.dump(meta, f)
            
            return True
            
        except Exception as e:
            print(f"写入缓存失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        cache_path = self._get_cache_path(key)
        meta_path = self._get_metadata_path(cache_path)
        
        if cache_path.exists():
            self._delete_files(cache_path, meta_path)
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        cache_path = self._get_cache_path(key)
        meta_path = self._get_metadata_path(cache_path)
        
        if not cache_path.exists() or not meta_path.exists():
            return False
        
        # 检查过期
        try:
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
            
            expires_at = metadata.get('expires_at')
            if expires_at:
                expires = datetime.fromisoformat(expires_at)
                if datetime.now() > expires:
                    self._delete_files(cache_path, meta_path)
                    return False
            
            return True
        except Exception:
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        if self._cache_dir.exists():
            shutil.rmtree(self._cache_dir)
            self._cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_stats(self) -> CacheStats:
        """获取缓存统计"""
        total_size = 0
        total_entries = 0
        
        for cache_file in self._cache_dir.rglob('*.cache'):
            total_size += cache_file.stat().st_size
            total_entries += 1
        
        total_requests = self._hit_count + self._miss_count
        hit_rate = self._hit_count / total_requests if total_requests > 0 else 0
        
        return CacheStats(
            total_entries=total_entries,
            total_size_bytes=total_size,
            hit_count=self._hit_count,
            miss_count=self._miss_count,
            eviction_count=self._eviction_count,
            hit_rate=hit_rate,
            avg_entry_size=total_size / total_entries if total_entries > 0 else 0,
            max_size_bytes=self._max_size_bytes,
            policy=CachePolicy.LRU
        )
    
    def get_entry(self, key: str) -> Optional[CacheEntry]:
        """获取完整缓存条目"""
        cache_path = self._get_cache_path(key)
        meta_path = self._get_metadata_path(cache_path)
        
        if not meta_path.exists():
            return None
        
        try:
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
            
            expires_at = metadata.get('expires_at')
            if expires_at:
                expires = datetime.fromisoformat(expires_at)
                if datetime.now() > expires:
                    return None
            
            return CacheEntry(
                key=key,
                value=None,  # 不加载值
                created_at=datetime.fromisoformat(metadata['created_at']),
                expires_at=expires,
                access_count=metadata.get('access_count', 0),
                last_accessed=datetime.fromisoformat(metadata.get('last_accessed', metadata['created_at'])),
                size_bytes=metadata['size_bytes'],
                metadata=metadata.get('metadata', {})
            )
        except Exception:
            return None
    
    def keys(self, pattern: Optional[str] = None) -> List[str]:
        """获取所有键"""
        keys = []
        for meta_file in self._cache_dir.rglob('*.meta'):
            try:
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                key = metadata.get('key')
                if key:
                    if pattern is None:
                        keys.append(key)
                    else:
                        import fnmatch
                        if fnmatch.fnmatch(key, pattern):
                            keys.append(key)
            except Exception:
                pass
        return keys
    
    def cleanup_expired(self) -> int:
        """清理过期条目"""
        count = 0
        for meta_file in list(self._cache_dir.rglob('*.meta')):
            try:
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                
                expires_at = metadata.get('expires_at')
                if expires_at:
                    expires = datetime.fromisoformat(expires_at)
                    if datetime.now() > expires:
                        cache_path = meta_file.with_suffix('.cache')
                        self._delete_files(cache_path, meta_file)
                        count += 1
            except Exception:
                pass
        return count
    
    def _delete_files(self, cache_path: Path, meta_path: Path) -> None:
        """删除缓存文件"""
        try:
            if cache_path.exists():
                cache_path.unlink()
            if meta_path.exists():
                meta_path.unlink()
        except Exception:
            pass
    
    def _evict_if_needed(self, required_bytes: int) -> None:
        """如果需要则清理空间"""
        current_size = sum(
            f.stat().st_size 
            for f in self._cache_dir.rglob('*')
            if f.is_file()
        )
        
        while current_size + required_bytes > self._max_size_bytes:
            # 找到最旧的文件
            oldest_file = None
            oldest_time = None
            
            for meta_file in self._cache_dir.rglob('*.meta'):
                try:
                    mtime = meta_file.stat().st_mtime
                    if oldest_time is None or mtime < oldest_time:
                        oldest_time = mtime
                        oldest_file = meta_file
                except Exception:
                    pass
            
            if oldest_file is None:
                break
            
            cache_path = oldest_file.with_suffix('.cache')
            self._delete_files(cache_path, oldest_file)
            
            if cache_path.exists():
                current_size -= cache_path.stat().st_size
            
            self._eviction_count += 1


class CacheManager:
    """
    缓存管理器
    
    统一管理内存缓存和磁盘缓存。
    """
    
    _instance: Optional['CacheManager'] = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._memory_cache = MemoryCache()
            self._disk_cache: Optional[DiskCache] = None
            self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'CacheManager':
        """获取实例"""
        return cls()
    
    def initialize_disk_cache(self, cache_dir: str, max_size_mb: int = 1000) -> None:
        """
        初始化磁盘缓存
        
        Args:
            cache_dir: 缓存目录
            max_size_mb: 最大大小
        """
        self._disk_cache = DiskCache(cache_dir, max_size_mb)
    
    def get(self, key: str, use_disk: bool = True) -> Optional[Any]:
        """
        获取缓存值
        
        先尝试内存缓存，再尝试磁盘缓存。
        
        Args:
            key: 缓存键
            use_disk: 是否使用磁盘缓存
            
        Returns:
            缓存值
        """
        # 先尝试内存缓存
        value = self._memory_cache.get(key)
        if value is not None:
            return value
        
        # 再尝试磁盘缓存
        if use_disk and self._disk_cache:
            value = self._disk_cache.get(key)
            if value is not None:
                # 回填到内存缓存
                self._memory_cache.set(key, value)
                return value
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None,
            use_disk: bool = False, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间
            use_disk: 是否同时写入磁盘缓存
            metadata: 元数据
            
        Returns:
            是否设置成功
        """
        success = self._memory_cache.set(key, value, ttl, metadata)
        
        if success and use_disk and self._disk_cache:
            self._disk_cache.set(key, value, ttl, metadata)
        
        return success
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        memory_deleted = self._memory_cache.delete(key)
        disk_deleted = False
        if self._disk_cache:
            disk_deleted = self._disk_cache.delete(key)
        return memory_deleted or disk_deleted
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if self._memory_cache.exists(key):
            return True
        if self._disk_cache:
            return self._disk_cache.exists(key)
        return False
    
    def clear(self, clear_disk: bool = False) -> None:
        """清空缓存"""
        self._memory_cache.clear()
        if clear_disk and self._disk_cache:
            self._disk_cache.clear()
    
    def get_stats(self) -> Dict[str, CacheStats]:
        """获取缓存统计"""
        stats = {
            'memory': self._memory_cache.get_stats()
        }
        if self._disk_cache:
            stats['disk'] = self._disk_cache.get_stats()
        return stats
    
    def cleanup_expired(self) -> int:
        """清理过期条目"""
        count = self._memory_cache.cleanup_expired()
        if self._disk_cache:
            count += self._disk_cache.cleanup_expired()
        return count
    
    def get_memory_cache(self) -> MemoryCache:
        """获取内存缓存"""
        return self._memory_cache
    
    def get_disk_cache(self) -> Optional[DiskCache]:
        """获取磁盘缓存"""
        return self._disk_cache


# 便捷函数
def get_cache_manager() -> CacheManager:
    """获取缓存管理器"""
    return CacheManager.get_instance()


def cached(ttl: Optional[int] = None, use_disk: bool = False,
           key_func: Optional[Callable] = None):
    """
    缓存装饰器
    
    Args:
        ttl: 过期时间
        use_disk: 是否使用磁盘缓存
        key_func: 自定义键生成函数
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = generate_cache_key(func.__name__, *args, **kwargs)
            
            # 尝试获取缓存
            cache = get_cache_manager()
            result = cache.get(cache_key, use_disk=use_disk)
            
            if result is not None:
                return result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            cache.set(cache_key, result, ttl=ttl, use_disk=use_disk)
            
            return result
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        
        return wrapper
    return decorator
