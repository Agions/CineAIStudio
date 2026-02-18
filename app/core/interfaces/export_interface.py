"""
导出接口定义

定义导出相关服务的统一接口。
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from datetime import datetime


class ExportFormat(Enum):
    """导出格式"""
    JIANYING = "jianying"
    FINAL_CUT = "final_cut"
    PREMIERE = "premiere"
    DAVINCI = "davinci"
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE_SEQUENCE = "image_sequence"


class ExportStatus(Enum):
    """导出状态"""
    PENDING = "pending"
    PREPARING = "preparing"
    PROCESSING = "processing"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class ExportConfig:
    """导出配置"""
    format: ExportFormat
    output_path: str
    quality: str = "high"
    resolution: Optional[str] = None
    fps: Optional[float] = None
    bitrate: Optional[int] = None
    codec: Optional[str] = None
    include_audio: bool = True
    metadata: Dict[str, Any] = None
    options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.options is None:
            self.options = {}


@dataclass
class ExportProgress:
    """导出进度"""
    status: ExportStatus
    progress: float  # 0.0 - 1.0
    current_stage: str
    processed_frames: int = 0
    total_frames: int = 0
    estimated_time_remaining: Optional[int] = None
    message: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def percentage(self) -> int:
        """获取百分比"""
        return int(self.progress * 100)


@dataclass
class ExportResult:
    """导出结果"""
    success: bool
    output_path: Optional[str] = None
    export_time: float = 0.0
    file_size: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.warnings is None:
            self.warnings = []


@dataclass
class ExportJob:
    """导出任务"""
    id: str
    name: str
    config: ExportConfig
    status: ExportStatus
    progress: ExportProgress
    result: Optional[ExportResult] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class IExporter(ABC):
    """
    导出器接口
    
    提供统一的导出功能。
    """
    
    @property
    @abstractmethod
    def supported_formats(self) -> List[ExportFormat]:
        """支持的导出格式"""
        pass
    
    @abstractmethod
    def can_export(self, format: ExportFormat) -> bool:
        """
        检查是否支持导出格式
        
        Args:
            format: 导出格式
            
        Returns:
            是否支持
        """
        pass
    
    @abstractmethod
    def export(self, source: Any, config: ExportConfig,
               progress_callback: Optional[callable] = None) -> ExportResult:
        """
        执行导出
        
        Args:
            source: 导出源数据
            config: 导出配置
            progress_callback: 进度回调
            
        Returns:
            导出结果
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: ExportConfig) -> bool:
        """
        验证导出配置
        
        Args:
            config: 导出配置
            
        Returns:
            配置是否有效
        """
        pass
    
    @abstractmethod
    def get_default_config(self, format: ExportFormat) -> ExportConfig:
        """
        获取默认配置
        
        Args:
            format: 导出格式
            
        Returns:
            默认配置
        """
        pass


class IProjectExporter(ABC):
    """
    项目导出器接口
    
    用于导出项目到外部编辑器。
    """
    
    @property
    @abstractmethod
    def editor_name(self) -> str:
        """编辑器名称"""
        pass
    
    @property
    @abstractmethod
    def file_extension(self) -> str:
        """文件扩展名"""
        pass
    
    @abstractmethod
    def create_project(self, name: str, config: Optional[Dict[str, Any]] = None) -> Any:
        """
        创建项目
        
        Args:
            name: 项目名称
            config: 项目配置
            
        Returns:
            项目对象
        """
        pass
    
    @abstractmethod
    def add_video_track(self, project: Any, track_data: Dict[str, Any]) -> Any:
        """
        添加视频轨道
        
        Args:
            project: 项目对象
            track_data: 轨道数据
            
        Returns:
            轨道对象
        """
        pass
    
    @abstractmethod
    def add_audio_track(self, project: Any, track_data: Dict[str, Any]) -> Any:
        """
        添加音频轨道
        
        Args:
            project: 项目对象
            track_data: 轨道数据
            
        Returns:
            轨道对象
        """
        pass
    
    @abstractmethod
    def add_text_track(self, project: Any, track_data: Dict[str, Any]) -> Any:
        """
        添加文字轨道
        
        Args:
            project: 项目对象
            track_data: 轨道数据
            
        Returns:
            轨道对象
        """
        pass
    
    @abstractmethod
    def add_segment(self, track: Any, segment_data: Dict[str, Any]) -> Any:
        """
        添加片段
        
        Args:
            track: 轨道对象
            segment_data: 片段数据
            
        Returns:
            片段对象
        """
        pass
    
    @abstractmethod
    def save_project(self, project: Any, output_path: Union[str, Path]) -> ExportResult:
        """
        保存项目
        
        Args:
            project: 项目对象
            output_path: 输出路径
            
        Returns:
            导出结果
        """
        pass
