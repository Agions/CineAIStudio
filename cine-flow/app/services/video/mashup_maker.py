"""
AI 视频混剪制作器 (Mashup Maker)

功能：多素材智能剪辑 + 节奏匹配 + 背景音乐

工作流程:
    1. 分析多个素材视频
    2. 根据背景音乐节奏剪辑
    3. 智能排序素材片段
    4. 添加转场效果
    5. 合成视频或导出剪映草稿

使用示例:
    from app.services.video import MashupMaker, MashupProject
    
    maker = MashupMaker()
    project = maker.create_project(
        source_videos=["clip1.mp4", "clip2.mp4", "clip3.mp4"],
        background_music="bgm.mp3",
        target_duration=30,
    )
    
    # 导出到剪映
    draft_path = maker.export_to_jianying(project, "/path/to/drafts")
"""

import os
import random
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..ai.scene_analyzer import SceneAnalyzer, SceneInfo, AnalysisConfig
from ..export.jianying_exporter import (
    JianyingExporter, JianyingDraft, JianyingConfig,
    Track, TrackType, Segment, TimeRange,
    VideoMaterial, AudioMaterial,
)


class MashupStyle(Enum):
    """混剪风格"""
    FAST_PACED = "fast_paced"      # 快节奏（适合动感音乐）
    CINEMATIC = "cinematic"        # 电影感（适合大气音乐）
    VLOG = "vlog"                  # Vlog 风格（自然过渡）
    HIGHLIGHT = "highlight"        # 高光集锦（体育/游戏）
    MONTAGE = "montage"            # 蒙太奇（情感叙事）


class TransitionType(Enum):
    """转场类型"""
    CUT = "cut"                    # 硬切
    FADE = "fade"                  # 淡入淡出
    DISSOLVE = "dissolve"          # 溶解
    WIPE = "wipe"                  # 擦除
    ZOOM = "zoom"                  # 缩放
    SLIDE = "slide"                # 滑动


@dataclass
class ClipInfo:
    """素材片段信息"""
    source_video: str              # 源视频路径
    source_index: int              # 源视频索引
    
    start: float                   # 片段开始时间
    end: float                     # 片段结束时间
    duration: float                # 片段时长
    
    # 分析数据
    scene_info: Optional[SceneInfo] = None
    suitability_score: float = 0.0
    
    # 在时间轴上的位置
    target_start: float = 0.0
    target_duration: float = 0.0
    
    # 转场
    transition_in: TransitionType = TransitionType.CUT
    transition_out: TransitionType = TransitionType.CUT


@dataclass
class BeatInfo:
    """节拍信息"""
    time: float                    # 节拍时间点（秒）
    strength: float = 1.0          # 节拍强度 (0-1)
    is_downbeat: bool = False      # 是否是强拍


@dataclass
class MashupProject:
    """混剪视频项目"""
    id: str = ""
    name: str = "新建混剪项目"
    
    # 源素材
    source_videos: List[str] = field(default_factory=list)
    background_music: str = ""
    
    # 分析结果
    all_clips: List[ClipInfo] = field(default_factory=list)  # 所有可用片段
    selected_clips: List[ClipInfo] = field(default_factory=list)  # 选中的片段
    beats: List[BeatInfo] = field(default_factory=list)  # 音乐节拍
    
    # 配置
    target_duration: float = 30.0  # 目标时长
    style: MashupStyle = MashupStyle.FAST_PACED
    transition_type: TransitionType = TransitionType.CUT
    
    # 输出
    output_dir: str = ""
    
    @property
    def total_duration(self) -> float:
        """实际总时长"""
        if not self.selected_clips:
            return 0.0
        last = self.selected_clips[-1]
        return last.target_start + last.target_duration


