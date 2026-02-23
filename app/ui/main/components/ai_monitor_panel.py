#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI状态监控面板
实时监控AI服务的运行状态、性能指标和使用情况
"""

import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QPushButton, QLabel, QFrame, QSpacerItem,
    QSizePolicy, QGroupBox, QStackedWidget, QSplitter,
    QTabWidget, QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QRadioButton, QButtonGroup,
    QFileDialog, QColorDialog, QFontDialog, QMessageBox,
    QSlider, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QListWidget, QListWidgetItem, QProgressBar,
    QFormLayout, QToolButton, QDialog, QDialogButtonBox,
    QSystemTrayIcon, QMenu, QApplication, QStyle
)
from PyQt6.QtCore import (
    Qt, QSize, QTimer, pyqtSignal, QPoint, QRect, QSettings,
    QMimeData, QUrl, QEvent, QRectF, QThread, pyqtSlot,
    QPropertyAnimation, QEasingCurve, QThread
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QFont, QPalette, QColor, QCursor,
    QPainter, QPen, QBrush, QPainterPath, QFontDatabase,
    QDesktopServices, QRegularExpression, QPainter
)

from ...core.config_manager import ConfigManager
from ...core.logger import Logger
from ...core.icon_manager import get_icon
from ...core.application import Application
from ...services.ai_service_manager import AIServiceManager, ServiceStatus
from ...utils.error_handler import handle_exception


class MonitorMode(Enum):
    """监控模式枚举"""
    OVERVIEW = "overview"
    SERVICES = "services"
    PERFORMANCE = "performance"
    USAGE = "usage"
    ALERTS = "alerts"


@dataclass
class AlertData:
    """告警数据"""
    id: str
    service_name: str
    level: str  # info, warning, error, critical
    message: str
    timestamp: float
    resolved: bool = False
    details: Optional[Dict[str, Any]] = None


class ServiceStatusWidget(QWidget):
    """服务状态部件"""

    def __init__(self, service_name: str, status: ServiceStatus, health_data: Dict[str, Any]):
        super().__init__()
        self.service_name = service_name
        self.status = status
        self.health_data = health_data
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 状态指示器
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(12, 12)
        self._update_status_indicator()
        layout.addWidget(self.status_indicator)

        # 服务名称
        name_label = QLabel(self.service_name)
        name_label.setProperty("class", "service-name")
        layout.addWidget(name_label)

        # 状态文本
        self.status_label = QLabel(self._get_status_text())
        self.status_label.setProperty("class", "service-status")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # 响应时间
        if self.health_data.get("response_time"):
            response_time = self.health_data["response_time"]
            time_label = QLabel(f"{response_time:.1f}ms")
            time_label.setProperty("class", "response-time")
            layout.addWidget(time_label)

        # 错误率
        if self.health_data.get("error_rate"):
            error_rate = self.health_data["error_rate"]
            error_label = QLabel(f"错误率: {error_rate:.1%}")
            # 根据错误率设置样式级别
            if error_rate > 0.1:
                error_label.setProperty("class", "error-rate high")
            elif error_rate > 0.05:
                error_label.setProperty("class", "error-rate medium")
            else:
                error_label.setProperty("class", "error-rate low")
            layout.addWidget(error_label)

    def _update_status_indicator(self):
        """更新状态指示器"""
        color_map = {
            ServiceStatus.ACTIVE: "#52c41a",
            ServiceStatus.INACTIVE: "#888888",
            ServiceStatus.ERROR: "#ff4d4f",
            ServiceStatus.MAINTENANCE: "#faad14"
        }

        color = color_map.get(self.status, "#888888")
        pixmap = QPixmap(12, 12)
        pixmap.fill(QColor("transparent"))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(color), 2))
        painter.setBrush(QBrush(QColor(color)))
        painter.drawEllipse(1, 1, 10, 10)
        painter.end()

        self.status_indicator.setPixmap(pixmap)

    def _get_status_text(self) -> str:
        """获取状态文本"""
        status_text_map = {
            ServiceStatus.ACTIVE: "正常运行",
            ServiceStatus.INACTIVE: "未激活",
            ServiceStatus.ERROR: "错误",
            ServiceStatus.MAINTENANCE: "维护中"
        }
        return status_text_map.get(self.status, "未知")

    def update_status(self, status: ServiceStatus, health_data: Dict[str, Any]):
        """更新状态"""
        self.status = status
        self.health_data = health_data
        self._update_status_indicator()
        self.status_label.setText(self._get_status_text())


class PerformanceChart(QWidget):
    """性能图表"""

    def __init__(self, title: str, max_value: float = 100):
        super().__init__()
        self.title = title
        self.max_value = max_value
        self.data_points = []
        self.max_points = 50
        self.setFixedSize(300, 100)

    def add_data_point(self, value: float):
        """添加数据点"""
        self.data_points.append(value)
        if len(self.data_points) > self.max_points:
            self.data_points.pop(0)
        self.update()

    def clear_data(self):
        """清除数据"""
        self.data_points.clear()
        self.update()

    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制背景
        painter.fillRect(self.rect(), QColor("#1a1a1a"))

        # 绘制标题
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.drawText(5, 15, self.title)

        # 绘制网格
        painter.setPen(QPen(QColor("#404040"), 1))
        for i in range(0, 5):
            y = 25 + i * 15
            painter.drawLine(5, y, self.width() - 5, y)

        # 绘制数据线
        if len(self.data_points) > 1:
            painter.setPen(QPen(QColor("#1890ff"), 2))

            path = QPainterPath()
            for i, value in enumerate(self.data_points):
                x = 5 + (i / (self.max_points - 1)) * (self.width() - 10)
                y = 90 - (value / self.max_value) * 60

                if i == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)

            painter.drawPath(path)

            # 绘制数据点
            painter.setPen(QPen(QColor("#1890ff"), 1))
            painter.setBrush(QBrush(QColor("#1890ff")))
            for i, value in enumerate(self.data_points):
                x = 5 + (i / (self.max_points - 1)) * (self.width() - 10)
                y = 90 - (value / self.max_value) * 60
                painter.drawEllipse(QPoint(x, y), 2, 2)

        # 绘制当前值
        if self.data_points:
            current_value = self.data_points[-1]
            painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.drawText(self.width() - 50, 15, f"{current_value:.1f}")


class AlertWidget(QWidget):
    """告警部件"""

    alert_clicked = pyqtSignal(AlertData)

    def __init__(self, alert: AlertData):
        super().__init__()
        self.alert = alert
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 告警图标
        icon_name = {
            "info": "info",
            "warning": "warning",
            "error": "error",
            "critical": "critical"
        }.get(self.alert.level, "info")

        icon_label = QLabel()
        icon_label.setPixmap(get_icon(icon_name, 16).pixmap(16, 16))
        layout.addWidget(icon_label)

        # 告警信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        # 服务名称和级别
        header_layout = QHBoxLayout()
        service_label = QLabel(self.alert.service_name)
        service_label.setProperty("class", "alert-service")
        header_layout.addWidget(service_label)

        level_label = QLabel(self.alert.level.upper())
        level_label.setProperty("class", f"alert-level {self.alert.level}")
        header_layout.addWidget(level_label)

        header_layout.addStretch()

        # 时间
        time_label = QLabel(self._format_time(self.alert.timestamp))
        time_label.setProperty("class", "alert-time")
        header_layout.addWidget(time_label)

        info_layout.addLayout(header_layout)

        # 消息
        message_label = QLabel(self.alert.message)
        message_label.setProperty("class", "alert-message")
        message_label.setWordWrap(True)
        info_layout.addWidget(message_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        # 状态指示器
        if self.alert.resolved:
            resolved_label = QLabel("已解决")
            resolved_label.setProperty("class", "alert-resolved")
            layout.addWidget(resolved_label)

        # 鼠标样式
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.mousePressEvent = self._on_clicked

    def _format_time(self, timestamp: float) -> str:
        """格式化时间"""
        dt = datetime.fromtimestamp(timestamp)
        now = datetime.now()
        delta = now - dt

        if delta < timedelta(minutes=1):
            return "刚刚"
        elif delta < timedelta(hours=1):
            return f"{delta.seconds // 60}分钟前"
        elif delta < timedelta(days=1):
            return f"{delta.seconds // 3600}小时前"
        else:
            return dt.strftime("%Y-%m-%d %H:%M")

    def _on_clicked(self, event):
        """点击处理"""
        self.alert_clicked.emit(self.alert)


class AIMonitorPanel(QWidget):
    """AI状态监控面板"""

    # 信号定义
    service_selected = pyqtSignal(str)
    alert_selected = pyqtSignal(AlertData)
    refresh_requested = pyqtSignal()

    def __init__(self, application: Application):
        super().__init__()
        self.application = application
        self.logger = application.get_service(Logger)
        self.ai_service_manager = None
        self.current_mode = MonitorMode.OVERVIEW
        self.alerts: List[AlertData] = []
        self.performance_data: Dict[str, List[float]] = {}

        # 获取AI服务管理器
        self._get_ai_service_manager()

        # 定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_monitor_data)
        self.update_timer.start(5000)  # 5秒更新一次

        self._init_ui()
        self._setup_connections()

    def _get_ai_service_manager(self):
        """获取AI服务管理器"""
        try:
            self.ai_service_manager = self.application.get_service_by_name("ai_service_manager")
            if not self.ai_service_manager:
                self.logger.warning("AI服务管理器未注册")
        except Exception as e:
            self.logger.error(f"获取AI服务管理器失败: {e}")

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 模式切换栏
        mode_bar = QFrame()
        mode_bar.setFrameShape(QFrame.Shape.StyledPanel)
        # 应用监控面板模式栏样式
        mode_bar.setProperty("class", "monitor-mode-bar")
        mode_layout = QHBoxLayout(mode_bar)
        mode_layout.setContentsMargins(10, 10, 10, 10)

        # 模式按钮
        mode_buttons = []
        for mode in MonitorMode:
            btn = QPushButton(self._get_mode_text(mode))
            btn.setFixedSize(80, 30)
            btn.setCheckable(True)
            btn.setProperty("class", "monitor-mode-button")
            btn.clicked.connect(lambda checked, m=mode: self._switch_mode(m))
            mode_layout.addWidget(btn)
            mode_buttons.append(btn)

        # 设置默认按钮
        mode_buttons[0].setChecked(True)
        mode_buttons[0].setProperty("class", "monitor-mode-button active")
        self.mode_buttons = mode_buttons

        mode_layout.addStretch()

        # 刷新按钮
        refresh_btn = QPushButton(get_icon("refresh", 16), "刷新")
        refresh_btn.setFixedSize(80, 30)
        refresh_btn.setProperty("class", "monitor-refresh-button")
        refresh_btn.clicked.connect(self._refresh_data)
        mode_layout.addWidget(refresh_btn)

        layout.addWidget(mode_bar)

        # 内容区域
        self.content_stack = QStackedWidget()
        self.content_stack.setProperty("class", "monitor-content-stack")

        # 创建各个模式的内容页面
        self.overview_page = self._create_overview_page()
        self.services_page = self._create_services_page()
        self.performance_page = self._create_performance_page()
        self.usage_page = self._create_usage_page()
        self.alerts_page = self._create_alerts_page()

        self.content_stack.addWidget(self.overview_page)
        self.content_stack.addWidget(self.services_page)
        self.content_stack.addWidget(self.performance_page)
        self.content_stack.addWidget(self.usage_page)
        self.content_stack.addWidget(self.alerts_page)

        layout.addWidget(self.content_stack)

    def _get_mode_text(self, mode: MonitorMode) -> str:
        """获取模式文本"""
        mode_texts = {
            MonitorMode.OVERVIEW: "概览",
            MonitorMode.SERVICES: "服务",
            MonitorMode.PERFORMANCE: "性能",
            MonitorMode.USAGE: "使用量",
            MonitorMode.ALERTS: "告警"
        }
        return mode_texts.get(mode, "未知")

    def _switch_mode(self, mode: MonitorMode):
        """切换模式"""
        self.current_mode = mode

        # 更新按钮状态
        for btn in self.mode_buttons:
            btn.setChecked(btn.text() == self._get_mode_text(mode))

        # 切换页面
        page_index = {
            MonitorMode.OVERVIEW: 0,
            MonitorMode.SERVICES: 1,
            MonitorMode.PERFORMANCE: 2,
            MonitorMode.USAGE: 3,
            MonitorMode.ALERTS: 4
        }.get(mode, 0)

        self.content_stack.setCurrentIndex(page_index)

    def _create_overview_page(self) -> QWidget:
        """创建概览页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 统计卡片
        stats_layout = QGridLayout()
        stats_layout.setSpacing(10)

        # 服务状态统计
        service_frame = self._create_stat_card("服务状态", "0/0", "正常运行/总数")
        stats_layout.addWidget(service_frame, 0, 0)

        # 总请求数
        requests_frame = self._create_stat_card("总请求数", "0", "今日请求")
        stats_layout.addWidget(requests_frame, 0, 1)

        # 成功率
        success_frame = self._create_stat_card("成功率", "100%", "请求成功率")
        stats_layout.addWidget(success_frame, 0, 2)

        # 平均响应时间
        response_frame = self._create_stat_card("响应时间", "0ms", "平均响应时间")
        stats_layout.addWidget(response_frame, 1, 0)

        # 总成本
        cost_frame = self._create_stat_card("总成本", "¥0.00", "今日成本")
        stats_layout.addWidget(cost_frame, 1, 1)

        # 告警数量
        alerts_frame = self._create_stat_card("告警", "0", "未解决告警")
        stats_layout.addWidget(alerts_frame, 1, 2)

        layout.addLayout(stats_layout)

        # 服务状态列表
        services_group = QGroupBox("服务状态")
        services_group.setProperty("class", "monitor-group")
        services_layout = QVBoxLayout(services_group)

        self.services_status_list = QWidget()
        self.services_status_layout = QVBoxLayout(self.services_status_list)
        self.services_status_layout.setContentsMargins(0, 0, 0, 0)
        self.services_status_layout.setSpacing(5)

        scroll_area = QScrollArea()
        scroll_area.setWidget(self.services_status_list)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)
        services_layout.addWidget(scroll_area)

        layout.addWidget(services_group)

        # 性能图表
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(10)

        # 响应时间图表
        self.response_time_chart = PerformanceChart("响应时间 (ms)", 1000)
        charts_layout.addWidget(self.response_time_chart)

        # 错误率图表
        self.error_rate_chart = PerformanceChart("错误率 (%)", 100)
        charts_layout.addWidget(self.error_rate_chart)

        # 吞吐量图表
        self.throughput_chart = PerformanceChart("吞吐量 (req/s)", 100)
        charts_layout.addWidget(self.throughput_chart)

        layout.addLayout(charts_layout)

        layout.addStretch()

        # 保存引用
        self.service_stats_label = service_frame.findChild(QLabel, "value_label")
        self.requests_stats_label = requests_frame.findChild(QLabel, "value_label")
        self.success_stats_label = success_frame.findChild(QLabel, "value_label")
        self.response_stats_label = response_frame.findChild(QLabel, "value_label")
        self.cost_stats_label = cost_frame.findChild(QLabel, "value_label")
        self.alerts_stats_label = alerts_frame.findChild(QLabel, "value_label")

        return page

    def _create_stat_card(self, title: str, value: str, subtitle: str) -> QFrame:
        """创建统计卡片 - 使用 QSS 类名"""
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setProperty("class", "monitor-stat-card")
        frame.setFixedSize(200, 80)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)

        # 标题
        title_label = QLabel(title)
        title_label.setProperty("class", "stat-card-title")
        layout.addWidget(title_label)

        # 数值
        value_label = QLabel(value)
        value_label.setProperty("class", "stat-card-value")
        value_label.setObjectName("value_label")
        layout.addWidget(value_label)

        # 副标题
        subtitle_label = QLabel(subtitle)
        subtitle_label.setProperty("class", "stat-card-subtitle")
        layout.addWidget(subtitle_label)

        return frame

    def _create_services_page(self) -> QWidget:
        """创建服务页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 服务列表
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(6)
        self.services_table.setHorizontalHeaderLabels(["服务", "状态", "响应时间", "错误率", "成功率", "操作"])
        self.services_table.horizontalHeader().setStretchLastSection(True)
        self.services_table.verticalHeader().setVisible(False)
        self.services_table.setAlternatingRowColors(True)
        self.services_table.setProperty("class", "monitor-services-table")

        layout.addWidget(self.services_table)

        return page

    def _create_performance_page(self) -> QWidget:
        """创建性能页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 性能图表区域
        charts_group = QGroupBox("性能指标")
        charts_group.setProperty("class", "monitor-group")
        charts_layout = QGridLayout(charts_group)

        # 响应时间趋势
        self.response_trend_chart = PerformanceChart("响应时间趋势 (ms)", 1000)
        charts_layout.addWidget(self.response_trend_chart, 0, 0)

        # 错误率趋势
        self.error_trend_chart = PerformanceChart("错误率趋势 (%)", 100)
        charts_layout.addWidget(self.error_trend_chart, 0, 1)

        # 吞吐量趋势
        self.throughput_trend_chart = PerformanceChart("吞吐量趋势 (req/s)", 100)
        charts_layout.addWidget(self.throughput_trend_chart, 1, 0)

        # CPU使用率
        self.cpu_usage_chart = PerformanceChart("CPU使用率 (%)", 100)
        charts_layout.addWidget(self.cpu_usage_chart, 1, 1)

        layout.addWidget(charts_group)

        return page

    def _create_usage_page(self) -> QWidget:
        """创建使用量页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 使用量统计
        usage_group = QGroupBox("使用量统计")
        usage_group.setProperty("class", "monitor-group")
        usage_layout = QVBoxLayout(usage_group)

        self.usage_table = QTableWidget()
        self.usage_table.setColumnCount(5)
        self.usage_table.setHorizontalHeaderLabels(["服务", "请求数", "成功数", "失败数", "成本"])
        self.usage_table.horizontalHeader().setStretchLastSection(True)
        self.usage_table.verticalHeader().setVisible(False)
        self.usage_table.setAlternatingRowColors(True)
        self.usage_table.setProperty("class", "monitor-usage-table")

        usage_layout.addWidget(self.usage_table)

        layout.addWidget(usage_group)

        return page

    def _create_alerts_page(self) -> QWidget:
        """创建告警页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 告警过滤器
        filter_layout = QHBoxLayout()

        filter_label = QLabel("过滤:")
        filter_layout.addWidget(filter_label)

        self.alert_filter_combo = QComboBox()
        self.alert_filter_combo.addItems(["全部", "信息", "警告", "错误", "严重"])
        self.alert_filter_combo.currentTextChanged.connect(self._filter_alerts)
        filter_layout.addWidget(self.alert_filter_combo)

        filter_layout.addStretch()

        # 清除告警按钮
        clear_btn = QPushButton("清除已解决")
        clear_btn.clicked.connect(self._clear_resolved_alerts)
        filter_layout.addWidget(clear_btn)

        layout.addLayout(filter_layout)

        # 告警列表
        self.alerts_list = QWidget()
        self.alerts_layout = QVBoxLayout(self.alerts_list)
        self.alerts_layout.setContentsMargins(0, 0, 0, 0)
        self.alerts_layout.setSpacing(5)

        alerts_scroll = QScrollArea()
        alerts_scroll.setWidget(self.alerts_list)
        alerts_scroll.setWidgetResizable(True)
        layout.addWidget(alerts_scroll)

        return page

    def _setup_connections(self):
        """设置信号连接"""
        # 连接AI服务管理器信号
        if self.ai_service_manager:
            self.ai_service_manager.service_health_updated.connect(self._on_service_health_updated)
            self.ai_service_manager.stats_updated.connect(self._on_stats_updated)

    def _update_monitor_data(self):
        """更新监控数据"""
        try:
            if not self.ai_service_manager:
                return

            # 更新服务状态
            self._update_services_status()

            # 更新统计数据
            self._update_stats()

            # 更新性能数据
            self._update_performance_data()

            # 更新告警
            self._update_alerts()

        except Exception as e:
            self.logger.error(f"更新监控数据失败: {e}")

    def _update_services_status(self):
        """更新服务状态"""
        try:
            if not self.ai_service_manager:
                return

            # 更新概览页面的服务状态
            self._update_services_status_list()

            # 更新服务页面的表格
            self._update_services_table()

        except Exception as e:
            self.logger.error(f"更新服务状态失败: {e}")

    def _update_services_status_list(self):
        """更新服务状态列表"""
        try:
            # 清除现有部件
            while self.services_status_layout.count():
                item = self.services_status_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # 添加新的服务状态部件
            if self.ai_service_manager:
                for service_name, health in self.ai_service_manager.service_health.items():
                    status_widget = ServiceStatusWidget(service_name, health.status, health.__dict__)
                    self.services_status_layout.addWidget(status_widget)

        except Exception as e:
            self.logger.error(f"更新服务状态列表失败: {e}")

    def _update_services_table(self):
        """更新服务表格"""
        try:
            if not self.ai_service_manager:
                return

            services = self.ai_service_manager.get_all_services()
            self.services_table.setRowCount(len(services))

            for row, (service_name, service) in enumerate(services.items()):
                health = self.ai_service_manager.get_service_health(service_name)
                stats = self.ai_service_manager.get_usage_stats(service_name)

                # 服务名称
                self.services_table.setItem(row, 0, QTableWidgetItem(service_name))

                # 状态
                status_item = QTableWidgetItem(health.status.value if health else "未知")
                status_color = {
                    ServiceStatus.ACTIVE: "#52c41a",
                    ServiceStatus.INACTIVE: "#888888",
                    ServiceStatus.ERROR: "#ff4d4f",
                    ServiceStatus.MAINTENANCE: "#faad14"
                }.get(health.status, "#888888")
                status_item.setBackground(QColor(status_color))
                self.services_table.setItem(row, 1, status_item)

                # 响应时间
                response_time = health.response_time if health else 0
                self.services_table.setItem(row, 2, QTableWidgetItem(f"{response_time:.1f}ms"))

                # 错误率
                error_rate = health.error_rate if health else 0
                self.services_table.setItem(row, 3, QTableWidgetItem(f"{error_rate:.1%}"))

                # 成功率
                success_rate = (stats.successful_requests / stats.total_requests * 100) if stats and stats.total_requests > 0 else 100
                self.services_table.setItem(row, 4, QTableWidgetItem(f"{success_rate:.1f}%"))

                # 操作按钮
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)

                test_btn = QPushButton("测试")
                test_btn.setFixedSize(60, 24)
                test_btn.clicked.connect(lambda checked, sn=service_name: self._test_service(sn))
                actions_layout.addWidget(test_btn)

                details_btn = QPushButton("详情")
                details_btn.setFixedSize(60, 24)
                details_btn.clicked.connect(lambda checked, sn=service_name: self._show_service_details(sn))
                actions_layout.addWidget(details_btn)

                self.services_table.setCellWidget(row, 5, actions_widget)

        except Exception as e:
            self.logger.error(f"更新服务表格失败: {e}")

    def _update_stats(self):
        """更新统计数据"""
        try:
            if not self.ai_service_manager:
                return

            summary = self.ai_service_manager.get_summary()

            # 更新概览页面统计
            if hasattr(self, 'service_stats_label'):
                self.service_stats_label.setText(f"{summary['active_services']}/{summary['total_services']}")
                self.requests_stats_label.setText(str(summary['total_requests']))

                # 计算成功率
                total_requests = summary.get('total_requests', 0)
                successful_requests = summary.get('successful_requests', 0)
                success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 100
                self.success_stats_label.setText(f"{success_rate:.1f}%")

                # 计算平均响应时间
                avg_response_time = self._calculate_avg_response_time()
                self.response_stats_label.setText(f"{avg_response_time:.1f}ms")

                self.cost_stats_label.setText(f"¥{summary['total_cost']:.2f}")
                self.alerts_stats_label.setText(str(len([a for a in self.alerts if not a.resolved])))

            # 更新使用量表格
            self._update_usage_table()

        except Exception as e:
            self.logger.error(f"更新统计数据失败: {e}")

    def _calculate_avg_response_time(self) -> float:
        """计算平均响应时间"""
        try:
            if not self.ai_service_manager:
                return 0.0

            total_time = 0
            count = 0

            for health in self.ai_service_manager.service_health.values():
                if health.response_time > 0:
                    total_time += health.response_time
                    count += 1

            return total_time / count if count > 0 else 0.0

        except Exception as e:
            self.logger.error(f"计算平均响应时间失败: {e}")
            return 0.0

    def _update_usage_table(self):
        """更新使用量表格"""
        try:
            if not self.ai_service_manager:
                return

            stats = self.ai_service_manager.usage_stats
            self.usage_table.setRowCount(len(stats))

            for row, (service_name, stat) in enumerate(stats.items()):
                self.usage_table.setItem(row, 0, QTableWidgetItem(service_name))
                self.usage_table.setItem(row, 1, QTableWidgetItem(str(stat.total_requests)))
                self.usage_table.setItem(row, 2, QTableWidgetItem(str(stat.successful_requests)))
                self.usage_table.setItem(row, 3, QTableWidgetItem(str(stat.failed_requests)))
                self.usage_table.setItem(row, 4, QTableWidgetItem(f"¥{stat.total_cost:.2f}"))

        except Exception as e:
            self.logger.error(f"更新使用量表格失败: {e}")

    def _update_performance_data(self):
        """更新性能数据"""
        try:
            if not self.ai_service_manager:
                return

            # 生成模拟性能数据
            response_time = self._calculate_avg_response_time()
            error_rate = self._calculate_error_rate()
            throughput = self._calculate_throughput()

            # 更新图表
            self.response_time_chart.add_data_point(response_time)
            self.error_rate_chart.add_data_point(error_rate * 100)
            self.throughput_chart.add_data_point(throughput)

            self.response_trend_chart.add_data_point(response_time)
            self.error_trend_chart.add_data_point(error_rate * 100)
            self.throughput_trend_chart.add_data_point(throughput)

            # 模拟CPU使用率
            import random
            cpu_usage = random.uniform(10, 80)
            self.cpu_usage_chart.add_data_point(cpu_usage)

        except Exception as e:
            self.logger.error(f"更新性能数据失败: {e}")

    def _calculate_error_rate(self) -> float:
        """计算错误率"""
        try:
            if not self.ai_service_manager:
                return 0.0

            total_errors = 0
            total_requests = 0

            for health in self.ai_service_manager.service_health.values():
                total_errors += health.error_count
                total_requests += health.success_count + health.error_count

            return total_errors / total_requests if total_requests > 0 else 0.0

        except Exception as e:
            self.logger.error(f"计算错误率失败: {e}")
            return 0.0

    def _calculate_throughput(self) -> float:
        """计算吞吐量"""
        try:
            if not self.ai_service_manager:
                return 0.0

            # 简单计算每秒请求数
            total_requests = sum(stat.total_requests for stat in self.ai_service_manager.usage_stats.values())
            return total_requests / 3600  # 假设统计的是1小时的数据

        except Exception as e:
            self.logger.error(f"计算吞吐量失败: {e}")
            return 0.0

    def _update_alerts(self):
        """更新告警"""
        try:
            if not self.ai_service_manager:
                return

            # 生成告警
            self._generate_alerts()

            # 更新告警列表
            self._update_alerts_list()

        except Exception as e:
            self.logger.error(f"更新告警失败: {e}")

    def _generate_alerts(self):
        """生成告警"""
        try:
            if not self.ai_service_manager:
                return

            current_time = time.time()

            # 检查服务健康状态
            for service_name, health in self.ai_service_manager.service_health.items():
                if health.status == ServiceStatus.ERROR:
                    alert = AlertData(
                        id=f"{service_name}_error_{int(current_time)}",
                        service_name=service_name,
                        level="error",
                        message="服务出现错误，请检查配置",
                        timestamp=current_time,
                        details={"error_rate": health.error_rate, "last_check": health.last_check}
                    )
                    self._add_alert(alert)

                elif health.error_rate > 0.1:
                    alert = AlertData(
                        id=f"{service_name}_high_error_rate_{int(current_time)}",
                        service_name=service_name,
                        level="warning",
                        message=f"错误率过高: {health.error_rate:.1%}",
                        timestamp=current_time,
                        details={"error_rate": health.error_rate}
                    )
                    self._add_alert(alert)

                elif health.response_time > 5000:  # 5秒
                    alert = AlertData(
                        id=f"{service_name}_slow_response_{int(current_time)}",
                        service_name=service_name,
                        level="warning",
                        message=f"响应时间过长: {health.response_time:.1f}ms",
                        timestamp=current_time,
                        details={"response_time": health.response_time}
                    )
                    self._add_alert(alert)

        except Exception as e:
            self.logger.error(f"生成告警失败: {e}")

    def _add_alert(self, alert: AlertData):
        """添加告警"""
        # 检查是否已存在相似的告警
        for existing_alert in self.alerts:
            if (existing_alert.service_name == alert.service_name and
                existing_alert.level == alert.level and
                existing_alert.message == alert.message and
                not existing_alert.resolved and
                current_time - existing_alert.timestamp < 300):  # 5分钟内
                return

        self.alerts.append(alert)

        # 保持告警数量在合理范围内
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

    def _update_alerts_list(self):
        """更新告警列表"""
        try:
            # 清除现有部件
            while self.alerts_layout.count():
                item = self.alerts_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # 获取过滤器
            filter_text = self.alert_filter_combo.currentText()
            if filter_text == "全部":
                filtered_alerts = self.alerts
            else:
                level_map = {
                    "信息": "info",
                    "警告": "warning",
                    "错误": "error",
                    "严重": "critical"
                }
                filter_level = level_map.get(filter_text)
                filtered_alerts = [a for a in self.alerts if a.level == filter_level]

            # 按时间排序
            filtered_alerts.sort(key=lambda x: x.timestamp, reverse=True)

            # 添加告警部件
            for alert in filtered_alerts[:20]:  # 只显示最近20个
                alert_widget = AlertWidget(alert)
                alert_widget.alert_clicked.connect(self.alert_selected)
                self.alerts_layout.addWidget(alert_widget)

            if not filtered_alerts:
                no_alerts_label = QLabel("暂无告警")
                no_alerts_label.setProperty("class", "no-alerts-label")
                no_alerts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.alerts_layout.addWidget(no_alerts_label)

        except Exception as e:
            self.logger.error(f"更新告警列表失败: {e}")

    def _filter_alerts(self, filter_text: str):
        """过滤告警"""
        self._update_alerts_list()

    def _clear_resolved_alerts(self):
        """清除已解决的告警"""
        self.alerts = [a for a in self.alerts if not a.resolved]
        self._update_alerts_list()

    def _test_service(self, service_name: str):
        """测试服务"""
        try:
            if self.ai_service_manager:
                # 测试第一个配置的模型
                configured_models = self.ai_service_manager.get_configured_models()
                if service_name in configured_models and configured_models[service_name]:
                    model_id = configured_models[service_name][0]
                    success = self.ai_service_manager.test_connection(service_name, model_id)

                    if success:
                        QMessageBox.information(self, "测试成功", f"{service_name} 连接测试成功")
                    else:
                        QMessageBox.warning(self, "测试失败", f"{service_name} 连接测试失败")
                else:
                    QMessageBox.warning(self, "未配置", f"{service_name} 未配置模型")
        except Exception as e:
            QMessageBox.critical(self, "测试错误", f"测试服务失败: {e}")

    def _show_service_details(self, service_name: str):
        """显示服务详情"""
        try:
            if not self.ai_service_manager:
                return

            health = self.ai_service_manager.get_service_health(service_name)
            stats = self.ai_service_manager.get_usage_stats(service_name)

            details = f"""
服务名称: {service_name}
状态: {health.status.value if health else '未知'}
响应时间: {health.response_time:.1f}ms if health else 'N/A'
错误率: {health.error_rate:.1% if health else 'N/A'}
成功率: {stats.successful_requests}/{stats.total_requests if stats else 'N/A'}
总成本: ¥{stats.total_cost:.2f if stats else 'N/A'}
最后检查: {datetime.fromtimestamp(health.last_check).strftime('%Y-%m-%d %H:%M:%S') if health else 'N/A'}
            """

            QMessageBox.information(self, "服务详情", details)

        except Exception as e:
            QMessageBox.critical(self, "详情错误", f"获取服务详情失败: {e}")

    def _refresh_data(self):
        """刷新数据"""
        self._update_monitor_data()

    def _on_service_health_updated(self, service_name: str, health_data: object):
        """服务健康状态更新处理"""
        self._update_services_status()

    def _on_stats_updated(self, stats: object):
        """统计数据更新处理"""
        self._update_stats()

    def refresh(self):
        """刷新面板"""
        self._update_monitor_data()

    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()

    def __del__(self):
        """析构函数"""
        self.cleanup()