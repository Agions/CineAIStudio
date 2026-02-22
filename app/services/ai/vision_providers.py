#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多模型视觉分析适配器
支持 OpenAI GPT-5、Gemini 3 Vision、通义千问 VL 等多种 Vision 模型
"""

import os
import base64
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class VisionAnalysisResult:
    """视觉分析结果"""
    description: str = ""
    content_type: str = "unknown"
    objects: List[str] = None
    text_content: str = ""
    emotion: str = "neutral"
    color_tone: str = "neutral"
    confidence: float = 0.0
    raw_response: str = ""

    def __post_init__(self):
        if self.objects is None:
            self.objects = []


VISION_ANALYSIS_PROMPT = """分析这张视频截图，返回JSON格式：
{
    "description": "详细描述画面内容（50-100字）",
    "content_type": "person/landscape/indoor/outdoor/text/product/animal/food/action",
    "objects": ["检测到的主要物体列表"],
    "text": "画面中出现的文字（如果有）",
    "emotion": "neutral/happy/sad/excited/calm/tense/romantic",
    "color_tone": "warm/cold/neutral",
    "suitable_for": {
        "commentary": 0-100,
        "monologue": 0-100,
        "mashup": 0-100
    }
}
只返回JSON，不要其他内容。"""


class VisionProvider(ABC):
    """视觉分析提供者基类"""

    @abstractmethod
    def analyze_image(self, image_base64: str,
                      prompt: str = VISION_ANALYSIS_PROMPT) -> Dict[str, Any]:
        """分析图片，返回解析后的字典"""
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    @staticmethod
    def _parse_json_response(content: str) -> Dict[str, Any]:
        """从可能包含 markdown 的响应中提取 JSON"""
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            return {"description": content.strip()}


class OpenAIVisionProvider(VisionProvider):
    """OpenAI GPT-5 Vision"""

    def __init__(self, api_key: str, model: str = "gpt-5",
                 base_url: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    def get_name(self) -> str:
        return f"OpenAI/{self.model}"

    def analyze_image(self, image_base64: str,
                      prompt: str = VISION_ANALYSIS_PROMPT) -> Dict[str, Any]:
        from openai import OpenAI
        kwargs = {"api_key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url

        client = OpenAI(**kwargs)
        response = client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}",
                        "detail": "low"
                    }}
                ]
            }],
            max_tokens=500,
        )
        return self._parse_json_response(response.choices[0].message.content)


class QwenVLProvider(VisionProvider):
    """通义千问 VL (Qwen-VL)"""

    def __init__(self, api_key: str,
                 base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
                 model: str = "qwen-vl-plus"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def get_name(self) -> str:
        return f"Qwen/{self.model}"

    def analyze_image(self, image_base64: str,
                      prompt: str = VISION_ANALYSIS_PROMPT) -> Dict[str, Any]:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        response = client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }}
                ]
            }],
            max_tokens=500,
        )
        return self._parse_json_response(response.choices[0].message.content)


class GeminiVisionProvider(VisionProvider):
    """Google Gemini 3 Vision"""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model

    def get_name(self) -> str:
        return f"Gemini/{self.model}"

    def analyze_image(self, image_base64: str,
                      prompt: str = VISION_ANALYSIS_PROMPT) -> Dict[str, Any]:
        import httpx

        url = (f"https://generativelanguage.googleapis.com/v1beta/"
               f"models/{self.model}:generateContent?key={self.api_key}")

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {
                        "mime_type": "image/jpeg",
                        "data": image_base64
                    }}
                ]
            }],
            "generationConfig": {"maxOutputTokens": 500}
        }

        resp = httpx.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return self._parse_json_response(text)


class VisionAnalyzerFactory:
    """
    视觉分析器工厂

    根据配置自动选择可用的 Vision 提供者，支持 fallback。

    用法:
        factory = VisionAnalyzerFactory(config)
        provider = factory.get_provider()
        result = provider.analyze_image(base64_data)
    """

    PROVIDER_MAP = {
        "openai": OpenAIVisionProvider,
        "qwen": QwenVLProvider,
        "gemini": GeminiVisionProvider,
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: LLM 配置字典，结构同 config/llm.yaml
        """
        self._config = config
        self._providers = []  # type: List[VisionProvider]
        self._init_providers()

    def _init_providers(self):
        llm = self._config.get("LLM", {})

        # OpenAI / 兼容接口
        openai_key = os.getenv("OPENAI_API_KEY") or llm.get("openai", {}).get("api_key", "")
        if openai_key and not openai_key.startswith("${"):
            self._providers.append(OpenAIVisionProvider(
                api_key=openai_key,
                model=llm.get("openai", {}).get("vision_model", "gpt-5"),
                base_url=llm.get("openai", {}).get("base_url"),
            ))

        # 通义千问 VL
        qwen_key = os.getenv("QWEN_API_KEY") or llm.get("qwen", {}).get("api_key", "")
        if qwen_key and not qwen_key.startswith("${"):
            self._providers.append(QwenVLProvider(
                api_key=qwen_key,
                model=llm.get("qwen", {}).get("vision_model", "qwen-vl-plus"),
            ))

        # Gemini
        gemini_key = os.getenv("GEMINI_API_KEY") or llm.get("gemini", {}).get("api_key", "")
        if gemini_key and not gemini_key.startswith("${"):
            self._providers.append(GeminiVisionProvider(
                api_key=gemini_key,
                model=llm.get("gemini", {}).get("vision_model", "gemini-2.0-flash"),
            ))

    def get_provider(self, preferred: Optional[str] = None) -> Optional[VisionProvider]:
        """获取可用的 Vision 提供者"""
        if preferred:
            for p in self._providers:
                if preferred.lower() in p.get_name().lower():
                    return p

        return self._providers[0] if self._providers else None

    def analyze_with_fallback(self, image_base64: str,
                               prompt: str = VISION_ANALYSIS_PROMPT) -> Dict[str, Any]:
        """带 fallback 的分析，自动切换提供者"""
        last_error = None
        for provider in self._providers:
            try:
                return provider.analyze_image(image_base64, prompt)
            except Exception as e:
                last_error = e
                print(f"⚠️ {provider.get_name()} 分析失败: {e}")
                continue

        if last_error:
            raise RuntimeError(f"所有视觉分析提供者均失败，最后错误: {last_error}")
        raise RuntimeError("没有可用的视觉分析提供者")

    def get_available_providers(self) -> List[str]:
        return [p.get_name() for p in self._providers]