class MashupMaker:
    """
    AI 视频混剪制作器
    
    将多个视频素材智能混剪成一个视频
    
    使用示例:
        maker = MashupMaker()
        
        # 创建项目
        project = maker.create_project(
            source_videos=["clip1.mp4", "clip2.mp4"],
            background_music="bgm.mp3",
            target_duration=30,
        )
        
        # 自动混剪
        maker.auto_mashup(project)
        
        # 导出到剪映
        draft_path = maker.export_to_jianying(project, "/path/to/drafts")
    """
    
    # 风格对应的参数
    STYLE_PARAMS = {
        MashupStyle.FAST_PACED: {
            "avg_clip_duration": 1.5,    # 平均片段时长
            "min_clip_duration": 0.5,
            "max_clip_duration": 3.0,
            "beat_sync": True,           # 是否同步节拍
            "motion_preference": 0.7,    # 倾向动态画面
        },
        MashupStyle.CINEMATIC: {
            "avg_clip_duration": 4.0,
            "min_clip_duration": 2.0,
            "max_clip_duration": 8.0,
            "beat_sync": False,
            "motion_preference": 0.4,
        },
        MashupStyle.VLOG: {
            "avg_clip_duration": 3.0,
            "min_clip_duration": 1.5,
            "max_clip_duration": 6.0,
            "beat_sync": False,
            "motion_preference": 0.5,
        },
        MashupStyle.HIGHLIGHT: {
            "avg_clip_duration": 2.0,
            "min_clip_duration": 0.8,
            "max_clip_duration": 4.0,
            "beat_sync": True,
            "motion_preference": 0.8,
        },
        MashupStyle.MONTAGE: {
            "avg_clip_duration": 3.5,
            "min_clip_duration": 1.5,
            "max_clip_duration": 6.0,
            "beat_sync": True,
            "motion_preference": 0.5,
        },
    }
    
    def __init__(self):
        self.scene_analyzer = SceneAnalyzer(AnalysisConfig(
            scene_threshold=0.3,
            min_scene_duration=0.5,
        ))
        self.jianying_exporter = JianyingExporter()
        
        self._progress_callback: Optional[Callable[[str, float], None]] = None
    
    def set_progress_callback(self, callback: Callable[[str, float], None]) -> None:
        """设置进度回调"""
        self._progress_callback = callback
    
    def _report_progress(self, stage: str, progress: float) -> None:
        """报告进度"""
        if self._progress_callback:
            self._progress_callback(stage, progress)
    
    def create_project(
        self,
        source_videos: List[str],
        background_music: Optional[str] = None,
        target_duration: float = 30.0,
        name: Optional[str] = None,
        style: MashupStyle = MashupStyle.FAST_PACED,
        output_dir: Optional[str] = None,
    ) -> MashupProject:
        """
        创建混剪项目
        
        Args:
            source_videos: 源视频列表
            background_music: 背景音乐路径
            target_duration: 目标时长（秒）
            name: 项目名称
            style: 混剪风格
            output_dir: 输出目录
        """
        import uuid
        
        # 验证文件
        for video in source_videos:
            if not Path(video).exists():
                raise FileNotFoundError(f"视频文件不存在: {video}")
        
        if background_music and not Path(background_music).exists():
            raise FileNotFoundError(f"音乐文件不存在: {background_music}")
        
        project = MashupProject(
            id=str(uuid.uuid4())[:8],
            name=name or "混剪视频",
            source_videos=[str(Path(v).absolute()) for v in source_videos],
            background_music=str(Path(background_music).absolute()) if background_music else "",
            target_duration=target_duration,
            style=style,
            output_dir=output_dir or "./output",
        )
        
        # 分析所有素材
        self._analyze_sources(project)
        
        # 分析音乐节拍
        if project.background_music:
            self._analyze_music_beats(project)
        
        return project
    
    def _analyze_sources(self, project: MashupProject) -> None:
        """分析所有源视频"""
        self._report_progress("分析素材", 0.0)
        
        all_clips = []
        total = len(project.source_videos)
        
        for idx, video_path in enumerate(project.source_videos):
            self._report_progress("分析素材", idx / total)
            
            # 分析场景
            scenes = self.scene_analyzer.analyze(video_path)
            
            # 创建片段
            for scene in scenes:
                clip = ClipInfo(
                    source_video=video_path,
                    source_index=idx,
                    start=scene.start,
                    end=scene.end,
                    duration=scene.duration,
                    scene_info=scene,
                    suitability_score=scene.suitability_score,
                )
                all_clips.append(clip)
        
        project.all_clips = all_clips
        self._report_progress("分析素材", 1.0)
    
    def _analyze_music_beats(self, project: MashupProject) -> None:
        """分析音乐节拍"""
        self._report_progress("分析音乐", 0.0)
        
        try:
            # 尝试使用 librosa 分析节拍
            import librosa
            import numpy as np
            
            y, sr = librosa.load(project.background_music)
            
            # 检测节拍
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            
            # 检测强拍（每4拍一个强拍）
            project.beats = []
            for i, time in enumerate(beat_times):
                beat = BeatInfo(
                    time=float(time),
                    strength=1.0 if i % 4 == 0 else 0.6,
                    is_downbeat=(i % 4 == 0),
                )
                project.beats.append(beat)
            
        except ImportError:
            # 如果没有 librosa，使用简单的固定节拍
            print("提示: 安装 librosa 可获得更好的节拍检测 (pip install librosa)")
            project.beats = self._generate_simple_beats(project.target_duration)
        
        except Exception as e:
            print(f"节拍分析失败: {e}")
            project.beats = self._generate_simple_beats(project.target_duration)
        
        self._report_progress("分析音乐", 1.0)
    
    def _generate_simple_beats(self, duration: float, bpm: float = 120.0) -> List[BeatInfo]:
        """生成简单的固定节拍"""
        beats = []
        interval = 60.0 / bpm  # 每拍间隔
        
        time = 0.0
        beat_count = 0
        
        while time < duration:
            beat = BeatInfo(
                time=time,
                strength=1.0 if beat_count % 4 == 0 else 0.6,
                is_downbeat=(beat_count % 4 == 0),
            )
            beats.append(beat)
            time += interval
            beat_count += 1
        
        return beats
    
    def auto_mashup(self, project: MashupProject) -> None:
        """
        自动混剪
        
        根据风格和节拍自动选择和排列素材
        """
        self._report_progress("智能混剪", 0.0)
        
        params = self.STYLE_PARAMS.get(project.style, self.STYLE_PARAMS[MashupStyle.FAST_PACED])
        
        # 筛选高质量片段
        quality_clips = [c for c in project.all_clips if c.suitability_score >= 40]
        if not quality_clips:
            quality_clips = project.all_clips
        
        # 根据风格偏好排序
        if params["motion_preference"] > 0.5:
            # 偏好动态画面
            quality_clips.sort(
                key=lambda c: (c.scene_info.motion_level if c.scene_info else 0.5),
                reverse=True
            )
        
        # 选择片段
        selected = []
        current_time = 0.0
        used_sources = set()
        
        while current_time < project.target_duration and quality_clips:
            # 确定本段时长
            if params["beat_sync"] and project.beats:
                # 同步节拍：找下一个强拍位置
                clip_duration = self._get_next_beat_duration(
                    current_time, project.beats, params
                )
            else:
                # 随机时长
                clip_duration = random.uniform(
                    params["min_clip_duration"],
                    params["max_clip_duration"]
                )
            
            # 限制不超过目标时长
            if current_time + clip_duration > project.target_duration:
                clip_duration = project.target_duration - current_time
            
            if clip_duration < params["min_clip_duration"]:
                break
            
            # 选择片段（尽量使用不同来源）
            clip = self._select_clip(quality_clips, used_sources, clip_duration)
            if not clip:
                break
            
            # 设置时间轴位置
            clip.target_start = current_time
            clip.target_duration = min(clip_duration, clip.duration)
            
            # 设置转场
            clip.transition_in = project.transition_type
            
            selected.append(clip)
            current_time += clip.target_duration
            used_sources.add(clip.source_index)
            
            # 如果所有来源都用过了，重置
            if len(used_sources) >= len(project.source_videos):
                used_sources.clear()
            
            self._report_progress("智能混剪", current_time / project.target_duration)
        
        project.selected_clips = selected
        self._report_progress("智能混剪", 1.0)
    
    def _get_next_beat_duration(
        self,
        current_time: float,
        beats: List[BeatInfo],
        params: dict,
    ) -> float:
        """获取到下一个合适节拍点的时长"""
        min_dur = params["min_clip_duration"]
        max_dur = params["max_clip_duration"]
        
        # 找到当前时间之后的节拍
        future_beats = [b for b in beats if b.time > current_time + min_dur]
        
        if not future_beats:
            return random.uniform(min_dur, max_dur)
        
        # 优先选择强拍
        for beat in future_beats:
            dur = beat.time - current_time
            if min_dur <= dur <= max_dur:
                if beat.is_downbeat:
                    return dur
        
        # 否则选择任意节拍
        for beat in future_beats:
            dur = beat.time - current_time
            if min_dur <= dur <= max_dur:
                return dur
        
        return random.uniform(min_dur, max_dur)
    
    def _select_clip(
        self,
        clips: List[ClipInfo],
        used_sources: set,
        target_duration: float,
    ) -> Optional[ClipInfo]:
        """选择合适的片段"""
        # 优先选择未使用来源的片段
        candidates = [c for c in clips if c.source_index not in used_sources]
        if not candidates:
            candidates = clips
        
        # 筛选时长足够的片段
        valid = [c for c in candidates if c.duration >= target_duration * 0.8]
        if not valid:
            valid = candidates
        
        if not valid:
            return None
        
        # 随机选择（带权重：分数越高越容易被选中）
        weights = [c.suitability_score + 10 for c in valid]
        total_weight = sum(weights)
        
        if total_weight <= 0:
            selected = random.choice(valid)
        else:
            r = random.uniform(0, total_weight)
            cumulative = 0
            selected = valid[0]
            for clip, weight in zip(valid, weights):
                cumulative += weight
                if r <= cumulative:
                    selected = clip
                    break
        
        # 从列表中移除（避免重复使用同一片段）
        clips.remove(selected)
        
        return selected
    
    def export_to_jianying(
        self,
        project: MashupProject,
        jianying_drafts_dir: str,
    ) -> str:
        """
        导出到剪映草稿
        
        Args:
            project: 项目对象
            jianying_drafts_dir: 剪映草稿目录
            
        Returns:
            草稿路径
        """
        self._report_progress("导出剪映", 0.0)
        
        exporter = JianyingExporter(JianyingConfig(
            canvas_ratio="9:16",
            copy_materials=True,
        ))
        
        draft = exporter.create_draft(project.name)
        
        # 1. 添加视频轨道
        video_track = Track(type=TrackType.VIDEO, attribute=1)
        draft.add_track(video_track)
        
        # 为每个源视频创建素材
        video_materials = {}
        for video_path in project.source_videos:
            material = VideoMaterial(path=video_path)
            draft.add_video(material)
            video_materials[video_path] = material
        
        # 添加视频片段
        for clip in project.selected_clips:
            material = video_materials.get(clip.source_video)
            if material:
                segment = Segment(
                    material_id=material.id,
                    source_timerange=TimeRange.from_seconds(clip.start, clip.target_duration),
                    target_timerange=TimeRange.from_seconds(clip.target_start, clip.target_duration),
                )
                video_track.add_segment(segment)
        
        # 2. 添加背景音乐轨道
        if project.background_music:
            audio_track = Track(type=TrackType.AUDIO)
            draft.add_track(audio_track)
            
            audio_material = AudioMaterial(
                path=project.background_music,
                duration=int(project.total_duration * 1_000_000),
                name=Path(project.background_music).stem,
            )
            draft.add_audio(audio_material)
            
            audio_segment = Segment(
                material_id=audio_material.id,
                source_timerange=TimeRange.from_seconds(0, project.total_duration),
                target_timerange=TimeRange.from_seconds(0, project.total_duration),
            )
            audio_track.add_segment(audio_segment)
        
        # 导出
        draft_path = exporter.export(draft, jianying_drafts_dir)
        
        self._report_progress("导出剪映", 1.0)
        
        return draft_path


