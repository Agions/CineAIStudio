"""
ClipFlow 导出服务模块

提供视频项目的导出能力:
- JianyingExporter: 剪映草稿导出
- PremiereExporter: Adobe Premiere 导出
- FinalCutExporter: Final Cut Pro 导出
- DaVinciExporter: DaVinci Resolve 导出
- VideoExporter: 视频文件导出
- BaseExporter: 导出器基类
"""

from .base_exporter import (
    BaseExporter, BaseProject, BaseTrack, BaseSegment, BaseMaterial,
    ExporterConfig, TimeHelper, safe_filename,
    get_video_duration, get_video_resolution, copy_material_to_folder,
)
from .jianying_exporter import (
    JianyingExporter, JianyingDraft, JianyingConfig,
    Track, TrackType, Segment, TimeRange,
    VideoMaterial, AudioMaterial, TextMaterial,
)
from .video_exporter import VideoExporter, ExportConfig, ExportFormat


__all__ = [
    # 基类
    "BaseExporter",
    "BaseProject",
    "BaseTrack",
    "BaseSegment",
    "BaseMaterial",
    "ExporterConfig",
    "TimeHelper",
    "safe_filename",
    "get_video_duration",
    "get_video_resolution",
    "copy_material_to_folder",

    # 剪映草稿导出
    "JianyingExporter",
    "JianyingDraft",
    "JianyingConfig",
    "Track",
    "TrackType",
    "Segment",
    "TimeRange",
    "VideoMaterial",
    "AudioMaterial",
    "TextMaterial",

    # 视频文件导出
    "VideoExporter",
    "ExportConfig",
    "ExportFormat",
]
