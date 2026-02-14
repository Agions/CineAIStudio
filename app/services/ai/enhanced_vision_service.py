#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强型视觉分析服务 v2.0

新增功能:
- 目标检测与识别
- 表情与情感分析
- 时序分析
- 运动分析
- 场景深度分析
- 表情识别、手势识别
- 动作识别
- 空间关系分析
"""

from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import asyncio
import json
from datetime import datetime

from .providers.qwen_vl import QwenVLProvider
from .base_LLM_provider import ProviderError


class EnhancedVisionService:
    """
    增强型视觉分析服务

    基础功能（已保留）:
    - 场景理解
    - OCR 文字提取
    - 标签生成
    - 字幕建议
    - 镜头分析
    - 颜色分析
    - 批量分析

    新增功能:
    - 目标检测与识别
    - 表情与情感分析
    - 手势识别
    - 动作识别
    - 时序分析
    - 运动分析
    - 场景深度分析
    - 空间关系分析
    - 社交线索分析
    - 光照分析
    - 构图评分
    - 艺术风格分析
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化服务

        Args:
            config: 配置字典
        """
        self.config = config
        self.provider: Optional[QwenVLProvider] = None
        self._init_provider()

    def _init_provider(self):
        """初始化 VL 提供商"""
        vl_config = self.config.get("VL", {})

        if not vl_config.get("enabled", False):
            raise RuntimeError("VL service is not enabled in config")

        # 初始化千问 VL
        qwen_config = vl_config.get("qwen_vl", {})
        api_key = qwen_config.get("api_key", "")

        if not api_key or api_key == "${QWEN_VL_API_KEY}":
            raise RuntimeError("Qwen VL API key is missing")

        self.provider = QwenVLProvider(
            api_key=api_key,
            base_url=qwen_config.get("base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        )

        self.default_model = qwen_config.get("model", "default")

    # ==================== 目标检测与识别 ====================

    async def detect_objects(
        self,
        image_path: str,
        object_types: List[str] = None,
    ) -> Dict[str, Any]:
        """
        检测和识别图像中的物体

        Args:
            image_path: 图像路径
            object_types: 目标类型列表（可选，如：['人物', '车辆', '动物']）

        Returns:
            检测结果字典
        """
        object_desc = f"包括：{', '.join(object_types)}" if object_types else "包括所有可见物体"

        prompt = (
            f"请检测并详细描述这张图片中的所有主要物体，{object_desc}。\n\n"
            "对于每个物体，请提供：\n"
            "1. 物体名称\n"
            "2. 位置（左上、右上、中央、左下、右下）\n"
            "3. 相对大小（大/中/小）\n"
            "4. 详细描述（颜色、形状、状态等）\n"
            "5. 重要性（主要/次要/背景）\n\n"
            "请以 JSON 格式输出，结构如下：\n"
            '{\n'
            '  "total_count": 数字,\n'
            '  "objects": [\n'
            '    {\n'
            '      "name": "物体名称",\n'
            '      "position": "位置",\n'
            '      "size": "大小",\n'
            '      "description": "描述",\n'
            '      "importance": "重要性"\n'
            '    }\n'
            '  ]\n'
            '}'
        )

        response = await self.provider.analyze_image(image_path, prompt)

        try:
            # 尝试解析 JSON
            # 提取 JSON 部分（因为模型可能在 JSON 前后添加文本）
            content = response.content.strip()

            # 查找 JSON 起始和结束
            start_idx = content.find('{')
            end_idx = content.rfind('}')

            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx + 1]
                result = json.loads(json_str)
            else:
                # 如果无法解析 JSON，使用备用格式
                result = {
                    "total_count": 0,
                    "objects": [],
                    "raw_text": content,
                }
        except json.JSONDecodeError:
            result = {
                "total_count": 0,
                "objects": [],
                "raw_text": response.content,
                "parse_error": True,
            }

        return {
            "success": True,
            "data": result,
            "model": self.default_model,
        }

    async def recognize_persons(
        self,
        image_path: str,
        recognize_faces: bool = True,
    ) -> Dict[str, Any]:
        """
        识别人物

        Args:
            image_path: 图像路径
            recognize_faces: 是否识别人脸

        Returns:
            人物识别结果
        """
        prompt = (
            "请识别图片中的所有人物。\n\n"
            "对于每个人物，请提供：\n"
            "1. 编号（从1开始）\n"
            "2. 性别（男/女/不确定）\n"
            "3. 大致年龄（儿童/青少年/青年/中年/老年）\n"
            "4. 位置（左/中/右，前/后）\n"
            "5. 动作姿态\n"
            "6. 服装描述\n"
            "7. 表情（" + "包含面部表情分析" if recognize_faces else "不含面部表情细节") + "\n"
            "8. 在画面中的重要性\n\n"
            "请以 JSON 格式输出。"
        )

        response = await self.provider.analyze_image(image_path, prompt)

        return {
            "success": True,
            "data": {"raw_text": response.content},
            "model": self.default_model,
        }

    async def recognize_face_expressions(
        self,
        image_path: str,
    ) -> Dict[str, Any]:
        """
        识别面部表情

        Args:
            image_path: 图像路径

        Returns:
            表情识别结果
        """
        prompt = (
            "请详细分析图片中每个人的面部表情。\n\n"
            "对于每个有清晰面部的任务，请提供：\n"
            "1. 编号\n"
            "2. 主要表情（快乐/悲伤/愤怒/惊讶/恐惧/厌恶/中性/其他）\n"
            "3. 表情强度（弱/中/强）\n"
            "4. 可能的情绪状态\n"
            "5. 表情的细微特征（微笑、皱眉、睁眼、闭眼等）\n"
            "6. 是否符合画面整体氛围\n\n"
            "请以 JSON 格式输出。"
        )

        response = await self.provider.analyze_image(image_path, prompt)

        return {
            "success": True,
            "data": {"raw_text": response.content},
            "model": self.default_model,
        }

    async def recognize_gestures(
        self,
        image_path: str,
    ) -> Dict[str, Any]:
        """
        识别手势

        Args:
            image_path: 图像路径

        Returns:
            手势识别结果
        """
        prompt = (
            "请分析图片中人物的手势。\n\n"
            "对于每个人物，请提供：\n"
            "1. 编号\n"
            "2. 左手手势（如果有）\n"
            "3. 右手手势（如果有）\n"
            "4. 手势含义（如：握拳、挥手、比赞、竖大拇指、指向等）\n"
            "5. 手势的情境含义（如：拒绝、欢迎、赞赏等）\n"
            "6. 身体语言配合\n\n"
            "请以 JSON 格式输出。"
        )

        response = await self.provider.analyze_image(image_path, prompt)

        return {
            "success": True,
            "data": {"raw_text": response.content},
            "model": self.default_model,
        }

    async def recognize_actions(
        self,
        image_path: str,
    ) -> Dict[str, Any]:
        """
        识别动作

        Args:
            image_path: 图像路径

        Returns:
            动作识别结果
        """
        prompt = (
            "请分析图片中人物的动作和活动。\n\n"
            "对于每个任务，请提供：\n"
            "1. 编号\n"
            "2. 主要动作（动词描述，如：站立、奔跑、坐、躺、拿、放下等）\n"
            "3. 动作方向（向前/向后/向左/向右/向上/向下）\n"
            "4. 动作状态（正在进行/已完成/准备中）\n"
            "5. 动作的意图或目的\n"
            "6. 动作与整体场景的关系\n\n"
            "请以 JSON 格式输出。"
        )

        response = await self.provider.analyze_image(image_path, prompt)

        return {
            "success": True,
            "data": {"raw_text": response.content},
            "model": self.default_model,
        }

    # ==================== 情感与社交分析 ====================

    async def analyze_emotion(
        self,
        image_path: str,
        include_context: bool = True,
    ) -> Dict[str, Any]:
        """
        整体情感分析

        Args:
            image_path: 图像路径
            include_context: 是否包含上下文信息

        Returns:
            情感分析结果
        """
        prompt = (
            "请分析这张图片的整体情感基调。\n\n"
            "请提供：\n"
            "1. 主要情感（如：欢快、悲伤、紧张、平静、激动等）\n"
            "2. 情感强度（1-10分）\n"
            "3. 情感来源（人物表情、场景氛围、色彩等）\n"
            "4. 情感层次（单一/复杂）"
        )

        if include_context:
            prompt += (
                "\n5. 可能引发观众哪种情感\n"
                "6. 适合的音乐风格\n"
                "7. 适合的叙事节奏"
            )

        prompt += "\n\n请以 JSON 格式输出。"

        response = await self.provider.analyze_image(image_path, prompt)

        return {
            "success": True,
            "data": {"raw_text": response.content},
            "model": self.default_model,
        }

    async def analyze_social_cues(
        self,
        image_path: str,
    ) -> Dict[str, Any]:
        """
        社交线索分析

        Args:
            image_path: 图像路径

        Returns:
            社交线索分析结果
        """
        prompt = (
            "请分析图片中的社交线索和互动关系。\n\n"
            "请提供：\n"
            "1. 人物总数\n"
            "2. 是否有互动（有/无）\n"
            "3. 互动类型（对话/合作/冲突/亲密/陌生等）\n"
            "4. 互动强度\n"
            "5. 视觉焦点（谁吸引注意力）\n"
            "6. 权力动态（主导者/跟随者/平等）\n"
            "7. 空间关系（距离远近、相对位置）\n"
            "8. 适合的剧情类型\n\n"
            "请以 JSON 格式输出。"
        )

        response = await self.provider.analyze_image(image_path, prompt)

        return {
            "success": True,
            "data": {"raw_text": response.content},
            "model": self.default_model,
        }

    # ==================== 空间与深度分析 ====================

    async def analyze_depth(
        self,
        image_path: str,
    ) -> Dict[str, Any]:
        """
        场景深度分析

        Args:
            image_path: 图像路径

        Returns:
            深度分析结果
        """
        prompt = (
            "请分析图片的空间深度和层次结构。\n\n"
            "请提供：\n"
            "1. 深度层次（2D平面/轻微深度/明显深度/强深度感）\n"
            "2. 前景元素（列表）\n"
            "3. 中景元素（列表）\n"
            "4. 背景元素（列表）\n"
            "5. 视觉焦点位置\n"
            "6. 景深效果（浅景深/深景深）\n"
            "7. 视线的引导路径\n"
            "8. 整体空间结构\n\n"
            "请以 JSON 格式输出。"
        )

        response = await self.provider.analyze_image(image_path, prompt)

        return {
            "success": True,
            "data": {"raw_text": response.content},
            "model": self.default_model,
        }

    async def analyze_spatial_relations(
        self,
        image_path: str,
    ) -> Dict[str, Any]:
        """
        空间关系分析

        Args:
            image_path: 图像路径

        Returns:
            空间关系分析结果
        """
        prompt = (
            "请分析图片中元素之间的空间关系。\n\n"
            "对于重要的物体组合，请提供：\n"
            "1. 元素A\n"
            "2. 元素B\n"
            "3. 相对位置（左/右/上/下/前/后/相邻/分离）\n"
            "4. 方向关系（朝向/背向/平行/交叉）\n"
            "5. 距离（近/中/远）\n"
            "6. 相对大小对比\n"
            "7. 视觉平衡感\n\n"
            "请以 JSON 格式输出。"
        )

        response = await self.provider.analyze_image(image_path, prompt)

        return {
            "success": True,
            "data": {"raw_text": response.content},
            "model": self.default_model,
        }

    # ==================== 光照与构图分析 ====================

    async def analyze_lighting(
        self,
        image_path: str,
    ) -> Dict[str, Any]:
        """
        光照分析

        Args:
            image_path: 图像路径

        Returns:
            光照分析结果
        """
        prompt = (
            "请分析图片的光照情况。\n\n"
            "请提供：\n"
            "1. 主要光源方向（顺光/逆光/侧光/顶光/底光）\n"
            "2. 光线强度（强光/正常/弱光）\n"
            "3. 光线质量（硬光/柔光）\n"
            "4. 光线温度（冷光/暖光/中性）\n"
            "5. 阴影情况（重阴影/轻阴影/无明显阴影）\n"
            "6. 曝光情况（曝光过度/正常曝光/曝光不足）\n"
            "7. 光照对氛围的影响\n"
            "8. 电影化用光建议\n\n"
            "请以 JSON 格式输出。"
        )

        response = await self.provider.analyze_image(image_path, prompt)

        return {
            "success": True,
            "data": {"raw_text": response.content},
            "model": self.default_model,
        }

    async def score_composition(
        self,
        image_path: str,
    ) -> Dict[str, Any]:
        """
        构图评分

        Args:
            image_path: 图像路径

        Returns:
            构图评分结果
        """
        prompt = (
            "请评估图片的构图质量。\n\n"
            "请从以下维度评分（1-10分）：\n"
            "1. 三分法则应用\n"
            "2. 视觉平衡\n"
            "3. 引导线运用\n"
            "4. 画面简洁度\n"
            "5. 焦点明确度\n"
            "6. 留白处理\n"
            "7. 整体和谐度\n\n"
            "总分：\n"
            "优点：\n"
            "改进建议：\n\n"
            "请以 JSON 格式输出。"
        )

        response = await self.provider.analyze_image(image_path, prompt)

        return {
            "success": True,
            "data": {"raw_text": response.content},
            "model": self.default_model,
        }

    async def analyze_artistic_style(
        self,
        image_path: str,
    ) -> Dict[str, Any]:
        """
        艺术风格分析

        Args:
            image_path: 图像路径

        Returns:
            艺术风格分析结果
        """
        prompt = (
            "请分析图片的艺术风格特征。\n\n"
            "请提供：\n"
            "1. 主要风格（现代/复古/抽象/写实/卡通等）\n"
            "2. 色彩风格（冷暖、饱和度、对比度）\n"
            "3. 纹理特征\n"
            "4. 构图特点\n"
            "5. 参考的艺术流派或知名作品\n"
            "6. 时效性（潮流/经典/前卫）\n"
            "7. 对目标受众的适配性\n\n"
            "请以 JSON 格式输出。"
        )

        response = await self.provider.analyze_image(image_path, prompt)

        return {
            "success": True,
            "data": {"raw_text": response.content},
            "model": self.default_model,
        }

    # ==================== 时序分析 ====================

    async def analyze_motion(
        self,
        image_path: str,
    ) -> Dict[str, Any]:
        """
        运动分析

        Args:
            image_path: 图像路径

        Returns:
            运动分析结果
        """
        prompt = (
            "请分析图片中的运动感（基于视觉线索和画面动态）。\n\n"
            "对于每个运动元素，请提供：\n"
            "1. 编号\n"
            "2. 运动主体（人物、物体、光影等）\n"
            "3. 运动方向（左/右/上/下/前/后、旋转）\n"
            "4. 运动速度（慢速/中速/快速）\n"
            "5. 运动性质（加速/减速/匀速）\n"
            "6. 运动强度（强/中/弱）\n\n"
            "整体动态感评分（1-10分）：\n"
            "运动建议：\n\n"
            "请以 JSON 格式输出。"
        )

        response = await self.provider.analyze_image(image_path, prompt)

        return {
            "success": True,
            "data": {"raw_text": response.content},
            "model": self.default_model,
        }

    # ==================== 综合分析 ====================

    async def comprehensive_analysis(
        self,
        image_path: str,
        include_all: bool = False,
    ) -> Dict[str, Any]:
        """
        综合分析（单帧全功能）

        Args:
            image_path: 图像路径
            include_all: 是否包含所有高级分析（较慢）

        Returns:
            综合分析结果
        """
        # 基础分析
        scene_result = await self.provider.understand_scene(image_path)
        tags_result = await self.provider.generate_tags(image_path)

        # 颜色分析
        color_prompt = (
            "分析色调、饱和度、对比度，推荐电影滤镜"
        )
        color_result = await self.provider.analyze_image(image_path, color_prompt)

        # 如果 include_all=True，执行所有高级分析
        if include_all:
            # 并发执行
            analyses = await asyncio.gather(
                self.detect_objects(image_path),
                self.recognize_persons(image_path, True),
                self.recognize_face_expressions(image_path),
                self.analyze_emotion(image_path, False),
                self.analyze_depth(image_path),
                self.analyze_lighting(image_path),
                self.score_composition(image_path),
                return_exceptions=True,
            )

            # 整理结果
            advanced_results = {
                "object_detection": analyses[0] if not isinstance(analyses[0], Exception) else None,
                "person_recognition": analyses[1] if not isinstance(analyses[1], Exception) else None,
                "face_expressions": analyses[2] if not isinstance(analyses[2], Exception) else None,
                "emotion_analysis": analyses[3] if not isinstance(analyses[3], Exception) else None,
                "depth_analysis": analyses[4] if not isinstance(analyses[4], Exception) else None,
                "lighting_analysis": analyses[5] if not isinstance(analyses[5], Exception) else None,
                "composition_score": analyses[6] if not isinstance(analyses[6], Exception) else None,
            }
        else:
            advanced_results = None

        return {
            "success": True,
            "data": {
                "timestamp": datetime.now().isoformat(),
                "image": image_path,
                "basic": {
                    "scene": scene_result,
                    "tags": tags_result,
                    "color": color_result,
                },
                "advanced": advanced_results,
            },
            "model": self.default_model,
        }

    async def close(self):
        """关闭服务"""
        if self.provider:
            await self.provider.close()
