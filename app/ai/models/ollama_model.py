#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from .base_model import BaseAIModel, AIModelConfig, AIResponse


class OllamaModel(BaseAIModel):
    """Ollama本地模型集成"""
    
    def __init__(self, config: AIModelConfig):
        super().__init__(config)
        self.session = None
        self.available_models = []
    
    async def initialize(self) -> bool:
        """初始化Ollama连接"""
        try:
            if not self.validate_config():
                return False
            
            # 创建HTTP会话
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            # 检查Ollama服务是否可用
            if not await self._check_ollama_service():
                return False
            
            # 获取可用模型列表
            await self._fetch_available_models()
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Ollama初始化失败: {e}")
            return False
    
    async def _check_ollama_service(self) -> bool:
        """检查Ollama服务是否运行"""
        try:
            url = f"{self.config.api_url}/api/tags"
            async with self.session.get(url) as response:
                return response.status == 200
        except Exception:
            return False
    
    async def _fetch_available_models(self):
        """获取可用模型列表"""
        try:
            url = f"{self.config.api_url}/api/tags"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    self.available_models = [model['name'] for model in data.get('models', [])]
                else:
                    self.available_models = []
        except Exception as e:
            print(f"获取Ollama模型列表失败: {e}")
            self.available_models = []
    
    async def generate_text(self, prompt: str, **kwargs) -> AIResponse:
        """生成文本内容"""
        if not self._initialized:
            return AIResponse(
                success=False,
                error_message="模型未初始化"
            )
        
        try:
            # 准备请求数据
            data = {
                "model": kwargs.get("model", self.config.name),
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "top_p": kwargs.get("top_p", self.config.top_p),
                    "num_predict": kwargs.get("max_tokens", self.config.max_tokens)
                }
            }
            
            # 发送请求
            url = f"{self.config.api_url}/api/generate"
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    return AIResponse(
                        success=True,
                        content=result.get('response', ''),
                        usage={
                            "prompt_tokens": result.get('prompt_eval_count', 0),
                            "completion_tokens": result.get('eval_count', 0),
                            "total_tokens": result.get('prompt_eval_count', 0) + result.get('eval_count', 0)
                        },
                        metadata={
                            "model": result.get('model', ''),
                            "created_at": result.get('created_at', ''),
                            "done": result.get('done', False)
                        }
                    )
                else:
                    error_text = await response.text()
                    return AIResponse(
                        success=False,
                        error_message=f"请求失败: {response.status} - {error_text}"
                    )
                    
        except Exception as e:
            return AIResponse(
                success=False,
                error_message=f"生成文本失败: {str(e)}"
            )
    
    async def analyze_content(self, content: str, analysis_type: str = "general") -> AIResponse:
        """分析内容"""
        # 根据分析类型构建提示词
        prompts = {
            "general": f"请分析以下内容的主要特点和要点：\n\n{content}",
            "emotion": f"请分析以下内容的情感色彩和情绪表达：\n\n{content}",
            "scene": f"请分析以下视频场景的内容和特点：\n\n{content}",
            "dialogue": f"请分析以下对话的内容和人物关系：\n\n{content}"
        }
        
        prompt = prompts.get(analysis_type, prompts["general"])
        return await self.generate_text(prompt)
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        return self._initialized and self.session is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "name": self.name,
            "type": "local",
            "provider": "Ollama",
            "api_url": self.config.api_url,
            "available_models": self.available_models,
            "initialized": self._initialized,
            "config": {
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "top_p": self.config.top_p
            }
        }
    
    async def list_models(self) -> List[str]:
        """获取可用模型列表"""
        if not self._initialized:
            await self.initialize()
        return self.available_models
    
    async def pull_model(self, model_name: str) -> bool:
        """拉取模型"""
        try:
            data = {"name": model_name}
            url = f"{self.config.api_url}/api/pull"
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    # 更新可用模型列表
                    await self._fetch_available_models()
                    return True
                return False
                
        except Exception as e:
            print(f"拉取模型失败: {e}")
            return False
    
    async def delete_model(self, model_name: str) -> bool:
        """删除模型"""
        try:
            data = {"name": model_name}
            url = f"{self.config.api_url}/api/delete"
            
            async with self.session.delete(url, json=data) as response:
                if response.status == 200:
                    # 更新可用模型列表
                    await self._fetch_available_models()
                    return True
                return False
                
        except Exception as e:
            print(f"删除模型失败: {e}")
            return False
    
    def validate_config(self) -> bool:
        """验证配置"""
        if not super().validate_config():
            return False
        
        # Ollama特定验证
        if not self.config.api_url:
            return False
        
        return True
    
    async def close(self):
        """关闭连接"""
        if self.session:
            await self.session.close()
            self.session = None
        self._initialized = False
    
    def __del__(self):
        """析构函数"""
        if self.session and not self.session.closed:
            # 在事件循环中关闭会话
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
                else:
                    loop.run_until_complete(self.close())
            except:
                pass
