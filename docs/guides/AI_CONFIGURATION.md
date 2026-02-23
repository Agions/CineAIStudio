# AI 服务配置指南

本指南将帮助你配置 ClipFlow 的 AI 服务，包括各种 LLM 提供商的 API 密钥设置。

## 📋 目录

- [支持的 AI 服务](#支持的-ai-服务)
- [配置方法](#配置方法)
- [各提供商配置](#各提供商配置)
- [测试配置](#测试配置)
- [常见问题](#常见问题)

---

## 🤖 支持的 AI 服务

ClipFlow 支持以下 AI 服务提供商（2026年2月最新版本）：

| 提供商 | 模型 | 功能 | 费用 |
|--------|------|------|------|
| **OpenAI** | GPT-5.2, GPT-5.3-Codex | 文本生成、视觉理解、配音 | 付费 |
| **Anthropic** | Claude Opus 4.6, Sonnet 4.6 | 文本生成、长文本处理 | 付费 |
| **Google** | Gemini 3 Flash, 3.1 Pro | 文本生成、视觉理解 | 付费 |
| **阿里云** | Qwen 3.5 | 文本生成、视觉理解 | 付费 |
| **智谱AI** | GLM-5 | 文本生成 | 付费 |
| **月之暗面** | Kimi K2.5 | 文本生成、长文本 | 付费 |
| **Edge TTS** | - | 语音合成 | 免费 |
| **Ollama** | 本地模型 | 文本生成 | 免费 |

---

## ⚙️ 配置方法

### 方法 1: 环境变量配置（推荐）

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的 API 密钥：
```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_BASE_URL=https://api.anthropic.com

# Google Gemini
GOOGLE_API_KEY=AIza...
GOOGLE_BASE_URL=https://generativelanguage.googleapis.com

# 阿里云通义千问
QWEN_API_KEY=sk-...
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 智谱 GLM
GLM_API_KEY=...
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/

# 月之暗面 Kimi
KIMI_API_KEY=...
KIMI_BASE_URL=https://api.moonshot.cn/v1
```

### 方法 2: 图形界面配置

1. 启动 ClipFlow
2. 点击左侧导航栏的 **⚙️ 设置**
3. 选择 **AI 模型配置**
4. 填入各提供商的 API 密钥
5. 点击 **测试连接** 验证配置
6. 点击 **保存** 应用配置

---

## 🔑 各提供商配置

### OpenAI (GPT-5.2)

**获取 API 密钥**:
1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 注册/登录账号
3. 进入 API Keys 页面
4. 创建新的 API 密钥

**配置示例**:
```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-5.2  # 或 gpt-5.3-codex
```

**推荐用途**: 脚本生成、视觉分析、AI 配音

---

### Anthropic Claude (Opus 4.6)

**获取 API 密钥**:
1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 注册/登录账号
3. 创建 API 密钥

**配置示例**:
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
ANTHROPIC_BASE_URL=https://api.anthropic.com
ANTHROPIC_MODEL=claude-opus-4-6  # 或 claude-sonnet-4-6
```

**推荐用途**: 长文本脚本生成、复杂场景分析

---

### Google Gemini (3 Flash)

**获取 API 密钥**:
1. 访问 [Google AI Studio](https://makersuite.google.com/)
2. 创建项目
3. 获取 API 密钥

**配置示例**:
```bash
GOOGLE_API_KEY=AIzaxxxxxxxxxxxxx
GOOGLE_BASE_URL=https://generativelanguage.googleapis.com
GOOGLE_MODEL=gemini-3-flash  # 或 gemini-3.1-pro
```

**推荐用途**: 视频直传分析、快速脚本生成

---

### 阿里云通义千问 (Qwen 3.5)

**获取 API 密钥**:
1. 访问 [阿里云模型服务](https://dashscope.aliyun.com/)
2. 开通服务
3. 创建 API Key

**配置示例**:
```bash
QWEN_API_KEY=sk-xxxxxxxxxxxxx
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen3.5  # 或 qwen-plus
```

**推荐用途**: 中文脚本生成、视觉分析

---

### 智谱 GLM-5

**获取 API 密钥**:
1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册/登录
3. 创建 API Key

**配置示例**:
```bash
GLM_API_KEY=xxxxxxxxxxxxx
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
GLM_MODEL=glm-5
```

**推荐用途**: 中文脚本生成

---

### 月之暗面 Kimi (K2.5)

**获取 API 密钥**:
1. 访问 [Moonshot AI](https://platform.moonshot.cn/)
2. 注册/登录
3. 创建 API Key

**配置示例**:
```bash
KIMI_API_KEY=xxxxxxxxxxxxx
KIMI_BASE_URL=https://api.moonshot.cn/v1
KIMI_MODEL=kimi-k2.5
```

**推荐用途**: 长文本处理、多模态分析

---

### Edge TTS (免费)

**无需配置**，开箱即用！

**支持的中文声音**:
- `zh-CN-XiaoxiaoNeural` - 女声，亲切
- `zh-CN-YunxiNeural` - 男声，沉稳
- `zh-CN-YunyangNeural` - 男声，新闻播报
- `zh-CN-XiaoyiNeural` - 女声，温柔

**推荐用途**: 免费 AI 配音

---

### Ollama (本地模型)

**安装 Ollama**:
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# 下载安装包: https://ollama.com/download
```

**拉取模型**:
```bash
# 推荐模型
ollama pull llama3.2
ollama pull qwen2.5
ollama pull deepseek-r1
```

**配置示例**:
```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

**推荐用途**: 离线使用、隐私保护

---

## ✅ 测试配置

### 命令行测试

```bash
# 测试所有配置
python -m app.utils.test_ai_config

# 测试特定提供商
python -m app.utils.test_ai_config --provider openai
```

### 图形界面测试

1. 打开 **设置 → AI 模型配置**
2. 点击每个提供商旁边的 **测试连接** 按钮
3. 查看测试结果：
   - ✅ 绿色：配置正确，连接成功
   - ❌ 红色：配置错误或连接失败
   - ⚠️ 黄色：配置正确但有警告

---

## 🎯 推荐配置方案

### 方案 1: 全功能配置（推荐）

```bash
# 主力模型 - 脚本生成
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.2

# 视觉分析
GOOGLE_API_KEY=AIza...
GOOGLE_MODEL=gemini-3-flash

# 免费配音
# Edge TTS 无需配置
```

**优点**: 功能完整，性能最佳  
**成本**: 约 $20-50/月

### 方案 2: 经济配置

```bash
# 中文模型
QWEN_API_KEY=sk-...
QWEN_MODEL=qwen3.5

# 免费配音
# Edge TTS 无需配置
```

**优点**: 成本低，中文效果好  
**成本**: 约 $10-20/月

### 方案 3: 完全免费

```bash
# 本地模型
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5

# 免费配音
# Edge TTS 无需配置
```

**优点**: 完全免费，隐私保护  
**缺点**: 需要本地 GPU，速度较慢

---

## ❓ 常见问题

### Q1: API 密钥无效怎么办？

**A**: 
1. 检查密钥是否正确复制（无多余空格）
2. 确认密钥未过期
3. 检查账户余额是否充足
4. 验证 API 权限是否开启

### Q2: 连接超时怎么办？

**A**:
1. 检查网络连接
2. 尝试使用代理
3. 更换 BASE_URL（如使用国内镜像）
4. 增加超时时间设置

### Q3: 如何切换默认模型？

**A**:
在设置页面选择 **默认 AI 模型**，或在 `.env` 中设置：
```bash
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-5.2
```

### Q4: 可以同时使用多个提供商吗？

**A**: 
可以！ClipFlow 支持多提供商配置，会自动选择最佳模型或进行 fallback。

### Q5: 本地模型性能如何？

**A**:
- **优点**: 免费、隐私、离线可用
- **缺点**: 需要 GPU（推荐 8GB+ 显存）
- **速度**: 比云端慢 3-5 倍
- **质量**: 接近 GPT-3.5 水平

---

## 🔒 安全建议

1. **不要提交 API 密钥到 Git**
   - `.env` 文件已在 `.gitignore` 中
   - 使用环境变量或密钥管理工具

2. **定期轮换密钥**
   - 建议每 3-6 个月更换一次
   - 发现泄露立即撤销

3. **设置使用限额**
   - 在提供商后台设置月度限额
   - 避免意外超支

4. **监控使用情况**
   - 定期检查 API 使用量
   - 关注异常调用

---

## 📚 相关文档

- [AI 视频创作指南](AI_VIDEO_GUIDE.md)
- [模型更新日志](../ai/MODEL_UPDATES_2026_02.md)
- [故障排除](TROUBLESHOOT.md)

---

**更新日期**: 2026-02-22  
**版本**: 3.0.0  
**维护者**: ClipFlow 团队
