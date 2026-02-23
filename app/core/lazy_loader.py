#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
懒加载模块 - 提升启动性能
"""

import importlib
import logging
from typing import Dict, Any, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class LazyLoader:
    """懒加载器"""
    
    _instance: Optional['LazyLoader'] = None
    _modules: Dict[str, Any] = {}
    _module_aliases = {
        # 核心模块
        "app.core.application": "app.core.application",
        "app.ui.main.main_window": "app.ui.main.main_window",
        
        # AI 服务
        "app.services.ai.llm_manager": "app.services.ai.llm_manager",
        "app.services.ai.scene_analyzer": "app.services.ai.scene_analyzer",
        "app.services.ai.script_generator": "app.services.ai.script_generator",
        
        # 视频服务
        "app.services.video.mashup_maker": "app.services.video.mashup_maker",
        "app.services.video.commentary_maker": "app.services.video.commentary_maker",
        
        # 导出服务
        "app.services.export.jianying_exporter": "app.services.export.jianying_exporter",
        "app.services.export.premiere_exporter": "app.services.export.premiere_exporter",
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get(self, module_path: str) -> Any:
        """懒加载获取模块"""
        if module_path in self._modules:
            return self._modules[module_path]
        
        # 解析模块路径
        actual_path = self._module_aliases.get(module_path, module_path)
        
        try:
            module = importlib.import_module(actual_path)
            self._modules[module_path] = module
            logger.debug(f"Lazy loaded: {module_path}")
            return module
        except ImportError as e:
            logger.error(f"Failed to lazy load {module_path}: {e}")
            return None
    
    def preload(self, module_paths: list) -> None:
        """预加载模块"""
        for path in module_paths:
            if path not in self._modules:
                self.get(path)
    
    def clear_cache(self) -> None:
        """清除缓存"""
        self._modules.clear()


# 全局实例
lazy_loader = LazyLoader()


def lazy_import(module_path: str):
    """装饰器：延迟导入"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            module = lazy_loader.get(module_path)
            if module is None:
                raise ImportError(f"Cannot load module: {module_path}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


# 常用模块快捷访问
def get_llm_manager():
    """获取 LLM 管理器"""
    return lazy_loader.get("app.services.ai.llm_manager")

def get_scene_analyzer():
    """获取场景分析器"""
    return lazy_loader.get("app.services.ai.scene_analyzer")

def get_script_generator():
    """获取脚本生成器"""
    return lazy_loader.get("app.services.ai.script_generator")

def get_mashup_maker():
    """获取混剪制作器"""
    return lazy_loader.get("app.services.video.mashup_maker")

def get_commentary_maker():
    """获取解说制作器"""
    return lazy_loader.get("app.services.video.commentary_maker")

def preload_core_modules() -> None:
    """预加载核心模块"""
    core_modules = [
        "app.core.application",
        "app.ui.main.main_window",
    ]
    lazy_loader.preload(core_modules)
    logger.info("Core modules preloaded")
