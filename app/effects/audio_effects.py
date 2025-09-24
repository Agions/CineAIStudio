"""
专业音频效果库 - 提供丰富的音频处理效果
包括均衡器、混响、降噪、压缩等专业音频处理
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging

from app.core.logger import Logger
from app.effects.effects_system import EffectInfo, EffectParameter
from app.utils.ffmpeg_utils import FFmpegUtils


class AudioEffectType(Enum):
    """音频效果类型"""
    EQUALIZER = "equalizer"    # 均衡器
    REVERB = "reverb"          # 混响
    COMPRESSOR = "compressor"  # 压缩器
    NOISE_REDUCTION = "noise_reduction"  # 降噪
    PITCH = "pitch"           # 变调
    TIME_STRETCH = "time_stretch"  # 时间拉伸
    DISTORTION = "distortion"  # 失真
    CHORUS = "chorus"         # 合唱
    DELAY = "delay"           # 延迟
    FLANGER = "flanger"       # 镶边
    PHASER = "phaser"         # 相位器


class AudioEffectPreset(Enum):
    """音频效果预设"""
    VOCAL_ENHANCEMENT = "vocal_enhancement"      # 人声增强
    MUSIC_MASTERING = "music_mastering"          # 音乐母带
    PODCAST = "podcast"                          # 播客
    KARAOKE = "karaoke"                          # 卡拉OK
    PHONE_VOICE = "phone_voice"                  # 电话音效
    ROBOT_VOICE = "robot_voice"                  # 机器人音效
    UNDERWATER = "underwater"                    # 水下音效
    ECHO_CHAMBER = "echo_chamber"                # 回声室


class AudioEffectsLibrary:
    """音频效果库"""

    def __init__(self):
        self.logger = Logger.get_logger("AudioEffectsLibrary")
        self.ffmpeg_utils = FFmpegUtils()

        # 初始化音频效果
        self._init_audio_effects()

    def _init_audio_effects(self):
        """初始化音频效果"""
        self.audio_effects = self._create_audio_effects()

    def _create_audio_effects(self) -> Dict[str, EffectInfo]:
        """创建音频效果定义"""
        effects = {}

        # 均衡器
        eq_params = [
            EffectParameter("low_freq", "float", 0.0, -20.0, 20.0, 0.1, "低频增益", "dB"),
            EffectParameter("mid_freq", "float", 0.0, -20.0, 20.0, 0.1, "中频增益", "dB"),
            EffectParameter("high_freq", "float", 0.0, -20.0, 20.0, 0.1, "高频增益", "dB"),
            EffectParameter("low_freq_center", "float", 200.0, 20.0, 1000.0, 10.0, "低频中心", "Hz"),
            EffectParameter("mid_freq_center", "float", 2000.0, 500.0, 5000.0, 100.0, "中频中心", "Hz"),
            EffectParameter("high_freq_center", "float", 6000.0, 4000.0, 20000.0, 100.0, "高频中心", "Hz")
        ]

        effects["equalizer"] = EffectInfo(
            id="equalizer", name="均衡器", type="audio",
            category="equalizer", description="三段参数均衡器",
            parameters=eq_params, presets=[], real_time=True
        )

        # 混响
        reverb_params = [
            EffectParameter("room_size", "float", 0.5, 0.0, 1.0, 0.01, "房间大小", ""),
            EffectParameter("damping", "float", 0.5, 0.0, 1.0, 0.01, "阻尼", ""),
            EffectParameter("wet_level", "float", 0.3, 0.0, 1.0, 0.01, "混响强度", ""),
            EffectParameter("dry_level", "float", 0.7, 0.0, 1.0, 0.01, "干声强度", ""),
            EffectParameter("width", "float", 1.0, 0.0, 2.0, 0.01, "立体声宽度", "")
        ]

        effects["reverb"] = EffectInfo(
            id="reverb", name="混响", type="audio",
            category="reverb", description="空间混响效果",
            parameters=reverb_params, presets=[], real_time=True
        )

        # 压缩器
        compressor_params = [
            EffectParameter("threshold", "float", -20.0, -60.0, 0.0, 0.1, "阈值", "dB"),
            EffectParameter("ratio", "float", 4.0, 1.0, 20.0, 0.1, "压缩比", ""),
            EffectParameter("attack", "float", 5.0, 0.1, 100.0, 0.1, "启动时间", "ms"),
            EffectParameter("release", "float", 100.0, 10.0, 1000.0, 1.0, "释放时间", "ms"),
            EffectParameter("makeup_gain", "float", 0.0, -20.0, 20.0, 0.1, "增益补偿", "dB")
        ]

        effects["compressor"] = EffectInfo(
            id="compressor", name="压缩器", type="audio",
            category="compressor", description="动态压缩器",
            parameters=compressor_params, presets=[], real_time=True
        )

        # 降噪
        noise_reduction_params = [
            EffectParameter("noise_reduction", "float", 12.0, 0.0, 30.0, 0.1, "降噪量", "dB"),
            Parameter("noise_floor", "float", -50.0, -80.0, -20.0, 0.1, "噪声门限", "dB"),
            EffectParameter("sensitivity", "float", 0.5, 0.0, 1.0, 0.01, "灵敏度", ""),
            EffectParameter("attack_time", "float", 20.0, 1.0, 100.0, 1.0, "启动时间", "ms"),
            EffectParameter("release_time", "float", 200.0, 50.0, 1000.0, 10.0, "释放时间", "ms")
        ]

        effects["noise_reduction"] = EffectInfo(
            id="noise_reduction", name="降噪", type="audio",
            category="noise_reduction", description="音频降噪处理",
            parameters=noise_reduction_params, presets=[], real_time=False
        )

        # 音量调整
        volume_params = [
            EffectParameter("volume", "float", 1.0, 0.0, 10.0, 0.1, "音量", ""),
            EffectParameter("fade_in", "float", 0.0, 0.0, 10.0, 0.1, "淡入时间", "s"),
            EffectParameter("fade_out", "float", 0.0, 0.0, 10.0, 0.1, "淡出时间", "s"),
            EffectParameter("delay", "float", 0.0, 0.0, 5.0, 0.1, "延迟", "s")
        ]

        effects["volume"] = EffectInfo(
            id="volume", name="音量", type="audio",
            category="basic", description="音量调整",
            parameters=volume_params, presets=[], real_time=True
        )

        # 变调
        pitch_params = [
            EffectParameter("pitch_shift", "float", 0.0, -12.0, 12.0, 0.1, "变调", "半音"),
            EffectParameter("formant_shift", "float", 1.0, 0.5, 2.0, 0.01, "共振峰", ""),
            EffectParameter("preserve_formants", "bool", True, None, None, None, "保持共振峰", "")
        ]

        effects["pitch"] = EffectInfo(
            id="pitch", name="变调", type="audio",
            category="pitch", description="音频变调效果",
            parameters=pitch_params, presets=[], real_time=False
        )

        # 延迟
        delay_params = [
            EffectParameter("delay_time", "float", 0.3, 0.0, 2.0, 0.01, "延迟时间", "s"),
            EffectParameter("feedback", "float", 0.5, 0.0, 1.0, 0.01, "反馈", ""),
            EffectParameter("mix", "float", 0.3, 0.0, 1.0, 0.01, "混合比例", ""),
            EffectParameter("low_pass", "float", 5000.0, 1000.0, 20000.0, 100.0, "低通滤波", "Hz")
        ]

        effects["delay"] = EffectInfo(
            id="delay", name="延迟", type="audio",
            category="delay", description="延迟效果",
            parameters=delay_params, presets=[], real_time=True
        )

        # 合唱
        chorus_params = [
            EffectParameter("delay_time", "float", 0.03, 0.01, 0.1, 0.001, "延迟时间", "s"),
            EffectParameter("mod_depth", "float", 0.5, 0.0, 1.0, 0.01, "调制深度", ""),
            EffectParameter("mod_rate", "float", 2.0, 0.1, 10.0, 0.1, "调制频率", "Hz"),
            EffectParameter("voices", "int", 2, 1, 8, 1, "声音数量", ""),
            EffectParameter("mix", "float", 0.5, 0.0, 1.0, 0.01, "混合比例", "")
        ]

        effects["chorus"] = EffectInfo(
            id="chorus", name="合唱", type="audio",
            category="chorus", description="合唱效果",
            parameters=chorus_params, presets=[], real_time=True
        )

        # 高通滤波器
        highpass_params = [
            EffectParameter("frequency", "float", 80.0, 20.0, 20000.0, 1.0, "截止频率", "Hz"),
            EffectParameter("order", "int", 2, 1, 8, 1, "阶数", ""),
            EffectParameter("resonance", "float", 1.0, 0.1, 10.0, 0.1, "共振", "")
        ]

        effects["highpass"] = EffectInfo(
            id="highpass", name="高通滤波器", type="audio",
            category="filter", description="高通滤波器",
            parameters=highpass_params, presets=[], real_time=True
        )

        # 低通滤波器
        lowpass_params = [
            EffectParameter("frequency", "float", 8000.0, 20.0, 20000.0, 1.0, "截止频率", "Hz"),
            EffectParameter("order", "int", 2, 1, 8, 1, "阶数", ""),
            EffectParameter("resonance", "float", 1.0, 0.1, 10.0, 0.1, "共振", "")
        ]

        effects["lowpass"] = EffectInfo(
            id="lowpass", name="低通滤波器", type="audio",
            category="filter", description="低通滤波器",
            parameters=lowpass_params, presets=[], real_time=True
        )

        return effects

    def get_effect_info(self, effect_id: str) -> Optional[EffectInfo]:
        """获取音频效果信息"""
        return self.audio_effects.get(effect_id)

    def list_effects(self, effect_type: AudioEffectType = None) -> List[EffectInfo]:
        """列出音频效果"""
        effects = list(self.audio_effects.values())

        if effect_type:
            effects = [e for e in effects if e.category == effect_type.value]

        return effects

    def apply_equalizer(self, input_path: str, output_path: str,
                      parameters: Dict[str, Any]) -> bool:
        """应用均衡器效果"""
        try:
            low_freq = parameters.get("low_freq", 0.0)
            mid_freq = parameters.get("mid_freq", 0.0)
            high_freq = parameters.get("high_freq", 0.0)

            # 构建均衡器滤镜
            filter_chain = f"equalizer=f={low_freq}:width_type=o:width=2:g={low_freq}"
            filter_chain += f",equalizer=f={mid_freq}:width_type=o:width=2:g={mid_freq}"
            filter_chain += f",equalizer=f={high_freq}:width_type=o:width=2:g={high_freq}"

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-af', filter_chain,
                '-c:a', 'aac',
                '-b:a', '192k',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply equalizer: {e}")
            return False

    def apply_reverb(self, input_path: str, output_path: str,
                    parameters: Dict[str, Any]) -> bool:
        """应用混响效果"""
        try:
            room_size = parameters.get("room_size", 0.5)
            damping = parameters.get("damping", 0.5)
            wet_level = parameters.get("wet_level", 0.3)
            dry_level = parameters.get("dry_level", 0.7)

            # 构建混响滤镜
            filter_chain = f"aecho=0.8:0.9:1000|1800:0.3|0.25"

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-af', filter_chain,
                '-c:a', 'aac',
                '-b:a', '192k',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply reverb: {e}")
            return False

    def apply_compressor(self, input_path: str, output_path: str,
                        parameters: Dict[str, Any]) -> bool:
        """应用压缩器效果"""
        try:
            threshold = parameters.get("threshold", -20.0)
            ratio = parameters.get("ratio", 4.0)
            attack = parameters.get("attack", 5.0)
            release = parameters.get("release", 100.0)
            makeup_gain = parameters.get("makeup_gain", 0.0)

            # 构建压缩器滤镜
            filter_chain = f"compand=attacks={attack}:decays={release}:points=-80/-80|-{threshold}/{threshold}|0/{makeup_gain}"

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-af', filter_chain,
                '-c:a', 'aac',
                '-b:a', '192k',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply compressor: {e}")
            return False

    def apply_noise_reduction(self, input_path: str, output_path: str,
                             parameters: Dict[str, Any]) -> bool:
        """应用降噪效果"""
        try:
            noise_reduction = parameters.get("noise_reduction", 12.0)
            noise_floor = parameters.get("noise_floor", -50.0)

            # 构建降噪滤镜
            filter_chain = f"afftdn=nf={noise_reduction}:nt=w"  # 使用FFT降噪

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-af', filter_chain,
                '-c:a', 'aac',
                '-b:a', '192k',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply noise reduction: {e}")
            return False

    def apply_volume_adjustment(self, input_path: str, output_path: str,
                               parameters: Dict[str, Any]) -> bool:
        """应用音量调整"""
        try:
            volume = parameters.get("volume", 1.0)
            fade_in = parameters.get("fade_in", 0.0)
            fade_out = parameters.get("fade_out", 0.0)

            filter_parts = []

            # 音量调整
            if volume != 1.0:
                filter_parts.append(f"volume={volume}")

            # 淡入淡出
            if fade_in > 0:
                filter_parts.append(f"afade=t=in:st=0:d={fade_in}")
            if fade_out > 0:
                # 需要获取音频长度来设置淡出开始时间
                filter_parts.append(f"afade=t=out:st=0:d={fade_out}")

            filter_chain = ",".join(filter_parts) if filter_parts else "volume=1.0"

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-af', filter_chain,
                '-c:a', 'aac',
                '-b:a', '192k',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply volume adjustment: {e}")
            return False

    def apply_pitch_shift(self, input_path: str, output_path: str,
                        parameters: Dict[str, Any]) -> bool:
        """应用变调效果"""
        try:
            pitch_shift = parameters.get("pitch_shift", 0.0)

            # 构建变调滤镜
            # 使用rubberband进行高质量变调
            filter_chain = f"rubberband=pitch={2**(pitch_shift/12)}"

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-af', filter_chain,
                '-c:a', 'aac',
                '-b:a', '192k',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply pitch shift: {e}")
            return False

    def apply_delay(self, input_path: str, output_path: str,
                   parameters: Dict[str, Any]) -> bool:
        """应用延迟效果"""
        try:
            delay_time = parameters.get("delay_time", 0.3)
            feedback = parameters.get("feedback", 0.5)
            mix = parameters.get("mix", 0.3)

            # 构建延迟滤镜
            filter_chain = f"adelay={int(delay_time*1000)}|{int(delay_time*1000)}"

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-af', filter_chain,
                '-c:a', 'aac',
                '-b:a', '192k',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply delay: {e}")
            return False

    def apply_chorus(self, input_path: str, output_path: str,
                    parameters: Dict[str, Any]) -> bool:
        """应用合唱效果"""
        try:
            delay_time = parameters.get("delay_time", 0.03)
            mod_depth = parameters.get("mod_depth", 0.5)
            mod_rate = parameters.get("mod_rate", 2.0)
            voices = parameters.get("voices", 2)
            mix = parameters.get("mix", 0.5)

            # 构建合唱滤镜
            filter_chain = f"chorus=0.5:0.9:{voices}|{delay_time}|{mod_rate}|{mod_depth}"

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-af', filter_chain,
                '-c:a', 'aac',
                '-b:a', '192k',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply chorus: {e}")
            return False

    def apply_highpass_filter(self, input_path: str, output_path: str,
                             parameters: Dict[str, Any]) -> bool:
        """应用高通滤波器"""
        try:
            frequency = parameters.get("frequency", 80.0)

            # 构建高通滤波器
            filter_chain = f"highpass=f={frequency}"

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-af', filter_chain,
                '-c:a', 'aac',
                '-b:a', '192k',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply highpass filter: {e}")
            return False

    def apply_lowpass_filter(self, input_path: str, output_path: str,
                            parameters: Dict[str, Any]) -> bool:
        """应用低通滤波器"""
        try:
            frequency = parameters.get("frequency", 8000.0)

            # 构建低通滤波器
            filter_chain = f"lowpass=f={frequency}"

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-af', filter_chain,
                '-c:a', 'aac',
                '-b:a', '192k',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply lowpass filter: {e}")
            return False

    def apply_vocal_enhancement(self, input_path: str, output_path: str) -> bool:
        """应用人声增强预设"""
        try:
            # 人声增强的参数组合
            filter_parts = []

            # 高通滤波去除低频噪声
            filter_parts.append("highpass=f=80")

            # 中频增强
            filter_parts.append("equalizer=f=2000:width_type=o:width=2:g=3")

            # 高频轻微提升增加清晰度
            filter_parts.append("equalizer=f=8000:width_type=o:width=2:g=1")

            # 轻微压缩
            filter_parts.append("compand=attacks=5:decays=100:points=-80/-80|-20/-20|0/2")

            filter_chain = ",".join(filter_parts)

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-af', filter_chain,
                '-c:a', 'aac',
                '-b:a', '192k',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply vocal enhancement: {e}")
            return False

    def apply_podcast_preset(self, input_path: str, output_path: str) -> bool:
        """应用播客预设"""
        try:
            filter_parts = []

            # 降噪
            filter_parts.append("afftdn=nf=12:nt=w")

            # 压缩器
            filter_parts.append("compand=attacks=10:decays=200:points=-80/-80|-15/-15|0/3")

            # 均衡器（人声优化）
            filter_parts.append("equalizer=f=200:width_type=o:width=2:g=-2")
            filter_parts.append("equalizer=f=2000:width_type=o:width=2:g=2")
            filter_parts.append("equalizer=f=8000:width_type=o:width=2:g=-1")

            filter_chain = ",".join(filter_parts)

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-af', filter_chain,
                '-c:a', 'aac',
                '-b:a', '128k',  # 播客用较低的比特率
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply podcast preset: {e}")
            return False

    def apply_karaoke_effect(self, input_path: str, output_path: str) -> bool:
        """应用卡拉OK效果"""
        try:
            # 移除人声（中央通道）
            filter_chain = "stereotools=muter=true"

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-af', filter_chain,
                '-c:a', 'aac',
                '-b:a', '192k',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply karaoke effect: {e}")
            return False

    def apply_robot_voice(self, input_path: str, output_path: str) -> bool:
        """应用机器人音效"""
        try:
            filter_parts = []

            # 变调效果
            filter_parts.append("rubberband=pitch=1.5")

            # 添加失真
            filter_parts.append("overdrive=g=10")

            # 低通滤波
            filter_parts.append("lowpass=f=3000")

            filter_chain = ",".join(filter_parts)

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-af', filter_chain,
                '-c:a', 'aac',
                '-b:a', '192k',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to apply robot voice: {e}")
            return False

    def batch_apply_audio_effects(self, input_path: str, output_path: str,
                                effects: List[Dict[str, Any]]) -> bool:
        """批量应用音频效果"""
        try:
            filter_parts = []

            for effect in effects:
                effect_name = effect.get("name")
                parameters = effect.get("parameters", {})

                if effect_name == "equalizer":
                    low_freq = parameters.get("low_freq", 0.0)
                    mid_freq = parameters.get("mid_freq", 0.0)
                    high_freq = parameters.get("high_freq", 0.0)
                    filter_parts.append(f"equalizer=f=200:width_type=o:width=2:g={low_freq}")
                    filter_parts.append(f"equalizer=f=2000:width_type=o:width=2:g={mid_freq}")
                    filter_parts.append(f"equalizer=f=8000:width_type=o:width=2:g={high_freq}")

                elif effect_name == "volume":
                    volume = parameters.get("volume", 1.0)
                    filter_parts.append(f"volume={volume}")

                elif effect_name == "compressor":
                    threshold = parameters.get("threshold", -20.0)
                    ratio = parameters.get("ratio", 4.0)
                    attack = parameters.get("attack", 5.0)
                    release = parameters.get("release", 100.0)
                    filter_parts.append(f"compand=attacks={attack}:decays={release}:points=-80/-80|-{threshold}/{threshold}|0/0")

                elif effect_name == "reverb":
                    # 混响效果比较复杂，这里简化处理
                    filter_parts.append("aecho=0.8:0.9:1000|1800:0.3|0.25")

                elif effect_name == "highpass":
                    frequency = parameters.get("frequency", 80.0)
                    filter_parts.append(f"highpass=f={frequency}")

                elif effect_name == "lowpass":
                    frequency = parameters.get("frequency", 8000.0)
                    filter_parts.append(f"lowpass=f={frequency}")

            if not filter_parts:
                return False

            filter_chain = ",".join(filter_parts)

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-af', filter_chain,
                '-c:a', 'aac',
                '-b:a', '192k',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to batch apply audio effects: {e}")
            return False

    def get_audio_presets(self) -> Dict[str, Dict[str, Any]]:
        """获取音频预设"""
        return {
            AudioEffectPreset.VOCAL_ENHANCEMENT.value: {
                "name": "人声增强",
                "description": "优化人声清晰度和质量",
                "effects": [
                    {"name": "highpass", "parameters": {"frequency": 80}},
                    {"name": "equalizer", "parameters": {"low_freq": 0, "mid_freq": 3, "high_freq": 1}},
                    {"name": "compressor", "parameters": {"threshold": -20, "ratio": 4}}
                ]
            },
            AudioEffectPreset.MUSIC_MASTERING.value: {
                "name": "音乐母带",
                "description": "专业音乐母带处理",
                "effects": [
                    {"name": "equalizer", "parameters": {"low_freq": 2, "mid_freq": 1, "high_freq": -1}},
                    {"name": "compressor", "parameters": {"threshold": -15, "ratio": 2.5}},
                    {"name": "volume", "parameters": {"volume": 1.1}}
                ]
            },
            AudioEffectPreset.PODCAST.value: {
                "name": "播客优化",
                "description": "播客音频优化",
                "effects": [
                    {"name": "noise_reduction", "parameters": {"noise_reduction": 15}},
                    {"name": "compressor", "parameters": {"threshold": -18, "ratio": 6}},
                    {"name": "equalizer", "parameters": {"low_freq": -2, "mid_freq": 2, "high_freq": -1}}
                ]
            },
            AudioEffectPreset.KARAOKE.value: {
                "name": "卡拉OK",
                "description": "移除人声，保留伴奏",
                "effects": [
                    {"name": "stereotools", "parameters": {"muter": True}}
                ]
            },
            AudioEffectPreset.ROBOT_VOICE.value: {
                "name": "机器人音效",
                "description": "机器人效果处理",
                "effects": [
                    {"name": "pitch", "parameters": {"pitch_shift": 5}},
                    {"name": "lowpass", "parameters": {"frequency": 3000}}
                ]
            },
            AudioEffectPreset.UNDERWATER.value: {
                "name": "水下音效",
                "description": "水下环境音效",
                "effects": [
                    {"name": "lowpass", "parameters": {"frequency": 2000}},
                    {"name": "reverb", "parameters": {"room_size": 0.8, "wet_level": 0.6}}
                ]
            }
        }

    def apply_audio_preset(self, input_path: str, output_path: str,
                          preset_name: str) -> bool:
        """应用音频预设"""
        try:
            presets = self.get_audio_presets()
            preset = presets.get(preset_name)

            if not preset:
                self.logger.error(f"Unknown preset: {preset_name}")
                return False

            effects = preset.get("effects", [])
            return self.batch_apply_audio_effects(input_path, output_path, effects)

        except Exception as e:
            self.logger.error(f"Failed to apply audio preset: {e}")
            return False

    def get_audio_info(self, input_path: str) -> Optional[Dict[str, Any]]:
        """获取音频信息"""
        try:
            # 使用FFprobe获取音频信息
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                input_path
            ]

            result = self.ffmpeg_utils.run_ffprobe_command(cmd)
            if result:
                return self._parse_audio_info(result)

        except Exception as e:
            self.logger.error(f"Failed to get audio info: {e}")

        return None

    def _parse_audio_info(self, probe_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析音频信息"""
        try:
            info = {
                "duration": 0.0,
                "sample_rate": 0,
                "channels": 0,
                "bitrate": 0,
                "codec": "unknown"
            }

            # 格式信息
            format_info = probe_data.get("format", {})
            info["duration"] = float(format_info.get("duration", 0))
            info["bitrate"] = int(format_info.get("bit_rate", 0))

            # 流信息
            streams = probe_data.get("streams", [])
            for stream in streams:
                if stream.get("codec_type") == "audio":
                    info["sample_rate"] = int(stream.get("sample_rate", 0))
                    info["channels"] = int(stream.get("channels", 0))
                    info["codec"] = stream.get("codec_name", "unknown")
                    break

            return info

        except Exception as e:
            self.logger.error(f"Failed to parse audio info: {e}")
            return {}

    def normalize_audio(self, input_path: str, output_path: str,
                       target_level: float = -16.0) -> bool:
        """音频归一化"""
        try:
            # 使用音频归一化滤镜
            filter_chain = f"loudnorm=I={target_level}:TP=-1.5:LRA=11"

            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-af', filter_chain,
                '-c:a', 'aac',
                '-b:a', '192k',
                '-y', output_path
            ]

            return self.ffmpeg_utils.run_ffmpeg_command(cmd)

        except Exception as e:
            self.logger.error(f"Failed to normalize audio: {e}")
            return False

    def get_effect_compatibility(self) -> Dict[str, bool]:
        """获取效果兼容性"""
        return {
            "real_time_effects": True,
            "batch_processing": True,
            "multi_channel": True,
            "high_quality": True,
            "preset_system": True
        }