#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基础AI服务抽象类
定义所有AI服务的通用接口和基础功能
"""

# from abc import ABC, abstractmethod  # 暂时移除以避免元类冲突
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal


class ModelStatus(Enum):
    """模型状态枚举"""
    NOT_CONFIGURED = "not_configured"
    CONFIGURED = "configured"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    DISABLED = "disabled"


class ModelCapability(Enum):
    """模型能力枚举"""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    IMAGE_GENERATION = "image_generation"
    AUDIO_GENERATION = "audio_generation"
    VIDEO_ANALYSIS = "video_analysis"
    CONTENT_UNDERSTANDING = "content_understanding"


@dataclass
class ModelInfo:
    """模型信息"""
    name: str
    version: str
    provider: str
    capabilities: List[ModelCapability]
    max_tokens: int
    cost_per_1k_tokens: float
    supported_languages: List[str]
    description: str = ""
    website: str = ""
    documentation: str = ""


@dataclass
class ModelRequest:
    """模型请求"""
    prompt: str
    model_id: str
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 0.9
    stream: bool = False
    stop_sequences: Optional[List[str]] = None
    system_prompt: Optional[str] = None
    context: Optional[List[Dict[str, str]]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ModelResponse:
    """模型响应"""
    content: str
    model_id: str
    usage: Dict[str, int]
    finish_reason: str
    cost: float
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None


class BaseAIService(QObject):
    """基础AI服务抽象类"""

    # 信号定义
    status_changed = pyqtSignal(str, ModelStatus)  # 状态变化
    request_started = pyqtSignal(str)  # 请求开始
    request_progress = pyqtSignal(str, int)  # 请求进度
    request_completed = pyqtSignal(str, ModelResponse)  # 请求完成
    request_error = pyqtSignal(str, str)  # 请求错误
    model_info_loaded = pyqtSignal(str, ModelInfo)  # 模型信息加载完成

    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name
        self.status = ModelStatus.NOT_CONFIGURED
        self.configured_models: Dict[str, ModelInfo] = {}
        self.is_processing = False
        self.current_request_id = None

    # @abstractmethod  # 暂时移除
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        pass

    # @abstractmethod  # 暂时移除
    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        pass

    # @abstractmethod  # 暂时移除
    def configure_model(self, model_id: str, api_key: str, **kwargs) -> bool:
        """配置模型"""
        pass

    # @abstractmethod  # 暂时移除
    def test_connection(self, model_id: str) -> bool:
        """测试连接"""
        pass

    # @abstractmethod  # 暂时移除
    def send_request(self, request: ModelRequest) -> Optional[ModelResponse]:
        """发送请求"""
        pass

    # @abstractmethod  # 暂时移除
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """获取模型信息"""
        pass

    # @abstractmethod  # 暂时移除
    def estimate_cost(self, request: ModelRequest) -> float:
        """估算成本"""
        pass

    def get_status(self) -> ModelStatus:
        """获取当前状态"""
        return self.status

    def is_configured(self, model_id: str) -> bool:
        """检查模型是否已配置"""
        return model_id in self.configured_models

    def get_configured_models(self) -> List[str]:
        """获取已配置的模型列表"""
        return list(self.configured_models.keys())

    def cancel_current_request(self) -> bool:
        """取消当前请求"""
        if self.is_processing:
            self.is_processing = False
            if self.current_request_id:
                self.request_error.emit(self.current_request_id, "用户取消操作")
            return True
        return False

    def validate_request(self, request: ModelRequest) -> bool:
        """验证请求参数"""
        if not request.prompt or not request.prompt.strip():
            return False

        if request.model_id not in self.configured_models:
            return False

        if request.max_tokens <= 0:
            return False

        if request.temperature < 0 or request.temperature > 2:
            return False

        if request.top_p < 0 or request.top_p > 1:
            return False

        return True

    def set_status(self, status: ModelStatus):
        """设置状态"""
        self.status = status
        self.status_changed.emit(self.service_name, status)

    def emit_request_started(self, request_id: str):
        """发送请求开始信号"""
        self.current_request_id = request_id
        self.is_processing = True
        self.request_started.emit(request_id)

    def emit_request_progress(self, request_id: str, progress: int):
        """发送请求进度信号"""
        self.request_progress.emit(request_id, progress)

    def emit_request_completed(self, request_id: str, response: ModelResponse):
        """发送请求完成信号"""
        self.is_processing = False
        self.current_request_id = None
        self.request_completed.emit(request_id, response)

    def emit_request_error(self, request_id: str, error_message: str):
        """发送请求错误信号"""
        self.is_processing = False
        self.current_request_id = None
        self.request_error.emit(request_id, error_message)

    def format_error_message(self, error: Exception) -> str:
        """格式化错误消息"""
        return f"{self.service_name} 错误: {str(error)}"

    def handle_error(self, error: Exception, context: str = ""):
        """处理错误"""
        error_message = self.format_error_message(error)
        if context:
            error_message = f"[{context}] {error_message}"

        if self.current_request_id:
            self.emit_request_error(self.current_request_id, error_message)

        return error_message

    def cleanup(self):
        """清理资源"""
        self.is_processing = False
        self.current_request_id = None
        self.set_status(ModelStatus.DISABLED)

    def __str__(self) -> str:
        return f"{self.service_name} AI Service"