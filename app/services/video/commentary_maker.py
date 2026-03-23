"""
AI 视频解说制作器 (Commentary Maker)

功能：原视频 + AI 解说配音 + 动态字幕

工作流程:
    1. 分析原视频场景
    2. 生成解说文案
    3. 生成 AI 配音
    4. 生成动态字幕
    5. 合成视频或导出剪映草稿

使用示例:
    from app.services.video import CommentaryMaker, CommentaryProject

    maker = CommentaryMaker()
    project = maker.create_project(
        source_video="input.mp4",
        topic="解析这部电影的深层含义",
    )

    # 导出到剪映
    draft_path = maker.export_to_jianying(project, "/path/to/drafts")
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from .base_maker import BaseVideoMaker, BaseProject, merge_audio_files, composite_video_with_audio
from ..ai.scene_analyzer import SceneAnalyzer, SceneInfo, AnalysisConfig
from ..ai.script_generator import ScriptGenerator, ScriptConfig, ScriptStyle
from ..ai.voice_generator import VoiceGenerator, VoiceConfig
from ..viral_video.caption_generator import CaptionGenerator, CaptionStyle
from ..export.jianying_exporter import (
    JianyingDraft,
    Track, TrackType, Segment, TimeRange,
    VideoMaterial, AudioMaterial, TextMaterial,
)


class CommentaryStyle(Enum):
    """解说风格"""
    EXPLAINER = "explainer"        # 解释说明型
    REVIEW = "review"              # 影评/测评型
    STORYTELLING = "storytelling"  # 故事讲述型
    EDUCATIONAL = "educational"    # 教育科普型
    NEWS = "news"                  # 新闻播报型


@dataclass
class CommentarySegment:
    """解说片段"""
    script: str                    # 解说文案
    video_start: float             # 对应视频开始时间
    video_end: float               # 对应视频结束时间
    audio_path: str = ""           # 配音文件路径
    audio_duration: float = 0.0    # 配音时长
    
    # 字幕
    captions: List[Dict] = field(default_factory=list)


@dataclass
class CommentaryProject(BaseProject):
    """解说视频项目"""
    # 解说内容
    topic: str = ""                # 解说主题
    full_script: str = ""          # 完整文案
    segments: List[CommentarySegment] = field(default_factory=list)

    # 配置
    style: CommentaryStyle = CommentaryStyle.EXPLAINER
    voice_config: VoiceConfig = field(default_factory=VoiceConfig)
    caption_style: CaptionStyle = field(default_factory=lambda: CaptionStyle.VIRAL)

    @property
    def total_duration(self) -> float:
        """总时长（配音时长）"""
        return sum(seg.audio_duration for seg in self.segments)


class CommentaryMaker(BaseVideoMaker[CommentaryProject]):
    """
    AI 视频解说制作器

    将原视频转换为带有 AI 解说的视频

    使用示例:
        maker = CommentaryMaker()

        # 创建项目
        project = maker.create_project(
            source_video="movie_clip.mp4",
            topic="这部电影讲述了一个关于勇气与牺牲的故事",
            style=CommentaryStyle.STORYTELLING,
        )

        # 生成解说
        maker.generate_script(project)

        # 生成配音
        maker.generate_voice(project)

        # 生成字幕
        maker.generate_captions(project)

        # 导出到剪映
        draft_path = maker.export_to_jianying(project, "/path/to/drafts")
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        voice_provider: str = "edge",
    ):
        super().__init__()
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.voice_provider = voice_provider

        self.voice_generator = VoiceGenerator(provider=voice_provider)
        self.caption_generator = CaptionGenerator()
    
    def create_project(
        self,
        source_video: str,
        topic: str,
        name: Optional[str] = None,
        style: CommentaryStyle = CommentaryStyle.EXPLAINER,
        voice_config: Optional[VoiceConfig] = None,
        caption_style: Optional[CaptionStyle] = None,
        output_dir: Optional[str] = None,
        **kwargs,
    ) -> CommentaryProject:
        """
        创建解说项目

        Args:
            source_video: 源视频路径
            topic: 解说主题/内容
            name: 项目名称
            style: 解说风格
            voice_config: 配音配置
            caption_style: 字幕风格
            output_dir: 输出目录
        """
        project = CommentaryProject(
            topic=topic,
            style=style,
            voice_config=voice_config or VoiceConfig(),
            caption_style=caption_style or CaptionStyle.VIRAL,
        )

        self._report_progress("分析视频", 0.0)
        self._init_project(project, source_video, name, output_dir)
        self._report_progress("分析视频", 1.0)

        return project
    
    def generate_script(
        self,
        project: CommentaryProject,
        custom_script: Optional[str] = None,
    ) -> None:
        """
        生成解说文案
        
        Args:
            project: 项目对象
            custom_script: 自定义文案（如果提供则跳过 AI 生成）
        """
        self._report_progress("生成文案", 0.0)
        
        if custom_script:
            project.full_script = custom_script
        else:
            if not self.openai_api_key:
                raise ValueError("生成文案需要 OpenAI API Key")
            
            # 使用 AI 生成文案
            script_generator = ScriptGenerator(api_key=self.openai_api_key)
            
            # 根据风格选择配置
            style_map = {
                CommentaryStyle.EXPLAINER: ScriptStyle.COMMENTARY,
                CommentaryStyle.REVIEW: ScriptStyle.COMMENTARY,
                CommentaryStyle.STORYTELLING: ScriptStyle.NARRATION,
                CommentaryStyle.EDUCATIONAL: ScriptStyle.EDUCATIONAL,
                CommentaryStyle.NEWS: ScriptStyle.COMMENTARY,
            }
            
            config = ScriptConfig(
                style=style_map.get(project.style, ScriptStyle.COMMENTARY),
                target_duration=project.video_duration,
                include_hook=True,
            )
            
            result = script_generator.generate(project.topic, config)
            project.full_script = result.content
        
        # 将文案分段，对应视频场景
        self._segment_script(project)
        
        self._report_progress("生成文案", 1.0)
    
    def _segment_script(self, project: CommentaryProject) -> None:
        """将文案分段，匹配视频场景"""
        # 按段落分割文案
        paragraphs = [p.strip() for p in project.full_script.split('\n\n') if p.strip()]
        
        if not paragraphs:
            paragraphs = [project.full_script]
        
        # 获取最佳场景
        best_scenes = self.scene_analyzer.get_best_scenes(
            project.scenes,
            count=len(paragraphs),
            min_score=30.0,
        )
        
        # 如果场景不够，重复使用
        while len(best_scenes) < len(paragraphs):
            best_scenes.extend(best_scenes[:len(paragraphs) - len(best_scenes)])
        
        # 创建片段
        project.segments = []
        for i, para in enumerate(paragraphs):
            scene = best_scenes[i] if i < len(best_scenes) else best_scenes[-1]
            
            segment = CommentarySegment(
                script=para,
                video_start=scene.start,
                video_end=scene.end,
            )
            project.segments.append(segment)
    
    def generate_voice(
        self,
        project: CommentaryProject,
        voice_config: Optional[VoiceConfig] = None,
    ) -> None:
        """
        生成 AI 配音
        
        Args:
            project: 项目对象
            voice_config: 配音配置
        """
        if voice_config:
            project.voice_config = voice_config
        
        output_dir = Path(project.output_dir) / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        total = len(project.segments)
        
        for i, segment in enumerate(project.segments):
            self._report_progress("生成配音", i / total)
            
            audio_path = output_dir / f"segment_{i:03d}.mp3"
            
            result = self.voice_generator.generate(
                text=segment.script,
                output_path=str(audio_path),
                config=project.voice_config,
            )
            
            segment.audio_path = result.audio_path
            segment.audio_duration = result.duration
        
        self._report_progress("生成配音", 1.0)
    
    def generate_captions(self, project: CommentaryProject) -> None:
        """
        生成动态字幕
        
        Args:
            project: 项目对象
        """
        self._report_progress("生成字幕", 0.0)
        
        current_time = 0.0
        
        for i, segment in enumerate(project.segments):
            # 使用爆款字幕生成器
            caption = self.caption_generator.generate_from_text(
                text=segment.script,
                start_time=current_time,
                duration=segment.audio_duration,
            )
            
            # 转换为简单格式
            segment.captions = []
            for word in caption.words:
                segment.captions.append({
                    "text": word.text,
                    "start": word.start_time,
                    "duration": word.duration,
                    "is_keyword": word.is_keyword,
                })
            
            current_time += segment.audio_duration
            self._report_progress("生成字幕", (i + 1) / len(project.segments))
        
        self._report_progress("生成字幕", 1.0)
    
    def _build_jianying_tracks(self, draft: JianyingDraft, project: CommentaryProject) -> None:
        """构建解说视频的剪映轨道"""
        # 1. 视频轨道
        video_track = Track(type=TrackType.VIDEO, attribute=1)
        draft.add_track(video_track)

        video_material = VideoMaterial(
            path=project.source_video,
            duration=int(project.video_duration * 1_000_000),
        )
        draft.add_video(video_material)

        # 根据配音时长添加视频片段
        current_time = 0.0
        for segment in project.segments:
            video_segment = Segment(
                material_id=video_material.id,
                source_timerange=TimeRange.from_seconds(
                    segment.video_start,
                    min(segment.audio_duration, segment.video_end - segment.video_start),
                ),
                target_timerange=TimeRange.from_seconds(current_time, segment.audio_duration),
            )
            video_track.add_segment(video_segment)
            current_time += segment.audio_duration

        # 2. 音频轨道（配音）
        audio_track = Track(type=TrackType.AUDIO)
        draft.add_track(audio_track)

        current_time = 0.0
        for segment in project.segments:
            if segment.audio_path:
                audio_material = AudioMaterial(
                    path=segment.audio_path,
                    duration=int(segment.audio_duration * 1_000_000),
                    name=Path(segment.audio_path).stem,
                )
                draft.add_audio(audio_material)

                audio_segment = Segment(
                    material_id=audio_material.id,
                    source_timerange=TimeRange.from_seconds(0, segment.audio_duration),
                    target_timerange=TimeRange.from_seconds(current_time, segment.audio_duration),
                )
                audio_track.add_segment(audio_segment)

            current_time += segment.audio_duration

        # 3. 字幕轨道
        text_track = Track(type=TrackType.TEXT)
        draft.add_track(text_track)

        for segment in project.segments:
            for cap in segment.captions:
                text_material = TextMaterial(
                    content=cap["text"],
                    font_size=8.0 if not cap.get("is_keyword") else 10.0,
                    font_color="#FFFFFF" if not cap.get("is_keyword") else "#F43F5E",
                )
                draft.add_text(text_material)

                text_segment = Segment(
                    material_id=text_material.id,
                    source_timerange=TimeRange.from_seconds(0, cap["duration"]),
                    target_timerange=TimeRange.from_seconds(cap["start"], cap["duration"]),
                )
                text_track.add_segment(text_segment)

    def export_video(
        self,
        project: CommentaryProject,
        output_path: str,
    ) -> str:
        """直接导出为视频文件（使用 FFmpeg）"""
        audio_list = [s.audio_path for s in project.segments if s.audio_path]
        if not audio_list:
            raise ValueError("没有可用的配音文件")

        Path(project.output_dir).mkdir(parents=True, exist_ok=True)
        merged_audio = Path(project.output_dir) / "merged_audio.mp3"

        merge_audio_files(audio_list, str(merged_audio))
        return composite_video_with_audio(project.source_video, str(merged_audio), output_path)


