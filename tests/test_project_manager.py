#!/usr/bin/env python3
"""测试项目管理器"""

import os
import json
import tempfile
import shutil
import pytest
from datetime import datetime

from app.core.project_manager import (
    ProjectManager,
    ProjectMetadata,
    ProjectStatus,
    ProjectType,
)


@pytest.fixture
def temp_project_dir():
    """创建临时项目目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def project_manager(temp_project_dir):
    """创建项目管理器实例"""
    return ProjectManager(project_root=temp_project_dir)


def test_create_project(project_manager):
    """测试创建项目"""
    metadata = ProjectMetadata(
        name="测试项目",
        description="这是一个测试项目"
    )
    
    project = project_manager.create_project(metadata)
    
    assert project is not None
    assert project.metadata.name == "测试项目"
    assert project.metadata.description == "这是一个测试项目"
    assert project.metadata.status == ProjectStatus.ACTIVE


def test_list_projects(project_manager):
    """测试列出项目"""
    # 创建两个测试项目
    metadata1 = ProjectMetadata(name="项目1")
    metadata2 = ProjectMetadata(name="项目2")
    
    project_manager.create_project(metadata1)
    project_manager.create_project(metadata2)
    
    projects = project_manager.list_projects()
    
    assert len(projects) == 2


def test_get_project(project_manager):
    """测试获取项目"""
    metadata = ProjectMetadata(name="测试项目")
    created = project_manager.create_project(metadata)
    
    retrieved = project_manager.get_project(created.id)
    
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.metadata.name == "测试项目"


def test_delete_project(project_manager):
    """测试删除项目"""
    metadata = ProjectMetadata(name="测试项目")
    project = project_manager.create_project(metadata)
    
    result = project_manager.delete_project(project.id)
    
    assert result is True
    assert project_manager.get_project(project.id) is None


def test_update_project_metadata(project_manager):
    """测试更新项目元数据"""
    metadata = ProjectMetadata(name="原始名称")
    project = project_manager.create_project(metadata)
    
    # 更新名称
    project.metadata.name = "新名称"
    project_manager.update_project(project)
    
    # 验证更新
    updated = project_manager.get_project(project.id)
    assert updated.metadata.name == "新名称"


def test_archive_project(project_manager):
    """测试归档项目"""
    metadata = ProjectMetadata(name="测试项目")
    project = project_manager.create_project(metadata)
    
    project_manager.archive_project(project.id)
    
    archived = project_manager.get_project(project.id)
    assert archived.metadata.status == ProjectStatus.ARCHIVED
