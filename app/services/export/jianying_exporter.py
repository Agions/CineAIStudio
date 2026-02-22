"""
剪映草稿导出器 (Jianying Exporter)

将 ClipFlow 项目导出为剪映草稿格式，实现与剪映的完美对接。

剪映草稿结构:
    drafts/
    └── {project_name}/
        ├── draft_content.json     # 主要内容
        ├── draft_meta_info.json   # 元信息
        └── 素材文件...

使用示例:
    from app.services.export import JianyingExporter
    
    exporter = JianyingExporter()
    draft_path = exporter.export(project, output_dir)
    print(f"草稿已导出: {draft_path}")
"""

import json
import uuid
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime


class TrackType(Enum):
    """轨道类型"""
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    STICKER = "sticker"
    EFFECT = "effect"


class MaterialType(Enum):
    """素材类型"""
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    IMAGE = "photo"
    SOUND_CHANNEL = "sound_channel"


@dataclass
class TimeRange:
    """
    时间范围（剪映使用微秒）
    
    Attributes:
        start: 开始时间（微秒）
        duration: 持续时间（微秒）
    """
    start: int = 0
    duration: int = 0
    
    @classmethod
    def from_seconds(cls, start: float, duration: float) -> 'TimeRange':
        """从秒转换"""
        return cls(
            start=int(start * 1_000_000),
            duration=int(duration * 1_000_000)
        )
    
    def to_dict(self) -> dict:
        return {"start": self.start, "duration": self.duration}


@dataclass
class Segment:
    """
    片段模型
    
    对应剪映中的一个视频/音频/字幕片段
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    material_id: str = ""
    target_timerange: TimeRange = field(default_factory=TimeRange)
    source_timerange: TimeRange = field(default_factory=TimeRange)
    
    # 视频/音频属性
    volume: float = 1.0
    speed: float = 1.0
    
    # 字幕专用
    caption_info: Optional[Dict] = None
    
    def to_dict(self) -> dict:
        """转换为剪映 JSON 格式"""
        result = {
            "id": self.id,
            "material_id": self.material_id,
            "target_timerange": self.target_timerange.to_dict(),
            "source_timerange": self.source_timerange.to_dict(),
            "volume": self.volume,
            "speed": self.speed,
        }
        
        if self.caption_info:
            result["caption_info"] = self.caption_info
            
        return result


@dataclass
class Track:
    """
    轨道模型
    
    一个轨道可以包含多个片段
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: TrackType = TrackType.VIDEO
    segments: List[Segment] = field(default_factory=list)
    
    # 轨道属性
    attribute: int = 0  # 0=普通, 1=主轨道
    flag: int = 0
    
    def add_segment(self, segment: Segment) -> None:
        """添加片段"""
        self.segments.append(segment)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "segments": [s.to_dict() for s in self.segments],
            "attribute": self.attribute,
            "flag": self.flag,
        }


@dataclass
class VideoMaterial:
    """视频素材"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    path: str = ""
    duration: int = 0  # 微秒
    width: int = 1920
    height: int = 1080
    
    # 素材来源
    type: str = "video"
    category_id: str = ""
    category_name: str = "local"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "path": self.path,
            "duration": self.duration,
            "width": self.width,
            "height": self.height,
            "type": self.type,
            "category_id": self.category_id,
            "category_name": self.category_name,
        }


@dataclass
class AudioMaterial:
    """音频素材"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    path: str = ""
    duration: int = 0  # 微秒
    
    # 音频属性
    type: str = "music"
    name: str = ""
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "path": self.path,
            "duration": self.duration,
            "type": self.type,
            "name": self.name,
        }


