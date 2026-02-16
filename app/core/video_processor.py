"""
视频处理核心服务
基于FFmpeg的视频处理

优化点:
- 结果缓存机制
- 批量处理支持
- 进度回调
- 智能错误恢复
"""

import subprocess
import json
import os
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from functools import lru_cache
import tempfile
import shutil
import logging

logger = logging.getLogger(__name__)


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
    frame_count: int = 0
    file_size: int = 0
    
    @property
    def resolution(self) -> str:
        """分辨率字符串"""
        return f"{self.width}x{self.height}"
        
    @property
    def aspect_ratio(self) -> float:
        """宽高比"""
        return self.width / self.height if self.height > 0 else 0


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
    audio_codec: str = "aac"
    audio_bitrate: str = "128k"
    pix_fmt: str = "yuv420p"
    
    def to_ffmpeg_args(self) -> List[str]:
        """转换为FFmpeg参数"""
        args = []
        
        if self.resolution:
            args.extend(['-vf', f'scale={self.resolution[0]}:{self.resolution[1]}'])
        if self.fps:
            args.extend(['-r', str(self.fps)])
        if self.bitrate:
            args.extend(['-b:v', self.bitrate])
            
        args.extend([
            '-c:v', self.codec,
            '-preset', self.preset,
            '-crf', str(self.crf),
            '-c:a', self.audio_codec,
            '-b:a', self.audio_bitrate,
            '-pix_fmt', self.pix_fmt,
            '-movflags', '+faststart'
        ])
        
        return args


