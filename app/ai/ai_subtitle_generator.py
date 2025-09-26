#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI智能字幕生成和翻译系统
提供语音识别、字幕生成、时间轴同步、多语言翻译等功能
"""

import cv2
import numpy as np
import wave
import json
import threading
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, deque
import logging
import queue
import tempfile
import os

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("警告: SpeechRecognition未安装，语音识别功能将被禁用")

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("警告: OpenAI Whisper未安装，高级语音识别功能将被禁用")

try:
    from googletrans import Translator
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    print("警告: googletrans未安装，翻译功能将被禁用")

try:
    from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
    from PyQt6.QtCore import pyqtSignal as Signal
except ImportError:
    try:
        from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread
        from PyQt5.QtCore import pyqtSignal as Signal
    except ImportError:
        try:
            from PySide2.QtCore import QObject, Signal, QTimer, QThread
        except ImportError:
            try:
                from PySide6.QtCore import QObject, Signal, QTimer, QThread
            except ImportError:
                class Signal:
                    def __init__(self, *args, **kwargs):
                        pass
                class QObject:
                    def __init__(self):
                        pass
                class QTimer:
                    def __init__(self):
                        pass
                class QThread:
                    def __init__(self):
                        pass


class SubtitleFormat(Enum):
    """字幕格式"""
    SRT = "srt"                    # SubRip格式
    VTT = "vtt"                    # WebVTT格式
    ASS = "ass"                    # Advanced SubStation Alpha
    SSA = "ssa"                    # SubStation Alpha
    TXT = "txt"                    # 纯文本格式


class Language(Enum):
    """支持的语言"""
    CHINESE = "zh"                 # 中文
    ENGLISH = "en"                 # 英语
    JAPANESE = "ja"                # 日语
    KOREAN = "ko"                  # 韩语
    FRENCH = "fr"                  # 法语
    GERMAN = "de"                  # 德语
    SPANISH = "es"                 # 西班牙语
    RUSSIAN = "ru"                 # 俄语
    ARABIC = "ar"                  # 阿拉伯语
    ITALIAN = "it"                 # 意大利语


@dataclass
class SubtitleSegment:
    """字幕段落"""
    start_time: float
    end_time: float
    text: str
    confidence: float
    language: Language
    speaker_id: Optional[str] = None
    emotion: Optional[str] = None


@dataclass
class SubtitleStyle:
    """字幕样式"""
    font_name: str = "Arial"
    font_size: int = 24
    font_color: str = "#FFFFFF"
    background_color: str = "#000000"
    background_opacity: float = 0.8
    outline_color: str = "#000000"
    outline_width: int = 1
    position: str = "bottom"       # top, bottom, center
    alignment: str = "center"       # left, center, right
    line_spacing: float = 1.2
    char_spacing: float = 1.0


class AudioExtractor:
    """音频提取器"""

    def __init__(self):
        self.sample_rate = 16000
        self.channels = 1

    def extract_audio_from_video(self, video_path: str, output_path: str = None) -> str:
        """从视频中提取音频"""
        if output_path is None:
            output_path = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name

        # 使用OpenCV提取音频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")

        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps

        # 使用ffmpeg提取音频（更可靠）
        import subprocess
        try:
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn', '-acodec', 'pcm_s16le',
                '-ar', str(self.sample_rate),
                '-ac', str(self.channels),
                '-y', output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"音频提取失败: {e}")
        finally:
            cap.release()

        return output_path

    def split_audio_into_segments(self, audio_path: str, segment_duration: float = 30.0) -> List[str]:
        """将音频分割成片段"""
        segments = []

        # 使用ffmpeg分割音频
        output_dir = tempfile.mkdtemp()
        base_name = os.path.splitext(os.path.basename(audio_path))[0]

        cmd = [
            'ffmpeg', '-i', audio_path,
            '-f', 'segment',
            '-segment_time', str(segment_duration),
            '-c', 'copy',
            os.path.join(output_dir, f"{base_name}%03d.wav")
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)

            # 收集分割后的文件
            for filename in sorted(os.listdir(output_dir)):
                if filename.startswith(base_name):
                    segments.append(os.path.join(output_dir, filename))

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"音频分割失败: {e}")

        return segments


class SpeechRecognizer:
    """语音识别器"""

    def __init__(self, model_type: str = "whisper"):
        self.model_type = model_type
        self.model = None
        self.recognizer = None

        if model_type == "whisper" and WHISPER_AVAILABLE:
            self.model = whisper.load_model("base")  # 使用base模型，可根据需要调整
        elif SPEECH_RECOGNITION_AVAILABLE:
            self.recognizer = sr.Recognizer()

    def recognize_audio(self, audio_path: str, language: Language = Language.CHINESE) -> SubtitleSegment:
        """识别音频文件"""
        try:
            if self.model_type == "whisper" and self.model is not None:
                return self._recognize_with_whisper(audio_path, language)
            elif self.recognizer is not None:
                return self._recognize_with_speech_recognition(audio_path, language)
            else:
                raise RuntimeError("没有可用的语音识别引擎")

        except Exception as e:
            logging.error(f"语音识别失败: {e}")
            return SubtitleSegment(
                start_time=0,
                end_time=0,
                text="[识别失败]",
                confidence=0.0,
                language=language
            )

    def _recognize_with_whisper(self, audio_path: str, language: Language) -> SubtitleSegment:
        """使用Whisper进行语音识别"""
        result = self.model.transcribe(
            audio_path,
            language=language.value,
            word_timestamps=True
        )

        # 提取文本和时间戳
        text = result["text"].strip()
        segments = result.get("segments", [])

        if segments:
            start_time = segments[0]["start"]
            end_time = segments[-1]["end"]
            confidence = np.mean([seg.get("no_speech_prob", 0) for seg in segments])
        else:
            start_time = end_time = 0
            confidence = 0.0

        return SubtitleSegment(
            start_time=start_time,
            end_time=end_time,
            text=text,
            confidence=1.0 - confidence,
            language=language
        )

    def _recognize_with_speech_recognition(self, audio_path: str, language: Language) -> SubtitleSegment:
        """使用SpeechRecognition进行语音识别"""
        with sr.AudioFile(audio_path) as source:
            audio = self.recognizer.record(source)

        try:
            text = self.recognizer.recognize_google(
                audio,
                language=language.value
            )
            confidence = 0.8  # Google Speech Recognition不提供置信度

            return SubtitleSegment(
                start_time=0,  # SpeechRecognition不提供时间戳
                end_time=0,
                text=text,
                confidence=confidence,
                language=language
            )

        except sr.UnknownValueError:
            return SubtitleSegment(
                start_time=0,
                end_time=0,
                text="[无法识别]",
                confidence=0.0,
                language=language
            )
        except sr.RequestError as e:
            return SubtitleSegment(
                start_time=0,
                end_time=0,
                text=f"[识别错误: {e}]",
                confidence=0.0,
                language=language
            )


class Translator:
    """翻译器"""

    def __init__(self):
        self.translator = None
        if TRANSLATION_AVAILABLE:
            self.translator = Translator()

    def translate_text(self, text: str, source_lang: Language, target_lang: Language) -> str:
        """翻译文本"""
        if not self.translator:
            return text  # 如果翻译器不可用，返回原文本

        try:
            result = self.translator.translate(
                text,
                src=source_lang.value,
                dest=target_lang.value
            )
            return result.text
        except Exception as e:
            logging.error(f"翻译失败: {e}")
            return text  # 翻译失败时返回原文本


class SubtitleGenerator:
    """字幕生成器"""

    def __init__(self):
        self.audio_extractor = AudioExtractor()
        self.speech_recognizer = SpeechRecognizer()
        self.translator = Translator()
        self.subtitle_segments: List[SubtitleSegment] = []

    def generate_subtitles(self, video_path: str, source_language: Language = Language.CHINESE,
                          target_languages: List[Language] = None,
                          segment_duration: float = 30.0) -> Dict[Language, List[SubtitleSegment]]:
        """生成字幕"""
        if target_languages is None:
            target_languages = [source_language]

        # 提取音频
        audio_path = self.audio_extractor.extract_audio_from_video(video_path)

        try:
            # 分割音频
            audio_segments = self.audio_extractor.split_audio_into_segments(audio_path, segment_duration)

            # 识别每个音频片段
            all_segments = []
            for i, segment_path in enumerate(audio_segments):
                segment = self.speech_recognizer.recognize_audio(segment_path, source_language)

                # 调整时间戳
                segment.start_time = i * segment_duration
                segment.end_time = (i + 1) * segment_duration

                all_segments.append(segment)

            # 优化时间轴
            self.subtitle_segments = self._optimize_timeline(all_segments)

            # 翻译字幕
            translated_subtitles = {}
            for target_lang in target_languages:
                if target_lang == source_language:
                    translated_subtitles[target_lang] = self.subtitle_segments
                else:
                    translated_subtitles[target_lang] = self._translate_subtitles(self.subtitle_segments, target_lang)

            return translated_subtitles

        finally:
            # 清理临时文件
            if os.path.exists(audio_path):
                os.remove(audio_path)

    def _optimize_timeline(self, segments: List[SubtitleSegment]) -> List[SubtitleSegment]:
        """优化时间轴"""
        optimized = []

        for segment in segments:
            # 调整字幕时长
            duration = segment.end_time - segment.start_time
            text_length = len(segment.text)

            # 基于文本长度调整显示时间
            optimal_duration = max(2.0, text_length * 0.1)  # 每个字符0.1秒，最少2秒

            if duration > optimal_duration:
                segment.end_time = segment.start_time + optimal_duration

            # 确保时间轴不重叠
            if optimized and segment.start_time < optimized[-1].end_time:
                segment.start_time = optimized[-1].end_time + 0.1

            optimized.append(segment)

        return optimized

    def _translate_subtitles(self, segments: List[SubtitleSegment], target_lang: Language) -> List[SubtitleSegment]:
        """翻译字幕"""
        translated = []

        for segment in segments:
            translated_text = self.translator.translate_text(
                segment.text, segment.language, target_lang
            )

            translated_segment = SubtitleSegment(
                start_time=segment.start_time,
                end_time=segment.end_time,
                text=translated_text,
                confidence=segment.confidence * 0.9,  # 翻译后置信度略有降低
                language=target_lang,
                speaker_id=segment.speaker_id,
                emotion=segment.emotion
            )
            translated.append(translated_segment)

        return translated

    def export_subtitles(self, segments: List[SubtitleSegment], output_path: str, format_type: SubtitleFormat = SubtitleFormat.SRT):
        """导出字幕文件"""
        if format_type == SubtitleFormat.SRT:
            self._export_srt(segments, output_path)
        elif format_type == SubtitleFormat.VTT:
            self._export_vtt(segments, output_path)
        elif format_type == SubtitleFormat.ASS:
            self._export_ass(segments, output_path)
        elif format_type == SubtitleFormat.TXT:
            self._export_txt(segments, output_path)
        else:
            raise ValueError(f"不支持的字幕格式: {format_type}")

    def _export_srt(self, segments: List[SubtitleSegment], output_path: str):
        """导出SRT格式字幕"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, 1):
                f.write(f"{i}\n")
                f.write(f"{self._format_time(segment.start_time)} --> {self._format_time(segment.end_time)}\n")
                f.write(f"{segment.text}\n\n")

    def _export_vtt(self, segments: List[SubtitleSegment], output_path: str):
        """导出WebVTT格式字幕"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            for segment in segments:
                f.write(f"{self._format_time_vtt(segment.start_time)} --> {self._format_time_vtt(segment.end_time)}\n")
                f.write(f"{segment.text}\n\n")

    def _export_ass(self, segments: List[SubtitleSegment], output_path: str):
        """导出ASS格式字幕"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("[Script Info]\n")
            f.write("Title: Generated Subtitles\n")
            f.write("ScriptType: v4.00+\n")
            f.write("WrapStyle: 0\n")
            f.write("ScaledBorderAndShadow: yes\n")
            f.write("YCbCr Matrix: None\n\n")
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
            f.write("Style: Default,Arial,24,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,1,0,2,0,0,0,1\n\n")
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

            for segment in segments:
                start = self._format_time_ass(segment.start_time)
                end = self._format_time_ass(segment.end_time)
                f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{segment.text}\n")

    def _export_txt(self, segments: List[SubtitleSegment], output_path: str):
        """导出纯文本格式字幕"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for segment in segments:
                f.write(f"[{self._format_time(segment.start_time)}] {segment.text}\n")

    def _format_time(self, seconds: float) -> str:
        """格式化时间（SRT格式）"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

    def _format_time_vtt(self, seconds: float) -> str:
        """格式化时间（WebVTT格式）"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"

    def _format_time_ass(self, seconds: float) -> str:
        """格式化时间（ASS格式）"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds % 1) * 100)
        return f"{hours:01d}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"


