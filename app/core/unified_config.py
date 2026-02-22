#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlow 统一配置加载器
合并 YAML、.env、QSettings 等多源配置为单一接口
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional


def _load_yaml(path: Path) -> Dict[str, Any]:
    """加载 YAML 配置"""
    try:
        import yaml
    except ImportError:
        return {}

    if not path.exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def _load_env(path: Path) -> Dict[str, str]:
    """加载 .env 文件"""
    env_vars = {}
    if not path.exists():
        return env_vars

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                env_vars[key] = value
    return env_vars


def _resolve_env_vars(obj: Any) -> Any:
    """递归替换 ${ENV_VAR} 占位符"""
    if isinstance(obj, dict):
        return {k: _resolve_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_resolve_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        if obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]
            return os.getenv(env_var, obj)
        return obj
    return obj


class UnifiedConfig:
    """
    统一配置管理器

    加载优先级（高覆盖低）：
    1. 环境变量
    2. .env 文件
    3. config/*.yaml 文件
    4. 内置默认值
    """

    def __init__(self, project_root: Optional[Path] = None):
        self._project_root = project_root or Path(__file__).parent.parent.parent
        self._config = {}  # type: Dict[str, Any]
        self._defaults = {
            "app": {
                "name": "ClipFlow",
                "version": "2.0.0-rc.1",
                "debug": False,
                "language": "zh-CN",
            },
            "LLM": {
                "default_provider": "qwen",
                "timeout": 30,
                "max_retries": 3,
            },
            "video": {
                "max_resolution": "1080p",
                "default_fps": 30,
                "cache_enabled": True,
            },
            "export": {
                "default_format": "jianying",
                "output_dir": "output",
            },
        }
        self._loaded = False

    def load(self) -> "UnifiedConfig":
        """加载所有配置源"""
        # 1. 从默认值开始
        self._config = self._deep_copy(self._defaults)

        # 2. 加载 YAML 配置
        config_dir = self._project_root / "config"
        if config_dir.exists():
            for yaml_file in sorted(config_dir.glob("*.yaml")):
                yaml_data = _load_yaml(yaml_file)
                self._deep_merge(self._config, yaml_data)

        # 3. 加载 .env 文件
        env_path = self._project_root / ".env"
        env_vars = _load_env(env_path)
        for key, value in env_vars.items():
            os.environ.setdefault(key, value)

        # 4. 解析环境变量占位符
        self._config = _resolve_env_vars(self._config)

        self._loaded = True
        return self

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号分隔的路径

        Args:
            key: 配置键，如 "LLM.default_provider"
            default: 默认值

        Returns:
            配置值
        """
        parts = key.split(".")
        obj = self._config
        for part in parts:
            if isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                return default
        return obj

    def set(self, key: str, value: Any) -> None:
        """动态设置配置值"""
        parts = key.split(".")
        obj = self._config
        for part in parts[:-1]:
            if part not in obj or not isinstance(obj[part], dict):
                obj[part] = {}
            obj = obj[part]
        obj[parts[-1]] = value

    def get_section(self, section: str) -> Dict[str, Any]:
        """获取整个配置节"""
        return self._config.get(section, {})

    def as_dict(self) -> Dict[str, Any]:
        """返回完整配置字典"""
        return self._deep_copy(self._config)

    @staticmethod
    def _deep_merge(base: Dict, override: Dict) -> Dict:
        """深度合并字典"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                UnifiedConfig._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    @staticmethod
    def _deep_copy(obj: Any) -> Any:
        """深拷贝"""
        import copy
        return copy.deepcopy(obj)


# 全局配置实例
_config_instance = None


def get_config(project_root: Optional[Path] = None) -> UnifiedConfig:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = UnifiedConfig(project_root).load()
    return _config_instance
