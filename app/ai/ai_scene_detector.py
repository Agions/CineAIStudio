#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI场景检测器
提供智能场景检测、镜头边界检测、关键帧提取等功能
"""

import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import threading
import queue
import time
from collections import defaultdict, deque
import logging
import json
from concurrent.futures import ThreadPoolExecutor


class DetectionMethod(Enum):
    """检测方法"""
    HISTOGRAM_DIFF = "histogram_diff"      # 直方图差异
    EDGE_DIFF = "edge_diff"               # 边缘差异
    MOTION_VECTOR = "motion_vector"       # 运动矢量
    CONTOUR_CHANGE = "contour_change"     # 轮廓变化
    DEEP_LEARNING = "deep_learning"       # 深度学习
    HYBRID = "hybrid"                     # 混合方法


class SceneCategory(Enum):
    """场景类别"""
    OPENING = "opening"              # 开场
    CLOSING = "closing"              # 结尾
    ACTION = "action"                # 动作
    DIALOGUE = "dialogue"            # 对话
    MONTAGE = "montage"              # 蒙太奇
    TRANSITION = "transition"        # 转场
    STABLE = "stable"                # 稳定
    DYNAMIC = "dynamic"              # 动态


@dataclass
class SceneBoundary:
    """场景边界"""
    frame_number: int
    timestamp: float
    confidence: float
    method: DetectionMethod
    features: Dict[str, Any]


@dataclass
class KeyFrame:
    """关键帧"""
    frame_number: int
    timestamp: float
    importance_score: float
    features: Dict[str, Any]
    thumbnail: Optional[np.ndarray] = None


@dataclass
class Shot:
    """镜头"""
    start_frame: int
    end_frame: int
    start_time: float
    end_time: float
    scene_boundaries: List[SceneBoundary]
    key_frames: List[KeyFrame]
    shot_type: str
    motion_level: float
    visual_complexity: float


class HistogramDetector:
    """直方图检测器"""

    def __init__(self, threshold: float = 0.3):
        self.threshold = threshold
        self.prev_hist = None

    def detect_change(self, frame: np.ndarray, frame_number: int) -> Optional[SceneBoundary]:
        """检测直方图变化"""
        # 计算当前帧的直方图
        hist = self._calculate_histogram(frame)

        if self.prev_hist is not None:
            # 计算直方图差异
            diff = self._calculate_histogram_difference(self.prev_hist, hist)

            if diff > self.threshold:
                return SceneBoundary(
                    frame_number=frame_number,
                    timestamp=frame_number / 30.0,  # 假设30fps
                    confidence=diff,
                    method=DetectionMethod.HISTOGRAM_DIFF,
                    features={"histogram_diff": diff}
                )

        self.prev_hist = hist
        return None

    def _calculate_histogram(self, frame: np.ndarray) -> np.ndarray:
        """计算颜色直方图"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 计算三个通道的直方图
        hist_h = cv2.calcHist([hsv], [0], None, [16], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [8], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], None, [8], [0, 256])

        # 归一化
        hist_h = cv2.normalize(hist_h, hist_h).flatten()
        hist_s = cv2.normalize(hist_s, hist_s).flatten()
        hist_v = cv2.normalize(hist_v, hist_v).flatten()

        return np.concatenate([hist_h, hist_s, hist_v])

    def _calculate_histogram_difference(self, hist1: np.ndarray, hist2: np.ndarray) -> float:
        """计算直方图差异"""
        # 使用相关性方法计算差异
        correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        return 1.0 - correlation


