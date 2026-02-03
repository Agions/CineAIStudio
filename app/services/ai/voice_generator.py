"""
AI 配音生成器 (Voice Generator)

将文本转换为高质量 AI 配音。

支持多种 TTS 后端:
- Azure Speech (推荐，支持情感)
- OpenAI TTS
- Edge TTS (免费)

使用示例:
    from app.services.ai import VoiceGenerator, VoiceConfig, VoiceStyle
    
    generator = VoiceGenerator(provider="edge")
    
    audio_path = generator.generate(
        text="欢迎观看这个视频",
        output_path="output.mp3",
        style=VoiceStyle.NARRATION,
    )
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod


class VoiceStyle(Enum):
    """配音风格"""
    NARRATION = "narration"        # 旁白/解说
    CONVERSATIONAL = "conversational"  # 对话
    NEWSCAST = "newscast"          # 新闻播报
    CHEERFUL = "cheerful"          # 欢快
    SAD = "sad"                    # 悲伤
    ANGRY = "angry"                # 愤怒
    FEARFUL = "fearful"            # 恐惧
    WHISPERING = "whispering"      # 耳语
    SHOUTING = "shouting"          # 大喊


class VoiceGender(Enum):
    """声音性别"""
    MALE = "male"
    FEMALE = "female"


@dataclass
class VoiceConfig:
    """配音配置"""
    # 声音选择
    voice_id: str = ""             # 声音 ID（不同提供商格式不同）
    gender: VoiceGender = VoiceGender.FEMALE
    
    # 风格
    style: VoiceStyle = VoiceStyle.NARRATION
    style_degree: float = 1.0      # 风格强度 (0.5-2.0)
    
    # 语速语调
    rate: float = 1.0              # 语速 (0.5-2.0)
    pitch: float = 1.0             # 音调 (0.5-2.0)
    volume: float = 1.0            # 音量 (0.0-1.0)
    
    # 输出格式
    output_format: str = "mp3"     # mp3, wav, ogg
    sample_rate: int = 24000       # 采样率
    
    # 语言
    language: str = "zh-CN"


@dataclass
class VoiceInfo:
    """声音信息"""
    id: str
    name: str
    gender: VoiceGender
    language: str
    styles: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class GeneratedVoice:
    """生成的配音"""
    audio_path: str                # 音频文件路径
    duration: float                # 时长（秒）
    text: str                      # 原始文本
    voice_id: str                  # 使用的声音
    
    # 元数据
    sample_rate: int = 24000
    format: str = "mp3"


class TTSProvider(ABC):
    """TTS 提供者抽象基类"""
    
    @abstractmethod
    def generate(
        self,
        text: str,
        output_path: str,
        config: VoiceConfig,
    ) -> GeneratedVoice:
        """生成配音"""
        pass
    
    @abstractmethod
    def list_voices(self, language: str = "zh-CN") -> List[VoiceInfo]:
        """列出可用声音"""
        pass


class EdgeTTSProvider(TTSProvider):
    """
    Edge TTS 提供者（免费）
    
    使用微软 Edge 的 TTS 服务，无需 API Key
    
    安装: pip install edge-tts
    """
    
    # 中文推荐声音
    CHINESE_VOICES = {
        "female": [
            ("zh-CN-XiaoxiaoNeural", "晓晓 - 温柔女声"),
            ("zh-CN-XiaoyiNeural", "晓依 - 知性女声"),
            ("zh-CN-XiaohanNeural", "晓涵 - 甜美女声"),
            ("zh-CN-XiaomoNeural", "晓墨 - 成熟女声"),
            ("zh-CN-XiaoxuanNeural", "晓萱 - 活泼女声"),
            ("zh-CN-XiaoruiNeural", "晓睿 - 少女音"),
        ],
        "male": [
            ("zh-CN-YunxiNeural", "云希 - 阳光男声"),
            ("zh-CN-YunjianNeural", "云健 - 磁性男声"),
            ("zh-CN-YunyangNeural", "云扬 - 新闻播报"),
        ],
    }
    
    def __init__(self):
        try:
            import edge_tts
            self.edge_tts = edge_tts
        except ImportError:
            raise ImportError("请安装 edge-tts: pip install edge-tts")
    
    def generate(
        self,
        text: str,
        output_path: str,
        config: VoiceConfig,
    ) -> GeneratedVoice:
        """生成配音"""
        # 选择声音
        voice = config.voice_id or self._select_voice(config)
        
        # 构建语速/音调参数
        rate_str = f"+{int((config.rate - 1) * 100)}%" if config.rate >= 1 else f"{int((config.rate - 1) * 100)}%"
        pitch_str = f"+{int((config.pitch - 1) * 50)}Hz" if config.pitch >= 1 else f"{int((config.pitch - 1) * 50)}Hz"
        
        # 异步生成
        async def _generate():
            communicate = self.edge_tts.Communicate(
                text,
                voice,
                rate=rate_str,
                pitch=pitch_str,
            )
            await communicate.save(output_path)
        
        asyncio.run(_generate())
        
        # 获取音频时长
        duration = self._get_audio_duration(output_path)
        
        return GeneratedVoice(
            audio_path=output_path,
            duration=duration,
            text=text,
            voice_id=voice,
            format=config.output_format,
        )
    
    def _select_voice(self, config: VoiceConfig) -> str:
        """根据配置选择声音"""
        gender_key = config.gender.value
        voices = self.CHINESE_VOICES.get(gender_key, self.CHINESE_VOICES["female"])
        
        # 根据风格选择
        if config.style == VoiceStyle.NEWSCAST:
            return "zh-CN-YunyangNeural"  # 新闻播报
        elif config.style == VoiceStyle.CHEERFUL:
            return "zh-CN-XiaoxuanNeural"  # 活泼
        elif config.style == VoiceStyle.CONVERSATIONAL:
            return "zh-CN-XiaoxiaoNeural"  # 对话
        else:
            return voices[0][0]  # 默认第一个
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长"""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_path)
            return len(audio) / 1000.0  # 毫秒转秒
        except ImportError:
            pass
        
        # 使用 ffprobe
        try:
            import subprocess
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'csv=p=0',
                audio_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception:
            pass
        
        return 0.0
    
    def list_voices(self, language: str = "zh-CN") -> List[VoiceInfo]:
        """列出可用声音"""
        voices = []
        
        for voice_id, name in self.CHINESE_VOICES["female"]:
            voices.append(VoiceInfo(
                id=voice_id,
                name=name,
                gender=VoiceGender.FEMALE,
                language=language,
            ))
        
        for voice_id, name in self.CHINESE_VOICES["male"]:
            voices.append(VoiceInfo(
                id=voice_id,
                name=name,
                gender=VoiceGender.MALE,
                language=language,
            ))
        
        return voices


