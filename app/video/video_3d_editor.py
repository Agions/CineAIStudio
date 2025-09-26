#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
专业级3D视频编辑系统
提供3D视频处理、立体编辑、深度图生成、3D特效等功能
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

try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
except ImportError:
    OPEN3D_AVAILABLE = False
    print("警告: Open3D未安装，3D点云处理功能将被限制")

try:
    from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
    from PyQt6.QtCore import pyqtSignal as Signal
except ImportError:
    try:
        from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread
        from PyQt5.QtCore import pyqtSignal as Signal
    except ImportError:
        try:
            from PySide2.QtCore import QObject, Signal, QTimer, QThread
        except ImportError:
            try:
                from PySide6.QtCore import QObject, Signal, QTimer, QThread
            except ImportError:
                class Signal:
                    def __init__(self, *args, **kwargs):
                        pass
                class QObject:
                    def __init__(self):
                        pass
                class QTimer:
                    def __init__(self):
                        pass
                class QThread:
                    def __init__(self):
                        pass


class StereoFormat(Enum):
    """立体视频格式"""
    SIDE_BY_SIDE = "side_by_side"        # 左右并列
    TOP_BOTTOM = "top_bottom"            # 上下排列
    ANAGLYPH = "anaglyph"               # 红青立体
    INTERLACED = "interlaced"           # 隔行扫描
    FRAME_SEQUENTIAL = "frame_sequential"  # 帧序列
    MONO_DEPTH = "mono_depth"           # 单目深度


class DepthEstimationMethod(Enum):
    """深度估计方法"""
    STEREO_MATCHING = "stereo_matching"  # 立体匹配
    MONOCULAR_DEPTH = "monocular_depth"  # 单目深度估计
    DEEP_LEARNING = "deep_learning"      # 深度学习
    MANUAL = "manual"                    # 手动调整


class Effect3DType(Enum):
    """3D特效类型"""
    DEPTH_OF_FIELD = "depth_of_field"    # 景深效果
    PARALLAX = "parallax"               # 视差效果
    FLOATING = "floating"               # 悬浮效果
    ROTATION_3D = "rotation_3d"         # 3D旋转
    ZOOM_3D = "zoom_3d"                 # 3D缩放
    WARP_3D = "warp_3d"                 # 3D扭曲
    PARTICLE_3D = "particle_3d"          # 3D粒子


@dataclass
class StereoFrame:
    """立体帧"""
    left_frame: np.ndarray
    right_frame: np.ndarray
    depth_map: Optional[np.ndarray] = None
    disparity_map: Optional[np.ndarray] = None
    timestamp: float = 0.0


@dataclass
class CameraParameters:
    """相机参数"""
    focal_length: float
    baseline: float
    cx: float
    cy: float
    image_width: int
    image_height: int


@dataclass
class Effect3D:
    """3D特效"""
    effect_type: Effect3DType
    parameters: Dict[str, Any]
    enabled: bool = True
    intensity: float = 1.0


