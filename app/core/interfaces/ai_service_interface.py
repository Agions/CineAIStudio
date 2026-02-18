"""
AI服务接口定义

定义AI相关服务的统一接口。
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, BinaryIO, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class AIServiceType(Enum):
    """AI服务类型"""
    VISION = "vision"
    VOICE = "voice"
    TEXT = "text"
    MULTIMODAL = "multimodal"


class AIProvider(Enum):
    """AI提供商"""
    OPENAI = "openai"
    AZURE = "azure"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    EDGE = "edge"


@dataclass
class AIRequest:
    """AI请求数据类"""
    prompt: str
    context: Optional[str] = None
    images: Optional[List[Union[str, bytes]]] = None
    max_tokens: int = 500
    temperature: float = 0.7
    model: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.images is None:
            self.images = []


@dataclass
class AIResponse:
    """AI响应数据类"""
    content: str
    model: str
    provider: AIProvider
    tokens_used: int = 0
    processing_time: float = 0.0
    raw_response: Any = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class VisionAnalysisResult:
    """视觉分析结果"""
    description: str
    objects: List[str]
    text_content: Optional[str] = None
    content_type: Optional[str] = None
    emotion: Optional[str] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.objects is None:
            self.objects = []


@dataclass
class VoiceConfig:
    """语音配置"""
    voice_id: str = "default"
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    language: str = "zh-CN"
    emotion: Optional[str] = None


@dataclass
class GeneratedVoice:
    """生成的语音"""
    audio_path: str
    duration: float
    text: str
    config: VoiceConfig
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class IAIService(ABC):
    """
    AI服务基础接口
    """
    
    @property
    @abstractmethod
    def provider(self) -> AIProvider:
        """服务提供商"""
        pass
    
    @property
    @abstractmethod
    def service_type(self) -> AIServiceType:
        """服务类型"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        检查服务是否可用
        
        Returns:
            是否可用
        """
        pass
    
    @abstractmethod
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        获取使用统计
        
        Returns:
            统计信息
        """
        pass


class IVisionService(IAIService):
    """
    视觉服务接口
    
    用于图像/视频分析。
    """
    
    @abstractmethod
    def analyze_image(self, image: Union[str, Path, bytes, BinaryIO],
                     prompt: Optional[str] = None) -> VisionAnalysisResult:
        """
        分析图像
        
        Args:
            image: 图像路径或数据
            prompt: 分析提示词
            
        Returns:
            分析结果
        """
        pass
    
    @abstractmethod
    def analyze_images_batch(self, images: List[Union[str, Path, bytes]],
                            prompt: Optional[str] = None,
                            max_workers: int = 4) -> List[VisionAnalysisResult]:
        """
        批量分析图像
        
        Args:
            images: 图像列表
            prompt: 分析提示词
            max_workers: 最大并发数
            
        Returns:
            分析结果列表
        """
        pass
    
    @abstractmethod
    def extract_text(self, image: Union[str, Path, bytes, BinaryIO]) -> str:
        """
        提取图像中的文字
        
        Args:
            image: 图像路径或数据
            
        Returns:
            提取的文字
        """
        pass


class IVoiceService(IAIService):
    """
    语音服务接口
    
    用于语音合成和识别。
    """
    
    @abstractmethod
    def synthesize(self, text: str, output_path: str,
                   config: Optional[VoiceConfig] = None) -> GeneratedVoice:
        """
        合成语音
        
        Args:
            text: 文本内容
            output_path: 输出路径
            config: 语音配置
            
        Returns:
            生成的语音
        """
        pass
    
    @abstractmethod
    def synthesize_batch(self, texts: List[str], output_dir: str,
                        config: Optional[VoiceConfig] = None,
                        max_workers: int = 4) -> List[GeneratedVoice]:
        """
        批量合成语音
        
        Args:
            texts: 文本列表
            output_dir: 输出目录
            config: 语音配置
            max_workers: 最大并发数
            
        Returns:
            生成的语音列表
        """
        pass
    
    @abstractmethod
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        获取可用语音列表
        
        Returns:
            语音列表
        """
        pass
    
    @abstractmethod
    def preview_voice(self, text: str, config: Optional[VoiceConfig] = None) -> bytes:
        """
        预览语音
        
        Args:
            text: 预览文本
            config: 语音配置
            
        Returns:
            音频数据
        """
        pass


class ITextService(IAIService):
    """
    文本服务接口
    
    用于文本生成和处理。
    """
    
    @abstractmethod
    def generate(self, request: AIRequest) -> AIResponse:
        """
        生成文本
        
        Args:
            request: 请求数据
            
        Returns:
            响应数据
        """
        pass
    
    @abstractmethod
    def generate_stream(self, request: AIRequest):
        """
        流式生成文本
        
        Args:
            request: 请求数据
            
        Yields:
            文本片段
        """
        pass
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]],
             system_prompt: Optional[str] = None) -> AIResponse:
        """
        对话
        
        Args:
            messages: 消息列表
            system_prompt: 系统提示词
            
        Returns:
            响应数据
        """
        pass
