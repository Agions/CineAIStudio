#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频分析服务
实现视频内容分析、智能剪辑等功能
"""

import os
import sys
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import cv2
# 修复MoviePy 2.x的导入
from moviepy.video.io.VideoFileClip import VideoFileClip


@dataclass
class Scene:
    """场景数据类"""
    id: str
    start_time: float
    end_time: float
    duration: float
    keyframes: List[int]
    is_high_energy: bool = False
    energy_score: float = 0.0
    scene_type: str = "unknown"  # conversation, action, landscape, etc.


@dataclass
class HighlightSegment:
    """高光片段数据类"""
    id: str
    start_time: float
    end_time: float
    duration: float
    score: float
    scene_id: str
    description: str = ""


@dataclass
class VideoAnalysisResult:
    """视频分析结果数据类"""
    total_duration: float
    total_frames: int
    fps: float
    width: int
    height: int
    scenes: List[Scene]
    highlight_segments: List[HighlightSegment]
    high_energy_segments: List[HighlightSegment]
    audio_loudness: List[float]
    average_loudness: float


class VideoAnalyzerService:
    """视频分析服务"""

    def __init__(self):
        """初始化视频分析服务"""
        self.logger = None
        self.min_scene_duration = 2.0  # 最小场景持续时间（秒）
        self.high_energy_threshold = 0.7  # 高能场景阈值

    def set_logger(self, logger):
        """设置日志记录器"""
        self.logger = logger

    def analyze_video(self, video_path: str) -> Optional[VideoAnalysisResult]:
        """分析视频内容"""
        try:
            if not os.path.exists(video_path):
                if self.logger:
                    self.logger.error(f"文件不存在: {video_path}")
                return None

            if self.logger:
                self.logger.info(f"开始分析视频: {video_path}")

            # 获取视频基本信息
            basic_info = self._get_video_basic_info(video_path)
            if not basic_info:
                return None

            # 场景检测
            scenes = self._detect_scenes(video_path, basic_info)
            if self.logger:
                self.logger.info(f"检测到 {len(scenes)} 个场景")

            # 音频分析
            audio_loudness, average_loudness = self._analyze_audio(video_path)
            if self.logger:
                self.logger.info(f"音频平均响度: {average_loudness}")

            # 高能片段检测
            high_energy_segments = self._detect_high_energy_segments(scenes, audio_loudness)
            if self.logger:
                self.logger.info(f"检测到 {len(high_energy_segments)} 个高能片段")

            # 高光片段生成
            highlight_segments = self._generate_highlight_segments(scenes, high_energy_segments)
            if self.logger:
                self.logger.info(f"生成 {len(highlight_segments)} 个高光片段")

            # 构建分析结果
            result = VideoAnalysisResult(
                total_duration=basic_info['duration'],
                total_frames=basic_info['total_frames'],
                fps=basic_info['fps'],
                width=basic_info['width'],
                height=basic_info['height'],
                scenes=scenes,
                highlight_segments=highlight_segments,
                high_energy_segments=high_energy_segments,
                audio_loudness=audio_loudness,
                average_loudness=average_loudness
            )

            if self.logger:
                self.logger.info(f"视频分析完成: {video_path}")
            return result

        except Exception as e:
            if self.logger:
                self.logger.error(f"视频分析失败: {video_path}, 错误: {e}")
            return None

    def _get_video_basic_info(self, video_path: str) -> Optional[Dict[str, Any]]:
        """获取视频基本信息"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"无法打开视频文件: {video_path}")

            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            cap.release()

            return {
                'fps': fps,
                'total_frames': total_frames,
                'duration': duration,
                'width': width,
                'height': height
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"获取视频基本信息失败: {video_path}, 错误: {e}")
            return None

    def _detect_scenes(self, video_path: str, basic_info: Dict[str, Any]) -> List[Scene]:
        """检测视频场景"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"无法打开视频文件: {video_path}")

            fps = basic_info['fps']
            total_frames = basic_info['total_frames']

            scenes = []
            current_scene_start = 0
            prev_hist = None
            scene_id = 1

            # 每隔5帧分析一次
            frame_step = 5

            for frame_idx in range(0, total_frames, frame_step):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    break

                # 计算直方图
                hist = self._calculate_frame_histogram(frame)

                # 如果是第一帧，初始化prev_hist
                if prev_hist is None:
                    prev_hist = hist
                    continue

                # 计算直方图差异
                diff = self._calculate_histogram_diff(prev_hist, hist)

                # 如果差异超过阈值，认为是新场景
                if diff > 0.3:  # 阈值可调整
                    # 计算当前场景结束时间
                    current_time = frame_idx / fps
                    duration = current_time - current_scene_start

                    # 只有持续时间超过最小阈值的才算是有效的场景
                    if duration >= self.min_scene_duration:
                        scene = Scene(
                            id=f"scene_{scene_id}",
                            start_time=current_scene_start,
                            end_time=current_time,
                            duration=duration,
                            keyframes=[frame_idx]
                        )
                        scenes.append(scene)
                        scene_id += 1
                        current_scene_start = current_time

                    prev_hist = hist

            # 添加最后一个场景
            last_scene_end = basic_info['duration']
            last_scene_duration = last_scene_end - current_scene_start
            if last_scene_duration >= self.min_scene_duration:
                scene = Scene(
                    id=f"scene_{scene_id}",
                    start_time=current_scene_start,
                    end_time=last_scene_end,
                    duration=last_scene_duration,
                    keyframes=[total_frames - 1]
                )
                scenes.append(scene)

            cap.release()
            return scenes

        except Exception as e:
            if self.logger:
                self.logger.error(f"场景检测失败: {video_path}, 错误: {e}")
            return []

    def _calculate_frame_histogram(self, frame: np.ndarray) -> np.ndarray:
        """计算帧的直方图"""
        # 转换为HSV色彩空间
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # 计算直方图
        hist = cv2.calcHist([hsv], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
        # 归一化
        hist = cv2.normalize(hist, hist).flatten()
        return hist

    def _calculate_histogram_diff(self, hist1: np.ndarray, hist2: np.ndarray) -> float:
        """计算两个直方图的差异"""
        # 使用巴氏距离
        return cv2.compareHist(hist1, hist2, cv2.HISTCMP_BHATTACHARYYA)

    def _analyze_audio(self, video_path: str) -> Tuple[List[float], float]:
        """分析音频"""
        try:
            # 使用moviepy提取音频
            video_clip = VideoFileClip(video_path)
            audio_clip = video_clip.audio

            if not audio_clip:
                return [], 0.0

            # 获取音频数据
            audio_data = audio_clip.to_soundarray(fps=44100)
            sample_rate = 44100

            # 计算每个时间段的响度
            window_size = sample_rate * 0.5  # 每0.5秒一个窗口
            loudness = []

            for i in range(0, len(audio_data), window_size):
                window = audio_data[i:i+window_size]
                if len(window) == 0:
                    continue

                # 计算RMS作为响度指标
                rms = np.sqrt(np.mean(window**2))
                loudness.append(rms)

            audio_clip.close()
            video_clip.close()

            average_loudness = np.mean(loudness) if loudness else 0.0
            return loudness, average_loudness

        except Exception as e:
            if self.logger:
                self.logger.error(f"音频分析失败: {video_path}, 错误: {e}")
            return [], 0.0

    def _detect_high_energy_segments(self, scenes: List[Scene], audio_loudness: List[float]) -> List[HighlightSegment]:
        """检测高能片段"""
        high_energy_segments = []
        segment_id = 1

        for scene in scenes:
            # 计算场景对应的音频窗口
            start_window = int(scene.start_time * 2)  # 每0.5秒一个窗口
            end_window = int(scene.end_time * 2)

            if start_window >= len(audio_loudness):
                continue

            end_window = min(end_window, len(audio_loudness))
            scene_loudness = audio_loudness[start_window:end_window]

            if not scene_loudness:
                continue

            # 计算场景的平均响度和最大响度
            avg_loudness = np.mean(scene_loudness)
            max_loudness = np.max(scene_loudness)

            # 计算能量分数（结合响度和时长）
            energy_score = (avg_loudness + max_loudness) / 2

            # 归一化能量分数
            if max(audio_loudness) > 0:
                energy_score = energy_score / max(audio_loudness)
            else:
                energy_score = 0

            # 如果能量分数超过阈值，标记为高能场景
            if energy_score > self.high_energy_threshold:
                segment = HighlightSegment(
                    id=f"high_energy_{segment_id}",
                    start_time=scene.start_time,
                    end_time=scene.end_time,
                    duration=scene.duration,
                    score=energy_score,
                    scene_id=scene.id,
                    description=f"高能场景: 能量分数 {energy_score:.2f}"
                )
                high_energy_segments.append(segment)
                segment_id += 1
                scene.is_high_energy = True
                scene.energy_score = energy_score

        return high_energy_segments

    def _generate_highlight_segments(self, scenes: List[Scene], high_energy_segments: List[HighlightSegment]) -> List[HighlightSegment]:
        """生成高光片段"""
        # 简单实现：将高能片段作为高光片段
        # 实际应用中可以结合AI分析、用户喜好等更复杂的逻辑
        return high_energy_segments

    def extract_highlight_video(self, video_path: str, output_path: str, duration: float = 60.0) -> bool:
        """提取高光视频"""
        try:
            if self.logger:
                self.logger.info(f"开始提取高光视频: {video_path} -> {output_path}, 目标时长: {duration}秒")

            # 分析视频
            analysis_result = self.analyze_video(video_path)
            if not analysis_result:
                return False

            # 按分数排序高光片段
            sorted_highlights = sorted(
                analysis_result.highlight_segments,
                key=lambda x: x.score, 
                reverse=True
            )

            # 选择总时长不超过目标时长的高光片段
            selected_segments = []
            total_selected_duration = 0.0

            for segment in sorted_highlights:
                if total_selected_duration + segment.duration <= duration:
                    selected_segments.append(segment)
                    total_selected_duration += segment.duration
                else:
                    # 如果剩余时间不足一个完整片段，跳过或截断
                    remaining = duration - total_selected_duration
                    if remaining > 1.0:  # 只添加至少1秒的片段
                        truncated_segment = HighlightSegment(
                            id=f"{segment.id}_truncated",
                            start_time=segment.start_time,
                            end_time=segment.start_time + remaining,
                            duration=remaining,
                            score=segment.score,
                            scene_id=segment.scene_id,
                            description=segment.description
                        )
                        selected_segments.append(truncated_segment)
                        total_selected_duration += remaining
                    break

            # 按时间顺序排序
            selected_segments.sort(key=lambda x: x.start_time)

            if self.logger:
                self.logger.info(f"选择了 {len(selected_segments)} 个高光片段，总时长: {total_selected_duration:.2f}秒")

            # 使用moviepy提取和合并片段
            video_clip = VideoFileClip(video_path)
            clips = []

            for segment in selected_segments:
                clip = video_clip.subclip(segment.start_time, segment.end_time)
                clips.append(clip)

            if clips:
                final_clip = concatenate_videoclips(clips)
                final_clip.write_videofile(
                    output_path,
                    codec="libx264",
                    audio_codec="aac",
                    bitrate="8000k",
                    fps=analysis_result.fps,
                    threads=4
                )
                final_clip.close()

            video_clip.close()

            if self.logger:
                self.logger.info(f"高光视频提取完成: {output_path}")
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"提取高光视频失败: {video_path}, 错误: {e}")
            return False

    def detect_highlights(self, video_path: str) -> List[HighlightSegment]:
        """检测视频高光片段"""
        analysis_result = self.analyze_video(video_path)
        if not analysis_result:
            return []
        return analysis_result.highlight_segments

    def cleanup(self) -> None:
        """清理资源"""
        pass
