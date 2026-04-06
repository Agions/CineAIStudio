"""
剪辑预览生成器 (Cut Preview Generator)

根据剪辑建议生成预览视频，支持多种输出格式。
"""

import os
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PreviewConfig:
    """预览配置"""
    output_width: int = 1280
    output_height: int = 720
    fps: int = 30
    codec: str = "libx264"
    crf: int = 23  # 质量，0-51，越低质量越好
    preset: str = "fast"  # 编码速度
    format: str = "mp4"  # 输出格式


class CutPreviewGenerator:
    """剪辑预览生成器"""

    def __init__(self, config: Optional[PreviewConfig] = None):
        """
        初始化预览生成器

        Args:
            config: 预览配置
        """
        self.config = config or PreviewConfig()
        logger.info("CutPreviewGenerator initialized")

    def generate_preview(
        self,
        video_path: str,
        cuts: List[Dict[str, Any]],
        output_path: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> str:
        """
        生成预览视频

        Args:
            video_path: 源视频路径
            cuts: 剪辑点列表
            output_path: 输出路径（可选，自动生成）
            progress_callback: 进度回调

        Returns:
            生成的预览视频路径
        """
        if not cuts:
            raise ValueError("No cuts provided")

        # 生成输出路径
        if not output_path:
            output_dir = Path.home() / ".narrafiilm" / "previews"
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(output_dir / f"preview_{timestamp}.{self.config.format}")

        logger.info(f"Generating preview: {output_path}")

        # 构建 FFmpeg filter complex
        filter_complex, input_count = self._build_filter_complex(video_path, cuts)

        # 构建 FFmpeg 命令
        cmd = self._build_ffmpeg_cmd(
            video_path, output_path, filter_complex, input_count
        )

        try:
            # 执行 FFmpeg
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # 监控进度
            total_duration = sum(c.get("duration", 0) for c in cuts)
            _processed = 0

            while True:
                line = process.stderr.readline()
                if not line and process.poll() is not None:
                    break

                # 解析进度
                if "time=" in line:
                    time_str = line.split("time=")[1].split()[0]
                    current_time = self._parse_time(time_str)
                    if total_duration > 0:
                        progress = min(int(current_time / total_duration * 100), 100)
                        if progress_callback:
                            progress_callback(progress)

            if process.returncode != 0:
                stderr = process.stderr.read()
                raise RuntimeError(f"FFmpeg failed: {stderr}")

            logger.info(f"Preview generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate preview: {e}")
            raise

    def generate_concat_list(
        self,
        video_path: str,
        cuts: List[Dict[str, Any]],
        output_path: Optional[str] = None
    ) -> str:
        """
        生成 FFmpeg concat 列表文件

        Args:
            video_path: 源视频路径
            cuts: 剪辑点列表
            output_path: 输出文件路径

        Returns:
            concat 文件路径
        """
        if not output_path:
            output_dir = Path.home() / ".narrafiilm" / "temp"
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(output_dir / f"concat_list_{timestamp}.txt")

        with open(output_path, 'w', encoding='utf-8') as f:
            for cut in cuts:
                if cut.get("type") == "keep":
                    start = cut.get("start", 0)
                    end = cut.get("end", 0)
                    f.write(f"file '{video_path}'\n")
                    f.write(f"inpoint={start}\n")
                    f.write(f"outpoint={end}\n")

        logger.info(f"Concat list generated: {output_path}")
        return output_path

    def generate_preview_with_concat(
        self,
        video_path: str,
        cuts: List[Dict[str, Any]],
        output_path: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> str:
        """
        使用 concat 协议生成预览（更快）

        Args:
            video_path: 源视频路径
            cuts: 剪辑点列表
            output_path: 输出路径
            progress_callback: 进度回调

        Returns:
            生成的预览视频路径
        """
        if not cuts:
            raise ValueError("No cuts provided")

        if not output_path:
            output_dir = Path.home() / ".narrafiilm" / "previews"
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(output_dir / f"preview_{timestamp}.{self.config.format}")

        # 首先生成 concat 列表
        concat_file = self.generate_concat_list(video_path, cuts)

        # 构建 FFmpeg 命令
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c:v', self.config.codec,
            '-crf', str(self.config.crf),
            '-preset', self.config.preset,
            '-r', str(self.config.fps),
            '-s', f"{self.config.output_width}x{self.config.output_height}",
            '-c:a', 'aac',
            '-b:a', '128k',
            output_path
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            while True:
                line = process.stderr.readline()
                if not line and process.poll() is not None:
                    break

                if progress_callback and "time=" in line:
                    progress_callback(50)  # 简化进度报告

            if process.returncode != 0:
                stderr = process.stderr.read()
                raise RuntimeError(f"FFmpeg failed: {stderr}")

            # 清理临时文件
            try:
                os.remove(concat_file)
            except OSError:
                pass

            logger.info(f"Preview generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate preview: {e}")
            raise

    def _build_filter_complex(
        self,
        video_path: str,
        cuts: List[Dict[str, Any]]
    ) -> tuple:
        """构建 FFmpeg filter complex"""
        _filters = []  # _
        select_parts = []
        count = 0

        for cut in cuts:
            if cut.get("type") == "keep":
                start = cut.get("start", 0)
                end = cut.get("end", 0)
                duration = end - start

                if duration > 0:
                    select_parts.append(
                        f"between(t,{start},{end})"
                    )
                    count += 1

        if not select_parts:
            raise ValueError("No valid cuts to process")

        # 使用 select 滤镜
        _filter_str = ";".join(select_parts)  # _
        filter_complex = f"[0:v]select='{'+'.join(select_parts)}',setpts=PTS-STARTPTS[v]"

        # 如果有音频
        filter_complex += f";[0:a]aselect='{'+'.join(select_parts)}',asetpts=PTS-STARTPTS[a]"

        return filter_complex, 1

    def _build_ffmpeg_cmd(
        self,
        video_path: str,
        output_path: str,
        filter_complex: str,
        input_count: int
    ) -> List[str]:
        """构建 FFmpeg 命令"""
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-filter_complex', filter_complex,
            '-map', '[v]',
            '-map', '[a]',
            '-c:v', self.config.codec,
            '-crf', str(self.config.crf),
            '-preset', self.config.preset,
            '-r', str(self.config.fps),
            '-s', f"{self.config.output_width}x{self.config.output_height}",
            '-c:a', 'aac',
            '-b:a', '128k',
            output_path
        ]
        return cmd

    def _parse_time(self, time_str: str) -> float:
        """解析 FFmpeg 时间字符串"""
        try:
            parts = time_str.split(':')
            if len(parts) == 3:
                hours = float(parts[0])
                minutes = float(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                minutes = float(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(parts[0])
        except (ValueError, IndexError):
            return 0.0

    def get_preview_info(self, preview_path: str) -> Dict[str, Any]:
        """获取预览视频信息"""
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-show_entries', 'format=duration,size:stream=codec_name,width,height',
            '-of', 'json',
            preview_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            data = json.loads(result.stdout)

            duration = 0.0
            if 'format' in data:
                duration = float(data['format'].get('duration', 0))

            video_info = {}
            if 'streams' in data:
                for stream in data['streams']:
                    if stream.get('codec_type') == 'video':
                        video_info = {
                            'width': stream.get('width', 0),
                            'height': stream.get('height', 0),
                            'codec': stream.get('codec_name', '')
                        }

            return {
                'duration': duration,
                'size': os.path.getsize(preview_path),
                'video': video_info
            }
        except Exception as e:
            logger.error(f"Failed to get preview info: {e}")
            return {}
