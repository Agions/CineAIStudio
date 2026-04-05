---
title: 架构概览
description: Narrafiilm 系统架构和技术设计的核心要点速查。
---

# 架构概览

本文档是 [完整架构文档](https://github.com/Agions/Narrafiilm/blob/main/ARCHITECTURE.md) 的精简版，帮助你快速理解 Narrafiilm 的核心设计。

---

## 系统架构

Narrafiilm 采用 **三层模块化架构**：

```
┌──────────────────────────────────────────────────────────────┐
│                         UI 层 (PySide6)                      │
│     主窗口 · 素材面板 · 预览区域 · 时间线面板 · 状态栏         │
├──────────────────────────────────────────────────────────────┤
│                        服务层 (Services)                      │
│   AI 服务 · 视频处理服务 · 音频服务 · 导出服务                 │
├──────────────────────────────────────────────────────────────┤
│                         核心层 (Core)                         │
│   配置管理 · 事件总线 · 依赖注入 · 安全密钥管理               │
├──────────────────────────────────────────────────────────────┤
│                        外部依赖层                              │
│        FFmpeg · OpenCV · librosa · LLM APIs · OS Keychain    │
└──────────────────────────────────────────────────────────────┘
```

**设计原则**：UI 层与业务逻辑完全解耦，可以独立替换 UI 框架而不影响核心功能。

---

## 目录结构

```
Narrafiilm/
├── app/
│   ├── core/                    # 核心模块
│   │   ├── application.py       # 应用生命周期
│   │   ├── config_manager.py    # 配置管理
│   │   ├── event_bus.py        # 事件总线（发布/订阅）
│   │   ├── service_container.py # 依赖注入容器
│   │   └── secure_key_manager.py # API 密钥安全管理
│   │
│   ├── services/                # 业务服务层
│   │   ├── ai/                  # AI 服务
│   │   │   ├── providers/       # LLM 提供商（OpenAI/Claude/Qwen...）
│   │   │   ├── llm_manager.py   # LLM 统一管理器
│   │   │   ├── scene_analyzer.py # 场景分析
│   │   │   ├── script_generator.py # 文案生成
│   │   │   └── voice_generator.py  # 语音合成
│   │   ├── video/               # 视频处理服务
│   │   │   ├── commentary_maker.py  # AI 解说
│   │   │   ├── mashup_maker.py     # 智能混剪
│   │   │   └── highlight_detector.py # 高光检测
│   │   └── export/              # 导出服务
│   │       ├── jianying_exporter.py  # 剪映
│   │       ├── premiere_exporter.py  # Premiere
│   │       └── ...
│   │
│   ├── plugins/                 # 插件系统
│   └── ui/                      # 界面层 (PySide6)
│
├── tests/                       # 测试
├── docs/                        # 文档
└── resources/                   # 资源文件
```

---

## 核心模块

### 1. Application（应用生命周期）

```
启动流程: main.py → ApplicationLauncher → Application → QMainWindow
```

| 组件 | 职责 |
|------|------|
| `ApplicationLauncher` | 命令行参数处理、早期初始化 |
| `Application` | 管理应用状态、服务、事件总线 |
| `ServiceContainer` | 依赖注入容器，按需懒加载服务 |
| `EventBus` | 模块间解耦通信（发布/订阅模式） |

### 2. LLMManager（AI 统一管理器）

```
LLMManager 是所有 AI 能力的统一入口：
```

| 方法 | 说明 |
|------|------|
| `complete(prompt, model?)` | 文本补全 |
| `analyze_video(video_path)` | 视频内容分析 |
| `generate_script(context)` | 生成解说文案 |
| `transcribe(audio_path)` | 语音转文字（Whisper） |

支持的 AI 提供商：

| 提供商 | 模型 | 特点 |
|--------|------|------|
| OpenAI | GPT-4o / GPT-5 | 最强通用能力 |
| Anthropic | Claude Sonnet 4.6 | 长上下文、安全性高 |
| Google | Gemini 3.1 Pro | 超长上下文 |
| 阿里云 | Qwen 2.5-Max | 中文优化 |
| DeepSeek | V3.2 | 性价比高 |
| Kimi | K2.5 | 超长上下文 |
| Ollama | 本地模型 | 完全私有离线 |

### 3. SecureKeyManager（密钥安全）

```
API Key 存储优先级:
1. OS Keychain (macOS Keychain / Windows Credential Manager / Linux Secret Service)
2. 加密文件 (Fernet + PBKDF2)
```

---

## 视频处理流程

### AI 解说制作

```
视频 → 场景检测 → AI 内容分析 → 文案生成 → 语音合成 → 字幕生成 → 视频合成 → 导出
```

| 步骤 | 核心技术 |
|------|----------|
| 场景检测 | PySceneDetect |
| 内容分析 | Gemini / GPT-4o 多模态 |
| 文案生成 | LLM |
| 语音合成 | Edge TTS / OpenAI TTS |
| 字幕生成 | Whisper |
| 视频合成 | FFmpeg |

### AI 智能混剪

```
多素材 → 节拍检测 (librosa) → 剪辑点计算 → 转场合 → 成 → 导出
```

---

## 插件系统

```
Plugin Interface (抽象基类)
       │
       ├── VideoProcessorPlugin
       ├── ExportPlugin
       ├── AIGeneratorPlugin
       └── UIExtensionPlugin
```

插件加载流程：

```
扫描 plugins/ 目录 → 验证 manifest.json → 签名验证 → 实例化 → 注册服务
```

---

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| GUI 框架 | **PySide6** (LGPL) |
| 视频处理 | FFmpeg、opencv-python |
| 音频分析 | librosa、soundfile |
| AI | 各厂商 OpenAI 兼容 API |
| 语音合成 | Edge TTS、OpenAI TTS |
| 加密 | cryptography (Fernet/AES) |
| 配置 | YAML、python-dotenv |
| 测试 | pytest、pytest-asyncio |

---

## 相关文档

- 🔧 [详细架构文档](https://github.com/Agions/Narrafiilm/blob/main/ARCHITECTURE.md) — 完整的架构说明
- 🔒 [安全设计](../security.md) — API 密钥安全和文件操作安全
- 🔌 [插件开发指南](./guide/plugin-development.md) — 如何编写插件
- 🧪 [测试策略](https://github.com/Agions/Narrafiilm/blob/main/tests/README.md) — 如何编写测试（待补充）
