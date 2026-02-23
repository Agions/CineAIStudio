"""
错误边界组件

提供统一的错误捕获和显示功能。
"""

import traceback
from typing import Optional, Callable, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from ...core.error_handler import (
    ApplicationError, ErrorCategory, ErrorSeverity,
    get_error_handler
)


class ErrorDisplay(QFrame):
    """
    错误显示组件
    
    显示错误信息和恢复选项。
    """
    
    retry_requested = pyqtSignal()
    dismiss_requested = pyqtSignal()
    details_expanded = pyqtSignal(bool)
    
    def __init__(self, parent: Optional[QWidget] = None):
        """初始化"""
        super().__init__(parent)
        
        self._error: Optional[ApplicationError] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        self.setStyleSheet("""
            ErrorDisplay {
                background-color: #1E1E1E;
                border: 1px solid #F44336;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        
        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(12)
        self._layout.setContentsMargins(16, 16, 16, 16)
        
        # 错误图标和标题
        header_layout = QHBoxLayout()
        
        self._icon_label = QLabel("⚠️")
        self._icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(self._icon_label)
        
        self._title_label = QLabel("出错了")
        self._title_label.setStyleSheet("""
            color: #F44336;
            font-size: 16px;
            font-weight: bold;
        """)
        header_layout.addWidget(self._title_label)
        header_layout.addStretch()
        
        # 错误ID
        self._id_label = QLabel("")
        self._id_label.setStyleSheet("color: #808080; font-size: 11px;")
        header_layout.addWidget(self._id_label)
        
        self._layout.addLayout(header_layout)
        
        # 错误消息
        self._message_label = QLabel("")
        self._message_label.setWordWrap(True)
        self._message_label.setStyleSheet("color: #E0E0E0; font-size: 13px;")
        self._layout.addWidget(self._message_label)
        
        # 恢复建议
        self._suggestion_label = QLabel("")
        self._suggestion_label.setWordWrap(True)
        self._suggestion_label.setStyleSheet("color: #FFC107; font-size: 12px;")
        self._layout.addWidget(self._suggestion_label)
        
        # 详情区域（可折叠）
        self._details_widget = QWidget()
        details_layout = QVBoxLayout(self._details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        
        self._details_text = QTextEdit()
        self._details_text.setReadOnly(True)
        self._details_text.setMaximumHeight(150)
        self._details_text.setStyleSheet("""
            QTextEdit {
                background-color: #121212;
                color: #B0B0B0;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 8px;
                font-family: monospace;
                font-size: 11px;
            }
        """)
        details_layout.addWidget(self._details_text)
        
        self._details_widget.hide()
        self._layout.addWidget(self._details_widget)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self._details_button = QPushButton("显示详情")
        self._details_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #808080;
                border: none;
                padding: 6px 12px;
            }
            QPushButton:hover {
                color: #B0B0B0;
            }
        """)
        self._details_button.clicked.connect(self._toggle_details)
        button_layout.addWidget(self._details_button)
        
        self._retry_button = QPushButton("重试")
        self._retry_button.setStyleSheet("""
            QPushButton {
                background-color: #2962FF;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #448AFF;
            }
        """)
        self._retry_button.clicked.connect(self.retry_requested.emit)
        button_layout.addWidget(self._retry_button)
        
        self._dismiss_button = QPushButton("关闭")
        self._dismiss_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #E0E0E0;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #2C2C2C;
            }
        """)
        self._dismiss_button.clicked.connect(self.dismiss_requested.emit)
        button_layout.addWidget(self._dismiss_button)
        
        self._layout.addLayout(button_layout)
    
    def set_error(self, error: ApplicationError):
        """
        设置错误
        
        Args:
            error: 应用错误
        """
        self._error = error
        
        # 更新UI
        self._id_label.setText(f"ID: {error.error_id}")
        self._message_label.setText(error.message)
        
        # 根据严重程度设置样式
        if error.severity == ErrorSeverity.CRITICAL:
            self._icon_label.setText("🚨")
            self._title_label.setText("严重错误")
        elif error.severity == ErrorSeverity.ERROR:
            self._icon_label.setText("⚠️")
            self._title_label.setText("错误")
        elif error.severity == ErrorSeverity.WARNING:
            self._icon_label.setText("⚡")
            self._title_label.setText("警告")
            self._title_label.setStyleSheet("color: #FFC107; font-size: 16px; font-weight: bold;")
        
        # 恢复建议
        if error.recovery_suggestion:
            self._suggestion_label.setText(f"💡 {error.recovery_suggestion}")
            self._suggestion_label.show()
        else:
            self._suggestion_label.hide()
        
        # 详情
        details = []
        if error.context.file_path:
            details.append(f"文件: {error.context.file_path}")
        if error.context.line_number:
            details.append(f"行号: {error.context.line_number}")
        if error.context.function_name:
            details.append(f"函数: {error.context.function_name}")
        if error.exception:
            details.append(f"\n异常类型: {type(error.exception).__name__}")
            details.append(f"异常信息: {str(error.exception)}")
            details.append(f"\n堆栈跟踪:\n{traceback.format_exception(type(error.exception), error.exception, error.exception.__traceback__)}")
        
        self._details_text.setText("\n".join(details))
    
    def _toggle_details(self):
        """切换详情显示"""
        is_visible = self._details_widget.isVisible()
        self._details_widget.setVisible(not is_visible)
        self._details_button.setText("隐藏详情" if not is_visible else "显示详情")
        self.details_expanded.emit(not is_visible)
    
    def show_retry_button(self, show: bool = True):
        """
        显示/隐藏重试按钮
        
        Args:
            show: 是否显示
        """
        self._retry_button.setVisible(show)
    
    def set_retry_callback(self, callback: Callable):
        """
        设置重试回调
        
        Args:
            callback: 回调函数
        """
        self._retry_button.clicked.disconnect()
        self._retry_button.clicked.connect(callback)


class ErrorBoundaryWidget(QWidget):
    """
    错误边界组件
    
    捕获子组件的错误并显示友好的错误界面。
    """
    
    error_occurred = pyqtSignal(ApplicationError)
    retry_requested = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        """初始化"""
        super().__init__(parent)
        
        self._content_widget: Optional[QWidget] = None
        self._error: Optional[ApplicationError] = None
        self._fallback_widget: Optional[QWidget] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        
        # 错误显示（初始隐藏）
        self._error_display = ErrorDisplay(self)
        self._error_display.hide()
        self._error_display.retry_requested.connect(self._on_retry)
        self._error_display.dismiss_requested.connect(self._on_dismiss)
        self._layout.addWidget(self._error_display)
    
    def set_content(self, widget: QWidget):
        """
        设置内容组件
        
        Args:
            widget: 内容组件
        """
        # 移除旧内容
        if self._content_widget:
            self._content_widget.setParent(None)
        
        self._content_widget = widget
        self._layout.insertWidget(0, widget)
        
        # 安装事件过滤器以捕获错误
        # 注意：Python中无法像React那样捕获子组件异常
        # 这里提供一种手动报告错误的机制
    
    def set_fallback(self, widget: QWidget):
        """
        设置回退组件
        
        Args:
            widget: 回退组件
        """
        self._fallback_widget = widget
    
    def handle_error(self, error: ApplicationError):
        """
        处理错误
        
        Args:
            error: 应用错误
        """
        self._error = error
        
        # 隐藏内容
        if self._content_widget:
            self._content_widget.hide()
        
        # 显示错误
        self._error_display.set_error(error)
        self._error_display.show()
        
        # 发送信号
        self.error_occurred.emit(error)
        
        # 记录错误
        get_error_handler().handle_error(error)
    
    def handle_exception(self, exception: Exception, message: Optional[str] = None):
        """
        处理异常
        
        Args:
            exception: 异常对象
            message: 错误消息
        """
        error = get_error_handler().create_error(
            message=message or str(exception),
            category=ErrorCategory.UI,
            severity=ErrorSeverity.ERROR,
            exception=exception
        )
        self.handle_error(error)
    
    def reset(self):
        """重置错误状态"""
        self._error = None
        self._error_display.hide()
        
        if self._content_widget:
            self._content_widget.show()
    
    def _on_retry(self):
        """重试处理"""
        self.reset()
        self.retry_requested.emit()
    
    def _on_dismiss(self):
        """关闭处理"""
        if self._fallback_widget:
            self._content_widget.hide()
            self._error_display.hide()
            self._fallback_widget.show()
        else:
            self.reset()
    
    def has_error(self) -> bool:
        """
        检查是否有错误
        
        Returns:
            是否有错误
        """
        return self._error is not None


class GlobalErrorHandler:
    """
    全局错误处理器
    
    管理应用程序全局的错误显示。
    """
    
    _instance: Optional['GlobalErrorHandler'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._error_widgets: List[ErrorDisplay] = []
            self._error_handler = get_error_handler()
            self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'GlobalErrorHandler':
        """获取实例"""
        return cls()
    
    def show_error(self, parent: QWidget, error: ApplicationError,
                   on_retry: Optional[Callable] = None,
                   on_dismiss: Optional[Callable] = None):
        """
        显示错误
        
        Args:
            parent: 父组件
            error: 错误
            on_retry: 重试回调
            on_dismiss: 关闭回调
        """
        error_display = ErrorDisplay(parent)
        error_display.set_error(error)
        
        if on_retry:
            error_display.retry_requested.connect(on_retry)
        else:
            error_display.show_retry_button(False)
        
        if on_dismiss:
            error_display.dismiss_requested.connect(on_dismiss)
        
        error_display.show()
        self._error_widgets.append(error_display)
    
    def show_error_message(self, parent: QWidget, message: str,
                          severity: ErrorSeverity = ErrorSeverity.ERROR,
                          suggestion: Optional[str] = None):
        """
        显示错误消息
        
        Args:
            parent: 父组件
            message: 消息
            severity: 严重程度
            suggestion: 恢复建议
        """
        error = self._error_handler.create_error(
            message=message,
            category=ErrorCategory.UI,
            severity=severity,
            recovery_suggestion=suggestion
        )
        self.show_error(parent, error)
