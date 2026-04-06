# Narrafiilm 架构文档

> 本文档详细描述 Narrafiilm 的系统架构和技术设计

---

## 📐 系统架构总览

Narrafiilm 采用模块化架构，将核心业务逻辑与 UI 层完全分离：

```
┌─────────────────────────────────────────────────────────────────┐
│                        Narrafiilm 应用                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   UI 层     │  │  服务层     │  │       核心层            │ │
│  │  (PySide6)  │  │ (Services)  │  │      (Core)             │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                      外部依赖 / 系统层                            │
│   FFmpeg · OpenCV · librosa · LLM APIs · OS Keychain           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 目录结构

```
Narrafiilm/
├── app/
│   ├── core/                    # 🔧 核心模块
│   │   ├── application.py       # 应用生命周期管理
│   │   ├── config_manager.py    # 配置管理
│   │   ├── event_bus.py        # 事件总线（发布/订阅）
│   │   ├── exceptions.py        # 统一异常类
│   │   ├── logger.py           # 日志系统
│   │   ├── secure_key_manager.py # API 密钥安全管理
│   │   ├── service_container.py # 依赖注入容器
│   │   ├── service_registry.py # 服务注册表
│   │   └── project_*.py         # 项目管理相关
│   │
│   ├── services/                # 🔧 业务服务层
│   │   ├── ai/                 # AI 服务
│   │   │   ├── providers/       # LLM 提供商
│   │   │   │   ├── qwen.py      # 通义千问
│   │   │   │   ├── claude.py    # Claude
│   │   │   │   ├── gemini.py    # Gemini
│   │   │   │   ├── deepseek.py  # DeepSeek
│   │   │   │   ├── kimi.py      # Kimi
│   │   │   │   ├── glm5.py      # 智谱 GLM
│   │   │   │   ├── doubao.py    # 字节豆包
│   │   │   │   ├── hunyuan.py   # 腾讯混元
│   │   │   │   └── local.py    # 本地 Ollama
│   │   │   ├── base_llm_provider.py  # Provider 基类
│   │   │   ├── llm_manager.py   # LLM 管理器
│   │   │   ├── scene_analyzer.py    # 场景分析
│   │   │   ├── script_generator.py   # 文案生成
│   │   │   └── voice_generator.py    # 语音合成
│   │   │
│   │   ├── video/               # 视频处理服务
│   │   │   ├── commentary_maker.py  # AI 解说制作
│   │   │   ├── monologue_maker.py   # 独白制作
│   │   │   ├── mashup_maker.py     # 混剪制作
│   │   │   ├── highlight_detector.py # 高光检测
│   │   │   └── ...
│   │   │
│   │   ├── audio/               # 音频处理服务
│   │   │   ├── beat_detector.py     # 节拍检测
│   │   │   └── sync_engine.py       # 音画同步
│   │   │
│   │   └── export/              # 导出服务
│   │       ├── jianying_exporter.py  # 剪映
│   │       ├── premiere_exporter.py  # Premiere
│   │       ├── finalcut_exporter.py # Final Cut Pro
│   │       ├── davinci_exporter.py  # DaVinci Resolve
│   │       └── ...
│   │
│   ├── plugins/                  # 🔌 插件系统
│   │   ├── plugin_interface.py   # 插件接口
│   │   ├── plugin_manager.py     # 插件管理器
│   │   ├── plugin_loader.py      # 插件加载器
│   │   └── secure_plugin_loader.py # 安全插件加载
│   │
│   └── ui/                      # 🖥️ 界面层 (PySide6)
│       ├── components/           # 通用 UI 组件
│       ├── main/                 # 主窗口与页面
│       │   ├── main_window.py    # 主窗口
│       │   └── pages/           # 各功能页面
│       └── theme/               # 主题管理
│
├── tests/                       # 🧪 测试
├── docs/                        # 📚 文档
├── scripts/                     # 🛠️ 工具脚本
└── resources/                  # 📦 资源文件
```

---

## 🔧 核心模块 (Core)

### 应用生命周期

```
main.py → ApplicationLauncher → Application → QMainWindow
```

| 类 | 职责 |
|---|---|
| `ApplicationLauncher` | 启动器，处理命令行参数、早期初始化 |
| `Application` | 应用核心，管理状态、服务、事件 |
| `ServiceContainer` | 依赖注入容器 |
| `EventBus` | 事件总线，解耦模块通信 |

### 配置管理

```
ConfigManager → YAML配置 → 环境变量替换
SecureKeyManager → OS Keychain / 加密文件
```

### 安全架构

| 组件 | 功能 |
|------|------|
| `SecureKeyManager` | API 密钥加密存储（Fernet + PBKDF2） |
| `SecureFileHandler` | 安全文件读写（路径验证、扩展名白名单） |
| `CommandValidator` | 命令执行安全验证 |
| `InputSanitizer` | 用户输入清理 |

---

## 🤖 AI 服务架构

### LLM 提供商抽象

```
                    ┌─────────────────┐
                    │   LLMManager    │
                    │  (统一入口)      │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ QwenProvider │   │ClaudeProvider│   │GeminiProvider│
