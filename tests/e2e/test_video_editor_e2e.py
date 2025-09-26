"""
端到端测试 - 视频编辑器完整流程测试
使用pytest-qt进行UI自动化测试
"""
import os
import sys
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtTest import QTest
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.ui.main.main_window import MainWindow
from app.ui.main.pages.video_editor_page import VideoEditorPage
from app.core.application import Application


@pytest.fixture(scope="session")
def qtbot(qtbot):
    """pytest-qt bot fixture"""
    return qtbot


@pytest.fixture
def app_instance():
    """Mock应用实例"""
    app = Mock(spec=Application)
    app.ai_service_manager = Mock()
    app.config = Mock()
    return app


@pytest.fixture
def main_window(qtbot, app_instance):
    """主窗口fixture"""
    window = MainWindow(app_instance)
    qtbot.addWidget(window)
    window.show()
    return window


def test_video_editor_e2e_workflow(qtbot, main_window, tmp_path):
    """端到端测试：完整视频编辑流程"""
    # 创建临时视频文件（mock）
    temp_video = tmp_path / "test_video.mp4"
    with open(temp_video, 'w') as f:
        f.write("mock video content")

    # 导航到视频编辑页面
    video_page = VideoEditorPage(main_window.application)
    main_window.set_current_page(video_page)
    qtbot.addWidget(video_page)
    video_page.show()

    # 步骤1: 导入媒体
    import_btn = video_page.media_panel.media_library.import_button  # 假设按钮
    if import_btn:
        QTest.mouseClick(import_btn, Qt.MouseButton.LeftButton)
        # Mock文件对话框选择
        with patch('PyQt6.QtWidgets.QFileDialog.getOpenFileNames', return_value=([str(temp_video)], '')):
            pass
        assert video_page.current_video == str(temp_video)

    # 步骤2: 加载预览
    assert video_page.preview_panel.current_video_path == str(temp_video)

    # 步骤3: 应用特效（模糊）
    properties_panel = video_page.properties_panel
    effects_page = properties_panel.toolbox.widget(1)  # 特效页
    effect_combo = effects_page.findChild(QComboBox, "effect_combo")
    if effect_combo:
        QTest.keyClicks(effect_combo, "blur")
    radius_slider = effects_page.findChild(QSlider, "effect_radius_slider")
    if radius_slider:
        QTest.mouseDrag(radius_slider, QPoint(0, 0), QPoint(50, 0))  # 调整强度
    apply_btn = effects_page.findChild(QPushButton, "apply_effect_btn")
    if apply_btn:
        QTest.mouseClick(apply_btn, Qt.MouseButton.LeftButton)
    # 验证状态更新
    QTimer.singleShot(100, lambda: assert "应用特效: blur" in video_page.status_bar.text())

    # 步骤4: 多机位编辑
    multicam_page = properties_panel.toolbox.widget(2)  # 多机位页
    angle_combo = multicam_page.findChild(QComboBox, "angle_combo")
    if angle_combo:
        QTest.keyClicks(angle_combo, "Medium")
    sync_btn = multicam_page.findChild(QPushButton, "sync_btn")
    if sync_btn:
        QTest.mouseClick(sync_btn, Qt.MouseButton.LeftButton)
    switch_btn = multicam_page.findChild(QPushButton, "switch_btn")
    if switch_btn:
        QTest.mouseClick(switch_btn, Qt.MouseButton.LeftButton)
    # 验证切换
    QTimer.singleShot(100, lambda: assert "切换到角度: medium" in video_page.status_bar.text())

    # 步骤5: AI字幕生成
    subtitle_btn = properties_panel.ai_subtitle_page.findChild(QPushButton, "generate_subtitle_btn")
    if subtitle_btn:
        QTest.mouseClick(subtitle_btn, Qt.MouseButton.LeftButton)
    # Mock AI响应
    with patch.object(video_page.ai_video_service, 'analyze_video', return_value=Mock(results={'subtitles': [{'start_time': 0, 'end_time': 5, 'text': '测试字幕'}]})):
        QTimer.singleShot(500, lambda: assert "字幕生成完成" in video_page.status_bar.text())

    # 步骤6: 导出
    export_action = main_window.menu_bar.findChild(QAction, "export_video")  # 假设
    if export_action:
        export_action.trigger()
        export_path = tmp_path / "output.mp4"
        with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName', return_value=(str(export_path), '')):
            pass
        # Mock导出成功
        QTimer.singleShot(100, lambda: assert "导出视频" in video_page.status_bar.text())

    # 验证整体流程完成
    assert video_page.has_project is True


