#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字幕提取服务
集成OCR和语音识别，提供统一的字幕提取接口
"""

import time
import asyncio
from typing import Dict, Any, Optional, Callable, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.core.subtitle_extractor import (
    OCRExtractor, SpeechExtractor, SubtitleProcessor,
    SubtitleExtractorResult, SubtitleTrack
)


class SubtitleExtractionService:
    """字幕提取服务"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化字幕提取服务
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        
        # 初始化提取器
        self.ocr_extractor = OCRExtractor(self.config.get('ocr', {}))
        self.speech_extractor = SpeechExtractor(self.config.get('speech', {}))
        self.processor = SubtitleProcessor(self.config.get('processor', {}))
        
        # 配置参数
        self.enable_ocr = self.config.get('enable_ocr', True)
        self.enable_speech = self.config.get('enable_speech', True)
        self.parallel_extraction = self.config.get('parallel_extraction', True)
        self.auto_merge = self.config.get('auto_merge', True)
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    def extract_subtitles(
        self,
        video_path: str,
        methods: List[str] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> 'SubtitleExtractionResult':
        """
        提取视频字幕
        
        Args:
            video_path: 视频文件路径
            methods: 提取方法列表 ['ocr', 'speech', 'both']
            progress_callback: 进度回调函数
            
        Returns:
            字幕提取结果
        """
        start_time = time.time()
        
        # 确定提取方法
        if methods is None:
            methods = []
            if self.enable_ocr:
                methods.append('ocr')
            if self.enable_speech:
                methods.append('speech')
        
        if not methods:
            raise ValueError("至少需要启用一种字幕提取方法")
        
        print(f"开始字幕提取，方法: {methods}")
        
        # 创建结果对象
        result = SubtitleExtractionResult()
        result.video_path = video_path
        result.methods = methods
        
        try:
            if self.parallel_extraction and len(methods) > 1:
                # 并行提取
                result = self._extract_parallel(video_path, methods, progress_callback)
            else:
                # 串行提取
                result = self._extract_sequential(video_path, methods, progress_callback)
            
            # 后处理
            if result.success and result.tracks:
                if progress_callback:
                    progress_callback(90, "正在后处理字幕...")
                
                result = self._post_process_result(result)
            
            result.processing_time = time.time() - start_time
            
            if progress_callback:
                progress_callback(100, "字幕提取完成")
            
            print(f"字幕提取完成，耗时: {result.processing_time:.2f}秒")
            
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            print(f"字幕提取失败: {e}")
        
        return result
    
    def _extract_parallel(
        self,
        video_path: str,
        methods: List[str],
        progress_callback: Optional[Callable[[float, str], None]]
    ) -> 'SubtitleExtractionResult':
        """并行提取字幕"""
        result = SubtitleExtractionResult()
        result.video_path = video_path
        result.methods = methods
        
        # 创建提取任务
        futures = {}
        
        if 'ocr' in methods:
            future = self.executor.submit(
                self._extract_ocr_with_progress, 
                video_path, 
                progress_callback
            )
            futures['ocr'] = future
        
        if 'speech' in methods:
            future = self.executor.submit(
                self._extract_speech_with_progress, 
                video_path, 
                progress_callback
            )
            futures['speech'] = future
        
        # 等待任务完成
        completed_count = 0
        total_count = len(futures)
        
        for method, future in futures.items():
            try:
                extraction_result = future.result(timeout=300)  # 5分钟超时
                
                if extraction_result.success:
                    result.tracks.extend(extraction_result.tracks)
                    result.extraction_results[method] = extraction_result
                else:
                    print(f"{method}提取失败: {extraction_result.error_message}")
                
                completed_count += 1
                
                if progress_callback:
                    progress = (completed_count / total_count) * 80  # 80%用于提取
                    progress_callback(progress, f"{method}提取完成")
                
            except Exception as e:
                print(f"{method}提取异常: {e}")
                result.extraction_results[method] = SubtitleExtractorResult()
                result.extraction_results[method].success = False
                result.extraction_results[method].error_message = str(e)
        
        result.success = len(result.tracks) > 0
        return result
    
    def _extract_sequential(
        self,
        video_path: str,
        methods: List[str],
        progress_callback: Optional[Callable[[float, str], None]]
    ) -> 'SubtitleExtractionResult':
        """串行提取字幕"""
        result = SubtitleExtractionResult()
        result.video_path = video_path
        result.methods = methods
        
        for i, method in enumerate(methods):
            try:
                if progress_callback:
                    progress = (i / len(methods)) * 80
                    progress_callback(progress, f"正在进行{method}提取...")
                
                if method == 'ocr':
                    extraction_result = self.ocr_extractor.extract_subtitles(
                        video_path, 
                        progress_callback=self._create_method_progress_callback(
                            progress_callback, i, len(methods), 80
                        )
                    )
                elif method == 'speech':
                    extraction_result = self.speech_extractor.extract_subtitles(
                        video_path,
                        progress_callback=self._create_method_progress_callback(
                            progress_callback, i, len(methods), 80
                        )
                    )
                else:
                    continue
                
                result.extraction_results[method] = extraction_result
                
                if extraction_result.success:
                    result.tracks.extend(extraction_result.tracks)
                else:
                    print(f"{method}提取失败: {extraction_result.error_message}")
                
            except Exception as e:
                print(f"{method}提取异常: {e}")
                result.extraction_results[method] = SubtitleExtractorResult()
                result.extraction_results[method].success = False
                result.extraction_results[method].error_message = str(e)
        
        result.success = len(result.tracks) > 0
        return result
    
    def _extract_ocr_with_progress(
        self, 
        video_path: str, 
        progress_callback: Optional[Callable[[float, str], None]]
    ) -> SubtitleExtractorResult:
        """带进度的OCR提取"""
        def ocr_progress(progress, message):
            if progress_callback:
                # OCR占总进度的40%
                adjusted_progress = progress * 0.4
                progress_callback(adjusted_progress, f"OCR: {message}")
        
        return self.ocr_extractor.extract_subtitles(video_path, ocr_progress)
    
    def _extract_speech_with_progress(
        self, 
        video_path: str, 
        progress_callback: Optional[Callable[[float, str], None]]
    ) -> SubtitleExtractorResult:
        """带进度的语音提取"""
        def speech_progress(progress, message):
            if progress_callback:
                # 语音识别占总进度的40%，从40%开始
                adjusted_progress = 40 + progress * 0.4
                progress_callback(adjusted_progress, f"语音识别: {message}")
        
        return self.speech_extractor.extract_subtitles(video_path, speech_progress)
    
    def _create_method_progress_callback(
        self, 
        main_callback: Optional[Callable[[float, str], None]], 
        method_index: int, 
        total_methods: int, 
        total_progress: float
    ) -> Optional[Callable[[float, str], None]]:
        """创建方法级别的进度回调"""
        if not main_callback:
            return None
        
        def method_progress(progress, message):
            # 计算在总进度中的位置
            method_progress_range = total_progress / total_methods
            base_progress = method_index * method_progress_range
            current_progress = base_progress + (progress / 100.0) * method_progress_range
            
            main_callback(current_progress, message)
        
        return method_progress
    
    def _post_process_result(self, result: 'SubtitleExtractionResult') -> 'SubtitleExtractionResult':
        """后处理提取结果"""
        if not result.tracks:
            return result
        
        try:
            # 处理每个轨道
            processed_tracks = []
            for track in result.tracks:
                processed_track = self.processor.process_track(track)
                if processed_track.segments:  # 只保留非空轨道
                    processed_tracks.append(processed_track)
            
            result.tracks = processed_tracks
            
            # 如果启用自动合并且有多个轨道
            if self.auto_merge and len(result.tracks) > 1:
                merged_track = self.processor.merge_tracks(result.tracks)
                result.merged_track = merged_track
            
            # 提取关键词
            if result.tracks:
                primary_track = result.get_primary_track()
                if primary_track:
                    result.keywords = self.processor.extract_keywords(primary_track)
            
        except Exception as e:
            print(f"后处理失败: {e}")
        
        return result
    
    def get_extraction_info(self, video_path: str) -> Dict[str, Any]:
        """
        获取提取信息（不实际提取）
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            提取信息
        """
        info = {
            "video_path": video_path,
            "available_methods": [],
            "estimated_time": {},
            "recommendations": []
        }
        
        # 检查可用方法
        if self.enable_ocr:
            info["available_methods"].append("ocr")
            info["estimated_time"]["ocr"] = "1-3分钟"
        
        if self.enable_speech:
            info["available_methods"].append("speech")
            try:
                estimated_time = self.speech_extractor.estimate_processing_time(video_path)
                info["estimated_time"]["speech"] = f"{estimated_time/60:.1f}分钟"
            except:
                info["estimated_time"]["speech"] = "2-5分钟"
        
        # 提供建议
        if len(info["available_methods"]) > 1:
            info["recommendations"].append("建议同时使用OCR和语音识别以获得最佳效果")
        
        if "speech" in info["available_methods"]:
            info["recommendations"].append("语音识别适合有清晰对话的视频")
        
        if "ocr" in info["available_methods"]:
            info["recommendations"].append("OCR适合有屏幕字幕的视频")
        
        return info


class SubtitleExtractionResult:
    """字幕提取结果"""
    
    def __init__(self):
        self.video_path: str = ""
        self.methods: List[str] = []
        self.tracks: List[SubtitleTrack] = []
        self.merged_track: Optional[SubtitleTrack] = None
        self.extraction_results: Dict[str, SubtitleExtractorResult] = {}
        self.keywords: List[tuple] = []
        
        # 状态信息
        self.success: bool = True
        self.error_message: Optional[str] = None
        self.processing_time: float = 0.0
        
        # 元数据
        self.metadata: Dict[str, Any] = {}
    
    def get_primary_track(self) -> Optional[SubtitleTrack]:
        """获取主要字幕轨道"""
        if self.merged_track:
            return self.merged_track
        
        if not self.tracks:
            return None
        
        # 优先返回语音识别轨道
        for track in self.tracks:
            if track.source == "speech":
                return track
        
        # 其次返回OCR轨道
        for track in self.tracks:
            if track.source == "ocr":
                return track
        
        return self.tracks[0]
    
    def get_combined_text(self) -> str:
        """获取合并的文本内容"""
        primary_track = self.get_primary_track()
        if not primary_track:
            return ""
        
        return " ".join(segment.text for segment in primary_track.segments)
    
    def export_srt(self, track_source: str = "primary") -> str:
        """导出SRT格式字幕"""
        if track_source == "primary":
            track = self.get_primary_track()
        else:
            track = next((t for t in self.tracks if t.source == track_source), None)
        
        if not track:
            return ""
        
        return track.to_srt()
    
    def export_vtt(self, track_source: str = "primary") -> str:
        """导出VTT格式字幕"""
        if track_source == "primary":
            track = self.get_primary_track()
        else:
            track = next((t for t in self.tracks if t.source == track_source), None)
        
        if not track:
            return ""
        
        return track.to_vtt()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "video_path": self.video_path,
            "methods": self.methods,
            "success": self.success,
            "error_message": self.error_message,
            "processing_time": self.processing_time,
            "tracks": [track.to_dict() for track in self.tracks],
            "merged_track": self.merged_track.to_dict() if self.merged_track else None,
            "keywords": self.keywords,
            "metadata": self.metadata
        }
