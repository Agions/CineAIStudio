# AI 模型配置

VideoForge 支持多种 AI 模型，2026年3月最新版本全面更新。

## 支持的模型列表

### 文本生成模型

| 提供商 | 模型 | 上下文 | 特点 | 推荐场景 |
|--------|------|--------|------|----------|
| **OpenAI** | GPT-5.4 | 128K | 最强通用能力 | 剧情分析、脚本生成 |
| **Anthropic** | Claude Sonnet 4.6 | 200K | 长上下文、安全性高 | 长文本分析、代码 |
| **Google** | Gemini 3.1 Pro | 1M | 超长上下文、多模态 | 视频理解、超长文本 |
| **DeepSeek** | V3.2 | 128K | 性价比高 | 翻译、日常任务 |
| **阿里云** | Qwen 2.5-Max | 128K | 中文优化 | 中文创作 |
| **智谱** | GLM-5 | 128K | 中文优化 | 中文创作 |
| **Kimi** | K2.5 | 200K+ | 超长上下文 | 长文本分析 |
| **豆包** | Doubao Pro | 128K | 字节出品 | 日常任务 |
| **腾讯** | Hunyuan Pro | 128K | 腾讯出品 | 企业场景 |
| **Ollama** | 本地模型 | 可配置 | 完全私有 | 隐私敏感 |

### 语音合成

| 提供商 | 质量 | 费用 | 特点 |
|--------|------|------|------|
| **Edge TTS** | ⭐⭐⭐⭐⭐ | 免费 | 多音色、中英文 |
| **OpenAI TTS** | ⭐⭐⭐⭐⭐ | 付费 | 超自然语音 |

### 视觉理解

| 提供商 | 模型 | 特点 |
|--------|------|------|
| GPT-4o | 顶级 | 多模态最强 |
| Claude Sonnet 4.6 | 顶级 | 安全性高 |
| Gemini 3.1 Pro | 强 | 超长上下文 |
| Qwen VL | 优 | 国产优选 |
| Kimi VL | 优 | 国产优选 |

## 快速配置

### 1. OpenAI

```bash
# 设置 API Key
export OPENAI_API_KEY="sk-..."

# 或在应用中配置
AI_PROVIDER=openai
OPENAI_MODEL=gpt-5.4
```

### 2. Anthropic Claude

```bash
export ANTHROPIC_API_KEY="sk-ant-..."

AI_PROVIDER=claude
CLAUDE_MODEL=claude-sonnet-4.6
```

### 3. Google Gemini

```bash
export GOOGLE_API_KEY="..."

AI_PROVIDER=gemini
GEMINI_MODEL=gemini-3.1-pro
```

### 4. 国产模型

```bash
# 通义千问
export DASHSCOPE_API_KEY="..."
AI_PROVIDER=qwen
QWEN_MODEL=qwen2.5-max

# 智谱 GLM
export ZHIPU_API_KEY="..."
AI_PROVIDER=glm
GLM_MODEL=glm-5

# Kimi
export MOONSHOT_API_KEY="..."
AI_PROVIDER=kimi
KIMI_MODEL=kimi-k2.5
```

## 模型选择建议

### 按场景

| 场景 | 推荐模型 | 原因 |
|------|----------|------|
| 电影解说 | GPT-5.4 / Claude Sonnet 4.6 | 强大的叙事分析能力 |
| 快速翻译 | DeepSeek V3.2 | 性价比高，速度快 |
| 长视频分析 | Claude Sonnet 4.6 / Kimi K2.5 | 超长上下文 |
| 中文内容 | Qwen 2.5-Max / GLM-5 | 中文优化 |
| 隐私敏感 | Ollama 本地 | 完全私有 |

### 按预算

| 预算 | 推荐组合 |
|------|----------|
| 免费 | Edge TTS + Ollama 本地 |
| 低预算 | DeepSeek V3.2 + Edge TTS |
| 中预算 | GPT-5.4 + Edge TTS |
| 高预算 | Claude Sonnet 4.6 + OpenAI TTS |

## API Key 安全

::: warning 安全提示
- 不要将 API Key 提交到代码仓库
- 使用环境变量或系统 Keychain 存储
- 定期轮换 API Key
:::

## 更多配置

详细的模型参数配置请参考 [配置参考](/config)。

## 更新日志

- **2026.03**: 更新至 GPT-5.4、Claude Sonnet 4.6、Gemini 3.1 Pro
- **2026.02**: 新增 Kimi K2.5、GLM-5 支持
- **2026.01**: 全面支持国产模型
