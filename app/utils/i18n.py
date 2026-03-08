#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
国际化支持模块
提供多语言切换功能
"""

import os
import json
from typing import Dict, Optional
from pathlib import Path


class I18n:
    """
    国际化管理器
    
    支持多语言切换
    """
    
    # 支持的语言
    SUPPORTED_LANGUAGES = {
        "zh-CN": "简体中文",
        "zh-TW": "繁體中文",
        "en-US": "English",
        "ja-JP": "日本語",
        "ko-KR": "한국어",
    }
    
    def __init__(self, locale: str = "zh-CN"):
        self._locale = locale
        self._translations: Dict[str, str] = {}
        self._fallback: Dict[str, str] = {}
        self._load_translations()
        
    def _load_translations(self):
        """加载翻译文件"""
        # 内置翻译
        builtins = self._get_builtin_translations()
        self._fallback = builtins.get("en-US", {})
        
        # 加载指定语言
        if self._locale in builtins:
            self._translations = builtins[self._locale]
        else:
            self._translations = self._fallback
    
    def _get_builtin_translations(self) -> Dict[str, Dict]:
        """获取内置翻译"""
        return {
            "zh-CN": {
                # 导航
                "nav.home": "首页",
                "nav.projects": "项目管理",
                "nav.editor": "视频剪辑",
                "nav.ai_create": "AI创作",
                "nav.ai_chat": "AI对话",
                "nav.settings": "设置",
                
                # 首页
                "home.welcome": "欢迎使用 ClipFlowCut",
                "home.subtitle": "AI 驱动的专业视频创作平台",
                "home.new_project": "新建项目",
                "home.import": "导入素材",
                "home.recent": "最近创作",
                
                # 项目
                "project.new": "新建项目",
                "project.open": "打开项目",
                "project.delete": "删除项目",
                "project.export": "导出项目",
                
                # 通用
                "common.save": "保存",
                "common.cancel": "取消",
                "common.confirm": "确认",
                "common.delete": "删除",
                "common.edit": "编辑",
                "common.search": "搜索",
                "common.loading": "加载中...",
                "common.success": "成功",
                "common.error": "错误",
                "common.warning": "警告",
            },
            "en-US": {
                # Navigation
                "nav.home": "Home",
                "nav.projects": "Projects",
                "nav.editor": "Video Editor",
                "nav.ai_create": "AI Create",
                "nav.ai_chat": "AI Chat",
                "nav.settings": "Settings",
                
                # Home
                "home.welcome": "Welcome to ClipFlowCut",
                "home.subtitle": "AI-Powered Video Creation Platform",
                "home.new_project": "New Project",
                "home.import": "Import",
                "home.recent": "Recent",
                
                # Projects
                "project.new": "New Project",
                "project.open": "Open Project",
                "project.delete": "Delete Project",
                "project.export": "Export Project",
                
                # Common
                "common.save": "Save",
                "common.cancel": "Cancel",
                "common.confirm": "Confirm",
                "common.delete": "Delete",
                "common.edit": "Edit",
                "common.search": "Search",
                "common.loading": "Loading...",
                "common.success": "Success",
                "common.error": "Error",
                "common.warning": "Warning",
            },
        }
    
    def set_locale(self, locale: str):
        """设置语言"""
        if locale in self.SUPPORTED_LANGUAGES:
            self._locale = locale
            self._load_translations()
    
    def get_locale(self) -> str:
        """获取当前语言"""
        return self._locale
    
    def t(self, key: str, **kwargs) -> str:
        """
        翻译文本
        
        Args:
            key: 翻译键
            **kwargs: 格式化参数
            
        Returns:
            翻译后的文本
        """
        # 优先使用当前语言
        text = self._translations.get(key)
        if text is None:
            # 使用备用语言
            text = self._fallback.get(key)
        if text is None:
            # 返回原始键
            return key
        
        # 格式化
        if kwargs:
            try:
                text = text.format(**kwargs)
            except Exception:
                pass
                
        return text
    
    def get_available_locales(self) -> Dict[str, str]:
        """获取可用语言列表"""
        return self.SUPPORTED_LANGUAGES.copy()


# 全局实例
_i18n = I18n()


def t(key: str, **kwargs) -> str:
    """快捷翻译函数"""
    return _i18n.t(key, **kwargs)


def set_locale(locale: str):
    """设置语言"""
    _i18n.set_locale(locale)


def get_locale() -> str:
    """获取当前语言"""
    return _i18n.get_locale()
