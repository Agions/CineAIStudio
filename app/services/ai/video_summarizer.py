#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
"""
AI 视频摘要生成器 (Video Summarizer)

基于视频画面分析生成智能摘要，支持多种摘要类型和风格。

功能:
- 生成视频内容摘要
- 提取关键信息点
- 生成时间戳标记
- 支持多种摘要风格（简洁、详细、故事化）

使用示例:
    from app.services.ai import VideoSummarizer, SummaryStyle

    summarizer = VideoSummarizer()
    summary = summarizer.summarize("video.mp4", style=SummaryStyle.DETAILED)

    print(f"标题: {summary.title}")
    print(f"摘要: {summary.content}")
    for point in summary.key_points:
        print(f"  [{point.timestamp}] {point.description}")
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from .video_content_analyzer import VideoContentAnalyzer, VideoAnalysisResult
from .llm_manager import LLMManager, load_llm_config, ProviderType
from .base_llm_provider import LLMRequest


logger = logging.getLogger(__name__)
class SummaryStyle(Enum):
    """摘要风格"""
    CONCISE = "concise"          # 简洁（100字以内）
    DETAILED = "detailed"        # 详细（300-500字）
    STORY = "story"              # 故事化
    BULLET = "bullet"            # 要点列表
    SOCIAL = "social"            # 社交媒体风格


class SummaryLength(Enum):
    """摘要长度"""
    SHORT = "short"              # 短（50-100字）
    MEDIUM = "medium"            # 中（200-300字）
    LONG = "long"                # 长（400-600字）


@dataclass
class KeyPoint:
    """关键信息点"""
    timestamp: float             # 时间戳（秒）
    description: str             # 描述
    importance: int = 5          # 重要程度 (1-10)


@dataclass
class VideoSummary:
    """视频摘要结果"""
    title: str                   # 标题
    content: str                 # 摘要内容
    style: SummaryStyle          # 风格
    key_points: List[KeyPoint] = field(default_factory=list)  # 关键信息点
    tags: List[str] = field(default_factory=list)  # 标签
    sentiment: str = "neutral"   # 情感倾向
    duration: float = 0.0        # 视频时长
    word_count: int = 0          # 字数


@dataclass
class SummarizerConfig:
    """摘要生成配置"""
    style: SummaryStyle = SummaryStyle.DETAILED
    length: SummaryLength = SummaryLength.MEDIUM
    include_timestamps: bool = True  # 是否包含时间戳
    include_tags: bool = True        # 是否生成标签
    language: str = "zh-CN"          # 语言
    provider: Optional[str] = None   # 指定 LLM 提供商


class VideoSummarizer:
    """
    AI 视频摘要生成器

    使用 LLM 基于视频画面分析生成智能摘要

    使用示例:
        summarizer = VideoSummarizer()

        # 生成详细摘要
        summary = summarizer.summarize("video.mp4")

        # 生成社交媒体风格摘要
        social_summary = summarizer.summarize(
            "video.mp4",
            config=SummarizerConfig(style=SummaryStyle.SOCIAL)
        )
    """

    # 风格对应的系统提示词
    STYLE_PROMPTS = {
        SummaryStyle.CONCISE: """你是一位专业的视频摘要撰写者。请生成简洁的视频摘要。
要求：
- 字数控制在100字以内
- 突出核心内容
- 语言精炼有力
- 适合快速浏览""",

        SummaryStyle.DETAILED: """你是一位专业的视频摘要撰写者。请生成详细的视频摘要。
要求：
- 字数300-500字
- 涵盖主要内容
- 逻辑清晰
- 适合深入了解视频内容""",

        SummaryStyle.STORY: """你是一位擅长讲故事的视频摘要撰写者。请以故事化的方式描述视频内容。
要求：
- 有起承转合
- 引人入胜
- 情感丰富
- 让读者有身临其境的感觉""",

        SummaryStyle.BULLET: """你是一位专业的视频摘要撰写者。请以要点列表的形式总结视频内容。
要求：
- 使用 bullet points
- 每个要点简洁明了
- 按重要性排序
- 便于快速获取信息""",

        SummaryStyle.SOCIAL: """你是一位社交媒体文案高手。请生成适合社交媒体分享的视频摘要。
