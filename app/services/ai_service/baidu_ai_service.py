#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
国产AI服务实现
包含文心一言、讯飞星火、通义千问、智谱AI、百川AI、月之暗面等国产模型
"""

import json
import time
import threading
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from urllib.parse import urljoin

from .base_ai_service import (
    BaseAIService, ModelInfo, ModelRequest, ModelResponse,
    ModelStatus, ModelCapability
)
from ...core.secure_key_manager import get_secure_key_manager


class WenxinService(BaseAIService):
    """文心一言服务"""

    def __init__(self):
        super().__init__("wenxin")
        self.api_base = "https://aip.baidubce.com"
        self.access_token = None
        self.models = {
            "ernie-bot-4": ModelInfo(
                name="ERNIE Bot 4.0",
                version="4.0",
                provider="百度",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.TRANSLATION],
                max_tokens=2048,
                cost_per_1k_tokens=0.12,
                supported_languages=["zh", "en"],
                description="百度最新一代大语言模型，具备强大的理解和生成能力",
                website="https://cloud.baidu.com/product/wenxinworkshop",
                documentation="https://cloud.baidu.com/doc/WENXINWORKSHOP/s/6ltgkzya5"
            ),
            "ernie-bot": ModelInfo(
                name="ERNIE Bot",
                version="3.5",
                provider="百度",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.TRANSLATION],
                max_tokens=1024,
                cost_per_1k_tokens=0.008,
                supported_languages=["zh", "en"],
                description="百度文心一言大模型，支持多种理解和生成任务",
                website="https://cloud.baidu.com/product/wenxinworkshop",
                documentation="https://cloud.baidu.com/doc/WENXINWORKSHOP/s/6ltgkzya5"
            )
        }

    def get_provider_name(self) -> str:
        return "百度文心一言"

    def get_available_models(self) -> List[str]:
        return list(self.models.keys())

    def configure_model(self, model_id: str, api_key: str, **kwargs) -> bool:
        if model_id not in self.models:
            return False

        try:
            # 获取access token
            client_id, client_secret = api_key.split("|")
            token_url = f"{self.api_base}/oauth/2.0/token"
            params = {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret
            }

            response = requests.post(token_url, params=params, timeout=30)
            response.raise_for_status()
            token_data = response.json()

            self.access_token = token_data.get("access_token")
            if not self.access_token:
                return False

            # 存储API密钥
            key_manager = get_secure_key_manager()
            key_manager.store_api_key(f"{self.service_name}_{model_id}", api_key, {
                "model_id": model_id,
                "client_id": client_id,
                "configured_at": time.time()
            })

            self.configured_models[model_id] = self.models[model_id]
            self.set_status(ModelStatus.CONFIGURED)
            self.model_info_loaded.emit(model_id, self.models[model_id])
            return True

        except Exception as e:
            self.handle_error(e, f"配置模型 {model_id}")
            return False

    def test_connection(self, model_id: str) -> bool:
        if model_id not in self.configured_models:
            return False

        try:
            request = ModelRequest(
                prompt="你好，请回复'连接测试成功'",
                model_id=model_id,
                max_tokens=50
            )
            response = self.send_request(request)
            return response is not None

        except Exception as e:
            self.handle_error(e, f"测试连接 {model_id}")
            return False

    def send_request(self, request: ModelRequest) -> Optional[ModelResponse]:
        if not self.validate_request(request):
            return None

        request_id = f"{self.service_name}_{int(time.time() * 1000)}"
        self.emit_request_started(request_id)

        try:
            if not self.access_token:
                return None

            url = f"{self.api_base}/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}"
            }

            data = {
                "messages": [
                    {"role": "user", "content": request.prompt}
                ],
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "stream": request.stream
            }

            if request.system_prompt:
                data["system"] = request.system_prompt

            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()

            # 计算成本
            cost = self.estimate_cost(request)

            # 创建响应对象
            model_response = ModelResponse(
                content=result.get("result", ""),
                model_id=request.model_id,
                usage=result.get("usage", {"total_tokens": 0}),
                finish_reason=result.get("finish_reason", "stop"),
                cost=cost,
                timestamp=time.time(),
                metadata={
                    "request_id": result.get("id", ""),
                    "object": result.get("object", "chat.completion")
                }
            )

            self.emit_request_completed(request_id, model_response)
            return model_response

        except Exception as e:
            self.emit_request_error(request_id, self.handle_error(e, f"发送请求 {request_id}"))
            return None

    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        return self.models.get(model_id)

    def estimate_cost(self, request: ModelRequest) -> float:
        model_info = self.models.get(request.model_id)
        if not model_info:
            return 0.0

        # 简单估算：输入token数 * 费率
        estimated_tokens = len(request.prompt) // 4  # 粗略估算
        return (estimated_tokens / 1000) * model_info.cost_per_1k_tokens


class SparkService(BaseAIService):
    """讯飞星火服务"""

    def __init__(self):
        super().__init__("spark")
        self.api_base = "https://spark-api-open.xf-yun.com"
        self.api_key = None
        self.api_secret = None
        self.models = {
            "spark-3.5": ModelInfo(
                name="星火大模型 3.5",
                version="3.5",
                provider="科大讯飞",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.TRANSLATION],
                max_tokens=4096,
                cost_per_1k_tokens=0.01,
                supported_languages=["zh", "en"],
                description="讯飞星火认知大模型，具备强大的理解和生成能力",
                website="https://xinghuo.xfyun.cn",
                documentation="https://www.xfyun.cn/doc/spark/HTTP%E8%B0%83%E7%94%A8%E6%96%87%E6%A1%A3.html"
            ),
            "spark-3.0": ModelInfo(
                name="星火大模型 3.0",
                version="3.0",
                provider="科大讯飞",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.TRANSLATION],
                max_tokens=2048,
                cost_per_1k_tokens=0.008,
                supported_languages=["zh", "en"],
                description="讯飞星火认知大模型，支持多种理解和生成任务",
                website="https://xinghuo.xfyun.cn",
                documentation="https://www.xfyun.cn/doc/spark/HTTP%E8%B0%83%E7%94%A8%E6%96%87%E6%A1%A3.html"
            )
        }

    def get_provider_name(self) -> str:
        return "科大讯飞星火"

    def get_available_models(self) -> List[str]:
        return list(self.models.keys())

    def configure_model(self, model_id: str, api_key: str, **kwargs) -> bool:
        if model_id not in self.models:
            return False

        try:
            # 解析API密钥和密钥
            self.api_key, self.api_secret = api_key.split("|")

            # 存储API密钥
            key_manager = get_secure_key_manager()
            key_manager.store_api_key(f"{self.service_name}_{model_id}", api_key, {
                "model_id": model_id,
                "configured_at": time.time()
            })

            self.configured_models[model_id] = self.models[model_id]
            self.set_status(ModelStatus.CONFIGURED)
            self.model_info_loaded.emit(model_id, self.models[model_id])
            return True

        except Exception as e:
            self.handle_error(e, f"配置模型 {model_id}")
            return False

    def test_connection(self, model_id: str) -> bool:
        if model_id not in self.configured_models:
            return False

        try:
            request = ModelRequest(
                prompt="你好，请回复'连接测试成功'",
                model_id=model_id,
                max_tokens=50
            )
            response = self.send_request(request)
            return response is not None

        except Exception as e:
            self.handle_error(e, f"测试连接 {model_id}")
            return False

    def send_request(self, request: ModelRequest) -> Optional[ModelResponse]:
        if not self.validate_request(request):
            return None

        request_id = f"{self.service_name}_{int(time.time() * 1000)}"
        self.emit_request_started(request_id)

        try:
            url = f"{self.api_base}/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            data = {
                "model": request.model_id,
                "messages": [
                    {"role": "user", "content": request.prompt}
                ],
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "stream": request.stream
            }

            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()

            # 计算成本
            cost = self.estimate_cost(request)

            # 创建响应对象
            model_response = ModelResponse(
                content=result.get("choices", [{}])[0].get("message", {}).get("content", ""),
                model_id=request.model_id,
                usage=result.get("usage", {"total_tokens": 0}),
                finish_reason=result.get("choices", [{}])[0].get("finish_reason", "stop"),
                cost=cost,
                timestamp=time.time(),
                metadata={
                    "request_id": result.get("id", ""),
                    "object": result.get("object", "chat.completion")
                }
            )

            self.emit_request_completed(request_id, model_response)
            return model_response

        except Exception as e:
            self.emit_request_error(request_id, self.handle_error(e, f"发送请求 {request_id}"))
            return None

    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        return self.models.get(model_id)

    def estimate_cost(self, request: ModelRequest) -> float:
        model_info = self.models.get(request.model_id)
        if not model_info:
            return 0.0

        estimated_tokens = len(request.prompt) // 4
        return (estimated_tokens / 1000) * model_info.cost_per_1k_tokens


class QwenService(BaseAIService):
    """通义千问服务"""

    def __init__(self):
        super().__init__("qwen")
        self.api_base = "https://dashscope.aliyuncs.com"
        self.api_key = None
        self.models = {
            "qwen-turbo": ModelInfo(
                name="Qwen-Turbo",
                version="turbo",
                provider="阿里云",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.TRANSLATION],
                max_tokens=6000,
                cost_per_1k_tokens=0.02,
                supported_languages=["zh", "en"],
                description="通义千问-Turbo，阿里云大语言模型，响应速度快",
                website="https://qianwen.aliyun.com",
                documentation="https://help.aliyun.com/zh/dashscope/developer-reference/api-details"
            ),
            "qwen-plus": ModelInfo(
                name="Qwen-Plus",
                version="plus",
                provider="阿里云",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.TRANSLATION],
                max_tokens=8000,
                cost_per_1k_tokens=0.05,
                supported_languages=["zh", "en"],
                description="通义千问-Plus，阿里云大语言模型，能力更强",
                website="https://qianwen.aliyun.com",
                documentation="https://help.aliyun.com/zh/dashscope/developer-reference/api-details"
            ),
            "qwen-max": ModelInfo(
                name="Qwen-Max",
                version="max",
                provider="阿里云",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.TRANSLATION],
                max_tokens=20000,
                cost_per_1k_tokens=0.1,
                supported_languages=["zh", "en"],
                description="通义千问-Max，阿里云大语言模型，最强版本",
                website="https://qianwen.aliyun.com",
                documentation="https://help.aliyun.com/zh/dashscope/developer-reference/api-details"
            )
        }

    def get_provider_name(self) -> str:
        return "阿里云通义千问"

    def get_available_models(self) -> List[str]:
        return list(self.models.keys())

    def configure_model(self, model_id: str, api_key: str, **kwargs) -> bool:
        if model_id not in self.models:
            return False

        try:
            self.api_key = api_key

            # 存储API密钥
            key_manager = get_secure_key_manager()
            key_manager.store_api_key(f"{self.service_name}_{model_id}", api_key, {
                "model_id": model_id,
                "configured_at": time.time()
            })

            self.configured_models[model_id] = self.models[model_id]
            self.set_status(ModelStatus.CONFIGURED)
            self.model_info_loaded.emit(model_id, self.models[model_id])
            return True

        except Exception as e:
            self.handle_error(e, f"配置模型 {model_id}")
            return False

    def test_connection(self, model_id: str) -> bool:
        if model_id not in self.configured_models:
            return False

        try:
            request = ModelRequest(
                prompt="你好，请回复'连接测试成功'",
                model_id=model_id,
                max_tokens=50
            )
            response = self.send_request(request)
            return response is not None

        except Exception as e:
            self.handle_error(e, f"测试连接 {model_id}")
            return False

    def send_request(self, request: ModelRequest) -> Optional[ModelResponse]:
        if not self.validate_request(request):
            return None

        request_id = f"{self.service_name}_{int(time.time() * 1000)}"
        self.emit_request_started(request_id)

        try:
            url = f"{self.api_base}/api/v1/services/aigc/text-generation/generation"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            data = {
                "model": request.model_id,
                "input": {
                    "messages": [
                        {"role": "user", "content": request.prompt}
                    ]
                },
                "parameters": {
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                    "enable_search": True
                }
            }

            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()

            # 计算成本
            cost = self.estimate_cost(request)

            # 创建响应对象
            model_response = ModelResponse(
                content=result.get("output", {}).get("text", ""),
                model_id=request.model_id,
                usage=result.get("usage", {"total_tokens": 0}),
                finish_reason="stop",
                cost=cost,
                timestamp=time.time(),
                metadata={
                    "request_id": result.get("request_id", ""),
                    "model": result.get("model", request.model_id)
                }
            )

            self.emit_request_completed(request_id, model_response)
            return model_response

        except Exception as e:
            self.emit_request_error(request_id, self.handle_error(e, f"发送请求 {request_id}"))
            return None

    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        return self.models.get(model_id)

    def estimate_cost(self, request: ModelRequest) -> float:
        model_info = self.models.get(request.model_id)
        if not model_info:
            return 0.0

        estimated_tokens = len(request.prompt) // 4
        return (estimated_tokens / 1000) * model_info.cost_per_1k_tokens


class GLMService(BaseAIService):
    """智谱AI服务"""

    def __init__(self):
        super().__init__("glm")
        self.api_base = "https://open.bigmodel.cn"
        self.api_key = None
        self.models = {
            "glm-4": ModelInfo(
                name="GLM-4",
                version="4",
                provider="智谱AI",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.TRANSLATION],
                max_tokens=128000,
                cost_per_1k_tokens=0.1,
                supported_languages=["zh", "en"],
                description="智谱GLM-4大模型，具备强大的理解和生成能力",
                website="https://open.bigmodel.cn",
                documentation="https://open.bigmodel.cn/dev/api#glm-4"
            ),
            "glm-4-air": ModelInfo(
                name="GLM-4-Air",
                version="4-air",
                provider="智谱AI",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.TRANSLATION],
                max_tokens=128000,
                cost_per_1k_tokens=0.05,
                supported_languages=["zh", "en"],
                description="智谱GLM-4-Air大模型，成本更低，性能依然出色",
                website="https://open.bigmodel.cn",
                documentation="https://open.bigmodel.cn/dev/api#glm-4"
            ),
            "glm-4-flash": ModelInfo(
                name="GLM-4-Flash",
                version="4-flash",
                provider="智谱AI",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.TRANSLATION],
                max_tokens=128000,
                cost_per_1k_tokens=0.001,
                supported_languages=["zh", "en"],
                description="智谱GLM-4-Flash大模型，成本极低，适合快速测试",
                website="https://open.bigmodel.cn",
                documentation="https://open.bigmodel.cn/dev/api#glm-4"
            )
        }

    def get_provider_name(self) -> str:
        return "智谱AI"

    def get_available_models(self) -> List[str]:
        return list(self.models.keys())

    def configure_model(self, model_id: str, api_key: str, **kwargs) -> bool:
        if model_id not in self.models:
            return False

        try:
            self.api_key = api_key

            # 存储API密钥
            key_manager = get_secure_key_manager()
            key_manager.store_api_key(f"{self.service_name}_{model_id}", api_key, {
                "model_id": model_id,
                "configured_at": time.time()
            })

            self.configured_models[model_id] = self.models[model_id]
            self.set_status(ModelStatus.CONFIGURED)
            self.model_info_loaded.emit(model_id, self.models[model_id])
            return True

        except Exception as e:
            self.handle_error(e, f"配置模型 {model_id}")
            return False

    def test_connection(self, model_id: str) -> bool:
        if model_id not in self.configured_models:
            return False

        try:
            request = ModelRequest(
                prompt="你好，请回复'连接测试成功'",
                model_id=model_id,
                max_tokens=50
            )
            response = self.send_request(request)
            return response is not None

        except Exception as e:
            self.handle_error(e, f"测试连接 {model_id}")
            return False

    def send_request(self, request: ModelRequest) -> Optional[ModelResponse]:
        if not self.validate_request(request):
            return None

        request_id = f"{self.service_name}_{int(time.time() * 1000)}"
        self.emit_request_started(request_id)

        try:
            url = f"{self.api_base}/api/paas/v4/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            data = {
                "model": request.model_id,
                "messages": [
                    {"role": "user", "content": request.prompt}
                ],
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "stream": request.stream
            }

            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()

            # 计算成本
            cost = self.estimate_cost(request)

            # 创建响应对象
            model_response = ModelResponse(
                content=result.get("choices", [{}])[0].get("message", {}).get("content", ""),
                model_id=request.model_id,
                usage=result.get("usage", {"total_tokens": 0}),
                finish_reason=result.get("choices", [{}])[0].get("finish_reason", "stop"),
                cost=cost,
                timestamp=time.time(),
                metadata={
                    "request_id": result.get("id", ""),
                    "object": result.get("object", "chat.completion")
                }
            )

            self.emit_request_completed(request_id, model_response)
            return model_response

        except Exception as e:
            self.emit_request_error(request_id, self.handle_error(e, f"发送请求 {request_id}"))
            return None

    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        return self.models.get(model_id)

    def estimate_cost(self, request: ModelRequest) -> float:
        model_info = self.models.get(request.model_id)
        if not model_info:
            return 0.0

        estimated_tokens = len(request.prompt) // 4
        return (estimated_tokens / 1000) * model_info.cost_per_1k_tokens


class BaichuanService(BaseAIService):
    """百川AI服务"""

    def __init__(self):
        super().__init__("baichuan")
        self.api_base = "https://api.baichuan-ai.com"
        self.api_key = None
        self.models = {
            "baichuan2-turbo": ModelInfo(
                name="Baichuan2-Turbo",
                version="2-turbo",
                provider="百川智能",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.TRANSLATION],
                max_tokens=4096,
                cost_per_1k_tokens=0.02,
                supported_languages=["zh", "en"],
                description="百川2-Turbo大模型，响应速度快",
                website="https://www.baichuan-ai.com",
                documentation="https://platform.baichuan-ai.com/docs/api"
            ),
            "baichuan2": ModelInfo(
                name="Baichuan2",
                version="2",
                provider="百川智能",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.TRANSLATION],
                max_tokens=8192,
                cost_per_1k_tokens=0.05,
                supported_languages=["zh", "en"],
                description="百川2大模型，能力更强",
                website="https://www.baichuan-ai.com",
                documentation="https://platform.baichuan-ai.com/docs/api"
            )
        }

    def get_provider_name(self) -> str:
        return "百川智能"

    def get_available_models(self) -> List[str]:
        return list(self.models.keys())

    def configure_model(self, model_id: str, api_key: str, **kwargs) -> bool:
        if model_id not in self.models:
            return False

        try:
            self.api_key = api_key

            # 存储API密钥
            key_manager = get_secure_key_manager()
            key_manager.store_api_key(f"{self.service_name}_{model_id}", api_key, {
                "model_id": model_id,
                "configured_at": time.time()
            })

            self.configured_models[model_id] = self.models[model_id]
            self.set_status(ModelStatus.CONFIGURED)
            self.model_info_loaded.emit(model_id, self.models[model_id])
            return True

        except Exception as e:
            self.handle_error(e, f"配置模型 {model_id}")
            return False

    def test_connection(self, model_id: str) -> bool:
        if model_id not in self.configured_models:
            return False

        try:
            request = ModelRequest(
                prompt="你好，请回复'连接测试成功'",
                model_id=model_id,
                max_tokens=50
            )
            response = self.send_request(request)
            return response is not None

        except Exception as e:
            self.handle_error(e, f"测试连接 {model_id}")
            return False

    def send_request(self, request: ModelRequest) -> Optional[ModelResponse]:
        if not self.validate_request(request):
            return None

        request_id = f"{self.service_name}_{int(time.time() * 1000)}"
        self.emit_request_started(request_id)

        try:
            url = f"{self.api_base}/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            data = {
                "model": request.model_id,
                "messages": [
                    {"role": "user", "content": request.prompt}
                ],
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "stream": request.stream
            }

            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()

            # 计算成本
            cost = self.estimate_cost(request)

            # 创建响应对象
            model_response = ModelResponse(
                content=result.get("choices", [{}])[0].get("message", {}).get("content", ""),
                model_id=request.model_id,
                usage=result.get("usage", {"total_tokens": 0}),
                finish_reason=result.get("choices", [{}])[0].get("finish_reason", "stop"),
                cost=cost,
                timestamp=time.time(),
                metadata={
                    "request_id": result.get("id", ""),
                    "object": result.get("object", "chat.completion")
                }
            )

            self.emit_request_completed(request_id, model_response)
            return model_response

        except Exception as e:
            self.emit_request_error(request_id, self.handle_error(e, f"发送请求 {request_id}"))
            return None

    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        return self.models.get(model_id)

    def estimate_cost(self, request: ModelRequest) -> float:
        model_info = self.models.get(request.model_id)
        if not model_info:
            return 0.0

        estimated_tokens = len(request.prompt) // 4
        return (estimated_tokens / 1000) * model_info.cost_per_1k_tokens


class MoonshotService(BaseAIService):
    """月之暗面服务"""

    def __init__(self):
        super().__init__("moonshot")
        self.api_base = "https://api.moonshot.cn"
        self.api_key = None
        self.models = {
            "moonshot-v1-8k": ModelInfo(
                name="Moonshot v1 8K",
                version="v1-8k",
                provider="月之暗面",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.TRANSLATION],
                max_tokens=8192,
                cost_per_1k_tokens=0.03,
                supported_languages=["zh", "en"],
                description="月之暗面大模型，支持8K上下文",
                website="https://moonshot.cn",
                documentation="https://platform.moonshot.cn/docs/api-reference"
            ),
            "moonshot-v1-32k": ModelInfo(
                name="Moonshot v1 32K",
                version="v1-32k",
                provider="月之暗面",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.TRANSLATION],
                max_tokens=32768,
                cost_per_1k_tokens=0.06,
                supported_languages=["zh", "en"],
                description="月之暗面大模型，支持32K超长上下文",
                website="https://moonshot.cn",
                documentation="https://platform.moonshot.cn/docs/api-reference"
            ),
            "moonshot-v1-128k": ModelInfo(
                name="Moonshot v1 128K",
                version="v1-128k",
                provider="月之暗面",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.TRANSLATION],
                max_tokens=128000,
                cost_per_1k_tokens=0.12,
                supported_languages=["zh", "en"],
                description="月之暗面大模型，支持128K超长上下文",
                website="https://moonshot.cn",
                documentation="https://platform.moonshot.cn/docs/api-reference"
            )
        }

    def get_provider_name(self) -> str:
        return "月之暗面"

    def get_available_models(self) -> List[str]:
        return list(self.models.keys())

    def configure_model(self, model_id: str, api_key: str, **kwargs) -> bool:
        if model_id not in self.models:
            return False

        try:
            self.api_key = api_key

            # 存储API密钥
            key_manager = get_secure_key_manager()
            key_manager.store_api_key(f"{self.service_name}_{model_id}", api_key, {
                "model_id": model_id,
                "configured_at": time.time()
            })

            self.configured_models[model_id] = self.models[model_id]
            self.set_status(ModelStatus.CONFIGURED)
            self.model_info_loaded.emit(model_id, self.models[model_id])
            return True

        except Exception as e:
            self.handle_error(e, f"配置模型 {model_id}")
            return False

    def test_connection(self, model_id: str) -> bool:
        if model_id not in self.configured_models:
            return False

        try:
            request = ModelRequest(
                prompt="你好，请回复'连接测试成功'",
                model_id=model_id,
                max_tokens=50
            )
            response = self.send_request(request)
            return response is not None

        except Exception as e:
            self.handle_error(e, f"测试连接 {model_id}")
            return False

    def send_request(self, request: ModelRequest) -> Optional[ModelResponse]:
        if not self.validate_request(request):
            return None

        request_id = f"{self.service_name}_{int(time.time() * 1000)}"
        self.emit_request_started(request_id)

        try:
            url = f"{self.api_base}/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            data = {
                "model": request.model_id,
                "messages": [
                    {"role": "user", "content": request.prompt}
                ],
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "stream": request.stream
            }

            response = requests.post(url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()

            # 计算成本
            cost = self.estimate_cost(request)

            # 创建响应对象
            model_response = ModelResponse(
                content=result.get("choices", [{}])[0].get("message", {}).get("content", ""),
                model_id=request.model_id,
                usage=result.get("usage", {"total_tokens": 0}),
                finish_reason=result.get("choices", [{}])[0].get("finish_reason", "stop"),
                cost=cost,
                timestamp=time.time(),
                metadata={
                    "request_id": result.get("id", ""),
                    "object": result.get("object", "chat.completion")
                }
            )

            self.emit_request_completed(request_id, model_response)
            return model_response

        except Exception as e:
            self.emit_request_error(request_id, self.handle_error(e, f"发送请求 {request_id}"))
            return None

    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        return self.models.get(model_id)

    def estimate_cost(self, request: ModelRequest) -> float:
        model_info = self.models.get(request.model_id)
        if not model_info:
            return 0.0

        estimated_tokens = len(request.prompt) // 4
        return (estimated_tokens / 1000) * model_info.cost_per_1k_tokens


# 服务工厂
class ChineseAIServiceFactory:
    """国产AI服务工厂"""

    @staticmethod
    def create_service(service_name: str) -> Optional[BaseAIService]:
        """创建服务实例"""
        services = {
            "wenxin": WenxinService,
            "spark": SparkService,
            "qwen": QwenService,
            "glm": GLMService,
            "baichuan": BaichuanService,
            "moonshot": MoonshotService
        }

        service_class = services.get(service_name)
        if service_class:
            return service_class()
        return None

    @staticmethod
    def get_available_services() -> List[str]:
        """获取可用的服务列表"""
        return ["wenxin", "spark", "qwen", "glm", "baichuan", "moonshot"]

    @staticmethod
    def get_service_info(service_name: str) -> Dict[str, Any]:
        """获取服务信息"""
        service_map = {
            "wenxin": {
                "name": "百度文心一言",
                "website": "https://cloud.baidu.com/product/wenxinworkshop",
                "description": "百度文心一言大模型，支持多种理解和生成任务"
            },
            "spark": {
                "name": "科大讯飞星火",
                "website": "https://xinghuo.xfyun.cn",
                "description": "讯飞星火认知大模型，具备强大的理解和生成能力"
            },
            "qwen": {
                "name": "阿里云通义千问",
                "website": "https://qianwen.aliyun.com",
                "description": "通义千问大模型，支持多种理解和生成任务"
            },
            "glm": {
                "name": "智谱AI",
                "website": "https://open.bigmodel.cn",
                "description": "智谱GLM大模型，具备强大的理解和生成能力"
            },
            "baichuan": {
                "name": "百川智能",
                "website": "https://www.baichuan-ai.com",
                "description": "百川大模型，支持多种理解和生成任务"
            },
            "moonshot": {
                "name": "月之暗面",
                "website": "https://moonshot.cn",
                "description": "月之暗面大模型，支持超长上下文"
            }
        }

        return service_map.get(service_name, {})