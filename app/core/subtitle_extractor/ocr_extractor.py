#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OCR字幕提取器
使用OCR技术从视频帧中提取字幕文本
"""

import cv2
import numpy as np
import time
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

from .subtitle_models import SubtitleSegment, SubtitleTrack, SubtitleExtractorResult


class OCRExtractor:
    """OCR字幕提取器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化OCR提取器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.ocr_engine = None
        self.backup_engine = None
        
        # 默认配置
        self.frame_interval = self.config.get('frame_interval', 1.0)  # 帧采样间隔(秒)
        self.subtitle_region = self.config.get('subtitle_region', None)  # 字幕区域
        self.min_confidence = self.config.get('min_confidence', 0.6)  # 最小置信度
        self.languages = self.config.get('languages', ['ch_sim', 'en'])  # 支持的语言
        
        self._init_ocr_engines()
    
    def _init_ocr_engines(self):
        """初始化OCR引擎"""
        try:
            # 尝试导入PaddleOCR
            from paddleocr import PaddleOCR
            self.ocr_engine = PaddleOCR(
                use_angle_cls=True,
                lang='ch',
                show_log=False
            )
            print("✅ PaddleOCR初始化成功")
        except ImportError:
            print("⚠️ PaddleOCR未安装，将使用备用OCR引擎")
        
        try:
            # 尝试导入EasyOCR作为备用
            import easyocr
            self.backup_engine = easyocr.Reader(self.languages, gpu=False)
            print("✅ EasyOCR初始化成功")
        except ImportError:
            print("⚠️ EasyOCR未安装")
        
        if not self.ocr_engine and not self.backup_engine:
            raise RuntimeError("没有可用的OCR引擎，请安装PaddleOCR或EasyOCR")
    
    def extract_subtitles(self, video_path: str, progress_callback=None) -> SubtitleExtractorResult:
        """
        从视频中提取字幕
        
        Args:
            video_path: 视频文件路径
            progress_callback: 进度回调函数
            
        Returns:
            字幕提取结果
        """
        start_time = time.time()
        result = SubtitleExtractorResult()
        
        try:
            # 打开视频文件
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"无法打开视频文件: {video_path}")
            
            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps
            
            # 计算采样帧
            frame_step = int(fps * self.frame_interval)
            sample_frames = list(range(0, total_frames, frame_step))
            
            print(f"视频时长: {duration:.2f}秒, 总帧数: {total_frames}, 采样帧数: {len(sample_frames)}")
            
            # 提取字幕片段
            segments = []
            processed_frames = 0
            
            for frame_idx in sample_frames:
                # 设置帧位置
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                # 计算时间戳
                timestamp = frame_idx / fps
                
                # 预处理帧
                processed_frame = self._preprocess_frame(frame)
                
                # OCR识别
                ocr_results = self._recognize_text(processed_frame)
                
                # 处理识别结果
                for text, confidence in ocr_results:
                    if confidence >= self.min_confidence and text.strip():
                        segment = SubtitleSegment(
                            start_time=timestamp,
                            end_time=timestamp + self.frame_interval,
                            text=text.strip(),
                            confidence=confidence,
                            language="zh",
                        )
                        segments.append(segment)
                
                processed_frames += 1
                
                # 更新进度
                if progress_callback:
                    progress = processed_frames / len(sample_frames) * 100
                    progress_callback(progress, f"OCR识别中... {processed_frames}/{len(sample_frames)}")
            
            cap.release()
            
            # 后处理字幕
            if segments:
                track = SubtitleTrack(segments, language="zh", source="ocr")
                # 合并相近的片段
                track = track.merge_segments(max_gap=2.0)
                # 过滤低置信度片段
                track = track.filter_by_confidence(self.min_confidence)
                
                result.add_track(track)
            
            result.processing_time = time.time() - start_time
            result.metadata = {
                "video_duration": duration,
                "total_frames": total_frames,
                "processed_frames": len(sample_frames),
                "frame_interval": self.frame_interval
            }
            
            print(f"OCR提取完成，耗时: {result.processing_time:.2f}秒")
            
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            print(f"OCR提取失败: {e}")
        
        return result
    
    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        预处理视频帧
        
        Args:
            frame: 原始帧
            
        Returns:
            处理后的帧
        """
        # 如果指定了字幕区域，裁剪图像
        if self.subtitle_region:
            x, y, w, h = self.subtitle_region
            frame = frame[y:y+h, x:x+w]
        else:
            # 默认取下半部分作为字幕区域
            height = frame.shape[0]
            frame = frame[height//2:, :]
        
        # 转换为灰度图
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        
        # 增强对比度
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=30)
        
        # 去噪
        gray = cv2.medianBlur(gray, 3)
        
        # 二值化
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    def _recognize_text(self, frame: np.ndarray) -> List[Tuple[str, float]]:
        """
        识别帧中的文字
        
        Args:
            frame: 预处理后的帧
            
        Returns:
            识别结果列表 [(文字, 置信度)]
        """
        results = []
        
        try:
            # 优先使用PaddleOCR
            if self.ocr_engine:
                ocr_results = self.ocr_engine.ocr(frame, cls=True)
                
                if ocr_results and ocr_results[0]:
                    for line in ocr_results[0]:
                        if line and len(line) >= 2:
                            text = line[1][0]
                            confidence = line[1][1]
                            results.append((text, confidence))
            
            # 如果PaddleOCR失败，使用EasyOCR
            elif self.backup_engine:
                ocr_results = self.backup_engine.readtext(frame)
                
                for result in ocr_results:
                    if len(result) >= 3:
                        text = result[1]
                        confidence = result[2]
                        results.append((text, confidence))
        
        except Exception as e:
            print(f"OCR识别错误: {e}")
        
        return results
    
    def set_subtitle_region(self, x: int, y: int, width: int, height: int):
        """
        设置字幕区域
        
        Args:
            x, y: 左上角坐标
            width, height: 区域宽高
        """
        self.subtitle_region = (x, y, width, height)
    
    def auto_detect_subtitle_region(self, video_path: str) -> Optional[Tuple[int, int, int, int]]:
        """
        自动检测字幕区域
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            字幕区域坐标 (x, y, width, height)
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
            
            # 采样几帧进行分析
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            sample_frames = [total_frames//4, total_frames//2, total_frames*3//4]
            
            text_regions = []
            
            for frame_idx in sample_frames:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                # 检测文字区域
                regions = self._detect_text_regions(frame)
                text_regions.extend(regions)
            
            cap.release()
            
            if text_regions:
                # 计算最常见的字幕区域
                return self._calculate_common_region(text_regions)
            
        except Exception as e:
            print(f"自动检测字幕区域失败: {e}")
        
        return None
    
    def _detect_text_regions(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """检测帧中的文字区域"""
        regions = []
        
        try:
            if self.ocr_engine:
                ocr_results = self.ocr_engine.ocr(frame, cls=True)
                
                if ocr_results and ocr_results[0]:
                    for line in ocr_results[0]:
                        if line and len(line) >= 2:
                            # 获取文字边界框
                            bbox = line[0]
                            x_coords = [point[0] for point in bbox]
                            y_coords = [point[1] for point in bbox]
                            
                            x = int(min(x_coords))
                            y = int(min(y_coords))
                            w = int(max(x_coords) - min(x_coords))
                            h = int(max(y_coords) - min(y_coords))
                            
                            regions.append((x, y, w, h))
        
        except Exception as e:
            print(f"文字区域检测错误: {e}")
        
        return regions
    
    def _calculate_common_region(self, regions: List[Tuple[int, int, int, int]]) -> Tuple[int, int, int, int]:
        """计算最常见的字幕区域"""
        if not regions:
            return None
        
        # 简单实现：取所有区域的平均值
        x_sum = sum(r[0] for r in regions)
        y_sum = sum(r[1] for r in regions)
        w_sum = sum(r[2] for r in regions)
        h_sum = sum(r[3] for r in regions)
        
        count = len(regions)
        
        return (
            x_sum // count,
            y_sum // count,
            w_sum // count,
            h_sum // count
        )
