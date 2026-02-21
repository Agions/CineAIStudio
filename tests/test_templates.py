#!/usr/bin/env python3
"""测试项目模板系统"""

import json
import tempfile
from pathlib import Path
import pytest

from app.core.templates.project_templates import (
    TemplateManager, ProjectTemplate, TemplateCategory,
    VoicePreset, ExportPreset, AIPreset, BUILTIN_TEMPLATES,
)


def test_builtin_templates_exist():
    """内置模板应该存在"""
    assert len(BUILTIN_TEMPLATES) >= 5


def test_template_manager_list():
    """列出所有模板"""
    mgr = TemplateManager()
    templates = mgr.list_templates()
    assert len(templates) >= 5
    
    names = [t.name for t in templates]
    assert any("电影解说" in n for n in names)
    assert any("混剪" in n for n in names)


def test_template_manager_filter_category():
    """按分类筛选"""
    mgr = TemplateManager()
    
    commentary = mgr.list_templates(category=TemplateCategory.COMMENTARY)
    assert all(t.category == TemplateCategory.COMMENTARY for t in commentary)


def test_template_manager_get():
    """获取单个模板"""
    mgr = TemplateManager()
    
    t = mgr.get_template("movie_commentary")
    assert t is not None
    assert t.name == "🎬 电影解说"
    assert t.voice.voice_id == "zh-CN-YunxiNeural"
    
    assert mgr.get_template("nonexistent") is None


def test_template_serialization():
    """模板序列化/反序列化"""
    original = BUILTIN_TEMPLATES[0]
    d = original.to_dict()
    
    assert isinstance(d, dict)
    assert d["category"] == original.category.value
    
    restored = ProjectTemplate.from_dict(d)
    assert restored.id == original.id
    assert restored.name == original.name
    assert restored.category == original.category


def test_user_template_save_load():
    """用户模板保存和加载"""
    tmpdir = tempfile.mkdtemp()
    mgr = TemplateManager(user_template_dir=tmpdir)
    
    custom = ProjectTemplate(
        id="my_template",
        name="我的模板",
        description="测试用",
        category=TemplateCategory.CUSTOM,
        tags=["测试"],
        voice=VoicePreset(voice_id="zh-CN-YunxiNeural"),
    )
    
    mgr.save_as_template(custom)
    
    # 文件应该存在
    assert (Path(tmpdir) / "my_template.json").exists()
    
    # 重新加载
    mgr2 = TemplateManager(user_template_dir=tmpdir)
    loaded = mgr2.get_template("my_template")
    assert loaded is not None
    assert loaded.name == "我的模板"


def test_user_template_delete():
    """删除用户模板"""
    tmpdir = tempfile.mkdtemp()
    mgr = TemplateManager(user_template_dir=tmpdir)
    
    custom = ProjectTemplate(
        id="to_delete",
        name="待删除",
        description="",
        category=TemplateCategory.CUSTOM,
    )
    mgr.save_as_template(custom)
    assert mgr.get_template("to_delete") is not None
    
    # 删除
    assert mgr.delete_template("to_delete") is True
    assert mgr.get_template("to_delete") is None
    
    # 不能删内置模板
    assert mgr.delete_template("movie_commentary") is False


def test_get_categories():
    """获取分类列表"""
    mgr = TemplateManager()
    cats = mgr.get_categories()
    assert len(cats) > 0
    assert any(c["id"] == "commentary" for c in cats)
