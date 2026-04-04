# VideoForge 技术规范文档

> 本文档描述 VideoForge 的技术设计决策、架构约束和实现规范。供维护者和贡献者参考。

---

## 版本信息

| 项目 | 版本 | 来源 |
|------|------|------|
| `pyproject.toml` | 3.1.1 | ✅ 唯一真实来源 |
| CHANGELOG.md | 3.1.1 | 与 pyproject.toml 一致 |
| GitHub Releases | v3.1.1 | 与 pyproject.toml 一致 |

---

## 核心架构

```
┌──────────────────────────────────────────────────────┐
│                     UI 层 (PySide6)                   │
│  main_window.py / pages/ / components/ / theme/       │
├──────────────────────────────────────────────────────┤
│                   服务层 (Services)                    │
│  ai/ · video/ · audio/ · export/ · publish/        │
│  service_manager.py · event_bus.py                   │
├──────────────────────────────────────────────────────┤
│                   核心层 (Core)                       │
│  application.py · config_manager.py                  │
│  secure_key_manager.py · event_bus.py               │
│  service_container.py · logger.py                    │
└──────────────────────────────────────────────────────┘
```

### 依赖注入

使用 `ServiceContainer` + `ServiceRegistry` 模式。服务通过容器获取，避免硬编码依赖。

```python
# ✅ 正确
container = ServiceContainer.get()
llm_manager = container.resolve(LLMManager)

# ❌ 错误 — 直接实例化
llm_manager = LLMManager()
```

---

## AI 服务架构

### LLM Provider 模型

支持 9 家提供商，统一通过 `BaseLLMProvider` 接口调用：

| Provider | 模型示例 | 用途 |
|----------|---------|------|
| `OpenAIProvider` | GPT-5.4 | 剧情分析/脚本生成 |
| `ClaudeProvider` | Sonnet 4.6 | 长文本分析 |
| `GeminiProvider` | Gemini 3.1 Pro | 多模态理解 |
| `DeepSeekProvider` | V3.2 | 翻译/日常任务 |
| `QwenProvider` | Qwen 2.5-Max | 中文内容创作 |
| `KimiProvider` | K2.5 | 长文本分析 |
| `GLM5Provider` | GLM-5 | 国产模型 |
| `DoubaoProvider` | Doubao Pro/Lite | 字节系 |
| `HunyuanProvider` | Hunyuan Pro | 腾讯系 |
| `LocalProvider` | Ollama | 本地模型 |

### Provider 实现规范

每个 Provider 必须：

1. 继承 `BaseLLMProvider`
2. 实现 `chat()` / `stream_chat()` / `count_tokens()` 方法
3. 处理 API Key 从 `SecureKeyManager` 读取（不硬编码）
4. 实现重试逻辑（指数退避）
5. 统一错误码：`APIError`, `RateLimitError`, `AuthError`, `TimeoutError`

```python
class APIError(Exception):
    """API 调用错误（非 200 响应）"""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code
```

### SenseVoice Provider

位于 `app/services/ai/sensevoice_provider.py`。

**功能：**
- `extract_emotions()` — 情感检测（开心/悲伤/愤怒/中性/恐惧/惊讶）
- `diarize()` — 说话人分离（Diarization）
- `detect_audio_events()` — 音频事件检测（笑声/掌声/静音）

**实现策略：**
1. 优先加载 SenseVoice CTranslate2 模型（最高精度）
2. 回退到 librosa 声学特征 + sklearn 聚类（无需额外模型）

```python
# 优先检查 SenseVoice 是否可用
provider = SenseVoiceProvider(model_size="large")
if provider.check_available():
    provider.load_model()
```

---

## 视频处理架构

### 服务组件

| 组件 | 文件 | 职责 |
|------|------|------|
| `HighlightDetector` | `highlight_detector.py` | 高光片段检测 |
| `BeatSyncMaker` | `beat_sync_maker.py` | BPM 节拍同步 |
| `StoryBuilder` | `story_builder.py` | 剧情构建 |
| `CommentaryMaker` | `commentary_maker.py` | AI 解说生成 |
| `MonologueMaker` | `monologue_maker.py` | AI 独白生成 |
| `MashupMaker` | `mashup_maker.py` | 智能混剪 |
| `VideoEnhancer` | `video_enhancer.py` | 视频增强 |
| `SubtitleExtractor` | `subtitle_extractor.py` | 字幕提取（OCR+Whisper）|
| `SubtitleRemover` | `subtitle_remover.py` | 字幕移除 |

### 字幕提取

`app/services/ai/subtitle_extractor.py`（816 行）支持两种模式：

1. **OCR 模式** — Vision API 识别视频帧中的文字
2. **语音转文字** — Faster-Whisper 提取音频内容

两种方式可组合使用，互相补充。

### Pipeline 模式

视频处理通过 `Pipeline` 串联：

```python
pipeline = VideoPipeline([
    HighlightDetector(),
    BeatSyncMaker(),
    StoryBuilder(),
    CommentaryMaker(),
])
result = pipeline.run(video_path)
```

