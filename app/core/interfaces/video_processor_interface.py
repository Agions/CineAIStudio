"""
视频处理接口定义

定义视频处理相关服务的统一接口。
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple, Callable, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import numpy as np


class VideoFormat(Enum):
    """视频格式"""
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    MKV = "mkv"
    WEBM = "webm"


class VideoQuality(Enum):
    """视频质量"""
    ULTRA = "4K"      # 3840x2160
    HIGH = "1080p"    # 1920x1080
    MEDIUM = "720p"   # 1280x720
    LOW = "480p"      # 854x480


@dataclass
class VideoInfo:
    """视频信息"""
    path: str
    duration: float
    width: int
    height: int
    fps: float
    bitrate: int
    codec: str
    format: str
    audio_codec: Optional[str] = None
    audio_channels: int = 2
    audio_sample_rate: int = 44100
    file_size: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def resolution(self) -> str:
        """获取分辨率字符串"""
        return f"{self.width}x{self.height}"
    
    @property
    def aspect_ratio(self) -> float:
        """获取宽高比"""
        return self.width / self.height if self.height > 0 else 0


@dataclass
class ProcessingOptions:
    """处理选项"""
    output_format: VideoFormat = VideoFormat.MP4
    quality: VideoQuality = VideoQuality.HIGH
    preserve_aspect_ratio: bool = True
    target_width: Optional[int] = None
    target_height: Optional[int] = None
    target_fps: Optional[float] = None
    target_bitrate: Optional[int] = None
    audio_codec: str = "aac"
    video_codec: str = "libx264"
    preset: str = "medium"  # ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
    crf: int = 23  # 0-51, 越低质量越好
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ProcessingResult:
    """处理结果"""
    success: bool
    output_path: Optional[str] = None
    processing_time: float = 0.0
    error_message: Optional[str] = None
    output_info: Optional[VideoInfo] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class KeyframeInfo:
    """关键帧信息"""
    timestamp: float
    frame_number: int
    image_path: Optional[str] = None
    image_data: Optional[np.ndarray] = None
    
    def get_image(self) -> Optional[np.ndarray]:
        """获取图像数据"""
        if self.image_data is not None:
            return self.image_data
        if self.image_path:
            # 延迟加载
            try:
                import cv2
                return cv2.imread(self.image_path)
            except Exception:
                return None
        return None


@dataclass
class SceneInfo:
    """场景信息"""
    start_time: float
    end_time: float
    duration: float
    keyframe: Optional[KeyframeInfo] = None
    score: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class IVideoProcessor(ABC):
    """
    视频处理器接口
    
    提供视频处理的基础操作。
    """
    
    @abstractmethod
    def get_info(self, video_path: Union[str, Path]) -> VideoInfo:
        """
        获取视频信息
        
        Args:
            video_path: 视频路径
            
        Returns:
            视频信息
        """
        pass
    
    @abstractmethod
    def extract_frames(self, video_path: Union[str, Path],
                      output_dir: Union[str, Path],
                      interval: float = 1.0,
                      max_frames: Optional[int] = None) -> List[KeyframeInfo]:
        """
        提取视频帧
        
        Args:
            video_path: 视频路径
            output_dir: 输出目录
            interval: 提取间隔（秒）
            max_frames: 最大帧数
            
        Returns:
            关键帧列表
        """
        pass
    
    @abstractmethod
    def extract_audio(self, video_path: Union[str, Path],
                     output_path: Union[str, Path],
                     format: str = "mp3") -> ProcessingResult:
        """
        提取音频
        
        Args:
            video_path: 视频路径
            output_path: 输出路径
            format: 音频格式
            
        Returns:
            处理结果
        """
        pass
    
    @abstractmethod
    def merge_audio_video(self, video_path: Union[str, Path],
                         audio_path: Union[str, Path],
                         output_path: Union[str, Path],
                         options: Optional[ProcessingOptions] = None) -> ProcessingResult:
        """
        合并音视频
        
        Args:
            video_path: 视频路径
            audio_path: 音频路径
            output_path: 输出路径
            options: 处理选项
            
        Returns:
            处理结果
        """
        pass
    
    @abstractmethod
    def trim(self, video_path: Union[str, Path],
            output_path: Union[str, Path],
            start_time: float,
            end_time: float,
            options: Optional[ProcessingOptions] = None) -> ProcessingResult:
        """
        裁剪视频
        
        Args:
            video_path: 视频路径
            output_path: 输出路径
            start_time: 开始时间
            end_time: 结束时间
            options: 处理选项
            
        Returns:
            处理结果
        """
        pass
    
    @abstractmethod
    def concatenate(self, video_paths: List[Union[str, Path]],
                   output_path: Union[str, Path],
                   options: Optional[ProcessingOptions] = None) -> ProcessingResult:
        """
        拼接视频
        
        Args:
            video_paths: 视频路径列表
            output_path: 输出路径
            options: 处理选项
            
        Returns:
            处理结果
        """
        pass
    
    @abstractmethod
    def transcode(self, video_path: Union[str, Path],
                 output_path: Union[str, Path],
                 options: ProcessingOptions) -> ProcessingResult:
        """
        转码视频
        
        Args:
            video_path: 视频路径
            output_path: 输出路径
            options: 处理选项
            
        Returns:
            处理结果
        """
        pass


class IVideoAnalyzer(ABC):
    """
    视频分析器接口
    
    提供视频内容分析功能。
    """
    
    @abstractmethod
    def detect_scenes(self, video_path: Union[str, Path],
                     threshold: float = 0.3) -> List[SceneInfo]:
        """
        检测场景
        
        Args:
            video_path: 视频路径
            threshold: 检测阈值
            
        Returns:
            场景列表
        """
        pass
    
    @abstractmethod
    def detect_beats(self, video_path: Union[str, Path],
                    min_bpm: float = 60.0,
                    max_bpm: float = 200.0) -> List[float]:
        """
        检测节拍
        
        Args:
            video_path: 视频路径
            min_bpm: 最小BPM
            max_bpm: 最大BPM
            
        Returns:
            节拍时间列表
        """
        pass
    
    @abstractmethod
    def analyze_motion(self, video_path: Union[str, Path],
                      sample_interval: float = 0.5) -> Dict[str, Any]:
        """
        分析运动
        
        Args:
            video_path: 视频路径
            sample_interval: 采样间隔
            
        Returns:
            运动分析结果
        """
        pass
    
    @abstractmethod
    def get_best_scenes(self, video_path: Union[str, Path],
                       count: int = 5,
                       min_duration: float = 1.0) -> List[SceneInfo]:
        """
        获取最佳场景
        
        Args:
            video_path: 视频路径
            count: 场景数量
            min_duration: 最小场景时长
            
        Returns:
            最佳场景列表
        """
        pass
