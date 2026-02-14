#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频处理服务

支持视频预处理、帧提取、时序分析、场景检测等
"""

from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import asyncio
from datetime import datetime, timedelta
import json

# 视频处理库
import cv2
import numpy as np


class VideoService:
    """
    视频处理服务

    功能:
    - 帧提取
    - 关键帧检测
    - 场景检测
    - 时序分析
    - 视频摘要
    - 运动分析
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化服务

        Args:
            config: 配置字典
        """
        self.config = config or {}

    def extract_frames(
        self,
        video_path: str,
        output_dir: str = None,
        interval: float = 1.0,
        max_frames: int = None,
        quality: int = 90,
        progress_callback: Callable[[int, int], None] = None,
    ) -> List[str]:
        """
        提取视频帧

        Args:
            video_path: 视频文件路径
            output_dir: 输出目录（默认：视频同目录/frames）
            interval: 提取间隔（秒）
            max_frames: 最大帧数
            quality: 图片质量 1-100
            progress_callback: 进度回调

        Returns:
            提取的帧文件路径列表
        """
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"无法打开视频文件: {video_path}")

        try:
            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0

            # 计算间隔帧数
            interval_frames = int(fps * interval) if fps > 0 else 30

            # 设置输出目录
            video_dir = Path(video_path).parent
            video_name = Path(video_path).stem
            if output_dir is None:
                output_dir = video_dir / f"{video_name}_frames"
            else:
                output_dir = Path(output_dir)

            output_dir.mkdir(parents=True, exist_ok=True)

            # 提取帧
            extracted_frames = []
            frame_idx = 0
            saved_count = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if max_frames and saved_count >= max_frames:
                    break

                # 按间隔提取
                if frame_idx % interval_frames == 0:
                    timestamp = frame_idx / fps if fps > 0 else 0

                    # 保存帧
                    frame_path = output_dir / f"frame_{saved_count:06d}_t{timestamp:.2f}s.jpg"
                    cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, quality])

                    extracted_frames.append(str(frame_path))
                    saved_count += 1

                    # 进度回调
                    if progress_callback:
                        progress_callback(frame_idx, total_frames)

                frame_idx += 1

            # 保存元数据
            metadata = {
                "video_path": video_path,
                "fps": fps,
                "total_frames": total_frames,
                "duration": duration,
                "interval": interval,
                "extracted_count": saved_count,
                "output_dir": str(output_dir),
                "extracted_at": datetime.now().isoformat(),
            }

            metadata_path = output_dir / "metadata.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            return extracted_frames

        finally:
            cap.release()

    def extract_key_frames(
        self,
        video_path: str,
        output_dir: str = None,
        threshold: float = 30.0,
        min_interval: int = 30,
        max_frames: int = 50,
        quality: int = 90,
    ) -> List[Dict[str, Any]]:
        """
        提取关键帧（基于场景变化）

        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            threshold: 场景变化阈值
            min_interval: 最小间隔帧数
            max_frames: 最大关键帧数
            quality: 图片质量

        Returns:
            关键帧信息列表
        """
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"无法打开视频文件: {video_path}")

        try:
            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)

            # 设置输出目录
            video_dir = Path(video_path).parent
            video_name = Path(video_path).stem
            if output_dir is None:
                output_dir = video_dir / f"{video_name}_keyframes"
            else:
                output_dir = Path(output_dir)

            output_dir.mkdir(parents=True, exist_ok=True)

            # 提取关键帧
            key_frames = []

            # 读取第一帧
            ret, prev_gray = cap.read()
            if not ret:
                return []

            # 转换为灰度
            prev_gray = cv2.cvtColor(prev_gray, cv2.COLOR_BGR2GRAY)

            frame_idx = 0
            key_frame_count = 0
            last_key_frame = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if max_frames and key_frame_count >= max_frames:
                    break

                frame_idx += 1

                # 检查最小间隔
                if frame_idx - last_key_frame < min_interval:
                    continue

                # 转换为灰度
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # 计算差异
                diff = cv2.absdiff(prev_gray, gray)
                diff_score = np.mean(diff)

                # 如果差异超过阈值，则提取关键帧
                if diff_score > threshold:
                    timestamp = frame_idx / fps if fps > 0 else 0

                    # 保存关键帧
                    frame_path = output_dir / f"keyframe_{key_frame_count:06d}_t{timestamp:.2f}s.jpg"
                    cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, quality])

                    key_frames.append({
                        "index": key_frame_count,
                        "frame_idx": frame_idx,
                        "timestamp": timestamp,
                        "path": str(frame_path),
                        "diff_score": diff_score,
                    })

                    key_frame_count += 1
                    last_key_frame = frame_idx
                    prev_gray = gray

            return key_frames

        finally:
            cap.release()

    def detect_scenes(
        self,
        video_path: str,
        threshold: float = 30.0,
        min_scene_duration: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """
        检测场景变化

        Args:
            video_path: 视频文件路径
            threshold: 场景变化阈值
            min_scene_duration: 最小场景持续时间（秒）

        Returns:
            场景列表
        """
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"无法打开视频文件: {video_path}")

        try:
            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)

            # 读取第一帧
            ret, prev_gray = cap.read()
            if not ret:
                return []

            prev_gray = cv2.cvtColor(prev_gray, cv2.COLOR_BGR2GRAY)

            scenes = []
            scene_start_idx = 0
            scene_count = 0

            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_idx += 1

                # 转换为灰度
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # 计算差异
                diff = cv2.absdiff(prev_gray, gray)
                diff_score = np.mean(diff)

                # 如果差异超过阈值，且持续时间足够
                if diff_score > threshold:
                    scene_start_time = scene_start_idx / fps if fps > 0 else 0
                    scene_end_time = frame_idx / fps if fps > 0 else 0
                    duration = scene_end_time - scene_start_time

                    if duration >= min_scene_duration:
                        scenes.append({
                            "id": scene_count,
                            "name": f"Scene {scene_count + 1}",
                            "start_frame": scene_start_idx,
                            "end_frame": frame_idx,
                            "start_time": scene_start_time,
                            "end_time": scene_end_time,
                            "duration": duration,
                            "change_threshold": diff_score,
                        })

                        scene_count += 1
                        scene_start_idx = frame_idx

                    prev_gray = gray

            # 添加最后一个场景
            scene_start_time = scene_start_idx / fps if fps > 0 else 0
            total_frames = frame_idx
            scene_end_time = total_frames / fps if fps > 0 else 0
            duration = scene_end_time - scene_start_time

            if duration >= min_scene_duration:
                scenes.append({
                    "id": scene_count,
                    "name": f"Scene {scene_count + 1}",
                    "start_frame": scene_start_idx,
                    "end_frame": total_frames,
                    "start_time": scene_start_time,
                    "end_time": scene_end_time,
                    "duration": duration,
                })

            return scenes

        finally:
            cap.release()

    def analyze_motion(
        self,
        video_path: str,
        frame_interval: int = 10,
    ) -> Dict[str, Any]:
        """
        分析运动

        Args:
            video_path: 视频文件路径
            frame_interval: 分析间隔帧数

        Returns:
            运动分析结果
        """
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"无法打开视频文件: {video_path}")

        try:
            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)

            # 读取第一帧
            ret, prev_frame = cap.read()
            if not ret:
                return {}

            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

            motion_scores = []
            frame_idx = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_idx += 1

                # 按间隔分析
                if frame_idx % frame_interval != 0:
                    continue

                # 转换为灰度
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # 计算光流（使用简单差异）
                diff = cv2.absdiff(prev_gray, gray)
                motion_score = np.mean(diff)
                motion_scores.append(motion_score)

                prev_gray = gray

            # 计算统计信息
            if motion_scores:
                avg_motion = np.mean(motion_scores)
                max_motion = np.max(motion_scores)
                min_motion = np.min(motion_scores)
                std_motion = np.std(motion_scores)

                return {
                    "fps": fps,
                    "total_frames": frame_idx,
                    "avg_motion": float(avg_motion),
                    "max_motion": float(max_motion),
                    "min_motion": float(min_motion),
                    "std_motion": float(std_motion),
                    "motion_timeline": motion_scores,
                    "frame_interval": frame_interval,
                }
            else:
                return {}

        finally:
            cap.release()

    def create_video_summary(
        self,
        video_path: str,
        output_path: str = None,
        key_frames: List[str] = None,
        duration_per_frame: float = 0.5,
        size: tuple = None,
    ) -> str:
        """
        创建视频摘要（从关键帧生成）

        Args:
            video_path: 原视频路径
            output_path: 输出路径
            key_frames: 关键帧图片路径列表
            duration_per_frame: 每帧显示时间（秒）
            size: 输出尺寸 (width, height)

        Returns:
            输出视频路径
        """
        # 设置输出路径
        if output_path is None:
            video_dir = Path(video_path).parent
            video_name = Path(video_path).stem
            output_path = video_dir / f"{video_name}_summary.mp4"

        # 使用关键帧创建摘要
        # 这里简化处理，实际应该使用更复杂的视频合成
        # 如 ffmpeg-python 或 moviepy

        # 读取第一帧获取尺寸
        if key_frames and len(key_frames) > 0:
            first_frame = cv2.imread(key_frames[0])
            if first_frame is not None:
                if size is None:
                    size = (first_frame.shape[1], first_frame.shape[0])
                else:
                    size = tuple(size[:2])

        # 实际实现需要视频编码器
        # 这里返回路径作为占位
        return str(output_path)

    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        获取视频信息

        Args:
            video_path: 视频文件路径

        Returns:
            视频信息字典
        """
        cap = cv2.VideoCapture(video_path)

        try:
            if not cap.isOpened():
                raise RuntimeError(f"无法打开视频文件: {video_path}")

            # 获取视频信息
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0

            return {
                "path": video_path,
                "width": width,
                "height": height,
                "fps": fps,
                "total_frames": total_frames,
                "duration": duration,
                "resolution": f"{width}x{height}",
                "format": Path(video_path).suffix,
            }
        finally:
            cap.release()

    async def extract_frames_async(
        self,
        video_path: str,
        output_dir: str = None,
        interval: float = 1.0,
        max_frames: int = None,
    ) -> List[str]:
        """
        异步提取视频帧

        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            interval: 提取间隔（秒）
            max_frames: 最大帧数

        Returns:
            提取的帧文件路径列表
        """
        # 在线程池中执行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.extract_frames(
                video_path, output_dir, interval, max_frames
            )
        )

    async def extract_key_frames_async(
        self,
        video_path: str,
        output_dir: str = None,
        threshold: float = 30.0,
        max_frames: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        异步提取关键帧

        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            threshold: 场景变化阈值
            max_frames: 最大关键帧数

        Returns:
            关键帧信息列表
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.extract_key_frames(
                video_path, output_dir, threshold, max_frames
            )
        )