---

## 导出架构

### ExportManager

统一导出管理器，支持 7 种格式：

```python
from app.services.export.export_manager import ExportManager, ExportFormat, ExportConfig

manager = ExportManager()
manager.export(project_data, ExportConfig(
    format=ExportFormat.MP4,
    quality="high",
    resolution="1080p",
    fps=30,
))
```

### Exporter 实现

| Exporter | 格式 | 平台 |
|----------|------|------|
| `DirectVideoExporter` | MP4/MOV/GIF | 全平台 |
| `JianyingExporter` | 剪映草稿 (.draft) | 剪映 App |
| `PremiereExporter` | .prproj | Adobe Premiere |
| `FinalCutExporter` | .fcpxml | Final Cut Pro |
| `DaVinciExporter` | DaVinci 项目 | DaVinci Resolve |

每个 Exporter 继承 `BaseExporter`，实现 `export(project_data, config)` 方法。

### BatchExportManager

批量导出，通过 `ThreadPoolExecutor` 并行处理 `_export_single` 任务。

---

## 配置与密钥

### API Key 管理

所有 API Key 通过 `SecureKeyManager` 管理，**禁止硬编码**：

```python
# ✅ 从 keychain/环境变量读取
key = SecureKeyManager.get("openai_api_key")

# ❌ 禁止硬编码
key = "sk-xxx..."
```

### 配置优先级

```
CLI 参数 > 环境变量 > ~/.videoforge/config.toml > 内置默认值
```

---

## 代码规范

### 异常类

所有自定义异常继承 `VideoForgeException`：

```python
class VideoForgeException(Exception):
    """基础异常类"""
    code = "VF_ERR"

class APIError(VideoForgeException):
    code = "API_ERR"

class ExportError(VideoForgeException):
    code = "EXPORT_ERR"
```

### 日志规范

```python
logger = logging.getLogger(__name__)  # 每个模块独立 logger

logger.info("操作描述")        # 一般信息
logger.warning("警告信息")     # 可恢复问题
logger.error("错误信息")       # 操作失败
logger.debug("调试信息")       # 详细信息（默认禁用）
```

DEBUG 日志默认禁用，需要通过 `Logger.set_level(logging.DEBUG)` 开启。

### 类型注解

- 所有公开接口必须有类型注解
- 内部实现不强求（`disallow_untyped_defs = false`）
- 泛型使用 `typing` 模块

### 测试

测试位于 `tests/`，使用 pytest：

```bash
pytest tests/ -x -q
```

测试覆盖：AI 服务、视频处理、导出、缓存等模块。

---

## 构建与发布

### 版本管理

**唯一真实来源：`pyproject.toml `[project].version`**

发布时：
1. 更新 `pyproject.toml` 版本号
2. 更新 `CHANGELOG.md`
3. 创建 Git tag `v{x.y.z}`

### Nuitka 打包

```bash
python build_nuitka.sh
```

生成单文件可执行文件，支持 Windows/macOS/Linux。

### PyInstaller 打包

```bash
python build_dmg.sh   # macOS
```

---

## 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | `snake_case.py` | `subtitle_extractor.py` |
| 类 | `PascalCase` | `SubtitleExtractor` |
| 函数/方法 | `snake_case` | `extract_emotions` |
| 常量 | `UPPER_SNAKE` | `MAX_FRAME_COUNT` |
| 私有成员 | `_leading_underscore` | `_model` |

---

## 国际化

UI 文本使用 `I18n` 模块，不允许硬编码用户可见字符串：

```python
# ✅ 正确
label.setText(I18n.get("export.start"))

# ❌ 错误
label.setText("开始导出")
```

---

## 已知限制

| 限制 | 原因 | 解决方案 |
|------|------|---------|
| SenseVoice 需要手动下载模型 | HuggingFace 模型文件大 | 设置 `SENSEVOICE_MODEL_PATH` 环境变量 |
| 发布平台（Bilibili/YouTube）`NotImplementedError` | 需要 OAuth API 对接 | 后续接入各平台官方 API |
| BatchExportManager 模拟进度 | 导出是同步阻塞操作 | 已接通 ExportManager，真实进度回调待完善 |

---

## v3.2.0 新增功能（2026-04-04）

### ClipRepurposingPipeline — 长视频转短片段自动化管线

参考：OpusClip / Reap / Vizard.ai

**新增文件**：`app/services/video_tools/clip_repurposing.py`

**管线步骤**：

```
Step 1: 音频提取（FFmpeg PCM 16kHz）
Step 2: 场景分割（FFmpeg scene detection，阈值 0.3）
Step 3: Faster-Whisper 转录（CPU int8，中文+英文）
Step 4: ClipScorer 多维 AI 评分
Step 5: Top-N 非重叠片段选择
Step 6: 格式转换（横→竖智能裁剪）+ 字幕烧录
```

**支持平台**：抖音 / 小红书 / TikTok / YouTube Shorts / Instagram Reels / Twitter

**使用方式**：
```python
from app.services.video_tools.clip_repurposing import (
    ClipRepurposingPipeline, AspectRatio, PlatformPreset
)