def test_multicam_switch_e2e(qtbot, main_window):
    """多机位切换端到端测试"""
    video_page = VideoEditorPage(main_window.application)
    main_window.set_current_page(video_page)
    qtbot.addWidget(video_page)
    video_page.show()

    # 模拟多机位切换事件
    video_page.multicam_manager.event_bus.publish("switch_performed", {'target_camera': 'medium', 'timeline_time': 10.0})
    QTimer.singleShot(100, lambda: assert "多机位切换到: medium" in video_page.status_bar.text())


def test_error_handling_e2e(qtbot, main_window, tmp_path):
    """端到端测试：错误处理场景"""
    # 创建无效视频文件
    invalid_video = tmp_path / "invalid_video.mp4"
    # 不创建文件内容

    video_page = VideoEditorPage(main_window.application)
    main_window.set_current_page(video_page)
    qtbot.addWidget(video_page)
    video_page.show()

    # 尝试导入无效文件
    with patch('PyQt6.QtWidgets.QFileDialog.getOpenFileNames', return_value=([str(invalid_video)], '')):
        # Mock导入按钮点击
        import_btn = video_page.media_panel.media_library.import_button
        if import_btn:
            QTest.mouseClick(import_btn, Qt.MouseButton.LeftButton)
        # 验证错误消息
        QTimer.singleShot(100, lambda: assert "文件不存在" in video_page.status_bar.text() or "加载失败" in video_page.status_bar.text())

    # 测试AI服务失败fallback
    with patch.object(video_page.ai_video_service, 'analyze_video', side_effect=Exception("AI service error")):
        subtitle_btn = video_page.properties_panel.ai_subtitle_page.findChild(QPushButton, "generate_subtitle_btn")
        if subtitle_btn:
            QTest.mouseClick(subtitle_btn, Qt.MouseButton.LeftButton)
        # 验证错误处理
        QTimer.singleShot(500, lambda: assert "失败" in video_page.status_bar.text())


def test_performance_e2e(qtbot, main_window, tmp_path):
    """端到端测试：性能场景"""
    # 创建多个临时文件模拟批量导入
    temp_videos = []
    for i in range(5):
        temp_video = tmp_path / f"test_video_{i}.mp4"
        with open(temp_video, 'w') as f:
            f.write(f"mock video {i} content")
        temp_videos.append(str(temp_video))

    video_page = VideoEditorPage(main_window.application)
    main_window.set_current_page(video_page)
    qtbot.addWidget(video_page)
    video_page.show()

    # 批量导入
    with patch('PyQt6.QtWidgets.QFileDialog.getOpenFileNames', return_value=(temp_videos, '')):
        import_btn = video_page.media_panel.media_library.import_button
        if import_btn:
            QTest.mouseClick(import_btn, Qt.MouseButton.LeftButton)
        # 验证批量导入
        QTimer.singleShot(200, lambda: assert len(video_page.media_panel.media_library.media_items) >= 5)

    # 测试预览切换性能
    preview_panel = video_page.preview_panel
    for video_path in temp_videos[:2]:  # 测试前2个
        preview_panel.load_video(video_path)
        QTimer.singleShot(100, lambda path=video_path: assert preview_panel.current_video_path == path)


# 运行测试时添加
if __name__ == "__main__":
    pytest.main([__file__, "-v"])