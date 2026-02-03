"""
CineAIStudio AI 服务模块

提供 AI 驱动的内容生成能力:
- SceneAnalyzer: 视频场景分析（基于FFmpeg）
- VideoContentAnalyzer: 视频内容深度分析（基于视觉AI）
- ScriptGenerator: 文案生成
- VoiceGenerator: AI 配音
"""

from .scene_analyzer import SceneAnalyzer, SceneInfo, SceneType, AnalysisConfig
from .script_generator import ScriptGenerator, ScriptConfig, ScriptStyle, GeneratedScript, VoiceTone
from .voice_generator import VoiceGenerator, VoiceConfig, VoiceStyle, GeneratedVoice
from .video_content_analyzer import (
    VideoContentAnalyzer, VideoAnalysisResult, KeyframeInfo,
    AnalyzerConfig, ContentType, Emotion, analyze_video,
)


__all__ = [
    # 场景分析
    'SceneAnalyzer',
    'SceneInfo',
    'SceneType',
    'AnalysisConfig',
    
    # 视频内容分析
    'VideoContentAnalyzer',
    'VideoAnalysisResult',
    'KeyframeInfo',
    'AnalyzerConfig',
    'ContentType',
    'Emotion',
    'analyze_video',
    
    # 文案生成
    'ScriptGenerator',
    'ScriptConfig',
    'ScriptStyle',
    'GeneratedScript',
    'VoiceTone',
    
    # AI 配音
    'VoiceGenerator',
    'VoiceConfig',
    'VoiceStyle',
    'GeneratedVoice',
]
