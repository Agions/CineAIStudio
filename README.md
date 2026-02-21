# 🎬 CineFlow AI - AI 视频创作工具

> AI 驱动的视频创作桌面工具，从画面理解到成片导出

CineFlow AI 是一款基于 Python + PyQt6 的 **AI 视频创作客户端**，支持 macOS 和 Windows。

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 🎙️ **AI 视频解说** | 画面分析 → 生成解说文案 → AI 配音 → 动态字幕 |
| 🎵 **AI 视频混剪** | 多素材 → 节拍匹配 → 自动转场 → 音画同步 |
| 🎭 **AI 第一人称独白** | 画面情感分析 → 情感独白 → 电影字幕 |
| 📺 **短剧切片** | 识别高能片段 → 自动切片 → 加字幕 |
| 🛍️ **产品推广** | 画面分析 → 卖点提取 → 推广文案 → 配音 |

## 🧠 AI 能力

### 画面理解
- **视频级理解** — Gemini 视频直传 + 多帧连续分析
- **多模型视觉分析** — OpenAI GPT-4o / 通义千问 VL / Gemini Pro Vision，自动 fallback
- **叙事结构识别** — 故事线、角色、情感弧线、高潮标记

### 字幕提取
- **语音转文字** — Whisper API / 本地 Whisper 模型
- **OCR 识别** — Vision API 从画面提取硬字幕
- **双模式合并** — 语音为主 + OCR 补充画面文字

### 音画同步
- **节拍检测** — 基于 librosa 的 BPM / 节拍 / 能量分析
- **4 种同步策略** — 节拍踩点 / 乐句段落 / 能量匹配 / 混合模式
- **智能转场** — 强拍硬切、弱拍淡化，速度曲线跟随能量

### AI 配音
- **内部生成** — Edge TTS（免费）/ OpenAI TTS
- **外部导入** — 支持 mp3 / wav / m4a 等格式
- **多种声音** — 晓晓、云扬、晓墨、云希等中文声音

## 📤 导出格式

| 格式 | 说明 |
|------|------|
| 剪映 | `.json` 草稿，直接导入剪映电脑版 |
| Premiere | Adobe Premiere Pro XML |
| Final Cut | FCPXML 格式 |
| 达芬奇 | DaVinci Resolve（FCPXML） |
| SRT 字幕 | 通用字幕格式 |
| ASS 字幕 | 高级样式字幕 |
| 视频文件 | MP4 直接导出（GPU 加速） |

## 🤖 支持的 LLM

| 提供者 | 文本 | 视觉 | 配音 |
|--------|:---:|:---:|:---:|
| OpenAI (GPT-4o) | ✅ | ✅ | ✅ |
| 通义千问 | ✅ | ✅ | ❌ |
| Gemini | ✅ | ✅ | ❌ |
| Kimi (月之暗面) | ✅ | ❌ | ❌ |
| GLM-5 (智谱) | ✅ | ❌ | ❌ |
| Claude | ✅ | ❌ | ❌ |
| 本地 (Ollama) | ✅ | ❌ | ❌ |
| Edge TTS | ❌ | ❌ | ✅ (免费) |

## 🚀 快速开始

### 环境要求
- Python 3.9+
- FFmpeg

### 安装

```bash
git clone git@github.com:Agions/cine-flow.git
cd cine-flow
pip install -r requirements.txt
```

### 配置

```bash
# 方式一：.env 文件
echo 'OPENAI_API_KEY=sk-xxx' > .env

# 方式二：启动后在设置页面配置
```

> 💡 没有 API Key 也能用！配音使用免费的 Edge TTS，文案可手动输入。

### 运行

```bash
python app/main.py
```

## 🏗️ 项目结构

```
cine-flow/
├── app/
│   ├── core/               # 核心（DI容器、配置、事件总线、任务队列）
│   ├── services/
│   │   ├── ai/             # AI 服务（LLM、视觉分析、字幕提取、配音）
│   │   ├── audio/          # 音频分析（节拍检测、音画同步）
│   │   ├── video/          # 视频制作（解说、混剪、独白）
│   │   ├── video_service/  # 视频底层（GPU渲染、批量处理）
│   │   └── export/         # 导出（剪映/Premiere/达芬奇/字幕）
│   ├── viewmodels/         # MVVM ViewModel 层
│   ├── ui/                 # PyQt6 UI
│   └── plugins/            # 插件系统
├── config/                 # 配置文件
├── docs/                   # 文档
│   ├── guides/             # 用户指南
│   ├── api/                # API 参考
│   └── dev/                # 开发文档
└── tests/                  # 测试
```

## 📖 文档

- [快速上手](docs/guides/QUICKSTART.md)
- [架构文档](docs/ARCHITECTURE.md)
- [API 参考](docs/api/API_REFERENCE.md)
- [安装指南](docs/guides/INSTALL.md)
- [故障排除](docs/guides/TROUBLESHOOT.md)

## 🛠️ 技术栈

- **UI**: PyQt6 + PyQt6-Fluent-Widgets
- **AI**: OpenAI / 通义千问 / Gemini / Kimi / GLM
- **视频**: OpenCV + FFmpeg + GPU 加速
- **音频**: librosa + soundfile
- **语音**: Edge TTS + OpenAI TTS + Whisper

## 📄 许可证

MIT License

## 🙏 贡献

欢迎提交 Issue 和 PR！详见 [贡献指南](docs/dev/CONTRIBUTING.md)。
