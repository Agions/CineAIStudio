#!/usr/bin/env python3
"""测试 FFmpeg 工具"""

import pytest
from unittest.mock import Mock, patch
from subprocess import CalledProcessError

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
        """测试获取视频时长失败（ffprobe 命令失败）"""
        # 必须是 CalledProcessError 才会被捕获
        mock_run.side_effect = CalledProcessError(1, "ffprobe", stderr="not found")

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

        # ffprobe 返回完整 JSON，duration 在 format 下
        assert "format" in info

    def test_check_ffmpeg_available(self):
        """测试检查 FFmpeg 可用性（方法不存在，跳过）"""
        pytest.skip("check_ffmpeg 方法不存在于 FFmpegTool")


class TestFFmpegToolStaticMethods:
    """测试静态方法"""

    def test_is_valid_video(self):
        """测试验证视频文件（方法不存在，跳过）"""
        pytest.skip("is_valid_video 方法不存在于 FFmpegTool")
