# CineFlow AI 国产 LLM 集成方案

**文档版本**: v1.0
**创建日期**: 2026-02-14

---

## 📋 需求分析

### 当前问题

```
现状: 仅支持 OpenAI API
问题:
1. ❌ 国产模型未集成（通义千问、Kimi、GLM-5）
2. ❌ API 锁定，无法切换
3. ❌ 不符合国产化要求
4. ❌ 成本高，速度慢
```

### 目标

```
目标: 支持多国产 LLM，本地优先
要求:
1. ✅ 通义千问 Qwen 3
2. ✅ Kimi 2.5
3. ✅ 智谱 GLM-5
4. ✅ 百度文心 ERNIE 4.5
5. ✅ 统一接口，易于切换
6. ✅ 本地模型支持（可选）
```

---

## 🏗️ 架构设计

### 1. 抽象层设计

```
┌─────────────────────────────────────────────┐
│            Application Layer               │
│    (ScriptGenerator, CommentaryMaker, ...)  │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│           LLM Manager Layer                 │
│     (LLMManager - 统一管理，自动切换)       │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│             Provider Interface               │
│      (BaseLLMProvider - 抽象接口)          │
└─────────────────────────────────────────────┘
                      ↓
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
    QwenProvider   KimiProvider  ...
```

### 2. 目录结构

```
app/services/ai/
├── __init__.py
├── base_LLM_provider.py       # 抽象基类
├── llm_manager.py             # LLM 管理器
├── providers/                 # 提供商实现
│   ├── __init__.py
│   ├── openai.py              # OpenAI
│   ├── qwen.py                # 通义千问
│   ├── kimi.py                # Kimi
│   ├── glm5.py                # GLM-5
│   ├── baidu.py               # 百度文心
│   └── local.py               # 本地模型
├── script_generator.py        # 文案生成器（更新）
└── config.py                  # LLM 配置
```

---

## 📝 接口设计

### BaseLLMProvider

```python
"""
LLM 提供商抽象基类
所有具体提供商必须实现此接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class LLMRequest:
    """LLM 请求"""
    prompt: str                          # 提示词
    system_prompt: str = ""               # 系统提示词
    model: str = "default"                # 模型名称
    max_tokens: int = 2000               # 最大生成长度
    temperature: float = 0.7              # 温度参数
    top_p: float = 0.9                   # Top-p 参数


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str                         # 生成内容
    model: str                           # 使用的模型
    tokens_used: int = 0                 # Token 使用量
    finish_reason: str = "stop"          # 结束原因
    metadata: Dict[str, Any] = None      # 元数据

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseLLMProvider(ABC):
    """
    LLM 提供商抽象基类

    所有 LLM 提供商必须继承此类并实现抽象方法
    """

    def __init__(self, api_key: str, base_url: str = ""):
        """
        初始化提供商

        Args:
            api_key: API 密钥
            base_url: API 基础 URL
        """
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """
        生成文本

        Args:
            request: LLM 请求

        Returns:
            LLM 响应

        Raises:
            ProviderError: 提供商错误
        """
        pass

    @abstractmethod
    def generate_batch(
        self,
        requests: List[LLMRequest],
    ) -> List[LLMResponse]:
        """
        批量生成文本

        Args:
            requests: LLM 请求列表

        Returns:
            LLM 响应列表
        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表

        Returns:
            模型名称列表
        """
        pass

    @abstractmethod
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        获取模型信息

        Args:
            model: 模型名称

        Returns:
            模型信息字典
        """
        pass

    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            是否健康
        """
        try:
            # 简单的测试请求
            test_request = LLMRequest(prompt="test", max_tokens=10)
            response = self.generate(test_request)
            return bool(response.content)
        except Exception:
            return False


class ProviderError(Exception):
    """提供商错误"""
    pass
```

---

## 🔧 提供商实现

### 1. 通义千问提供商

