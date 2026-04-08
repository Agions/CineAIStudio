"""
页面模块
"""

from .base_page import BasePage
from .home_page import HomePage
from .settings_page import SettingsPage
from .creation_wizard_page import CreationWizardPage

# CreatorPage 暂时禁用 — 底层 FirstPersonNarrator 引用已废弃的相对路径
# from .creator_page import CreatorPage

__all__ = [
    "BasePage",
    "HomePage",
    "SettingsPage",
    "CreationWizardPage",
]
