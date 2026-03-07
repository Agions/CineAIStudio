#!/usr/bin/env python3
"""测试项目版本管理器"""

import pytest
from datetime import datetime
from dataclasses import asdict

from app.core.project_version_manager import (
    ProjectVersion,
    ProjectVersionManager,
)


class TestProjectVersion:
    """测试项目版本数据类"""

    def test_creation(self):
        """测试创建"""
        version = ProjectVersion(
            version_id="v1.0.0",
            timestamp=datetime.now(),
            description="初始版本",
            changes=["创建项目"],
            file_hash="abc123",
            size=1024,
        )
        
        assert version.version_id == "v1.0.0"
        assert version.description == "初始版本"
        assert version.size == 1024

    def test_to_dict(self):
        """测试转换为字典"""
        version = ProjectVersion(
            version_id="v1.0.0",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            description="测试",
            changes=[],
            file_hash="hash",
            size=100,
        )
        
        d = version.to_dict()
        
        assert d["version_id"] == "v1.0.0"
        assert d["description"] == "测试"

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "version_id": "v1.0.0",
            "timestamp": "2024-01-01T12:00:00",
            "description": "测试版本",
            "changes": ["添加功能"],
            "file_hash": "hash123",
            "size": 2048,
            "tags": ["stable"],
            "is_auto_backup": False,
            "is_major": True,
        }
        
        version = ProjectVersion.from_dict(data)
        
        assert version.version_id == "v1.0.0"
        assert version.tags == ["stable"]
        assert version.is_major is True


class TestProjectVersionManager:
    """测试项目版本管理器"""

    def test_init_default(self):
        """测试默认初始化"""
        manager = ProjectVersionManager()
        
        assert manager._versions is not None
        assert manager._versions_dir == ""

    def test_init_custom_dir(self):
        """测试自定义目录"""
        manager = ProjectVersionManager(versions_dir="/custom/versions")
        
        assert manager._versions_dir == "/custom/versions"

    def test_create_version_id(self):
        """测试创建版本 ID"""
        manager = ProjectVersionManager()
        
        version_id = manager._create_version_id()
        
        assert version_id.startswith("v")
        assert len(version_id) > 1

    def test_calculate_file_hash(self):
        """测试计算文件哈希"""
        manager = ProjectVersionManager()
        
        # 使用临时文件测试
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            hash_value = manager._calculate_file_hash(temp_path)
            assert hash_value is not None
            assert len(hash_value) > 0
        finally:
            os.unlink(temp_path)

    def test_parse_version_string(self):
        """测试解析版本字符串"""
        manager = ProjectVersionManager()
        
        # 测试标准版本格式
        major, minor, patch = manager._parse_version_string("1.2.3")
        
        assert major == 1
        assert minor == 2
        assert patch == 3

    def test_parse_invalid_version(self):
        """测试解析无效版本"""
        manager = ProjectVersionManager()
        
        major, minor, patch = manager._parse_version_string("invalid")
        
        assert major == 0
        assert minor == 0
        assert patch == 0


class TestVersionComparison:
    """测试版本比较"""

    def test_compare_versions(self):
        """测试版本比较"""
        manager = ProjectVersionManager()
        
        # 1.0.0 < 1.0.1 < 1.1.0 < 2.0.0
        assert manager._compare_version("1.0.0", "1.0.1") < 0
        assert manager._compare_version("1.0.1", "1.0.0") > 0
        assert manager._compare_version("1.0.0", "1.0.0") == 0
        assert manager._compare_version("1.1.0", "1.0.9") > 0
        assert manager._compare_version("1.1.0", "1.0.9") > 0
        assert manager._compare_version("2.0.0", "1.9.9") > 0