@dataclass
class TextMaterial:
    """
    字幕/文本素材
    
    剪映字幕的核心结构
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    
    # 样式
    font_path: str = ""
    font_size: float = 8.0  # 剪映使用相对尺寸
    font_color: str = "#FFFFFF"
    
    # 位置
    alignment: int = 1  # 0=左, 1=中, 2=右
    
    # 特效
    background_color: str = ""
    has_shadow: bool = True
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "font_path": self.font_path,
            "font_size": self.font_size,
            "font_color": self.font_color,
            "alignment": self.alignment,
            "background_color": self.background_color,
            "has_shadow": self.has_shadow,
            "type": "text",
        }


@dataclass
class JianyingMaterials:
    """素材集合"""
    videos: List[VideoMaterial] = field(default_factory=list)
    audios: List[AudioMaterial] = field(default_factory=list)
    texts: List[TextMaterial] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "videos": [v.to_dict() for v in self.videos],
            "audios": [a.to_dict() for a in self.audios],
            "texts": [t.to_dict() for t in self.texts],
        }


@dataclass
class CanvasConfig:
    """画布配置"""
    width: int = 1080  # 竖屏短视频
    height: int = 1920
    ratio: str = "9:16"
    
    def to_dict(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "ratio": self.ratio,
        }


@dataclass
class JianyingDraft:
    """
    剪映草稿完整模型
    
    这是导出的核心数据结构，包含所有轨道、素材和配置信息
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "ClipFlow Project"
    duration: int = 0  # 总时长（微秒）
    
    # 轨道
    tracks: List[Track] = field(default_factory=list)
    
    # 素材
    materials: JianyingMaterials = field(default_factory=JianyingMaterials)
    
    # 配置
    canvas_config: CanvasConfig = field(default_factory=CanvasConfig)
    
    # 元数据
    create_time: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    update_time: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    
    # 版本
    version: int = 360000  # 剪映版本号
    platform: str = "all"
    
    def add_track(self, track: Track) -> None:
        """添加轨道"""
        self.tracks.append(track)
    
    def add_video(self, material: VideoMaterial) -> None:
        """添加视频素材"""
        self.materials.videos.append(material)
    
    def add_audio(self, material: AudioMaterial) -> None:
        """添加音频素材"""
        self.materials.audios.append(material)
    
    def add_text(self, material: TextMaterial) -> None:
        """添加文本素材"""
        self.materials.texts.append(material)
    
    def calculate_duration(self) -> None:
        """计算总时长"""
        max_end = 0
        for track in self.tracks:
            for segment in track.segments:
                end = segment.target_timerange.start + segment.target_timerange.duration
                max_end = max(max_end, end)
        self.duration = max_end
    
    def to_draft_content(self) -> dict:
        """
        生成 draft_content.json 内容
        
        这是剪映草稿的核心文件
        """
        self.calculate_duration()
        
        return {
            "id": self.id,
            "name": self.name,
            "duration": self.duration,
            "canvas_config": self.canvas_config.to_dict(),
            "tracks": [t.to_dict() for t in self.tracks],
            "materials": self.materials.to_dict(),
            "version": self.version,
            "platform": self.platform,
            "create_time": self.create_time,
            "update_time": self.update_time,
        }
    
    def to_draft_meta_info(self) -> dict:
        """生成 draft_meta_info.json 内容"""
        return {
            "draft_id": self.id,
            "draft_name": self.name,
            "draft_root_path": "",  # 导出时填充
            "tm_draft_create": self.create_time // 1000,
            "tm_draft_modified": self.update_time // 1000,
            "draft_materials_copied": True,
        }


@dataclass
class JianyingConfig:
    """导出配置"""
    copy_materials: bool = True  # 是否复制素材到草稿目录
    canvas_ratio: str = "9:16"   # 画布比例: 9:16, 16:9, 1:1
    version: int = 360000        # 剪映版本号


