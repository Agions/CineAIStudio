#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 媒体服务测试套件
测试媒体导入、元数据提取、缩略图生成等功能
"""

import os
import sys
import tempfile
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import pytest
from PyQt6.QtCore import QObject, pyqtSignal, QThreadPool
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFileDialog

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.media_service import (
    MediaService, MetadataWorker, ThumbnailWorker,
    MediaType, VideoInfo, AudioInfo, ImageInfo,
    ImportResult, MetadataResult
)


@pytest.fixture
def media_service():
    """媒体服务fixture"""
    with patch('app.services.media_service.QThreadPool') as mock_pool:
        service = MediaService()
        service.thread_pool = mock_pool.return_value
        return service


@pytest.fixture
def mock_qfile_dialog():
    """Mock QFileDialog"""
    mock_dialog = Mock(spec=QFileDialog)
    mock_dialog.selectedFiles.return_value = ["/tmp/test_video.mp4"]
    mock_dialog.selectedFilter.return_value = ""
    return mock_dialog


class TestMediaServiceInitialization:
    """测试媒体服务初始化"""

    def test_media_service_init(self, media_service):
        """测试初始化"""
        assert isinstance(media_service, QObject)
        assert hasattr(media_service, 'import_completed')
        assert hasattr(media_service, 'metadata_extracted')
        assert hasattr(media_service, 'thumbnail_generated')
        assert hasattr(media_service, 'import_error')
        assert media_service.import_cache.maxsize == 100
        assert media_service.thumbnail_cache.maxsize == 50


class TestMediaImport:
    """测试媒体导入"""

    def test_import_media_no_parent(self, media_service, mock_qfile_dialog):
        """测试无父窗口导入"""
        with patch('PyQt6.QtWidgets.QFileDialog.getOpenFileNames', return_value=(["/tmp/video.mp4"], "")):
            with patch.object(media_service, 'start_import_worker'):
                result = media_service.import_media()
                media_service.start_import_worker.assert_called_once()
                assert result is None  # 异步，无返回

    def test_import_media_with_parent(self, media_service, mock_qfile_dialog):
        """测试有父窗口导入"""
        mock_parent = Mock()
        with patch('PyQt6.QtWidgets.QFileDialog.getOpenFileNames', return_value=(["/tmp/video.mp4"], "")):
            with patch.object(media_service, 'start_import_worker'):
                result = media_service.import_media(mock_parent)
                assert mock_qfile_dialog == ANY  # 父窗口传递
                media_service.start_import_worker.assert_called_once()

    def test_import_media_no_files_selected(self, media_service):
        """测试无文件选择"""
        with patch('PyQt6.QtWidgets.QFileDialog.getOpenFileNames', return_value=([], "")):
            with patch.object(media_service, 'start_import_worker') as mock_worker:
                result = media_service.import_media()
                mock_worker.assert_not_called()

    @patch('app.services.media_service.MetadataWorker')
    def test_start_import_worker(self, mock_metadata_worker, media_service):
        """测试启动导入worker"""
        file_paths = ["/tmp/video.mp4"]
        mock_worker_instance = Mock()
        mock_metadata_worker.return_value = mock_worker_instance

        media_service.start_import_worker(file_paths)

        mock_metadata_worker.assert_called_once_with("/tmp/video.mp4", media_service)
        media_service.thread_pool.start.assert_called_once_with(mock_worker_instance)


class TestMetadataExtraction:
    """测试元数据提取"""

    @patch('app.services.media_service.probe_video_metadata')
    @patch('app.services.media_service.extract_audio_metadata')
    @patch('app.services.media_service.get_image_metadata')
    def test_extract_metadata_video(self, mock_image, mock_audio, mock_video, media_service):
        """测试视频元数据提取"""
        mock_video.return_value = VideoInfo(
            path="/tmp/video.mp4",
            duration=60.0,
            width=1920,
            height=1080,
            fps=30.0,
            bitrate=5000,
            format="mp4",
            has_audio=True,
            audio_channels=2,
            sample_rate=48000
        )
        mock_audio.return_value = None
        mock_image.return_value = None

        result = media_service.extract_metadata("/tmp/video.mp4")
        assert isinstance(result, MetadataResult)
        assert result.success
        assert result.media_type == MediaType.VIDEO
        assert result.info.duration == 60.0
        mock_video.assert_called_once_with("/tmp/video.mp4")
        mock_audio.assert_not_called()
        mock_image.assert_not_called()

    @patch('app.services.media_service.probe_video_metadata')
    @patch('app.services.media_service.extract_audio_metadata')
    @patch('app.services.media_service.get_image_metadata')
    def test_extract_metadata_audio(self, mock_image, mock_audio, mock_video, media_service):
        """测试音频元数据提取"""
        mock_video.return_value = None
        mock_audio.return_value = AudioInfo(
            path="/tmp/audio.mp3",
            duration=180.0,
            bitrate=128,
            sample_rate=44100,
            channels=2,
            format="mp3"
        )
        mock_image.return_value = None

        result = media_service.extract_metadata("/tmp/audio.mp3")
        assert result.success
        assert result.media_type == MediaType.AUDIO
        assert result.info.duration == 180.0
        mock_audio.assert_called_once_with("/tmp/audio.mp3")

    @patch('app.services.media_service.probe_video_metadata')
    @patch('app.services.media_service.extract_audio_metadata')
    @patch('app.services.media_service.get_image_metadata')
    def test_extract_metadata_image(self, mock_image, mock_audio, mock_video, media_service):
        """测试图像元数据提取"""
        mock_video.return_value = None
        mock_audio.return_value = None
        mock_image.return_value = ImageInfo(
            path="/tmp/image.jpg",
            width=1920,
            height=1080,
            format="jpeg",
            size=1024*1024
        )

        result = media_service.extract_metadata("/tmp/image.jpg")
        assert result.success
        assert result.media_type == MediaType.IMAGE
        assert result.info.width == 1920
        mock_image.assert_called_once_with("/tmp/image.jpg")

    @patch('app.services.media_service.probe_video_metadata')
    def test_extract_metadata_failure(self, mock_video, media_service):
        """测试元数据提取失败"""
        mock_video.side_effect = Exception("File not found")
        result = media_service.extract_metadata("/tmp/invalid.mp4")
        assert not result.success
        assert "File not found" in result.error
        mock_video.assert_called_once_with("/tmp/invalid.mp4")

    def test_metadata_cache_hit(self, media_service):
        """测试元数据缓存命中"""
        file_path = "/tmp/cached.mp4"
        # 首次提取
        with patch('app.services.media_service.probe_video_metadata', return_value=VideoInfo(path=file_path, duration=30.0)):
            result1 = media_service.extract_metadata(file_path)
            assert result1.success

        # 缓存命中
        with patch('app.services.media_service.probe_video_metadata') as mock_probe:
            result2 = media_service.extract_metadata(file_path)
            assert result2.success
            assert result2.info.duration == 30.0
            mock_probe.assert_not_called()  # 缓存命中

    def test_metadata_cache_miss(self, media_service):
        """测试元数据缓存失效（不同文件）"""
        with patch('app.services.media_service.probe_video_metadata', side_effect=[
            VideoInfo(path="/tmp/file1.mp4", duration=10.0),
            VideoInfo(path="/tmp/file2.mp4", duration=20.0)
        ]) as mock_probe:
            media_service.extract_metadata("/tmp/file1.mp4")
            media_service.extract_metadata("/tmp/file2.mp4")
            assert mock_probe.call_count == 2  # 无缓存命中


class TestThumbnailGeneration:
    """测试缩略图生成"""

    @patch('app.services.media_service.cv2.VideoCapture')
    def test_generate_thumbnail_video(self, mock_capture, media_service):
        """测试视频缩略图生成"""
        mock_cap = Mock()
        mock_frame = Mock()
        mock_frame.shape = (1080, 1920, 3)
        mock_cap.read.return_value = (True, mock_frame)
        mock_capture.return_value = mock_cap

        pixmap = media_service._generate_thumbnail("/tmp/video.mp4")
        assert isinstance(pixmap, QPixmap)
        assert pixmap.width() == 320
        assert pixmap.height() == 180
        mock_capture.assert_called_once_with("/tmp/video.mp4")
        mock_cap.set.assert_called_with(1, 150)  # 第5帧 (150/30=5s)

    @patch('app.services.media_service.cv2.VideoCapture')
    def test_generate_thumbnail_video_no_frame(self, mock_capture, media_service):
        """测试视频无帧"""
        mock_cap = Mock()
        mock_cap.read.return_value = (False, None)
        mock_capture.return_value = mock_cap

        pixmap = media_service._generate_thumbnail("/tmp/video.mp4")
        assert pixmap.isNull()  # 空Pixmap
        mock_cap.read.assert_called()

    @patch('app.services.media_service.PIL.Image.open')
    def test_generate_thumbnail_image(self, mock_pil_open, media_service):
        """测试图像缩略图生成"""
        mock_image = Mock()
        mock_image.size = (1920, 1080)
        mock_image.convert.return_value = mock_image
        mock_image.save.return_value = None
        mock_pil_open.return_value = mock_image

        with patch('app.services.media_service.ImageQt') as mock_imageqt:
            mock_qimage = Mock()
            mock_imageqt.ImageQt.return_value = mock_qimage
            pixmap = media_service._generate_thumbnail("/tmp/image.jpg")
            assert isinstance(pixmap, QPixmap)
            mock_pil_open.assert_called_once_with("/tmp/image.jpg")
            mock_imageqt.ImageQt.assert_called_once_with(mock_image)

    def test_thumbnail_cache_hit(self, media_service):
        """测试缩略图缓存命中"""
        file_path = "/tmp/cached_video.mp4"
        # 首次生成
        with patch('app.services.media_service.cv2.VideoCapture') as mock_cv2:
            mock_cap = Mock()
            mock_frame = Mock(shape=(1080, 1920, 3))
            mock_cap.read.return_value = (True, mock_frame)
            mock_cv2.return_value = mock_cap
            with patch('app.services.media_service.QPixmap.fromImage') as mock_pixmap:
                pixmap1 = media_service._generate_thumbnail(file_path)
                assert pixmap1 is not None

        # 缓存命中
        with patch('app.services.media_service.cv2.VideoCapture') as mock_cv2:
            pixmap2 = media_service._generate_thumbnail(file_path)
            assert pixmap2 is not None
            mock_cv2.assert_not_called()  # 缓存

    def test_generate_thumbnails_batch(self, media_service):
        """测试批量缩略图生成"""
        files = ["/tmp/v1.mp4", "/tmp/v2.mp4"]
        with patch.object(media_service, '_generate_thumbnail', side_effect=[QPixmap(320, 180), QPixmap(320, 180)]):
            with patch.object(media_service, 'start_thumbnail_workers'):
                results = media_service.generate_thumbnails_batch(files)
                media_service.start_thumbnail_workers.assert_called_once_with(files)
                assert len(results) == 2
                assert all(isinstance(r, QPixmap) for r in results)


class TestWorkers:
    """测试Worker类"""

    def test_metadata_worker_success(self, media_service):
        """测试元数据worker成功"""
        file_path = "/tmp/test.mp4"
        worker = MetadataWorker(file_path, media_service)

        with patch('app.services.media_service.probe_video_metadata', return_value=VideoInfo(path=file_path, duration=30.0)):
            worker.run()
            media_service.metadata_extracted.emit.assert_called_once_with(
                MetadataResult(success=True, media_type=MediaType.VIDEO, info=ANY)
            )
            media_service.import_completed.emit.assert_called_once_with(
                ImportResult(success=True, file_path=file_path, media_info=ANY)
            )

    def test_metadata_worker_failure(self, media_service):
        """测试元数据worker失败"""
        file_path = "/tmp/invalid.mp4"
        worker = MetadataWorker(file_path, media_service)

        with patch('app.services.media_service.probe_video_metadata', side_effect=Exception("Error")):
            worker.run()
            media_service.import_error.emit.assert_called_once_with(file_path, "Error")
            media_service.import_completed.emit.assert_called_once_with(
                ImportResult(success=False, file_path=file_path, error="Error")
            )

    def test_thumbnail_worker_success(self, media_service):
        """测试缩略图worker成功"""
        file_path = "/tmp/test.mp4"
        worker = ThumbnailWorker(file_path, media_service, 320, 180)

        with patch('app.services.media_service.cv2.VideoCapture') as mock_cv2:
            mock_cap = Mock()
            mock_frame = Mock(shape=(1080, 1920, 3))
            mock_cap.read.return_value = (True, mock_frame)
            mock_cv2.return_value = mock_cap
            with patch('app.services.media_service.QPixmap.fromImage', return_value=QPixmap(320, 180)):
                worker.run()
                media_service.thumbnail_generated.emit.assert_called_once_with(file_path, ANY)

    def test_thumbnail_worker_failure(self, media_service):
        """测试缩略图worker失败"""
        file_path = "/tmp/invalid.mp4"
        worker = ThumbnailWorker(file_path, media_service, 320, 180)

        with patch('app.services.media_service.cv2.VideoCapture', side_effect=Exception("CV Error")):
            worker.run()
            media_service.import_error.emit.assert_called_once_with(file_path, "CV Error")


class TestMediaServiceSignals:
    """测试媒体服务信号"""

    def test_import_completed_signal(self, media_service):
        """测试导入完成信号"""
        result = ImportResult(success=True, file_path="/tmp/success.mp4", media_info=VideoInfo(duration=10.0))
        media_service.import_completed.emit(result)
        # 信号发射验证（通过emit调用）

    def test_metadata_extracted_signal(self, media_service):
        """测试元数据提取信号"""
        result = MetadataResult(success=True, media_type=MediaType.VIDEO, info=VideoInfo(duration=20.0))
        media_service.metadata_extracted.emit(result)

    def test_thumbnail_generated_signal(self, media_service):
        """测试缩略图生成信号"""
        pixmap = QPixmap(320, 180)
        media_service.thumbnail_generated.emit("/tmp/thumb.mp4", pixmap)

    def test_import_error_signal(self, media_service):
        """测试导入错误信号"""
        media_service.import_error.emit("/tmp/error.mp4", "Test error")


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])