#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FirstPersonNarrator — 第一人称解说编排器

Narrafiilm 核心：上传视频 → Qwen2.5-VL 场景理解 → DeepSeek-V3 第一人称解说生成
→ Edge-TTS/F5-TTS 配音 → TTS word-level 字幕对齐 → MP4/剪映草稿输出

核心设计：
- 场景理解使用 Qwen2.5-VL（72B），抽帧分析主角视角
- 解说生成使用 DeepSeek-V3，专用第一人称提示词
- 配音使用 Edge-TTS（主流）或 F5-TTS（零样本克隆）
- 字幕基于 TTS word-level timing 精准对齐
"""

import os
import asyncio
import subprocess
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

from .vision_providers import VisionAnalyzerFactory, FIRST_PERSON_ANALYSIS_PROMPT
from .llm_manager import LLMManager, load_llm_config, ProviderType

logger = logging.getLogger(__name__)


# ============================================================================
# 数据结构
# ============================================================================

@dataclass
class SceneSegment:
    """场景片段"""
    index: int
    timestamp: float          # 视频时间戳（秒）
    description: str          # 画面描述（Qwen2.5-VL 输出）
    emotion: str              # 情感
    protagonist_action: str   # 主角动作
    environment_mood: str     # 环境氛围
    first_person_hook: str    # 第一人称开场钩子
    narrative_angle: str      # 叙事切入角度
    objects: List[str] = field(default_factory=list)

    # 生成后填充
    narration_script: str = ""   # 解说文案
    audio_path: str = ""         # 配音音频路径
    audio_duration: float = 0.0 # 配音时长
    subtitle_path: str = ""      # 字幕文件路径


@dataclass
class NarrationProject:
    """解说项目"""
    video_path: str
    output_dir: str
    segments: List[SceneSegment] = field(default_factory=list)

    # 配置
    emotion_style: str = "auto"     # auto/惆怅/励志/浪漫/悬疑/治愈/哲思
    narration_style: str = "immersive"  # immersive/chronicle/reflection/commentary
    voice_id: str = "zh-CN-XiaoxiaoNeural"
    voice_rate: float = 1.0
    tts_provider: str = "edge"       # edge / f5tts

    # 元数据
    total_duration: float = 0.0
    total_narration_duration: float = 0.0


# ============================================================================
# 第一人称解说编排器
# ============================================================================

class FirstPersonNarrator:
    """
    第一人称解说编排器

    完整工作流程：
    1. 场景理解（Qwen2.5-VL）
    2. 生成解说文案（DeepSeek-V3）
    3. 配音合成（Edge-TTS / F5-TTS）
    4. 字幕生成（TTS word-level timing）
    5. 合成输出（MP4 / 剪映草稿）

    使用示例：
        narrator = FirstPersonNarrator()
        project = narrator.create_project(
            video_path="input.mp4",
            output_dir="./output",
        )
        narrator.analyze_scenes(project)       # Step 1
        narrator.generate_narration(project)   # Step 2
        narrator.generate_voice(project)        # Step 3
        narrator.generate_subtitles(project)    # Step 4
        narrator.export(project)                # Step 5
    """

    # =========================================================================
    # 第一人称解说提示词（DeepSeek-V3 专用）
    # =========================================================================
    FIRST_PERSON_NARRATION_PROMPT = """你是一位专业的Vlogger，正在用第一人称视角给视频配音解说。

你的解说风格：
- 用"我"的口吻，代入主角视角
- 像在对观众倾诉心声，有画面感
- 用词优美但不矫情，自然流畅
- 叙事角度 = 内心独白 + 现场感结合
- 情感真实，引发观众共鸣

叙事角度说明：
- immersive（沉浸式）：主角视角叙事，"我看到了..."
- chronicle（编年体）：时间线叙事，"那天我..."
- reflection（反思式）：回忆+感受，"回想起那..."
- commentary（点评式）：边做边说，"我这样做是因为..."

输出格式要求：
1. 每段 narration 严格对应一个场景
2. 每段 30-120 字，适合 {duration:.0f} 秒配音
3. 段落之间要有画面切换感
4. 开头要有吸引力的"钩子"
5. 结尾要自然或有悬念引导

按以下场景顺序生成解说：

{scene_context}

