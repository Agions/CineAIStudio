```
  ____ _ _       _____ _
 / ___| (_)_ __ |  ___| | _____      __
| |   | | | '_ \| |_  | |/ _ \ \ /\ / /
| |___| | | |_) |  _| | | (_) \ V  V /
 \____|_|_| .__/|_|   |_|\___/ \_/\_/
           |_|
```

<p align="center">
  <strong>ClipFlow  — AI 视频创作桌面客户端</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-3.0.0-blue.svg" alt="Version" />
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License" />
  <img src="https://img.shields.io/badge/Python-3.9+-3776ab?logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/PyQt6-6.0+-41cd52" alt="PyQt6" />
  <img src="https://img.shields.io/badge/FFmpeg-required-007808" alt="FFmpeg" />
  <img src="https://img.shields.io/badge/platform-macOS%20|%20Windows-lightgrey" alt="Platform" />
</p>

---

## 📖 简介

**ClipFlow Desktop** 是专业的 AI 视频创作桌面应用，基于 PyQt6 构建原生界面，提供从画面理解到成片导出的完整创作能力。

> 🔗 **Web 版本**: [ClipFlow Web](https://github.com/Agions/clip-flow) — React + TypeScript + Tauri  
> 🖥️ **桌面版本**: ClipFlow Desktop — Python + PyQt6 + FFmpeg（本地处理，更强大）  
> 📚 **完整文档**: [文档中心](docs/README.md) — 安装、使用、开发指南

### ✨ 核心优势

- 🎥 **视频级 AI 理解** — Gemini 3 视频直传 + 多帧连续分析 + 叙事结构识别
- 🎵 **音画同步引擎** — librosa 节拍检测 + 4种同步策略（踩点/乐句/能量/混合）
- 🎙️ **AI 配音内置** — Edge TTS（免费）/ OpenAI TTS，支持多种中文声音
- 📤 **专业导出** — 剪映 / Premiere / Final Cut / 达芬奇 / SRT / ASS / MP4
- 🖥️ **原生性能** — FFmpeg + OpenCV + GPU 加速，本地处理不依赖网络
- 🤖 **多模型支持** — 8家 AI 提供商，智能 fallback，2026年2月最新版本

---

## 🎬 五大创作模式

| 模式 | 说明 |
|------|------|
| 🎙️ **AI 视频解说** | 画面分析 → 生成解说文案 → AI 配音 → 动态字幕 |
| 🎵 **AI 视频混剪** | 多素材 → 节拍匹配 → 自动转场 → 音画同步 |
| 🎭 **AI 第一人称独白** | 画面情感分析 → 情感独白 → 电影字幕 |
| 📺 **短剧切片** | 识别高能片段 → 自动切片 → 加字幕 |
| 🛍️ **产品推广** | 画面分析 → 卖点提取 → 推广文案 → 配音 |

---

## 🔄 优化工作流（3步完成创作）

```
Step 1: 素材 + 模式 → Step 2: 智能编辑 → Step 3: 一键导出
```

> 💡 **工作流优化**: 从原来的8步简化到3步，减少63%的页面切换，AI分析后台进行不阻塞操作。  
> 📖 详见 [工作流程优化文档](docs/design/WORKFLOW_OPTIMIZATION.md)

### 详细工作流程

<details>
<summary>点击展开查看详细步骤</summary>

### Step 1: 📤 素材导入

| 项目 | 说明 |
|------|------|
| **输入** | 视频文件（MP4/MOV/AVI/MKV/WebM，无大小限制） |
| **处理** | FFmpeg 元数据提取、缩略图生成、多文件批量导入 |
| **输出** | 视频信息 + 预览缩略图 |

### Step 2: 🔍 AI 智能分析（后台进行）

| 项目 | 说明 |
|------|------|
| **输入** | 视频文件 |
| **处理** | 视频级理解（Gemini 3）/ 多帧视觉分析（GPT-5/Qwen 3.5 VL）/ 叙事结构识别 |
| **输出** | 场景列表、角色、情感弧线、高潮标记、内容摘要 |

### Step 3: 📋 创作模式选择

| 项目 | 说明 |
|------|------|
| **输入** | 视频分析结果 + 用户选择 |
| **处理** | 5种创作模式模板匹配 |
| **输出** | 创作配置（模式 + 风格 + 参数） |

### Step 4: 📝 AI 脚本生成

| 项目 | 说明 |
|------|------|
| **输入** | 视频分析 + 创作配置 |
| **处理** | 多模型调度生成脚本（支持 8 种 LLM），智能 fallback |
| **输出** | 结构化脚本（分段、时间码、情感标注） |

### Step 5: ✏️ 脚本编辑（实时预览）

| 项目 | 说明 |
|------|------|
| **输入** | AI 生成的脚本 |
| **处理** | 富文本编辑、段落调整、Undo/Redo、实时预览 |
| **输出** | 最终脚本 |

### Step 6: 🎬 时间轴编排

| 项目 | 说明 |
|------|------|
| **输入** | 脚本 + 视频素材 + 分析数据 |
| **处理** | 脚本-场景自动匹配、多轨时间轴、转场效果 |
| **输出** | 时间轴数据（视频轨/音频轨/字幕轨） |

### Step 7: 🔊 AI 配音 + 音画同步

| 项目 | 说明 |
|------|------|
| **输入** | 脚本文本 + 配音参数 + 音乐 |
| **处理** | TTS 语音合成（Edge/OpenAI）+ librosa 节拍检测 + 音画同步 |
| **输出** | 配音音轨 + BGM + 同步时间码 |

### Step 8: 📦 导出发布

| 项目 | 说明 |
|------|------|
| **输入** | 时间轴 + 音轨 + 字幕 + 导出设置 |
| **处理** | FFmpeg 编码（GPU 加速）、多格式导出 |
| **输出** | 剪映 JSON / Premiere XML / FCPXML / SRT / ASS / MP4 |

</details>

---

## 🧠 AI 能力矩阵（2026年2月最新）

### 支持的 LLM

| 提供商 | 最新模型 | 文本 | 视觉 | 配音 | 发布日期 |
|--------|---------|:---:|:---:|:---:|---------|
| **OpenAI** | GPT-5.2, GPT-5.3-Codex | ✅ | ✅ | ✅ | 2026-02 |
| **Anthropic** | Claude Opus 4.6, Sonnet 4.6 | ✅ | ✅ | ❌ | 2026-02-05 |
| **Google** | Gemini 3 Flash, 3.1 Pro | ✅ | ✅ | ❌ | 2026-02-11 |
| **阿里云** | Qwen 3.5 (397B MoE) | ✅ | ✅ | ❌ | 2026-02-16 |
| **DeepSeek** | DeepSeek Chat/Coder | ✅ | ❌ | ❌ | 2026-02 |
| **智谱AI** | GLM-5 (744B) | ✅ | ❌ | ❌ | 2026-02-11 |
| **月之暗面** | Kimi K2.5 (1.04T) | ✅ | ✅ | ❌ | 2026-01-27 |
| **本地** | Ollama (多模型) | ✅ | ❌ | ❌ | - |
| **Edge TTS** | 微软语音 | ❌ | ❌ | ✅ | 免费 |

> 📖 详见 [模型更新日志](MODEL_UPDATES_2026_02.md) 和 [AI 配置指南](docs/guides/AI_CONFIGURATION.md)

### 画面理解

- **视频级理解** — Gemini 视频直传 + 多帧连续分析
- **多模型视觉分析** — GPT-5 / 千问 3.5 VL / Gemini 3，自动 fallback
- **叙事结构识别** — 故事线、角色、情感弧线、高潮标记

### 字幕提取

- **语音转文字** — Whisper API / 本地 Whisper 模型
- **OCR 识别** — Vision API 从画面提取硬字幕
- **双模式合并** — 语音为主 + OCR 补充画面文字

### 音画同步

- **节拍检测** — 基于 librosa 的 BPM / 节拍 / 能量分析
- **4 种同步策略** — 节拍踩点 / 乐句段落 / 能量匹配 / 混合模式
- **智能转场** — 强拍硬切、弱拍淡化，速度曲线跟随能量

---

## 🖥️ 界面设计（2026现代化）

### 主窗口布局

```
┌────────────────────────────────────────────────────────┐
│  ClipFlow                          [最小化] [最大化] [×] │
├────┬───────────────────────────────────────────────────┤
│ 🏠 │  页面标题              [新建] [导入] [导出]        │
│    ├───────────────────────────────────────────────────┤
│ 📁 │                                                   │
│    │              主内容区域                            │
│ ⚙️ │          (三栏专业布局)                           │
│    │                                                   │
└────┴───────────────────────────────────────────────────┘
│  状态栏: 就绪 | AI: 可用 | 2026-02-22 15:30:45        │
└────────────────────────────────────────────────────────┘
```

### 核心页面

| 页面 | 功能 | 快捷键 |
|------|------|--------|
| 🏠 **首页** | 创作模式选择、快速开始、最近项目 | Cmd+1 |
| 📁 **项目管理** | 项目列表、搜索筛选、状态管理 | Cmd+2 |
| ⚙️ **设置** | API 密钥配置、AI 模型管理、导出偏好、主题 | Cmd+, |

> 📖 详见 [UI/UX 优化方案](docs/design/UI_UX_OPTIMIZATION_2026.md)

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.9 或更高版本
- **FFmpeg**: 必须安装并加入 PATH
- **操作系统**: macOS 10.15+ / Windows 10+
- **内存**: 建议 8GB 以上
- **GPU**: 可选，用于加速渲染

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/Agions/cine-flow.git
cd cine-flow
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置 AI 服务**
```bash
cp .env.example .env
# 编辑 .env，填入 AI 模型 API Key
```

4. **运行应用**
```bash
python main.py
```

> 📖 详细安装指南请查看 [安装文档](docs/guides/INSTALL.md)  
> 🔑 AI 配置教程请查看 [AI 配置指南](docs/guides/AI_CONFIGURATION.md)

---

## 📁 项目结构

```
cine-flow/
├── app/                           # 应用主目录
│   ├── core/                      # 核心层
│   │   ├── application.py         # 应用生命周期
│   │   ├── config_manager.py      # 配置管理
│   │   ├── event_bus.py           # 事件总线
│   │   ├── service_container.py   # 服务容器（DI）
│   │   └── task_queue.py          # 异步任务队列
│   │
│   ├── services/                  # 服务层
│   │   ├── ai/                    # AI 服务
│   │   │   ├── llm_manager.py     # LLM 多模型调度
│   │   │   ├── providers/         # 各 LLM 提供者实现
│   │   │   │   ├── claude.py      # Claude Opus 4.6
│   │   │   │   ├── gemini.py      # Gemini 3 Flash
│   │   │   │   ├── glm5.py        # GLM-5
│   │   │   │   ├── kimi.py        # Kimi K2.5
│   │   │   │   ├── qwen.py        # Qwen 3.5
│   │   │   │   └── local.py       # Ollama 本地模型
│   │   │   ├── scene_analyzer.py  # 场景分析
│   │   │   ├── script_generator.py # 脚本生成
│   │   │   └── voice_generator.py # AI 配音
│   │   │
│   │   ├── audio/                 # 音频处理
│   │   │   ├── beat_detector.py   # 节拍检测 (librosa)
│   │   │   └── sync_engine.py     # 音画同步引擎
│   │   │
│   │   ├── video/                 # 视频处理
│   │   │   ├── commentary_maker.py # 解说制作
│   │   │   ├── mashup_maker.py    # 混剪制作
│   │   │   └── transition_effects.py # 转场效果
│   │   │
│   │   └── export/                # 导出引擎
│   │       ├── jianying_exporter.py  # 剪映
│   │       ├── premiere_exporter.py  # Premiere
│   │       ├── finalcut_exporter.py  # Final Cut
│   │       └── davinci_exporter.py   # 达芬奇
│   │
│   └── ui/                        # 界面层 (PyQt6)
│       ├── design_system_v2.py    # 设计系统 V2.0
│       ├── main/
│       │   ├── main_window.py     # 主窗口
│       │   └── pages/             # 页面组件
│       └── theme/
│           └── modern_v2.qss      # 现代主题样式
│
├── docs/                          # 文档目录
│   ├── README.md                  # 文档导航
│   ├── guides/                    # 用户指南
│   ├── design/                    # 设计文档
│   ├── architecture/              # 架构文档
│   ├── api/                       # API 文档
│   ├── dev/                       # 开发文档
│   └── ai/                        # AI 模型文档
│
├── tests/                         # 测试目录
├── main.py                        # 应用入口
├── requirements.txt               # Python 依赖
├── .env.example                   # 环境变量模板
└── README.md                      # 项目说明（本文件）
```

> 📖 详细架构说明请查看 [系统架构文档](docs/architecture/ARCHITECTURE.md)

---

## 🛠️ 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| **GUI 框架** | PyQt6 | 6.0+ |
| **视频处理** | FFmpeg + OpenCV | Latest |
| **音频分析** | librosa | 0.10+ |
| **AI 配音** | Edge TTS / OpenAI TTS | Latest |
| **LLM 调度** | 自研多模型管理器 | - |
| **视觉 AI** | GPT-5 / Qwen 3.5 VL / Gemini 3 | 2026-02 |
| **字幕提取** | Whisper + OCR | Latest |
| **GPU 加速** | FFmpeg NVENC / VideoToolbox | - |
| **代码规范** | flake8 + mypy + pylint | Latest |
| **测试框架** | pytest | 7.0+ |

> 📖 详细技术栈说明请查看 [技术栈文档](docs/architecture/TECH-STACK.md)

---

## 🆚 版本对比

| 特性 | ClipFlow Web | ClipFlow Desktop |
|------|:---:|:---:|
| 界面技术 | React + Ant Design | PyQt6 原生 |
| 视频处理 | 浏览器端 + 命令生成 | **FFmpeg 本地处理** |
| AI 视觉 | 简单场景检测 | **视频级理解 + 多模型** |
| 音画同步 | ❌ | **✅ librosa 引擎** |
| AI 配音 | ❌ | **✅ Edge TTS / OpenAI** |
| 导出格式 | MP4/WebM/MOV | **7种格式（含剪映/PR/FCP）** |
| 跨平台 | Web + Tauri | macOS + Windows |
| 安装门槛 | npm install | Python + FFmpeg |

---

## 📚 文档

### 快速导航

- 📖 [完整文档中心](docs/README.md) - 所有文档的入口
- 🚀 [快速入门](docs/guides/QUICKSTART.md) - 5分钟上手教程
- 🔑 [AI 配置指南](docs/guides/AI_CONFIGURATION.md) - API 密钥配置
- 🎨 [UI/UX 优化方案](docs/design/UI_UX_OPTIMIZATION_2026.md) - 2026最新设计
- 🏗️ [系统架构](docs/architecture/ARCHITECTURE.md) - 架构设计说明
- 👨‍💻 [开发指南](docs/dev/DEVELOPER.md) - 开发环境搭建
- 🤝 [贡献指南](docs/dev/CONTRIBUTING.md) - 如何参与贡献

### 文档结构

```
docs/
├── guides/          # 用户指南（安装、使用、配置）
├── design/          # 设计文档（UI/UX、工作流）
├── architecture/    # 架构文档（系统设计、技术栈）
├── api/             # API 文档（接口说明）
├── dev/             # 开发文档（开发、测试、发布）
├── ai/              # AI 模型文档（更新日志、对比）
└── planning/        # 规划文档（路线图、需求）
```

---

## 🤝 参与贡献

我们欢迎所有形式的贡献！

### 贡献方式

1. 🐛 **报告 Bug** - [提交 Issue](https://github.com/Agions/cine-flow/issues)
2. 💡 **功能建议** - [发起讨论](https://github.com/Agions/cine-flow/discussions)
3. 📝 **改进文档** - 修正错误或补充内容
4. 💻 **提交代码** - Fork 并提交 Pull Request

### 开发流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

> 📖 详细贡献指南请查看 [CONTRIBUTING.md](docs/dev/CONTRIBUTING.md)

---

## 📄 许可证

本项目采用 [MIT License](./LICENSE) 开源。

---

## 🌟 Star History

如果这个项目对你有帮助，请给我们一个 ⭐️ Star！

[![Star History Chart](https://api.star-history.com/svg?repos=Agions/cine-flow&type=Date)](https://star-history.com/#Agions/cine-flow&Date)

---


<p align="center">
  <strong>ClipFlow Desktop</strong> — 从画面理解到成片导出<br>
  用 AI 重新定义视频创作
</p>

<p align="center">
  Made with ❤️ by Agions
</p>
