#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
爆款脚本生成器
生成具有爆款潜力的视频脚本
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import random


@dataclass
class ViralTemplate:
    """爆款脚本模板"""
    name: str
    category: str
    structure: List[str]  # 脚本结构
    hook_templates: List[str]  # 开头模板
    keywords: List[str]  # 关键词


class ViralScriptGenerator:
    """
    爆款脚本生成器
    
    基于爆款数据分析生成高潜力脚本
    """
    
    # 爆款模板库
    TEMPLATES = {
        # 知识类
        "知识科普": ViralTemplate(
            name="知识科普",
            category="知识",
            structure=[
                "开头悬念引入",
                "核心知识点1",
                "核心知识点2", 
                "核心知识点3",
                "总结+引导",
            ],
            hook_templates=[
                "90%的人都不知道的{topic}...",
                "原来{topic}竟然是这样...",
                "今天教你{topic}...",
                "关于{topic}，你必须知道...",
            ],
            keywords=["干货", "知识", "技巧", "方法", "注意"],
        ),
        
        # 情感类
        "情感共鸣": ViralTemplate(
            name="情感共鸣",
            category="情感",
            structure=[
                "痛点场景引入",
                "情感转折",
                "共情故事",
                "解决方法",
                "温暖结尾",
            ],
            hook_templates=[
                "你是否也...",
                "你是否经历过...",
                "太真实了...",
                "破防了...",
            ],
            keywords=["真实", "扎心", "感动", "温暖", "治愈"],
        ),
        
        # 剧情类
        "剧情反转": ViralTemplate(
            name="剧情反转",
            category="娱乐",
            structure=[
                "日常开场",
                "意外事件",
                "反转发展",
                "高潮结局",
                "互动引导",
            ],
            hook_templates=[
                "本来以为...",
                "没想到...",
                "最后竟然...",
                "结果...",
            ],
            keywords=["反转", "意外", "没想到", "真相", "搞笑"],
        ),
        
        # 教程类
        "技能教程": ViralTemplate(
            name="技能教程",
            category="知识",
            structure=[
                "效果展示",
                "痛点引入",
                "步骤1",
                "步骤2",
                "步骤3",
                "避坑提醒",
            ],
            hook_templates=[
                "3分钟学会{topic}...",
                "简单又实用的{topic}技巧...",
                "学会这3招{topic}...",
                "原来{topic}这么简单...",
            ],
            keywords=["教程", "技巧", "步骤", "简单", "实用"],
        ),
        
        # 励志类
        "励志成长": ViralTemplate(
            name="励志成长",
            category="情感",
            structure=[
                "低谷开场",
                "转折点",
                "努力过程",
                "成功逆袭",
                "金句总结",
            ],
            hook_templates=[
                "曾经的我...",
                "差点放弃...",
                "直到...",
                "终于...",
            ],
            keywords=["努力", "坚持", "逆袭", "加油", "梦想"],
        ),
        
        # 热点类
        "热点解读": ViralTemplate(
            name="热点解读",
            category="热点",
            structure=[
                "热点引入",
                "事件回顾",
                "深度分析",
                "观点输出",
                "互动话题",
            ],
            hook_templates=[
                "热搜第一...",
                "刚刚发生的...",
                "大家都在讨论...",
                "关于{topic}...",
            ],
            keywords=["热点", "事件", "分析", "观点", "看法"],
        ),
    }
    
    # 热门话题
    HOT_TOPICS = {
        "知识": ["AI", "搞钱", "认知", "思维", "效率", "副业", "职场", "人际关系"],
        "情感": ["爱情", "友情", "亲情", "成长", "孤独", "压力", "焦虑", "自我"],
        "娱乐": ["搞笑", "剧情", "明星", "八卦", "游戏", "动漫", "电影", "音乐"],
        "热点": ["社会热点", "国际局势", "科技新闻", "商业动态", "娱乐八卦"],
    }
    
    def __init__(self):
        self._template = None
        self._topic = ""
    
    def generate(
        self,
        template_type: str,
        topic: str,
        duration: int = 60,
        style: str = "auto",
    ) -> str:
        """
        生成爆款脚本
        
        Args:
            template_type: 模板类型 (知识科普/情感共鸣/剧情反转/...)
            topic: 主题
            duration: 时长(秒)
            style: 风格 (auto/正式/轻松/煽情)
            
        Returns:
            生成的脚本
        """
        # 获取模板
        template = self.TEMPLATES.get(template_type)
        if not template:
            template = random.choice(list(self.TEMPLATES.values()))
        
        self._template = template
        self._topic = topic
        
        # 生成开头
        hook = self._generate_hook(topic)
        
        # 生成主体
        body = self._generate_body(topic, duration)
        
        # 组合
        script = hook + "\n\n" + body
        
        # 风格优化
        if style == "轻松":
            script = self._make_casual(script)
        elif style == "煽情":
            script = self._make_emotional(script)
        
        return script
    
    def _generate_hook(self, topic: str) -> str:
        """生成开头 (黄金3秒)"""
        template = self._template
        
        # 选择开头模板
        hook_template = random.choice(template.hook_templates)
        
        # 填充话题
        hook = hook_template.format(topic=topic)
        
        # 添加悬念或情绪词
        enhancements = [
            "！", "！", "！",
            "，你绝对想不到...",
            "，我直接震惊...",
            "，但愿你永远不要知道...",
        ]
        
        if random.random() > 0.5:
            hook += random.choice(enhancements)
        
        return hook
    
    def _generate_body(self, topic: str, duration: int) -> str:
        """生成主体内容"""
        lines = []
        template = self._template
        
        # 根据结构生成内容
        for i, section in enumerate(template.structure[1:], 1):  # 跳过开头
            if "核心知识点" in section:
                lines.append(f"{i}. 关于{topic}，最重要的点是...")
            elif "步骤" in section:
                lines.append(f"{i}. {self._generate_step(topic)}")
            elif "情感转折" in section:
                lines.append(f"{i}. {self._generate_emotion_turn()}")
            elif "避坑" in section:
                lines.append(f"{i}. {self._generate_warning()}")
            elif "互动引导" in section or "引导" in section:
                lines.append(f"{i}. {self._generate_cta()}")
            elif "总结" in section:
                lines.append(f"{i}. {self._generate_summary(topic)}")
            else:
                lines.append(f"{i}. {self._generate_content(topic, section)}")
        
        return "\n".join(lines)
    
    def _generate_step(self, topic: str) -> str:
        """生成步骤"""
        steps = [
            f"首先，打开{topic}的正确方式...",
            f"然后，注意这个关键点...",
            f"最后，这样做效果最好...",
        ]
        return random.choice(steps)
    
    def _generate_emotion_turn(self) -> str:
        """生成情感转折"""
        turns = [
            "但我突然意识到...",
            "没想到结果竟然...",
            "这一刻我破防了...",
            "终于明白...",
        ]
        return random.choice(turns)
    
    def _generate_warning(self) -> str:
        """生成避坑提醒"""
        warnings = [
            "千万别踩这个坑...",
            "大多数人都会忽略...",
            "记住这3点...",
            "一定要避免...",
        ]
        return random.choice(warnings)
    
    def _generate_cta(self) -> str:
        """生成互动引导"""
        ctas = [
            "你遇到过吗？在评论区告诉我",
            "觉得有用的点赞",
            "转发给需要的人",
            "关注我，下期更精彩",
            "你们遇到过类似的情况吗？",
        ]
        return random.choice(ctas)
    
    def _generate_summary(self, topic: str) -> str:
        """生成总结"""
        summaries = [
            f"关于{topic}，你学会了吗？",
            f"希望这个{topic}技巧对你有帮助",
            f"记住{topic}的关键是...",
        ]
        return random.choice(summaries)
    
    def _generate_content(self, topic: str, section: str) -> str:
        """生成通用内容"""
        keywords = self._template.keywords
        keyword = random.choice(keywords) if keywords else ""
        
        return f"{keyword}方面，{topic}的核心是..."
    
    def _make_casual(self, script: str) -> str:
        """改为轻松风格"""
        casual_words = ["呀", "啊", "吧", "呢", "哦", "嗯"]
        
        for word in casual_words:
            if random.random() > 0.7:
                # 在句子中间插入
                pass
        
        return script
    
    def _make_emotional(self, script: str) -> str:
        """改为煽情风格"""
        emotional_words = ["真的", "太", "终于", "感动", "泪目"]
        
        for word in emotional_words:
            if random.random() > 0.5:
                pass
        
        return script
    
    def suggest_topics(self, category: str = None) -> List[str]:
        """推荐热门话题"""
        if category and category in self.HOT_TOPICS:
            return self.HOT_TOPICS[category]
        
        # 返回所有热门话题
        all_topics = []
        for topics in self.HOT_TOPICS.values():
            all_topics.extend(topics)
        
        return random.sample(all_topics, min(5, len(all_topics)))
    
    def get_template_list(self) -> List[str]:
        """获取可用模板列表"""
        return list(self.TEMPLATES.keys())


# 全局实例
_viral_generator = ViralScriptGenerator()


def generate_viral_script(
    template: str,
    topic: str,
    duration: int = 60,
) -> str:
    """生成爆款脚本"""
    return _viral_generator.generate(template, topic, duration)


def suggest_viral_topics(category: str = None) -> List[str]:
    """推荐热门话题"""
    return _viral_generator.suggest_topics(category)


__all__ = [
    "ViralTemplate",
    "ViralScriptGenerator",
    "generate_viral_script",
    "suggest_viral_topics",
]
