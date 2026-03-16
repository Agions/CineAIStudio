<div align="center">

<!-- 建议录制一个 30 秒的 Demo GIF 放在这里，展示 AI 视频解说/混剪效果 -->
<!-- <img src="docs/images/demo.gif" alt="ClipFlowCut Demo" width="100%"> -->

# 🎬 ClipFlowCut

**AI-Powered Video Creation Desktop App · AI 驱动的视频创作桌面应用**

*从素材到成片，全程 AI 自动化 · From raw footage to final cut, fully AI-automated*

<p align="center">
  <a href="https://github.com/Agions/ClipFlowCut/stargazers"><img src="https://img.shields.io/github/stars/Agions/ClipFlowCut?style=for-the-badge&logo=github&color=FFD700" alt="Stars"></a>
  <a href="https://github.com/Agions/ClipFlowCut/forks"><img src="https://img.shields.io/github/forks/Agions/ClipFlowCut?style=for-the-badge&logo=github&color=4CAF50" alt="Forks"></a>
  <a href="https://github.com/Agions/ClipFlowCut/issues"><img src="https://img.shields.io/github/issues/Agions/ClipFlowCut?style=for-the-badge&color=FF6B6B" alt="Issues"></a>
  <a href="https://github.com/Agions/ClipFlowCut/releases"><img src="https://img.shields.io/github/v/release/Agions/ClipFlowCut?style=for-the-badge&color=blue" alt="Release"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/PyQt6-6.0+-41cd52?style=flat-square" alt="PyQt6">
  <img src="https://img.shields.io/badge/Platform-macOS%20|%20Windows-lightgrey?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/FFmpeg-Required-007808?style=flat-square" alt="FFmpeg">
</p>

<p align="center">
  <a href="README.md">中文</a> · <a href="docs/README_EN.md">English</a> · <a href="https://agions.github.io/ClipFlowCut">文档</a> · <a href="https://github.com/Agions/ClipFlowCut/releases">下载</a> · <a href="https://github.com/Agions/ClipFlowCut/issues/new?template=bug_report.md">报告 Bug</a> · <a href="https://github.com/Agions/ClipFlowCut/issues/new?template=feature_request.md">功能建议</a>
</p>

</div>

---

## 🤔 为什么选择 ClipFlowCut？

> 传统视频剪辑需要你手动完成每一步。ClipFlowCut 让 AI 替你完成。

| ClipFlowCut 能做什么 | |
|------|:---:|
| 🤖 AI 自动解说配音，一键生成专业旁白 | ✅ |
| 🔀 自由切换 9+ 主流 LLM，不锁定单一服务商 | ✅ |
| 📤 导出全格式，兼容主流专业工作流 | ✅ |
| 🏠 支持本地 Ollama 私有部署，数据不出本机 | ✅ |
| 🆓 MIT 开源免费，无订阅无限制 | ✅ |
| 💻 跨平台桌面应用，macOS & Windows 原生体验 | ✅ |
| 🎵 AI 节拍自动对齐，卡点混剪零手动 | ✅ |

---

## ✨ 核心功能

### 🎙️ AI 视频解说
> 上传视频 → AI 分析场景 → 自动生成解说文案 → AI 配音 → 动态字幕合成

一键将任意视频变成专业解说视频，支持多种风格（科普、娱乐、纪录片...）

### 🎵 AI 视频混剪
> 多素材导入 → BPM 节拍检测 → 智能剪辑点 → 自动转场 → 成片导出

卡点混剪从此不再需要手动对齐，AI 自动完成节拍匹配

### 🎭 AI 第一人称独白
> 画面情感分析 → 情感独白生成 → AI 配音 → 电影级字幕

让你的 Vlog 拥有电影质感的内心独白

---

## 🤖 支持的 AI 模型

| 提供商 | 模型 | 文本 | 视觉 | 配音 |
|--------|------|:----:|:----:|:----:|
| **OpenAI** | GPT-4o / GPT-5 | ✅ | ✅ | ✅ TTS |
| **Anthropic** | Claude Sonnet 4.5 | ✅ | ✅ | — |
| **Google** | Gemini 2.0 Flash | ✅ | ✅ | — |
| **阿里云** | Qwen 3.5 | ✅ | ✅ | — |
| **DeepSeek** | R1 / V3 | ✅ | — | — |
| **智谱 AI** | GLM-5 | ✅ | — | — |
| **月之暗面** | Kimi K2.5 | ✅ | ✅ | — |
| **本地** | Ollama（任意模型） | ✅ | — | — |
| **微软** | Edge TTS | — | — | ✅ 免费 |

