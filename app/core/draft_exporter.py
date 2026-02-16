"""
剪映草稿导出器
将项目导出为剪映草稿格式
"""

import json
import os
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class DraftMaterial:
    """草稿素材"""
    id: str
    type: str  # "video", "audio", "text"
    path: str
    name: str
    duration: float
    width: int = 0
    height: int = 0
    fps: float = 30.0


@dataclass
class DraftTrack:
    """草稿轨道"""
    id: str
    type: str  # "video", "audio", "text"
    segments: List[Dict[str, Any]]


@dataclass
class DraftProject:
    """草稿项目"""
    name: str
    duration: float
    width: int
    height: int
    fps: float
    materials: List[DraftMaterial]
    tracks: List[DraftTrack]


class DraftExporter:
    """
    剪映草稿导出器
    
    支持导出到剪映专业版和剪映电脑版
    """
    
    # 剪映草稿路径
    JIANYING_DRAFT_PATHS = {
        'windows': [
            os.path.expandvars(r'%LOCALAPPDATA%\JianyingPro\User Data\Projects\com.lveditor.draft'),
            os.path.expandvars(r'%LOCALAPPDATA%\Jianying\User Data\Projects\com.lveditor.draft'),
        ],
        'macos': [
            os.path.expanduser('~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft'),
            os.path.expanduser('~/Movies/Jianying/User Data/Projects/com.lveditor.draft'),
        ]
    }
    
    def __init__(self, platform: str = 'auto'):
        if platform == 'auto':
            import sys
            if sys.platform == 'darwin':
                self.platform = 'macos'
            else:
                self.platform = 'windows'
        else:
            self.platform = platform
            
    def find_draft_path(self) -> Optional[str]:
        """查找剪映草稿目录"""
        paths = self.JIANYING_DRAFT_PATHS.get(self.platform, [])
        
        for path in paths:
            if os.path.exists(path):
                return path
                
        return None
        
    def export(
        self,
        project: DraftProject,
        output_path: Optional[str] = None
    ) -> str:
        """
        导出草稿
        
        Args:
            project: 草稿项目
            output_path: 输出路径，默认为剪映草稿目录
            
        Returns:
            导出的草稿路径
        """
        if output_path is None:
            draft_root = self.find_draft_path()
            if draft_root is None:
                # 使用临时目录
                output_path = os.path.join(
                    os.path.expanduser('~'),
                    'CineFlow_Exports',
                    project.name
                )
            else:
                output_path = os.path.join(draft_root, project.name)
                
        # 创建草稿目录
        os.makedirs(output_path, exist_ok=True)
        
        # 生成草稿JSON
        draft_json = self._generate_draft_json(project)
        
        # 保存草稿
        draft_file = os.path.join(output_path, 'draft.json')
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft_json, f, ensure_ascii=False, indent=2)
            
        # 复制素材
        self._copy_materials(project, output_path)
        
        return output_path
        
    def _generate_draft_json(self, project: DraftProject) -> Dict[str, Any]:
        """生成剪映草稿JSON"""
        draft_id = str(uuid.uuid4()).replace('-', '').upper()[:20]
        
        # 基础结构
        draft = {
            'id': draft_id,
            'name': project.name,
            'duration': int(project.duration * 1000000),  # 微秒
            'width': project.width,
            'height': project.height,
            'fps': project.fps,
            'create_time': int(datetime.now().timestamp()),
            'update_time': int(datetime.now().timestamp()),
            'platform': {
                'os': self.platform,
                'version': '3.0.0'
            },
            'materials': {
                'videos': [],
                'audios': [],
                'texts': [],
                'effects': [],
                'filters': []
            },
            'tracks': []
        }
        
        # 添加素材
        for material in project.materials:
            material_json = {
                'id': material.id,
                'name': material.name,
                'path': material.path,
                'duration': int(material.duration * 1000000),
            }
            
            if material.type == 'video':
                material_json.update({
                    'width': material.width,
                    'height': material.height,
                    'fps': material.fps
                })
                draft['materials']['videos'].append(material_json)
            elif material.type == 'audio':
                draft['materials']['audios'].append(material_json)
            elif material.type == 'text':
                draft['materials']['texts'].append(material_json)
                
        # 添加轨道
        for track in project.tracks:
            track_json = {
                'id': track.id,
                'type': track.type,
                'segments': track.segments
            }
            draft['tracks'].append(track_json)
            
        return draft
        
    def _copy_materials(self, project: DraftProject, output_path: str):
        """复制素材到草稿目录"""
        import shutil
        
        materials_dir = os.path.join(output_path, 'materials')
        os.makedirs(materials_dir, exist_ok=True)
        
        for material in project.materials:
            if os.path.exists(material.path):
                # 复制素材
                dest_path = os.path.join(materials_dir, os.path.basename(material.path))
                if not os.path.exists(dest_path):
                    shutil.copy2(material.path, dest_path)
                    
    def create_from_timeline(
        self,
        name: str,
        timeline: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """
        从时间线创建草稿
        
        Args:
            name: 项目名称
            timeline: 时间线数据
                {
                    'width': 1920,
                    'height': 1080,
                    'fps': 30,
                    'segments': [
                        {
                            'video_path': str,
                            'start_time': float,
                            'end_time': float,
                            'position': {'x': 0, 'y': 0},
                            'scale': 1.0
                        }
                    ]
                }
        """
        width = timeline.get('width', 1920)
        height = timeline.get('height', 1080)
        fps = timeline.get('fps', 30)
        segments = timeline.get('segments', [])
        
        # 计算总时长
        duration = max(
            (s.get('end_time', 0) for s in segments),
            default=0
        )
        
        # 创建素材
        materials = []
        tracks = []
        
        video_track_segments = []
        
        for i, segment in enumerate(segments):
            video_path = segment.get('video_path', '')
            if not video_path or not os.path.exists(video_path):
                continue
                
            material_id = f"video_{i}"
            
            # 创建素材
            material = DraftMaterial(
                id=material_id,
                type='video',
                path=video_path,
                name=os.path.basename(video_path),
                duration=segment.get('end_time', 0) - segment.get('start_time', 0),
                width=width,
                height=height,
                fps=fps
            )
            materials.append(material)
            
            # 创建片段
            segment_json = {
                'id': f"segment_{i}",
                'material_id': material_id,
                'start_time': int(segment.get('start_time', 0) * 1000000),
                'end_time': int(segment.get('end_time', 0) * 1000000),
                'source_start': 0,
                'source_end': int((segment.get('end_time', 0) - segment.get('start_time', 0)) * 1000000),
                'position': segment.get('position', {'x': 0, 'y': 0}),
                'scale': segment.get('scale', 1.0),
                'rotation': segment.get('rotation', 0)
            }
            video_track_segments.append(segment_json)
            
        # 创建视频轨道
        if video_track_segments:
            video_track = DraftTrack(
                id='video_track_0',
                type='video',
                segments=video_track_segments
            )
            tracks.append(video_track)
            
        # 创建项目
        project = DraftProject(
            name=name,
            duration=duration,
            width=width,
            height=height,
            fps=fps,
            materials=materials,
            tracks=tracks
        )
        
        return self.export(project, output_path)
        
    def add_captions(
        self,
        draft_path: str,
        captions: List[Dict[str, Any]]
    ):
        """
        添加字幕到草稿
        
        Args:
            captions: [
                {
                    'text': str,
                    'start_time': float,
                    'end_time': float,
                    'style': dict
                }
            ]
        """
        draft_file = os.path.join(draft_path, 'draft.json')
        
        if not os.path.exists(draft_file):
            raise FileNotFoundError(f"草稿文件不存在: {draft_file}")
            
        with open(draft_file, 'r', encoding='utf-8') as f:
            draft = json.load(f)
            
        # 创建字幕素材
        for i, caption in enumerate(captions):
            text_id = f"text_{i}"
            
            # 添加文本素材
            draft['materials']['texts'].append({
                'id': text_id,
                'content': caption.get('text', ''),
                'style': caption.get('style', {})
            })
            
        # 添加字幕轨道
        text_segments = []
        for i, caption in enumerate(captions):
            text_segments.append({
                'id': f"text_segment_{i}",
                'material_id': f"text_{i}",
                'start_time': int(caption.get('start_time', 0) * 1000000),
                'end_time': int(caption.get('end_time', 0) * 1000000),
                'position': {'x': 0.5, 'y': 0.85}  # 底部居中
            })
            
        draft['tracks'].append({
            'id': 'text_track_0',
            'type': 'text',
            'segments': text_segments
        })
        
        # 保存
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft, f, ensure_ascii=False, indent=2)
            
    def add_effects(
        self,
        draft_path: str,
        effects: List[Dict[str, Any]]
    ):
        """
        添加特效到草稿
        
        Args:
            effects: [
                {
                    'type': str,  # 'transition', 'filter', 'animation'
                    'start_time': float,
                    'end_time': float,
                    'params': dict
                }
            ]
        """
        draft_file = os.path.join(draft_path, 'draft.json')
        
        if not os.path.exists(draft_file):
            raise FileNotFoundError(f"草稿文件不存在: {draft_file}")
            
        with open(draft_file, 'r', encoding='utf-8') as f:
            draft = json.load(f)
            
        # 添加特效
        for i, effect in enumerate(effects):
            effect_id = f"effect_{i}"
            
            draft['materials']['effects'].append({
                'id': effect_id,
                'type': effect.get('type'),
                'params': effect.get('params', {})
            })
            
        # 保存
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump(draft, f, ensure_ascii=False, indent=2)
