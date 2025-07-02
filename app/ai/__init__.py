"""
AI module for VideoEpicCreator

This module contains all AI-related functionality including:
- AI model integrations (OpenAI, 通义千问, 文心一言, Ollama, etc.)
- Content generators (commentary, compilation, monologue)
- Video analyzers (scene detection, emotion analysis, highlight detection)
"""

from .ai_manager import AIManager
from .scene_detector import SceneDetector, SceneInfo
from .content_generator import ContentGenerator, GeneratedContent, ContentSegment
from .models import (
    BaseAIModel, AIModelConfig, AIResponse,
    OpenAIModel, QianwenModel, WenxinModel, OllamaModel
)

__version__ = "1.0.0"

__all__ = [
    'AIManager', 'SceneDetector', 'SceneInfo',
    'ContentGenerator', 'GeneratedContent', 'ContentSegment',
    'BaseAIModel', 'AIModelConfig', 'AIResponse',
    'OpenAIModel', 'QianwenModel', 'WenxinModel', 'OllamaModel'
]
