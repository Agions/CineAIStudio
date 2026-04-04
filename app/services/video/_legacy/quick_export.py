#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速导出工具
一键导出视频到各平台
"""

import os
import subprocess
from typing import List
from dataclasses import dataclass

from .presets import PlatformPreset
from .effects_presets import FilterPreset


@dataclass
class ExportResult:
    """导出结果"""
    success: bool
    output_path: str = ""
    error: str = ""
    duration: float = 0.0


class QuickExporter:
    """
    快速导出器
    
    一键导出视频到各平台
    """
    
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg = ffmpeg_path
    
    def export(
        self,
        input_path: str,
        output_path: str,
        platform: str = "bilibili",
        quality: str = "standard",
        filter_preset: str = "",
    ) -> ExportResult:
        """
        快速导出
        
        Args:
            input_path: 输入路径
            output_path: 输出路径
            platform: 平台 (bilibili/youtube/tiktok/wechat)
            quality: 质量 (low/standard/high/ultra)
            filter_preset: 滤镜预设
        """
        # 获取预设
        platform_preset = PlatformPreset.get_defaults().get(platform)
        if not platform_preset:
            return ExportResult(False, error=f"Unknown platform: {platform}")
        
        # 构建 FFmpeg 命令
        cmd = [self.ffmpeg, "-y", "-i", input_path]
        
        # 视频滤镜
        _filters = []
        
        # 分辨率
        if platform_preset.vertical:
            # 竖屏
            cmd.extend(["-vf", f"scale=-2:{platform_preset.resolution.height}"])
        else:
            cmd.extend(["-vf", f"scale={platform_preset.resolution.width}:-2"])
        
        # 帧率
        cmd.extend(["-r", str(platform_preset.fps)])
        
        # 视频编码
        cmd.extend(["-c:v", "libx264", "-preset", "medium"])
        
        # 码率
        bitrate = platform_preset.bitrate.replace("M", "M")
        cmd.extend(["-b:v", bitrate])
        
        # 音频
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        
        # 输出
        cmd.append(output_path)
        
        try:
            # 执行
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,  # 1小时超时
            )
            
            if result.returncode == 0:
                duration = self._get_duration(output_path)
                return ExportResult(
                    success=True,
                    output_path=output_path,
                    duration=duration,
                )
            else:
                return ExportResult(
                    success=False,
                    error=result.stderr or "Unknown error",
                )
                
        except subprocess.TimeoutExpired:
            return ExportResult(False, error="Export timeout")
        except Exception as e:
            return ExportResult(False, error=str(e))
    
    def export_with_filter(
        self,
        input_path: str,
        output_path: str,
        filter_preset: FilterPreset,
    ) -> ExportResult:
        """使用滤镜导出"""
        cmd = [self.ffmpeg, "-y", "-i", input_path]
        
        # 构建滤镜
        filter_parts = []
        
        if filter_preset.brightness != 0:
            brightness = filter_preset.brightness * 100
            filter_parts.append(f"eq=brightness={brightness}:1")
        
        if filter_preset.contrast != 0:
            contrast = 1 + filter_preset.contrast
            filter_parts.append(f"eq=contrast={contrast}")
        
        if filter_preset.saturation != 0:
            saturation = 1 + filter_preset.saturation
            filter_parts.append(f"eq=saturation={saturation}")
        
        if filter_parts:
            cmd.extend(["-vf", ",".join(filter_parts)])
        
        cmd.extend(["-c:v", "libx264", "-preset", "fast", "-crf", "23"])
        cmd.extend(["-c:a", "aac"])
        cmd.append(output_path)
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=3600)
            return ExportResult(
                success=result.returncode == 0,
                output_path=output_path if result.returncode == 0 else "",
                error=result.stderr if result.returncode != 0 else "",
            )
        except Exception as e:
            return ExportResult(False, error=str(e))
    
    def export_batch(
        self,
        inputs: List[str],
        output_dir: str,
        platform: str = "bilibili",
    ) -> List[ExportResult]:
        """批量导出"""
        results = []
        
        for i, input_path in enumerate(inputs):
            output_path = os.path.join(
                output_dir,
                f"output_{i+1}.mp4"
            )
            
            result = self.export(input_path, output_path, platform)
            results.append(result)
        
        return results
    
    def _get_duration(self, path: str) -> float:
        """获取视频时长"""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return float(result.stdout.strip() or 0)
        except Exception:
            return 0.0


# 便捷函数
def quick_export(
    input_path: str,
    output_path: str,
    platform: str = "bilibili",
) -> ExportResult:
    """快速导出"""
    exporter = QuickExporter()
    return exporter.export(input_path, output_path, platform)


def quick_export_with_filter(
    input_path: str,
    output_path: str,
    filter_name: str = "vivid",
) -> ExportResult:
    """带滤镜导出"""
    filters = FilterPreset.get_defaults()
    preset = filters.get(filter_name)
    
    if not preset:
        return ExportResult(False, error=f"Unknown filter: {filter_name}")
    
    exporter = QuickExporter()
    return exporter.export_with_filter(input_path, output_path, preset)


__all__ = [
    "ExportResult",
    "QuickExporter",
    "quick_export",
    "quick_export_with_filter",
]
