#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 媒体服务
负责媒体文件的导入、元数据提取、格式转换和基本处理
"""

import os
import sys
from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass

from PyQt6.QtWidgets import QFileDialog, QApplication
from PyQt6.QtCore import QObject, pyqtSignal, QMimeData, QUrl
from PyQt6.QtGui import QPixmap, QImage

import cv2
import ffmpeg
from PIL import Image
import numpy as np
from functools import lru_cache
from PyQt6.QtCore import QThreadPool, QRunnable, pyqtSignal, QObject
import gc
import weakref

from app.core.logger import Logger
from ...utils.file_utils import get_supported_formats, validate_media_file


@dataclass
class MediaMetadata:
    """媒体元数据"""
    path: str
    filename: str
    file_size: int
    duration: float  # seconds
    width: int
    height: int
    fps: float
    format: str
    codec: str
    has_audio: bool
    thumbnail: Optional[QPixmap] = None


class MediaService(QObject):
    """媒体服务 - 处理媒体导入和基本操作"""

    # 信号定义
    media_imported = pyqtSignal(MediaMetadata)  # 媒体导入完成
    import_progress = pyqtSignal(int, str)      # 导入进度
    import_error = pyqtSignal(str)              # 导入错误
    media_list_updated = pyqtSignal(list)       # 媒体列表更新

    def __init__(self, logger: Logger):
        super().__init__()
        self.logger = logger
        self.media_library: List[MediaMetadata] = []
        self.supported_formats = get_supported_formats()
        self.thumbnail_cache = weakref.WeakKeyDictionary()  # 使用弱引用缓存，避免内存泄漏
        self.cache_size = 50  # 最大缓存50个缩略图
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(4)  # 限制并发线程
        self.logger.info("媒体服务初始化完成")

    def import_media(self, parent_widget=None) -> List[MediaMetadata]:
        """导入媒体文件（异步）"""
        try:
            # 使用文件对话框选择文件
            file_dialog = QFileDialog(parent_widget)
            file_dialog.setNameFilter("Media Files (*.mp4 *.avi *.mov *.mkv *.jpg *.png *.jpeg)")
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
            file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)

            if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
                file_paths = file_dialog.selectedFiles()
                imported_media = []

                # 异步处理每个文件
                for i, file_path in enumerate(file_paths):
                    if not validate_media_file(file_path):
                        self.import_error.emit(f"不支持的文件格式: {file_path}")
                        continue

                    self.import_progress.emit(int((i / len(file_paths)) * 100), f"处理 {Path(file_path).name}...")

                    # 使用线程池异步提取元数据
                    worker = MetadataWorker(file_path, self)
                    worker.signals.result.connect(lambda meta: self._on_metadata_ready(meta, imported_media))
                    worker.signals.error.connect(lambda err: self.import_error.emit(err))
                    self.thread_pool.start(worker)

                # 等待所有任务完成（简化，实际可使用信号计数）
                self.import_progress.emit(100, "导入完成")
                return imported_media

            return []

        except Exception as e:
            error_msg = f"媒体导入失败: {str(e)}"
            self.logger.error(error_msg)
            self.import_error.emit(error_msg)
            return []

    def _on_metadata_ready(self, metadata: Optional[MediaMetadata], imported_media: List[MediaMetadata]):
        """元数据准备完成回调"""
        if metadata:
            self.media_library.append(metadata)
            imported_media.append(metadata)
            self.media_imported.emit(metadata)
            self.logger.info(f"导入媒体: {metadata.filename}")
            self.media_list_updated.emit(self.media_library)
        gc.collect()  # 强制垃圾回收以释放临时资源

    def _extract_metadata(self, file_path: str) -> Optional[MediaMetadata]:
        """提取媒体元数据（在worker中调用）"""
        try:
            path_obj = Path(file_path)
            stat = path_obj.stat()
            filename = path_obj.name
            file_size = stat.st_size

            # 使用FFmpeg提取视频元数据
            probe = ffmpeg.probe(file_path)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)

            if video_stream:
                duration = float(probe['format']['duration'])
                width = int(video_stream['width'])
                height = int(video_stream['height'])
                fps = eval(video_stream['r_frame_rate'])  # e.g., '30/1' -> 30.0
                format_name = probe['format']['format_name']
                codec = video_stream['codec_name']
                has_audio = bool(audio_stream)

                # 生成缩略图（使用缓存）
                thumbnail = self._generate_thumbnail(file_path)
                thumbnail_ref = weakref.ref(thumbnail) if thumbnail else None  # 弱引用

                return MediaMetadata(
                    path=file_path,
                    filename=filename,
                    file_size=file_size,
                    duration=duration,
                    width=width,
                    height=height,
                    fps=fps,
                    format=format_name,
                    codec=codec,
                    has_audio=has_audio,
                    thumbnail=thumbnail_ref  # 存储弱引用
                )

            # 图像文件处理
            elif path_obj.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                # 使用PIL提取图像元数据
                with Image.open(file_path) as img:
                    width, height = img.size
                    # 图像无duration/fps
                    duration = 0.0
                    fps = 0.0
                    format_name = img.format.lower() if img.format else 'unknown'
                    codec = 'image'
                    has_audio = False

                    # 生成缩略图（使用缓存）
                    thumbnail = self._generate_image_thumbnail(file_path)
                    thumbnail_ref = weakref.ref(thumbnail) if thumbnail else None  # 弱引用

                return MediaMetadata(
                    path=file_path,
                    filename=filename,
                    file_size=file_size,
                    duration=duration,
                    width=width,
                    height=height,
                    fps=fps,
                    format=format_name,
                    codec=codec,
                    has_audio=has_audio,
                    thumbnail=thumbnail_ref  # 存储弱引用
                )

            else:
                self.logger.warning(f"无法提取元数据: {file_path}")
                return None

        except ffmpeg.Error as e:
            self.logger.error(f"FFmpeg错误: {e}")
            return None
        except Exception as e:
            self.logger.error(f"元数据提取失败: {str(e)}")
            return None

    @lru_cache(maxsize=50)
    def _generate_thumbnail(self, video_path: str) -> Optional[QPixmap]:
        """生成视频缩略图（缓存）"""
        try:
            # 使用OpenCV捕获帧
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            target_frame = min(1, frame_count - 1) if frame_count > 0 else 0  # 第一秒帧

            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ret, frame = cap.read()
            cap.release()

            if ret:
                # 转换为QPixmap
                height, width = frame.shape[:2]
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                qimg = QImage(rgb_frame.data, width, height, width * 3, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(qimg.scaled(320, 180, Qt.AspectRatioMode.KeepAspectRatio))
                # 使用弱引用缓存
                self.thumbnail_cache[pixmap] = None  # WeakKeyDictionary键为pixmap
                return pixmap
            return None

        except Exception as e:
            self.logger.warning(f"生成缩略图失败: {e}")
            return None

    def _generate_image_thumbnail(self, file_path: str) -> Optional[QPixmap]:
        """生成图像缩略图（缓存）"""
        try:
            with Image.open(file_path) as img:
                img.thumbnail((320, 180), Image.Resampling.LANCZOS)
                qimg = QImage(img.tobytes(), img.width, img.height, img.mode)
                pixmap = QPixmap.fromImage(qimg)
                # 使用弱引用缓存
                self.thumbnail_cache[pixmap] = None
                return pixmap
        except Exception as e:
            self.logger.warning(f"生成图像缩略图失败: {e}")
            return None

    def get_media_library(self) -> List[MediaMetadata]:
        """获取媒体库"""
        return self.media_library

    def remove_media(self, metadata: MediaMetadata) -> bool:
        """移除媒体"""
        try:
            self.media_library.remove(metadata)
            self.media_list_updated.emit(self.media_library)
            self.logger.info(f"移除媒体: {metadata.filename}")
            return True
        except ValueError:
            self.logger.warning(f"媒体未找到: {metadata.filename}")
            return False

    def clear_media_library(self) -> None:
        """清空媒体库"""
        # 释放弱引用
        for metadata in self.media_library:
            if metadata.thumbnail:
                metadata.thumbnail = None  # 清除弱引用
        self.media_library.clear()
        self.thumbnail_cache = weakref.WeakKeyDictionary()  # 重置弱缓存
        gc.collect()
        self.media_list_updated.emit([])
        self.logger.info("清空媒体库")

    def search_media(self, query: str) -> List[MediaMetadata]:
        """搜索媒体"""
        query_lower = query.lower()
        return [
            media for media in self.media_library
            if query_lower in media.filename.lower() or query_lower in media.path.lower()
        ]

    def get_supported_formats(self) -> Dict[str, List[str]]:
        """获取支持的格式"""
        return {
            'video': ['mp4', 'avi', 'mov', 'mkv', 'webm'],
            'audio': ['mp3', 'wav', 'aac', 'flac'],
            'image': ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif']
        }

# Worker类用于异步元数据提取
class Signals(QObject):
    result = pyqtSignal(object)
    error = pyqtSignal(str)

class MetadataWorker(QRunnable):
    def __init__(self, file_path: str, media_service: MediaService):
        super().__init__()
        self.file_path = file_path
        self.media_service = media_service
        self.signals = Signals()

    def run(self):
        try:
            metadata = self.media_service._extract_metadata(self.file_path)
            self.signals.result.emit(metadata)
        except Exception as e:
            self.signals.error.emit(str(e))