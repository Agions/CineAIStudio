#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineFlow AI LLM 缓存和重试机制
提高 LLM API 调用性能和可靠性
"""

import hashlib
import json
import time
from typing import Optional, Dict, Any, Callable
from functools import wraps
from datetime import datetime, timedelta
from pathlib import Path


class LLMMemoryCache:
    """LLM 响应内存缓存"""

    def __init__(self, max_size: int = 100, ttl: int = 3600):
        """
        初始化缓存

        Args:
            max_size: 最大缓存条目数
            ttl: 缓存过期时间 (秒)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl = ttl
        self.access_order: list = []

    def _generate_key(
        self,
        messages: list,
        model: str,
        temperature: Optional[float] = None
    ) -> str:
        """生成缓存键"""
        # 创建包含所有参数的字符串
        data = {
            "messages": messages,
            "model": model,
            "temperature": temperature
        }
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)

        # 使用 MD5 哈希生成键
        return hashlib.md5(data_str.encode()).hexdigest()

    def get(
        self,
        messages: list,
        model: str,
        temperature: Optional[float] = None
    ) -> Optional[str]:
        """获取缓存响应"""
        key = self._generate_key(messages, model, temperature)

        if key in self.cache:
            entry = self.cache[key]

            # 检查是否过期
            if time.time() - entry["timestamp"] < self.ttl:
                # 更新访问顺序
                if key in self.access_order:
                    self.access_order.remove(key)
                self.access_order.append(key)

                return entry["response"]
            else:
                # 已过期，删除
                del self.cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)

        return None

    def set(
        self,
        messages: list,
        model: str,
        response: str,
        temperature: Optional[float] = None
    ) -> None:
        """设置缓存"""
        key = self._generate_key(messages, model, temperature)

        # 如果达到最大容量，删除最旧的条目
        if len(self.cache) >= self.max_size:
            if self.access_order:
                oldest_key = self.access_order.pop(0)
                if oldest_key in self.cache:
                    del self.cache[oldest_key]

        # 添加新条目
        self.cache[key] = {
            "response": response,
            "timestamp": time.time()
        }
        self.access_order.append(key)

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.access_order.clear()

    def get_stats(self) -> Dict[str, int]:
        """获取缓存统计信息"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl": self.ttl
        }


class LLMRetryPolicy:
    """LLM 请求重试策略"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0
    ):
        """
        初始化重试策略

        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟时间 (秒)
            max_delay: 最大延迟时间 (秒)
            backoff_factor: 退避因子 (指数退避)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor

    def get_delay(self, retry_count: int) -> float:
        """
        计算下一次重试的延迟时间

        Args:
            retry_count: 已重试次数

        Returns:
            延迟时间 (秒)
        """
        delay = self.base_delay * (self.backoff_factor ** retry_count)
        return min(delay, self.max_delay)


def with_retry(
    policy: Optional[LLMRetryPolicy] = None,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None
):
    """
    装饰器: 为函数添加重试功能

    Args:
        policy: 重试策略
        exceptions: 需要重试的异常类型
        on_retry: 重试回调函数
    """
    if policy is None:
        policy = LLMRetryPolicy()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(policy.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    # 如果是最后一次尝试，抛出异常
                    if attempt >= policy.max_retries:
                        break

                    # 计算延迟
                    delay = policy.get_delay(attempt)

                    # 调用重试回调
                    if on_retry:
                        on_retry(attempt + 1, e)

                    # 等待后重试
                    if delay > 0:
                        time.sleep(delay)

            raise last_exception

        return wrapper
    return decorator


class LLMPerformanceMonitor:
    """LLM 性能监控"""

    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }

    def record_request(
        self,
        success: bool,
        tokens: Optional[int] = None,
        time_taken: Optional[float] = None
    ) -> None:
        """记录请求"""
        self.metrics["total_requests"] += 1

        if success:
            self.metrics["successful_requests"] += 1
            if tokens:
                self.metrics["total_tokens"] += tokens
            if time_taken:
                self.metrics["total_time"] += time_taken
        else:
            self.metrics["failed_requests"] += 1

    def record_cache_hit(self) -> None:
        """记录缓存命中"""
        self.metrics["cache_hits"] += 1

    def record_cache_miss(self) -> None:
        """记录缓存未命中"""
        self.metrics["cache_misses"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.metrics.copy()

        # 计算命中率
        total_cache_access = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        if total_cache_access > 0:
            stats["cache_hit_rate"] = self.metrics["cache_hits"] / total_cache_access

        # 计算成功率
        if self.metrics["total_requests"] > 0:
            stats["success_rate"] = self.metrics["successful_requests"] / self.metrics["total_requests"]

        # 计算平均响应时间
        if self.metrics["successful_requests"] > 0:
            stats["avg_response_time"] = self.metrics["total_time"] / self.metrics["successful_requests"]
        else:
            stats["avg_response_time"] = 0.0

        # 计算总花费 (按 0.001 元 / token 估算)
        stats["estimated_cost"] = self.metrics["total_tokens"] * 0.001

        return stats

    def print_stats(self) -> None:
        """打印统计信息"""
        stats = self.get_stats()

        print("\n📊 LLM 性能统计")
        print("=" * 50)
        print(f"总请求数: {stats['total_requests']}")
        print(f"成功请求: {stats['successful_requests']}")
        print(f"失败请求: {stats['failed_requests']}")

        if "success_rate" in stats:
            print(f"成功率: {stats['success_rate']:.1%}")

        print(f"\n缓存命中: {stats['cache_hits']}")
        print(f"缓存未命中: {stats['cache_misses']}")

        if "cache_hit_rate" in stats:
            print(f"缓存命中率: {stats['cache_hit_rate']:.1%}")

        print(f"\n总 Token 数: {stats['total_tokens']}")
        print(f"估计成本: ¥{stats['estimated_cost']:.2f}")

        if stats['avg_response_time'] > 0:
            print(f"平均响应时间: {stats['avg_response_time']:.2f} 秒")

        print("=" * 50)

    def reset(self) -> None:
        """重置统计信息"""
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }


# 全局缓存和监控实例
_global_cache = LLMMemoryCache()
_global_monitor = LLMPerformanceMonitor()


def get_global_cache() -> LLMMemoryCache:
    """获取全局缓存实例"""
    return _global_cache


def get_global_monitor() -> LLMPerformanceMonitor:
    """获取全局监控实例"""
    return _global_monitor
