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
    
    # 预设配置 - 不同Agent使用不同模型
    AGENT_MODELS = {
        'director': {
            'provider': ModelProvider.OPENAI,
            'model': 'gpt-4',
            'description': '导演Agent - 需要强规划和推理能力'
        },
        'editor': {
            'provider': ModelProvider.ANTHROPIC,
            'model': 'claude-3-opus-20240229',
            'description': '剪辑Agent - 需要长上下文理解视频结构'
        },
        'colorist': {
            'provider': ModelProvider.OPENAI,
            'model': 'gpt-4-vision-preview',
            'description': '调色Agent - 需要视觉理解能力'
        },
        'sound': {
            'provider': ModelProvider.BAIDU,
            'model': 'ERNIE-4.0',
            'description': '音效Agent - 百度语音/音效理解'
        },
        'vfx': {
            'provider': ModelProvider.OPENAI,
            'model': 'dall-e-3',
            'description': '特效Agent - 需要视觉生成能力'
        },
        'reviewer': {
            'provider': ModelProvider.ANTHROPIC,
            'model': 'claude-3-sonnet-20240229',
            'description': '审核Agent - 需要细致分析和评估'
        },
        'script': {
            'provider': ModelProvider.OPENAI,
            'model': 'gpt-4',
            'description': '文案Agent - 创意写作能力'
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
        # 模拟百度API调用
        # 实际实现需要接入百度千帆平台
        return {
            'success': True,
            'content': f"[百度{self.config.model}响应] {prompt[:50]}...",
            'usage': {'prompt_tokens': 100, 'completion_tokens': 50}
        }
        
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
        """图像分析（用于ColoristAgent）"""
        if self.config.provider != ModelProvider.OPENAI:
            return {
                'success': False,
                'content': '',
                'error': '图像分析需要OpenAI Vision模型'
            }
            
        try:
            import openai
            import base64
            
            # 读取图片
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
                
            client = openai.AsyncOpenAI(
                api_key=self.config.api_key or os.getenv('OPENAI_API_KEY')
            )
            
            response = await client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }],
                max_tokens=1000
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
        """图像生成（用于VFXAgent）"""
        if self.config.model != 'dall-e-3':
            return {
                'success': False,
                'content': '',
                'error': '图像生成需要DALL-E 3模型'
            }
            
        try:
            import openai
            
            client = openai.AsyncOpenAI(
                api_key=self.config.api_key or os.getenv('OPENAI_API_KEY')
            )
            
            response = await client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality="standard",
                n=1
            )
            
            return {
                'success': True,
                'content': response.data[0].url,
                'usage': {}
            }
        except Exception as e:
            return {'success': False, 'content': '', 'error': str(e)}
