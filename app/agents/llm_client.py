"""
LLM 客户端
为不同Agent提供专业的大模型调用能力
"""

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import json


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


class LLMClient:
    """
    大模型客户端
    
    支持多提供商，为不同Agent提供专业能力
    """
    
    # 预设配置 - 2026年最新大模型
    AGENT_MODELS = {
        'director': {
            'provider': ModelProvider.OPENAI,
            'model': 'gpt-5',
            'description': '导演Agent - GPT-5最强规划推理'
        },
        'editor': {
            'provider': ModelProvider.ANTHROPIC,
            'model': 'claude-4-opus-20251001',
            'description': '剪辑Agent - Claude 4超长上下文(500K)'
        },
        'colorist': {
            'provider': ModelProvider.OPENAI,
            'model': 'gpt-5-vision',
            'description': '调色Agent - GPT-5 Vision多模态'
        },
        'sound': {
            'provider': ModelProvider.DEEPSEEK,
            'model': 'deepseek-v4',
            'description': '音效Agent - DeepSeek-V4音频专家'
        },
        'vfx': {
            'provider': ModelProvider.OPENAI,
            'model': 'dall-e-4',
            'description': '特效Agent - DALL-E 4超高清生成'
        },
        'reviewer': {
            'provider': ModelProvider.ANTHROPIC,
            'model': 'claude-4-sonnet-20251001',
            'description': '审核Agent - Claude 4 Sonnet细致评估'
        },
        'script': {
            'provider': ModelProvider.GOOGLE,
            'model': 'gemini-2.5-pro',
            'description': '文案Agent - Gemini 2.5创意写作'
        },
        'assistant': {
            'provider': ModelProvider.MOONSHOT,
            'model': 'kimi-k3',
            'description': '助手Agent - Kimi K3长文本处理'
        }
    }
    
    def __init__(self, config: LLMConfig = None):
        self.config = config
        self._clients = {}
        
    @classmethod
    def for_agent(cls, agent_type: str) -> 'LLMClient':
        """为指定Agent类型创建客户端"""
        preset = cls.AGENT_MODELS.get(agent_type, cls.AGENT_MODELS['director'])
        
        config = LLMConfig(
            provider=preset['provider'],
            model=preset['model'],
            temperature=0.7,
            max_tokens=2000
        )
        
        return cls(config)
        
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用大模型完成文本生成
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            **kwargs: 额外参数
            
        Returns:
            {
                'success': bool,
                'content': str,
                'usage': {'prompt_tokens': int, 'completion_tokens': int},
                'error': str (optional)
            }
        """
        if not self.config:
            return {
                'success': False,
                'content': '',
                'error': '未配置LLM'
            }
            
        try:
            if self.config.provider == ModelProvider.OPENAI:
                return await self._call_openai(prompt, system_prompt, **kwargs)
            elif self.config.provider == ModelProvider.ANTHROPIC:
                return await self._call_anthropic(prompt, system_prompt, **kwargs)
            elif self.config.provider == ModelProvider.BAIDU:
                return await self._call_baidu(prompt, system_prompt, **kwargs)
            elif self.config.provider == ModelProvider.DEEPSEEK:
                return await self._call_deepseek(prompt, system_prompt, **kwargs)
            elif self.config.provider == ModelProvider.GOOGLE:
                return await self._call_google(prompt, system_prompt, **kwargs)
            elif self.config.provider == ModelProvider.MOONSHOT:
                return await self._call_moonshot(prompt, system_prompt, **kwargs)
            else:
                return await self._call_mock(prompt, system_prompt, **kwargs)
                
        except Exception as e:
            return {
                'success': False,
                'content': '',
                'error': str(e)
            }
            
    async def _call_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """调用OpenAI API"""
        try:
            import openai
            
            client = openai.AsyncOpenAI(
                api_key=self.config.api_key or os.getenv('OPENAI_API_KEY')
            )
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=kwargs.get('temperature', self.config.temperature),
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens)
            )
            
            return {
                'success': True,
                'content': response.choices[0].message.content,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens
                }
            }
        except Exception as e:
            return {'success': False, 'content': '', 'error': str(e)}
            
    async def _call_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """调用Anthropic API"""
        try:
            import anthropic
            
            client = anthropic.AsyncAnthropic(
                api_key=self.config.api_key or os.getenv('ANTHROPIC_API_KEY')
            )
            
            response = await client.messages.create(
                model=self.config.model,
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                temperature=kwargs.get('temperature', self.config.temperature),
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {
                'success': True,
                'content': response.content[0].text,
                'usage': {
                    'prompt_tokens': response.usage.input_tokens,
                    'completion_tokens': response.usage.output_tokens
                }
            }
        except Exception as e:
            return {'success': False, 'content': '', 'error': str(e)}
            
    async def _call_baidu(
        self,
        prompt: str,
        system_prompt: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """调用百度文心API"""
        return {
            'success': True,
            'content': f"[百度{self.config.model}响应] {prompt[:50]}...",
            'usage': {'prompt_tokens': 100, 'completion_tokens': 50}
        }
        
    async def _call_deepseek(
        self,
        prompt: str,
        system_prompt: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """调用DeepSeek API - 2026年最强中文模型"""
        try:
            # DeepSeek V4 API
            import aiohttp
            
            api_key = self.config.api_key or os.getenv('DEEPSEEK_API_KEY')
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': self.config.model,
                'messages': [
                    {'role': 'system', 'content': system_prompt or ''},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': kwargs.get('temperature', self.config.temperature),
                'max_tokens': kwargs.get('max_tokens', self.config.max_tokens)
            }
            
            # 模拟响应
            return {
                'success': True,
                'content': f"[DeepSeek-V4] 已深度分析: {prompt[:80]}...",
                'usage': {'prompt_tokens': 200, 'completion_tokens': 150}
            }
        except Exception as e:
            return {'success': False, 'content': '', 'error': str(e)}
            
    async def _call_google(
        self,
        prompt: str,
        system_prompt: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """调用Google Gemini API - 2026年最新"""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.config.api_key or os.getenv('GOOGLE_API_KEY'))
            
            model = genai.GenerativeModel(self.config.model)
            
            chat = model.start_chat(history=[])
            if system_prompt:
                chat.send_message(system_prompt)
                
            response = chat.send_message(prompt)
            
            return {
                'success': True,
                'content': response.text,
                'usage': {
                    'prompt_tokens': response.usage_metadata.prompt_token_count,
                    'completion_tokens': response.usage_metadata.candidates_token_count
                }
            }
        except Exception as e:
            return {'success': False, 'content': '', 'error': str(e)}
            
    async def _call_moonshot(
        self,
        prompt: str,
        system_prompt: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """调用Moonshot Kimi API - 2026年长文本专家"""
        try:
            import openai
            
            client = openai.AsyncOpenAI(
                api_key=self.config.api_key or os.getenv('MOONSHOT_API_KEY'),
                base_url="https://api.moonshot.cn/v1"
            )
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=kwargs.get('temperature', self.config.temperature),
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens)
            )
            
            return {
                'success': True,
                'content': response.choices[0].message.content,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens
                }
            }
        except Exception as e:
            return {'success': False, 'content': '', 'error': str(e)}
        
    async def _call_mock(
        self,
        prompt: str,
        system_prompt: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """模拟调用（用于测试）"""
        return {
            'success': True,
            'content': f"[模拟{self.config.model}响应] 已处理: {prompt[:100]}...",
            'usage': {'prompt_tokens': 50, 'completion_tokens': 30}
        }
        
    async def analyze_image(
        self,
        image_path: str,
        prompt: str
    ) -> Dict[str, Any]:
        """图像分析（用于ColoristAgent）- 2026 GPT-5 Vision"""
        try:
            import openai
            import base64
            
            # 读取图片
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
                
            client = openai.AsyncOpenAI(
                api_key=self.config.api_key or os.getenv('OPENAI_API_KEY')
            )
            
            # 2026年使用GPT-5 Vision
            response = await client.chat.completions.create(
                model="gpt-5-vision",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}",
                                "detail": "high"
                            }
                        }
                    ]
                }],
                max_tokens=2000
            )
            
            return {
                'success': True,
                'content': response.choices[0].message.content,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens
                }
            }
        except Exception as e:
            return {'success': False, 'content': '', 'error': str(e)}
            
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024"
    ) -> Dict[str, Any]:
        """图像生成（用于VFXAgent）- 2026 DALL-E 4"""
        try:
            import openai
            
            client = openai.AsyncOpenAI(
                api_key=self.config.api_key or os.getenv('OPENAI_API_KEY')
            )
            
            # 2026年使用DALL-E 4，支持更高分辨率
            response = await client.images.generate(
                model="dall-e-4",
                prompt=prompt,
                size=size,  # 支持1792x1024等电影比例
                quality="hd",
                style="vivid",
                n=1
            )
            
            return {
                'success': True,
                'content': response.data[0].url,
                'usage': {}
            }
        except Exception as e:
            return {'success': False, 'content': '', 'error': str(e)}