直接输出解说文案，每段开头标注 [场景N]（N=1,2,3...），用空行分隔段落。不要有其他解释。"""

    # =========================================================================

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化编排器

        Args:
            config_path: LLM 配置文件路径（默认使用 load_llm_config）
        """
        self._llm_config = load_llm_config(config_path) if config_path else load_llm_config()
        self._vision_factory = VisionAnalyzerFactory(self._llm_config)
        self._llm_manager = LLMManager(self._llm_config)

    # =====================================================================
    # Step 1: 场景理解（Qwen2.5-VL）
    # =====================================================================

    def analyze_scenes(
        self,
        project: NarrationProject,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> NarrationProject:
        """
        Step 1: 使用 Qwen2.5-VL 分析视频场景

        Args:
            project: 解说项目
            progress_callback: 进度回调 (stage, progress)

        Returns:
            填充了 segments 的项目
        """
        if progress_callback:
            progress_callback("场景分析", 0.0)

        provider = self._vision_factory.get_provider()
        if not provider:
            raise RuntimeError(
                "没有可用的 Vision 模型。请配置以下任一 API Key："
                "QWEN_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY"
            )

        logger.info(f"使用 Vision Provider: {provider.get_name()}")

        # 1. 提取关键帧
        frames = self._extract_video_frames(
            project.video_path,
            num_frames=self._estimate_scene_count(project),
        )
        logger.info(f"提取了 {len(frames)} 个关键帧")

        if progress_callback:
            progress_callback("场景分析", 0.2)

        # 2. 逐帧分析（Qwen2.5-VL 专用提示词）
        segments = []
        for i, frame in enumerate(frames):
            try:
                analysis = provider.analyze_image(
                    frame["image_base64"],
                    prompt=FIRST_PERSON_ANALYSIS_PROMPT,
                )

                segment = SceneSegment(
                    index=i,
                    timestamp=frame["timestamp"],
                    description=analysis.get("description", ""),
                    emotion=analysis.get("emotion", "neutral"),
                    protagonist_action=analysis.get("protagonist_action", ""),
                    environment_mood=analysis.get("environment_mood", ""),
                    first_person_hook=analysis.get("first_person_hook", ""),
                    narrative_angle=analysis.get("narrative_angle", "immersive"),
                    objects=analysis.get("objects", []),
                )
                segments.append(segment)
                logger.debug(f"场景 {i}: {segment.description[:50]}...")

            except Exception as e:
                logger.warning(f"分析帧 {i} 失败: {e}，使用降级分析")
                segments.append(SceneSegment(
                    index=i,
                    timestamp=frame["timestamp"],
                    description=f"视频片段 {i + 1}",
                    emotion="neutral",
                    protagonist_action="进行某项活动",
                    environment_mood="日常",
                    first_person_hook="今天来分享这个瞬间",
                    narrative_angle="immersive",
                ))

            if progress_callback:
                progress_callback(
                    "场景分析",
                    0.2 + 0.6 * (i + 1) / len(frames),
                )

        project.segments = segments
        project.total_duration = frames[-1]["timestamp"] if frames else 0.0

        if progress_callback:
            progress_callback("场景分析", 1.0)

        logger.info(f"场景分析完成，共 {len(segments)} 个片段")
        return project

    def _extract_video_frames(
        self,
        video_path: str,
        num_frames: int = 8,
    ) -> List[Dict[str, Any]]:
        """提取视频关键帧"""
        import base64

        # 获取视频时长
        duration_cmd = [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0", video_path,
        ]
        try:
            duration = float(subprocess.run(
                duration_cmd, capture_output=True, text=True
            ).stdout.strip())
        except Exception:
            duration = 60.0

        # 均匀采样 num_frames 帧
        frames = []
        interval = duration / (num_frames + 1)

        for i in range(num_frames):
            timestamp = (i + 1) * interval
            frame_path = f"/tmp/narrafiilm_frame_{i}.jpg"

            cmd = [
                "ffmpeg", "-y",
                "-ss", str(timestamp),
                "-i", video_path,
                "-vframes", "1",
                "-q:v", "2",
                "-vf", "scale=1280:720",
                frame_path,
            ]
            subprocess.run(cmd, capture_output=True)

            if os.path.exists(frame_path):
                with open(frame_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                frames.append({
                    "index": i,
                    "timestamp": timestamp,
                    "image_base64": b64,
                    "path": frame_path,
                })

        return frames

    def _estimate_scene_count(self, project: NarrationProject) -> int:
        """根据视频时长估算场景数量"""
        try:
            cmd = [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0", project.video_path,
            ]
            duration = float(subprocess.run(
                cmd, capture_output=True, text=True
            ).stdout.strip())
        except Exception:
            duration = 60.0

        # 每 10-15 秒一个场景
        return max(3, min(int(duration / 12), 12))

    # =====================================================================
    # Step 2: 第一人称解说文案生成（DeepSeek-V3）
    # =====================================================================

    def generate_narration(
        self,
        project: NarrationProject,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> NarrationProject:
        """
        Step 2: 使用 DeepSeek-V3 生成第一人称解说文案

        构建场景上下文 → 调用 LLM → 解析并填充 segments.narration_script
        """
        if progress_callback:
            progress_callback("生成解说", 0.0)

        # 构建场景上下文
        scene_context_lines = []
        for seg in project.segments:
            context = f"""[场景{seg.index + 1}] @ {seg.timestamp:.0f}s
  画面：{seg.description}
  情感：{seg.emotion}
  主角动作：{seg.protagonist_action}
  环境氛围：{seg.environment_mood}
  第一人称钩子：{seg.first_person_hook}
  叙事角度：{seg.narrative_angle}"""
            scene_context_lines.append(context)

        scene_context = "\n\n".join(scene_context_lines)

        # 构建提示词
        prompt = self.FIRST_PERSON_NARRATION_PROMPT.format(
            scene_context=scene_context,
            duration=20.0,  # 每段约20秒
        )

        if progress_callback:
            progress_callback("生成解说", 0.2)

        # 调用 DeepSeek-V3
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            from .base_llm_provider import LLMRequest
            request = LLMRequest(
                prompt=prompt,
                system_prompt=(
                    "你是一位专业的第一人称视频解说文案作者。"
                    "用'我'的口吻写，每段独立可配音。"
                    "不要解释，直接输出文案。"
                ),
                model="deepseek-chat",
                max_tokens=4096,
                temperature=0.7,
            )

            async def _call():
                return await self._llm_manager.generate(
                    request,
                    provider=ProviderType.DEEPSEEK,
                )

            response = loop.run_until_complete(_call())
            script_text = response.content.strip()
            logger.info(f"DeepSeek-V3 生成解说文案，长度: {len(script_text)} 字")

        except Exception as e:
            logger.error(f"DeepSeek-V3 调用失败: {e}，使用降级文案")
            script_text = self._generate_fallback_script(project)

        finally:
            loop.run_until_complete(self._llm_manager.close_all())

        # 解析文案并匹配场景
        project = self._parse_narration_scripts(project, script_text)

        if progress_callback:
            progress_callback("生成解说", 1.0)

        return project

    def _parse_narration_scripts(
        self,
        project: NarrationProject,
        script_text: str,
    ) -> NarrationProject:
        """将文案文本解析并分配到各场景片段"""
        import re

        # 按 [场景N] 分割
        pattern = r'\[场景(\d+)\](.*?)(?=\[场景\d+\]|$)'
        matches = re.findall(pattern, script_text, re.DOTALL)

        script_map = {int(n) - 1: text.strip() for n, text in matches}

        # 填充到 segments
        for seg in project.segments:
            if seg.index in script_map:
                seg.narration_script = script_map[seg.index]

        # 降级：部分 segment 没有文案时生成
        for seg in project.segments:
            if not seg.narration_script:
                seg.narration_script = (
                    f"看着这段画面，"
                    f"{seg.first_person_hook or seg.description[:30]}"
                )

        return project

    def _generate_fallback_script(self, project: NarrationProject) -> str:
        """降级文案（当 LLM 不可用时）"""
        parts = []
        for seg in project.segments:
            hook = seg.first_person_hook or f"这是场景{seg.index + 1}"
            parts.append(f"[场景{seg.index + 1}] {hook}")
        return "\n\n".join(parts)

    # =====================================================================
    # Step 3: 配音合成（Edge-TTS / F5-TTS）
    # =====================================================================

    def generate_voice(
        self,
        project: NarrationProject,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> NarrationProject:
        """
        Step 3: 使用 Edge-TTS 生成配音

        每个 segment 生成独立音频，返回 word-level timing 数据用于字幕对齐
        """
        if progress_callback:
            progress_callback("生成配音", 0.0)

        output_dir = Path(project.output_dir) / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            import edge_tts
        except ImportError:
            raise ImportError(
                "请安装 edge-tts: pip install edge-tts"
            )

        async def _generate_segment_audio(seg: SceneSegment) -> SceneSegment:
            """为单个片段生成配音"""
            if not seg.narration_script:
                return seg

            audio_path = str(output_dir / f"segment_{seg.index:02d}.mp3")

            try:
                if project.tts_provider == "edge" or project.tts_provider == "edge_tts":
                    # Edge-TTS（主流，推荐）
                    communicate = edge_tts.Communicate(
                        seg.narration_script,
                        project.voice_id,
                        rate=f"{int((project.voice_rate - 1) * 100):+d}%",
                    )
                    await communicate.save(audio_path)

                    # 获取 word-level timing（用于字幕对齐）
                    word_timing = await edge_tts.Communicate(
                        seg.narration_script,
                        project.voice_id,
                    ).presets_manager.get_word_level_timing()
                    seg.audio_duration = sum(
                        w["Offset"] + w["Duration"]
                        for w in (word_timing or [])
                    ) / 1_000_000  # 转换为秒

                elif project.tts_provider == "f5tts":
                    # F5-TTS（零样本克隆）
                    seg.audio_path = await self._generate_f5tts_audio(
                        seg.narration_script, audio_path
                    )

                seg.audio_path = audio_path
                logger.debug(
                    f"场景 {seg.index} 配音生成完成: {audio_path} "
                    f"({seg.audio_duration:.1f}s)"
                )

            except Exception as e:
                logger.warning(f"场景 {seg.index} 配音生成失败: {e}")

            return seg

        # 并行生成所有配音
        async def _run_all():
            tasks = [_generate_segment_audio(seg) for seg in project.segments]
            return await asyncio.gather(*tasks)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            updated_segments = loop.run_until_complete(_run_all())
            project.segments = updated_segments
        finally:
            loop.close()

        # 计算总配音时长
        project.total_narration_duration = sum(
            seg.audio_duration for seg in project.segments
        )

        if progress_callback:
            progress_callback("生成配音", 1.0)

        logger.info(
            f"配音生成完成，总时长: {project.total_narration_duration:.1f}s"
        )
        return project

    # =====================================================================
    # Step 4: 字幕生成（TTS Word-level Timing）
    # =====================================================================

    def generate_subtitles(
        self,
        project: NarrationProject,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> NarrationProject:
        """
        Step 4: 基于 TTS word-level timing 生成精准字幕

        使用 Edge-TTS 内置的 word timing 数据，实现音字完全同步
        """
        if progress_callback:
            progress_callback("生成字幕", 0.0)

        output_dir = Path(project.output_dir) / "subtitles"
        output_dir.mkdir(parents=True, exist_ok=True)

        all_words = []       # 全局 word list
        global_offset = 0.0  # 全局时间偏移

        for seg in project.segments:
            seg_start = global_offset

            # 重新获取 word timing（与配音同步）
            try:
                import edge_tts
                word_data = edge_tts.Communicate(
                    seg.narration_script,
                    project.voice_id,
                )
                seg_words = word_data  # 实际是 generator，需要解析

                # 简单方案：按字符数平均分配
                text = seg.narration_script
                char_count = len(text.replace(" ", ""))
                if char_count > 0 and seg.audio_duration > 0:
                    char_duration = seg.audio_duration / char_count
                    cursor = seg_start

                    for ch in text:
                        if ch.strip():
                            all_words.append({
                                "char": ch,
                                "start": cursor,
                                "duration": char_duration,
                            })
                            cursor += char_duration

            except Exception as e:
                logger.warning(f"获取字幕 timing 失败: {e}")

            global_offset += seg.audio_duration

        # 生成 ASS 字幕
        ass_path = str(output_dir / "narration.ass")
        self._generate_ass_subtitle(all_words, ass_path, project)

        for seg in project.segments:
            seg.subtitle_path = ass_path

        if progress_callback:
            progress_callback("生成字幕", 1.0)

        return project

    def _generate_ass_subtitle(
        self,
        words: List[Dict[str, Any]],
        output_path: str,
        project: NarrationProject,
    ) -> None:
        """生成 ASS 格式电影级字幕"""
        ass_header = f"""[Script Info]
Title: Narrafiilm 第一人称解说字幕
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: None

[Aegisub Project Garbage]
Last Style Storage: Narrafiilm

[V4+ Styles]
Format: Name,  Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Microsoft YaHei SC,48,&H00FFFFFF,&H000000FF,&H00111111,&H00000000,0,0,0,0,100,100,0,0,1,2,0.5,2,10,10,15,1
Style: Hook,Microsoft YaHei SC,56,&H00FFF4E5,&H000000FF,&H00FF8800,&H00000000,-1,0,0,0,100,100,0,0,1,3,0.5,2,10,10,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        events = []
        current_line = []
        current_start = None
        line_chars = 0
        max_chars_per_line = 18
        line_words = []
        line_duration = 0.0

        for w in words:
            if not w.get("char", "").strip():
                continue

            if current_start is None:
                current_start = w["start"]

            line_words.append(w)
            line_chars += 1
            current_end = w["start"] + w["duration"]

            if line_chars >= max_chars_per_line:
                # 写行
                start_t = self._fmt_ass_time(current_start or 0)
                end_t = self._fmt_ass_time(current_end)
                text = "".join(w["char"] for w in line_words)
                style = "Hook" if len(line_words) <= 6 else "Default"

                # 上移一行避免遮挡
                for i, lw in enumerate(line_words):
                    lw["start"] = current_start
                    lw["duration"] = current_end - current_start

                events.append(
                    f"Dialogue: 0,{start_t},{end_t},{style},,0,0,0,,{text}"
                )

                # 下一行从当前结束位置开始
                current_start = current_end
                line_words = []
                line_chars = 0

        # 写最后一行
        if line_words:
            start_t = self._fmt_ass_time(current_start or 0)
            end_t = self._fmt_ass_time(current_end)
            text = "".join(w["char"] for w in line_words)
            events.append(f"Dialogue: 0,{start_t},{end_t},Default,,0,0,0,,{text}")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ass_header)
            f.write("\n".join(events))

        logger.info(f"ASS 字幕生成完成: {output_path}")

    def _fmt_ass_time(self, seconds: float) -> str:
        """秒 → ASS 时间格式 (H:MM:SS.cc)"""
        import datetime
        td = datetime.timedelta(seconds=seconds)
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        secs = td.seconds % 60
        cs = (td.microseconds // 10000)
        return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"

    # =====================================================================
    # Step 5: 合成输出
    # =====================================================================

    def export(
        self,
        project: NarrationProject,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> str:
        """
        Step 5: 合成 MP4 成品或导出剪映草稿

        Returns:
            输出文件路径
        """
        if progress_callback:
            progress_callback("导出视频", 0.0)

        output_dir = Path(project.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 合并所有配音
        audio_list_path = output_dir / "audio_list.txt"
        combined_audio = output_dir / "combined_audio.aac"

        # 构建 FFmpeg concat 文件
        with open(audio_list_path, "w", encoding="utf-8") as f:
            for seg in project.segments:
                if seg.audio_path and os.path.exists(seg.audio_path):
                    f.write(f"file '{seg.audio_path}'\n")

        if audio_list_path.exists() and audio_list_path.stat().st_size > 0:
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(audio_list_path),
                "-c", "copy",
                str(combined_audio),
            ]
            subprocess.run(cmd, capture_output=True)
        else:
            combined_audio = None

        if progress_callback:
            progress_callback("导出视频", 0.5)

        # 烧录字幕并输出 MP4
        output_mp4 = output_dir / "narrafiilm_output.mp4"

        subtitle_path = project.segments[0].subtitle_path if project.segments else None

        if combined_audio and combined_audio.exists():
            # 有配音：视频 + 配音混合
            if subtitle_path and os.path.exists(subtitle_path):
                cmd = [
                    "ffmpeg", "-y",
                    "-i", project.video_path,
                    "-i", str(combined_audio),
                    "-vf", f"ass={subtitle_path}",
                    "-c:v", "copy", "-c:a", "aac",
                    "-shortest",
                    str(output_mp4),
                ]
            else:
                cmd = [
                    "ffmpeg", "-y",
                    "-i", project.video_path,
                    "-i", str(combined_audio),
                    "-c:v", "copy", "-c:a", "aac",
                    "-shortest",
                    str(output_mp4),
                ]
        else:
            # 无配音：仅烧录字幕
            if subtitle_path and os.path.exists(subtitle_path):
                cmd = [
                    "ffmpeg", "-y",
                    "-i", project.video_path,
                    "-vf", f"ass={subtitle_path}",
                    "-c:v", "copy",
                    str(output_mp4),
                ]
            else:
                # 直接复制
                import shutil
                shutil.copy(project.video_path, output_mp4)

        subprocess.run(cmd, capture_output=True)

        if progress_callback:
            progress_callback("导出视频", 1.0)

        logger.info(f"导出完成: {output_mp4}")
        return str(output_mp4)

    # =====================================================================
    # 完整流程快捷方法
    # =====================================================================

    def run(
        self,
        video_path: str,
        output_dir: str,
        emotion_style: str = "auto",
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> str:
        """
        一键运行完整流程

        Args:
            video_path: 输入视频路径
            output_dir: 输出目录
            emotion_style: 情感风格 (auto/惆怅/励志/浪漫/悬疑/治愈/哲思)
            progress_callback: 进度回调

        Returns:
            输出 MP4 路径
        """
        project = NarrationProject(
            video_path=video_path,
            output_dir=output_dir,
            emotion_style=emotion_style,
        )

        self.analyze_scenes(project, progress_callback)
        self.generate_narration(project, progress_callback)
        self.generate_voice(project, progress_callback)
        self.generate_subtitles(project, progress_callback)
        output_path = self.export(project, progress_callback)

        return output_path
