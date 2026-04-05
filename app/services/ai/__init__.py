"""
Narrafiilm AI 服务模块

提供AI能力:
- LLM: 大语言模型支持（DeepSeek-V3 主力）
- Vision: 视觉理解（Qwen2.5-VL 72B SOTA）
- Voice: 语音合成（Edge-TTS / F5-TTS）
- Analysis: 视频分析
- FirstPersonNarrator: 第一人称解说编排器（核心）
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
from .vision_providers import (
    VisionProvider,
    VisionAnalyzerFactory,
    FIRST_PERSON_ANALYSIS_PROMPT,
)

# 语音相关
from .voice_generator import VoiceGenerator, VoiceConfig, VoiceStyle

# 第一人称解说编排器 ⭐
from .first_person_narrator import (
    FirstPersonNarrator,
    NarrationProject,
    SceneSegment,
)

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
    "FIRST_PERSON_ANALYSIS_PROMPT",

    # Voice
    "VoiceGenerator",
    "VoiceConfig",
    "VoiceStyle",

    # FirstPersonNarrator ⭐
    "FirstPersonNarrator",
    "NarrationProject",
    "SceneSegment",

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