```python
"""
通义千问 Qwen 3 提供商
支持 Qwen 3 Plus / Max / Flash 等模型
"""

from typing import List, Dict, Any
import httpx
from ..base_LLM_provider import BaseLLMProvider, LLMRequest, LLMResponse, ProviderError


class QwenProvider(BaseLLMProvider):
    """
    通义千问提供商

    API 文档: https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope
    """

    # 可用模型列表
    MODELS = {
        "qwen-plus": {
            "name": "Qwen 3 Plus",
            "description": "综合最佳模型",
            "max_tokens": 8000,
            "context_length": 32000,
        },
        "qwen3-max": {
            "name": "Qwen 3 Max",
            "description": "最强性能模型",
            "max_tokens": 8000,
            "context_length": 128000,
        },
        "qwen-flash": {
            "name": "Qwen Flash",
            "description": "超快响应模型",
            "max_tokens": 6000,
            "context_length": 32000,
        },
        "qwq-plus": {
            "name": "QwQ Plus",
            "description": "推理能力模型",
            "max_tokens": 32768,
            "context_length": 32768,
        },
    }

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    ):
        """
        初始化提供商

        Args:
            api_key: API 密钥
            base_url: API 基础 URL
        """
        super().__init__(api_key, base_url)
        self.http_client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    def _get_model_name(self, model: str) -> str:
        """获取模型实际名称"""
        if model == "default":
            return "qwen-plus"
        if model in self.MODELS:
            return model
        raise ValueError(f"Unknown model: {model}")

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        生成文本

        Args:
            request: LLM 请求

        Returns:
            LLM 响应
        """
        model = self._get_model_name(request.model)

        # 构建消息
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        # 调用 API
        try:
            response = await self.http_client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                },
            )

            data = response.json()

            # 解析响应
            if "error" in data:
                raise ProviderError(data["error"]["message"])

            choice = data["choices"][0]
            content = choice["message"]["content"]

            return LLMResponse(
                content=content,
                model=model,
                tokens_used=data.get("usage", {}).get("total_tokens", 0),
                finish_reason=choice.get("finish_reason", "stop"),
            )

        except httpx.HTTPStatusError as e:
            raise ProviderError(f"HTTP 错误: {e.response.status_code}")
        except Exception as e:
            raise ProviderError(f"生成失败: {str(e)}")

    async def generate_batch(
        self,
        requests: List[LLMRequest],
    ) -> List[LLMResponse]:
        """
        批量生成文本

        Args:
            requests: LLM 请求列表

        Returns:
            LLM 响应列表
        """
        responses = []
        for request in requests:
            response = await self.generate(request)
            responses.append(response)
        return responses

    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return list(self.MODELS.keys())

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """获取模型信息"""
        return self.MODELS.get(model, {})
```

### 2. Kimi 提供商

```python
"""
Kimi (月之暗面) 提供商
支持 Kimi 2.5
"""

from typing import List, Dict, Any
import httpx
from ..base_LLM_provider import BaseLLMProvider, LLMRequest, LLMResponse, ProviderError


class KimiProvider(BaseLLMProvider):
    """
    Kimi 提供商

    API 文档: https://platform.moonshot.cn/docs
    """

    MODELS = {
        "kimi-2.5": {
            "name": "Kimi 2.5",
            "description": "最新版本",
            "max_tokens": 4000,
            "context_length": 128000,
        },
    }

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.moonshot.cn/v1",
    ):
        super().__init__(api_key, base_url)
        self.http_client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """生成文本"""
        model = request.model if request.model != "default" else "kimi-2.5"

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        try:
            response = await self.http_client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                },
            )

            data = response.json()
            choice = data["choices"][0]

            return LLMResponse(
                content=choice["message"]["content"],
                model=model,
                tokens_used=data.get("usage", {}).get("total_tokens", 0),
                finish_reason=choice.get("finish_reason", "stop"),
            )

        except Exception as e:
            raise ProviderError(f"生成失败: {str(e)}")

    async def generate_batch(
        self,
        requests: List[LLMRequest],
    ) -> List[LLMResponse]:
        responses = []
        for request in requests:
            responses.append(await self.generate(request))
        return responses

    def get_available_models(self) -> List[str]:
        return list(self.MODELS.keys())

    def get_model_info(self, model: str) -> Dict[str, Any]:
        return self.MODELS.get(model, {})
```

