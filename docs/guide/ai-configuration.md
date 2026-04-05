---
title: AI 配置指南
description: 在 Narrafiilm 中配置 AI 提供商（DeepSeek / OpenAI / Claude / Qwen 等）的方法。
---

# AI 配置指南

Narrafiilm 支持多个 AI 提供商，按用途分为视频理解和解说生成两个维度。

---

## 快速配置

只需配置 **DeepSeek API Key** 即可完整运行。获取地址：[platform.deepseek.com](https://platform.deepseek.com)

```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

在应用内：设置 → AI 配置 → 粘贴 Key → 保存 → 连接测试

---

## 视频理解模型（场景分析）

| 提供商 | 模型 | 说明 |
|--------|------|------|
| **阿里云百炼** | Qwen2.5-VL (7B/72B) | 默认，视频理解 SOTA |
| **OpenAI** | GPT-4.1 | 多模态，能力强 |
| **Google** | Gemini 2.5 Flash | 性价比高 |

### 阿里云百炼配置

```env
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx
```

在应用中设置 → AI 配置 → 阿里云百炼 → 填入 Key

### OpenAI 配置

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4.1
```

---

## 解说生成模型（文稿撰写）

| 提供商 | 模型 | 说明 |
|--------|------|------|
| **DeepSeek** | DeepSeek-V3.2 | 默认，性价比最高 |
| **OpenAI** | GPT-4.1 | 最强通用能力 |
| **Anthropic** | Claude Opus 4.6 | 超长上下文 |
| **阿里云** | Qwen2.5-Max | 中文优化 |

### DeepSeek 配置（默认）

```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
DEEPSEEK_MODEL=deepseek-chat
```

### Claude 配置

```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-opus-4.6-20260219
```

---

## 配音合成

| 引擎 | 配置 | 说明 |
|------|------|------|
| **Edge-TTS**（默认） | 无需 Key | 免费，多音色 |
| **F5-TTS** | 需安装 | 零样本克隆 |
| **OpenAI TTS** | 需 OpenAI Key | 超自然语音 |

Edge-TTS 无需任何配置，开箱即用。

---

## 环境变量方式

所有配置也可以通过 `.env` 文件管理（放在项目根目录，已加入 .gitignore）：

```env
# DeepSeek（解说生成，默认）
DEEPSEEK_API_KEY=sk-xxx

# 阿里云百炼（视频理解）
DASHSCOPE_API_KEY=sk-xxx

# OpenAI（可选全栈）
OPENAI_API_KEY=sk-xxx

# 配音引擎：edge-tts（默认）/ f5-tts / openai
TTS_ENGINE=edge-tts
```

---

## 多提供商组合建议

| 场景 | 视频理解 | 解说生成 | 成本 |
|------|----------|----------|------|
| **免费入门** | Qwen2.5-VL（本地） | DeepSeek-V3.2 | 接近零 |
| **日常创作** | Qwen2.5-VL（API） | DeepSeek-V3.2 | 低 |
| **最高质量** | GPT-4.1 | Claude Opus 4.6 | 高 |
