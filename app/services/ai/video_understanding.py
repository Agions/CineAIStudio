#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频级理解模块
从"逐帧分析"升级为"视频级叙事理解"

支持两种模式:
1. Gemini 视频直传（推荐，一次调用完成）
2. 多帧连续分析 + LLM 汇总（降级方案，兼容任意 Vision API）
"""

import os
import json
import base64
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class NarrativeStructure(Enum):
    """叙事结构"""
    THREE_ACT = "three_act"         # 三幕式
    LINEAR = "linear"               # 线性叙事
    CIRCULAR = "circular"           # 环形叙事
    PARALLEL = "parallel"           # 平行叙事
    MONTAGE = "montage"             # 蒙太奇
    UNKNOWN = "unknown"


@dataclass
class Character:
    """角色"""
    name: str = ""
    description: str = ""
    appearances: List[float] = field(default_factory=list)  # 出现的时间点
    role: str = ""  # 主角/配角/路人


@dataclass
class EmotionPoint:
    """情感节点"""
    timestamp: float
    emotion: str       # happy/sad/tense/calm/excited
    intensity: float   # 0-1
    description: str = ""


@dataclass
class Highlight:
    """高亮/亮点片段"""
    start: float
    end: float
    type: str          # climax/twist/funny/emotional/action
    description: str
    score: float = 0.0  # 0-100 精彩程度


@dataclass
class CutPoint:
    """AI 建议的剪辑点"""
    timestamp: float
    reason: str        # beat_match/scene_change/emotion_shift/silence
    confidence: float = 0.0


@dataclass
class VideoUnderstanding:
    """视频级理解结果"""
    video_path: str
    duration: float

    # 整体理解
    storyline: str = ""                                    # 故事线摘要
    narrative_structure: NarrativeStructure = NarrativeStructure.UNKNOWN
    theme: str = ""                                        # 主题
    tone: str = ""                                         # 基调

    # 角色
    characters: List[Character] = field(default_factory=list)

    # 情感弧线
    emotion_arc: List[EmotionPoint] = field(default_factory=list)

    # 亮点
    highlights: List[Highlight] = field(default_factory=list)

    # 剪辑建议
    suggested_cuts: List[CutPoint] = field(default_factory=list)

    # 关键词 & 标签
    keywords: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # 原始数据
    raw_analysis: str = ""


UNDERSTANDING_PROMPT = """你是专业的视频内容分析师。请深度分析这段视频，返回 JSON 格式：

{
    "storyline": "完整的故事线描述（200字以内）",
    "narrative_structure": "three_act/linear/circular/parallel/montage",
    "theme": "视频主题",
    "tone": "基调（如：温馨/紧张/搞笑/伤感/励志）",
    "characters": [
        {"name": "角色描述", "role": "主角/配角", "description": "特征"}
    ],
    "emotion_arc": [
        {"timestamp": 0.0, "emotion": "calm", "intensity": 0.3, "description": "开场"}
    ],
    "highlights": [
        {"start": 10.0, "end": 15.0, "type": "climax", "description": "描述", "score": 85}
    ],
    "suggested_cuts": [
        {"timestamp": 5.0, "reason": "scene_change", "confidence": 0.9}
    ],
    "keywords": ["关键词1", "关键词2"],
    "tags": ["标签1", "标签2"]
}

