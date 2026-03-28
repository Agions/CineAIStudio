<div align="center">

# 🎬 VideoForge

**AI-Powered Video Creation Desktop App · AI 驱动的视频创作桌面应用**

*从素材到成片，全程 AI 自动化 · From raw footage to final cut, fully AI-automated*

[![GitHub stars](https://img.shields.io/github/stars/Agions/VideoForge?style=for-the-badge&logo=github&color=FFD700)](https://github.com/Agions/VideoForge/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Agions/VideoForge?style=for-the-badge&logo=github&color=4CAF50)](https://github.com/Agions/VideoForge/forks)
[![GitHub issues](https://img.shields.io/github/issues/VideoForge?style=for-the-badge&color=FF6B6B)](https://github.com/Agions/VideoForge/issues)
[![GitHub release](https://img.shields.io/github/v/release/Agions/VideoForge?style=for-the-badge&color=blue)](https://github.com/Agions/VideoForge/releases)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

### ✨ 一句话介绍

> VideoForge 是一款**AI 驱动的视频创作工具**，支持剧情分析、智能剪辑、解说配音、多素材混剪，让视频制作变得前所未有的简单。

### 🎯 核心特性

| 特性 | 说明 |
|------|:----:|
| 🤖 **AI 剧情分析** | 智能分析视频叙事结构、情感曲线、高光时刻 |
| 🎬 **剧情剪辑模式** | 基于故事弧线自动生成剪辑点建议 |
| 🎙️ **AI 解说配音** | 一键生成专业旁白，支持多种音色 |
| 🎵 **智能混剪** | BPM 节拍检测，自动卡点混剪 |
| 🎭 **AI 独白** | 画面情感分析，生成电影级内心独白 |
| 📤 **全格式导出** | 剪映/PR/FCPXML/DaVinci/RAW |

---

## 🚀 快速开始

### 下载安装包（推荐）

| 平台 | 下载地址 |
|------|----------|
| macOS | [VideoForge-x.x.x.dmg](https://github.com/Agions/VideoForge/releases) |
| Windows | [VideoForge-x.x.x-setup.exe](https://github.com/Agions/VideoForge/releases) |

### 源码运行

```bash
# 1. 克隆项目
git clone https://github.com/Agions/VideoForge.git
cd VideoForge

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置 API Key
cp .env.example .env
# 编辑 .env，填入 AI 服务密钥

# 5. 启动
python main.py
```

> 💡 **只需要一个 API Key 即可开始** · Edge TTS 配音完全免费

---

## 🎨 剪辑模式

VideoForge 提供四种 AI 剪辑模式，适应不同创作需求：

### 1️⃣ 剧情分析模式 🆕

```
视频输入 → AI 剧情分析 → 故事结构识别 → 智能剪辑建议
```

**核心能力：**
- 📊 分析叙事结构（起承转合）
- 🎭 识别情感曲线和关键时刻
- ✂️ 生成基于故事的剪辑点
- 🎬 支持叙事/高光/预告片三种风格

**适用场景：** 电影解说、故事类短视频、Vlog 整理

### 2️⃣ AI 解说模式

```
视频输入 → 场景分析 → 文案生成 → 配音合成 → 字幕匹配
```

**核心能力：**
- 🎙️ 多音色 AI 配音（支持中文/英文/方言）
- 📝 自动生成解说文案
- 🔄 音画自动同步
- 🎨 多种解说风格可选

**适用场景：** 科普视频、知识分享、产品介绍

### 3️⃣ 智能混剪模式

```
多素材 → BPM 检测 → 节奏分析 → 自动卡点 → 成片导出
```

**核心能力：**
- 🎵 节拍精准检测（librosa 音频分析）
- 🔀 智能转场匹配
- ⚡ 并行处理多素材
- 📋 批量导出

**适用场景：** 音乐剪辑、舞蹈视频、节奏类内容

### 4️⃣ AI 独白模式

```
视频输入 → 情感分析 → 独白生成 → 电影级字幕
```

**核心能力：**
- 😊 画面情感识别
- 💭 AI 内心独白生成
- 🎬 电影感字幕设计
- 🎭 多种情感风格

**适用场景：** Vlog 内心独白、纪录片旁白、电影感视频

---

## 🤖 支持的 AI 模型

| 提供商 | 模型 | 文本 | 视觉 | 配音 |
|--------|------|:----:|:----:|:----:|
| **OpenAI** | GPT-4o / GPT-5 | ✅ | ✅ | ✅ TTS |
| **Anthropic** | Claude Sonnet 4.5 | ✅ | ✅ | — |
| **Google** | Gemini 3.1 Flash/Pro | ✅ | ✅ | — |
| **阿里云** | Qwen 3.5 | ✅ | ✅ | — |
| **DeepSeek** | R1 / V3.2 | ✅ | — | — |
| **智谱 AI** | GLM-5 | ✅ | — | — |
| **月之暗面** | Kimi K2.5 | ✅ | ✅ | — |
| **字节豆包** | Doubao Pro | ✅ | — | — |
| **腾讯混元** | Hunyuan | ✅ | ✅ | — |
| **本地** | Ollama（任意模型） | ✅ | — | — |
| **微软** | Edge TTS | — | — | ✅ 免费 |

---

## 📤 导出格式

| 格式 | 说明 | 兼容性 |
|------|------|--------|
| 📱 **剪映草稿** | Draft JSON | 剪映 App/专业版 |
| 🎬 **Premiere Pro** | .prproj | Adobe Premiere |
| ✂️ **Final Cut Pro** | .fcpxml | Final Cut Pro X |
| 🎞️ **DaVinci Resolve** | .drp | DaVinci Resolve |
| 📹 **EDL** | CMX 3600 | 通用剪辑软件 |
| 🎥 **RAW Video** | MP4/MOV | 全平台 |
| 📝 **字幕** | SRT / ASS | 通用 |

---

## 🏗️ 项目架构

```
VideoForge/
├── app/
│   ├── core/                 # 核心模块（应用、配置、日志、事件）
│   ├── services/
│   │   ├── ai/              # AI 服务
│   │   │   ├── providers/   # LLM 提供商
│   │   │   ├── story_analyzer.py   # 🆕 剧情分析
│   │   │   ├── scene_analyzer.py   # 场景分析
│   │   │   ├── script_generator.py # 文案生成
│   │   │   └── voice_generator.py  # 语音合成
│   │   ├── video/           # 视频处理
│   │   ├── audio/           # 音频处理
│   │   └── export/          # 导出引擎
│   ├── ui/                  # PySide6 界面层
│   └── plugins/             # 插件系统
├── tests/                   # 测试套件
├── docs/                    # 完整文档
├── scripts/                 # 构建脚本
└── resources/              # 资源文件
```

---

## 🛠️ 技术栈

| 类别 | 技术选型 |
|------|----------|
| **GUI 框架** | PySide6 (LGPL) |
| **视频处理** | FFmpeg + OpenCV |
| **音频分析** | librosa |
| **AI 接入** | OpenAI SDK + 各厂商 API |
| **语音合成** | Edge TTS / OpenAI TTS |
| **构建打包** | PyInstaller |

---

## 📖 文档

| 文档 | 说明 |
|------|------|
| [快速开始](docs/getting-started.md) | 5 分钟快速上手 |
| [功能指南](docs/features.md) | 全部功能详解 |
| [AI 配置](docs/guides/AI_CONFIGURATION.md) | API Key 配置教程 |
| [常见问题](docs/faq.md) | FAQ 故障排查 |
| [开发指南](docs/guides/INSTALL.md) | 开发者环境搭建 |

---

## 🗺️ Roadmap

| 版本 | 计划 |
|------|------|
| v4.0 | 🆕 剧情分析剪辑模式正式上线 |
| v4.0 | Web 版本（浏览器直接使用） |
| v4.1 | 批量处理模式 |
| v4.2 | 自定义 AI 提示词模板 |
| v4.3 | 视频字幕翻译（多语言） |
| v4.5 | 插件系统 |

---

## 🤝 贡献

欢迎提交 PR 和 Issue！

```bash
# Fork 后克隆
git clone https://github.com/YOUR_USERNAME/VideoForge.git
cd VideoForge

# 创建分支
git checkout -b feature/amazing-feature

# 提交
git commit -m 'feat: add amazing feature'

# 推送
git push origin feature/amazing-feature
```

---

## 📄 许可证

[MIT License](LICENSE) · Copyright (c) 2025-2026 [Agions](https://github.com/Agions)

---

## ⭐ 如果对你有帮助，请给一个 Star

[![Star History](https://api.star-history.com/svg?repos=Agions/VideoForge&type=Date)](https://star-history.com/#Agions/VideoForge&Date)

---

<div align="center">
  <sub>Made with ❤️ by <a href="https://github.com/Agions">Agions</a></sub>
</div>

</div>
