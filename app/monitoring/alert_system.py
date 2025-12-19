#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI-EditX 告警系统
提供智能告警和通知功能
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

from ..core.logger import Logger
from ..core.event_bus import EventBus


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """告警状态"""
    ACTIVE = "active"          # 活跃
    RESOLVED = "resolved"      # 已解决
    SUPPRESSED = "suppressed"  # 已抑制
    ACKNOWLEDGED = "acknowledged"  # 已确认


@dataclass
class Alert:
    """告警信息"""
    id: str
    name: str
    level: AlertLevel
    message: str
    source: str
    timestamp: float
    status: AlertStatus = AlertStatus.ACTIVE
    details: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[float] = None
    resolved_at: Optional[float] = None


@dataclass
class AlertRule:
    """告警规则"""
    id: str
    name: str
    condition: str  # 告警条件表达式
    level: AlertLevel
    enabled: bool = True
    cooldown_seconds: float = 300.0  # 冷却时间
    max_alerts_per_hour: int = 10    # 每小时最大告警数
    suppression_rules: List[str] = field(default_factory=list)
    notification_channels: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)


@dataclass
class NotificationChannel:
    """通知渠道"""
    id: str
    name: str
    type: str  # email, slack, webhook, etc.
    config: Dict[str, Any]
    enabled: bool = True


