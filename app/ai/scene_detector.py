#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import asyncio
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal

from app.core.video_manager import VideoClip


@dataclass
class SceneInfo:
    """场景信息"""
    start_time: float  # 开始时间（秒）
    end_time: float    # 结束时间（秒）
    scene_type: str    # 场景类型
    confidence: float  # 置信度
    description: str   # 场景描述
    thumbnail_path: Optional[str] = None  # 缩略图路径
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SceneDetector(QObject):
    """智能场景检测器"""
    
    # 信号
    scene_detected = pyqtSignal(SceneInfo)  # 检测到场景
    detection_progress = pyqtSignal(int)    # 检测进度
    detection_completed = pyqtSignal(list)  # 检测完成
    
    def __init__(self):
        super().__init__()
        
        # 检测参数
        self.motion_threshold = 0.3      # 运动检测阈值
        self.scene_change_threshold = 0.5 # 场景变化阈值
        self.min_scene_duration = 1.0    # 最小场景时长（秒）
        self.max_scene_duration = 30.0   # 最大场景时长（秒）
        
        # 场景类型定义
        self.scene_types = {
            "high_energy": "高能场景",
            "dialogue": "对话场景", 
            "emotional": "情感场景",
            "action": "动作场景",
            "quiet": "安静场景",
            "transition": "转场场景"
        }
    
    async def detect_scenes(self, video: VideoClip) -> List[SceneInfo]:
        """检测视频中的场景"""
        if not video.file_path or not cv2.os.path.exists(video.file_path):
            return []
        
        scenes = []
        cap = cv2.VideoCapture(video.file_path)
        
        try:
            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            if duration <= 0:
                return []
            
            # 检测场景变化点
            scene_changes = await self._detect_scene_changes(cap, fps, total_frames)
            
            # 分析每个场景
            for i, (start_frame, end_frame) in enumerate(scene_changes):
                start_time = start_frame / fps
                end_time = end_frame / fps
                
                # 分析场景类型
                scene_type, confidence = await self._analyze_scene_type(
                    cap, start_frame, end_frame, fps
                )
                
                # 创建场景信息
                scene = SceneInfo(
                    start_time=start_time,
                    end_time=end_time,
                    scene_type=scene_type,
                    confidence=confidence,
                    description=self._generate_scene_description(scene_type, start_time, end_time),
                    metadata={
                        "start_frame": start_frame,
                        "end_frame": end_frame,
                        "duration": end_time - start_time
                    }
                )
                
                scenes.append(scene)
                self.scene_detected.emit(scene)
                
                # 更新进度
                progress = int((i + 1) / len(scene_changes) * 100)
                self.detection_progress.emit(progress)
                
                # 让出控制权，避免阻塞UI
                await asyncio.sleep(0.01)
            
            self.detection_completed.emit(scenes)
            return scenes
            
        except Exception as e:
            print(f"场景检测失败: {e}")
            return []
        finally:
            cap.release()
    
    async def _detect_scene_changes(self, cap: cv2.VideoCapture, fps: float, total_frames: int) -> List[Tuple[int, int]]:
        """检测场景变化点"""
        scene_changes = []
        prev_frame = None
        scene_start = 0
        
        # 采样间隔（每秒采样几帧）
        sample_interval = max(1, int(fps / 5))  # 每秒采样5帧
        
        for frame_idx in range(0, total_frames, sample_interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # 转换为灰度图
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (320, 240))  # 降低分辨率加速处理
            
            if prev_frame is not None:
                # 计算帧间差异
                diff = cv2.absdiff(prev_frame, gray)
                diff_score = np.mean(diff) / 255.0
                
                # 检测场景变化
                if diff_score > self.scene_change_threshold:
                    # 检查场景时长
                    scene_duration = (frame_idx - scene_start) / fps
                    if scene_duration >= self.min_scene_duration:
                        scene_changes.append((scene_start, frame_idx))
                        scene_start = frame_idx
            
            prev_frame = gray
            
            # 让出控制权
            if frame_idx % (sample_interval * 10) == 0:
                await asyncio.sleep(0.001)
        
        # 添加最后一个场景
        if scene_start < total_frames:
            scene_duration = (total_frames - scene_start) / fps
            if scene_duration >= self.min_scene_duration:
                scene_changes.append((scene_start, total_frames))
        
        return scene_changes
    
    async def _analyze_scene_type(self, cap: cv2.VideoCapture, start_frame: int, end_frame: int, fps: float) -> Tuple[str, float]:
        """分析场景类型"""
        # 采样几帧进行分析
        sample_frames = min(10, end_frame - start_frame)
        frame_interval = max(1, (end_frame - start_frame) // sample_frames)
        
        motion_scores = []
        brightness_scores = []
        
        for i in range(sample_frames):
            frame_idx = start_frame + i * frame_interval
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            
            if not ret:
                continue
            
            # 转换为灰度图
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (320, 240))
            
            # 计算运动强度（使用光流法的简化版本）
            if i > 0:
                motion_score = self._calculate_motion_score(prev_gray, gray)
                motion_scores.append(motion_score)
            
            # 计算亮度
            brightness = np.mean(gray) / 255.0
            brightness_scores.append(brightness)
            
            prev_gray = gray
        
        # 分析场景特征
        avg_motion = np.mean(motion_scores) if motion_scores else 0
        avg_brightness = np.mean(brightness_scores) if brightness_scores else 0
        scene_duration = (end_frame - start_frame) / fps
        
        # 场景分类逻辑
        if avg_motion > 0.7:
            return "action", 0.8
        elif avg_motion > 0.4:
            return "high_energy", 0.7
        elif scene_duration < 3.0 and avg_motion > 0.2:
            return "transition", 0.6
        elif avg_brightness < 0.3:
            return "emotional", 0.6
        elif scene_duration > 10.0 and avg_motion < 0.2:
            return "dialogue", 0.7
        else:
            return "quiet", 0.5
    
    def _calculate_motion_score(self, prev_frame: np.ndarray, curr_frame: np.ndarray) -> float:
        """计算运动分数"""
        # 使用简单的帧差法
        diff = cv2.absdiff(prev_frame, curr_frame)
        motion_score = np.mean(diff) / 255.0
        return motion_score
    
    def _generate_scene_description(self, scene_type: str, start_time: float, end_time: float) -> str:
        """生成场景描述"""
        type_name = self.scene_types.get(scene_type, scene_type)
        duration = end_time - start_time
        
        start_min = int(start_time // 60)
        start_sec = int(start_time % 60)
        end_min = int(end_time // 60)
        end_sec = int(end_time % 60)
        
        return f"{type_name} ({start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}, {duration:.1f}秒)"
    
    async def detect_highlights(self, video: VideoClip) -> List[SceneInfo]:
        """检测视频亮点"""
        scenes = await self.detect_scenes(video)
        
        # 筛选高能场景和动作场景作为亮点
        highlights = []
        for scene in scenes:
            if scene.scene_type in ["high_energy", "action"] and scene.confidence > 0.6:
                highlights.append(scene)
        
        return highlights
    
    async def detect_emotional_moments(self, video: VideoClip) -> List[SceneInfo]:
        """检测情感时刻"""
        scenes = await self.detect_scenes(video)
        
        # 筛选情感场景
        emotional_scenes = []
        for scene in scenes:
            if scene.scene_type == "emotional" and scene.confidence > 0.5:
                emotional_scenes.append(scene)
        
        return emotional_scenes
    
    def set_detection_parameters(self, **kwargs):
        """设置检测参数"""
        if "motion_threshold" in kwargs:
            self.motion_threshold = kwargs["motion_threshold"]
        if "scene_change_threshold" in kwargs:
            self.scene_change_threshold = kwargs["scene_change_threshold"]
        if "min_scene_duration" in kwargs:
            self.min_scene_duration = kwargs["min_scene_duration"]
        if "max_scene_duration" in kwargs:
            self.max_scene_duration = kwargs["max_scene_duration"]
