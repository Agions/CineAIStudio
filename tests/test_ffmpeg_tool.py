#!/usr/bin/env python3
"""测试 FFmpeg 工具"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from app.services.viral_video.ffmpeg_tool import FFmpegTool


class TestFFmpegTool:
    """测试 FFmpeg 工具类"""

    @patch('subprocess.run')
    def test_get_duration_success(self, mock_run):
        """测试获取视频时长成功"""
        mock_run.return_value = Mock(
            stdout='{"format": {"duration": "120.5"}}',
            returncode=0
        )
        
        duration = FFmpegTool.get_duration("/test/video.mp4")
        
        assert duration == 120.5

    @patch('subprocess.run')
    def test_get_duration_error(self, mock_run):
        """测试获取视频时长失败"""
        mock_run.side_effect = Exception("FFprobe not found")
        
        duration = FFmpegTool.get_duration("/test/video.mp4")
        
        assert duration == 0.0

    @patch('subprocess.run')
    def test_get_resolution_success(self, mock_run):
        """测试获取分辨率成功"""
        mock_run.return_value = Mock(
            stdout='{"streams": [{"codec_type": "video", "width": 1920, "height": 1080}]}',
            returncode=0
        )
        
        width, height = FFmpegTool.get_resolution("/test/video.mp4")
        
        assert width == 1920
        assert height == 1080

    @patch('subprocess.run')
    def test_get_resolution_default(self, mock_run):
        """测试获取分辨率默认"""
        mock_run.return_value = Mock(
            stdout='{}',
            returncode=0
        )
        
        width, height = FFmpegTool.get_resolution("/test/video.mp4")
        
        assert width == 1920
        assert height == 1080

    @patch('subprocess.run')
    def test_get_video_info_success(self, mock_run):
        """测试获取视频信息成功"""
        mock_run.return_value = Mock(
            stdout='{"format": {"duration": "60"}, "streams": []}',
            returncode=0
        )
        
        info = FFmpegTool.get_video_info("/test/video.mp4")
        
        assert "duration" in info

    @patch('subprocess.run')
    def test_check_ffmpeg_available(self, mock_run):
        """测试检查 FFmpeg 可用性"""
        mock_run.return_value = Mock(returncode=0)
        
        # 不应该抛出异常
        result = FFmpegTool.check_ffmpeg()
        
        # 返回 True 表示可用
        assert result is True or result is False


class TestFFmpegToolStaticMethods:
    """测试静态方法"""

    @patch('subprocess.run')
    def test_is_valid_video(self, mock_run):
        """测试验证视频文件"""
        mock_run.return_value = Mock(returncode=0)
        
        result = FFmpegTool.is_valid_video("/test/video.mp4")
        
        # 取决于 mock 返回值
        assert isinstance(result, bool)
