"""
Professional Audio Analysis Module for CineAIStudio
Provides real-time audio analysis, metering, and visualization capabilities
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import time
from collections import deque
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread, pyqtSlot
import librosa
import soundfile as sf
from scipy import signal
from scipy.fft import fft, fftfreq
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import warnings
warnings.filterwarnings('ignore')


class MeterType(Enum):
    """Audio meter types"""
    PEAK = "peak"
    RMS = "rms"
    LUFS = "lufs"
    EBU = "ebu"
    TRUE_PEAK = "true_peak"


class AnalysisMode(Enum):
    """Analysis modes"""
    REALTIME = "realtime"
    OFFLINE = "offline"
    HYBRID = "hybrid"


@dataclass
class AudioMetrics:
    """Audio measurement metrics"""
    peak_level: float = -float('inf')
    rms_level: float = -float('inf')
    lufs_level: float = -float('inf')
    lra_range: float = 0.0
    max_true_peak: float = -float('inf')
    crest_factor: float = 0.0
    dynamic_range: float = 0.0
    phase_correlation: float = 1.0
    stereo_width: float = 0.0
    frequency_spectrum: np.ndarray = None
    spectrogram: np.ndarray = None


class LevelMeter:
    """Professional level meter with various measurement modes"""

    def __init__(self, sample_rate: int = 48000, buffer_size: int = 1024):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size

        # Level history for ballistics
        self.peak_history = deque(maxlen=10)
        self.rms_history = deque(maxlen=100)

        # LUFS calculation
        self.lufs_history = deque(maxlen=sample_rate * 10)  # 10 seconds
        self.gating_threshold = -70.0  # LUFS gating threshold

        # Ballistics
        self.peak_attack_time = 0.01  # 10ms
        self.peak_release_time = 1.5  # 1.5s
        self.rms_attack_time = 0.3  # 300ms
        self.rms_release_time = 1.0  # 1s

        self.current_peak = -float('inf')
        self.current_rms = -float('inf')
        self.current_lufs = -float('inf')

    def update(self, audio_data: np.ndarray) -> AudioMetrics:
        """Update meter with new audio data"""
        metrics = AudioMetrics()

        # Peak level
        peak = np.max(np.abs(audio_data))
        metrics.peak_level = self._dbfs(peak)

        # RMS level
        rms = np.sqrt(np.mean(audio_data ** 2))
        metrics.rms_level = self._dbfs(rms)

        # LUFS calculation (simplified EBU R128)
        if len(audio_data.shape) == 2 and audio_data.shape[0] >= 2:
            lufs = self._calculate_lufs(audio_data)
            metrics.lufs_level = lufs

        # True peak detection
        true_peak = self._calculate_true_peak(audio_data)
        metrics.max_true_peak = true_peak

        # Crest factor
        if rms > 0:
            metrics.crest_factor = self._dbfs(peak / rms)

        # Update with ballistics
        self._update_levels_with_ballistics(metrics)

        return metrics

    def _dbfs(self, value: float) -> float:
        """Convert linear value to dBFS"""
        return 20 * np.log10(value) if value > 0 else -float('inf')

    def _calculate_lufs(self, audio_data: np.ndarray) -> float:
        """Calculate LUFS (simplified EBU R128)"""
        # Apply K-weighting filter (simplified)
        filtered_audio = self._k_weighting_filter(audio_data)

        # Calculate mean square
        if len(filtered_audio.shape) == 2:
            # For stereo, calculate channel mean
            ms = np.mean(filtered_audio ** 2)
        else:
            ms = np.mean(filtered_audio ** 2)

        # Convert to LUFS
        lufs = -0.691 + 10 * np.log10(ms) if ms > 0 else -float('inf')

        return lufs

    def _k_weighting_filter(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply simplified K-weighting filter"""
        # High shelf filter at 2kHz (simplified)
        fs = self.sample_rate
        f0 = 2000
        Q = 0.707
        gain_db = 4.0

        # High shelf filter coefficients
        w0 = 2 * np.pi * f0 / fs
        alpha = np.sin(w0) / (2 * Q)
        A = 10 ** (gain_db / 40)

        b0 = A * ((A + 1) + (A - 1) * np.cos(w0) + 2 * np.sqrt(A) * alpha)
        b1 = -2 * A * ((A - 1) + (A + 1) * np.cos(w0))
        b2 = A * ((A + 1) + (A - 1) * np.cos(w0) - 2 * np.sqrt(A) * alpha)
        a0 = (A + 1) - (A - 1) * np.cos(w0) + 2 * np.sqrt(A) * alpha
        a1 = 2 * ((A - 1) - (A + 1) * np.cos(w0))
        a2 = (A + 1) - (A - 1) * np.cos(w0) - 2 * np.sqrt(A) * alpha

        # Normalize coefficients
        b = np.array([b0, b1, b2]) / a0
        a = np.array([a0, a1, a2]) / a0

        # Apply filter
        filtered = signal.filtfilt(b, a, audio_data, axis=0)

        return filtered

    def _calculate_true_peak(self, audio_data: np.ndarray) -> float:
        """Calculate true peak with oversampling"""
        # Oversample by 4x for true peak detection
        oversampled = signal.resample_poly(audio_data, 4, 1, axis=0)
        true_peak = np.max(np.abs(oversampled))

        return self._dbfs(true_peak)

    def _update_levels_with_ballistics(self, metrics: AudioMetrics):
        """Update levels with professional meter ballistics"""
        dt = 1.0 / self.sample_rate

        # Peak level ballistics
        if metrics.peak_level > self.current_peak:
            # Attack phase
            alpha = 1 - np.exp(-dt / self.peak_attack_time)
            self.current_peak = self.current_peak + alpha * (metrics.peak_level - self.current_peak)
        else:
            # Release phase
            alpha = 1 - np.exp(-dt / self.peak_release_time)
            self.current_peak = self.current_peak + alpha * (metrics.peak_level - self.current_peak)

        # RMS level ballistics
        if metrics.rms_level > self.current_rms:
            # Attack phase
            alpha = 1 - np.exp(-dt / self.rms_attack_time)
            self.current_rms = self.current_rms + alpha * (metrics.rms_level - self.current_rms)
        else:
            # Release phase
            alpha = 1 - np.exp(-dt / self.rms_release_time)
            self.current_rms = self.current_rms + alpha * (metrics.rms_level - self.current_rms)

        metrics.peak_level = self.current_peak
        metrics.rms_level = self.current_rms


