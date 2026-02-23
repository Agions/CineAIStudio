# 🎬 CineFlow - AI 视频创作桌面应用

<p align="center">
  <img src="https://img.shields.io/badge/version-3.0.0-blue.svg" alt="Version" />
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License" />
  <img src="https://img.shields.io/badge/Python-3.9+-3776ab?logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/PyQt6-6.0+-41cd52" alt="PyQt6" />
  <img src="https://img.shields.io/badge/FFmpeg-required-007808" alt="FFmpeg" />
  <img src="https://img.shields.io/badge/platform-macOS%20|%20Windows-lightgrey" alt="Platform" />
</p>

---

## ✨ 简介

CineFlow 是专业的 AI 视频创作桌面应用，基于 **PyQt6** 构建原生界面，提供从画面理解到成片导出的完整创作能力。

| 版本 | 特点 |
|------|------|
| 🖥️ **Desktop** | Python + PyQt6 + FFmpeg，本地处理，更强大 |
| 🌐 **Web** | React + TypeScript + Tauri，浏览器端创作 |

---

## 🎯 核心功能

### 5 大创作模式

| 模式 | 说明 |
|------|------|
| 🎙️ **AI 视频解说** | 画面分析 → 生成解说文案 → AI 配音 → 动态字幕 |
| 🎵 **AI 视频混剪** | 多素材 → 节拍匹配 → 自动转场 → 音画同步 |
| 🎭 **AI 第一人称独白** | 画面情感分析 → 情感独白 → 电影字幕 |
| 📺 **短剧切片** | 识别高能片段 → 自动切片 → 加字幕 |
| 🛍️ **产品推广** | 画面分析 → 卖点提取 → 推广文案 → 配音 |

### 3 步快速创作

```
素材导入 → AI 智能编辑 → 一键导出
```

---

## 🤖 AI 能力

### 支持的 LLM

| 提供商 | 模型 | 文本 | 视觉 | 配音 |
|--------|------|:---:|:---:|:---:|
| **OpenAI** | GPT-5 | ✅ | ✅ | ✅ |
| **Anthropic** | Claude Opus 4.6 | ✅ | ✅ | ❌ |
| **Google** | Gemini 3 | ✅ | ✅ | ❌ |
| **阿里云** | Qwen 3.5 | ✅ | ✅ | ❌ |
| **DeepSeek** | DeepSeek Chat | ✅ | ❌ | ❌ |
| **智谱AI** | GLM-5 | ✅ | ❌ | ❌ |
| **月之暗面** | Kimi K2.5 | ✅ | ✅ | ❌ |
| **本地** | Ollama | ✅ | ❌ | ❌ |
| **Edge TTS** | 微软语音 | ❌ | ❌ | ✅ |

### 特色能力

- 🎥 **视频级理解** — Gemini 3 视频直传 + 多帧连续分析
- 🎵 **音画同步** — librosa 节拍检测 + 4 种同步策略
- 🎙️ **AI 配音** — Edge TTS（免费）/ OpenAI TTS

---

## 📤 导出格式

支持 7 种导出格式，兼容主流剪辑软件：

- 📱 **剪映** (Draft JSON)
- 🎬 **Premiere** (XML)
- 🍎 **Final Cut** (FCPXML)
- 🎞️ **达芬奇** (DaVinci)
- 📄 **SRT** / **ASS** 字幕
- 🎥 **MP4** 直接导出

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- FFmpeg（需加入 PATH）
- macOS 10.15+ / Windows 10+

### 安装

```bash
# 1. 克隆项目
git clone https://github.com/Agions/cine-flow.git
cd cine-flow

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 AI 服务
cp .env.example .env
# 编辑 .env，填入 API Key

# 4. 运行
python main.py
```

---

## 📁 项目结构

```
cine-flow/
├── app/
│   ├── core/          # 核心模块
│   ├── services/      # 服务层
│   │   ├── ai/        # AI 服务
│   │   ├── audio/     # 音频处理
│   │   ├── video/     # 视频处理
│   │   └── export/    # 导出引擎
│   └── ui/            # 界面层
├── docs/              # 文档
├── examples/          # 示例
├── resources/         # 资源文件
└── tests/             # 测试
```

---

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| GUI | PyQt6 6.0+ |
| 视频 | FFmpeg, OpenCV |
| 音频 | librosa |
| AI | OpenAI, Anthropic, Google, 阿里云, 智谱, 月之暗面 |
| 配音 | Edge TTS, OpenAI TTS |

---

## 📄 许可证

MIT License - 详见 [LICENSE](./LICENSE)

---

## ⭐️ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Agions/cine-flow&type=Date)](https://star-history.com/#Agions/cine-flow&Date)

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/Agions">Agions</a>
</p>
