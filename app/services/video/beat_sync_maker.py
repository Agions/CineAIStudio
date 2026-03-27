#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Beat-Sync 混剪制作器

基于音乐节拍的智能视频混剪，确保视频切换点与音乐节拍完美对齐。

工作流程:
    1. 分析背景音乐的节拍（BPM、节拍点、段落结构）
    2. 分析素材视频的场景和画面
    3. 根据节拍生成 Beat-sync 剪辑点
    4. 将素材分配到节拍点，创建节奏感强的混剪
    5. 添加转场效果
    6. 导出视频或项目文件

使用示例:
    from app.services.video import BeatSyncMashupMaker, BeatSyncConfig
    
    maker = BeatSyncMashupMaker()
    
    # 创建 Beat-sync 混剪
    project = maker.create_beat_sync_project(
        source_videos=["clip1.mp4", "clip2.mp4"],
        background_music="bgm.mp3",
        target_duration=60,
    )
    
    # 导出视频
    maker.export_video(project, "output.mp4")
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# 获取 logger
logger = logging.getLogger(__name__)

from .base_maker import BaseVideoMaker
from ..audio.beat_detector import (
    BeatDetector, 
    BeatInfo, 
    BeatSyncCutpoint,
    BeatStrength,
    MusicSection,
)
from ..ai.scene_analyzer import SceneAnalyzer, SceneInfo


class BeatSyncStyle(Enum):
    """Beat-sync 混剪风格"""
    STROBE = "strobe"           # 强节奏快速切换
    SMOOTH = "smooth"           # 流畅过渡
    DYNAMIC = "dynamic"         # 动态（根据段落变化节奏）
    IMPACT = "impact"           # 冲击感（强拍大切换）


class CutPosition(Enum):
    """剪辑位置偏好"""
    ON_BEAT = "on_beat"         # 在节拍上
    BEFORE_BEAT = "before_beat" # 节拍前
    AFTER_BEAT = "after_beat"   # 节拍后


@dataclass
class BeatSyncConfig:
    """Beat-sync 配置"""
    # 目标参数
    target_duration: float = 60.0      # 目标时长（秒）
    target_fps: float = 30.0           # 输出帧率
    
    # 节拍参数
    bpm_override: float = 0.0          # 手动指定 BPM（0 = 自动检测）
    min_cut_interval: float = 0.5      # 最小剪辑间隔（秒）
    prefer_strong_beats: bool = True   # 优先使用强拍
    energy_threshold: float = 0.3      # 能量阈值
    
    # 风格参数
    style: BeatSyncStyle = BeatSyncStyle.DYNAMIC
    cut_position: CutPosition = CutPosition.BEFORE_BEAT
    
    # 素材参数
    max_clips_per_video: int = 10      # 每个视频最大使用片段数
    min_clip_duration: float = 0.3     # 最小片段时长（秒）
    
    # 转场
    use_beat_transitions: bool = True  # 是否在节拍点使用特殊转场


@dataclass
class BeatSyncSegment:
    """
    Beat-sync 片段
    
    带有节拍对齐信息的视频片段
    """
    # 源信息
    source_video: str
    source_start: float           # 源视频开始时间
    source_end: float             # 源视频结束时间
    scene_info: Optional[SceneInfo] = None
    
    # Beat-sync 信息
    target_start: float = 0.0     # 在时间轴上的开始时间
    target_end: float = 0.0       # 在时间轴上的结束时间
    beat_timestamp: float = 0.0   # 对齐的节拍时间点
    beat_strength: BeatStrength = BeatStrength.WEAK
    
    # 画面特征
    brightness: float = 0.5       # 亮度 0-1
    motion_level: float = 0.5      # 运动程度 0-1
    has_audio: bool = True        # 是否有音频


@dataclass
class BeatSyncProject:
    """Beat-sync 混剪项目"""
    id: str = ""
    name: str = "Beat-Sync 混剪"
    
    # 配置
    config: BeatSyncConfig = field(default_factory=BeatSyncConfig)
    
    # 分析结果
    audio_analysis: Any = None    # 音频分析结果
    
    # 片段
    segments: List[BeatSyncSegment] = field(default_factory=list)
    
    # 元数据
    total_duration: float = 0.0
    cut_count: int = 0
    bpm: float = 0.0


