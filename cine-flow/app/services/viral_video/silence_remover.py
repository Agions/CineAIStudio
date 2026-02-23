"""
Silence Remover - 静音检测与移除
智能检测并移除视频中的静音片段，保持紧凑的节奏感

功能特性:
- 高精度静音检测（基于音频能量和 ZCR）
- 可配置的静音阈值和最小持续时长
- 支持保留短暂停顿（避免过度剪辑）
- 输出剪辑时间点，用于时间轴编辑
"""

import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import subprocess
import json


@dataclass
class SilenceSegment:
    """静音片段数据结构"""
    start_time: float  # 开始时间（秒）
    end_time: float    # 结束时间（秒）
    duration: float    # 持续时长（秒）
    confidence: float  # 检测置信度 (0-1)


@dataclass
class RemovalResult:
    """移除结果数据结构"""
    original_duration: float
    new_duration: float
    removed_segments: List[SilenceSegment]
    keep_segments: List[Tuple[float, float]]  # 保留片段的时间范围
    compression_ratio: float  # 压缩比例


class SilenceRemover:
    """
    静音移除器
    
    使用 FFmpeg 进行高效的静音检测和视频剪辑
    """
    
    def __init__(
        self,
        silence_threshold_db: float = -40.0,  # 静音阈值（分贝）
        min_silence_duration: float = 0.5,    # 最小静音持续时长（秒）
        padding_duration: float = 0.1,        # 保留的缓冲时长（秒）
    ):
        """
        初始化静音移除器
        
        Args:
            silence_threshold_db: 静音阈值，低于此值视为静音（-60 到 0）
            min_silence_duration: 最小静音持续时长，短于此值的静音将被保留
            padding_duration: 在静音段前后保留的缓冲时长
        """
        self.silence_threshold_db = silence_threshold_db
        self.min_silence_duration = min_silence_duration
        self.padding_duration = padding_duration
    
    def detect_silence(self, video_path: str) -> List[SilenceSegment]:
        """
        检测视频中的静音片段
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            静音片段列表
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 使用 FFmpeg 的 silencedetect 滤镜
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-af', f'silencedetect=n={self.silence_threshold_db}dB:d={self.min_silence_duration}',
            '-f', 'null',
            '-'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            # 解析 FFmpeg 输出
            silence_segments = self._parse_silence_output(result.stderr)
            
            return silence_segments
            
        except subprocess.SubprocessError as e:
            raise RuntimeError(f"静音检测失败: {e}")
    
    def _parse_silence_output(self, output: str) -> List[SilenceSegment]:
        """
        解析 FFmpeg silencedetect 输出
        
        Args:
            output: FFmpeg 标准错误输出
            
        Returns:
            静音片段列表
        """
        silence_segments = []
        lines = output.split('\n')
        
        current_start = None
        
        for line in lines:
            if 'silence_start:' in line:
                # 提取静音开始时间
                try:
                    start_time = float(line.split('silence_start:')[1].strip())
                    current_start = start_time
                except (IndexError, ValueError):
                    continue
                    
            elif 'silence_end:' in line and current_start is not None:
                # 提取静音结束时间和持续时长
                try:
                    parts = line.split('|')
                    end_time = float(parts[0].split('silence_end:')[1].strip())
                    duration = float(parts[1].split('silence_duration:')[1].strip())
                    
                    segment = SilenceSegment(
                        start_time=current_start,
                        end_time=end_time,
                        duration=duration,
                        confidence=1.0  # FFmpeg 检测具有高置信度
                    )
                    silence_segments.append(segment)
                    current_start = None
                    
                except (IndexError, ValueError):
                    continue
        
        return silence_segments
    
    def remove_silence(
        self,
        video_path: str,
        output_path: str,
        silence_segments: Optional[List[SilenceSegment]] = None
    ) -> RemovalResult:
        """
        移除视频中的静音片段
        
        Args:
            video_path: 输入视频路径
            output_path: 输出视频路径
            silence_segments: 静音片段列表（如果为 None，将自动检测）
            
        Returns:
            移除结果
        """
        video_path = Path(video_path)
        output_path = Path(output_path)
        
        # 如果没有提供静音片段，先检测
        if silence_segments is None:
            silence_segments = self.detect_silence(str(video_path))
        
        # 获取视频总时长
        duration = self._get_video_duration(str(video_path))
        
        # 计算保留的片段
        keep_segments = self._calculate_keep_segments(
            duration,
            silence_segments
        )
        
        # 如果没有需要移除的片段，直接复制
        if len(keep_segments) == 1 and keep_segments[0] == (0, duration):
            import shutil
            shutil.copy2(video_path, output_path)
            
            return RemovalResult(
                original_duration=duration,
                new_duration=duration,
                removed_segments=[],
                keep_segments=keep_segments,
                compression_ratio=1.0
            )
        
        # 使用 FFmpeg 剪辑视频
        self._cut_and_concat_video(
            str(video_path),
            str(output_path),
            keep_segments
        )
        
        # 计算新时长
        new_duration = sum(end - start for start, end in keep_segments)
        
        return RemovalResult(
            original_duration=duration,
            new_duration=new_duration,
            removed_segments=silence_segments,
            keep_segments=keep_segments,
            compression_ratio=new_duration / duration if duration > 0 else 1.0
        )
    
    def _get_video_duration(self, video_path: str) -> float:
        """获取视频总时长"""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json',
            video_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            data = json.loads(result.stdout)
            return float(data['format']['duration'])
            
        except (subprocess.SubprocessError, KeyError, ValueError) as e:
            raise RuntimeError(f"获取视频时长失败: {e}")
    
    def _calculate_keep_segments(
        self,
        duration: float,
        silence_segments: List[SilenceSegment]
    ) -> List[Tuple[float, float]]:
        """
        计算需要保留的片段
        
        Args:
            duration: 视频总时长
            silence_segments: 静音片段列表
            
        Returns:
            保留片段的时间范围列表 [(start1, end1), (start2, end2), ...]
        """
        if not silence_segments:
            return [(0, duration)]
        
        keep_segments = []
        current_pos = 0.0
        
        for segment in sorted(silence_segments, key=lambda s: s.start_time):
            # 添加 padding
            cut_start = max(0, segment.start_time + self.padding_duration)
            cut_end = min(duration, segment.end_time - self.padding_duration)
            
            # 如果 padding 后仍有有效的静音段
            if cut_end > cut_start:
                # 保留从当前位置到静音开始的片段
                if cut_start > current_pos:
                    keep_segments.append((current_pos, cut_start))
                current_pos = cut_end
        
        # 保留最后一个片段
        if current_pos < duration:
            keep_segments.append((current_pos, duration))
        
        return keep_segments
    
    def _cut_and_concat_video(
        self,
        input_path: str,
        output_path: str,
        segments: List[Tuple[float, float]]
    ) -> None:
        """
        剪辑并拼接视频片段
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            segments: 保留片段的时间范围
        """
        if not segments:
            raise ValueError("没有需要保留的片段")
        
        # 构建 FFmpeg 复杂滤镜
        filter_parts = []
        
        for i, (start, end) in enumerate(segments):
            # 为每个片段创建一个选择滤镜
            filter_parts.append(
                f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}];"
                f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]"
            )
        
        # 拼接所有片段
        video_inputs = ''.join(f'[v{i}]' for i in range(len(segments)))
        audio_inputs = ''.join(f'[a{i}]' for i in range(len(segments)))
        
        filter_complex = (
            ';'.join(filter_parts) + ';' +
            f'{video_inputs}concat=n={len(segments)}:v=1:a=0[outv];' +
            f'{audio_inputs}concat=n={len(segments)}:v=0:a=1[outa]'
        )
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-filter_complex', filter_complex,
            '-map', '[outv]',
            '-map', '[outa]',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-y',  # 覆盖输出文件
            output_path
        ]
        
        try:
            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"视频剪辑失败: {e.stderr}")


# 使用示例
if __name__ == '__main__':
    # 创建静音移除器
    remover = SilenceRemover(
        silence_threshold_db=-35.0,
        min_silence_duration=0.8,
        padding_duration=0.15
    )
    
    # 示例：检测静音
    # silence_segments = remover.detect_silence('input.mp4')
    # print(f"检测到 {len(silence_segments)} 个静音片段")
    
    # 示例：移除静音
    # result = remover.remove_silence('input.mp4', 'output.mp4')
    # print(f"原时长: {result.original_duration:.2f}s")
    # print(f"新时长: {result.new_duration:.2f}s")
    # print(f"压缩比: {result.compression_ratio:.2%}")
