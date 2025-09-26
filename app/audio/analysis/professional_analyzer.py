"""
Professional Audio Analysis System for CineAIStudio
Provides comprehensive audio analysis with advanced metrics and visualization
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
from pathlib import Path
from collections import deque
import threading
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
import librosa
import soundfile as sf
from scipy import signal
from scipy.signal import butter, filtfilt, lfilter, hilbert, spectrogram
from scipy.fft import fft, ifft, fftfreq, rfft, irfft
from scipy.stats import entropy, skew, kurtosis
from scipy.ndimage import gaussian_filter1d
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Import existing components
from app.audio.analysis.audio_analyzer import AudioAnalyzer, AudioMetrics, LevelMeter, SpectrumAnalyzer, PhaseMeter


class AnalysisType(Enum):
    """Audio analysis types"""
    SPECTRAL = "spectral"
    TEMPORAL = "temporal"
    STATISTICAL = "statistical"
    PERCEPTUAL = "perceptual"
    TECHNICAL = "technical"
    COMPARATIVE = "comparative"


class MetricCategory(Enum):
    """Audio metric categories"""
    LEVEL = "level"
    DYNAMICS = "dynamics"
    SPECTRAL = "spectral"
    SPATIAL = "spatial"
    DISTORTION = "distortion"
    PERCEPTUAL = "perceptual"
    QUALITY = "quality"


@dataclass
class SpectralFeatures:
    """Comprehensive spectral analysis features"""
    spectral_centroid: float = 0.0
    spectral_bandwidth: float = 0.0
    spectral_rolloff: float = 0.0
    spectral_flatness: float = 0.0
    spectral_flux: float = 0.0
    spectral_contrast: np.ndarray = field(default_factory=lambda: np.zeros(7))
    spectral_crest: float = 0.0
    spectral_entropy: float = 0.0
    harmonic_content: float = 0.0
    inharmonicity: float = 0.0
    chroma_features: np.ndarray = field(default_factory=lambda: np.zeros(12))
    mfcc_features: np.ndarray = field(default_factory=lambda: np.zeros(13))


@dataclass
class TemporalFeatures:
    """Temporal analysis features"""
    zero_crossing_rate: float = 0.0
    onset_density: float = 0.0
    attack_time: float = 0.0
    decay_time: float = 0.0
    sustain_time: float = 0.0
    release_time: float = 0.0
    tempo: float = 0.0
    beat_strength: float = 0.0
    rhythmic_consistency: float = 0.0
    groove_consistency: float = 0.0
    transients: np.ndarray = field(default_factory=lambda: np.array([]))


@dataclass
class PerceptualFeatures:
    """Perceptual audio features"""
    loudness: float = 0.0
    sharpness: float = 0.0
    roughness: float = 0.0
    tonality: float = 0.0
    warmth: float = 0.0
    brightness: float = 0.0
    fullness: float = 0.0
    clarity: float = 0.0
    presence: float = 0.0
    air: float = 0.0
    punch: float = 0.0
    sweetness: float = 0.0
    hardness: float = 0.0


@dataclass
class TechnicalMetrics:
    """Technical audio quality metrics"""
    thd: float = 0.0  # Total Harmonic Distortion
    thd_n: float = 0.0  # THD + Noise
    snr: float = 0.0  # Signal-to-Noise Ratio
    sinad: float = 0.0  # Signal-to-Noise and Distortion
    enob: float = 0.0  # Effective Number of Bits
    sfdr: float = 0.0  # Spurious-Free Dynamic Range
    imd: float = 0.0  # Intermodulation Distortion
    phase_noise: float = 0.0
    jitter: float = 0.0
    wow_flutter: float = 0.0
    dc_offset: float = 0.0


@dataclass
class AudioQualityAssessment:
    """Comprehensive audio quality assessment"""
    overall_score: float = 0.0
    clarity_score: float = 0.0
    balance_score: float = 0.0
    dynamics_score: float = 0.0
    frequency_balance: float = 0.0
    stereo_image_score: float = 0.0
    noise_score: float = 0.0
    artifacts_score: float = 0.0
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0


class AdvancedSpectrumAnalyzer:
    """Advanced spectrum analyzer with professional features"""

    def __init__(self, sample_rate: int = 48000, fft_size: int = 8192):
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        self.window = np.blackman(fft_size)

        # Frequency resolution
        self.freq_resolution = sample_rate / fft_size

        # Analysis bands (ISO octave bands)
        self.octave_bands = self._create_octave_bands()
        self.critical_bands = self._create_critical_bands()

        # Spectral history for waterfall display
        self.spectral_history = deque(maxlen=500)
        self.peak_hold = np.zeros(fft_size // 2)
        self.average_spectrum = np.zeros(fft_size // 2)

        # Smoothing parameters
        self.spectrum_smoothing = 0.3

    def _create_octave_bands(self) -> List[Dict[str, Any]]:
        """Create ISO octave band frequencies"""
        center_freqs = [31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
        bands = []

        for cf in center_freqs:
            lower = cf / 2**(1/2)  # -3dB points
            upper = cf * 2**(1/2)
            bands.append({
                "center": cf,
                "lower": lower,
                "upper": upper,
                "bandwidth": upper - lower
            })

        return bands

    def _create_critical_bands(self) -> List[Dict[str, Any]]:
        """Create critical band frequencies (Bark scale)"""
        # Bark scale critical bands
        bark_freqs = [
            20, 100, 200, 300, 400, 510, 630, 770, 920, 1080, 1270, 1480,
            1720, 2000, 2320, 2700, 3150, 3700, 4400, 5300, 6400, 7700, 9500, 12000, 15500
        ]
        bands = []

        for i, freq in enumerate(bark_freqs[:-1]):
            bands.append({
                "bark_number": i + 1,
                "center_freq": freq,
                "upper_freq": bark_freqs[i + 1],
                "bandwidth": bark_freqs[i + 1] - freq
            })

        return bands

    def analyze_spectrum(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """Perform comprehensive spectral analysis"""
        # Ensure correct length
        if len(audio_data) < self.fft_size:
            padded = np.zeros(self.fft_size)
            padded[:len(audio_data)] = audio_data
            audio_data = padded
        else:
            audio_data = audio_data[:self.fft_size]

        # Apply window
        windowed = audio_data * self.window

        # FFT
        fft_result = fft(windowed)
        magnitude = np.abs(fft_result[:self.fft_size // 2])
        phase = np.angle(fft_result[:self.fft_size // 2])

        # Convert to dB
        magnitude_db = 20 * np.log10(magnitude + 1e-10)

        # Frequency array
        frequencies = fftfreq(self.fft_size, 1/self.sample_rate)[:self.fft_size // 2]

        # Update history
        self.spectral_history.append(magnitude_db.copy())

        # Update peak hold
        self.peak_hold = np.maximum(self.peak_hold * 0.999, magnitude_db)

        # Update average
        self.average_spectrum = self.average_spectrum * (1 - self.spectrum_smoothing) + magnitude_db * self.spectrum_smoothing

        # Calculate octave band levels
        octave_levels = self._calculate_octave_band_levels(magnitude, frequencies)

        # Calculate critical band levels
        critical_levels = self._calculate_critical_band_levels(magnitude, frequencies)

        return {
            "magnitude": magnitude_db,
            "phase": phase,
            "frequencies": frequencies,
            "peak_hold": self.peak_hold.copy(),
            "average": self.average_spectrum.copy(),
            "octave_bands": octave_levels,
            "critical_bands": critical_levels,
            "spectral_centroid": self._calculate_spectral_centroid(magnitude, frequencies),
            "spectral_bandwidth": self._calculate_spectral_bandwidth(magnitude, frequencies),
            "spectral_rolloff": self._calculate_spectral_rolloff(magnitude, frequencies)
        }

    def _calculate_octave_band_levels(self, magnitude: np.ndarray, frequencies: np.ndarray) -> Dict[str, float]:
        """Calculate octave band levels"""
        octave_levels = {}

        for band in self.octave_bands:
            lower, upper = band["lower"], band["upper"]

            # Find frequency indices
            lower_idx = np.argmin(np.abs(frequencies - lower))
            upper_idx = np.argmin(np.abs(frequencies - upper))

            # Calculate RMS level in band
            band_magnitude = magnitude[lower_idx:upper_idx]
            if len(band_magnitude) > 0:
                band_rms = np.sqrt(np.mean(band_magnitude ** 2))
                band_db = 20 * np.log10(band_rms + 1e-10)
                octave_levels[f"{band['center']}Hz"] = band_db

        return octave_levels

    def _calculate_critical_band_levels(self, magnitude: np.ndarray, frequencies: np.ndarray) -> List[float]:
        """Calculate critical band levels (Bark scale)"""
        critical_levels = []

        for band in self.critical_bands:
            lower = band["center_freq"]
            upper = band["upper_freq"]

            # Find frequency indices
            lower_idx = np.argmin(np.abs(frequencies - lower))
            upper_idx = np.argmin(np.abs(frequencies - upper))

            # Calculate energy in band
            band_magnitude = magnitude[lower_idx:upper_idx]
            if len(band_magnitude) > 0:
                band_energy = np.sum(band_magnitude ** 2)
                critical_levels.append(band_energy)
            else:
                critical_levels.append(0.0)

        return critical_levels

    def _calculate_spectral_centroid(self, magnitude: np.ndarray, frequencies: np.ndarray) -> float:
        """Calculate spectral centroid (brightness)"""
        magnitude_norm = magnitude / (np.sum(magnitude) + 1e-10)
        centroid = np.sum(frequencies * magnitude_norm)
        return centroid

    def _calculate_spectral_bandwidth(self, magnitude: np.ndarray, frequencies: np.ndarray) -> float:
        """Calculate spectral bandwidth"""
        centroid = self._calculate_spectral_centroid(magnitude, frequencies)
        magnitude_norm = magnitude / (np.sum(magnitude) + 1e-10)
        bandwidth = np.sqrt(np.sum(magnitude_norm * (frequencies - centroid) ** 2))
        return bandwidth

    def _calculate_spectral_rolloff(self, magnitude: np.ndarray, frequencies: np.ndarray, rolloff_percent: float = 0.85) -> float:
        """Calculate spectral rolloff frequency"""
        total_energy = np.sum(magnitude ** 2)
        rolloff_energy = rolloff_percent * total_energy

        cumulative_energy = np.cumsum(magnitude ** 2)
        rolloff_idx = np.argmax(cumulative_energy >= rolloff_energy)

        return frequencies[rolloff_idx] if rolloff_idx < len(frequencies) else frequencies[-1]

    def get_spectral_waterfall(self) -> np.ndarray:
        """Get spectral waterfall data"""
        if len(self.spectral_history) == 0:
            return np.array([])

        # Convert to numpy array and transpose
        waterfall = np.array(list(self.spectral_history)).T
        return waterfall


class PerceptualAnalyzer:
    """Perceptual audio analysis using psychoacoustic models"""

    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.fft_size = 2048

        # Psychoacoustic parameters
        self.absolute_threshold = self._create_absolute_threshold()
        self.critical_bands = self._create_bark_scale()
        self.equal_loudness_curve = self._create_equal_loudness_curve()

    def _create_absolute_threshold(self) -> np.ndarray:
        """Create absolute threshold of hearing curve"""
        frequencies = np.logspace(np.log10(20), np.log10(20000), 1000)
        # Threshold in quiet (approximation)
        threshold_db = 3.64 * (frequencies/1000)**(-0.8) - 6.5 * np.exp(-0.6 * (frequencies/1000 - 3.3)**2) + 10**(-3)
        return np.interp(np.arange(0, self.sample_rate//2, self.sample_rate/self.fft_size), frequencies, threshold_db)

    def _create_bark_scale(self) -> List[Dict[str, Any]]:
        """Create Bark scale for critical band analysis"""
        bark_bands = []
        for z in range(25):  # 25 critical bands
            # Bark to Hz conversion
            freq_low = 1960 * (z + 0.5) / (26.28 - z) if z < 15 else 1960 * (z + 0.5) / (26.28 - z)
            freq_high = 1960 * (z + 1.5) / (26.28 - (z + 1)) if z < 14 else 1960 * (z + 1.5) / (26.28 - (z + 1))

            bark_bands.append({
                "bark": z + 1,
                "center_freq": (freq_low + freq_high) / 2,
                "lower_freq": freq_low,
                "upper_freq": freq_high
            })

        return bark_bands

    def _create_equal_loudness_curve(self) -> np.ndarray:
        """Create equal loudness contour (Fletcher-Munson)"""
        frequencies = np.logspace(np.log10(20), np.log10(20000), 1000)
        # Approximation of equal loudness at 40 phon
        loudness_db = np.where(
            frequencies < 1000,
            20 * np.log10(frequencies / 1000) + 40,
            40
        )
        return np.interp(np.arange(0, self.sample_rate//2, self.sample_rate/self.fft_size), frequencies, loudness_db)

    def analyze_loudness(self, audio_data: np.ndarray) -> Dict[str, float]:
        """Calculate loudness metrics (EBU R128 compatible)"""
        # Apply K-weighting filter
        filtered_audio = self._apply_k_weighting(audio_data)

        # Calculate momentary loudness (400ms window)
        window_size = int(0.4 * self.sample_rate)
        momentary_loudness = []

        for i in range(0, len(filtered_audio) - window_size, window_size // 2):
            window = filtered_audio[i:i + window_size]
            loudness = self._calculate_loudness(window)
            momentary_loudness.append(loudness)

        # Calculate short-term loudness (3s window)
        short_term_window = int(3.0 * self.sample_rate)
        short_term_loudness = []

        for i in range(0, len(filtered_audio) - short_term_window, short_term_window // 4):
            window = filtered_audio[i:i + short_term_window]
            loudness = self._calculate_loudness(window)
            short_term_loudness.append(loudness)

        # Calculate integrated loudness
        integrated_loudness = self._calculate_loudness(filtered_audio)

        # Calculate loudness range
        if len(short_term_loudness) > 1:
            loudness_range = np.max(short_term_loudness) - np.min(short_term_loudness)
        else:
            loudness_range = 0.0

        return {
            "integrated": integrated_loudness,
            "momentary": np.mean(momentary_loudness) if momentary_loudness else integrated_loudness,
            "short_term": np.mean(short_term_loudness) if short_term_loudness else integrated_loudness,
            "loudness_range": loudness_range,
            "max_momentary": np.max(momentary_loudness) if momentary_loudness else integrated_loudness,
            "min_momentary": np.min(momentary_loudness) if momentary_loudness else integrated_loudness
        }

    def _apply_k_weighting(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply K-weighting filter (simplified)"""
        # High shelf filter at 2kHz
        fs = self.sample_rate
        f0 = 2000
        Q = 0.707
        gain_db = 4.0

        w0 = 2 * np.pi * f0 / fs
        alpha = np.sin(w0) / (2 * Q)
        A = 10 ** (gain_db / 40)

        b0 = A * ((A + 1) + (A - 1) * np.cos(w0) + 2 * np.sqrt(A) * alpha)
        b1 = -2 * A * ((A - 1) + (A + 1) * np.cos(w0))
        b2 = A * ((A + 1) + (A - 1) * np.cos(w0) - 2 * np.sqrt(A) * alpha)
        a0 = (A + 1) - (A - 1) * np.cos(w0) + 2 * np.sqrt(A) * alpha
        a1 = 2 * ((A - 1) - (A + 1) * np.cos(w0))
        a2 = (A + 1) - (A - 1) * np.cos(w0) - 2 * np.sqrt(A) * alpha

        b = np.array([b0, b1, b2]) / a0
        a = np.array([a0, a1, a2]) / a0

        return filtfilt(b, a, audio_data)

    def _calculate_loudness(self, audio_data: np.ndarray) -> float:
        """Calculate loudness in LUFS"""
        # Calculate mean square
        if len(audio_data.shape) > 1:
            # For stereo, calculate channel mean
            ms = np.mean(audio_data ** 2)
        else:
            ms = np.mean(audio_data ** 2)

        # Convert to LUFS
        lufs = -0.691 + 10 * np.log10(ms) if ms > 0 else -float('inf')

        return lufs

    def analyze_sharpness(self, audio_data: np.ndarray) -> float:
        """Calculate sharpness (perceived brightness)"""
        # Analyze spectral content
        spectrum_analyzer = AdvancedSpectrumAnalyzer(self.sample_rate)
        analysis = spectrum_analyzer.analyze_spectrum(audio_data)

        # Calculate sharpness based on high-frequency content
        frequencies = analysis["frequencies"]
        magnitude = 10 ** (analysis["magnitude"] / 20)  # Convert dB to linear

        # Weight high frequencies more heavily
        high_freq_mask = frequencies > 3000
        low_freq_mask = frequencies <= 3000

        high_freq_energy = np.sum(magnitude[high_freq_mask] * frequencies[high_freq_mask])
        low_freq_energy = np.sum(magnitude[low_freq_mask] * frequencies[low_freq_mask])

        sharpness = high_freq_energy / (low_freq_energy + 1e-10)
        return sharpness

    def analyze_roughness(self, audio_data: np.ndarray) -> float:
        """Calculate roughness (perceived roughness)"""
        # Roughness is related to amplitude modulation in high frequencies
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=0)  # Convert to mono

        # Envelope extraction
        envelope = np.abs(hilbert(audio_data))

        # Calculate modulation spectrum
        modulation_spectrum = np.abs(fft(envelope))
        modulation_freqs = fftfreq(len(envelope), 1/self.sample_rate)

        # Focus on modulation frequencies that cause roughness (15-300 Hz)
        roughness_mask = (modulation_freqs >= 15) & (modulation_freqs <= 300)
        roughness_energy = np.sum(modulation_spectrum[roughness_mask])

        return roughness_energy


