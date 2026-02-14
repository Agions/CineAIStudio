#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视觉分析服务
统一接口处理图像理解和分析
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import asyncio

from .providers.qwen_vl import QwenVLProvider
from .base_LLM_provider import ProviderError


class VisionService:
    """
    视觉分析服务

    功能:
    - 场景理解
    - 文字提取 (OCR)
    - 标签生成
    - 字幕建议
    - 图像描述
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

    async def understand_scene(
        self,
        image_path: str,
        detail_level: str = "high"
    ) -> Dict[str, Any]:
        """
        理解场景

        Args:
            image_path: 图像路径
            detail_level: 详细程度 (high/medium/low)

        Returns:
            场景理解结果
        """
        if not self.provider:
            raise RuntimeError("VL provider is not initialized")

        result = await self.provider.understand_scene(image_path, detail_level)

        return {
            "success": True,
            "data": result,
            "model": self.default_model,
        }

    async def extract_text(self, image_path: str) -> Dict[str, Any]:
        """
        提取文字 (OCR)

        Args:
            image_path: 图像路径

        Returns:
            提取的文字
        """
        if not self.provider:
            raise RuntimeError("VL provider is not initialized")

        result = await self.provider.extract_text(image_path)

        return {
            "success": True,
            "data": result,
            "model": self.default_model,
        }

    async def generate_tags(self, image_path: str) -> Dict[str, Any]:
        """
        生成标签

        Args:
            image_path: 图像路径

        Returns:
            标签列表
        """
        if not self.provider:
            raise RuntimeError("VL provider is not initialized")

        tags = await self.provider.generate_tags(image_path)

        return {
            "success": True,
            "data": {
                "tags": tags,
                "count": len(tags),
            },
            "model": self.default_model,
        }

    async def suggest_subtitle(
        self,
        image_path: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        建议字幕

        Args:
            image_path: 图像路径
            context: 上下文信息

        Returns:
            字幕建议
        """
        if not self.provider:
            raise RuntimeError("VL provider is not initialized")

        result = await self.provider.subtitle_suggestion(image_path, context)

        return {
            "success": True,
            "data": result,
            "model": self.default_model,
        }

    async def analyze_shot(
        self,
        image_path: str,
        shot_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        分析镜头

        Args:
            image_path: 图像路径
            shot_type: 镜头类型 (auto/close-up/medium/long)

        Returns:
            镜头分析
        """
        prompt = (
            "请分析这张图片的镜头类型和拍摄手法：\n"
            "1. 镜头类型（特写、中景、远景）\n"
            "2. 拍摄角度（平视、俯拍、仰拍）\n"
            "3. 构图特点\n"
            "4. 焦点所在\n"
            "5. 适合的电影风格"
        )

        if not self.provider:
            raise RuntimeError("VL provider is not initialized")

        result = await self.provider.analyze_image(image_path, prompt)

        return {
            "success": True,
            "data": result,
            "model": self.default_model,
        }

    async def color_analysis(self, image_path: str) -> Dict[str, Any]:
        """
        颜色分析

        Args:
            image_path: 图像路径

        Returns:
            颜色分析结果
        """
        prompt = (
            "请分析这张图片的色调和色彩风格：\n"
            "1. 主要颜色\n"
            "2. 色调（暖色/冷色/中性）\n"
            "3. 饱和度\n"
            "4. 对比度\n"
            "5. 适合的电影滤镜建议"
        )

        if not self.provider:
            raise RuntimeError("VL provider is not initialized")

        result = await self.provider.analyze_image(image_path, prompt)

        return {
            "success": True,
            "data": result,
            "model": self.default_model,
        }

    async def batch_analyze(
        self,
        image_paths: List[str],
        task: str = "scene"
    ) -> List[Dict[str, Any]]:
        """
        批量分析

        Args:
            image_paths: 图像路径列表
            task: 任务类型 (scene/text/tags/subtitle/shot/color)

        Returns:
            分析结果列表
        """
        if not self.provider:
            raise RuntimeError("VL provider is not initialized")

        # 映射任务到方法
        task_map = {
            "scene": self.understand_scene,
            "text": self.extract_text,
            "tags": self.generate_tags,
            "subtitle": self.suggest_subtitle,
            "shot": self.analyze_shot,
            "color": self.color_analysis,
        }

        if task not in task_map:
            raise ValueError(f"Unknown task: {task}")

        method = task_map[task]

        # 并发执行
        tasks = [method(path) for path in image_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        formatted_results = []
        for path, result in zip(image_paths, results):
            if isinstance(result, Exception):
                formatted_results.append({
                    "success": False,
                    "error": str(result),
                    "image": path,
                })
            else:
                formatted_results.append(result)

        return formatted_results

    async def close(self):
        """关闭服务"""
        if self.provider:
            await self.provider.close()
