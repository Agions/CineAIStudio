#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字幕提取模块
支持两种方式：
1. OCR 提取 — 从视频画面中识别字幕文字（Vision API）
2. 语音转文字 — 从音频中提取语音内容（Whisper / 在线 API）

两种方式可以组合使用，互相补充。
"""

import os
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class SubtitleSegment:
    """字幕片段"""
    start: float           # 开始时间（秒）
    end: float             # 结束时间（秒）
    text: str              # 字幕文本
    confidence: float = 1.0
    source: str = ""       # "ocr" / "speech" / "merged"


@dataclass
class SubtitleExtractionResult:
    """字幕提取结果"""
    video_path: str
    duration: float
    segments: List[SubtitleSegment] = field(default_factory=list)
    full_text: str = ""
    language: str = "zh"
    method: str = ""       # "ocr" / "speech" / "both"


class OCRSubtitleExtractor:
    """
    OCR 字幕提取器
    从视频关键帧中通过 Vision API 识别画面中的字幕文字
    """

    def __init__(self, api_key: Optional[str] = None,
                 provider: str = "openai"):
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._provider = provider

    def extract(self, video_path: str,
                sample_interval: float = 1.0,
                max_frames: int = 60) -> SubtitleExtractionResult:
        """
        从视频提取 OCR 字幕

        Args:
            video_path: 视频路径
            sample_interval: 采样间隔（秒）
            max_frames: 最大帧数
        """
        import base64

        path = Path(video_path)
        if not path.exists():
            raise FileNotFoundError(f"视频不存在: {video_path}")

        duration = self._get_duration(video_path)
        result = SubtitleExtractionResult(
            video_path=video_path,
            duration=duration,
            method="ocr",
        )

        # 提取关键帧
        frames = self._extract_frames(video_path, duration,
                                       sample_interval, max_frames)

        if not frames:
            return result

        # 批量 OCR
        segments = []
        prev_text = ""

        for timestamp, frame_path in frames:
            try:
                with open(frame_path, 'rb') as f:
                    img_b64 = base64.b64encode(f.read()).decode()

                text = self._ocr_frame(img_b64)

                if text and text != prev_text:
                    # 新字幕出现
                    if segments and segments[-1].text == prev_text:
                        segments[-1].end = timestamp

                    segments.append(SubtitleSegment(
                        start=timestamp,
                        end=timestamp + sample_interval,
                        text=text,
                        source="ocr",
                    ))
                    prev_text = text
                elif text and text == prev_text and segments:
                    # 字幕延续
                    segments[-1].end = timestamp + sample_interval

            except Exception as e:
                print(f"OCR 帧 {timestamp:.1f}s 失败: {e}")

        # 清理临时文件
        for _, fp in frames:
            try:
                os.unlink(fp)
            except Exception:
                pass

        result.segments = segments
        result.full_text = " ".join(s.text for s in segments)
        return result

    def _ocr_frame(self, image_base64: str) -> str:
        """对单帧进行 OCR"""
        if self._provider == "openai":
            return self._ocr_openai(image_base64)
        return ""

    def _ocr_openai(self, image_base64: str) -> str:
        """使用 OpenAI Vision 做 OCR"""
        from openai import OpenAI

        client = OpenAI(api_key=self._api_key)
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "提取这张视频截图中的字幕文字。只返回字幕文字内容，如果没有字幕则返回空字符串。不要加任何解释。"},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}",
                        "detail": "low"
                    }}
                ]
            }],
            max_tokens=200,
        )
        text = response.choices[0].message.content.strip()
        if text in ("", "无", "无字幕", "空", "没有字幕"):
            return ""
        return text

    def _extract_frames(self, video_path: str, duration: float,
                        interval: float, max_frames: int) -> List[Tuple[float, str]]:
        """提取关键帧"""
        tmpdir = tempfile.mkdtemp(prefix="clipflow_ocr_")
        frames = []
        num = min(int(duration / interval) + 1, max_frames)

        for i in range(num):
            ts = i * interval
            if ts > duration:
                break
            out = os.path.join(tmpdir, f"frame_{i:04d}.jpg")
            cmd = [
                'ffmpeg', '-y', '-ss', str(ts),
                '-i', video_path, '-vframes', '1',
                '-q:v', '5', out
            ]
            r = subprocess.run(cmd, capture_output=True)
            if r.returncode == 0 and os.path.exists(out):
                frames.append((ts, out))

        return frames

    def _get_duration(self, video_path: str) -> float:
        """获取视频时长"""
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'csv=p=0', video_path
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        try:
            return float(r.stdout.strip())
        except (ValueError, AttributeError):
            return 0.0


class SpeechSubtitleExtractor:
    """
    语音转字幕提取器
    从视频/音频中通过语音识别提取字幕

    支持：
    1. OpenAI Whisper API（推荐，精度高）
    2. 本地 whisper 模型（离线，需安装 openai-whisper）
    """

    def __init__(self, api_key: Optional[str] = None,
                 mode: str = "api"):
        """
        Args:
            api_key: OpenAI API key（mode=api 时需要）
            mode: "api"（OpenAI Whisper API） / "local"（本地 whisper）
        """
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._mode = mode

    def extract(self, video_path: str,
                language: str = "zh") -> SubtitleExtractionResult:
        """
        从视频/音频提取语音字幕

        Args:
            video_path: 视频或音频文件路径
            language: 语言代码
        """
        path = Path(video_path)
        duration = self._get_duration(str(path))

        result = SubtitleExtractionResult(
            video_path=str(path),
            duration=duration,
            language=language,
            method="speech",
        )

        # 先提取音频
        audio_path = self._extract_audio(str(path))

        try:
            if self._mode == "api":
                segments = self._transcribe_api(audio_path, language)
            else:
                segments = self._transcribe_local(audio_path, language)

            result.segments = segments
            result.full_text = " ".join(s.text for s in segments)
        finally:
            # 清理临时音频
            if audio_path != str(path):
                try:
                    os.unlink(audio_path)
                except Exception:
                    pass

        return result

    def _transcribe_api(self, audio_path: str,
                        language: str) -> List[SubtitleSegment]:
        """使用 OpenAI Whisper API 转录"""
        from openai import OpenAI

        client = OpenAI(api_key=self._api_key)

        with open(audio_path, 'rb') as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language=language,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

        segments = []
        if hasattr(response, 'segments') and response.segments:
            for seg in response.segments:
                segments.append(SubtitleSegment(
                    start=seg.get("start", seg.start) if isinstance(seg, dict) else seg.start,
                    end=seg.get("end", seg.end) if isinstance(seg, dict) else seg.end,
                    text=(seg.get("text", "") if isinstance(seg, dict) else seg.text).strip(),
                    confidence=seg.get("avg_logprob", 0) if isinstance(seg, dict) else getattr(seg, 'avg_logprob', 0),
                    source="speech",
                ))
        elif hasattr(response, 'text'):
            # 无时间戳，整段返回
            segments.append(SubtitleSegment(
                start=0, end=self._get_duration(audio_path),
                text=response.text.strip(),
                source="speech",
            ))

        return segments

    def _transcribe_local(self, audio_path: str,
                          language: str) -> List[SubtitleSegment]:
        """使用本地 whisper 模型转录"""
        try:
            import whisper
        except ImportError:
            raise ImportError(
                "本地 Whisper 需要安装: pip install openai-whisper"
            )

        model = whisper.load_model("base")
        result = model.transcribe(audio_path, language=language)

        segments = []
        for seg in result.get("segments", []):
            segments.append(SubtitleSegment(
                start=seg["start"],
                end=seg["end"],
                text=seg["text"].strip(),
                source="speech",
            ))

        return segments

    def _extract_audio(self, video_path: str) -> str:
        """从视频提取音频"""
        # 如果已经是音频文件，直接返回
        ext = Path(video_path).suffix.lower()
        if ext in ('.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'):
            return video_path

        output = tempfile.mktemp(suffix='.wav', prefix='clipflow_stt_')
        cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le',
            '-ar', '16000', '-ac', '1',
            output
        ]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode != 0:
            raise RuntimeError(f"音频提取失败: {r.stderr.decode()[:200]}")
        return output

    def _get_duration(self, path: str) -> float:
        cmd = ['ffprobe', '-v', 'quiet', '-show_entries',
               'format=duration', '-of', 'csv=p=0', path]
        r = subprocess.run(cmd, capture_output=True, text=True)
        try:
            return float(r.stdout.strip())
        except (ValueError, AttributeError):
            return 0.0


class SubtitleMerger:
    """
    字幕合并器
    将 OCR 字幕和语音字幕合并，去重，生成最终字幕
    """

    @staticmethod
    def merge(ocr_result: SubtitleExtractionResult,
              speech_result: SubtitleExtractionResult,
              overlap_threshold: float = 0.5) -> SubtitleExtractionResult:
        """
        合并两种来源的字幕

        策略：
        - 时间重叠且文本相似 → 保留语音版（时间更准）
        - 仅 OCR 有 → 保留（可能是画面中的标题/注释）
        - 仅语音有 → 保留（可能是画外音）
        """
        merged = SubtitleExtractionResult(
            video_path=ocr_result.video_path,
            duration=max(ocr_result.duration, speech_result.duration),
            method="both",
        )

        speech_segs = list(speech_result.segments)
        ocr_segs = list(ocr_result.segments)

        used_ocr = set()

        # 以语音为主
        for sp_seg in speech_segs:
            merged.segments.append(SubtitleSegment(
                start=sp_seg.start,
                end=sp_seg.end,
                text=sp_seg.text,
                confidence=sp_seg.confidence,
                source="speech",
            ))

            # 标记时间重叠的 OCR 字幕
            for i, ocr_seg in enumerate(ocr_segs):
                overlap = SubtitleMerger._overlap_ratio(sp_seg, ocr_seg)
                if overlap > overlap_threshold:
                    used_ocr.add(i)

        # 添加未匹配的 OCR 字幕（画面标题、注释等）
        for i, ocr_seg in enumerate(ocr_segs):
            if i not in used_ocr and ocr_seg.text.strip():
                merged.segments.append(SubtitleSegment(
                    start=ocr_seg.start,
                    end=ocr_seg.end,
                    text=f"[画面] {ocr_seg.text}",
                    confidence=ocr_seg.confidence,
                    source="ocr",
                ))

        # 按时间排序
        merged.segments.sort(key=lambda s: s.start)
        merged.full_text = " ".join(s.text for s in merged.segments)

        return merged

    @staticmethod
    def _overlap_ratio(a: SubtitleSegment, b: SubtitleSegment) -> float:
        """计算两个时间段的重叠比例"""
        overlap_start = max(a.start, b.start)
        overlap_end = min(a.end, b.end)
        overlap = max(0, overlap_end - overlap_start)
        total = max(a.end - a.start, b.end - b.start, 0.001)
        return overlap / total


# ========== 便捷函数 ==========

def extract_subtitles(video_path: str,
                      method: str = "speech",
                      api_key: Optional[str] = None,
                      language: str = "zh") -> SubtitleExtractionResult:
    """
    提取字幕的便捷函数

    Args:
        video_path: 视频路径
        method: "ocr" / "speech" / "both"
        api_key: API key
        language: 语言

    Returns:
        字幕提取结果
    """
    if method == "ocr":
        extractor = OCRSubtitleExtractor(api_key=api_key)
        return extractor.extract(video_path)

    elif method == "speech":
        extractor = SpeechSubtitleExtractor(api_key=api_key)
        return extractor.extract(video_path, language=language)

    elif method == "both":
        ocr_ext = OCRSubtitleExtractor(api_key=api_key)
        speech_ext = SpeechSubtitleExtractor(api_key=api_key)

        ocr_result = ocr_ext.extract(video_path)
        speech_result = speech_ext.extract(video_path, language=language)

        return SubtitleMerger.merge(ocr_result, speech_result)

    else:
        raise ValueError(f"不支持的方法: {method}，可选: ocr/speech/both")
