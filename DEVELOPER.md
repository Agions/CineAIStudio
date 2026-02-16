# CineFlow AI 开发指南

> 面向开发者的快速上手指南

---

## 📦 开发环境设置

### 1. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 API 密钥（开发模式）

```bash
# 设置环境变量（本地开发方便测试）
export QWEN_API_KEY="your-api-key"
export KIMI_API_KEY="your-api-key"
export GLM5_API_KEY="your-api-key"

# 或在 config/llm.yaml 中配置
```

### 3. 运行应用

```bash
python3 app/main.py
# 或
cineflow-ai
```

---

## 🧪 测试

### 运行所有测试

```bash
# 基础测试（不需要 API 密钥）
pytest tests/ -v

# 完整测试（包含集成测试，需要 API 密钥）
pytest tests/ -v -m "integration"
```

### 运行特定测试

```bash
# 版本测试
pytest tests/test_version.py -v

# LLM 提供商测试
pytest tests/test_llm_providers.py -v

# 文案生成器测试
pytest tests/test_script_generator.py -v

# 集成测试
pytest tests/test_integration.py -v -m "integration"
```

### 测试覆盖率

```bash
# 生成覆盖率报告
pytest --cov=app --cov-report=html tests/

# 查看报告
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
```

---

## 📐 代码结构

```
CineFlow/
├── app/                    # 应用代码
│   ├── core/              # 核心模块
│   │   ├── models/        # 数据模型 (LLM, Script 等)
│   │   ├── config.py      # 配置管理
│   │   └── logger.py      # 日志管理
│   ├── services/          # 服务层
│   │   ├── ai/           # AI 服务 (LLM, 文案生成)
│   │   │   ├── llm_manager.py       # LLM 管理器
│   │   │   ├── script_generator.py  # 文案生成器
│   │   │   ├── base_LLM_provider.py # LLM 抽象接口
│   │   │   └── providers/            # LLM 提供商
│   │   │       ├── qwen.py
│   │   │       ├── kimi.py
│   │   │       └── glm5.py
│   │   ├── video/        # 视频服务
│   │   └── audio/        # 音频服务
│   └── utils/            # 工具模块
│       └── version.py    # 版本管理
├── config/               # 配置文件
├── tests/                # 测试代码
├── docs/                 # 文档
├── pyproject.toml        # 项目配置 (Python 3.12+)
├── requirements.txt       # 依赖列表
└── main.py               # 应用入口
```

---

## 🚀 添加新的 LLM 提供商

### 步骤 1: 创建提供商类

在 `app/services/ai/providers/` 创建新文件：

```python
# app/services/ai/providers/custom_provider.py

from app.services.ai.base_LLM_provider import BaseLLMProvider
from app.core.models.llm_models import LLMRequest, LLMResponse

class CustomProvider(BaseLLMProvider):
    """自定义 LLM 提供商"""

    def __init__(self, api_key: str, base_url: str = None):
        super().__init__(api_key, base_url)
        self.models = {
            "custom-model": {
                "name": "custom-model",
                "max_tokens": 4096,
                "supports_vision": False
            }
        }
        self.default_model = "custom-model"

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """实现补全逻辑"""
        # 调用 API
        # 返回 LLMResponse
        pass

    async def check_health(self) -> bool:
        """健康检查"""
        # 检查 API 可用性
        # 返回 True/False
        pass
```

### 步骤 2: 在 LLMManager 中注册

编辑 `config/llm.yaml`:

```yaml
LLM:
  custom:
    enabled: true
    api_key: "your-api-key"
    base_url: "https://api.custom.com/v1"
    model: "custom-model"
```

### 步骤 3: 添加测试

创建 `tests/test_custom_provider.py`:

```python
from app.services.ai.providers.custom_provider import CustomProvider
from app.core.models.llm_models import LLMRequest

def test_custom_provider_init():
    provider = CustomProvider(api_key="test")
    assert "custom-model" in provider.models
    assert provider.default_model == "custom-model"

def test_custom_provider_request():
    provider = CustomProvider(api_key="test")
    request = LLMRequest(
        messages=[{"role": "user", "content": "Hello"}],
        model="custom-model"
    )
    response = await provider.complete(request)
    assert response.success is True
```

### 步骤 4: 更新文档

更新 `NATIVE-LLM-INTEGRATION.md` 和 `INSTALL.md`。

---

## 🔄 Git 工作流

### 分支策略

```
main (主分支，稳定版本)
├── develop (开发分支)
└── feature/* (功能分支)
```

### 提交规范

```
类型(范围): 简短描述

[可选的详细说明]

[可选的关联 Issues]

类型:
- ✨ feature: 新功能
- 🐛 fix: 修复 Bug
- 📝 docs: 文档更新
- 🎨 style: 代码格式
- ♻️ refactor: 重构
- ✅ test: 测试相关
- ⚡ perf: 性能优化
```

### 提交示例

```bash
git add .
git commit -m "✨ 添加自定义 LLM 提供商支持

- 实现 CustomProvider
- 添加配置选项
- 增加单元测试

Fixes #123"
```

### 推送到 GitHub

```bash
git push origin main
# 或使用 SSH 配置
GIT_SSH_COMMAND="ssh -i ~/.ssh/man_pipeline" git push origin main
```

---

## 📋 待办事项

### v2.0.0 正式版

- [ ] 完成集成测试
- [ ] 添加更多测试用例
- [ ] 性能优化
- [ ] 更 CHANGELOG.md
- [ ] 发布 v2.0.0 正式版

### v2.1.0

- [ ] 本地 LLM 支持 (Ollama)
- [ ] 更多语音风格
- [ ] 批量处理功能

---

## 🆘 常见问题

### Q: 测试失败怎么办？

**A**: 检查以下几点：

1. 是否配置了 API 密钥？
```bash
export QWEN_API_KEY="your-key"
```

2. 是否安装了所有依赖？
```bash
pip install -r requirements.txt
```

3. 是否启动了虚拟环境？
```bash
source .venv/bin/activate
```

### Q: 如何调试 LLM 调用？

**A**: 启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Q: 如何贡献代码？

**A**:

1. Fork 项目
2. 创建功能分支
3. 编写测试
4. 提交 Pull Request

---

## 📚 参考文档

- [INSTALL.md](INSTALL.md) - 安装指南
- [TECH-STACK.md](TECH-STACK.md) - 技术栈说明
- [NATIVE-LLM-INTEGRATION.md](NATIVE-LLM-INTEGRATION.md) - LLM 集成设计
- [VERSION-UNIFICATION.md](VERSION-UNIFICATION.md) - 版本管理策略

---

**最后更新**: 2026-02-14
**版本**: v2.0.0-rc.1