└──────────────┘   └──────────────┘   └──────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
   通义千问 API         Claude API          Gemini API
```

### 支持的 LLM 提供商

| 提供商 | API 类型 | 模型 |
|--------|----------|------|
| OpenAI | OpenAI 兼容 | GPT-4o, GPT-5 |
| Claude | Anthropic | Claude Sonnet 4.5, Opus 4.6 |
| Gemini | Google | Gemini 3.1 Flash/Pro |
| Qwen | 阿里云 | Qwen 3.5, Plus, Max |
| DeepSeek | DeepSeek | R1, V3.2, Coder |
| Kimi | 月之暗面 | Kimi K2.5 |
| GLM | 智谱 | GLM-5 |
| Doubao | 字节 | Doubao Pro/Lite |
| Hunyuan | 腾讯 | Hunyuan Pro/Standard |
| Local | Ollama | 任意本地模型 |

### 语音合成

| 提供商 | 类型 | 费用 |
|--------|------|------|
| Edge TTS | 微软 | 免费 |
| OpenAI TTS | OpenAI | 付费 |

---

## 🎬 视频处理流程

### AI 解说制作

```
1. 视频输入 → 2. 场景检测 → 3. AI 分析 → 4. 文案生成 → 5. 语音合成 → 6. 字幕生成 → 7. 视频合成
```

| 步骤 | 服务 | 技术 |
|------|------|------|
| 场景检测 | SceneAnalyzer | PySceneDetect |
| 内容分析 | VideoUnderstanding | Gemini/GPT-4o |
| 文案生成 | ScriptGenerator | LLM |
| 语音合成 | VoiceGenerator | Edge TTS / OpenAI TTS |
| 字幕生成 | SubtitleExtractor | Whisper |
| 视频合成 | VideoExporter | FFmpeg |

### AI 混剪制作

```
1. 多素材 → 2. 节拍检测 → 3. 剪辑点 → 4. 转场合成 → 5. 导出
```

---

## 🖥️ UI 层架构 (PySide6)

### 页面结构

```
MainWindow
├── NavigationBar (导航栏)
├── ContentArea (内容区)
│   ├── HomePage (首页)
│   ├── ProjectsPage (项目管理)
│   ├── AIVideoCreatorPage (AI 视频创作)
│   ├── VideoEditorPage (视频编辑)
│   ├── AIConfigPage (AI 配置)
│   └── SettingsPage (设置)
├── StatusBar (状态栏)
└── Dialogs (对话框)
```

### 主题支持

- **Light Theme**: 浅色主题
- **Dark Theme**: 深色主题
- **macOS Theme**: macOS 原生风格

---

## 🔌 插件系统

```
Plugin Interface
      │
      ├── VideoProcessorPlugin
      ├── ExportPlugin  
      ├── AIGeneratorPlugin
      └── UIExtensionPlugin
```

### 插件加载流程

1. 扫描 `plugins/` 目录
2. 验证插件签名
3. 加载插件元数据
4. 实例化插件
5. 注册到对应服务

---

## 🔒 安全设计

### API 密钥存储

```
用户输入 API Key
      │
      ▼
SecureKeyManager
      │
      ├── OS Keychain (优先)
      │   ├── macOS: Keychain
      │   ├── Windows: Credential Manager
      │   └── Linux: Secret Service
      │
      └── 加密文件 (降级方案)
            │
            └── master.key (用户目录)
```

### 文件操作安全

- 路径穿越防护 (`..` 检测)
- 危险路径禁止访问 (`/etc`, `/proc` 等)
- 文件扩展名白名单
- 文件大小限制

### 命令执行安全

- 命令白名单 (`ffmpeg`, `ffprobe`)
- 危险命令关键词检测
- 环境变量清理 (`LD_PRELOAD` 等)

---

## 📊 技术栈汇总

| 层级 | 技术 |
|------|------|
| GUI 框架 | **PySide6** (LGPL) |
| 视频处理 | FFmpeg, opencv-python |
| 音频分析 | librosa, soundfile |
| AI/ML | OpenAI SDK, 各厂商 API |
| 语音合成 | Edge TTS, openai |
| 加密 | cryptography (Fernet/AES) |
| 配置 | YAML, python-dotenv |
| 日志 | logging |
| 测试 | pytest, pytest-asyncio |

---

## 📝 更新日志

- **v3.0** (2026.03): PySide6 迁移，代码审核修复，安全增强
- **v2.0** (2025.XX): AI 混剪、独白、多 LLM 支持
- **v1.0** (2025.XX): AI 解说基础功能

---

## 🆕 新增模块规划 (v3.1+)

### 设计理念
- **风格**: 深色科技感 + 电影级专业
- **主色调**: 深空灰 `#0D0D0F` + 翡翠绿 `#10B981` + 紫罗兰 `#8B5CF6`
- **布局**: 左侧垂直导航 + 右侧动态内容区