class BeatSyncMashupMaker:
    """
    Beat-Sync 混剪制作器
    
    基于音乐节拍的智能视频剪辑
    """
    
    def __init__(self):
        self.beat_detector = BeatDetector()
        self.scene_analyzer = SceneAnalyzer()
    
    def create_beat_sync_project(
        self,
        source_videos: List[str],
        background_music: str,
        config: Optional[BeatSyncConfig] = None,
    ) -> BeatSyncProject:
        """
        创建 Beat-sync 混剪项目
        
        Args:
            source_videos: 源视频列表
            background_music: 背景音乐路径
            config: 配置
            
        Returns:
            Beat-sync 项目
        """
        config = config or BeatSyncConfig()
        project = BeatSyncProject(
            config=config,
            name=f"Beat-Sync {Path(background_music).stem}"
        )
        
        # 1. 分析背景音乐
        project.audio_analysis = self._analyze_music(background_music, config)
        project.bpm = project.audio_analysis.bpm
        project.cut_count = len(project.audio_analysis.beat_sync_cutpoints)
        
        # 2. 分析所有源视频
        video_scenes = self._analyze_all_videos(source_videos)
        
        # 3. 根据节拍分配片段
        project.segments = self._assign_segments_to_beats(
            video_scenes, 
            project.audio_analysis,
            config
        )
        
        # 4. 计算总时长
        if project.segments:
            project.total_duration = max(s.target_end for s in project.segments)
        
        return project
    
    def _analyze_music(
        self, 
        music_path: str, 
        config: BeatSyncConfig
    ) -> Any:
        """分析背景音乐"""
        # 如果是视频，先提取音频
        if music_path.endswith(('.mp4', '.avi', '.mov', '.mkv')):
            music_path = self.beat_detector.extract_audio_from_video(music_path)
        
        # 分析音频
        analysis = self.beat_detector.analyze(music_path)
        
        # 如果指定了 BPM，覆盖检测值
        if config.bpm_override > 0:
            analysis.bpm = config.bpm_override
            analysis.beat_interval = 60.0 / config.bpm_override
        
        return analysis
    
    def _analyze_all_videos(
        self, 
        video_paths: List[str]
    ) -> Dict[str, List[SceneInfo]]:
        """分析所有源视频的场景"""
        video_scenes = {}
        
        for video_path in video_paths:
            try:
                scenes = self.scene_analyzer.analyze(video_path)
                video_scenes[video_path] = scenes
            except Exception as e:
                logger.warning(f"分析视频失败 {video_path}: {e}")
                video_scenes[video_path] = []
        
        return video_scenes
    
    def _assign_segments_to_beats(
        self,
        video_scenes: Dict[str, List[SceneInfo]],
        audio_analysis: Any,
        config: BeatSyncConfig,
    ) -> List[BeatSyncSegment]:
        """根据节拍点分配视频片段"""
        segments = []
        cutpoints = audio_analysis.beat_sync_cutpoints
        
        if not cutpoints:
            return segments
        
        # 计算需要的片段数（留出开头和结尾的余量）
        usable_cutpoints = cutpoints[1:-1] if len(cutpoints) > 2 else cutpoints
        
        # 按视频轮询分配
        video_list = list(video_scenes.keys())
        if not video_list:
            return segments
        
        video_idx = 0
        clip_count = 0
        
        for i, cutpoint in enumerate(usable_cutpoints):
            # 检查是否达到目标时长
            if config.target_duration > 0:
                if cutpoint.timestamp >= config.target_duration:
                    break
            
            # 获取当前视频的场景
            current_video = video_list[video_idx % len(video_list)]
            scenes = video_scenes.get(current_video, [])
            
            if not scenes:
                video_idx += 1
                continue
            
            # 选择一个合适的场景片段
            scene = self._select_scene_for_beat(scenes, cutpoint, config)
            
            if scene:
                segment = BeatSyncSegment(
                    source_video=current_video,
                    source_start=scene.start,
                    source_end=scene.end,
                    scene_info=scene,
                    target_start=cutpoint.timestamp,
                    target_end=cutpoint.timestamp + scene.duration,
                    beat_timestamp=cutpoint.timestamp,
                    beat_strength=cutpoint.strength,
                    brightness=scene.avg_brightness,
                    motion_level=scene.motion_level,
                )
                segments.append(segment)
                clip_count += 1
            
            # 轮转到下一个视频
            video_idx += 1
            
            # 检查片段数量限制
            if clip_count >= config.max_clips_per_video * len(video_list):
                break
        
        return segments
    
    def _select_scene_for_beat(
        self,
        scenes: List[SceneInfo],
        cutpoint: BeatSyncCutpoint,
        config: BeatSyncConfig,
    ) -> Optional[SceneInfo]:
        """为节拍点选择合适的场景"""
        # 过滤时长太短的场景
        valid_scenes = [s for s in scenes 
                      if s.duration >= config.min_clip_duration]
        
        if not valid_scenes:
            return None
        
        # 根据风格选择
        if config.style == BeatSyncStyle.STROBE:
            # 快节奏：优先选择短片段
            valid_scenes.sort(key=lambda s: s.duration)
            # 优先选择运动较多的
            return valid_scenes[0]
        
        elif config.style == BeatSyncStyle.IMPACT:
            # 冲击感：优先强拍 + 高能量
            if cutpoint.strength == BeatStrength.STRONG:
                # 强拍优先选择运动镜头
                valid_scenes.sort(key=lambda s: -s.motion_level)
            else:
                # 弱拍选择静态镜头
                valid_scenes.sort(key=lambda s: s.motion_level)
            return valid_scenes[0] if valid_scenes else None
        
        elif config.style == BeatSyncStyle.SMOOTH:
            # 流畅：优先选择亮度、节奏平稳的
            valid_scenes.sort(key=lambda s: abs(s.avg_brightness - 0.5) + abs(s.motion_level - 0.3))
            return valid_scenes[0] if valid_scenes else None
        
        else:  # DYNAMIC
            # 动态：根据节拍强度选择
            if cutpoint.strength == BeatStrength.STRONG and cutpoint.energy > 0.7:
                # 高能量强拍：选择运动镜头
                valid_scenes.sort(key=lambda s: -s.motion_level)
            else:
                # 其他：选择中等运动
                valid_scenes.sort(key=lambda s: abs(s.motion_level - 0.4))
            return valid_scenes[0] if valid_scenes else None
    
    def get_beat_sync_report(self, project: BeatSyncProject) -> Dict[str, Any]:
        """
        生成 Beat-sync 分析报告
        
        Args:
            project: Beat-sync 项目
            
        Returns:
            分析报告
        """
        report = {
            "project_name": project.name,
            "total_duration": project.total_duration,
            "bpm": project.bpm,
            "beat_interval": 60.0 / project.bpm if project.bpm > 0 else 0,
            "total_cuts": project.cut_count,
            "segments_count": len(project.segments),
            "style": project.config.style.value,
            "audio_analysis": None,
        }
        
        # 音频分析摘要
        if project.audio_analysis:
            analysis = project.audio_analysis
            report["audio_analysis"] = {
                "duration": analysis.duration,
                "bpm": analysis.bpm,
                "total_beats": len(analysis.beats),
                "sections": [
                    {
                        "type": s.section_type.value,
                        "start": s.start,
                        "end": s.end,
                        "duration": s.end - s.start,
                    }
                    for s in analysis.sections
                ],
            }
        
        # 节拍使用统计
        beat_usage = {"strong": 0, "medium": 0, "weak": 0}
        for seg in project.segments:
            beat_usage[seg.beat_strength.value] += 1
        report["beat_usage"] = beat_usage
        
        return report
    
    def export_video(
        self,
        project: BeatSyncProject,
        output_path: str,
        quality: str = "high",
    ) -> str:
        """
        导出 Beat-sync 混剪视频
        
        Args:
            project: 项目
            output_path: 输出路径
            quality: 质量 (low/medium/high)
            
        Returns:
            输出文件路径
        """
        if not project.segments:
            raise ValueError("项目没有片段可导出")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建临时文件列表
        concat_list = output_path.parent / "concat_list.txt"
        
        # 先将每个片段单独导出
        temp_dir = output_path.parent / "temp_segments"
        temp_dir.mkdir(exist_ok=True)
        
        segment_files = []
        for i, segment in enumerate(project.segments):
            temp_file = temp_dir / f"seg_{i:03d}.mp4"
            self._export_single_segment(segment, str(temp_file))
            if temp_file.exists():
                segment_files.append(temp_file)
        
        # 生成合成列表
        with open(concat_list, 'w') as f:
            for seg_file in segment_files:
                f.write(f"file '{seg_file}'\n")
        
        # 合并视频
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_list),
            '-c:v', 'libx264' if quality == 'high' else 'libx265',
            '-preset', 'medium',
            '-crf', '23' if quality == 'high' else '28',
            '-c:a', 'aac',
            '-b:a', '192k',
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"导出视频失败: {e}")
            raise
        
        # 清理临时文件
        for f in segment_files:
            try:
                f.unlink()
            except Exception:
                logger.debug("Operation failed")
        
        try:
            concat_list.unlink()
            temp_dir.rmdir()
        except Exception:
            logger.debug("Operation failed")
        
        return str(output_path)
    
    def _export_single_segment(
        self,
        segment: BeatSyncSegment,
        output_path: str,
    ) -> bool:
        """导出单个片段"""
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(segment.source_start),
            '-t', str(segment.source_end - segment.source_start),
            '-i', segment.source_video,
            '-c:v', 'copy',
            '-c:a', 'copy',
            '-avoid_negative_ts', 'make_zero',
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            return result.returncode == 0
        except Exception:
            return False


