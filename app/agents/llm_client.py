"""
LLM 客户端
为不同Agent提供专业的大模型调用能力

优化点:
- 连接池复用
- 智能重试机制
- 流式响应支持
- 性能监控
"""

import os
import time
import asyncio
from typing import Dict, Any, List, Optional, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
import json
import logging

# 配置日志
logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """模型提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    BAIDU = "baidu"
    ALIBABA = "alibaba"
    GOOGLE = "google"
    DEEPSEEK = "deepseek"
    MOONSHOT = "moonshot"
    LOCAL = "local"


@dataclass
class LLMConfig:
    """LLM配置"""
    provider: ModelProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def __post_init__(self):
        """验证配置"""
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("temperature必须在0-2之间")
        if self.max_tokens < 1:
            raise ValueError("max_tokens必须大于0")


@dataclass
class LLMResponse:
    """LLM响应"""
    success: bool
    content: str
    usage: Dict[str, int] = field(default_factory=dict)
    latency: float = 0.0
    error: Optional[str] = None
    model: str = ""
    finish_reason: str = ""


class LLMClient:
    """
    大模型客户端
    
    支持多提供商，为不同Agent提供专业能力
    优化特性:
    - HTTP连接池复用
    - 指数退避重试
    - 请求超时控制
    - 性能指标收集
    """
    
    # 预设配置 - 全部使用国产大模型 (2025年最新)
    AGENT_MODELS = {
        'director': {
            'provider': ModelProvider.DEEPSEEK,
            'model': 'deepseek-chat',
            'description': '导演Agent - DeepSeek-V3最强规划推理'
        },
        'editor': {
            'provider': ModelProvider.MOONSHOT,
            'model': 'kimi-k2.5',
            'description': '剪辑Agent - Kimi K2.5 标准版 (256K上下文)'
        },
        'colorist': {
            'provider': ModelProvider.MOONSHOT,
            'model': 'kimi-k2.5',
            'description': '调色Agent - Kimi K2.5 视觉理解'
        },
        'sound': {
            'provider': ModelProvider.ALIBABA,
            'model': 'qwen2.5-72b-instruct',
            'description': '音效Agent - 通义千问2.5音频理解'
        },
        'vfx': {
            'provider': ModelProvider.MOONSHOT,
            'model': 'kimi-k2.5',
            'description': '特效Agent - Kimi K2.5 画面理解'
        },
        'reviewer': {
            'provider': ModelProvider.DEEPSEEK,
            'model': 'deepseek-coder',
            'description': '审核Agent - DeepSeek Coder细致评估'
        },
        'script': {
            'provider': ModelProvider.MOONSHOT,
            'model': 'kimi-k2.5',
            'description': '文案Agent - Kimi K2.5 创意写作'
        },
        'assistant': {
            'provider': ModelProvider.ALIBABA,
            'model': 'qwen-max-latest',
            'description': '助手Agent - 通义千问Max全能助手'
        }
    }
    
    # 类级别的HTTP会话缓存
    _session_cache: Dict[str, Any] = {}
    
    def __init__(self, config: LLMConfig = None):
        self.config = config
        self._stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_latency': 0.0,
            'tokens_input': 0,
            'tokens_output': 0,
        }
        
    @classmethod
    def for_agent(cls, agent_type: str) -> 'LLMClient':
        """为指定Agent类型创建客户端"""
        preset = cls.AGENT_MODELS.get(agent_type, cls.AGENT_MODELS['director'])
        
        config = LLMConfig(
            provider=preset['provider'],
            model=preset['model'],
            temperature=0.7,
            max_tokens=2000,
            max_retries=3,
            retry_delay=1.0
        )
        
        return cls(config)
        
    def _get_api_key(self) -> Optional[str]:
        """获取API密钥"""
        if self.config and self.config.api_key:
            return self.config.api_key
            
        env_vars = {
            ModelProvider.DEEPSEEK: 'DEEPSEEK_API_KEY',
            ModelProvider.MOONSHOT: 'MOONSHOT_API_KEY',
            ModelProvider.BAIDU: 'BAIDU_API_KEY',
            ModelProvider.ALIBABA: 'DASHSCOPE_API_KEY',
            ModelProvider.OPENAI: 'OPENAI_API_KEY',
        }
        
        env_var = env_vars.get(self.config.provider)
        return os.getenv(env_var) if env_var else None
        
    def _get_session(self):
        """获取或创建HTTP会话（连接池）"""
        provider_key = self.config.provider.value
        
        if provider_key not in self._session_cache:
            import httpx
            # 配置连接池
            limits = httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10,
                keepalive_expiry=30.0
            )
            timeout = httpx.Timeout(
                connect=5.0,
                read=self.config.timeout,
                write=5.0,
                pool=5.0
            )
            
            self._session_cache[provider_key] = httpx.AsyncClient(
                limits=limits,
                timeout=timeout
            )
            
        return self._session_cache[provider_key]
        
    async def complete(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = None,
        max_tokens: int = None,
        stream: bool = False
    ) -> LLMResponse:
        """
        调用大模型完成请求
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            
        Returns:
            LLMResponse: 响应结果
        """
        if not self.config:
            return LLMResponse(
                success=False,
                content='',
                error='配置未初始化'
            )
            
        api_key = self._get_api_key()
        if not api_key:
            return LLMResponse(
                success=False,
                content='',
                error=f'未找到API密钥: {self.config.provider.value}'
            )
            
        # 使用配置参数或默认值
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        
        # 重试机制
        for attempt in range(self.config.max_retries):
            try:
                start_time = time.time()
                
                if self.config.provider == ModelProvider.DEEPSEEK:
                    result = await self._call_deepseek(
                        api_key, prompt, system_prompt, temp, tokens, stream
                    )
                elif self.config.provider == ModelProvider.MOONSHOT:
                    result = await self._call_moonshot(
                        api_key, prompt, system_prompt, temp, tokens, stream
                    )
                elif self.config.provider == ModelProvider.BAIDU:
                    result = await self._call_baidu(
                        api_key, prompt, system_prompt, temp, tokens, stream
                    )
                elif self.config.provider == ModelProvider.ALIBABA:
                    result = await self._call_alibaba(
                        api_key, prompt, system_prompt, temp, tokens, stream
                    )
                else:
                    return LLMResponse(
                        success=False,
                        content='',
                        error=f'不支持的提供商: {self.config.provider.value}'
                    )
                    
                # 更新统计
                latency = time.time() - start_time
                self._update_stats(result, latency)
                
                if result.success:
                    return result
                elif attempt < self.config.max_retries - 1:
                    # 失败时等待后重试
                    wait_time = self.config.retry_delay * (2 ** attempt)
                    logger.warning(f"请求失败，{wait_time}s后重试: {result.error}")
                    await asyncio.sleep(wait_time)
                else:
                    return result
                    
            except asyncio.TimeoutError:
                if attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_delay * (2 ** attempt)
                    logger.warning(f"请求超时，{wait_time}s后重试")
                    await asyncio.sleep(wait_time)
                else:
                    return LLMResponse(
                        success=False,
                        content='',
                        error='请求超时，已达到最大重试次数'
                    )
            except Exception as e:
                logger.error(f"请求异常: {e}")
                if attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_delay * (2 ** attempt)
                    await asyncio.sleep(wait_time)
                else:
                    return LLMResponse(
                        success=False,
                        content='',
                        error=str(e)
                    )
                    
        return LLMResponse(
            success=False,
            content='',
            error='所有重试均失败'
        )
        
    def _update_stats(self, result: LLMResponse, latency: float):
        """更新统计信息"""
        self._stats['total_requests'] += 1
        self._stats['total_latency'] += latency
        
        if result.success:
            self._stats['successful_requests'] += 1
        else:
            self._stats['failed_requests'] += 1
            
        if result.usage:
            self._stats['tokens_input'] += result.usage.get('prompt_tokens', 0)
            self._stats['tokens_output'] += result.usage.get('completion_tokens', 0)
            
    async def _call_deepseek(
        self,
        api_key: str,
        prompt: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        stream: bool
    ) -> LLMResponse:
        """调用DeepSeek API"""
        session = self._get_session()
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})
        
        payload = {
            'model': self.config.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'stream': stream
        }
        
        try:
            response = await session.post(
                'https://api.deepseek.com/v1/chat/completions',
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                success=True,
                content=data['choices'][0]['message']['content'],
                usage=data.get('usage', {}),
                model=data.get('model', ''),
                finish_reason=data['choices'][0].get('finish_reason', '')
            )
        except Exception as e:
            return LLMResponse(
                success=False,
                content='',
                error=f'DeepSeek API错误: {str(e)}'
            )
            
    async def _call_moonshot(
        self,
        api_key: str,
        prompt: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        stream: bool
    ) -> LLMResponse:
        """调用Moonshot (Kimi) API"""
        session = self._get_session()
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.append({'role': 'user', 'content': prompt})
        
        payload = {
            'model': self.config.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'stream': stream
        }
        
        try:
            response = await session.post(
                'https://api.moonshot.cn/v1/chat/completions',
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                success=True,
                content=data['choices'][0]['message']['content'],
                usage=data.get('usage', {}),
                model=data.get('model', ''),
                finish_reason=data['choices'][0].get('finish_reason', '')
            )
        except Exception as e:
            return LLMResponse(
                success=False,
                content='',
                error=f'Moonshot API错误: {str(e)}'
            )
            
    async def _call_baidu(
        self,
        api_key: str,
        prompt: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        stream: bool
    ) -> LLMResponse:
        """调用百度文心 API"""
        import qianfan
        
        try:
            chat_comp = qianfan.ChatCompletion(
                ak=api_key,
                sk=os.getenv('BAIDU_SECRET_KEY')
            )
            
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt})
            
            resp = chat_comp.do(
                model=self.config.model,
                messages=messages,
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            
            result = resp['body']
            
            return LLMResponse(
                success=True,
                content=result['result'],
                usage={
                    'prompt_tokens': result.get('usage', {}).get('prompt_tokens', 0),
                    'completion_tokens': result.get('usage', {}).get('completion_tokens', 0)
                },
                model=self.config.model
            )
        except Exception as e:
            return LLMResponse(
                success=False,
                content='',
                error=f'百度API错误: {str(e)}'
            )
            
    async def _call_alibaba(
        self,
        api_key: str,
        prompt: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        stream: bool
    ) -> LLMResponse:
        """调用阿里通义千问 API"""
        import dashscope
        
        try:
            dashscope.api_key = api_key
            
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': prompt})
            
            response = dashscope.Generation.call(
                model=self.config.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                result_format='message'
            )
            
            if response.status_code == 200:
                return LLMResponse(
                    success=True,
                    content=response.output.choices[0].message.content,
                    usage={
                        'prompt_tokens': response.usage.input_tokens,
                        'completion_tokens': response.usage.output_tokens
                    },
                    model=self.config.model
                )
            else:
                return LLMResponse(
                    success=False,
                    content='',
                    error=f'阿里API错误: {response.message}'
                )
        except Exception as e:
            return LLMResponse(
                success=False,
                content='',
                error=f'阿里API错误: {str(e)}'
            )
            
    async def analyze_image(
        self,
        image_path: str,
        prompt: str = "描述这张图片"
    ) -> LLMResponse:
        """
        分析图片 (视觉理解)
        
        使用Kimi K2.5 Vision或Qwen-VL
        """
        if self.config.provider == ModelProvider.MOONSHOT:
            return await self._analyze_image_moonshot(image_path, prompt)
        elif self.config.provider == ModelProvider.ALIBABA:
            return await self._analyze_image_qwen(image_path, prompt)
        else:
            return LLMResponse(
                success=False,
                content='',
                error='当前模型不支持视觉分析'
            )
            
    async def _analyze_image_moonshot(
        self,
        image_path: str,
        prompt: str
    ) -> LLMResponse:
        """使用Kimi分析图片"""
        import base64
        
        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
                
            session = self._get_session()
            api_key = self._get_api_key()
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'kimi-k2.5',
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{image_data}'}},
                            {'type': 'text', 'text': prompt}
                        ]
                    }
                ]
            }
            
            response = await session.post(
                'https://api.moonshot.cn/v1/chat/completions',
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                success=True,
                content=data['choices'][0]['message']['content'],
                usage=data.get('usage', {})
            )
        except Exception as e:
            return LLMResponse(
                success=False,
                content='',
                error=f'图片分析失败: {str(e)}'
            )
            
    async def _analyze_image_qwen(
        self,
        image_path: str,
        prompt: str
    ) -> LLMResponse:
        """使用Qwen-VL分析图片"""
        import dashscope
        
        try:
            dashscope.api_key = self._get_api_key()
            
            response = dashscope.MultiModalConversation.call(
                model='qwen-vl-max',
                messages=[{
                    'role': 'user',
                    'content': [
                        {'image': image_path},
                        {'text': prompt}
                    ]
                }]
            )
            
            if response.status_code == 200:
                return LLMResponse(
                    success=True,
                    content=response.output.choices[0].message.content[0]['text']
                )
            else:
                return LLMResponse(
                    success=False,
                    content='',
                    error=f'Qwen-VL错误: {response.message}'
                )
        except Exception as e:
            return LLMResponse(
                success=False,
                content='',
                error=f'图片分析失败: {str(e)}'
            )
            
    async def analyze_video_frame(
        self,
        video_path: str,
        timestamp: float,
        prompt: str = "描述这一帧画面"
    ) -> LLMResponse:
        """
        分析视频帧
        
        先提取帧，再使用视觉模型分析
        """
        import tempfile
        import cv2
        
        try:
            # 提取帧
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return LLMResponse(
                    success=False,
                    content='',
                    error='无法提取视频帧'
                )
                
            # 保存临时文件
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                cv2.imwrite(tmp.name, frame)
                frame_path = tmp.name
                
            try:
                # 分析帧
                result = await self.analyze_image(frame_path, prompt)
                return result
            finally:
                # 清理临时文件
                os.unlink(frame_path)
                
        except Exception as e:
            return LLMResponse(
                success=False,
                content='',
                error=f'视频帧分析失败: {str(e)}'
            )
            
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self._stats.copy()
        if stats['total_requests'] > 0:
            stats['avg_latency'] = stats['total_latency'] / stats['total_requests']
            stats['success_rate'] = stats['successful_requests'] / stats['total_requests']
        else:
            stats['avg_latency'] = 0.0
            stats['success_rate'] = 0.0
        return stats
        
    @classmethod
    def close_all_sessions(cls):
        """关闭所有HTTP会话"""
        for session in cls._session_cache.values():
            asyncio.create_task(session.aclose())
        cls._session_cache.clear()
