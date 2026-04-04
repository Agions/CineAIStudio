"""
ClipScorer — 多维评分引擎
对每个候选片段打分，输出排序后的片段列表。

评分维度（6 个信号）：
  1. laughter_density    — 笑声/鼓掌密度
  2. emotion_peak       — 情感峰值（惊喜/愤怒/兴奋）
  3. speech_completeness — 对话完整性（是否被打断）
  4. silence_ratio      — 有声占比（过低=纯静音，过高=嘈杂）
  5. speaking_pace      — 语速健康度（太快/太慢都要扣分）
  6. keyword_boost      — 关键词命中（"必须"/"最重要"/"揭秘"等高 engagement 词）

评分范围：0-100，权重可配置。
CPU 运行，无外部 API 调用（基于本地 ASR 特征提取）。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


# ============================================================
# Data Types
# ============================================================

@dataclass
class ClipSegment:
    """候选片段（输入）"""
    start_time: float       # 秒
    end_time: float         # 秒
    scene_type: str = ""    # 场景类型标签
    audio_path: Optional[str] = None  # 音频文件路径（可选）
    transcript: str = ""   # 原始转录文本


@dataclass
class ClipScore:
    """片段评分结果（输出）"""
    segment: ClipSegment
    total_score: float      # 综合分 0-100

    laughter_density: float = 0.0
    emotion_peak: float = 0.0
    speech_completeness: float = 0.0
    silence_ratio: float = 0.0
    speaking_pace: float = 0.0
    keyword_boost: float = 0.0

    reasons: List[str] = field(default_factory=list)  # 可读原因描述

    @property
    def duration(self) -> float:
        return self.segment.end_time - self.segment.start_time


# ============================================================
# High-Engagement Keywords（需中英双语）
# ============================================================

HIGH_ENGAGEMENT_KEYWORDS = [
    # 中文
    "必须", "一定", "揭秘", "真相", "秘密", "关键", "重要",
    "竟然", "没想到", "令人震惊", "太惊讶了", "难以置信",
    "第一次", "终于", "终于明白", "后悔", "经验", "建议",
    "推荐", "必看", "干货", "技巧", "秘诀", "窍门",
    "搞笑", "笑死", "太逗了", "绝了", "炸裂", "爆笑",
    "感动", "泪目", "太励志", "热血", "燃", "热血沸腾",
    "冲突", "矛盾", "反转", "意外", "震惊", "崩溃",
    # English
    "must watch", "secret", "truth", "revealed", "honest",
    "first time", "finally", "regret", "lesson", "advice",
    "you won't believe", "shocking", "amazing", "incredible",
    "funny", "laughing", "hilarious", "omg", "wow",
    "emotional", "touching", "inspiring", "motivational",
    "twist", "plot twist", "surprising", "unexpected",
]


# ============================================================
# Main Scorer
# ============================================================

class ClipScorer:
    """
    多维评分引擎

    使用方式：
        scorer = ClipScorer()
        segments = [ClipSegment(start=0, end=30, ...), ...]
        scores = scorer.score_segments(segments)
        top_clips = sorted(scores, key=lambda s: s.total_score, reverse=True)[:5]
    """

    # 默认权重（可覆盖）
    DEFAULT_WEIGHTS = {
        "laughter_density": 0.20,
        "emotion_peak": 0.20,
        "speech_completeness": 0.20,
        "silence_ratio": 0.10,
        "speaking_pace": 0.10,
        "keyword_boost": 0.20,
    }

    def __init__(
        self,
        weights: Optional[dict] = None,
        min_clip_duration: float = 15.0,   # 秒，最短片段
        max_clip_duration: float = 120.0,  # 秒，最长片段
    ):
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.min_clip_duration = min_clip_duration
        self.max_clip_duration = max_clip_duration

        # 验证权重和为 1
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.001:
            # 自动归一化
            for k in self.weights:
                self.weights[k] /= total
            logger.warning(f"ClipScorer weights not sum to 1, normalized: {self.weights}")

    def score_segments(self, segments: List[ClipSegment]) -> List[ClipScore]:
        """
        对所有候选片段打分

        Args:
            segments: 候选片段列表

        Returns:
            按 total_score 降序排列的 ClipScore 列表
        """
        if not segments:
            return []

        results: List[ClipScore] = []
        for seg in segments:
            try:
                score = self._score_single(seg)
                results.append(score)
            except Exception as e:
                logger.warning(f"片段评分失败 [{seg.start_time:.1f}s]: {e}")
                # 失败时给最低分
                results.append(ClipScore(
                    segment=seg,
                    total_score=0.0,
                    reasons=[f"评分异常: {e}"],
                ))

        # 降序排列
        results.sort(key=lambda s: s.total_score, reverse=True)
        return results

    def _score_single(self, seg: ClipSegment) -> ClipScore:
        """对一个片段计算六个维度的分数"""
        duration = seg.end_time - seg.start_time
        transcript = seg.transcript or ""

        # --- Dimension 1: 笑声密度（假设有音频能量特征）---
        laughter_score = self._score_laughter(seg, transcript)

        # --- Dimension 2: 情感峰值 ---
        emotion_score = self._score_emotion(transcript)

        # --- Dimension 3: 对话完整性 ---
        completeness_score = self._score_completeness(seg, transcript)

        # --- Dimension 4: 有声占比 ---
        silence_score = self._score_silence_ratio(seg)

        # --- Dimension 5: 语速健康度 ---
        pace_score = self._score_pace(transcript, duration)

        # --- Dimension 6: 关键词命中 ---
        keyword_score = self._score_keywords(transcript)

        # --- 综合分数（加权）---
        total = sum([
            laughter_score * self.weights["laughter_density"],
            emotion_score * self.weights["emotion_peak"],
            completeness_score * self.weights["speech_completeness"],
            silence_score * self.weights["silence_ratio"],
            pace_score * self.weights["speaking_pace"],
            keyword_score * self.weights["keyword_boost"],
        ])

        # 时长惩罚：过短或过长都要扣分
        if duration < self.min_clip_duration:
            total *= 0.7
        elif duration > self.max_clip_duration:
            total *= 0.85

        # 生成原因描述
        reasons = self._build_reasons(
            laughter_score, emotion_score, completeness_score,
            silence_score, pace_score, keyword_score,
            transcript, duration,
        )

        return ClipScore(
            segment=seg,
            total_score=round(total, 2),
            laughter_density=round(laughter_score, 2),
            emotion_peak=round(emotion_score, 2),
            speech_completeness=round(completeness_score, 2),
            silence_ratio=round(silence_score, 2),
            speaking_pace=round(pace_score, 2),
            keyword_boost=round(keyword_score, 2),
            reasons=reasons,
        )

    # --------------------------------------------------------
    # Dimension Scorers
    # --------------------------------------------------------

    def _score_laughter(self, seg: ClipSegment, transcript: str) -> float:
        """笑声/掌声密度"""
        laughter_count = sum(
            transcript.lower().count(kw)
            for kw in ["笑", "哈哈", "laughter", "laughing", "haha", "lol", "掌声", "applause"]
        )
        duration = seg.end_time - seg.start_time
        density = laughter_count / max(duration / 60, 1)  # per minute
        # 0-100，基准：每分钟 2 次笑声 = 60 分
        return min(100.0, density / 2.0 * 60)

    def _score_emotion(self, transcript: str) -> float:
        """情感峰值（惊喜/愤怒/兴奋/震惊关键词）"""
        emotion_keywords = [
            "震惊", "惊讶", "惊人", "不敢相信", "wow", "omg", "shocking",
            "愤怒", "生气", "气死我了", "angry", "furious",
            "兴奋", "太棒了", "激动", "amazing", "incredible", "exciting",
            "搞笑", "笑死", "太逗", "hilarious", "funny",
            "感动", "泪目", "心疼", "touching", "emotional",
        ]
        hits = sum(transcript.count(kw) for kw in emotion_keywords)
        # 每个情感词 +20 分，封顶 100
        return min(100.0, hits * 20.0)

    def _score_completeness(self, seg: ClipSegment, transcript: str) -> float:
        """对话完整性：是否有完整的句子结构"""
        if not transcript.strip():
            return 0.0

        # 检查开头是否像句子中间（被截断的标志）
        starts_mid = transcript[0].islower() if transcript else False
        # 检查结尾是否有句号/问号/感叹号
        ends_complete = transcript.rstrip().endswith(("。", "！", "？", ".", "!", "?"))

        score = 50.0
        if not starts_mid:
            score += 25.0
        if ends_complete:
            score += 25.0

        return score

    def _score_silence_ratio(self, seg: ClipSegment) -> float:
        """
        有声占比。
        注：精确计算需要音频能量分析（这里用转录文本密度估算）。
        如果有音频 energy 数据请替换此函数。
        """
        duration = seg.end_time - seg.start_time
        transcript_len = len(seg.transcript or "")

        # 经验值：正常说话速度约 150 字/分钟
        expected_chars = duration / 60 * 150
        ratio = min(transcript_len / max(expected_chars, 1), 2.0)

        if ratio < 0.3:
            return ratio / 0.3 * 40  # 太静 → 低分
        if ratio > 1.5:
            return max(0, 100 - (ratio - 1.5) / 0.5 * 30)  # 太密 → 轻微扣分
        return 70 + min(30, (ratio - 0.3) / 1.2 * 30)  # 0.3-1.5 之间最优

    def _score_pace(self, transcript: str, duration: float) -> float:
        """语速健康度（字/分钟）"""
        if duration == 0:
            return 0.0
        chars_per_min = len(transcript) / duration * 60
        # 健康范围：100-200 字/分钟
        if 100 <= chars_per_min <= 200:
            return 80.0
        if chars_per_min < 100:
            return max(0, chars_per_min / 100 * 50)
        # > 200 字/分钟：太快
        return max(0, 80 - (chars_per_min - 200) / 100 * 40)

    def _score_keywords(self, transcript: str) -> float:
        """关键词命中得分"""
        text_lower = transcript.lower()
        hits = sum(1 for kw in HIGH_ENGAGEMENT_KEYWORDS if kw.lower() in text_lower)
        return min(100.0, hits * 15.0)

    def _build_reasons(
        self,
        laughter: float, emotion: float, completeness: float,
        silence: float, pace: float, keywords: float,
        transcript: str,
        duration: float,
    ) -> List[str]:
        """生成人类可读的原因描述"""
        reasons = []
        if laughter > 60:
            reasons.append("笑声密集")
        if emotion > 60:
            reasons.append("情感充沛")
        if completeness > 80:
            reasons.append("对话完整")
        if keywords > 30:
            reasons.append("高吸引力关键词")
        if silence > 70:
            reasons.append("声音清晰")
        if duration < self.min_clip_duration:
            reasons.append(f"时长偏短({duration:.0f}s)")
        elif duration > self.max_clip_duration:
            reasons.append(f"时长偏长({duration:.0f}s)")
        if not reasons:
            reasons.append("综合评分")
        return reasons
