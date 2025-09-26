#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 导出系统测试套件
使用pytest进行全面单元测试覆盖
"""

import os
import sys
import tempfile
import json
import time
from unittest.mock import Mock, patch, MagicMock, ANY
from pathlib import Path
import pytest
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.export.export_system import (
    ExportFormat, ExportQuality, ExportStatus,
    ExportPreset, ExportTask, JianyingDraftConfig,
    ExportEngine, FFmpegEngine, JianyingEngine,
    ExportQueueManager, ExportPresetManager, ExportSystem
)


@pytest.fixture
def sample_preset():
    """示例导出预设fixture"""
    return ExportPreset(
        id="test_preset",
        name="Test Preset",
        format=ExportFormat.MP4_H264,
        quality=ExportQuality.HIGH,
        resolution=(1920, 1080),
        bitrate=8000,
        fps=30.0,
        audio_bitrate=128,
        description="Test description"
    )


@pytest.fixture
def sample_task(sample_preset):
    """示例导出任务fixture"""
    return ExportTask(
        id="test_task",
        project_id="test_project",
        output_path="/tmp/test_output.mp4",
        preset=sample_preset,
        status=ExportStatus.PENDING,
        progress=0.0,
        metadata={"input_file": "/tmp/input.mp4", "duration": 60.0}
    )


@pytest.fixture
def sample_jianying_config():
    """示例剪映配置fixture"""
    return JianyingDraftConfig(
        project_name="Test Project",
        version="1.0",
        fps=30.0,
        resolution=(1920, 1080),
        audio_sample_rate=48000,
        tracks=[{"id": "track1", "type": "video"}],
        materials=[{"id": "mat1", "path": "/tmp/video.mp4"}],
        effects=[{"type": "fade"}],
        text_overlays=[{"text": "Test", "time": 0.0}]
    )


class TestExportEnumsAndDataclasses:
    """测试枚举和数据类"""

    def test_export_format_enum(self):
        """测试导出格式枚举"""
        assert ExportFormat.MP4_H264.value == "mp4_h264"
        assert len(ExportFormat) == 10  # 根据定义计数

    def test_export_quality_enum(self):
        """测试导出质量枚举"""
        assert ExportQuality.HIGH.value == "high"
        assert ExportQuality.CUSTOM.value == "custom"

    def test_export_status_enum(self):
        """测试导出状态枚举"""
        assert ExportStatus.PROCESSING.value == "processing"
        assert ExportStatus.FAILED.value == "failed"

    def test_export_preset_dataclass(self, sample_preset):
        """测试导出预设数据类"""
        assert sample_preset.id == "test_preset"
        assert sample_preset.format == ExportFormat.MP4_H264
        assert sample_preset.resolution == (1920, 1080)

    def test_export_task_dataclass(self, sample_task):
        """测试导出任务数据类"""
        assert sample_task.id == "test_task"
        assert sample_task.status == ExportStatus.PENDING
        assert sample_task.progress == 0.0
        assert sample_task.metadata == {"input_file": "/tmp/input.mp4", "duration": 60.0}


class TestExportEngines:
    """测试导出引擎"""

    def test_ffmpeg_engine_initialization(self):
        """测试FFmpeg引擎初始化"""
        with patch('app.export.export_system.shutil.which', return_value='/usr/bin/ffmpeg'):
            with patch('app.export.export_system.get_hardware_acceleration', return_value=Mock(hw_acceleration_type='cuda')):
                engine = FFmpegEngine()
                assert engine.ffmpeg_path == '/usr/bin/ffmpeg'
                assert len(engine.supported_formats) == 9  # MP4_H264 等

    def test_ffmpeg_engine_capabilities(self):
        """测试FFmpeg引擎能力"""
        with patch('app.export.export_system.shutil.which', return_value='/usr/bin/ffmpeg'):
            engine = FFmpegEngine()
            capabilities = engine.get_capabilities()
            assert ExportFormat.MP4_H264 in capabilities
            assert ExportFormat.JIANYING_DRAFT not in capabilities

    @patch('app.export.export_system.subprocess.Popen')
    def test_ffmpeg_export_success(self, mock_popen, sample_task):
        """测试FFmpeg导出成功"""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.poll.return_value = None
        mock_process.stderr.readline.side_effect = ['frame=  10 fps= 30 q=24.8 size=     512kB time=00:00:00.33 bitrate=12500.0kbits/s speed=1x    \n', '', None]
        mock_popen.return_value = mock_process

        with patch('app.export.export_system.shutil.which', return_value='/usr/bin/ffmpeg'):
            engine = FFmpegEngine()
            sample_task.preset.hw_acceleration = None
            success = engine.export(sample_task)
            assert success is True
            assert sample_task.progress > 0  # 解析进度

    @patch('app.export.export_system.subprocess.Popen')
    def test_ffmpeg_export_failure(self, mock_popen, sample_task):
        """测试FFmpeg导出失败"""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        with patch('app.export.export_system.shutil.which', return_value='/usr/bin/ffmpeg'):
            engine = FFmpegEngine()
            success = engine.export(sample_task)
            assert success is False
            assert "FFmpeg export failed" in sample_task.error_message

    def test_ffmpeg_build_command(self, sample_task):
        """测试FFmpeg命令构建"""
        with patch('app.export.export_system.shutil.which', return_value='/usr/bin/ffmpeg'):
            engine = FFmpegEngine()
            cmd = engine._build_ffmpeg_command(sample_task)
            assert cmd[0] == '/usr/bin/ffmpeg'
            assert '-i' in cmd
            assert '-c:v' in cmd
            assert '-y' in cmd
            assert sample_task.output_path == cmd[-1]

    def test_ffmpeg_parse_progress(self, sample_task):
        """测试FFmpeg进度解析"""
        with patch('app.export.export_system.shutil.which', return_value='/usr/bin/ffmpeg'):
            engine = FFmpegEngine()
            line = 'frame=  10 fps= 30 q=24.8 size=     512kB time=00:00:10.00 bitrate=12500.0kbits/s speed=1x    \n'
            progress = engine._parse_ffmpeg_progress(line, sample_task)
            assert 0 < progress <= 100  # 10s / 60s = ~16.67%

    def test_ffmpeg_parse_time(self):
        """测试时间解析"""
        with patch('app.export.export_system.shutil.which', return_value='/usr/bin/ffmpeg'):
            engine = FFmpegEngine()
            time_str = '00:01:30.50'
            parsed_time = engine._parse_time(time_str)
            assert parsed_time == 90.5

    def test_jianying_engine_initialization(self):
        """测试剪映引擎初始化"""
        engine = JianyingEngine()
        assert len(engine.supported_formats) == 1
        assert ExportFormat.JIANYING_DRAFT in engine.supported_formats

    def test_jianying_engine_capabilities(self):
        """测试剪映引擎能力"""
        engine = JianyingEngine()
        capabilities = engine.get_capabilities()
        assert capabilities == [ExportFormat.JIANYING_DRAFT]

    def test_jianying_export_success(self, sample_task, sample_jianying_config):
        """测试剪映导出成功"""
        sample_task.metadata["jianying_config"] = sample_jianying_config
        sample_task.preset.format = ExportFormat.JIANYING_DRAFT

        with patch('builtins.open', new_callable=MagicMock) as mock_file:
            mock_file.return_value.__enter__.return_value.write = Mock()
            engine = JianyingEngine()
            success = engine.export(sample_task)
            assert success is True
            mock_file.assert_called_once()

    def test_jianying_export_failure(self, sample_task):
        """测试剪映导出失败"""
        sample_task.preset.format = ExportFormat.JIANYING_DRAFT
        # 无config
        engine = JianyingEngine()
        success = engine.export(sample_task)
        assert success is False
        assert "Jianying config not provided" in sample_task.error_message

    def test_jianying_generate_draft_data(self, sample_jianying_config):
        """测试剪映草稿数据生成"""
        engine = JianyingEngine()
        draft_data = engine._generate_draft_data(sample_jianying_config)
        assert draft_data["version"] == "1.0"
        assert draft_data["project_name"] == "Test Project"
        assert "tracks" in draft_data
        assert "materials" in draft_data
        assert draft_data["metadata"]["created_by"] == "CineAIStudio"


class TestExportQueueManager:
    """测试导出队列管理器"""

    @pytest.fixture
    def queue_manager(self):
        """队列管理器fixture"""
        with patch('app.export.export_system.threading.Thread') as mock_thread:
            with patch('app.export.export_system.QThreadPool') as mock_pool:
                manager = ExportQueueManager()
                manager.is_running = False  # 停止循环以测试
                return manager

    def test_queue_manager_initialization(self, queue_manager):
        """测试队列管理器初始化"""
        assert len(queue_manager.engines) >= 2  # FFmpeg + Jianying
        assert queue_manager.max_concurrent_tasks == 2
        assert queue_manager.task_queue.qsize() == 0

    @patch('app.export.export_system.QRunnable')
    def test_add_task(self, mock_runnable, queue_manager, sample_task):
        """测试添加任务"""
        queue_manager.add_task(sample_task)
        assert sample_task.status == ExportStatus.QUEUED
        assert queue_manager.task_queue.qsize() == 1
        queue_manager.task_added.emit.assert_called_once_with(sample_task)

    def test_cancel_task_active(self, queue_manager, sample_task):
        """测试取消活动任务"""
        queue_manager.active_tasks[sample_task.id] = sample_task
        success = queue_manager.cancel_task(sample_task.id)
        assert success is True
        assert sample_task.status == ExportStatus.CANCELLED
        queue_manager.task_cancelled.emit.assert_called_once_with(sample_task)

    def test_cancel_task_queued(self, queue_manager, sample_task):
        """测试取消队列任务（当前不支持）"""
        queue_manager.task_queue.put((0, sample_task.id, sample_task))
        success = queue_manager.cancel_task(sample_task.id)
        assert success is False  # 当前实现不支持

    @patch.object(ExportQueueManager, '_execute_task')
    def test_execute_task_success(self, mock_execute, queue_manager, sample_task):
        """测试任务执行成功"""
        mock_execute.return_value = None
        queue_manager._execute_task(sample_task)
        assert sample_task.status == ExportStatus.COMPLETED
        assert sample_task.started_at is not None
        assert sample_task.completed_at is not None
        queue_manager.task_completed.emit.assert_called_once_with(sample_task)

    @patch.object(ExportQueueManager, '_execute_task')
    def test_execute_task_failure_with_retry(self, mock_execute, queue_manager, sample_task):
        """测试任务执行失败并重试"""
        mock_execute.side_effect = [Exception("Retry error"), None]  # 第一次失败，第二次成功
        queue_manager._execute_task(sample_task, max_retries=2)
        assert sample_task.status == ExportStatus.COMPLETED
        assert mock_execute.call_count == 2

    @patch.object(ExportQueueManager, '_execute_task')
    def test_execute_task_all_retries_fail(self, mock_execute, queue_manager, sample_task):
        """测试所有重试失败"""
        mock_execute.side_effect = [Exception("Fail"), Exception("Fail")]
        queue_manager._execute_task(sample_task, max_retries=2)
        assert sample_task.status == ExportStatus.FAILED
        assert "All retries failed" in sample_task.error_message
        queue_manager.task_failed.emit.assert_called()

    def test_get_queue_status(self, queue_manager, sample_task):
        """测试获取队列状态"""
        queue_manager.active_tasks[sample_task.id] = sample_task
        queue_manager.completed_tasks.append(sample_task)
        status = queue_manager.get_queue_status()
        assert status["active_tasks"] == 1
        assert status["completed_tasks"] == 1
        assert status["queue_size"] == 0

    def test_get_task_history(self, queue_manager, sample_task):
        """测试获取任务历史"""
        sample_task.completed_at = time.time()
        queue_manager.completed_tasks = [sample_task]
        queue_manager.failed_tasks = {sample_task.id: sample_task}
        history = queue_manager.get_task_history(limit=10)
        assert len(history) == 2
        assert sample_task in history


class TestExportPresetManager:
    """测试导出预设管理器"""

    def test_preset_manager_initialization(self):
        """测试预设管理器初始化"""
        manager = ExportPresetManager()
        assert len(manager.presets) == 6  # 默认预设数量
        assert "youtube_1080p" in manager.presets

    def test_add_preset(self, sample_preset):
        """测试添加预设"""
        manager = ExportPresetManager()
        success = manager.add_preset(sample_preset)
        assert success is True
        assert sample_preset.id in manager.presets
        assert manager.presets[sample_preset.id] == sample_preset

    def test_remove_preset(self, sample_preset):
        """测试删除预设"""
        manager = ExportPresetManager()
        manager.add_preset(sample_preset)
        success = manager.remove_preset(sample_preset.id)
        assert success is True
        assert sample_preset.id not in manager.presets

    def test_get_preset(self):
        """测试获取预设"""
        manager = ExportPresetManager()
        preset = manager.get_preset("youtube_1080p")
        assert preset is not None
        assert preset.name == "YouTube 1080p"

    def test_get_all_presets(self):
        """测试获取所有预设"""
        manager = ExportPresetManager()
        presets = manager.get_all_presets()
        assert len(presets) == 6
        assert all(isinstance(p, ExportPreset) for p in presets)

    def test_get_presets_by_format(self):
        """测试按格式获取预设"""
        manager = ExportPresetManager()
        presets = manager.get_presets_by_format(ExportFormat.MP4_H264)
        assert len(presets) > 0
        assert all(p.format == ExportFormat.MP4_H264 for p in presets)

    def test_save_load_presets(self, tmp_path):
        """测试预设保存和加载"""
        file_path = tmp_path / "presets.json"
        manager = ExportPresetManager()
        manager.add_preset(ExportPreset(
            id="custom",
            name="Custom",
            format=ExportFormat.MP4_H265,
            quality=ExportQuality.MEDIUM,
            resolution=(1280, 720),
            bitrate=5000,
            fps=30.0,
            audio_bitrate=128
        ))
        manager.save_presets(str(file_path))

        # 验证文件
        assert file_path.exists()
        with open(file_path, 'r') as f:
            data = json.load(f)
            assert "custom" in data
            assert data["custom"]["name"] == "Custom"

        # 加载到新管理器
        new_manager = ExportPresetManager()
        new_manager.presets.clear()  # 清空默认
        new_manager.load_presets(str(file_path))
        assert "custom" in new_manager.presets
        assert new_manager.presets["custom"].name == "Custom"


class TestExportSystem:
    """测试导出系统"""

    @pytest.fixture
    def export_system(self):
        """导出系统fixture"""
        with patch('app.export.export_system.ExportQueueManager') as mock_queue:
            with patch('app.export.export_system.ExportPresetManager') as mock_preset:
                with patch('app.export.export_system.EventBus') as mock_event:
                    mock_queue.return_value = Mock()
                    mock_preset.return_value = Mock(get_preset=Mock(return_value=ExportPreset(
                        id="test", name="Test", format=ExportFormat.MP4_H264, quality=ExportQuality.HIGH,
                        resolution=(1920, 1080), bitrate=8000, fps=30, audio_bitrate=128
                    )))
                    mock_event.return_value = Mock()
                    system = ExportSystem()
                    system.queue_manager.add_task = Mock(return_value=True)
                    return system

    def test_export_system_initialization(self, export_system):
        """测试导出系统初始化"""
        assert export_system.queue_manager is not None
        assert export_system.preset_manager is not None
        assert export_system.event_system is not None

    def test_export_project(self, export_system, sample_task):
        """测试导出项目"""
        with patch.object(export_system.queue_manager, 'add_task', return_value=True):
            task_id = export_system.export_project(
                project_id="test_proj",
                output_path="/tmp/output.mp4",
                preset_id="test_preset"
            )
            assert task_id.startswith("export_")
            export_system.queue_manager.add_task.assert_called_once()

    def test_export_project_preset_not_found(self, export_system):
        """测试预设未找到"""
        export_system.preset_manager.get_preset = Mock(return_value=None)
        with pytest.raises(ValueError, match="Preset not found"):
            export_system.export_project("test", "/tmp/out.mp4", "invalid")

    def test_export_batch(self, export_system):
        """测试批量导出"""
        configs = [
            {"project_id": "proj1", "output_path": "/tmp/out1.mp4", "preset_id": "test"},
            {"project_id": "proj2", "output_path": "/tmp/out2.mp4", "preset_id": "test"}
        ]
        with patch.object(export_system, 'export_project', side_effect=["task1", "task2"]):
            task_ids = export_system.export_batch(configs)
            assert task_ids == ["task1", "task2"]
            export_system.export_project.assert_called()

    def test_cancel_export(self, export_system, sample_task):
        """测试取消导出"""
        export_system.queue_manager.cancel_task = Mock(return_value=True)
        success = export_system.cancel_export(sample_task.id)
        assert success is True
        export_system.queue_manager.cancel_task.assert_called_with(sample_task.id)

    def test_get_queue_status(self, export_system):
        """测试获取队列状态"""
        export_system.queue_manager.get_queue_status = Mock(return_value={"queue_size": 0})
        status = export_system.get_queue_status()
        assert "queue_size" in status

    def test_get_task_history(self, export_system):
        """测试获取任务历史"""
        export_system.queue_manager.get_task_history = Mock(return_value=[Mock()])
        history = export_system.get_task_history()
        assert len(history) == 1

    def test_get_presets(self, export_system):
        """测试获取预设"""
        export_system.preset_manager.get_all_presets = Mock(return_value=[Mock()])
        presets = export_system.get_presets()
        assert len(presets) == 1

    def test_add_remove_preset(self, export_system, sample_preset):
        """测试添加/删除预设"""
        export_system.preset_manager.add_preset = Mock(return_value=True)
        export_system.preset_manager.remove_preset = Mock(return_value=True)
        assert export_system.add_preset(sample_preset) is True
        assert export_system.remove_preset(sample_preset.id) is True

    def test_shutdown(self, export_system):
        """测试关闭"""
        export_system.queue_manager.shutdown = Mock()
        export_system.shutdown()
        export_system.queue_manager.shutdown.assert_called_once()


class TestExportSystemSignals:
    """测试导出系统信号"""

    def test_signal_connections(self):
        """测试信号连接"""
        system = ExportSystem()
        # 检查内部连接（通过mock验证发射）
        with patch.object(system.queue_manager, 'task_started') as mock_started:
            with patch.object(system, '_on_task_started'):
                # 模拟发射
                mock_task = Mock()
                system.queue_manager.task_started.emit(mock_task)
                system._on_task_started.assert_called_once_with(mock_task)
                system.export_started.emit.assert_called_once_with(mock_task.id)

    def test_on_task_progress(self):
        """测试进度信号"""
        system = ExportSystem()
        with patch.object(system, 'export_progress') as mock_progress:
            with patch.object(system.event_system, 'emit'):
                mock_task = Mock(id="test", progress=50.0)
                system._on_task_progress(mock_task, 50.0)
                mock_progress.emit.assert_called_once_with("test", 50.0)

    def test_on_task_completed(self):
        """测试完成信号"""
        system = ExportSystem()
        with patch.object(system, 'export_completed') as mock_completed:
            with patch.object(system.event_system, 'emit'):
                mock_task = Mock(id="test", output_path="/tmp/out.mp4")
                system._on_task_completed(mock_task)
                mock_completed.emit.assert_called_once_with("test", "/tmp/out.mp4")

    def test_on_task_failed(self):
        """测试失败信号"""
        system = ExportSystem()
        with patch.object(system, 'export_failed') as mock_failed:
            with patch.object(system.event_system, 'emit'):
                mock_task = Mock(id="test")
                error = "Test error"
                system._on_task_failed(mock_task, error)
                mock_failed.emit.assert_called_once_with("test", error)

    def test_on_task_cancelled(self):
        """测试取消信号"""
        system = ExportSystem()
        with patch.object(system, 'export_cancelled') as mock_cancelled:
            with patch.object(system.event_system, 'emit'):
                mock_task = Mock(id="test")
                system._on_task_cancelled(mock_task)
                mock_cancelled.emit.assert_called_once_with("test")


# 运行所有测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])