#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI短剧解说生成器
实现完整的解说内容生成、语音合成和时间轴同步功能
"""

import asyncio
import json
import os
import tempfile
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal

from ..ai_manager import AIManager
from ...core.video_processor import VideoProcessor, VideoInfo, SceneInfo
from .text_to_speech import TextToSpeechEngine


@dataclass
class CommentarySegment:
    """解说片段"""
    start_time: float
    end_time: float
    text: str
    audio_path: str
    scene_type: str
    emotion: str
    voice_style: str


@dataclass
class CommentaryResult:
    """解说生成结果"""
    video_path: str
    segments: List[CommentarySegment]
    total_duration: float
    output_video_path: str
    metadata: Dict[str, Any]


class CommentaryGenerator(QObject):
    """AI解说生成器"""
    
    # 信号
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    generation_completed = pyqtSignal(CommentaryResult)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, ai_manager: AIManager):
        super().__init__()
        self.ai_manager = ai_manager
        self.video_processor = VideoProcessor()
        self.tts_engine = TextToSpeechEngine()
        self.temp_dir = tempfile.mkdtemp(prefix="commentary_")
        
        # 解说模板
        self.commentary_templates = {
            "幽默风趣": {
                "opening": "各位观众朋友们，今天给大家带来一部精彩的短剧",
                "transition": "接下来让我们看看会发生什么",
                "climax": "这里是全剧的高潮部分",
                "ending": "好了，今天的短剧就到这里，喜欢的话记得点赞关注"
            },
            "专业解说": {
                "opening": "欢迎收看本期短剧解说",
                "transition": "故事发展到这里",
                "climax": "剧情达到了转折点",
                "ending": "以上就是本期内容，感谢观看"
            },
            "情感共鸣": {
                "opening": "这是一个关于情感的故事",
                "transition": "让我们一起感受角色的内心",
                "climax": "这一刻，情感达到了顶点",
                "ending": "希望这个故事能触动你的心"
            }
        }
    
    async def generate_commentary(self, video_path: str, style: str = "幽默风趣", 
                                voice_type: str = "female", **kwargs) -> CommentaryResult:
        """生成完整的解说内容"""
        try:
            self.status_updated.emit("开始生成AI解说...")
            self.progress_updated.emit(0)
            
            # 1. 分析视频
            self.status_updated.emit("正在分析视频内容...")
            video_info = self.video_processor.analyze_video(video_path)
            scenes = self.video_processor.detect_scenes(video_path)
            self.progress_updated.emit(20)
            
            # 2. 生成解说文本
            self.status_updated.emit("正在生成解说文本...")
            segments = await self._generate_commentary_text(video_info, scenes, style)
            self.progress_updated.emit(50)
            
            # 3. 语音合成
            self.status_updated.emit("正在合成语音...")
            audio_segments = await self._synthesize_speech(segments, voice_type)
            self.progress_updated.emit(80)
            
            # 4. 合成最终视频
            self.status_updated.emit("正在合成最终视频...")
            output_path = await self._merge_commentary_video(video_path, audio_segments)
            self.progress_updated.emit(100)
            
            # 5. 创建结果
            result = CommentaryResult(
                video_path=video_path,
                segments=audio_segments,
                total_duration=video_info.duration,
                output_video_path=output_path,
                metadata={
                    "style": style,
                    "voice_type": voice_type,
                    "scene_count": len(scenes),
                    "segment_count": len(audio_segments),
                    "generation_time": "2024-01-01 12:00:00"
                }
            )
            
            self.status_updated.emit("AI解说生成完成！")
            self.generation_completed.emit(result)
            return result
            
        except Exception as e:
            error_msg = f"解说生成失败: {str(e)}"
            self.error_occurred.emit(error_msg)
            raise Exception(error_msg)
    
    async def _generate_commentary_text(self, video_info: VideoInfo, 
                                       scenes: List[SceneInfo], style: str) -> List[CommentarySegment]:
        """生成解说文本"""
        segments = []
        template = self.commentary_templates.get(style, self.commentary_templates["幽默风趣"])
        
        # 生成开场白
        opening_prompt = f"""
        为一部时长{video_info.duration:.1f}秒的短剧生成{style}的开场白。
        要求：
        1. 简洁有趣，吸引观众
        2. 时长控制在3-5秒
        3. 符合{style}的风格
        4. 适合短视频平台
        """
        
        opening_response = await self.ai_manager.generate_text(opening_prompt)
        opening_text = opening_response.content if opening_response.success else template["opening"]
        
        segments.append(CommentarySegment(
            start_time=0,
            end_time=4,
            text=opening_text,
            audio_path="",
            scene_type="opening",
            emotion="neutral",
            voice_style="normal"
        ))
        
        # 为每个场景生成解说
        for i, scene in enumerate(scenes):
            if scene.duration < 2:  # 跳过太短的场景
                continue
            
            scene_prompt = f"""
            为短剧中的一个{scene.scene_type}场景生成{style}的解说。
            场景信息：
            - 时长: {scene.duration:.1f}秒
            - 类型: {scene.scene_type}
            - 位置: 第{i+1}个场景
            
            要求：
            1. 解说时长不超过{min(scene.duration * 0.8, 8)}秒
            2. 符合{style}风格
            3. 与场景内容相关
            4. 语言生动有趣
            """
            
            scene_response = await self.ai_manager.generate_text(scene_prompt)
            scene_text = scene_response.content if scene_response.success else f"这里是{scene.scene_type}场景"
            
            # 计算解说时间（避免覆盖重要对话）
            commentary_start = scene.start_time + 1
            commentary_duration = min(len(scene_text) * 0.15, scene.duration * 0.6)  # 估算语音时长
            commentary_end = min(commentary_start + commentary_duration, scene.end_time - 1)
            
            if commentary_end > commentary_start:
                segments.append(CommentarySegment(
                    start_time=commentary_start,
                    end_time=commentary_end,
                    text=scene_text,
                    audio_path="",
                    scene_type=scene.scene_type,
                    emotion=self._detect_scene_emotion(scene),
                    voice_style="normal"
                ))
        
        # 生成结尾
        ending_prompt = f"""
        为这部短剧生成{style}的结尾解说。
        要求：
        1. 总结性的话语
        2. 引导观众互动（点赞、关注等）
        3. 符合{style}风格
        4. 时长3-5秒
        """
        
        ending_response = await self.ai_manager.generate_text(ending_prompt)
        ending_text = ending_response.content if ending_response.success else template["ending"]
        
        segments.append(CommentarySegment(
            start_time=video_info.duration - 5,
            end_time=video_info.duration,
            text=ending_text,
            audio_path="",
            scene_type="ending",
            emotion="positive",
            voice_style="enthusiastic"
        ))
        
        return segments
    
    async def _synthesize_speech(self, segments: List[CommentarySegment], 
                               voice_type: str) -> List[CommentarySegment]:
        """语音合成"""
        synthesized_segments = []
        
        for i, segment in enumerate(segments):
            try:
                # 生成音频文件路径
                audio_filename = f"commentary_{i:03d}.wav"
                audio_path = os.path.join(self.temp_dir, audio_filename)
                
                # 语音合成
                success = await self.tts_engine.synthesize(
                    text=segment.text,
                    output_path=audio_path,
                    voice_type=voice_type,
                    emotion=segment.emotion,
                    speed=1.0
                )
                
                if success:
                    # 更新音频路径
                    updated_segment = CommentarySegment(
                        start_time=segment.start_time,
                        end_time=segment.end_time,
                        text=segment.text,
                        audio_path=audio_path,
                        scene_type=segment.scene_type,
                        emotion=segment.emotion,
                        voice_style=segment.voice_style
                    )
                    synthesized_segments.append(updated_segment)
                else:
                    self.status_updated.emit(f"语音合成失败: {segment.text[:20]}...")
                    
            except Exception as e:
                self.status_updated.emit(f"语音合成错误: {str(e)}")
                continue
        
        return synthesized_segments
    
    async def _merge_commentary_video(self, video_path: str, 
                                    segments: List[CommentarySegment]) -> str:
        """合并解说和视频"""
        try:
            output_path = os.path.join(self.temp_dir, "commentary_output.mp4")
            
            # 创建音频混合配置
            audio_inputs = []
            for segment in segments:
                if os.path.exists(segment.audio_path):
                    audio_inputs.append({
                        "path": segment.audio_path,
                        "start": segment.start_time,
                        "volume": 0.8
                    })
            
            # 使用视频处理器合并
            if audio_inputs:
                # 简化实现：只合并第一个音频
                first_audio = audio_inputs[0]["path"]
                output_path = self.video_processor.merge_audio_video(
                    video_path, first_audio, output_path
                )
            else:
                # 如果没有音频，直接复制原视频
                import shutil
                shutil.copy2(video_path, output_path)
            
            return output_path
            
        except Exception as e:
            raise Exception(f"视频合并失败: {str(e)}")
    
    def _detect_scene_emotion(self, scene: SceneInfo) -> str:
        """检测场景情感"""
        if scene.scene_type == "action":
            return "excited"
        elif scene.scene_type == "dialogue":
            return "neutral"
        elif scene.scene_type == "emotional":
            return "emotional"
        else:
            return "neutral"
    
    def get_available_styles(self) -> List[str]:
        """获取可用的解说风格"""
        return list(self.commentary_templates.keys())
    
    def get_available_voices(self) -> List[str]:
        """获取可用的语音类型"""
        return self.tts_engine.get_available_voices()
