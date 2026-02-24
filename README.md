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

CineFlow 是专业的 **AI 驱动** 视频创作桌面应用，区别于传统手动剪辑软件（如 Premiere、Final Cut），CineFlow 通过 AI 实现自动化创作。

基于 **PyQt6** 构建原生桌面界面，提供从视频理解到成片导出的完整创作能力。

---

## 🎯 核心功能

### 3 大 AI 创作模式

| 模式 | 说明 | 工作流 |
|------|------|--------|
| 🎙️ **AI 视频解说** | 原视频 + AI 配音 + 动态字幕 | 场景分析 → 文案生成 → AI 配音 → 字幕合成 |
| 🎵 **AI 视频混剪** | 多素材 + 节拍匹配 + 自动转场 | 素材分析 → BPM 检测 → 智能剪辑 → 转场合成 |
| 🎭 **AI 第一人称独白** | 画面情感 + 情感独白 + 电影字幕 | 情感分析 → 独白生成 → 配音合成 → 电影字幕 |

### 创作流程

```
素材导入 → AI 分析 → 模式选择 → 脚本生成 → 脚本编辑 → 时间轴编排 → AI 配音 → 预览 → 导出
```

---

## 🤖 AI 能力

### 支持的 LLM

| 提供商 | 模型 | 文本 | 视觉 | 配音 |
|--------|------|:---:|:---:|:---:|
| **OpenAI** | GPT-5 | ✅ | ✅ | ✅ |
| **Anthropic** | Claude Opus 4.6 | ✅ | ✅ | ❌ |
| **Google** | Gemini 3 | ✅ | ✅ | ❌ |
| **阿里云** | Qwen 3.5 VL | ✅ | ✅ | ❌ |
| **DeepSeek** | DeepSeek Chat | ✅ | ❌ | ❌ |
| **智谱AI** | GLM-5 | ✅ | ❌ | ❌ |
| **月之暗面** | Kimi K2.5 | ✅ | ✅ | ❌ |
| **本地** | Ollama | ✅ | ❌ | ❌ |
| **Edge TTS** | 微软语音 | ❌ | ❌ | ✅ |

### 核心 AI 能力

| 能力 | 说明 | 技术 |
|------|------|------|
| 🎬 **场景理解** | 视频内容分析、场景分割、关键帧提取 | FFmpeg + OpenCV |
| 📝 **文案生成** | 多风格文案创作（解说/独白/旁白） | LLM (Qwen/Kimi/GLM/GPT) |
| 🎙️ **语音合成** | AI 配音，多种声音风格 | Edge TTS / OpenAI TTS |
| 📄 **字幕生成** | 动态字幕、多样式风格 | 自研字幕引擎 |
| 🎵 **音画同步** | BPM 检测、智能对齐 | librosa 节拍检测 |

---

## 📤 导出格式

| 格式 | 文件类型 | 兼容软件 |
|------|----------|----------|
| 📱 **剪映** | Draft JSON | 剪映 |
| 🎬 **Premiere** | XML | Adobe Premiere Pro |
| 🍎 **Final Cut** | FCPXML | Apple Final Cut Pro |
| 🎞️ **DaVinci** | DaVinci Resolve | DaVinci Resolve |
| 🎥 **MP4** | H.264/H.265 | 所有播放器 |
| 📄 **SRT/ASS** | 字幕文件 | 播放器/编辑软件 |

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- FFmpeg（需加入系统 PATH）
- macOS 10.15+ / Windows 10+

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/Agions/cine-flow.git
cd cine-flow

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置 API 密钥
cp .env.example .env
# 编辑 .env，填入所需的 API Key

# 5. 运行应用
python main.py
```

---

## 📁 项目结构

```
cine-flow/
├── app/
│   ├── core/                 # 核心模块
│   │   ├── application.py    # 应用入口
│   │   ├── project_manager.py    # 项目管理
│   │   ├── config_manager.py     # 配置管理
│   │   └── ...
│   ├── services/             # 业务服务
│   │   ├── ai/              # AI 服务
│   │   │   ├── scene_analyzer.py     # 场景分析
│   │   │   ├── script_generator.py   # 文案生成
│   │   │   ├── voice_generator.py   # 语音合成
│   │   │   └── ...
│   │   ├── video/           # 视频处理
│   │   │   ├── commentary_maker.py  # AI 解说
│   │   │   ├── mashup_maker.py      # AI 混剪
│   │   │   └── monologue_maker.py   # AI 独白
│   │   ├── audio/           # 音频处理
│   │   │   ├── beat_detector.py     # 节拍检测
│   │   │   └── sync_engine.py       # 音画同步
│   │   └── export/          # 导出引擎
│   │       ├── jianying_exporter.py  # 剪映导出
│   │       ├── premiere_exporter.py # PR 导出
│   │       └── ...
│   └── ui/                  # 界面层
│       ├── components/      # UI 组件
│       ├── theme/          # 主题样式
│       └── main/           # 主界面
├── resources/               # 资源文件
├── tests/                  # 测试
└── docs/                   # 文档
```

---

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| **GUI 框架** | PyQt6 6.0+ |
| **视频处理** | FFmpeg, OpenCV |
| **音频处理** | librosa, soundfile |
| **AI 大模型** | OpenAI, Anthropic, Google, 阿里云, 智谱, 月之暗面 |
| **语音合成** | Edge TTS, OpenAI TTS |
| **构建工具** | PyInstaller, Setuptools |

---

## 📖 更多文档

- [AI 架构详解](./AI_ARCHITECTURE.md) - AI 能力详细技术文档
- [贡献指南](./CONTRIBUTING.md) - 如何贡献代码

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
