#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频处理管道
协调视频制作的各个步骤
"""

from typing import Dict, Any, Callable, List
from dataclasses import dataclass, field
from enum import Enum
import logging


from .base_maker import MakerProgress, MakerStatus
from .presets import (
    CommentaryConfig,
    MashupConfig,
    MonologueConfig,
    EncodingConfig,
    PresetFactory,
)

logger = logging.getLogger(__name__)

class PipelineStage(Enum):
    """管道阶段"""
    IDLE = "idle"
    ANALYZING = "analyzing"
    GENERATING_SCRIPT = "generating_script"
    GENERATING_VOICE = "generating_voice"
    GENERATING_CAPTIONS = "generating_captions"
    RENDERING = "rendering"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineResult:
    """管道结果"""
    success: bool
    output_path: str = ""
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 各阶段结果
    script: str = ""
    voice_path: str = ""
    captions_path: str = ""
    duration: float = 0.0


class VideoPipeline:
    """
    视频处理管道
    
    协调视频制作的完整流程
    """
    
    def __init__(self):
        self._progress = MakerProgress()
        self._current_stage: PipelineStage = PipelineStage.IDLE
        self._stages: List[PipelineStage] = []
        self._stage_index: int = 0
        self._logger = logging.getLogger(__name__)
        self._callbacks: List[Callable] = []
    
    @property
    def progress(self) -> MakerProgress:
        return self._progress
    
    @property
    def current_stage(self) -> PipelineStage:
        return self._current_stage
    
    def add_callback(self, callback: Callable[[PipelineStage, float], None]):
        """添加阶段回调"""
        self._callbacks.append(callback)
    
    def _update_stage(self, stage: PipelineStage, progress: float = None):
        """更新阶段"""
        self._current_stage = stage
        
        # 更新进度
        if self._stages and progress is not None:
            base = (self._stage_index / len(self._stages)) * 100
            current = base + (progress / len(self._stages))
            self._progress.progress = current
        
        # 更新状态
        status_map = {
            PipelineStage.ANALYZING: MakerStatus.PREPARING,
            PipelineStage.GENERATING_SCRIPT: MakerStatus.PROCESSING,
            PipelineStage.GENERATING_VOICE: MakerStatus.PROCESSING,
            PipelineStage.GENERATING_CAPTIONS: MakerStatus.PROCESSING,
            PipelineStage.RENDERING: MakerStatus.RENDERING,
            PipelineStage.EXPORTING: MakerStatus.RENDERING,
            PipelineStage.COMPLETED: MakerStatus.COMPLETED,
            PipelineStage.FAILED: MakerStatus.FAILED,
        }
        self._progress.status = status_map.get(stage, MakerStatus.IDLE)
        
        # 回调
        for cb in self._callbacks:
            try:
                cb(stage, progress or 0)
            except Exception as e:
                logger.warning(f"回调执行失败: {e}")
    
    async def run_commentary(
        self,
        config: CommentaryConfig,
        input_path: str,
        output_path: str,
    ) -> PipelineResult:
        """运行解说视频管道"""
        self._stages = [
            PipelineStage.ANALYZING,
            PipelineStage.GENERATING_SCRIPT,
            PipelineStage.GENERATING_VOICE,
            PipelineStage.GENERATING_CAPTIONS,
            PipelineStage.RENDERING,
            PipelineStage.EXPORTING,
        ]
        self._stage_index = 0
        result = PipelineResult(success=False)
        
        try:
            # 1. 分析视频
            self._update_stage(PipelineStage.ANALYZING, 0)
            scene_info = await self._analyze_video(input_path)
            result.metadata["scenes"] = scene_info
            
            # 2. 生成脚本
            self._update_stage(PipelineStage.GENERATING_SCRIPT, 20)
            script = await self._generate_script(config, scene_info)
            result.script = script
            
            # 3. 生成配音
            self._update_stage(PipelineStage.GENERATING_VOICE, 40)
            voice_path = await self._generate_voice(config, script)
            result.voice_path = voice_path
            
            # 4. 生成字幕
            self._update_stage(PipelineStage.GENERATING_CAPTIONS, 60)
            captions_path = await self._generate_captions(voice_path)
            result.captions_path = captions_path
            
            # 5. 渲染
            self._update_stage(PipelineStage.RENDERING, 80)
            await self._render_video(input_path, voice_path, captions_path, output_path)
            
            # 6. 导出
            self._update_stage(PipelineStage.EXPORTING, 95)
            final_path = await self._export_video(output_path, config.encoding)
            
            # 完成
            self._update_stage(PipelineStage.COMPLETED, 100)
            result.success = True
            result.output_path = final_path
            
        except Exception as e:
            self._logger.exception("Pipeline failed")
            self._update_stage(PipelineStage.FAILED, 0)
            result.error = str(e)
        
        return result
    
    async def run_mashup(
        self,
        config: MashupConfig,
        input_paths: List[str],
        output_path: str,
    ) -> PipelineResult:
        """运行混剪视频管道"""
        self._stages = [
            PipelineStage.ANALYZING,
            PipelineStage.GENERATING_SCRIPT,
            PipelineStage.RENDERING,
            PipelineStage.EXPORTING,
        ]
        self._stage_index = 0
        result = PipelineResult(success=False)
        
        try:
            # 1. 分析所有素材
            self._update_stage(PipelineStage.ANALYZING, 0)
            scenes = []
            for path in input_paths:
                scene = await self._analyze_video(path)
                scenes.append(scene)
            result.metadata["scenes"] = scenes
            
            # 2. 生成脚本
            self._update_stage(PipelineStage.GENERATING_SCRIPT, 30)
            script = await self._generate_mashup_script(config, scenes)
            result.script = script
            
            # 3. 渲染
            self._update_stage(PipelineStage.RENDERING, 60)
            await self._render_mashup(input_paths, script, output_path)
            
            # 4. 导出
            self._update_stage(PipelineStage.EXPORTING, 90)
            final_path = await self._export_video(output_path, config.encoding)
            
            # 完成
            self._update_stage(PipelineStage.COMPLETED, 100)
            result.success = True
            result.output_path = final_path
            
        except Exception as e:
            self._logger.exception("Mashup pipeline failed")
            self._update_stage(PipelineStage.FAILED, 0)
            result.error = str(e)
        
        return result
    
    async def run_monologue(
        self,
        config: MonologueConfig,
        input_path: str,
        output_path: str,
    ) -> PipelineResult:
        """运行独白视频管道"""
        self._stages = [
            PipelineStage.ANALYZING,
            PipelineStage.GENERATING_SCRIPT,
            PipelineStage.GENERATING_VOICE,
            PipelineStage.GENERATING_CAPTIONS,
            PipelineStage.RENDERING,
            PipelineStage.EXPORTING,
        ]
        self._stage_index = 0
        result = PipelineResult(success=False)
        
        try:
            # 1. 分析画面
            self._update_stage(PipelineStage.ANALYZING, 0)
            frames = await self._analyze_frames(input_path, config.frame_interval)
            result.metadata["frames"] = frames
            
            # 2. 生成独白
            self._update_stage(PipelineStage.GENERATING_SCRIPT, 20)
            script = await self._generate_monologue_script(config, frames)
            result.script = script
            
            # 3. 生成配音
            self._update_stage(PipelineStage.GENERATING_VOICE, 40)
            voice_path = await self._generate_voice_for_monologue(config, script)
            result.voice_path = voice_path
            
            # 4. 生成字幕
            self._update_stage(PipelineStage.GENERATING_CAPTIONS, 60)
            captions_path = await self._generate_captions(voice_path)
            result.captions_path = captions_path
            
            # 5. 渲染
            self._update_stage(PipelineStage.RENDERING, 80)
            await self._render_monologue(input_path, voice_path, captions_path, output_path)
            
            # 6. 导出
            self._update_stage(PipelineStage.EXPORTING, 95)
            final_path = await self._export_video(output_path, config.encoding)
            
            # 完成
            self._update_stage(PipelineStage.COMPLETED, 100)
            result.success = True
            result.output_path = final_path
            
        except Exception as e:
            self._logger.exception("Monologue pipeline failed")
            self._update_stage(PipelineStage.FAILED, 0)
            result.error = str(e)
        
        return result
    
    # ===== 内部方法 =====
    
    async def _analyze_video(self, path: str) -> Dict:
        """分析视频"""
        # 调用 SceneAnalyzer
        try:
            from ..ai.scene_analyzer import SceneAnalyzer
            analyzer = SceneAnalyzer()
            scenes = await analyzer.analyze(path)
            return {
                "duration": sum(s.end - s.start for s in scenes) if scenes else 60,
                "scenes": [{"start": s.start, "end": s.end, "desc": s.description} for s in scenes],
                "scene_count": len(scenes),
            }
        except Exception as e:
            return {"duration": 60, "scenes": [], "error": str(e)}
    
    async def _generate_script(self, config: CommentaryConfig, scene_info: Dict) -> str:
        """生成脚本"""
        # 调用 ScriptGenerator
        try:
            from ..ai.script_generator import ScriptGenerator, ScriptConfig
            generator = ScriptGenerator()
            script_config = ScriptConfig(
                topic=config.topic,
                style=config.style,
                duration=scene_info.get("duration", 60),
            )
            return await generator.generate(scene_info, script_config)
        except Exception:
            return f"关于{config.topic}的解说..."
    
    async def _generate_voice(self, config: CommentaryConfig, script: str) -> str:
        """生成配音"""
        # 调用 VoiceGenerator
        try:
            from ..ai.voice_generator import VoiceGenerator, VoiceConfig
            generator = VoiceGenerator()
            voice_config = VoiceConfig(
                voice_id=config.voice,
                rate=config.voice_speed,
            )
            return await generator.generate(script, voice_config)
        except Exception:
            return "/tmp/voice.mp3"
    
    async def _generate_captions(self, audio_path: str) -> str:
        """生成字幕"""
        # 调用 CaptionGenerator
        try:
            from ...video_tools.caption_generator import CaptionGenerator
            generator = CaptionGenerator()
            captions = generator.generate_from_audio(audio_path)
            return generator.generate_srt(captions)
        except Exception:
            return "/tmp/captions.srt"
    
    async def _render_video(
        self,
        video_path: str,
        audio_path: str,
        captions_path: str,
        output_path: str,
    ):
        """渲染视频"""
        # 使用 FFmpeg 合成
        import subprocess
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-vf", f"subtitles='{captions_path}'",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_path,
        ]
        subprocess.run(cmd, capture_output=True)
    
    async def _export_video(self, path: str, encoding: EncodingConfig) -> str:
        """导出视频"""
        # 直接返回路径
        # 实际可调用 VideoExporter
        return path
    
    async def _generate_mashup_script(self, config: MashupConfig, scenes: List[Dict]) -> str:
        """生成混剪脚本"""
        return f"混剪解说 - {config.theme}"
    
    async def _render_mashup(
        self,
        input_paths: List[str],
        script: str,
        output_path: str,
    ):
        """渲染混剪"""
        # 简化: 拼接所有视频
        import subprocess
        
        # 创建临时文件列表
        list_file = "/tmp/mashup_list.txt"
        with open(list_file, "w") as f:
            for path in input_paths:
                f.write(f"file '{path}'\n")
        
        # 合并视频
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            output_path,
        ]
        subprocess.run(cmd, capture_output=True)
    
    async def _analyze_frames(self, path: str, interval: float = 1.0) -> List[Dict]:
        """分析画面帧"""
        # 简化: 返回空列表
        # 实际项目中可调用 SceneAnalyzer
        return []
    
    async def _generate_monologue_script(
        self,
        config: MonologueConfig,
        frames: List[Dict],
    ) -> str:
        """生成独白脚本"""
        return f"第一人称独白 - {config.theme}"
    
    async def _generate_voice_for_monologue(
        self,
        config: MonologueConfig,
        script: str,
    ) -> str:
        """生成独白配音"""
        try:
            from ..ai.voice_generator import VoiceGenerator, VoiceConfig
            generator = VoiceGenerator()
            voice_config = VoiceConfig(voice_id=config.voice)
            return await generator.generate(script, voice_config)
        except Exception:
            return "/tmp/monologue_voice.mp3"
    
    async def _render_monologue(
        self,
        video_path: str,
        audio_path: str,
        captions_path: str,
        output_path: str,
    ):
        """渲染独白"""
        # 与普通渲染相同
        await self._render_video(video_path, audio_path, captions_path, output_path)


# 便捷函数
async def quick_commentary(
    topic: str,
    input_path: str,
    output_path: str,
    platform: str = "bilibili",
) -> PipelineResult:
    """快速创建解说视频"""
    config = PresetFactory.create_commentary_config(topic, platform=platform)
    pipeline = VideoPipeline()
    return await pipeline.run_commentary(config, input_path, output_path)


async def quick_mashup(
    theme: str,
    input_paths: List[str],
    output_path: str,
    platform: str = "bilibili",
) -> PipelineResult:
    """快速创建混剪视频"""
    config = PresetFactory.create_mashup_config(theme, platform=platform)
    pipeline = VideoPipeline()
    return await pipeline.run_mashup(config, input_paths, output_path)


async def quick_monologue(
    topic: str,
    input_path: str,
    output_path: str,
    platform: str = "bilibili",
) -> PipelineResult:
    """快速创建独白视频"""
    config = PresetFactory.create_monologue_config(topic, platform=platform)
    pipeline = VideoPipeline()
    return await pipeline.run_monologue(config, input_path, output_path)


__all__ = [
    "PipelineStage",
    "PipelineResult",
    "VideoPipeline",
    "quick_commentary",
    "quick_mashup",
    "quick_monologue",
]
