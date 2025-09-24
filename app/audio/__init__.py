"""
Audio Processing Module for CineAIStudio
Provides comprehensive audio processing capabilities including mixing, analysis, and effects
"""

from .mixer.audio_mixer import AudioMixer, AudioTrack, AudioBus, AutomationMode
from .analysis.audio_analyzer import AudioAnalyzer, AudioMetrics, AnalysisMode, LevelMeter, SpectrumAnalyzer
from .effects.advanced_effects import AdvancedEffectsProcessor, AudioEffect

__all__ = [
    'AudioMixer',
    'AudioTrack',
    'AudioBus',
    'AutomationMode',
    'AudioAnalyzer',
    'AudioMetrics',
    'AnalysisMode',
    'LevelMeter',
    'SpectrumAnalyzer',
    'AdvancedEffectsProcessor',
    'AudioEffect'
]