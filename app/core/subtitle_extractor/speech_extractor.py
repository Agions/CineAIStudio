#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
语音字幕提取器
使用语音识别技术从视频音频中提取字幕文本
"""

import os
import time
import tempfile
import subprocess
from typing import List, Optional, Dict, Any
from pathlib import Path

from .subtitle_models import SubtitleSegment, SubtitleTrack, SubtitleExtractorResult


class SpeechExtractor:
    """语音字幕提取器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化语音提取器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.whisper_model = None
        self.model_size = self.config.get('model_size', 'base')  # tiny, base, small, medium, large
        self.language = self.config.get('language', 'zh')  # 语言代码
        self.device = self.config.get('device', 'cpu')  # cpu, cuda
        
        self._init_models()
    
    def _init_models(self):
        """初始化语音识别模型"""
        try:
            import whisper
            print(f"正在加载Whisper模型: {self.model_size}")
            self.whisper_model = whisper.load_model(self.model_size, device=self.device)
            print("✅ Whisper模型加载成功")
        except ImportError:
            print("⚠️ Whisper未安装，请运行: pip install openai-whisper")
        except Exception as e:
            print(f"❌ Whisper模型加载失败: {e}")
    
    def extract_subtitles(self, video_path: str, progress_callback=None) -> SubtitleExtractorResult:
        """
        从视频中提取语音字幕
        
        Args:
            video_path: 视频文件路径
            progress_callback: 进度回调函数
            
        Returns:
            字幕提取结果
        """
        start_time = time.time()
        result = SubtitleExtractorResult()
        
        try:
            if not self.whisper_model:
                raise RuntimeError("Whisper模型未初始化")
            
            # 提取音频
            if progress_callback:
                progress_callback(10, "正在提取音频...")
            
            audio_path = self._extract_audio(video_path)
            
            if progress_callback:
                progress_callback(30, "正在进行语音识别...")
            
            # 语音识别
            transcribe_result = self.whisper_model.transcribe(
                audio_path,
                language=self.language if self.language != 'auto' else None,
                word_timestamps=True,
                verbose=False
            )
            
            if progress_callback:
                progress_callback(80, "正在处理识别结果...")
            
            # 处理识别结果
            segments = self._process_transcribe_result(transcribe_result)
            
            if segments:
                track = SubtitleTrack(segments, language=self.language, source="speech")
                result.add_track(track)
            
            # 清理临时文件
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            result.processing_time = time.time() - start_time
            result.metadata = {
                "model_size": self.model_size,
                "language": transcribe_result.get("language", "unknown"),
                "segments_count": len(segments)
            }
            
            if progress_callback:
                progress_callback(100, "语音识别完成")
            
            print(f"语音识别完成，耗时: {result.processing_time:.2f}秒")
            
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            print(f"语音识别失败: {e}")
        
        return result
    
    def _extract_audio(self, video_path: str) -> str:
        """
        从视频中提取音频
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            音频文件路径
        """
        # 创建临时音频文件
        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, f"temp_audio_{int(time.time())}.wav")
        
        try:
            # 使用ffmpeg提取音频
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # 不要视频
                '-acodec', 'pcm_s16le',  # 音频编码
                '-ar', '16000',  # 采样率
                '-ac', '1',  # 单声道
                '-y',  # 覆盖输出文件
                audio_path
            ]
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not os.path.exists(audio_path):
                raise RuntimeError("音频提取失败")
            
            return audio_path
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffmpeg执行失败: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("ffmpeg未找到，请确保已安装ffmpeg")
    
    def _process_transcribe_result(self, result: Dict[str, Any]) -> List[SubtitleSegment]:
        """
        处理Whisper识别结果
        
        Args:
            result: Whisper识别结果
            
        Returns:
            字幕片段列表
        """
        segments = []
        
        try:
            for segment_data in result.get("segments", []):
                # 基本信息
                start_time = segment_data.get("start", 0.0)
                end_time = segment_data.get("end", 0.0)
                text = segment_data.get("text", "").strip()
                
                if not text:
                    continue
                
                # 计算置信度（Whisper没有直接提供，使用平均概率）
                confidence = 1.0
                if "avg_logprob" in segment_data:
                    # 将对数概率转换为置信度
                    avg_logprob = segment_data["avg_logprob"]
                    confidence = min(1.0, max(0.0, (avg_logprob + 1.0)))
                
                # 检测说话人（如果有词级时间戳）
                speaker_id = None
                if "words" in segment_data:
                    # 这里可以添加说话人分离逻辑
                    pass
                
                segment = SubtitleSegment(
                    start_time=start_time,
                    end_time=end_time,
                    text=text,
                    confidence=confidence,
                    speaker_id=speaker_id,
                    language=result.get("language", "zh")
                )
                
                segments.append(segment)
        
        except Exception as e:
            print(f"处理识别结果时出错: {e}")
        
        return segments
    
    def extract_with_speaker_diarization(self, video_path: str, progress_callback=None) -> SubtitleExtractorResult:
        """
        带说话人分离的语音识别
        
        Args:
            video_path: 视频文件路径
            progress_callback: 进度回调函数
            
        Returns:
            字幕提取结果
        """
        # 这里可以集成pyannote.audio等说话人分离库
        # 目前先使用基础的语音识别
        return self.extract_subtitles(video_path, progress_callback)
    
    def set_model_size(self, model_size: str):
        """
        设置模型大小
        
        Args:
            model_size: 模型大小 (tiny, base, small, medium, large)
        """
        if model_size != self.model_size:
            self.model_size = model_size
            self._init_models()
    
    def set_language(self, language: str):
        """
        设置识别语言
        
        Args:
            language: 语言代码 (zh, en, auto等)
        """
        self.language = language
    
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        try:
            import whisper
            return list(whisper.tokenizer.LANGUAGES.keys())
        except:
            return ["zh", "en", "ja", "ko", "fr", "de", "es", "ru"]
    
    def estimate_processing_time(self, video_path: str) -> float:
        """
        估算处理时间
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            预估处理时间(秒)
        """
        try:
            # 获取视频时长
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            duration = float(result.stdout.strip())
            
            # 根据模型大小估算处理时间
            time_factors = {
                'tiny': 0.1,
                'base': 0.2,
                'small': 0.3,
                'medium': 0.5,
                'large': 0.8
            }
            
            factor = time_factors.get(self.model_size, 0.3)
            estimated_time = duration * factor
            
            return estimated_time
            
        except Exception as e:
            print(f"估算处理时间失败: {e}")
            return 60.0  # 默认返回60秒


