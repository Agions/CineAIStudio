#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI服务错误处理演示
展示如何使用增强的错误处理系统
"""

import time
from typing import Dict, Any, Optional, Callable
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit, QLabel
from PyQt6.QtCore import QTimer

from .mock_ai_service import MockAIService, MockAIServiceConfig
from .enhanced_base_ai_service import ServiceConfig
from .enhanced_ai_error_handler import AIErrorHandler, AIErrorType
from ..core.logger import Logger
from ..utils.error_handler import get_global_error_handler


class ErrorHandlingDemo(QMainWindow):
    """错误处理演示窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI服务错误处理演示")
        self.setGeometry(100, 100, 800, 600)

        # 初始化日志
        self.logger = Logger("ErrorHandlingDemo")

        # 初始化错误处理器
        self.ai_error_handler = AIErrorHandler(self.logger)
        self.global_error_handler = get_global_error_handler()

        # 创建AI服务配置
        self.ai_config = MockAIServiceConfig(
            max_retries=3,
            base_retry_delay=1.0,
            max_retry_delay=10.0,
            timeout_threshold=30.0,
            enable_fallback=True,
            simulate_failures=True,
            failure_rate=0.3  # 30%失败率
        )

        # 创建AI服务
        self.ai_service = MockAIService(self.ai_config)

        # 连接信号
        self._connect_signals()

        # 初始化UI
        self._init_ui()

        # 定时更新状态
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)

    def _init_ui(self):
        """初始化用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # 标题
        title_label = QLabel("AI服务错误处理演示")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)

        # 控制按钮
        button_layout = QVBoxLayout()

        self.test_normal_btn = QPushButton("测试正常处理")
        self.test_normal_btn.clicked.connect(self.test_normal_processing)
        button_layout.addWidget(self.test_normal_btn)

        self.test_retry_btn = QPushButton("测试重试机制")
        self.test_retry_btn.clicked.connect(self.test_retry_mechanism)
        button_layout.addWidget(self.test_retry_btn)

        self.test_circuit_breaker_btn = QPushButton("测试熔断器")
        self.test_circuit_breaker_btn.clicked.connect(self.test_circuit_breaker)
        button_layout.addWidget(self.test_circuit_breaker_btn)

        self.test_fallback_btn = QPushButton("测试降级服务")
        self.test_fallback_btn.clicked.connect(self.test_fallback_service)
        button_layout.addWidget(self.test_fallback_btn)

        self.test_auth_error_btn = QPushButton("测试认证错误")
        self.test_auth_error_btn.clicked.connect(self.test_authentication_error)
        button_layout.addWidget(self.test_auth_error_btn)

        self.test_quota_error_btn = QPushButton("测试配额错误")
        self.test_quota_error_btn.clicked.connect(self.test_quota_error)
        button_layout.addWidget(self.test_quota_error_btn)

        self.test_network_error_btn = QPushButton("测试网络错误")
        self.test_network_error_btn.clicked.connect(self.test_network_error)
        button_layout.addWidget(self.test_network_error_btn)

        self.clear_log_btn = QPushButton("清空日志")
        self.clear_log_btn.clicked.connect(self.clear_log)
        button_layout.addWidget(self.clear_log_btn)

        layout.addLayout(button_layout)

        # 状态显示
        self.status_label = QLabel("状态: 就绪")
        self.status_label.setStyleSheet("font-weight: bold; color: green;")
        layout.addWidget(self.status_label)

        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(400)
        layout.addWidget(self.log_text)

        # 统计信息
        self.stats_label = QLabel("统计信息: 等待数据...")
        layout.addWidget(self.stats_label)

    def _connect_signals(self):
        """连接信号"""
        self.ai_service.processing_started.connect(self.on_processing_started)
        self.ai_service.processing_progress.connect(self.on_processing_progress)
        self.ai_service.processing_completed.connect(self.on_processing_completed)
        self.ai_service.processing_error.connect(self.on_processing_error)
        self.ai_service.retry_attempt.connect(self.on_retry_attempt)
        self.ai_service.fallback_triggered.connect(self.on_fallback_triggered)

        self.ai_error_handler.ai_error_occurred.connect(self.on_ai_error_occurred)
        self.ai_error_handler.recovery_attempt.connect(self.on_recovery_attempt)
        self.ai_error_handler.quota_warning.connect(self.on_quota_warning)
        self.ai_error_handler.model_health_update.connect(self.on_model_health_update)

    def log_message(self, message: str, level: str = "INFO"):
        """记录消息"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}"
        self.log_text.append(formatted_message)
        self.logger.info(message)

    def test_normal_processing(self):
        """测试正常处理"""
        self.log_message("开始测试正常处理...")

        def callback(result):
            if result:
                self.log_message(f"正常处理完成: {result}")
            else:
                self.log_message("正常处理失败", "ERROR")

        self.ai_service.analyze_video("test_video.mp4", callback)

    def test_retry_mechanism(self):
        """测试重试机制"""
        self.log_message("开始测试重试机制...")

        def callback(result):
            if result and not result.get("error"):
                attempts = result.get("attempts", 1)
                self.log_message(f"重试机制成功，重试次数: {attempts}")
            else:
                self.log_message(f"重试机制失败: {result}", "ERROR")

        self.ai_service.analyze_video("retry_test_video.mp4", callback)

    def test_circuit_breaker(self):
        """测试熔断器"""
        self.log_message("开始测试熔断器...")

        # 连续发送多个请求以触发熔断器
        for i in range(6):
            def callback(result, index=i):
                if result and not result.get("error"):
                    self.log_message(f"请求 {index+1} 成功")
                else:
                    self.log_message(f"请求 {index+1} 失败: {result}", "WARNING")

            self.ai_service.analyze_video(f"circuit_test_{i}.mp4", callback)
            time.sleep(0.5)  # 短暂延迟

    def test_fallback_service(self):
        """测试降级服务"""
        self.log_message("开始测试降级服务...")

        def callback(result):
            if result:
                if result.get("fallback"):
                    self.log_message(f"降级服务成功，使用服务: {result.get('service', 'unknown')}")
                else:
                    self.log_message("主要服务成功")
            else:
                self.log_message("所有服务都失败", "ERROR")

        self.ai_service.analyze_video("fallback_test_video.mp4", callback)

    def test_authentication_error(self):
        """测试认证错误"""
        self.log_message("开始测试认证错误...")

        def callback(result):
            if result and result.get("error"):
                self.log_message(f"认证错误测试完成: {result.get('error')}", "WARNING")
            else:
                self.log_message("认证错误测试未按预期工作")

        # 模拟认证错误的特殊请求
        self.ai_service.analyze_video("auth_error_test.mp4", callback)

    def test_quota_error(self):
        """测试配额错误"""
        self.log_message("开始测试配额错误...")

        def callback(result):
            if result and result.get("error"):
                self.log_message(f"配额错误测试完成: {result.get('error')}", "WARNING")
            else:
                self.log_message("配额错误测试未按预期工作")

        self.ai_service.analyze_video("quota_error_test.mp4", callback)

    def test_network_error(self):
        """测试网络错误"""
        self.log_message("开始测试网络错误...")

        def callback(result):
            if result and result.get("error"):
                self.log_message(f"网络错误测试完成: {result.get('error')}", "WARNING")
            else:
                self.log_message("网络错误测试未按预期工作")

        self.ai_service.analyze_video("network_error_test.mp4", callback)

    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.log_message("日志已清空")

    def update_status(self):
        """更新状态"""
        try:
            # 更新AI服务状态
            ai_status = self.ai_service.get_status()
            cb_status = self.ai_service.get_circuit_breaker_status()
            stats = self.ai_service.get_processing_stats()

            status_text = f"AI服务状态: {ai_status.value}"
            if cb_status["state"] == "open":
                status_text += " | 熔断器: 开启"
            elif cb_status["state"] == "half_open":
                status_text += " | 熔断器: 半开"
            else:
                status_text += " | 熔断器: 关闭"

            self.status_label.setText(status_text)

            # 更新统计信息
            stats_text = (
                f"总请求: {stats.get('total_requests', 0)} | "
                f"成功: {stats.get('successful_requests', 0)} | "
                f"失败: {stats.get('failed_requests', 0)} | "
                f"重试: {stats.get('retry_count', 0)} | "
                f"降级: {stats.get('fallback_count', 0)} | "
                f"平均时间: {stats.get('average_processing_time', 0):.2f}s"
            )
            self.stats_label.setText(stats_text)

        except Exception as e:
            self.logger.error(f"更新状态失败: {e}")

    # 信号处理方法
    def on_processing_started(self, task_name: str):
        """处理开始"""
        self.log_message(f"开始处理: {task_name}")

    def on_processing_progress(self, task_name: str, progress: int):
        """处理进度"""
        self.log_message(f"处理进度: {task_name} - {progress}%")

    def on_processing_completed(self, task_name: str, result: str):
        """处理完成"""
        self.log_message(f"处理完成: {task_name}")

    def on_processing_error(self, task_name: str, error: str):
        """处理错误"""
        self.log_message(f"处理错误: {task_name} - {error}", "ERROR")

    def on_retry_attempt(self, task_name: str, attempt: int):
        """重试尝试"""
        self.log_message(f"重试尝试: {task_name} - 第 {attempt} 次", "WARNING")

    def on_fallback_triggered(self, task_name: str, service_name: str):
        """降级服务触发"""
        self.log_message(f"降级服务触发: {task_name} -> {service_name}", "WARNING")

    def on_ai_error_occurred(self, error_info, ai_error_details):
        """AI错误发生"""
        self.log_message(f"AI错误: {ai_error_details.error_type.value} - {ai_error_details.error_message}", "ERROR")

    def on_recovery_attempt(self, service_name: str, model_id: str, attempt: int):
        """恢复尝试"""
        self.log_message(f"恢复尝试: {service_name}.{model_id} - 第 {attempt} 次", "WARNING")

    def on_quota_warning(self, service_name: str, used_quota: float, total_quota: float):
        """配额警告"""
        self.log_message(f"配额警告: {service_name} - 已用 {used_quota}/{total_quota}", "WARNING")

    def on_model_health_update(self, service_name: str, model_id: str, is_healthy: bool):
        """模型健康状态更新"""
        status = "健康" if is_healthy else "不健康"
        self.log_message(f"模型健康状态更新: {service_name}.{model_id} - {status}")


def main():
    """主函数"""
    import sys

    app = QApplication(sys.argv)

    # 设置全局错误处理器
    global_error_handler = get_global_error_handler()

    # 创建演示窗口
    demo = ErrorHandlingDemo()
    demo.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()