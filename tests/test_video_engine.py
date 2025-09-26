#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Video Engine Test Suite for CineAIStudio
Test the core video processing engine
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.video_engine import VideoEngine, EngineState, EngineSettings, OperationResult
from app.core.logger import get_logger
from app.utils.ffmpeg_utils import get_ffmpeg_utils, VideoInfo

class TestVideoEngineInitialization(unittest.TestCase):
    """Test video engine initialization"""

    def setUp(self):
        self.logger = get_logger("TestVideoEngine")
        self.settings = EngineSettings(
            max_concurrent_operations=2,
            memory_limit=1024 * 1024 * 1024,  # 1GB
            temp_directory=tempfile.mkdtemp(),
            enable_hardware_acceleration=False
        )
        self.engine = VideoEngine(self.settings, self.logger)

    def tearDown(self):
        if hasattr(self, 'engine'):
            self.engine.cleanup()
        if hasattr(self, 'settings') and os.path.exists(self.settings.temp_directory):
            import shutil
            shutil.rmtree(self.settings.temp_directory)

    def test_engine_creation(self):
        """Test engine creation"""
        self.assertIsInstance(self.engine, VideoEngine)
        self.assertEqual(self.engine.state, EngineState.UNINITIALIZED)
        self.assertIsNotNone(self.engine.logger)

    @patch('app.core.video_engine.get_hardware_acceleration')
    @patch('app.core.video_engine.get_ffmpeg_utils')
    def test_engine_initialize_success(self, mock_ffmpeg, mock_hw):
        """Test successful engine initialization"""
        mock_hw_instance = Mock()
        mock_hw.return_value = mock_hw_instance
        mock_ffmpeg_instance = Mock()
        mock_ffmpeg.return_value = mock_ffmpeg_instance

        result = self.engine.initialize()
        self.assertTrue(result.success)
        self.assertEqual(self.engine.state, EngineState.READY)
        self.assertIsNotNone(self.engine.video_processor)

    @patch('app.core.video_engine.get_hardware_acceleration')
    @patch('app.core.video_engine.get_ffmpeg_utils')
    def test_engine_initialize_failure(self, mock_ffmpeg, mock_hw):
        """Test engine initialization failure"""
        mock_hw.side_effect = Exception("Hardware error")
        result = self.engine.initialize()
        self.assertFalse(result.success)
        self.assertEqual(self.engine.state, EngineState.ERROR)

class TestVideoStreamOperations(unittest.TestCase):
    """Test video stream operations"""

    def setUp(self):
        self.logger = get_logger("TestVideoStream")
        self.temp_dir = tempfile.mkdtemp()
        self.test_video_path = os.path.join(self.temp_dir, "test_video.mp4")
        with open(self.test_video_path, 'w') as f:
            f.write("dummy video content")
        self.settings = EngineSettings(temp_directory=self.temp_dir)
        self.engine = VideoEngine(self.settings, self.logger)
        self.engine.initialize()

    def tearDown(self):
        self.engine.cleanup()
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch('app.core.video_engine.get_ffmpeg_utils')
    def test_open_video_stream_success(self, mock_ffmpeg):
        """Test opening video stream successfully"""
        mock_ffmpeg_instance = Mock()
        mock_video_info = Mock(spec=VideoInfo)
        mock_video_info.width = 1920
        mock_video_info.height = 1080
        mock_video_info.duration = 300.0
        mock_video_info.fps = 30.0
        mock_ffmpeg_instance.get_video_info.return_value = mock_video_info
        mock_ffmpeg.return_value = mock_ffmpeg_instance

        result = self.engine.open_video_stream(self.test_video_path)
        self.assertTrue(result.success)
        self.assertIn('stream_id', result.data)

        stream_id = result.data['stream_id']
        stream = self.engine.get_video_stream(stream_id)
        self.assertIsNotNone(stream)
        self.assertEqual(stream.path, self.test_video_path)
        self.assertTrue(stream.is_open)

    @patch('app.core.video_engine.get_ffmpeg_utils')
    def test_open_nonexistent_video(self, mock_ffmpeg):
        """Test opening non-existent video"""
        mock_ffmpeg_instance = Mock()
        mock_ffmpeg_instance.get_video_info.side_effect = FileNotFoundError("File not found")
        mock_ffmpeg.return_value = mock_ffmpeg_instance

        result = self.engine.open_video_stream("/nonexistent/video.mp4")
        self.assertFalse(result.success)
        self.assertIn("不存在", result.message)

    def test_close_video_stream(self):
        """Test closing video stream"""
        # First open a stream
        with patch('app.core.video_engine.get_ffmpeg_utils'):
            open_result = self.engine.open_video_stream(self.test_video_path)
            self.assertTrue(open_result.success)
            stream_id = open_result.data['stream_id']

        # Close the stream
        close_result = self.engine.close_video_stream(stream_id)
        self.assertTrue(close_result.success)

        # Verify stream is closed
        stream = self.engine.get_video_stream(stream_id)
        self.assertIsNone(stream)

    def test_get_all_streams(self):
        """Test getting all streams"""
        # Open multiple streams
        stream_ids = []
        for i in range(3):
            temp_file = os.path.join(self.temp_dir, f"test_video_{i}.mp4")
            with open(temp_file, 'w') as f:
                f.write("dummy content")
            with patch('app.core.video_engine.get_ffmpeg_utils'):
                result = self.engine.open_video_stream(temp_file)
                if result.success:
                    stream_ids.append(result.data['stream_id'])

        streams = self.engine.get_all_streams()
        self.assertEqual(len(streams), len(stream_ids))

