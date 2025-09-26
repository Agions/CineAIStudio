#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
专业级音频降噪和增强系统
提供噪声消除、回声抑制、语音增强、音质优化等功能
"""

import numpy as np
import librosa
import soundfile as sf
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import threading
import queue
import time
from collections import defaultdict, deque
import logging
import tempfile
import os
import math

try:
    import noisereduce as nr
    NOISEREDUCE_AVAILABLE = True
except ImportError:
    NOISEREDUCE_AVAILABLE = False
    print("警告: noisereduce库未安装，降噪功能将被限制")

try:
    from scipy import signal
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("警告: scipy未安装，信号处理功能将被限制")

try:
    from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
    from PyQt6.QtCore import pyqtSignal as Signal
except ImportError:
    try:
        from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread
        from PyQt5.QtCore import pyqtSignal as Signal
    except ImportError:
        try:
            from PySide2.QtCore import QObject, Signal, QTimer, QThread
        except ImportError:
            try:
                from PySide6.QtCore import QObject, Signal, QTimer, QThread
            except ImportError:
                class Signal:
                    def __init__(self, *args, **kwargs):
                        pass
                class QObject:
                    def __init__(self):
                        pass
                class QTimer:
                    def __init__(self):
                        pass
                class QThread:
                    def __init__(self):
                        pass


class EnhancementType(Enum):
    """增强类型"""
    NOISE_REDUCTION = "noise_reduction"      # 降噪
    ECHO_CANCELLATION = "echo_cancellation"  # 回声消除
    VOICE_ENHANCEMENT = "voice_enhancement"  # 语音增强
    BASS_BOOST = "bass_boost"               # 低音增强
    TREBLE_BOOST = "treble_boost"           # 高音增强
    VOLUME_NORMALIZATION = "volume_normalization"  # 音量标准化
    DYNAMIC_RANGE_COMPRESSION = "dynamic_range_compression"  # 动态范围压缩
    EQUALIZATION = "equalization"           # 均衡器
    PITCH_CORRECTION = "pitch_correction"   # 音高校正
    STEREO_ENHANCEMENT = "stereo_enhancement"  # 立体声增强


class NoiseType(Enum):
    """噪声类型"""
    WHITE_NOISE = "white_noise"           # 白噪声
    PINK_NOISE = "pink_noise"             # 粉红噪声
    BROWN_NOISE = "brown_noise"           # 棕噪声
    IMPULSE_NOISE = "impulse_noise"       # 脉冲噪声
    BACKGROUND_HUM = "background_hum"      # 背景嗡嗡声
    WIND_NOISE = "wind_noise"             # 风噪声
    ELECTRICAL_NOISE = "electrical_noise"  # 电气噪声


@dataclass
class AudioProfile:
    """音频配置"""
    sample_rate: int
    channels: int
    duration: float
    bit_depth: int
    format: str


@dataclass
class EnhancementConfig:
    """增强配置"""
    enhancement_type: EnhancementType
    parameters: Dict[str, Any]
    enabled: bool = True
    intensity: float = 1.0


class NoiseProfiler:
    """噪声分析器"""

    def __init__(self):
        self.sample_rate = 44100
        self.frame_size = 1024
        self.hop_length = 512

    def analyze_noise_profile(self, audio_data: np.ndarray, noise_regions: List[Tuple[float, float]] = None) -> Dict[str, Any]:
        """分析噪声特征"""
        if noise_regions is None:
            # 自动检测噪声区域（通常在音频开始和结束的静音段）
            noise_regions = self._detect_noise_regions(audio_data)

        if not noise_regions:
            return {"noise_type": NoiseType.WHITE_NOISE.value, "noise_level": 0.0}

        # 提取噪声样本
        noise_samples = []
        for start_time, end_time in noise_regions:
            start_sample = int(start_time * self.sample_rate)
            end_sample = int(end_time * self.sample_rate)
            noise_samples.append(audio_data[start_sample:end_sample])

        if not noise_samples:
            return {"noise_type": NoiseType.WHITE_NOISE.value, "noise_level": 0.0}

        # 合并噪声样本
        combined_noise = np.concatenate(noise_samples)

        # 分析噪声特征
        noise_profile = {
            "noise_type": self._classify_noise_type(combined_noise),
            "noise_level": self._calculate_noise_level(combined_noise),
            "frequency_spectrum": self._analyze_frequency_spectrum(combined_noise),
            "statistical_features": self._extract_statistical_features(combined_noise)
        }

        return noise_profile

    def _detect_noise_regions(self, audio_data: np.ndarray) -> List[Tuple[float, float]]:
        """检测噪声区域"""
        # 计算短时能量
        frame_energy = []
        for i in range(0, len(audio_data) - self.frame_size, self.hop_length):
            frame = audio_data[i:i + self.frame_size]
            energy = np.sum(frame ** 2) / len(frame)
            frame_energy.append(energy)

        frame_energy = np.array(frame_energy)

        # 寻找低能量段（可能是噪声）
        energy_threshold = np.mean(frame_energy) * 0.1
        noise_regions = []

        in_noise_region = False
        region_start = 0

        for i, energy in enumerate(frame_energy):
            if energy < energy_threshold:
                if not in_noise_region:
                    region_start = i
                    in_noise_region = True
            else:
                if in_noise_region:
                    region_end = i
                    if region_end - region_start > 10:  # 至少10帧
                        start_time = region_start * self.hop_length / self.sample_rate
                        end_time = region_end * self.hop_length / self.sample_rate
                        noise_regions.append((start_time, end_time))
                    in_noise_region = False

        return noise_regions

    def _classify_noise_type(self, noise_data: np.ndarray) -> str:
        """分类噪声类型"""
        # 计算频谱特征
        freqs, times, Sxx = signal.spectrogram(noise_data, self.sample_rate)
        power_spectrum = np.mean(Sxx, axis=1)

        # 分析频谱特征
        freq_bins = len(freqs)
        low_freq = power_spectrum[:freq_bins//4]
        mid_freq = power_spectrum[freq_bins//4:freq_bins//2]
        high_freq = power_spectrum[freq_bins//2:]

        # 基于频谱特征分类
        low_power = np.mean(low_freq)
        mid_power = np.mean(mid_freq)
        high_power = np.mean(high_freq)

        if high_power > low_power * 2:
            return NoiseType.WHITE_NOISE.value
        elif low_power > high_power * 2:
            return NoiseType.BROWN_NOISE.value
        elif abs(low_power - mid_power) < 0.1 and abs(mid_power - high_power) < 0.1:
            return NoiseType.PINK_NOISE.value
        else:
            return NoiseType.BACKGROUND_HUM.value

    def _calculate_noise_level(self, noise_data: np.ndarray) -> float:
        """计算噪声水平"""
        rms = np.sqrt(np.mean(noise_data ** 2))
        db_level = 20 * np.log10(rms + 1e-10)
        return db_level

    def _analyze_frequency_spectrum(self, noise_data: np.ndarray) -> Dict[str, float]:
        """分析频谱特征"""
        freqs, psd = signal.welch(noise_data, self.sample_rate)

        return {
            "peak_frequency": float(freqs[np.argmax(psd)]),
            "spectral_centroid": float(np.sum(freqs * psd) / np.sum(psd)),
            "spectral_bandwidth": float(np.sqrt(np.sum(((freqs - np.sum(freqs * psd) / np.sum(psd)) ** 2) * psd) / np.sum(psd))),
            "spectral_rolloff": float(freqs[np.where(np.cumsum(psd) >= 0.85 * np.sum(psd))[0][0]])
        }

    def _extract_statistical_features(self, noise_data: np.ndarray) -> Dict[str, float]:
        """提取统计特征"""
        return {
            "mean": float(np.mean(noise_data)),
            "std": float(np.std(noise_data)),
            "skewness": float(self._calculate_skewness(noise_data)),
            "kurtosis": float(self._calculate_kurtosis(noise_data)),
            "zero_crossing_rate": float(self._calculate_zcr(noise_data))
        }

    def _calculate_skewness(self, data: np.ndarray) -> float:
        """计算偏度"""
        mean = np.mean(data)
        std = np.std(data)
        return np.mean(((data - mean) / std) ** 3)

    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """计算峰度"""
        mean = np.mean(data)
        std = np.std(data)
        return np.mean(((data - mean) / std) ** 4) - 3

    def _calculate_zcr(self, data: np.ndarray) -> float:
        """计算过零率"""
        zero_crossings = np.where(np.diff(np.sign(data)))[0]
        return len(zero_crossings) / len(data)


class NoiseReducer:
    """降噪器"""

    def __init__(self):
        self.profiler = NoiseProfiler()
        self.noise_profile = None

    def reduce_noise(self, audio_data: np.ndarray, noise_profile: Dict[str, Any] = None,
                   reduction_strength: float = 0.8) -> np.ndarray:
        """降噪处理"""
        if noise_profile is None:
            noise_profile = self.profiler.analyze_noise_profile(audio_data)

        if NOISEREDUCE_AVAILABLE:
            return self._reduce_noise_with_library(audio_data, noise_profile, reduction_strength)
        else:
            return self._reduce_noise_manual(audio_data, noise_profile, reduction_strength)

    def _reduce_noise_with_library(self, audio_data: np.ndarray, noise_profile: Dict[str, Any],
                                  reduction_strength: float) -> np.ndarray:
        """使用noisereduce库降噪"""
        if not NOISEREDUCE_AVAILABLE:
            return self._reduce_noise_with_librosa(audio_data, noise_profile, reduction_strength)

        try:
            # 如果有噪声样本，使用噪声样本进行降噪
            if "noise_sample" in noise_profile:
                noise_sample = noise_profile["noise_sample"]
                reduced_noise = nr.reduce_noise(
                    y=audio_data,
                    y_noise=noise_sample,
                    prop_decrease=reduction_strength
                )
            else:
                # 使用统计降噪
                reduced_noise = nr.reduce_noise(
                    y=audio_data,
                    sr=self.profiler.sample_rate,
                    prop_decrease=reduction_strength
                )

            return reduced_noise

        except Exception as e:
            logging.warning(f"noisereduce库降噪失败，使用手动降噪: {e}")
            return self._reduce_noise_manual(audio_data, noise_profile, reduction_strength)

    def _reduce_noise_manual(self, audio_data: np.ndarray, noise_profile: Dict[str, Any],
                           reduction_strength: float) -> np.ndarray:
        """手动降噪（频谱减法）"""
        if not SCIPY_AVAILABLE:
            return audio_data

        try:
            # 短时傅里叶变换
            f, t, Zxx = signal.stft(audio_data, self.profiler.sample_rate, nperseg=1024)

            # 计算噪声频谱（从噪声profile中获取或估计）
            noise_spectrum = self._estimate_noise_spectrum(Zxx, noise_profile)

            # 频谱减法
            alpha = reduction_strength  # 减法系数
            beta = 0.1  # 最小增益

            magnitude = np.abs(Zxx)
            phase = np.angle(Zxx)

            # 应用频谱减法
            enhanced_magnitude = magnitude - alpha * noise_spectrum
            enhanced_magnitude = np.maximum(enhanced_magnitude, beta * magnitude)

            # 重建信号
            enhanced_Zxx = enhanced_magnitude * np.exp(1j * phase)
            _, enhanced_audio = signal.istft(enhanced_Zxx, self.profiler.sample_rate)

            return enhanced_audio.astype(np.float32)

        except Exception as e:
            logging.error(f"手动降噪失败: {e}")
            return audio_data

    def _estimate_noise_spectrum(self, Zxx: np.ndarray, noise_profile: Dict[str, Any]) -> np.ndarray:
        """估计噪声频谱"""
        # 基于噪声profile估计噪声频谱
        if "frequency_spectrum" in noise_profile:
            # 简化的噪声频谱估计
            noise_level = noise_profile.get("noise_level", -60)
            noise_spectrum = np.full(Zxx.shape, 10 ** (noise_level / 20))
        else:
            # 使用频谱的最小值作为噪声估计
            noise_spectrum = np.min(np.abs(Zxx), axis=1, keepdims=True)

        return noise_spectrum


class VoiceEnhancer:
    """语音增强器"""

    def __init__(self):
        self.sample_rate = 44100

    def enhance_voice(self, audio_data: np.ndarray, enhancement_params: Dict[str, Any]) -> np.ndarray:
        """语音增强"""
        enhanced = audio_data.copy()

        # 动态范围压缩
        if enhancement_params.get("dynamic_range_compression", False):
            enhanced = self._apply_dynamic_range_compression(
                enhanced,
                enhancement_params.get("compression_ratio", 4.0),
                enhancement_params.get("threshold", -20.0),
                enhancement_params.get("attack_time", 0.003),
                enhancement_params.get("release_time", 0.1)
            )

        # 频率均衡
        if enhancement_params.get("equalization", False):
            enhanced = self._apply_equalization(
                enhanced,
                enhancement_params.get("eq_bands", {})
            )

        # 去除混响
        if enhancement_params.get("dereverberation", False):
            enhanced = self._apply_dereverberation(enhanced)

        return enhanced

    def _apply_dynamic_range_compression(self, audio_data: np.ndarray, ratio: float,
                                       threshold_db: float, attack_time: float,
                                       release_time: float) -> np.ndarray:
        """应用动态范围压缩"""
        # 将音频转换为dB
        audio_db = 20 * np.log10(np.abs(audio_data) + 1e-10)

        # 计算增益
        gain = np.zeros_like(audio_db)
        above_threshold = audio_db > threshold_db

        gain[above_threshold] = threshold_db + (audio_db[above_threshold] - threshold_db) / ratio
        gain[~above_threshold] = audio_db[~above_threshold]

        gain_reduction = gain - audio_db

        # 应用平滑的增益变化
        attack_samples = int(attack_time * self.sample_rate)
        release_samples = int(release_time * self.sample_rate)

        smoothed_gain = self._smooth_gain_changes(gain_reduction, attack_samples, release_samples)

        # 应用增益
        gain_linear = 10 ** (smoothed_gain / 20)
        enhanced_audio = audio_data * gain_linear

        return enhanced_audio

    def _smooth_gain_changes(self, gain_reduction: np.ndarray, attack_samples: int,
                           release_samples: int) -> np.ndarray:
        """平滑增益变化"""
        smoothed = np.zeros_like(gain_reduction)

        for i in range(1, len(gain_reduction)):
            if gain_reduction[i] < gain_reduction[i-1]:
                # 增益减少（使用attack时间）
                alpha = 1 - np.exp(-1 / attack_samples)
            else:
                # 增益增加（使用release时间）
                alpha = 1 - np.exp(-1 / release_samples)

            smoothed[i] = alpha * gain_reduction[i] + (1 - alpha) * smoothed[i-1]

        return smoothed

    def _apply_equalization(self, audio_data: np.ndarray, eq_bands: Dict[str, float]) -> np.ndarray:
        """应用均衡器"""
        if not SCIPY_AVAILABLE:
            return audio_data

        enhanced = audio_data.copy()

        # 定义频段
        bands = {
            "bass": (60, 250),
            "low_mid": (250, 500),
            "mid": (500, 2000),
            "high_mid": (2000, 4000),
            "treble": (4000, 16000)
        }

        for band_name, gain_db in eq_bands.items():
            if band_name in bands and gain_db != 0:
                low_freq, high_freq = bands[band_name]
                enhanced = self._apply_band_pass_filter(
                    enhanced, low_freq, high_freq, gain_db
                )

        return enhanced

    def _apply_band_pass_filter(self, audio_data: np.ndarray, low_freq: float,
                               high_freq: float, gain_db: float) -> np.ndarray:
        """应用带通滤波器和增益"""
        try:
            # 设计带通滤波器
            nyquist = self.sample_rate / 2
            low = low_freq / nyquist
            high = high_freq / nyquist

            b, a = signal.butter(4, [low, high], btype='band')

            # 应用滤波器
            filtered = signal.filtfilt(b, a, audio_data)

            # 应用增益
            gain_linear = 10 ** (gain_db / 20)
            filtered *= gain_linear

            # 混合原始信号和滤波信号
            mixed = audio_data + filtered * 0.5

            return mixed

        except Exception as e:
            logging.error(f"带通滤波失败: {e}")
            return audio_data

    def _apply_dereverberation(self, audio_data: np.ndarray) -> np.ndarray:
        """应用去混响"""
        # 简化的去混响算法
        try:
            # 使用频谱减法去除混响
            f, t, Zxx = signal.stft(audio_data, self.sample_rate, npersec=1024)

            magnitude = np.abs(Zxx)
            phase = np.angle(Zxx)

            # 估计混响成分
            reverb_estimate = self._estimate_reverberation(magnitude)

            # 减去混响成分
            dereverbed_magnitude = magnitude - 0.3 * reverb_estimate
            dereverbed_magnitude = np.maximum(dereverbed_magnitude, 0.1 * magnitude)

            # 重建信号
            dereverbed_Zxx = dereverbed_magnitude * np.exp(1j * phase)
            _, dereverbed_audio = signal.istft(dereverbed_Zxx, self.sample_rate)

            return dereverbed_audio.astype(np.float32)

        except Exception as e:
            logging.error(f"去混响失败: {e}")
            return audio_data

    def _estimate_reverberation(self, magnitude: np.ndarray) -> np.ndarray:
        """估计混响成分"""
        # 使用频谱的平滑版本作为混响估计
        window_size = 5
        reverb_estimate = np.zeros_like(magnitude)

        for i in range(magnitude.shape[1]):
            if i >= window_size:
                reverb_estimate[:, i] = np.mean(magnitude[:, i-window_size:i], axis=1)
            else:
                reverb_estimate[:, i] = magnitude[:, i]

        return reverb_estimate


class StereoEnhancer:
    """立体声增强器"""

    def __init__(self):
        self.sample_rate = 44100

    def enhance_stereo(self, audio_data: np.ndarray, enhancement_params: Dict[str, Any]) -> np.ndarray:
        """立体声增强"""
        if len(audio_data.shape) == 1:
            # 单声道转立体声
            stereo_data = np.column_stack((audio_data, audio_data))
        else:
            stereo_data = audio_data.copy()

        # 宽度增强
        if enhancement_params.get("width_enhancement", False):
            width_amount = enhancement_params.get("width_amount", 1.5)
            stereo_data = self._enhance_width(stereo_data, width_amount)

        # 声像调整
        if enhancement_params.get("panning", False):
            pan_value = enhancement_params.get("pan_value", 0.0)
            stereo_data = self._apply_panning(stereo_data, pan_value)

        return stereo_data

    def _enhance_width(self, stereo_data: np.ndarray, width_amount: float) -> np.ndarray:
        """增强立体声宽度"""
        left = stereo_data[:, 0]
        right = stereo_data[:, 1]

        # 计算中央和侧边信号
        mid = (left + right) / 2
        side = (left - right) / 2

        # 增强侧边信号
        enhanced_side = side * width_amount

        # 重建左右声道
        enhanced_left = mid + enhanced_side
        enhanced_right = mid - enhanced_side

        # 防止削波
        enhanced_left = np.clip(enhanced_left, -1, 1)
        enhanced_right = np.clip(enhanced_right, -1, 1)

        return np.column_stack((enhanced_left, enhanced_right))

    def _apply_panning(self, stereo_data: np.ndarray, pan_value: float) -> np.ndarray:
        """应用声像调整"""
        # pan_value: -1 (左) 到 1 (右)
        left_gain = np.cos((pan_value + 1) * np.pi / 4)
        right_gain = np.sin((pan_value + 1) * np.pi / 4)

        enhanced_left = stereo_data[:, 0] * left_gain
        enhanced_right = stereo_data[:, 1] * right_gain

        return np.column_stack((enhanced_left, enhanced_right))


class AudioEnhancer(QObject):
    """音频增强器主类"""

    # 信号定义
    enhancement_started = Signal(str)  # 增强开始
    enhancement_progress = Signal(int, str)  # 增强进度
    enhancement_completed = Signal(str, str)  # 增强完成
    enhancement_error = Signal(str)  # 增强错误
    analysis_completed = Signal(dict)  # 分析完成

    def __init__(self):
        super().__init__()
        self.noise_reducer = NoiseReducer()
        self.voice_enhancer = VoiceEnhancer()
        self.stereo_enhancer = StereoEnhancer()
        self.is_processing = False
        self.enhancement_thread = None

    def analyze_audio(self, audio_path: str) -> Dict[str, Any]:
        """分析音频"""
        try:
            # 加载音频
            audio_data, sample_rate = librosa.load(audio_path, sr=None, mono=False)

            # 分析音频配置
            profile = self._analyze_audio_profile(audio_data, sample_rate)

            # 分析噪声特征
            if len(audio_data.shape) == 1:
                noise_profile = self.noise_reducer.profiler.analyze_noise_profile(audio_data)
            else:
                # 对于立体声，分析左声道
                noise_profile = self.noise_reducer.profiler.analyze_noise_profile(audio_data[:, 0])

            analysis_result = {
                "audio_profile": profile,
                "noise_profile": noise_profile,
                "enhancement_suggestions": self._generate_enhancement_suggestions(profile, noise_profile)
            }

            self.analysis_completed.emit(analysis_result)
            return analysis_result

        except Exception as e:
            self.enhancement_error.emit(f"音频分析失败: {str(e)}")
            return {}

    def _analyze_audio_profile(self, audio_data: np.ndarray, sample_rate: int) -> AudioProfile:
        """分析音频配置"""
        duration = len(audio_data) / sample_rate if len(audio_data.shape) == 1 else audio_data.shape[0] / sample_rate
        channels = 1 if len(audio_data.shape) == 1 else audio_data.shape[1]
        bit_depth = 16  # 假设16位

        return AudioProfile(
            sample_rate=sample_rate,
            channels=channels,
            duration=duration,
            bit_depth=bit_depth,
            format="PCM"
        )

    def _generate_enhancement_suggestions(self, profile: AudioProfile,
                                         noise_profile: Dict[str, Any]) -> List[EnhancementConfig]:
        """生成增强建议"""
        suggestions = []

        # 基于噪声水平建议降噪
        noise_level = noise_profile.get("noise_level", -60)
        if noise_level > -40:  # 噪声较高
            suggestions.append(EnhancementConfig(
                enhancement_type=EnhancementType.NOISE_REDUCTION,
                parameters={"reduction_strength": 0.8},
                enabled=True
            ))

        # 基于音频类型建议语音增强
        if profile.duration > 10:  # 长音频可能包含语音
            suggestions.append(EnhancementConfig(
                enhancement_type=EnhancementType.VOICE_ENHANCEMENT,
                parameters={
                    "dynamic_range_compression": True,
                    "equalization": True,
                    "eq_bands": {"bass": -2, "mid": 1, "treble": 1}
                },
                enabled=True
            ))

        # 立体声增强建议
        if profile.channels == 2:
            suggestions.append(EnhancementConfig(
                enhancement_type=EnhancementType.STEREO_ENHANCEMENT,
                parameters={"width_enhancement": True, "width_amount": 1.2},
                enabled=True
            ))

        return suggestions

    def enhance_audio_async(self, audio_path: str, output_path: str,
                          enhancement_configs: List[EnhancementConfig] = None):
        """异步音频增强"""
        if self.is_processing:
            self.enhancement_error.emit("正在处理音频中，请等待完成")
            return

        self.is_processing = True
        self.enhancement_started.emit(audio_path)

        # 创建增强线程
        self.enhancement_thread = AudioEnhancementThread(
            self, audio_path, output_path, enhancement_configs
        )
        self.enhancement_thread.progress_updated.connect(self.enhancement_progress.emit)
        self.enhancement_thread.enhancement_completed.connect(self._on_enhancement_completed)
        self.enhancement_thread.error_occurred.connect(self.enhancement_error.emit)
        self.enhancement_thread.start()

    def _on_enhancement_completed(self, input_path: str, output_path: str):
        """增强完成回调"""
        self.is_processing = False
        self.enhancement_completed.emit(input_path, output_path)

    def enhance_audio_sync(self, audio_path: str, output_path: str,
                          enhancement_configs: List[EnhancementConfig] = None) -> bool:
        """同步音频增强"""
        try:
            # 加载音频
            audio_data, sample_rate = librosa.load(audio_path, sr=None, mono=False)

            # 如果没有提供配置，使用默认配置
            if enhancement_configs is None:
                enhancement_configs = self._get_default_enhancement_configs()

            # 应用增强
            enhanced_audio = self._apply_enhancements(audio_data, enhancement_configs)

            # 保存增强后的音频
            sf.write(output_path, enhanced_audio, sample_rate)

            return True

        except Exception as e:
            logging.error(f"音频增强失败: {e}")
            return False

    def _apply_enhancements(self, audio_data: np.ndarray,
                          enhancement_configs: List[EnhancementConfig]) -> np.ndarray:
        """应用增强处理"""
        enhanced = audio_data.copy()

        for config in enhancement_configs:
            if not config.enabled:
                continue

            try:
                if config.enhancement_type == EnhancementType.NOISE_REDUCTION:
                    if len(enhanced.shape) == 1:
                        enhanced = self.noise_reducer.reduce_noise(
                            enhanced, reduction_strength=config.parameters.get("reduction_strength", 0.8)
                        )
                    else:
                        # 对立体声的每个声道分别处理
                        enhanced[:, 0] = self.noise_reducer.reduce_noise(
                            enhanced[:, 0], reduction_strength=config.parameters.get("reduction_strength", 0.8)
                        )
                        enhanced[:, 1] = self.noise_reducer.reduce_noise(
                            enhanced[:, 1], reduction_strength=config.parameters.get("reduction_strength", 0.8)
                        )

                elif config.enhancement_type == EnhancementType.VOICE_ENHANCEMENT:
                    if len(enhanced.shape) == 1:
                        enhanced = self.voice_enhancer.enhance_voice(enhanced, config.parameters)
                    else:
                        enhanced[:, 0] = self.voice_enhancer.enhance_voice(enhanced[:, 0], config.parameters)
                        enhanced[:, 1] = self.voice_enhancer.enhance_voice(enhanced[:, 1], config.parameters)

                elif config.enhancement_type == EnhancementType.STEREO_ENHANCEMENT:
                    enhanced = self.stereo_enhancer.enhance_stereo(enhanced, config.parameters)

            except Exception as e:
                logging.error(f"应用增强 {config.enhancement_type.value} 失败: {e}")

        return enhanced

    def _get_default_enhancement_configs(self) -> List[EnhancementConfig]:
        """获取默认增强配置"""
        return [
            EnhancementConfig(
                enhancement_type=EnhancementType.NOISE_REDUCTION,
                parameters={"reduction_strength": 0.7},
                enabled=True
            ),
            EnhancementConfig(
                enhancement_type=EnhancementType.VOICE_ENHANCEMENT,
                parameters={
                    "dynamic_range_compression": True,
                    "compression_ratio": 3.0,
                    "threshold": -15.0
                },
                enabled=True
            )
        ]

    def stop_processing(self):
        """停止处理"""
        if self.enhancement_thread and self.enhancement_thread.isRunning():
            self.enhancement_thread.stop()
            self.is_processing = False


class AudioEnhancementThread(QThread):
    """音频增强线程"""

    progress_updated = Signal(int, str)
    enhancement_completed = Signal(str, str)
    error_occurred = Signal(str)

    def __init__(self, enhancer: AudioEnhancer, audio_path: str, output_path: str,
                 enhancement_configs: List[EnhancementConfig]):
        super().__init__()
        self.enhancer = enhancer
        self.audio_path = audio_path
        self.output_path = output_path
        self.enhancement_configs = enhancement_configs
        self._is_running = True

    def run(self):
        """运行音频增强"""
        try:
            self.progress_updated.emit(10, "加载音频文件...")

            # 加载音频
            audio_data, sample_rate = librosa.load(self.audio_path, sr=None, mono=False)

            if not self._is_running:
                return

            self.progress_updated.emit(30, "应用音频增强...")

            # 应用增强
            enhanced_audio = self.enhancer._apply_enhancements(audio_data, self.enhancement_configs)

            if not self._is_running:
                return

            self.progress_updated.emit(80, "保存增强后的音频...")

            # 保存增强后的音频
            sf.write(self.output_path, enhanced_audio, sample_rate)

            self.progress_updated.emit(100, "音频增强完成")
            self.enhancement_completed.emit(self.audio_path, self.output_path)

        except Exception as e:
            self.error_occurred.emit(f"音频增强失败: {str(e)}")

    def stop(self):
        """停止线程"""
        self._is_running = False
        self.wait()


# 工具函数
def create_audio_enhancer() -> AudioEnhancer:
    """创建音频增强器"""
    return AudioEnhancer()


def quick_enhance_audio(input_path: str, output_path: str) -> bool:
    """快速音频增强（同步版本）"""
    enhancer = create_audio_enhancer()
    return enhancer.enhance_audio_sync(input_path, output_path)


def main():
    """主函数 - 用于测试"""
    # 创建音频增强器
    enhancer = create_audio_enhancer()

    # 测试音频增强功能
    print("音频增强器创建成功")
    print(f"降噪功能可用: {NOISEREDUCE_AVAILABLE or SCIPY_AVAILABLE}")


if __name__ == "__main__":
    main()