"""
视频处理核心服务
基于FFmpeg的视频处理
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import tempfile


@dataclass
class VideoInfo:
    """视频信息"""
    path: str
    duration: float
    width: int
    height: int
    fps: float
    bitrate: int
    codec: str
    audio_codec: Optional[str] = None
    audio_sample_rate: Optional[int] = None


@dataclass
class ProcessingConfig:
    """处理配置"""
    output_path: str
    resolution: Optional[Tuple[int, int]] = None
    fps: Optional[float] = None
    bitrate: Optional[str] = None
    codec: str = "libx264"
    preset: str = "medium"
    crf: int = 23


class VideoProcessor:
    """
    视频处理器
    
    提供视频处理的基础功能：
    - 视频信息获取
    - 格式转换
    - 分辨率调整
    - 帧率调整
    - 视频剪辑
    - 关键帧提取
    """
    
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffmpeg_path.replace("ffmpeg", "ffprobe")
        
    def get_video_info(self, video_path: str) -> VideoInfo:
        """获取视频信息"""
        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        
        # 查找视频流
        video_stream = None
        audio_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
            elif stream.get('codec_type') == 'audio':
                audio_stream = stream
                
        if not video_stream:
            raise ValueError("未找到视频流")
            
        # 解析时长
        duration = float(data.get('format', {}).get('duration', 0))
        if duration == 0 and video_stream.get('duration'):
            duration = float(video_stream.get('duration'))
            
        # 解析帧率
        fps_str = video_stream.get('r_frame_rate', '30/1')
        if '/' in fps_str:
            num, den = fps_str.split('/')
            fps = float(num) / float(den)
        else:
            fps = float(fps_str)
            
        return VideoInfo(
            path=video_path,
            duration=duration,
            width=int(video_stream.get('width', 0)),
            height=int(video_stream.get('height', 0)),
            fps=fps,
            bitrate=int(data.get('format', {}).get('bit_rate', 0)),
            codec=video_stream.get('codec_name', 'unknown'),
            audio_codec=audio_stream.get('codec_name') if audio_stream else None,
            audio_sample_rate=int(audio_stream.get('sample_rate')) if audio_stream else None
        )
        
    def extract_keyframes(
        self,
        video_path: str,
        output_dir: str,
        num_frames: int = 10
    ) -> List[str]:
        """提取关键帧"""
        info = self.get_video_info(video_path)
        duration = info.duration
        
        # 计算采样时间点
        timestamps = [
            duration * i / (num_frames + 1)
            for i in range(1, num_frames + 1)
        ]
        
        frame_paths = []
        os.makedirs(output_dir, exist_ok=True)
        
        for i, ts in enumerate(timestamps):
            output_path = os.path.join(output_dir, f"frame_{i:03d}.jpg")
            
            cmd = [
                self.ffmpeg_path,
                "-ss", str(ts),
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "2",
                "-y",
                output_path
            ]
            
            subprocess.run(cmd, capture_output=True)
            
            if os.path.exists(output_path):
                frame_paths.append(output_path)
                
        return frame_paths
        
    def cut_video(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_path: str
    ) -> str:
        """剪辑视频片段"""
        duration = end_time - start_time
        
        cmd = [
            self.ffmpeg_path,
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", video_path,
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            "-y",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if not os.path.exists(output_path):
            raise RuntimeError(f"剪辑失败: {result.stderr}")
            
        return output_path
        
    def merge_videos(
        self,
        video_paths: List[str],
        output_path: str,
        transitions: Optional[List[Dict]] = None
    ) -> str:
        """合并多个视频"""
        if len(video_paths) == 1:
            # 单个视频直接复制
            import shutil
            shutil.copy(video_paths[0], output_path)
            return output_path
            
        # 创建临时文件列表
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for path in video_paths:
                f.write(f"file '{os.path.abspath(path)}'\n")
            concat_file = f.name
            
        try:
            if transitions:
                # 使用xfade滤镜添加转场
                filter_complex = self._build_transition_filter(video_paths, transitions)
                
                cmd = [
                    self.ffmpeg_path,
                    "-f", "concat",
                    "-safe", "0",
                    "-i", concat_file,
                    "-filter_complex", filter_complex,
                    "-map", "[out]",
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "23",
                    "-y",
                    output_path
                ]
            else:
                # 简单拼接
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
                raise RuntimeError(f"合并失败: {result.stderr}")
                
        finally:
            os.unlink(concat_file)
            
        return output_path
        
    def _build_transition_filter(
        self,
        video_paths: List[str],
        transitions: List[Dict]
    ) -> str:
        """构建转场滤镜"""
        # 简化的转场实现
        n = len(video_paths)
        filter_parts = []
        
        for i in range(n):
            filter_parts.append(f"[{i}:v][{i}:a]")
            
        filter_parts.append(f"concat=n={n}:v=1:a=1[outv][outa]")
        
        return "".join(filter_parts)
        
    def apply_color_grade(
        self,
        video_path: str,
        output_path: str,
        lut_path: Optional[str] = None,
        brightness: float = 0.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        gamma: float = 1.0
    ) -> str:
        """应用调色"""
        filter_parts = []
        
        # 基础调色
        filters = []
        if brightness != 0 or contrast != 1.0:
            filters.append(f"eq=brightness={brightness}:contrast={contrast}")
        if saturation != 1.0:
            filters.append(f"eq=saturation={saturation}")
        if gamma != 1.0:
            filters.append(f"eq=gamma={gamma}")
            
        # LUT
        if lut_path and os.path.exists(lut_path):
            filters.append(f"lut3d='{lut_path}'")
            
        filter_str = ",".join(filters) if filters else "copy"
        
        cmd = [
            self.ffmpeg_path,
            "-i", video_path,
            "-vf", filter_str,
            "-c:a", "copy",
            "-preset", "medium",
            "-crf", "23",
            "-y",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if not os.path.exists(output_path):
            raise RuntimeError(f"调色失败: {result.stderr}")
            
        return output_path
        
    def add_audio(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        audio_volume: float = 1.0,
        mix_original: bool = False
    ) -> str:
        """添加音频到视频"""
        if mix_original:
            # 混音
            filter_complex = (
                f"[0:a]volume={audio_volume}[a1];"
                f"[1:a]volume=1.0[a2];"
                f"[a1][a2]amix=inputs=2:duration=first[outa]"
            )
            
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-i", audio_path,
                "-filter_complex", filter_complex,
                "-map", "0:v",
                "-map", "[outa]",
                "-c:v", "copy",
                "-y",
                output_path
            ]
        else:
            # 替换音频
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                "-y",
                output_path
            ]
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if not os.path.exists(output_path):
            raise RuntimeError(f"添加音频失败: {result.stderr}")
            
        return output_path
        
    def generate_preview(
        self,
        video_path: str,
        output_path: str,
        width: int = 480,
        duration: Optional[float] = None
    ) -> str:
        """生成预览视频"""
        info = self.get_video_info(video_path)
        
        # 计算高度保持比例
        height = int(width * info.height / info.width)
        height = height - (height % 2)  # 确保偶数
        
        cmd = [
            self.ffmpeg_path,
            "-i", video_path,
            "-vf", f"scale={width}:{height}",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "28",
            "-c:a", "aac",
            "-b:a", "64k",
            "-y"
        ]
        
        if duration:
            cmd.extend(["-t", str(duration)])
            
        cmd.append(output_path)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if not os.path.exists(output_path):
            raise RuntimeError(f"生成预览失败: {result.stderr}")
            
        return output_path
        
    def detect_scenes(
        self,
        video_path: str,
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """检测场景切换点"""
        cmd = [
            self.ffmpeg_path,
            "-i", video_path,
            "-filter:v", f"select='gt(scene,{threshold})',showinfo",
            "-f", "null",
            "-"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        scenes = []
        for line in result.stderr.split('\n'):
            if 'pts_time:' in line:
                try:
                    time_str = line.split('pts_time:')[1].split()[0]
                    time = float(time_str)
                    scenes.append({'time': time, 'type': 'scene_change'})
                except:
                    pass
                    
        return scenes
