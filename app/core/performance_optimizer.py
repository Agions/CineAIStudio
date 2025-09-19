#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
性能优化模块 - 提供系统性能监控和优化功能
"""

import os
import sys
import psutil
import time
import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from collections import deque

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread, QThreadPool, QRunnable
from PyQt6.QtWidgets import QApplication


class PerformanceLevel(Enum):
    """性能级别枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    thread_count: int
    handle_count: int
    fps: Optional[float] = None
    ui_response_time: Optional[float] = None
    custom_metrics: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'memory_used_mb': self.memory_used_mb,
            'memory_total_mb': self.memory_total_mb,
            'thread_count': self.thread_count,
            'handle_count': self.handle_count,
            'fps': self.fps,
            'ui_response_time': self.ui_response_time,
            'custom_metrics': self.custom_metrics or {}
        }


class PerformanceMonitor(QObject):
    """性能监控器"""
    
    # 信号定义
    metrics_updated = pyqtSignal(PerformanceMetrics)  # 性能指标更新信号
    performance_warning = pyqtSignal(str)  # 性能警告信号
    memory_warning = pyqtSignal(float)  # 内存警告信号
    cpu_warning = pyqtSignal(float)  # CPU警告信号
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        
        self._monitoring = False
        self._metrics_history: deque = deque(maxlen=1000)
        self._warning_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'thread_count': 100,
            'ui_response_time': 100.0  # ms
        }
        
        self._monitor_timer = QTimer()
        self._monitor_timer.timeout.connect(self._collect_metrics)
        
        self._last_ui_response_time = time.time()
        self._fps_counter = 0
        self._fps_timer = QTimer()
        self._fps_timer.timeout.connect(self._calculate_fps)
        
    def start_monitoring(self, interval_ms: int = 1000) -> None:
        """开始监控"""
        if self._monitoring:
            return
            
        self._monitoring = True
        self._monitor_timer.start(interval_ms)
        self._fps_timer.start(1000)  # 每秒计算一次FPS
        
    def stop_monitoring(self) -> None:
        """停止监控"""
        self._monitoring = False
        self._monitor_timer.stop()
        self._fps_timer.stop()
        
    def _collect_metrics(self) -> None:
        """收集性能指标"""
        try:
            process = psutil.Process()
            
            # 获取基本指标
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_info.rss / 1024 / 1024,
                memory_total_mb=psutil.virtual_memory().total / 1024 / 1024,
                thread_count=process.num_threads(),
                handle_count=len(process.open_files()),
                fps=self._fps_counter,
                ui_response_time=self._calculate_ui_response_time()
            )
            
            # 添加到历史记录
            self._metrics_history.append(metrics)
            
            # 检查警告
            self._check_warnings(metrics)
            
            # 发射信号
            self.metrics_updated.emit(metrics)
            
        except Exception as e:
            print(f"性能监控错误: {e}")
    
    def _calculate_fps(self) -> None:
        """计算FPS"""
        self._fps_counter = 0
    
    def _calculate_ui_response_time(self) -> float:
        """计算UI响应时间"""
        current_time = time.time()
        response_time = (current_time - self._last_ui_response_time) * 1000
        self._last_ui_response_time = current_time
        return response_time
    
    def _check_warnings(self, metrics: PerformanceMetrics) -> None:
        """检查性能警告"""
        # CPU警告
        if metrics.cpu_percent > self._warning_thresholds['cpu_percent']:
            self.cpu_warning.emit(metrics.cpu_percent)
            self.performance_warning.emit(f"CPU使用率过高: {metrics.cpu_percent:.1f}%")
        
        # 内存警告
        if metrics.memory_percent > self._warning_thresholds['memory_percent']:
            self.memory_warning.emit(metrics.memory_percent)
            self.performance_warning.emit(f"内存使用率过高: {metrics.memory_percent:.1f}%")
        
        # 线程数警告
        if metrics.thread_count > self._warning_thresholds['thread_count']:
            self.performance_warning.emit(f"线程数过多: {metrics.thread_count}")
        
        # UI响应时间警告
        if (metrics.ui_response_time and 
            metrics.ui_response_time > self._warning_thresholds['ui_response_time']):
            self.performance_warning.emit(f"UI响应时间过长: {metrics.ui_response_time:.1f}ms")
    
    def get_metrics_history(self, limit: Optional[int] = None) -> List[PerformanceMetrics]:
        """获取性能历史"""
        history = list(self._metrics_history)
        if limit:
            history = history[-limit:]
        return history
    
    def get_average_metrics(self, duration_seconds: int = 60) -> Optional[PerformanceMetrics]:
        """获取平均性能指标"""
        cutoff_time = datetime.now().timestamp() - duration_seconds
        recent_metrics = [
            m for m in self._metrics_history 
            if m.timestamp.timestamp() > cutoff_time
        ]
        
        if not recent_metrics:
            return None
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_percent=sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
            memory_percent=sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
            memory_used_mb=sum(m.memory_used_mb for m in recent_metrics) / len(recent_metrics),
            memory_total_mb=recent_metrics[0].memory_total_mb,
            thread_count=sum(m.thread_count for m in recent_metrics) / len(recent_metrics),
            handle_count=sum(m.handle_count for m in recent_metrics) / len(recent_metrics),
            fps=sum(m.fps for m in recent_metrics if m.fps) / len([m for m in recent_metrics if m.fps]),
            ui_response_time=sum(m.ui_response_time for m in recent_metrics if m.ui_response_time) / len([m for m in recent_metrics if m.ui_response_time])
        )
    
    def set_warning_threshold(self, metric: str, threshold: float) -> None:
        """设置警告阈值"""
        self._warning_thresholds[metric] = threshold
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """获取当前性能指标"""
        return self._metrics_history[-1] if self._metrics_history else None


