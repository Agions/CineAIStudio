---
title: AI 模型配置
description: Narrafiilm 支持的所有 AI 模型一览，包括文本、语音合成和视觉理解模型。
---

# AI 模型配置

Narrafiilm 支持多种 AI 模型，以下为 2026 年 4 月最新版本。

## 支持的模型列表

### 文本生成模型

| 提供商 | 模型 | 上下文 | 特点 | 推荐场景 |
|--------|------|--------|------|----------|
| **OpenAI** | GPT-4.1 | 1M | 最强通用能力 | 剧情分析、脚本生成 |
| **Anthropic** | Claude Opus 4.5 | 200K | 长上下文、安全性高 | 长文本分析、代码 |
| **Google** | Gemini 3 Pro | 1M+ | 超长上下文、多模态 | 视频理解、超长文本 |
| **DeepSeek** | DeepSeek-V3.2 | 128K | 性价比高 | 翻译、日常任务 |
| **阿里云** | Qwen3-Max | 128K | 中文优化、推理强 | 中文创作 |
| **智谱** | GLM-4 | 128K | 中文优化 | 中文创作 |
| **Kimi** | Kimi 2 | 200K+ | 超长上下文 | 长文本分析 |
| **豆包** | Doubao Pro | 128K | 字节出品 | 日常任务 |
| **腾讯** | Hunyuan Pro | 128K | 腾讯出品 | 企业场景 |
| **Ollama** | 本地模型 | 可配置 | 完全私有 | 隐私敏感 |

### 语音合成

| 提供商 | 质量 | 费用 | 特点 |
|--------|------|------|------|
| **Edge TTS** | ⭐⭐⭐⭐⭐ | 免费 | 多音色、中英文 |
| **F5-TTS v0.1** | ⭐⭐⭐⭐ | 免费 | 零样本音色克隆（2026.03） |
| **OpenAI TTS** | ⭐⭐⭐⭐⭐ | 付费 | 超自然语音 |

### 视觉理解

| 提供商 | 模型 | 特点 |
|--------|------|------|
| **Qwen** | Qwen3-VL (235B MoE / 32B) | 国产最强，2025.09 开源 |
| **OpenAI** | GPT-4.1 | 多模态最强 |
| **Anthropic** | Claude Opus 4.5 | 安全性高 |
| **Google** | Gemini 3 Pro | 超长上下文 |

## 快速配置

### 1. OpenAI

```bash
# 设置 API Key
export OPENAI_API_KEY="sk-..."

# 或在应用中配置
AI_PROVIDER=openai
OPENAI_MODEL=gpt-4.1
```

### 2. Anthropic Claude

```bash
export ANTHROPIC_API_KEY="sk-ant-..."

AI_PROVIDER=claude
CLAUDE_MODEL=claude-opus-4.5
```

### 3. Google Gemini

```bash
export GOOGLE_API_KEY="..."

AI_PROVIDER=gemini
GEMINI_MODEL=gemini-3-pro
```

### 4. 国产模型

```bash
# 通义千问
export DASHSCOPE_API_KEY="..."
AI_PROVIDER=qwen
QWEN_MODEL=qwen3-max

# 智谱 GLM
export ZHIPU_API_KEY="..."
AI_PROVIDER=glm
GLM_MODEL=glm-4

# Kimi
export MOONSHOT_API_KEY="..."
AI_PROVIDER=kimi
KIMI_MODEL=kimi-2
```

## 模型选择建议

### 按场景

| 场景 | 推荐模型 | 原因 |
|------|----------|------|
| 电影解说 | GPT-4.1 / Claude Opus 4.5 | 强大的叙事分析能力 |
| 快速翻译 | DeepSeek-V3.2 | 性价比高，速度快 |
| 长视频分析 | Claude Opus 4.5 / Kimi 2 | 超长上下文 |
| 中文内容 | Qwen3-Max / GLM-4 | 中文优化 |
| 隐私敏感 | Ollama 本地 | 完全私有 |

### 按预算

| 预算 | 推荐组合 |
|------|----------|
| 免费 | Edge TTS + Ollama 本地 |
| 低预算 | DeepSeek-V3.2 + Edge TTS |
| 中预算 | GPT-4.1 + Edge TTS |
| 高预算 | Claude Opus 4.5 + OpenAI TTS |

## API Key 安全

::: warning 安全提示
- 不要将 API Key 提交到代码仓库
- 使用环境变量或系统 Keychain 存储
- 定期轮换 API Key
:::

## 更多配置

详细的模型参数配置请参考 [配置参考](/config)。

## 更新日志

- **2026.04**: 更新至 GPT-4.1、Claude Opus 4.5、Gemini 3 Pro、Qwen3-VL、DeepSeek-V3.2
- **2026.03**: 新增 F5-TTS v0.1 音色克隆支持
- **2026.01**: 全面支持国产模型
