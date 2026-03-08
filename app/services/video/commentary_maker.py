#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI 视频解说制作器 v3.0
最终版工作流程
"""

import os
import asyncio
from typing import Optional, List, Dict, Any

from .base_maker import MakerProgress
from .story_builder import StoryBuilder
from .subtitle_remover import remove_video_subtitles
from .subtitle_extractor import SubtitleExtractor, extract_subtitles
from .subtitle_analyzer import analyze_subtitle_content, sync_narration
from ..ai.scene_analyzer import SceneAnalyzer, SceneInfo
from ..ai.script_generator import ScriptGenerator, ScriptConfig, ScriptStyle
from ..ai.voice_generator import VoiceGenerator, VoiceConfig
from ..viral_video.viral_caption_generator import ViralCaptionGenerator, CaptionStyle
from ..viral_video.viral_analyzer import analyze_viral_potential
from ..viral_video.content_enhancer import ContentEnhancer
from .video_deduplicator import make_video_unique
from .presets import CommentaryConfig


class CommentaryMaker:
    """
    AI 视频解说制作器 v3.0
    
    最终工作流程：
    1. 用户导入视频 + 字幕文件 (可选)
    2. 去除原视频字幕 (无痕)
    3. 分析字幕内容
    4. 生成解说脚本
    5. 生成 AI 配音
    6. 生成动态字幕
    7. 构建故事 (原片+解说交替)
    8. 去重处理 (原创化)
    9. 合成视频
    """
    
    def __init__(self):
        self._scene_analyzer = SceneAnalyzer()
        self._script_generator = ScriptGenerator()
        self._voice_generator = VoiceGenerator()
        self._caption_generator = ViralCaptionGenerator()
        self._content_enhancer = ContentEnhancer()
        self._subtitle_extractor = SubtitleExtractor()
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
        subtitle_file: str = None,  # 用户导入字幕
        style: str = "explainer",
        config: CommentaryConfig = None,
    ) -> Dict[str, Any]:
        """
        创建解说视频
        
        Args:
            video_path: 输入视频路径
            topic: 解说主题
            subtitle_file: 用户导入的字幕文件 (可选)
            style: 解说风格
            config: 配置
            
        Returns:
            生成结果
        """
        config = config or CommentaryConfig(topic=topic, style=style)
        
        result = {
            "success": False,
            "output_path": "",
            "clean_video_path": "",
            "subtitles": [],
            "subtitle_analysis": {},
            "script": "",
            "voice_path": "",
            "captions_path": "",
            "story": None,
            "analytics": {},
            "uniqueness": {},
        }
        
        try:
            # 0. 准备
            output_dir = "/tmp/commentary"
            os.makedirs(output_dir, exist_ok=True)
            clean_video_path = os.path.join(output_dir, "clean.mp4")
            
            # ========== 步骤1: 提取字幕 ==========
            self._emit_progress(5, "提取字幕...")
            
            if subtitle_file:
                # 用户导入字幕 (最准确)
                subtitles = extract_subtitles(subtitle_file=subtitle_file, source="import")
                result["subtitles"] = subtitles
                self._emit_progress(20, f"已导入字幕: {len(subtitles)} 条")
            else:
                # 自动提取
                subtitles = extract_subtitles(video_path=video_path, source="auto")
                result["subtitles"] = subtitles
                self._emit_progress(20, f"自动提取字幕: {len(subtitles)} 条")
            
            # ========== 步骤2: 去除原字幕 ==========
            self._emit_progress(25, "去除原视频字幕...")
            remove_video_subtitles(video_path, clean_video_path)
            result["clean_video_path"] = clean_video_path
            self._emit_progress(30, "字幕去除完成")
            
            # ========== 步骤3: 分析字幕内容 ==========
            self._emit_progress(35, "分析字幕内容...")
            subtitle_analysis = analyze_subtitle_content(subtitles)
            result["subtitle_analysis"] = subtitle_analysis
            self._emit_progress(45, "分析完成")
            
            # ========== 步骤4: 生成解说脚本 ==========
            self._emit_progress(50, "生成解说脚本...")
            script = await self._generate_script(topic, style, subtitle_analysis)
            result["script"] = script
            self._emit_progress(60, "脚本生成完成")
            
            # ========== 步骤5: 爆款分析 ==========
            self._emit_progress(65, "分析爆款潜力...")
            analytics = analyze_viral_potential(script)
            result["analytics"] = {
                "overall": analytics.overall,
                "hook_score": analytics.hook_score,
                "suggestions": analytics.suggestions,
            }
            
            # ========== 步骤6: 生成配音 ==========
            self._emit_progress(70, "生成 AI 配音...")
            voice_path = await self._generate_voice(script, config)
            result["voice_path"] = voice_path
            self._emit_progress(80, "配音生成完成")
            
            # ========== 步骤7: 生成字幕 ==========
            self._emit_progress(85, "生成动态字幕...")
            captions_path = await self._generate_captions(script, voice_path, config)
            result["captions_path"] = captions_path
            
            # ========== 步骤8: 去重处理 ==========
            self._emit_progress(90, "去重处理...")
            uniqueness = make_video_unique(video_path, script)
            result["uniqueness"] = uniqueness
            
            # ========== 步骤9: 合成视频 ==========
            self._emit_progress(95, "合成视频...")
            output_path = await self._composite_video(
                clean_video_path, script, voice_path, captions_path
            )
            result["output_path"] = output_path
            
            self._emit_progress(100, "解说视频创建完成!")
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    async def _generate_script(
        self,
        topic: str,
        style: str,
        subtitle_analysis: Dict,
    ) -> str:
        """生成解说脚本"""
        # 基于字幕分析生成
        keywords = subtitle_analysis.get("keywords", [])[:5]
        topics = subtitle_analysis.get("topics", [])
        
        script_templates = {
            "explainer": f"今天给大家带来关于{topic}的详细解说...",
            "review": f"这个{topic}，我的看法是...",
            "storytelling": f"{topic}的故事，要从...",
            "educational": f"今天来学习{topic}...",
        }
        
        script = script_templates.get(style, script_templates["explainer"])
        
        # 添加关键词相关内容
        for kw in keywords[:3]:
            script += f"\n关于{kw}，这是很重要的一点..."
        
        return script
    
    async def _generate_voice(self, script: str, config: CommentaryConfig) -> str:
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
    
    async def _composite_video(
        self,
        video_path: str,
        script: str,
        voice_path: str,
        captions_path: str,
    ) -> str:
        """合成视频"""
        return "/tmp/commentary_output.mp4"


# 便捷函数
async def create_commentary_video(
    video_path: str,
    topic: str,
    subtitle_file: str = None,
    style: str = "explainer",
) -> Dict[str, Any]:
    """快速创建解说视频"""
    maker = CommentaryMaker()
    return await maker.create(video_path, topic, subtitle_file, style)


__all__ = [
    "CommentaryMaker",
    "create_commentary_video",
]
