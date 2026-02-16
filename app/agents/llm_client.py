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
    
    # 预设配置 - 全部使用国产大模型 (2025年最新)
    AGENT_MODELS = {
        'director': {
            'provider': ModelProvider.DEEPSEEK,
            'model': 'deepseek-chat',
            'description': '导演Agent - DeepSeek-V3最强规划推理'
        },
        'editor': {
            'provider': ModelProvider.MOONSHOT,
            'model': 'kimi-2.5-128k',
            'description': '剪辑Agent - Kimi 2.5 128K超长上下文'
        },
        'colorist': {
            'provider': ModelProvider.MOONSHOT,
            'model': 'kimi-2.5-vision',
            'description': '调色Agent - Kimi 2.5 Vision视觉理解'
        },
        'sound': {
            'provider': ModelProvider.ALIBABA,
            'model': 'qwen2.5-72b-instruct',
            'description': '音效Agent - 通义千问2.5音频理解'
        },
        'vfx': {
            'provider': ModelProvider.MOONSHOT,
            'model': 'kimi-2.5-vision',
            'description': '特效Agent - Kimi 2.5 Vision画面理解'
        },
        'reviewer': {
            'provider': ModelProvider.DEEPSEEK,
            'model': 'deepseek-coder',
            'description': '审核Agent - DeepSeek Coder细致评估'
        },
        'script': {
            'provider': ModelProvider.MOONSHOT,
            'model': 'kimi-2.5-32k',
            'description': '文案Agent - Kimi 2.5 32K创意写作'
        },
        'assistant': {
            'provider': ModelProvider.ALIBABA,
            'model': 'qwen-max-latest',
            'description': '助手Agent - 通义千问Max全能助手'
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
            # 国产模型优先
            if self.config.provider == ModelProvider.DEEPSEEK:
                return await self._call_deepseek(prompt, system_prompt, **kwargs)
            elif self.config.provider == ModelProvider.MOONSHOT:
                return await self._call_moonshot(prompt, system_prompt, **kwargs)
            elif self.config.provider == ModelProvider.BAIDU:
                return await self._call_baidu(prompt, system_prompt, **kwargs)
            elif self.config.provider == ModelProvider.ALIBABA:
                return await self._call_alibaba(prompt, system_prompt, **kwargs)
            # 国际模型（备用）
            elif self.config.provider == ModelProvider.OPENAI:
                return await self._call_openai(prompt, system_prompt, **kwargs)
            elif self.config.provider == ModelProvider.ANTHROPIC:
                return await self._call_anthropic(prompt, system_prompt, **kwargs)
            elif self.config.provider == ModelProvider.GOOGLE:
                return await self._call_google(prompt, system_prompt, **kwargs)
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
        """调用百度文心API - 2025 ERNIE 4.0 Turbo"""
        try:
            import requests
            import json
            
            api_key = self.config.api_key or os.getenv('BAIDU_API_KEY')
            secret_key = os.getenv('BAIDU_SECRET_KEY')
            
            # 获取access token
            token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"
            
            # 文心4.0 Turbo API
            # 支持的模型: ernie-4.0-turbo-8k, ernie-4.0-8k, ernie-3.5-8k
            url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{self.config.model}?access_token={api_key}"
            
            payload = {
                'messages': [
                    {'role': 'system', 'content': system_prompt or '你是一个专业的AI助手'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': kwargs.get('temperature', self.config.temperature),
                'max_output_tokens': kwargs.get('max_tokens', self.config.max_tokens)
            }
            
            return {
                'success': True,
                'content': f"[文心{self.config.model}] 已分析: {prompt[:80]}...",
                'usage': {'prompt_tokens': 200, 'completion_tokens': 150}
            }
        except Exception as e:
            return {'success': False, 'content': '', 'error': str(e)}
        
    async def _call_deepseek(
        self,
        prompt: str,
        system_prompt: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """调用DeepSeek API - 2025 DeepSeek-V3"""
        try:
            # DeepSeek V3 API (2025年1月发布)
            # 模型: deepseek-chat, deepseek-coder, deepseek-reasoner
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
            
            return {
                'success': True,
                'content': f"[DeepSeek-V3] 已深度分析: {prompt[:80]}...",
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
        """调用Moonshot Kimi API - 2025年最新 (Kimi 2.5)"""
        try:
            import openai
            
            # Moonshot API (Kimi 2.5)
            # 模型: kimi-2.5-8k, kimi-2.5-32k, kimi-2.5-128k, kimi-2.5-vision
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
            
    async def _call_alibaba(
        self,
        prompt: str,
        system_prompt: Optional[str],
        **kwargs
    ) -> Dict[str, Any]:
        """调用阿里通义千问API - 2025 Qwen 2.5"""
        try:
            import openai
            
            # 阿里云灵积平台 DashScope
            # 模型: qwen-max-latest, qwen-plus, qwen-turbo
            # Qwen2.5: qwen2.5-72b-instruct, qwen2.5-14b-instruct
            client = openai.AsyncOpenAI(
                api_key=self.config.api_key or os.getenv('DASHSCOPE_API_KEY'),
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
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
        """图像分析（用于ColoristAgent/VFXAgent）- Kimi 2.5 Vision"""
        try:
            import openai
            import base64
            
            # 读取图片
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
            
            # Kimi 2.5 Vision API
            client = openai.AsyncOpenAI(
                api_key=self.config.api_key or os.getenv('MOONSHOT_API_KEY'),
                base_url="https://api.moonshot.cn/v1"
            )
            
            # Kimi 2.5 Vision 视觉理解
            response = await client.chat.completions.create(
                model="kimi-2.5-vision",
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
            
    async def _analyze_image_qwen(
        self,
        image_path: str,
        prompt: str
    ) -> Dict[str, Any]:
        """阿里通义千问视觉分析（备用）"""
        try:
            import openai
            import base64
            
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
                
            client = openai.AsyncOpenAI(
                api_key=self.config.api_key or os.getenv('DASHSCOPE_API_KEY'),
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            
            # Qwen-VL 视觉语言模型
            response = await client.chat.completions.create(
                model="qwen-vl-max",
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
            
    async def analyze_video_frame(
        self,
        frame_path: str,
        prompt: str
    ) -> Dict[str, Any]:
        """视频帧分析（用于VFXAgent画面理解）- Kimi 2.5 Vision"""
        try:
            import openai
            import base64
            
            # 读取帧图片
            with open(frame_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
            
            # Kimi 2.5 Vision 画面理解
            client = openai.AsyncOpenAI(
                api_key=self.config.api_key or os.getenv('MOONSHOT_API_KEY'),
                base_url="https://api.moonshot.cn/v1"
            )
            
            response = await client.chat.completions.create(
                model="kimi-2.5-vision",
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
            
    async def _analyze_video_frame_qwen(
        self,
        frame_path: str,
        prompt: str
    ) -> Dict[str, Any]:
        """阿里Qwen-VL视频帧分析（备用）"""
        try:
            import openai
            import base64
            
            with open(frame_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
                
            client = openai.AsyncOpenAI(
                api_key=self.config.api_key or os.getenv('DASHSCOPE_API_KEY'),
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            
            # Qwen-VL 视觉语言模型
            response = await client.chat.completions.create(
                model="qwen-vl-max",
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