要求：
- 开头抓人眼球
- 使用 emoji 增加趣味性
- 适合抖音、小红书、微博等平台
- 鼓励互动（点赞、评论、转发）""",
    }

    def __init__(
        self,
        use_llm_manager: bool = True,
        llm_config: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None,
    ):
        """
        初始化摘要生成器

        Args:
            use_llm_manager: 是否使用 LLMManager
            llm_config: LLM 配置
            api_key: OpenAI API Key（传统方式）
        """
        self.use_llm_manager = use_llm_manager
        self.llm_manager: Optional[LLMManager] = None
        self.video_analyzer = VideoContentAnalyzer()

        if use_llm_manager:
            config = llm_config or load_llm_config()
            self.llm_manager = LLMManager(config)
        elif api_key:
            self.api_key = api_key
        else:
            self.api_key = os.getenv("OPENAI_API_KEY")

    async def summarize(
        self,
        video_path: str,
        config: Optional[SummarizerConfig] = None,
    ) -> VideoSummary:
        """
        生成视频摘要

        Args:
            video_path: 视频路径
            config: 摘要配置

        Returns:
            视频摘要
        """
        config = config or SummarizerConfig()

        # 1. 分析视频内容
        logger.info("正在分析视频内容...")
        analysis = self.video_analyzer.analyze(video_path)

        # 2. 生成摘要
        logger.info("正在生成摘要...")
        if self.use_llm_manager and self.llm_manager:
            summary_data = await self._generate_with_llm_manager(analysis, config)
        else:
            summary_data = self._generate_with_openai(analysis, config)

        # 3. 构建结果
        summary = VideoSummary(
            title=summary_data.get("title", "视频摘要"),
            content=summary_data.get("content", ""),
            style=config.style,
            key_points=summary_data.get("key_points", []),
            tags=summary_data.get("tags", []),
            sentiment=summary_data.get("sentiment", "neutral"),
            duration=analysis.duration,
            word_count=len(summary_data.get("content", "")),
        )

        return summary

    async def _generate_with_llm_manager(
        self,
        analysis: VideoAnalysisResult,
        config: SummarizerConfig,
    ) -> Dict[str, Any]:
        """使用 LLMManager 生成摘要"""
        # 构建提示词
        system_prompt = self.STYLE_PROMPTS.get(
            config.style,
            self.STYLE_PROMPTS[SummaryStyle.DETAILED]
        )

        user_prompt = self._build_summary_prompt(analysis, config)

        # 确定提供商
        provider_type = None
        if config.provider:
            try:
                provider_type = ProviderType(config.provider)
            except ValueError:
                pass

        # 构建请求
        request = LLMRequest(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=2000,
            temperature=0.7,
        )

        # 调用 LLM
        response = await self.llm_manager.generate(request, provider=provider_type)

        # 解析响应
        return self._parse_summary_response(response.content)

    def _generate_with_openai(
        self,
        analysis: VideoAnalysisResult,
        config: SummarizerConfig,
    ) -> Dict[str, Any]:
        """使用 OpenAI 生成摘要"""
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)

            system_prompt = self.STYLE_PROMPTS.get(
                config.style,
                self.STYLE_PROMPTS[SummaryStyle.DETAILED]
            )

            user_prompt = self._build_summary_prompt(analysis, config)

            response = client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=2000,
                temperature=0.7,
            )

            content = response.choices[0].message.content
            return self._parse_summary_response(content)

        except Exception as e:
            logger.error(f"OpenAI 生成失败: {e}")
            return self._generate_fallback_summary(analysis)

    def _build_summary_prompt(
        self,
        analysis: VideoAnalysisResult,
        config: SummarizerConfig,
    ) -> str:
        """构建摘要生成提示词"""
        # 收集关键帧描述
        frame_descriptions = []
        for kf in analysis.keyframes[:10]:  # 最多取10帧
            if kf.description:
                frame_descriptions.append(f"[{kf.timestamp:.1f}s] {kf.description}")

        # 长度要求
        length_map = {
            SummaryLength.SHORT: "50-100字",
            SummaryLength.MEDIUM: "200-300字",
            SummaryLength.LONG: "400-600字",
        }
        length_req = length_map.get(config.length, "200-300字")

        prompt_parts = [
            "请为以下视频生成摘要：",
            "",
            "视频信息：",
            f"- 时长: {analysis.duration:.1f}秒",
            f"- 分辨率: {analysis.resolution[0]}x{analysis.resolution[1]}",
            f"- 主要主题: {', '.join(analysis.main_topics) if analysis.main_topics else '未识别'}",
            f"- 情感基调: {analysis.main_emotion.value}",
            "",
            "画面描述：",
        ]

        for desc in frame_descriptions:
            prompt_parts.append(f"  {desc}")

        prompt_parts.extend([
            "",
            "要求：",
            f"- 字数要求: {length_req}",
        ])

        if config.include_timestamps:
            prompt_parts.append("- 包含3-5个关键时间点及其描述")

        if config.include_tags:
            prompt_parts.append("- 生成5-8个相关标签")

        prompt_parts.extend([
            "",
            "请按以下JSON格式输出：",
            "```json",
            "{",
            '  "title": "视频标题",',
            '  "content": "摘要内容",',
            '  "key_points": [',
            '    {"timestamp": 10.5, "description": "关键时刻描述", "importance": 8}',
            '  ],',
            '  "tags": ["标签1", "标签2"],',
            '  "sentiment": "positive/neutral/negative"',
            "}",
            "```",
        ])

        return "\n".join(prompt_parts)

    def _parse_summary_response(self, content: str) -> Dict[str, Any]:
        """解析 LLM 响应"""
        import json
        import re

        # 尝试提取 JSON
        try:
            # 查找 JSON 代码块
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析
                json_str = content

            data = json.loads(json_str)

            # 转换关键信息点
            key_points = []
            for point in data.get("key_points", []):
                key_points.append(KeyPoint(
                    timestamp=point.get("timestamp", 0),
                    description=point.get("description", ""),
                    importance=point.get("importance", 5),
                ))

            return {
                "title": data.get("title", "视频摘要"),
                "content": data.get("content", ""),
                "key_points": key_points,
                "tags": data.get("tags", []),
                "sentiment": data.get("sentiment", "neutral"),
            }

        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            # 返回简化版本
            return {
                "title": "视频摘要",
                "content": content[:500],
                "key_points": [],
                "tags": [],
                "sentiment": "neutral",
            }

    def _generate_fallback_summary(
        self,
        analysis: VideoAnalysisResult,
    ) -> Dict[str, Any]:
        """生成备用摘要（当 LLM 失败时）"""
        # 基于分析结果生成简单摘要
        descriptions = [kf.description for kf in analysis.keyframes if kf.description]
        content = " ".join(descriptions[:5]) if descriptions else "视频内容分析完成"

        return {
            "title": f"{analysis.duration:.0f}秒视频摘要",
            "content": content,
            "key_points": [
                KeyPoint(
                    timestamp=kf.timestamp,
                    description=kf.description[:50] if kf.description else f"场景 {i+1}",
                    importance=5,
                )
                for i, kf in enumerate(analysis.keyframes[:5])
            ],
            "tags": analysis.main_topics,
            "sentiment": analysis.main_emotion.value,
        }

    def generate_title(
        self,
        video_path: str,
        style: str = "catchy",  # catchy, descriptive, seo
    ) -> str:
        """
        生成视频标题

        Args:
            video_path: 视频路径
            style: 标题风格 (catchy=抓眼球, descriptive=描述性, seo=SEO优化)

        Returns:
            标题
        """
        # 简化实现：先分析再生成
        analysis = self.video_analyzer.analyze(video_path)

        # 基于分析结果生成标题
        if style == "catchy":
            return f"震惊！{analysis.main_topics[0] if analysis.main_topics else '这个视频'}竟然..."
        elif style == "descriptive":
            return f"{analysis.duration:.0f}秒带你了解{', '.join(analysis.main_topics[:2])}"
        else:
            return f"{', '.join(analysis.keywords[:5])} | 视频解析"

    def generate_chapters(
        self,
        video_path: str,
    ) -> List[Dict[str, Any]]:
        """
        生成视频章节

        Args:
            video_path: 视频路径

        Returns:
            章节列表
        """
        analysis = self.video_analyzer.analyze(video_path)

        chapters = []
        for i, kf in enumerate(analysis.keyframes):
            if kf.description:
                chapters.append({
                    "timestamp": kf.timestamp,
                    "title": f"章节 {i+1}",
                    "description": kf.description[:50],
                })

        return chapters


# =========== 便捷函数 ===========

async def summarize_video(
    video_path: str,
    style: SummaryStyle = SummaryStyle.DETAILED,
    use_llm_manager: bool = True,
) -> VideoSummary:
    """
    快速生成视频摘要

    Args:
        video_path: 视频路径
        style: 摘要风格
        use_llm_manager: 是否使用 LLMManager

    Returns:
        视频摘要
    """
    summarizer = VideoSummarizer(use_llm_manager=use_llm_manager)
    config = SummarizerConfig(style=style)
    return await summarizer.summarize(video_path, config)


def demo_summarize():
    """演示视频摘要生成"""
    print("=" * 60)
    print("🎬 AI 视频摘要生成器")
    print("=" * 60)

    # 检查测试视频
    test_videos = list(Path("test_assets").glob("*.mp4"))

    if not test_videos:
        print("\n⚠️  没有找到测试视频")
        print("请将 .mp4 文件放入 test_assets 目录")
        return

    video_path = str(test_videos[0])
    print(f"\n分析视频: {video_path}")

    import asyncio

    async def run():
        summarizer = VideoSummarizer(use_llm_manager=True)

        # 生成不同风格的摘要
        for style in [SummaryStyle.CONCISE, SummaryStyle.DETAILED]:
            print(f"\n{'='*60}")
            print(f"风格: {style.value}")
            print("=" * 60)

            config = SummarizerConfig(style=style)
            summary = await summarizer.summarize(video_path, config)

            print(f"\n📌 标题: {summary.title}")
            print(f"📝 摘要: {summary.content[:200]}...")
            print(f"🏷️  标签: {', '.join(summary.tags[:5])}")
            print(f"💭 情感: {summary.sentiment}")

            if summary.key_points:
                print("\n⏱️  关键时间点:")
                for point in summary.key_points[:3]:
                    print(f"   [{point.timestamp:.1f}s] {point.description[:50]}...")

    asyncio.run(run())


if __name__ == '__main__':
    demo_summarize()
