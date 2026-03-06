#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlow 统一工作流引擎

将所有创作模式统一为标准化的 9 步流水线：
  上传 → AI分析 → 模式选择 → 脚本生成 → 编辑 → 时间轴 → 配音 → 导出

与 ClipFlow Web 版 (clip-flow) 的 workflow.service.ts 对齐。
"""

import os
import uuid
import time
import json
import subprocess
from enum import Enum
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field


# ============ 枚举 ============

class WorkflowStep(Enum):
    IMPORT = "import"
    ANALYZE = "analyze"
    MODE_SELECT = "mode_select"
    SCRIPT_GENERATE = "script_gen"
    SCRIPT_EDIT = "script_edit"
    TIMELINE = "timeline"
    VOICEOVER = "voiceover"
    PREVIEW = "preview"
    EXPORT = "export"


class CreationMode(Enum):
    COMMENTARY = "commentary"
    MASHUP = "mashup"
    MONOLOGUE = "monologue"


class WorkflowStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class ExportFormat(Enum):
    JIANYING = "jianying"
    PREMIERE = "premiere"
    FINALCUT = "finalcut"
    DAVINCI = "davinci"
    MP4 = "mp4"
    SRT = "srt"
    ASS = "ass"


# ============ 数据模型 ============

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


# ============ 工作流引擎 ============

class WorkflowEngine:
    """
    ClipFlow 统一工作流引擎
    9 步流水线，每步有明确的输入/处理/输出。
    """

    def __init__(self):
        self._state = WorkflowState()
        self._callbacks = WorkflowCallbacks()
        self._aborted = False

    @property
    def state(self) -> WorkflowState:
        return self._state

    def set_callbacks(self, callbacks: WorkflowCallbacks) -> None:
        self._callbacks = callbacks

    def reset(self) -> None:
        self._state = WorkflowState()
        self._aborted = False

    def abort(self) -> None:
        self._aborted = True
        self._update(status=WorkflowStatus.IDLE)

    def _update(self, **kwargs):
        old_step = self._state.step
        for k, v in kwargs.items():
            if hasattr(self._state, k):
                setattr(self._state, k, v)
        if 'step' in kwargs and kwargs['step'] != old_step and self._callbacks.on_step_change:
            self._callbacks.on_step_change(kwargs['step'], old_step)
        if 'progress' in kwargs and self._callbacks.on_progress:
            self._callbacks.on_progress(kwargs['progress'])
        if 'status' in kwargs and self._callbacks.on_status_change:
            self._callbacks.on_status_change(kwargs['status'])
        if 'error' in kwargs and kwargs['error'] and self._callbacks.on_error:
            self._callbacks.on_error(kwargs['error'])

    # ---- Step 1: 素材导入 ----

    def step_import(self, video_paths: List[str]) -> List[VideoSource]:
        """
        输入: 视频文件路径列表
        处理: 校验 + FFprobe 提取元数据
        输出: VideoSource 列表
        """
        self._update(step=WorkflowStep.IMPORT, status=WorkflowStatus.RUNNING, progress=5)
        sources = []

        for i, path in enumerate(video_paths):
            if self._aborted:
                break
            if not os.path.exists(path):
                continue

            source = VideoSource(path=path, name=os.path.basename(path), size=os.path.getsize(path))

            try:
                result = subprocess.run(
                    ["ffprobe", "-v", "quiet", "-print_format", "json",
                     "-show_format", "-show_streams", path],
                    capture_output=True, text=True, timeout=15
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    fmt = data.get("format", {})
                    source.duration = float(fmt.get("duration", 0))
                    for s in data.get("streams", []):
                        if s.get("codec_type") == "video":
                            source.width = int(s.get("width", 0))
                            source.height = int(s.get("height", 0))
                            rfr = s.get("r_frame_rate", "30/1")
                            if "/" in str(rfr):
                                n, d = rfr.split("/")
                                source.fps = float(n) / max(float(d), 1)
                            else:
                                source.fps = float(rfr)
                            break
            except Exception:
                pass

            sources.append(source)
            self._update(progress=5 + (i + 1) / len(video_paths) * 10)

        self._state.sources = sources
        self._update(progress=15)
        return sources

    # ---- Step 2: AI 智能分析 ----

    def step_analyze(self, provider: str = "auto") -> AnalysisResult:
        """
        输入: 视频源
        处理: 场景分析（SceneAnalyzer）/ 视频级理解（Gemini）
        输出: AnalysisResult（场景/角色/情感/摘要）
        """
        self._update(step=WorkflowStep.ANALYZE, progress=20)

        if not self._state.sources:
            raise ValueError("没有导入视频素材")

        primary = self._state.sources[0]
        result = AnalysisResult()

        try:
            from ..ai.scene_analyzer import SceneAnalyzer, AnalysisConfig
            analyzer = SceneAnalyzer()
            config = AnalysisConfig(
                min_scene_duration=2.0,
                max_scenes=50,
                extract_emotions=True,
                extract_objects=True,
            )
            scenes = analyzer.analyze(primary.path, config)
            self._update(progress=35)

            result.scenes = [
                {
                    "id": getattr(s, "id", str(i)),
                    "start": getattr(s, "start_time", 0),
                    "end": getattr(s, "end_time", 0),
                    "description": getattr(s, "description", ""),
                    "tags": getattr(s, "tags", []),
                }
                for i, s in enumerate(scenes or [])
            ]
        except Exception as e:
            self._update(error=f"场景分析失败: {e}")

        result.summary = (
            f"视频时长 {primary.duration:.0f}s, "
            f"{primary.width}x{primary.height}, "
            f"检测到 {len(result.scenes)} 个场景"
        )

        self._state.analysis = result
        self._update(progress=40)
        return result

    # ---- Step 3: 创作模式选择 ----

    def step_select_mode(self, mode: CreationMode) -> CreationMode:
        """
        输入: 用户选择的模式（解说/混剪/独白）
        输出: 确认的模式
        """
        self._update(step=WorkflowStep.MODE_SELECT, progress=45)
        self._state.mode = mode
        return mode

    # ---- Step 4: AI 脚本生成 ----

    def step_generate_script(
        self, topic: str = "", style: str = "professional"
    ) -> ScriptData:
        """
        输入: 视频分析 + 模式 + 主题
        处理: ScriptGenerator 多模型调度
        输出: ScriptData
        """
        self._update(step=WorkflowStep.SCRIPT_GENERATE, progress=50)

        if not self._state.sources:
            raise ValueError("没有视频素材")

        primary = self._state.sources[0]

        # 分析上下文
        context = ""
        if self._state.analysis:
            context = self._state.analysis.summary
            scene_descs = [s.get("description", "") for s in self._state.analysis.scenes[:10]]
            if scene_descs:
                context += "\n场景: " + " | ".join(filter(None, scene_descs))

        try:
            from ..ai.script_generator import ScriptGenerator, ScriptConfig, ScriptStyle
            generator = ScriptGenerator()

            style_map = {
                CreationMode.COMMENTARY: ScriptStyle.EXPLAINER,
                CreationMode.MASHUP: ScriptStyle.DYNAMIC,
                CreationMode.MONOLOGUE: ScriptStyle.EMOTIONAL,
            }
            script_style = style_map.get(
                self._state.mode or CreationMode.COMMENTARY,
                ScriptStyle.EXPLAINER
            )

            config = ScriptConfig(
                style=script_style,
                target_duration=primary.duration,
                language="zh",
            )
            result = generator.generate(
                video_path=primary.path,
                topic=topic or primary.name,
                config=config,
                context=context,
            )
            self._update(progress=60)

            script = ScriptData(
                title=f"{primary.name} - {(self._state.mode or CreationMode.COMMENTARY).value}",
                content=getattr(result, "content", str(result)),
                segments=getattr(result, "segments", []),
                word_count=len(getattr(result, "content", "")),
                estimated_duration=primary.duration,
                style=style,
            )
        except Exception as e:
            script = ScriptData(
                title=primary.name,
                content=f"[脚本生成失败: {e}] 请手动编写或重试。",
                estimated_duration=primary.duration,
            )
            self._update(error=f"脚本生成失败: {e}")

        self._state.script = script
        self._update(progress=65)
        return script

    # ---- Step 5: 脚本编辑 ----

    def step_edit_script(self, content: str, segments: Optional[List[Dict]] = None) -> ScriptData:
        """
        输入: 用户编辑后的脚本
        输出: 更新后的 ScriptData
        """
        self._update(step=WorkflowStep.SCRIPT_EDIT)

        if not self._state.script:
            self._state.script = ScriptData()

        self._state.script.content = content
        self._state.script.word_count = len(content)
        if segments:
            self._state.script.segments = segments

        self._update(progress=70)
        return self._state.script

    # ---- Step 6: 时间轴编排 ----

    def step_timeline(self, auto_match: bool = True) -> TimelineData:
        """
        输入: 脚本 + 视频分析 + 素材
        处理: 脚本-场景自动匹配，多轨编排
        输出: TimelineData（视频轨/音频轨/字幕轨）
        """
        self._update(step=WorkflowStep.TIMELINE, progress=72)

        if not self._state.sources:
            raise ValueError("没有视频素材")

        primary = self._state.sources[0]
        script = self._state.script
        analysis = self._state.analysis
        timeline = TimelineData(total_duration=primary.duration)

        if auto_match and script:
            segments = script.segments or [{"content": script.content}]
            seg_dur = primary.duration / max(len(segments), 1)

            for i, seg in enumerate(segments):
                start = i * seg_dur
                end = min((i + 1) * seg_dur, primary.duration)

                # 如果有分析场景，尝试匹配最近场景的时间
                if analysis and analysis.scenes and i < len(analysis.scenes):
                    scene = analysis.scenes[i]
                    start = scene.get("start", start)
                    end = scene.get("end", end)

                timeline.video_track.append({
                    "id": f"v-{i}", "source": primary.path,
                    "start": start, "end": end,
                    "transition": "fade" if i > 0 else "none",
                })

                text = seg.get("content", seg.get("text", "")) if isinstance(seg, dict) else str(seg)
                timeline.subtitle_track.append({
                    "id": f"s-{i}", "text": text, "start": start, "end": end,
                })
        else:
            timeline.video_track.append({
                "id": "v-0", "source": primary.path,
                "start": 0, "end": primary.duration, "transition": "none",
            })

        self._state.timeline = timeline
        self._update(progress=80)
        return timeline

    # ---- Step 7: AI 配音 + 音画同步 ----

    def step_voiceover(
        self,
        voice: str = "xiaoxiao",
        music_path: Optional[str] = None,
        beat_sync: bool = False,
        output_dir: str = "",
    ) -> VoiceoverData:
        """
        输入: 脚本 + 配音参数 + 可选音乐
        处理: TTS 合成（Edge/OpenAI）+ librosa 节拍检测 + 同步
        输出: VoiceoverData（音频段 + 同步信息）
        """
        self._update(step=WorkflowStep.VOICEOVER, progress=82)

        if not self._state.script:
            raise ValueError("没有脚本内容")

        if not output_dir:
            output_dir = os.path.join(os.path.expanduser("~"), ".clipflow", "audio")
        os.makedirs(output_dir, exist_ok=True)

        voiceover = VoiceoverData(voice_style=voice, beat_sync=beat_sync)
        segments = self._state.script.segments or [{"content": self._state.script.content}]

        try:
            from ..ai.voice_generator import VoiceGenerator, VoiceConfig
            vg = VoiceGenerator()
            config = VoiceConfig(voice=voice)

            for i, seg in enumerate(segments):
                text = seg.get("content", seg.get("text", "")) if isinstance(seg, dict) else str(seg)
                if not text.strip():
                    continue

                audio_file = os.path.join(output_dir, f"voice_{self._state.project_id}_{i}.mp3")

                try:
                    result = vg.generate(text=text, config=config, output_path=audio_file)
                    voiceover.segments.append({
                        "index": i, "text": text, "audio_path": audio_file,
                        "duration": getattr(result, "duration", 0),
                    })
                except Exception as e:
                    voiceover.segments.append({
                        "index": i, "text": text, "audio_path": "", "error": str(e),
                    })

                self._update(progress=82 + (i + 1) / len(segments) * 8)

        except ImportError:
            self._update(error="VoiceGenerator 不可用")
        except Exception as e:
            self._update(error=f"配音失败: {e}")

        # 音画同步
        if beat_sync and music_path and os.path.exists(music_path):
            try:
                from ..audio.beat_detector import BeatDetector
                detector = BeatDetector()
                beats = detector.detect(music_path)
                voiceover.beat_sync = True

                # 将视频切点对齐到节拍
                if self._state.timeline and beats:
                    for i, clip in enumerate(self._state.timeline.video_track):
                        if i < len(beats):
                            beat_time = getattr(beats[i], "time", beats[i]) if not isinstance(beats[i], (int, float)) else beats[i]
                            clip["beat_aligned"] = True
                            clip["beat_time"] = beat_time
            except Exception:
                pass

        self._state.voiceover = voiceover
        self._update(progress=92)
        return voiceover

    # ---- Step 8: 预览 ----

    def step_preview(self) -> Dict[str, Any]:
        """返回预览摘要"""
        self._update(step=WorkflowStep.PREVIEW, progress=95)
        return {
            "project_id": self._state.project_id,
            "mode": self._state.mode.value if self._state.mode else "unknown",
            "sources": [{"name": s.name, "duration": s.duration} for s in self._state.sources],
            "script_preview": (self._state.script.content[:200] + "...") if self._state.script else "",
            "timeline_clips": len(self._state.timeline.video_track) if self._state.timeline else 0,
            "voiceover_segments": len(self._state.voiceover.segments) if self._state.voiceover else 0,
        }

    # ---- Step 9: 导出 ----

    def step_export(
        self,
        fmt: ExportFormat = ExportFormat.MP4,
        output_dir: str = "",
        quality: str = "high",
    ) -> str:
        """
        输入: 时间轴 + 音轨 + 字幕 + 格式
        处理: 调用对应导出器（剪映/PR/FCP/达芬奇/MP4/SRT/ASS）
        输出: 导出文件路径
        """
        self._update(step=WorkflowStep.EXPORT, progress=96)

        if not output_dir:
            output_dir = os.path.join(os.path.expanduser("~"), ".clipflow", "exports")
        os.makedirs(output_dir, exist_ok=True)

        pid = self._state.project_id
        ts = int(time.time())
        output_path = ""

        try:
            if fmt == ExportFormat.SRT:
                output_path = os.path.join(output_dir, f"clipflow_{pid}_{ts}.srt")
                self._export_srt(output_path)

            elif fmt == ExportFormat.ASS:
                output_path = os.path.join(output_dir, f"clipflow_{pid}_{ts}.ass")
                self._export_ass(output_path)

            elif fmt == ExportFormat.JIANYING:
                from ..export.jianying_exporter import JianyingExporter
                output_path = os.path.join(output_dir, f"clipflow_{pid}_{ts}")
                exporter = JianyingExporter()
                exporter.export(self._build_export_data(), output_path)

            elif fmt == ExportFormat.PREMIERE:
                from ..export.premiere_exporter import PremiereExporter
                output_path = os.path.join(output_dir, f"clipflow_{pid}_{ts}.xml")
                exporter = PremiereExporter()
                exporter.export(self._build_export_data(), output_path)

            elif fmt == ExportFormat.FINALCUT:
                from ..export.finalcut_exporter import FinalCutExporter
                output_path = os.path.join(output_dir, f"clipflow_{pid}_{ts}.fcpxml")
                exporter = FinalCutExporter()
                exporter.export(self._build_export_data(), output_path)

            elif fmt == ExportFormat.DAVINCI:
                from ..export.davinci_exporter import DaVinciExporter
                output_path = os.path.join(output_dir, f"clipflow_{pid}_{ts}.fcpxml")
                exporter = DaVinciExporter()
                exporter.export(self._build_export_data(), output_path)

            else:  # MP4
                from ..export.direct_video_exporter import DirectVideoExporter
                output_path = os.path.join(output_dir, f"clipflow_{pid}_{ts}.mp4")
                exporter = DirectVideoExporter()
                exporter.export(self._build_export_data(), output_path, quality=quality)

        except Exception as e:
            self._update(error=f"导出失败: {e}")

        self._state.export_path = output_path
        self._state.export_format = fmt
        self._update(progress=100, status=WorkflowStatus.COMPLETED)

        if self._callbacks.on_complete:
            self._callbacks.on_complete(self._state)

        return output_path

    # ---- 辅助 ----

    def _build_export_data(self) -> Dict[str, Any]:
        return {
            "project_id": self._state.project_id,
            "sources": [{"path": s.path, "duration": s.duration} for s in self._state.sources],
            "script": {"content": self._state.script.content, "segments": self._state.script.segments} if self._state.script else {},
            "timeline": {
                "video": self._state.timeline.video_track,
                "audio": self._state.timeline.audio_track,
                "subtitle": self._state.timeline.subtitle_track,
                "duration": self._state.timeline.total_duration,
            } if self._state.timeline else {},
            "voiceover": {
                "segments": self._state.voiceover.segments,
                "voice": self._state.voiceover.voice_style,
            } if self._state.voiceover else {},
        }

    def _export_srt(self, path: str) -> None:
        """导出 SRT 字幕"""
        if not self._state.timeline:
            return
        with open(path, "w", encoding="utf-8") as f:
            for i, sub in enumerate(self._state.timeline.subtitle_track):
                start = self._fmt_srt_time(sub.get("start", 0))
                end = self._fmt_srt_time(sub.get("end", 0))
                text = sub.get("text", "")
                f.write(f"{i + 1}\n{start} --> {end}\n{text}\n\n")

    def _export_ass(self, path: str) -> None:
        """导出 ASS 字幕"""
        if not self._state.timeline:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("[Script Info]\nTitle: ClipFlow Export\nScriptType: v4.00+\n\n")
            f.write("[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n")
            f.write("Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,10,10,10,1\n\n")
            f.write("[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
            for sub in self._state.timeline.subtitle_track:
                start = self._fmt_ass_time(sub.get("start", 0))
                end = self._fmt_ass_time(sub.get("end", 0))
                text = sub.get("text", "").replace("\n", "\\N")
                f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")

    @staticmethod
    def _fmt_srt_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    @staticmethod
    def _fmt_ass_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds % 1) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


# ---- 快捷函数 ----

def create_workflow() -> WorkflowEngine:
    """创建工作流引擎实例"""
    return WorkflowEngine()
