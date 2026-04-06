# NARRAFILM 技术规范文档

> 本文档描述 NARRAFILM 的技术设计决策、架构约束和实现规范。

---

## 版本信息

| 项目 | 版本 | 来源 |
|------|------|------|
| `pyproject.toml` | 3.2.0 | ✅ 唯一真实来源 |
| CHANGELOG.md | 3.2.0 | 与 pyproject.toml 一致 |
| GitHub Releases | v3.2.0 | 与 pyproject.toml 一致 |

---

## 产品定位

**NARRAFILM** — AI First-Person Video Narrator

> 上传视频，AI 代入画面主角视角，一键生成配音解说。

核心使用场景：vlog 叙事化改造、教学实操视频、游戏录屏解说、会议录制叙事、会议回顾、纪录片风格改造。

---

## 核心架构

```
┌──────────────────────────────────────────────────┐
│                  UI 层 (PySide6)                  │
│         home_page + ai_video_creator_page           │
├──────────────────────────────────────────────────┤
│               服务层 (Services)                     │
│  monologue_maker.py  ← 唯一核心                   │
│  voice_generator.py / caption_generator.py          │
│  jianying_exporter.py                              │
├──────────────────────────────────────────────────┤
│               AI 层 (ai/)                          │
│  video_content_analyzer.py  (Qwen2.5-VL)           │
│  script_generator.py      (DeepSeek-V3)            │
│  sensevoice_provider.py   (SenseVoice ASR)          │
│  vision_providers.py      (多模态统一接口)           │
├──────────────────────────────────────────────────┤
│               核心层 (Core)                        │
│  application.py / config_manager.py                 │
│  secure_key_manager.py / logger.py                 │
│  event_bus.py / service_registry.py               │
└──────────────────────────────────────────────────┘
```

---

## 技术流程（Pipeline）

```
Step 1: 视频理解
  └─ VideoContentAnalyzer + Qwen2.5-VL
      抽帧 → 逐帧画面描述 → 时间轴场景序列

Step 2: 第一人称解说生成
  └─ ScriptGenerator + DeepSeek-V3
      输入场景描述 → 第一人称解说稿（含时间戳）

Step 3: 情感配音合成
  └─ VoiceGenerator + Edge-TTS / F5-TTS
      解说稿 → 多风格旁白 WAV/MP3

Step 4: 字幕生成
  └─ 基于 TTS word-level timing
      音字同步对齐 → ASS 电影级字幕

Step 5: 合成输出
  └─ JianyingExporter / DirectVideoExporter
      MP4 成品 / 剪映草稿
```

---

## 模块职责

| 模块 | 文件 | 职责 |
|------|------|------|
| **MonologueMaker** | `services/video/monologue_maker.py` | 第一人称解说核心编排器 |
| **VideoContentAnalyzer** | `services/ai/video_content_analyzer.py` | Qwen2.5-VL 场景理解 |
| **ScriptGenerator** | `services/ai/script_generator.py` | DeepSeek-V3 解说文案生成 |
| **VoiceGenerator** | `services/ai/voice_generator.py` | Edge-TTS / F5-TTS 配音 |
| **CaptionGenerator** | `services/video_tools/caption_generator.py` | 字幕生成 + 时间轴对齐 |
| **JianyingExporter** | `services/export/jianying_exporter.py` | 导出剪映草稿 |

---

## AI 模型选型（2025-2026 最新）

### 场景理解 — Qwen2.5-VL (72B)

**推荐配置**：阿里云百炼 API（Qwen2.5-VL-72B-Instruct）

```python
# 使用通义千问 API
from openai import OpenAI
client = OpenAI(
    api_key=os.getenv("QWEN_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)
```

**本地备选**：`Qwen2.5-VL-7B-Instruct`（量化 int4，~8GB VRAM）

### 解说生成 — DeepSeek-V3

```python
# DeepSeek API
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)
model="deepseek-chat"
```

**第一人称提示词核心策略**：
```
你是一个Vlogger，正在用第一人称介绍这段视频。
视频中的人物正在做XXX，你作为TA，描述你在做什么、
看到了什么、有什么感受。
```

### ASR — SenseVoice

```python
# FunAudioLLM/SenseVoice（本地运行）
from funasr import AutoModel
model = AutoModel(
    model="iic/SenseVoiceLarge",
    vad_model="fsmn-vad",
    punc_model="ct-punc"
)
```

**Faster-Whisper 备选**（Whisper large-v3，int8 量化）

### TTS — Edge-TTS（主流）+ F5-TTS（高级）

