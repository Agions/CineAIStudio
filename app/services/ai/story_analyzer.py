"""
剧情分析器 (Story Analyzer)

AI 分析视频的剧情结构、叙事流程、场景转换和情感曲线，
为智能剪辑提供基于故事的剪辑点建议。

功能:
- 分析视频叙事结构（起承转合）
- 识别场景类型和转换点
- 分析情感曲线
- 生成基于剧情的剪辑建议
- 提取高光时刻

使用示例:
    from app.services.ai import StoryAnalyzer
    
    analyzer = StoryAnalyzer(
        llm_manager=llm_manager,
        vision_provider=vision_provider
    )
    
    # 分析剧情
    result = analyzer.analyze("video.mp4")
    
    logger.info(f"故事类型: {result.plot_type}")
    for segment in result.segments:
        logger.info(f"场景 {segment.order}: {segment.title}")
    
    # 获取剪辑建议
    cuts = analyzer.get_cut_recommendations(result, target_duration=60)
"""

import os
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class PlotType(Enum):
    """剧情类型"""
    LINEAR = ("linear", "线性叙事", "故事按时间顺序发展，没有倒叙或插叙")
    NONLINEAR = ("nonlinear", "非线性叙事", "故事采用倒叙、插叙或多时间线叙事")
    EPISODIC = ("episodic", "单元剧", "由多个相对独立的故事单元组成")
    MONTAGE = ("montage", "蒙太奇式", "通过快速剪辑的画面组合表达主题")
    QUEST = ("quest", "冒险/追求", "主角追求某个目标的故事")
    LOVE = ("love", "爱情", "以爱情为核心主题的故事")
    CONFLICT = ("conflict", "冲突对抗", "以冲突和对抗为核心的故事")
    GROWTH = ("growth", "成长", "以主角成长为核心的故事")
    MYSTERY = ("mystery", "悬疑", "以悬疑和推理为核心的故事")
    COMEDY = ("comedy", "喜剧", "以喜剧元素为核心的故事")
    ACTION = ("action", "动作", "以动作场面为核心的故事")
    DOCUMENTARY = ("documentary", "纪录片", "真实记录类内容")
    UNKNOWN = ("unknown", "未知", "无法确定剧情类型")

    def __init__(self, value: str, display_name: str, description: str = ""):
        self._value_ = value
        self.display_name = display_name
        self.description = description

    @property
    def value(self) -> str:
        return self._value_


class SceneType(Enum):
    """场景类型"""
    OPENING = ("opening", "开场", "故事开场，设置基调")
    INTRODUCTION = ("introduction", "介绍", "介绍背景和人物")
    RISING_ACTION = ("rising_action", "发展", "故事推进，矛盾升级")
    CLIMAX = ("climax", "高潮", "故事最精彩、最紧张的时刻")
    FALLING_ACTION = ("falling_action", "回落", "高潮后的缓和")
    CONCLUSION = ("conclusion", "结局", "故事收尾")
    TRANSITION = ("transition", "转场", "场景转换")
    MONTAGE = ("montage", "蒙太奇", "快速剪辑组合")
    FLASHBACK = ("flashback", "闪回", "回忆过去")
    HIGHLIGHT = ("highlight", "高光", "精彩片段")

    def __init__(self, value: str, display_name: str, description: str = ""):
        self._value_ = value
        self.display_name = display_name
        self.description = description

    @property
    def value(self) -> str:
        return self._value_


@dataclass
class EmotionalPoint:
    """情感节点"""
    timestamp: float
    emotion: str
    intensity: float  # 0-1
    description: str


@dataclass
class SceneSegment:
    """场景片段"""
    order: int
    title: str
    scene_type: SceneType
    start_time: float
    end_time: float
    duration: float
    description: str
    key_moments: List[str] = field(default_factory=list)
    cut_suggestion: str = ""
    relevance_score: float = 1.0  # 0-1，与主线相关性

    def __post_init__(self):
        if self.duration == 0:
            self.duration = self.end_time - self.start_time


@dataclass
class StoryArc:
    """故事弧线"""
    name: str
    description: str
    start_time: float
    end_time: float
    peak_time: Optional[float] = None
    emotional_tone: str = "neutral"


