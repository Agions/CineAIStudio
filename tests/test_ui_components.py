#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 UI组件测试
测试主窗口、页面切换、媒体导入等UI功能
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtTest import QTest

from app.core.application import Application
from app.ui.main.main_window import MainWindow, PageType
from app.services.media_service import MediaService
from app.ui.main.pages.video_editor_page import VideoEditorPage
from app.ui.main.pages.ai_dialog_page import AIDialogPage


class TestMainWindow(unittest.TestCase):
    """主窗口测试"""

    @classmethod
    def setUpClass(cls):
        """设置测试应用"""
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

    def setUp(self):
        """设置测试"""
        # Mock Application
        self.mock_app = Mock(spec=Application)
        self.mock_app.get_service_by_name.return_value = Mock()
        self.mock_app.get_config.return_value = {}
        self.mock_app.get_state.return_value = "ready"

        # Mock Logger
        mock_logger = Mock()
        self.mock_app.get_service_by_name.return_value = mock_logger

        # Mock MediaService
        self.mock_media_service = Mock(spec=MediaService)
        self.mock_app.register_service = Mock()
        self.mock_app.register_service("media_service", self.mock_media_service)

        self.main_window = MainWindow(self.mock_app)

    def tearDown(self):
        """清理测试"""
        self.main_window.close()
        self.main_window.deleteLater()

    def test_main_window_creation(self):
        """测试主窗口创建"""
        self.assertIsInstance(self.main_window, MainWindow)
        self.assertEqual(self.main_window.windowTitle(), "CineAIStudio v2.0")
        self.assertTrue(self.main_window.isVisible())

    def test_page_switching(self):
        """测试页面切换"""
        # 测试切换到首页
        self.main_window.switch_to_page(PageType.HOME)
        self.assertEqual(self.main_window.current_page, PageType.HOME)

        # 测试切换到视频编辑页面
        self.main_window.switch_to_page(PageType.VIDEO_EDITOR)
        self.assertEqual(self.main_window.current_page, PageType.VIDEO_EDITOR)

        # 测试切换到AI对话页面
        self.main_window.switch_to_page(PageType.AI_DIALOG)
        self.assertEqual(self.main_window.current_page, PageType.AI_DIALOG)

    def test_media_import(self):
        """测试媒体导入"""
        with patch.object(self.main_window.media_service, 'import_media') as mock_import:
            mock_import.return_value = [Mock()]
            self.main_window._import_media()
            mock_import.assert_called_once()

    def test_theme_toggle(self):
        """测试主题切换"""
        initial_dark = self.main_window.is_dark_theme
        self.main_window.toggle_theme()
        self.assertNotEqual(self.main_window.is_dark_theme, initial_dark)

    def test_fullscreen_toggle(self):
        """测试全屏切换"""
        initial_fullscreen = self.main_window.is_fullscreen
        self.main_window.toggle_fullscreen()
        self.assertNotEqual(self.main_window.is_fullscreen, initial_fullscreen)

    def test_shortcuts(self):
        """测试快捷键"""
        # 测试Ctrl+Q退出
        QTest.keyClick(self.main_window, Qt.Key.Key_Q, Qt.KeyboardModifier.ControlModifier)
        # 由于closeEvent有确认对话，测试复杂，跳过详细验证

        # 测试F11全屏
        initial_fullscreen = self.main_window.is_fullscreen
        QTest.keyClick(self.main_window, Qt.Key.Key_F11)
        self.assertNotEqual(self.main_window.is_fullscreen, initial_fullscreen)


class TestVideoEditorPage(unittest.TestCase):
    """视频编辑页面测试"""

    def setUp(self):
        self.mock_app = Mock(spec=Application)
        self.video_editor_page = VideoEditorPage(self.mock_app)

    def test_video_editor_creation(self):
        """测试视频编辑页面创建"""
        self.assertIsInstance(self.video_editor_page, VideoEditorPage)
        self.assertEqual(self.video_editor_page.page_name, "video_editor")

    def test_ai_function_calls(self):
        """测试AI功能调用"""
        with patch.object(self.video_editor_page.ai_service, 'smart_editing') as mock_smart:
            self.video_editor_page._apply_smart_editing()
            mock_smart.assert_called_once()

        with patch.object(self.video_editor_page.ai_service, 'reduce_noise') as mock_noise:
            self.video_editor_page._apply_noise_reduction()
            mock_noise.assert_called_once()

        with patch.object(self.video_editor_page.ai_service, 'generate_subtitle') as mock_subtitle:
            self.video_editor_page._apply_auto_subtitle()
            mock_subtitle.assert_called_once()

        with patch.object(self.video_editor_page.ai_service, 'enhance_quality') as mock_enhance:
            self.video_editor_page._apply_quality_enhancement()
            mock_enhance.assert_called_once()


class TestAIDialogPage(unittest.TestCase):
    """AI对话页面测试"""

    def setUp(self):
        self.mock_app = Mock(spec=Application)
        self.ai_dialog_page = AIDialogPage(self.mock_app)

    def test_ai_dialog_creation(self):
        """测试AI对话页面创建"""
        self.assertIsInstance(self.ai_dialog_page, AIDialogPage)
        self.assertEqual(self.ai_dialog_page.page_name, "ai_dialog")

    def test_message_sending(self):
        """测试消息发送"""
        with patch.object(self.ai_dialog_page, '_process_message') as mock_process:
            message = "测试消息"
            self.ai_dialog_page._on_message_sent(message)
            mock_process.assert_called_once_with(message)

    def test_context_switching(self):
        """测试上下文切换"""
        initial_context = self.ai_dialog_page.current_context
        self.ai_dialog_page._on_context_changed("通用助手")
        self.assertEqual(self.ai_dialog_page.current_context, "通用助手")
        self.assertNotEqual(self.ai_dialog_page.current_context, initial_context)

    def test_clear_chat(self):
        """测试清空聊天"""
        with patch.object(self.ai_dialog_page.chat_widget, 'clear_chat') as mock_clear:
            self.ai_dialog_page._clear_chat()
            mock_clear.assert_called_once()

    def test_export_chat(self):
        """测试导出聊天"""
        with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName') as mock_dialog:
            mock_dialog.return_value = ("test_chat.txt", "")
            with patch.object(self.ai_dialog_page.chat_widget, 'export_chat') as mock_export:
                self.ai_dialog_page._export_chat()
                mock_dialog.assert_called_once()
                mock_export.assert_called_once_with("test_chat.txt")


if __name__ == '__main__':
    unittest.main()