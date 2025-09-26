#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能视频稳定和防抖系统
提供运动估计、路径平滑、相机运动补偿、视频稳定等功能
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
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor


class StabilizationMethod(Enum):
    """稳定方法"""
    FEATURE_BASED = "feature_based"        # 基于特征点
    OPTICAL_FLOW = "optical_flow"          # 光流法
    GLOBAL_MOTION = "global_motion"        # 全局运动估计
    DEEP_LEARNING = "deep_learning"        # 深度学习
    HYBRID = "hybrid"                      # 混合方法


class MotionType(Enum):
    """运动类型"""
    TRANSLATION = "translation"           # 平移
    ROTATION = "rotation"                 # 旋转
    ZOOM = "zoom"                         # 缩放
    PERSPECTIVE = "perspective"           # 透视
    COMBINED = "combined"                 # 组合运动


@dataclass
class MotionVector:
    """运动矢量"""
    dx: float
    dy: float
    angle: float
    scale: float
    confidence: float
    timestamp: float


@dataclass
class StabilizationParams:
    """稳定参数"""
    smoothing_radius: int = 30            # 平滑半径
    crop_ratio: float = 0.9              # 裁剪比例
    border_type: str = "reflect"         # 边界类型
    max_correction: float = 50.0         # 最大校正量
    motion_threshold: float = 0.1        # 运动阈值


@dataclass
class StabilizationResult:
    """稳定结果"""
    stabilized_frames: int
    total_frames: int
    average_motion_reduction: float
    processing_time: float
    quality_metrics: Dict[str, float]