### 3. GLM-5 提供商

```python
"""
智谱 GLM-5 提供商
"""

from typing import List, Dict, Any
import httpx
from ..base_LLM_provider import BaseLLMProvider, LLMRequest, LLMResponse, ProviderError


class GLM5Provider(BaseLLMProvider):
    """智谱 GLM-5 提供商"""

    MODELS = {
        "glm-5": {
            "name": "GLM-5",
            "description": "正式版",
            "max_tokens": 8000,
            "context_length": 128000,
        },
    }

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://open.bigmodel.cn/api/paas/v4/",
    ):
        super().__init__(api_key, base_url)
        self.http_client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """生成文本"""
        model = request.model if request.model != "default" else "glm-5"

        try:
            response = await self.http_client.post(
                f"{self.base_url}chat/completions",
                json={
                    "model": model,
                    "messages": [
                        {"role": "user", "content": request.prompt},
                    ],
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                },
            )

            data = response.json()
            choice = data["choices"][0]

            return LLMResponse(
                content=choice["message"]["content"],
                model=model,
                tokens_used=data.get("usage", {}).get("total_tokens", 0),
            )

        except Exception as e:
            raise ProviderError(f"生成失败: {str(e)}")

    async def generate_batch(self, requests: List[LLMRequest]) -> List[LLMResponse]:
        return [await self.generate(req) for req in requests]

    def get_available_models(self) -> List[str]:
        return list(self.MODELS.keys())

    def get_model_info(self, model: str) -> Dict[str, Any]:
        return self.MODELS.get(model, {})
```

---

## 🎮 LLM 管理器

### LLMManager