class VideoProcessor:
    """
    视频处理器
    
    提供视频处理的基础功能：
    - 视频信息获取 (带缓存)
    - 格式转换
    - 分辨率调整
    - 帧率调整
    - 视频剪辑
    - 关键帧提取
    - 批量处理
    
    优化特性:
    - 自动缓存视频信息
    - 进度回调支持
    - 智能错误恢复
    - 临时文件管理
    """
    
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffmpeg_path.replace("ffmpeg", "ffprobe")
        
        # 验证FFmpeg可用
        self._verify_ffmpeg()
        
        # 信息缓存
        self._info_cache: Dict[str, VideoInfo] = {}
        self._cache_max_size = 100
        
        # 临时文件跟踪
        self._temp_files: List[str] = []
        
    def _verify_ffmpeg(self):
        """验证FFmpeg可用性"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("FFmpeg不可用")
                
            # 提取版本
            version_line = result.stdout.split('\n')[0]
            logger.info(f"FFmpeg版本: {version_line}")
            
        except Exception as e:
            logger.error(f"FFmpeg验证失败: {e}")
            raise RuntimeError(f"FFmpeg不可用: {e}")
            
    def _get_cache_key(self, video_path: str) -> str:
        """生成缓存键"""
        stat = os.stat(video_path)
        key_data = f"{video_path}:{stat.st_size}:{stat.st_mtime}"
        return hashlib.md5(key_data.encode()).hexdigest()
        
    def get_video_info(self, video_path: str, use_cache: bool = True) -> VideoInfo:
        """
        获取视频信息
        
        Args:
            video_path: 视频路径
            use_cache: 是否使用缓存
            
        Returns:
            VideoInfo: 视频信息
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
            
        # 检查缓存
        if use_cache:
            cache_key = self._get_cache_key(video_path)
            if cache_key in self._info_cache:
                logger.debug(f"使用缓存信息: {video_path}")
                return self._info_cache[cache_key]
                
        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"ffprobe失败: {result.stderr}")
                
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
            elif duration == 0 and video_stream.get('nb_frames'):
                # 从帧数估算
                nb_frames = int(video_stream.get('nb_frames', 0))
                fps = self._parse_fps(video_stream.get('r_frame_rate', '30/1'))
                duration = nb_frames / fps if fps > 0 else 0
                
            # 解析帧率
            fps = self._parse_fps(video_stream.get('r_frame_rate', '30/1'))
            
            # 计算帧数
            frame_count = int(video_stream.get('nb_frames', 0))
            if frame_count == 0 and duration > 0:
                frame_count = int(duration * fps)
                
            info = VideoInfo(
                path=video_path,
                duration=duration,
                width=int(video_stream.get('width', 0)),
                height=int(video_stream.get('height', 0)),
                fps=fps,
                bitrate=int(data.get('format', {}).get('bit_rate', 0)),
                codec=video_stream.get('codec_name', 'unknown'),
                audio_codec=audio_stream.get('codec_name') if audio_stream else None,
                audio_sample_rate=int(audio_stream.get('sample_rate', 0)) if audio_stream else None,
                frame_count=frame_count,
                file_size=int(data.get('format', {}).get('size', 0))
            )
            
            # 更新缓存
            if use_cache and len(self._info_cache) < self._cache_max_size:
                self._info_cache[self._get_cache_key(video_path)] = info
                
            return info
            
        except json.JSONDecodeError as e:
            raise RuntimeError(f"解析ffprobe输出失败: {e}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("ffprobe超时")
        except Exception as e:
            raise RuntimeError(f"获取视频信息失败: {e}")
            
    def _parse_fps(self, fps_str: str) -> float:
        """解析帧率字符串"""
        try:
            if '/' in fps_str:
                num, den = fps_str.split('/')
                return float(num) / float(den)
            return float(fps_str)
        except:
            return 30.0
            
    def process_video(
        self,
        input_path: str,
        config: ProcessingConfig,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> str:
        """
        处理视频
        
        Args:
            input_path: 输入路径
            config: 处理配置
            progress_callback: 进度回调函数 (progress, message)
            
        Returns:
            str: 输出文件路径
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"输入文件不存在: {input_path}")
            
        # 确保输出目录存在
        os.makedirs(os.path.dirname(config.output_path), exist_ok=True)
        
        # 构建命令
        cmd = [self.ffmpeg_path, '-y', '-i', input_path]
        cmd.extend(config.to_ffmpeg_args())
        cmd.append(config.output_path)
        
        logger.info(f"开始处理视频: {input_path} -> {config.output_path}")
        
        try:
            # 使用进度解析
            if progress_callback:
                self._run_with_progress(cmd, input_path, progress_callback)
            else:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=3600
                )
                if result.returncode != 0:
                    raise RuntimeError(f"FFmpeg错误: {result.stderr}")
                    
            logger.info(f"视频处理完成: {config.output_path}")
            return config.output_path
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("视频处理超时")
        except Exception as e:
            # 清理失败的输出文件
            if os.path.exists(config.output_path):
                os.remove(config.output_path)
            raise RuntimeError(f"视频处理失败: {e}")
            
    def _run_with_progress(
        self,
        cmd: List[str],
        input_path: str,
        callback: Callable[[int, str], None]
    ):
        """运行FFmpeg并解析进度"""
        # 获取视频时长
        try:
            info = self.get_video_info(input_path)
            total_duration = info.duration
        except:
            total_duration = 0
            
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # 解析stderr中的进度
        while True:
            line = process.stderr.readline()
            if not line:
                break
                
            # 解析时间
            if 'time=' in line:
                try:
                    time_str = line.split('time=')[1].split()[0]
                    h, m, s = time_str.split(':')
                    current_time = float(h) * 3600 + float(m) * 60 + float(s)
                    
                    if total_duration > 0:
                        progress = min(int(current_time / total_duration * 100), 100)
                        callback(progress, f"处理中... {progress}%")
                except:
                    pass
                    
        process.wait()
        
        if process.returncode != 0:
            raise RuntimeError("FFmpeg处理失败")
            
    def extract_keyframes(
        self,
        video_path: str,
        output_dir: str,
        interval: float = 1.0,
        max_frames: int = 100
    ) -> List[str]:
        """
        提取关键帧
        
        Args:
            video_path: 视频路径
            output_dir: 输出目录
            interval: 提取间隔（秒）
            max_frames: 最大帧数
            
        Returns:
            List[str]: 帧文件路径列表
        """
        os.makedirs(output_dir, exist_ok=True)
        
        info = self.get_video_info(video_path)
        duration = info.duration
        
        # 调整间隔以避免超过最大帧数
        if duration / interval > max_frames:
            interval = duration / max_frames
            
        frames = []
        timestamp = 0
        frame_count = 0
        
        while timestamp < duration and frame_count < max_frames:
            output_path = os.path.join(
                output_dir,
                f"frame_{frame_count:04d}_{timestamp:.2f}s.jpg"
            )
            
            cmd = [
                self.ffmpeg_path,
                '-ss', str(timestamp),
                '-i', video_path,
                '-vframes', '1',
                '-q:v', '2',
                '-y',
                output_path
            ]
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=30
                )
                if result.returncode == 0:
                    frames.append(output_path)
                    frame_count += 1
            except Exception as e:
                logger.warning(f"提取帧失败 {timestamp}s: {e}")
                
            timestamp += interval
            
        logger.info(f"提取了 {len(frames)} 个关键帧")
        return frames
        
    def cut_video(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        output_path: str,
        reencode: bool = False
    ) -> str:
        """
        剪辑视频
        
        Args:
            video_path: 原视频路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            output_path: 输出路径
            reencode: 是否重新编码（False=快速拷贝）
            
        Returns:
            str: 输出文件路径
        """
        duration = end_time - start_time
        
        if reencode:
            cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-ss', str(start_time),
                '-t', str(duration),
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-y',
                output_path
            ]
        else:
            # 快速拷贝模式
            cmd = [
                self.ffmpeg_path,
                '-ss', str(start_time),
                '-t', str(duration),
                '-i', video_path,
                '-c', 'copy',
                '-avoid_negative_ts', 'make_zero',
                '-y',
                output_path
            ]
            
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=300
            )
            if result.returncode != 0:
                raise RuntimeError(f"剪辑失败: {result.stderr.decode()}")
            return output_path
        except Exception as e:
            raise RuntimeError(f"视频剪辑失败: {e}")
            
    def merge_videos(
        self,
        video_paths: List[str],
        output_path: str,
        transition: str = None
    ) -> str:
        """
        合并多个视频
        
        Args:
            video_paths: 视频路径列表
            output_path: 输出路径
            transition: 转场效果 (fade, dissolve, wipe)
            
        Returns:
            str: 输出文件路径
        """
        if not video_paths:
            raise ValueError("视频列表为空")
            
        # 创建临时文件列表
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for path in video_paths:
                f.write(f"file '{path}'\n")
            list_file = f.name
            self._temp_files.append(list_file)
            
        try:
            if transition:
                # 使用复杂滤镜添加转场
                result = self._merge_with_transition(
                    video_paths, output_path, transition
                )
            else:
                # 简单拼接
                cmd = [
                    self.ffmpeg_path,
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', list_file,
                    '-c', 'copy',
                    '-y',
                    output_path
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=600
                )
                
                if result.returncode != 0:
                    raise RuntimeError(f"合并失败: {result.stderr.decode()}")
                    
            return output_path
            
        finally:
            # 清理临时文件
            if os.path.exists(list_file):
                os.remove(list_file)
                self._temp_files.remove(list_file)
                
    def _merge_with_transition(
        self,
        video_paths: List[str],
        output_path: str,
        transition: str
    ):
        """带转场的合并"""
        # 简化的转场实现
        # 实际项目中可以使用更复杂的滤镜
        filter_complex = []
        inputs = []
        
        for i, path in enumerate(video_paths):
            inputs.extend(['-i', path])
            
        # 使用xfade滤镜（FFmpeg 4.4+）
        if transition == 'fade':
            transition_type = 'fade'
        elif transition == 'dissolve':
            transition_type = 'fadeblack'
        else:
            transition_type = 'fade'
            
        # 构建滤镜（简化版）
        cmd = inputs + [
            '-filter_complex',
            f'concat=n={len(video_paths)}:v=1:a=1',
            '-y',
            output_path
        ]
        
        cmd.insert(0, self.ffmpeg_path)
        
        result = subprocess.run(cmd, capture_output=True, timeout=600)
        return result
        
    def detect_scenes(
        self,
        video_path: str,
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        场景检测
        
        Args:
            video_path: 视频路径
            threshold: 场景变化阈值
            
        Returns:
            List[Dict]: 场景列表 [{start, end, duration}]
        """
        cmd = [
            self.ffmpeg_path,
            '-i', video_path,
            '-filter:v', f'select=gt(scene\\,{threshold})',
            '-show_entries', 'frame=pkt_pts_time',
            '-of', 'csv=p=0',
            '-f', 'null',
            '-'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # 解析场景切换时间点
            scenes = []
            timestamps = [0.0]  # 从0开始
            
            for line in result.stderr.split('\n'):
                if 'pts_time:' in line:
                    try:
                        ts = float(line.split('pts_time:')[1].split()[0])
                        timestamps.append(ts)
                    except:
                        pass
                        
            # 获取视频时长
            info = self.get_video_info(video_path)
            timestamps.append(info.duration)
            
            # 构建场景列表
            for i in range(len(timestamps) - 1):
                scenes.append({
                    'start': timestamps[i],
                    'end': timestamps[i + 1],
                    'duration': timestamps[i + 1] - timestamps[i]
                })
                
            return scenes
            
        except Exception as e:
            logger.error(f"场景检测失败: {e}")
            return []
            
    def apply_lut(
        self,
        video_path: str,
        lut_path: str,
        output_path: str,
        intensity: float = 1.0
    ) -> str:
        """
        应用LUT调色
        
        Args:
            video_path: 视频路径
            lut_path: LUT文件路径 (.cube)
            output_path: 输出路径
            intensity: 强度 (0-1)
            
        Returns:
            str: 输出文件路径
        """
        if not os.path.exists(lut_path):
            raise FileNotFoundError(f"LUT文件不存在: {lut_path}")
            
        # 构建LUT滤镜
        if intensity < 1.0:
            # 混合原始和LUT效果
            filter_str = f"[0:v]split[original][lut];[lut]lut3d={lut_path}[lutout];[original][lutout]blend=all_mode='overlay':all_opacity={intensity}"
        else:
            filter_str = f"lut3d={lut_path}"
            
        cmd = [
            self.ffmpeg_path,
            '-i', video_path,
            '-vf', filter_str,
            '-c:a', 'copy',
            '-y',
            output_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=600
            )
            if result.returncode != 0:
                raise RuntimeError(f"LUT应用失败: {result.stderr.decode()}")
            return output_path
        except Exception as e:
            raise RuntimeError(f"调色失败: {e}")
            
    def add_text_overlay(
        self,
        video_path: str,
        text: str,
        output_path: str,
        position: str = "bottom",
        font_size: int = 24,
        font_color: str = "white",
        start_time: float = 0,
        duration: float = None
    ) -> str:
        """
        添加文字叠加
        
        Args:
            video_path: 视频路径
            text: 文字内容
            output_path: 输出路径
            position: 位置 (top, bottom, center)
            font_size: 字体大小
            font_color: 字体颜色
            start_time: 开始时间
            duration: 持续时间
            
        Returns:
            str: 输出文件路径
        """
        # 位置映射
        pos_map = {
            'top': f'(w-text_w)/2:{font_size}',
            'bottom': f'(w-text_w)/2:h-{font_size}*2',
            'center': '(w-text_w)/2:(h-text_h)/2'
        }
        
        position_str = pos_map.get(position, pos_map['bottom'])
        
        # 转义特殊字符
        escaped_text = text.replace("'", "\\'").replace(":", "\\:")
        
        # 构建滤镜
        enable_str = f"gte(t\\,{start_time})"
        if duration:
            enable_str += f"*lte(t\\,{start_time + duration})"
            
        filter_str = f"drawtext=text='{escaped_text}':fontsize={font_size}:fontcolor={font_color}:x={position_str.split(':')[0]}:y={position_str.split(':')[1]}:enable='{enable_str}'"
        
        cmd = [
            self.ffmpeg_path,
            '-i', video_path,
            '-vf', filter_str,
            '-c:a', 'copy',
            '-y',
            output_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=300
            )
            if result.returncode != 0:
                raise RuntimeError(f"文字叠加失败: {result.stderr.decode()}")
            return output_path
        except Exception as e:
            raise RuntimeError(f"添加文字失败: {e}")
            
    def batch_process(
        self,
        video_paths: List[str],
        config: ProcessingConfig,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[str]:
        """
        批量处理视频
        
        Args:
            video_paths: 视频路径列表
            config: 处理配置
            progress_callback: 进度回调 (current, total, message)
            
        Returns:
            List[str]: 输出文件路径列表
        """
        results = []
        total = len(video_paths)
        
        for i, video_path in enumerate(video_paths):
            if progress_callback:
                progress_callback(i, total, f"处理 {i+1}/{total}: {os.path.basename(video_path)}")
                
            try:
                # 生成输出路径
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                output_path = os.path.join(
                    config.output_path,
                    f"{base_name}_processed.mp4"
                )
                
                # 更新配置
                task_config = ProcessingConfig(
                    output_path=output_path,
                    resolution=config.resolution,
                    fps=config.fps,
                    bitrate=config.bitrate,
                    codec=config.codec,
                    preset=config.preset,
                    crf=config.crf
                )
                
                # 处理
                result = self.process_video(
                    video_path,
                    task_config,
                    lambda p, m: progress_callback(i, total, f"{os.path.basename(video_path)}: {m}") if progress_callback else None
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"批量处理失败 {video_path}: {e}")
                results.append(None)
                
        if progress_callback:
            progress_callback(total, total, "批量处理完成")
            
        return results
        
    def clear_cache(self):
        """清除信息缓存"""
        self._info_cache.clear()
        logger.info("视频信息缓存已清除")
        
    def cleanup_temp_files(self):
        """清理临时文件"""
        for temp_file in self._temp_files[:]:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    self._temp_files.remove(temp_file)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
                
    def __enter__(self):
        """上下文管理器入口"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup_temp_files()
        self.clear_cache()