class EdgeDetector:
    """边缘检测器"""

    def __init__(self, threshold: float = 0.4):
        self.threshold = threshold
        self.prev_edges = None

    def detect_change(self, frame: np.ndarray, frame_number: int) -> Optional[SceneBoundary]:
        """检测边缘变化"""
        # 计算边缘
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)

        if self.prev_edges is not None:
            # 计算边缘差异
            diff = self._calculate_edge_difference(self.prev_edges, edges)

            if diff > self.threshold:
                return SceneBoundary(
                    frame_number=frame_number,
                    timestamp=frame_number / 30.0,
                    confidence=diff,
                    method=DetectionMethod.EDGE_DIFF,
                    features={"edge_diff": diff}
                )

        self.prev_edges = edges
        return None

    def _calculate_edge_difference(self, edges1: np.ndarray, edges2: np.ndarray) -> float:
        """计算边缘差异"""
        # 计算边缘像素差异
        diff = cv2.absdiff(edges1, edges2)
        return np.sum(diff) / (edges1.size * 255.0)


class MotionVectorDetector:
    """运动矢量检测器"""

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.prev_frame = None
        self.feature_params = dict(
            maxCorners=100,
            qualityLevel=0.3,
            minDistance=7,
            blockSize=7
        )
        self.lk_params = dict(
            winSize=(15, 15),
            maxLevel=2,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
        )

    def detect_change(self, frame: np.ndarray, frame_number: int) -> Optional[SceneBoundary]:
        """检测运动矢量变化"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if self.prev_frame is None:
            self.prev_frame = gray
            return None

        # 检测特征点
        p0 = cv2.goodFeaturesToTrack(gray, mask=None, **self.feature_params)

        if p0 is not None:
            # 计算光流
            p1, st, err = cv2.calcOpticalFlowPyrLK(
                self.prev_frame, gray, p0, None, **self.lk_params
            )

            if p1 is not None:
                # 计算运动矢量
                motion_vectors = p1[st == 1] - p0[st == 1]
                motion_magnitude = np.linalg.norm(motion_vectors, axis=1)

                # 分析运动模式
                motion_stats = self._analyze_motion_pattern(motion_magnitude)

                if motion_stats['change_score'] > self.threshold:
                    return SceneBoundary(
                        frame_number=frame_number,
                        timestamp=frame_number / 30.0,
                        confidence=motion_stats['change_score'],
                        method=DetectionMethod.MOTION_VECTOR,
                        features=motion_stats
                    )

        self.prev_frame = gray
        return None

    def _analyze_motion_pattern(self, motion_magnitude: np.ndarray) -> Dict[str, float]:
        """分析运动模式"""
        if len(motion_magnitude) == 0:
            return {"change_score": 0.0, "avg_motion": 0.0, "motion_variance": 0.0}

        avg_motion = np.mean(motion_magnitude)
        motion_variance = np.var(motion_magnitude)

        # 计算变化分数
        change_score = (avg_motion + motion_variance) / 2.0

        return {
            "change_score": min(change_score, 1.0),
            "avg_motion": avg_motion,
            "motion_variance": motion_variance
        }


class ContourDetector:
    """轮廓检测器"""

    def __init__(self, threshold: float = 0.3):
        self.threshold = threshold
        self.prev_contours = None

    def detect_change(self, frame: np.ndarray, frame_number: int) -> Optional[SceneBoundary]:
        """检测轮廓变化"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 二值化
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if self.prev_contours is not None:
            # 计算轮廓变化
            change_score = self._calculate_contour_change(self.prev_contours, contours)

            if change_score > self.threshold:
                return SceneBoundary(
                    frame_number=frame_number,
                    timestamp=frame_number / 30.0,
                    confidence=change_score,
                    method=DetectionMethod.CONTOUR_CHANGE,
                    features={"contour_change": change_score}
                )

        self.prev_contours = contours
        return None

    def _calculate_contour_change(self, contours1: List, contours2: List) -> float:
        """计算轮廓变化"""
        # 计算轮廓数量变化
        count_diff = abs(len(contours1) - len(contours2))

        # 计算轮廓面积变化
        areas1 = [cv2.contourArea(c) for c in contours1]
        areas2 = [cv2.contourArea(c) for c in contours2]

        total_area1 = sum(areas1) if areas1 else 0
        total_area2 = sum(areas2) if areas2 else 0

        area_diff = abs(total_area1 - total_area2) / max(total_area1, total_area2, 1)

        # 综合变化分数
        return (count_diff / max(len(contours1), len(contours2), 1) + area_diff) / 2.0


