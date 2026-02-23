#!/usr/bin/env python3
"""测试导出模块"""

import tempfile
from pathlib import Path
import pytest

from app.services.export.davinci_exporter import (
    DaVinciExporter, DaVinciTimeline, DaVinciClip, SubtitleExporter,
)


class TestSubtitleExporter:
    """字幕导出测试"""

    SAMPLE_SUBS = [
        {"start": 0.0, "end": 3.5, "text": "第一句话"},
        {"start": 4.0, "end": 7.2, "text": "第二句话"},
        {"start": 8.0, "end": 12.0, "text": "最后一句"},
    ]

    def test_srt_export(self):
        """SRT 导出"""
        with tempfile.NamedTemporaryFile(suffix=".srt", delete=False) as f:
            path = SubtitleExporter.export_srt(self.SAMPLE_SUBS, f.name)
        
        content = Path(path).read_text(encoding="utf-8")
        assert "1\n" in content
        assert "00:00:00,000 --> 00:00:03,500" in content
        assert "第一句话" in content
        assert "第二句话" in content

    def test_ass_export(self):
        """ASS 导出"""
        with tempfile.NamedTemporaryFile(suffix=".ass", delete=False) as f:
            path = SubtitleExporter.export_ass(
                self.SAMPLE_SUBS, f.name, font="PingFang SC"
            )
        
        content = Path(path).read_text(encoding="utf-8")
        assert "[Script Info]" in content
        assert "PingFang SC" in content
        assert "Dialogue:" in content
        assert "第一句话" in content

    def test_srt_time_format(self):
        """SRT 时间格式"""
        result = SubtitleExporter._format_srt_time(3661.5)
        assert result == "01:01:01,500"

    def test_ass_time_format(self):
        """ASS 时间格式"""
        result = SubtitleExporter._format_ass_time(3661.5)
        assert result == "1:01:01.50"


class TestDaVinciExporter:
    """达芬奇导出测试"""

    def test_basic_export(self):
        """基本 FCPXML 导出"""
        timeline = DaVinciTimeline(
            name="Test Project",
            fps=30.0,
            width=1920,
            height=1080,
        )
        timeline.video_clips.append(DaVinciClip(
            name="clip1",
            file_path="/tmp/test.mp4",
            start=0.0,
            end=10.0,
        ))
        
        with tempfile.NamedTemporaryFile(suffix=".fcpxml", delete=False) as f:
            output = f.name
        
        exporter = DaVinciExporter()
        path = exporter.export(timeline, output)
        
        content = Path(path).read_text(encoding="utf-8")
        assert '<?xml' in content
        assert 'fcpxml' in content
        assert 'Test Project' in content

    def test_export_with_subtitles(self):
        """带字幕的导出"""
        timeline = DaVinciTimeline(name="Sub Test")
        timeline.subtitles = [
            {"start": 0.0, "end": 3.0, "text": "你好世界"},
        ]
        
        with tempfile.NamedTemporaryFile(suffix=".fcpxml", delete=False) as f:
            output = f.name
        
        exporter = DaVinciExporter()
        path = exporter.export(timeline, output)
        
        content = Path(path).read_text(encoding="utf-8")
        assert "你好世界" in content
