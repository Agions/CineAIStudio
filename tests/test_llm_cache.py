#!/usr/bin/env python3
"""测试 LLM 缓存模块"""

import pytest
import time
from unittest.mock import Mock, patch

from app.services.ai.cache import LLMMemoryCache


class TestLLMMemoryCache:
    """测试 LLM 内存缓存"""

    def test_init_default(self):
        """测试默认初始化"""
        cache = LLMMemoryCache()
        
        assert cache.max_size == 100
        assert cache.ttl == 3600
        assert cache.cache == {}

    def test_init_custom(self):
        """测试自定义初始化"""
        cache = LLMMemoryCache(max_size=50, ttl=1800)
        
        assert cache.max_size == 50
        assert cache.ttl == 1800

    def test_generate_key(self):
        """测试生成缓存键"""
        cache = LLMMemoryCache()
        
        messages = [{"role": "user", "content": "Hello"}]
        key1 = cache._generate_key(messages, "gpt-4")
        key2 = cache._generate_key(messages, "gpt-4")
        
        # 相同输入应该生成相同的键
        assert key1 == key2

    def test_generate_key_different_inputs(self):
        """测试不同输入生成不同键"""
        cache = LLMMemoryCache()
        
        messages1 = [{"role": "user", "content": "Hello"}]
        messages2 = [{"role": "user", "content": "World"}]
        
        key1 = cache._generate_key(messages1, "gpt-4")
        key2 = cache._generate_key(messages2, "gpt-4")
        
        # 不同输入应该生成不同的键
        assert key1 != key2

    def test_set_and_get(self):
        """测试设置和获取缓存"""
        cache = LLMMemoryCache()
        
        messages = [{"role": "user", "content": "Hello"}]
        
        # 设置缓存
        cache.set(messages, "gpt-4", "Hello! I'm GPT-4.")
        
        # 获取缓存
        result = cache.get(messages, "gpt-4")
        
        assert result == "Hello! I'm GPT-4."

    def test_get_not_exists(self):
        """测试获取不存在的缓存"""
        cache = LLMMemoryCache()
        
        messages = [{"role": "user", "content": "Nonexistent"}]
        result = cache.get(messages, "gpt-4")
        
        assert result is None

    def test_clear(self):
        """测试清空缓存"""
        cache = LLMMemoryCache()
        
        messages = [{"role": "user", "content": "Hello"}]
        cache.set(messages, "gpt-4", "Response")
        
        assert len(cache.cache) > 0
        
        cache.clear()
        
        assert len(cache.cache) == 0

    def test_max_size_limit(self):
        """测试最大容量限制"""
        cache = LLMMemoryCache(max_size=2)
        
        # 添加超过最大容量的缓存
        for i in range(3):
            messages = [{"role": "user", "content": f"Message {i}"}]
            cache.set(messages, "gpt-4", f"Response {i}")
        
        # 应该只保留最新的缓存
        assert len(cache.cache) <= 2


class TestLLMCacheManager:
    """测试 LLM 缓存管理器"""

    def test_init(self):
        """测试初始化"""
        manager = LLMCacheManager()
        
        assert manager._cache is not None
        assert manager._max_size == 100

    def test_cache_response(self):
        """测试缓存响应"""
        manager = LLMCacheManager()
        
        messages = [{"role": "user", "content": "test"}]
        
        # 缓存响应
        manager.cache_response(messages, "gpt-4", "Cached response")
        
        # 获取缓存响应
        result = manager.get_cached_response(messages, "gpt-4")
        
        assert result == "Cached response"

    def test_get_cache_stats(self):
        """测试获取缓存统计"""
        manager = LLMCacheManager()
        
        stats = manager.get_cache_stats()
        
        assert "size" in stats
        assert "max_size" in stats
        assert "hit_rate" in stats
