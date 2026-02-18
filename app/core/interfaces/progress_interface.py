"""
进度追踪接口定义

定义统一的进度追踪和报告接口。
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class ProgressStage(Enum):
    """进度阶段枚举"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    GENERATING = "generating"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class ProgressInfo:
    """进度信息数据类"""
    stage: ProgressStage
    progress: float  # 0.0 - 1.0
    message: str
    detail: Optional[str] = None
    estimated_time_remaining: Optional[int] = None  # 秒
    processed_items: int = 0
    total_items: int = 0
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def percentage(self) -> int:
        """获取百分比"""
        return int(self.progress * 100)
    
    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.stage == ProgressStage.COMPLETED
    
    @property
    def is_error(self) -> bool:
        """是否出错"""
        return self.stage == ProgressStage.ERROR


class IProgressTracker(ABC):
    """
    进度追踪器接口
    
    用于追踪长时间运行任务的进度。
    """
    
    @abstractmethod
    def start_stage(self, stage: ProgressStage, total_items: int = 1, message: str = "") -> None:
        """
        开始新阶段
        
        Args:
            stage: 阶段类型
            total_items: 总项目数
            message: 阶段描述
        """
        pass
    
    @abstractmethod
    def update_progress(self, progress: float, message: Optional[str] = None, 
                       detail: Optional[str] = None) -> None:
        """
        更新进度
        
        Args:
            progress: 进度值 (0.0 - 1.0)
            message: 进度消息
            detail: 详细信息
        """
        pass
    
    @abstractmethod
    def increment_progress(self, items: int = 1) -> None:
        """
        增加进度
        
        Args:
            items: 完成的项目数
        """
        pass
    
    @abstractmethod
    def complete_stage(self, message: Optional[str] = None) -> None:
        """
        完成当前阶段
        
        Args:
            message: 完成消息
        """
        pass
    
    @abstractmethod
    def set_error(self, error_message: str) -> None:
        """
        设置错误状态
        
        Args:
            error_message: 错误信息
        """
        pass
    
    @abstractmethod
    def cancel(self) -> None:
        """取消任务"""
        pass
    
    @abstractmethod
    def get_current_progress(self) -> ProgressInfo:
        """
        获取当前进度信息
        
        Returns:
            进度信息
        """
        pass
    
    @abstractmethod
    def is_cancelled(self) -> bool:
        """
        检查是否已取消
        
        Returns:
            是否已取消
        """
        pass


class IProgressReporter(ABC):
    """
    进度报告器接口
    
    用于向UI报告进度更新。
    """
    
    @abstractmethod
    def register_callback(self, callback: Callable[[ProgressInfo], None]) -> None:
        """
        注册进度回调
        
        Args:
            callback: 回调函数
        """
        pass
    
    @abstractmethod
    def unregister_callback(self, callback: Callable[[ProgressInfo], None]) -> None:
        """
        注销进度回调
        
        Args:
            callback: 回调函数
        """
        pass
    
    @abstractmethod
    def report_progress(self, progress_info: ProgressInfo) -> None:
        """
        报告进度
        
        Args:
            progress_info: 进度信息
        """
        pass
    
    @abstractmethod
    def create_tracker(self, name: str) -> IProgressTracker:
        """
        创建进度追踪器
        
        Args:
            name: 追踪器名称
            
        Returns:
            进度追踪器实例
        """
        pass