class TestVideoProcessing(unittest.TestCase):
    """Test video processing operations"""

    def setUp(self):
        self.logger = get_logger("TestVideoProcessing")
        self.temp_dir = tempfile.mkdtemp()
        self.input_path = os.path.join(self.temp_dir, "input.mp4")
        self.output_path = os.path.join(self.temp_dir, "output.mp4")
        with open(self.input_path, 'w') as f:
            f.write("input content")
        self.settings = EngineSettings(temp_directory=self.temp_dir)
        self.engine = VideoEngine(self.settings, self.logger)
        self.engine.initialize()

    def tearDown(self):
        self.engine.cleanup()
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch('app.core.video_engine.VideoProcessor')
    def test_process_video_success(self, mock_processor):
        """Test successful video processing"""
        mock_processor_instance = Mock()
        mock_processor_instance.add_task.return_value = True
        mock_processor.return_value = mock_processor_instance

        result = self.engine.process_video(
            self.input_path,
            self.output_path,
            "resize",
            {"width": 1280, "height": 720},
            callback=None
        )
        self.assertTrue(result.success)
        mock_processor_instance.add_task.assert_called()

    @patch('app.core.video_engine.VideoProcessor')
    def test_process_video_failure(self, mock_processor):
        """Test video processing failure"""
        mock_processor_instance = Mock()
        mock_processor_instance.add_task.return_value = False
        mock_processor.return_value = mock_processor_instance

        result = self.engine.process_video(
            self.input_path,
            self.output_path,
            "resize"
        )
        self.assertFalse(result.success)

    @patch('app.core.video_engine.get_ffmpeg_utils')
    def test_create_thumbnail_success(self, mock_ffmpeg):
        """Test thumbnail creation success"""
        mock_ffmpeg_instance = Mock()
        mock_ffmpeg.return_value = mock_ffmpeg_instance

        result = self.engine.create_thumbnail(
            self.input_path,
            self.output_path,
            timestamp=1.0,
            size=(320, 180)
        )
        self.assertTrue(result.success)
        mock_ffmpeg_instance.create_thumbnail.assert_called()

    @patch('app.core.video_engine.get_ffmpeg_utils')
    def test_create_thumbnail_failure(self, mock_ffmpeg):
        """Test thumbnail creation failure"""
        mock_ffmpeg_instance = Mock()
        mock_ffmpeg_instance.create_thumbnail.side_effect = Exception("Thumbnail error")
        mock_ffmpeg.return_value = mock_ffmpeg_instance

        result = self.engine.create_thumbnail(self.input_path, self.output_path)
        self.assertFalse(result.success)

    @patch('app.core.video_engine.get_ffmpeg_utils')
    def test_extract_audio_success(self, mock_ffmpeg):
        """Test audio extraction success"""
        mock_ffmpeg_instance = Mock()
        mock_ffmpeg.return_value = mock_ffmpeg_instance

        result = self.engine.extract_audio(
            self.input_path,
            self.output_path,
            bitrate=128000
        )
        self.assertTrue(result.success)
        mock_ffmpeg_instance.extract_audio.assert_called()

class TestEngineStatusAndPerformance(unittest.TestCase):
    """Test engine status and performance monitoring"""

    def setUp(self):
        self.logger = get_logger("TestEngineStatus")
        self.temp_dir = tempfile.mkdtemp()
        self.settings = EngineSettings(temp_directory=self.temp_dir)
        self.engine = VideoEngine(self.settings, self.logger)
        self.engine.initialize()

    def tearDown(self):
        self.engine.cleanup()
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_get_engine_status(self):
        """Test getting engine status"""
        status = self.engine.get_engine_status()
        self.assertIn('state', status)
        self.assertEqual(status['state'], 'ready')
        self.assertIn('streams', status)
        self.assertIn('capabilities', status)
        self.assertIn('performance', status)

    def test_get_performance_metrics(self):
        """Test getting performance metrics"""
        metrics = self.engine.get_performance_metrics()
        self.assertIn('engine_stats', metrics)
        self.assertIn('hardware_metrics', metrics)
        self.assertIn('ffmpeg_metrics', metrics)
        self.assertIn('cache_size', metrics)

    def test_optimize_performance(self):
        """Test performance optimization"""
        with patch.object(self.engine.hardware_acceleration, 'optimize_for_video_processing') as mock_optimize:
            mock_optimize.return_value = {'max_workers': 4, 'memory_limit': 1024 * 1024 * 1024}
            result = self.engine.optimize_performance()
            self.assertTrue(result.success)
            mock_optimize.assert_called_once()

    def test_shutdown(self):
        """Test engine shutdown"""
        result = self.engine.shutdown()
        self.assertTrue(result.success)
        self.assertEqual(self.engine.state, EngineState.UNINITIALIZED)

if __name__ == '__main__':
    unittest.main(verbosity=2)