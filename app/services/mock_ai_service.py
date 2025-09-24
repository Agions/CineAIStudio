#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mock AI Service for testing purposes
"""

import time
import threading
from typing import Optional, Callable, Dict, Any
from enum import Enum
from dataclasses import dataclass
from functools import wraps
import logging

from PyQt6.QtCore import QObject, pyqtSignal

from ..utils.error_handler import ErrorType, ErrorSeverity, RecoveryAction, ErrorContext, ErrorInfo, error_handler_decorator


class MockAIServiceErrorType(Enum):
    """模拟AI服务错误类型"""
    NETWORK_TIMEOUT = "network_timeout"
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION_ERROR = "authentication_error"
    MODEL_OVERLOADED = "model_overloaded"
    SERVICE_UNAVAILABLE = "service_unavailable"
    INVALID_INPUT = "invalid_input"


@dataclass
class MockAIServiceConfig:
    """模拟AI服务配置"""
    max_retries: int = 3
    enable_fallback: bool = True
    simulate_errors: bool = False
    error_rate: float = 0.1
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60


class MockAIService(QObject):
    """模拟AI服务"""

    # 信号定义
    processing_started = pyqtSignal(str)  # 处理开始信号
    processing_progress = pyqtSignal(str, int)  # 处理进度信号
    processing_completed = pyqtSignal(str, object)  # 处理完成信号
    processing_error = pyqtSignal(str, str)  # 处理错误信号
    retry_attempt = pyqtSignal(str, int)  # 重试尝试信号

    def __init__(self, config: MockAIServiceConfig = None):
        """初始化模拟AI服务"""
        super().__init__()
        self.config = config or MockAIServiceConfig()
        self.logger = logging.getLogger(__name__)

        # 处理状态
        self.is_processing = False
        self.current_task = None

        # 统计信息
        self.processing_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retry_count": 0,
            "fallback_count": 0
        }

        # 熔断器状态
        self.circuit_breaker_state = {
            "failure_count": 0,
            "last_failure_time": 0,
            "is_open": False
        }

        # 降级服务
        self.fallback_services = {
            "simple_response": self._simple_fallback,
            "cached_result": self._cached_fallback
        }

        # 错误处理器
        self.error_handler = None

    def set_error_handler(self, error_handler):
        """设置错误处理器"""
        self.error_handler = error_handler

    def _check_circuit_breaker(self) -> bool:
        """检查熔断器状态"""
        if self.circuit_breaker_state["is_open"]:
            # 检查是否可以重置熔断器
            if time.time() - self.circuit_breaker_state["last_failure_time"] > self.config.circuit_breaker_timeout:
                self.logger.info("熔断器超时，重置状态")
                self.circuit_breaker_state["is_open"] = False
                self.circuit_breaker_state["failure_count"] = 0
                return True
            else:
                self.logger.warning("熔断器开启，服务暂时不可用")
                return False

        return True

    def _record_failure(self):
        """记录失败"""
        self.circuit_breaker_state["failure_count"] += 1
        self.circuit_breaker_state["last_failure_time"] = time.time()

        if self.circuit_breaker_state["failure_count"] >= self.config.circuit_breaker_threshold:
            self.circuit_breaker_state["is_open"] = True
            self.logger.error(f"熔断器开启，失败次数达到阈值: {self.config.circuit_breaker_threshold}")

    def _simulate_error(self) -> Optional[MockAIServiceErrorType]:
        """模拟错误"""
        if not self.config.simulate_errors:
            return None

        import random
        if random.random() < self.config.error_rate:
            # 随机选择错误类型
            error_types = list(MockAIServiceErrorType)
            return random.choice(error_types)

        return None

    def _get_retry_delay(self, attempt: int) -> float:
        """计算重试延迟"""
        # 指数退避算法
        base_delay = 1.0
        max_delay = 10.0
        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)

        # 添加抖动
        import random
        jitter = delay * 0.1 * random.random()
        return delay + jitter

    def _update_processing_stats(self, success: bool, processing_time: float):
        """更新处理统计"""
        self.processing_stats["total_requests"] += 1
        if success:
            self.processing_stats["successful_requests"] += 1
        else:
            self.processing_stats["failed_requests"] += 1

        # 记录性能指标
        self.logger.info(f"处理统计 - 总请求: {self.processing_stats['total_requests']}, "
                        f"成功: {self.processing_stats['successful_requests']}, "
                        f"失败: {self.processing_stats['failed_requests']}, "
                        f"处理时间: {processing_time:.2f}秒")

    def _simple_fallback(self, input_path: str) -> Dict[str, Any]:
        """简单降级服务"""
        self.logger.info("使用简单降级服务")
        return {
            "fallback": True,
            "service": "simple_response",
            "message": "使用简化处理模式",
            "result": {
                "status": "success",
                "output_path": f"{input_path}_simple_fallback"
            }
        }

    def _cached_fallback(self, input_path: str) -> Dict[str, Any]:
        """缓存降级服务"""
        self.logger.info("使用缓存降级服务")
        return {
            "fallback": True,
            "service": "cached_result",
            "message": "使用缓存结果",
            "result": {
                "status": "success",
                "output_path": f"{input_path}_cached_fallback"
            }
        }

    def _try_fallback_services(self, task_name: str, input_path: str, callback: Optional[Callable] = None) -> Optional[Dict[str, Any]]:
        """尝试降级服务"""
        self.processing_stats["fallback_count"] += 1

        for service_name, service_func in self.fallback_services.items():
            try:
                self.logger.info(f"尝试降级服务: {service_name}")
                result = service_func(input_path)

                if result and result.get("result", {}).get("status") == "success":
                    self.logger.info(f"降级服务成功: {service_name}")
                    self.processing_completed.emit(task_name, result)

                    if callback:
                        callback(result)

                    return result

            except Exception as e:
                self.logger.error(f"降级服务失败 {service_name}: {e}")
                continue

        self.logger.error("所有降级服务都失败")
        return None

    @error_handler_decorator(
        error_type=ErrorType.AI,
        severity=ErrorSeverity.MEDIUM,
        recovery_action=RecoveryAction.RETRY,
        user_message="AI分析失败，正在重试..."
    )
    def analyze_video(self, video_path: str, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """分析视频内容"""
        start_time = time.time()
        self.processing_stats["total_requests"] += 1

        # 验证输入参数
        if not video_path or not isinstance(video_path, str):
            error_info = ErrorInfo(
                error_type=ErrorType.VALIDATION,
                severity=ErrorSeverity.LOW,
                message="Invalid video path provided",
                context=ErrorContext(
                    component="MockAIService",
                    operation="analyze_video",
                    user_action="video_analysis"
                ),
                user_message="视频路径无效"
            )
            if self.error_handler:
                self.error_handler.handle_error(error_info)
            return {"error": "Invalid video path"}

        if not self._check_circuit_breaker():
            if self.config.enable_fallback:
                return self._try_fallback_services("视频分析", video_path, callback)
            return {"error": "Service unavailable"}

        result = self._simulate_processing_with_retry("视频分析", video_path, callback, start_time)
        return {
            "duration": 180,
            "scenes": 5,
            "quality_score": 85,
            "recommended_actions": ["智能剪辑", "字幕生成"],
            "output_path": f"{video_path}_analyzed.json"
        }

    def smart_edit(self, video_path: str, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """智能剪辑"""
        if not self._check_circuit_breaker():
            if self.config.enable_fallback:
                return self._try_fallback_services("智能剪辑", video_path, callback)
            return {"error": "Service unavailable"}

        result = self._simulate_processing_with_retry("智能剪辑", video_path, callback, time.time())
        return {
            "highlights": [
                {"start": 30, "end": 45, "description": "精彩片段1"},
                {"start": 120, "end": 150, "description": "精彩片段2"}
            ],
            "output_path": f"{video_path}_edited.mp4"
        }

    def generate_commentary(self, video_path: str, style: str = "drama", callback: Optional[Callable] = None) -> str:
        """生成解说"""
        style_map = {
            "drama": "短剧解说",
            "third_person": "第三人称解说",
            "highlight": "高能混剪"
        }

        task_name = style_map.get(style, "解说生成")
        if not self._check_circuit_breaker():
            if self.config.enable_fallback:
                return self._try_fallback_services(task_name, video_path, callback)
            return {"error": "Service unavailable"}

        result = self._simulate_processing_with_retry(task_name, video_path, callback, time.time())
        return f"{video_path}_commentary.mp3"

    def _simulate_processing_with_retry(self, task_name: str, input_path: str, callback: Optional[Callable] = None, start_time: float = None) -> Any:
        """模拟AI处理过程 - 增强错误处理版本"""
        def process():
            try:
                self.is_processing = True
                self.current_task = task_name
                self.processing_started.emit(task_name)

                attempt = 0
                last_error = None
                processing_start_time = start_time or time.time()

                while attempt < self.config.max_retries:
                    attempt += 1
                    self.processing_stats["retry_count"] += 1
                    self.retry_attempt.emit(task_name, attempt)

                    try:
                        # 检查是否应该模拟错误
                        simulated_error = self._simulate_error()
                        if simulated_error:
                            if simulated_error == MockAIServiceErrorType.NETWORK_TIMEOUT:
                                raise TimeoutError("网络连接超时")
                            elif simulated_error == MockAIServiceErrorType.RATE_LIMIT:
                                raise Exception("API速率限制 exceeded")
                            elif simulated_error == MockAIServiceErrorType.AUTHENTICATION_ERROR:
                                raise Exception("API密钥认证失败")
                            elif simulated_error == MockAIServiceErrorType.MODEL_OVERLOADED:
                                raise Exception("模型负载过高")
                            elif simulated_error == MockAIServiceErrorType.SERVICE_UNAVAILABLE:
                                raise Exception("服务暂时不可用")
                            elif simulated_error == MockAIServiceErrorType.INVALID_INPUT:
                                raise ValueError("输入参数无效")

                        # 模拟处理进度
                        for progress in range(0, 101, 10):
                            if not self.is_processing:
                                break

                            self.processing_progress.emit(task_name, progress)
                            time.sleep(0.1)  # 模拟处理时间

                        # 生成模拟结果
                        if "分析" in task_name:
                            result = {
                                "duration": 180,  # 3分钟
                                "scenes": 5,
                                "quality_score": 85,
                                "recommended_actions": ["智能剪辑", "字幕生成"],
                                "processing_time": time.time() - processing_start_time,
                                "attempts": attempt
                            }
                        elif "剪辑" in task_name:
                            result = {
                                "segments": 3,
                                "total_duration": 120,
                                "highlights": ["开场", "高潮", "结尾"],
                                "processing_time": time.time() - processing_start_time,
                                "attempts": attempt
                            }
                        else:
                            result = {
                                "output_path": f"{input_path}_processed",
                                "processing_time": time.time() - processing_start_time,
                                "attempts": attempt
                            }

                        # 处理成功
                        self.processing_stats["successful_requests"] += 1
                        self._update_processing_stats(True, time.time() - processing_start_time)
                        self.processing_completed.emit(task_name, result)

                        if callback:
                            callback(result)

                        return result

                    except Exception as e:
                        self.logger.warning(f"AI处理失败 (尝试 {attempt}/{self.config.max_retries}): {e}")
                        last_error = e

                        # 创建错误信息
                        error_info = ErrorInfo(
                            error_type=ErrorType.AI,
                            severity=ErrorSeverity.MEDIUM,
                            message=f"AI处理失败: {str(e)}",
                            exception=e,
                            context=ErrorContext(
                                component="MockAIService",
                                operation=task_name,
                                user_action="AI processing",
                                system_state={
                                    "task_name": task_name,
                                    "input_path": input_path,
                                    "attempt": attempt,
                                    "processing_time": time.time() - processing_start_time
                                }
                            ),
                            recovery_action=RecoveryAction.RETRY if attempt < self.config.max_retries else RecoveryAction.CONTACT_SUPPORT,
                            user_message=f"AI处理失败，正在重试 ({attempt}/{self.config.max_retries})..."
                        )

                        # 处理错误
                        if self.error_handler:
                            self.error_handler.handle_error(error_info, show_dialog=False)

                        if attempt < self.config.max_retries:
                            # 计算重试延迟
                            delay = self._get_retry_delay(attempt)
                            self.logger.info(f"等待 {delay:.2f} 秒后重试第 {attempt} 次...")
                            time.sleep(delay)
                            continue
                        else:
                            # 所有重试都失败，尝试降级服务
                            if self.config.enable_fallback:
                                self.logger.warning(f"所有重试失败，尝试降级服务: {task_name}")
                                fallback_result = self._try_fallback_services(task_name, input_path, callback)
                                if fallback_result and not fallback_result.get("error"):
                                    return fallback_result

                            # 所有重试和降级都失败
                            final_error_msg = f"{task_name}失败: {str(e)}"
                            self.processing_error.emit(task_name, final_error_msg)
                            self._update_processing_stats(False, time.time() - processing_start_time)

                            if callback:
                                callback({"error": final_error_msg, "attempts": attempt})

                            return {"error": final_error_msg, "attempts": attempt}

            finally:
                self.is_processing = False
                self.current_task = None

        # 在新线程中处理
        thread = threading.Thread(target=process)
        thread.daemon = True
        thread.start()

        # 返回一个占位符
        return {
            "status": "processing",
            "task": task_name,
            "max_attempts": self.config.max_retries,
            "fallback_enabled": self.config.enable_fallback
        }

    def cancel_processing(self):
        """取消当前处理"""
        if self.is_processing:
            self.is_processing = False
            self.logger.info("处理已取消")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.processing_stats,
            "circuit_breaker": self.circuit_breaker_state,
            "config": {
                "max_retries": self.config.max_retries,
                "enable_fallback": self.config.enable_fallback,
                "simulate_errors": self.config.simulate_errors,
                "error_rate": self.config.error_rate
            }
        }

    def reset_stats(self):
        """重置统计信息"""
        self.processing_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retry_count": 0,
            "fallback_count": 0
        }
        self.circuit_breaker_state = {
            "failure_count": 0,
            "last_failure_time": 0,
            "is_open": False
        }
        self.logger.info("统计信息已重置")