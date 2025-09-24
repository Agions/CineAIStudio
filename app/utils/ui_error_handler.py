#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 UI错误处理模块
专门处理UI相关的错误，提供用户友好的错误显示和恢复建议
"""

import traceback
from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps

from PyQt6.QtWidgets import (
    QMessageBox, QWidget, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QTextEdit, QFrame,
    QApplication, QScrollArea, QSplitter
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QObject, QThread, QPropertyAnimation,
    QEasingCurve, QRect, QPoint
)
from PyQt6.QtGui import (
    QFont, QPixmap, QPainter, QColor, QPen, QBrush,
    QPainterPath, QIcon
)

from .error_handler import (
    ErrorHandler, ErrorInfo, ErrorType, ErrorSeverity,
    RecoveryAction, ErrorContext, get_global_error_handler
)


class UIErrorType(Enum):
    """UI错误类型"""
    WIDGET_CREATION = "widget_creation"
    LAYOUT_ERROR = "layout_error"
    SIGNAL_CONNECTION = "signal_connection"
    EVENT_HANDLING = "event_handling"
    STYLING_ERROR = "styling_error"
    ANIMATION_ERROR = "animation_error"
    DIALOG_ERROR = "dialog_error"
    INPUT_VALIDATION = "input_validation"
    RESOURCE_LOADING = "resource_loading"


class UIErrorSeverity(Enum):
    """UI错误严重程度"""
    MINOR = "minor"  # 不影响主要功能
    MODERATE = "moderate"  # 影响部分功能
    MAJOR = "major"  # 影响主要功能
    CRITICAL = "critical"  # UI崩溃


@dataclass
class UIErrorContext:
    """UI错误上下文"""
    widget_type: str
    widget_name: str
    parent_widget: Optional[str] = None
    layout_type: Optional[str] = None
    event_type: Optional[str] = None
    user_action: str = ""
    ui_state: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UIErrorInfo(ErrorInfo):
    """UI错误信息"""
    ui_error_type: UIErrorType = None
    ui_severity: UIErrorSeverity = None
    ui_context: Optional[UIErrorContext] = None
    widget: Optional[QWidget] = None
    recovery_widget: Optional[QWidget] = None


class ErrorDialog(QDialog):
    """增强的错误对话框"""

    error_reported = pyqtSignal(UIErrorInfo)

    def __init__(self, error_info: UIErrorInfo, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.error_info = error_info
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("错误详情")
        self.setModal(True)
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 错误图标和标题
        header_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(self._get_error_icon().pixmap(48, 48))
        header_layout.addWidget(icon_label)

        title_layout = QVBoxLayout()
        title_label = QLabel(self._get_error_title())
        title_font = QFont("Arial", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {self._get_error_color()};")
        title_layout.addWidget(title_label)

        description_label = QLabel(self.error_info.user_message)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #666666; font-size: 12px;")
        title_layout.addWidget(description_label)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # 创建选项卡
        tab_widget = QSplitter(Qt.Orientation.Vertical)

        # 错误详情
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)

        details_label = QLabel("错误详情")
        details_font = QFont("Arial", 12, QFont.Weight.Bold)
        details_label.setFont(details_font)
        details_layout.addWidget(details_label)

        details_text = QTextEdit()
        details_text.setReadOnly(True)
        details_text.setMaximumHeight(150)
        details_text.setText(self._format_error_details())
        details_layout.addWidget(details_text)

        tab_widget.addWidget(details_widget)

        # 技术详情
        if self.error_info.stack_trace:
            tech_widget = QWidget()
            tech_layout = QVBoxLayout(tech_widget)
            tech_layout.setContentsMargins(0, 0, 0, 0)

            tech_label = QLabel("技术信息")
            tech_label.setFont(details_font)
            tech_layout.addWidget(tech_label)

            tech_text = QTextEdit()
            tech_text.setReadOnly(True)
            tech_text.setMaximumHeight(150)
            tech_text.setPlainText(self.error_info.stack_trace)
            tech_layout.addWidget(tech_text)

            tab_widget.addWidget(tech_widget)

        # 恢复建议
        if self.error_info.recovery_action != RecoveryAction.NONE:
            recovery_widget = QWidget()
            recovery_layout = QVBoxLayout(recovery_widget)
            recovery_layout.setContentsMargins(0, 0, 0, 0)

            recovery_label = QLabel("恢复建议")
            recovery_label.setFont(details_font)
            recovery_layout.addWidget(recovery_label)

            recovery_text = QLabel(self._get_recovery_suggestion())
            recovery_text.setWordWrap(True)
            recovery_text.setStyleSheet("color: #2196F3; font-size: 11px;")
            recovery_layout.addWidget(recovery_text)

            tab_widget.addWidget(recovery_widget)

        layout.addWidget(tab_widget)

        # 按钮区域
        button_layout = QHBoxLayout()

        # 报告错误按钮
        if self.error_info.ui_severity in [UIErrorSeverity.MAJOR, UIErrorSeverity.CRITICAL]:
            report_btn = QPushButton("报告错误")
            report_btn.clicked.connect(self._report_error)
            button_layout.addWidget(report_btn)

        button_layout.addStretch()

        # 重试按钮
        if self.error_info.recovery_action == RecoveryAction.RETRY:
            retry_btn = QPushButton("重试")
            retry_btn.clicked.connect(self._retry_action)
            button_layout.addWidget(retry_btn)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 8px;
            }
            QLabel {
                color: #333333;
            }
            QTextEdit {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                background-color: #f8f8f8;
                font-family: monospace;
                font-size: 10px;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)

    def _get_error_icon(self) -> QIcon:
        """获取错误图标"""
        # 这里应该从资源管理器获取图标
        # 临时使用文字图标
        return QIcon()

    def _get_error_title(self) -> str:
        """获取错误标题"""
        titles = {
            UIErrorSeverity.MINOR: "小提示",
            UIErrorSeverity.MODERATE: "警告",
            UIErrorSeverity.MAJOR: "错误",
            UIErrorSeverity.CRITICAL: "严重错误"
        }
        return titles.get(self.error_info.ui_severity, "错误")

    def _get_error_color(self) -> str:
        """获取错误颜色"""
        colors = {
            UIErrorSeverity.MINOR: "#4CAF50",  # 绿色
            UIErrorSeverity.MODERATE: "#FF9800",  # 橙色
            UIErrorSeverity.MAJOR: "#F44336",  # 红色
            UIErrorSeverity.CRITICAL: "#D32F2F"  # 深红色
        }
        return colors.get(self.error_info.ui_severity, "#F44336")

    def _format_error_details(self) -> str:
        """格式化错误详情"""
        details = []
        details.append(f"错误类型: {self.error_info.ui_error_type.value}")
        details.append(f"严重程度: {self.error_info.ui_severity.value}")

        if self.error_info.ui_context:
            ctx = self.error_info.ui_context
            details.append(f"组件: {ctx.widget_type}")
            if ctx.widget_name:
                details.append(f"组件名称: {ctx.widget_name}")
            if ctx.parent_widget:
                details.append(f"父组件: {ctx.parent_widget}")
            if ctx.event_type:
                details.append(f"事件类型: {ctx.event_type}")

        details.append(f"错误信息: {self.error_info.message}")

        return "\n".join(details)

    def _get_recovery_suggestion(self) -> str:
        """获取恢复建议"""
        suggestions = {
            RecoveryAction.RETRY: "请检查网络连接后重试操作",
            RecoveryAction.SKIP: "您可以跳过此步骤继续其他操作",
            RecoveryAction.ROLLBACK: "系统将尝试回滚到之前的状态",
            RecoveryAction.RESET: "请重置相关设置后重试",
            RecoveryAction.CONTACT_SUPPORT: "请联系技术支持获取帮助"
        }
        return suggestions.get(self.error_info.recovery_action, "请稍后重试")

    def _report_error(self):
        """报告错误"""
        self.error_reported.emit(self.error_info)
        QMessageBox.information(self, "错误报告", "错误报告已发送，感谢您的反馈！")

    def _retry_action(self):
        """重试操作"""
        self.accept()
        # 这里可以触发重试信号或调用重试函数


class UIErrorHandler(ErrorHandler):
    """UI错误处理器"""

    # 信号定义
    ui_error_occurred = pyqtSignal(UIErrorInfo)  # UI错误发生信号
    error_dialog_requested = pyqtSignal(UIErrorInfo)  # 错误对话框请求信号
    widget_recovery_needed = pyqtSignal(UIErrorInfo, QWidget)  # 组件恢复需求信号

    def __init__(self, logger=None):
        """初始化UI错误处理器"""
        super().__init__(logger)
        self.error_widgets: Dict[str, QWidget] = {}
        self.recovery_strategies: Dict[str, Callable] = {}
        self.suppressed_errors: List[str] = []

    def handle_ui_error(
        self,
        ui_error_info: UIErrorInfo,
        show_dialog: bool = True,
        parent: Optional[QWidget] = None
    ) -> None:
        """处理UI错误"""
        # 转换为通用错误信息
        error_info = ErrorInfo(
            error_type=ErrorType.UI,
            severity=self._convert_severity(ui_error_info.ui_severity),
            message=ui_error_info.message,
            exception=ui_error_info.exception,
            context=ui_error_info.context,
            recovery_action=ui_error_info.recovery_action,
            user_message=ui_error_info.user_message,
            technical_details=ui_error_info.technical_details
        )

        # 处理通用错误
        super().handle_error(error_info, show_dialog=False)

        # 发送UI特定信号
        self.ui_error_occurred.emit(ui_error_info)

        # 记录UI特定日志
        self._log_ui_error(ui_error_info)

        # 显示UI错误对话框
        if show_dialog:
            self._show_ui_error_dialog(ui_error_info, parent)

        # 尝试UI恢复
        self._attempt_ui_recovery(ui_error_info)

    def _log_ui_error(self, ui_error_info: UIErrorInfo) -> None:
        """记录UI错误"""
        log_message = f"[UI_ERROR] {ui_error_info.ui_error_type.value}: {ui_error_info.message}"

        if ui_error_info.ui_context:
            ctx = ui_error_info.ui_context
            log_message += f" (Widget: {ctx.widget_type}"
            if ctx.widget_name:
                log_message += f", Name: {ctx.widget_name}"
            if ctx.parent_widget:
                log_message += f", Parent: {ctx.parent_widget}"
            log_message += ")"

        if ui_error_info.exception:
            log_message += f" Exception: {str(ui_error_info.exception)}"

        # 根据严重程度选择日志级别
        if ui_error_info.ui_severity == UIErrorSeverity.CRITICAL:
            self.logger.critical(log_message, exc_info=ui_error_info.exception)
        elif ui_error_info.ui_severity == UIErrorSeverity.MAJOR:
            self.logger.error(log_message, exc_info=ui_error_info.exception)
        elif ui_error_info.ui_severity == UIErrorSeverity.MODERATE:
            self.logger.warning(log_message, exc_info=ui_error_info.exception)
        else:
            self.logger.info(log_message)

    def _show_ui_error_dialog(self, ui_error_info: UIErrorInfo, parent: Optional[QWidget] = None) -> None:
        """显示UI错误对话框"""
        try:
            dialog = ErrorDialog(ui_error_info, parent)
            dialog.error_reported.connect(self._on_error_reported)
            dialog.exec()
        except Exception as e:
            # 如果对话框创建失败，回退到简单消息框
            self.logger.error(f"创建错误对话框失败: {e}")
            if parent and QApplication.instance():
                QMessageBox.critical(
                    parent,
                    "错误",
                    ui_error_info.user_message or ui_error_info.message
                )

    def _attempt_ui_recovery(self, ui_error_info: UIErrorInfo) -> None:
        """尝试UI恢复"""
        if ui_error_info.recovery_action == RecoveryAction.NONE:
            return

        try:
            # 根据错误类型执行恢复策略
            recovery_key = f"{ui_error_info.ui_error_type.value}_{ui_error_info.recovery_action.value}"
            if recovery_key in self.recovery_strategies:
                recovery_func = self.recovery_strategies[recovery_key]
                recovery_func(ui_error_info)

            # 发送恢复需求信号
            if ui_error_info.widget:
                self.widget_recovery_needed.emit(ui_error_info, ui_error_info.widget)

            self.logger.info(f"UI恢复成功: {recovery_key}")

        except Exception as recovery_error:
            self.logger.error(f"UI恢复失败: {recovery_error}")

    def _on_error_reported(self, ui_error_info: UIErrorInfo) -> None:
        """处理错误报告"""
        # 这里可以发送错误报告到服务器
        self.logger.info(f"用户报告了UI错误: {ui_error_info.ui_error_type.value}")

    def _convert_severity(self, ui_severity: UIErrorSeverity) -> ErrorSeverity:
        """转换UI严重程度为通用严重程度"""
        mapping = {
            UIErrorSeverity.MINOR: ErrorSeverity.LOW,
            UIErrorSeverity.MODERATE: ErrorSeverity.MEDIUM,
            UIErrorSeverity.MAJOR: ErrorSeverity.HIGH,
            UIErrorSeverity.CRITICAL: ErrorSeverity.CRITICAL
        }
        return mapping.get(ui_severity, ErrorSeverity.MEDIUM)

    def register_recovery_strategy(
        self,
        error_type: UIErrorType,
        recovery_action: RecoveryAction,
        strategy: Callable[[UIErrorInfo], None]
    ) -> None:
        """注册恢复策略"""
        key = f"{error_type.value}_{recovery_action.value}"
        self.recovery_strategies[key] = strategy

    def suppress_error(self, error_type: UIErrorType, message_pattern: str) -> None:
        """抑制特定错误"""
        suppression_key = f"{error_type.value}_{message_pattern}"
        if suppression_key not in self.suppressed_errors:
            self.suppressed_errors.append(suppression_key)

    def is_error_suppressed(self, ui_error_info: UIErrorInfo) -> bool:
        """检查错误是否被抑制"""
        suppression_key = f"{ui_error_info.ui_error_type.value}_{ui_error_info.message}"
        return suppression_key in self.suppressed_errors

    def create_error_widget(
        self,
        ui_error_info: UIErrorInfo,
        parent: Optional[QWidget] = None
    ) -> QWidget:
        """创建错误显示组件"""
        error_widget = QFrame()
        error_widget.setObjectName("errorWidget")
        error_widget.setFrameStyle(QFrame.Shape.Box)

        # 根据严重程度设置样式
        color = self._get_severity_color(ui_error_info.ui_severity)
        error_widget.setStyleSheet(f"""
            QFrame#errorWidget {{
                background-color: #fff3e0;
                border: 1px solid {color};
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }}
        """)

        layout = QVBoxLayout(error_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # 错误图标和消息
        header_layout = QHBoxLayout()
        icon_label = QLabel("⚠️")
        header_layout.addWidget(icon_label)

        message_label = QLabel(ui_error_info.user_message or ui_error_info.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        header_layout.addWidget(message_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # 恢复按钮
        if ui_error_info.recovery_action != RecoveryAction.NONE:
            button_layout = QHBoxLayout()
            button_layout.addStretch()

            if ui_error_info.recovery_action == RecoveryAction.RETRY:
                retry_btn = QPushButton("重试")
                retry_btn.clicked.connect(lambda: self._retry_error_action(ui_error_info))
                button_layout.addWidget(retry_btn)

            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(lambda: error_widget.setParent(None))
            button_layout.addWidget(close_btn)

            layout.addLayout(button_layout)

        return error_widget

    def _get_severity_color(self, severity: UIErrorSeverity) -> str:
        """获取严重程度颜色"""
        colors = {
            UIErrorSeverity.MINOR: "#4CAF50",
            UIErrorSeverity.MODERATE: "#FF9800",
            UIErrorSeverity.MAJOR: "#F44336",
            UIErrorSeverity.CRITICAL: "#D32F2F"
        }
        return colors.get(severity, "#F44336")

    def _retry_error_action(self, ui_error_info: UIErrorInfo) -> None:
        """重试错误操作"""
        # 这里可以触发重试逻辑
        self.logger.info(f"重试UI操作: {ui_error_info.ui_error_type.value}")


def ui_error_handler_decorator(
    ui_error_type: UIErrorType,
    ui_severity: UIErrorSeverity = UIErrorSeverity.MODERATE,
    recovery_action: RecoveryAction = RecoveryAction.NONE,
    user_message: str = "UI操作失败"
):
    """UI错误处理装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 获取UI错误处理器
                ui_handler = getattr(wrapper, 'ui_error_handler', None)
                if not ui_handler:
                    ui_handler = get_global_error_handler()

                # 创建UI错误信息
                ui_error_info = UIErrorInfo(
                    error_type=ErrorType.UI,
                    severity=ErrorSeverity.MEDIUM,
                    message=f"{func.__name__} failed: {str(e)}",
                    exception=e,
                    ui_error_type=ui_error_type,
                    ui_severity=ui_severity,
                    recovery_action=recovery_action,
                    user_message=user_message,
                    ui_context=UIErrorContext(
                        widget_type=func.__class__.__name__ if hasattr(func, '__class__') else "Function",
                        widget_name=func.__name__,
                        user_action="decorated_function_call"
                    )
                )

                # 处理UI错误
                if isinstance(ui_handler, UIErrorHandler):
                    ui_handler.handle_ui_error(ui_error_info)
                else:
                    ui_handler.handle_error(ui_error_info)

                # 根据严重程度决定是否重新抛出异常
                if ui_severity in [UIErrorSeverity.MAJOR, UIErrorSeverity.CRITICAL]:
                    raise

        return wrapper
    return decorator


# 全局UI错误处理器实例
_global_ui_error_handler: Optional[UIErrorHandler] = None


def get_ui_error_handler() -> UIErrorHandler:
    """获取全局UI错误处理器"""
    global _global_ui_error_handler
    if _global_ui_error_handler is None:
        _global_ui_error_handler = UIErrorHandler()
    return _global_ui_error_handler


def set_ui_error_handler(handler: UIErrorHandler) -> None:
    """设置全局UI错误处理器"""
    global _global_ui_error_handler
    _global_ui_error_handler = handler

    # 为装饰器设置错误处理器
    ui_error_handler_decorator.ui_error_handler = handler