class AdvancedSpeechExtractor(SpeechExtractor):
    """高级语音提取器，支持更多功能"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.enable_vad = config.get('enable_vad', True)  # 语音活动检测
        self.enable_noise_reduction = config.get('enable_noise_reduction', True)  # 降噪
        self.chunk_length = config.get('chunk_length', 30)  # 分块长度(秒)
    
    def extract_subtitles_chunked(self, video_path: str, progress_callback=None) -> SubtitleExtractorResult:
        """
        分块处理长视频
        
        Args:
            video_path: 视频文件路径
            progress_callback: 进度回调函数
            
        Returns:
            字幕提取结果
        """
        start_time = time.time()
        result = SubtitleExtractorResult()
        
        try:
            # 获取视频时长
            duration = self._get_video_duration(video_path)
            
            # 计算分块
            chunks = []
            current_time = 0
            while current_time < duration:
                end_time = min(current_time + self.chunk_length, duration)
                chunks.append((current_time, end_time))
                current_time = end_time
            
            print(f"视频时长: {duration:.2f}秒, 分为{len(chunks)}块处理")
            
            all_segments = []
            
            for i, (start, end) in enumerate(chunks):
                if progress_callback:
                    progress = (i / len(chunks)) * 100
                    progress_callback(progress, f"处理第{i+1}/{len(chunks)}块...")
                
                # 提取音频片段
                audio_path = self._extract_audio_chunk(video_path, start, end)
                
                # 识别音频片段
                chunk_result = self.whisper_model.transcribe(
                    audio_path,
                    language=self.language if self.language != 'auto' else None,
                    word_timestamps=True,
                    verbose=False
                )
                
                # 处理结果并调整时间戳
                chunk_segments = self._process_transcribe_result(chunk_result)
                for segment in chunk_segments:
                    segment.start_time += start
                    segment.end_time += start
                
                all_segments.extend(chunk_segments)
                
                # 清理临时文件
                if os.path.exists(audio_path):
                    os.remove(audio_path)
            
            if all_segments:
                track = SubtitleTrack(all_segments, language=self.language, source="speech")
                result.add_track(track)
            
            result.processing_time = time.time() - start_time
            result.metadata = {
                "model_size": self.model_size,
                "chunks_count": len(chunks),
                "total_segments": len(all_segments)
            }
            
            if progress_callback:
                progress_callback(100, "分块处理完成")
            
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            print(f"分块处理失败: {e}")
        
        return result
    
    def _get_video_duration(self, video_path: str) -> float:
        """获取视频时长"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip())
        except:
            return 0.0
    
    def _extract_audio_chunk(self, video_path: str, start_time: float, end_time: float) -> str:
        """提取音频片段"""
        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, f"chunk_{int(start_time)}_{int(time.time())}.wav")
        
        try:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', str(start_time),
                '-t', str(end_time - start_time),
                '-vn',
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                '-y',
                audio_path
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            return audio_path
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"音频片段提取失败: {e}")
