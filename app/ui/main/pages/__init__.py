"""
页面模块
"""

from .base_page import BasePage
from .video_editor_page import VideoEditorPage
from .home_page import HomePage
from .settings_page import SettingsPage
from .ai_video_creator_page import AIVideoCreatorPage

__all__ = [
    'BasePage',
    'VideoEditorPage',
    'HomePage',
    'SettingsPage',
    'AIVideoCreatorPage',
]