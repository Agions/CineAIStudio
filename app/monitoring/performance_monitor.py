#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 性能监控器
提供全面的性能监控、分析和报告功能
"""

import os
import time
import threading
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
from pathlib import Path

from .metrics_collector import MetricsCollector, timer
from .resource_monitor import ResourceMonitor
from .operation_profiler import OperationProfiler
from ..core.logger import Logger
from ..core.event_bus import EventBus


class PerformanceLevel(Enum):
    """性能级别"""
    EXCELLENT = "excellent"      # 优秀
    GOOD = "good"               # 良好
    FAIR = "fair"               # 一般
    POOR = "poor"               # 较差
    CRITICAL = "critical"       # 严重


@dataclass
class PerformanceThresholds:
    """性能阈值配置"""
    cpu_usage_warning: float = 70.0      # CPU使用率警告阈值
    cpu_usage_critical: float = 90.0     # CPU使用率严重阈值
    memory_usage_warning: float = 80.0   # 内存使用率警告阈值
    memory_usage_critical: float = 95.0  # 内存使用率严重阈值
    disk_usage_warning: float = 85.0     # 磁盘使用率警告阈值
    disk_usage_critical: float = 95.0    # 磁盘使用率严重阈值
    response_time_warning: float = 2.0   # 响应时间警告阈值（秒）
    response_time_critical: float = 5.0  # 响应时间严重阈值（秒）
    error_rate_warning: float = 5.0      # 错误率警告阈值（%）
    error_rate_critical: float = 10.0    # 错误率严重阈值（%）


@dataclass
class PerformanceReport:
    """性能报告"""
    timestamp: float
    performance_level: PerformanceLevel
    system_metrics: Dict[str, Any]
    application_metrics: Dict[str, Any]
    bottlenecks: List[Dict[str, Any]]
    recommendations: List[str]
    alerts: List[Dict[str, Any]]


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, logger: Logger, event_bus: EventBus,
                 thresholds: Optional[PerformanceThresholds] = None,
                 monitoring_interval: float = 5.0):
        self.logger = logger
        self.event_bus = event_bus
        self.thresholds = thresholds or PerformanceThresholds()
        self.monitoring_interval = monitoring_interval

        # 监控组件
        self.metrics_collector = MetricsCollector(logger, event_bus)
        self.resource_monitor = ResourceMonitor(logger, event_bus)
        self.operation_profiler = OperationProfiler(logger, event_bus)

        # 监控状态
        self._is_monitoring = False
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # 性能历史数据
        self._performance_history: deque = deque(maxlen=1000)
        self._alert_history: deque = deque(maxlen=1000)

        # 回调函数
        self._alert_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._report_callbacks: List[Callable[[PerformanceReport], None]] = []

        # 订阅事件
        self._subscribe_events()

    def start_monitoring(self) -> None:
        """开始性能监控"""
        if self._is_monitoring:
            self.logger.warning("Performance monitoring already started")
            return

        self._is_monitoring = True
        self._stop_event.clear()

        # 启动监控线程
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self._monitoring_thread.start()

        self.logger.info("Performance monitoring started")

    def stop_monitoring(self) -> None:
        """停止性能监控"""
        if not self._is_monitoring:
            return

        self._is_monitoring = False
        self._stop_event.set()

        # 等待监控线程结束
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=10.0)

        self.logger.info("Performance monitoring stopped")

    def generate_report(self, time_range: Optional[float] = None) -> PerformanceReport:
        """生成性能报告"""
        current_time = time.time()
        start_time = current_time - (time_range or 300.0)  # 默认5分钟

        # 收集指标
        system_metrics = self._collect_system_metrics()
        application_metrics = self._collect_application_metrics()

        # 分析性能
        performance_level = self._evaluate_performance_level(system_metrics, application_metrics)

        # 识别瓶颈
        bottlenecks = self._identify_bottlenecks(system_metrics, application_metrics)

        # 生成建议
        recommendations = self._generate_recommendations(bottlenecks)

        # 检查告警
        alerts = self._check_alerts(system_metrics, application_metrics)

        report = PerformanceReport(
            timestamp=current_time,
            performance_level=performance_level,
            system_metrics=system_metrics,
            application_metrics=application_metrics,
            bottlenecks=bottlenecks,
            recommendations=recommendations,
            alerts=alerts
        )

        # 保存到历史
        self._performance_history.append(report)

        # 调用回调
        self._call_report_callbacks(report)

        return report

    def get_current_performance_level(self) -> PerformanceLevel:
        """获取当前性能级别"""
        system_metrics = self._collect_system_metrics()
        application_metrics = self._collect_application_metrics()
        return self._evaluate_performance_level(system_metrics, application_metrics)

    def get_bottlenecks(self) -> List[Dict[str, Any]]:
        """获取当前瓶颈"""
        system_metrics = self._collect_system_metrics()
        application_metrics = self._collect_application_metrics()
        return self._identify_bottlenecks(system_metrics, application_metrics)

    def get_recommendations(self) -> List[str]:
        """获取性能优化建议"""
        bottlenecks = self._get_current_bottlenecks()
        return self._generate_recommendations(bottlenecks)

    def add_alert_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """添加告警回调函数"""
        self._alert_callbacks.append(callback)

    def add_report_callback(self, callback: Callable[[PerformanceReport], None]) -> None:
        """添加报告回调函数"""
        self._report_callbacks.append(callback)

    def get_performance_history(self, count: int = 100) -> List[PerformanceReport]:
        """获取性能历史"""
        return list(self._performance_history)[-count:]

    def get_alert_history(self, count: int = 100) -> List[Dict[str, Any]]:
        """获取告警历史"""
        return list(self._alert_history)[-count:]

    def update_thresholds(self, thresholds: PerformanceThresholds) -> None:
        """更新性能阈值"""
        self.thresholds = thresholds
        self.logger.info("Performance thresholds updated")

    def export_metrics(self, file_path: str, format: str = "json") -> bool:
        """导出指标数据"""
        try:
            all_metrics = self.metrics_collector.get_all_metrics()

            if format.lower() == "json":
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(all_metrics, f, indent=2, default=str)
            elif format.lower() == "csv":
                import pandas as pd
                df = pd.DataFrame(all_metrics)
                df.to_csv(file_path, index=False)
            else:
                raise ValueError(f"Unsupported format: {format}")

            self.logger.info(f"Metrics exported to {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export metrics: {e}")
            return False

    # 私有方法

    def _monitoring_loop(self) -> None:
        """监控循环"""
        while not self._stop_event.wait(self.monitoring_interval):
            try:
                # 生成性能报告
                report = self.generate_report()

                # 处理告警
                for alert in report.alerts:
                    self._handle_alert(alert)

                # 发布监控事件
                self.event_bus.publish("performance.monitoring", {
                    "performance_level": report.performance_level.value,
                    "bottlenecks_count": len(report.bottlenecks),
                    "alerts_count": len(report.alerts)
                })

            except Exception as e:
                self.logger.error(f"Performance monitoring error: {e}")

    def _collect_system_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        return self.metrics_collector._system_metrics

    def _collect_application_metrics(self) -> Dict[str, Any]:
        """收集应用程序指标"""
        return self.metrics_collector.get_all_metrics()

    def _evaluate_performance_level(self, system_metrics: Dict[str, Any],
                                  application_metrics: Dict[str, Any]) -> PerformanceLevel:
        """评估性能级别"""
        # 系统指标权重
        cpu_weight = 0.3
        memory_weight = 0.3
        disk_weight = 0.2
        response_weight = 0.2

        # 计算各指标得分（0-100）
        cpu_score = self._calculate_metric_score(
            system_metrics.get("cpu", {}).get("percent", 0),
            self.thresholds.cpu_usage_warning,
            self.thresholds.cpu_usage_critical
        )

        memory_score = self._calculate_metric_score(
            system_metrics.get("memory", {}).get("percent", 0),
            self.thresholds.memory_usage_warning,
            self.thresholds.memory_usage_critical
        )

        disk_score = self._calculate_metric_score(
            system_metrics.get("disk", {}).get("percent", 0),
            self.thresholds.disk_usage_warning,
            self.thresholds.disk_usage_critical
        )

        # 响应时间得分（需要从应用指标中获取）
        response_time = self._get_average_response_time(application_metrics)
        response_score = self._calculate_response_time_score(response_time)

        # 计算综合得分
        overall_score = (
            cpu_score * cpu_weight +
            memory_score * memory_weight +
            disk_score * disk_weight +
            response_score * response_weight
        )

        # 确定性能级别
        if overall_score >= 90:
            return PerformanceLevel.EXCELLENT
        elif overall_score >= 70:
            return PerformanceLevel.GOOD
        elif overall_score >= 50:
            return PerformanceLevel.FAIR
        elif overall_score >= 30:
            return PerformanceLevel.POOR
        else:
            return PerformanceLevel.CRITICAL

    def _calculate_metric_score(self, value: float, warning_threshold: float,
                               critical_threshold: float) -> float:
        """计算指标得分"""
        if value >= critical_threshold:
            return 0
        elif value >= warning_threshold:
            # 在警告阈值和严重阈值之间线性降低
            ratio = (value - warning_threshold) / (critical_threshold - warning_threshold)
            return 25 * (1 - ratio)
        else:
            # 在正常范围内线性降低
            ratio = value / warning_threshold
            return 100 - 75 * ratio

    def _calculate_response_time_score(self, response_time: float) -> float:
        """计算响应时间得分"""
        if response_time >= self.thresholds.response_time_critical:
            return 0
        elif response_time >= self.thresholds.response_time_warning:
            ratio = (response_time - self.thresholds.response_time_warning) / \
                   (self.thresholds.response_time_critical - self.thresholds.response_time_warning)
            return 25 * (1 - ratio)
        else:
            ratio = response_time / self.thresholds.response_time_warning
            return 100 - 75 * ratio

    def _get_average_response_time(self, application_metrics: Dict[str, Any]) -> float:
        """获取平均响应时间"""
        # 从计时指标中计算平均响应时间
        timers = application_metrics.get("timers", {})
        if not timers:
            return 0.0

        total_mean = 0.0
        count = 0

        for timer_stats in timers.values():
            if isinstance(timer_stats, dict) and "mean" in timer_stats:
                total_mean += timer_stats["mean"]
                count += 1

        return total_mean / count if count > 0 else 0.0

    def _identify_bottlenecks(self, system_metrics: Dict[str, Any],
                            application_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别性能瓶颈"""
        bottlenecks = []

        # CPU瓶颈
        cpu_percent = system_metrics.get("cpu", {}).get("percent", 0)
        if cpu_percent > self.thresholds.cpu_usage_critical:
            bottlenecks.append({
                "type": "cpu",
                "severity": "critical",
                "value": cpu_percent,
                "threshold": self.thresholds.cpu_usage_critical,
                "description": "CPU使用率过高"
            })
        elif cpu_percent > self.thresholds.cpu_usage_warning:
            bottlenecks.append({
                "type": "cpu",
                "severity": "warning",
                "value": cpu_percent,
                "threshold": self.thresholds.cpu_usage_warning,
                "description": "CPU使用率较高"
            })

        # 内存瓶颈
        memory_percent = system_metrics.get("memory", {}).get("percent", 0)
        if memory_percent > self.thresholds.memory_usage_critical:
            bottlenecks.append({
                "type": "memory",
                "severity": "critical",
                "value": memory_percent,
                "threshold": self.thresholds.memory_usage_critical,
                "description": "内存使用率过高"
            })
        elif memory_percent > self.thresholds.memory_usage_warning:
            bottlenecks.append({
                "type": "memory",
                "severity": "warning",
                "value": memory_percent,
                "threshold": self.thresholds.memory_usage_warning,
                "description": "内存使用率较高"
            })

        # 磁盘瓶颈
        disk_percent = system_metrics.get("disk", {}).get("percent", 0)
        if disk_percent > self.thresholds.disk_usage_critical:
            bottlenecks.append({
                "type": "disk",
                "severity": "critical",
                "value": disk_percent,
                "threshold": self.thresholds.disk_usage_critical,
                "description": "磁盘空间不足"
            })
        elif disk_percent > self.thresholds.disk_usage_warning:
            bottlenecks.append({
                "type": "disk",
                "severity": "warning",
                "value": disk_percent,
                "threshold": self.thresholds.disk_usage_warning,
                "description": "磁盘空间较少"
            })

        # 响应时间瓶颈
        response_time = self._get_average_response_time(application_metrics)
        if response_time > self.thresholds.response_time_critical:
            bottlenecks.append({
                "type": "response_time",
                "severity": "critical",
                "value": response_time,
                "threshold": self.thresholds.response_time_critical,
                "description": "响应时间过长"
            })
        elif response_time > self.thresholds.response_time_warning:
            bottlenecks.append({
                "type": "response_time",
                "severity": "warning",
                "value": response_time,
                "threshold": self.thresholds.response_time_warning,
                "description": "响应时间较长"
            })

        # 分析操作性能瓶颈
        operation_bottlenecks = self.operation_profiler.get_slow_operations()
        for op in operation_bottlenecks:
            bottlenecks.append({
                "type": "operation",
                "severity": "warning" if op["avg_duration"] < 5.0 else "critical",
                "value": op["avg_duration"],
                "operation": op["name"],
                "description": f"操作 {op['name']} 执行时间过长"
            })

        return bottlenecks

    def _generate_recommendations(self, bottlenecks: List[Dict[str, Any]]) -> List[str]:
        """生成性能优化建议"""
        recommendations = []

        for bottleneck in bottlenecks:
            btype = bottleneck["type"]

            if btype == "cpu":
                recommendations.append("考虑优化CPU密集型算法，使用多线程或GPU加速")
                recommendations.append("检查是否有死循环或低效代码")
                recommendations.append("考虑升级CPU或增加核心数量")

            elif btype == "memory":
                recommendations.append("优化内存使用，避免内存泄漏")
                recommendations.append("增加系统内存或使用内存优化技术")
                recommendations.append("检查是否有大对象未及时释放")

            elif btype == "disk":
                recommendations.append("清理不必要的文件释放磁盘空间")
                recommendations.append("考虑使用更大的存储设备")
                recommendations.append("实施磁盘清理策略")

            elif btype == "response_time":
                recommendations.append("优化网络请求和数据传输")
                recommendations.append("使用缓存减少重复计算")
                recommendations.append("优化数据库查询")

            elif btype == "operation":
                recommendations.append(f"优化操作 {bottleneck.get('operation', '')} 的执行效率")
                recommendations.append("考虑使用更高效的算法或数据结构")
                recommendations.append("实施异步处理")

        # 去重
        return list(set(recommendations))

    def _check_alerts(self, system_metrics: Dict[str, Any],
                     application_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查告警"""
        alerts = []

        # 系统指标告警
        for metric_name, value in [("cpu", "cpu_percent"), ("memory", "memory_percent")]:
            metric_value = system_metrics.get(metric_name, {}).get("percent", 0)
            warning_threshold = getattr(self.thresholds, f"{metric_name}_usage_warning")
            critical_threshold = getattr(self.thresholds, f"{metric_name}_usage_critical")

            if metric_value >= critical_threshold:
                alerts.append({
                    "level": "critical",
                    "type": "system",
                    "metric": metric_name,
                    "value": metric_value,
                    "threshold": critical_threshold,
                    "message": f"{metric_name.upper()}使用率严重超标: {metric_value:.1f}%"
                })
            elif metric_value >= warning_threshold:
                alerts.append({
                    "level": "warning",
                    "type": "system",
                    "metric": metric_name,
                    "value": metric_value,
                    "threshold": warning_threshold,
                    "message": f"{metric_name.upper()}使用率过高: {metric_value:.1f}%"
                })

        # 应用程序告警
        error_rate = self._calculate_error_rate(application_metrics)
        if error_rate >= self.thresholds.error_rate_critical:
            alerts.append({
                "level": "critical",
                "type": "application",
                "metric": "error_rate",
                "value": error_rate,
                "threshold": self.thresholds.error_rate_critical,
                "message": f"错误率严重超标: {error_rate:.1f}%"
            })
        elif error_rate >= self.thresholds.error_rate_warning:
            alerts.append({
                "level": "warning",
                "type": "application",
                "metric": "error_rate",
                "value": error_rate,
                "threshold": self.thresholds.error_rate_warning,
                "message": f"错误率过高: {error_rate:.1f}%"
            })

        return alerts

    def _calculate_error_rate(self, application_metrics: Dict[str, Any]) -> float:
        """计算错误率"""
        # 从指标中计算错误率
        # 这里需要根据实际的错误指标来实现
        return 0.0  # 暂时返回0

    def _handle_alert(self, alert: Dict[str, Any]) -> None:
        """处理告警"""
        # 添加到历史
        self._alert_history.append(alert)

        # 调用回调函数
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")

        # 发布告警事件
        self.event_bus.publish("performance.alert", alert)

        # 记录日志
        log_level = "error" if alert["level"] == "critical" else "warning"
        getattr(self.logger, log_level)(f"Performance alert: {alert['message']}")

    def _get_current_bottlenecks(self) -> List[Dict[str, Any]]:
        """获取当前瓶颈"""
        system_metrics = self._collect_system_metrics()
        application_metrics = self._collect_application_metrics()
        return self._identify_bottlenecks(system_metrics, application_metrics)

    def _call_report_callbacks(self, report: PerformanceReport) -> None:
        """调用报告回调函数"""
        for callback in self._report_callbacks:
            try:
                callback(report)
            except Exception as e:
                self.logger.error(f"Report callback error: {e}")

    def _subscribe_events(self) -> None:
        """订阅事件"""
        # 订阅应用程序事件以收集指标
        self.event_bus.subscribe("operation.started", self._on_operation_started)
        self.event_bus.subscribe("operation.completed", self._on_operation_completed)
        self.event_bus.subscribe("operation.failed", self._on_operation_failed)

    def _on_operation_started(self, data: Dict[str, Any]) -> None:
        """操作开始事件处理"""
        operation_name = data.get("operation", "unknown")
        self.operation_profiler.start_operation(operation_name)

    def _on_operation_completed(self, data: Dict[str, Any]) -> None:
        """操作完成事件处理"""
        operation_name = data.get("operation", "unknown")
        duration = data.get("duration", 0.0)
        self.operation_profiler.complete_operation(operation_name, duration, True)

    def _on_operation_failed(self, data: Dict[str, Any]) -> None:
        """操作失败事件处理"""
        operation_name = data.get("operation", "unknown")
        duration = data.get("duration", 0.0)
        error = data.get("error", "unknown error")
        self.operation_profiler.complete_operation(operation_name, duration, False, error)

    def cleanup(self) -> None:
        """清理资源"""
        self.stop_monitoring()
        self.metrics_collector.cleanup()
        self.resource_monitor.cleanup()
        self.operation_profiler.cleanup()


# 全局性能监控器
_performance_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    global _performance_monitor
    if _performance_monitor is None:
        raise RuntimeError("Performance monitor not initialized")
    return _performance_monitor


def set_performance_monitor(monitor: PerformanceMonitor) -> None:
    """设置全局性能监控器"""
    global _performance_monitor
    _performance_monitor = monitor


# 便捷函数
def monitor_performance(name: str):
    """性能监控装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                monitor.metrics_collector.record_timer(f"operation.{name}", duration)
                monitor.metrics_collector.increment_counter(f"operation.{name}.success")
                return result
            except Exception as e:
                duration = time.time() - start_time
                monitor.metrics_collector.record_timer(f"operation.{name}", duration)
                monitor.metrics_collector.increment_counter(f"operation.{name}.error")
                raise
        return wrapper
    return decorator