class StereoMatcher:
    """立体匹配器"""

    def __init__(self, method: str = "SGBM"):
        self.method = method
        self.matcher = self._create_matcher()

    def _create_matcher(self):
        """创建匹配器"""
        if self.method == "SGBM":
            return cv2.StereoSGBM_create(
                minDisparity=0,
                numDisparities=64,
                blockSize=7,
                P1=8 * 3 * 7 ** 2,
                P2=32 * 3 * 7 ** 2,
                disp12MaxDiff=1,
                uniquenessRatio=15,
                speckleWindowSize=100,
                speckleRange=32
            )
        elif self.method == "BM":
            return cv2.StereoBM_create(numDisparities=64, blockSize=7)
        else:
            return cv2.StereoSGBM_create()

    def compute_disparity(self, left_frame: np.ndarray, right_frame: np.ndarray) -> np.ndarray:
        """计算视差图"""
        # 转换为灰度图
        if len(left_frame.shape) == 3:
            left_gray = cv2.cvtColor(left_frame, cv2.COLOR_BGR2GRAY)
            right_gray = cv2.cvtColor(right_frame, cv2.COLOR_BGR2GRAY)
        else:
            left_gray = left_frame
            right_gray = right_frame

        # 计算视差
        disparity = self.matcher.compute(left_gray, right_gray)

        # 归一化视差
        disparity = cv2.normalize(disparity, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

        return disparity

    def compute_depth(self, disparity: np.ndarray, camera_params: CameraParameters) -> np.ndarray:
        """计算深度图"""
        # 避免除零错误
        disparity_safe = np.where(disparity == 0, 0.1, disparity.astype(np.float32))

        # 计算深度
        depth = (camera_params.focal_length * camera_params.baseline) / disparity_safe

        return depth


class DepthEstimator:
    """深度估计器"""

    def __init__(self, method: DepthEstimationMethod = DepthEstimationMethod.MONOCULAR_DEPTH):
        self.method = method
        self.model = None

        if method == DepthEstimationMethod.DEEP_LEARNING:
            self._load_depth_model()

    def _load_depth_model(self):
        """加载深度模型"""
        try:
            # 加载MiDaS深度估计模型
            self.model = cv2.dnn.readNetFromTensorflow(
                "model-f6b98070.onnx"  # MiDaS模型文件
            )
        except Exception:
            print("深度模型加载失败，使用传统方法")
            self.method = DepthEstimationMethod.MONOCULAR_DEPTH

    def estimate_depth(self, frame: np.ndarray) -> np.ndarray:
        """估计深度"""
        if self.method == DepthEstimationMethod.STEREO_MATCHING:
            return self._estimate_from_stereo(frame)
        elif self.method == DepthEstimationMethod.DEEP_LEARNING and self.model is not None:
            return self._estimate_with_deep_learning(frame)
        else:
            return self._estimate_monocular_depth(frame)

    def _estimate_from_stereo(self, frame: np.ndarray) -> np.ndarray:
        """从立体图像估计深度"""
        # 假设输入是并排立体图像
        height, width = frame.shape[:2]
        mid = width // 2

        left_frame = frame[:, :mid]
        right_frame = frame[:, mid:]

        matcher = StereoMatcher()
        disparity = matcher.compute_disparity(left_frame, right_frame)

        # 假设的相机参数
        camera_params = CameraParameters(
            focal_length=width,
            baseline=0.1,
            cx=width/4,
            cy=height/2,
            image_width=mid,
            image_height=height
        )

        return matcher.compute_depth(disparity, camera_params)

    def _estimate_with_deep_learning(self, frame: np.ndarray) -> np.ndarray:
        """使用深度学习估计深度"""
        try:
            # 预处理图像
            input_blob = cv2.dnn.blobFromImage(
                frame, 1/255.0, (384, 384), (0.485, 0.456, 0.406), swapRB=True
            )

            # 推理
            self.model.setInput(input_blob)
            depth_map = self.model.forward()

            # 后处理
            depth_map = np.squeeze(depth_map)
            depth_map = cv2.resize(depth_map, (frame.shape[1], frame.shape[0]))

            return depth_map

        except Exception as e:
            logging.error(f"深度学习深度估计失败: {e}")
            return self._estimate_monocular_depth(frame)

    def _estimate_monocular_depth(self, frame: np.ndarray) -> np.ndarray:
        """单目深度估计"""
        # 基于图像特征的传统深度估计
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        # 计算图像梯度
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)

        # 基于梯度的深度估计（梯度大的地方通常深度变化大）
        depth_map = 1.0 / (1.0 + gradient_magnitude / 100.0)

        # 应用高斯模糊平滑
        depth_map = cv2.GaussianBlur(depth_map, (5, 5), 0)

        return depth_map


