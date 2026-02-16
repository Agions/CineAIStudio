"""
项目管理器
管理项目生命周期
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum, auto


class ProjectStatus(Enum):
    """项目状态"""
    CREATED = auto()
    ANALYZING = auto()
    PLANNING = auto()
    EDITING = auto()
    COLORING = auto()
    SOUNDING = auto()
    VFXING = auto()
    REVIEWING = auto()
    EXPORTING = auto()
    COMPLETED = auto()
    ERROR = auto()


@dataclass
class Project:
    """项目"""
    id: str
    name: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    source_files: List[str]
    output_path: str
    config: Dict[str, Any]
    metadata: Dict[str, Any]
    agent_results: Dict[str, Any]


class ProjectManager:
    """
    项目管理器
    
    管理项目：
    - 创建/删除项目
    - 保存/加载项目
    - 项目状态跟踪
    - 项目历史记录
    """
    
    def __init__(self, projects_dir: Optional[str] = None):
        if projects_dir is None:
            projects_dir = os.path.join(
                os.path.expanduser('~'),
                'CineFlow',
                'Projects'
            )
            
        self.projects_dir = projects_dir
        os.makedirs(projects_dir, exist_ok=True)
        
        # 项目缓存
        self._projects: Dict[str, Project] = {}
        
        # 加载现有项目
        self._load_projects()
        
    def _load_projects(self):
        """加载所有项目"""
        for project_dir in Path(self.projects_dir).iterdir():
            if project_dir.is_dir():
                project_file = project_dir / 'project.json'
                if project_file.exists():
                    try:
                        with open(project_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                        project = Project(
                            id=data['id'],
                            name=data['name'],
                            status=ProjectStatus[data['status']],
                            created_at=datetime.fromisoformat(data['created_at']),
                            updated_at=datetime.fromisoformat(data['updated_at']),
                            source_files=data.get('source_files', []),
                            output_path=data.get('output_path', ''),
                            config=data.get('config', {}),
                            metadata=data.get('metadata', {}),
                            agent_results=data.get('agent_results', {})
                        )
                        
                        self._projects[project.id] = project
                        
                    except Exception as e:
                        print(f"加载项目失败 {project_dir}: {e}")
                        
    def create_project(
        self,
        name: str,
        source_files: List[str],
        config: Optional[Dict[str, Any]] = None
    ) -> Project:
        """创建新项目"""
        import uuid
        
        project_id = str(uuid.uuid4())[:8]
        
        # 创建项目目录
        project_dir = os.path.join(self.projects_dir, project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        # 创建子目录
        for subdir in ['source', 'output', 'temp', 'cache']:
            os.makedirs(os.path.join(project_dir, subdir), exist_ok=True)
            
        # 创建项目
        now = datetime.now()
        project = Project(
            id=project_id,
            name=name,
            status=ProjectStatus.CREATED,
            created_at=now,
            updated_at=now,
            source_files=source_files,
            output_path=os.path.join(project_dir, 'output'),
            config=config or {},
            metadata={
                'version': '3.0.0',
                'platform': self._get_platform()
            },
            agent_results={}
        )
        
        # 保存项目
        self._projects[project_id] = project
        self._save_project(project)
        
        return project
        
    def _get_platform(self) -> str:
        """获取平台"""
        import sys
        if sys.platform == 'darwin':
            return 'macos'
        elif sys.platform == 'win32':
            return 'windows'
        else:
            return 'linux'
            
    def _save_project(self, project: Project):
        """保存项目到文件"""
        project_dir = os.path.join(self.projects_dir, project.id)
        project_file = os.path.join(project_dir, 'project.json')
        
        data = {
            'id': project.id,
            'name': project.name,
            'status': project.status.name,
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat(),
            'source_files': project.source_files,
            'output_path': project.output_path,
            'config': project.config,
            'metadata': project.metadata,
            'agent_results': project.agent_results
        }
        
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def get_project(self, project_id: str) -> Optional[Project]:
        """获取项目"""
        return self._projects.get(project_id)
        
    def get_all_projects(self) -> List[Project]:
        """获取所有项目"""
        return list(self._projects.values())
        
    def get_projects_by_status(self, status: ProjectStatus) -> List[Project]:
        """按状态获取项目"""
        return [
            p for p in self._projects.values()
            if p.status == status
        ]
        
    def update_project_status(
        self,
        project_id: str,
        status: ProjectStatus
    ) -> bool:
        """更新项目状态"""
        project = self._projects.get(project_id)
        if not project:
            return False
            
        project.status = status
        project.updated_at = datetime.now()
        
        self._save_project(project)
        return True
        
    def update_agent_result(
        self,
        project_id: str,
        agent_name: str,
        result: Dict[str, Any]
    ) -> bool:
        """更新Agent结果"""
        project = self._projects.get(project_id)
        if not project:
            return False
            
        project.agent_results[agent_name] = {
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        
        project.updated_at = datetime.now()
        self._save_project(project)
        return True
        
    def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        project = self._projects.get(project_id)
        if not project:
            return False
            
        # 删除项目目录
        import shutil
        project_dir = os.path.join(self.projects_dir, project_id)
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
            
        # 从缓存移除
        del self._projects[project_id]
        
        return True
        
    def duplicate_project(self, project_id: str, new_name: str) -> Optional[Project]:
        """复制项目"""
        project = self._projects.get(project_id)
        if not project:
            return None
            
        # 创建新项目
        new_project = self.create_project(
            name=new_name,
            source_files=project.source_files.copy(),
            config=project.config.copy()
        )
        
        # 复制元数据
        new_project.metadata = project.metadata.copy()
        
        self._save_project(new_project)
        
        return new_project
        
    def export_project(self, project_id: str, export_path: str) -> str:
        """导出项目为压缩包"""
        import shutil
        
        project = self._projects.get(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")
            
        project_dir = os.path.join(self.projects_dir, project_id)
        
        # 创建压缩包
        archive_path = shutil.make_archive(
            export_path,
            'zip',
            project_dir
        )
        
        return archive_path
        
    def import_project(self, archive_path: str) -> Optional[Project]:
        """导入项目"""
        import shutil
        import zipfile
        
        if not os.path.exists(archive_path):
            raise FileNotFoundError(f"文件不存在: {archive_path}")
            
        # 解压到临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
                
            # 查找项目文件
            for item in Path(tmpdir).iterdir():
                if item.is_dir():
                    project_file = item / 'project.json'
                    if project_file.exists():
                        # 读取项目信息
                        with open(project_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                        # 创建新项目ID
                        import uuid
                        new_id = str(uuid.uuid4())[:8]
                        
                        # 复制到项目目录
                        project_dir = os.path.join(self.projects_dir, new_id)
                        shutil.copytree(item, project_dir)
                        
                        # 更新项目ID
                        data['id'] = new_id
                        data['created_at'] = datetime.now().isoformat()
                        data['updated_at'] = datetime.now().isoformat()
                        
                        with open(os.path.join(project_dir, 'project.json'), 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                            
                        # 重新加载
                        self._load_projects()
                        
                        return self._projects.get(new_id)
                        
        return None
        
    def get_project_stats(self) -> Dict[str, Any]:
        """获取项目统计"""
        total = len(self._projects)
        
        status_counts = {}
        for status in ProjectStatus:
            count = len(self.get_projects_by_status(status))
            status_counts[status.name] = count
            
        # 最近项目
        recent = sorted(
            self._projects.values(),
            key=lambda p: p.updated_at,
            reverse=True
        )[:5]
        
        return {
            'total_projects': total,
            'status_counts': status_counts,
            'recent_projects': [
                {
                    'id': p.id,
                    'name': p.name,
                    'status': p.status.name,
                    'updated_at': p.updated_at.isoformat()
                }
                for p in recent
            ]
        }
        
    def cleanup_temp_files(self, project_id: str):
        """清理临时文件"""
        project = self._projects.get(project_id)
        if not project:
            return
            
        project_dir = os.path.join(self.projects_dir, project_id)
        temp_dir = os.path.join(project_dir, 'temp')
        cache_dir = os.path.join(project_dir, 'cache')
        
        import shutil
        
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            os.makedirs(temp_dir, exist_ok=True)
            
        if os.path.exists(cache_dir):
            # 保留最近7天的缓存
            now = datetime.now()
            for item in Path(cache_dir).iterdir():
                if item.is_file():
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if (now - mtime).days > 7:
                        item.unlink()
