"""
VideoForge AI 服务模块

提供AI能力:
- LLM: 大语言模型支持
- Vision: 视觉理解
- Voice: 语音合成
- Analysis: 视频分析
"""

# LLM 相关
from .base_llm_provider import (
    BaseLLMProvider,
    LLMRequest,
    LLMResponse,
    ProviderType,
    ProviderError,
)
from .llm_manager import LLMManager

# 视觉相关
from .vision_providers import VisionProvider, VisionAnalyzerFactory

# 语音相关
from .voice_generator import VoiceGenerator, VoiceConfig, VoiceStyle

# 分析相关
from .scene_analyzer import SceneAnalyzer, SceneInfo
from .video_understanding import VideoUnderstanding
from .video_summarizer import VideoSummarizer
from .script_generator import ScriptGenerator
from .story_analyzer import StoryAnalyzer, StoryAnalysisResult, PlotType, SceneType
from .cut_template import CutTemplateManager, CutTemplate, TemplateStyle
from .batch_story_processor import BatchStoryProcessor, BatchStatus
from .cut_preview import CutPreviewGenerator, PreviewConfig

# 缓存
from .cache import LLMMemoryCache


__all__ = [
    # LLM
    "BaseLLMProvider",
    "LLMRequest",
    "LLMResponse",
    "ProviderType",
    "ProviderError",
    "LLMManager",

    # Vision
    "VisionProvider",
    "VisionAnalyzerFactory",

    # Voice
    "VoiceGenerator",
    "VoiceConfig",
    "VoiceStyle",

    # Analysis
    "SceneAnalyzer",
    "SceneInfo",
    "VideoUnderstanding",
    "VideoSummarizer",
    "ScriptGenerator",
    "StoryAnalyzer",
    "StoryAnalysisResult",
    "PlotType",
    "SceneType",

    # Template
    "CutTemplateManager",
    "CutTemplate",
    "TemplateStyle",

    # Batch Processing
    "BatchStoryProcessor",
    "BatchStatus",

    # Preview
    "CutPreviewGenerator",
    "PreviewConfig",

    # Cache
    "LLMMemoryCache",
]
