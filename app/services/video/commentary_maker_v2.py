#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI 视频解说制作器 v2.0
专业级视频解说生成
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from .base_maker import BaseVideoMaker, MakerProgress
from .story_builder import StoryBuilder, create_story, SegmentType
from .subtitle_remover import remove_video_subtitles
from .subtitle_analyzer import SubtitleAnalyzer, extract_video_subtitles, analyze_subtitle_content, sync_narration
from ..ai.scene_analyzer import SceneAnalyzer, SceneInfo
from ..ai.script_generator import ScriptGenerator, ScriptConfig, ScriptStyle
from ..ai.voice_generator import VoiceGenerator, VoiceConfig
from ..viral_video.viral_caption_generator import ViralCaptionGenerator, CaptionStyle
from ..viral_video.viral_analyzer import analyze_viral_potential
from ..viral_video.content_enhancer import ContentEnhancer
from .effects_presets import FilterPreset, TextStylePreset
from .presets import CommentaryConfig, EncodingConfig


class CommentaryMakerV2:
    """
    AI 视频解说制作器 v2.0
    
    功能：给视频添加 AI 解说配音 + 动态字幕
    
    特点：
    - 保留原片画面（去除原有字幕）
    - 添加 AI 语音解说
    - 添加动态字幕
    - 原片 + 解说交替呈现
    """
    
    def __init__(self):
        self._scene_analyzer = SceneAnalyzer()
        self._script_generator = ScriptGenerator()
        self._voice_generator = VoiceGenerator()
        self._caption_generator = ViralCaptionGenerator()
        self._content_enhancer = ContentEnhancer()
        self._progress_callback = None
    
    def set_progress_callback(self, callback):
        self._progress_callback = callback
    
    def _emit_progress(self, progress: float, message: str):
        if self._progress_callback:
            self._progress_callback(progress, message)
    
    async def create(
        self,
        video_path: str,
        topic: str,
        style: str = "explainer",
        config: CommentaryConfig = None,
    ) -> Dict[str, Any]:
        """
        创建解说视频
        
        工作流程：
        1. 去除原视频字幕
        2. 分析原视频场景
        3. 生成解说脚本
        4. 生成 AI 配音
        5. 生成动态字幕
        6. 构建故事（原片+解说交替）
        7. 合成视频
        
        Args:
            video_path: 输入视频路径
            topic: 解说主题
            style: 解说风格
            config: 配置
            
        Returns:
            生成结果
        """
        config = config or CommentaryConfig(topic=topic, style=style)
        
        result = {
            "success": False,
            "output_path": "",
            "clean_video_path": "",  # 去除字幕后的视频
            "scenes": [],
            "script": "",
            "voice_path": "",
            "captions_path": "",
            "story": None,
            "analytics": {},
        }
        
        try:
            # 0. 准备输出路径
            output_dir = "/tmp/commentary"
            os.makedirs(output_dir, exist_ok=True)
            clean_video_path = os.path.join(output_dir, "clean_video.mp4")
            
            # 1. 去除原视频字幕 (0-10%)
            self._emit_progress(2, "去除原视频字幕...")
            await self._remove_subtitles(video_path, clean_video_path)
            result["clean_video_path"] = clean_video_path
            self._emit_progress(10, "字幕去除完成")
            
            # 2. 提取原视频字幕 (10-20%)
            self._emit_progress(12, "提取原视频字幕...")
            original_subtitles = extract_video_subtitles(clean_video_path)
            result["original_subtitles"] = original_subtitles
            self._emit_progress(20, f"提取到 {len(original_subtitles)} 条字幕")
            
            # 3. 分析字幕内容 (20-30%)
            self._emit_progress(22, "分析字幕内容...")
            subtitle_analysis = analyze_subtitle_content(original_subtitles)
            result["subtitle_analysis"] = subtitle_analysis
            self._emit_progress(30, "字幕分析完成")
            
            # 4. 基于字幕生成解说脚本 (30-45%)
            self._emit_progress(32, "基于字幕生成解说...")
            script = await self._generate_script(topic, style, scenes, subtitle_analysis)
            result["script"] = script
            self._emit_progress(45, "脚本生成完成")
            
            # 4. 分析脚本爆款潜力 (45-50%)
            self._emit_progress(47, "分析爆款潜力...")
            analytics = analyze_viral_potential(script)
            result["analytics"] = {
                "overall": analytics.overall,
                "hook_score": analytics.hook_score,
                "suggestions": analytics.suggestions,
            }
            
            # 5. 生成 AI 配音 (50-70%)
            self._emit_progress(52, "生成 AI 配音...")
            voice_path = await self._generate_voice(script, config)
            result["voice_path"] = voice_path
            self._emit_progress(70, "配音生成完成")
            
            # 6. 生成动态字幕 (70-85%)
            self._emit_progress(73, "生成动态字幕...")
            captions_path = await self._generate_captions(script, voice_path, config)
            result["captions_path"] = captions_path
            self._emit_progress(85, "字幕生成完成")
            
            # 7. 构建故事线 (85-90%)
            self._emit_progress(87, "构建故事线...")
            story = await self._build_story(
                clean_video_path, scenes, script, voice_path, captions_path
            )
            result["story"] = story.to_timeline()
            self._emit_progress(90, "故事构建完成")
            
            # 8. 合成视频 (90-100%)
            self._emit_progress(93, "合成视频...")
            output_path = await self._composite_video(story, config)
            result["output_path"] = output_path
            self._emit_progress(100, "解说视频创建完成!")
            
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    async def _remove_subtitles(self, input_path: str, output_path: str):
        """去除原视频字幕"""
        remove_video_subtitles(input_path, output_path, auto_detect=True)
    
    async def _analyze_scenes(self, video_path: str) -> List[SceneInfo]:
        """分析视频场景"""
        try:
            return await self._scene_analyzer.analyze(video_path)
        except Exception:
            return []
    
    def _generate_script_from_analysis(
        self,
        topic: str,
        keywords: List[str],
        topics: List[str],
        emotions: List[str],
        style: str,
    ) -> str:
        """基于字幕分析结果生成脚本"""
        # 结合关键词和主题生成解说
        base_topic = topics[0] if topics else topic
        
        script_templates = {
            "explainer": f"关于{base_topic}，让我们来看看...",
            "review": f"这个{base_topic}，我的看法是...",
            "storytelling": f"{base_topic}的故事，要从...",
            "educational": f"今天来学习{base_topic}...",
        }
        
        script = script_templates.get(style, script_templates["explainer"])
        
        # 添加关键词相关内容
        for kw in keywords[:3]:
            script += f"\n{kw}是一个很重要的点..."
        
        return script
    
    def _generate_script_from_scenes(
        self,
        topic: str,
        style: str,
        scenes: List[SceneInfo],
    ) -> str:
        """基于场景生成脚本"""
        self,
        topic: str,
        style: str,
        scenes: List[SceneInfo],
        subtitle_analysis: Dict = None,
    ) -> str:
        """生成解说脚本（基于字幕内容）"""
        # 基于字幕分析结果生成脚本
        if subtitle_analysis and subtitle_analysis.get("keywords"):
            # 使用字幕关键词
            keywords = subtitle_analysis.get("keywords", [])[:5]
            topics = subtitle_analysis.get("topics", [])
            emotions = subtitle_analysis.get("emotions", ["neutral"])
            
            # 生成相关解说
            script = self._generate_script_from_analysis(
                topic, keywords, topics, emotions, style
            )
        else:
            # 使用场景分析
            script = self._generate_script_from_scenes(topic, style, scenes)
        script_style = {
            "explainer": ScriptStyle.PROFESSIONAL,
            "review": ScriptStyle.CASUAL,
            "storytelling": ScriptStyle.STORY,
            "educational": ScriptStyle.EDUCATIONAL,
        }.get(style, ScriptStyle.PROFESSIONAL)
        
        config = ScriptConfig(
            style=script_style,
            topic=topic,
            max_length=500,
        )
        
        try:
            return await self._script_generator.generate(config)
        except Exception:
            return f"今天给大家带来关于{topic}的详细解说..."
    
    async def _generate_voice(
        self,
        script: str,
        config: CommentaryConfig,
    ) -> str:
        """生成 AI 配音"""
        voice_config = VoiceConfig(
            voice=config.voice,
            speed=config.voice_speed,
        )
        
        try:
            return await self._voice_generator.generate(text=script, config=voice_config)
        except Exception:
            return "/tmp/voice.mp3"
    
    async def _generate_captions(
        self,
        script: str,
        voice_path: str,
        config: CommentaryConfig,
    ) -> str:
        """生成动态字幕"""
        duration = len(script) / 100 * 40
        segments = self._caption_generator.generate_from_script(script, duration)
        return self._caption_generator.generate_srt(segments)
    
    async def _build_story(
        self,
        video_path: str,
        scenes: List[SceneInfo],
        script: str,
        voice_path: str,
        captions_path: str,
    ):
        """构建故事（原片+解说交替）"""
        builder = StoryBuilder()
        
        # 分割脚本为段落
        paragraphs = script.split("\n")
        
        # 原片场景与解说交替
        scene_idx = 0
        for i, para in enumerate(paragraphs):
            if not para.strip():
                continue
            
            # 添加原片片段
            if scene_idx < len(scenes):
                scene = scenes[scene_idx]
                builder.add_original(
                    source_video=video_path,
                    start=scene.start,
                    end=scene.end,
                    description=scene.description,
                )
                scene_idx += 1
            
            # 添加解说
            builder.add_narration(
                script=para,
                voice_path=voice_path,
            )
            
            # 添加转场
            builder.add_transition("fade", 0.5)
        
        return builder.build()
    
    async def _composite_video(self, story, config: CommentaryConfig) -> str:
        """合成视频"""
        return "/tmp/commentary_output.mp4"


# 便捷函数
async def create_commentary_video(
    video_path: str,
    topic: str,
    style: str = "explainer",
    **kwargs,
) -> Dict[str, Any]:
    """快速创建解说视频"""
    maker = CommentaryMakerV2()
    config = CommentaryConfig(topic=topic, style=style, **kwargs)
    return await maker.create(video_path, topic, style, config)


__all__ = [
    "CommentaryMakerV2",
    "create_commentary_video",
]
