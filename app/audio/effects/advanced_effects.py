"""
Advanced Audio Effects Module for CineAIStudio
Provides professional-grade audio effects and processing capabilities
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import librosa
import soundfile as sf
from scipy import signal
from scipy.signal import butter, filtfilt, iirnotch, lfilter
from scipy.fft import fft, ifft, fftfreq
import subprocess
import tempfile
import json
from pathlib import Path


class EffectType(Enum):
    """Audio effect types"""
    DYNAMICS = "dynamics"
    EQUALIZATION = "equalization"
    SPATIAL = "spatial"
    TIME_BASED = "time_based"
    DISTORTION = "distortion"
    RESTORATION = "restoration"
    PITCH_SHIFT = "pitch_shift"


@dataclass
class EffectParameter:
    """Effect parameter definition"""
    name: str
    type: str  # float, int, bool, enum
    min_value: float
    max_value: float
    default_value: float
    description: str
    unit: str = ""
    scale: str = "linear"  # linear, logarithmic


@dataclass
class AudioEffect:
    """Audio effect configuration"""
    id: str
    name: str
    type: EffectType
    parameters: Dict[str, EffectParameter]
    current_values: Dict[str, float]
    enabled: bool = True
    wet_level: float = 1.0
    dry_level: float = 0.0

    def __post_init__(self):
        # Initialize current values with defaults
        for param_name, param in self.parameters.items():
            if param_name not in self.current_values:
                self.current_values[param_name] = param.default_value


class MultibandCompressor:
    """Professional multiband compressor"""

    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate

        # Band frequencies (standard 4-band)
        self.bands = [
            {"name": "Low", "range": (20, 250), "enabled": True},
            {"name": "Low Mid", "range": (250, 2000), "enabled": True},
            {"name": "High Mid", "range": (2000, 8000), "enabled": True},
            {"name": "High", "range": (8000, 20000), "enabled": True}
        ]

        # Default parameters
        self.threshold = -20.0  # dB
        self.ratio = 4.0
        self.attack_time = 0.003  # seconds
        self.release_time = 0.1  # seconds
        self.makeup_gain = 0.0  # dB
        self.knee_width = 6.0  # dB

        # State variables
        self.band_states = {}
        self._initialize_band_states()

    def _initialize_band_states(self):
        """Initialize compressor state for each band"""
        for band in self.bands:
            self.band_states[band["name"]] = {
                "gain_reduction": 0.0,
                "envelope": 0.0,
                "filter_state": {"b": None, "a": None, "state": None}
            }

    def _create_bandpass_filter(self, low_freq: float, high_freq: float) -> Tuple[np.ndarray, np.ndarray]:
        """Create bandpass filter for frequency band"""
        nyquist = self.sample_rate / 2

        # Design bandpass filter
        low = low_freq / nyquist
        high = high_freq / nyquist

        b, a = butter(4, [low, high], btype='band')
        return b, a

    def _compressor_curve(self, input_db: float, threshold: float, ratio: float,
                         knee_width: float) -> float:
        """Calculate compressor gain reduction"""
        if input_db < threshold - knee_width/2:
            return 0.0  # Below threshold
        elif input_db > threshold + knee_width/2:
            # Above knee, apply compression
            gain_reduction = (input_db - threshold) * (1 - 1/ratio)
            return gain_reduction
        else:
            # In knee region, smooth transition
            knee_pos = (input_db - (threshold - knee_width/2)) / knee_width
            gain_reduction = knee_pos * (input_db - threshold) * (1 - 1/ratio) * 0.5
            return gain_reduction

    def _process_band(self, audio_data: np.ndarray, band_name: str) -> np.ndarray:
        """Process single frequency band"""
        band = next((b for b in self.bands if b["name"] == band_name), None)
        if not band or not band["enabled"]:
            return audio_data

        state = self.band_states[band_name]

        # Create bandpass filter if not exists
        if state["filter_state"]["b"] is None:
            low_freq, high_freq = band["range"]
            b, a = self._create_bandpass_filter(low_freq, high_freq)
            state["filter_state"]["b"] = b
            state["filter_state"]["a"] = a
            state["filter_state"]["state"] = np.zeros(max(len(a), len(b)) - 1)

        # Apply bandpass filter
        b, a = state["filter_state"]["b"], state["filter_state"]["a"]
        zi = state["filter_state"]["state"]
        filtered, zi_new = lfilter(b, a, audio_data, zi=zi)
        state["filter_state"]["state"] = zi_new

        # Calculate envelope
        attack_coeff = 1 - np.exp(-1 / (self.attack_time * self.sample_rate))
        release_coeff = 1 - np.exp(-1 / (self.release_time * self.sample_rate))

        envelope = np.zeros_like(filtered)
        envelope[0] = state["envelope"]

        for i in range(1, len(filtered)):
            level = abs(filtered[i])
            if level > envelope[i-1]:
                envelope[i] = attack_coeff * level + (1 - attack_coeff) * envelope[i-1]
            else:
                envelope[i] = release_coeff * level + (1 - release_coeff) * envelope[i-1]

        state["envelope"] = envelope[-1]

        # Calculate gain reduction
        envelope_db = 20 * np.log10(envelope + 1e-10)
        gain_reduction_db = np.array([
            self._compressor_curve(db, self.threshold, self.ratio, self.knee_width)
            for db in envelope_db
        ])

        # Apply gain reduction
        gain_linear = 10 ** (-gain_reduction_db / 20)
        compressed = filtered * gain_linear

        # Apply makeup gain
        makeup_linear = 10 ** (self.makeup_gain / 20)
        compressed *= makeup_linear

        return compressed

    def process(self, audio_data: np.ndarray) -> np.ndarray:
        """Process audio through multiband compressor"""
        # Process each band
        band_outputs = []
        for band in self.bands:
            if band["enabled"]:
                band_output = self._process_band(audio_data, band["name"])
                band_outputs.append(band_output)

        # Mix bands
        if band_outputs:
            output = np.sum(band_outputs, axis=0)
        else:
            output = audio_data

        return output


class GraphicEqualizer:
    """31-band graphic equalizer (ISO standard frequencies)"""

    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate

        # ISO 31-band frequencies
        self.frequencies = [
            20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500,
            630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000,
            10000, 12500, 16000, 20000
        ]

        # Default gains (all flat)
        self.gains = np.zeros(len(self.frequencies))

        # Filter states
        self.filter_states = {}

    def set_band_gain(self, band_index: int, gain_db: float):
        """Set gain for specific frequency band"""
        if 0 <= band_index < len(self.gains):
            self.gains[band_index] = np.clip(gain_db, -12, 12)  # ±12dB range

    def _create_peak_filter(self, frequency: float, gain_db: float, q: float = 1.0):
        """Create peak EQ filter"""
        nyquist = self.sample_rate / 2
        w0 = 2 * np.pi * frequency / self.sample_rate
        alpha = np.sin(w0) / (2 * q)
        A = 10 ** (gain_db / 40)

        b0 = 1 + alpha * A
        b1 = -2 * np.cos(w0)
        b2 = 1 - alpha * A
        a0 = 1 + alpha / A
        a1 = -2 * np.cos(w0)
        a2 = 1 - alpha / A

        # Normalize
        b = np.array([b0, b1, b2]) / a0
        a = np.array([a0, a1, a2]) / a0

        return b, a

    def process(self, audio_data: np.ndarray) -> np.ndarray:
        """Process audio through graphic equalizer"""
        output = audio_data.copy()

        # Apply each band's filter
        for i, (freq, gain) in enumerate(zip(self.frequencies, self.gains)):
            if abs(gain) > 0.1:  # Only process if gain is significant
                b, a = self._create_peak_filter(freq, gain)

                if i not in self.filter_states:
                    self.filter_states[i] = np.zeros(max(len(a), len(b)) - 1)

                zi = self.filter_states[i]
                output, zi_new = lfilter(b, a, output, zi=zi)
                self.filter_states[i] = zi_new

        return output


class DeEsser:
    """Professional de-esser for sibilance reduction"""

    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate

        # Parameters
        self.threshold = -20.0  # dB
        self.ratio = 10.0
        self.frequency = 5000.0  # Hz (sibilance range)
        self.bandwidth = 2000.0  # Hz
        self.attack_time = 0.001  # 1ms
        self.release_time = 0.05  # 50ms

        # State
        self.envelope = 0.0

    def process(self, audio_data: np.ndarray) -> np.ndarray:
        """Process audio through de-esser"""
        # Create bandpass filter for sibilance detection
        nyquist = self.sample_rate / 2
        low_freq = self.frequency - self.bandwidth / 2
        high_freq = self.frequency + self.bandwidth / 2

        # Normalize frequencies
        low = max(0.01, low_freq / nyquist)
        high = min(0.99, high_freq / nyquist)

        b, a = butter(4, [low, high], btype='band')

        # Filter to isolate sibilance
        sibilance = filtfilt(b, a, audio_data)

        # Calculate envelope
        attack_coeff = 1 - np.exp(-1 / (self.attack_time * self.sample_rate))
        release_coeff = 1 - np.exp(-1 / (self.release_time * self.sample_rate))

        envelope = np.zeros_like(sibilance)
        envelope[0] = self.envelope

        for i in range(1, len(sibilance)):
            level = abs(sibilance[i])
            if level > envelope[i-1]:
                envelope[i] = attack_coeff * level + (1 - attack_coeff) * envelope[i-1]
            else:
                envelope[i] = release_coeff * level + (1 - release_coeff) * envelope[i-1]

        self.envelope = envelope[-1]

        # Calculate gain reduction
        envelope_db = 20 * np.log10(envelope + 1e-10)
        gain_reduction = np.where(
            envelope_db > self.threshold,
            (envelope_db - self.threshold) * (1 - 1/self.ratio),
            0
        )

        # Apply gain reduction
        gain_linear = 10 ** (-gain_reduction / 20)
        output = audio_data * gain_linear

        return output


class StereoEnhancer:
    """Stereo width enhancer"""

    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate

        # Parameters
        self.width = 1.0  # 0.0 = mono, 1.0 = normal, 2.0 = wide
        self.phase_correction = True
        self.low_freq_limit = 150.0  # Hz - don't enhance below this

    def process(self, audio_data: np.ndarray) -> np.ndarray:
        """Process stereo enhancement"""
        if len(audio_data.shape) < 2 or audio_data.shape[0] < 2:
            return audio_data  # Input is mono

        left = audio_data[0]
        right = audio_data[1]

        # Apply high-pass filter to low frequencies (preserve bass in mono)
        nyquist = self.sample_rate / 2
        if self.low_freq_limit > 0:
            b, a = butter(2, self.low_freq_limit / nyquist, btype='high')
            left_filtered = filtfilt(b, a, left)
            right_filtered = filtfilt(b, a, right)
        else:
            left_filtered = left
            right_filtered = right

        # Calculate mid/side
        mid = (left_filtered + right_filtered) / 2
        side = (left_filtered - right_filtered) / 2

        # Enhance side signal
        enhanced_side = side * self.width

        # Phase correction (optional)
        if self.phase_correction:
            # Simple phase alignment
            enhanced_side = np.roll(enhanced_side, 1)

        # Convert back to left/right
        enhanced_left = mid + enhanced_side
        enhanced_right = mid - enhanced_side

        # Mix with original low frequencies
        if self.low_freq_limit > 0:
            b, a = butter(2, self.low_freq_limit / nyquist, btype='low')
            left_low = filtfilt(b, a, left)
            right_low = filtfilt(b, a, right)

            enhanced_left += left_low
            enhanced_right += right_low

        return np.array([enhanced_left, enhanced_right])


class AdvancedEffectsProcessor:
    """Advanced audio effects processor"""

    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.effects = {}

        # Initialize effect processors
        self.multiband_compressor = MultibandCompressor(sample_rate)
        self.graphic_eq = GraphicEqualizer(sample_rate)
        self.deesser = DeEsser(sample_rate)
        self.stereo_enhancer = StereoEnhancer(sample_rate)

    def _create_effect_definition(self, effect_id: str, name: str,
                                effect_type: EffectType, parameters: List[Dict]) -> AudioEffect:
        """Create effect definition"""
        params = {}
        defaults = {}

        for param in parameters:
            param_obj = EffectParameter(**param)
            params[param["name"]] = param_obj
            defaults[param["name"]] = param["default_value"]

        return AudioEffect(
            id=effect_id,
            name=name,
            type=effect_type,
            parameters=params,
            current_values=defaults
        )

    def get_available_effects(self) -> Dict[str, AudioEffect]:
        """Get all available effects"""
        effects = {}

        # Multiband Compressor
        effects["multiband_compressor"] = self._create_effect_definition(
            "multiband_compressor",
            "Multiband Compressor",
            EffectType.DYNAMICS,
            [
                {
                    "name": "threshold",
                    "type": "float",
                    "min_value": -60.0,
                    "max_value": 0.0,
                    "default_value": -20.0,
                    "description": "Compression threshold",
                    "unit": "dB"
                },
                {
                    "name": "ratio",
                    "type": "float",
                    "min_value": 1.0,
                    "max_value": 20.0,
                    "default_value": 4.0,
                    "description": "Compression ratio",
                    "unit": ":1"
                },
                {
                    "name": "attack",
                    "type": "float",
                    "min_value": 0.001,
                    "max_value": 0.1,
                    "default_value": 0.003,
                    "description": "Attack time",
                    "unit": "s"
                },
                {
                    "name": "release",
                    "type": "float",
                    "min_value": 0.01,
                    "max_value": 2.0,
                    "default_value": 0.1,
                    "description": "Release time",
                    "unit": "s"
                },
                {
                    "name": "makeup_gain",
                    "type": "float",
                    "min_value": -20.0,
                    "max_value": 20.0,
                    "default_value": 0.0,
                    "description": "Makeup gain",
                    "unit": "dB"
                }
            ]
        )

        # Graphic Equalizer
        effects["graphic_eq"] = self._create_effect_definition(
            "graphic_eq",
            "31-Band Graphic EQ",
            EffectType.EQUALIZATION,
            [
                {
                    "name": "overall_gain",
                    "type": "float",
                    "min_value": -12.0,
                    "max_value": 12.0,
                    "default_value": 0.0,
                    "description": "Overall gain",
                    "unit": "dB"
                }
            ]
        )

        # De-Esser
        effects["deesser"] = self._create_effect_definition(
            "deesser",
            "De-Esser",
            EffectType.DYNAMICS,
            [
                {
                    "name": "threshold",
                    "type": "float",
                    "min_value": -40.0,
                    "max_value": 0.0,
                    "default_value": -20.0,
                    "description": "Sibilance threshold",
                    "unit": "dB"
                },
                {
                    "name": "frequency",
                    "type": "float",
                    "min_value": 2000.0,
                    "max_value": 10000.0,
                    "default_value": 5000.0,
                    "description": "Sibilance frequency",
                    "unit": "Hz"
                },
                {
                    "name": "bandwidth",
                    "type": "float",
                    "min_value": 500.0,
                    "max_value": 5000.0,
                    "default_value": 2000.0,
                    "description": "Detection bandwidth",
                    "unit": "Hz"
                }
            ]
        )

        # Stereo Enhancer
        effects["stereo_enhancer"] = self._create_effect_definition(
            "stereo_enhancer",
            "Stereo Enhancer",
            EffectType.SPATIAL,
            [
                {
                    "name": "width",
                    "type": "float",
                    "min_value": 0.0,
                    "max_value": 3.0,
                    "default_value": 1.0,
                    "description": "Stereo width",
                    "unit": ""
                },
                {
                    "name": "low_freq_limit",
                    "type": "float",
                    "min_value": 20.0,
                    "max_value": 500.0,
                    "default_value": 150.0,
                    "description": "Low frequency limit",
                    "unit": "Hz"
                }
            ]
        )

        return effects

    def apply_effect(self, audio_data: np.ndarray, effect_id: str,
                    parameters: Dict[str, float] = None) -> np.ndarray:
        """Apply effect to audio data"""
        if parameters is None:
            parameters = {}

        try:
            if effect_id == "multiband_compressor":
                # Update multiband compressor parameters
                self.multiband_compressor.threshold = parameters.get("threshold", -20.0)
                self.multiband_compressor.ratio = parameters.get("ratio", 4.0)
                self.multiband_compressor.attack_time = parameters.get("attack", 0.003)
                self.multiband_compressor.release_time = parameters.get("release", 0.1)
                self.multiband_compressor.makeup_gain = parameters.get("makeup_gain", 0.0)

                return self.multiband_compressor.process(audio_data)

            elif effect_id == "graphic_eq":
                # Apply overall gain
                overall_gain = parameters.get("overall_gain", 0.0)
                if overall_gain != 0.0:
                    gain_linear = 10 ** (overall_gain / 20)
                    audio_data = audio_data * gain_linear

                return self.graphic_eq.process(audio_data)

            elif effect_id == "deesser":
                # Update de-esser parameters
                self.deesser.threshold = parameters.get("threshold", -20.0)
                self.deesser.frequency = parameters.get("frequency", 5000.0)
                self.deesser.bandwidth = parameters.get("bandwidth", 2000.0)

                return self.deesser.process(audio_data)

            elif effect_id == "stereo_enhancer":
                # Update stereo enhancer parameters
                self.stereo_enhancer.width = parameters.get("width", 1.0)
                self.stereo_enhancer.low_freq_limit = parameters.get("low_freq_limit", 150.0)

                return self.stereo_enhancer.process(audio_data)

            else:
                print(f"Unknown effect: {effect_id}")
                return audio_data

        except Exception as e:
            print(f"Error applying effect {effect_id}: {e}")
            return audio_data

    def apply_effect_chain(self, audio_data: np.ndarray,
                          effect_chain: List[Dict[str, Any]]) -> np.ndarray:
        """Apply chain of effects"""
        processed = audio_data.copy()

        for effect in effect_chain:
            if effect.get("enabled", True):
                effect_id = effect.get("id")
                parameters = effect.get("parameters", {})
                wet_level = effect.get("wet_level", 1.0)
                dry_level = effect.get("dry_level", 0.0)

                # Apply effect
                wet_signal = self.apply_effect(processed, effect_id, parameters)

                # Mix wet and dry
                processed = wet_signal * wet_level + processed * dry_level

        return processed

    def export_effect_preset(self, effect_id: str, parameters: Dict[str, float],
                           preset_name: str) -> Dict[str, Any]:
        """Export effect preset"""
        return {
            "preset_name": preset_name,
            "effect_id": effect_id,
            "parameters": parameters,
            "timestamp": __import__('time').time()
        }

    def import_effect_preset(self, preset_data: Dict[str, Any]) -> bool:
        """Import effect preset"""
        try:
            effect_id = preset_data.get("effect_id")
            parameters = preset_data.get("parameters", {})

            # Validate effect exists
            available_effects = self.get_available_effects()
            if effect_id not in available_effects:
                print(f"Unknown effect in preset: {effect_id}")
                return False

            # Validate parameters
            effect_def = available_effects[effect_id]
            for param_name, param_value in parameters.items():
                if param_name in effect_def.parameters:
                    param_def = effect_def.parameters[param_name]
                    # Validate parameter range
                    if param_def.min_value <= param_value <= param_def.max_value:
                        continue
                    else:
                        print(f"Parameter {param_name} value out of range")
                        return False

            return True

        except Exception as e:
            print(f"Error importing preset: {e}")
            return False

    def get_effect_recommendations(self, audio_data: np.ndarray) -> Dict[str, float]:
        """Get recommended effect settings based on audio analysis"""
        recommendations = {}

        try:
            # Analyze audio characteristics
            rms_level = np.sqrt(np.mean(audio_data ** 2))
            peak_level = np.max(np.abs(audio_data))
            crest_factor = peak_level / rms_level if rms_level > 0 else 1.0

            # Frequency analysis
            if len(audio_data.shape) > 1 and audio_data.shape[0] >= 2:
                # For stereo, analyze mid channel
                mid = (audio_data[0] + audio_data[1]) / 2
            else:
                mid = audio_data

            # Simple frequency analysis
            fft_result = np.fft.fft(mid)
            magnitude = np.abs(fft_result[:len(fft_result)//2])
            freqs = np.fft.fftfreq(len(mid), 1/self.sample_rate)[:len(fft_result)//2]

            # High frequency content analysis
            high_freq_mask = freqs > 3000
            high_freq_energy = np.mean(magnitude[high_freq_mask]) if np.any(high_freq_mask) else 0
            total_energy = np.mean(magnitude)
            high_freq_ratio = high_freq_energy / total_energy if total_energy > 0 else 0

            # Generate recommendations
            if crest_factor > 10:  # High dynamic range
                recommendations["multiband_compressor_threshold"] = -15.0
                recommendations["multiband_compressor_ratio"] = 3.0
                recommendations["multiband_compressor_makeup_gain"] = 3.0

            if high_freq_ratio > 0.3:  # Bright audio
                recommendations["deesser_threshold"] = -18.0
                recommendations["deesser_frequency"] = 4500.0

            if len(audio_data.shape) > 1 and audio_data.shape[0] >= 2:
                # Check stereo width
                correlation = np.corrcoef(audio_data[0], audio_data[1])[0, 1]
                if abs(correlation) < 0.7:  # Wide stereo
                    recommendations["stereo_enhancer_width"] = 1.2
                else:  # Narrow stereo
                    recommendations["stereo_enhancer_width"] = 1.5

        except Exception as e:
            print(f"Error generating recommendations: {e}")

        return recommendations