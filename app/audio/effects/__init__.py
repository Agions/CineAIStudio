"""
Audio Effects Module for CineAIStudio
Professional audio effects and processing capabilities
"""

from .advanced_effects import (
    AdvancedEffectsProcessor, AudioEffect, EffectType, EffectParameter,
    MultibandCompressor, GraphicEqualizer, DeEsser, StereoEnhancer
)

__all__ = [
    'AdvancedEffectsProcessor',
    'AudioEffect',
    'EffectType',
    'EffectParameter',
    'MultibandCompressor',
    'GraphicEqualizer',
    'DeEsser',
    'StereoEnhancer'
]