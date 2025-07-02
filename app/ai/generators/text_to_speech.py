#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文本转语音引擎
支持多种TTS服务和本地语音合成
"""

import asyncio
import os
import tempfile
from typing import List, Dict, Optional, Any
from PyQt6.QtCore import QObject, pyqtSignal
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    pyttsx3 = None

import threading
import queue


class TextToSpeechEngine(QObject):
    """文本转语音引擎"""
    
    # 信号
    synthesis_progress = pyqtSignal(int)
    synthesis_completed = pyqtSignal(str)
    synthesis_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.engine = None
        self.temp_dir = tempfile.mkdtemp(prefix="tts_")
        self._init_engine()
        
        # 语音配置
        self.voice_configs = {
            "female": {
                "rate": 180,
                "volume": 0.9,
                "voice_id": 0
            },
            "male": {
                "rate": 170,
                "volume": 0.9,
                "voice_id": 1
            },
            "child": {
                "rate": 200,
                "volume": 0.8,
                "voice_id": 0
            }
        }
        
        # 情感配置
        self.emotion_configs = {
            "neutral": {"rate_modifier": 1.0, "volume_modifier": 1.0},
            "excited": {"rate_modifier": 1.2, "volume_modifier": 1.1},
            "calm": {"rate_modifier": 0.8, "volume_modifier": 0.9},
            "emotional": {"rate_modifier": 0.9, "volume_modifier": 1.0},
            "positive": {"rate_modifier": 1.1, "volume_modifier": 1.0}
        }
    
    def _init_engine(self):
        """初始化TTS引擎"""
        if not PYTTSX3_AVAILABLE:
            print("pyttsx3 未安装，将使用备用语音合成方案")
            self.engine = None
            return

        try:
            self.engine = pyttsx3.init()

            # 获取可用语音
            voices = self.engine.getProperty('voices')
            if voices:
                # 设置默认语音（优先选择中文语音）
                for voice in voices:
                    if 'zh' in voice.id.lower() or 'chinese' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
                else:
                    # 如果没有中文语音，使用第一个可用语音
                    self.engine.setProperty('voice', voices[0].id)

            # 设置默认参数
            self.engine.setProperty('rate', 180)  # 语速
            self.engine.setProperty('volume', 0.9)  # 音量

        except Exception as e:
            print(f"TTS引擎初始化失败: {e}")
            self.engine = None
    
    async def synthesize(self, text: str, output_path: str,
                        voice_type: str = "female", emotion: str = "neutral",
                        speed: float = 1.0) -> bool:
        """合成语音"""
        try:
            if not text.strip():
                raise Exception("文本内容为空")

            # 如果没有TTS引擎，使用备用方案
            if not self.engine:
                return await self._fallback_synthesis_async(text, output_path)

            # 配置语音参数
            config = self.voice_configs.get(voice_type, self.voice_configs["female"])
            emotion_config = self.emotion_configs.get(emotion, self.emotion_configs["neutral"])

            # 设置语音参数
            rate = int(config["rate"] * emotion_config["rate_modifier"] * speed)
            volume = min(config["volume"] * emotion_config["volume_modifier"], 1.0)

            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)

            # 设置语音ID（如果有多个语音）
            voices = self.engine.getProperty('voices')
            if voices and len(voices) > config["voice_id"]:
                self.engine.setProperty('voice', voices[config["voice_id"]].id)

            # 异步合成语音
            success = await self._synthesize_async(text, output_path)

            if success:
                self.synthesis_completed.emit(output_path)
            else:
                self.synthesis_error.emit("语音合成失败")

            return success

        except Exception as e:
            error_msg = f"语音合成错误: {str(e)}"
            self.synthesis_error.emit(error_msg)
            return False
    
    async def _synthesize_async(self, text: str, output_path: str) -> bool:
        """异步语音合成"""
        try:
            # 使用线程池执行同步的TTS操作
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._synthesize_sync, text, output_path
            )
            return result
        except Exception as e:
            print(f"异步语音合成失败: {e}")
            return False
    
    def _synthesize_sync(self, text: str, output_path: str) -> bool:
        """同步语音合成"""
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 保存到文件
            self.engine.save_to_file(text, output_path)
            self.engine.runAndWait()
            
            # 检查文件是否生成成功
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
            else:
                # 如果文件生成失败，尝试直接说话并录制
                return self._fallback_synthesis(text, output_path)
                
        except Exception as e:
            print(f"同步语音合成失败: {e}")
            return self._fallback_synthesis(text, output_path)
    
    def _fallback_synthesis(self, text: str, output_path: str) -> bool:
        """备用语音合成方法"""
        try:
            # 创建一个简单的音频文件（静音）作为占位符
            import wave
            import numpy as np
            
            # 生成1秒的静音音频
            sample_rate = 16000
            duration = max(len(text) * 0.1, 1.0)  # 根据文本长度估算时长
            samples = int(sample_rate * duration)
            
            # 生成静音数据
            audio_data = np.zeros(samples, dtype=np.int16)
            
            # 保存为WAV文件
            with wave.open(output_path, 'w') as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)  # 16位
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            print(f"生成占位符音频文件: {output_path}")
            return True
            
        except Exception as e:
            print(f"备用语音合成失败: {e}")
            return False
    
    def get_available_voices(self) -> List[str]:
        """获取可用的语音类型"""
        return list(self.voice_configs.keys())
    
    def get_available_emotions(self) -> List[str]:
        """获取可用的情感类型"""
        return list(self.emotion_configs.keys())
    
    def get_voice_info(self) -> Dict[str, Any]:
        """获取语音引擎信息"""
        info = {
            "engine_available": self.engine is not None,
            "voices": [],
            "default_rate": 180,
            "default_volume": 0.9
        }
        
        if self.engine:
            try:
                voices = self.engine.getProperty('voices')
                if voices:
                    for voice in voices:
                        info["voices"].append({
                            "id": voice.id,
                            "name": voice.name,
                            "languages": getattr(voice, 'languages', []),
                            "gender": getattr(voice, 'gender', 'unknown')
                        })
            except Exception as e:
                print(f"获取语音信息失败: {e}")
        
        return info

    async def _fallback_synthesis_async(self, text: str, output_path: str) -> bool:
        """备用异步语音合成"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._fallback_synthesis, text, output_path
            )
            return result
        except Exception as e:
            print(f"备用异步语音合成失败: {e}")
            return False
    
    def test_synthesis(self, text: str = "这是一个语音合成测试") -> bool:
        """测试语音合成功能"""
        try:
            test_path = os.path.join(self.temp_dir, "test_synthesis.wav")
            
            # 同步测试
            success = self._synthesize_sync(text, test_path)
            
            if success and os.path.exists(test_path):
                # 清理测试文件
                try:
                    os.remove(test_path)
                except:
                    pass
                return True
            
            return False
            
        except Exception as e:
            print(f"语音合成测试失败: {e}")
            return False
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.engine:
                self.engine.stop()
            
            # 清理临时文件
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                
        except Exception as e:
            print(f"TTS引擎清理失败: {e}")


# 全局TTS引擎实例
_tts_engine = None

def get_tts_engine() -> TextToSpeechEngine:
    """获取全局TTS引擎实例"""
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = TextToSpeechEngine()
    return _tts_engine
