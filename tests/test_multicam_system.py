#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 多摄像机编辑系统测试
测试多摄像机编辑功能的核心组件
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.multicam_engine import (
    get_multicam_engine, MultiCamEngine, CameraSource, CameraAngle,
    SyncMethod, SwitchMode, MultiCamProject, MultiCamClip
)
from app.core.multicam_integration import (
    get_multicam_integration_manager, MultiCamIntegrationManager,
    IntegrationMode, ConversionSettings, ConversionStrategy
)
from app.ui.components.multicam_editor_component import (
    MultiCamEditorComponent, CameraWidget, PreviewQuality
)


class TestMultiCamEngine(unittest.TestCase):
    """测试多摄像机引擎"""

    def setUp(self):
        """测试设置"""
        self.multicam_engine = get_multicam_engine()
        self.temp_dir = tempfile.mkdtemp()
        self.test_video_path = os.path.join(self.temp_dir, "test_video.mp4")

        # 创建测试视频文件
        with open(self.test_video_path, 'w') as f:
            f.write("dummy video content")

    def tearDown(self):
        """测试清理"""
        shutil.rmtree(self.temp_dir)
        if hasattr(self.multicam_engine, 'cleanup'):
            self.multicam_engine.cleanup()

    def test_create_project(self):
        """测试创建项目"""
        project_id = self.multicam_engine.create_project(
            "测试项目",
            "这是一个测试项目"
        )

        self.assertIsNotNone(project_id)
        self.assertIn(project_id, self.multicam_engine.projects)
        self.assertEqual(self.multicam_engine.current_project.name, "测试项目")

    def test_add_camera_source(self):
        """测试添加摄像机源"""
        camera_id = self.multicam_engine.add_camera_source(
            self.test_video_path,
            "测试摄像机",
            CameraAngle.WIDE
        )

        self.assertIsNotNone(camera_id)
        self.assertIn(camera_id, self.multicam_engine.camera_sources)

        camera = self.multicam_engine.camera_sources[camera_id]
        self.assertEqual(camera.name, "测试摄像机")
        self.assertEqual(camera.camera_angle, CameraAngle.WIDE)

    def test_remove_camera_source(self):
        """测试移除摄像机源"""
        camera_id = self.multicam_engine.add_camera_source(
            self.test_video_path,
            "测试摄像机",
            CameraAngle.WIDE
        )

        success = self.multicam_engine.remove_camera_source(camera_id)
        self.assertTrue(success)
        self.assertNotIn(camera_id, self.multicam_engine.camera_sources)

    def test_create_multicam_clip(self):
        """测试创建多摄像机剪辑"""
        camera_id = self.multicam_engine.add_camera_source(
            self.test_video_path,
            "测试摄像机",
            CameraAngle.WIDE
        )

        clip_id = self.multicam_engine.create_multicam_clip(
            start_time=0.0,
            end_time=30.0,
            primary_camera_id=camera_id
        )

        self.assertIsNotNone(clip_id)
        self.assertEqual(len(self.multicam_engine.current_project.clips), 1)

        clip = self.multicam_engine.current_project.clips[0]
        self.assertEqual(clip.start_time, 0.0)
        self.assertEqual(clip.end_time, 30.0)
        self.assertEqual(clip.primary_camera_id, camera_id)

    def test_synchronize_cameras(self):
        """测试摄像机同步"""
        # 添加多个摄像机
        camera1_id = self.multicam_engine.add_camera_source(
            self.test_video_path,
            "摄像机1",
            CameraAngle.WIDE
        )

        camera2_id = self.multicam_engine.add_camera_source(
            self.test_video_path,
            "摄像机2",
            CameraAngle.MEDIUM
        )

        # 测试同步
        with patch.object(self.multicam_engine.sync_engine, 'synchronize_cameras') as mock_sync:
            mock_sync.return_value = {camera1_id: 0.0, camera2_id: 0.1}

            success = self.multicam_engine.synchronize_cameras(
                SyncMethod.AUDIO_WAVE,
                camera1_id
            )

            self.assertTrue(success)
            mock_sync.assert_called_once()

    def test_switch_camera(self):
        """测试摄像机切换"""
        camera_id = self.multicam_engine.add_camera_source(
            self.test_video_path,
            "测试摄像机",
            CameraAngle.WIDE
        )

        clip_id = self.multicam_engine.create_multicam_clip(
            start_time=0.0,
            end_time=30.0,
            primary_camera_id=camera_id
        )

        # 测试切换
        with patch.object(self.multicam_engine.switch_engine, 'switch_camera') as mock_switch:
            mock_switch.return_value = True

            success = self.multicam_engine.switch_camera(
                timeline_time=10.0,
                target_camera_id=camera_id
            )

            self.assertTrue(success)
            mock_switch.assert_called_once_with(10.0, camera_id, 0.0)

    def test_get_engine_status(self):
        """测试获取引擎状态"""
        status = self.multicam_engine.get_engine_status()

        self.assertIn('current_project', status)
        self.assertIn('camera_count', status)
        self.assertIn('sync_status', status)
        self.assertIn('switch_status', status)
        self.assertIn('performance', status)


