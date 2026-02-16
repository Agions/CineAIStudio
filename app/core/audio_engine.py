"""
音频引擎核心服务
处理音频合成、TTS、音效
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import tempfile


@dataclass
class AudioInfo:
    """音频信息"""
    path: str
    duration: float
    sample_rate: int
    channels: int
    bitrate: int
    codec: str


@dataclass
class TTSTask:
    """TTS任务"""
    text: str
    voice: str
    speed: float = 1.0
    pitch: float = 0.0
    output_path: Optional[str] = None


class AudioEngine:
    """
    音频引擎
    
    提供音频处理功能：
    - 音频信息获取
    - 音频剪辑
    - 音频混合
    - TTS配音
    - 音效处理
    """
    
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffmpeg_path.replace("ffmpeg", "ffprobe")
        
    def get_audio_info(self, audio_path: str) -> AudioInfo:
        """获取音频信息"""
        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            audio_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        
        # 查找音频流
        audio_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'audio':
                audio_stream = stream
                break
                
        if not audio_stream:
            raise ValueError("未找到音频流")
            
        duration = float(data.get('format', {}).get('duration', 0))
        
        return AudioInfo(
            path=audio_path,
            duration=duration,
            sample_rate=int(audio_stream.get('sample_rate', 44100)),
            channels=int(audio_stream.get('channels', 2)),
            bitrate=int(data.get('format', {}).get('bit_rate', 0)),
            codec=audio_stream.get('codec_name', 'unknown')
        )
        
    def cut_audio(
        self,
        audio_path: str,
        start_time: float,
        end_time: float,
        output_path: str
    ) -> str:
        """剪辑音频"""
        duration = end_time - start_time
        
        cmd = [
            self.ffmpeg_path,
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", audio_path,
            "-c", "copy",
            "-y",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if not os.path.exists(output_path):
            raise RuntimeError(f"音频剪辑失败: {result.stderr}")
            
        return output_path
        
    def merge_audios(
        self,
        audio_paths: List[str],
        output_path: str,
        crossfade: float = 0.0
    ) -> str:
        """合并多个音频"""
        if len(audio_paths) == 1:
            import shutil
            shutil.copy(audio_paths[0], output_path)
            return output_path
            
        # 创建临时文件列表
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for path in audio_paths:
                f.write(f"file '{os.path.abspath(path)}'\n")
            concat_file = f.name
            
        try:
            cmd = [
                self.ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                "-y",
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if not os.path.exists(output_path):
                raise RuntimeError(f"音频合并失败: {result.stderr}")
                
        finally:
            os.unlink(concat_file)
            
        return output_path
        
    def mix_audios(
        self,
        audio_tracks: List[Dict[str, Any]],
        output_path: str
    ) -> str:
        """
        混音
        
        Args:
            audio_tracks: [
                {'path': str, 'volume': float, 'delay': float},
                ...
            ]
        """
        if len(audio_tracks) == 1:
            track = audio_tracks[0]
            volume = track.get('volume', 1.0)
            
            cmd = [
                self.ffmpeg_path,
                "-i", track['path'],
                "-af", f"volume={volume}",
                "-y",
                output_path
            ]
        else:
            # 多轨道混音
            inputs = []
            filters = []
            
            for i, track in enumerate(audio_tracks):
                inputs.extend(["-i", track['path']])
                volume = track.get('volume', 1.0)
                delay = track.get('delay', 0)
                
                if delay > 0:
                    filters.append(f"[{i}:a]adelay={int(delay*1000)}|{int(delay*1000)},volume={volume}[a{i}]")
                else:
                    filters.append(f"[{i}:a]volume={volume}[a{i}]")
                    
            # 构建amix
            mix_inputs = "".join([f"[a{i}]" for i in range(len(audio_tracks))])
            filters.append(f"{mix_inputs}amix=inputs={len(audio_tracks)}:duration=longest[outa]")
            
            cmd = [
                self.ffmpeg_path,
                *inputs,
                "-filter_complex", ";".join(filters),
                "-map", "[outa]",
                "-y",
                output_path
            ]
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if not os.path.exists(output_path):
            raise RuntimeError(f"混音失败: {result.stderr}")
            
        return output_path
        
    def apply_effects(
        self,
        audio_path: str,
        output_path: str,
        noise_reduction: bool = False,
        compression: Optional[float] = None,
        eq_bands: Optional[List[Dict]] = None,
        reverb: Optional[Dict] = None
    ) -> str:
        """应用音频效果"""
        filters = []
        
        # 降噪
        if noise_reduction:
            filters.append("arnndn=m=./models/rnnoise.rnnn")
            
        # 压缩
        if compression:
            filters.append(f"acompressor=threshold=-20dB:ratio={compression}")
            
        # EQ
        if eq_bands:
            eq_str = "equalizer=" + ":".join([
                f"f={band['freq']}:t=h:w={band.get('q', 1.0)*band['freq']/2}:g={band['gain']}"
                for band in eq_bands
            ])
            filters.append(eq_str)
            
        # 混响
        if reverb:
            room_size = reverb.get('room_size', 0.5)
            damping = reverb.get('damping', 0.5)
            filters.append(f"aecho=0.8:0.9:{int(room_size*1000)}|{int(room_size*1200)}:0.3|0.25")
            
        if not filters:
            import shutil
            shutil.copy(audio_path, output_path)
            return output_path
            
        filter_str = ",".join(filters)
        
        cmd = [
            self.ffmpeg_path,
            "-i", audio_path,
            "-af", filter_str,
            "-y",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if not os.path.exists(output_path):
            raise RuntimeError(f"应用效果失败: {result.stderr}")
            
        return output_path
        
    async def text_to_speech(
        self,
        task: TTSTask,
        provider: str = "edge"
    ) -> str:
        """
        文字转语音
        
        支持:
        - edge: Edge TTS (免费)
        - aliyun: 阿里云TTS
        """
        if task.output_path is None:
            task.output_path = tempfile.mktemp(suffix='.mp3')
            
        if provider == "edge":
            return await self._tts_edge(task)
        elif provider == "aliyun":
            return await self._tts_aliyun(task)
        else:
            raise ValueError(f"不支持的TTS提供商: {provider}")
            
    async def _tts_edge(self, task: TTSTask) -> str:
        """使用Edge TTS"""
        try:
            import edge_tts
            
            communicate = edge_tts.Communicate(
                text=task.text,
                voice=task.voice,
                rate=f"{int((task.speed - 1) * 100)}%",
                pitch=f"{int(task.pitch)}Hz"
            )
            
            await communicate.save(task.output_path)
            
            return task.output_path
            
        except ImportError:
            raise RuntimeError("未安装edge-tts: pip install edge-tts")
            
    async def _tts_aliyun(self, task: TTSTask) -> str:
        """使用阿里云TTS"""
        # TODO: 实现阿里云TTS调用
        raise NotImplementedError("阿里云TTS待实现")
        
    def detect_beats(
        self,
        audio_path: str,
        min_bpm: int = 60,
        max_bpm: int = 200
    ) -> List[float]:
        """
        检测音乐节拍
        
        返回节拍时间点列表
        """
        try:
            import librosa
            
            # 加载音频
            y, sr = librosa.load(audio_path, sr=None)
            
            # 获取节拍帧
            tempo, beat_frames = librosa.beat.beat_track(
                y=y,
                sr=sr,
                start_bpm=120,
                units='time'
            )
            
            return beat_frames.tolist()
            
        except ImportError:
            # 使用FFmpeg回退
            return self._detect_beats_ffmpeg(audio_path)
            
    def _detect_beats_ffmpeg(self, audio_path: str) -> List[float]:
        """使用FFmpeg检测节拍（简化版）"""
        # 提取音频能量
        cmd = [
            self.ffmpeg_path,
            "-i", audio_path,
            "-af", "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level",
            "-f", "null",
            "-"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 解析能量峰值作为节拍点
        beats = []
        current_time = 0
        
        for line in result.stderr.split('\n'):
            if 'RMS_level' in line:
                try:
                    level = float(line.split('=')[1])
                    if level > -20:  # 能量阈值
                        beats.append(current_time)
                    current_time += 0.1
                except:
                    pass
                    
        return beats
        
    def normalize_audio(
        self,
        audio_path: str,
        output_path: str,
        target_level: float = -14.0
    ) -> str:
        """音频标准化 (LUFS)"""
        # 使用loudnorm滤镜
        cmd = [
            self.ffmpeg_path,
            "-i", audio_path,
            "-af", f"loudnorm=I={target_level}:TP=-1.5:LRA=11",
            "-y",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if not os.path.exists(output_path):
            raise RuntimeError(f"标准化失败: {result.stderr}")
            
        return output_path