class StereoConverter:
    """立体转换器"""

    def __init__(self):
        self.camera_params = None

    def convert_to_stereo(self, frame: np.ndarray, depth_map: np.ndarray,
                        target_format: StereoFormat = StereoFormat.SIDE_BY_SIDE) -> StereoFrame:
        """转换为立体视频"""
        # 生成左右视图
        left_frame, right_frame = self._generate_stereo_views(frame, depth_map)

        return StereoFrame(
            left_frame=left_frame,
            right_frame=right_frame,
            depth_map=depth_map,
            timestamp=time.time()
        )

    def _generate_stereo_views(self, frame: np.ndarray, depth_map: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """生成立体视图"""
        height, width = frame.shape[:2]

        # 计算视差
        max_disparity = width // 10  # 最大视差为图像宽度的1/10
        disparity = (depth_map - np.min(depth_map)) / (np.max(depth_map) - np.min(depth_map))
        disparity = disparity * max_disparity

        # 生成左右视图
        left_frame = frame.copy()
        right_frame = frame.copy()

        # 应用视差位移
        for y in range(height):
            for x in range(width):
                d = int(disparity[y, x])
                if x + d < width:
                    right_frame[y, x + d] = frame[y, x]

        return left_frame, right_frame

    def convert_from_stereo(self, stereo_frame: StereoFrame,
                           source_format: StereoFormat) -> np.ndarray:
        """从立体视频转换"""
        if source_format == StereoFormat.SIDE_BY_SIDE:
            return self._convert_side_by_side_to_mono(stereo_frame)
        elif source_format == StereoFormat.TOP_BOTTOM:
            return self._convert_top_bottom_to_mono(stereo_frame)
        elif source_format == StereoFormat.ANAGLYPH:
            return self._convert_anaglyph_to_mono(stereo_frame)
        else:
            return stereo_frame.left_frame

    def _convert_side_by_side_to_mono(self, stereo_frame: StereoFrame) -> np.ndarray:
        """转换左右并列为单目"""
        return np.hstack((stereo_frame.left_frame, stereo_frame.right_frame))

    def _convert_top_bottom_to_mono(self, stereo_frame: StereoFrame) -> np.ndarray:
        """转换上下排列为单目"""
        return np.vstack((stereo_frame.left_frame, stereo_frame.right_frame))

    def _convert_anaglyph_to_mono(self, stereo_frame: StereoFrame) -> np.ndarray:
        """转换红青立体为单目"""
        left = stereo_frame.left_frame
        right = stereo_frame.right_frame

        # 提取颜色通道
        if len(left.shape) == 3:
            anaglyph = np.zeros_like(left)
            anaglyph[:, :, 0] = left[:, :, 0]    # 红色通道来自左图像
            anaglyph[:, :, 1] = right[:, :, 1]  # 绿色通道来自右图像
            anaglyph[:, :, 2] = right[:, :, 2]  # 蓝色通道来自右图像
            return anaglyph
        else:
            return left


class Effect3DProcessor:
    """3D特效处理器"""

    def __init__(self):
        self.effects = []

    def add_effect(self, effect: Effect3D):
        """添加3D特效"""
        self.effects.append(effect)

    def remove_effect(self, effect_type: Effect3DType):
        """移除3D特效"""
        self.effects = [e for e in self.effects if e.effect_type != effect_type]

    def apply_effects(self, stereo_frame: StereoFrame) -> StereoFrame:
        """应用3D特效"""
        processed_frame = stereo_frame

        for effect in self.effects:
            if effect.enabled:
                processed_frame = self._apply_single_effect(processed_frame, effect)

        return processed_frame

    def _apply_single_effect(self, stereo_frame: StereoFrame, effect: Effect3D) -> StereoFrame:
        """应用单个3D特效"""
        if effect.effect_type == Effect3DType.DEPTH_OF_FIELD:
            return self._apply_depth_of_field(stereo_frame, effect)
        elif effect.effect_type == Effect3DType.PARALLAX:
            return self._apply_parallax(stereo_frame, effect)
        elif effect.effect_type == Effect3DType.FLOATING:
            return self._apply_floating(stereo_frame, effect)
        elif effect.effect_type == Effect3DType.ROTATION_3D:
            return self._apply_3d_rotation(stereo_frame, effect)
        elif effect.effect_type == Effect3DType.ZOOM_3D:
            return self._apply_3d_zoom(stereo_frame, effect)
        else:
            return stereo_frame

    def _apply_depth_of_field(self, stereo_frame: StereoFrame, effect: Effect3D) -> StereoFrame:
        """应用景深效果"""
        if stereo_frame.depth_map is None:
            return stereo_frame

        depth_map = stereo_frame.depth_map
        focus_depth = effect.parameters.get("focus_depth", 0.5)
        blur_amount = effect.parameters.get("blur_amount", 5)

        # 归一化深度图
        depth_normalized = (depth_map - np.min(depth_map)) / (np.max(depth_map) - np.min(depth_map))

        # 创建模糊蒙版
        blur_mask = np.abs(depth_normalized - focus_depth)
        blur_mask = blur_mask / np.max(blur_mask)

        # 应用景深模糊
        left_blurred = cv2.GaussianBlur(stereo_frame.left_frame, (blur_amount*2+1, blur_amount*2+1), 0)
        right_blurred = cv2.GaussianBlur(stereo_frame.right_frame, (blur_amount*2+1, blur_amount*2+1), 0)

        # 混合原始图像和模糊图像
        for i in range(3):  # 对每个颜色通道
            stereo_frame.left_frame[:, :, i] = (
                stereo_frame.left_frame[:, :, i] * (1 - blur_mask) +
                left_blurred[:, :, i] * blur_mask
            )
            stereo_frame.right_frame[:, :, i] = (
                stereo_frame.right_frame[:, :, i] * (1 - blur_mask) +
                right_blurred[:, :, i] * blur_mask
            )

        return stereo_frame

    def _apply_parallax(self, stereo_frame: StereoFrame, effect: Effect3D) -> StereoFrame:
        """应用视差效果"""
        parallax_amount = effect.parameters.get("parallax_amount", 10)

        if stereo_frame.depth_map is None:
            return stereo_frame

        depth_map = stereo_frame.depth_map
        height, width = depth_map.shape

        # 基于深度计算视差位移
        depth_normalized = (depth_map - np.min(depth_map)) / (np.max(depth_map) - np.min(depth_map))
        disparity_map = depth_normalized * parallax_amount

        # 应用视差位移
        left_result = stereo_frame.left_frame.copy()
        right_result = stereo_frame.right_frame.copy()

        for y in range(height):
            for x in range(width):
                shift = int(disparity_map[y, x])
                if 0 <= x + shift < width:
                    right_result[y, x] = stereo_frame.right_frame[y, x + shift]
                if 0 <= x - shift < width:
                    left_result[y, x] = stereo_frame.left_frame[y, x - shift]

        stereo_frame.left_frame = left_result
        stereo_frame.right_frame = right_result

        return stereo_frame

    def _apply_floating(self, stereo_frame: StereoFrame, effect: Effect3D) -> StereoFrame:
        """应用悬浮效果"""
        float_amount = effect.parameters.get("float_amount", 5)
        frequency = effect.parameters.get("frequency", 0.1)

        # 计算悬浮偏移
        time_offset = time.time() * frequency * 2 * np.pi
        offset_x = int(np.sin(time_offset) * float_amount)
        offset_y = int(np.cos(time_offset * 0.7) * float_amount)

        # 应用偏移
        height, width = stereo_frame.left_frame.shape[:2]

        # 平移图像
        M = np.float32([[1, 0, offset_x], [0, 1, offset_y]])
        stereo_frame.left_frame = cv2.warpAffine(stereo_frame.left_frame, M, (width, height))
        stereo_frame.right_frame = cv2.warpAffine(stereo_frame.right_frame, M, (width, height))

        return stereo_frame

    def _apply_3d_rotation(self, stereo_frame: StereoFrame, effect: Effect3D) -> StereoFrame:
        """应用3D旋转效果"""
        angle_x = effect.parameters.get("angle_x", 10)
        angle_y = effect.parameters.get("angle_y", 0)
        angle_z = effect.parameters.get("angle_z", 0)

        # 转换为弧度
        angle_x_rad = np.radians(angle_x)
        angle_y_rad = np.radians(angle_y)
        angle_z_rad = np.radians(angle_z)

        height, width = stereo_frame.left_frame.shape[:2]
        center = (width // 2, height // 2)

        # 3D旋转矩阵
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(angle_x_rad), -np.sin(angle_x_rad)],
            [0, np.sin(angle_x_rad), np.cos(angle_x_rad)]
        ])

        Ry = np.array([
            [np.cos(angle_y_rad), 0, np.sin(angle_y_rad)],
            [0, 1, 0],
            [-np.sin(angle_y_rad), 0, np.cos(angle_y_rad)]
        ])

        Rz = np.array([
            [np.cos(angle_z_rad), -np.sin(angle_z_rad), 0],
            [np.sin(angle_z_rad), np.cos(angle_z_rad), 0],
            [0, 0, 1]
        ])

        R = Rz @ Ry @ Rx

        # 应用旋转
        for frame in [stereo_frame.left_frame, stereo_frame.right_frame]:
            # 简化的2D投影
            M = cv2.getRotationMatrix2D(center, angle_z, 1.0)
            frame[:] = cv2.warpAffine(frame, M, (width, height))

        return stereo_frame

    def _apply_3d_zoom(self, stereo_frame: StereoFrame, effect: Effect3D) -> StereoFrame:
        """应用3D缩放效果"""
        zoom_factor = effect.parameters.get("zoom_factor", 1.2)
        zoom_center = effect.parameters.get("zoom_center", [0.5, 0.5])

        height, width = stereo_frame.left_frame.shape[:2]
        center_x = int(width * zoom_center[0])
        center_y = int(height * zoom_center[1])

        # 创建缩放矩阵
        M = cv2.getRotationMatrix2D((center_x, center_y), 0, zoom_factor)

        # 应用缩放
        stereo_frame.left_frame = cv2.warpAffine(stereo_frame.left_frame, M, (width, height))
        stereo_frame.right_frame = cv2.warpAffine(stereo_frame.right_frame, M, (width, height))

        return stereo_frame


