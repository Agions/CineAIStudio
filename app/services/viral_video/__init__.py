"""
Viral Video Service
百万爆款视频处理服务

提供以下核心功能：
- 静音检测与移除 (Silence Removal)
- 智能节奏分析 (Pace Analysis)
- 动态字幕生成 (Dynamic Caption)
- 视觉冲击力增强 (Visual Impact Enhancement)
"""

from .silence_remover import SilenceRemover
from .pace_analyzer import PaceAnalyzer
from .caption_generator import CaptionGenerator

__all__ = [
    'SilenceRemover',
    'PaceAnalyzer', 
    'CaptionGenerator',
]
