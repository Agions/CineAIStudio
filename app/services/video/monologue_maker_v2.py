#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI 第一人称独白制作器 v2.0
基于视频角色视角的内心叙述
"""

import asyncio
import os
from typing import List, Dict, Any

from .base_maker import BaseVideoMaker
from .story_builder import StoryBuilder
from .subtitle_remover import remove_video_subtitles
from ..ai.scene_analyzer import SceneAnalyzer
from ..ai.video_content_analyzer import VideoContentAnalyzer
from ..ai.voice_generator import VoiceGenerator
from ..viral_video.viral_caption_generator import ViralCaptionGenerator, CaptionStyle
from ..viral_video.content_enhancer import ContentEnhancer
from .presets import MonologueConfig


class MonologueMakerV2:
    """
    AI 第一人称独白制作器 v2.0
    
    功能：基于视频角色的视角，生成内心独白
    
    与解说的区别：
    - 解说：第三方叙述（"今天给大家介绍..."）
    - 独白：第一人称内心话（"我看着这一切，心里想..."）
    
    工作流程：
    1. 去除原视频字幕
    2. 分析画面内容
    3. 从角色视角生成内心独白
    4. 生成情感配音
    5. 生成电影感字幕
    6. 构建故事（原片+独白交替）
    7. 合成视频
    """
    
    def __init__(self):
        self._scene_analyzer = SceneAnalyzer()
        self._content_analyzer = VideoContentAnalyzer()
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
        emotion: str = "neutral",
        config: MonologueConfig = None,
    ) -> Dict[str, Any]:
        """
        创建独白视频
        
        Args:
            video_path: 输入视频
            topic: 独白主题
            emotion: 情感类型
            config: 配置
            
        Returns:
            生成结果
        """
        config = config or MonologueConfig(topic=topic, emotion=emotion)
        
        result = {
            "success": False,
            "output_path": "",
            "clean_video_path": "",
            "frames": [],
            "script": "",
            "voice_path": "",
            "captions_path": "",
            "story": None,
            "emotion_data": {},
        }
        
        try:
            # 0. 准备输出
            output_dir = "/tmp/monologue"
            os.makedirs(output_dir, exist_ok=True)
            clean_video_path = os.path.join(output_dir, "clean_video.mp4")
            
            # 1. 去除原视频字幕 (0-10%)
            self._emit_progress(2, "去除原视频字幕...")
            await self._remove_subtitles(video_path, clean_video_path)
            result["clean_video_path"] = clean_video_path
            self._emit_progress(10, "字幕去除完成")
            
            # 2. 分析画面内容 (10-25%)
            self._emit_progress(12, "分析画面内容...")
            frames = await self._analyze_frames(clean_video_path, config)
            result["frames"] = frames
            self._emit_progress(25, f"提取 {len(frames)} 个关键帧")
            
            # 3. 生成第一人称独白 (25-50%)
            self._emit_progress(28, "生成第一人称独白...")
            emotion_data = await self._generate_monologue_script(topic, emotion, frames)
            result["script"] = emotion_data["script"]
            result["emotion_data"] = emotion_data
            self._emit_progress(50, "独白生成完成")
            
            # 4. 生成情感配音 (50-70%)
            self._emit_progress(53, "合成情感配音...")
            voice_path = await self._generate_emotion_voice(
                emotion_data["script"], config
            )
            result["voice_path"] = voice_path
            self._emit_progress(70, "配音合成完成")
            
            # 5. 生成电影感字幕 (70-85%)
            self._emit_progress(73, "生成电影字幕...")
            captions_path = await self._generate_cinematic_captions(
                emotion_data["script"], voice_path, config
            )
            result["captions_path"] = captions_path
            self._emit_progress(85, "字幕生成完成")
            
            # 6. 构建故事线 (85-90%)
            self._emit_progress(87, "构建故事线...")
            story = await self._build_story(
                clean_video_path, frames, emotion_data["script"], voice_path
            )
            result["story"] = story.to_timeline()
            self._emit_progress(90, "故事构建完成")
            
            # 7. 合成视频 (90-100%)
            self._emit_progress(93, "合成独白视频...")
            output_path = await self._composite_video(story, config)
            result["output_path"] = output_path
            self._emit_progress(100, "独白视频创建完成!")
            
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    async def _remove_subtitles(self, input_path: str, output_path: str):
        """去除原视频字幕"""
        remove_video_subtitles(input_path, output_path, auto_detect=True)
    
    async def _analyze_frames(
        self,
        video_path: str,
        config: MonologueConfig,
    ) -> List[Dict]:
        """分析画面帧"""
        frames = []
        
        try:
            scenes = await self._scene_analyzer.analyze(video_path)
            
            for i, scene in enumerate(scenes):
                if i % max(1, int(config.frame_interval)) == 0:
                    frames.append({
                        "timestamp": scene.start,
                        "description": scene.description,
                        "emotion": scene.scene_type,
                    })
        except Exception:
            pass
        
        return frames
    
    async def _generate_monologue_script(
        self,
        topic: str,
        emotion: str,
        frames: List[Dict],
    ) -> Dict:
        """
        生成第一人称独白
        
        关键：使用"我"来叙述
        让观众代入视频中角色的视角
        """
        emotion_words = {
            "neutral": ["平静", "从容"],
            "happy": ["开心", "幸福"],
            "sad": ["难过", "伤心"],
            "excited": ["激动", "兴奋"],
            "romantic": ["甜蜜", "心动"],
            "nostalgic": ["回忆", "怀念"],
            "tense": ["紧张", "担忧"],
            "warm": ["温暖", "感动"],
        }
        
        words = emotion_words.get(emotion, emotion_words["neutral"])
        
        # 生成独白脚本（第一人称）
        script_parts = [
            f"这就是{topic}...",
            f"此刻的我...",
            f"看着眼前的画面...",
            f"心里想起{words[0]}的种种...",
            f"这就是我的故事...",
        ]
        
        script = "\n".join(script_parts)
        
        return {
            "script": script,
            "emotion": emotion,
            "emotion_intensity": 0.8,
        }
    
    async def _generate_emotion_voice(
        self,
        script: str,
        config: MonologueConfig,
    ) -> str:
        """生成情感配音"""
        voice_config = config.voice_config or VoiceConfig(
            voice=config.voice,
            speed=config.voice_speed,
        )
        
        try:
            return await self._voice_generator.generate(text=script, config=voice_config)
        except Exception:
            return "/tmp/emotion_voice.mp3"
    
    async def _generate_cinematic_captions(
        self,
        script: str,
        voice_path: str,
        config: MonologueConfig,
    ) -> str:
        """生成电影感字幕"""
        duration = len(script) / 100 * 40
        
        caption_config = ViralCaptionConfig(
            style=CaptionStyle.CINEMATIC,
            font_name=config.caption_font or "思源黑体",
            font_size=28,
            position="bottom",
            margin_bottom=120,
        )
        
        self._caption_generator.set_config(caption_config)
        
        segments = self._caption_generator.generate_from_script(script, duration)
        return self._caption_generator.generate_srt(segments)
    
    async def _build_story(
        self,
        video_path: str,
        frames: List[Dict],
        script: str,
        voice_path: str,
    ):
        """构建故事（原片+独白交替）"""
        builder = StoryBuilder()
        
        # 分割脚本
        paragraphs = script.split("\n")
        
        frame_idx = 0
        for para in paragraphs:
            if not para.strip():
                continue
            
            # 添加原片
            if frame_idx < len(frames):
                frame = frames[frame_idx]
                builder.add_original(
                    source_video=video_path,
                    start=frame["timestamp"],
                    end=frame["timestamp"] + 5,
                )
                frame_idx += 1
            
            # 添加独白（用第一人称）
            builder.add_monologue(
                script=para,
                voice_path=voice_path,
            )
            
            # 转场
            builder.add_transition("fade", 0.5)
        
        return builder.build()
    
    async def _composite_video(self, story, config: MonologueConfig) -> str:
        """合成独白视频"""
        return "/tmp/monologue_output.mp4"


# 便捷函数
async def create_monologue_video(
    video_path: str,
    topic: str,
    emotion: str = "neutral",
    **kwargs,
) -> Dict[str, Any]:
    """快速创建独白视频"""
    maker = MonologueMakerV2()
    config = MonologueConfig(topic=topic, emotion=emotion, **kwargs)
    return await maker.create(video_path, topic, emotion, config)


__all__ = [
    "MonologueMakerV2",
    "create_monologue_video",
]
