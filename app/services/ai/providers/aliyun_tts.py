#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
阿里云语音合成提供商
支持 10+ 种语音风格和精细化参数控制
"""

from typing import List, Dict, Any
import httpx
import base64
from pathlib import Path


try:
    from .voice_generator import TTSProvider, VoiceConfig, GeneratedVoice, VoiceInfo, VoiceGender, VoiceStyle as BaseVoiceStyle
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from app.services.ai.voice_generator import TTSProvider, VoiceConfig, GeneratedVoice, VoiceInfo, VoiceGender, VoiceStyle as BaseVoiceStyle


class AliyunVoiceStyle:
    """阿里云 TTS 风格枚举"""
    # 普通话风格
    XIAOYUN = "xiaoyun"          # 小云 - 温柔女声
    XIAOGANG = "xiaogang"        # 小刚 - 磁性男声
    XIAOQI = "xiaoqi"            # 小琪 - 知性女声
    XIAOMEI = "iaomei"           # 小美 - 活泼女声
    SITONG = "sitong"            # 思佟 - 新闻播报
    AITONG = "aitong"            # 艾佟 - 客服
    AIXIA = "aixia"              # 艾晓 - 情感丰富
    
    # 方言风格
    XIAOJUN = "xiaojun"          # 小君 - 东北话
    XIAOFENG = "xiaofeng"        # 小峰 - 四川话
    XIAOXIN = "xiaoxin"          # 小新 - 粤语
    
    # 英语等多语言
    ALICE = "alice"              # Alice - 美式英语女声


class AliyunTTSProvider(TTSProvider):
    """
    阿里云语音合成提供商
    
    支持特点:
    - 20+ 种声音风格
    - 情感语音合成（带情感标签）
    - SSML 支持
    - 多语言支持（中文、英文、方言）
    
    官方文档: https://help.aliyun.com/document_detail/84435.html
    """
    
    # 声音映射表
    VOICES = {
        "female": [
            ("xiaoyun", "小云", "温柔女声", ["narration", "conversational"]),
            ("xiaogi", "小琪", "知性女声", ["narration", "news"]),
            ("xiaomei", "小美", "活沷女声", ["cheerful", "conversational"]),
            ("sitong", "思佟", "新闻播报", ["news", "narration"]),
            ("aitong", "艾佟", "客服声音", ["conversational", "cheerful"]),
            ("aixia", "艾晓", "情感丰富", ["emotional", "narration"]),
            ("xiaojun", "小君", "东北话", ["conversational"]),
            ("xiaofeng", "小峰", "四川话", ["conversational"]),
            ("xiaoxin", "小新", "粤语", ["conversational"]),
        ],
        "male": [
            ("xiaogang", "小刚", "磁性男声", ["narration", "news"]),
        ],
        "english": [
            ("alice", "Alice", "美式英语", ["narration"]),
        ],
    }
    
    # 风格到音色 ID 的映射
    STYLE_MAPPING = {
        "narration": "xiaoyun",           # 旁白
        "conversational": "xiaoyun",      # 对话
        "newscast": "sitong",             # 新闻
        "cheerful": "xiaomei",            # 欢快
        "sad": "aixia",                   # 悲伤
        "angry": "xiaogang",              # 愤怒
        "whispering": "xiaoyun",          # 耳语
        "emotional": "aixia",             # 情感
    }
    
    def __init__(self, appkey: str, access_key_id: str, access_key_secret: str):
        """
        初始化提供商
        
        Args:
            appkey: 项目 AppKey
            access_key_id: AccessKey ID
            access_key_secret: AccessKey Secret
        """
        self.appkey = appkey
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        
        # 使用 NLS Cloud SDK 或直接 HTTP API
        self.http_client = httpx.Client(timeout=60.0)
        
    def generate(
        self,
        text: str,
        output_path: str,
        config: VoiceConfig,
    ) -> GeneratedVoice:
        """
        生成语音
        
        Args:
            text: 要合成的文本
            output_path: 输出文件路径
            config: 语音配置
            
        Returns:
            生成的语音信息
        """
        # 选择声音
        voice_id = self._select_voice(config)
        
        # 构建请求参数
        params = {
            "appkey": self.appkey,
            "token": self._get_token(),
            "text": text,
            "format": config.output_format,
            "sample_rate": config.sample_rate,
            "voice": voice_id,
            "volume": int(config.volume * 100),  # 0-100
            "speech_rate": int(config.rate * 100),  # 相对百分比
            "pitch_rate": int(config.pitch * 100),  # 相对百分比
        }
        
        # 添加情感标签
        emotion = self._get_emotion_tag(config.style)
        if emotion:
            params["emotion"] = emotion
        
        try:
            # 调用阿里云 API
            response = self.http_client.post(
                "https://nls-gateway.cn-shanghai.aliyuncs.com/stream/v1/tts",
                params=params,
            )
            response.raise_for_status()
            
            # 保存音频文件
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            # 获取时长
            duration = self._get_audio_duration(output_path)
            
            return GeneratedVoice(
                audio_path=output_path,
                duration=duration,
                text=text,
                voice_id=voice_id,
                format=config.output_format,
                sample_rate=config.sample_rate,
            )
            
        except Exception as e:
            raise RuntimeError(f"阿里云 TTS 生成失败: {str(e)}")
    
    def generate_with_emotion(
        self,
        text: str,
        output_path: str,
        voice_id: str = None,
        emotion: str = "happy",
        emotion_intensity: float = 1.0,
        **kwargs
    ) -> GeneratedVoice:
        """
        带情感的语音生成
        
        Args:
            text: 文本
            output_path: 输出路径
            voice_id: 声音 ID
            emotion: 情感类型
            emotion_intensity: 情感强度 (0.0-2.0)
            **kwargs: 其他参数
            
        Returns:
            生成的语音
        """
        config = VoiceConfig(
            voice_id=voice_id or "xiaoyun",
            **kwargs
        )
        
        # 情感映射到风格
        emotion_map = {
            "happy": VoiceStyle.CHEERFUL,
            "sad": VoiceStyle.SAD,
            "angry": VoiceStyle.ANGRY,
            "fear": VoiceStyle.FEARFUL,
            "neutral": VoiceStyle.NARRATION,
        }
        
        config.style = emotion_map.get(emotion, VoiceStyle.NARRATION)
        config.style_degree = emotion_intensity
        
        return self.generate(text, output_path, config)
    
    def _select_voice(self, config: VoiceConfig) -> str:
        """根据配置选择声音"""
        # 如果指定了 voice_id 直接使用
        if config.voice_id:
            return config.voice_id
        
        # 根据性别和风格选择
        gender_key = config.gender.value
        
        # 优先根据风格
        style = config.style.value
        if style in self.STYLE_MAPPING:
            suggested_voice = self.STYLE_MAPPING[style]
            # 验证声音存在
            for voices in self.VOICES.values():
                for vid, _, _, styles in voices:
                    if vid == suggested_voice:
                        return suggested_voice
        
        # 默认返回第一个可用声音
        return "xiaoyun"
    
    def _get_emotion_tag(self, style) -> str:
        """获取情感标签"""
        emotion_map = {
            VoiceStyle.CHEERFUL: "happy",
            VoiceStyle.SAD: "sad",
            VoiceStyle.ANGRY: "angry",
            VoiceStyle.FEARFUL: "fearful",
        }
        return emotion_map.get(style, None)
    
    def _get_token(self) -> str:
        """获取访问 token（简化版）"""
        # 实际应该调用 STS 接口获取 token
        # 这里简化处理
        import hashlib
        import time
        timestamp = str(int(time.time()))
        signature = hashlib.md5(
            f"{self.access_key_id}:{self.access_key_secret}:{timestamp}".encode()
        ).hexdigest()
        return f"{self.access_key_id}:{timestamp}:{signature}"
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长"""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_path)
            return len(audio) / 1000.0
        except:
            pass
        
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
        except:
            pass
        
        return 0.0
    
    def list_voices(self, language: str = "zh-CN") -> List[VoiceInfo]:
        """列出可用声音"""
        voices = []
        
        for gender, voice_list in self.VOICES.items():
            gender_enum = VoiceGender.FEMALE if gender == "female" else VoiceGender.MALE
            
            for vid, name, desc, styles in voice_list:
                voices.append(VoiceInfo(
                    id=vid,
                    name=f"{name} ({desc})",
                    gender=gender_enum,
                    language=language,
                    styles=styles,
                    description=desc,
                ))
        
        return voices
    
    def get_available_emotions(self) -> List[Dict[str, str]]:
        """获取可用情感"""
        return [
            {"emotion": "happy", "name": "开心", "voice": "xiaomei"},
            {"emotion": "sad", "name": "悲伤", "voice": "aixia"},
            {"emotion": "angry", "name": "愤怒", "voice": "xiaogang"},
            {"emotion": "fearful", "name": "恐惧", "voice": "aixia"},
            {"emotion": "neutral", "name": "平静", "voice": "xiaoyun"},
        ]
    
    def get_available_dialects(self) -> List[Dict[str, str]]:
        """获取可用方言"""
        return [
            {"dialect": "dongbei", "name": "东北话", "voice": "xiaojun"},
            {"dialect": "sichuan", "name": "四川话", "voice": "xiaofeng"},
            {"dialect": "cantonese", "name": "粤语", "voice": "xiaoxin"},
        ]
    
    def close(self):
        """关闭连接"""
        self.http_client.close()


# 风格枚举扩展
class ExtendedVoiceStyle:
    """扩展的语音风格枚举"""
    NARRATION = "narration"
    CONVERSATIONAL = "conversational"
    NEWSCAST = "newscast"
    CHEERFUL = "cheerful"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    WHISPERING = "whispering"
    SHOUTING = "shouting"
    EMOTIONAL = "emotional"
    ROMANTIC = "romantic"
    JOYFUL = "joyful"
    SERIOUS = "serious"
    CASUAL = "casual"
    EXCITED = "excited"
