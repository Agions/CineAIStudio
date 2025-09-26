"""
Real-time Audio Processing Engine for CineAIStudio
Provides low-latency real-time audio processing with professional quality
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import threading
import queue
import time
import asyncio
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    sd = None
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
import librosa
import soundfile as sf
from scipy import signal
from scipy.signal import butter, filtfilt, lfilter, sosfilt
try:
    import numba as nb
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    nb = None
from concurrent.futures import ThreadPoolExecutor
import warnings
warnings.filterwarnings('ignore')

# Import audio components
from app.audio.processing.professional_audio_engine import (
    AudioRestorationEngine, SpatialAudioProcessor, AudioVideoSynchronizer
)


class LatencyMode(Enum):
    """Audio processing latency modes"""
    ULTRA_LOW = "ultra_low"    # < 5ms
    LOW = "low"                # < 10ms
    MEDIUM = "medium"          # < 20ms
    HIGH = "high"              # < 50ms


class ProcessingPriority(Enum):
    """Processing priority levels"""
    CRITICAL = 0    # Real-time monitoring, effects
    HIGH = 1        # Main audio processing
    MEDIUM = 2      # Analysis, metering
    LOW = 3         # Background tasks


@dataclass
class AudioBuffer:
    """Real-time audio buffer"""
    data: np.ndarray
    sample_rate: int
    channels: int
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProcessingChain:
    """Audio processing chain configuration"""
    id: str
    name: str
    effects: List[Dict[str, Any]]
    enabled: bool = True
    priority: ProcessingPriority = ProcessingPriority.MEDIUM
    latency_mode: LatencyMode = LatencyMode.MEDIUM


class LowLatencyBuffer:
    """Low-latency circular buffer for real-time audio"""

    def __init__(self, size: int, channels: int, dtype: np.dtype = np.float32):
        self.size = size
        self.channels = channels
        self.dtype = dtype
        self.buffer = np.zeros((size, channels), dtype=dtype)
        self.write_pos = 0
        self.read_pos = 0
        self.available = 0
        self.lock = threading.Lock()

    def write(self, data: np.ndarray):
        """Write data to buffer"""
        with self.lock:
            samples = data.shape[0]
            if samples > self.size:
                # Buffer overflow, write latest samples
                data = data[-self.size:]
                samples = self.size

            # Calculate available space
            available_space = self.size - self.available

            if samples > available_space:
                # Overwrite oldest data
                self.read_pos = (self.read_pos + samples - available_space) % self.size
                self.available = self.size

            # Write data
            end_pos = min(self.write_pos + samples, self.size)
            chunk1_size = end_pos - self.write_pos
            chunk2_size = samples - chunk1_size

            self.buffer[self.write_pos:end_pos] = data[:chunk1_size]

            if chunk2_size > 0:
                self.buffer[:chunk2_size] = data[chunk1_size:]

            self.write_pos = (self.write_pos + samples) % self.size
            self.available = min(self.available + samples, self.size)

    def read(self, samples: int) -> np.ndarray:
        """Read data from buffer"""
        with self.lock:
            samples = min(samples, self.available)

            if samples == 0:
                return np.zeros((0, self.channels), dtype=self.dtype)

            end_pos = min(self.read_pos + samples, self.size)
            chunk1_size = end_pos - self.read_pos
            chunk2_size = samples - chunk1_size

            data = np.zeros((samples, self.channels), dtype=self.dtype)

            data[:chunk1_size] = self.buffer[self.read_pos:end_pos]

            if chunk2_size > 0:
                data[chunk1_size:] = self.buffer[:chunk2_size]

            self.read_pos = (self.read_pos + samples) % self.size
            self.available -= samples

            return data

    def clear(self):
        """Clear buffer"""
        with self.lock:
            self.buffer.fill(0)
            self.write_pos = 0
            self.read_pos = 0
            self.available = 0

    def get_available(self) -> int:
        """Get available samples"""
        with self.lock:
            return self.available

    def get_space(self) -> int:
        """Get available space"""
        with self.lock:
            return self.size - self.available


class RealTimeEffect:
    """Base class for real-time audio effects"""

    def __init__(self, sample_rate: int, buffer_size: int):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.enabled = True
        self.bypass = False
        self.dry_wet = 1.0  # 0.0 = dry, 1.0 = wet
        self.parameters = {}

    def process(self, audio_data: np.ndarray) -> np.ndarray:
        """Process audio data"""
        if self.bypass or not self.enabled:
            return audio_data

        processed = self._process_internal(audio_data)

        # Apply dry/wet mix
        if self.dry_wet < 1.0:
            processed = processed * self.dry_wet + audio_data * (1.0 - self.dry_wet)

        return processed

    def _process_internal(self, audio_data: np.ndarray) -> np.ndarray:
        """Internal processing method (to be overridden)"""
        return audio_data

    def set_parameter(self, name: str, value: float):
        """Set effect parameter"""
        self.parameters[name] = value
        self._update_parameters()

    def _update_parameters(self):
        """Update internal parameters (to be overridden)"""
        pass

    def reset(self):
        """Reset effect state"""
        pass


class RealTimeCompressor(RealTimeEffect):
    """Real-time compressor with smooth envelope following"""

    def __init__(self, sample_rate: int, buffer_size: int):
        super().__init__(sample_rate, buffer_size)

        # Default parameters
        self.threshold = -20.0  # dB
        self.ratio = 4.0
        self.attack_time = 0.003  # seconds
        self.release_time = 0.1   # seconds
        self.makeup_gain = 0.0    # dB
        self.knee_width = 6.0     # dB

        # State variables
        self.envelope = 0.0
        self.gain_reduction = 0.0

        # Pre-calculate coefficients
        self._update_coefficients()

    def _update_coefficients(self):
        """Update filter coefficients"""
        self.attack_coeff = 1.0 - np.exp(-1.0 / (self.attack_time * self.sample_rate))
        self.release_coeff = 1.0 - np.exp(-1.0 / (self.release_time * self.sample_rate))

    def _update_parameters(self):
        """Update parameters"""
        self.threshold = self.parameters.get('threshold', self.threshold)
        self.ratio = self.parameters.get('ratio', self.ratio)
        self.attack_time = self.parameters.get('attack_time', self.attack_time)
        self.release_time = self.parameters.get('release_time', self.release_time)
        self.makeup_gain = self.parameters.get('makeup_gain', self.makeup_gain)
        self.knee_width = self.parameters.get('knee_width', self.knee_width)
        self._update_coefficients()

    @nb.jit(nopython=True)
    def _compressor_curve(self, input_db: float, threshold: float, ratio: float,
                         knee_width: float) -> float:
        """Calculate compressor gain reduction (optimized with numba)"""
        if input_db < threshold - knee_width/2:
            return 0.0
        elif input_db > threshold + knee_width/2:
            return (input_db - threshold) * (1.0 - 1.0/ratio)
        else:
            knee_pos = (input_db - (threshold - knee_width/2)) / knee_width
            return knee_pos * (input_db - threshold) * (1.0 - 1.0/ratio) * 0.5

    def _process_internal(self, audio_data: np.ndarray) -> np.ndarray:
        """Process audio with compression"""
        # Calculate input level
        input_level = np.abs(audio_data)
        input_db = 20 * np.log10(input_level + 1e-10)

        # Calculate envelope
        envelope = np.zeros_like(input_level)
        envelope[0] = self.envelope

        for i in range(1, len(input_level)):
            if input_level[i] > envelope[i-1]:
                envelope[i] = self.attack_coeff * input_level[i] + (1 - self.attack_coeff) * envelope[i-1]
            else:
                envelope[i] = self.release_coeff * input_level[i] + (1 - self.release_coeff) * envelope[i-1]

        self.envelope = envelope[-1]

        # Calculate gain reduction
        envelope_db = 20 * np.log10(envelope + 1e-10)
        gain_reduction_db = np.array([
            self._compressor_curve(db, self.threshold, self.ratio, self.knee_width)
            for db in envelope_db
        ])

        self.gain_reduction = np.mean(gain_reduction_db)

        # Apply gain reduction
        gain_linear = 10 ** (-gain_reduction_db / 20)
        processed = audio_data * gain_linear

        # Apply makeup gain
        makeup_linear = 10 ** (self.makeup_gain / 20)
        processed *= makeup_linear

        return processed


class RealTimeEqualizer(RealTimeEffect):
    """Real-time parametric equalizer with multiple bands"""

    def __init__(self, sample_rate: int, buffer_size: int):
        super().__init__(sample_rate, buffer_size)

        # EQ bands (Low, Low-Mid, Mid, High-Mid, High)
        self.bands = [
            {"freq": 100, "q": 0.7, "gain": 0.0, "type": "low_shelf"},
            {"freq": 350, "q": 1.0, "gain": 0.0, "type": "peaking"},
            {"freq": 1000, "q": 1.0, "gain": 0.0, "type": "peaking"},
            {"freq": 3500, "q": 1.0, "gain": 0.0, "type": "peaking"},
            {"freq": 10000, "q": 0.7, "gain": 0.0, "type": "high_shelf"}
        ]

        # Filter states
        self.filter_states = [np.zeros(4) for _ in self.bands]

    def _create_filter_coefficients(self, band: Dict) -> Tuple[np.ndarray, np.ndarray]:
        """Create filter coefficients for EQ band"""
        freq = band["freq"]
        q = band["q"]
        gain = band["gain"]
        filter_type = band["type"]

        nyquist = self.sample_rate / 2
        w0 = 2 * np.pi * freq / self.sample_rate
        alpha = np.sin(w0) / (2 * q)
        A = 10 ** (gain / 40)

        if filter_type == "peaking":
            b0 = 1 + alpha * A
            b1 = -2 * np.cos(w0)
            b2 = 1 - alpha * A
            a0 = 1 + alpha / A
            a1 = -2 * np.cos(w0)
            a2 = 1 - alpha / A
        elif filter_type == "low_shelf":
            b0 = A * ((A + 1) - (A - 1) * np.cos(w0) + 2 * np.sqrt(A) * alpha)
            b1 = 2 * A * ((A - 1) - (A + 1) * np.cos(w0))
            b2 = A * ((A + 1) - (A - 1) * np.cos(w0) - 2 * np.sqrt(A) * alpha)
            a0 = (A + 1) + (A - 1) * np.cos(w0) + 2 * np.sqrt(A) * alpha
            a1 = -2 * ((A - 1) + (A + 1) * np.cos(w0))
            a2 = (A + 1) + (A - 1) * np.cos(w0) - 2 * np.sqrt(A) * alpha
        elif filter_type == "high_shelf":
            b0 = A * ((A + 1) + (A - 1) * np.cos(w0) + 2 * np.sqrt(A) * alpha)
            b1 = -2 * A * ((A - 1) + (A + 1) * np.cos(w0))
            b2 = A * ((A + 1) + (A - 1) * np.cos(w0) - 2 * np.sqrt(A) * alpha)
            a0 = (A + 1) - (A - 1) * np.cos(w0) + 2 * np.sqrt(A) * alpha
            a1 = 2 * ((A - 1) - (A + 1) * np.cos(w0))
            a2 = (A + 1) - (A - 1) * np.cos(w0) - 2 * np.sqrt(A) * alpha

        # Normalize
        b = np.array([b0, b1, b2]) / a0
        a = np.array([a0, a1, a2]) / a0

        return b, a

    def _process_internal(self, audio_data: np.ndarray) -> np.ndarray:
        """Process audio through EQ"""
        processed = audio_data.copy()

        for i, band in enumerate(self.bands):
            if abs(band["gain"]) > 0.1:  # Only process if gain is significant
                b, a = self._create_filter_coefficients(band)

                # Use SOS filtering for stability
                sos = np.array([[b[0], b[1], b[2], a[0], a[1], a[2]]])
                processed, self.filter_states[i] = sosfilt(sos, processed, zi=self.filter_states[i])

        return processed

    def set_band_gain(self, band_index: int, gain_db: float):
        """Set gain for specific EQ band"""
        if 0 <= band_index < len(self.bands):
            self.bands[band_index]["gain"] = gain_db

    def _update_parameters(self):
        """Update EQ parameters"""
        for i, band in enumerate(self.bands):
            param_name = f"band_{i}_gain"
            if param_name in self.parameters:
                self.bands[i]["gain"] = self.parameters[param_name]


class RealTimeLimiter(RealTimeEffect):
    """Real-time peak limiter for preventing clipping"""

    def __init__(self, sample_rate: int, buffer_size: int):
        super().__init__(sample_rate, buffer_size)

        self.threshold = -1.0  # dB
        self.attack_time = 0.001  # 1ms
        self.release_time = 0.01   # 10ms
        self.lookahead = 0.003     # 3ms

        # State variables
        self.gain = 1.0
        self.lookahead_buffer = np.zeros(int(self.lookahead * sample_rate))

        self._update_coefficients()

    def _update_coefficients(self):
        """Update filter coefficients"""
        self.attack_coeff = 1.0 - np.exp(-1.0 / (self.attack_time * self.sample_rate))
        self.release_coeff = 1.0 - np.exp(-1.0 / (self.release_time * self.sample_rate))

    def _update_parameters(self):
        """Update parameters"""
        self.threshold = self.parameters.get('threshold', self.threshold)
        self.attack_time = self.parameters.get('attack_time', self.attack_time)
        self.release_time = self.parameters.get('release_time', self.release_time)
        self.lookahead = self.parameters.get('lookahead', self.lookahead)
        self._update_coefficients()

    def _process_internal(self, audio_data: np.ndarray) -> np.ndarray:
        """Process audio with lookahead limiting"""
        # Add to lookahead buffer
        lookahead_size = len(self.lookahead_buffer)
        input_with_lookahead = np.concatenate([self.lookahead_buffer, audio_data])

        # Calculate peak levels
        peak_levels = np.max(np.abs(input_with_lookahead), axis=-1)

        # Calculate required gain
        threshold_linear = 10 ** (self.threshold / 20)
        required_gain = threshold_linear / np.maximum(peak_levels, threshold_linear)

        # Apply envelope following
        gain = np.zeros_like(required_gain)
        gain[0] = self.gain

        for i in range(1, len(required_gain)):
            if required_gain[i] < gain[i-1]:  # Attack
                gain[i] = self.attack_coeff * required_gain[i] + (1 - self.attack_coeff) * gain[i-1]
            else:  # Release
                gain[i] = self.release_coeff * required_gain[i] + (1 - self.release_coeff) * gain[i-1]

        self.gain = gain[-1]

        # Apply gain to audio (skip lookahead portion)
        processed_gain = gain[lookahead_size:]
        processed = audio_data * processed_gain[:, np.newaxis] if len(audio_data.shape) > 1 else audio_data * processed_gain

        # Update lookahead buffer
        if len(audio_data) >= lookahead_size:
            self.lookahead_buffer = audio_data[-lookahead_size:]
        else:
            self.lookahead_buffer = np.concatenate([self.lookahead_buffer[len(audio_data):], audio_data])

        return processed


class RealTimeNoiseGate(RealTimeEffect):
    """Real-time noise gate for removing low-level noise"""

    def __init__(self, sample_rate: int, buffer_size: int):
        super().__init__(sample_rate, buffer_size)

        self.threshold = -40.0  # dB
        self.attack_time = 0.001  # 1ms
        self.release_time = 0.1   # 100ms
        self.hold_time = 0.05     # 50ms
        self.range = -60.0        # dB reduction when closed

        # State variables
        self.gain = 1.0
        self.hold_counter = 0

        self._update_coefficients()

    def _update_coefficients(self):
        """Update filter coefficients"""
        self.attack_coeff = 1.0 - np.exp(-1.0 / (self.attack_time * self.sample_rate))
        self.release_coeff = 1.0 - np.exp(-1.0 / (self.release_time * self.sample_rate))
        self.hold_samples = int(self.hold_time * self.sample_rate)

    def _update_parameters(self):
        """Update parameters"""
        self.threshold = self.parameters.get('threshold', self.threshold)
        self.attack_time = self.parameters.get('attack_time', self.attack_time)
        self.release_time = self.parameters.get('release_time', self.release_time)
        self.hold_time = self.parameters.get('hold_time', self.hold_time)
        self.range = self.parameters.get('range', self.range)
        self._update_coefficients()

    def _process_internal(self, audio_data: np.ndarray) -> np.ndarray:
        """Process audio with noise gate"""
        # Calculate input level
        input_level = np.max(np.abs(audio_data))
        input_db = 20 * np.log10(input_level + 1e-10)

        # Determine if gate should be open or closed
        gate_open = input_db > self.threshold

        # Calculate target gain
        if gate_open:
            target_gain = 1.0
            self.hold_counter = 0
        else:
            if self.hold_counter < self.hold_samples:
                target_gain = 1.0
                self.hold_counter += 1
            else:
                target_gain = 10 ** (self.range / 20)

        # Apply envelope following
        if target_gain < self.gain:  # Attack
            self.gain = self.attack_coeff * target_gain + (1 - self.attack_coeff) * self.gain
        else:  # Release
            self.gain = self.release_coeff * target_gain + (1 - self.release_coeff) * self.gain

        # Apply gain
        processed = audio_data * self.gain

        return processed


class AudioProcessingPipeline:
    """Real-time audio processing pipeline with multiple chains"""

    def __init__(self, sample_rate: int, buffer_size: int):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size

        # Processing chains
        self.chains: Dict[str, ProcessingChain] = {}
        self.effects: Dict[str, RealTimeEffect] = {}

        # Input and output buffers
        self.input_buffer = LowLatencyBuffer(buffer_size * 4, 2)  # 4x buffer size
        self.output_buffer = LowLatencyBuffer(buffer_size * 4, 2)

        # Processing state
        self.processing_enabled = True
        self.latency_mode = LatencyMode.MEDIUM

        # Performance monitoring
        self.processing_times = []
        self.overload_count = 0

    def add_chain(self, chain: ProcessingChain):
        """Add processing chain"""
        self.chains[chain.id] = chain

        # Create effects for this chain
        chain_effects = []
        for effect_config in chain.effects:
            effect = self._create_effect(effect_config)
            chain_effects.append(effect)

        self.effects[chain.id] = chain_effects

    def remove_chain(self, chain_id: str):
        """Remove processing chain"""
        if chain_id in self.chains:
            del self.chains[chain_id]
            if chain_id in self.effects:
                del self.effects[chain_id]

    def _create_effect(self, effect_config: Dict[str, Any]) -> RealTimeEffect:
        """Create real-time effect from configuration"""
        effect_type = effect_config.get("type")

        if effect_type == "compressor":
            effect = RealTimeCompressor(self.sample_rate, self.buffer_size)
        elif effect_type == "equalizer":
            effect = RealTimeEqualizer(self.sample_rate, self.buffer_size)
        elif effect_type == "limiter":
            effect = RealTimeLimiter(self.sample_rate, self.buffer_size)
        elif effect_type == "noise_gate":
            effect = RealTimeNoiseGate(self.sample_rate, self.buffer_size)
        else:
            effect = RealTimeEffect(self.sample_rate, self.buffer_size)

        # Set parameters
        for param_name, param_value in effect_config.get("parameters", {}).items():
            effect.set_parameter(param_name, param_value)

        return effect

    def process_audio(self, input_data: np.ndarray) -> np.ndarray:
        """Process audio through all enabled chains"""
        start_time = time.time()

        if not self.processing_enabled:
            return input_data

        processed_data = input_data.copy()

        # Process each chain
        for chain_id, chain in self.chains.items():
            if chain.enabled:
                chain_data = processed_data.copy()

                # Apply effects in chain
                for effect in self.effects.get(chain_id, []):
                    chain_data = effect.process(chain_data)

                # Mix with previous result
                processed_data = processed_data * 0.5 + chain_data * 0.5

        # Monitor performance
        processing_time = time.time() - start_time
        self.processing_times.append(processing_time)

        # Check for overload
        max_latency = self._get_max_latency()
        if processing_time > max_latency:
            self.overload_count += 1

        return processed_data

    def _get_max_latency(self) -> float:
        """Get maximum allowed latency based on mode"""
        if self.latency_mode == LatencyMode.ULTRA_LOW:
            return 0.005  # 5ms
        elif self.latency_mode == LatencyMode.LOW:
            return 0.010  # 10ms
        elif self.latency_mode == LatencyMode.MEDIUM:
            return 0.020  # 20ms
        else:
            return 0.050  # 50ms

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        if not self.processing_times:
            return {"average_processing_time": 0.0, "max_processing_time": 0.0, "overload_count": 0}

        return {
            "average_processing_time": np.mean(self.processing_times),
            "max_processing_time": np.max(self.processing_times),
            "min_processing_time": np.min(self.processing_times),
            "overload_count": self.overload_count,
            "latency_mode": self.latency_mode.value,
            "buffer_size": self.buffer_size,
            "sample_rate": self.sample_rate
        }


class RealTimeAudioProcessor(QObject):
    """Real-time audio processing system"""

    # Signals
    audio_processed = pyqtSignal(np.ndarray)  # Processed audio data
    level_updated = pyqtSignal(dict)  # Audio levels
    clipping_detected = pyqtSignal()  # Clipping warning
    performance_updated = pyqtSignal(dict)  # Performance metrics
    processing_started = pyqtSignal()
    processing_stopped = pyqtSignal()

    def __init__(self, sample_rate: int = 48000, buffer_size: int = 512):
        super().__init__()

        self.sample_rate = sample_rate
        self.buffer_size = buffer_size

        # Audio pipeline
        self.pipeline = AudioProcessingPipeline(sample_rate, buffer_size)

        # Audio I/O
        self.input_stream = None
        self.output_stream = None
        self.is_streaming = False

        # Processing threads
        self.processing_thread = None
        self.monitor_thread = None

        # Monitoring
        self.level_history = []
        self.clipping_threshold = 0.95

        # Setup default processing chains
        self._setup_default_chains()

    def _setup_default_chains(self):
        """Setup default processing chains"""
        # Monitoring chain (low latency)
        monitor_chain = ProcessingChain(
            id="monitor",
            name="Monitoring",
            effects=[
                {"type": "limiter", "parameters": {"threshold": -1.0, "attack_time": 0.001}}
            ],
            priority=ProcessingPriority.CRITICAL,
            latency_mode=LatencyMode.ULTRA_LOW
        )
        self.pipeline.add_chain(monitor_chain)

        # Main processing chain
        main_chain = ProcessingChain(
            id="main",
            name="Main Processing",
            effects=[
                {"type": "noise_gate", "parameters": {"threshold": -40.0}},
                {"type": "equalizer", "parameters": {"band_0_gain": 2.0, "band_4_gain": -1.0}},
                {"type": "compressor", "parameters": {"threshold": -18.0, "ratio": 3.0}}
            ],
            priority=ProcessingPriority.HIGH,
            latency_mode=LatencyMode.LOW
        )
        self.pipeline.add_chain(main_chain)

    def start_streaming(self, input_device: Optional[int] = None,
                       output_device: Optional[int] = None):
        """Start real-time audio streaming"""
        try:
            # Setup input stream
            self.input_stream = sd.InputStream(
                device=input_device,
                channels=2,
                samplerate=self.sample_rate,
                blocksize=self.buffer_size,
                dtype=np.float32,
                callback=self._input_callback
            )

            # Setup output stream
            self.output_stream = sd.OutputStream(
                device=output_device,
                channels=2,
                samplerate=self.sample_rate,
                blocksize=self.buffer_size,
                dtype=np.float32,
                callback=self._output_callback
            )

            # Start streams
            self.input_stream.start()
            self.output_stream.start()
            self.is_streaming = True

            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()

            self.processing_started.emit()

        except Exception as e:
            print(f"Failed to start streaming: {e}")

    def stop_streaming(self):
        """Stop real-time audio streaming"""
        self.is_streaming = False

        if self.input_stream:
            self.input_stream.stop()
            self.input_stream.close()

        if self.output_stream:
            self.output_stream.stop()
            self.output_stream.close()

        self.processing_stopped.emit()

    def _input_callback(self, indata: np.ndarray, frames: int,
                        time_info: dict, status: Any) -> None:
        """Audio input callback"""
        if status and SOUNDDEVICE_AVAILABLE:
            print(f"Input stream status: {status}")

        # Add to input buffer
        self.pipeline.input_buffer.write(indata)

    def _output_callback(self, outdata: np.ndarray, frames: int,
                         time_info: dict, status: Any) -> None:
        """Audio output callback"""
        if status and SOUNDDEVICE_AVAILABLE:
            print(f"Output stream status: {status}")

        # Get processed audio
        processed = self.pipeline.output_buffer.read(frames)

        # Fill output buffer if needed
        if len(processed) < frames:
            silence = np.zeros((frames - len(processed), 2), dtype=np.float32)
            processed = np.concatenate([processed, silence])

        outdata[:] = processed

    def _monitor_loop(self):
        """Monitoring loop for levels and performance"""
        while self.is_streaming:
            try:
                # Monitor audio levels
                available_samples = self.pipeline.input_buffer.get_available()
                if available_samples >= self.buffer_size:
                    audio_chunk = self.pipeline.input_buffer.read(self.buffer_size)

                    # Calculate levels
                    peak_level = np.max(np.abs(audio_chunk))
                    rms_level = np.sqrt(np.mean(audio_chunk ** 2))

                    levels = {
                        "peak": peak_level,
                        "rms": rms_level,
                        "peak_db": 20 * np.log10(peak_level + 1e-10),
                        "rms_db": 20 * np.log10(rms_level + 1e-10)
                    }

                    self.level_history.append(levels)
                    self.level_updated.emit(levels)

                    # Check for clipping
                    if peak_level > self.clipping_threshold:
                        self.clipping_detected.emit()

                # Process audio
                if available_samples >= self.buffer_size:
                    input_chunk = self.pipeline.input_buffer.read(self.buffer_size)
                    processed = self.pipeline.process_audio(input_chunk)

                    # Send to output buffer
                    self.pipeline.output_buffer.write(processed)

                    # Emit processed audio
                    self.audio_processed.emit(processed)

                # Monitor performance
                performance = self.pipeline.get_performance_metrics()
                self.performance_updated.emit(performance)

                time.sleep(0.01)  # 10ms monitoring interval

            except Exception as e:
                print(f"Monitor loop error: {e}")

    def add_processing_chain(self, chain: ProcessingChain):
        """Add processing chain"""
        self.pipeline.add_chain(chain)

    def remove_processing_chain(self, chain_id: str):
        """Remove processing chain"""
        self.pipeline.remove_chain(chain_id)

    def set_effect_parameter(self, chain_id: str, effect_index: int,
                           parameter_name: str, value: float):
        """Set effect parameter"""
        if chain_id in self.pipeline.effects:
            effects = self.pipeline.effects[chain_id]
            if effect_index < len(effects):
                effects[effect_index].set_parameter(parameter_name, value)

    def get_available_devices(self) -> Dict[str, List[dict]]:
        """Get available audio devices"""
        try:
            devices = sd.query_devices()
            input_devices = []
            output_devices = []

            for i, device in enumerate(devices):
                device_info = {
                    "id": i,
                    "name": device['name'],
                    "channels": device['max_input_channels'] if device['max_input_channels'] > 0 else device['max_output_channels'],
                    "sample_rate": device['default_samplerate']
                }

                if device['max_input_channels'] > 0:
                    input_devices.append(device_info)
                if device['max_output_channels'] > 0:
                    output_devices.append(device_info)

            return {
                "input": input_devices,
                "output": output_devices
            }
        except Exception as e:
            print(f"Failed to query devices: {e}")
            return {"input": [], "output": []}

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        pipeline_metrics = self.pipeline.get_performance_metrics()

        # Calculate additional metrics
        if self.level_history:
            recent_levels = self.level_history[-100:]  # Last 100 measurements
            avg_peak = np.mean([level["peak"] for level in recent_levels])
            avg_rms = np.mean([level["rms"] for level in recent_levels])
        else:
            avg_peak = 0.0
            avg_rms = 0.0

        return {
            "pipeline": pipeline_metrics,
            "audio_levels": {
                "average_peak": avg_peak,
                "average_rms": avg_rms,
                "clipping_count": sum(1 for level in self.level_history if level["peak"] > self.clipping_threshold)
            },
            "system": {
                "buffer_size": self.buffer_size,
                "sample_rate": self.sample_rate,
                "is_streaming": self.is_streaming,
                "active_chains": len([c for c in self.pipeline.chains.values() if c.enabled])
            }
        }


# Example usage
if __name__ == "__main__":
    # Create real-time processor
    processor = RealTimeAudioProcessor(sample_rate=48000, buffer_size=512)

    # Get available devices
    devices = processor.get_available_devices()
    print("Available Audio Devices:")
    print(f"Input devices: {len(devices['input'])}")
    print(f"Output devices: {len(devices['output'])}")

    # Setup custom processing chain
    custom_chain = ProcessingChain(
        id="custom",
        name="Custom Chain",
        effects=[
            {"type": "compressor", "parameters": {"threshold": -15.0, "ratio": 4.0}},
            {"type": "equalizer", "parameters": {"band_2_gain": 3.0}},
            {"type": "limiter", "parameters": {"threshold": -0.5}}
        ]
    )
    processor.add_processing_chain(custom_chain)

    print("Real-time Audio Processor Ready")
    print("Press Enter to start streaming...")
    input()

    # Start streaming (would need actual audio hardware)
    # processor.start_streaming()

    print("Streaming started (simulated)")
    print("Available processing chains:")
    for chain_id, chain in processor.pipeline.chains.items():
        print(f"  - {chain.name}: {len(chain.effects)} effects")