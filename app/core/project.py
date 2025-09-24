#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 项目核心类
提供项目文件的创建、加载、保存和管理功能
"""

import os
import json
import uuid
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum
import logging

from PyQt6.QtCore import QObject, pyqtSignal


class ProjectStatus(Enum):
    """项目状态枚举"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    TEMPLATE = "template"
    CORRUPTED = "corrupted"


class ProjectType(Enum):
    """项目类型枚举"""
    VIDEO_EDITING = "video_editing"
    AI_ENHANCEMENT = "ai_enhancement"
    COMPILATION = "compilation"
    COMMENTARY = "commentary"
    MULTIMEDIA = "multimedia"


@dataclass
class ProjectMetadata:
    """项目元数据"""
    name: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    author: str = ""
    tags: List[str] = field(default_factory=list)
    thumbnail_path: Optional[str] = None
    project_type: ProjectType = ProjectType.VIDEO_EDITING
    status: ProjectStatus = ProjectStatus.ACTIVE

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 转换datetime对象为字符串
        data['created_at'] = self.created_at.isoformat()
        data['modified_at'] = self.modified_at.isoformat()
        data['project_type'] = self.project_type.value
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectMetadata':
        """从字典创建实例"""
        # 转换字符串为datetime对象
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('modified_at'), str):
            data['modified_at'] = datetime.fromisoformat(data['modified_at'])

        # 转换枚举值
        if isinstance(data.get('project_type'), str):
            data['project_type'] = ProjectType(data['project_type'])
        if isinstance(data.get('status'), str):
            data['status'] = ProjectStatus(data['status'])

        return cls(**data)


@dataclass
class ProjectSettings:
    """项目设置"""
    video_resolution: str = "1920x1080"
    video_fps: int = 30
    video_bitrate: str = "8000k"
    audio_sample_rate: int = 44100
    audio_bitrate: str = "192k"
    auto_save_interval: int = 300  # 秒
    backup_enabled: bool = True
    backup_count: int = 10
    ai_settings: Dict[str, Any] = field(default_factory=dict)
    export_settings: Dict[str, Any] = field(default_factory=dict)
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectMedia:
    """项目媒体文件"""
    id: str
    file_path: str
    media_type: str  # video, audio, image
    duration: Optional[float] = None
    size: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectMedia':
        return cls(**data)


@dataclass
class ProjectTimeline:
    """项目时间线"""
    tracks: List[Dict[str, Any]] = field(default_factory=list)
    duration: float = 0.0
    markers: List[Dict[str, Any]] = field(default_factory=list)
    effects: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectTimeline':
        return cls(**data)