class HybridDetector:
    """混合检测器"""

    def __init__(self, weights: Dict[DetectionMethod, float] = None):
        self.weights = weights or {
            DetectionMethod.HISTOGRAM_DIFF: 0.3,
            DetectionMethod.EDGE_DIFF: 0.2,
            DetectionMethod.MOTION_VECTOR: 0.3,
            DetectionMethod.CONTOUR_CHANGE: 0.2
        }

        self.detectors = {
            DetectionMethod.HISTOGRAM_DIFF: HistogramDetector(),
            DetectionMethod.EDGE_DIFF: EdgeDetector(),
            DetectionMethod.MOTION_VECTOR: MotionVectorDetector(),
            DetectionMethod.CONTOUR_CHANGE: ContourDetector()
        }

    def detect_changes(self, frame: np.ndarray, frame_number: int) -> List[SceneBoundary]:
        """检测场景变化"""
        boundaries = []

        # 使用各种检测器
        for method, detector in self.detectors.items():
            boundary = detector.detect_change(frame, frame_number)
            if boundary:
                boundaries.append(boundary)

        # 合并检测结果
        if boundaries:
            return self._merge_boundaries(boundaries)

        return []

    def _merge_boundaries(self, boundaries: List[SceneBoundary]) -> SceneBoundary:
        """合并边界检测结果"""
        # 计算加权平均置信度
        total_confidence = sum(b.confidence * self.weights[b.method] for b in boundaries)
        total_weight = sum(self.weights[b.method] for b in boundaries)
        avg_confidence = total_confidence / total_weight

        # 合并特征
        merged_features = {}
        for boundary in boundaries:
            merged_features.update(boundary.features)

        return SceneBoundary(
            frame_number=boundaries[0].frame_number,
            timestamp=boundaries[0].timestamp,
            confidence=avg_confidence,
            method=DetectionMethod.HYBRID,
            features=merged_features
        )


