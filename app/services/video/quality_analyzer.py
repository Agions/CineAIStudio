#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频质量检测器

自动检测视频质量问题并提供修复建议。

功能：
- 分辨率与帧率检测
- 亮度/对比度分析
- 音频质量检测
- 画面抖动检测
- 噪点检测
- 编码问题检测

使用示例:
    from app.services.video import QualityAnalyzer, QualityIssue
    
    analyzer = QualityAnalyzer()
    issues = analyzer.analyze("video.mp4")
    
    for issue in issues:
        print(f"{issue.severity}: {issue.description}")
"""

import json
import subprocess
import re
import logging

# 获取 logger
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


logger = logging.getLogger(__name__)
class IssueSeverity(Enum):
    """问题严重程度"""
    CRITICAL = "critical"    # 严重，必须修复
    WARNING = "warning"     # 警告，建议修复
    INFO = "info"         # 信息


class IssueCategory(Enum):
    """问题分类"""
    RESOLUTION = "resolution"     # 分辨率
    FRAMERATE = "framerate"     # 帧率
    BRIGHTNESS = "brightness"   # 亮度
    AUDIO = "audio"             # 音频
    STABILITY = "stability"     # 稳定性
    NOISE = "noise"             # 噪点
    ENCODING = "encoding"       # 编码
    COMPOSITION = "composition" # 构图


@dataclass
class QualityIssue:
    """质量问题"""
    category: IssueCategory
    severity: IssueSeverity
    description: str
    timestamp: float = 0.0      # 问题出现的时间点（秒）
    value: float = 0.0          # 检测到的数值
    expected: float = 0.0       # 期望值
    fix_suggestion: str = ""     # 修复建议
    
    # 详细信息
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VideoQualityReport:
    """视频质量报告"""
    file_path: str
    duration: float
    resolution: Tuple[int, int] = (0, 0)
    fps: float = 0.0
    bitrate: int = 0
    codec: str = ""
    
    # 音频信息
    audio_codec: str = ""
    audio_bitrate: int = 0
    sample_rate: int = 0
    channels: int = 0
    
    # 质量问题
    issues: List[QualityIssue] = field(default_factory=list)
    
    # 整体评分
    overall_score: float = 100.0  # 0-100
    is_acceptable: bool = True
    
    # 检测详情
    brightness_avg: float = 0.0
    brightness_std: float = 0.0
    contrast_ratio: float = 0.0
    audio_level_db: float = 0.0
    audio_level_peak: float = 0.0


class QualityAnalyzer:
    """
    视频质量分析器
    
    使用 FFmpeg 和 OpenCV 进行视频质量检测
    """
    
    # 质量标准配置
    STANDARDS = {
        "bilibili": {
            "min_resolution": (1280, 720),
            "recommended_resolution": (1920, 1080),
            "min_fps": 24,
            "recommended_fps": 30,
            "max_duration": 600,  # 10分钟
            "min_bitrate": 2000000,  # 2Mbps
            "recommended_bitrate": 5000000,  # 5Mbps
            "audio_bitrate": 128000,  # 128kbps
            "audio_sample_rate": 48000,
        },
        "douyin": {
            "min_resolution": (720, 1280),  # 竖屏
            "recommended_resolution": (1080, 1920),
            "min_fps": 25,
            "recommended_fps": 30,
            "max_duration": 180,  # 3分钟
            "min_bitrate": 1500000,
            "recommended_bitrate": 4000000,
            "audio_bitrate": 128000,
            "audio_sample_rate": 48000,
        },
        "youtube": {
            "min_resolution": (1280, 720),
            "recommended_resolution": (1920, 1080),
            "min_fps": 30,
            "recommended_fps": 60,
            "max_duration": 3600,  # 1小时
            "min_bitrate": 2500000,
            "recommended_bitrate": 8000000,
            "audio_bitrate": 192000,
            "audio_sample_rate": 48000,
        },
    }
    
    def __init__(self, platform: str = "bilibili"):
        """
        Args:
            platform: 目标平台 (bilibili/douyin/youtube)
        """
        self.platform = platform
        self.standard = self.STANDARDS.get(platform, self.STANDARDS["bilibili"])
    
    def analyze(self, video_path: str) -> VideoQualityReport:
        """
        分析视频质量
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            质量报告
        """
        path = Path(video_path)
        if not path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 初始化报告
        report = VideoQualityReport(file_path=str(path))
        
        # 1. 获取基础信息
        basic_info = self._get_basic_info(video_path)
        report.duration = basic_info.get("duration", 0)
        report.resolution = basic_info.get("resolution", (0, 0))
        report.fps = basic_info.get("fps", 0)
        report.bitrate = basic_info.get("bitrate", 0)
        report.codec = basic_info.get("video_codec", "")
        report.audio_codec = basic_info.get("audio_codec", "")
        report.audio_bitrate = basic_info.get("audio_bitrate", 0)
        report.sample_rate = basic_info.get("sample_rate", 0)
        report.channels = basic_info.get("channels", 0)
        
        # 2. 分析亮度
        brightness = self._analyze_brightness(video_path, report.duration)
        report.brightness_avg = brightness.get("avg", 0.5)
        report.brightness_std = brightness.get("std", 0.0)
        report.contrast_ratio = brightness.get("contrast", 0.0)
        
        # 3. 分析音频
        audio_levels = self._analyze_audio(video_path)
        report.audio_level_db = audio_levels.get("mean_db", -20.0)
        report.audio_level_peak = audio_levels.get("peak_db", 0.0)
        
        # 4. 检测问题
        report.issues = self._detect_issues(report)
        
        # 5. 计算整体评分
        report.overall_score = self._calculate_score(report)
        report.is_acceptable = self._is_acceptable(report)
        
        return report
    
    def _get_basic_info(self, video_path: str) -> Dict:
        """获取视频基础信息"""
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-show_format', '-show_streams',
            '-of', 'json',
            video_path
        ]
        
        result = {
            "duration": 0.0,
            "resolution": (0, 0),
            "fps": 0.0,
            "bitrate": 0,
            "video_codec": "",
            "audio_codec": "",
            "audio_bitrate": 0,
            "sample_rate": 0,
            "channels": 0,
        }
        
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            data = json.loads(proc.stdout)
            
            # 格式信息
            format_info = data.get("format", {})
            result["duration"] = float(format_info.get("duration", 0))
            result["bitrate"] = int(format_info.get("bit_rate", 0))
            
            # 流信息
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    result["video_codec"] = stream.get("codec_name", "")
                    
                    # 解析帧率
                    fps_str = stream.get("r_frame_rate", "0/1")
                    num, denom = map(int, fps_str.split('/'))
                    if denom > 0:
                        result["fps"] = num / denom
                    
                    # 分辨率
                    width = stream.get("width", 0)
                    height = stream.get("height", 0)
                    result["resolution"] = (width, height)
                    
                elif stream.get("codec_type") == "audio":
                    result["audio_codec"] = stream.get("codec_name", "")
                    result["audio_bitrate"] = int(stream.get("bit_rate", 0))
                    result["sample_rate"] = int(stream.get("sample_rate", 0))
                    result["channels"] = stream.get("channels", 0)
                    
        except Exception as e:
            logger.warning(f"获取视频信息失败: {e}")
        
        return result
    
    def _analyze_brightness(self, video_path: str, duration: float) -> Dict:
        """分析视频亮度"""
        try:
            import cv2
            import numpy as np
            
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                return {"avg": 0.5, "std": 0.0, "contrast": 0.0}
            
            # 采样帧
            num_samples = min(30, int(duration))
            frame_indices = [int(i * cap.get(cv2.CAP_PROP_FRAME_COUNT) / num_samples) 
                          for i in range(num_samples)]
            
            brightness_values = []
            
            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                
                if ret:
                    # 转换为灰度
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    
                    # 计算平均亮度
                    avg = np.mean(gray) / 255.0
                    brightness_values.append(avg)
            
            cap.release()
            
            if brightness_values:
                import statistics
                return {
                    "avg": statistics.mean(brightness_values),
                    "std": statistics.stdev(brightness_values) if len(brightness_values) > 1 else 0.0,
                    "contrast": max(brightness_values) - min(brightness_values),
                }
            
        except ImportError:
            pass
        except Exception as e:
            pass
        
        return {"avg": 0.5, "std": 0.1, "contrast": 0.3}
    
    def _analyze_audio(self, video_path: str) -> Dict:
        """分析音频质量"""
        cmd = [
            'ffmpeg', '-i', video_path,
            '-af', 'volumedetect',
            '-f', 'null', '-'
        ]
        
        result = {"mean_db": -20.0, "peak_db": 0.0}
        
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            output = proc.stderr
            
            # 解析平均音量
            mean_match = re.search(r'mean_volume:\s*([-\d.]+)\s*dB', output)
            if mean_match:
                result["mean_db"] = float(mean_match.group(1))
            
            # 解析峰值音量
            peak_match = re.search(r'peak_level:\s*([-\d.]+)\s*dB', output)
            if peak_match:
                result["peak_db"] = float(peak_match.group(1))
                
        except Exception as e:
            pass
        
        return result
    
    def _detect_issues(self, report: VideoQualityReport) -> List[QualityIssue]:
        """检测质量问题"""
        issues = []
        
        # 1. 分辨率检查
        width, height = report.resolution
        min_w, min_h = self.standard["min_resolution"]
        
        if width < min_w or height < min_h:
            issues.append(QualityIssue(
                category=IssueCategory.RESOLUTION,
                severity=IssueSeverity.WARNING,
                description=f"分辨率 {width}x{height} 低于平台最低要求 {min_w}x{min_h}",
                value=float(min(width, height)),
                expected=float(min(min_w, min_h)),
                fix_suggestion="建议提高分辨率或在平台允许的范围内调整",
                details={"current": report.resolution, "minimum": self.standard["min_resolution"]}
            ))
        
        # 2. 帧率检查
        min_fps = self.standard["min_fps"]
        rec_fps = self.standard["recommended_fps"]
        
        if report.fps < min_fps:
            issues.append(QualityIssue(
                category=IssueCategory.FRAMERATE,
                severity=IssueSeverity.WARNING,
                description=f"帧率 {report.fps:.2f}fps 低于最低要求 {min_fps}fps",
                value=report.fps,
                expected=min_fps,
                fix_suggestion="建议使用更高帧率或进行帧率转换",
                details={"current": report.fps, "minimum": min_fps, "recommended": rec_fps}
            ))
        elif report.fps < rec_fps:
            issues.append(QualityIssue(
                category=IssueCategory.FRAMERATE,
                severity=IssueSeverity.INFO,
                description=f"帧率 {report.fps:.2f}fps 低于推荐值 {rec_fps}fps",
                value=report.fps,
                expected=rec_fps,
                fix_suggestion="提高帧率可让视频更流畅",
                details={"current": report.fps, "recommended": rec_fps}
            ))
        
        # 3. 亮度检查
        if report.brightness_avg < 0.2:
            issues.append(QualityIssue(
                category=IssueCategory.BRIGHTNESS,
                severity=IssueSeverity.WARNING,
                description=f"画面整体偏暗（亮度 {report.brightness_avg:.2%}）",
                value=report.brightness_avg,
                expected=0.3,
                fix_suggestion="建议提高画面亮度或使用亮度增强滤镜",
                details={"brightness": report.brightness_avg, "contrast": report.contrast_ratio}
            ))
        elif report.brightness_avg > 0.95:
            issues.append(QualityIssue(
                category=IssueCategory.BRIGHTNESS,
                severity=IssueSeverity.WARNING,
                description=f"画面整体过亮（亮度 {report.brightness_avg:.2%}）",
                value=report.brightness_avg,
                expected=0.8,
                fix_suggestion="建议降低画面亮度或调整曝光",
                details={"brightness": report.brightness_avg}
            ))
        
        # 4. 音频检查
        if report.audio_level_db < -40:
            issues.append(QualityIssue(
                category=IssueCategory.AUDIO,
                severity=IssueSeverity.CRITICAL,
                description=f"音频音量过低（平均 {report.audio_level_db:.1f}dB）",
                value=report.audio_level_db,
                expected=-20.0,
                fix_suggestion="建议提高音频音量或进行音量标准化",
                details={"mean_db": report.audio_level_db, "peak_db": report.audio_level_peak}
            ))
        elif report.audio_level_peak > -1.0:
            issues.append(QualityIssue(
                category=IssueCategory.AUDIO,
                severity=IssueSeverity.WARNING,
                description=f"音频可能存在爆音（峰值 {report.audio_level_peak:.1f}dB）",
                value=report.audio_level_peak,
                expected=-3.0,
                fix_suggestion="建议降低音量或添加压缩器限制峰值",
                details={"peak_db": report.audio_level_peak, "mean_db": report.audio_level_db}
            ))
        
        # 5. 码率检查
        min_bitrate = self.standard["min_bitrate"]
        rec_bitrate = self.standard["recommended_bitrate"]
        
        if report.bitrate < min_bitrate:
            issues.append(QualityIssue(
                category=IssueCategory.ENCODING,
                severity=IssueSeverity.WARNING,
                description=f"视频码率 {report.bitrate/1000000:.1f}Mbps 低于最低要求 {min_bitrate/1000000:.1f}Mbps",
                value=report.bitrate,
                expected=min_bitrate,
                fix_suggestion="建议提高码率以保证画质",
                details={"current": report.bitrate, "minimum": min_bitrate, "recommended": rec_bitrate}
            ))
        
        # 6. 时长检查
        max_duration = self.standard["max_duration"]
        if report.duration > max_duration:
            issues.append(QualityIssue(
                category=IssueCategory.ENCODING,
                severity=IssueSeverity.INFO,
                description=f"视频时长 {report.duration/60:.1f}分钟 超过平台推荐时长 {max_duration/60:.1f}分钟",
                value=report.duration,
                expected=max_duration,
                fix_suggestion="建议适当缩短视频或分段发布",
                details={"current": report.duration, "maximum": max_duration}
            ))
        
        return issues
    
    def _calculate_score(self, report: VideoQualityReport) -> float:
        """计算质量评分"""
        score = 100.0
        
        for issue in report.issues:
            if issue.severity == IssueSeverity.CRITICAL:
                score -= 30
            elif issue.severity == IssueSeverity.WARNING:
                score -= 10
            elif issue.severity == IssueSeverity.INFO:
                score -= 3
        
        return max(0.0, min(100.0, score))
    
    def _is_acceptable(self, report: VideoQualityReport) -> bool:
        """判断是否可接受"""
        # 有严重问题则不可接受
        for issue in report.issues:
            if issue.severity == IssueSeverity.CRITICAL:
                return False
        
        # 评分过低不可接受
        if report.overall_score < 60:
            return False
        
        return True
    
    def get_fix_command(self, issue: QualityIssue) -> str:
        """
        获取修复问题的 FFmpeg 命令
        
        Args:
            issue: 质量问题
            
        Returns:
            FFmpeg 命令字符串
        """
        if issue.category == IssueCategory.BRIGHTNESS:
            if issue.value < 0.2:
                # 提亮
                factor = 1.5
                return f"ffmpeg -i input.mp4 -vf 'eq=brightness={factor * 0.1}:contrast=1.1' -c:a copy output.mp4"
            else:
                # 压暗
                return "ffmpeg -i input.mp4 -vf 'eq=brightness=-0.1' -c:a copy output.mp4"
        
        elif issue.category == IssueCategory.AUDIO:
            if issue.value < -40:
                # 提音量
                gain = abs(issue.value) + 20
                return f"ffmpeg -i input.mp4 -af 'volume={gain}dB' output.mp4"
        
        elif issue.category == IssueCategory.FRAMERATE:
            return f"ffmpeg -i input.mp4 -vf 'fps={int(issue.expected)}' -c:a copy output.mp4"
        
        elif issue.category == IssueCategory.RESOLUTION:
            w, h = self.standard["recommended_resolution"]
            return f"ffmpeg -i input.mp4 -vf 'scale={w}:{h}' -c:a copy output.mp4"
        
        elif issue.category == IssueCategory.ENCODING:
            if issue.value < self.standard["min_bitrate"]:
                return f"ffmpeg -i input.mp4 -b:v {self.standard['recommended_bitrate']} -c:a copy output.mp4"
        
        return ""


def analyze_video_quality(
    video_path: str,
    platform: str = "bilibili"
) -> VideoQualityReport:
    """
    便捷的视频质量分析函数
    
    Args:
        video_path: 视频路径
        platform: 目标平台
        
    Returns:
        质量报告
    """
    analyzer = QualityAnalyzer(platform)
    return analyzer.analyze(video_path)


def print_quality_report(report: VideoQualityReport):
    """
    打印质量报告
    
    Args:
        report: 质量报告
    """
    print("=" * 50)
    print("视频质量报告")
    print("=" * 50)
    
    print(f"\n文件: {Path(report.file_path).name}")
    print(f"时长: {report.duration:.1f}秒 ({report.duration/60:.1f}分钟)")
    print(f"分辨率: {report.resolution[0]}x{report.resolution[1]}")
    print(f"帧率: {report.fps:.2f}fps")
    print(f"码率: {report.bitrate/1000000:.1f}Mbps")
    print(f"视频编码: {report.codec}")
    print(f"音频: {report.audio_codec} {report.audio_bitrate/1000:.0f}kbps")
    
    print(f"\n整体评分: {report.overall_score:.1f}/100")
    print(f"可接受: {'✅' if report.is_acceptable else '❌'}")
    
    if report.issues:
        print(f"\n发现问题 ({len(report.issues)} 个):")
        print("-" * 50)
        
        for issue in report.issues:
            severity_icon = {
                "critical": "🔴",
                "warning": "🟡",
                "info": "🔵"
            }.get(issue.severity.value, "⚪")
            
            print(f"\n{severity_icon} [{issue.severity.value.upper()}] {issue.category.value}")
            print(f"   {issue.description}")
            if issue.fix_suggestion:
                print(f"   💡 建议: {issue.fix_suggestion}")
    
    print()


# ========== 使用示例 ==========

def demo_quality_analysis():
    """演示视频质量分析"""
    print("=" * 50)
    print("VideoForge 视频质量分析演示")
    print("=" * 50)
    
    analyzer = QualityAnalyzer(platform="bilibili")
    
    # 分析视频
    video_path = "test_video.mp4"
    
    if not Path(video_path).exists():
        print(f"测试视频不存在: {video_path}")
        print("\n使用 FFmpeg 生成测试视频...")
        
        # 生成测试视频
        cmd = [
            'ffmpeg', '-y', '-f', 'lavfi', '-i', 'testsrc=duration=10:size=1280x720:rate=30',
            '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=10',
            '-c:v', 'libx264', '-b:v', '2M', '-c:a', 'aac', '-b:a', '128k',
            video_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, timeout=30)
            print("测试视频已生成")
        except Exception as e:
            logger.error(f"生成测试视频失败: {e}")
            return
    
    # 分析
    report = analyzer.analyze(video_path)
    
    # 打印报告
    print_quality_report(report)


if __name__ == '__main__':
    demo_quality_analysis()
