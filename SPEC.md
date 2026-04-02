# VideoForge 技术规范文档

> 本文档描述 VideoForge 的技术设计决策、架构约束和实现规范。供维护者和贡献者参考。

---

## 版本信息

| 项目 | 版本 | 来源 |
|------|------|------|
| `pyproject.toml` | 3.1.0 | ✅ 唯一真实来源 |
| CHANGELOG.md | 3.1.0 | 与 pyproject.toml 一致 |
| GitHub Releases | v1.0.0 | 历史遗留，待清理 |

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