class Project(QObject):
    """项目类"""

    # 信号定义
    modified_changed = pyqtSignal(bool)    # 项目修改状态变化信号
    media_added = pyqtSignal(str)         # 媒体文件添加信号
    media_removed = pyqtSignal(str)       # 媒体文件移除信号
    settings_changed = pyqtSignal()        # 设置变更信号

    def __init__(self, project_id: str, project_path: str, metadata: ProjectMetadata):
        super().__init__()
        self.id = project_id
        self.path = project_path
        self.metadata = metadata
        self.settings = ProjectSettings()
        self.media_files: Dict[str, ProjectMedia] = {}
        self.timeline = ProjectTimeline()
        self.is_modified = False
        self.is_loaded = False

    def add_media_file(self, media_file: ProjectMedia) -> None:
        """添加媒体文件"""
        self.media_files[media_file.id] = media_file
        self.is_modified = True
        self.metadata.modified_at = datetime.now()
        self.media_added.emit(media_file.id)
        self.modified_changed.emit(True)

    def remove_media_file(self, media_id: str) -> bool:
        """移除媒体文件"""
        if media_id in self.media_files:
            del self.media_files[media_id]
            self.is_modified = True
            self.metadata.modified_at = datetime.now()
            self.media_removed.emit(media_id)
            self.modified_changed.emit(True)
            return True
        return False

    def get_media_file(self, media_id: str) -> Optional[ProjectMedia]:
        """获取媒体文件"""
        return self.media_files.get(media_id)

    def get_all_media_files(self) -> List[ProjectMedia]:
        """获取所有媒体文件"""
        return list(self.media_files.values())

    def update_settings(self, settings: Dict[str, Any]) -> None:
        """更新项目设置"""
        for key, value in settings.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
            else:
                self.settings.custom_settings[key] = value
        self.is_modified = True
        self.metadata.modified_at = datetime.now()
        self.settings_changed.emit()
        self.modified_changed.emit(True)

    def save(self) -> bool:
        """保存项目"""
        try:
            project_data = {
                'metadata': self.metadata.to_dict(),
                'settings': asdict(self.settings),
                'media_files': {k: v.to_dict() for k, v in self.media_files.items()},
                'timeline': self.timeline.to_dict(),
                'version': '2.0.0'
            }

            # 保存主项目文件
            project_file = os.path.join(self.path, 'project.json')
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)

            # 保存项目锁文件
            lock_file = os.path.join(self.path, '.lock')
            with open(lock_file, 'w') as f:
                f.write(str(os.getpid()))

            self.is_modified = False
            self.modified_changed.emit(False)
            return True

        except Exception as e:
            logging.error(f"Failed to save project {self.id}: {e}")
            return False

    def load(self) -> bool:
        """加载项目"""
        try:
            project_file = os.path.join(self.path, 'project.json')
            if not os.path.exists(project_file):
                return False

            with open(project_file, 'r', encoding='utf-8') as f:
                project_data = json.load(f)

            # 加载元数据
            self.metadata = ProjectMetadata.from_dict(project_data['metadata'])

            # 加载设置
            settings_data = project_data.get('settings', {})
            self.settings = ProjectSettings(**settings_data)

            # 加载媒体文件
            self.media_files.clear()
            for media_id, media_data in project_data.get('media_files', {}).items():
                self.media_files[media_id] = ProjectMedia.from_dict(media_data)

            # 加载时间线
            timeline_data = project_data.get('timeline', {})
            self.timeline = ProjectTimeline.from_dict(timeline_data)

            self.is_loaded = True
            self.is_modified = False
            self.modified_changed.emit(False)
            return True

        except Exception as e:
            logging.error(f"Failed to load project {self.id}: {e}")
            return False

    def create_backup(self) -> Optional[str]:
        """创建项目备份"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"
            backup_path = os.path.join(self.path, 'backups', backup_name)

            os.makedirs(backup_path, exist_ok=True)

            # 复制项目文件
            shutil.copy2(os.path.join(self.path, 'project.json'),
                        os.path.join(backup_path, 'project.json'))

            # 创建备份信息文件
            backup_info = {
                'timestamp': timestamp,
                'created_at': datetime.now().isoformat(),
                'project_version': self.metadata.version,
                'description': f"自动备份 - {timestamp}"
            }

            with open(os.path.join(backup_path, 'backup_info.json'), 'w') as f:
                json.dump(backup_info, f, indent=2)

            return backup_path

        except Exception as e:
            logging.error(f"Failed to create backup for project {self.id}: {e}")
            return None

    def cleanup_old_backups(self, keep_count: int = 10) -> None:
        """清理旧备份"""
        try:
            backup_dir = os.path.join(self.path, 'backups')
            if not os.path.exists(backup_dir):
                return

            backups = []
            for backup_name in os.listdir(backup_dir):
                backup_path = os.path.join(backup_dir, backup_name)
                if os.path.isdir(backup_path):
                    backup_info_file = os.path.join(backup_path, 'backup_info.json')
                    if os.path.exists(backup_info_file):
                        with open(backup_info_file, 'r') as f:
                            backup_info = json.load(f)
                            backups.append((backup_path, backup_info['timestamp']))

            # 按时间戳排序，保留最新的keep_count个备份
            backups.sort(key=lambda x: x[1], reverse=True)
            for backup_path, _ in backups[keep_count:]:
                shutil.rmtree(backup_path)

        except Exception as e:
            logging.error(f"Failed to cleanup backups for project {self.id}: {e}")

    def get_project_info(self) -> Dict[str, Any]:
        """获取项目信息"""
        return {
            'id': self.id,
            'name': self.metadata.name,
            'description': self.metadata.description,
            'path': self.path,
            'created_at': self.metadata.created_at.isoformat(),
            'modified_at': self.metadata.modified_at.isoformat(),
            'project_type': self.metadata.project_type.value,
            'status': self.metadata.status.value,
            'media_count': len(self.media_files),
            'duration': self.timeline.duration,
            'is_modified': self.is_modified,
            'is_loaded': self.is_loaded
        }