class SubtitleRenderer:
    """字幕渲染器"""

    def __init__(self):
        self.style = SubtitleStyle()

    def render_subtitle_on_frame(self, frame: np.ndarray, segment: SubtitleSegment) -> np.ndarray:
        """在帧上渲染字幕"""
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np

        # 转换为PIL图像
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image)

        # 设置字体
        try:
            font = ImageFont.truetype(self.style.font_name, self.style.font_size)
        except:
            font = ImageFont.load_default()

        # 计算文本位置
        text = segment.text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        frame_height, frame_width = frame.shape[:2]

        if self.style.position == "bottom":
            y = frame_height - text_height - 50
        elif self.style.position == "top":
            y = 30
        else:  # center
            y = (frame_height - text_height) // 2

        if self.style.alignment == "center":
            x = (frame_width - text_width) // 2
        elif self.style.alignment == "left":
            x = 50
        else:  # right
            x = frame_width - text_width - 50

        # 绘制背景
        padding = 10
        bg_coords = [
            x - padding, y - padding,
            x + text_width + padding, y + text_height + padding
        ]

        # 转换颜色
        bg_color = self._hex_to_rgb(self.style.background_color)
        bg_color = (*bg_color, int(self.style.background_opacity * 255))

        # 创建透明背景
        overlay = Image.new('RGBA', pil_image.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # 绘制半透明背景
        overlay_draw.rectangle(bg_coords, fill=bg_color)

        # 绘制文本
        text_color = self._hex_to_rgb(self.style.font_color)
        draw.text((x, y), text, font=font, fill=text_color)

        # 如果有描边，绘制描边
        if self.style.outline_width > 0:
            outline_color = self._hex_to_rgb(self.style.outline_color)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
            draw.text((x, y), text, font=font, fill=text_color)

        # 合并图像
        pil_image = Image.alpha_composite(pil_image.convert('RGBA'), overlay)
        result = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

        return result

    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """十六进制颜色转RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


class AISubtitleGenerator(QObject):
    """AI字幕生成器主类"""

    # 信号定义
    generation_started = Signal(str)  # 生成开始
    generation_progress = Signal(int, str)  # 生成进度
    generation_completed = Signal(dict)  # 生成完成
    generation_error = Signal(str)  # 生成错误
    rendering_completed = Signal(str)  # 渲染完成

    def __init__(self):
        super().__init__()
        self.generator = SubtitleGenerator()
        self.renderer = SubtitleRenderer()
        self.is_generating = False
        self.generation_thread = None

    def generate_subtitles_async(self, video_path: str, source_language: Language = Language.CHINESE,
                               target_languages: List[Language] = None,
                               output_dir: str = None):
        """异步生成字幕"""
        if self.is_generating:
            self.generation_error.emit("正在生成字幕中，请等待完成")
            return

        self.is_generating = True
        self.generation_started.emit(video_path)

        # 创建生成线程
        self.generation_thread = SubtitleGenerationThread(
            self.generator, video_path, source_language, target_languages, output_dir
        )
        self.generation_thread.progress_updated.connect(self.generation_progress.emit)
        self.generation_thread.generation_completed.connect(self._on_generation_completed)
        self.generation_thread.error_occurred.connect(self.generation_error.emit)
        self.generation_thread.start()

    def _on_generation_completed(self, results: Dict[Language, List[SubtitleSegment]]):
        """生成完成回调"""
        self.is_generating = False
        self.generation_completed.emit(results)

    def render_subtitles_to_video(self, video_path: str, segments: List[SubtitleSegment],
                                 output_path: str, language: Language = Language.CHINESE):
        """将字幕渲染到视频"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"无法打开视频文件: {video_path}")

            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            frame_count = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # 获取当前时间
                current_time = frame_count / fps

                # 查找当前时间段的字幕
                current_subtitle = None
                for segment in segments:
                    if segment.start_time <= current_time <= segment.end_time:
                        current_subtitle = segment
                        break

                # 渲染字幕
                if current_subtitle:
                    frame = self.renderer.render_subtitle_on_frame(frame, current_subtitle)

                # 写入帧
                out.write(frame)
                frame_count += 1

            cap.release()
            out.release()

            self.rendering_completed.emit(output_path)

        except Exception as e:
            self.generation_error.emit(f"视频渲染失败: {str(e)}")

    def stop_generation(self):
        """停止生成"""
        if self.generation_thread and self.generation_thread.isRunning():
            self.generation_thread.stop()
            self.is_generating = False

    def update_style(self, style: SubtitleStyle):
        """更新字幕样式"""
        self.renderer.style = style


class SubtitleGenerationThread(QThread):
    """字幕生成线程"""

    progress_updated = Signal(int, str)
    generation_completed = Signal(dict)
    error_occurred = Signal(str)

    def __init__(self, generator: SubtitleGenerator, video_path: str,
                 source_language: Language, target_languages: List[Language], output_dir: str):
        super().__init__()
        self.generator = generator
        self.video_path = video_path
        self.source_language = source_language
        self.target_languages = target_languages
        self.output_dir = output_dir
        self._is_running = True

    def run(self):
        """运行字幕生成"""
        try:
            self.progress_updated.emit(10, "开始生成字幕...")

            # 生成字幕
            results = self.generator.generate_subtitles(
                self.video_path, self.source_language, self.target_languages
            )

            if not self._is_running:
                return

            self.progress_updated.emit(80, "导出字幕文件...")

            # 导出字幕文件
            if self.output_dir:
                import os
                os.makedirs(self.output_dir, exist_ok=True)

                for language, segments in results.items():
                    filename = f"subtitles_{language.value}.srt"
                    output_path = os.path.join(self.output_dir, filename)
                    self.generator.export_subtitles(segments, output_path, SubtitleFormat.SRT)

            self.progress_updated.emit(100, "字幕生成完成")
            self.generation_completed.emit(results)

        except Exception as e:
            self.error_occurred.emit(f"字幕生成失败: {str(e)}")

    def stop(self):
        """停止线程"""
        self._is_running = False
        self.wait()


# 工具函数
def create_subtitle_generator() -> AISubtitleGenerator:
    """创建字幕生成器"""
    return AISubtitleGenerator()


def quick_generate_subtitles(video_path: str, source_lang: str = "zh", output_dir: str = None) -> Dict[str, List[SubtitleSegment]]:
    """快速生成字幕（同步版本）"""
    generator = SubtitleGenerator()
    source_language = Language(source_lang)
    results = generator.generate_subtitles(video_path, source_language)

    if output_dir:
        import os
        os.makedirs(output_dir, exist_ok=True)
        for language, segments in results.items():
            filename = f"subtitles_{language.value}.srt"
            output_path = os.path.join(output_dir, filename)
            generator.export_subtitles(segments, output_path, SubtitleFormat.SRT)

    return results


def main():
    """主函数 - 用于测试"""
    # 创建字幕生成器
    generator = create_subtitle_generator()

    # 测试字幕生成功能
    print("AI字幕生成器创建成功")
    print(f"语音识别可用: {SPEECH_RECOGNITION_AVAILABLE or WHISPER_AVAILABLE}")
    print(f"翻译功能可用: {TRANSLATION_AVAILABLE}")


if __name__ == "__main__":
    main()