class MemoryOptimizer(QObject):
    """内存优化器"""
    
    # 信号定义
    memory_optimized = pyqtSignal(int)  # 内存优化完成信号，参数为释放的MB数
    optimization_started = pyqtSignal()  # 优化开始信号
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._optimization_threshold = 80.0  # 内存使用率阈值
        self._auto_optimize = True
        
    def set_optimization_threshold(self, threshold: float) -> None:
        """设置优化阈值"""
        self._optimization_threshold = threshold
        
    def set_auto_optimize(self, enabled: bool) -> None:
        """设置自动优化"""
        self._auto_optimize = enabled
        
    def optimize_memory(self) -> int:
        """优化内存，返回释放的MB数"""
        self.optimization_started.emit()
        
        try:
            import gc
            
            # 获取优化前的内存使用
            process = psutil.Process()
            before_memory = process.memory_info().rss / 1024 / 1024
            
            # 强制垃圾回收
            gc.collect()
            
            # 清理PyQt缓存
            if QApplication.instance():
                QApplication.instance().processEvents()
            
            # 获取优化后的内存使用
            after_memory = process.memory_info().rss / 1024 / 1024
            freed_memory = before_memory - after_memory
            
            if freed_memory > 0:
                self.memory_optimized.emit(int(freed_memory))
                
            return int(freed_memory)
            
        except Exception as e:
            print(f"内存优化失败: {e}")
            return 0
    
    def should_optimize(self) -> bool:
        """判断是否需要优化"""
        if not self._auto_optimize:
            return False
            
        try:
            process = psutil.Process()
            memory_percent = process.memory_percent()
            return memory_percent > self._optimization_threshold
        except:
            return False


class ThreadManager:
    """线程管理器"""
    
    def __init__(self, max_threads: int = 8):
        self._thread_pool = QThreadPool()
        self._thread_pool.setMaxThreadCount(max_threads)
        self._active_threads = {}
        self._thread_counter = 0
        
    def execute_task(self, task: QRunnable, task_id: Optional[str] = None) -> None:
        """执行任务"""
        if not task_id:
            self._thread_counter += 1
            task_id = f"task_{self._thread_counter}"
        
        # 记录活动线程
        self._active_threads[task_id] = {
            'start_time': datetime.now(),
            'runnable': task
        }
        
        # 任务完成时清理
        def cleanup():
            self._active_threads.pop(task_id, None)
        
        if hasattr(task, 'finished'):
            task.finished.connect(cleanup)
        else:
            # 如果没有finished信号，使用定时器清理
            QTimer.singleShot(60000, cleanup)  # 60秒后清理
        
        self._thread_pool.start(task)
    
    def get_active_threads(self) -> Dict[str, Any]:
        """获取活动线程"""
        return self._active_threads.copy()
    
    def get_thread_count(self) -> int:
        """获取线程数"""
        return len(self._active_threads)
    
    def clear_completed_threads(self) -> None:
        """清理已完成的线程"""
        current_time = datetime.now()
        completed_threads = []
        
        for task_id, thread_info in self._active_threads.items():
            if (current_time - thread_info['start_time']).total_seconds() > 300:  # 5分钟
                completed_threads.append(task_id)
        
        for task_id in completed_threads:
            self._active_threads.pop(task_id, None)
    
    def set_max_threads(self, max_threads: int) -> None:
        """设置最大线程数"""
        self._thread_pool.setMaxThreadCount(max_threads)