只返回 JSON，不要其他内容。"""


class VideoUnderstandingEngine:
    """
    视频级理解引擎

    使用策略:
    1. 优先使用 Gemini 直传视频（最佳效果）
    2. 降级到多帧 Vision API + LLM 汇总
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}
        self._gemini_key = os.getenv("GEMINI_API_KEY") or \
            self._config.get("LLM", {}).get("gemini", {}).get("api_key", "")
        self._openai_key = os.getenv("OPENAI_API_KEY") or \
            self._config.get("LLM", {}).get("openai", {}).get("api_key", "")

    def analyze(self, video_path: str,
                mode: str = "auto") -> VideoUnderstanding:
        """
        分析视频

        Args:
            video_path: 视频文件路径
            mode: "auto" / "gemini" / "multiframe"

        Returns:
            VideoUnderstanding 结果
        """
        video_path = str(Path(video_path).resolve())

        if mode == "auto":
            if self._gemini_key and not self._gemini_key.startswith("${"):
                mode = "gemini"
            elif self._openai_key:
                mode = "multiframe"
            else:
                raise RuntimeError("没有可用的 API Key，无法分析视频")

        if mode == "gemini":
            return self._analyze_with_gemini(video_path)
        else:
            return self._analyze_multiframe(video_path)

    def _analyze_with_gemini(self, video_path: str) -> VideoUnderstanding:
        """使用 Gemini 直传视频分析"""
        try:
            import google.generativeai as genai

            genai.configure(api_key=self._gemini_key)

            model = genai.GenerativeModel("gemini-2.0-flash")

            # 上传视频文件
            video_file = genai.upload_file(video_path)

            # 等待处理完成
            import time
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)

            if video_file.state.name == "FAILED":
                raise RuntimeError(f"Gemini 视频处理失败: {video_file.state.name}")

            # 分析
            response = model.generate_content(
                [video_file, UNDERSTANDING_PROMPT],
                generation_config=genai.GenerationConfig(
                    max_output_tokens=2000,
                    temperature=0.3,
                ),
            )

            # 清理上传的文件
            try:
                genai.delete_file(video_file.name)
            except Exception:
                pass

            return self._parse_response(video_path, response.text)

        except ImportError:
            raise ImportError("请安装 google-generativeai: pip install google-generativeai")

    def _analyze_multiframe(self, video_path: str) -> VideoUnderstanding:
        """多帧分析 + LLM 汇总"""
        from .video_content_analyzer import VideoContentAnalyzer, AnalyzerConfig

        # 密集提取关键帧
        analyzer = VideoContentAnalyzer(
            vision_api_key=self._openai_key,
            config=AnalyzerConfig(
                keyframe_interval=1.5,
                max_keyframes=40,
                use_vision_api=True,
                parallel_analysis=True,
            ),
        )

        result = analyzer.analyze(video_path)

        # 构建时序描述
        timeline = []
        for kf in result.keyframes:
            if kf.description:
                timeline.append(f"[{kf.timestamp:.1f}s] {kf.description}")

        if not timeline:
            return VideoUnderstanding(
                video_path=video_path,
                duration=result.duration,
                storyline="无法获取画面描述",
            )

        # 用 LLM 做叙事理解
        prompt = f"""基于以下视频画面时间线描述，进行深度叙事分析。

视频时长: {result.duration:.1f}秒
关键帧描述:
{chr(10).join(timeline)}

{UNDERSTANDING_PROMPT}"""

        from openai import OpenAI
        client = OpenAI(api_key=self._openai_key)
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3,
        )

        return self._parse_response(
            video_path, response.choices[0].message.content,
            duration=result.duration
        )

    def _parse_response(self, video_path: str, text: str,
                        duration: float = 0.0) -> VideoUnderstanding:
        """解析 LLM 响应为 VideoUnderstanding"""
        # 提取 JSON
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        try:
            data = json.loads(text.strip())
        except json.JSONDecodeError:
            return VideoUnderstanding(
                video_path=video_path,
                duration=duration,
                storyline=text.strip()[:500],
                raw_analysis=text,
            )

        # 构建结果
        result = VideoUnderstanding(
            video_path=video_path,
            duration=duration,
            storyline=data.get("storyline", ""),
            theme=data.get("theme", ""),
            tone=data.get("tone", ""),
            keywords=data.get("keywords", []),
            tags=data.get("tags", []),
            raw_analysis=text,
        )

        # 叙事结构
        ns = data.get("narrative_structure", "unknown")
        try:
            result.narrative_structure = NarrativeStructure(ns)
        except ValueError:
            result.narrative_structure = NarrativeStructure.UNKNOWN

        # 角色
        for c in data.get("characters", []):
            result.characters.append(Character(
                name=c.get("name", ""),
                description=c.get("description", ""),
                role=c.get("role", ""),
            ))

        # 情感弧线
        for e in data.get("emotion_arc", []):
            result.emotion_arc.append(EmotionPoint(
                timestamp=float(e.get("timestamp", 0)),
                emotion=e.get("emotion", "neutral"),
                intensity=float(e.get("intensity", 0.5)),
                description=e.get("description", ""),
            ))

        # 亮点
        for h in data.get("highlights", []):
            result.highlights.append(Highlight(
                start=float(h.get("start", 0)),
                end=float(h.get("end", 0)),
                type=h.get("type", ""),
                description=h.get("description", ""),
                score=float(h.get("score", 0)),
            ))

        # 剪辑建议
        for cp in data.get("suggested_cuts", []):
            result.suggested_cuts.append(CutPoint(
                timestamp=float(cp.get("timestamp", 0)),
                reason=cp.get("reason", ""),
                confidence=float(cp.get("confidence", 0)),
            ))

        return result
