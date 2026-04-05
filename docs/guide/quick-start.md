---
title: 5 分钟快速开始
description: 最简化的 Narrafiilm 上手指引，5 分钟内完成从安装到第一个 AI 视频创作。
---

# 5 分钟快速开始

> ⏱️ 如果你已经熟悉视频编辑工具，可以直接跳到 [安装 Narrafiilm](#快速安装)。

本指南将带你用 **5 分钟** 完成 Narrafiilm 的安装与首次 AI 视频创作。

---

## 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10+ / macOS 11+ / Ubuntu 20.04+ |
| 内存 | 8 GB（推荐 16 GB） |
| 显卡 | NVIDIA 4GB（可选，GPU 加速） |
| 网络 | 互联网连接（用于 AI 功能） |

---

## 快速安装

### 方式一：下载安装包（推荐）

1. 打开 [GitHub Releases](https://github.com/Agions/Narrafiilm/releases/latest)
2. 下载对应平台的最新版本：

| 平台 | 安装包 |
|------|--------|
| Windows | `Narrafiilm-Setup-x.x.x.exe` |
| macOS | `Narrafiilm-x.x.x.dmg` |
| Linux | `Narrafiilm-x.x.x.AppImage` |

3. 运行安装程序，按提示完成安装

### 方式二：Homebrew（macOS / Linux）

```bash
brew install videoforge
```

### 方式三：源码安装

```bash
git clone https://github.com/Agions/Narrafiilm.git
cd Narrafiilm
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app/main.py
```

---

## 配置 AI（3 步搞定）

### 第 1 步：获取 API Key

Narrafiilm 支持多种 AI 提供商，只需配置一个即可使用全部功能：

| 提供商 | 获取地址 | 特点 |
|--------|----------|------|
| **DeepSeek** | [platform.deepseek.com](https://platform.deepseek.com) | 🏆 性价比最高 |
| **OpenAI** | [platform.openai.com](https://platform.openai.com) | 能力最强 |
| **通义千问** | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com) | 中文优化 |
| **Kimi** | [platform.moonshot.cn](https://platform.moonshot.cn) | 超长上下文 |
| **Ollama**（本地） | [ollama.ai](https://ollama.ai) | 🔒 完全免费离线 |

### 第 2 步：配置 API Key

启动 Narrafiilm 后，进入 **设置 → AI 配置**，粘贴你的 API Key。

或直接编辑 `.env` 文件（项目根目录）：

```env
# 选择一个你申请的 AI 提供商
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx

# 语音合成（免费，使用微软 Edge TTS）
TIKTOKEN_API_KEY=
```

### 第 3 步：验证配置

进入 **设置 → AI 配置**，点击 **连接测试**。看到 ✅ 就说明配置成功。

---

## 创建第一个 AI 视频（3 步）

### 1️⃣ 新建项目

- 启动应用 → 点击 **新建项目**
- 选择项目保存位置
- 选择创作模式

### 2️⃣ 导入素材

- 点击 **导入素材** 或直接将视频文件拖入窗口
- 支持格式：`MP4`, `MOV`, `AVI`, `MKV`, `WebM`

### 3️⃣ 开始创作

选择你的创作模式：

| 模式 | 适用场景 | 创作效果 |
|------|----------|----------|
| 🎬 **剧情分析** | 电影解说、Vlog 整理 | 智能分析叙事结构 |
| 🎙️ **AI 解说** | 纪录片、产品介绍 | AI 生成旁白 + 字幕 |
| 🎵 **智能混剪** | 音乐视频、节奏剪辑 | BPM 自动卡点 |
| 🎭 **AI 独白** | 情感视频、电影感 Vlog | 电影级字幕 |
| 📱 **短视频切片** | 直播切片、社交媒体 | 一键高光片段 |
| 🌐 **视频翻译** | 内容出海、本地化 | 100+ 语言支持 |

点击 **开始创作**，等待 AI 处理完成，预览 → 导出。

---

## 常见问题

### ❓ 提示 "FFmpeg not found"

Narrafiilm 需要 FFmpeg 处理视频。安装方法：

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows
# 下载 https://ffmpeg.org/download.html 并添加到 PATH
```

### ❓ AI 功能报错 401

API Key 配置有误。进入 **设置 → AI 配置**，重新粘贴正确的 Key。

### ❓ 处理速度很慢

- 确认电脑有足够的内存（建议 16GB+）
- 使用 NVIDIA 显卡可加速处理
- 关闭其他占用资源的程序

---

## 下一步

- 🎬 [功能详细介绍](/features) — 了解每个 AI 模式的使用技巧
- 🤖 [AI 模型配置](/ai-models) — 切换和优化 AI 提供商
- ❓ [常见问题](/faq) — 更多常见问题解答
- 📖 [详细安装指南](/guide/installation) — 包含各平台完整安装步骤

::: tip 💡 小技巧
首次使用建议从 **AI 解说** 或 **短视频切片** 开始，这两个模式对硬件要求最低，效果也最直观。
:::
