#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from typing import Dict, List, Optional, Any, Type
from PyQt6.QtCore import QObject, pyqtSignal

from .models.base_model import BaseAIModel, AIModelConfig, AIResponse
from .models.openai_model import OpenAIModel
from .models.qianwen_model import QianwenModel
from .models.wenxin_model import WenxinModel
from .models.ollama_model import OllamaModel
from .models.zhipu_model import ZhipuModel
from .models.xunfei_model import XunfeiModel
from .models.hunyuan_model import HunyuanModel
from .models.deepseek_model import DeepSeekModel
from app.config.settings_manager import SettingsManager


class AIManager(QObject):
    """AI模型管理器 - 统一管理所有AI模型"""
    
    # 信号
    model_initialized = pyqtSignal(str, bool)  # 模型名称, 是否成功
    model_response_ready = pyqtSignal(str, AIResponse)  # 模型名称, 响应结果
    
    def __init__(self, settings_manager: SettingsManager):
        super().__init__()
        
        self.settings_manager = settings_manager
        self.models: Dict[str, BaseAIModel] = {}
        self.model_classes: Dict[str, Type[BaseAIModel]] = {
            "openai": OpenAIModel,
            "qianwen": QianwenModel,
            "wenxin": WenxinModel,
            "ollama": OllamaModel,
            "zhipu": ZhipuModel,
            "xunfei": XunfeiModel,
            "hunyuan": HunyuanModel,
            "deepseek": DeepSeekModel
        }
        
        # 默认模型
        self.default_model = None
        
        # 初始化所有配置的模型
        self._initialize_models()

        # 延迟初始化的模型列表
        self._delayed_init_models = []
    
    def _initialize_models(self):
        """初始化所有配置的模型"""
        # 获取AI模型配置
        ai_config = self.settings_manager.get_setting("ai_models", {})
        
        for provider, config in ai_config.items():
            if provider in self.model_classes and config.get("enabled", False):
                self._create_model(provider, config)
    
    def _create_model(self, provider: str, config: Dict[str, Any]):
        """创建AI模型实例"""
        try:
            # 获取API密钥
            api_key = self.settings_manager.get_api_key(provider)
            
            # 创建模型配置
            model_config = AIModelConfig(
                name=config.get("model", provider),
                api_key=api_key,
                api_url=config.get("api_url", ""),
                max_tokens=config.get("max_tokens", 4096),
                temperature=config.get("temperature", 0.7),
                top_p=config.get("top_p", 0.9),
                frequency_penalty=config.get("frequency_penalty", 0.0),
                presence_penalty=config.get("presence_penalty", 0.0),
                enabled=config.get("enabled", False),
                use_proxy=config.get("use_proxy", False),
                proxy_url=config.get("proxy_url", ""),
                custom_headers=config.get("custom_headers", {})
            )
            
            # 创建模型实例
            model_class = self.model_classes[provider]
            model = model_class(model_config)
            
            self.models[provider] = model
            
            # 异步初始化模型
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._initialize_model_async(provider, model))
                else:
                    # 如果没有运行的事件循环，延迟初始化
                    self._delayed_init_models = getattr(self, '_delayed_init_models', [])
                    self._delayed_init_models.append((provider, model))
            except RuntimeError:
                # 没有事件循环，延迟初始化
                self._delayed_init_models.append((provider, model))

        except Exception as e:
            print(f"创建{provider}模型失败: {e}")

    def initialize_delayed_models(self):
        """初始化延迟的模型"""
        if hasattr(self, '_delayed_init_models') and self._delayed_init_models:
            for provider, model in self._delayed_init_models:
                try:
                    asyncio.create_task(self._initialize_model_async(provider, model))
                except Exception as e:
                    print(f"延迟初始化{provider}模型失败: {e}")
            self._delayed_init_models.clear()
    
    async def _initialize_model_async(self, provider: str, model: BaseAIModel):
        """异步初始化模型"""
        try:
            success = await model.initialize()
            self.model_initialized.emit(provider, success)
            
            # 设置默认模型
            if success and self.default_model is None:
                self.default_model = provider
                
        except Exception as e:
            print(f"初始化{provider}模型失败: {e}")
            self.model_initialized.emit(provider, False)
    
    def get_model(self, provider: str = None) -> Optional[BaseAIModel]:
        """获取AI模型"""
        if provider is None:
            provider = self.default_model
        
        return self.models.get(provider)
    
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        available = []
        for provider, model in self.models.items():
            if model.is_available():
                available.append(provider)
        return available
    
    def get_model_info(self, provider: str = None) -> Dict[str, Any]:
        """获取模型信息"""
        model = self.get_model(provider)
        if model:
            return model.get_model_info()
        return {}
    
    async def generate_text(self, prompt: str, provider: str = None, **kwargs) -> AIResponse:
        """生成文本"""
        model = self.get_model(provider)
        if not model:
            return AIResponse(
                success=False,
                error_message=f"模型 {provider or self.default_model} 不可用"
            )
        
        try:
            response = await model.generate_text(prompt, **kwargs)
            self.model_response_ready.emit(provider or self.default_model, response)
            return response
        except Exception as e:
            error_response = AIResponse(
                success=False,
                error_message=f"生成文本失败: {str(e)}"
            )
            self.model_response_ready.emit(provider or self.default_model, error_response)
            return error_response
    
    async def analyze_content(self, content: str, analysis_type: str = "general", provider: str = None) -> AIResponse:
        """分析内容"""
        model = self.get_model(provider)
        if not model:
            return AIResponse(
                success=False,
                error_message=f"模型 {provider or self.default_model} 不可用"
            )
        
        try:
            response = await model.analyze_content(content, analysis_type)
            self.model_response_ready.emit(provider or self.default_model, response)
            return response
        except Exception as e:
            error_response = AIResponse(
                success=False,
                error_message=f"分析内容失败: {str(e)}"
            )
            self.model_response_ready.emit(provider or self.default_model, error_response)
            return error_response
    
    async def generate_commentary(self, video_info: Dict[str, Any], style: str = "幽默风趣", provider: str = None) -> AIResponse:
        """生成视频解说"""
        model = self.get_model(provider)
        if not model:
            return AIResponse(
                success=False,
                error_message=f"模型 {provider or self.default_model} 不可用"
            )
        
        try:
            # 检查模型是否支持解说生成
            if hasattr(model, 'generate_commentary'):
                response = await model.generate_commentary(video_info, style)
            else:
                # 使用通用文本生成
                prompt = self._build_commentary_prompt(video_info, style)
                response = await model.generate_text(prompt)
            
            self.model_response_ready.emit(provider or self.default_model, response)
            return response
        except Exception as e:
            error_response = AIResponse(
                success=False,
                error_message=f"生成解说失败: {str(e)}"
            )
            self.model_response_ready.emit(provider or self.default_model, error_response)
            return error_response
    
    async def generate_monologue(self, video_info: Dict[str, Any], character: str = "主角", emotion: str = "平静", provider: str = None) -> AIResponse:
        """生成第一人称独白"""
        model = self.get_model(provider)
        if not model:
            return AIResponse(
                success=False,
                error_message=f"模型 {provider or self.default_model} 不可用"
            )
        
        try:
            # 检查模型是否支持独白生成
            if hasattr(model, 'generate_monologue'):
                response = await model.generate_monologue(video_info, character, emotion)
            else:
                # 使用通用文本生成
                prompt = self._build_monologue_prompt(video_info, character, emotion)
                response = await model.generate_text(prompt)
            
            self.model_response_ready.emit(provider or self.default_model, response)
            return response
        except Exception as e:
            error_response = AIResponse(
                success=False,
                error_message=f"生成独白失败: {str(e)}"
            )
            self.model_response_ready.emit(provider or self.default_model, error_response)
            return error_response
    
    def _build_commentary_prompt(self, video_info: Dict[str, Any], style: str) -> str:
        """构建解说提示词"""
        return f"""
请为以下短剧视频生成{style}的解说内容：

视频信息：
- 时长：{video_info.get('duration', '未知')}
- 场景：{video_info.get('scenes', '未知')}
- 人物：{video_info.get('characters', '未知')}
- 剧情：{video_info.get('plot', '未知')}

要求：
1. 解说风格：{style}
2. 语言生动有趣
3. 突出剧情亮点
4. 适合短视频观众
5. 控制在适当长度

请生成解说文本：
"""
    
    def _build_monologue_prompt(self, video_info: Dict[str, Any], character: str, emotion: str) -> str:
        """构建独白提示词"""
        return f"""
请为以下短剧视频生成{character}的第一人称独白：

视频信息：
- 时长：{video_info.get('duration', '未知')}
- 场景：{video_info.get('scenes', '未知')}
- 人物：{video_info.get('characters', '未知')}
- 剧情：{video_info.get('plot', '未知')}

要求：
1. 角色视角：{character}
2. 情感基调：{emotion}
3. 第一人称叙述
4. 符合角色性格
5. 贴合剧情发展

请生成独白文本：
"""
    
    def set_default_model(self, provider: str):
        """设置默认模型"""
        if provider in self.models and self.models[provider].is_available():
            self.default_model = provider
    
    def reload_models(self):
        """重新加载模型配置"""
        # 关闭现有模型
        for model in self.models.values():
            if hasattr(model, 'close'):
                asyncio.create_task(model.close())
        
        # 清空模型字典
        self.models.clear()
        self.default_model = None
        
        # 重新初始化
        self._initialize_models()
    
    def update_model_config(self, provider: str, config: Dict[str, Any]):
        """更新模型配置"""
        if provider in self.models:
            # 更新配置
            model = self.models[provider]
            api_key = self.settings_manager.get_api_key(provider)
            
            new_config = AIModelConfig(
                name=config.get("model", provider),
                api_key=api_key,
                api_url=config.get("api_url", ""),
                max_tokens=config.get("max_tokens", 4096),
                temperature=config.get("temperature", 0.7),
                top_p=config.get("top_p", 0.9),
                frequency_penalty=config.get("frequency_penalty", 0.0),
                presence_penalty=config.get("presence_penalty", 0.0),
                enabled=config.get("enabled", False),
                use_proxy=config.get("use_proxy", False),
                proxy_url=config.get("proxy_url", ""),
                custom_headers=config.get("custom_headers", {})
            )
            
            model.update_config(new_config)
            
            # 重新初始化
            asyncio.create_task(self._initialize_model_async(provider, model))
    
    async def close_all(self):
        """关闭所有模型连接"""
        for model in self.models.values():
            if hasattr(model, 'close'):
                await model.close()
    
    def __del__(self):
        """析构函数"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.close_all())
            else:
                loop.run_until_complete(self.close_all())
        except:
            pass