class PointCloudGenerator:
    """点云生成器"""

    def __init__(self):
        self.open3d_available = OPEN3D_AVAILABLE

    def generate_point_cloud(self, frame: np.ndarray, depth_map: np.ndarray,
                           camera_params: CameraParameters) -> Optional[Any]:
        """生成点云"""
        if not self.open3d_available:
            return None

        try:
            height, width = depth_map.shape

            # 创建像素坐标网格
            u, v = np.meshgrid(np.arange(width), np.arange(height))

            # 转换为相机坐标系
            fx, fy = camera_params.focal_length, camera_params.focal_length
            cx, cy = camera_params.cx, camera_params.cy

            # 计算3D坐标
            z = depth_map
            x = (u - cx) * z / fx
            y = (v - cy) * z / fy

            # 重塑点云
            points = np.stack([x.flatten(), y.flatten(), z.flatten()], axis=1)

            # 移除无效点
            valid_mask = z.flatten() > 0
            points = points[valid_mask]

            # 获取颜色
            if len(frame.shape) == 3:
                colors = frame.reshape(-1, 3)[valid_mask]
            else:
                colors = np.ones((len(points), 3)) * 128

            # 创建Open3D点云
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(points)
            pcd.colors = o3d.utility.Vector3dVector(colors / 255.0)

            return pcd

        except Exception as e:
            logging.error(f"点云生成失败: {e}")
            return None

    def save_point_cloud(self, point_cloud, filename: str):
        """保存点云"""
        if self.open3d_available and point_cloud is not None:
            o3d.io.write_point_cloud(filename, point_cloud)