```python
"""
LLM 管理器
统一管理所有 LLM 提供商，支持自动切换和负载均衡
"""

from typing import Dict, Optional, List, Any
from enum import Enum

from .base_LLM_provider import (
    BaseLLMProvider,
    LLMRequest,
    LLMResponse,
    ProviderError,
)
from .providers.qwen import QwenProvider
from .providers.kimi import KimiProvider
from .providers.glm5 import GLM5Provider
from .providers.openai import OpenAIProvider


class ProviderType(Enum):
    """提供商类型"""
    QWEN = "qwen"
    KIMI = "kimi"
    GLM5 = "glm5"
    OPENAI = "openai"
    LOCAL = "local"


class LLMManager:
    """
    LLM 管理器

    功能:
    1. 统一接口访问所有提供商
    2. 自动切换失败提供商
    3. 负载均衡（可选）
    4. 配置驱动
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化管理器

        Args:
            config: 配置字典
        """
        self.config = config
        self.providers: Dict[ProviderType, BaseLLMProvider] = {}
        self._default_provider: Optional[ProviderType] = None

        # 初始化提供商
        self._init_providers()

    def _init_providers(self):
        """初始化所有提供商"""
        # 通义千问
        if self.config.get("qwen", {}).get("api_key"):
            qwen_config = self.config["qwen"]
            self.providers[ProviderType.QWEN] = QwenProvider(
                api_key=qwen_config["api_key"],
                base_url=qwen_config.get("base_url", ""),
            )

        # Kimi
        if self.config.get("kimi", {}).get("api_key"):
            kimi_config = self.config["kimi"]
            self.providers[ProviderType.KIMI] = KimiProvider(
                api_key=kimi_config["api_key"],
                base_url=kimi_config.get("base_url", ""),
            )

        # GLM-5
        if self.config.get("glm5", {}).get("api_key"):
            glm5_config = self.config["glm5"]
            self.providers[ProviderType.GLM5] = GLM5Provider(
                api_key=glm5_config["api_key"],
                base_url=glm5_config.get("base_url", ""),
            )

        # OpenAI
        if self.config.get("openai", {}).get("api_key"):
            openai_config = self.config["openai"]
            self.providers[ProviderType.OPENAI] = OpenAIProvider(
                api_key=openai_config["api_key"],
                base_url=openai_config.get("base_url", ""),
            )

        # 设置默认提供商
        default_name = self.config.get("default_provider", "qwen")
        try:
            self._default_provider = ProviderType(default_name)
        except ValueError:
            if self.providers:
                self._default_provider = list(self.providers.keys())[0]

    async def generate(
        self,
        request: LLMRequest,
        provider: Optional[ProviderType] = None,
    ) -> LLMResponse:
        """
        生成文本

        Args:
            request: LLM 请求
            provider: 指定提供商（可选）

        Returns:
            LLM 响应
        """
        # 确定使用的提供商
        if provider and provider in self.providers:
            active_provider = self.providers[provider]
        else:
            provider = self._default_provider
            if not provider:
                raise ProviderError("没有可用的提供商")
            active_provider = self.providers[provider]

        try:
            return await active_provider.generate(request)

        except ProviderError as e:
            # 自动切换到下一个可用的提供商
            print(f"提供商 {provider.value} 失败，尝试切换...")
            return await self._try_fallback(request, exclude=[provider])

    async def _try_fallback(
        self,
        request: LLMRequest,
        exclude: List[ProviderType],
    ) -> LLMResponse:
        """尝试备用提供商"""
        for provider_type, provider in self.providers.items():
            if provider_type not in exclude:
                try:
                    return await provider.generate(request)
                except ProviderError:
                    continue

        raise ProviderError("所有提供商均失败")

    def get_provider(self, provider_type: ProviderType) -> BaseLLMProvider:
        """获取指定提供商"""
        if provider_type not in self.providers:
            raise ValueError(f"提供商 {provider_type} 不可用")
        return self.providers[provider_type]

    def get_available_providers(self) -> List[ProviderType]:
        """获取可用的提供商列表"""
        return list(self.providers.keys())

    def health_check(self) -> Dict[ProviderType, bool]:
        """健康检查所有提供商"""
        results = {}
        for provider_type, provider in self.providers.items():
            results[provider_type] = provider.health_check()
        return results
```

---

## ⚙️ 配置管理

### LLM 配置文件

**文件**: `config/llm.yaml`

```yaml
# LLM 配置

# 默认提供商
default_provider: qwen  # qwen | kimi | glm5 | openai | local

# 通义千问
qwen:
  api_key: ${QWEN_API_KEY}  # 从环境变量读取
  base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
  model: qwen-plus
  max_tokens: 2000
  temperature: 0.7

# Kimi
kimi:
  api_key: ${KIMI_API_KEY}
  base_url: https://api.moonshot.cn/v1
  model: kimi-2.5
  max_tokens: 2000
  temperature: 0.7

# GLM-5
glm5:
  api_key: ${GLM5_API_KEY}
  base_url: https://open.bigmodel.cn/api/paas/v4/
  model: glm-5
  max_tokens: 2000
  temperature: 0.7

# OpenAI (可选)
openai:
  api_key: ${OPENAI_API_KEY}
  base_url: https://api.openai.com/v1
  model: gpt-4
  max_tokens: 2000
  temperature: 0.7
```

---

## 📝 使用示例

### 更新 ScriptGenerator

