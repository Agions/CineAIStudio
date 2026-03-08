#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字幕提取器 - 支持多种方式
1. 用户导入字幕文件 (SRT/ASS/VTT)
2. 语音识别 (ASR)
3. OCR 识别硬字幕
"""

from typing import List, Dict, Optional
from enum import Enum
from pathlib import Path


class SubtitleSource(Enum):
    """字幕来源"""
    IMPORT = "import"    # 用户导入
    ASR = "asr"        # 语音识别
    OCR = "ocr"         # OCR 识别


class SubtitleExtractor:
    """
    多方式字幕提取器
    
    支持：
    1. 用户导入字幕文件
    2. 语音识别 (ASR)
    3. OCR 识别硬字幕
    """
    
    def __init__(self):
        self._source = SubtitleSource.IMPORT
    
    def extract(
        self,
        video_path: str = None,
        subtitle_file: str = None,
        source: str = "auto",
    ) -> List[Dict]:
        """
        提取字幕
        
        Args:
            video_path: 视频路径
            subtitle_file: 用户导入的字幕文件 (可选)
            source: auto/import/asr/ocr
            
        Returns:
            [{"start": 0, "end": 5, "text": "..."}, ...]
        """
        # 1. 用户导入字幕 (最准确)
        if source == "import" or source == "auto":
            if subtitle_file:
                return self._extract_from_file(subtitle_file)
        
        # 2. 语音识别 (ASR)
        if source == "asr" or source == "auto":
            if video_path:
                return self._extract_from_asr(video_path)
        
        # 3. OCR 识别 (最后选项)
        if source == "ocr" or source == "auto":
            if video_path:
                return self._extract_from_ocr(video_path)
        
        return []
    
    def _extract_from_file(self, file_path: str) -> List[Dict]:
        """
        从用户导入的字幕文件提取
        
        支持格式：SRT, ASS, VTT
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix == ".srt":
            return self._parse_srt(file_path)
        elif suffix == ".ass" or suffix == ".ssa":
            return self._parse_ass(file_path)
        elif suffix == ".vtt":
            return self._parse_vtt(file_path)
        else:
            # 尝试自动识别
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(100)
                
                if "WEBVTT" in content:
                    return self._parse_vtt(file_path)
                elif "[Script Info]" in content or "[Events]" in content:
                    return self._parse_ass(file_path)
                else:
                    return self._parse_srt(file_path)
    
    def _extract_from_asr(self, video_path: str) -> List[Dict]:
        """
        通过语音识别提取字幕
        
        使用 ASR 技术识别视频中的语音
        """
        # TODO: 集成 ASR 服务
        # 可以使用:
        # - Whisper (本地)
        # - 阿里云 ASR
        # - 腾讯云 ASR
        
        return []
    
    def _extract_from_ocr(self, video_path: str) -> List[Dict]:
        """
        通过 OCR 识别硬字幕
        
        识别视频中嵌入的文字
        """
        # TODO: 实现 OCR 识别
        # 可以使用:
        # - EasyOCR
        # - Tesseract
        # - 云服务 OCR
        
        return []
    
    # ===== SRT 解析 =====
    
    def _parse_srt(self, file_path: str) -> List[Dict]:
        """解析 SRT 文件"""
        subtitles = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        blocks = content.strip().split("\n\n")
        
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue
            
            # 解析时间
            time_line = lines[1]
            times = time_line.split(" --> ")
            
            if len(times) != 2:
                continue
            
            start = self._parse_srt_time(times[0].strip())
            end = self._parse_srt_time(times[1].strip())
            text = "\n".join(lines[2:])
            
            subtitles.append({
                "start": start,
                "end": end,
                "text": text.strip(),
                "source": SubtitleSource.IMPORT.value,
                "confidence": 0.98,
            })
        
        return subtitles
    
    def _parse_srt_time(self, time_str: str) -> float:
        """解析 SRT 时间"""
        # 格式: 00:00:00,000
        time_str = time_str.replace(",", ".")
        parts = time_str.split(":")
        
        if len(parts) == 3:
            h = float(parts[0])
            m = float(parts[1])
            s = float(parts[2])
            return h * 3600 + m * 60 + s
        
        return 0.0
    
    # ===== ASS 解析 =====
    
    def _parse_ass(self, file_path: str) -> List[Dict]:
        """解析 ASS 文件"""
        subtitles = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for line in content.split("\n"):
            if line.startswith("Dialogue:"):
                parts = line[9:].split(",", 9)
                
                if len(parts) >= 10:
                    start = self._parse_ass_time(parts[1].strip())
                    end = self._parse_ass_time(parts[2].strip())
                    text = parts[9].strip()
                    
                    # 清理样式标签
                    import re
                    text = re.sub(r'\{[^}]*\}', '', text)
                    text = text.replace("\\N", " ").replace("\\n", " ")
                    
                    subtitles.append({
                        "start": start,
                        "end": end,
                        "text": text.strip(),
                        "source": SubtitleSource.IMPORT.value,
                        "confidence": 0.95,
                    })
        
        return subtitles
    
    def _parse_ass_time(self, time_str: str) -> float:
        """解析 ASS 时间"""
        # 格式: 0:00:00.00
        parts = time_str.split(":")
        
        if len(parts) == 3:
            h = float(parts[0])
            m = float(parts[1])
            s = float(parts[2])
            return h * 3600 + m * 60 + s
        
        return 0.0
    
    # ===== VTT 解析 =====
    
    def _parse_vtt(self, file_path: str) -> List[Dict]:
        """解析 VTT 文件"""
        subtitles = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 移除 WEBVTT 头
        if "WEBVTT" in content:
            content = content.split("WEBVTT", 1)[1]
        
        blocks = content.strip().split("\n\n")
        
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 2:
                continue
            
            # 找时间行
            time_line = None
            text_start = 1
            
            for i, line in enumerate(lines):
                if "-->" in line:
                    time_line = line
                    text_start = i + 1
                    break
            
            if not time_line:
                continue
            
            times = time_line.split(" --> ")
            
            if len(times) != 2:
                continue
            
            start = self._parse_vtt_time(times[0].strip())
            end = self._parse_vtt_time(times[1].strip())
            text = "\n".join(lines[text_start:])
            
            subtitles.append({
                "start": start,
                "end": end,
                "text": text.strip(),
                "source": SubtitleSource.IMPORT.value,
                "confidence": 0.97,
            })
        
        return subtitles
    
    def _parse_vtt_time(self, time_str: str) -> float:
        """解析 VTT 时间"""
        # 格式: 00:00:00.000 或 00:00.000
        parts = time_str.split(":")
        
        if len(parts) == 3:
            h = float(parts[0])
            m = float(parts[1])
            s = float(parts[2])
            return h * 3600 + m * 60 + s
        elif len(parts) == 2:
            m = float(parts[0])
            s = float(parts[1])
            return m * 60 + s
        
        return 0.0


# 全局实例
_subtitle_extractor = SubtitleExtractor()


def extract_subtitles(
    video_path: str = None,
    subtitle_file: str = None,
    source: str = "auto",
) -> List[Dict]:
    """
    提取字幕
    
    Args:
        video_path: 视频路径
        subtitle_file: 用户导入的字幕文件 (SRT/ASS/VTT)
        source: auto/import/asr/ocr
        
    Returns:
        字幕列表
    """
    return _subtitle_extractor.extract(video_path, subtitle_file, source)


def extract_from_file(subtitle_file: str) -> List[Dict]:
    """从字幕文件提取"""
    return _subtitle_extractor._extract_from_file(subtitle_file)


def extract_from_asr(video_path: str) -> List[Dict]:
    """通过语音识别提取"""
    return _subtitle_extractor._extract_from_asr(video_path)


def extract_from_ocr(video_path: str) -> List[Dict]:
    """通过 OCR 提取"""
    return _subtitle_extractor._extract_from_ocr(video_path)


__all__ = [
    "SubtitleSource",
    "SubtitleExtractor",
    "extract_subtitles",
    "extract_from_file",
    "extract_from_asr",
    "extract_from_ocr",
]
