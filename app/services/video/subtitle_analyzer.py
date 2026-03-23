#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字幕分析器
提取原视频字幕，分析内容，用于生成解说
"""

from typing import List, Dict, Optional, Tuple
import re


class SubtitleAnalyzer:
    """
    字幕分析器
    
    功能：
    1. 提取原视频字幕
    2. 分析字幕内容
    3. 生成解说要点
    4. 音画同步对齐
    """
    
    def __init__(self):
        pass
    
    def extract_subtitles(self, video_path: str) -> List[Dict]:
        """
        提取视频字幕
        
        Returns:
            [{"start": 0.0, "end": 5.0, "text": "对话内容"}, ...]
        """
        # 调用字幕提取器
        from .subtitle_extractor import extract_subtitles
        return extract_subtitles(video_path=video_path, source="auto")
    
    def analyze_subtitles(self, subtitles: List[Dict]) -> Dict:
        """
        分析字幕内容
        
        用于生成解说：
        - 提取关键信息
        - 理解对话上下文
        - 识别情感变化
        """
        if not subtitles:
            return {
                "topics": [],
                "emotions": [],
                "keywords": [],
                "summary": "",
            }
        
        # 合并所有文本
        all_text = " ".join([s["text"] for s in subtitles])
        
        # 提取关键词
        keywords = self._extract_keywords(all_text)
        
        # 分析情感
        emotions = self._analyze_emotion(all_text)
        
        # 生成摘要
        summary = self._generate_summary(subtitles)
        
        # 提取主题
        topics = self._extract_topics(all_text)
        
        return {
            "keywords": keywords,
            "emotions": emotions,
            "summary": summary,
            "topics": topics,
            "subtitle_count": len(subtitles),
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单实现：提取高频词
        # 实际项目中使用 NLP
        
        words = text.split()
        word_count = {}
        
        for word in words:
            if len(word) > 2:
                word_count[word] = word_count.get(word, 0) + 1
        
        # 返回 top 10
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [w[0] for w in sorted_words[:10]]
    
    def _analyze_emotion(self, text: str) -> List[str]:
        """分析情感"""
        emotions = []
        
        emotion_keywords = {
            "happy": ["开心", "高兴", "快乐", "幸福", "哈哈"],
            "sad": ["难过", "伤心", "悲伤", "哭"],
            "angry": ["生气", "愤怒", "讨厌", "气"],
            "surprise": ["惊讶", "震惊", "意外", "没想到"],
        }
        
        for emotion, keywords in emotion_keywords.items():
            if any(kw in text for kw in keywords):
                emotions.append(emotion)
        
        return emotions if emotions else ["neutral"]
    
    def _generate_summary(self, subtitles: List[Dict]) -> str:
        """生成摘要"""
        if not subtitles:
            return ""
        
        # 取首尾字幕
        first = subtitles[0]["text"][:50] if subtitles else ""
        last = subtitles[-1]["text"][-50:] if subtitles else ""
        
        return f"{first}...{last}"
    
    def _extract_topics(self, text: str) -> List[str]:
        """提取主题"""
        # 简单实现
        topics = []
        
        topic_keywords = {
            "生活": ["生活", "日常", "今天"],
            "工作": ["工作", "上班", "公司"],
            "学习": ["学习", "学校", "考试"],
            "情感": ["喜欢", "爱", "感情"],
            "科技": ["手机", "电脑", "AI", "技术"],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in text for kw in keywords):
                topics.append(topic)
        
        return topics
    
    def sync_narration_to_video(
        self,
        subtitles: List[Dict],
        narration: str,
    ) -> List[Dict]:
        """
        音画同步
        
        将解说词与原视频画面/字幕时间对齐
        
        Args:
            subtitles: 原字幕 [{"start": 0, "end": 5, "text": "..."}, ...]
            narration: 解说词
            
        Returns:
            对齐后的解说 [{"start": 0, "end": 5, "text": "解说内容"}, ...]
        """
        if not subtitles:
            # 没有原字幕，按平均分配
            duration = 60  # 假设1分钟
            words = narration.split()
            word_count = len(words)
            
            if word_count == 0:
                return []
            
            avg_duration = duration / word_count
            result = []
            current_time = 0
            
            for word in words:
                result.append({
                    "start": current_time,
                    "end": current_time + avg_duration,
                    "text": word,
                })
                current_time += avg_duration
            
            return result
        
        # 有原字幕，与原字幕时间对齐
        narration_parts = narration.split("\n")
        result = []
        
        # 将解说词分配给各字幕段
        for i, subtitle in enumerate(subtitles):
            if i < len(narration_parts):
                text = narration_parts[i]
            else:
                text = ""
            
            result.append({
                "start": subtitle["start"],
                "end": subtitle["end"],
                "text": text,
                "original_subtitle": subtitle["text"],  # 保留原字幕参考
            })
        
        return result
    
    def generate_narration_points(self, subtitles: List[Dict]) -> List[str]:
        """
        基于原字幕生成解说要点
        
        每段字幕生成对应的解说
        """
        points = []
        
        for sub in subtitles:
            text = sub["text"]
            
            # 基于原字幕内容生成解说要点
            # 实际项目中使用 AI 分析
            
            if text:
                # 简化：复制原字幕作为参考
                points.append(f"关于这段内容：{text[:20]}...")
            else:
                points.append("")
        
        return points


# 全局实例
_subtitle_analyzer = SubtitleAnalyzer()


def extract_video_subtitles(video_path: str) -> List[Dict]:
    """提取视频字幕"""
    return _subtitle_analyzer.extract_subtitles(video_path)


def analyze_subtitle_content(subtitles: List[Dict]) -> Dict:
    """分析字幕内容"""
    return _subtitle_analyzer.analyze_subtitles(subtitles)


def sync_narration(subtitles: List[Dict], narration: str) -> List[Dict]:
    """音画同步"""
    return _subtitle_analyzer.sync_narration_to_video(subtitles, narration)


__all__ = [
    "SubtitleAnalyzer",
    "extract_video_subtitles",
    "analyze_subtitle_content",
    "sync_narration",
]
