#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
爆款视频分析器
分析视频爆款潜力并提供优化建议
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import re


class ViralFactor(Enum):
    """爆款因子"""
    HOOK = "hook"              # 开头吸引力
    EMOTION = "emotion"        # 情绪共鸣
    INFO = "info"              # 信息价值
    ENTERTAINMENT = "entertainment"  # 娱乐性
    SURPRISE = "surprise"      # 惊喜/反转
    RELATABLE = "relatable"    # 代入感
    TIMING = "timing"          # 时机热点
    FORMAT = "format"          # 格式节奏


@dataclass
class ViralScore:
    """爆款评分"""
    overall: float = 0.0        # 综合评分 (0-100)
    hook_score: float = 0.0     # 开头评分
    emotion_score: float = 0.0 # 情绪评分
    info_score: float = 0.0    # 信息评分
    entertainment_score: float = 0.0  # 娱乐评分
    format_score: float = 0.0   # 格式评分
    
    # 建议
    suggestions: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)


@dataclass
class TrendingTopic:
    """热门话题"""
    id: str
    title: str
    category: str
    heat: int  # 热度指数
    hashtags: List[str]


class ViralAnalyzer:
    """
    爆款视频分析器
    
    分析视频各维度，提供爆款优化建议
    """
    
    # 热门话题库 (示例)
    TRENDING_TOPICS = {
        "情感": [
            ("情感共鸣", ["情感", "共鸣", "扎心", "破防"]),
            ("励志成长", ["成长", "逆袭", "努力", "奋斗"]),
            ("职场话题", ["职场", "工作", "老板", "同事"]),
        ],
        "知识": [
            ("科普知识", ["科普", "知识", "涨知识", "干货"]),
            ("技能教程", ["教程", "技巧", "教学", "分享"]),
            ("行业揭秘", ["揭秘", "行业", "内幕", "真相"]),
        ],
        "娱乐": [
            ("搞笑段子", ["搞笑", "段子", "欢乐", "沙雕"]),
            ("剧情反转", ["反转", "意外", "没想到", "真相"]),
            ("明星热点", ["明星", "八卦", "官宣", "塌房"]),
        ],
    }
    
    # 高热度开场白模板
    HOOK_TEMPLATES = [
        r"(竟然|居然|原来|竟然|居然|没想到)",
        r"(千万别|不要|不要啊|注意|小心)",
        r"(99%|90%|80%的人|大部分人)",
        r"(今天|刚才|刚刚|昨天|上周)",
        r"(揭秘|告诉你|教你|分享|推荐)",
        r"(崩溃|哭了|笑死|惊艳|震撼)",
    ]
    
    # 情绪关键词
    EMOTION_KEYWORDS = {
        "感动": ["泪目", "哭了", "感动", "泪崩", "破防"],
        "愤怒": ["气死", "愤怒", "生气", "无语", "吐槽"],
        "搞笑": ["笑死", "哈哈哈", "搞笑", "欢乐", "沙雕"],
        "惊讶": ["震惊", "没想到", "竟然", "惊讶", "意外"],
        "温暖": ["暖心", "感动", "治愈", "温馨", "幸福"],
        "励志": ["加油", "努力", "奋斗", "坚持", "梦想"],
    }
    
    def __init__(self):
        self._initialize_patterns()
    
    def _initialize_patterns(self):
        """初始化正则模式"""
        self._hook_patterns = [
            re.compile(p, re.IGNORECASE) 
            for p in self.HOOK_TEMPLATES
        ]
    
    def analyze_script(self, script: str) -> ViralScore:
        """
        分析脚本爆款潜力
        
        Args:
            script: 视频脚本
            
        Returns:
            ViralScore 爆款评分
        """
        score = ViralScore()
        
        # 1. 开头分析 (hook)
        score.hook_score = self._analyze_hook(script)
        
        # 2. 情绪分析
        score.emotion_score = self._analyze_emotion(script)
        
        # 3. 信息价值
        score.info_score = self._analyze_info_value(script)
        
        # 4. 娱乐性
        score.entertainment_score = self._analyze_entertainment(script)
        
        # 5. 格式分析
        score.format_score = self._analyze_format(script)
        
        # 综合评分
        score.overall = (
            score.hook_score * 0.25 +
            score.emotion_score * 0.20 +
            score.info_score * 0.20 +
            score.entertainment_score * 0.20 +
            score.format_score * 0.15
        )
        
        # 生成建议
        score.suggestions = self._generate_suggestions(score)
        score.strengths = self._identify_strengths(score)
        
        return score
    
    def _analyze_hook(self, script: str) -> float:
        """分析开头吸引力"""
        if not script:
            return 0.0
        
        # 检查是否有过渡词
        hook_count = 0
        for pattern in self._hook_patterns:
            if pattern.search(script[:200]):  # 只检查前200字
                hook_count += 1
        
        # 开头是否直接入题
        first_sentence = script[:50]
        if any(word in first_sentence for word in ["今天", "教你", "告诉", "分享", "揭秘"]):
            hook_count += 1
        
        # 评分
        score = min(hook_count * 20, 100)
        return score
    
    def _analyze_emotion(self, script: str) -> float:
        """分析情绪共鸣"""
        if not script:
            return 0.0
        
        emotion_count = 0
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            if any(kw in script for kw in keywords):
                emotion_count += 1
        
        # 检查感叹号和问号
        emotion_count += script.count("！") + script.count("?") + script.count("？")
        
        return min(emotion_count * 15, 100)
    
    def _analyze_info_value(self, script: str) -> float:
        """分析信息价值"""
        if not script:
            return 0.0
        
        # 知识密度
        info_keywords = [
            "因为", "所以", "但是", "其实", "关键", 
            "重点", "注意", "记住", "一定要", "不要",
            "建议", "方法", "技巧", "步骤", "原因",
        ]
        
        info_count = sum(1 for kw in info_keywords if kw in script)
        
        # 数字列表 (步骤、要点)
        numbers = len(re.findall(r'\d+[、.]|\d+个|\d+种', script))
        
        score = min((info_count * 10 + numbers * 15), 100)
        return score
    
    def _analyze_entertainment(self, script: str) -> float:
        """分析娱乐性"""
        if not script:
            return 0.0
        
        # 悬念词
        suspense_words = ["竟然", "没想到", "最后", "结果", "但是", "没想到"]
        suspense_count = sum(1 for w in suspense_words if w in script)
        
        # 反转
        reversal_words = ["反转", "没想到", "其实", "真相", "但是"]
        reversal_count = sum(1 for w in reversal_words if w in script)
        
        # 口语化
        casual_words = ["啊", "呀", "吧", "呢", "哦", "嗯"]
        casual_count = sum(script.count(w) for w in casual_words)
        
        score = min(suspense_count * 15 + reversal_count * 20 + casual_count * 2, 100)
        return score
    
    def _analyze_format(self, script: str) -> float:
        """分析格式节奏"""
        if not script:
            return 0.0
        
        # 长度适中 (30-120秒最合适)
        char_count = len(script)
        if 500 <= char_count <= 2000:
            length_score = 100
        elif char_count < 500:
            length_score = 50
        else:
            length_score = max(0, 100 - (char_count - 2000) // 100)
        
        # 段落清晰
        paragraphs = script.split("\n")
        paragraph_score = min(len(paragraphs) * 15, 100) if paragraphs else 0
        
        return (length_score + paragraph_score) / 2
    
    def _generate_suggestions(self, score: ViralScore) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        if score.hook_score < 50:
            suggestions.append("💡 开头吸引力不足，建议使用悬念或痛点开头")
        
        if score.emotion_score < 40:
            suggestions.append("💡 增加情绪共鸣，使用感叹词和情感词")
        
        if score.info_score < 40:
            suggestions.append("💡 增加干货信息，使用123要点结构")
        
        if score.entertainment_score < 40:
            suggestions.append("💡 增加悬念和反转，提高娱乐性")
        
        if score.format_score < 60:
            suggestions.append("💡 优化内容长度，保持30-120秒")
        
        return suggestions
    
    def _identify_strengths(self, score: ViralScore) -> List[str]:
        """识别优势"""
        strengths = []
        
        if score.hook_score >= 70:
            strengths.append("✅ 开头吸引力强")
        if score.emotion_score >= 70:
            strengths.append("✅ 情绪共鸣好")
        if score.info_score >= 70:
            strengths.append("✅ 信息价值高")
        if score.entertainment_score >= 70:
            strengths.append("✅ 娱乐性强")
        if score.format_score >= 70:
            strengths.append("✅ 格式节奏好")
        
        return strengths
    
    def optimize_script(
        self, 
        script: str, 
        target_platform: str = "tiktok"
    ) -> str:
        """
        优化脚本为爆款格式
        
        Args:
            script: 原始脚本
            target_platform: 目标平台
            
        Returns:
            优化后的脚本
        """
        lines = script.split("\n")
        optimized = []
        
        # 平台特定优化
        if target_platform == "tiktok":
            max_duration = 60  # 抖音60秒
        elif target_platform == "xiaohongshu":
            max_duration = 120  # 小红书2分钟
        else:
            max_duration = 180
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # 开头优化
            if i == 0:
                line = self._optimize_hook(line)
            
            # 情绪增强
            line = self._enhance_emotion(line)
            
            optimized.append(line)
        
        return "\n".join(optimized)
    
    def _optimize_hook(self, line: str) -> str:
        """优化开头"""
        # 如果没有悬念词，尝试添加
        hook_words = ["竟然", "没想到", "千万别", "教你"]
        if not any(w in line for w in hook_words):
            line = "教你" + line[2:] if len(line) > 2 else line
        
        return line
    
    def _enhance_emotion(self, line: str) -> str:
        """增强情绪"""
        # 添加感叹词
        if line and not line.endswith(("！", "?", "？", "!")):
            if len(line) > 10:
                line += "！"
        
        return line
    
    def get_trending_topics(self, category: str = None) -> List[TrendingTopic]:
        """获取热门话题"""
        topics = []
        
        if category and category in self.TRENDING_TOPICS:
            categories = [category]
        else:
            categories = self.TRENDING_TOPICS.keys()
        
        for cat in categories:
            for idx, (title, tags) in enumerate(self.TRENDING_TOPICS[cat]):
                topics.append(TrendingTopic(
                    id=f"{cat}_{idx}",
                    title=title,
                    category=cat,
                    heat=1000 - idx * 100,
                    hashtags=tags,
                ))
        
        return topics


# 全局实例
_viral_analyzer = ViralAnalyzer()


def analyze_viral_potential(script: str) -> ViralScore:
    """分析脚本爆款潜力"""
    return _viral_analyzer.analyze_script(script)


def optimize_for_viral(script: str, platform: str = "tiktok") -> str:
    """优化脚本为爆款"""
    return _viral_analyzer.optimize_script(script, platform)


def get_trending_topics(category: str = None) -> List[TrendingTopic]:
    """获取热门话题"""
    return _viral_analyzer.get_trending_topics(category)


__all__ = [
    "ViralFactor",
    "ViralScore", 
    "TrendingTopic",
    "ViralAnalyzer",
    "analyze_viral_potential",
    "optimize_for_viral",
    "get_trending_topics",
]
