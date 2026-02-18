"""
进度管理器

实现统一的进度追踪和报告功能。
"""

import uuid
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock

from .interfaces.progress_interface import (
    IProgressTracker, IProgressReporter, 
    ProgressInfo, ProgressStage
)


@dataclass
class TrackerState:
    """追踪器状态"""
    stage: ProgressStage = ProgressStage.PENDING
    progress: float = 0.0
    message: str = ""
    detail: str = ""
    total_items: int = 1
    processed_items: int = 0
    start_time: Optional[float] = None
    stage_start_time: Optional[float] = None
    cancelled: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProgressTracker(IProgressTracker):
    """
    进度追踪器实现
    
    用于追踪单个任务的进度。
    """
    
    def __init__(self, name: str, reporter: 'ProgressReporter'):
        """
        初始化追踪器
        
        Args:
            name: 追踪器名称
            reporter: 报告器实例
        """
        self._name = name
        self._reporter = reporter
        self._state = TrackerState()
        self._lock = Lock()
    
    @property
    def name(self) -> str:
        """获取名称"""
        return self._name
    
    def start_stage(self, stage: ProgressStage, total_items: int = 1, message: str = "") -> None:
        """
        开始新阶段
        
        Args:
            stage: 阶段类型
            total_items: 总项目数
            message: 阶段描述
        """
        with self._lock:
            self._state.stage = stage
            self._state.total_items = max(1, total_items)
            self._state.processed_items = 0
            self._state.progress = 0.0
            self._state.message = message
            self._state.detail = ""
            self._state.stage_start_time = time.time()
            
            if self._state.start_time is None:
                self._state.start_time = time.time()
        
        self._report()
    
    def update_progress(self, progress: float, message: Optional[str] = None,
                       detail: Optional[str] = None) -> None:
        """
        更新进度
        
        Args:
            progress: 进度值 (0.0 - 1.0)
            message: 进度消息
            detail: 详细信息
        """
        with self._lock:
            self._state.progress = max(0.0, min(1.0, progress))
            if message:
                self._state.message = message
            if detail:
                self._state.detail = detail
        
        self._report()
    
    def increment_progress(self, items: int = 1) -> None:
        """
        增加进度
        
        Args:
            items: 完成的项目数
        """
        with self._lock:
            self._state.processed_items += items
            if self._state.total_items > 0:
                self._state.progress = min(1.0, self._state.processed_items / self._state.total_items)
        
        self._report()
    
    def complete_stage(self, message: Optional[str] = None) -> None:
        """
        完成当前阶段
        
        Args:
            message: 完成消息
        """
        with self._lock:
            self._state.stage = ProgressStage.COMPLETED
            self._state.progress = 1.0
            if message:
                self._state.message = message
        
        self._report()
    
    def set_error(self, error_message: str) -> None:
        """
        设置错误状态
        
        Args:
            error_message: 错误信息
        """
        with self._lock:
            self._state.stage = ProgressStage.ERROR
            self._state.detail = error_message
        
        self._report()
    
    def cancel(self) -> None:
        """取消任务"""
        with self._lock:
            self._state.cancelled = True
            self._state.stage = ProgressStage.CANCELLED
        
        self._report()
    
    def get_current_progress(self) -> ProgressInfo:
        """
        获取当前进度信息
        
        Returns:
            进度信息
        """
        with self._lock:
            # 计算预计剩余时间
            estimated_time = None
            if (self._state.start_time and 
                self._state.progress > 0 and 
                self._state.progress < 1.0):
                elapsed = time.time() - self._state.start_time
                estimated_total = elapsed / self._state.progress
                estimated_time = int(estimated_total - elapsed)
            
            return ProgressInfo(
                stage=self._state.stage,
                progress=self._state.progress,
                message=self._state.message,
                detail=self._state.detail,
                estimated_time_remaining=estimated_time,
                processed_items=self._state.processed_items,
                total_items=self._state.total_items,
                timestamp=datetime.now(),
                metadata=self._state.metadata.copy()
            )
    
    def is_cancelled(self) -> bool:
        """
        检查是否已取消
        
        Returns:
            是否已取消
        """
        with self._lock:
            return self._state.cancelled
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        设置元数据
        
        Args:
            key: 键
            value: 值
        """
        with self._lock:
            self._state.metadata[key] = value
    
    def _report(self) -> None:
        """报告进度"""
        progress_info = self.get_current_progress()
        self._reporter.report_progress(progress_info)


class ProgressReporter(IProgressReporter):
    """
    进度报告器实现
    
    管理多个追踪器并分发进度更新。
    """
    
    def __init__(self):
        """初始化报告器"""
        self._trackers: Dict[str, ProgressTracker] = {}
        self._callbacks: List[Callable[[ProgressInfo], None]] = []
        self._lock = Lock()
    
    def register_callback(self, callback: Callable[[ProgressInfo], None]) -> None:
        """
        注册进度回调
        
        Args:
            callback: 回调函数
        """
        with self._lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[ProgressInfo], None]) -> None:
        """
        注销进度回调
        
        Args:
            callback: 回调函数
        """
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
    
    def report_progress(self, progress_info: ProgressInfo) -> None:
        """
        报告进度
        
        Args:
            progress_info: 进度信息
        """
        with self._lock:
            callbacks = self._callbacks.copy()
        
        # 在锁外调用回调
        for callback in callbacks:
            try:
                callback(progress_info)
            except Exception as e:
                print(f"进度回调错误: {e}")
    
    def create_tracker(self, name: str) -> IProgressTracker:
        """
        创建进度追踪器
        
        Args:
            name: 追踪器名称
            
        Returns:
            进度追踪器实例
        """
        with self._lock:
            if name in self._trackers:
                # 返回现有追踪器
                return self._trackers[name]
            
            tracker = ProgressTracker(name, self)
            self._trackers[name] = tracker
            return tracker
    
    def get_tracker(self, name: str) -> Optional[ProgressTracker]:
        """
        获取追踪器
        
        Args:
            name: 追踪器名称
            
        Returns:
            追踪器实例
        """
        with self._lock:
            return self._trackers.get(name)
    
    def remove_tracker(self, name: str) -> bool:
        """
        移除追踪器
        
        Args:
            name: 追踪器名称
            
        Returns:
            是否成功移除
        """
        with self._lock:
            if name in self._trackers:
                del self._trackers[name]
                return True
            return False
    
    def get_all_trackers(self) -> List[ProgressTracker]:
        """
        获取所有追踪器
        
        Returns:
            追踪器列表
        """
        with self._lock:
            return list(self._trackers.values())
    
    def clear_trackers(self) -> None:
        """清除所有追踪器"""
        with self._lock:
            self._trackers.clear()


class ProgressManager:
    """
    进度管理器
    
    单例模式，提供全局进度管理功能。
    """
    
    _instance: Optional['ProgressManager'] = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._reporter = ProgressReporter()
            self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'ProgressManager':
        """
        获取实例
        
        Returns:
            进度管理器实例
        """
        return cls()
    
    def create_tracker(self, name: Optional[str] = None) -> IProgressTracker:
        """
        创建进度追踪器
        
        Args:
            name: 追踪器名称，None则自动生成
            
        Returns:
            进度追踪器
        """
        if name is None:
            name = f"tracker_{uuid.uuid4().hex[:8]}"
        return self._reporter.create_tracker(name)
    
    def register_callback(self, callback: Callable[[ProgressInfo], None]) -> None:
        """
        注册全局进度回调
        
        Args:
            callback: 回调函数
        """
        self._reporter.register_callback(callback)
    
    def unregister_callback(self, callback: Callable[[ProgressInfo], None]) -> None:
        """
        注销全局进度回调
        
        Args:
            callback: 回调函数
        """
        self._reporter.unregister_callback(callback)
    
    def get_reporter(self) -> IProgressReporter:
        """
        获取报告器
        
        Returns:
            进度报告器
        """
        return self._reporter


# 便捷函数
def get_progress_manager() -> ProgressManager:
    """
    获取进度管理器
    
    Returns:
        进度管理器实例
    """
    return ProgressManager.get_instance()


def create_progress_tracker(name: Optional[str] = None) -> IProgressTracker:
    """
    创建进度追踪器
    
    Args:
        name: 追踪器名称
        
    Returns:
        进度追踪器
    """
    return get_progress_manager().create_tracker(name)
