"""
媒体文件元数据提取和缩略图生成服务
提供专业的媒体文件分析、缩略图生成和元数据管理功能
"""

import os
import json
import subprocess
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QImage, QPixmap, QIcon
from PyQt6.QtWidgets import QApplication

from app.core.logger import Logger
from app.utils.error_handler import handle_exception, safe_execute
from app.utils.file_error_handler import FileErrorHandler, FileOperationError


@dataclass
class MediaMetadata:
    """媒体文件元数据"""
    file_path: str
    file_name: str
    file_size: int
    file_type: str  # video, audio, image
    mime_type: str
    duration: Optional[float] = None  # 秒
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    bitrate: Optional[int] = None
    codec: Optional[str] = None
    audio_codec: Optional[str] = None
    audio_bitrate: Optional[int] = None
    audio_channels: Optional[int] = None
    sample_rate: Optional[int] = None
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    thumbnail_path: Optional[str] = None
    is_valid: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 转换datetime对象为字符串
        if data['creation_date']:
            data['creation_date'] = data['creation_date'].isoformat()
        if data['modification_date']:
            data['modification_date'] = data['modification_date'].isoformat()
        return data


class ThumbnailGenerator(QObject):
    """缩略图生成器"""

    thumbnail_generated = pyqtSignal(str, str)  # file_path, thumbnail_path
    thumbnail_failed = pyqtSignal(str, str)  # file_path, error_message
    progress_updated = pyqtSignal(int, int)  # current, total

    def __init__(self, cache_dir: str = None):
        super().__init__()
        self.logger = Logger.get_logger("ThumbnailGenerator")
        self.cache_dir = cache_dir or os.path.join(os.path.expanduser("~"), ".cineaistudio", "thumbnails")
        self.file_handler = FileErrorHandler()

        # 创建缓存目录
        os.makedirs(self.cache_dir, exist_ok=True)

        # 线程池用于后台生成
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.active_tasks = {}

        # 支持的视频格式
        self.video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp', '.tga'}

    def generate_thumbnail(self, file_path: str, size: Tuple[int, int] = (320, 180)) -> Optional[str]:
        """生成缩略图"""
        try:
            if not os.path.exists(file_path):
                self.logger.warning(f"File not found: {file_path}")
                return None

            ext = os.path.splitext(file_path)[1].lower()

            # 生成缓存文件名
            file_hash = hashlib.md5(file_path.encode()).hexdigest()
            cache_name = f"{file_hash}_{size[0]}x{size[1]}.jpg"
            thumbnail_path = os.path.join(self.cache_dir, cache_name)

            # 检查缓存
            if os.path.exists(thumbnail_path):
                return thumbnail_path

            # 根据文件类型生成缩略图
            if ext in self.image_extensions:
                return self._generate_image_thumbnail(file_path, thumbnail_path, size)
            elif ext in self.video_extensions:
                return self._generate_video_thumbnail(file_path, thumbnail_path, size)
            else:
                self.logger.warning(f"Unsupported file type for thumbnail: {ext}")
                return None

        except Exception as e:
            error_msg = f"Failed to generate thumbnail for {file_path}: {e}"
            self.logger.error(error_msg)
            self.thumbnail_failed.emit(file_path, error_msg)
            return None

    def _generate_image_thumbnail(self, file_path: str, thumbnail_path: str, size: Tuple[int, int]) -> str:
        """生成图片缩略图"""
        try:
            # 使用QImage加载和缩放图片
            image = QImage(file_path)
            if image.isNull():
                raise ValueError(f"Failed to load image: {file_path}")

            # 计算保持宽高比的缩放
            scaled_image = image.scaled(
                size[0], size[1],
                QImage.AspectRatioMode.KeepAspectRatio,
                QImage.TransformationMode.SmoothTransformation
            )

            # 保存缩略图
            if scaled_image.save(thumbnail_path, "JPEG", quality=85):
                self.logger.debug(f"Generated image thumbnail: {thumbnail_path}")
                return thumbnail_path
            else:
                raise ValueError("Failed to save thumbnail")

        except Exception as e:
            self.logger.error(f"Failed to generate image thumbnail: {e}")
            raise

    def _generate_video_thumbnail(self, file_path: str, thumbnail_path: str, size: Tuple[int, int]) -> str:
        """生成视频缩略图"""
        try:
            # 检查FFmpeg是否可用
            if not self._check_ffmpeg():
                raise RuntimeError("FFmpeg not found. Please install FFmpeg for video thumbnail generation.")

            # 使用FFmpeg提取视频帧
            cmd = [
                'ffmpeg',
                '-i', file_path,
                '-ss', '00:00:02',  # 从2秒处提取
                '-vframes', '1',
                '-vf', f'scale={size[0]}:{size[1]}:force_original_aspect_ratio=decrease',
                '-q:v', '2',
                '-y',  # 覆盖输出文件
                thumbnail_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and os.path.exists(thumbnail_path):
                self.logger.debug(f"Generated video thumbnail: {thumbnail_path}")
                return thumbnail_path
            else:
                error_msg = result.stderr or "Unknown FFmpeg error"
                raise RuntimeError(f"FFmpeg failed: {error_msg}")

        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg timeout while generating thumbnail")
        except Exception as e:
            self.logger.error(f"Failed to generate video thumbnail: {e}")
            raise

    def _check_ffmpeg(self) -> bool:
        """检查FFmpeg是否可用"""
        try:
            result = subprocess.run(['ffmpeg', '-version'],
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def generate_thumbnails_async(self, file_paths: List[str], size: Tuple[int, int] = (320, 180)) -> None:
        """异步生成多个缩略图"""
        total = len(file_paths)
        self.active_tasks.clear()

        for i, file_path in enumerate(file_paths):
            future = self.thread_pool.submit(self.generate_thumbnail, file_path, size)
            self.active_tasks[future] = file_path

            # 连接完成回调
            future.add_done_callback(lambda f: self._on_thumbnail_completed(f, i + 1, total))

    def _on_thumbnail_completed(self, future, current: int, total: int) -> None:
        """缩略图生成完成回调"""
        try:
            file_path = self.active_tasks.pop(future)
            result = future.result()

            if result:
                self.thumbnail_generated.emit(file_path, result)
            else:
                self.thumbnail_failed.emit(file_path, "Failed to generate thumbnail")

            self.progress_updated.emit(current, total)

        except Exception as e:
            file_path = self.active_tasks.get(future, "unknown")
            error_msg = f"Thumbnail generation failed: {e}"
            self.logger.error(error_msg)
            self.thumbnail_failed.emit(file_path, error_msg)
            self.progress_updated.emit(current, total)

    def get_thumbnail(self, file_path: str, size: Tuple[int, int] = (320, 180)) -> Optional[QPixmap]:
        """获取缩略图"""
        thumbnail_path = self.generate_thumbnail(file_path, size)
        if thumbnail_path and os.path.exists(thumbnail_path):
            return QPixmap(thumbnail_path)
        return None

    def cleanup_cache(self, max_age_days: int = 30) -> int:
        """清理过期缓存"""
        cleaned_count = 0
        cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)

        try:
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    if os.path.getmtime(file_path) < cutoff_time:
                        os.remove(file_path)
                        cleaned_count += 1

            self.logger.info(f"Cleaned {cleaned_count} old thumbnails")
            return cleaned_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup thumbnail cache: {e}")
            return 0

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            total_size = 0
            file_count = 0

            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
                    file_count += 1

            return {
                'file_count': file_count,
                'total_size': total_size,
                'cache_dir': self.cache_dir
            }

        except Exception as e:
            self.logger.error(f"Failed to get cache stats: {e}")
            return {'file_count': 0, 'total_size': 0, 'cache_dir': self.cache_dir}


class MediaMetadataExtractor:
    """媒体元数据提取器"""

    def __init__(self):
        self.logger = Logger.get_logger("MediaMetadataExtractor")
        self.file_handler = FileErrorHandler()

    def extract_metadata(self, file_path: str) -> MediaMetadata:
        """提取媒体文件元数据"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # 获取基本信息
            stat = os.stat(file_path)
            file_name = os.path.basename(file_path)
            file_size = stat.st_size

            # 检测文件类型
            mime_type, _ = mimetypes.guess_type(file_path)
            file_type = self._detect_file_type(file_path)

            # 创建基础元数据
            metadata = MediaMetadata(
                file_path=file_path,
                file_name=file_name,
                file_size=file_size,
                file_type=file_type,
                mime_type=mime_type or 'application/octet-stream',
                creation_date=datetime.fromtimestamp(stat.st_ctime),
                modification_date=datetime.fromtimestamp(stat.st_mtime)
            )

            # 根据文件类型提取特定元数据
            if file_type == 'video':
                self._extract_video_metadata(file_path, metadata)
            elif file_type == 'audio':
                self._extract_audio_metadata(file_path, metadata)
            elif file_type == 'image':
                self._extract_image_metadata(file_path, metadata)

            return metadata

        except Exception as e:
            self.logger.error(f"Failed to extract metadata from {file_path}: {e}")
            return MediaMetadata(
                file_path=file_path,
                file_name=os.path.basename(file_path),
                file_size=0,
                file_type='unknown',
                mime_type='application/octet-stream',
                is_valid=False,
                error_message=str(e)
            )

    def _detect_file_type(self, file_path: str) -> str:
        """检测文件类型"""
        ext = os.path.splitext(file_path)[1].lower()

        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.mpg', '.mpeg'}
        audio_extensions = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus', '.aiff'}
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp', '.tga', '.svg'}

        if ext in video_extensions:
            return 'video'
        elif ext in audio_extensions:
            return 'audio'
        elif ext in image_extensions:
            return 'image'
        else:
            return 'unknown'

    def _extract_video_metadata(self, file_path: str, metadata: MediaMetadata) -> None:
        """提取视频元数据"""
        try:
            if self._check_ffprobe():
                # 使用FFprobe获取视频信息
                cmd = [
                    'ffprobe',
                    '-v', 'quiet',
                    '-print_format', 'json',
                    '-show_format',
                    '-show_streams',
                    file_path
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

                if result.returncode == 0:
                    probe_data = json.loads(result.stdout)

                    # 提取格式信息
                    format_info = probe_data.get('format', {})
                    metadata.duration = float(format_info.get('duration', 0))
                    metadata.bitrate = int(format_info.get('bit_rate', 0))

                    # 提取流信息
                    streams = probe_data.get('streams', [])
                    video_stream = None
                    audio_stream = None

                    for stream in streams:
                        if stream.get('codec_type') == 'video' and video_stream is None:
                            video_stream = stream
                        elif stream.get('codec_type') == 'audio' and audio_stream is None:
                            audio_stream = stream

                    # 视频流信息
                    if video_stream:
                        metadata.width = int(video_stream.get('width', 0))
                        metadata.height = int(video_stream.get('height', 0))
                        metadata.codec = video_stream.get('codec_name')

                        # 计算FPS
                        fps_str = video_stream.get('r_frame_rate')
                        if fps_str and '/' in fps_str:
                            num, den = fps_str.split('/')
                            metadata.fps = float(num) / float(den) if den != '0' else 0

                    # 音频流信息
                    if audio_stream:
                        metadata.audio_codec = audio_stream.get('codec_name')
                        metadata.audio_bitrate = int(audio_stream.get('bit_rate', 0))
                        metadata.audio_channels = int(audio_stream.get('channels', 0))
                        metadata.sample_rate = int(audio_stream.get('sample_rate', 0))
            else:
                # 回退到基本检测
                self._basic_video_detection(file_path, metadata)

        except Exception as e:
            self.logger.warning(f"Failed to extract video metadata: {e}")
            self._basic_video_detection(file_path, metadata)

    def _extract_audio_metadata(self, file_path: str, metadata: MediaMetadata) -> None:
        """提取音频元数据"""
        try:
            if self._check_ffprobe():
                # 使用FFprobe获取音频信息
                cmd = [
                    'ffprobe',
                    '-v', 'quiet',
                    '-print_format', 'json',
                    '-show_format',
                    '-show_streams',
                    file_path
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

                if result.returncode == 0:
                    probe_data = json.loads(result.stdout)

                    # 提取格式信息
                    format_info = probe_data.get('format', {})
                    metadata.duration = float(format_info.get('duration', 0))
                    metadata.bitrate = int(format_info.get('bit_rate', 0))

                    # 提取流信息
                    streams = probe_data.get('streams', [])
                    for stream in streams:
                        if stream.get('codec_type') == 'audio':
                            metadata.audio_codec = stream.get('codec_name')
                            metadata.audio_bitrate = int(stream.get('bit_rate', 0))
                            metadata.audio_channels = int(stream.get('channels', 0))
                            metadata.sample_rate = int(stream.get('sample_rate', 0))
                            break
            else:
                # 回退到基本检测
                self._basic_audio_detection(file_path, metadata)

        except Exception as e:
            self.logger.warning(f"Failed to extract audio metadata: {e}")
            self._basic_audio_detection(file_path, metadata)

    def _extract_image_metadata(self, file_path: str, metadata: MediaMetadata) -> None:
        """提取图片元数据"""
        try:
            # 使用QImage获取图片信息
            image = QImage(file_path)
            if not image.isNull():
                metadata.width = image.width()
                metadata.height = image.height()

                # 获取图片格式信息
                format_info = image.__dict__.get('_format', 'Unknown')
                metadata.codec = format_info

        except Exception as e:
            self.logger.warning(f"Failed to extract image metadata: {e}")

    def _basic_video_detection(self, file_path: str, metadata: MediaMetadata) -> None:
        """基本视频信息检测"""
        try:
            # 使用QMediaPlayer进行基本检测
            from PyQt6.QtMultimedia import QMediaPlayer, QMediaContent
            from PyQt6.QtCore import QUrl

            player = QMediaPlayer()
            media = QMediaContent(QUrl.fromLocalFile(file_path))
            player.setSource(media)

            # 等待加载
            QApplication.processEvents()

            # 获取基本信息
            if player.duration() > 0:
                metadata.duration = player.duration() / 1000  # 转换为秒

            player.deleteLater()

        except Exception as e:
            self.logger.debug(f"Basic video detection failed: {e}")

    def _basic_audio_detection(self, file_path: str, metadata: MediaMetadata) -> None:
        """基本音频信息检测"""
        try:
            # 使用QMediaPlayer进行基本检测
            from PyQt6.QtMultimedia import QMediaPlayer, QMediaContent
            from PyQt6.QtCore import QUrl

            player = QMediaPlayer()
            media = QMediaContent(QUrl.fromLocalFile(file_path))
            player.setSource(media)

            # 等待加载
            QApplication.processEvents()

            # 获取基本信息
            if player.duration() > 0:
                metadata.duration = player.duration() / 1000  # 转换为秒

            player.deleteLater()

        except Exception as e:
            self.logger.debug(f"Basic audio detection failed: {e}")

    def _check_ffprobe(self) -> bool:
        """检查FFprobe是否可用"""
        try:
            result = subprocess.run(['ffprobe', '-version'],
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def batch_extract_metadata(self, file_paths: List[str]) -> List[MediaMetadata]:
        """批量提取元数据"""
        metadata_list = []

        for file_path in file_paths:
            try:
                metadata = self.extract_metadata(file_path)
                metadata_list.append(metadata)
            except Exception as e:
                self.logger.error(f"Failed to extract metadata from {file_path}: {e}")
                # 添加错误条目
                metadata_list.append(MediaMetadata(
                    file_path=file_path,
                    file_name=os.path.basename(file_path),
                    file_size=0,
                    file_type='unknown',
                    mime_type='application/octet-stream',
                    is_valid=False,
                    error_message=str(e)
                ))

        return metadata_list


class MediaManager(QObject):
    """媒体管理器 - 统一的媒体文件管理服务"""

    media_imported = pyqtSignal(list)  # 导入的媒体文件列表
    metadata_updated = pyqtSignal(str, dict)  # file_path, metadata
    thumbnail_generated = pyqtSignal(str, str)  # file_path, thumbnail_path
    import_progress = pyqtSignal(int, int, str)  # current, total, status

    def __init__(self, cache_dir: str = None):
        super().__init__()
        self.logger = Logger.get_logger("MediaManager")

        # 初始化组件
        self.thumbnail_generator = ThumbnailGenerator(cache_dir)
        self.metadata_extractor = MediaMetadataExtractor()
        self.file_handler = FileErrorHandler()

        # 连接信号
        self.thumbnail_generator.thumbnail_generated.connect(self.thumbnail_generated)
        self.thumbnail_generator.thumbnail_failed.connect(self._on_thumbnail_failed)
        self.thumbnail_generator.progress_updated.connect(self._on_thumbnail_progress)

        # 媒体数据库
        self.media_database = {}
        self.database_path = os.path.join(
            os.path.expanduser("~"),
            ".cineaistudio",
            "media_database.json"
        )

        # 加载数据库
        self._load_database()

        # 支持的文件类型
        self.supported_extensions = {
            # 视频
            '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.mpg', '.mpeg',
            # 音频
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus', '.aiff',
            # 图片
            '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp', '.tga', '.svg'
        }

    def import_media_files(self, file_paths: List[str], project_id: str = None) -> List[Dict[str, Any]]:
        """导入媒体文件"""
        valid_files = []

        # 过滤有效文件
        for file_path in file_paths:
            if os.path.exists(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                if ext in self.supported_extensions:
                    valid_files.append(file_path)
                else:
                    self.logger.warning(f"Unsupported file type: {file_path}")
            else:
                self.logger.warning(f"File not found: {file_path}")

        if not valid_files:
            return []

        # 批量提取元数据
        self.import_progress.emit(0, len(valid_files), "正在提取元数据...")
        metadata_list = self.metadata_extractor.batch_extract_metadata(valid_files)

        # 生成缩略图
        self.import_progress.emit(0, len(valid_files), "正在生成缩略图...")
        self.thumbnail_generator.generate_thumbnails_async(valid_files)

        # 添加到数据库
        imported_files = []
        for metadata in metadata_list:
            file_data = {
                'metadata': metadata.to_dict(),
                'project_id': project_id,
                'import_time': datetime.now().isoformat(),
                'tags': [],
                'collections': []
            }

            self.media_database[metadata.file_path] = file_data
            imported_files.append(file_data)

        # 保存数据库
        self._save_database()

        # 发送信号
        self.media_imported.emit(imported_files)

        self.logger.info(f"Imported {len(imported_files)} media files")
        return imported_files

    def get_media_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """获取媒体文件信息"""
        return self.media_database.get(file_path)

    def get_media_by_type(self, file_type: str) -> List[Dict[str, Any]]:
        """按类型获取媒体文件"""
        return [
            data for data in self.media_database.values()
            if data['metadata'].get('file_type') == file_type
        ]

    def get_media_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """按项目获取媒体文件"""
        return [
            data for data in self.media_database.values()
            if data.get('project_id') == project_id
        ]

    def search_media(self, query: str, file_type: str = None) -> List[Dict[str, Any]]:
        """搜索媒体文件"""
        results = []
        query_lower = query.lower()

        for data in self.media_database.values():
            metadata = data['metadata']

            # 按文件类型过滤
            if file_type and metadata.get('file_type') != file_type:
                continue

            # 搜索文件名
            file_name = metadata.get('file_name', '').lower()
            if query_lower in file_name:
                results.append(data)
                continue

            # 搜索标签
            tags = data.get('tags', [])
            if any(query_lower in tag.lower() for tag in tags):
                results.append(data)

        return results

    def delete_media(self, file_path: str) -> bool:
        """删除媒体文件"""
        try:
            if file_path in self.media_database:
                del self.media_database[file_path]
                self._save_database()
                self.logger.info(f"Deleted media from database: {file_path}")
                return True
            return False

        except Exception as e:
            self.logger.error(f"Failed to delete media: {e}")
            return False

    def get_thumbnail(self, file_path: str, size: Tuple[int, int] = (320, 180)) -> Optional[QPixmap]:
        """获取缩略图"""
        return self.thumbnail_generator.get_thumbnail(file_path, size)

    def refresh_metadata(self, file_path: str) -> bool:
        """刷新媒体文件元数据"""
        try:
            if not os.path.exists(file_path):
                return False

            # 重新提取元数据
            metadata = self.metadata_extractor.extract_metadata(file_path)

            # 更新数据库
            if file_path in self.media_database:
                self.media_database[file_path]['metadata'] = metadata.to_dict()
                self._save_database()

                # 发送信号
                self.metadata_updated.emit(file_path, metadata.to_dict())

                # 重新生成缩略图
                self.thumbnail_generator.generate_thumbnail(file_path)

                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to refresh metadata: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取媒体库统计信息"""
        stats = {
            'total_files': len(self.media_database),
            'file_types': {},
            'total_size': 0,
            'cache_stats': self.thumbnail_generator.get_cache_stats()
        }

        for data in self.media_database.values():
            metadata = data['metadata']

            # 统计文件类型
            file_type = metadata.get('file_type', 'unknown')
            stats['file_types'][file_type] = stats['file_types'].get(file_type, 0) + 1

            # 统计总大小
            file_size = metadata.get('file_size', 0)
            stats['total_size'] += file_size

        return stats

    def cleanup_database(self) -> int:
        """清理数据库中的无效文件"""
        removed_count = 0
        invalid_files = []

        # 检查文件是否存在
        for file_path in list(self.media_database.keys()):
            if not os.path.exists(file_path):
                invalid_files.append(file_path)

        # 删除无效文件记录
        for file_path in invalid_files:
            del self.media_database[file_path]
            removed_count += 1

        if removed_count > 0:
            self._save_database()
            self.logger.info(f"Cleaned up {removed_count} invalid files from database")

        return removed_count

    def _load_database(self) -> None:
        """加载媒体数据库"""
        try:
            if os.path.exists(self.database_path):
                with open(self.database_path, 'r', encoding='utf-8') as f:
                    self.media_database = json.load(f)
                self.logger.info(f"Loaded media database with {len(self.media_database)} entries")
            else:
                self.media_database = {}

        except Exception as e:
            self.logger.error(f"Failed to load media database: {e}")
            self.media_database = {}

    def _save_database(self) -> None:
        """保存媒体数据库"""
        try:
            os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
            with open(self.database_path, 'w', encoding='utf-8') as f:
                json.dump(self.media_database, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save media database: {e}")

    def _on_thumbnail_failed(self, file_path: str, error_message: str) -> None:
        """缩略图生成失败处理"""
        self.logger.warning(f"Thumbnail generation failed for {file_path}: {error_message}")

    def _on_thumbnail_progress(self, current: int, total: int) -> None:
        """缩略图生成进度更新"""
        self.import_progress.emit(current, total, "正在生成缩略图...")

    def shutdown(self) -> None:
        """关闭媒体管理器"""
        self.logger.info("Shutting down media manager...")
        self.thumbnail_generator.thread_pool.shutdown(wait=True)
        self._save_database()