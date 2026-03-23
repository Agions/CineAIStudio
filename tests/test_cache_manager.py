#!/usr/bin/env python3
"""测试缓存管理器"""

import pytest
import time

from app.core.cache_manager import MemoryCache
from app.core.interfaces.cache_interface import CachePolicy


class TestMemoryCache:
    """测试内存缓存"""

    def test_init(self):
        """测试初始化"""
        cache = MemoryCache(max_size=100, max_memory_mb=10)
        
        assert cache._max_size == 100
        assert cache._policy == CachePolicy.LRU

    def test_set_and_get(self):
        """测试设置和获取"""
        cache = MemoryCache()
        
        cache.set("key1", "value1")
        value = cache.get("key1")
        
        assert value == "value1"

    def test_get_nonexistent(self):
        """测试获取不存在的键"""
        cache = MemoryCache()
        
        value = cache.get("nonexistent")
        
        assert value is None

    def test_delete(self):
        """测试删除"""
        cache = MemoryCache()
        
        cache.set("key1", "value1")
        cache.delete("key1")
        value = cache.get("key1")
        
        assert value is None

    def test_clear(self):
        """测试清空"""
        cache = MemoryCache()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_contains(self):
        """测试包含"""
        cache = MemoryCache()
        
        cache.set("key1", "value1")
        
        assert "key1" in cache
        assert "key2" not in cache

    def test_size(self):
        """测试大小"""
        cache = MemoryCache()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        assert cache.size() == 2

    def test_lru_eviction(self):
        """测试 LRU 淘汰"""
        cache = MemoryCache(max_size=2)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # key1 应该被淘汰
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