# =========== 便捷函数 ===========

def create_commentary(
    source_video: str,
    topic: str,
    output_jianying_dir: str,
    style: CommentaryStyle = CommentaryStyle.EXPLAINER,
) -> str:
    """
    一键创建解说视频
    
    Args:
        source_video: 源视频
        topic: 解说主题
        output_jianying_dir: 剪映草稿目录
        style: 解说风格
        
    Returns:
        剪映草稿路径
    """
    maker = CommentaryMaker()
    
    # 创建项目
    project = maker.create_project(source_video, topic, style=style)
    
    # 生成内容
    maker.generate_script(project)
    maker.generate_voice(project)
    maker.generate_captions(project)
    
    # 导出
    return maker.export_to_jianying(project, output_jianying_dir)


def demo_commentary():
    """演示解说视频制作"""
    print("=" * 50)
    print("AI 视频解说制作演示")
    print("=" * 50)
    
    # 注意：需要准备一个测试视频
    maker = CommentaryMaker(voice_provider="edge")
    
    # 假设有一个测试视频
    test_video = "test_video.mp4"
    
    if not Path(test_video).exists():
        print(f"测试视频不存在: {test_video}")
        print("请准备一个测试视频后再运行")
        return
    
    # 创建项目
    project = maker.create_project(
        source_video=test_video,
        topic="这是一个关于自然风光的视频，让我们一起欣赏大自然的美丽",
        style=CommentaryStyle.STORYTELLING,
    )
    
    print(f"\n项目创建成功: {project.name}")
    print(f"视频时长: {project.video_duration:.2f}秒")
    print(f"检测到 {len(project.scenes)} 个场景")
    
    # 使用自定义文案（避免调用 OpenAI API）
    custom_script = """
    你好，欢迎来到这个美丽的世界。
    
    今天我们将一起欣赏大自然最动人的风景。
    
    让我们放慢脚步，感受这份宁静与美好。
    """
    
    maker.generate_script(project, custom_script=custom_script)
    print(f"\n文案已生成，共 {len(project.segments)} 个片段")
    
    # 生成配音
    maker.generate_voice(project)
    print(f"配音已生成，总时长: {project.total_duration:.2f}秒")
    
    # 生成字幕
    maker.generate_captions(project)
    print("字幕已生成")
    
    # 导出到剪映（假设目录）
    output_dir = "./output/jianying_drafts"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    draft_path = maker.export_to_jianying(project, output_dir)
    print(f"\n✅ 剪映草稿已导出: {draft_path}")


if __name__ == '__main__':
    demo_commentary()