class JianyingExporter:
    """
    剪映草稿导出器
    
    将项目导出为剪映可识别的草稿格式
    
    使用示例:
        exporter = JianyingExporter()
        
        # 创建草稿
        draft = exporter.create_draft("我的视频")
        
        # 添加视频轨道
        video_track = Track(type=TrackType.VIDEO)
        video_material = VideoMaterial(path="/path/to/video.mp4", duration=5000000)
        draft.add_video(video_material)
        
        video_segment = Segment(
            material_id=video_material.id,
            target_timerange=TimeRange.from_seconds(0, 5),
            source_timerange=TimeRange.from_seconds(0, 5),
        )
        video_track.add_segment(video_segment)
        draft.add_track(video_track)
        
        # 导出
        draft_path = exporter.export(draft, "/path/to/output")
    """
    
    def __init__(self, config: Optional[JianyingConfig] = None):
        self.config = config or JianyingConfig()
    
    def create_draft(self, name: str) -> JianyingDraft:
        """创建新草稿"""
        canvas_config = self._get_canvas_config(self.config.canvas_ratio)
        
        return JianyingDraft(
            name=name,
            canvas_config=canvas_config,
            version=self.config.version,
        )
    
    def _get_canvas_config(self, ratio: str) -> CanvasConfig:
        """根据比例获取画布配置"""
        configs = {
            "9:16": CanvasConfig(width=1080, height=1920, ratio="9:16"),  # 竖屏
            "16:9": CanvasConfig(width=1920, height=1080, ratio="16:9"),  # 横屏
            "1:1": CanvasConfig(width=1080, height=1080, ratio="1:1"),    # 方形
            "3:4": CanvasConfig(width=1080, height=1440, ratio="3:4"),    # 小红书
        }
        return configs.get(ratio, configs["9:16"])
    
    def export(self, draft: JianyingDraft, output_dir: str) -> str:
        """
        导出草稿到指定目录
        
        Args:
            draft: 剪映草稿对象
            output_dir: 输出目录（剪映草稿目录）
            
        Returns:
            草稿文件夹路径
        """
        output_path = Path(output_dir)
        
        # 创建草稿文件夹（使用项目名称）
        safe_name = self._safe_filename(draft.name)
        draft_folder = output_path / safe_name
        draft_folder.mkdir(parents=True, exist_ok=True)
        
        # 复制素材（如果启用）
        if self.config.copy_materials:
            self._copy_materials(draft, draft_folder)
        
        # 生成 draft_content.json
        content = draft.to_draft_content()
        content_path = draft_folder / "draft_content.json"
        self._write_json(content_path, content)
        
        # 生成 draft_meta_info.json
        meta = draft.to_draft_meta_info()
        meta["draft_root_path"] = str(draft_folder)
        meta_path = draft_folder / "draft_meta_info.json"
        self._write_json(meta_path, meta)
        
        return str(draft_folder)
    
    def _safe_filename(self, name: str) -> str:
        """生成安全的文件名"""
        # 移除或替换不安全字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()
    
    def _copy_materials(self, draft: JianyingDraft, draft_folder: Path) -> None:
        """复制素材到草稿目录"""
        materials_folder = draft_folder / "materials"
        materials_folder.mkdir(exist_ok=True)
        
        # 复制视频素材
        for video in draft.materials.videos:
            if video.path and Path(video.path).exists():
                src = Path(video.path)
                dst = materials_folder / src.name
                if not dst.exists():
                    shutil.copy2(src, dst)
                # 更新路径为相对路径
                video.path = str(dst)
        
        # 复制音频素材
        for audio in draft.materials.audios:
            if audio.path and Path(audio.path).exists():
                src = Path(audio.path)
                dst = materials_folder / src.name
                if not dst.exists():
                    shutil.copy2(src, dst)
                audio.path = str(dst)
    
    def _write_json(self, path: Path, data: dict) -> None:
        """写入 JSON 文件"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # =========== 便捷方法 ===========
    
    def add_video_segment(
        self,
        draft: JianyingDraft,
        video_path: str,
        start: float,
        duration: float,
        target_start: float = None,
    ) -> Segment:
        """
        便捷方法：添加视频片段
        
        Args:
            draft: 草稿对象
            video_path: 视频文件路径
            start: 源视频开始时间（秒）
            duration: 持续时间（秒）
            target_start: 目标时间轴开始位置（秒），默认为自动计算
            
        Returns:
            创建的片段对象
        """
        # 获取视频信息
        video_info = self._get_video_info(video_path)
        
        # 创建素材
        material = VideoMaterial(
            path=video_path,
            duration=video_info.get('duration', int(duration * 1_000_000)),
            width=video_info.get('width', 1920),
            height=video_info.get('height', 1080),
        )
        draft.add_video(material)
        
        # 计算目标开始时间
        if target_start is None:
            # 找到视频轨道的最后位置
            video_tracks = [t for t in draft.tracks if t.type == TrackType.VIDEO]
            if video_tracks:
                last_track = video_tracks[0]
                if last_track.segments:
                    last_seg = last_track.segments[-1]
                    target_start = (last_seg.target_timerange.start + 
                                   last_seg.target_timerange.duration) / 1_000_000
                else:
                    target_start = 0
            else:
                # 创建新的视频轨道
                new_track = Track(type=TrackType.VIDEO, attribute=1)
                draft.add_track(new_track)
                target_start = 0
        
        # 创建片段
        segment = Segment(
            material_id=material.id,
            source_timerange=TimeRange.from_seconds(start, duration),
            target_timerange=TimeRange.from_seconds(target_start, duration),
        )
        
        # 添加到视频轨道
        video_tracks = [t for t in draft.tracks if t.type == TrackType.VIDEO]
        if video_tracks:
            video_tracks[0].add_segment(segment)
        
        return segment
    
    def add_audio_segment(
        self,
        draft: JianyingDraft,
        audio_path: str,
        start: float,
        duration: float,
        target_start: float = 0,
        volume: float = 1.0,
    ) -> Segment:
        """
        便捷方法：添加音频片段
        
        Args:
            draft: 草稿对象
            audio_path: 音频文件路径
            start: 源音频开始时间（秒）
            duration: 持续时间（秒）
            target_start: 目标时间轴开始位置（秒）
            volume: 音量（0.0 - 1.0）
            
        Returns:
            创建的片段对象
        """
        # 创建素材
        material = AudioMaterial(
            path=audio_path,
            duration=int(duration * 1_000_000),
            name=Path(audio_path).stem,
        )
        draft.add_audio(material)
        
        # 获取或创建音频轨道
        audio_tracks = [t for t in draft.tracks if t.type == TrackType.AUDIO]
        if not audio_tracks:
            audio_track = Track(type=TrackType.AUDIO)
            draft.add_track(audio_track)
            audio_tracks = [audio_track]
        
        # 创建片段
        segment = Segment(
            material_id=material.id,
            source_timerange=TimeRange.from_seconds(start, duration),
            target_timerange=TimeRange.from_seconds(target_start, duration),
            volume=volume,
        )
        
        audio_tracks[0].add_segment(segment)
        return segment
    
    def add_caption(
        self,
        draft: JianyingDraft,
        text: str,
        start: float,
        duration: float,
        font_size: float = 8.0,
        font_color: str = "#FFFFFF",
    ) -> Segment:
        """
        便捷方法：添加字幕
        
        Args:
            draft: 草稿对象
            text: 字幕文本
            start: 开始时间（秒）
            duration: 持续时间（秒）
            font_size: 字体大小（剪映相对尺寸，默认8.0）
            font_color: 字体颜色（十六进制）
            
        Returns:
            创建的片段对象
        """
        # 创建文本素材
        material = TextMaterial(
            content=text,
            font_size=font_size,
            font_color=font_color,
        )
        draft.add_text(material)
        
        # 获取或创建字幕轨道
        text_tracks = [t for t in draft.tracks if t.type == TrackType.TEXT]
        if not text_tracks:
            text_track = Track(type=TrackType.TEXT)
            draft.add_track(text_track)
            text_tracks = [text_track]
        
        # 创建片段
        segment = Segment(
            material_id=material.id,
            source_timerange=TimeRange.from_seconds(0, duration),
            target_timerange=TimeRange.from_seconds(start, duration),
            caption_info={
                "content": text,
                "font_size": font_size,
                "font_color": font_color,
            },
        )
        
        text_tracks[0].add_segment(segment)
        return segment
    
    def _get_video_info(self, video_path: str) -> dict:
        """
        获取视频信息
        
        使用 FFprobe 获取视频的时长、分辨率等信息
        """
        import subprocess
        
        try:
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_format', '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # 查找视频流
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        duration = float(data.get('format', {}).get('duration', 0))
                        return {
                            'width': stream.get('width', 1920),
                            'height': stream.get('height', 1080),
                            'duration': int(duration * 1_000_000),
                        }
            
        except Exception as e:
            print(f"获取视频信息失败: {e}")
        
        return {'width': 1920, 'height': 1080, 'duration': 0}


# =========== 使用示例 ===========

def demo_export():
    """演示导出剪映草稿"""
    
    # 创建导出器
    exporter = JianyingExporter(JianyingConfig(
        canvas_ratio="9:16",  # 竖屏短视频
        copy_materials=True,
    ))
    
    # 创建草稿
    draft = exporter.create_draft("我的AI解说视频")
    
    # 添加视频片段
    exporter.add_video_segment(
        draft,
        video_path="/path/to/source.mp4",
        start=0,
        duration=10,
    )
    
    # 添加配音
    exporter.add_audio_segment(
        draft,
        audio_path="/path/to/voiceover.mp3",
        start=0,
        duration=10,
        volume=1.0,
    )
    
    # 添加字幕
    exporter.add_caption(
        draft,
        text="欢迎观看这个视频",
        start=0,
        duration=3,
        font_size=8.0,
        font_color="#FFFFFF",
    )
    
    exporter.add_caption(
        draft,
        text="这是AI自动解说生成的内容",
        start=3,
        duration=4,
    )
    
    # 导出到剪映草稿目录
    # macOS: ~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/drafts/
    output = exporter.export(draft, "/path/to/jianying/drafts")
    print(f"草稿已导出: {output}")


if __name__ == '__main__':
    demo_export()