---

## 📤 导出格式

一次创作，多端使用：

```
✅ 剪映草稿 (Draft JSON)   ✅ Adobe Premiere (XML)
✅ Final Cut Pro (FCPXML)  ✅ DaVinci Resolve
✅ MP4 (H.264/H.265)       ✅ SRT / ASS 字幕
```

---

## 🚀 快速开始

### 方式一：下载安装包（推荐）

前往 [Releases](https://github.com/Agions/ClipFlowCut/releases) 下载最新版本：
- macOS：`ClipFlowCut-x.x.x.dmg`
- Windows：`ClipFlowCut-x.x.x-setup.exe`

### 方式二：源码运行

**环境要求：** Python 3.9+ · FFmpeg · macOS 10.15+ / Windows 10+

```bash
# 1. 克隆项目
git clone https://github.com/Agions/ClipFlowCut.git
cd ClipFlowCut

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置 API Key
cp .env.example .env
# 编辑 .env，填入至少一个 AI 服务的 API Key

# 5. 启动
python main.py
```

> 💡 **只需要一个 API Key 即可开始使用**，Edge TTS 配音完全免费无需 Key

---

## 📸 截图预览

<!-- 建议添加以下截图：主界面、AI解说工作流、混剪界面、导出界面 -->
<!-- <img src="docs/images/screenshot-main.png" width="49%"> <img src="docs/images/screenshot-workflow.png" width="49%"> -->

> 📷 截图即将更新，欢迎提交你的使用截图！

---

## 🗺️ Roadmap

- [x] AI 视频解说（v1.0）
- [x] AI 视频混剪 + 节拍检测（v2.0）
- [x] AI 第一人称独白（v2.0）
- [x] 多 LLM 支持 + 国产模型（v2.0）
- [x] 专业格式导出（v3.0）
- [x] PyQt6 Fluent UI 重构（v3.0）
- [ ] 🔄 Web 版本（浏览器直接使用）
- [ ] 🔄 批量处理模式
- [ ] 🔄 自定义 AI 提示词模板市场
- [ ] 🔄 视频字幕翻译（多语言）
- [ ] 🔄 插件系统

---

## 🏗️ 项目结构

```
ClipFlowCut/
├── app/
│   ├── core/          # 核心模块（项目管理、配置）
│   ├── services/
│   │   ├── ai/        # AI 服务（场景分析、文案生成、语音合成）
│   │   ├── video/     # 视频处理（解说、混剪、独白）
│   │   ├── audio/     # 音频处理（节拍检测、音画同步）
│   │   └── export/    # 导出引擎（剪映/PR/FCPXML/DaVinci）
│   └── ui/            # PyQt6 界面层
├── tests/             # 测试套件
├── docs/              # 文档
└── resources/         # 资源文件
```

---

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| GUI 框架 | PyQt6 + PyQt6-Fluent-Widgets |
| 视频处理 | FFmpeg + OpenCV |
| 音频分析 | librosa（节拍检测） |
| AI 接入 | OpenAI SDK + 各厂商 API |
| 语音合成 | Edge TTS（免费）/ OpenAI TTS |
| 构建打包 | PyInstaller |

---

## 🤝 参与贡献

欢迎任何形式的贡献！无论是 Bug 修复、新功能、文档改进还是翻译。

👉 请先阅读 [贡献指南](CONTRIBUTING.md)

```bash
# Fork 后克隆你的仓库
git clone https://github.com/YOUR_USERNAME/ClipFlowCut.git

# 创建功能分支
git checkout -b feature/amazing-feature

# 提交更改
git commit -m 'feat: add amazing feature'

# 推送并创建 PR
git push origin feature/amazing-feature
```

---

## 📖 文档

- [快速开始](docs/getting-started.md)
- [功能指南](docs/features.md)
- [工作流程](docs/workflow.md)
- [常见问题](docs/faq.md)
- [更新日志](docs/CHANGELOG.md)
- [English README](docs/README_EN.md)

---

## 📄 许可证

[MIT License](LICENSE) © 2026 [Agions](https://github.com/Agions)

---

## ⭐ Star History

如果这个项目对你有帮助，请给一个 Star ⭐ 支持一下！

[![Star History Chart](https://api.star-history.com/svg?repos=Agions/ClipFlowCut&type=Date)](https://star-history.com/#Agions/ClipFlowCut&Date)

---

<div align="center">
  <sub>Made with ❤️ by <a href="https://github.com/Agions">Agions</a> · 如有问题欢迎 <a href="https://github.com/Agions/ClipFlowCut/issues">提 Issue</a></sub>
</div>