pipeline = ClipRepurposingPipeline(output_dir="./output/clips")
results = pipeline.run(
    video_path="/path/to/podcast.mp4",
    max_clips=5,
    platform="douyin",          # 使用抖音预设
    languages=["zh", "en"],
)
for clip in results:
    print(f"→ {clip.output_path} score={clip.score.total_score:.1f}")
```

### ClipScorer — 多维评分引擎

**新增文件**：`app/services/video_tools/clip_scorer.py`

**评分维度（权重可配置）**：

| 维度 | 权重 | 信号 |
|------|------|------|
| `laughter_density` | 20% | 笑声/鼓掌密度（转录文本匹配） |
| `emotion_peak` | 20% | 情感关键词命中（震惊/愤怒/搞笑等） |
| `speech_completeness` | 20% | 对话完整性（句子是否被打断） |
| `silence_ratio` | 10% | 有声占比（过静/过嘈杂都扣分） |
| `speaking_pace` | 10% | 语速健康度（100-200字/分钟最优） |
| `keyword_boost` | 20% | 高 engagement 关键词命中（中英双语） |

**内置关键词库**：69 个高吸引力词（揭秘/干货/must watch/plot twist 等）

### 平台预设（PlatformPreset）

| 平台 | 宽高比 | 最大时长 |
|------|--------|---------|
| 抖音/小红书/TikTok/Shorts/Reels | 9:16 竖版 | 60s |
| Twitter/X | 1:1 方形 | 140s |

### CPU 友好设计

- **Faster-Whisper**：`int8` 量化，CPU 可运行（`small` 模型 ~1GB RAM）
- **FFmpeg 裁剪**：纯 CPU，无外部 GPU 依赖
- **无外部 API 调用**：评分引擎完全本地计算

### 扩展方式

- **自定义评分权重**：`ClipScorer(weights={"laughter_density": 0.4, ...})`
- **覆盖 Step 实现**：子类化 `ClipRepurposingPipeline`，覆盖 `_extract_audio` / `_split_scenes` / `_transcribe_segments`
- **接入 GPU**：将 `faster-whisper` 改为 `whisper` + CUDA，或使用 ` WhisperX`

---

## 目录结构

```
app/
├── core/                          应用核心（配置/日志/事件总线）
├── plugins/                       插件系统
├── services/                      业务服务层
│   ├── ai/                       AI 服务（LLM/视觉/语音）
│   │   └── providers/             多模型 provider
│   ├── ai_service/               Mock AIService（开发/测试）
│   ├── audio/                    音频处理
│   ├── export/                   导出服务（剪映/PR/FCP/DaVinci）
│   ├── video/                    视频制作工具
│   ├── video_tools/              病毒视频工具（原 viral_video，v3.2.0）
│   ├── orchestration/            编排服务（原 core，v1.2 重命名）
│   │   ├── workflow_engine.py    工作流引擎
│   │   ├── project_manager.py    项目管理
│   │   ├── batch_processor.py    批量处理
│   │   ├── undo_manager.py       撤销管理
│   │   └── prompt_templates.py   提示词模板
│   ├── publish/                  多平台发布
│   └── service_manager.py
├── ui/                           UI 层（PyQt6）
│   ├── common/                   macOS 专用组件
│   ├── components/               原子组件库
│   │   ├── buttons/
│   │   ├── containers/           preview_panel / project_card / video_player
│   │   ├── inputs/
│   │   ├── labels/
│   │   ├── layout/
│   │   ├── loading/              skeleton / pulse_indicator
│   │   └── onboarding/           feature_tour / welcome_screen
│   ├── main/                     主应用
│   │   ├── components/           主窗口组件（timeline/preview/export_panel）
│   │   ├── dialogs/
│   │   ├── layouts/
│   │   ├── pages/                页面（home/projects/video_editor/ai_chat）
│   │   ├── constants.py           UI 常量
│   │   ├── event_handler.py       事件处理器
│   │   └── main_window.py        主窗口入口
│   └── theme/                    主题管理
└── utils/                        工具函数
```

## 重构记录

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 0 | 死代码清理（main_window.py/splash_screen.py/macOS_migration.py 移至 scripts/） | ✅ v3.2 |
| Phase 1 | viral_video → video_tools，目录重命名 + 导入路径全量更新 | ✅ v3.2 |
| Phase 2 | services/core → services/orchestration，消除与 app/core/ 命名冲突 | ✅ v3.2 |
| Phase 3 | UI 组件专业化（UI 结构已较清晰，暂缓大范围重构） | ⏸ 暂缓 |

**命名冲突说明**：`app/core/`（应用核心）与 `app/services/core/`（编排服务）是两个不同目录，Python 按完整路径解析，无运行时冲突，但语义上已通过重命名消除歧义。
