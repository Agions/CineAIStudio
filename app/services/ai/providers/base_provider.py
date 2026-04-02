#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM Provider 基类
减少 Provider 代码重复
"""

import httpx
from typing import Optional, Dict, AsyncGenerator, List
from abc import ABC

from ..base_llm_provider import (
    LLMRequest,
    LLMResponse,
)


class CommonLLMProvider(ABC):
    """
    LLM Provider 通用基类
    
    抽取公共逻辑，减少重复代码
    """
    
    # 子类必须定义
    DEFAULT_MODEL: str = ""
    MODELS: Dict[str, Dict] = {}
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "",
        timeout: float = 60.0,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        
    def _get_model_name(self, model: str = None) -> str:
        """获取模型名称"""
        return model or self.DEFAULT_MODEL
    
    def _build_messages(self, request: LLMRequest) -> List[Dict]:
        """构建消息列表"""
        messages = []
        
        # 系统消息
        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
            })
        
        # 用户消息
        if isinstance(request.prompt, str):
            messages.append({
                "role": "user",
                "content": request.prompt
            })
        elif isinstance(request.prompt, list):
            messages.extend(request.prompt)
            
        return messages
    
    def _extract_content(self, response: Dict) -> str:
        """提取响应内容 - 子类可重写"""
        choices = response.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "")
        return ""
    
    def _extract_usage(self, response: Dict) -> Dict:
        """提取使用统计"""
        return response.get("usage", {})
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """生成文本 - 子类需实现具体请求"""
        raise NotImplementedError
    
    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """流式生成 - 子类需实现"""
        raise NotImplementedError
    
    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers=self._get_headers()
            )
        return self._client
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头 - 子类可重写"""
        return {
            "Content-Type": "application/json",
        }
    
    def get_model_info(self, model: str = None) -> Dict:
        """获取模型信息"""
        model = model or self.DEFAULT_MODEL
        return self.MODELS.get(model, {})


class HTTPProviderMixin:
    """HTTP Provider 混入 - 通用 HTTP 请求逻辑"""
    
    async def _post(
        self,
        endpoint: str,
        json_data: Dict,
        stream: bool = False,
    ) -> httpx.Response:
        """发送 POST 请求"""
        url = f"{self.base_url}{endpoint}"
        
        if stream:
            return await self.client.post(url, json=json_data, stream=True)
        return await self.client.post(url, json=json_data)
    
    async def _get(self, endpoint: str, params: Dict = None) -> httpx.Response:
        """发送 GET 请求"""
        url = f"{self.base_url}{endpoint}"
        return await self.client.get(url, params=params)


class BatchProviderMixin:
    """批量处理混入"""
    
    async def batch_generate(
        self,
        prompts: List[str],
        model: str = None,
        **kwargs,
    ) -> List[LLMResponse]:
        """批量生成"""
        import asyncio
        
        requests = [
            LLMRequest(prompt=prompt, model=model or self.DEFAULT_MODEL, **kwargs)
            for prompt in prompts
        ]
        
        tasks = [self.generate(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤错误
        return [
            r if isinstance(r, LLMResponse) else None
            for r in results
        ]


class RetryProviderMixin:
    """重试逻辑混入"""
    
    def __init__(self, max_retries: int = 3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_retries = max_retries
    
    async def _retry_generate(self, request: LLMRequest) -> LLMResponse:
        """带重试的生成"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return await self.generate(request)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                    
        raise last_error
