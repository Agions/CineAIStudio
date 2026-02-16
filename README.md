# 🎬 CineFlow v3.0 - 多Agent智能视频剪辑

> 专业Agent协同，一键生成剪映草稿 | 支持 Windows & macOS

CineFlow 是一款基于 **多Agent协同** 的智能视频剪辑工具，6个专业Agent分工协作，为您打造高质量视频内容。

[![Windows](https://img.shields.io/badge/Windows-0078D6?style=flat-square&logo=windows&logoColor=white)](./INSTALL.md#windows)
[![macOS](https://img.shields.io/badge/macOS-000000?style=flat-square&logo=apple&logoColor=white)](./INSTALL.md#macos)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](./requirements.txt)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](./LICENSE)

## ✨ 核心特性

### 🤖 多Agent专业协同

| Agent | 职责 | 能力 |
|-------|------|------|
| 🎬 **Director** | 导演 | 项目规划、任务分配、质量把控 |
| ✂️ **Editor** | 剪辑 | 粗剪精剪、转场节奏、结构优化 |
| 🎨 **Colorist** | 调色 | 色彩分析、风格化、LUT匹配 |
| 🎵 **Sound** | 音效 | 音频分析、配乐混音、AI配音 |
| ✨ **VFX** | 特效 | 画面理解、特效生成、合成 |
| 🔍 **Reviewer** | 审核 | 质量检查、问题反馈、优化建议 |

### 💻 跨平台原生支持

- **Windows** - `.exe` 安装程序，原生体验
- **macOS** - `.app` / `.dmg` 安装包，M1/M2/Intel 全支持
- **内置FFmpeg** - 无需额外安装，开箱即用

### 🎬 三大创作模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| 🎙️ **AI解说** | 画面分析 → 解说文案 → AI配音 → 动态字幕 | 影视解说、知识分享 |
| 🎵 **AI混剪** | 多素材智能剪辑 → 节拍匹配 → 自动转场 | 音乐MV、短视频 |
| 🎭 **AI独白** | 画面情感分析 → 情感独白 → 电影字幕 | Vlog、情感短片 |

### 🔗 剪映无缝对接

- 一键导出剪映草稿
- 完美保留剪辑信息
- 支持剪映电脑版/专业版

## ✨ 核心功能

| 功能                   | 说明                                      |
| ---------------------- | ----------------------------------------- |
| 🎙️ **AI 视频解说**     | 基于画面分析生成解说 + AI 配音 + 动态字幕 |
| 🎵 **AI 视频混剪**     | 多素材智能剪辑 + 节拍匹配 + 自动转场      |
| 🎭 **AI 第一人称独白** | 画面情感分析 + 情感独白 + 电影字幕        |
| 📦 **剪映草稿导出**    | 完美适配剪映电脑版                        |

### 🔍 画面分析能力

所有功能都基于 **视频画面深度分析**：

1. **关键帧提取** - 自动提取视频关键画面
2. **内容识别** - 使用 Vision API 识别画面内容
3. **情感分析** - 分析画面情感氛围
4. **文案生成** - 基于画面内容生成文案
5. **配音匹配** - 根据情感选择合适的配音风格

### 🧠 国产大模型支持

| 功能 | 模型 | 提供商 |
|------|------|--------|
| 规划/推理 | DeepSeek-V3 | 深度求索 |
| 长文本/视觉 | Kimi K2.5 | 月之暗面 |
| 音频/多模态 | Qwen 2.5 | 阿里巴巴 |
| 创意生成 | ERNIE 4.0 | 百度 |

## 🚀 快速开始

### 0. 克隆仓库

```bash
# 使用 HTTPS（推荐）
git clone https://github.com/Agions/CineFlow.git
cd CineFlow

# 或使用 SSH
git clone git@github.com:Agions/CineFlow.git
cd CineFlow
```

### 1. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 确保安装 FFmpeg
# macOS: brew install ffmpeg
# Windows: 下载 https://ffmpeg.org/download.html
```

### 2. 配置 API（推荐国产模型）

```bash
# DeepSeek (深度求索)
export DEEPSEEK_API_KEY="sk-..."

# Moonshot (月之暗面) - Kimi
export MOONSHOT_API_KEY="sk-..."

# 阿里 (通义千问)
export DASHSCOPE_API_KEY="sk-..."

# 百度 (文心一言)
export BAIDU_API_KEY="..."
export BAIDU_SECRET_KEY="..."
```

> 💡 支持国产大模型，数据更安全，中文理解更好

### 3. 运行

```bash
# 命令行模式
python app/main.py

# 快速演示
python examples/quick_start.py

# 完整演示（需要视频素材）
python examples/full_demo.py all
```

## 📦 打包安装程序

### macOS

```bash
# 打包为 .app
python build/build_app.py

# 打包为 .dmg
python build/build_app.py --dmg
```

### Windows

```bash
# 打包为 .exe
python build/build_app.py
```

输出位置: `dist/CineFlow AI.app` 或 `dist/CineFlow AI.exe`

## 📁 项目结构

```
CineFlow/
├── app/
│   ├── agents/                      # 🤖 多Agent系统
│   │   ├── base_agent.py            # Agent基类
│   │   ├── agent_manager.py         # Agent管理器
│   │   ├── director_agent.py        # 导演Agent
│   │   ├── editor_agent.py          # 剪辑Agent
│   │   ├── colorist_agent.py        # 调色Agent
│   │   ├── sound_agent.py           # 音效Agent
│   │   ├── vfx_agent.py             # 特效Agent
│   │   ├── reviewer_agent.py        # 审核Agent
│   │   └── llm_client.py            # 国产大模型客户端
│   │
│   ├── ui/                          # 🎨 React前端
│   │   ├── src/
│   │   │   ├── components/          # 组件
│   │   │   ├── pages/               # 页面
│   │   │   │   ├── Dashboard/       # 仪表盘
│   │   │   │   ├── AgentMonitor/    # Agent监控
│   │   │   │   ├── Creator/         # 创作向导
│   │   │   │   └── Export/          # 导出中心
│   │   │   └── stores/              # 状态管理
│   │   └── package.json
│   │
│   ├── core/                        # 核心服务
│   │   ├── video_processor.py       # 视频处理
│   │   ├── audio_engine.py          # 音频引擎
│   │   ├── draft_exporter.py        # 剪映导出
│   │   └── project_manager.py       # 项目管理
│   │
│   └── main.py                      # 主入口
│
├── build/                           # 📦 打包配置
│   ├── windows/                     # Windows打包
│   └── macos/                       # macOS打包
│
├── resources/                       # 🎨 资源
│   ├── ffmpeg/                      # 内置FFmpeg
│   └── presets/                     # 预设配置
│
└── tests/                           # 🧪 测试
│       │   └── parallel_processor.py # 并行处理
│       │
│       └── export/                  # 导出服务
│           ├── jianying_exporter.py # 剪映草稿
│           └── video_exporter.py    # 视频文件
│
├── build/                           # 打包配置
│   ├── cineflow.spec           # PyInstaller 配置
│   └── build_app.py                # 打包脚本
│
├── examples/                        # 使用示例
│   ├── quick_start.py              # 快速开始
│   └── full_demo.py                # 完整演示
│
├── docs/
│   └── AI_VIDEO_GUIDE.md           # 详细使用指南
│
└── requirements.txt                 # Python 依赖
```

## 🎯 使用流程

### AI 视频解说

```python
from app.services.ai import VideoContentAnalyzer
from app.services.video import CommentaryMaker, CommentaryStyle

# 1. 分析视频画面
analyzer = VideoContentAnalyzer(vision_api_key="sk-xxx")
analysis = analyzer.analyze("movie_clip.mp4")

print(f"视频摘要: {analysis.summary}")
print(f"建议风格: {analysis.suggested_style}")
print(f"脚本建议: {analysis.script_suggestion}")

# 2. 创建解说视频
maker = CommentaryMaker(voice_provider="edge")
project = maker.create_project(
    source_video="movie_clip.mp4",
    topic=analysis.summary,
    style=CommentaryStyle.STORYTELLING,
)

# 3. 使用分析结果生成文案
maker.generate_script(project, custom_script=analysis.script_suggestion)
maker.generate_voice(project)
maker.generate_captions(project)

# 4. 导出剪映草稿
draft = maker.export_to_jianying(project, "/path/to/drafts")
```

### AI 视频混剪

```python
from app.services.video import MashupMaker, MashupStyle

maker = MashupMaker()

# 创建项目（自动分析所有素材）
project = maker.create_project(
    source_videos=["clip1.mp4", "clip2.mp4", "clip3.mp4"],
    background_music="bgm.mp3",
    target_duration=30.0,
    style=MashupStyle.FAST_PACED,
)

# 智能混剪（节拍匹配）
maker.auto_mashup(project)

# 导出
draft = maker.export_to_jianying(project, "/path/to/drafts")
```

### AI 第一人称独白

```python
from app.services.video import MonologueMaker, MonologueStyle

maker = MonologueMaker(voice_provider="edge")

# 分析视频并创建独白
project = maker.create_project(
    source_video="night_walk.mp4",
    context="深夜独自走在城市街头",
    emotion="惆怅",
    style=MonologueStyle.MELANCHOLIC,
)

# 生成独白
maker.generate_script(project)
maker.generate_voice(project)
maker.generate_captions(project, style="cinematic")

# 导出
draft = maker.export_to_jianying(project, "/path/to/drafts")
```

## 🔧 技术栈

### 多Agent系统
| Agent | 模型 | 提供商 |
|-------|------|--------|
| Director | DeepSeek-V3 | 深度求索 |
| Editor | Kimi K2.5 | 月之暗面 |
| Colorist | Kimi K2.5 | 月之暗面 |
| Sound | Qwen 2.5 | 阿里巴巴 |
| VFX | Kimi K2.5 | 月之暗面 |
| Reviewer | DeepSeek-Coder | 深度求索 |

### 核心技术
| 组件 | 技术 |
|------|------|
| 前端 | React + TypeScript + Electron |
| 后端 | Python + FastAPI |
| 视频处理 | FFmpeg |
| 打包 | PyInstaller |
| 跨平台 | Windows / macOS 原生支持 |
| AI 配音 | Edge TTS (免费) / 阿里TTS |
| 视频处理 | FFmpeg (内置) |
| 场景检测 | FFmpeg Scene Detection |
| 节拍检测 | librosa |
| 转场效果 | FFmpeg xfade |

## 📋 系统要求

| 平台 | 最低版本 | 推荐配置 |
|------|---------|---------|
| **Windows** | Windows 10 | Windows 11 |
| **macOS** | 10.15 (Catalina) | 13+ (Ventura) |
| **Python** | 3.9 | 3.11 |
| **内存** | 4GB | 8GB+ |
| **硬盘** | 2GB | 10GB+ |
| **网络** | 可选 | 推荐（用于AI功能）|

## 📚 文档

| 文档 | 说明 |
|------|------|
| [**项目规划**](PROJECT_PLAN_v3.md) | v3.0 多Agent系统完整规划 |
| [**安装指南**](INSTALL.md) | Windows/macOS 安装配置 |
| [**开发者指南**](DEVELOPER.md) | 开发环境、测试、Git 工作流 |
| [**技术栈说明**](TECH-STACK.md) | 技术架构详解 |
| [**故障排查**](TROUBLESHOOT.md) | 常见问题和解决方法 |
| [**更新日志**](CHANGELOG.md) | 版本更新记录 |
| [**项目路线图**](ROADMAP.md) | 开发路线图 |

## 🎨 支持的风格

### 解说风格

- `EXPLAINER` - 说明型解说
- `STORYTELLING` - 故事型解说
- `COMMENTARY` - 评论型解说
- `REVIEW` - 测评型解说

### 混剪风格

- `FAST_PACED` - 快节奏
- `CINEMATIC` - 电影感
- `VLOG` - Vlog 风格
- `HIGHLIGHT` - 高光集锦

### 独白风格

- `MELANCHOLIC` - 惆怅/忧郁
- `INSPIRATIONAL` - 励志/向上
- `ROMANTIC` - 浪漫/温馨
- `HEALING` - 治愈/温暖

## 📄 许可证

MIT License

---

**版本**: v3.0.0-beta  
**更新**: 2025-01-20  
**规划**: [PROJECT_PLAN_v3.md](./PROJECT_PLAN_v3.md)
