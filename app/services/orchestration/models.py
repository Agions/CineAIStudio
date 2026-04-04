"""
工作流数据模型

从 workflow_engine.py 提取，保持独立便于维护和类型复用。
"""

import uuid
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable

from .enums import WorkflowStep, WorkflowStatus, CreationMode, ExportFormat


@dataclass
class VideoSource:
    id: str = ""
    path: str = ""
    name: str = ""
    duration: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    size: int = 0

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


@dataclass
class AnalysisResult:
    scenes: List[Dict[str, Any]] = field(default_factory=list)
    characters: List[str] = field(default_factory=list)
    emotions: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class ScriptData:
    id: str = ""
    title: str = ""
    content: str = ""
    segments: List[Dict[str, Any]] = field(default_factory=list)
    word_count: int = 0
    estimated_duration: float = 0.0
    style: str = ""
    model_used: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


@dataclass
class TimelineData:
    video_track: List[Dict[str, Any]] = field(default_factory=list)
    audio_track: List[Dict[str, Any]] = field(default_factory=list)
    subtitle_track: List[Dict[str, Any]] = field(default_factory=list)
    total_duration: float = 0.0


@dataclass
class VoiceoverData:
    segments: List[Dict[str, Any]] = field(default_factory=list)
    voice_style: str = ""
    beat_sync: bool = False


@dataclass
class WorkflowState:
    project_id: str = ""
    step: WorkflowStep = WorkflowStep.IMPORT
    status: WorkflowStatus = WorkflowStatus.IDLE
    progress: float = 0.0
    error: str = ""
    mode: Optional[CreationMode] = None
    sources: List[VideoSource] = field(default_factory=list)
    analysis: Optional[AnalysisResult] = None
    script: Optional[ScriptData] = None
    timeline: Optional[TimelineData] = None
    voiceover: Optional[VoiceoverData] = None
    export_path: str = ""
    export_format: Optional[ExportFormat] = None

    def __post_init__(self):
        if not self.project_id:
            self.project_id = str(uuid.uuid4())[:8]


@dataclass
class WorkflowCallbacks:
    on_step_change: Optional[Callable] = None
    on_progress: Optional[Callable] = None
    on_status_change: Optional[Callable] = None
    on_error: Optional[Callable] = None
    on_complete: Optional[Callable] = None