class Video3DEditor(QObject):
    """3D视频编辑器主类"""

    # 信号定义
    processing_started = Signal(str)  # 处理开始
    processing_progress = Signal(int, str)  # 处理进度
    processing_completed = Signal(str, str)  # 处理完成
    processing_error = Signal(str)  # 处理错误
    stereo_generated = Signal(StereoFrame)  # 立体帧生成
    depth_estimated = Signal(np.ndarray)  # 深度估计完成

    def __init__(self):
        super().__init__()
        self.depth_estimator = DepthEstimator()
        self.stereo_converter = StereoConverter()
        self.effect_processor = Effect3DProcessor()
        self.point_cloud_generator = PointCloudGenerator()

        self.is_processing = False
        self.processing_thread = None

        self.camera_params = CameraParameters(
            focal_length=800,
            baseline=0.1,
            cx=320,
            cy=240,
            image_width=640,
            image_height=480
        )

    def set_camera_parameters(self, params: CameraParameters):
        """设置相机参数"""
        self.camera_params = params

    def estimate_depth_async(self, frame: np.ndarray,
                           method: DepthEstimationMethod = DepthEstimationMethod.MONOCULAR_DEPTH):
        """异步深度估计"""
        if self.is_processing:
            self.processing_error.emit("正在处理中，请等待完成")
            return

        self.is_processing = True
        self.processing_started.emit("深度估计")

        # 创建处理线程
        self.processing_thread = DepthEstimationThread(
            self.depth_estimator, frame, method
        )
        self.processing_thread.progress_updated.connect(self.processing_progress.emit)
        self.processing_thread.depth_estimated.connect(self._on_depth_estimated)
        self.processing_thread.error_occurred.connect(self.processing_error.emit)
        self.processing_thread.start()

    def _on_depth_estimated(self, depth_map: np.ndarray):
        """深度估计完成回调"""
        self.is_processing = False
        self.depth_estimated.emit(depth_map)

    def generate_stereo_async(self, frame: np.ndarray, depth_map: np.ndarray = None,
                            target_format: StereoFormat = StereoFormat.SIDE_BY_SIDE):
        """异步生成立体视频"""
        if depth_map is None:
            # 如果没有提供深度图，先估计深度
            self.estimate_depth_async(frame)
            return

        if self.is_processing:
            self.processing_error.emit("正在处理中，请等待完成")
            return

        self.is_processing = True
        self.processing_started.emit("立体视频生成")

        # 创建处理线程
        self.processing_thread = StereoGenerationThread(
            self.stereo_converter, frame, depth_map, target_format
        )
        self.processing_thread.progress_updated.connect(self.processing_progress.emit)
        self.processing_thread.stereo_generated.connect(self._on_stereo_generated)
        self.processing_thread.error_occurred.connect(self.processing_error.emit)
        self.processing_thread.start()

    def _on_stereo_generated(self, stereo_frame: StereoFrame):
        """立体视频生成完成回调"""
        self.is_processing = False
        self.stereo_generated.emit(stereo_frame)

    def process_3d_video_async(self, input_path: str, output_path: str,
                             effects: List[Effect3D] = None,
                             target_format: StereoFormat = StereoFormat.SIDE_BY_SIDE):
        """异步处理3D视频"""
        if self.is_processing:
            self.processing_error.emit("正在处理中，请等待完成")
            return

        self.is_processing = True
        self.processing_started.emit(input_path)

        # 设置特效
        if effects:
            self.effect_processor.effects = effects

        # 创建处理线程
        self.processing_thread = Video3DProcessingThread(
            self, input_path, output_path, target_format
        )
        self.processing_thread.progress_updated.connect(self.processing_progress.emit)
        self.processing_thread.processing_completed.connect(self._on_processing_completed)
        self.processing_thread.error_occurred.connect(self.processing_error.emit)
        self.processing_thread.start()

    def _on_processing_completed(self, input_path: str, output_path: str):
        """处理完成回调"""
        self.is_processing = False
        self.processing_completed.emit(input_path, output_path)

    def add_3d_effect(self, effect: Effect3D):
        """添加3D特效"""
        self.effect_processor.add_effect(effect)

    def remove_3d_effect(self, effect_type: Effect3DType):
        """移除3D特效"""
        self.effect_processor.remove_effect(effect_type)

    def generate_point_cloud_from_frame(self, frame: np.ndarray, depth_map: np.ndarray):
        """从帧生成点云"""
        return self.point_cloud_generator.generate_point_cloud(
            frame, depth_map, self.camera_params
        )

    def stop_processing(self):
        """停止处理"""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.stop()
            self.is_processing = False