class OpenAITTSProvider(TTSProvider):
    """
    OpenAI TTS 提供者
    
    使用 OpenAI 的 TTS API
    """
    
    VOICES = {
        "alloy": "Alloy - 中性",
        "echo": "Echo - 男声",
        "fable": "Fable - 英式男声",
        "onyx": "Onyx - 低沉男声",
        "nova": "Nova - 温柔女声",
        "shimmer": "Shimmer - 清脆女声",
    }
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("请安装 openai: pip install openai")
    
    def generate(
        self,
        text: str,
        output_path: str,
        config: VoiceConfig,
    ) -> GeneratedVoice:
        """生成配音"""
        voice = config.voice_id or "nova"  # 默认 nova
        
        # 语速映射 (OpenAI TTS 不支持精确控制，只能通过 SSML 或模型选择)
        speed = min(max(config.rate, 0.25), 4.0)
        
        response = self.client.audio.speech.create(
            model="tts-1-hd",
            voice=voice,
            input=text,
            speed=speed,
        )
        
        # 保存文件
        response.stream_to_file(output_path)
        
        # 获取时长
        duration = self._get_audio_duration(output_path)
        
        return GeneratedVoice(
            audio_path=output_path,
            duration=duration,
            text=text,
            voice_id=voice,
            format=config.output_format,
        )
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长"""
        try:
            import subprocess
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'csv=p=0',
                audio_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception:
            pass
        return 0.0
    
    def list_voices(self, language: str = "zh-CN") -> List[VoiceInfo]:
        """列出可用声音"""
        return [
            VoiceInfo(id=vid, name=name, gender=VoiceGender.FEMALE, language="en-US")
            for vid, name in self.VOICES.items()
        ]


class VoiceGenerator:
    """
    AI 配音生成器
    
    统一的配音生成接口，支持多种 TTS 后端
    
    使用示例:
        # 使用免费的 Edge TTS
        generator = VoiceGenerator(provider="edge")
        
        # 使用 OpenAI TTS
        generator = VoiceGenerator(provider="openai", api_key="sk-xxx")
        
        # 生成配音
        result = generator.generate(
            text="欢迎观看这个视频，今天我们来聊一聊AI的发展",
            output_path="voiceover.mp3",
        )
        print(f"配音时长: {result.duration:.2f}秒")
    """
    
    def __init__(
        self,
        provider: str = "edge",
        api_key: Optional[str] = None,
        **kwargs,
    ):
        """
        初始化配音生成器
        
        Args:
            provider: 提供者 ("edge", "openai", "azure")
            api_key: API Key（某些提供者需要）
        """
        self.provider_name = provider
        
        if provider == "edge":
            self._provider = EdgeTTSProvider()
        elif provider == "openai":
            key = api_key or os.getenv("OPENAI_API_KEY")
            if not key:
                raise ValueError("OpenAI TTS 需要 API Key")
            self._provider = OpenAITTSProvider(key)
        else:
            raise ValueError(f"不支持的提供者: {provider}")
    
    def generate(
        self,
        text: str,
        output_path: str,
        config: Optional[VoiceConfig] = None,
    ) -> GeneratedVoice:
        """
        生成配音
        
        Args:
            text: 要转换的文本
            output_path: 输出文件路径
            config: 配音配置
            
        Returns:
            生成的配音信息
        """
        config = config or VoiceConfig()
        
        # 确保输出目录存在
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        return self._provider.generate(text, output_path, config)
    
    def generate_segments(
        self,
        segments: List[Dict[str, Any]],
        output_dir: str,
        config: Optional[VoiceConfig] = None,
    ) -> List[GeneratedVoice]:
        """
        批量生成配音片段
        
        Args:
            segments: 片段列表，每个包含 text, start, duration
            output_dir: 输出目录
            config: 配音配置
            
        Returns:
            生成的配音列表
        """
        config = config or VoiceConfig()
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = []
        
        for i, segment in enumerate(segments):
            text = segment.get("text", "")
            if not text:
                continue
            
            file_path = output_path / f"segment_{i:03d}.mp3"
            
            result = self.generate(text, str(file_path), config)
            
            # 保留原始时间信息
            result.start_time = segment.get("start", 0.0)
            
            results.append(result)
        
        return results
    
    def list_voices(self, language: str = "zh-CN") -> List[VoiceInfo]:
        """列出可用声音"""
        return self._provider.list_voices(language)
    
    def preview_voice(
        self,
        voice_id: str,
        text: str = "你好，这是一段语音测试。欢迎使用 AI 配音功能。",
        output_path: str = "preview.mp3",
    ) -> GeneratedVoice:
        """预览指定声音"""
        config = VoiceConfig(voice_id=voice_id)
        return self.generate(text, output_path, config)


# =========== 便捷函数 ===========

def generate_voice(
    text: str,
    output_path: str,
    provider: str = "edge",
    voice: Optional[str] = None,
    rate: float = 1.0,
) -> GeneratedVoice:
    """
    快速生成配音
    
    Args:
        text: 文本
        output_path: 输出路径
        provider: 提供者
        voice: 声音 ID
        rate: 语速
    """
    generator = VoiceGenerator(provider=provider)
    config = VoiceConfig(voice_id=voice or "", rate=rate)
    return generator.generate(text, output_path, config)


def demo_generate():
    """演示配音生成"""
    print("=" * 50)
    print("AI 配音生成演示")
    print("=" * 50)
    
    # 使用免费的 Edge TTS
    generator = VoiceGenerator(provider="edge")
    
    # 列出可用声音
    print("\n可用声音:")
    for voice in generator.list_voices():
        print(f"  - {voice.id}: {voice.name}")
    
    # 生成配音
    text = """
    欢迎来到 CineAIStudio！
    这是一款 AI 驱动的视频创作工具。
    让我们一起创作爆款视频吧！
    """
    
    print(f"\n正在生成配音...")
    result = generator.generate(
        text=text.strip(),
        output_path="demo_voice.mp3",
        config=VoiceConfig(
            voice_id="zh-CN-XiaoxiaoNeural",
            rate=1.1,
        )
    )
    
    print(f"\n✅ 配音生成成功!")
    print(f"   文件: {result.audio_path}")
    print(f"   时长: {result.duration:.2f}秒")
    print(f"   声音: {result.voice_id}")


if __name__ == '__main__':
    demo_generate()
