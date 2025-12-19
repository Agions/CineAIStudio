#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI-EditX 插件系统
提供插件管理、加载和扩展功能
"""

from .plugin_manager import PluginManager
from .plugin_interface import PluginInterface, PluginType, PluginStatus
from .plugin_loader import PluginLoader
from .plugin_registry import PluginRegistry

__all__ = [
    'PluginManager',
    'PluginInterface',
    'PluginType',
    'PluginStatus',
    'PluginLoader',
    'PluginRegistry'
]