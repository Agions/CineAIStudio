#!/usr/bin/env python3
"""测试统一配置加载器"""

import os
import tempfile
from pathlib import Path
import pytest


def test_unified_config_defaults():
    """测试默认配置"""
    from app.core.unified_config import UnifiedConfig
    
    config = UnifiedConfig(project_root=Path(tempfile.mkdtemp())).load()
    
    assert config.get("app.name") == "ClipFlow"
    assert config.get("app.version") == "2.0.0-rc.1"
    assert config.get("LLM.default_provider") == "qwen"
    assert config.get("LLM.timeout") == 30
    assert config.get("video.default_fps") == 30


def test_unified_config_dot_path():
    """测试点号路径访问"""
    from app.core.unified_config import UnifiedConfig
    
    config = UnifiedConfig(project_root=Path(tempfile.mkdtemp())).load()
    
    assert config.get("nonexistent.path") is None
    assert config.get("nonexistent.path", "default") == "default"


def test_unified_config_set():
    """测试动态设置"""
    from app.core.unified_config import UnifiedConfig
    
    config = UnifiedConfig(project_root=Path(tempfile.mkdtemp())).load()
    
    config.set("LLM.timeout", 60)
    assert config.get("LLM.timeout") == 60
    
    config.set("custom.nested.key", "value")
    assert config.get("custom.nested.key") == "value"


def test_unified_config_yaml_loading():
    """测试 YAML 配置加载"""
    from app.core.unified_config import UnifiedConfig
    
    tmpdir = Path(tempfile.mkdtemp())
    config_dir = tmpdir / "config"
    config_dir.mkdir()
    
    (config_dir / "llm.yaml").write_text(
        "LLM:\n  default_provider: gemini\n  timeout: 60\n",
        encoding="utf-8"
    )
    
    config = UnifiedConfig(project_root=tmpdir).load()
    assert config.get("LLM.default_provider") == "gemini"
    assert config.get("LLM.timeout") == 60
    # 默认值仍在
    assert config.get("app.name") == "ClipFlow"


def test_unified_config_env_resolution():
    """测试环境变量解析"""
    from app.core.unified_config import UnifiedConfig
    
    os.environ["TEST_CINEFLOW_KEY"] = "test-api-key"
    
    tmpdir = Path(tempfile.mkdtemp())
    config_dir = tmpdir / "config"
    config_dir.mkdir()
    
    (config_dir / "test.yaml").write_text(
        "test:\n  api_key: ${TEST_CINEFLOW_KEY}\n",
        encoding="utf-8"
    )
    
    config = UnifiedConfig(project_root=tmpdir).load()
    assert config.get("test.api_key") == "test-api-key"
    
    del os.environ["TEST_CINEFLOW_KEY"]


def test_unified_config_as_dict():
    """测试导出为字典"""
    from app.core.unified_config import UnifiedConfig
    
    config = UnifiedConfig(project_root=Path(tempfile.mkdtemp())).load()
    d = config.as_dict()
    
    assert isinstance(d, dict)
    assert "app" in d
    assert "LLM" in d