---

### 1️⃣ 模板市场 (TemplateMarket)

**功能**: 预设工作流模板，一键启动创作

```
模板分类:
├── 📹 AI 解说模板
│   ├── 知识科普型
│   ├── 娱乐搞笑型
│   └── 情感励志型
├── ✂️ AI 混剪模板
│   ├── 音乐卡点型
│   ├── 影视剪辑型
│   └── 素材混搭型
├── ⭐ 高光时刻模板
│   ├── 游戏高光
│   ├── 体育精彩
│   └── 直播切片
└── 🔥 病毒视频模板
    ├── 挑战类
    ├── 剧情类
    └── 热点类
```

**核心组件**:
- `TemplateCard` - 模板卡片（缩略图+标题+标签）
- `TemplateFilter` - 分类筛选器
- `TemplatePreview` - 模板预览弹窗
- `TemplateLauncher` - 模板启动器

---

### 2️⃣ 批量处理面板 (BatchProcessor)

**功能**: 多视频排队处理，进度可视化

**UI 布局**:
```
┌─────────────────────────────────────────────────────────┐
│  批量处理                                    [+ 添加]   │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │ 📹 video_001.mp4    ████████░░░░  80%  正在处理 │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 📹 video_002.mp4    ⏸️ 已暂停       等待中     │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 📹 video_003.mp4    ✅ 完成                    │   │
│  └─────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│  进度: 1/3 完成  │  预计剩余: 5分钟  │  [全部暂停]     │
└─────────────────────────────────────────────────────────┘
```

**核心组件**:
- `BatchJobItem` - 任务项卡片
- `BatchProgressBar` - 进度条
- `BatchQueueManager` - 队列管理器
- `BatchStatsPanel` - 统计面板

---

### 3️⃣ 实时预览窗口 (RealtimePreview)

**功能**: 视频预览 + 时间轴 + 关键帧标记

**UI 布局**:
```
┌─────────────────────────────────────────────────────────┐
│  📹 video_preview.mp4                         [⛶ 全屏] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│                    [视频预览区域]                        │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  00:01:23 ─●────────────────────────────── 00:05:47    │
│           ▲         ▲                    ▲             │
│          关键帧1   关键帧2               关键帧3          │
├─────────────────────────────────────────────────────────┤
│  🎬 播放  ⏸️ 暂停  ⏮️ 上帧  ⏭️ 下帧  🔊 音量         │
└─────────────────────────────────────────────────────────┘
```

**核心组件**:
- `VideoPlayer` - 视频播放器（基于 QMediaPlayer）
- `TimelineWidget` - 时间轴组件
- `KeyframeMarker` - 关键帧标记
- `PlaybackControls` - 播放控制栏

---

### 新增页面结构

```
MainWindow
├── NavigationBar (左侧导航)
├── ContentArea (右侧内容)
│   ├── HomePage (首页)
│   ├── ProjectsPage (项目管理)
│   ├── TemplateMarketPage (模板市场) 🆕
│   ├── BatchProcessorPage (批量处理) 🆕
│   ├── AIVideoCreatorPage (AI 视频创作)
│   ├── RealtimePreviewPage (实时预览) 🆕
│   ├── VideoEditorPage (视频编辑)
│   ├── AIConfigPage (AI 配置)
│   └── SettingsPage (设置)
├── StatusBar (状态栏)
└── Dialogs (对话框)
```

---

### 新增服务层

```
services/
├── template/                  # 🆕 模板服务
│   ├── template_manager.py    # 模板管理器
│   ├── template_store.py      # 模板商店
│   └── template_renderer.py   # 模板渲染器
├── batch/                     # 🆕 批量处理服务
│   ├── batch_queue.py         # 处理队列
│   ├── batch_processor.py     # 批处理器
│   └── batch_scheduler.py     # 调度器
└── preview/                  # 🆕 预览服务
    ├── preview_generator.py   # 预览生成器
    └── thumbnail_generator.py # 缩略图生成器
```
