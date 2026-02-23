"""
统一错误处理框架

提供统一的错误处理和报告功能。
"""

import sys
import traceback
import logging
from typing import Optional, Dict, Any, List, Callable, Type
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
from pathlib import Path
import json


class ErrorCategory(Enum):
    """错误分类"""
    SYSTEM = auto()
    NETWORK = auto()
    FILE_IO = auto()
    VIDEO_PROCESSING = auto()
    AI_SERVICE = auto()
    CONFIGURATION = auto()
    VALIDATION = auto()
    UI = auto()
    UNKNOWN = auto()


class ErrorSeverity(Enum):
    """错误严重程度"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """错误上下文"""
    timestamp: datetime = field(default_factory=datetime.now)
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    user_action: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApplicationError:
    """应用错误"""
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    exception: Optional[Exception] = None
    context: ErrorContext = field(default_factory=ErrorContext)
    error_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S%f"))
    recovery_suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'error_id': self.error_id,
            'message': self.message,
            'category': self.category.name,
            'severity': self.severity.value,
            'timestamp': self.context.timestamp.isoformat(),
            'file_path': self.context.file_path,
            'line_number': self.context.line_number,
            'function_name': self.context.function_name,
            'traceback': traceback.format_exception(type(self.exception), self.exception, self.exception.__traceback__) if self.exception else None,
            'recovery_suggestion': self.recovery_suggestion
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class ErrorHandler:
    """
    错误处理器
    
    统一的错误处理中心。
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化错误处理器
        
        Args:
            logger: 日志记录器
        """
        self._logger = logger or logging.getLogger(__name__)
        self._error_history: List[ApplicationError] = []
        self._max_history = 100
        self._handlers: Dict[ErrorCategory, List[Callable]] = {}
        self._global_handlers: List[Callable] = []
        
        # 设置全局异常钩子
        self._original_excepthook = sys.excepthook
        sys.excepthook = self._handle_uncaught_exception
    
    def handle_error(self, error: ApplicationError) -> None:
        """
        处理错误
        
        Args:
            error: 应用错误
        """
        # 记录到历史
        self._error_history.append(error)
        if len(self._error_history) > self._max_history:
            self._error_history.pop(0)
        
        # 记录日志
        self._log_error(error)
        
        # 调用分类处理器
        if error.category in self._handlers:
            for handler in self._handlers[error.category]:
                try:
                    handler(error)
                except Exception as e:
                    self._logger.error(f"错误处理器执行失败: {e}")
        
        # 调用全局处理器
        for handler in self._global_handlers:
            try:
                handler(error)
            except Exception as e:
                self._logger.error(f"全局错误处理器执行失败: {e}")
    
    def create_error(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN,
                    severity: ErrorSeverity = ErrorSeverity.ERROR,
                    exception: Optional[Exception] = None,
                    recovery_suggestion: Optional[str] = None) -> ApplicationError:
        """
        创建错误
        
        Args:
            message: 错误消息
            category: 错误分类
            severity: 严重程度
            exception: 原始异常
            recovery_suggestion: 恢复建议
            
        Returns:
            应用错误
        """
        # 获取调用上下文
        context = self._get_error_context()
        
        return ApplicationError(
            message=message,
            category=category,
            severity=severity,
            exception=exception,
            context=context,
            recovery_suggestion=recovery_suggestion
        )
    
    def handle_exception(self, exception: Exception, category: ErrorCategory = ErrorCategory.UNKNOWN,
                        message: Optional[str] = None, severity: ErrorSeverity = ErrorSeverity.ERROR) -> ApplicationError:
        """
        处理异常
        
        Args:
            exception: 异常对象
            category: 错误分类
            message: 错误消息
            severity: 严重程度
            
        Returns:
            应用错误
        """
        error_message = message or str(exception)
        error = self.create_error(
            message=error_message,
            category=category,
            severity=severity,
            exception=exception
        )
        self.handle_error(error)
        return error
    
    def register_handler(self, category: ErrorCategory, handler: Callable[[ApplicationError], None]) -> None:
        """
        注册分类错误处理器
        
        Args:
            category: 错误分类
            handler: 处理器函数
        """
        if category not in self._handlers:
            self._handlers[category] = []
        self._handlers[category].append(handler)
    
    def register_global_handler(self, handler: Callable[[ApplicationError], None]) -> None:
        """
        注册全局错误处理器
        
        Args:
            handler: 处理器函数
        """
        self._global_handlers.append(handler)
    
    def get_error_history(self, category: Optional[ErrorCategory] = None,
                         severity: Optional[ErrorSeverity] = None) -> List[ApplicationError]:
        """
        获取错误历史
        
        Args:
            category: 错误分类筛选
            severity: 严重程度筛选
            
        Returns:
            错误列表
        """
        errors = self._error_history
        
        if category:
            errors = [e for e in errors if e.category == category]
        
        if severity:
            errors = [e for e in errors if e.severity == severity]
        
        return errors
    
    def clear_history(self) -> None:
        """清空错误历史"""
        self._error_history.clear()
    
    def export_errors(self, file_path: str) -> bool:
        """
        导出错误到文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功
        """
        try:
            errors_data = [e.to_dict() for e in self._error_history]
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(errors_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self._logger.error(f"导出错误失败: {e}")
            return False
    
    def _log_error(self, error: ApplicationError) -> None:
        """记录错误日志"""
        log_message = f"[{error.error_id}] {error.category.name}: {error.message}"
        
        if error.context.file_path:
            log_message += f" (at {error.context.file_path}:{error.context.line_number})"
        
        if error.severity == ErrorSeverity.DEBUG:
            self._logger.debug(log_message, exc_info=error.exception)
        elif error.severity == ErrorSeverity.INFO:
            self._logger.info(log_message, exc_info=error.exception)
        elif error.severity == ErrorSeverity.WARNING:
            self._logger.warning(log_message, exc_info=error.exception)
        elif error.severity == ErrorSeverity.ERROR:
            self._logger.error(log_message, exc_info=error.exception)
        elif error.severity == ErrorSeverity.CRITICAL:
            self._logger.critical(log_message, exc_info=error.exception)
    
    def _get_error_context(self) -> ErrorContext:
        """获取错误上下文"""
        context = ErrorContext()
        
        # 获取调用栈信息
        try:
            tb = traceback.extract_stack()
            # 跳过当前函数和调用者
            if len(tb) >= 3:
                frame = tb[-3]
                context.file_path = frame.filename
                context.line_number = frame.lineno
                context.function_name = frame.name
        except Exception:
            pass
        
        return context
    
    def _handle_uncaught_exception(self, exc_type: Type, exc_value: Exception, exc_traceback) -> None:
        """处理未捕获的异常"""
        error = self.create_error(
            message=f"未捕获的异常: {exc_value}",
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.CRITICAL,
            exception=exc_value
        )
        self.handle_error(error)
        
        # 调用原始异常钩子
        if self._original_excepthook:
            self._original_excepthook(exc_type, exc_value, exc_traceback)


# 便捷函数
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """
    获取错误处理器
    
    Returns:
        错误处理器实例
    """
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def set_error_handler(handler: ErrorHandler) -> None:
    """
    设置错误处理器
    
    Args:
        handler: 错误处理器
    """
    global _error_handler
    _error_handler = handler


def handle_error(message: str, category: ErrorCategory = ErrorCategory.UNKNOWN,
                severity: ErrorSeverity = ErrorSeverity.ERROR,
                exception: Optional[Exception] = None) -> ApplicationError:
    """
    便捷的错误处理函数
    
    Args:
        message: 错误消息
        category: 错误分类
        severity: 严重程度
        exception: 异常对象
        
    Returns:
        应用错误
    """
    handler = get_error_handler()
    error = handler.create_error(message, category, severity, exception)
    handler.handle_error(error)
    return error


def safe_execute(func: Callable, *args, **kwargs) -> tuple[bool, Any]:
    """
    安全执行函数
    
    Args:
        func: 要执行的函数
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        (是否成功, 结果或错误)
    """
    try:
        result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        error = handle_error(
            message=f"执行 {func.__name__} 失败: {str(e)}",
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.ERROR,
            exception=e
        )
        return False, error


class ErrorBoundary:
    """
    错误边界
    
    用于包装可能出错的代码块。
    """
    
    def __init__(self, category: ErrorCategory = ErrorCategory.UNKNOWN,
                 severity: ErrorSeverity = ErrorSeverity.ERROR,
                 fallback_value: Any = None,
                 on_error: Optional[Callable[[ApplicationError], None]] = None):
        """
        初始化错误边界
        
        Args:
            category: 错误分类
            severity: 严重程度
            fallback_value: 出错时的回退值
            on_error: 错误回调
        """
        self.category = category
        self.severity = severity
        self.fallback_value = fallback_value
        self.on_error = on_error
        self.error: Optional[ApplicationError] = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.error = handle_error(
                message=str(exc_val),
                category=self.category,
                severity=self.severity,
                exception=exc_val
            )
            
            if self.on_error:
                self.on_error(self.error)
            
            # 抑制异常
            return True
        return False
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        执行函数
        
        Args:
            func: 函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数结果或回退值
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.error = handle_error(
                message=f"执行 {func.__name__} 失败: {str(e)}",
                category=self.category,
                severity=self.severity,
                exception=e
            )
            
            if self.on_error:
                self.on_error(self.error)
            
            return self.fallback_value