class DepthEstimationThread(QThread):
    """深度估计线程"""

    progress_updated = Signal(int, str)
    depth_estimated = Signal(np.ndarray)
    error_occurred = Signal(str)

    def __init__(self, depth_estimator: DepthEstimator, frame: np.ndarray,
                 method: DepthEstimationMethod):
        super().__init__()
        self.depth_estimator = depth_estimator
        self.frame = frame
        self.method = method
        self._is_running = True

    def run(self):
        """运行深度估计"""
        try:
            self.progress_updated.emit(30, "正在估计深度...")

            # 估计深度
            depth_map = self.depth_estimator.estimate_depth(self.frame)

            if not self._is_running:
                return

            self.progress_updated.emit(100, "深度估计完成")
            self.depth_estimated.emit(depth_map)

        except Exception as e:
            self.error_occurred.emit(f"深度估计失败: {str(e)}")

    def stop(self):
        """停止线程"""
        self._is_running = False
        self.wait()


class StereoGenerationThread(QThread):
    """立体生成线程"""

    progress_updated = Signal(int, str)
    stereo_generated = Signal(StereoFrame)
    error_occurred = Signal(str)

    def __init__(self, stereo_converter: StereoConverter, frame: np.ndarray,
                 depth_map: np.ndarray, target_format: StereoFormat):
        super().__init__()
        self.stereo_converter = stereo_converter
        self.frame = frame
        self.depth_map = depth_map
        self.target_format = target_format
        self._is_running = True

    def run(self):
        """运行立体生成"""
        try:
            self.progress_updated.emit(30, "正在生成立体视图...")

            # 生成立体帧
            stereo_frame = self.stereo_converter.convert_to_stereo(
                self.frame, self.depth_map, self.target_format
            )

            if not self._is_running:
                return

            self.progress_updated.emit(100, "立体视频生成完成")
            self.stereo_generated.emit(stereo_frame)

        except Exception as e:
            self.error_occurred.emit(f"立体视频生成失败: {str(e)}")

    def stop(self):
        """停止线程"""
        self._is_running = False
        self.wait()