class TestMultiCamIntegration(unittest.TestCase):
    """测试多摄像机集成管理器"""

    def setUp(self):
        """测试设置"""
        self.integration_manager = get_multicam_integration_manager()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试清理"""
        shutil.rmtree(self.temp_dir)
        if hasattr(self.integration_manager, 'cleanup'):
            self.integration_manager.cleanup()

    def test_integration_mode(self):
        """测试集成模式设置"""
        self.integration_manager.set_integration_mode(IntegrationMode.EMBEDDED)

        status = self.integration_manager.get_integration_status()
        self.assertEqual(status['integration_mode'], 'embedded')

    def test_conversion_settings(self):
        """测试转换设置"""
        settings = ConversionSettings(
            mode=ConversionStrategy.PRESERVE_STRUCTURE,
            create_backup=True,
            preserve_metadata=True
        )

        self.integration_manager.set_conversion_settings(settings)

        status = self.integration_manager.get_integration_status()
        self.assertEqual(status['conversion_settings']['mode'], 'preserve_structure')
        self.assertTrue(status['conversion_settings']['create_backup'])

    def test_resource_allocation(self):
        """测试资源分配"""
        allocation = self.integration_manager.resource_manager.allocate_resources(4)

        self.assertIn('gpu_memory', allocation)
        self.assertIn('cpu_threads', allocation)
        self.assertIn('disk_space', allocation)
        self.assertIn('success', allocation)

    def test_cache_management(self):
        """测试缓存管理"""
        # 测试缓存初始化
        self.integration_manager.cache_manager.initialize()

        # 测试缓存操作
        camera_id = "test_camera"
        time = 10.0
        frame_path = "/tmp/test_frame.jpg"

        # 测试缓存帧
        cached_path = self.integration_manager.cache_manager.get_preview_frame(camera_id, time)
        self.assertIsNone(cached_path)

        # 缓存帧
        self.integration_manager.cache_manager.cache_preview_frame(camera_id, time, frame_path)

        # 获取缓存的帧
        cached_path = self.integration_manager.cache_manager.get_preview_frame(camera_id, time)
        self.assertEqual(cached_path, frame_path)

    def test_performance_monitoring(self):
        """测试性能监控"""
        # 启动性能监控
        self.integration_manager.performance_monitor.start()

        # 获取性能状态
        status = self.integration_manager.performance_monitor.get_status()
        self.assertTrue(status['is_monitoring'])
        self.assertIn('performance_data', status)

        # 停止性能监控
        self.integration_manager.performance_monitor.stop()


class TestCameraWidget(unittest.TestCase):
    """测试摄像机组件"""

    def setUp(self):
        """测试设置"""
        self.camera_source = CameraSource(
            id="test_camera",
            name="测试摄像机",
            file_path="/tmp/test.mp4",
            camera_angle=CameraAngle.WIDE
        )

        # 创建模拟的多摄像机引擎
        self.mock_multicam_engine = Mock()
        self.mock_multicam_engine.get_camera_preview.return_value = None

    def test_camera_widget_creation(self):
        """测试摄像机组件创建"""
        with patch('app.ui.components.multicam_editor_component.get_multicam_engine') as mock_get_engine:
            mock_get_engine.return_value = self.mock_multicam_engine

            widget = CameraWidget(self.camera_source)

            self.assertIsNotNone(widget)
            self.assertEqual(widget.camera_source.name, "测试摄像机")
            self.assertEqual(widget.camera_source.camera_angle, CameraAngle.WIDE)

    def test_preview_quality_setting(self):
        """测试预览质量设置"""
        with patch('app.ui.components.multicam_editor_component.get_multicam_engine') as mock_get_engine:
            mock_get_engine.return_value = self.mock_multicam_engine

            widget = CameraWidget(self.camera_source)

            # 测试设置不同质量
            widget.set_preview_quality(PreviewQuality.LOW)
            self.assertEqual(widget.preview_quality, PreviewQuality.LOW)

            widget.set_preview_quality(PreviewQuality.HIGH)
            self.assertEqual(widget.preview_quality, PreviewQuality.HIGH)

    def test_camera_selection(self):
        """测试摄像机选择"""
        with patch('app.ui.components.multicam_editor_component.get_multicam_engine') as mock_get_engine:
            mock_get_engine.return_value = self.mock_multicam_engine

            widget = CameraWidget(self.camera_source)

            # 测试选择状态
            widget.set_selected(True)
            self.assertTrue(widget.is_selected)

            widget.set_selected(False)
            self.assertFalse(widget.is_selected)


class TestMultiCamEditorComponent(unittest.TestCase):
    """测试多摄像机编辑器组件"""

    def setUp(self):
        """测试设置"""
        self.mock_multicam_engine = Mock()
        self.mock_multicam_engine.camera_sources = {}
        self.mock_multicam_engine.current_project = None
        self.mock_multicam_engine.event_bus = Mock()

    def test_editor_component_creation(self):
        """测试编辑器组件创建"""
        with patch('app.ui.components.multicam_editor_component.get_multicam_engine') as mock_get_engine:
            mock_get_engine.return_value = self.mock_multicam_engine

            component = MultiCamEditorComponent(self.mock_multicam_engine)

            self.assertIsNotNone(component)
            self.assertEqual(component.display_mode, MultiCamDisplayMode.GRID)
            self.assertEqual(component.preview_quality, PreviewQuality.MEDIUM)

    def test_display_mode_setting(self):
        """测试显示模式设置"""
        with patch('app.ui.components.multicam_editor_component.get_multicam_engine') as mock_get_engine:
            mock_get_engine.return_value = self.mock_multicam_engine

            component = MultiCamEditorComponent(self.mock_multicam_engine)

            # 测试设置不同显示模式
            component._set_display_mode(MultiCamDisplayMode.SINGLE)
            self.assertEqual(component.display_mode, MultiCamDisplayMode.SINGLE)

            component._set_display_mode(MultiCamDisplayMode.GRID)
            self.assertEqual(component.display_mode, MultiCamDisplayMode.GRID)

    def test_preview_quality_setting(self):
        """测试预览质量设置"""
        with patch('app.ui.components.multicam_editor_component.get_multicam_engine') as mock_get_engine:
            mock_get_engine.return_value = self.mock_multicam_engine

            component = MultiCamEditorComponent(self.mock_multicam_engine)

            # 测试设置不同质量
            component._set_preview_quality(PreviewQuality.LOW)
            self.assertEqual(component.preview_quality, PreviewQuality.LOW)

            component._set_preview_quality(PreviewQuality.ORIGINAL)
            self.assertEqual(component.preview_quality, PreviewQuality.ORIGINAL)

    def test_seek_to_time(self):
        """测试跳转到指定时间"""
        with patch('app.ui.components.multicam_editor_component.get_multicam_engine') as mock_get_engine:
            mock_get_engine.return_value = self.mock_multicam_engine

            component = MultiCamEditorComponent(self.mock_multicam_engine)

            # 测试时间跳转
            component.seek_to_time(10.5)
            self.assertEqual(component.current_time, 10.5)

            component.seek_to_time(25.0)
            self.assertEqual(component.current_time, 25.0)


class TestSyncEngine(unittest.TestCase):
    """测试同步引擎"""

    def setUp(self):
        """测试设置"""
        self.mock_multicam_engine = Mock()
        self.sync_engine = self.mock_multicam_engine.sync_engine

    def test_audio_wave_sync(self):
        """测试音频波形同步"""
        # 创建测试摄像机
        camera1 = CameraSource("cam1", "Camera1", "/tmp/video1.mp4", CameraAngle.WIDE)
        camera2 = CameraSource("cam2", "Camera2", "/tmp/video2.mp4", CameraAngle.MEDIUM)

        cameras = [camera1, camera2]
        reference_camera = camera1

        with patch.object(self.sync_engine, '_extract_audio_waveform') as mock_extract:
            mock_extract.return_value = np.array([0.1, 0.2, 0.3, 0.2, 0.1])

            with patch.object(self.sync_engine, '_calculate_waveform_correlation') as mock_correlate:
                mock_correlate.return_value = (0.5, 0.8)

                results = self.sync_engine._sync_by_audio_wave(cameras, reference_camera)

                self.assertIn(camera1.id, results)
                self.assertIn(camera2.id, results)
                self.assertEqual(results[camera1.id], 0.0)

    def test_timecode_sync(self):
        """测试时间码同步"""
        camera1 = CameraSource("cam1", "Camera1", "/tmp/video1.mp4", CameraAngle.WIDE)
        camera2 = CameraSource("cam2", "Camera2", "/tmp/video2.mp4", CameraAngle.MEDIUM)

        cameras = [camera1, camera2]
        reference_camera = camera1

        results = self.sync_engine._sync_by_timecode(cameras, reference_camera)

        self.assertIn(camera1.id, results)
        self.assertIn(camera2.id, results)
        self.assertEqual(results[camera1.id], 0.0)


class TestSwitchEngine(unittest.TestCase):
    """测试切换引擎"""

    def setUp(self):
        """测试设置"""
        self.mock_multicam_engine = Mock()
        self.switch_engine = self.mock_multicam_engine.switch_engine

    def test_camera_switch(self):
        """测试摄像机切换"""
        # 创建测试剪辑
        clip = MultiCamClip(
            id="test_clip",
            start_time=0.0,
            end_time=30.0,
            duration=30.0,
            primary_camera_id="cam1"
        )

        self.mock_multicam_engine.current_project = Mock()
        self.mock_multicam_engine.current_project.clips = [clip]

        # 测试切换
        success = self.switch_engine.switch_camera(
            timeline_time=10.0,
            target_camera_id="cam2",
            transition_duration=0.0
        )

        self.assertTrue(success)
        self.assertEqual(len(clip.camera_switches), 1)
        self.assertEqual(clip.camera_switches[0]['time'], 10.0)
        self.assertEqual(clip.camera_switches[0]['to_camera'], "cam2")

    def test_auto_switch_start(self):
        """测试自动切换启动"""
        with patch.object(self.switch_engine, '_auto_cut_worker') as mock_worker:
            mock_worker.return_value = None

            success = self.switch_engine.start_auto_switch(
                SwitchMode.AUTO_CUT,
                {'confidence_threshold': 0.7}
            )

            self.assertTrue(success)
            self.assertEqual(self.switch_engine.switch_mode, SwitchMode.AUTO_CUT)


class TestAnalysisEngine(unittest.TestCase):
    """测试分析引擎"""

    def setUp(self):
        """测试设置"""
        self.mock_multicam_engine = Mock()
        self.analysis_engine = self.mock_multicam_engine.analysis_engine

    def test_single_camera_analysis(self):
        """测试单个摄像机分析"""
        camera = CameraSource("cam1", "Camera1", "/tmp/video1.mp4", CameraAngle.WIDE)

        with patch.object(self.analysis_engine, '_analyze_composition') as mock_composition:
            mock_composition.return_value = 0.8

            with patch.object(self.analysis_engine, '_analyze_focus') as mock_focus:
                mock_focus.return_value = 0.9

                with patch.object(self.analysis_engine, '_analyze_exposure') as mock_exposure:
                    mock_exposure.return_value = 0.7

                    with patch.object(self.analysis_engine, '_analyze_motion') as mock_motion:
                        mock_motion.return_value = 0.6

                        with patch.object(self.analysis_engine, '_analyze_audio_quality') as mock_audio:
                            mock_audio.return_value = {'clarity': 0.8, 'noise_level': 0.2}

                            with patch.object(self.analysis_engine, '_recommend_cut_points') as mock_cuts:
                                mock_cuts.return_value = [{'time': 10.0, 'confidence': 0.7}]

                                result = self.analysis_engine._analyze_single_camera(camera)

                                self.assertEqual(result['composition_score'], 0.8)
                                self.assertEqual(result['focus_score'], 0.9)
                                self.assertEqual(result['exposure_score'], 0.7)
                                self.assertEqual(result['motion_score'], 0.6)
                                self.assertEqual(result['audio_quality']['clarity'], 0.8)
                                self.assertEqual(len(result['recommended_cuts']), 1)


def create_test_suite():
    """创建测试套件"""
    suite = unittest.TestSuite()

    # 添加测试类
    suite.addTest(unittest.makeSuite(TestMultiCamEngine))
    suite.addTest(unittest.makeSuite(TestMultiCamIntegration))
    suite.addTest(unittest.makeSuite(TestCameraWidget))
    suite.addTest(unittest.makeSuite(TestMultiCamEditorComponent))
    suite.addTest(unittest.makeSuite(TestSyncEngine))
    suite.addTest(unittest.makeSuite(TestSwitchEngine))
    suite.addTest(unittest.makeSuite(TestAnalysisEngine))

    return suite


def run_performance_tests():
    """运行性能测试"""
    print("\n=== 性能测试 ===")

    import time

    # 测试多摄像机引擎性能
    engine = get_multicam_engine()

    # 测试项目创建性能
    start_time = time.time()
    for i in range(10):
        engine.create_project(f"性能测试项目{i}")
    project_creation_time = time.time() - start_time

    print(f"项目创建性能: {project_creation_time:.4f}秒 (10个项目)")

    # 测试摄像机添加性能
    start_time = time.time()
    for i in range(20):
        engine.add_camera_source(f"/tmp/test_video{i}.mp4", f"摄像机{i}", CameraAngle.WIDE)
    camera_add_time = time.time() - start_time

    print(f"摄像机添加性能: {camera_add_time:.4f}秒 (20个摄像机)")

    # 测试剪辑创建性能
    if engine.camera_sources:
        camera_ids = list(engine.camera_sources.keys())
        start_time = time.time()
        for i in range(50):
            engine.create_multicam_clip(i * 10.0, (i + 1) * 10.0, camera_ids[0])
        clip_creation_time = time.time() - start_time

        print(f"剪辑创建性能: {clip_creation_time:.4f}秒 (50个剪辑)")


if __name__ == '__main__':
    print("CineAIStudio 多摄像机编辑系统测试")
    print("=" * 50)

    # 运行单元测试
    runner = unittest.TextTestRunner(verbosity=2)
    suite = create_test_suite()
    result = runner.run(suite)

    # 运行性能测试
    run_performance_tests()

    # 输出测试结果
    print("\n" + "=" * 50)
    print(f"测试结果:")
    print(f"运行测试: {result.testsRun}")
    print(f"失败测试: {len(result.failures)}")
    print(f"错误测试: {len(result.errors)}")

    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    if result.wasSuccessful():
        print("\n✅ 所有测试通过!")
    else:
        print("\n❌ 有测试失败!")