class KeyFrameExtractor:
    """关键帧提取器"""

    def __init__(self, max_keyframes_per_shot: int = 5):
        self.max_keyframes_per_shot = max_keyframes_per_shot

    def extract_keyframes(self, frames: List[np.ndarray], shot: Shot) -> List[KeyFrame]:
        """提取关键帧"""
        if len(frames) == 0:
            return []

        # 计算每帧的重要性分数
        importance_scores = self._calculate_importance_scores(frames)

        # 选择关键帧
        keyframes = self._select_keyframes(frames, importance_scores, shot)

        return keyframes

    def _calculate_importance_scores(self, frames: List[np.ndarray]) -> List[float]:
        """计算每帧的重要性分数"""
        scores = []

        for i, frame in enumerate(frames):
            score = 0.0

            # 计算视觉复杂性
            complexity = self._calculate_visual_complexity(frame)
            score += complexity * 0.3

            # 计算边缘密度
            edge_density = self._calculate_edge_density(frame)
            score += edge_density * 0.2

            # 计算颜色丰富度
            color_richness = self._calculate_color_richness(frame)
            score += color_richness * 0.2

            # 计算运动强度（如果有前一帧）
            if i > 0:
                motion_intensity = self._calculate_motion_intensity(frames[i-1], frame)
                score += motion_intensity * 0.3

            scores.append(score)

        return scores

    def _calculate_visual_complexity(self, frame: np.ndarray) -> float:
        """计算视觉复杂性"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 计算图像的标准差
        std_dev = np.std(gray)

        # 归一化到0-1
        return min(std_dev / 128.0, 1.0)

    def _calculate_edge_density(self, frame: np.ndarray) -> float:
        """计算边缘密度"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)

        return np.sum(edges > 0) / edges.size

    def _calculate_color_richness(self, frame: np.ndarray) -> float:
        """计算颜色丰富度"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 计算色调直方图
        hist_h = cv2.calcHist([hsv], [0], None, [16], [0, 180])

        # 计算直方图的熵
        hist_norm = hist_h / np.sum(hist_h)
        entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-10))

        # 归一化到0-1
        return min(entropy / 4.0, 1.0)

    def _calculate_motion_intensity(self, prev_frame: np.ndarray, curr_frame: np.ndarray) -> float:
        """计算运动强度"""
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)

        # 计算帧差
        diff = cv2.absdiff(prev_gray, curr_gray)

        return np.mean(diff) / 255.0

    def _select_keyframes(self, frames: List[np.ndarray], scores: List[float], shot: Shot) -> List[KeyFrame]:
        """选择关键帧"""
        if len(frames) <= self.max_keyframes_per_shot:
            # 如果帧数较少，选择所有帧
            selected_indices = list(range(len(frames)))
        else:
            # 使用峰值检测选择关键帧
            selected_indices = self._peak_detection(scores, self.max_keyframes_per_shot)

        keyframes = []
        for idx in selected_indices:
            keyframe = KeyFrame(
                frame_number=shot.start_frame + idx,
                timestamp=shot.start_time + idx / 30.0,
                importance_score=scores[idx],
                features={"visual_complexity": scores[idx]},
                thumbnail=frames[idx].copy()
            )
            keyframes.append(keyframe)

        return keyframes

    def _peak_detection(self, scores: List[float], max_peaks: int) -> List[int]:
        """峰值检测"""
        peaks = []

        # 简单的峰值检测算法
        for i in range(1, len(scores) - 1):
            if scores[i] > scores[i-1] and scores[i] > scores[i+1]:
                peaks.append(i)

        # 按分数排序并选择前max_peaks个
        peaks.sort(key=lambda x: scores[x], reverse=True)
        return peaks[:max_peaks]


class AISceneDetector:
    """AI场景检测器主类"""

    def __init__(self, detection_method: DetectionMethod = DetectionMethod.HYBRID):
        self.detection_method = detection_method
        self.detector = self._create_detector(detection_method)
        self.keyframe_extractor = KeyFrameExtractor()
        self.is_processing = False

    def _create_detector(self, method: DetectionMethod):
        """创建检测器"""
        if method == DetectionMethod.HYBRID:
            return HybridDetector()
        elif method == DetectionMethod.HISTOGRAM_DIFF:
            return HistogramDetector()
        elif method == DetectionMethod.EDGE_DIFF:
            return EdgeDetector()
        elif method == DetectionMethod.MOTION_VECTOR:
            return MotionVectorDetector()
        elif method == DetectionMethod.CONTOUR_CHANGE:
            return ContourDetector()
        else:
            return HybridDetector()

    def detect_scenes(self, video_path: str) -> List[Shot]:
        """检测视频场景"""
        self.is_processing = True

        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"无法打开视频文件: {video_path}")

            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            scenes = []
            current_shot_start = 0
            current_shot_frames = []
            scene_boundaries = []

            frame_number = 0
            while cap.isOpened() and self.is_processing:
                ret, frame = cap.read()
                if not ret:
                    break

                # 检测场景变化
                boundaries = self.detector.detect_changes(frame, frame_number)
                if boundaries:
                    scene_boundaries.extend(boundaries)

                    # 创建新的镜头
                    if len(current_shot_frames) > 0:
                        shot = self._create_shot(
                            current_shot_start, frame_number - 1,
                            current_shot_frames, scene_boundaries, fps
                        )
                        scenes.append(shot)

                    current_shot_start = frame_number
                    current_shot_frames = []

                current_shot_frames.append(frame)
                frame_number += 1

            # 添加最后一个镜头
            if len(current_shot_frames) > 0:
                shot = self._create_shot(
                    current_shot_start, frame_number - 1,
                    current_shot_frames, scene_boundaries, fps
                )
                scenes.append(shot)

            cap.release()
            return scenes

        except Exception as e:
            self.is_processing = False
            raise e

    def _create_shot(self, start_frame: int, end_frame: int,
                    frames: List[np.ndarray], boundaries: List[SceneBoundary], fps: float) -> Shot:
        """创建镜头"""
        # 计算镜头统计信息
        motion_level = self._calculate_motion_level(frames)
        visual_complexity = self._calculate_visual_complexity(frames)

        # 提取关键帧
        shot = Shot(
            start_frame=start_frame,
            end_frame=end_frame,
            start_time=start_frame / fps,
            end_time=end_frame / fps,
            scene_boundaries=boundaries,
            key_frames=[],  # 将在后面填充
            shot_type=self._classify_shot_type(frames, motion_level),
            motion_level=motion_level,
            visual_complexity=visual_complexity
        )

        # 提取关键帧
        shot.key_frames = self.keyframe_extractor.extract_keyframes(frames, shot)

        return shot

    def _calculate_motion_level(self, frames: List[np.ndarray]) -> float:
        """计算镜头运动水平"""
        if len(frames) < 2:
            return 0.0

        motion_levels = []
        for i in range(1, len(frames)):
            prev_gray = cv2.cvtColor(frames[i-1], cv2.COLOR_BGR2GRAY)
            curr_gray = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)

            # 计算光流
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, curr_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
            )

            magnitude = np.sqrt(flow[:, :, 0]**2 + flow[:, :, 1]**2)
            motion_levels.append(np.mean(magnitude))

        return np.mean(motion_levels) if motion_levels else 0.0

    def _calculate_visual_complexity(self, frames: List[np.ndarray]) -> float:
        """计算视觉复杂性"""
        complexities = []
        for frame in frames:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            complexity = np.std(gray) / 128.0
            complexities.append(complexity)

        return np.mean(complexities) if complexities else 0.0

    def _classify_shot_type(self, frames: List[np.ndarray], motion_level: float) -> str:
        """分类镜头类型"""
        if motion_level > 5.0:
            return SceneCategory.DYNAMIC.value
        elif motion_level < 1.0:
            return SceneCategory.STABLE.value
        else:
            return SceneCategory.ACTION.value

    def stop_detection(self):
        """停止检测"""
        self.is_processing = False

    def export_scene_detection_results(self, scenes: List[Shot], output_path: str):
        """导出场景检测结果"""
        export_data = []
        for i, scene in enumerate(scenes):
            data = {
                "shot_id": i,
                "start_frame": scene.start_frame,
                "end_frame": scene.end_frame,
                "start_time": scene.start_time,
                "end_time": scene.end_time,
                "duration": scene.end_time - scene.start_time,
                "shot_type": scene.shot_type,
                "motion_level": scene.motion_level,
                "visual_complexity": scene.visual_complexity,
                "keyframe_count": len(scene.key_frames),
                "boundary_count": len(scene.scene_boundaries)
            }
            export_data.append(data)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

    def export_keyframes(self, scenes: List[Shot], output_dir: str):
        """导出关键帧"""
        import os
        os.makedirs(output_dir, exist_ok=True)

        for i, scene in enumerate(scenes):
            for j, keyframe in enumerate(scene.key_frames):
                if keyframe.thumbnail is not None:
                    filename = f"scene_{i}_keyframe_{j}.jpg"
                    filepath = os.path.join(output_dir, filename)
                    cv2.imwrite(filepath, keyframe.thumbnail)


# 工具函数
def create_scene_detector(method: DetectionMethod = DetectionMethod.HYBRID) -> AISceneDetector:
    """创建场景检测器"""
    return AISceneDetector(method)


def detect_video_scenes(video_path: str, method: DetectionMethod = DetectionMethod.HYBRID) -> List[Shot]:
    """检测视频场景"""
    detector = create_scene_detector(method)
    return detector.detect_scenes(video_path)


def main():
    """主函数 - 用于测试"""
    # 创建测试检测器
    detector = create_scene_detector()

    # 测试检测功能（需要实际视频文件）
    print("AI场景检测器创建成功")
    print(f"检测方法: {detector.detection_method.value}")


if __name__ == "__main__":
    main()