```python
"""
更新后的文案生成器
使用 LLM Manager 而不是直接依赖 OpenAI
"""

from .llm_manager import LLMManager, ProviderType
from .base_LLM_provider import LLMRequest, LLMResponse
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ScriptConfig:
    """文案生成配置"""
    style: str = "commentary"
    tone: str = "neutral"
    target_duration: float = 60.0
    provider: Optional[str] = None  # 指定提供商


class ScriptGenerator:
    """
    AI 文案生成器

    现在支持多提供商自动切换
    """

    def __init__(
        self,
        llm_manager: Optional[LLMManager] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化生成器

        Args:
            llm_manager: LLM 管理器（可选）
            config: 配置字典
        """
        if llm_manager:
            self.llm_manager = llm_manager
        elif config:
            self.llm_manager = LLMManager(config)
        else:
            from .config import load_llm_config
            self.llm_manager = LLMManager(load_llm_config())

    async def generate(
        self,
        topic: str,
        config: Optional[ScriptConfig] = None,
    ) -> LLMResponse:
        """
        生成文案

        Args:
            topic: 主题
            config: 配置

        Returns:
            LLM 响应
        """
        config = config or ScriptConfig()

        # 构建请求
        request = LLMRequest(
            prompt=self._build_prompt(topic, config),
            system_prompt=self._get_system_prompt(config.style),
            model=config.get("model", "default"),
            max_tokens=int(config.target_duration * 3),  # 约3字/秒
            temperature=0.7,
        )

        # 确定提供商
        provider = None
        if config.provider:
            try:
                provider = ProviderType(config.provider)
            except ValueError:
                pass

        # 生成
        response = await self.llm_manager.generate(request, provider=provider)

        return response

    def _build_prompt(self, topic: str, config: ScriptConfig) -> str:
        """构建用户提示词"""
        return f"请为以下主题生成视频文案：\n\n{topic}"

    def _get_system_prompt(self, style: str) -> str:
        """获取系统提示词"""
        prompts = {
            "commentary": "你是一位专业的视频解说文案撰写者。",
            "monologue": "你是一位擅长写第一人称独白的文案作者。",
            "viral": "你是一位爆款短视频文案高手。",
        }
        return prompts.get(style, "你是一位文案撰写者。")
```

---

## 🧪 测试计划

### 单元测试

```python
"""
LLM 提供商单元测试
"""

import pytest
from app.services.ai.providers.qwen import QwenProvider
from app.services.ai.base_LLM_provider import LLMRequest


@pytest.mark.asyncio
async def test_qwen_provider():
    """测试通义千问提供商"""
    provider = QwenProvider(api_key="test-key")
    request = LLMRequest(prompt="测试", max_tokens=10)

    # 使用 Mock
    # response = await provider.generate(request)
    # assert response.content
```

### 集成测试

```python
"""
LLM 管理器集成测试
"""

from app.services.ai.llm_manager import LLMManager


async def test_llm_manager():
    """测试 LLM 管理器"""
    config = {
        "default_provider": "qwen",
        "qwen": {"api_key": "test-key"},
    }

    manager = LLMManager(config)

    # 测试生成
    # response = await manager.generate(test_request)
    # assert response.content
```

---

## 📊 迁移计划

### 立即执行

1. [ ] 创建 `app/services/ai/base_LLM_provider.py`
2. [ ] 实现通义千问提供商
3. [ ] 实现 Kimi 提供商
4. [ ] 实现 GLM-5 提供商
5. [ ] 创建 LLM 管理器
6. [ ] 更新 ScriptGenerator 使用新架构

### 后续工作

1. [ ] 添加百度文心提供商
2. [ ] 添加本地模型支持（Ollama 等）
3. [ ] 实现负载均衡
4. [ ] 添加缓存层
5. [ ] 完善单元测试

---

## 🎉 总结

### 关键改进

1. **抽象接口**: 统一的 LLMProvider 接口
2. **多提供商**: 支持国产主流 LLM
3. **自动切换**: 失败自动切换备用提供商
4. **配置驱动**: YAML 配置管理
5. **易于测试**: 支持 Mock 和 Stub

### 下一步

- [ ] 实施编码
- [ ] 编写单元测试
- [ ] 更新现有代码集成新架构

---

**文档状态**: ✅ 完成
**实施状态**: ⏳ 待执行