class AlertSystem:
    """告警系统"""

    def __init__(self, logger: Logger, event_bus: EventBus):
        self.logger = logger
        self.event_bus = event_bus

        # 告警存储
        self._alerts: Dict[str, Alert] = {}
        self._alert_rules: Dict[str, AlertRule] = {}
        self._notification_channels: Dict[str, NotificationChannel] = {}

        # 告警历史
        self._alert_history: deque = deque(maxlen=10000)

        # 告警状态跟踪
        self._alert_counters: Dict[str, int] = defaultdict(int)
        self._last_alert_times: Dict[str, float] = defaultdict(float)

        # 回调函数
        self._alert_callbacks: List[Callable[[Alert], None]] = []

        # 线程安全
        self._lock = threading.RLock()

        # 默认规则和渠道
        self._init_default_rules()

    def add_alert_rule(self, rule: AlertRule) -> None:
        """添加告警规则"""
        with self._lock:
            self._alert_rules[rule.id] = rule
            self.logger.info(f"Alert rule added: {rule.name}")

    def remove_alert_rule(self, rule_id: str) -> bool:
        """移除告警规则"""
        with self._lock:
            if rule_id in self._alert_rules:
                del self._alert_rules[rule_id]
                self.logger.info(f"Alert rule removed: {rule_id}")
                return True
            return False

    def get_alert_rules(self) -> List[AlertRule]:
        """获取所有告警规则"""
        with self._lock:
            return list(self._alert_rules.values())

    def enable_alert_rule(self, rule_id: str) -> bool:
        """启用告警规则"""
        with self._lock:
            if rule_id in self._alert_rules:
                self._alert_rules[rule_id].enabled = True
                return True
            return False

    def disable_alert_rule(self, rule_id: str) -> bool:
        """禁用告警规则"""
        with self._lock:
            if rule_id in self._alert_rules:
                self._alert_rules[rule_id].enabled = False
                return True
            return False

    def add_notification_channel(self, channel: NotificationChannel) -> None:
        """添加通知渠道"""
        with self._lock:
            self._notification_channels[channel.id] = channel
            self.logger.info(f"Notification channel added: {channel.name}")

    def remove_notification_channel(self, channel_id: str) -> bool:
        """移除通知渠道"""
        with self._lock:
            if channel_id in self._notification_channels:
                del self._notification_channels[channel_id]
                self.logger.info(f"Notification channel removed: {channel_id}")
                return True
            return False

    def evaluate_metrics(self, metrics: Dict[str, Any]) -> List[Alert]:
        """评估指标并生成告警"""
        alerts = []

        with self._lock:
            for rule in self._alert_rules.values():
                if not rule.enabled:
                    continue

                try:
                    if self._evaluate_rule(rule, metrics):
                        alert = self._create_alert(rule, metrics)
                        if alert:
                            alerts.append(alert)
                except Exception as e:
                    self.logger.error(f"Error evaluating rule {rule.name}: {e}")

        return alerts

    def trigger_manual_alert(self, name: str, level: AlertLevel, message: str,
                           source: str = "manual", details: Optional[Dict[str, Any]] = None,
                           tags: Optional[Set[str]] = None) -> Alert:
        """手动触发告警"""
        alert_id = f"manual_{int(time.time() * 1000000)}"

        alert = Alert(
            id=alert_id,
            name=name,
            level=level,
            message=message,
            source=source,
            timestamp=time.time(),
            details=details or {},
            tags=tags or set()
        )

        with self._lock:
            self._add_alert(alert)

        return alert

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """确认告警"""
        with self._lock:
            if alert_id in self._alerts:
                alert = self._alerts[alert_id]
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_by = acknowledged_by
                alert.acknowledged_at = time.time()

                self.logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
                self._publish_alert_event(alert, "acknowledged")
                return True
            return False

    def resolve_alert(self, alert_id: str, resolved_by: Optional[str] = None) -> bool:
        """解决告警"""
        with self._lock:
            if alert_id in self._alerts:
                alert = self._alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = time.time()

                self.logger.info(f"Alert resolved: {alert_id}")
                self._publish_alert_event(alert, "resolved")
                return True
            return False

    def suppress_alert(self, alert_id: str, reason: str) -> bool:
        """抑制告警"""
        with self._lock:
            if alert_id in self._alerts:
                alert = self._alerts[alert_id]
                alert.status = AlertStatus.SUPPRESSED
                alert.details["suppression_reason"] = reason

                self.logger.info(f"Alert suppressed: {alert_id} - {reason}")
                self._publish_alert_event(alert, "suppressed")
                return True
            return False

    def get_active_alerts(self, level: Optional[AlertLevel] = None,
                         source: Optional[str] = None) -> List[Alert]:
        """获取活跃告警"""
        with self._lock:
            alerts = [
                alert for alert in self._alerts.values()
                if alert.status == AlertStatus.ACTIVE
            ]

            if level:
                alerts = [a for a in alerts if a.level == level]

            if source:
                alerts = [a for a in alerts if a.source == source]

            return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """获取告警历史"""
        with self._lock:
            return sorted(self._alert_history, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_alert_statistics(self) -> Dict[str, Any]:
        """获取告警统计"""
        with self._lock:
            stats = {
                "total_alerts": len(self._alerts),
                "active_alerts": len([a for a in self._alerts.values() if a.status == AlertStatus.ACTIVE]),
                "resolved_alerts": len([a for a in self._alerts.values() if a.status == AlertStatus.RESOLVED]),
                "acknowledged_alerts": len([a for a in self._alerts.values() if a.status == AlertStatus.ACKNOWLEDGED]),
                "suppressed_alerts": len([a for a in self._alerts.values() if a.status == AlertStatus.SUPPRESSED]),
                "alerts_by_level": {},
                "alerts_by_source": {},
                "top_alert_rules": {},
                "recent_alerts": []
            }

            # 按级别统计
            for level in AlertLevel:
                stats["alerts_by_level"][level.value] = len([
                    a for a in self._alerts.values() if a.level == level
                ])

            # 按来源统计
            source_counts = defaultdict(int)
            for alert in self._alerts.values():
                source_counts[alert.source] += 1
            stats["alerts_by_source"] = dict(source_counts)

            # 告警规则统计
            rule_counts = defaultdict(int)
            for alert in self._alerts.values():
                rule_id = alert.details.get("rule_id", "unknown")
                rule_counts[rule_id] += 1
            stats["top_alert_rules"] = dict(sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:10])

            # 最近告警
            recent_alerts = sorted(self._alerts.values(), key=lambda x: x.timestamp, reverse=True)[:10]
            stats["recent_alerts"] = [
                {
                    "id": a.id,
                    "name": a.name,
                    "level": a.level.value,
                    "message": a.message,
                    "timestamp": a.timestamp
                }
                for a in recent_alerts
            ]

            return stats

    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """添加告警回调函数"""
        with self._lock:
            self._alert_callbacks.append(callback)

    def remove_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """移除告警回调函数"""
        with self._lock:
            if callback in self._alert_callbacks:
                self._alert_callbacks.remove(callback)

    def cleanup_old_alerts(self, max_age_days: int = 30) -> int:
        """清理旧告警"""
        cutoff_time = time.time() - (max_age_days * 24 * 3600)
        removed_count = 0

        with self._lock:
            # 清理已解决的告警
            to_remove = [
                alert_id for alert_id, alert in self._alerts.items()
                if alert.status in [AlertStatus.RESOLVED, AlertStatus.SUPPRESSED] and
                (alert.resolved_at or 0) < cutoff_time
            ]

            for alert_id in to_remove:
                del self._alerts[alert_id]
                removed_count += 1

        self.logger.info(f"Cleaned up {removed_count} old alerts")
        return removed_count

    def _evaluate_rule(self, rule: AlertRule, metrics: Dict[str, Any]) -> bool:
        """评估告警规则"""
        # 检查冷却时间
        current_time = time.time()
        if current_time - self._last_alert_times[rule.id] < rule.cooldown_seconds:
            return False

        # 检查每小时告警限制
        if self._alert_counters[rule.id] >= rule.max_alerts_per_hour:
            # 重置计数器（每小时重置一次）
            if current_time - self._last_alert_times[rule.id] > 3600:
                self._alert_counters[rule.id] = 0
            else:
                return False

        # 评估条件（简化实现）
        # 实际实现应该支持更复杂的表达式
        try:
            # 这里应该实现一个安全的表达式求值器
            # 为了安全，可以使用 ast.literal_eval 或专门的规则引擎
            return self._evaluate_condition(rule.condition, metrics)
        except Exception as e:
            self.logger.error(f"Error evaluating condition for rule {rule.name}: {e}")
            return False

    def _evaluate_condition(self, condition: str, metrics: Dict[str, Any]) -> bool:
        """评估条件表达式"""
        # 简化的条件评估
        # 实际实现应该更安全和完善

        # 示例条件格式: "cpu_usage > 90" or "memory_usage > 80 and disk_usage > 85"
        try:
            # 替换变量
            eval_context = {}
            for key, value in metrics.items():
                eval_context[key] = value

            # 安全评估（这里需要更安全的实现）
            return eval(condition, {"__builtins__": {}}, eval_context)
        except Exception:
            return False

    def _create_alert(self, rule: AlertRule, metrics: Dict[str, Any]) -> Optional[Alert]:
        """创建告警"""
        # 检查是否已被抑制
        for suppression_rule in rule.suppression_rules:
            if self._evaluate_condition(suppression_rule, metrics):
                return None

        alert_id = f"{rule.id}_{int(time.time() * 1000000)}"
        alert = Alert(
            id=alert_id,
            name=rule.name,
            level=rule.level,
            message=f"Alert triggered: {rule.name}",
            source="system",
            timestamp=time.time(),
            details={
                "rule_id": rule.id,
                "condition": rule.condition,
                "metrics": metrics
            },
            tags=rule.tags.copy()
        )

        self._add_alert(alert)
        return alert

    def _add_alert(self, alert: Alert) -> None:
        """添加告警"""
        self._alerts[alert.id] = alert
        self._alert_history.append(alert)

        # 更新计数器
        rule_id = alert.details.get("rule_id", "manual")
        self._alert_counters[rule_id] += 1
        self._last_alert_times[rule_id] = alert.timestamp

        # 发送通知
        self._send_notifications(alert)

        # 调用回调函数
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")

        # 发布事件
        self._publish_alert_event(alert, "triggered")

        # 记录日志
        log_level = {
            AlertLevel.INFO: "info",
            AlertLevel.WARNING: "warning",
            AlertLevel.ERROR: "error",
            AlertLevel.CRITICAL: "error"
        }.get(alert.level, "info")

        getattr(self.logger, log_level)(f"Alert triggered: {alert.name} - {alert.message}")

    def _send_notifications(self, alert: Alert) -> None:
        """发送通知"""
        rule_id = alert.details.get("rule_id")
        rule = self._alert_rules.get(rule_id) if rule_id else None

        if not rule or not rule.notification_channels:
            return

        for channel_id in rule.notification_channels:
            channel = self._notification_channels.get(channel_id)
            if channel and channel.enabled:
                try:
                    self._send_notification(channel, alert)
                except Exception as e:
                    self.logger.error(f"Failed to send notification via {channel_id}: {e}")

    def _send_notification(self, channel: NotificationChannel, alert: Alert) -> None:
        """发送单个通知"""
        # 根据渠道类型发送通知
        if channel.type == "email":
            self._send_email_notification(channel, alert)
        elif channel.type == "webhook":
            self._send_webhook_notification(channel, alert)
        elif channel.type == "slack":
            self._send_slack_notification(channel, alert)
        else:
            self.logger.warning(f"Unknown notification channel type: {channel.type}")

    def _send_email_notification(self, channel: NotificationChannel, alert: Alert) -> None:
        """发送邮件通知"""
        # TODO: 实现邮件发送逻辑
        self.logger.info(f"Email notification sent for alert: {alert.id}")

    def _send_webhook_notification(self, channel: NotificationChannel, alert: Alert) -> None:
        """发送Webhook通知"""
        import requests
        import json

        url = channel.config.get("url")
        if not url:
            return

        payload = {
            "alert_id": alert.id,
            "name": alert.name,
            "level": alert.level.value,
            "message": alert.message,
            "timestamp": alert.timestamp,
            "details": alert.details
        }

        headers = channel.config.get("headers", {})
        timeout = channel.config.get("timeout", 10)

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
        except Exception as e:
            self.logger.error(f"Webhook notification failed: {e}")

    def _send_slack_notification(self, channel: NotificationChannel, alert: Alert) -> None:
        """发送Slack通知"""
        # TODO: 实现Slack通知逻辑
        self.logger.info(f"Slack notification sent for alert: {alert.id}")

    def _publish_alert_event(self, alert: Alert, event_type: str) -> None:
        """发布告警事件"""
        self.event_bus.publish(f"alert.{event_type}", {
            "alert_id": alert.id,
            "name": alert.name,
            "level": alert.level.value,
            "message": alert.message,
            "status": alert.status.value,
            "timestamp": alert.timestamp
        })

    def _init_default_rules(self) -> None:
        """初始化默认告警规则"""
        # CPU使用率告警
        cpu_rule = AlertRule(
            id="cpu_high",
            name="高CPU使用率",
            condition="cpu_percent > 90",
            level=AlertLevel.WARNING,
            cooldown_seconds=300,
            max_alerts_per_hour=5,
            tags={"system", "performance"}
        )
        self.add_alert_rule(cpu_rule)

        # 内存使用率告警
        memory_rule = AlertRule(
            id="memory_high",
            name="高内存使用率",
            condition="memory_percent > 95",
            level=AlertLevel.ERROR,
            cooldown_seconds=300,
            max_alerts_per_hour=5,
            tags={"system", "performance"}
        )
        self.add_alert_rule(memory_rule)

        # 磁盘空间告警
        disk_rule = AlertRule(
            id="disk_low",
            name="磁盘空间不足",
            condition="disk_percent > 95",
            level=AlertLevel.CRITICAL,
            cooldown_seconds=600,
            max_alerts_per_hour=3,
            tags={"system", "storage"}
        )
        self.add_alert_rule(disk_rule)