def create_beat_sync_mashup(
    source_videos: List[str],
    background_music: str,
    output_path: str,
    target_duration: float = 60.0,
    style: BeatSyncStyle = BeatSyncStyle.DYNAMIC,
) -> str:
    """
    便捷的 Beat-sync 混剪创建函数
    
    Args:
        source_videos: 源视频列表
        background_music: 背景音乐
        output_path: 输出路径
        target_duration: 目标时长
        style: 混剪风格
        
    Returns:
        输出文件路径
    """
    config = BeatSyncConfig(
        target_duration=target_duration,
        style=style,
    )
    
    maker = BeatSyncMashupMaker()
    project = maker.create_beat_sync_project(
        source_videos=source_videos,
        background_music=background_music,
        config=config,
    )
    
    return maker.export_video(project, output_path)


# ========== 使用示例 ==========

def demo_beat_sync():
    """演示 Beat-sync 混剪"""
    print("=" * 50)
    print("Beat-Sync 混剪演示")
    print("=" * 50)
    
    maker = BeatSyncMashupMaker()
    
    # 假设有测试文件
    test_music = "demo_music.mp3"
    test_videos = ["clip1.mp4", "clip2.mp4", "clip3.mp4"]
    
    if not Path(test_music).exists():
        print(f"测试音乐不存在: {test_music}")
        return
    
    # 创建配置
    config = BeatSyncConfig(
        target_duration=30.0,  # 30秒
        style=BeatSyncStyle.DYNAMIC,
        prefer_strong_beats=True,
    )
    
    # 创建项目
    project = maker.create_beat_sync_project(
        source_videos=test_videos,
        background_music=test_music,
        config=config,
    )
    
    print(f"\n项目: {project.name}")
    print(f"BPM: {project.bpm}")
    print(f"节拍剪辑点: {project.cut_count}")
    print(f"生成片段: {len(project.segments)}")
    print(f"总时长: {project.total_duration:.2f}s")
    
    # 打印报告
    report = maker.get_beat_sync_report(project)
    print(f"\n节拍使用统计: {report['beat_usage']}")
    
    # 导出视频
    # output = maker.export_video(project, "output_beatsync.mp4")
    # print(f"\n已导出: {output}")


if __name__ == '__main__':
    demo_beat_sync()