class SpectrumAnalyzer:
    """Real-time spectrum analyzer with FFT"""

    def __init__(self, sample_rate: int = 48000, fft_size: int = 2048):
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        self.window = np.hanning(fft_size)

        # Spectrum data
        self.frequencies = fftfreq(fft_size, 1/sample_rate)[:fft_size//2]
        self.spectrum_history = deque(maxlen=100)
        self.peak_hold = np.full(fft_size//2, -float('inf'))
        self.average_spectrum = np.zeros(fft_size//2)

        # Visualization settings
        self.frequency_bands = self._create_frequency_bands()
        self.decay_rate = 0.8  # Peak hold decay

    def analyze(self, audio_data: np.ndarray) -> Dict[str, np.ndarray]:
        """Analyze audio spectrum"""
        # Ensure correct length
        if len(audio_data) < self.fft_size:
            # Pad with zeros
            padded = np.zeros(self.fft_size)
            padded[:len(audio_data)] = audio_data
            audio_data = padded
        else:
            audio_data = audio_data[:self.fft_size]

        # Apply window
        windowed = audio_data * self.window

        # FFT
        fft_result = fft(windowed)
        magnitude = np.abs(fft_result[:self.fft_size//2])

        # Convert to dB
        spectrum_db = 20 * np.log10(magnitude + 1e-10)

        # Update peak hold
        self.peak_hold = np.maximum(self.peak_hold * self.decay_rate, spectrum_db)

        # Update average
        self.average_spectrum = self.average_spectrum * 0.9 + spectrum_db * 0.1

        # Store history
        self.spectrum_history.append(spectrum_db.copy())

        return {
            "spectrum": spectrum_db,
            "peak_hold": self.peak_hold.copy(),
            "average": self.average_spectrum.copy(),
            "frequencies": self.frequencies.copy()
        }

    def _create_frequency_bands(self) -> List[Dict[str, Any]]:
        """Create standard frequency bands for analysis"""
        bands = [
            {"name": "Sub Bass", "range": (20, 60), "color": "#FF0000"},
            {"name": "Bass", "range": (60, 250), "color": "#FF7F00"},
            {"name": "Low Mid", "range": (250, 500), "color": "#FFFF00"},
            {"name": "Mid", "range": (500, 2000), "color": "#00FF00"},
            {"name": "High Mid", "range": (2000, 4000), "color": "#0000FF"},
            {"name": "High", "range": (4000, 6000), "color": "#4B0082"},
            {"name": "Ultra High", "range": (6000, 20000), "color": "#9400D3"}
        ]

        return bands

    def get_frequency_band_energy(self, spectrum: np.ndarray) -> Dict[str, float]:
        """Get energy in each frequency band"""
        band_energies = {}

        for band in self.frequency_bands:
            low, high = band["range"]

            # Find frequency indices
            low_idx = np.argmin(np.abs(self.frequencies - low))
            high_idx = np.argmin(np.abs(self.frequencies - high))

            # Calculate energy in band
            band_energy = np.mean(spectrum[low_idx:high_idx])
            band_energies[band["name"]] = band_energy

        return band_energies

    def get_spectral_centroid(self, spectrum: np.ndarray) -> float:
        """Calculate spectral centroid (brightness)"""
        magnitude = 10 ** (spectrum / 20)  # Convert dB to magnitude
        total_energy = np.sum(magnitude)

        if total_energy > 0:
            centroid = np.sum(self.frequencies * magnitude) / total_energy
            return centroid
        return 0.0

    def get_spectral_entropy(self, spectrum: np.ndarray) -> float:
        """Calculate spectral entropy (complexity)"""
        magnitude = 10 ** (spectrum / 20)  # Convert dB to magnitude
        magnitude = magnitude / np.sum(magnitude)  # Normalize

        # Remove zeros to avoid log(0)
        magnitude = magnitude[magnitude > 0]

        if len(magnitude) > 0:
            entropy = -np.sum(magnitude * np.log2(magnitude))
            return entropy
        return 0.0


class PhaseMeter:
    """Phase correlation meter for stereo analysis"""

    def __init__(self, sample_rate: int = 48000, buffer_size: int = 1024):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size

        # Phase history
        self.phase_history = deque(maxlen=100)
        self.correlation_history = deque(maxlen=100)

    def analyze(self, audio_data: np.ndarray) -> Dict[str, float]:
        """Analyze phase correlation"""
        if len(audio_data.shape) < 2 or audio_data.shape[0] < 2:
            return {"correlation": 1.0, "phase_difference": 0.0}

        left_channel = audio_data[0]
        right_channel = audio_data[1]

        # Phase correlation
        correlation = np.corrcoef(left_channel, right_channel)[0, 1]
        if np.isnan(correlation):
            correlation = 1.0

        # Phase difference
        left_fft = np.fft.fft(left_channel)
        right_fft = np.fft.fft(right_channel)

        phase_diff = np.angle(right_fft) - np.angle(left_fft)
        mean_phase_diff = np.mean(phase_diff)

        # Store history
        self.correlation_history.append(correlation)
        self.phase_history.append(mean_phase_diff)

        return {
            "correlation": correlation,
            "phase_difference": mean_phase_diff,
            "stereo_width": 1.0 - abs(correlation)
        }

    def get_phase_warnings(self) -> List[str]:
        """Get phase-related warnings"""
        warnings = []

        if len(self.correlation_history) > 0:
            avg_correlation = np.mean(list(self.correlation_history))

            if avg_correlation < -0.5:
                warnings.append("Phase inversion detected")
            elif avg_correlation < 0.0:
                warnings.append("Poor phase correlation")

        return warnings


class AudioAnalyzer(QObject):
    """Comprehensive audio analysis system"""

    # Signals
    levels_updated = pyqtSignal(dict)  # Level data
    spectrum_updated = pyqtSignal(dict)  # Spectrum data
    phase_updated = pyqtSignal(dict)  # Phase data
    metrics_updated = pyqtSignal(object)  # AudioMetrics
    analysis_complete = pyqtSignal(dict)  # Complete analysis results
    warning_detected = pyqtSignal(str)  # Warning message

    def __init__(self, sample_rate: int = 48000, buffer_size: int = 1024):
        super().__init__()

        self.sample_rate = sample_rate
        self.buffer_size = buffer_size

        # Analysis components
        self.level_meter = LevelMeter(sample_rate, buffer_size)
        self.spectrum_analyzer = SpectrumAnalyzer(sample_rate, buffer_size)
        self.phase_meter = PhaseMeter(sample_rate, buffer_size)

        # Analysis state
        self.is_analyzing = False
        self.analysis_mode = AnalysisMode.REALTIME
        self.update_interval = 50  # ms

        # Timer for real-time analysis
        self.analysis_timer = QTimer()
        self.analysis_timer.timeout.connect(self._perform_analysis)

        # Current audio data
        self.current_audio_data = None
        self.audio_buffer = deque(maxlen=buffer_size * 10)

        # Metrics history
        self.metrics_history = deque(maxlen=1000)

    def start_analysis(self, mode: AnalysisMode = AnalysisMode.REALTIME):
        """Start audio analysis"""
        self.analysis_mode = mode
        self.is_analyzing = True

        if mode == AnalysisMode.REALTIME:
            self.analysis_timer.start(self.update_interval)

    def stop_analysis(self):
        """Stop audio analysis"""
        self.is_analyzing = False
        self.analysis_timer.stop()

    def set_audio_data(self, audio_data: np.ndarray):
        """Set audio data for analysis"""
        self.current_audio_data = audio_data

        # Add to buffer
        if len(audio_data.shape) == 1:
            # Mono
            self.audio_buffer.extend(audio_data)
        else:
            # Multi-channel - use first channel for level meter
            self.audio_buffer.extend(audio_data[0])

    def _perform_analysis(self):
        """Perform audio analysis"""
        if not self.is_analyzing or self.current_audio_data is None:
            return

        try:
            # Level analysis
            level_metrics = self.level_meter.update(self.current_audio_data)

            # Spectrum analysis
            spectrum_data = self.spectrum_analyzer.analyze(self.current_audio_data)

            # Phase analysis (if stereo)
            phase_data = self.phase_meter.analyze(self.current_audio_data)

            # Combine metrics
            level_metrics.frequency_spectrum = spectrum_data["spectrum"]
            level_metrics.phase_correlation = phase_data["correlation"]
            level_metrics.stereo_width = phase_data["stereo_width"]

            # Calculate additional metrics
            self._calculate_advanced_metrics(level_metrics)

            # Store in history
            self.metrics_history.append(level_metrics)

            # Emit signals
            self.levels_updated.emit({
                "peak": level_metrics.peak_level,
                "rms": level_metrics.rms_level,
                "lufs": level_metrics.lufs_level,
                "true_peak": level_metrics.max_true_peak
            })

            self.spectrum_updated.emit(spectrum_data)
            self.phase_updated.emit(phase_data)
            self.metrics_updated.emit(level_metrics)

            # Check for warnings
            self._check_warnings(level_metrics)

        except Exception as e:
            print(f"Error in audio analysis: {e}")

    def _calculate_advanced_metrics(self, metrics: AudioMetrics):
        """Calculate advanced audio metrics"""
        if metrics.frequency_spectrum is not None:
            # Spectral centroid
            metrics.spectral_centroid = self.spectrum_analyzer.get_spectral_centroid(
                metrics.frequency_spectrum
            )

            # Spectral entropy
            metrics.spectral_entropy = self.spectrum_analyzer.get_spectral_entropy(
                metrics.frequency_spectrum
            )

            # Frequency band energies
            metrics.band_energies = self.spectrum_analyzer.get_frequency_band_energy(
                metrics.frequency_spectrum
            )

    def _check_warnings(self, metrics: AudioMetrics):
        """Check for audio warnings"""
        warnings = []

        # Clipping detection
        if metrics.peak_level >= -0.1:
            warnings.append("Clipping detected!")

        # Low LUFS warning
        if metrics.lufs_level < -24.0:
            warnings.append("Audio level is low")

        # Phase warnings
        phase_warnings = self.phase_meter.get_phase_warnings()
        warnings.extend(phase_warnings)

        # Emit warnings
        for warning in warnings:
            self.warning_detected.emit(warning)

    def analyze_file(self, file_path: str) -> AudioMetrics:
        """Analyze audio file offline"""
        try:
            # Load audio file
            audio_data, sr = librosa.load(file_path, sr=None, mono=False)

            # Resample if necessary
            if sr != self.sample_rate:
                audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=self.sample_rate)

            # Analyze in chunks
            chunk_size = self.buffer_size
            total_metrics = []

            for i in range(0, len(audio_data[0]) if len(audio_data.shape) > 1 else len(audio_data), chunk_size):
                chunk = audio_data[:, i:i+chunk_size] if len(audio_data.shape) > 1 else audio_data[i:i+chunk_size]

                if len(chunk.shape) == 1:
                    chunk = chunk.reshape(1, -1)

                chunk_metrics = self.level_meter.update(chunk)
                total_metrics.append(chunk_metrics)

            # Calculate overall metrics
            if total_metrics:
                overall_metrics = AudioMetrics(
                    peak_level = max(m.peak_level for m in total_metrics),
                    rms_level = np.mean([m.rms_level for m in total_metrics]),
                    lufs_level = np.mean([m.lufs_level for m in total_metrics]),
                    max_true_peak = max(m.max_true_peak for m in total_metrics)
                )

                return overall_metrics

        except Exception as e:
            print(f"Error analyzing file: {e}")
            return AudioMetrics()

    def get_current_metrics(self) -> AudioMetrics:
        """Get current audio metrics"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return AudioMetrics()

    def get_average_metrics(self, duration: float = 1.0) -> AudioMetrics:
        """Get average metrics over specified duration"""
        samples_needed = int(duration * self.sample_rate / self.buffer_size)

        if len(self.metrics_history) < samples_needed:
            return AudioMetrics()

        recent_metrics = list(self.metrics_history)[-samples_needed:]

        avg_metrics = AudioMetrics(
            peak_level = np.mean([m.peak_level for m in recent_metrics]),
            rms_level = np.mean([m.rms_level for m in recent_metrics]),
            lufs_level = np.mean([m.lufs_level for m in recent_metrics]),
            max_true_peak = np.mean([m.max_true_peak for m in recent_metrics]),
            crest_factor = np.mean([m.crest_factor for m in recent_metrics]),
            phase_correlation = np.mean([m.phase_correlation for m in recent_metrics])
        )

        return avg_metrics

    def export_analysis_report(self, file_path: str, metrics: AudioMetrics = None) -> bool:
        """Export analysis report to file"""
        try:
            if metrics is None:
                metrics = self.get_average_metrics()

            report = {
                "analysis_timestamp": time.time(),
                "sample_rate": self.sample_rate,
                "buffer_size": self.buffer_size,
                "metrics": {
                    "peak_level_dbfs": metrics.peak_level,
                    "rms_level_dbfs": metrics.rms_level,
                    "lufs_level": metrics.lufs_level,
                    "true_peak_level": metrics.max_true_peak,
                    "crest_factor": metrics.crest_factor,
                    "dynamic_range": metrics.dynamic_range,
                    "phase_correlation": metrics.phase_correlation,
                    "stereo_width": metrics.stereo_width
                }
            }

            if hasattr(metrics, 'spectral_centroid'):
                report["metrics"]["spectral_centroid"] = metrics.spectral_centroid

            if hasattr(metrics, 'spectral_entropy'):
                report["metrics"]["spectral_entropy"] = metrics.spectral_entropy

            if hasattr(metrics, 'band_energies'):
                report["metrics"]["frequency_bands"] = metrics.band_energies

            with open(file_path, 'w') as f:
                import json
                json.dump(report, f, indent=2)

            return True

        except Exception as e:
            print(f"Error exporting analysis report: {e}")
            return False

    def reset_analysis(self):
        """Reset analysis state"""
        self.metrics_history.clear()
        self.audio_buffer.clear()
        self.level_meter = LevelMeter(self.sample_rate, self.buffer_size)
        self.spectrum_analyzer = SpectrumAnalyzer(self.sample_rate, self.buffer_size)
        self.phase_meter = PhaseMeter(self.sample_rate, self.buffer_size)