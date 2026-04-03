#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频处理工具函数
"""

import os
import subprocess
import json
from typing import Optional, Tuple, List
import logging
import tempfile




class VideoInfo:
    """视频信息"""
    
    def __init__(self, path: str):
        self.path = path
        self.duration: float = 0
        self.width: int = 0
        self.height: int = 0
        self.fps: float = 0
        self.codec: str = ""
        self.bitrate: int = 0
        self.size: int = 0
        
    def __repr__(self):
        return (
            f"VideoInfo({self.width}x{self.height}@{self.fps}fps, "
            f"{self.duration:.1f}s, {self.size//1024//1024}MB)"
        )


def get_video_info(path: str) -> Optional[VideoInfo]:
    """
    获取视频信息
    
    Args:
        path: 视频路径
        
    Returns:
        VideoInfo 或 None
    """
    if not os.path.exists(path):
        return None
    
    try:
        # 使用 ffprobe
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            path,
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode != 0:
            return None
            
        data = json.loads(result.stdout)
        
        info = VideoInfo(path)
        
        # 查找视频流
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                info.width = stream.get("width", 0)
                info.height = stream.get("height", 0)
                fps_str = stream.get("r_frame_rate", "0/1")
                if "/" in fps_str:
                    num, den = fps_str.split("/")
                    info.fps = float(num) / float(den) if den != "0" else 0
                info.codec = stream.get("codec_name", "")
                break
        
        # 格式信息
        format_data = data.get("format", {})
        info.duration = float(format_data.get("duration", 0))
        info.bitrate = int(format_data.get("bit_rate", 0))
        info.size = int(format_data.get("size", 0))
        
        return info
        
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
        return None


def extract_thumbnail(
    video_path: str,
    output_path: str,
    timestamp: float = 1.0,
) -> bool:
    """
    提取缩略图
    
    Args:
        video_path: 视频路径
        output_path: 输出路径
        timestamp: 时间戳 (秒)
        
    Returns:
        是否成功
    """
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(timestamp),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            output_path,
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        return result.returncode == 0
        
    except Exception as e:
        logger.error(f"Failed to extract thumbnail: {e}")
        return False


def get_video_duration(path: str) -> float:
    """获取视频时长 (秒)"""
    info = get_video_info(path)
    return info.duration if info else 0


def get_video_resolution(path: str) -> Tuple[int, int]:
    """获取视频分辨率 (宽, 高)"""
    info = get_video_info(path)
    return (info.width, info.height) if info else (0, 0)


def get_video_fps(path: str) -> float:
    """获取视频帧率"""
    info = get_video_info(path)
    return info.fps if info else 0


def concat_videos(
    input_paths: List[str],
    output_path: str,
    method: str = "concat",
) -> bool:
    """
    合并视频
    
    Args:
        input_paths: 输入路径列表
        output_path: 输出路径
        method: concat/demuxer
        
    Returns:
        是否成功
    """
    if method == "concat":
        # 使用 concat 协议
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for p in input_paths:
                f.write(f"file '{p}'\n")
            list_path = f.name
        
        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", list_path,
                "-c", "copy",
                output_path,
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=300)
            return result.returncode == 0
        finally:
            os.unlink(list_path)
            
    else:
        # 使用 concat demuxer
        filter_str = "".join([f"[{i}:v][{i}:a]" for i in range(len(input_paths))])
        
        cmd = [
            "ffmpeg",
            "-y",
        ]
        
        for p in input_paths:
            cmd.extend(["-i", p])
        
        cmd.extend([
            "-filter_complex", f"{filter_str}concat=n={len(input_paths)}:v=1:a=1[v][a]",
            "-map", "[v]",
            "-map", "[a]",
            output_path,
        ])
        
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        return result.returncode == 0


def trim_video(
    input_path: str,
    output_path: str,
    start: float,
    end: float,
) -> bool:
    """
    裁剪视频
    
    Args:
        input_path: 输入路径
        output_path: 输出路径
        start: 开始时间 (秒)
        end: 结束时间 (秒)
        
    Returns:
        是否成功
    """
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(start),
            "-to", str(end),
            "-i", input_path,
            "-c", "copy",
            output_path,
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        return result.returncode == 0
        
    except Exception as e:
        logger.error(f"Failed to trim video: {e}")
        return False


def add_subtitle(
    video_path: str,
    subtitle_path: str,
    output_path: str,
    language: str = "zh",
) -> bool:
    """
    添加字幕
    
    Args:
        video_path: 视频路径
        subtitle_path: 字幕路径
        output_path: 输出路径
        language: 字幕语言
        
    Returns:
        是否成功
    """
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vf", f"subtitles='{subtitle_path}'",
            "-c:a", "copy",
            output_path,
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        return result.returncode == 0
        
    except Exception as e:
        logger.error(f"Failed to add subtitle: {e}")
        return False


def change_speed(
    input_path: str,
    output_path: str,
    speed: float,
) -> bool:
    """
    改变视频速度
    
    Args:
        input_path: 输入路径
        output_path: 输出路径
        speed: 速度倍数 (0.5=慢放, 2.0=快进)
        
    Returns:
        是否成功
    """
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-i", input_path,
            "-filter:v", f"setpts={1/speed}*PTS",
            "-filter:a", f"atempo={speed}",
            output_path,
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        return result.returncode == 0
        
    except Exception as e:
        logger.error(f"Failed to change speed: {e}")
        return False


def generate_waveform(
    audio_path: str,
    output_path: str,
    width: int = 800,
    height: int = 200,
) -> bool:
    """
    生成音频波形图
    
    Args:
        audio_path: 音频路径
        output_path: 输出路径
        width: 宽度
        height: 高度
        
    Returns:
        是否成功
    """
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-i", audio_path,
            "-filter_complex", 
            f"aformat=channel_layouts=mono,showwavespic=s={width}x{height}",
            "-frames:v", "1",
            "-png", output_path,
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        return result.returncode == 0
        
    except Exception as e:
        logger.error(f"Failed to generate waveform: {e}")
        return False


logger = logging.getLogger(__name__)