```python
# Edge-TTS — 主流优质选择
edge-tts --voice zh-CN-XiaoxiaoNeural --text "你好" output.mp3

# F5-TTS — 零样本音色克隆
# pip install F5-TTS
from F5TTS import F5TTS
f5tts = F5TTS()
audio = f5tts.generate(text, ref_audio)
```

---

## 依赖精简

| 依赖 | 版本 | 用途 |
|------|------|------|
| `pyside6` | ≥6.5 | UI 框架 |
| `ffmpeg-python` | latest | 视频处理 |
| `edge-tts` | latest | TTS 配音 |
| `openai` | ≥1.0 | LLM API 调用 |
| `funasr` | latest | SenseVoice ASR |
| `moviepy` | latest | 视频合成 |
| `pydub` | latest | 音频处理 |
| `httpx` | latest | HTTP 客户端 |

**已移除**：PyTorch（改用纯 CPU FFmpeg）、torchvision、transformers（按需调用 API）

---

## 导出架构

仅保留两个 Exporter：

| Exporter | 格式 | 说明 |
|----------|------|------|
| `DirectVideoExporter` | MP4 | 最终成品 |
| `JianyingExporter` | .draft.json | 剪映原生草稿 |

已移除：PremiereExporter / DaVinciExporter / FinalCutExporter / EDLExporter

---

## 配置与密钥

所有 API Key 通过 `SecureKeyManager` 管理，**禁止硬编码**：

```python
# ✅ 正确
key = SecureKeyManager.get("deepseek_api_key")

# ❌ 禁止
key = "sk-xxx..."
```

**配置优先级**：`CLI 参数 > 环境变量 > ~/.narrafiilm/config.toml > 内置默认值`

---

## 代码规范

### 异常类

```python
class NarraFilmException(Exception):
    code = "NF_ERR"

class VideoAnalysisError(NarraFilmException):
    code = "ANALYSIS_ERR"

class ScriptGenerationError(NarraFilmException):
    code = "SCRIPT_ERR"

class ExportError(NarraFilmException):
    code = "EXPORT_ERR"
```

### 日志规范

```python
logger = logging.getLogger(__name__)

logger.info("操作描述")     # 一般信息
logger.warning("警告信息")  # 可恢复问题
logger.error("错误信息")   # 操作失败
```

---

## 目录结构（精简后）

```
app/
├── core/                          应用核心
│   ├── application.py
│   ├── config_manager.py
│   ├── event_bus.py
│   ├── logger.py
│   └── secure_key_manager.py
├── services/
│   ├── ai/
│   │   ├── script_generator.py   ← 解说文案生成
│   │   ├── video_content_analyzer.py  ← Qwen2.5-VL 场景理解
│   │   ├── voice_generator.py     ← Edge-TTS / F5-TTS
│   │   ├── sensevoice_provider.py ← ASR + 说话人分离
│   │   └── vision_providers.py    ← 多模态统一接口
│   ├── video/
│   │   ├── base_maker.py
│   │   ├── monologue_maker.py     ← ⭐ 唯一核心 Maker
│   │   └── _legacy/               ← 历史代码（已隔离）
│   ├── video_tools/
│   │   └── caption_generator.py   ← 字幕生成
│   └── export/
│       ├── jianying_exporter.py   ← 剪映导出
│       └── direct_video_exporter.py
├── ui/
│   ├── main/
│   │   ├── main_window.py
│   │   └── pages/
│   │       ├── home_page.py
│   │       └── ai_video_creator_page.py
│   └── components/
│       └── ...
└── utils/
    └── ...
```

---

## 已知限制

| 限制 | 原因 | 解决方案 |
|------|------|---------|
| Qwen2.5-VL 需要 API Key 或本地 GPU | 模型过大 | 使用通义千问 API（推荐），或本地 7B 量化版 |
| F5-TTS 需要参考音频 | 零样本克隆原理 | 使用 Edge-TTS（无需参考音频）|
| SenseVoice 首次下载模型文件大 | HuggingFace 模型 | 设置 `SENSEVOICE_MODEL_PATH` 环境变量 |

---

## 重构记录

| 日期 | 内容 |
|------|------|
| 2026-04-05 | 品牌重命名 Narrafiilm → NARRAFILM，产品定位专注第一人称解说 |
| 2026-04-05 | 裁剪全部冗余 Maker（MashupMaker/BeatSyncMaker 等）|
| 2026-04-05 | 裁剪 4 个冗余 Exporter（Premiere/DaVinci/FinalCut/EDL）|
| 2026-04-05 | 模型升级：Qwen2.5-VL / DeepSeek-V3 / SenseVoice / Edge-TTS + F5-TTS |