class FeatureDetector:
    """特征检测器"""

    def __init__(self, feature_type: str = "ORB"):
        self.feature_type = feature_type
        self.detector = self._create_detector()

    def _create_detector(self):
        """创建特征检测器"""
        if self.feature_type == "SIFT":
            return cv2.SIFT_create()
        elif self.feature_type == "SURF":
            return cv2.xfeatures2d.SURF_create()
        elif self.feature_type == "ORB":
            return cv2.ORB_create(nfeatures=1000)
        elif self.feature_type == "AKAZE":
            return cv2.AKAZE_create()
        else:
            return cv2.ORB_create(nfeatures=1000)

    def detect_features(self, frame: np.ndarray) -> Tuple[List[cv2.KeyPoint], np.ndarray]:
        """检测特征点"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        keypoints, descriptors = self.detector.detectAndCompute(gray, None)
        return keypoints, descriptors


class OpticalFlowEstimator:
    """光流估计器"""

    def __init__(self, method: str = "farneback"):
        self.method = method
        self.prev_frame = None
        self.prev_keypoints = None

    def estimate_motion(self, current_frame: np.ndarray,
                       prev_keypoints: List[cv2.KeyPoint] = None) -> MotionVector:
        """估计运动"""
        gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)

        if self.prev_frame is None:
            self.prev_frame = gray
            self.prev_keypoints = prev_keypoints
            return MotionVector(0, 0, 0, 1, 0, time.time())

        if self.method == "farneback":
            return self._farneback_optical_flow(gray)
        elif self.method == "lucas_kanade" and prev_keypoints:
            return self._lucas_kanade_optical_flow(gray, prev_keypoints)
        else:
            return self._farneback_optical_flow(gray)

    def _farneback_optical_flow(self, gray: np.ndarray) -> MotionVector:
        """Farneback光流法"""
        flow = cv2.calcOpticalFlowFarneback(
            self.prev_frame, gray, None,
            0.5, 3, 15, 3, 5, 1.2, 0
        )

        # 计算平均运动
        dx = np.mean(flow[:, :, 0])
        dy = np.mean(flow[:, :, 1])

        # 计算旋转和缩放
        angle = np.arctan2(dy, dx)
        magnitude = np.sqrt(dx**2 + dy**2)

        self.prev_frame = gray

        return MotionVector(
            dx=dx, dy=dy, angle=angle,
            scale=1.0, confidence=magnitude,
            timestamp=time.time()
        )

    def _lucas_kanade_optical_flow(self, gray: np.ndarray,
                                 prev_keypoints: List[cv2.KeyPoint]) -> MotionVector:
        """Lucas-Kanade光流法"""
        if prev_keypoints is None:
            return MotionVector(0, 0, 0, 1, 0, time.time())

        # 转换关键点为点数组
        prev_pts = np.array([kp.pt for kp in prev_keypoints], dtype=np.float32)

        # 计算光流
        next_pts, status, _ = cv2.calcOpticalFlowPyrLK(
            self.prev_frame, gray, prev_pts, None
        )

        # 选择成功的跟踪点
        good_prev = prev_pts[status == 1]
        good_next = next_pts[status == 1]

        if len(good_prev) < 10:
            return MotionVector(0, 0, 0, 1, 0, time.time())

        # 计算运动
        motion_vectors = good_next - good_prev
        dx = np.mean(motion_vectors[:, 0])
        dy = np.mean(motion_vectors[:, 1])

        # 计算旋转和缩放
        angle = np.arctan2(dy, dx)
        magnitude = np.sqrt(dx**2 + dy**2)

        self.prev_frame = gray

        return MotionVector(
            dx=dx, dy=dy, angle=angle,
            scale=1.0, confidence=len(good_prev) / len(prev_keypoints),
            timestamp=time.time()
        )


class MotionSmoother:
    """运动平滑器"""

    def __init__(self, smoothing_radius: int = 30):
        self.smoothing_radius = smoothing_radius
        self.motion_history = deque(maxlen=smoothing_radius * 2)

    def smooth_motion(self, motion: MotionVector) -> MotionVector:
        """平滑运动"""
        self.motion_history.append(motion)

        if len(self.motion_history) < self.smoothing_radius:
            return motion

        # 使用移动平均进行平滑
        window_size = min(self.smoothing_radius, len(self.motion_history))
        recent_motions = list(self.motion_history)[-window_size:]

        # 计算加权平均（越新的权重越大）
        weights = np.exp(np.linspace(-1, 0, len(recent_motions)))
        weights = weights / np.sum(weights)

        smoothed_dx = np.sum([m.dx * w for m, w in zip(recent_motions, weights)])
        smoothed_dy = np.sum([m.dy * w for m, w in zip(recent_motions, weights)])

        # 计算 smoothed 运动矢量
        smoothed_motion = MotionVector(
            dx=smoothed_dx,
            dy=smoothed_dy,
            angle=np.arctan2(smoothed_dy, smoothed_dx),
            scale=1.0,
            confidence=motion.confidence,
            timestamp=motion.timestamp
        )

        return smoothed_motion

    def get_smoothed_trajectory(self, motions: List[MotionVector]) -> List[MotionVector]:
        """获取平滑轨迹"""
        if not motions:
            return []

        # 计算累积运动
        cumulative_x = np.cumsum([m.dx for m in motions])
        cumulative_y = np.cumsum([m.dy for m in motions])

        # 应用高斯平滑
        smoothed_x = self._gaussian_smooth(cumulative_x, self.smoothing_radius)
        smoothed_y = self._gaussian_smooth(cumulative_y, self.smoothing_radius)

        # 计算平滑后的运动
        smoothed_motions = []
        for i, motion in enumerate(motions):
            if i == 0:
                smoothed_dx = smoothed_x[i]
                smoothed_dy = smoothed_y[i]
            else:
                smoothed_dx = smoothed_x[i] - smoothed_x[i-1]
                smoothed_dy = smoothed_y[i] - smoothed_y[i-1]

            smoothed_motion = MotionVector(
                dx=smoothed_dx,
                dy=smoothed_dy,
                angle=np.arctan2(smoothed_dy, smoothed_dx),
                scale=1.0,
                confidence=motion.confidence,
                timestamp=motion.timestamp
            )
            smoothed_motions.append(smoothed_motion)

        return smoothed_motions

    def _gaussian_smooth(self, data: np.ndarray, sigma: float) -> np.ndarray:
        """高斯平滑"""
        from scipy.ndimage import gaussian_filter1d
        try:
            return gaussian_filter1d(data, sigma=sigma)
        except ImportError:
            # 如果scipy不可用，使用简单的移动平均
            kernel_size = int(sigma * 3)
            if kernel_size % 2 == 0:
                kernel_size += 1

            kernel = np.ones(kernel_size) / kernel_size
            return np.convolve(data, kernel, mode='same')


class TransformEstimator:
    """变换估计器"""

    def __init__(self):
        self.prev_frame = None
        self.prev_keypoints = None
        self.prev_descriptors = None

    def estimate_transform(self, frame: np.ndarray,
                          prev_keypoints: List[cv2.KeyPoint] = None,
                          prev_descriptors: np.ndarray = None) -> Tuple[np.ndarray, float]:
        """估计变换矩阵"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if self.prev_frame is None:
            self.prev_frame = gray
            self.prev_keypoints = prev_keypoints
            self.prev_descriptors = prev_descriptors
            return np.eye(3), 0.0

        # 特征匹配
        if prev_keypoints is not None and prev_descriptors is not None:
            transform_matrix, confidence = self._estimate_transform_from_features(
                gray, prev_keypoints, prev_descriptors
            )
        else:
            transform_matrix, confidence = self._estimate_transform_from_intensity(gray)

        self.prev_frame = gray
        self.prev_keypoints = prev_keypoints
        self.prev_descriptors = prev_descriptors

        return transform_matrix, confidence

    def _estimate_transform_from_features(self, gray: np.ndarray,
                                         prev_keypoints: List[cv2.KeyPoint],
                                         prev_descriptors: np.ndarray) -> Tuple[np.ndarray, float]:
        """基于特征估计变换"""
        # 检测当前帧特征
        detector = cv2.ORB_create(nfeatures=1000)
        curr_keypoints, curr_descriptors = detector.detectAndCompute(gray, None)

        if curr_descriptors is None or prev_descriptors is None:
            return np.eye(3), 0.0

        # 特征匹配
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = matcher.match(prev_descriptors, curr_descriptors)

        if len(matches) < 10:
            return np.eye(3), 0.0

        # 提取匹配点
        prev_pts = np.array([prev_keypoints[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        curr_pts = np.array([curr_keypoints[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

        # 估计变换矩阵
        transform_matrix, mask = cv2.findHomography(prev_pts, curr_pts, cv2.RANSAC, 5.0)

        if transform_matrix is None:
            return np.eye(3), 0.0

        confidence = np.sum(mask) / len(mask)
        return transform_matrix, confidence

    def _estimate_transform_from_intensity(self, gray: np.ndarray) -> Tuple[np.ndarray, float]:
        """基于强度估计变换"""
        # 使用ECC算法估计仿射变换
        warp_matrix = np.eye(2, 3, dtype=np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 50, 1e-6)

        try:
            cc, warp_matrix = cv2.findTransformECC(
                self.prev_frame, gray, warp_matrix, cv2.MOTION_AFFINE, criteria
            )

            # 转换为3x3矩阵
            transform_matrix = np.eye(3)
            transform_matrix[:2, :] = warp_matrix

            return transform_matrix, abs(cc)

        except Exception:
            return np.eye(3), 0.0


class VideoStabilizer:
    """视频稳定器"""

    def __init__(self, method: StabilizationMethod = StabilizationMethod.HYBRID):
        self.method = method
        self.params = StabilizationParams()
        self.feature_detector = FeatureDetector()
        self.optical_flow = OpticalFlowEstimator()
        self.motion_smoother = MotionSmoother(self.params.smoothing_radius)
        self.transform_estimator = TransformEstimator()

        self.motion_vectors = []
        self.transform_matrices = []
        self.smoothed_transforms = []

    def stabilize_video(self, input_path: str, output_path: str) -> StabilizationResult:
        """稳定视频"""
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {input_path}")

        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # 计算裁剪后的尺寸
        crop_width = int(width * self.params.crop_ratio)
        crop_height = int(height * self.params.crop_ratio)
        crop_x = (width - crop_width) // 2
        crop_y = (height - crop_height) // 2

        # 创建视频写入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (crop_width, crop_height))

        start_time = time.time()
        processed_frames = 0

        # 第一阶段：运动估计
        motion_estimation_start = time.time()
        self._estimate_motion(cap)
        motion_estimation_time = time.time() - motion_estimation_start

        # 第二阶段：运动平滑
        smoothing_start = time.time()
        self._smooth_motion()
        smoothing_time = time.time() - smoothing_start

        # 重置视频读取
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        frame_index = 0

        # 第三阶段：应用稳定
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            try:
                # 应用稳定变换
                stabilized_frame = self._apply_stabilization(
                    frame, frame_index, crop_x, crop_y, crop_width, crop_height
                )

                # 写入稳定后的帧
                out.write(stabilized_frame)
                processed_frames += 1

            except Exception as e:
                logging.warning(f"处理第 {frame_index} 帧时出错: {e}")
                # 如果稳定失败，写入原始帧
                cropped_frame = frame[crop_y:crop_y+crop_height, crop_x:crop_x+crop_width]
                out.write(cropped_frame)
                processed_frames += 1

            frame_index += 1

        cap.release()
        out.release()

        # 计算质量指标
        quality_metrics = self._calculate_quality_metrics()

        total_time = time.time() - start_time

        return StabilizationResult(
            stabilized_frames=processed_frames,
            total_frames=total_frames,
            average_motion_reduction=self._calculate_motion_reduction(),
            processing_time=total_time,
            quality_metrics=quality_metrics
        )

    def _estimate_motion(self, cap: cv2.VideoCapture):
        """估计运动"""
        frame_index = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # 检测特征点
            keypoints, descriptors = self.feature_detector.detect_features(frame)

            # 估计运动
            if self.method == StabilizationMethod.OPTICAL_FLOW:
                motion = self.optical_flow.estimate_motion(frame, keypoints)
                self.motion_vectors.append(motion)
            elif self.method == StabilizationMethod.FEATURE_BASED:
                transform_matrix, confidence = self.transform_estimator.estimate_transform(
                    frame, keypoints, descriptors
                )
                self.transform_matrices.append(transform_matrix)
            elif self.method == StabilizationMethod.HYBRID:
                # 混合方法：使用特征匹配和光流
                motion = self.optical_flow.estimate_motion(frame, keypoints)
                transform_matrix, confidence = self.transform_estimator.estimate_transform(
                    frame, keypoints, descriptors
                )
                self.motion_vectors.append(motion)
                self.transform_matrices.append(transform_matrix)

            frame_index += 1

    def _smooth_motion(self):
        """平滑运动"""
        if self.method == StabilizationMethod.OPTICAL_FLOW:
            self.smoothed_transforms = self.motion_smoother.get_smoothed_trajectory(self.motion_vectors)
        elif self.method == StabilizationMethod.FEATURE_BASED:
            # 平滑变换矩阵
            self.smoothed_transforms = self._smooth_transform_matrices(self.transform_matrices)
        elif self.method == StabilizationMethod.HYBRID:
            # 结合两种方法的平滑结果
            smoothed_motion = self.motion_smoother.get_smoothed_trajectory(self.motion_vectors)
            smoothed_transforms = self._smooth_transform_matrices(self.transform_matrices)

            # 加权融合
            self.smoothed_transforms = []
            for i in range(len(smoothed_motion)):
                if i < len(smoothed_transforms):
                    # 简单的加权融合
                    alpha = 0.6  # 运动矢量权重
                    beta = 0.4    # 变换矩阵权重

                    # 转换为统一格式
                    smoothed_transform = self._combine_motion_estimates(
                        smoothed_motion[i], smoothed_transforms[i], alpha, beta
                    )
                    self.smoothed_transforms.append(smoothed_transform)

    def _smooth_transform_matrices(self, transforms: List[np.ndarray]) -> List[np.ndarray]:
        """平滑变换矩阵"""
        if not transforms:
            return []

        # 提取变换参数
        translations_x = []
        translations_y = []
        rotations = []
        scales = []

        for transform in transforms:
            # 分解仿射变换
            tx = transform[0, 2]
            ty = transform[1, 2]
            angle = np.arctan2(transform[1, 0], transform[0, 0])
            scale_x = np.sqrt(transform[0, 0]**2 + transform[1, 0]**2)
            scale_y = np.sqrt(transform[0, 1]**2 + transform[1, 1]**2)
            scale = (scale_x + scale_y) / 2

            translations_x.append(tx)
            translations_y.append(ty)
            rotations.append(angle)
            scales.append(scale)

        # 分别平滑每个参数
        smoothed_tx = self.motion_smoother._gaussian_smooth(np.array(translations_x), self.params.smoothing_radius)
        smoothed_ty = self.motion_smoother._gaussian_smooth(np.array(translations_y), self.params.smoothing_radius)
        smoothed_rot = self.motion_smoother._gaussian_smooth(np.array(rotations), self.params.smoothing_radius)
        smoothed_scale = self.motion_smoother._gaussian_smooth(np.array(scales), self.params.smoothing_radius)

        # 重建变换矩阵
        smoothed_transforms = []
        for i in range(len(transforms)):
            transform = np.eye(3)
            transform[0, 0] = smoothed_scale[i] * np.cos(smoothed_rot[i])
            transform[0, 1] = -smoothed_scale[i] * np.sin(smoothed_rot[i])
            transform[1, 0] = smoothed_scale[i] * np.sin(smoothed_rot[i])
            transform[1, 1] = smoothed_scale[i] * np.cos(smoothed_rot[i])
            transform[0, 2] = smoothed_tx[i]
            transform[1, 2] = smoothed_ty[i]

            smoothed_transforms.append(transform)

        return smoothed_transforms

    def _combine_motion_estimates(self, motion: MotionVector, transform: np.ndarray,
                                 alpha: float, beta: float) -> np.ndarray:
        """结合运动估计"""
        # 从运动矢量创建变换矩阵
        motion_transform = np.eye(3)
        motion_transform[0, 2] = motion.dx
        motion_transform[1, 2] = motion.dy

        # 加权融合
        combined_transform = alpha * motion_transform + beta * transform

        return combined_transform

    def _apply_stabilization(self, frame: np.ndarray, frame_index: int,
                           crop_x: int, crop_y: int, crop_width: int, crop_height: int) -> np.ndarray:
        """应用稳定变换"""
        if frame_index >= len(self.smoothed_transforms):
            # 如果没有对应的变换，返回裁剪后的帧
            return frame[crop_y:crop_y+crop_height, crop_x:crop_x+crop_width]

        # 获取平滑后的变换
        smoothed_transform = self.smoothed_transforms[frame_index]

        # 计算逆变换用于稳定
        try:
            inverse_transform = np.linalg.inv(smoothed_transform)

            # 应用逆变换
            height, width = frame.shape[:2]
            stabilized_frame = cv2.warpPerspective(
                frame, inverse_transform, (width, height),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REFLECT
            )

            # 裁剪到目标尺寸
            cropped_frame = stabilized_frame[crop_y:crop_y+crop_height, crop_x:crop_x+crop_width]

            return cropped_frame

        except Exception as e:
            logging.warning(f"应用稳定变换失败: {e}")
            # 返回裁剪后的原始帧
            return frame[crop_y:crop_y+crop_height, crop_x:crop_x+crop_width]

    def _calculate_motion_reduction(self) -> float:
        """计算运动减少量"""
        if len(self.motion_vectors) == 0 or len(self.smoothed_transforms) == 0:
            return 0.0

        # 计算原始运动总量
        original_motion = sum(np.sqrt(m.dx**2 + m.dy**2) for m in self.motion_vectors)

        # 计算平滑后运动总量
        smoothed_motion = 0
        for transform in self.smoothed_transforms:
            dx = transform[0, 2]
            dy = transform[1, 2]
            smoothed_motion += np.sqrt(dx**2 + dy**2)

        if original_motion == 0:
            return 0.0

        return (original_motion - smoothed_motion) / original_motion

    def _calculate_quality_metrics(self) -> Dict[str, float]:
        """计算质量指标"""
        metrics = {}

        # 计算帧间运动的稳定性
        if len(self.smoothed_transforms) > 1:
            motion_differences = []
            for i in range(1, len(self.smoothed_transforms)):
                diff = np.abs(self.smoothed_transforms[i] - self.smoothed_transforms[i-1])
                motion_diff = np.sqrt(diff[0, 2]**2 + diff[1, 2]**2)
                motion_differences.append(motion_diff)

            metrics["motion_smoothness"] = 1.0 / (1.0 + np.std(motion_differences))
            metrics["average_motion"] = np.mean(motion_differences)
        else:
            metrics["motion_smoothness"] = 0.0
            metrics["average_motion"] = 0.0

        # 计算变换的合理性
        if self.transform_matrices:
            scales = []
            for transform in self.transform_matrices:
                scale_x = np.sqrt(transform[0, 0]**2 + transform[1, 0]**2)
                scale_y = np.sqrt(transform[0, 1]**2 + transform[1, 1]**2)
                scales.append((scale_x + scale_y) / 2)

            metrics["scale_stability"] = 1.0 / (1.0 + np.std(scales))
            metrics["average_scale"] = np.mean(scales)
        else:
            metrics["scale_stability"] = 0.0
            metrics["average_scale"] = 1.0

        return metrics

    def set_parameters(self, params: StabilizationParams):
        """设置参数"""
        self.params = params
        self.motion_smoother = MotionSmoother(params.smoothing_radius)


class RealTimeVideoStabilizer:
    """实时视频稳定器"""

    def __init__(self, stabilization_params: StabilizationParams = None):
        self.params = stabilization_params or StabilizationParams()
        self.stabilizer = VideoStabilizer(StabilizationMethod.HYBRID)
        self.stabilizer.set_parameters(self.params)

        self.frame_buffer = deque(maxlen=self.params.smoothing_radius * 2)
        self.motion_buffer = deque(maxlen=self.params.smoothing_radius * 2)

    def stabilize_frame(self, frame: np.ndarray) -> np.ndarray:
        """稳定单帧"""
        # 添加到缓冲区
        self.frame_buffer.append(frame.copy())

        if len(self.frame_buffer) < self.params.smoothing_radius:
            return frame

        # 简化的实时稳定处理
        try:
            # 使用最近的帧进行运动估计
            recent_frames = list(self.frame_buffer)[-self.params.smoothing_radius:]

            # 估计当前帧的运动
            if len(recent_frames) >= 2:
                prev_frame = recent_frames[-2]
                curr_frame = recent_frames[-1]

                # 计算运动
                flow = cv2.calcOpticalFlowFarneback(
                    cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY),
                    cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY),
                    None, 0.5, 3, 15, 3, 5, 1.2, 0
                )

                # 计算平均运动
                dx = np.mean(flow[:, :, 0])
                dy = np.mean(flow[:, :, 1])

                # 应用运动补偿
                motion_compensation = np.eye(3)
                motion_compensation[0, 2] = -dx * 0.5  # 部分补偿
                motion_compensation[1, 2] = -dy * 0.5

                # 应用变换
                height, width = frame.shape[:2]
                stabilized_frame = cv2.warpPerspective(
                    frame, motion_compensation, (width, height),
                    flags=cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_REFLECT
                )

                return stabilized_frame

        except Exception as e:
            logging.warning(f"实时稳定失败: {e}")

        return frame


# 工具函数
def create_video_stabilizer(method: StabilizationMethod = StabilizationMethod.HYBRID) -> VideoStabilizer:
    """创建视频稳定器"""
    return VideoStabilizer(method)


def quick_stabilize_video(input_path: str, output_path: str) -> StabilizationResult:
    """快速视频稳定"""
    stabilizer = create_video_stabilizer()
    return stabilizer.stabilize_video(input_path, output_path)


def main():
    """主函数 - 用于测试"""
    # 创建视频稳定器
    stabilizer = create_video_stabilizer()

    # 测试稳定功能
    print("视频稳定器创建成功")
    print(f"稳定方法: {stabilizer.method.value}")


if __name__ == "__main__":
    main()