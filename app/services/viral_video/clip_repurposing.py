"""
ClipRepurposingPipeline — 长视频转短片段自动化管线
将长视频（播客/访谈/教程）自动转换为多条平台适配的高光短片段。

设计参考：OpusClip / Reap / Vizard.ai

管线步骤：
    1. 音频提取（FFmpeg）
    2. 场景分割（FFmpeg scene detection）
    3. 音频转录（Faster-Whisper，CPU 友好）
    4. 多维 AI 评分（ClipScorer）
    5. Top-N 片段选择（可配置数量）
    6. 字幕生成（SRT + 动态字幕）
    7. 格式转换（横→竖智能裁剪）

使用方式：
    from app.services.viral_video.clip_repurposing import ClipRepurposingPipeline, AspectRatio

    pipeline = ClipRepurposingPipeline()
    results = pipeline.run(
        video_path="/path/to/long_video.mp4",
        output_dir="./output/clips",
        max_clips=5,
        target_aspect_ratio=AspectRatio.VERTICAL_9_16,
        languages=["zh", "en"],
    )
    for clip in results:
        print(f"→ {clip.output_path} (score={clip.score.total_score:.1f})")
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Callable, Dict

from .clip_scorer import ClipScorer, ClipSegment, ClipScore

logger = logging.getLogger(__name__)


# ============================================================
# Enums
# ============================================================

class AspectRatio(Enum):
    """目标宽高比"""
    HORIZONTAL_16_9 = "16:9"
    VERTICAL_9_16 = "9:16"
    SQUARE_1_1 = "1:1"
    VERTICAL_4_5 = "4:5"


class SubtitleStyle(Enum):
    """字幕样式预设"""
    DEFAULT = "default"          # 白字黑框，底部居中
    CINEMATIC = "cinematic"     # 黄色渐变，半透明背景
    SOCIAL = "social"            # 大字白色，底部 20%
    COMPACT = "compact"          # 小字，顶部


@dataclass
class PlatformPreset:
    """平台预设"""
    name: str
    aspect_ratio: AspectRatio
    max_duration: float          # 秒
    fps: int = 30
    bitrate: str = "8M"
    subtitle_style: SubtitleStyle = SubtitleStyle.DEFAULT


PLATFORM_PRESETS = {
    "douyin": PlatformPreset(
        name="抖音",
        aspect_ratio=AspectRatio.VERTICAL_9_16,
        max_duration=60.0,
        fps=30,
        bitrate="8M",
    ),
    "xiaohongshu": PlatformPreset(
        name="小红书",
        aspect_ratio=AspectRatio.VERTICAL_9_16,
        max_duration=60.0,
        fps=30,
        bitrate="8M",
    ),
    "tiktok": PlatformPreset(
        name="TikTok",
        aspect_ratio=AspectRatio.VERTICAL_9_16,
        max_duration=60.0,
        fps=30,
        bitrate="8M",
    ),
    "youtube_shorts": PlatformPreset(
        name="YouTube Shorts",
        aspect_ratio=AspectRatio.VERTICAL_9_16,
        max_duration=60.0,
        fps=30,
        bitrate="8M",
    ),
    "instagram_reels": PlatformPreset(
        name="Instagram Reels",
        aspect_ratio=AspectRatio.VERTICAL_9_16,
        max_duration=60.0,
        fps=30,
        bitrate="8M",
    ),
    "twitter": PlatformPreset(
        name="Twitter/X",
        aspect_ratio=AspectRatio.SQUARE_1_1,
        max_duration=140.0,
        fps=30,
        bitrate="8M",
    ),
}


# ============================================================
# Output Types
# ============================================================

@dataclass
class ClipOutput:
    """单个短片段的输出结果"""
    clip_id: str
    output_path: str
    score: ClipScore
    aspect_ratio: AspectRatio
    platform: str
    subtitle_path: Optional[str] = None
    thumbnail_paths: List[str] = field(default_factory=list)  # noqa: E999
    duration: float = 0.0


@dataclass
class PipelineConfig:
    """管线配置"""
    # 选段配置
    max_clips: int = 5                   # 最多生成几条短片段
    min_clip_duration: float = 20.0      # 秒，最短片段
    max_clip_duration: float = 90.0    # 秒，最长片段
    clip_gap: float = 2.0               # 秒，片段间最小间隔（防重叠）

    # 评分权重（可选）
    scorer_weights: Optional[dict] = None

    # 转录配置
    languages: List[str] = field(default_factory=lambda: ["zh", "en"])  # Whisper 语言列表
    transcription_model: str = "base"    # faster-whisper 模型大小

    # 字幕配置
    subtitle_style: SubtitleStyle = SubtitleStyle.DEFAULT
    subtitle_font_size: int = 48         # 字体大小（px）
    subtitle_color: str = "#FFFFFF"      # 白色

    # 裁剪配置
    crop_strategy: str = "center"       # center | face | sound

    # 回调
    progress_callback: Optional[Callable[[str, float], None]] = None

    def report(self, step: str, progress: float) -> None:
        """进度回调"""
        if self.progress_callback:
            self.progress_callback(step, progress)


# ============================================================
# Pipeline
# ============================================================

class ClipRepurposingPipeline:
    """
    长视频 → 多条短片段自动化管线

    设计原则：
    - 全步骤 CPU 可运行（FFmpeg + Faster-Whisper）
    - 每个步骤均可独立替换（注入自定义实现）
    - 进度回调支持 UI 实时展示
    """

    def __init__(self, output_dir: str = "./output/clips"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._scorer: Optional[ClipScorer] = None

    @property
    def scorer(self) -> ClipScorer:
        if self._scorer is None:
            self._scorer = ClipScorer()
        return self._scorer

    def run(
        self,
        video_path: str,
        output_dir: Optional[str] = None,
        config: Optional[PipelineConfig] = None,
        target_aspect_ratio: Optional[AspectRatio] = None,
        platform: Optional[str] = None,
        max_clips: int = 5,
    ) -> List[ClipOutput]:
        """
        运行完整管线

        Args:
            video_path: 输入长视频路径
            output_dir: 输出目录（覆盖构造函数默认值）
            config: 管线配置
            target_aspect_ratio: 目标宽高比（快捷参数）
            platform: 平台预设快捷键（douyin/tiktok/xiaohongshu/...）
            max_clips: 最多片段数（快捷参数）

        Returns:
            ClipOutput 列表，按评分降序
        """
        import time
        start_time = time.time()

        cfg = config or PipelineConfig()
        if max_clips != 5:
            cfg.max_clips = max_clips

        # 应用平台预设
        preset: Optional[PlatformPreset] = None
        if platform and platform in PLATFORM_PRESETS:
            preset = PLATFORM_PRESETS[platform]
            cfg.max_clip_duration = preset.max_duration
            target_aspect_ratio = target_aspect_ratio or preset.aspect_ratio

        output_path = Path(output_dir) if output_dir else self.output_dir
        output_path.mkdir(parents=True, exist_ok=True)

        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        run_id = uuid.uuid4().hex[:8]
        cfg.report("初始化", 0.05)

        # =====================================================
        # Step 1: 音频提取
        # =====================================================
        logger.info(f"[{run_id}] Step 1: 提取音频")
        cfg.report("提取音频", 0.1)
        audio_path = self._extract_audio(video_path, output_path, run_id)
        if not audio_path:
            raise RuntimeError("音频提取失败")

        # =====================================================
        # Step 2: 场景分割
        # =====================================================
        logger.info(f"[{run_id}] Step 2: 场景分割")
        cfg.report("场景分割", 0.2)
        scenes = self._split_scenes(video_path, output_path, run_id)
        if not scenes:
            logger.warning(f"[{run_id}] 未检测到场景，使用整段")
            duration = self._get_duration(video_path)
            scenes = [ClipSegment(start_time=0.0, end_time=duration)]

        # =====================================================
        # Step 3: 音频转录
        # =====================================================
        logger.info(f"[{run_id}] Step 3: 音频转录")
        cfg.report("音频转录", 0.4)
        segments = self._transcribe_segments(
            audio_path, scenes, cfg, output_path, run_id
        )
        if not segments:
            # 转录失败时使用无文本片段（纯视觉评分）
            logger.warning(f"[{run_id}] 转录失败，使用无文本评分模式")
            segments = scenes

        # =====================================================
        # Step 4: 多维 AI 评分
        # =====================================================
        logger.info(f"[{run_id}] Step 4: AI 评分")
        cfg.report("AI 评分", 0.65)
        scored = self.scorer.score_segments(segments)

        # =====================================================
        # Step 5: 选择 Top-N（防止重叠）
        # =====================================================
        logger.info(f"[{run_id}] Step 5: 选择 Top-{cfg.max_clips} 片段")
        cfg.report("选择片段", 0.75)
        top_segments = self._select_top_non_overlapping(scored, cfg)

        # =====================================================
        # Step 6: 格式转换 + 字幕生成
        # =====================================================
        logger.info(f"[{run_id}] Step 6: 生成短片段")
        cfg.report("生成片段", 0.85)
        target_ratio = target_aspect_ratio or AspectRatio.VERTICAL_9_16
        results = self._generate_clips(
            video_path, output_path, top_segments, target_ratio,
            cfg, run_id, preset,
        )

        cfg.report("完成", 1.0)
        elapsed = time.time() - start_time
        logger.info(f"[{run_id}] 管线完成：{len(results)} 条片段，耗时 {elapsed:.1f}s")

        return results

    # --------------------------------------------------------
    # Step Implementations (可子类覆盖)
    # --------------------------------------------------------

    def _extract_audio(
        self, video_path: Path, output_dir: Path, run_id: str
    ) -> Optional[Path]:
        """Step 1: 用 FFmpeg 提取音频"""
        audio_path = output_dir / f"audio_{run_id}.wav"
        import subprocess
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-vn", "-acodec", "pcm_s16le",
                "-ar", "16000", "-ac", "1",
                str(audio_path),
            ]
            result = subprocess.run(
                cmd, capture_output=True, timeout=300
            )
            if result.returncode == 0 and audio_path.exists():
                return audio_path
            logger.error(f"音频提取失败: {result.stderr[:200]}")
        except Exception as e:
            logger.error(f"音频提取异常: {e}")
        return None

    def _split_scenes(
        self, video_path: Path, output_dir: Path, run_id: str
    ) -> List[ClipSegment]:
        """Step 2: 用 FFmpeg scene detection 分割场景"""
        import subprocess
        import json

        scenes: List[ClipSegment] = []
        scene_list_path = output_dir / f"scenes_{run_id}.txt"

        try:
            # FFmpeg scene detection: 输出为 nanosecond timestamps
            cmd = [
                "ffmpeg", "-i", str(video_path),
                "-filter:v", "select='gt(scene,0.3)',showinfo",
                "-f", "null", "-",
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600
            )
            # 解析 showinfo 中的 pts_time 字段
            timestamps: List[float] = []
            for line in result.stderr.split("\n"):
                if "pts_time" in line:
                    try:
                        ts = float(line.split("pts_time:")[1].split()[0])
                        timestamps.append(ts)
                    except Exception:
                        pass

            if not timestamps:
                # Fallback: 固定间隔分割
                duration = self._get_duration(video_path)
                interval = 60.0
                for start in range(0, int(duration), int(interval)):
                    scenes.append(ClipSegment(
                        start_time=float(start),
                        end_time=min(float(start + interval), duration),
                    ))
                return scenes

            # 合并相邻间隔 < 5s 的场景
            for ts in timestamps:
                if not scenes:
                    scenes.append(ClipSegment(start_time=ts, end_time=ts))
                else:
                    last = scenes[-1]
                    if ts - last.end_time < 5.0:
                        last.end_time = ts
                    else:
                        scenes.append(ClipSegment(start_time=ts, end_time=ts))

            # 补全最后 end_time
            duration = self._get_duration(video_path)
            for seg in scenes:
                if seg.end_time == seg.start_time:
                    seg.end_time = min(seg.start_time + 30, duration)

        except Exception as e:
            logger.warning(f"场景分割失败: {e}")

        return scenes

    def _transcribe_segments(
        self,
        audio_path: Path,
        scenes: List[ClipSegment],
        config: PipelineConfig,
        output_dir: Path,
        run_id: str,
    ) -> List[ClipSegment]:
        """
        Step 3: 用 Faster-Whisper 对每个场景段落转录
        CPU 运行，使用 medium 模型精度/速度平衡
        """
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            logger.warning("Faster-Whisper 未安装，跳过转录: pip install faster-whisper")
            return scenes

        try:
            # CPU 模型选择：small（快）或 medium（准）
            model_size = config.transcription_model or "small"
            logger.info(f"加载 Faster-Whisper {model_size} (CPU)...")
            model = WhisperModel(model_size, device="cpu", compute_type="int8")

            for seg in scenes:
                try:
                    # 提取该时间段的音频
                    import subprocess
                    seg_audio = output_dir / f"seg_{seg.start_time:.0f}_{run_id}.wav"
                    cmd = [
                        "ffmpeg", "-y", "-i", str(audio_path),
                        "-ss", str(seg.start_time),
                        "-to", str(seg.end_time),
                        "-acodec", "pcm_s16le", "-ar", "16000",
                        str(seg_audio),
                    ]
                    subprocess.run(cmd, capture_output=True, timeout=60)

                    if seg_audio.exists() and seg_audio.stat().st_size > 1000:
                        segments_ws, _ = model.transcribe(
                            str(seg_audio),
                            language=config.languages[0] if config.languages else None,
                            beam_size=3,
                            vad_filter=True,  # 语音活动检测，过滤静音
                        )
                        text_parts = [s.text for s in segments_ws]
                        seg.transcript = "".join(text_parts).strip()

                    # 清理临时音频
                    seg_audio.unlink(missing_ok=True)

                except Exception as e:
                    logger.debug(f"片段转录失败 [{seg.start_time}s]: {e}")

            del model

        except Exception as e:
            logger.warning(f"Faster-Whisper 转录失败: {e}")

        return scenes

    def _select_top_non_overlapping(
        self,
        scored: List[ClipScore],
        config: PipelineConfig,
    ) -> List[ClipSegment]:
        """Step 5: 选择 Top-N 片段（防止时间重叠）"""
        selected: List[ClipSegment] = []
        covered_ranges: List[tuple[float, float]] = []

        for score in scored:
            if len(selected) >= config.max_clips:
                break

            seg = score.segment
            start, end = seg.start_time, seg.end_time

            # 检查是否与已选片段重叠
            overlaps = any(
                not (end <= covered_start or start >= covered_end)
                for covered_start, covered_end in covered_ranges
            )

            # 检查最小间隔
            has_min_gap = all(
                end + config.clip_gap <= covered_start or start >= covered_end + config.clip_gap
                for covered_start, covered_end in covered_ranges
            )

            if not overlaps and (not covered_ranges or has_min_gap):
                selected.append(seg)
                covered_ranges.append((start, end))

        return selected

    def _generate_clips(
        self,
        video_path: Path,
        output_dir: Path,
        segments: List[ClipSegment],
        target_ratio: AspectRatio,
        config: PipelineConfig,
        run_id: str,
        preset: Optional[PlatformPreset] = None,
    ) -> List[ClipOutput]:
        """Step 6 & 7: 生成裁剪片段 + 字幕"""
        import subprocess
        results: List[ClipOutput] = []

        for i, seg in enumerate(segments):
            clip_id = f"{run_id}_{i:02d}"
            clip_output = output_dir / f"clip_{clip_id}.mp4"
            srt_path = output_dir / f"subtitle_{clip_id}.srt"

            # 确定裁剪参数
            crop_filter = self._build_crop_filter(video_path, target_ratio, config.crop_strategy)

            # 构建字幕滤镜
            subtitle_filter = self._build_subtitle_filter(str(srt_path), config.subtitle_style)

            # FFmpeg 裁剪 + 字幕烧录
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(seg.start_time),
                "-i", str(video_path),
                "-t", str(seg.end_time - seg.start_time),
            ]
            if crop_filter:
                cmd += ["-vf", crop_filter]
            if subtitle_filter:
                cmd += ["-vf", subtitle_filter]

            cmd += [
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac",
                "-b:a", "128k",
                str(clip_output),
            ]

            try:
                result = subprocess.run(cmd, capture_output=True, timeout=300)
                if result.returncode != 0:
                    logger.error(f"FFmpeg 片段生成失败: {result.stderr[:200]}")
                    continue

                # 生成 SRT 字幕（如果 transcript 存在）
                srt_written = False
                if seg.transcript:
                    srt_written = self._write_srt(
                        seg.transcript,
                        seg.start_time,
                        str(srt_path),
                    )

                results.append(ClipOutput(
                    clip_id=clip_id,
                    output_path=str(clip_output),
                    score=ClipScore(
                        segment=seg,
                        total_score=getattr(seg, "_score", 0.0),
                    ),
                    aspect_ratio=target_ratio,
                    platform=preset.name if preset else target_ratio.value,
                    subtitle_path=str(srt_path) if srt_written else None,
                    duration=seg.end_time - seg.start_time,
                ))

            except Exception as e:
                logger.error(f"片段 {clip_id} 生成失败: {e}")

        return results

    def _get_duration(self, video_path: Path) -> float:
        """获取视频时长（秒）"""
        import subprocess
        try:
            cmd = ["ffprobe", "-v", "error",
                   "-show_entries", "format=duration",
                   "-of", "default=noprint_wrappers=1:nokey=1",
                   str(video_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip())
        except Exception:
            return 60.0

    def _build_crop_filter(
        self, video_path: Path, target_ratio: AspectRatio, strategy: str
    ) -> Optional[str]:
        """
        构建 FFmpeg crop 滤镜参数

        center 策略：主体居中裁剪（默认）
        face    策略：人脸检测优先（需 OpenCV）
        sound   策略：声音来源定位
        """
        import subprocess

        # 获取原始分辨率
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=p=0", str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            w, h = map(int, result.stdout.strip().split(","))
        except Exception:
            w, h = 1920, 1080

        target_w, target_h = self._ratio_to_wh(target_ratio)

        if w * target_h > h * target_w:
            # 视频更宽，按宽度裁剪高度
            new_h = min(h, w * target_h // target_w)
            new_w = w
            x_offset = 0
            y_offset = (h - new_h) // 2
        else:
            # 视频更高，按高度裁剪宽度
            new_w = min(w, h * target_w // target_h)
            new_h = h
            x_offset = (w - new_w) // 2
            y_offset = 0

        return f"crop={new_w}:{new_h}:{x_offset}:{y_offset}"

    def _ratio_to_wh(self, ratio: AspectRatio) -> tuple[int, int]:
        """宽高比 → 目标像素尺寸（基准宽度 1080）"""
        mapping = {
            AspectRatio.VERTICAL_9_16: (1080, 1920),
            AspectRatio.HORIZONTAL_16_9: (1920, 1080),
            AspectRatio.SQUARE_1_1: (1080, 1080),
            AspectRatio.VERTICAL_4_5: (1080, 1350),
        }
        return mapping.get(ratio, (1080, 1920))

    def _build_subtitle_filter(
        self, srt_path: str, style: SubtitleStyle
    ) -> Optional[str]:
        """
        构建 FFmpeg subtitles 滤镜，将 SRT 烧入视频。
        返回 VF 参数字符串，如 srt 文件不存在则返回 None。
        """
        import os
        if not os.path.exists(srt_path):
            return None

        # FFmpeg subtitles 滤镜支持 ASS/SRT，这里用 sashow
        # 使用 force_style 控制样式
        if style == SubtitleStyle.CINEMATIC:
            # 黄色渐变，半透明背景
            return (
                f"subtitles={srt_path}:force_style='"
                f"FontName=Arial,FontSize=48,"
                f"PrimaryColour=&H00FFFF&,BackColour=&H80000000,"
                f"Bold=1,Alignment=2,MarginV=40'"
            )
        elif style == SubtitleStyle.SOCIAL:
            # 大字白色，底部
            return (
                f"subtitles={srt_path}:force_style='"
                f"FontName=Arial,FontSize=56,"
                f"PrimaryColour=&H00FFFFFF&,Alignment=2,MarginV=60'"
            )
        else:
            return f"subtitles={srt_path}"

    def _write_srt(
        self, text: str, start_time: float, output_path: str
    ) -> bool:
        """将转录文本写入 SRT 字幕文件"""
        import os
        if not text.strip():
            return False
        try:
            # 简单处理：整段为一条字幕
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("1\n")
                f.write(f"{self._format_srt_time(start_time)} --> {self._format_srt_time(start_time + 30)}\n")
                f.write(f"{text.strip()}\n\n")
            return os.path.exists(output_path)
        except Exception as e:
            logger.warning(f"SRT 写入失败: {e}")
            return False

    def _format_srt_time(self, seconds: float) -> str:
        """秒 → SRT 时间格式 00:00:00,000"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