# =========== 便捷函数 ===========

def create_mashup(
    source_videos: List[str],
    background_music: str,
    output_jianying_dir: str,
    target_duration: float = 30.0,
    style: MashupStyle = MashupStyle.FAST_PACED,
) -> str:
    """
    一键创建混剪视频
    
    Args:
        source_videos: 源视频列表
        background_music: 背景音乐
        output_jianying_dir: 剪映草稿目录
        target_duration: 目标时长
        style: 混剪风格
        
    Returns:
        剪映草稿路径
    """
    maker = MashupMaker()
    
    project = maker.create_project(
        source_videos=source_videos,
        background_music=background_music,
        target_duration=target_duration,
        style=style,
    )
    
    maker.auto_mashup(project)
    
    return maker.export_to_jianying(project, output_jianying_dir)


def demo_mashup():
    """演示混剪视频制作"""
    print("=" * 50)
    print("AI 视频混剪制作演示")
    print("=" * 50)
    
    # 检查测试文件
    test_videos = ["clip1.mp4", "clip2.mp4", "clip3.mp4"]
    test_music = "bgm.mp3"
    
    for f in test_videos + [test_music]:
        if not Path(f).exists():
            print(f"测试文件不存在: {f}")
            print("请准备测试文件后再运行")
            return
    
    maker = MashupMaker()
    
    # 创建项目
    project = maker.create_project(
        source_videos=test_videos,
        background_music=test_music,
        target_duration=30.0,
        style=MashupStyle.FAST_PACED,
    )
    
    print(f"\n项目创建成功: {project.name}")
    print(f"素材数量: {len(project.source_videos)}")
    print(f"可用片段: {len(project.all_clips)}")
    print(f"检测节拍: {len(project.beats)}")
    
    # 自动混剪
    maker.auto_mashup(project)
    
    print(f"\n混剪完成:")
    print(f"选中片段: {len(project.selected_clips)}")
    print(f"总时长: {project.total_duration:.2f}秒")
    
    for i, clip in enumerate(project.selected_clips):
        print(f"  片段 {i+1}: 来源{clip.source_index} "
              f"[{clip.start:.2f}s-{clip.end:.2f}s] -> "
              f"[{clip.target_start:.2f}s, {clip.target_duration:.2f}s]")
    
    # 导出
    output_dir = "./output/jianying_drafts"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    draft_path = maker.export_to_jianying(project, output_dir)
    print(f"\n✅ 剪映草稿已导出: {draft_path}")


if __name__ == '__main__':
    demo_mashup()
