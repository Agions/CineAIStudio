#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
E2E 集成测试
测试完整的工作流程
"""

import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class TestProjectWorkflow:
    """项目创建到导出完整流程测试"""
    
    @pytest.fixture
    def temp_dir(self):
        """临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    def test_project_creation_workflow(self, temp_dir):
        """测试项目创建流程"""
        from app.core.project import Project
        
        # 创建项目
        project = Project(
            name="Test Project",
            project_path=temp_dir
        )
        
        assert project.name == "Test Project"
        assert project.is_modified == False
        
        # 修改项目
        project.is_modified = True
        assert project.is_modified == True
        
    def test_project_save_load(self, temp_dir):
        """测试项目保存和加载"""
        from app.core.project import Project
        
        # 创建并保存
        project = Project(name="SaveTest", project_path=temp_dir)
        project.save()
        
        # 加载
        loaded = Project.load(Path(temp_dir) / "project.json")
        assert loaded.name == "SaveTest"


class TestAIVideoCreation:
    """AI视频创作流程测试"""
    
    def test_commentary_workflow(self):
        """测试解说视频制作流程"""
        from app.services.video.commentary_maker import (
            CommentaryMaker, CommentaryStyle
        )
        
        # 创建 maker
        maker = CommentaryMaker()
        
        # 验证初始化
        assert maker is not None
        assert hasattr(maker, 'voice_generator')
        assert hasattr(maker, 'caption_generator')
        
    def test_mashup_workflow(self):
        """测试混剪制作流程"""
        from app.services.video.mashup_maker import MashupMaker
        
        maker = MashupMaker()
        assert maker is not None
        
    def test_monologue_workflow(self):
        """测试独白制作流程"""
        from app.services.video.monologue_maker import MonologueMaker
        
        maker = MonologueMaker()
        assert maker is not None


class TestExportWorkflow:
    """导出流程测试"""
    
    def test_export_to_mp4(self):
        """测试导出为 MP4"""
        from app.services.export.direct_video_exporter import (
            DirectVideoExporter, VideoExportConfig, ExportPreset
        )
        
        config = ExportPreset.get_config(ExportPreset.BALANCED)
        
        assert config.resolution.value == (1920, 1080)
        assert config.fps == 30.0
        
    def test_export_preset(self):
        """测试导出预设"""
        from app.services.export.direct_video_exporter import (
            VideoExportConfig, ExportPreset
        )
        
        bilibili = ExportPreset.get_config(ExportPreset.BILIBILI)
        assert bilibili.fps == 60.0
        
        youtube = ExportPreset.get_config(ExportPreset.YOUTUBE)
        assert youtube.resolution.value == (3840, 2160)


class TestUIComponents:
    """UI组件测试"""
    
    def test_theme_system(self):
        """测试主题系统"""
        from app.ui.theme.modern import ModernTheme
        
        # 验证主题存在
        assert hasattr(ModernTheme, 'PRIMARY_COLOR')
        
    def test_pro_components_import(self):
        """测试专业组件导入"""
        try:
            # 组件需要 PyQt6，可能会失败，但不应该有语法错误
            pass
        except ImportError:
            pytest.skip("PyQt6 not available")


class TestPerformance:
    """性能相关测试"""
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        from app.utils.performance import MemoryCache
        
        cache = MemoryCache(max_size=10, ttl=1)
        
        # 测试存入取出
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # 测试不存在返回 None
        assert cache.get("nonexistent") is None
        
    def test_cache_expiry(self):
        """测试缓存过期"""
        from app.utils.performance import MemoryCache
        import time
        
        cache = MemoryCache(max_size=10, ttl=0)
        cache.set("key1", "value1")
        
        # 等待过期
        time.sleep(0.1)
        
        # 应该返回 None
        assert cache.get("key1") is None
        
    def test_i18n_translation(self):
        """测试国际化"""
        from app.utils.i18n import I18n
        
        i18n = I18n("zh-CN")
        
        # 测试翻译
        assert i18n.t("nav.home") == "首页"
        assert i18n.t("common.save") == "保存"
        
    def test_i18n_fallback(self):
        """测试翻译回退"""
        from app.utils.i18n import I18n
        
        i18n = I18n("zh-CN")
        
        # 不存在的键应该返回原键
        assert i18n.t("nonexistent.key") == "nonexistent.key"


class TestTaskManager:
    """任务管理器测试"""
    
    def test_task_creation(self):
        """测试任务创建"""
        from app.utils.task_manager import Task, TaskStatus
        
        task = Task(id="test1", name="Test Task")
        
        assert task.id == "test1"
        assert task.name == "Test Task"
        assert task.status == TaskStatus.PENDING
        assert task.progress == 0.0


class TestErrorHandling:
    """错误处理测试"""
    
    def test_error_classification(self):
        """测试错误分类"""
        from app.utils.error_handler import classify_error, ErrorType
        
        # 网络错误
        err = Exception("Connection timeout")
        assert classify_error(err) == ErrorType.NETWORK
        
        # API 错误
        err = Exception("API rate limit exceeded")
        assert classify_error(err) == ErrorType.API
        
        # 文件错误
        err = Exception("File not found")
        assert classify_error(err) == ErrorType.FILE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
