#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
国际化支持模块
提供完整的多语言切换功能
"""

from typing import Dict, List
import logging
logger = logging.getLogger(__name__)


class I18n:
    """
    国际化管理器
    
    支持多语言切换，完整UI翻译
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
        from .i18n_data import get_translations
        builtins = get_translations()
        self._fallback = builtins.get("en-US", {})

        if self._locale in builtins:
            self._translations = builtins[self._locale]
        else:
            self._translations = self._fallback

    def set_locale(self, locale: str):
        """设置语言"""
        if locale in self.SUPPORTED_LANGUAGES:
            self._locale = locale
            self._load_translations()
    
    def get_locale(self) -> str:
        """获取当前语言"""
        return self._locale
    
    def t(self, key: str, **kwargs) -> str:
        """翻译文本"""
        text = self._translations.get(key) or self._fallback.get(key) or key
        
        if kwargs:
            try:
                text = text.format(**kwargs)
            except Exception:
                logger.debug("Operation failed")
                
        return text
    
    def get_available_locales(self) -> Dict[str, str]:
        """获取可用语言列表"""
        return self.SUPPORTED_LANGUAGES.copy()
    
    def get_all_keys(self) -> List[str]:
        """获取所有翻译键"""
        return list(self._fallback.keys())


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


def get_available_locales() -> Dict[str, str]:
    """获取可用语言"""
    return _i18n.get_available_locales()
