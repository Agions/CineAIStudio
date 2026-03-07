#!/usr/bin/env python3
"""测试缓存管理器"""

import os
import json
import tempfile
import time
import pytest

from app.core.cache_manager import CacheManager, CacheEntry


@pytest.fixture
def temp_cache_dir():
    """创建临时缓存目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def cache_manager(temp_cache_dir):
    """创建缓存管理器实例"""
    return CacheManager(cache_root=temp_cache_dir)


class TestCacheManager:
    """缓存管理器测试"""

    def test_set_and_get(self, cache_manager):
        """测试设置和获取缓存"""
        cache_manager.set("test_key", {"data": "value"})
        result = cache_manager.get("test_key")
        
        assert result is not None
        assert result["data"] == "value"

    def test_get_nonexistent(self, cache_manager):
        """测试获取不存在的键"""
        result = cache_manager.get("nonexistent")
        assert result is None

    def test_exists(self, cache_manager):
        """测试键是否存在"""
        cache_manager.set("exists_key", "value")
        
        assert cache_manager.exists("exists_key") is True
        assert cache_manager.exists("nonexistent") is False

    def test_delete(self, cache_manager):
        """测试删除缓存"""
        cache_manager.set("to_delete", "value")
        assert cache_manager.exists("to_delete") is True
        
        cache_manager.delete("to_delete")
        assert cache_manager.exists("to_delete") is False

    def test_clear(self, cache_manager):
        """测试清空缓存"""
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", "value2")
        
        cache_manager.clear()
        
        assert cache_manager.exists("key1") is False
        assert cache_manager.exists("key2") is False

    def test_ttl_expiration(self, temp_cache_dir):
        """测试 TTL 过期"""
        # 创建 1 秒过期的缓存
        cm = CacheManager(cache_root=temp_cache_dir, default_ttl=1)
        cm.set("ttl_key", "value")
        
        # 立即获取应该存在
        assert cm.get("ttl_key") is not None
        
        # 等待过期
        time.sleep(1.5)
        
        # 应该返回 None
        assert cm.get("ttl_key") is None

    def test_cache_stats(self, cache_manager):
        """测试缓存统计"""
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", "value2")
        
        stats = cache_manager.get_stats()
        
        assert stats["total_keys"] == 2
        assert "size_bytes" in stats


class TestCacheEntry:
    """缓存条目测试"""

    def test_entry_creation(self):
        """测试创建缓存条目"""
        entry = CacheEntry(key="test", value={"data": "value"})
        
        assert entry.key == "test"
        assert entry.value["data"] == "value"
        assert entry.created_at > 0

    def test_entry_is_expired(self):
        """测试条目过期"""
        entry = CacheEntry(key="test", value="value", ttl=-1)  # 已过期
        
        assert entry.is_expired() is True

    def test_entry_not_expired(self):
        """测试条目未过期"""
        entry = CacheEntry(key="test", value="value", ttl=3600)  # 1小时后过期
        
        assert entry.is_expired() is False
