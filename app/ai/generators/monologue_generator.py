#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI第一人称独白生成器
实现角色分析、情感检测、独白生成和片段匹配
"""

import asyncio
import json
import os
import tempfile
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal

from ..ai_manager import AIManager
from ...core.video_processor import VideoProcessor, VideoInfo, SceneInfo
from .text_to_speech import TextToSpeechEngine


@dataclass
class CharacterProfile:
    """角色档案"""
    name: str
    personality: str  # "内向", "外向", "冷静", "热情"
    age_group: str   # "青年", "中年", "老年"
    background: str  # 角色背景
    speaking_style: str  # 说话风格
    emotional_traits: List[str]  # 情感特征


@dataclass
class MonologueSegment:
    """独白片段"""
    start_time: float
    end_time: float
    text: str
    emotion: str  # "思考", "回忆", "感慨", "决心", "困惑"
    intensity: float  # 情感强度 0-1
    audio_path: str
    character: str
    scene_context: str


@dataclass
class MonologueResult:
    """独白生成结果"""
    video_path: str
    character_profile: CharacterProfile
    segments: List[MonologueSegment]
    total_duration: float
    output_video_path: str
    metadata: Dict[str, Any]


class MonologueGenerator(QObject):
    """AI第一人称独白生成器"""
    
    # 信号
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    generation_completed = pyqtSignal(MonologueResult)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, ai_manager: AIManager):
        super().__init__()
        self.ai_manager = ai_manager
        self.video_processor = VideoProcessor()
        self.tts_engine = TextToSpeechEngine()
        self.temp_dir = tempfile.mkdtemp(prefix="monologue_")
        
        # 角色类型模板
        self.character_templates = {
            "都市白领": {
                "personality": "理性冷静",
                "age_group": "青年",
                "speaking_style": "简洁专业",
                "emotional_traits": ["压力", "追求", "理性", "焦虑"],
                "common_thoughts": ["工作压力", "人际关系", "未来规划", "生活平衡"]
            },
            "校园学生": {
                "personality": "青春活力",
                "age_group": "青年",
                "speaking_style": "活泼直接",
                "emotional_traits": ["好奇", "冲动", "纯真", "困惑"],
                "common_thoughts": ["学习压力", "友情爱情", "梦想追求", "成长烦恼"]
            },
            "家庭主妇": {
                "personality": "温和细腻",
                "age_group": "中年",
                "speaking_style": "温暖贴心",
                "emotional_traits": ["关爱", "操心", "温柔", "坚强"],
                "common_thoughts": ["家庭和谐", "孩子教育", "夫妻关系", "生活琐事"]
            },
            "创业者": {
                "personality": "坚韧果断",
                "age_group": "青年",
                "speaking_style": "激情澎湃",
                "emotional_traits": ["野心", "坚持", "焦虑", "兴奋"],
                "common_thoughts": ["事业发展", "资金压力", "团队管理", "市场竞争"]
            },
            "退休老人": {
                "personality": "睿智平和",
                "age_group": "老年",
                "speaking_style": "深沉感慨",
                "emotional_traits": ["怀念", "智慧", "平静", "关怀"],
                "common_thoughts": ["人生感悟", "家庭亲情", "健康养生", "回忆往昔"]
            }
        }
        
        # 情感映射
        self.emotion_mapping = {
            "dialogue": "思考",
            "action": "紧张",
            "emotional": "感慨",
            "transition": "回忆",
            "normal": "平静"
        }
    
    async def generate_monologue(self, video_path: str, character_type: str = "都市白领",
                               perspective: str = "主角", **kwargs) -> MonologueResult:
        """生成第一人称独白"""
        try:
            self.status_updated.emit("开始生成AI第一人称独白...")
            self.progress_updated.emit(0)
            
            # 1. 分析视频和场景
            self.status_updated.emit("正在分析视频内容和场景...")
            video_info = self.video_processor.analyze_video(video_path)
            scenes = self.video_processor.detect_scenes(video_path)
            self.progress_updated.emit(20)
            
            # 2. 创建角色档案
            self.status_updated.emit("正在创建角色档案...")
            character_profile = await self._create_character_profile(
                character_type, scenes, video_info
            )
            self.progress_updated.emit(35)
            
            # 3. 分析情感节点
            self.status_updated.emit("正在分析情感节点...")
            emotional_moments = await self._analyze_emotional_moments(scenes, character_profile)
            self.progress_updated.emit(50)
            
            # 4. 生成独白内容
            self.status_updated.emit("正在生成独白内容...")
            monologue_segments = await self._generate_monologue_content(
                emotional_moments, character_profile, perspective
            )
            self.progress_updated.emit(70)
            
            # 5. 语音合成
            self.status_updated.emit("正在合成角色语音...")
            audio_segments = await self._synthesize_character_voice(
                monologue_segments, character_profile
            )
            self.progress_updated.emit(85)
            
            # 6. 合成最终视频
            self.status_updated.emit("正在合成最终视频...")
            output_path = await self._create_monologue_video(
                video_path, audio_segments
            )
            self.progress_updated.emit(100)
            
            # 7. 创建结果
            result = MonologueResult(
                video_path=video_path,
                character_profile=character_profile,
                segments=audio_segments,
                total_duration=video_info.duration,
                output_video_path=output_path,
                metadata={
                    "character_type": character_type,
                    "perspective": perspective,
                    "scene_count": len(scenes),
                    "monologue_count": len(audio_segments),
                    "total_monologue_duration": sum(s.end_time - s.start_time for s in audio_segments)
                }
            )
            
            self.status_updated.emit("AI第一人称独白生成完成！")
            self.generation_completed.emit(result)
            return result
            
        except Exception as e:
            error_msg = f"独白生成失败: {str(e)}"
            self.error_occurred.emit(error_msg)
            raise Exception(error_msg)
    
    async def _create_character_profile(self, character_type: str, scenes: List[SceneInfo],
                                      video_info: VideoInfo) -> CharacterProfile:
        """创建角色档案"""
        template = self.character_templates.get(character_type, self.character_templates["都市白领"])
        
        # 使用AI分析视频内容来定制角色
        analysis_prompt = f"""
        基于以下视频信息，为{character_type}角色创建详细的人物档案：
        
        视频信息：
        - 时长: {video_info.duration:.1f}秒
        - 场景数量: {len(scenes)}
        - 主要场景类型: {', '.join(set(scene.scene_type for scene in scenes))}
        
        角色模板：
        - 性格: {template['personality']}
        - 年龄段: {template['age_group']}
        - 说话风格: {template['speaking_style']}
        
        请分析并返回：
        1. 角色的具体背景故事
        2. 角色的核心性格特征
        3. 角色在这个故事中的处境
        4. 角色的内心世界特点
        
        请以自然的语言描述，不超过200字。
        """
        
        response = await self.ai_manager.generate_text(analysis_prompt)
        background = response.content if response.success else f"一个典型的{character_type}，正在经历人生的重要时刻。"
        
        return CharacterProfile(
            name=f"{character_type}主角",
            personality=template["personality"],
            age_group=template["age_group"],
            background=background,
            speaking_style=template["speaking_style"],
            emotional_traits=template["emotional_traits"]
        )
    
    async def _analyze_emotional_moments(self, scenes: List[SceneInfo],
                                       character: CharacterProfile) -> List[Dict[str, Any]]:
        """分析情感节点"""
        emotional_moments = []
        
        for scene in scenes:
            if scene.duration < 3:  # 跳过太短的场景
                continue
            
            # 分析场景的情感强度
            emotion_prompt = f"""
            分析这个{scene.scene_type}场景对{character.name}的情感影响：
            
            场景信息：
            - 类型: {scene.scene_type}
            - 时长: {scene.duration:.1f}秒
            - 置信度: {scene.confidence:.2f}
            
            角色特征：
            - 性格: {character.personality}
            - 情感特质: {', '.join(character.emotional_traits)}
            
            请评估：
            1. 这个场景对角色的情感冲击程度 (0-1)
            2. 角色可能的内心感受
            3. 适合独白的时机点
            
            请以JSON格式返回: {{"intensity": 强度值, "emotion": "情感类型", "suitable": true/false, "reason": "原因"}}
            """
            
            response = await self.ai_manager.generate_text(emotion_prompt)
            
            try:
                # 尝试解析AI返回的结果
                import re
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                    
                    if analysis.get("suitable", False):
                        emotional_moments.append({
                            "scene": scene,
                            "intensity": float(analysis.get("intensity", 0.5)),
                            "emotion": analysis.get("emotion", "思考"),
                            "reason": analysis.get("reason", "")
                        })
            except:
                # 如果解析失败，使用默认策略
                if scene.confidence > 0.5:
                    emotional_moments.append({
                        "scene": scene,
                        "intensity": scene.confidence,
                        "emotion": self.emotion_mapping.get(scene.scene_type, "思考"),
                        "reason": f"{scene.scene_type}场景"
                    })
        
        # 按情感强度排序，选择最重要的时刻
        emotional_moments.sort(key=lambda x: x["intensity"], reverse=True)
        return emotional_moments[:8]  # 最多8个独白时刻
    
    async def _generate_monologue_content(self, emotional_moments: List[Dict[str, Any]],
                                        character: CharacterProfile, perspective: str) -> List[MonologueSegment]:
        """生成独白内容"""
        segments = []
        
        for i, moment in enumerate(emotional_moments):
            scene = moment["scene"]
            emotion = moment["emotion"]
            intensity = moment["intensity"]
            
            # 生成独白文本
            monologue_prompt = f"""
            为{character.name}在这个时刻生成第一人称内心独白：
            
            角色信息：
            - 背景: {character.background}
            - 性格: {character.personality}
            - 说话风格: {character.speaking_style}
            
            当前情境：
            - 场景类型: {scene.scene_type}
            - 情感状态: {emotion}
            - 情感强度: {intensity:.2f}
            - 时间点: {scene.start_time:.1f}秒
            
            要求：
            1. 使用第一人称"我"
            2. 体现角色的{character.speaking_style}风格
            3. 情感要符合{emotion}状态
            4. 独白时长控制在3-8秒
            5. 语言要自然真实，有内心感
            
            请生成独白文本（不超过50字）：
            """
            
            response = await self.ai_manager.generate_text(monologue_prompt)
            monologue_text = response.content if response.success else f"我在想，这个{emotion}的时刻..."
            
            # 清理文本
            monologue_text = monologue_text.strip().replace('"', '').replace("'", "")
            if len(monologue_text) > 100:
                monologue_text = monologue_text[:100] + "..."
            
            # 计算独白时间
            monologue_start = scene.start_time + scene.duration * 0.3  # 在场景30%处开始
            monologue_duration = min(len(monologue_text) * 0.15, 8.0)  # 估算语音时长
            monologue_end = min(monologue_start + monologue_duration, scene.end_time - 0.5)
            
            if monologue_end > monologue_start:
                segment = MonologueSegment(
                    start_time=monologue_start,
                    end_time=monologue_end,
                    text=monologue_text,
                    emotion=emotion,
                    intensity=intensity,
                    audio_path="",
                    character=character.name,
                    scene_context=scene.scene_type
                )
                segments.append(segment)
        
        return segments
    
    async def _synthesize_character_voice(self, segments: List[MonologueSegment],
                                        character: CharacterProfile) -> List[MonologueSegment]:
        """合成角色语音"""
        synthesized_segments = []
        
        # 根据角色特征选择语音参数
        voice_config = self._get_character_voice_config(character)
        
        for i, segment in enumerate(segments):
            try:
                audio_filename = f"monologue_{i:03d}.wav"
                audio_path = os.path.join(self.temp_dir, audio_filename)
                
                # 语音合成
                success = await self.tts_engine.synthesize(
                    text=segment.text,
                    output_path=audio_path,
                    voice_type=voice_config["voice_type"],
                    emotion=voice_config["emotion_map"].get(segment.emotion, "neutral"),
                    speed=voice_config["speed"]
                )
                
                if success:
                    updated_segment = MonologueSegment(
                        start_time=segment.start_time,
                        end_time=segment.end_time,
                        text=segment.text,
                        emotion=segment.emotion,
                        intensity=segment.intensity,
                        audio_path=audio_path,
                        character=segment.character,
                        scene_context=segment.scene_context
                    )
                    synthesized_segments.append(updated_segment)
                    
            except Exception as e:
                print(f"语音合成失败: {e}")
                continue
        
        return synthesized_segments
    
    def _get_character_voice_config(self, character: CharacterProfile) -> Dict[str, Any]:
        """获取角色语音配置"""
        config = {
            "voice_type": "female",
            "speed": 1.0,
            "emotion_map": {
                "思考": "neutral",
                "回忆": "calm",
                "感慨": "emotional",
                "决心": "excited",
                "困惑": "neutral",
                "紧张": "excited",
                "平静": "calm"
            }
        }
        
        # 根据角色年龄和性格调整
        if character.age_group == "老年":
            config["speed"] = 0.9
            config["voice_type"] = "male"
        elif character.age_group == "青年":
            config["speed"] = 1.1
            
        if "冷静" in character.personality:
            config["speed"] = 0.9
        elif "活力" in character.personality:
            config["speed"] = 1.2
            
        return config
    
    async def _create_monologue_video(self, original_video: str,
                                    segments: List[MonologueSegment]) -> str:
        """创建独白视频"""
        try:
            output_path = os.path.join(self.temp_dir, "monologue_output.mp4")
            
            # 简化实现：如果有音频片段，合并第一个
            if segments and segments[0].audio_path and os.path.exists(segments[0].audio_path):
                output_path = self.video_processor.merge_audio_video(
                    original_video, segments[0].audio_path, output_path
                )
            else:
                # 如果没有音频，直接复制原视频
                import shutil
                shutil.copy2(original_video, output_path)
            
            return output_path
            
        except Exception as e:
            # 如果合并失败，返回原视频
            import shutil
            output_path = os.path.join(self.temp_dir, "monologue_output.mp4")
            shutil.copy2(original_video, output_path)
            print(f"视频合并失败，使用原视频: {e}")
            return output_path
    
    def get_available_character_types(self) -> List[str]:
        """获取可用的角色类型"""
        return list(self.character_templates.keys())
    
    def get_character_info(self, character_type: str) -> Dict[str, Any]:
        """获取角色信息"""
        return self.character_templates.get(character_type, {})