class PerformanceOptimizer(QObject):
    """性能优化器 - 整合所有优化功能"""
    
    # 信号定义
    optimization_complete = pyqtSignal(dict)  # 优化完成信号
    performance_report = pyqtSignal(dict)  # 性能报告信号
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        
        self._monitor = PerformanceMonitor(self)
        self._memory_optimizer = MemoryOptimizer(self)
        self._thread_manager = ThreadManager()
        
        # 连接信号
        self._monitor.performance_warning.connect(self._on_performance_warning)
        self._memory_optimizer.memory_optimized.connect(self._on_memory_optimized)
        
        # 自动优化定时器
        self._auto_optimize_timer = QTimer()
        self._auto_optimize_timer.timeout.connect(self._auto_optimize)
        
    def start_monitoring(self, interval_ms: int = 1000) -> None:
        """开始监控"""
        self._monitor.start_monitoring(interval_ms)
        self._auto_optimize_timer.start(30000)  # 每30秒检查一次
        
    def stop_monitoring(self) -> None:
        """停止监控"""
        self._monitor.stop_monitoring()
        self._auto_optimize_timer.stop()
        
    def _on_performance_warning(self, message: str) -> None:
        """处理性能警告"""
        print(f"性能警告: {message}")
        
        # 自动优化
        if "内存" in message and self._memory_optimizer.should_optimize():
            self._memory_optimizer.optimize_memory()
    
    def _on_memory_optimized(self, freed_mb: int) -> None:
        """处理内存优化完成"""
        print(f"内存优化完成，释放了 {freed_mb} MB")
        
    def _auto_optimize(self) -> None:
        """自动优化"""
        # 内存优化
        if self._memory_optimizer.should_optimize():
            self._memory_optimizer.optimize_memory()
        
        # 清理线程
        self._thread_manager.clear_completed_threads()
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        current_metrics = self._monitor.get_current_metrics()
        average_metrics = self._monitor.get_average_metrics(300)  # 5分钟平均值
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'current_metrics': current_metrics.to_dict() if current_metrics else None,
            'average_metrics': average_metrics.to_dict() if average_metrics else None,
            'active_threads': self._thread_manager.get_thread_count(),
            'thread_pool_capacity': self._thread_manager._thread_pool.maxThreadCount(),
            'warnings': {
                'cpu_threshold': self._monitor._warning_thresholds['cpu_percent'],
                'memory_threshold': self._monitor._warning_thresholds['memory_percent'],
                'thread_threshold': self._monitor._warning_thresholds['thread_count']
            }
        }
        
        self.performance_report.emit(report)
        return report
    
    def optimize_system(self) -> Dict[str, Any]:
        """系统优化"""
        results = {
            'memory_freed_mb': 0,
            'threads_cleaned': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        # 内存优化
        results['memory_freed_mb'] = self._memory_optimizer.optimize_memory()
        
        # 线程清理
        before_threads = self._thread_manager.get_thread_count()
        self._thread_manager.clear_completed_threads()
        after_threads = self._thread_manager.get_thread_count()
        results['threads_cleaned'] = before_threads - after_threads
        
        self.optimization_complete.emit(results)
        return results
    
    def get_monitor(self) -> PerformanceMonitor:
        """获取性能监控器"""
        return self._monitor
    
    def get_memory_optimizer(self) -> MemoryOptimizer:
        """获取内存优化器"""
        return self._memory_optimizer
    
    def get_thread_manager(self) -> ThreadManager:
        """获取线程管理器"""
        return self._thread_manager


# 全局性能优化器实例
global_performance_optimizer = PerformanceOptimizer()


def get_performance_optimizer() -> PerformanceOptimizer:
    """获取全局性能优化器"""
    return global_performance_optimizer


def start_performance_monitoring(interval_ms: int = 1000) -> None:
    """开始性能监控"""
    global_performance_optimizer.start_monitoring(interval_ms)


def stop_performance_monitoring() -> None:
    """停止性能监控"""
    global_performance_optimizer.stop_monitoring()