"""
AI 第一人称独白制作器 (Monologue Maker)

功能：原视频 + AI 独白配音 + 沉浸式字幕

工作流程:
    1. 分析原视频内容
    2. 生成第一人称独白文案
    3. 生成情感化 AI 配音
    4. 生成电影级字幕
    5. 合成视频或导出剪映草稿

使用示例:
    from app.services.video import MonologueMaker, MonologueProject
    
    maker = MonologueMaker()
    project = maker.create_project(
        source_video="input.mp4",
        context="深夜独自走在街头，回忆涌上心头",
        emotion="惆怅",
    )
    
    # 导出到剪映
    draft_path = maker.export_to_jianying(project, "/path/to/drafts")
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from ..ai.scene_analyzer import SceneAnalyzer, SceneInfo
from ..ai.script_generator import ScriptGenerator, ScriptConfig, ScriptStyle, GeneratedScript, VoiceTone
from ..ai.voice_generator import VoiceGenerator, VoiceConfig, VoiceStyle, GeneratedVoice
from ..viral_video.caption_generator import CaptionGenerator, CaptionStyle
from ..export.jianying_exporter import (
    JianyingExporter, JianyingDraft, JianyingConfig,
    Track, TrackType, Segment, TimeRange,
    VideoMaterial, AudioMaterial, TextMaterial,
)


class MonologueStyle(Enum):
    """独白风格"""
    MELANCHOLIC = "melancholic"    # 惆怅/忧郁
    INSPIRATIONAL = "inspirational"  # 励志/向上
    ROMANTIC = "romantic"          # 浪漫/温馨
    MYSTERIOUS = "mysterious"      # 神秘/悬疑
    NOSTALGIC = "nostalgic"        # 怀旧/追忆
    PHILOSOPHICAL = "philosophical"  # 哲思/沉思
    HEALING = "healing"            # 治愈/温暖


class EmotionType(Enum):
    """情感类型"""
    NEUTRAL = "neutral"
    SAD = "sad"
    HAPPY = "happy"
    ANGRY = "angry"
    CALM = "calm"
    EXCITED = "excited"
    TENDER = "tender"


@dataclass
class MonologueSegment:
    """独白片段"""
    script: str                    # 独白文案
    emotion: EmotionType           # 情感
    
    # 视频片段
    video_start: float
    video_end: float
    
    # 音频
    audio_path: str = ""
    audio_duration: float = 0.0
    
    # 字幕
    captions: List[Dict] = field(default_factory=list)


@dataclass
class MonologueProject:
    """独白视频项目"""
    id: str = ""
    name: str = "新建独白项目"
    
    # 源视频
    source_video: str = ""
    video_duration: float = 0.0
    
    # 独白内容
    context: str = ""              # 场景/情境描述
    emotion: str = ""              # 情感基调
    full_script: str = ""          # 完整独白
    segments: List[MonologueSegment] = field(default_factory=list)
    
    # 场景分析
    scenes: List[SceneInfo] = field(default_factory=list)
    
    # 配置
    style: MonologueStyle = MonologueStyle.MELANCHOLIC
    voice_config: VoiceConfig = field(default_factory=VoiceConfig)
    caption_style: str = "cinematic"  # cinematic, minimal, expressive
    
    # 输出
    output_dir: str = ""
    
    @property
    def total_duration(self) -> float:
        """总时长"""
        return sum(seg.audio_duration for seg in self.segments)


class MonologueMaker:
    """
    AI 第一人称独白制作器
    
    将原视频转换为带有沉浸式独白的视频
    
    使用示例:
        maker = MonologueMaker()
        
        # 创建项目
        project = maker.create_project(
            source_video="night_walk.mp4",
            context="深夜独自走在雨后的街道上",
            emotion="惆怅",
            style=MonologueStyle.MELANCHOLIC,
        )
        
        # 生成独白
        maker.generate_script(project)
        
        # 生成配音
        maker.generate_voice(project)
        
        # 生成字幕
        maker.generate_captions(project)
        
        # 导出到剪映
        draft_path = maker.export_to_jianying(project, "/path/to/drafts")
    """
    
    # 风格对应的配置
    STYLE_CONFIG = {
        MonologueStyle.MELANCHOLIC: {
            "tone": VoiceTone.CALM,
            "voice_style": VoiceStyle.NARRATION,
            "rate": 0.9,
            "prompt_hint": "忧郁、沉思、内心独白",
        },
        MonologueStyle.INSPIRATIONAL: {
            "tone": VoiceTone.EXCITED,
            "voice_style": VoiceStyle.NARRATION,
            "rate": 1.0,
            "prompt_hint": "励志、向上、充满力量",
        },
        MonologueStyle.ROMANTIC: {
            "tone": VoiceTone.EMOTIONAL,
            "voice_style": VoiceStyle.CONVERSATIONAL,
            "rate": 0.95,
            "prompt_hint": "温柔、浪漫、深情",
        },
        MonologueStyle.MYSTERIOUS: {
            "tone": VoiceTone.MYSTERIOUS,
            "voice_style": VoiceStyle.WHISPERING,
            "rate": 0.85,
            "prompt_hint": "神秘、悬疑、低沉",
        },
        MonologueStyle.NOSTALGIC: {
            "tone": VoiceTone.CALM,
            "voice_style": VoiceStyle.NARRATION,
            "rate": 0.9,
            "prompt_hint": "怀旧、追忆、温暖",
        },
        MonologueStyle.PHILOSOPHICAL: {
            "tone": VoiceTone.CALM,
            "voice_style": VoiceStyle.NARRATION,
            "rate": 0.88,
            "prompt_hint": "深邃、哲思、引人深思",
        },
        MonologueStyle.HEALING: {
            "tone": VoiceTone.CALM,
            "voice_style": VoiceStyle.CONVERSATIONAL,
            "rate": 0.92,
            "prompt_hint": "治愈、温暖、安慰",
        },
    }
    
    # 电影级字幕样式
    CAPTION_STYLES = {
        "cinematic": {
            "font_size": 6.0,
            "font_color": "#FFFFFF",
            "position": "bottom",
            "shadow": True,
            "animation": "fade",
        },
        "minimal": {
            "font_size": 5.0,
            "font_color": "#E0E0E0",
            "position": "bottom",
            "shadow": False,
            "animation": "none",
        },
        "expressive": {
            "font_size": 7.0,
            "font_color": "#FFFFFF",
            "position": "center",
            "shadow": True,
            "animation": "typewriter",
        },
    }
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        voice_provider: str = "edge",
    ):
        """
        初始化制作器
        
        Args:
            openai_api_key: OpenAI API Key
            voice_provider: 配音提供者
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.voice_provider = voice_provider
        
        self.scene_analyzer = SceneAnalyzer()
        self.voice_generator = VoiceGenerator(provider=voice_provider)
        self.caption_generator = CaptionGenerator()
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
        source_video: str,
        context: str,
        emotion: str = "neutral",
        name: Optional[str] = None,
        style: MonologueStyle = MonologueStyle.MELANCHOLIC,
        output_dir: Optional[str] = None,
    ) -> MonologueProject:
        """
        创建独白项目
        
        Args:
            source_video: 源视频路径
            context: 场景/情境描述
            emotion: 情感基调
            name: 项目名称
            style: 独白风格
            output_dir: 输出目录
        """
        import uuid
        
        source_path = Path(source_video)
        if not source_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {source_video}")
        
        project = MonologueProject(
            id=str(uuid.uuid4())[:8],
            name=name or source_path.stem,
            source_video=str(source_path.absolute()),
            context=context,
            emotion=emotion,
            style=style,
            output_dir=output_dir or str(source_path.parent / "output"),
        )
        
        # 分析视频场景
        self._report_progress("分析视频", 0.0)
        project.scenes = self.scene_analyzer.analyze(source_video)
        project.video_duration = sum(s.duration for s in project.scenes) if project.scenes else 0
        self._report_progress("分析视频", 1.0)
        
        return project
    
    def generate_script(
        self,
        project: MonologueProject,
        custom_script: Optional[str] = None,
    ) -> None:
        """
        生成独白文案
        
        Args:
            project: 项目对象
            custom_script: 自定义文案
        """
        self._report_progress("生成独白", 0.0)
        
        if custom_script:
            project.full_script = custom_script
        else:
            if not self.openai_api_key:
                raise ValueError("生成独白需要 OpenAI API Key")
            
            script_generator = ScriptGenerator(api_key=self.openai_api_key)
            
            # 获取风格配置
            style_cfg = self.STYLE_CONFIG.get(
                project.style,
                self.STYLE_CONFIG[MonologueStyle.MELANCHOLIC]
            )
            
            config = ScriptConfig(
                style=ScriptStyle.MONOLOGUE,
                tone=style_cfg["tone"],
                target_duration=project.video_duration,
            )
            
            # 构建主题
            topic = f"""
场景: {project.context}
情感: {project.emotion}
风格: {style_cfg["prompt_hint"]}

请用第一人称视角写一段独白，要求：
1. 像是在对观众倾诉内心
2. 有画面感，能配合视频画面
3. 语言优美但不矫情
4. 符合{project.emotion}的情感基调
"""
            
            result = script_generator.generate(topic, config)
            project.full_script = result.content
        
        # 分段
        self._segment_script(project)
        
        self._report_progress("生成独白", 1.0)
    
    def _segment_script(self, project: MonologueProject) -> None:
        """将独白分段"""
        paragraphs = [p.strip() for p in project.full_script.split('\n\n') if p.strip()]
        
        if not paragraphs:
            paragraphs = [project.full_script]
        
        # 匹配场景
        scenes = project.scenes if project.scenes else [None]
        
        project.segments = []
        for i, para in enumerate(paragraphs):
            scene = scenes[i % len(scenes)] if scenes[0] else None
            
            # 根据内容推断情感
            emotion = self._infer_emotion(para, project.emotion)
            
            segment = MonologueSegment(
                script=para,
                emotion=emotion,
                video_start=scene.start if scene else 0,
                video_end=scene.end if scene else project.video_duration / len(paragraphs),
            )
            project.segments.append(segment)
    
    def _infer_emotion(self, text: str, base_emotion: str) -> EmotionType:
        """根据文本内容推断情感"""
        # 简单关键词匹配
        emotion_keywords = {
            EmotionType.SAD: ["悲", "泪", "哭", "失去", "离别", "孤独", "寂寞"],
            EmotionType.HAPPY: ["开心", "快乐", "笑", "幸福", "美好", "温暖"],
            EmotionType.CALM: ["平静", "安宁", "静", "默", "沉思"],
            EmotionType.TENDER: ["温柔", "爱", "思念", "想", "心"],
            EmotionType.EXCITED: ["激动", "兴奋", "期待", "梦想", "未来"],
        }
        
        # 检查关键词
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return emotion
        
        # 使用基础情感
        emotion_map = {
            "惆怅": EmotionType.SAD,
            "忧郁": EmotionType.SAD,
            "开心": EmotionType.HAPPY,
            "平静": EmotionType.CALM,
            "温柔": EmotionType.TENDER,
            "excited": EmotionType.EXCITED,
        }
        
        return emotion_map.get(base_emotion, EmotionType.NEUTRAL)
    
    def generate_voice(
        self,
        project: MonologueProject,
        voice_config: Optional[VoiceConfig] = None,
    ) -> None:
        """
        生成 AI 配音
        
        Args:
            project: 项目对象
            voice_config: 配音配置
        """
        # 获取风格配置
        style_cfg = self.STYLE_CONFIG.get(
            project.style,
            self.STYLE_CONFIG[MonologueStyle.MELANCHOLIC]
        )
        
        if voice_config:
            project.voice_config = voice_config
        else:
            project.voice_config = VoiceConfig(
                style=style_cfg["voice_style"],
                rate=style_cfg["rate"],
            )
        
        output_dir = Path(project.output_dir) / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        total = len(project.segments)
        
        for i, segment in enumerate(project.segments):
            self._report_progress("生成配音", i / total)
            
            audio_path = output_dir / f"monologue_{i:03d}.mp3"
            
            # 根据情感调整配音
            config = VoiceConfig(
                voice_id=project.voice_config.voice_id,
                rate=project.voice_config.rate,
            )
            
            result = self.voice_generator.generate(
                text=segment.script,
                output_path=str(audio_path),
                config=config,
            )
            
            segment.audio_path = result.audio_path
            segment.audio_duration = result.duration
        
        self._report_progress("生成配音", 1.0)
    
    def generate_captions(
        self,
        project: MonologueProject,
        style: str = "cinematic",
    ) -> None:
        """
        生成电影级字幕
        
        Args:
            project: 项目对象
            style: 字幕风格 (cinematic, minimal, expressive)
        """
        self._report_progress("生成字幕", 0.0)
        
        project.caption_style = style
        caption_cfg = self.CAPTION_STYLES.get(style, self.CAPTION_STYLES["cinematic"])
        
        current_time = 0.0
        
        for i, segment in enumerate(project.segments):
            # 按句子分割
            import re
            sentences = re.split(r'([。！？，；])', segment.script)
            
            segment.captions = []
            segment_words = len(segment.script.replace(' ', ''))
            
            current_start = current_time
            current_text = ""
            
            for part in sentences:
                if not part:
                    continue
                
                if part in '。！？，；':
                    current_text += part
                    
                    if len(current_text) >= 3:
                        word_count = len(current_text)
                        duration = (word_count / max(segment_words, 1)) * segment.audio_duration
                        
                        segment.captions.append({
                            "text": current_text,
                            "start": current_start,
                            "duration": max(duration, 0.5),
                            "style": caption_cfg,
                            "emotion": segment.emotion.value,
                        })
                        
                        current_start += duration
                        current_text = ""
                else:
                    current_text += part
            
            # 处理剩余文本
            if current_text.strip():
                word_count = len(current_text)
                duration = (word_count / max(segment_words, 1)) * segment.audio_duration
                
                segment.captions.append({
                    "text": current_text,
                    "start": current_start,
                    "duration": max(duration, 0.5),
                    "style": caption_cfg,
                    "emotion": segment.emotion.value,
                })
            
            current_time += segment.audio_duration
            self._report_progress("生成字幕", (i + 1) / len(project.segments))
        
        self._report_progress("生成字幕", 1.0)
    
    def export_to_jianying(
        self,
        project: MonologueProject,
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
        
        # 1. 视频轨道
        video_track = Track(type=TrackType.VIDEO, attribute=1)
        draft.add_track(video_track)
        
        video_material = VideoMaterial(
            path=project.source_video,
            duration=int(project.video_duration * 1_000_000),
        )
        draft.add_video(video_material)
        
        # 添加视频片段（根据独白时长）
        current_time = 0.0
        for segment in project.segments:
            video_segment = Segment(
                material_id=video_material.id,
                source_timerange=TimeRange.from_seconds(
                    segment.video_start,
                    min(segment.audio_duration, segment.video_end - segment.video_start),
                ),
                target_timerange=TimeRange.from_seconds(
                    current_time,
                    segment.audio_duration,
                ),
            )
            video_track.add_segment(video_segment)
            current_time += segment.audio_duration
        
        # 2. 音频轨道（独白）
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
        
        caption_cfg = self.CAPTION_STYLES.get(
            project.caption_style,
            self.CAPTION_STYLES["cinematic"]
        )
        
        for segment in project.segments:
            for cap in segment.captions:
                text_material = TextMaterial(
                    content=cap["text"],
                    font_size=caption_cfg["font_size"],
                    font_color=caption_cfg["font_color"],
                    has_shadow=caption_cfg["shadow"],
                )
                draft.add_text(text_material)
                
                text_segment = Segment(
                    material_id=text_material.id,
                    source_timerange=TimeRange.from_seconds(0, cap["duration"]),
                    target_timerange=TimeRange.from_seconds(cap["start"], cap["duration"]),
                )
                text_track.add_segment(text_segment)
        
        # 导出
        draft_path = exporter.export(draft, jianying_drafts_dir)
        
        self._report_progress("导出剪映", 1.0)
        
        return draft_path


# =========== 便捷函数 ===========

def create_monologue(
    source_video: str,
    context: str,
    emotion: str,
    output_jianying_dir: str,
    style: MonologueStyle = MonologueStyle.MELANCHOLIC,
) -> str:
    """
    一键创建独白视频
    
    Args:
        source_video: 源视频
        context: 场景描述
        emotion: 情感
        output_jianying_dir: 剪映草稿目录
        style: 独白风格
        
    Returns:
        剪映草稿路径
    """
    maker = MonologueMaker()
    
    project = maker.create_project(
        source_video=source_video,
        context=context,
        emotion=emotion,
        style=style,
    )
    
    maker.generate_script(project)
    maker.generate_voice(project)
    maker.generate_captions(project)
    
    return maker.export_to_jianying(project, output_jianying_dir)


def demo_monologue():
    """演示独白视频制作"""
    print("=" * 50)
    print("AI 第一人称独白制作演示")
    print("=" * 50)
    
    maker = MonologueMaker(voice_provider="edge")
    
    test_video = "test_video.mp4"
    
    if not Path(test_video).exists():
        print(f"测试视频不存在: {test_video}")
        print("请准备测试视频后再运行")
        return
    
    # 创建项目
    project = maker.create_project(
        source_video=test_video,
        context="深夜独自走在下过雨的街道上，霓虹灯倒映在积水中",
        emotion="惆怅",
        style=MonologueStyle.MELANCHOLIC,
    )
    
    print(f"\n项目创建成功: {project.name}")
    print(f"视频时长: {project.video_duration:.2f}秒")
    
    # 自定义独白
    custom_script = """
    有些路，只能一个人走。
    
    夜深了，霓虹灯还在闪烁，
    我的影子被拉得很长很长。
    
    这座城市从不缺少热闹，
    只是热闹从来都不属于我。
    
    但我知道，
    总有一盏灯，会为我而亮。
    """
    
    maker.generate_script(project, custom_script=custom_script)
    print(f"\n独白已生成，共 {len(project.segments)} 个片段")
    
    maker.generate_voice(project)
    print(f"配音已生成，总时长: {project.total_duration:.2f}秒")
    
    maker.generate_captions(project, style="cinematic")
    print("字幕已生成 (电影级风格)")
    
    # 导出
    output_dir = "./output/jianying_drafts"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    draft_path = maker.export_to_jianying(project, output_dir)
    print(f"\n✅ 剪映草稿已导出: {draft_path}")


if __name__ == '__main__':
    demo_monologue()
