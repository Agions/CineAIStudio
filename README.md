# 🎬 CineFlow AI - AI 视频创作工具(未完成)

> 打造爆款短视频，一键生成剪映草稿

CineFlow AI 是一款 **AI 驱动的视频创作客户端工具**，支持打包为 macOS (.app/.dmg) 和 Windows (.exe) 安装程序。

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

## 🚀 快速开始

### 0. 克隆仓库

```bash
# 使用 HTTPS（推荐）
git clone https://github.com/Agions/CineFlow.git
cd CineAIStudio

# 或使用 SSH
git clone git@github.com:Agions/CineFlow.git
cd CineAIStudio
```

### 1. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 确保安装 FFmpeg
# macOS: brew install ffmpeg
# Windows: 下载 https://ffmpeg.org/download.html
```

### 2. 配置 API（可选）

```bash
# 用于画面分析和文案生成
export OPENAI_API_KEY="your-api-key"
```

> 💡 如果没有 API Key，可以使用自定义文案，配音使用免费的 Edge TTS

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
CineFlow AI/
├── app/
│   ├── main.py                      # 主程序入口
│   └── services/
│       ├── ai/                      # AI 服务
│       │   ├── scene_analyzer.py    # 场景分析
│       │   ├── video_content_analyzer.py  # 画面深度分析 ✨
│       │   ├── script_generator.py  # 文案生成
│       │   └── voice_generator.py   # AI 配音
│       │
│       ├── video/                   # 视频制作
│       │   ├── commentary_maker.py  # 解说视频
│       │   ├── mashup_maker.py      # 混剪视频
│       │   ├── monologue_maker.py   # 独白视频
│       │   ├── transition_effects.py # 转场效果
│       │   └── parallel_processor.py # 并行处理
│       │
│       └── export/                  # 导出服务
│           ├── jianying_exporter.py # 剪映草稿
│           └── video_exporter.py    # 视频文件
│
├── build/                           # 打包配置
│   ├── cineaistudio.spec           # PyInstaller 配置
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

| 组件     | 技术                         |
| -------- | ---------------------------- |
| 画面分析 | OpenAI GPT-4o Vision         |
| 文案生成 | OpenAI GPT-4o / 本地 LLM     |
| AI 配音  | Edge TTS (免费) / OpenAI TTS |
| 视频处理 | FFmpeg                       |
| 场景检测 | FFmpeg Scene Detection       |
| 节拍检测 | librosa                      |
| 转场效果 | FFmpeg xfade                 |
| 打包工具 | PyInstaller                  |

## 📋 系统要求

- **操作系统**: macOS 10.15+ / Windows 10+
- **Python**: 3.10+
- **FFmpeg**: 必需（用于视频处理）
- **硬盘空间**: 至少 500MB
- **网络**: 需要网络连接 API（或使用本地模式）

## 📚 文档

| 文档 | 说明 |
|------|------|
| [**安装指南**](INSTALL.md) | 完整的安装、配置和故障排查指南 |
| [**技术栈说明**](TECH-STACK.md) | 字幕渲染、特效实现的技术详解 |
| [**开发者指南**](DEVELOPER.md) | 开发环境、测试、Git 工作流 |
| [**故障排查**](TROUBLESHOOT.md) | 常见问题和解决方法 |
| [**更新日志**](CHANGELOG.md) | 版本更新记录和 Breaking Changes |
| [**项目路线图**](ROADMAP.md) | v2.0.0-rc.1 → v3.0.0 开发计划 |

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

**版本**: 1.5.0  
**更新**: 2026-02-02
