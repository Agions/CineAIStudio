# VideoForge

<div align="center">

<img src="docs/public/logo.svg" alt="VideoForge" width="200" />

### AI-Powered Video Creation Desktop Application

**从素材到成片，AI 全流程自动化处理**

[![Stars](https://img.shields.io/github/stars/Agions/VideoForge?style=for-the-badge)](https://github.com/Agions/VideoForge/stargazers)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Qt](https://img.shields.io/badge/Qt-6.5+-41?style=for-the-badge&logo=qt)](https://www.qt.io/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-FF6B6B?style=for-the-badge&logo=linux&logoColor=white)](https://github.com/Agions/VideoForge)

**免费 · 开源 · 跨平台** 支持 Windows / macOS / Linux

</div>

---

## 🎯 一句话介绍

> **VideoForge** 是一款**AI 驱动的专业智能视频剪辑工具**，支持剧情分析、智能剪辑、多素材混剪、字幕生成、AI 配音等全链路 AI 剪辑能力，让专业视频制作变得简单。

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 🎬 **剧情分析** | AI 分析视频叙事结构、情感曲线 |
| 🎙️ **AI 解说** | 多音色 AI 配音，音画自动同步 |
| 🎵 **智能混剪** | BPM 节拍检测，自动卡点拼接 |
| 🎭 **AI 独白** | 画面情感分析，电影级字幕 |
| 📱 **短视频切片** | 长视频一键转高光短片段 |
| 🌐 **视频翻译** | 100+语言翻译，唇形同步 |

## 🚀 快速开始

### 安装

**方式一：下载安装包**

访问 [Releases](https://github.com/Agions/VideoForge/releases) 下载对应平台的安装包。

**方式二：从源码构建**

```bash
git clone https://github.com/Agions/VideoForge.git
cd VideoForge
pip install -r requirements.txt
python app/main.py
```

### 配置 AI

```bash
# 设置 API Key
export OPENAI_API_KEY="sk-your-key"

# 或使用免费的 Ollama
export OLLAMA_URL="http://localhost:11434"
```

详细配置请参考 [AI 模型配置](docs/ai-models.md)。

## 🤖 支持的 AI 模型 (2026年3月最新)

| 提供商 | 推荐模型 | 场景 |
|--------|----------|------|
| OpenAI | GPT-5.4 | 剧情分析、脚本生成 |
| Anthropic | Claude Sonnet 4.6 | 长文本分析、代码 |
| Google | Gemini 3.1 Pro | 多模态理解 |
| DeepSeek | V3.2 | 翻译、日常任务 |
| 阿里云 | Qwen 2.5-Max | 中文内容创作 |
| Kimi | K2.5 | 长文本分析 |

## 📂 项目结构

```
VideoForge/
├── app/
│   ├── main.py              # 应用入口
│   ├── ui/                  # Qt UI 组件
│   ├── services/            # 核心服务
│   │   ├── ai/             # AI 服务
│   │   └── video/          # 视频处理
│   └── utils/              # 工具函数
├── docs/                    # 项目文档
├── resources/              # 资源文件
└── tests/                  # 测试
```

## 📖 文档

| 文档 | 说明 |
|------|------|
| [快速开始](docs/guide/getting-started.md) | 5 分钟上手 |
| [功能介绍](docs/features.md) | 全部功能详解 |
| [AI 模型配置](docs/ai-models.md) | AI 服务配置 |
| [安装配置](docs/guide/installation.md) | 详细安装指南 |
| [常见问题](docs/faq.md) | FAQ 故障排查 |

完整文档：https://docs.videoforge.ai

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| UI 框架 | PySide6 (Qt) |
| 编程语言 | Python 3.10+ |
| 视频处理 | FFmpeg + OpenCV |
| AI 接入 | OpenAI SDK + 多厂商 API |
| 状态管理 | 自研事件系统 |

## 🐛 反馈问题

如发现问题或建议，请提交 [GitHub Issues](https://github.com/Agions/VideoForge/issues)。

## 📄 许可证

[MIT License](LICENSE) · Copyright © 2025-2026 [Agions](https://github.com/Agions)

---

<div align="center">

⭐ 如果这个项目对您有帮助，请给一个 Star

</div>
