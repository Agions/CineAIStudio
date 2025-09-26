#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 智能剪辑引擎
基于AI的智能剪辑决策系统，提供自动化视频剪辑、场景检测和内容优化
"""

import os
import time
import threading
import numpy as np
import cv2
from typing import Dict, List, Optional, Tuple, Union, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
from collections import defaultdict, deque
import logging

from .logger import get_logger
from .event_system import EventBus
from .ai_video_engine import AIVideoEngine, AIModelType, AnalysisResult, AITask
from .video_engine import VideoEngine, OperationResult
from .timeline_engine import TimelineEngine, Clip, Transition
from ..utils.error_handler import ErrorInfo, ErrorType, ErrorSeverity, ErrorContext, get_global_error_handler
from ..utils.ffmpeg_utils import get_ffmpeg_utils, VideoInfo


class EditingDecision(Enum):
    """剪辑决策枚举"""
    KEEP = "keep"
    CUT = "cut"
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    TRANSITION = "transition"
    SLOW_MOTION = "slow_motion"
    FAST_FORWARD = "fast_forward"
    HIGHLIGHT = "highlight"
    REMOVE = "remove"


class SceneType(Enum):
    """场景类型枚举"""
    INTRODUCTION = "introduction"
    ACTION = "action"
    DIALOGUE = "dialogue"
    EMOTIONAL = "emotional"
    LANDSCAPE = "landscape"
    CLOSE_UP = "close_up"
    MEDIUM_SHOT = "medium_shot"
    WIDE_SHOT = "wide_shot"
    TRANSITIONAL = "transitional"
    CONCLUSION = "conclusion"


class ContentQuality(Enum):
    """内容质量枚举"""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    UNUSABLE = "unusable"


@dataclass
class SceneSegment:
    """场景片段数据类"""
    id: str
    start_time: float
    end_time: float
    duration: float
    scene_type: SceneType
    content_quality: ContentQuality
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    analysis_results: List[AnalysisResult] = field(default_factory=list)


@dataclass
class EditingPoint:
    """剪辑点数据类"""
    timestamp: float
    decision: EditingDecision
    confidence: float
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EditingSuggestion:
    """剪辑建议数据类"""
    id: str
    type: str
    description: str
    start_time: float
    end_time: float
    confidence: float
    priority: int
    parameters: Dict[str, Any] = field(default_factory=dict)
    expected_improvement: float = 0.0


class ContentAnalyzer:
    """内容分析器"""

    def __init__(self, ai_engine: AIVideoEngine, logger=None):
        self.ai_engine = ai_engine
        self.logger = logger or get_logger("ContentAnalyzer")
        self.error_handler = get_global_error_handler()

        # 分析配置
        self.scene_threshold = 0.3
        self.min_scene_duration = 2.0
        self.max_scene_duration = 60.0

        # 质量评估权重
        self.quality_weights = {
            'visual_quality': 0.3,
            'audio_quality': 0.2,
            'content_interest': 0.3,
            'technical_stability': 0.2
        }

    def analyze_video_content(self, video_path: str) -> List[SceneSegment]:
        """分析视频内容"""
        try:
            self.logger.info(f"开始分析视频内容: {video_path}")

            # 获取视频信息
            video_info = get_ffmpeg_utils().get_video_info(video_path)

            # 场景分割
            scene_segments = self._detect_scenes(video_path, video_info)

            # 内容质量评估
            for segment in scene_segments:
                quality_score = self._assess_content_quality(
                    video_path, segment
                )
                segment.content_quality = self._score_to_quality(quality_score)

            # 场景分类
            for segment in scene_segments:
                scene_type = self._classify_scene(segment)
                segment.scene_type = scene_type

            # 标签提取
            for segment in scene_segments:
                tags = self._extract_tags(segment)
                segment.tags.extend(tags)

            self.logger.info(f"视频内容分析完成，发现 {len(scene_segments)} 个场景")
            return scene_segments

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.AI,
                severity=ErrorSeverity.HIGH,
                message=f"视频内容分析失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="ContentAnalyzer",
                    operation="analyze_video_content"
                ),
                user_message="视频内容分析失败"
            )
            self.error_handler.handle_error(error_info)
            raise

    def _detect_scenes(self, video_path: str, video_info: VideoInfo) -> List[SceneSegment]:
        """检测场景"""
        try:
            segments = []
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                raise ValueError(f"无法打开视频: {video_path}")

            fps = video_info.fps
            frame_count = int(video_info.duration * fps)

            # 场景检测参数
            prev_hist = None
            scene_start = 0.0
            frame_idx = 0

            while frame_idx < frame_count:
                ret, frame = cap.read()
                if not ret:
                    break

                # 计算颜色直方图
                hist = cv2.calcHist([frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
                hist = hist.flatten()

                if prev_hist is not None:
                    # 计算直方图差异
                    diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)

                    # 如果差异超过阈值，检测到场景切换
                    if diff < self.scene_threshold:
                        scene_end = frame_idx / fps
                        duration = scene_end - scene_start

                        if duration >= self.min_scene_duration:
                            segment = SceneSegment(
                                id=f"scene_{len(segments)}",
                                start_time=scene_start,
                                end_time=scene_end,
                                duration=duration,
                                scene_type=SceneType.TRANSITIONAL,
                                content_quality=ContentQuality.AVERAGE,
                                confidence=0.8
                            )
                            segments.append(segment)

                        scene_start = scene_end

                prev_hist = hist
                frame_idx += 1

            # 添加最后一个场景
            scene_end = frame_idx / fps
            duration = scene_end - scene_start
            if duration >= self.min_scene_duration:
                segment = SceneSegment(
                    id=f"scene_{len(segments)}",
                    start_time=scene_start,
                    end_time=scene_end,
                    duration=duration,
                    scene_type=SceneType.TRANSITIONAL,
                    content_quality=ContentQuality.AVERAGE,
                    confidence=0.8
                )
                segments.append(segment)

            cap.release()
            return segments

        except Exception as e:
            self.logger.error(f"场景检测失败: {str(e)}")
            raise

    def _assess_content_quality(self, video_path: str, segment: SceneSegment) -> float:
        """评估内容质量"""
        try:
            # 视觉质量评估
            visual_score = self._assess_visual_quality(video_path, segment)

            # 内容兴趣度评估
            interest_score = self._assess_content_interest(video_path, segment)

            # 技术稳定性评估
            stability_score = self._assess_technical_stability(video_path, segment)

            # 加权总分
            total_score = (
                visual_score * self.quality_weights['visual_quality'] +
                interest_score * self.quality_weights['content_interest'] +
                stability_score * self.quality_weights['technical_stability']
            )

            return total_score

        except Exception as e:
            self.logger.error(f"内容质量评估失败: {str(e)}")
            return 0.5

    def _assess_visual_quality(self, video_path: str, segment: SceneSegment) -> float:
        """评估视觉质量"""
        try:
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(segment.start_time * 30))

            frame_count = int(segment.duration * 30)
            quality_scores = []

            for i in range(min(frame_count, 30)):  # 采样30帧
                ret, frame = cap.read()
                if not ret:
                    break

                # 计算清晰度
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
                sharpness_score = min(sharpness / 1000.0, 1.0)

                # 计算亮度
                brightness = np.mean(gray)
                brightness_score = 1.0 - abs(brightness - 128) / 128.0

                # 计算对比度
                contrast = gray.std()
                contrast_score = min(contrast / 64.0, 1.0)

                # 综合视觉质量
                frame_quality = (sharpness_score + brightness_score + contrast_score) / 3.0
                quality_scores.append(frame_quality)

            cap.release()

            return np.mean(quality_scores) if quality_scores else 0.5

        except Exception as e:
            self.logger.error(f"视觉质量评估失败: {str(e)}")
            return 0.5

    def _assess_content_interest(self, video_path: str, segment: SceneSegment) -> float:
        """评估内容兴趣度"""
        try:
            # 基于场景长度评估
            duration_score = 1.0
            if segment.duration < 3.0:
                duration_score = 0.7
            elif segment.duration > 30.0:
                duration_score = 0.8

            # 基于运动量评估
            motion_score = self._assess_motion_level(video_path, segment)

            # 基于复杂度评估
            complexity_score = self._assess_scene_complexity(video_path, segment)

            return (duration_score + motion_score + complexity_score) / 3.0

        except Exception as e:
            self.logger.error(f"内容兴趣度评估失败: {str(e)}")
            return 0.5

    def _assess_motion_level(self, video_path: str, segment: SceneSegment) -> float:
        """评估运动水平"""
        try:
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(segment.start_time * 30))

            prev_frame = None
            motion_scores = []

            for i in range(int(min(segment.duration, 5.0) * 30)):  # 采样5秒
                ret, frame = cap.read()
                if not ret:
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (21, 21), 0)

                if prev_frame is not None:
                    # 计算帧差
                    diff = cv2.absdiff(prev_frame, gray)
                    threshold_diff = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
                    motion_pixels = np.sum(threshold_diff) / 255
                    motion_score = min(motion_pixels / (frame.shape[0] * frame.shape[1]), 1.0)
                    motion_scores.append(motion_score)

                prev_frame = gray

            cap.release()

            return np.mean(motion_scores) if motion_scores else 0.5

        except Exception as e:
            self.logger.error(f"运动水平评估失败: {str(e)}")
            return 0.5

    def _assess_scene_complexity(self, video_path: str, segment: SceneSegment) -> float:
        """评估场景复杂度"""
        try:
            # 基于场景长度
            length_score = min(segment.duration / 10.0, 1.0)

            # 基于场景数量（如果有多个子场景）
            complexity_score = length_score

            return complexity_score

        except Exception as e:
            self.logger.error(f"场景复杂度评估失败: {str(e)}")
            return 0.5

    def _assess_technical_stability(self, video_path: str, segment: SceneSegment) -> float:
        """评估技术稳定性"""
        try:
            # 检查视频稳定性
            stability_score = 0.9  # 默认值，实际需要更复杂的算法

            return stability_score

        except Exception as e:
            self.logger.error(f"技术稳定性评估失败: {str(e)}")
            return 0.5

    def _score_to_quality(self, score: float) -> ContentQuality:
        """将分数转换为质量等级"""
        if score >= 0.9:
            return ContentQuality.EXCELLENT
        elif score >= 0.7:
            return ContentQuality.GOOD
        elif score >= 0.5:
            return ContentQuality.AVERAGE
        elif score >= 0.3:
            return ContentQuality.POOR
        else:
            return ContentQuality.UNUSABLE

    def _classify_scene(self, segment: SceneSegment) -> SceneType:
        """分类场景类型"""
        try:
            # 基于持续时间分类
            if segment.duration < 3.0:
                return SceneType.TRANSITIONAL
            elif segment.duration > 30.0:
                return SceneType.LANDSCAPE

            # 基于质量分类
            if segment.content_quality in [ContentQuality.EXCELLENT, ContentQuality.GOOD]:
                return SceneType.ACTION
            else:
                return SceneType.DIALOGUE

        except Exception as e:
            self.logger.error(f"场景分类失败: {str(e)}")
            return SceneType.TRANSITIONAL

    def _extract_tags(self, segment: SceneSegment) -> List[str]:
        """提取标签"""
        tags = []

        # 基于场景类型添加标签
        if segment.scene_type == SceneType.ACTION:
            tags.extend(["动作", "动态", "高能量"])
        elif segment.scene_type == SceneType.DIALOGUE:
            tags.extend(["对话", "静态", "叙事"])
        elif segment.scene_type == SceneType.LANDSCAPE:
            tags.extend(["风景", "全景", "静态"])
        elif segment.scene_type == SceneType.TRANSITIONAL:
            tags.extend(["过渡", "转换"])

        # 基于质量添加标签
        if segment.content_quality == ContentQuality.EXCELLENT:
            tags.extend(["高质量", "推荐保留"])
        elif segment.content_quality == ContentQuality.POOR:
            tags.extend(["低质量", "考虑删除"])

        return tags


class EditingDecisionEngine:
    """剪辑决策引擎"""

    def __init__(self, ai_engine: AIVideoEngine, logger=None):
        self.ai_engine = ai_engine
        self.logger = logger or get_logger("EditingDecisionEngine")
        self.error_handler = get_global_error_handler()

        # 决策规则
        self.decision_rules = {
            'quality_threshold': 0.4,
            'min_keep_duration': 2.0,
            'max_keep_duration': 45.0,
            'highlight_threshold': 0.8,
            'remove_threshold': 0.3
        }

    def generate_editing_decisions(self, segments: List[SceneSegment]) -> List[EditingPoint]:
        """生成剪辑决策"""
        try:
            editing_points = []

            for segment in segments:
                # 基于质量的决策
                quality_decision = self._make_quality_decision(segment)

                # 基于时长的决策
                duration_decision = self._make_duration_decision(segment)

                # 基于内容的决策
                content_decision = self._make_content_decision(segment)

                # 综合决策
                final_decision = self._combine_decisions(
                    segment, quality_decision, duration_decision, content_decision
                )

                if final_decision:
                    editing_points.extend(final_decision)

            # 优化决策序列
            editing_points = self._optimize_editing_sequence(editing_points)

            self.logger.info(f"生成了 {len(editing_points)} 个剪辑决策")
            return editing_points

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.AI,
                severity=ErrorSeverity.HIGH,
                message=f"生成剪辑决策失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="EditingDecisionEngine",
                    operation="generate_editing_decisions"
                ),
                user_message="剪辑决策生成失败"
            )
            self.error_handler.handle_error(error_info)
            raise

    def _make_quality_decision(self, segment: SceneSegment) -> List[EditingPoint]:
        """基于质量做决策"""
        decisions = []
        quality_score = self._quality_to_score(segment.content_quality)

        # 高质量片段：保留或高亮
        if quality_score >= self.decision_rules['highlight_threshold']:
            decisions.append(EditingPoint(
                timestamp=segment.start_time,
                decision=EditingDecision.KEEP,
                confidence=quality_score,
                reason="高质量内容"
            ))

            if quality_score > 0.9:
                decisions.append(EditingPoint(
                    timestamp=segment.start_time,
                    decision=EditingDecision.HIGHLIGHT,
                    confidence=quality_score,
                    reason="极高价值内容"
                ))

        # 低质量片段：删除
        elif quality_score < self.decision_rules['remove_threshold']:
            decisions.append(EditingPoint(
                timestamp=segment.start_time,
                decision=EditingDecision.REMOVE,
                confidence=1.0 - quality_score,
                reason="低质量内容"
            ))

        # 中等质量：基于其他因素决定
        else:
            decisions.append(EditingPoint(
                timestamp=segment.start_time,
                decision=EditingDecision.KEEP,
                confidence=quality_score,
                reason="中等质量内容"
            ))

        return decisions

    def _make_duration_decision(self, segment: SceneSegment) -> List[EditingPoint]:
        """基于时长做决策"""
        decisions = []

        # 过短片段：可能删除或合并
        if segment.duration < self.decision_rules['min_keep_duration']:
            decisions.append(EditingPoint(
                timestamp=segment.start_time,
                decision=EditingDecision.REMOVE,
                confidence=0.8,
                reason="片段过短"
            ))

        # 过长片段：考虑分割
        elif segment.duration > self.decision_rules['max_keep_duration']:
            # 在中间点添加剪辑点
            split_time = segment.start_time + segment.duration / 2
            decisions.append(EditingPoint(
                timestamp=split_time,
                decision=EditingDecision.CUT,
                confidence=0.7,
                reason="片段过长，需要分割"
            ))

        return decisions

    def _make_content_decision(self, segment: SceneSegment) -> List[EditingPoint]:
        """基于内容做决策"""
        decisions = []

        # 基于场景类型的决策
        if segment.scene_type == SceneType.INTRODUCTION:
            decisions.append(EditingPoint(
                timestamp=segment.start_time,
                decision=EditingDecision.FADE_IN,
                confidence=0.9,
                reason="开场需要淡入效果"
            ))

        elif segment.scene_type == SceneType.CONCLUSION:
            decisions.append(EditingPoint(
                timestamp=segment.end_time,
                decision=EditingDecision.FADE_OUT,
                confidence=0.9,
                reason="结尾需要淡出效果"
            ))

        elif segment.scene_type == SceneType.ACTION:
            # 动作场景可能需要慢动作
            if "高能量" in segment.tags:
                decisions.append(EditingPoint(
                    timestamp=segment.start_time,
                    decision=EditingDecision.SLOW_MOTION,
                    confidence=0.6,
                    reason="动作场景适合慢动作"
                ))

        return decisions

    def _combine_decisions(self, segment: SceneSegment,
                          quality_decisions: List[EditingPoint],
                          duration_decisions: List[EditingPoint],
                          content_decisions: List[EditingPoint]) -> List[EditingPoint]:
        """综合决策"""
        try:
            # 合并所有决策
            all_decisions = quality_decisions + duration_decisions + content_decisions

            # 按时间排序
            all_decisions.sort(key=lambda x: x.timestamp)

            # 冲突解决
            final_decisions = []
            for decision in all_decisions:
                # 删除决策优先级最高
                if decision.decision == EditingDecision.REMOVE:
                    final_decisions = [d for d in final_decisions if d.timestamp != decision.timestamp]
                    final_decisions.append(decision)
                # 其他决策需要检查冲突
                else:
                    # 检查时间冲突
                    conflict = False
                    for existing in final_decisions:
                        if abs(existing.timestamp - decision.timestamp) < 1.0:
                            conflict = True
                            # 选择置信度更高的决策
                            if decision.confidence > existing.confidence:
                                final_decisions.remove(existing)
                                final_decisions.append(decision)
                            break

                    if not conflict:
                        final_decisions.append(decision)

            return final_decisions

        except Exception as e:
            self.logger.error(f"决策综合失败: {str(e)}")
            return all_decisions

    def _optimize_editing_sequence(self, editing_points: List[EditingPoint]) -> List[EditingPoint]:
        """优化剪辑序列"""
        try:
            # 按时间排序
            editing_points.sort(key=lambda x: x.timestamp)

            # 移除相邻的相同决策
            optimized_points = []
            prev_decision = None

            for point in editing_points:
                if prev_decision is None or point.decision != prev_decision.decision:
                    optimized_points.append(point)
                    prev_decision = point

            # 确保序列的合理性
            final_points = []
            for i, point in enumerate(optimized_points):
                # 检查删除后的片段是否过短
                if point.decision == EditingDecision.REMOVE:
                    if i > 0 and i < len(optimized_points) - 1:
                        prev_time = optimized_points[i-1].timestamp
                        next_time = optimized_points[i+1].timestamp
                        if next_time - prev_time < self.decision_rules['min_keep_duration']:
                            # 取消删除决策
                            continue

                final_points.append(point)

            return final_points

        except Exception as e:
            self.logger.error(f"剪辑序列优化失败: {str(e)}")
            return editing_points

    def _quality_to_score(self, quality: ContentQuality) -> float:
        """将质量转换为分数"""
        quality_scores = {
            ContentQuality.EXCELLENT: 0.95,
            ContentQuality.GOOD: 0.8,
            ContentQuality.AVERAGE: 0.6,
            ContentQuality.POOR: 0.4,
            ContentQuality.UNUSABLE: 0.2
        }
        return quality_scores.get(quality, 0.5)


class IntelligentEditingEngine:
    """智能剪辑引擎"""

    def __init__(self, ai_engine: AIVideoEngine, timeline_engine: TimelineEngine, logger=None):
        self.ai_engine = ai_engine
        self.timeline_engine = timeline_engine
        self.logger = logger or get_logger("IntelligentEditingEngine")
        self.error_handler = get_global_error_handler()

        # 核心组件
        self.content_analyzer = ContentAnalyzer(ai_engine, self.logger)
        self.decision_engine = EditingDecisionEngine(ai_engine, self.logger)

        # 编辑项目
        self.editing_projects: Dict[str, Dict] = {}
        self.project_lock = threading.Lock()

        # 设置
        self.settings = {
            'auto_analysis': True,
            'auto_editing': True,
            'quality_threshold': 0.6,
            'style_templates': ['documentary', 'vlog', 'music_video', 'presentation']
        }

    def create_editing_project(self, project_id: str, video_paths: List[str],
                             output_path: str, style: str = 'auto') -> bool:
        """创建剪辑项目"""
        try:
            with self.project_lock:
                self.editing_projects[project_id] = {
                    'id': project_id,
                    'video_paths': video_paths,
                    'output_path': output_path,
                    'style': style,
                    'status': 'created',
                    'segments': [],
                    'editing_points': [],
                    'suggestions': [],
                    'created_time': time.time(),
                    'updated_time': time.time()
                }

                if self.settings['auto_analysis']:
                    self.analyze_project_content(project_id)

                self.logger.info(f"剪辑项目创建成功: {project_id}")
                return True

        except Exception as e:
            self.logger.error(f"剪辑项目创建失败: {str(e)}")
            return False

    def analyze_project_content(self, project_id: str) -> bool:
        """分析项目内容"""
        try:
            if project_id not in self.editing_projects:
                return False

            project = self.editing_projects[project_id]
            project['status'] = 'analyzing'

            all_segments = []

            # 分析每个视频
            for video_path in project['video_paths']:
                segments = self.content_analyzer.analyze_video_content(video_path)
                all_segments.extend(segments)

            project['segments'] = all_segments
            project['updated_time'] = time.time()

            # 生成剪辑决策
            editing_points = self.decision_engine.generate_editing_decisions(all_segments)
            project['editing_points'] = editing_points

            # 生成剪辑建议
            suggestions = self.generate_editing_suggestions(project_id)
            project['suggestions'] = suggestions

            project['status'] = 'analyzed'
            self.logger.info(f"项目内容分析完成: {project_id}")

            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.AI,
                severity=ErrorSeverity.HIGH,
                message=f"项目内容分析失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="IntelligentEditingEngine",
                    operation="analyze_project_content"
                ),
                user_message="项目内容分析失败"
            )
            self.error_handler.handle_error(error_info)
            return False

    def generate_editing_suggestions(self, project_id: str) -> List[EditingSuggestion]:
        """生成剪辑建议"""
        try:
            if project_id not in self.editing_projects:
                return []

            project = self.editing_projects[project_id]
            segments = project['segments']
            editing_points = project['editing_points']

            suggestions = []

            # 基于剪辑决策生成建议
            for point in editing_points:
                suggestion = self._create_suggestion_from_decision(point, segments)
                if suggestion:
                    suggestions.append(suggestion)

            # 基于风格生成建议
            style_suggestions = self._generate_style_suggestions(project_id, segments)
            suggestions.extend(style_suggestions)

            # 基于质量生成建议
            quality_suggestions = self._generate_quality_suggestions(project_id, segments)
            suggestions.extend(quality_suggestions)

            # 按优先级排序
            suggestions.sort(key=lambda x: x.priority, reverse=True)

            return suggestions

        except Exception as e:
            self.logger.error(f"生成剪辑建议失败: {str(e)}")
            return []

    def _create_suggestion_from_decision(self, decision: EditingPoint,
                                       segments: List[SceneSegment]) -> Optional[EditingSuggestion]:
        """从决策创建建议"""
        try:
            # 找到对应的片段
            segment = None
            for seg in segments:
                if seg.start_time <= decision.timestamp <= seg.end_time:
                    segment = seg
                    break

            if not segment:
                return None

            suggestion_id = f"suggestion_{int(time.time() * 1000)}"

            if decision.decision == EditingDecision.REMOVE:
                return EditingSuggestion(
                    id=suggestion_id,
                    type="remove_segment",
                    description=f"删除低质量片段 ({segment.start_time:.1f}s - {segment.end_time:.1f}s)",
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    confidence=decision.confidence,
                    priority=8,
                    parameters={'reason': decision.reason}
                )

            elif decision.decision == EditingDecision.HIGHLIGHT:
                return EditingSuggestion(
                    id=suggestion_id,
                    type="highlight_segment",
                    description=f"高亮显示精彩片段 ({segment.start_time:.1f}s - {segment.end_time:.1f}s)",
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    confidence=decision.confidence,
                    priority=7,
                    parameters={'highlight_type': 'brightness'}
                )

            elif decision.decision == EditingDecision.SLOW_MOTION:
                return EditingSuggestion(
                    id=suggestion_id,
                    type="apply_slow_motion",
                    description=f"为动作片段添加慢动作效果 ({segment.start_time:.1f}s - {segment.end_time:.1f}s)",
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    confidence=decision.confidence,
                    priority=5,
                    parameters={'speed_factor': 0.5}
                )

            return None

        except Exception as e:
            self.logger.error(f"从决策创建建议失败: {str(e)}")
            return None

    def _generate_style_suggestions(self, project_id: str,
                                  segments: List[SceneSegment]) -> List[EditingSuggestion]:
        """生成风格建议"""
        try:
            if project_id not in self.editing_projects:
                return []

            project = self.editing_projects[project_id]
            style = project['style']
            suggestions = []

            if style == 'documentary':
                suggestions.extend(self._generate_documentary_suggestions(segments))
            elif style == 'vlog':
                suggestions.extend(self._generate_vlog_suggestions(segments))
            elif style == 'music_video':
                suggestions.extend(self._generate_music_video_suggestions(segments))
            elif style == 'presentation':
                suggestions.extend(self._generate_presentation_suggestions(segments))

            return suggestions

        except Exception as e:
            self.logger.error(f"生成风格建议失败: {str(e)}")
            return []

    def _generate_documentary_suggestions(self, segments: List[SceneSegment]) -> List[EditingSuggestion]:
        """生成纪录片风格建议"""
        suggestions = []

        # 为高质量片段添加旁白建议
        high_quality_segments = [s for s in segments if s.content_quality == ContentQuality.EXCELLENT]
        for segment in high_quality_segments[:3]:  # 限制数量
            suggestions.append(EditingSuggestion(
                id=f"suggestion_{int(time.time() * 1000)}",
                type="add_narration",
                description=f"为精彩片段添加旁白 ({segment.start_time:.1f}s - {segment.end_time:.1f}s)",
                start_time=segment.start_time,
                end_time=segment.end_time,
                confidence=0.8,
                priority=6,
                parameters={'narration_type': 'documentary'}
            ))

        return suggestions

    def _generate_vlog_suggestions(self, segments: List[SceneSegment]) -> List[EditingSuggestion]:
        """生成Vlog风格建议"""
        suggestions = []

        # 添加过渡效果建议
        for i in range(len(segments) - 1):
            current = segments[i]
            next_seg = segments[i + 1]

            if abs(current.end_time - next_seg.start_time) < 1.0:
                suggestions.append(EditingSuggestion(
                    id=f"suggestion_{int(time.time() * 1000)}",
                    type="add_transition",
                    description=f"添加场景过渡效果 ({current.end_time:.1f}s)",
                    start_time=current.end_time - 0.5,
                    end_time=next_seg.start_time + 0.5,
                    confidence=0.7,
                    priority=4,
                    parameters={'transition_type': 'fade'}
                ))

        return suggestions

    def _generate_music_video_suggestions(self, segments: List[SceneSegment]) -> List[EditingSuggestion]:
        """生成音乐视频风格建议"""
        suggestions = []

        # 为动作场景添加节拍同步建议
        action_segments = [s for s in segments if s.scene_type == SceneType.ACTION]
        for segment in action_segments:
            suggestions.append(EditingSuggestion(
                id=f"suggestion_{int(time.time() * 1000)}",
                type="sync_to_beat",
                description=f"将动作场景与音乐节拍同步 ({segment.start_time:.1f}s - {segment.end_time:.1f}s)",
                start_time=segment.start_time,
                end_time=segment.end_time,
                confidence=0.6,
                priority=5,
                parameters={'sync_type': 'beat'}
            ))

        return suggestions

    def _generate_presentation_suggestions(self, segments: List[SceneSegment]) -> List[EditingSuggestion]:
        """生成演示风格建议"""
        suggestions = []

        # 为重要片段添加标注建议
        important_segments = [s for s in segments if s.content_quality in [ContentQuality.EXCELLENT, ContentQuality.GOOD]]
        for segment in important_segments:
            suggestions.append(EditingSuggestion(
                id=f"suggestion_{int(time.time() * 1000)}",
                type="add_annotation",
                description=f"为重要片段添加标注 ({segment.start_time:.1f}s - {segment.end_time:.1f}s)",
                start_time=segment.start_time,
                end_time=segment.end_time,
                confidence=0.7,
                priority=4,
                parameters={'annotation_type': 'text'}
            ))

        return suggestions

    def _generate_quality_suggestions(self, project_id: str,
                                    segments: List[SceneSegment]) -> List[EditingSuggestion]:
        """生成质量改进建议"""
        suggestions = []

        # 为低质量片段生成改进建议
        poor_segments = [s for s in segments if s.content_quality == ContentQuality.POOR]
        for segment in poor_segments:
            suggestions.append(EditingSuggestion(
                id=f"suggestion_{int(time.time() * 1000)}",
                type="enhance_quality",
                description=f"增强低质量片段 ({segment.start_time:.1f}s - {segment.end_time:.1f}s)",
                start_time=segment.start_time,
                end_time=segment.end_time,
                confidence=0.8,
                priority=9,
                parameters={'enhancement_type': 'super_resolution'},
                expected_improvement=0.3
            ))

        return suggestions

    def apply_suggestion(self, project_id: str, suggestion_id: str) -> bool:
        """应用剪辑建议"""
        try:
            if project_id not in self.editing_projects:
                return False

            project = self.editing_projects[project_id]
            suggestions = project['suggestions']

            # 找到对应的建议
            suggestion = None
            for s in suggestions:
                if s.id == suggestion_id:
                    suggestion = s
                    break

            if not suggestion:
                return False

            # 应用建议
            success = self._apply_editing_suggestion(project_id, suggestion)

            if success:
                # 移除已应用的建议
                project['suggestions'] = [s for s in suggestions if s.id != suggestion_id]
                project['updated_time'] = time.time()

            return success

        except Exception as e:
            self.logger.error(f"应用剪辑建议失败: {str(e)}")
            return False

    def _apply_editing_suggestion(self, project_id: str, suggestion: EditingSuggestion) -> bool:
        """应用剪辑建议"""
        try:
            if suggestion.type == "remove_segment":
                # 删除片段
                return self.timeline_engine.remove_clip(
                    suggestion.start_time, suggestion.end_time
                )

            elif suggestion.type == "highlight_segment":
                # 高亮片段
                return self.timeline_engine.add_highlight(
                    suggestion.start_time, suggestion.end_time
                )

            elif suggestion.type == "apply_slow_motion":
                # 应用慢动作
                return self.timeline_engine.apply_speed_effect(
                    suggestion.start_time, suggestion.end_time,
                    suggestion.parameters.get('speed_factor', 0.5)
                )

            elif suggestion.type == "add_transition":
                # 添加过渡
                return self.timeline_engine.add_transition(
                    suggestion.start_time, suggestion.end_time,
                    suggestion.parameters.get('transition_type', 'fade')
                )

            elif suggestion.type == "enhance_quality":
                # 增强质量
                return self.ai_engine.enhance_video(
                    f"temp_input.mp4", f"temp_output.mp4",
                    suggestion.parameters.get('enhancement_type', 'super_resolution')
                )

            return False

        except Exception as e:
            self.logger.error(f"应用剪辑建议失败: {str(e)}")
            return False

    def auto_edit_project(self, project_id: str) -> bool:
        """自动编辑项目"""
        try:
            if project_id not in self.editing_projects:
                return False

            project = self.editing_projects[project_id]
            project['status'] = 'auto_editing'

            # 获取建议并按优先级应用
            suggestions = sorted(project['suggestions'], key=lambda x: x.priority)

            applied_count = 0
            for suggestion in suggestions:
                if applied_count >= 10:  # 限制自动应用数量
                    break

                if self.apply_suggestion(project_id, suggestion.id):
                    applied_count += 1

            project['status'] = 'auto_edited'
            project['updated_time'] = time.time()

            self.logger.info(f"自动编辑完成: {project_id} (应用了 {applied_count} 个建议)")
            return True

        except Exception as e:
            error_info = ErrorInfo(
                error_type=ErrorType.AI,
                severity=ErrorSeverity.HIGH,
                message=f"自动编辑失败: {str(e)}",
                exception=e,
                context=ErrorContext(
                    component="IntelligentEditingEngine",
                    operation="auto_edit_project"
                ),
                user_message="自动编辑失败"
            )
            self.error_handler.handle_error(error_info)
            return False

    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """获取项目状态"""
        if project_id not in self.editing_projects:
            return {}

        project = self.editing_projects[project_id]
        return {
            'id': project['id'],
            'status': project['status'],
            'segments_count': len(project['segments']),
            'editing_points_count': len(project['editing_points']),
            'suggestions_count': len(project['suggestions']),
            'created_time': project['created_time'],
            'updated_time': project['updated_time'],
            'style': project['style']
        }

    def get_project_analysis(self, project_id: str) -> Dict[str, Any]:
        """获取项目分析结果"""
        if project_id not in self.editing_projects:
            return {}

        project = self.editing_projects[project_id]

        # 统计信息
        total_duration = sum(seg.duration for seg in project['segments'])
        quality_distribution = {}
        type_distribution = {}

        for segment in project['segments']:
            quality = segment.content_quality.value
            quality_distribution[quality] = quality_distribution.get(quality, 0) + 1

            scene_type = segment.scene_type.value
            type_distribution[scene_type] = type_distribution.get(scene_type, 0) + 1

        return {
            'total_duration': total_duration,
            'segments_count': len(project['segments']),
            'quality_distribution': quality_distribution,
            'type_distribution': type_distribution,
            'editing_decisions': [
                {
                    'timestamp': point.timestamp,
                    'decision': point.decision.value,
                    'confidence': point.confidence,
                    'reason': point.reason
                }
                for point in project['editing_points']
            ]
        }

    def get_project_suggestions(self, project_id: str) -> List[Dict[str, Any]]:
        """获取项目建议"""
        if project_id not in self.editing_projects:
            return []

        project = self.editing_projects[project_id]
        return [
            {
                'id': s.id,
                'type': s.type,
                'description': s.description,
                'start_time': s.start_time,
                'end_time': s.end_time,
                'confidence': s.confidence,
                'priority': s.priority,
                'parameters': s.parameters,
                'expected_improvement': s.expected_improvement
            }
            for s in project['suggestions']
        ]

    def export_editing_decisions(self, project_id: str, output_path: str) -> bool:
        """导出剪辑决策"""
        try:
            if project_id not in self.editing_projects:
                return False

            project = self.editing_projects[project_id]

            export_data = {
                'project_id': project_id,
                'style': project['style'],
                'segments': [
                    {
                        'id': seg.id,
                        'start_time': seg.start_time,
                        'end_time': seg.end_time,
                        'duration': seg.duration,
                        'scene_type': seg.scene_type.value,
                        'content_quality': seg.content_quality.value,
                        'confidence': seg.confidence,
                        'tags': seg.tags
                    }
                    for seg in project['segments']
                ],
                'editing_points': [
                    {
                        'timestamp': point.timestamp,
                        'decision': point.decision.value,
                        'confidence': point.confidence,
                        'reason': point.reason
                    }
                    for point in project['editing_points']
                ],
                'suggestions': [
                    {
                        'id': s.id,
                        'type': s.type,
                        'description': s.description,
                        'start_time': s.start_time,
                        'end_time': s.end_time,
                        'confidence': s.confidence,
                        'priority': s.priority,
                        'parameters': s.parameters
                    }
                    for s in project['suggestions']
                ]
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"剪辑决策导出成功: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"剪辑决策导出失败: {str(e)}")
            return False

    def cleanup(self):
        """清理资源"""
        try:
            # 清理项目
            with self.project_lock:
                self.editing_projects.clear()

            self.logger.info("智能剪辑引擎清理完成")

        except Exception as e:
            self.logger.error(f"清理失败: {str(e)}")


# 全局智能剪辑引擎实例
_intelligent_editing_engine: Optional[IntelligentEditingEngine] = None


def get_intelligent_editing_engine(ai_engine: AIVideoEngine,
                                 timeline_engine: TimelineEngine) -> IntelligentEditingEngine:
    """获取全局智能剪辑引擎实例"""
    global _intelligent_editing_engine
    if _intelligent_editing_engine is None:
        _intelligent_editing_engine = IntelligentEditingEngine(ai_engine, timeline_engine)
    return _intelligent_editing_engine


def cleanup_intelligent_editing_engine() -> None:
    """清理全局智能剪辑引擎实例"""
    global _intelligent_editing_engine
    if _intelligent_editing_engine is not None:
        _intelligent_editing_engine.cleanup()
        _intelligent_editing_engine = None