class Video3DProcessingThread(QThread):
    """3D视频处理线程"""

    progress_updated = Signal(int, str)
    processing_completed = Signal(str, str)
    error_occurred = Signal(str)

    def __init__(self, editor: Video3DEditor, input_path: str, output_path: str,
                 target_format: StereoFormat):
        super().__init__()
        self.editor = editor
        self.input_path = input_path
        self.output_path = output_path
        self.target_format = target_format
        self._is_running = True

    def run(self):
        """运行3D视频处理"""
        try:
            cap = cv2.VideoCapture(self.input_path)
            if not cap.isOpened():
                self.error_occurred.emit(f"无法打开视频文件: {self.input_path}")
                return

            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            if self.target_format == StereoFormat.SIDE_BY_SIDE:
                out_width = width * 2
                out_height = height
            elif self.target_format == StereoFormat.TOP_BOTTOM:
                out_width = width
                out_height = height * 2
            else:
                out_width = width
                out_height = height

            out = cv2.VideoWriter(self.output_path, fourcc, fps, (out_width, out_height))

            frame_count = 0

            while cap.isOpened() and self._is_running:
                ret, frame = cap.read()
                if not ret:
                    break

                # 深度估计
                depth_map = self.editor.depth_estimator.estimate_depth(frame)

                # 生成立体帧
                stereo_frame = self.editor.stereo_converter.convert_to_stereo(
                    frame, depth_map, self.target_format
                )

                # 应用3D特效
                stereo_frame = self.editor.effect_processor.apply_effects(stereo_frame)

                # 转换为输出格式
                if self.target_format == StereoFormat.SIDE_BY_SIDE:
                    output_frame = np.hstack((stereo_frame.left_frame, stereo_frame.right_frame))
                elif self.target_format == StereoFormat.TOP_BOTTOM:
                    output_frame = np.vstack((stereo_frame.left_frame, stereo_frame.right_frame))
                else:
                    output_frame = stereo_frame.left_frame

                # 写入帧
                out.write(output_frame)
                frame_count += 1

                # 更新进度
                progress = int((frame_count / total_frames) * 100)
                self.progress_updated.emit(progress, f"处理中... {frame_count}/{total_frames}")

            cap.release()
            out.release()

            self.progress_updated.emit(100, "处理完成")
            self.processing_completed.emit(self.input_path, self.output_path)

        except Exception as e:
            self.error_occurred.emit(f"3D视频处理失败: {str(e)}")

    def stop(self):
        """停止线程"""
        self._is_running = False
        self.wait()


# 工具函数
def create_3d_editor() -> Video3DEditor:
    """创建3D视频编辑器"""
    return Video3DEditor()


def quick_convert_to_3d(input_path: str, output_path: str,
                        format_type: StereoFormat = StereoFormat.SIDE_BY_SIDE) -> bool:
    """快速转换为3D视频"""
    editor = create_3d_editor()

    try:
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            return False

        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if format_type == StereoFormat.SIDE_BY_SIDE:
            out_width = width * 2
            out_height = height
        elif format_type == StereoFormat.TOP_BOTTOM:
            out_width = width
            out_height = height * 2
        else:
            out_width = width
            out_height = height

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (out_width, out_height))

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # 估计深度
            depth_map = editor.depth_estimator.estimate_depth(frame)

            # 生成立体帧
            stereo_frame = editor.stereo_converter.convert_to_stereo(
                frame, depth_map, format_type
            )

            # 转换为输出格式
            if format_type == StereoFormat.SIDE_BY_SIDE:
                output_frame = np.hstack((stereo_frame.left_frame, stereo_frame.right_frame))
            elif format_type == StereoFormat.TOP_BOTTOM:
                output_frame = np.vstack((stereo_frame.left_frame, stereo_frame.right_frame))
            else:
                output_frame = stereo_frame.left_frame

            out.write(output_frame)

        cap.release()
        out.release()
        return True

    except Exception as e:
        logging.error(f"3D转换失败: {e}")
        return False


def main():
    """主函数 - 用于测试"""
    # 创建3D视频编辑器
    editor = create_3d_editor()

    # 测试3D编辑功能
    print("3D视频编辑器创建成功")
    print(f"深度估计方法: {editor.depth_estimator.method.value}")
    print(f"Open3D可用: {OPEN3D_AVAILABLE}")


if __name__ == "__main__":
    main()