class TechnicalAnalyzer:
    """Technical audio quality analysis"""

    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.analysis_window = 1024

    def analyze_distortion(self, audio_data: np.ndarray, fundamental_freq: float = None) -> TechnicalMetrics:
        """Analyze harmonic distortion and technical quality"""
        metrics = TechnicalMetrics()

        if fundamental_freq is None:
            # Try to detect fundamental frequency
            fundamental_freq = self._detect_fundamental_frequency(audio_data)

        if fundamental_freq is not None and fundamental_freq > 20:
            # Calculate THD
            metrics.thd = self._calculate_thd(audio_data, fundamental_freq)
            metrics.thd_n = self._calculate_thd_n(audio_data, fundamental_freq)

        # Calculate SNR
        metrics.snr = self._calculate_snr(audio_data)

        # Calculate SINAD
        metrics.sinad = self._calculate_sinad(audio_data)

        # Calculate ENOB
        metrics.enob = self._calculate_enob(metrics.sinad)

        # Calculate SFDR
        metrics.sfdr = self._calculate_sfdr(audio_data)

        # Calculate IMD
        metrics.imd = self._calculate_imd(audio_data)

        # Calculate DC offset
        metrics.dc_offset = np.mean(audio_data)

        return metrics

    def _detect_fundamental_frequency(self, audio_data: np.ndarray) -> Optional[float]:
        """Detect fundamental frequency using autocorrelation"""
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=0)  # Convert to mono

        # Autocorrelation
        autocorr = np.correlate(audio_data, audio_data, mode='full')
        autocorr = autocorr[len(autocorr)//2:]

        # Find first peak (excluding zero lag)
        min_period = int(self.sample_rate / 2000)  # Max 2kHz
        max_period = int(self.sample_rate / 80)   # Min 80Hz

        search_range = autocorr[min_period:max_period]
        if len(search_range) > 0:
            peak_idx = np.argmax(search_range) + min_period
            fundamental_freq = self.sample_rate / peak_idx
            return fundamental_freq

        return None

    def _calculate_thd(self, audio_data: np.ndarray, fundamental_freq: float) -> float:
        """Calculate Total Harmonic Distortion"""
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=0)

        # FFT
        fft_result = fft(audio_data)
        magnitude = np.abs(fft_result[:len(fft_result)//2])
        frequencies = fftfreq(len(audio_data), 1/self.sample_rate)[:len(fft_result)//2]

        # Find fundamental and harmonic peaks
        fundamental_idx = np.argmin(np.abs(frequencies - fundamental_freq))
        fundamental_magnitude = magnitude[fundamental_idx]

        # Calculate harmonic energy (2nd to 10th harmonics)
        harmonic_energy = 0.0
        for harmonic in range(2, 11):
            harmonic_freq = fundamental_freq * harmonic
            if harmonic_freq < self.sample_rate / 2:
                harmonic_idx = np.argmin(np.abs(frequencies - harmonic_freq))
                harmonic_energy += magnitude[harmonic_idx] ** 2

        # Calculate THD
        thd = np.sqrt(harmonic_energy) / fundamental_magnitude if fundamental_magnitude > 0 else 0.0
        return thd

    def _calculate_thd_n(self, audio_data: np.ndarray, fundamental_freq: float) -> float:
        """Calculate THD + Noise"""
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=0)

        # FFT
        fft_result = fft(audio_data)
        magnitude = np.abs(fft_result[:len(fft_result)//2])
        frequencies = fftfreq(len(audio_data), 1/self.sample_rate)[:len(fft_result)//2]

        # Find fundamental peak
        fundamental_idx = np.argmin(np.abs(frequencies - fundamental_freq))
        fundamental_magnitude = magnitude[fundamental_idx]

        # Calculate total energy minus fundamental
        total_energy = np.sum(magnitude ** 2) - fundamental_magnitude ** 2
        fundamental_energy = fundamental_magnitude ** 2

        thd_n = np.sqrt(total_energy) / np.sqrt(fundamental_energy) if fundamental_energy > 0 else 0.0
        return thd_n

    def _calculate_snr(self, audio_data: np.ndarray) -> float:
        """Calculate Signal-to-Noise Ratio"""
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=0)

        # Simple SNR estimation using RMS levels
        signal_rms = np.sqrt(np.mean(audio_data ** 2))

        # Estimate noise from high-frequency content
        fft_result = fft(audio_data)
        magnitude = np.abs(fft_result[:len(fft_result)//2])
        frequencies = fftfreq(len(audio_data), 1/self.sample_rate)[:len(fft_result)//2]

        # Use high frequencies as noise estimate
        noise_mask = frequencies > 10000
        if np.any(noise_mask):
            noise_magnitude = magnitude[noise_mask]
            noise_rms = np.sqrt(np.mean(noise_magnitude ** 2))
        else:
            noise_rms = signal_rms * 0.001  # Default noise floor

        snr = 20 * np.log10(signal_rms / (noise_rms + 1e-10))
        return snr

    def _calculate_sinad(self, audio_data: np.ndarray) -> float:
        """Calculate Signal-to-Noise and Distortion ratio"""
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=0)

        # SINAD is essentially the inverse of THD+N
        total_rms = np.sqrt(np.mean(audio_data ** 2))

        # Estimate noise and distortion
        fft_result = fft(audio_data)
        magnitude = np.abs(fft_result[:len(fft_result)//2])

        # Remove DC component
        magnitude[0] = 0

        # Total noise + distortion
        noise_distortion_rms = np.sqrt(np.sum(magnitude ** 2)) / len(magnitude)

        # Find fundamental
        fundamental_idx = np.argmax(magnitude)
        fundamental_magnitude = magnitude[fundamental_idx]
        fundamental_rms = fundamental_magnitude / len(magnitude)

        sinad = 20 * np.log10(fundamental_rms / (noise_distortion_rms + 1e-10))
        return sinad

    def _calculate_enob(self, sinad: float) -> float:
        """Calculate Effective Number of Bits"""
        if sinad > 0:
            enob = (sinad - 1.76) / 6.02
            return max(0, enob)
        return 0.0

    def _calculate_sfdr(self, audio_data: np.ndarray) -> float:
        """Calculate Spurious-Free Dynamic Range"""
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=0)

        # FFT
        fft_result = fft(audio_data)
        magnitude_db = 20 * np.log10(np.abs(fft_result[:len(fft_result)//2]) + 1e-10)

        # Find fundamental peak
        fundamental_level = np.max(magnitude_db)

        # Find largest spur (excluding fundamental)
        spur_level = -float('inf')
        for i, level in enumerate(magnitude_db):
            if i != np.argmax(magnitude_db) and level > spur_level:
                spur_level = level

        sfdr = fundamental_level - spur_level
        return sfdr

    def _calculate_imd(self, audio_data: np.ndarray) -> float:
        """Calculate Intermodulation Distortion"""
        # Simplified IMD calculation using two-tone test
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=0)

        # FFT
        fft_result = fft(audio_data)
        magnitude = np.abs(fft_result[:len(fft_result)//2])
        frequencies = fftfreq(len(audio_data), 1/self.sample_rate)[:len(fft_result)//2]

        # Look for intermodulation products (simplified)
        # In real implementation, would use specific test frequencies
        total_magnitude = np.sum(magnitude ** 2)
        imd_magnitude = 0.0

        # Look for sidebands (simplified approach)
        for i in range(1, len(magnitude) - 1):
            if magnitude[i] > magnitude[i-1] and magnitude[i] > magnitude[i+1]:
                # Found a peak, check if it's an intermodulation product
                freq = frequencies[i]
                if 100 < freq < 1000:  # Typical IMD product range
                    imd_magnitude += magnitude[i] ** 2

        imd = np.sqrt(imd_magnitude) / np.sqrt(total_magnitude) if total_magnitude > 0 else 0.0
        return imd


class ProfessionalAudioAnalyzer(QObject):
    """Professional comprehensive audio analyzer"""

    # Signals
    analysis_started = pyqtSignal(str)  # Analysis type
    analysis_progress = pyqtSignal(float)  # Progress 0-100
    analysis_complete = pyqtSignal(dict)  # Analysis results
    quality_assessment_complete = pyqtSignal(object)  # Quality assessment
    visualization_data_ready = pyqtSignal(dict)  # Visualization data

    def __init__(self, sample_rate: int = 48000):
        super().__init__()

        self.sample_rate = sample_rate
        self.buffer_size = 1024

        # Analyzers
        self.basic_analyzer = AudioAnalyzer(sample_rate, self.buffer_size)
        self.spectrum_analyzer = AdvancedSpectrumAnalyzer(sample_rate)
        self.perceptual_analyzer = PerceptualAnalyzer(sample_rate)
        self.technical_analyzer = TechnicalAnalyzer(sample_rate)

        # Analysis state
        self.is_analyzing = False
        self.current_analysis = None
        self.analysis_results = {}

        # Processing
        self.analysis_thread = None
        self.thread_pool = ThreadPoolExecutor(max_workers=4)

        # Real-time monitoring
        self.monitoring_enabled = False
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._update_monitoring)

    def analyze_audio_file(self, file_path: str, analysis_types: List[AnalysisType] = None) -> str:
        """Analyze audio file with comprehensive analysis"""
        if analysis_types is None:
            analysis_types = list(AnalysisType)

        try:
            # Load audio file
            audio_data, sr = librosa.load(file_path, sr=self.sample_rate, mono=False)

            # Start analysis
            analysis_id = f"analysis_{time.time()}"
            self.current_analysis = analysis_id

            # Start analysis in thread
            self.analysis_thread = threading.Thread(
                target=self._perform_comprehensive_analysis,
                args=(analysis_id, audio_data, sr, analysis_types),
                daemon=True
            )
            self.analysis_thread.start()

            return analysis_id

        except Exception as e:
            print(f"Error analyzing file: {e}")
            return None

    def _perform_comprehensive_analysis(self, analysis_id: str, audio_data: np.ndarray,
                                      sample_rate: int, analysis_types: List[AnalysisType]):
        """Perform comprehensive audio analysis"""
        self.is_analyzing = True
        self.analysis_started.emit("comprehensive")

        results = {}
        total_steps = len(analysis_types)
        current_step = 0

        try:
            for analysis_type in analysis_types:
                if analysis_type == AnalysisType.SPECTRAL:
                    results["spectral"] = self._analyze_spectral_comprehensive(audio_data, sample_rate)
                elif analysis_type == AnalysisType.TEMPORAL:
                    results["temporal"] = self._analyze_temporal_comprehensive(audio_data, sample_rate)
                elif analysis_type == AnalysisType.PERCEPTUAL:
                    results["perceptual"] = self._analyze_perceptual_comprehensive(audio_data, sample_rate)
                elif analysis_type == AnalysisType.TECHNICAL:
                    results["technical"] = self._analyze_technical_comprehensive(audio_data, sample_rate)
                elif analysis_type == AnalysisType.STATISTICAL:
                    results["statistical"] = self._analyze_statistical_comprehensive(audio_data, sample_rate)

                current_step += 1
                progress = (current_step / total_steps) * 100
                self.analysis_progress.emit(progress)

            # Quality assessment
            quality_assessment = self._assess_audio_quality(results)
            results["quality_assessment"] = quality_assessment

            self.analysis_complete.emit(results)
            self.quality_assessment_complete.emit(quality_assessment)

        except Exception as e:
            error_result = {"error": str(e), "analysis_id": analysis_id}
            self.analysis_complete.emit(error_result)

        finally:
            self.is_analyzing = False
            self.current_analysis = None

    def _analyze_spectral_comprehensive(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """Comprehensive spectral analysis"""
        # Convert to mono for spectral analysis
        if len(audio_data.shape) > 1:
            mono_audio = np.mean(audio_data, axis=0)
        else:
            mono_audio = audio_data

        # Advanced spectrum analysis
        spectrum_results = self.spectrum_analyzer.analyze_spectrum(mono_audio)

        # Calculate additional spectral features
        spectral_features = self._calculate_spectral_features(mono_audio, sample_rate)

        return {
            "spectrum": spectrum_results,
            "features": spectral_features,
            "chroma": self._analyze_chroma(mono_audio, sample_rate),
            "mfcc": self._analyze_mfcc(mono_audio, sample_rate)
        }

    def _analyze_temporal_comprehensive(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """Comprehensive temporal analysis"""
        if len(audio_data.shape) > 1:
            mono_audio = np.mean(audio_data, axis=0)
        else:
            mono_audio = audio_data

        # Onset detection
        onsets = librosa.onset.onset_detect(y=mono_audio, sr=sample_rate)

        # Tempo estimation
        tempo, beat_frames = librosa.beat.beat_track(y=mono_audio, sr=sample_rate)

        # Envelope analysis
        envelope = np.abs(librosa.amplitude_to_db(np.abs(librosa.stft(mono_audio)), ref=np.max))

        return {
            "onsets": onsets,
            "tempo": tempo,
            "beats": beat_frames,
            "envelope": envelope,
            "zero_crossing_rate": librosa.feature.zero_crossing_rate(mono_audio)[0],
            "rms_energy": librosa.feature.rms(y=mono_audio)[0]
        }

    def _analyze_perceptual_comprehensive(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """Comprehensive perceptual analysis"""
        # Loudness analysis
        loudness_metrics = self.perceptual_analyzer.analyze_loudness(audio_data)

        # Sharpness and roughness
        sharpness = self.perceptual_analyzer.analyze_sharpness(audio_data)
        roughness = self.perceptual_analyzer.analyze_roughness(audio_data)

        return {
            "loudness": loudness_metrics,
            "sharpness": sharpness,
            "roughness": roughness,
            "perceptual_features": self._calculate_perceptual_features(audio_data, sample_rate)
        }

    def _analyze_technical_comprehensive(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """Comprehensive technical analysis"""
        # Technical metrics
        technical_metrics = self.technical_analyzer.analyze_distortion(audio_data)

        # Additional technical analysis
        frequency_response = self._analyze_frequency_response(audio_data, sample_rate)
        phase_response = self._analyze_phase_response(audio_data, sample_rate)

        return {
            "distortion": technical_metrics,
            "frequency_response": frequency_response,
            "phase_response": phase_response,
            "technical_features": self._calculate_technical_features(audio_data, sample_rate)
        }

    def _analyze_statistical_comprehensive(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """Comprehensive statistical analysis"""
        if len(audio_data.shape) > 1:
            mono_audio = np.mean(audio_data, axis=0)
        else:
            mono_audio = audio_data

        # Basic statistics
        mean_val = np.mean(mono_audio)
        std_val = np.std(mono_audio)
        skewness = skew(mono_audio)
        kurt = kurtosis(mono_audio)

        # Distribution analysis
        hist, bins = np.histogram(mono_audio, bins=100, density=True)

        return {
            "statistics": {
                "mean": mean_val,
                "std": std_val,
                "skewness": skewness,
                "kurtosis": kurtosis,
                "min": np.min(mono_audio),
                "max": np.max(mono_audio),
                "range": np.max(mono_audio) - np.min(mono_audio)
            },
            "distribution": {
                "histogram": hist,
                "bins": bins,
                "entropy": entropy(hist + 1e-10)
            }
        }

    def _calculate_spectral_features(self, audio_data: np.ndarray, sample_rate: int) -> SpectralFeatures:
        """Calculate comprehensive spectral features"""
        # Extract spectral features using librosa
        spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)[0]
        spectral_bandwidths = librosa.feature.spectral_bandwidth(y=audio_data, sr=sample_rate)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=sample_rate)[0]
        spectral_flatness = librosa.feature.spectral_flatness(y=audio_data)[0]

        # Chroma features
        chroma = librosa.feature.chroma_stft(y=audio_data, sr=sample_rate)

        # MFCC features
        mfcc = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)

        # Tonnetz (tonal centroid features)
        tonnetz = librosa.feature.tonnetz(y=audio_data, sr=sample_rate)

        return SpectralFeatures(
            spectral_centroid=np.mean(spectral_centroids),
            spectral_bandwidth=np.mean(spectral_bandwidths),
            spectral_rolloff=np.mean(spectral_rolloff),
            spectral_flatness=np.mean(spectral_flatness),
            chroma_features=np.mean(chroma, axis=1),
            mfcc_features=np.mean(mfcc, axis=1)
        )

    def _calculate_perceptual_features(self, audio_data: np.ndarray, sample_rate: int) -> PerceptualFeatures:
        """Calculate perceptual features"""
        if len(audio_data.shape) > 1:
            mono_audio = np.mean(audio_data, axis=0)
        else:
            mono_audio = audio_data

        # Basic perceptual features
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=mono_audio, sr=sample_rate)[0])
        zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(mono_audio)[0])

        # Calculate perceptual attributes
        brightness = spectral_centroid / (sample_rate / 2)  # Normalized brightness
        warmth = 1.0 - brightness  # Inverse of brightness
        clarity = 1.0 / (1.0 + zero_crossing_rate)  # Inverse of noisiness

        return PerceptualFeatures(
            brightness=brightness,
            warmth=warmth,
            clarity=clarity,
            presence=np.mean(np.abs(mono_audio)),  # Signal strength
            fullness=np.std(mono_audio)  # Dynamic range indicator
        )

    def _calculate_technical_features(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """Calculate technical features"""
        if len(audio_data.shape) > 1:
            mono_audio = np.mean(audio_data, axis=0)
        else:
            mono_audio = audio_data

        # Calculate RMS levels
        rms = np.sqrt(np.mean(mono_audio ** 2))
        peak = np.max(np.abs(mono_audio))
        crest_factor = peak / rms if rms > 0 else 1.0

        # Calculate dynamic range
        dynamic_range = 20 * np.log10(peak / (rms + 1e-10))

        return {
            "rms_level": 20 * np.log10(rms + 1e-10),
            "peak_level": 20 * np.log10(peak + 1e-10),
            "crest_factor": crest_factor,
            "dynamic_range_db": dynamic_range,
            "dc_offset": np.mean(mono_audio)
        }

    def _analyze_chroma(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Analyze chroma features"""
        chroma = librosa.feature.chroma_stft(y=audio_data, sr=sample_rate)
        return np.mean(chroma, axis=1)

    def _analyze_mfcc(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Analyze MFCC features"""
        mfcc = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
        return np.mean(mfcc, axis=1)

    def _analyze_frequency_response(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, np.ndarray]:
        """Analyze frequency response"""
        if len(audio_data.shape) > 1:
            mono_audio = np.mean(audio_data, axis=0)
        else:
            mono_audio = audio_data

        # Frequency response using FFT
        fft_result = fft(mono_audio)
        magnitude = np.abs(fft_result[:len(fft_result)//2])
        frequencies = fftfreq(len(mono_audio), 1/sample_rate)[:len(fft_result)//2]

        return {
            "frequencies": frequencies,
            "magnitude_db": 20 * np.log10(magnitude + 1e-10),
            "phase": np.angle(fft_result[:len(fft_result)//2])
        }

    def _analyze_phase_response(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, np.ndarray]:
        """Analyze phase response"""
        if len(audio_data.shape) < 2 or audio_data.shape[0] < 2:
            return {"phase_coherence": np.array([]), "phase_diff": np.array([])}

        left_channel = audio_data[0]
        right_channel = audio_data[1]

        # Calculate phase difference
        left_fft = fft(left_channel)
        right_fft = fft(right_channel)

        phase_diff = np.angle(right_fft) - np.angle(left_fft)
        phase_coherence = np.cos(phase_diff)

        return {
            "phase_coherence": phase_coherence[:len(phase_diff)//2],
            "phase_diff": phase_diff[:len(phase_diff)//2]
        }

    def _assess_audio_quality(self, analysis_results: Dict[str, Any]) -> AudioQualityAssessment:
        """Assess overall audio quality"""
        assessment = AudioQualityAssessment()

        try:
            # Initialize scores
            clarity_score = 0.0
            balance_score = 0.0
            dynamics_score = 0.0
            frequency_balance = 0.0
            stereo_image_score = 0.0
            noise_score = 0.0
            artifacts_score = 0.0

            # Assess based on technical metrics
            if "technical" in analysis_results:
                tech = analysis_results["technical"]
                distortion = tech.get("distortion")

                if distortion:
                    # Clarity based on distortion
                    if distortion.thd < 0.01:  # 1% THD
                        clarity_score = 90
                    elif distortion.thd < 0.05:  # 5% THD
                        clarity_score = 70
                    else:
                        clarity_score = 50

                    # Noise score based on SNR
                    if distortion.snr > 60:
                        noise_score = 90
                    elif distortion.snr > 40:
                        noise_score = 70
                    else:
                        noise_score = 50

            # Assess based on spectral analysis
            if "spectral" in analysis_results:
                spectral = analysis_results["spectral"]

                # Frequency balance based on spectral features
                if "features" in spectral:
                    features = spectral["features"]
                    # Assess spectral balance
                    spectral_centroid = features.spectral_centroid
                    if 500 < spectral_centroid < 3000:  # Good balance
                        frequency_balance = 80
                    else:
                        frequency_balance = 60

            # Assess based on perceptual analysis
            if "perceptual" in analysis_results:
                perceptual = analysis_results["perceptual"]
                loudness = perceptual.get("loudness", {})

                # Loudness assessment
                integrated_loudness = loudness.get("integrated", -23.0)
                if -24 <= integrated_loudness <= -16:  # Good loudness range
                    balance_score = 80
                else:
                    balance_score = 60

            # Assess dynamics
            if "spectral" in analysis_results and "temporal" in analysis_results:
                # Dynamic range assessment
                crest_factor = analysis_results["spectral"].get("features", SpectralFeatures()).spectral_crest
                if crest_factor > 10:  # Good dynamics
                    dynamics_score = 80
                else:
                    dynamics_score = 60

            # Calculate overall score
            weights = {
                "clarity": 0.2,
                "balance": 0.15,
                "dynamics": 0.15,
                "frequency_balance": 0.15,
                "stereo_image": 0.1,
                "noise": 0.15,
                "artifacts": 0.1
            }

            overall_score = (
                clarity_score * weights["clarity"] +
                balance_score * weights["balance"] +
                dynamics_score * weights["dynamics"] +
                frequency_balance * weights["frequency_balance"] +
                stereo_image_score * weights["stereo_image"] +
                noise_score * weights["noise"] +
                artifacts_score * weights["artifacts"]
            )

            assessment.overall_score = overall_score
            assessment.clarity_score = clarity_score
            assessment.balance_score = balance_score
            assessment.dynamics_score = dynamics_score
            assessment.frequency_balance = frequency_balance
            assessment.stereo_image_score = stereo_image_score
            assessment.noise_score = noise_score
            assessment.artifacts_score = artifacts_score

            # Generate recommendations
            assessment.recommendations = self._generate_recommendations(assessment)

            # Calculate confidence
            assessment.confidence = self._calculate_confidence(assessment, analysis_results)

        except Exception as e:
            print(f"Error in quality assessment: {e}")
            assessment.overall_score = 50.0
            assessment.issues.append("Analysis incomplete due to errors")

        return assessment

    def _generate_recommendations(self, assessment: AudioQualityAssessment) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        if assessment.clarity_score < 70:
            recommendations.append("Consider noise reduction or EQ to improve clarity")

        if assessment.balance_score < 70:
            recommendations.append("Adjust overall levels and apply compression for better balance")

        if assessment.dynamics_score < 70:
            recommendations.append("Apply dynamic range compression or expansion")

        if assessment.frequency_balance < 70:
            recommendations.append("Use EQ to balance frequency response")

        if assessment.noise_score < 70:
            recommendations.append("Apply noise reduction or gating")

        if assessment.artifacts_score < 70:
            recommendations.append("Check for clipping or distortion artifacts")

        return recommendations

    def _calculate_confidence(self, assessment: AudioQualityAssessment,
                            analysis_results: Dict[str, Any]) -> float:
        """Calculate confidence in assessment"""
        confidence = 0.5  # Base confidence

        # Increase confidence based on available analysis types
        available_types = len(analysis_results)
        max_types = 5  # spectral, temporal, perceptual, technical, statistical

        confidence += (available_types / max_types) * 0.3

        # Increase confidence based on score consistency
        scores = [
            assessment.clarity_score,
            assessment.balance_score,
            assessment.dynamics_score,
            assessment.frequency_balance,
            assessment.stereo_image_score,
            assessment.noise_score,
            assessment.artifacts_score
        ]

        score_std = np.std(scores)
        if score_std < 20:  # Low variation in scores
            confidence += 0.2

        return min(confidence, 1.0)

    def start_realtime_monitoring(self, audio_callback: Callable = None):
        """Start real-time audio monitoring"""
        self.monitoring_enabled = True
        self.monitor_timer.start(100)  # 100ms update rate

    def stop_realtime_monitoring(self):
        """Stop real-time audio monitoring"""
        self.monitoring_enabled = False
        self.monitor_timer.stop()

    def _update_monitoring(self):
        """Update real-time monitoring"""
        if not self.monitoring_enabled:
            return

        # In real implementation, this would process real-time audio data
        # and emit monitoring updates
        pass

    def get_visualization_data(self, analysis_id: str) -> Dict[str, Any]:
        """Get visualization data for analysis results"""
        if analysis_id in self.analysis_results:
            results = self.analysis_results[analysis_id]

            viz_data = {
                "spectrum": {},
                "waveform": {},
                "spectrogram": {},
                "phase": {},
                "levels": {}
            }

            # Prepare spectrum visualization data
            if "spectral" in results:
                spectral = results["spectral"]
                if "spectrum" in spectral:
                    spectrum = spectral["spectrum"]
                    viz_data["spectrum"] = {
                        "frequencies": spectrum["frequencies"].tolist(),
                        "magnitude": spectrum["magnitude"].tolist(),
                        "peak_hold": spectrum["peak_hold"].tolist(),
                        "average": spectrum["average"].tolist()
                    }

            self.visualization_data_ready.emit(viz_data)
            return viz_data

        return {}

    def export_analysis_report(self, analysis_id: str, output_path: str) -> bool:
        """Export analysis report to file"""
        try:
            if analysis_id not in self.analysis_results:
                return False

            results = self.analysis_results[analysis_id]

            # Create comprehensive report
            report = {
                "analysis_id": analysis_id,
                "timestamp": time.time(),
                "sample_rate": self.sample_rate,
                "results": results,
                "quality_assessment": results.get("quality_assessment", {}).__dict__
            }

            import json
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            return True

        except Exception as e:
            print(f"Error exporting report: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Create professional analyzer
    analyzer = ProfessionalAudioAnalyzer()

    print("Professional Audio Analysis System")
    print("Available analysis types:")
    for analysis_type in AnalysisType:
        print(f"  - {analysis_type.value}")

    print("\nAnalysis features:")
    print("  - Comprehensive spectral analysis")
    print("  - Perceptual loudness measurement")
    print("  - Technical quality metrics")
    print("  - Statistical analysis")
    print("  - Quality assessment and recommendations")
    print("  - Real-time monitoring capabilities")

    # Example of what would happen during actual analysis
    print("\nTo analyze an audio file:")
    print("  analyzer.analyze_audio_file('audio.wav')")
    print("  # This would return an analysis_id and emit signals with results")