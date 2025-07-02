#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from PyQt6.QtCore import QObject, pyqtSignal

from .video_manager import VideoManager, VideoClip


@dataclass
class ProjectInfo:
    """项目信息"""
    id: str
    name: str
    description: str = ""
    created_at: str = ""
    modified_at: str = ""
    file_path: str = ""
    thumbnail_path: str = ""
    video_count: int = 0
    duration: float = 0.0  # 总时长（秒）
    editing_mode: str = "commentary"  # commentary, compilation, monologue
    status: str = "draft"  # draft, editing, processing, completed
    progress: float = 0.0  # 编辑进度 0.0-1.0
    last_edited_feature: str = ""  # 最后编辑的AI功能
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.modified_at:
            self.modified_at = self.created_at
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectInfo':
        """从字典创建"""
        return cls(**data)


class ProjectManager(QObject):
    """项目管理器"""
    
    # 信号
    project_created = pyqtSignal(ProjectInfo)
    project_loaded = pyqtSignal(ProjectInfo)
    project_saved = pyqtSignal(ProjectInfo)
    project_deleted = pyqtSignal(str)  # project_id
    project_list_updated = pyqtSignal()
    
    def __init__(self, settings_manager=None):
        super().__init__()
        
        self.settings_manager = settings_manager
        self.video_manager = VideoManager()
        
        # 当前项目
        self.current_project: Optional[ProjectInfo] = None
        self.project_modified = False
        
        # 项目列表缓存
        self._project_list: List[ProjectInfo] = []
        
        # 连接信号
        self.video_manager.video_added.connect(self._on_video_added)
        self.video_manager.video_removed.connect(self._on_video_removed)
    
    def create_project(self, name: str, description: str = "", editing_mode: str = "commentary") -> ProjectInfo:
        """创建新项目"""
        # 创建项目信息
        project = ProjectInfo(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            editing_mode=editing_mode
        )
        
        # 设置项目文件路径
        if self.settings_manager:
            project_dir = self.settings_manager.get_setting("project.default_location")
        else:
            project_dir = str(Path.home() / "VideoEpicCreator" / "Projects")
        
        # 确保项目目录存在
        Path(project_dir).mkdir(parents=True, exist_ok=True)
        
        # 生成项目文件路径
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        project_file = Path(project_dir) / f"{safe_name}_{project.id[:8]}.vecp"
        project.file_path = str(project_file)
        
        # 清空当前视频管理器
        self.video_manager.clear()
        
        # 设置为当前项目
        self.current_project = project
        self.project_modified = False
        
        # 发射信号
        self.project_created.emit(project)
        
        return project
    
    def load_project(self, file_path: str) -> bool:
        """加载项目"""
        try:
            if not os.path.exists(file_path):
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # 解析项目信息
            project_info = project_data.get('project_info', {})
            project = ProjectInfo.from_dict(project_info)
            project.file_path = file_path
            
            # 加载视频数据
            video_data = project_data.get('videos', [])
            timeline_data = project_data.get('timeline', [])
            
            # 清空当前数据
            self.video_manager.clear()
            
            # 加载视频
            for video_info in video_data:
                clip = VideoClip.from_dict(video_info)
                self.video_manager.videos.append(clip)
            
            # 加载时间线
            for timeline_item in timeline_data:
                # TODO: 实现时间线数据加载
                pass
            
            # 设置为当前项目
            self.current_project = project
            self.project_modified = False
            
            # 更新项目列表
            self._update_project_in_list(project)
            
            # 发射信号
            self.project_loaded.emit(project)
            
            return True
            
        except Exception as e:
            print(f"加载项目失败: {e}")
            return False
    
    def save_project(self, file_path: Optional[str] = None) -> bool:
        """保存项目"""
        if not self.current_project:
            return False
        
        try:
            # 确定保存路径
            if file_path:
                self.current_project.file_path = file_path
            elif not self.current_project.file_path:
                return False
            
            # 更新项目信息
            self.current_project.modified_at = datetime.now().isoformat()
            self.current_project.video_count = len(self.video_manager.videos)
            
            # 计算总时长
            total_duration = sum(clip.duration for clip in self.video_manager.videos) / 1000.0
            self.current_project.duration = total_duration
            
            # 准备保存数据
            project_data = {
                'version': '1.0',
                'project_info': self.current_project.to_dict(),
                'videos': [clip.to_dict() for clip in self.video_manager.videos],
                'timeline': [],  # TODO: 实现时间线数据保存
                'ai_settings': {},  # TODO: 实现AI设置保存
                'export_settings': {}  # TODO: 实现导出设置保存
            }
            
            # 保存到文件
            with open(self.current_project.file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
            
            # 更新状态
            self.project_modified = False
            
            # 更新项目列表
            self._update_project_in_list(self.current_project)
            
            # 发射信号
            self.project_saved.emit(self.current_project)
            
            return True
            
        except Exception as e:
            print(f"保存项目失败: {e}")
            return False
    
    def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        try:
            # 从列表中找到项目
            project = None
            for p in self._project_list:
                if p.id == project_id:
                    project = p
                    break
            
            if not project:
                return False
            
            # 删除项目文件
            if project.file_path and os.path.exists(project.file_path):
                os.remove(project.file_path)
            
            # 删除缩略图
            if project.thumbnail_path and os.path.exists(project.thumbnail_path):
                os.remove(project.thumbnail_path)
            
            # 从列表中移除
            self._project_list = [p for p in self._project_list if p.id != project_id]
            
            # 如果是当前项目，清空
            if self.current_project and self.current_project.id == project_id:
                self.current_project = None
                self.video_manager.clear()
            
            # 发射信号
            self.project_deleted.emit(project_id)
            self.project_list_updated.emit()
            
            return True
            
        except Exception as e:
            print(f"删除项目失败: {e}")
            return False
    
    def get_project_list(self) -> List[ProjectInfo]:
        """获取项目列表"""
        if not self._project_list:
            self._load_project_list()
        return self._project_list.copy()
    
    def _load_project_list(self):
        """加载项目列表"""
        self._project_list = []
        
        # 从设置管理器获取项目列表
        if self.settings_manager:
            projects_data = self.settings_manager.get_projects()
            for project_data in projects_data:
                try:
                    project = ProjectInfo.from_dict(project_data)
                    self._project_list.append(project)
                except Exception as e:
                    print(f"加载项目信息失败: {e}")
    
    def _update_project_in_list(self, project: ProjectInfo):
        """更新项目列表中的项目"""
        # 在列表中查找并更新
        for i, p in enumerate(self._project_list):
            if p.id == project.id:
                self._project_list[i] = project
                break
        else:
            # 如果不存在，添加到列表
            self._project_list.append(project)
        
        # 保存到设置管理器
        if self.settings_manager:
            projects_data = [p.to_dict() for p in self._project_list]
            self.settings_manager._projects = projects_data
            self.settings_manager.save_projects()
        
        # 发射信号
        self.project_list_updated.emit()
    
    def _on_video_added(self, clip: VideoClip):
        """视频添加回调"""
        if self.current_project:
            self.project_modified = True
    
    def _on_video_removed(self, index: int):
        """视频移除回调"""
        if self.current_project:
            self.project_modified = True
    
    def is_project_modified(self) -> bool:
        """检查项目是否已修改"""
        return self.project_modified
    
    def get_current_project(self) -> Optional[ProjectInfo]:
        """获取当前项目"""
        return self.current_project

    def update_project_status(self, project_id: str, status: str, progress: float = None, feature: str = None) -> bool:
        """更新项目状态"""
        try:
            # 查找项目
            project = None
            if self.current_project and self.current_project.id == project_id:
                project = self.current_project
            else:
                # 从项目列表中查找
                for p in self._project_list:
                    if p.id == project_id:
                        project = p
                        break

            if not project:
                return False

            # 更新状态
            project.status = status
            project.modified_at = datetime.now().isoformat()

            if progress is not None:
                project.progress = max(0.0, min(1.0, progress))

            if feature:
                project.last_edited_feature = feature

            # 标记为已修改
            if project == self.current_project:
                self.project_modified = True

            # 自动保存
            if project.file_path:
                self.save_project(project.file_path)

            return True

        except Exception as e:
            print(f"更新项目状态失败: {e}")
            return False

    def get_project_by_id(self, project_id: str) -> Optional[ProjectInfo]:
        """根据ID获取项目"""
        if self.current_project and self.current_project.id == project_id:
            return self.current_project

        for project in self._project_list:
            if project.id == project_id:
                return project

        return None

    def update_editing_progress(self, project_id: str, feature: str, progress: float):
        """更新编辑进度"""
        status_map = {
            0.0: "draft",
            0.1: "editing",
            0.5: "processing",
            1.0: "completed"
        }

        # 根据进度确定状态
        status = "editing"
        for threshold, stat in status_map.items():
            if progress >= threshold:
                status = stat

        return self.update_project_status(project_id, status, progress, feature)
