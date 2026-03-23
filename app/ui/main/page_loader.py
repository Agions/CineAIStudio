"""
页面加载器 - 处理页面动态加载
"""

from typing import Dict, Any, Optional
import logging


class PageLoader:
    """页面加载器"""
    
    # 页面配置映射
    PAGES_CONFIG = [
        {"id": "projects", "name": "项目页面", "class": "ProjectsPage", "attribute": "projects_page"},
        {"id": "video_editor", "name": "视频编辑器页面", "class": "VideoEditorPage", "attribute": "video_editor_page"},
        {"id": "ai_video_creator", "name": "AI视频创作页面", "class": "AIVideoCreatorPage", "attribute": "ai_video_creator_page"},
        {"id": "ai_chat", "name": "AI聊天页面", "class": "AIChatPage", "attribute": "ai_chat_page"},
        {"id": "settings", "name": "设置页面", "class": "SettingsPage", "attribute": "settings_page"},
    ]
    
    @staticmethod
    def get_page_class(page_class_name: str):
        """获取页面类"""
        mapping = {
            "ProjectsPage": "app.ui.main.pages.projects_page",
            "VideoEditorPage": "app.ui.main.pages.video_editor_page",
            "AIVideoCreatorPage": "app.ui.main.pages.ai_video_creator_page",
            "AIChatPage": "app.ui.main.pages.ai_chat_page",
            "SettingsPage": "app.ui.main.pages.settings_page",
        }
        
        module_path = mapping.get(page_class_name)
        if not module_path:
            raise ImportError(f"未知的页面类: {page_class_name}")
        
        # 延迟导入
        from importlib import import_module
        module = import_module(module_path)
        return getattr(module, page_class_name)
    
    @staticmethod
    def get_pages_to_load() -> list:
        """获取要加载的页面列表"""
        return PageLoader.PAGES_CONFIG.copy()
    
    @staticmethod
    def validate_page_config(config: Dict[str, str]) -> bool:
        """验证页面配置"""
        required_keys = ["id", "name", "class", "attribute"]
        return all(key in config for key in required_keys)