@dataclass
class StoryAnalysisResult:
    """剧情分析结果"""
    video_path: str
    duration: float
    plot_type: PlotType

    # 叙事结构
    segments: List[SceneSegment] = field(default_factory=list)
    story_arcs: List[StoryArc] = field(default_factory=list)
    opening: Optional[SceneSegment] = None
    climax: Optional[SceneSegment] = None
    conclusion: Optional[SceneSegment] = None

    # 情感分析
    emotional_curve: List[EmotionalPoint] = field(default_factory=list)

    # 剪辑建议
    recommended_cuts: List[Dict[str, Any]] = field(default_factory=list)
    highlight_moments: List[Dict[str, Any]] = field(default_factory=list)

    # 故事质量
    coherence_score: float = 0.0  # 0-1
    pacing_score: float = 0.0  # 0-1
    engagement_score: float = 0.0  # 0-1

    # 元数据
    summary: str = ""
    themes: List[str] = field(default_factory=list)
    characters: List[str] = field(default_factory=list)
    settings: List[str] = field(default_factory=list)

    analyzed_at: datetime = field(default_factory=datetime.now)


class StoryAnalyzer:
    """剧情分析器"""

    # 帧提取间隔（秒）
    DEFAULT_FRAME_INTERVAL = 5.0
    # 每批次处理的帧数
    FRAMES_PER_BATCH = 10

    def __init__(
        self,
        llm_manager=None,
        vision_provider=None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化剧情分析器

        Args:
            llm_manager: LLM 管理器实例
            vision_provider: 视觉理解提供者
            config: 配置字典
        """
        self.llm = llm_manager
        self.vision = vision_provider
        self.config = config or {}
        self.frame_interval = self.config.get("frame_interval", self.DEFAULT_FRAME_INTERVAL)
        self.language = self.config.get("language", "zh")

        logger.info(f"StoryAnalyzer initialized (language={self.language})")

    def analyze(
        self,
        video_path: str,
        extract_frames: bool = True,
        frame_interval: Optional[float] = None
    ) -> StoryAnalysisResult:
        """
        分析视频剧情

        Args:
            video_path: 视频文件路径
            extract_frames: 是否提取帧进行分析
            frame_interval: 帧提取间隔（秒）

        Returns:
            StoryAnalysisResult: 剧情分析结果
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        video_path = Path(video_path)
        logger.info(f"Analyzing story for: {video_path}")

        # 获取视频信息
        duration = self._get_video_duration(str(video_path))
        if duration <= 0:
            raise ValueError(f"Invalid video duration: {duration}")

        # 提取帧用于分析
        frames_info = []
        if extract_frames:
            frames_info = self._extract_frames(str(video_path), frame_interval or self.frame_interval)

        # 使用 AI 分析剧情
        result = self._analyze_with_ai(str(video_path), duration, frames_info)

        logger.info(f"Story analysis complete: plot_type={result.plot_type.value}, "
                   f"segments={len(result.segments)}")
        return result

    def _get_video_duration(self, video_path: str) -> float:
        """获取视频时长"""
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'csv=p=0',
            video_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except Exception as e:
            logger.warning(f"Failed to get video duration: {e}")

        return 0.0

    def _extract_frames(
        self,
        video_path: str,
        interval: float
    ) -> List[Dict[str, Any]]:
        """
        提取视频帧用于分析

        Args:
            video_path: 视频路径
            interval: 提取间隔（秒）

        Returns:
            帧信息列表 [{timestamp, image_path}, ...]
        """
        frames = []
        temp_dir = Path.home() / ".videoforge" / "temp" / "story_frames"
        temp_dir.mkdir(parents=True, exist_ok=True)

        duration = self._get_video_duration(video_path)
        if duration <= 0:
            return frames

        # 计算需要提取的时间点
        timestamps = []
        current_time = 0.0
        while current_time < duration:
            timestamps.append(current_time)
            current_time += interval

        logger.info(f"Extracting {len(timestamps)} frames from {video_path}")

        for i, ts in enumerate(timestamps):
            output_path = temp_dir / f"frame_{i:04d}_{int(ts)}.jpg"

            cmd = [
                'ffmpeg', '-y', '-ss', str(ts),
                '-i', video_path,
                '-vframes', '1',
                '-q:v', '2',
                '-s', '640x360',  # 降低分辨率以提高速度
                str(output_path)
            ]

            try:
                subprocess.run(cmd, capture_output=True, timeout=10)
                if output_path.exists():
                    frames.append({
                        "timestamp": ts,
                        "image_path": str(output_path),
                        "index": i
                    })
            except Exception as e:
                logger.warning(f"Failed to extract frame at {ts}s: {e}")

        return frames

    def _analyze_with_ai(
        self,
        video_path: str,
        duration: float,
        frames_info: List[Dict[str, Any]]
    ) -> StoryAnalysisResult:
        """
        使用 AI 分析剧情

        Args:
            video_path: 视频路径
            duration: 视频时长
            frames_info: 提取的帧信息

        Returns:
            剧情分析结果
        """
        # 如果没有 LLM 管理器，返回基础分析结果
        if not self.llm:
            logger.warning("No LLM manager available, returning basic result")
            return self._create_basic_result(video_path, duration)

        # 构建分析提示词
        prompt = self._build_analysis_prompt(video_path, duration, frames_info)

        try:
            # 调用 LLM 分析
            response = self.llm.generate(
                prompt=prompt,
                system_prompt=self._get_system_prompt()
            )

            # 解析 LLM 响应
            result = self._parse_llm_response(video_path, duration, response, frames_info)
            return result

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return self._create_basic_result(video_path, duration)

    def _build_analysis_prompt(
        self,
        video_path: str,
        duration: float,
        frames_info: List[Dict[str, Any]]
    ) -> str:
        """构建分析提示词"""
        duration_min = int(duration // 60)
        duration_sec = int(duration % 60)

        # 帧描述（如果有视觉能力）
        frame_descriptions = []
        if self.vision and frames_info:
            for frame in frames_info[:20]:  # 限制分析帧数
                frame_descriptions.append(
                    f"- 第 {frame['index']} 帧 ({int(frame['timestamp'])}秒): {frame['image_path']}"
                )
        elif frames_info:
            for frame in frames_info[:20]:
                frame_descriptions.append(
                    f"- 时刻 {int(frame['timestamp'])}秒 (帧 {frame['index']})"
                )

        frames_text = "\n".join(frame_descriptions) if frame_descriptions else "无可用帧"

        prompt = f"""分析以下视频的剧情结构：

视频信息：
- 文件: {Path(video_path).name}
- 时长: {duration_min}分{duration_sec}秒
- 已提取的帧（共{len(frames_info)}帧）:
{frames_text}

请分析并返回 JSON 格式的结果，包含以下字段：
{{
    "plot_type": "linear/nonlinear/episodic/montage/quest/love/conflict/growth/mystery/comedy/action/documentary",
    "summary": "故事概要（100字内）",
    "themes": ["主题1", "主题2"],
    "segments": [
        {{
            "order": 1,
            "title": "场景标题",
            "scene_type": "opening/introduction/rising_action/climax/falling_action/conclusion",
            "start_time": 0.0,
            "end_time": 30.0,
            "description": "场景描述",
            "key_moments": ["关键时刻1", "关键时刻2"],
            "relevance_score": 0.9
        }}
    ],
    "emotional_curve": [
        {{"timestamp": 5.0, "emotion": "平静", "intensity": 0.3, "description": "..."}}
    ],
    "highlight_moments": [
        {{"timestamp": 45.0, "description": "精彩时刻描述"}}
    ],
    "coherence_score": 0.8,
    "pacing_score": 0.7,
    "engagement_score": 0.85
}}

只返回 JSON，不要其他内容。"""

        return prompt

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        if self.language == "en":
            return """You are a professional film analyst. Analyze video story structure, narrative, and emotional arc. Return valid JSON only."""
        else:
            return """你是一位专业的影视编剧和叙事分析师。分析视频的剧情结构、叙事流程和情感曲线。只返回 JSON 格式的结果。"""

    def _parse_llm_response(
        self,
        video_path: str,
        duration: float,
        response: str,
        frames_info: List[Dict[str, Any]]
    ) -> StoryAnalysisResult:
        """解析 LLM 响应"""
        try:
            # 尝试提取 JSON
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())

            # 构建结果
            plot_type = PlotType.UNKNOWN
            for pt in PlotType:
                if pt.value == data.get("plot_type"):
                    plot_type = pt
                    break

            # 转换场景片段
            segments = []
            for seg_data in data.get("segments", []):
                scene_type = SceneType.UNKNOWN
                for st in SceneType:
                    if st.value == seg_data.get("scene_type"):
                        scene_type = st
                        break

                segment = SceneSegment(
                    order=seg_data.get("order", 0),
                    title=seg_data.get("title", ""),
                    scene_type=scene_type,
                    start_time=seg_data.get("start_time", 0.0),
                    end_time=seg_data.get("end_time", 0.0),
                    duration=seg_data.get("end_time", 0.0) - seg_data.get("start_time", 0.0),
                    description=seg_data.get("description", ""),
                    key_moments=seg_data.get("key_moments", []),
                    relevance_score=seg_data.get("relevance_score", 1.0)
                )
                segments.append(segment)

            # 转换情感曲线
            emotional_curve = []
            for ep in data.get("emotional_curve", []):
                emotional_curve.append(EmotionalPoint(
                    timestamp=ep.get("timestamp", 0.0),
                    emotion=ep.get("emotion", ""),
                    intensity=ep.get("intensity", 0.0),
                    description=ep.get("description", "")
                ))

            # 转换高光时刻
            highlight_moments = data.get("highlight_moments", [])

            # 找出开场、高潮、结局
            opening = None
            climax = None
            conclusion = None

            for seg in segments:
                if seg.scene_type == SceneType.OPENING:
                    opening = seg
                elif seg.scene_type == SceneType.CLIMAX:
                    climax = seg
                elif seg.scene_type == SceneType.CONCLUSION:
                    conclusion = seg

            result = StoryAnalysisResult(
                video_path=video_path,
                duration=duration,
                plot_type=plot_type,
                segments=segments,
                story_arcs=[],
                opening=opening,
                climax=climax,
                conclusion=conclusion,
                emotional_curve=emotional_curve,
                highlight_moments=highlight_moments,
                coherence_score=data.get("coherence_score", 0.0),
                pacing_score=data.get("pacing_score", 0.0),
                engagement_score=data.get("engagement_score", 0.0),
                summary=data.get("summary", ""),
                themes=data.get("themes", []),
                characters=data.get("characters", []),
                settings=data.get("settings", [])
            )

            return result

        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return self._create_basic_result(video_path, duration)

    def _create_basic_result(self, video_path: str, duration: float) -> StoryAnalysisResult:
        """创建基础结果（当 AI 分析不可用时）"""
        return StoryAnalysisResult(
            video_path=video_path,
            duration=duration,
            plot_type=PlotType.UNKNOWN,
            segments=[],
            story_arcs=[],
            summary="剧情分析功能需要配置 AI 服务"
        )

    def get_cut_recommendations(
        self,
        result: StoryAnalysisResult,
        target_duration: Optional[float] = None,
        style: str = "narrative",
        template_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        根据剧情分析获取剪辑建议

        Args:
            result: 剧情分析结果
            target_duration: 目标时长（秒），None 表示保持原长
            style: 剪辑风格 ("narrative", "highlight", "trailer")
            template_id: 剪辑模板 ID（可选）

        Returns:
            剪辑点列表
        """
        # 如果指定了模板，使用模板管理器
        if template_id:
            return self._apply_template(template_id, result, target_duration)

        # 否则使用内置风格
        if style == "narrative":
            return self._get_narrative_cuts(result, target_duration)
        elif style == "highlight":
            return self._get_highlight_cuts(result, target_duration)
        elif style == "trailer":
            return self._get_trailer_cuts(result, target_duration)
        else:
            return self._get_narrative_cuts(result, target_duration)

    def _apply_template(
        self,
        template_id: str,
        result: StoryAnalysisResult,
        target_duration: Optional[float]
    ) -> List[Dict[str, Any]]:
        """应用模板生成剪辑点"""
        try:
            from .cut_template import CutTemplateManager

            manager = CutTemplateManager()
            template = manager.get_template_by_id(template_id)

            if template:
                return manager.apply_template(template, result)
            else:
                logger.warning(f"Template not found: {template_id}, using narrative style")
                return self._get_narrative_cuts(result, target_duration)

        except Exception as e:
            logger.error(f"Failed to apply template {template_id}: {e}")
            return self._get_narrative_cuts(result, target_duration)

    def _get_narrative_cuts(
        self,
        result: StoryAnalysisResult,
        target_duration: Optional[float]
    ) -> List[Dict[str, Any]]:
        """生成叙事性剪辑建议 - 保留故事完整性"""
        cuts = []

        # 如果没有分段，按时间均匀分割
        if not result.segments:
            return self._generate_uniform_cuts(result, target_duration)

        for segment in result.segments:
            cuts.append({
                "type": "keep",
                "start": segment.start_time,
                "end": segment.end_time,
                "duration": segment.duration,
                "title": segment.title,
                "reason": f"保留{segment.scene_type.display_name}：{segment.title}",
                "scene_type": segment.scene_type.value,
                "relevance_score": segment.relevance_score
            })

        # 如果需要缩短，裁剪低相关性片段
        if target_duration:
            cuts = self._adjust_cuts_to_duration(cuts, target_duration)

        return cuts

    def _get_highlight_cuts(
        self,
        result: StoryAnalysisResult,
        target_duration: Optional[float]
    ) -> List[Dict[str, Any]]:
        """生成高光剪辑建议 - 只保留精彩片段"""
        cuts = []

        # 先添加高光时刻
        for highlight in result.highlight_moments:
            cuts.append({
                "type": "keep",
                "start": highlight.get("timestamp", 0),
                "end": highlight.get("timestamp", 0) + 5,
                "duration": 5,
                "title": "高光时刻",
                "reason": f"高光：{highlight.get('description', '')}",
                "scene_type": "highlight",
                "relevance_score": 1.0
            })

        # 添加高潮场景
        if result.climax:
            cuts.append({
                "type": "keep",
                "start": result.climax.start_time,
                "end": result.climax.end_time,
                "duration": result.climax.duration,
                "title": result.climax.title,
                "reason": f"高潮场景：{result.climax.title}",
                "scene_type": "climax",
                "relevance_score": 1.0
            })

        # 按时间排序
        cuts.sort(key=lambda x: x["start"])

        # 合并重叠的片段
        cuts = self._merge_overlapping_cuts(cuts)

        # 如果需要缩短，继续裁剪
        if target_duration:
            cuts = self._adjust_cuts_to_duration(cuts, target_duration)

        return cuts

    def _get_trailer_cuts(
        self,
        result: StoryAnalysisResult,
        target_duration: Optional[float]
    ) -> List[Dict[str, Any]]:
        """生成预告片风格剪辑建议 - 制造悬念和期待"""
        cuts = []
        max_clips = 12  # 预告片通常 12-15 个镜头

        # 开场（吸引注意）
        if result.opening:
            duration = min(5, result.opening.duration)
            cuts.append({
                "type": "keep",
                "start": result.opening.start_time,
                "end": result.opening.start_time + duration,
                "duration": duration,
                "title": "开场",
                "reason": "开场吸引注意",
                "scene_type": "opening",
                "relevance_score": 1.0
            })

        # 高潮片段
        if result.climax:
            duration = min(result.climax.duration, 10)
            cuts.append({
                "type": "keep",
                "start": result.climax.start_time,
                "end": result.climax.start_time + duration,
                "duration": duration,
                "title": result.climax.title,
                "reason": "高潮场景",
                "scene_type": "climax",
                "relevance_score": 1.0
            })

        # 发展阶段的关键时刻
        for segment in result.segments:
            if segment.scene_type == SceneType.RISING_ACTION and len(cuts) < max_clips:
                # 选择最相关的时刻
                if segment.key_moments and segment.relevance_score > 0.7:
                    cuts.append({
                        "type": "keep",
                        "start": segment.start_time,
                        "end": min(segment.start_time + 3, segment.end_time),
                        "duration": 3,
                        "title": segment.title,
                        "reason": f"关键时刻：{segment.key_moments[0]}",
                        "scene_type": "rising_action",
                        "relevance_score": segment.relevance_score
                    })

        # 按时间排序
        cuts.sort(key=lambda x: x["start"])

        # 如果需要缩短
        if target_duration:
            cuts = self._adjust_cuts_to_duration(cuts, target_duration)

        return cuts[:max_clips]

    def _generate_uniform_cuts(
        self,
        result: StoryAnalysisResult,
        target_duration: Optional[float]
    ) -> List[Dict[str, Any]]:
        """生成均匀分割的剪辑建议"""
        cuts = []
        clip_duration = 10  # 默认每个片段 10 秒
        current_time = 0.0

        while current_time < result.duration:
            end_time = min(current_time + clip_duration, result.duration)
            cuts.append({
                "type": "keep",
                "start": current_time,
                "end": end_time,
                "duration": end_time - current_time,
                "title": f"片段 {len(cuts) + 1}",
                "reason": "自动分割",
                "scene_type": "segment",
                "relevance_score": 1.0
            })
            current_time = end_time

        if target_duration:
            cuts = self._adjust_cuts_to_duration(cuts, target_duration)

        return cuts

    def _merge_overlapping_cuts(self, cuts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并重叠的剪辑片段"""
        if not cuts:
            return []

        merged = [cuts[0]]

        for cut in cuts[1:]:
            last = merged[-1]
            if cut["start"] <= last["end"]:
                # 重叠，合并
                last["end"] = max(last["end"], cut["end"])
                last["duration"] = last["end"] - last["start"]
            else:
                merged.append(cut)

        return merged

    def _adjust_cuts_to_duration(
        self,
        cuts: List[Dict[str, Any]],
        target_duration: float
    ) -> List[Dict[str, Any]]:
        """调整剪辑以达到目标时长"""
        current_duration = sum(c["duration"] for c in cuts)

        if current_duration <= target_duration:
            return cuts

        # 计算需要删除的比例
        ratio = target_duration / current_duration
        adjusted = []

        for cut in cuts:
            new_duration = cut["duration"] * ratio
            adjusted.append({
                **cut,
                "end": cut["start"] + new_duration,
                "duration": new_duration
            })

        return adjusted
