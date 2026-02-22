# CineFlow AI 架构文档

## 概览

CineFlow AI 是一款基于 Python + PyQt6 的 AI 视频创作桌面工具。

```
CineFlow AI/
├── app/
│   ├── core/               # 核心模块
│   │   ├── application.py         # 应用生命周期管理
│   │   ├── async_bridge.py        # 异步桥接（PyQt ↔ asyncio）
│   │   ├── config_manager.py      # 配置管理器
│   │   ├── unified_config.py      # 统一配置加载器
│   │   ├── event_bus.py           # 事件发布/订阅
│   │   ├── service_registry.py    # 高级服务注册表（DI）
│   │   ├── service_bootstrap.py   # 服务引导程序
│   │   ├── task_queue.py          # 异步任务队列
│   │   ├── logger.py              # 日志
│   │   ├── exceptions.py          # 统一异常定义
│   │   ├── interfaces/            # 接口抽象层
│   │   └── templates/             # 项目模板系统
│   │
│   ├── services/            # 业务服务层
│   │   ├── ai/                    # AI 服务
│   │   │   ├── base_LLM_provider.py    # LLM 提供者基类
│   │   │   ├── llm_manager.py          # LLM 管理器（多模型切换）
│   │   │   ├── vision_providers.py     # 多模型视觉分析
│   │   │   ├── scene_analyzer.py       # 场景分析
│   │   │   ├── video_content_analyzer.py # 视频内容深度分析
│   │   │   ├── script_generator.py     # 文案生成
│   │   │   ├── voice_generator.py      # AI 配音（Edge/OpenAI）
│   │   │   └── providers/              # LLM 提供者实现
│   │   │       ├── qwen.py             # 通义千问
│   │   │       ├── kimi.py             # Kimi
│   │   │       ├── glm5.py             # 智谱 GLM-5
│   │   │       ├── claude.py           # Claude
│   │   │       ├── gemini.py           # Gemini
│   │   │       └── local.py            # 本地模型（Ollama）
│   │   │
│   │   ├── video/                 # 视频制作
│   │   │   ├── commentary_maker.py     # 解说视频
│   │   │   ├── mashup_maker.py         # 混剪视频
│   │   │   ├── monologue_maker.py      # 独白视频
│   │   │   └── transition_effects.py   # 转场效果
│   │   │
│   │   ├── video_service/         # 视频底层服务
│   │   │   ├── gpu_renderer.py         # GPU 加速渲染
│   │   │   ├── batch_processor.py      # 批量处理
│   │   │   └── video_analyzer.py       # 视频分析
│   │   │
│   │   └── export/                # 导出
│   │       ├── jianying_exporter.py    # 剪映草稿
│   │       ├── premiere_exporter.py    # Premiere
│   │       ├── finalcut_exporter.py    # Final Cut Pro
│   │       ├── davinci_exporter.py     # 达芬奇 + 字幕导出
│   │       └── video_exporter.py       # 视频文件
│   │
│   ├── viewmodels/          # ViewModel 层（MVVM）
│   │   ├── base_viewmodel.py           # 基类
│   │   └── ai_video_creator_vm.py      # AI 视频创作 VM
│   │
│   ├── ui/                  # UI 层（PyQt6）
│   │   ├── main/                  # 主窗口和页面
│   │   ├── components/            # 通用组件
│   │   ├── common/                # 公共 UI 模块
│   │   └── theme/                 # 主题
│   │
│   ├── plugins/             # 插件系统
│   └── monitoring/          # 性能监控
│
├── config/                  # 配置文件
│   └── llm.yaml                   # LLM 配置
├── resources/               # 静态资源（图标、样式）
├── tests/                   # 测试
└── docs/                    # 文档
```

## 核心设计模式

### 1. 依赖注入（DI）

使用 `ServiceRegistry` 管理所有服务的注册、解析和生命周期。

```python
from app.core.service_bootstrap import get_service

# 获取服务
llm_manager = get_service("llm_manager")
```

### 2. MVVM 模式

UI 层 → ViewModel → Service 层，通过 Qt 信号通信。

```python
# ViewModel 持有业务逻辑
vm = AIVideoCreatorViewModel(llm_manager=llm, scene_analyzer=analyzer)
vm.analysis_completed.connect(ui.on_analysis_done)  # 信号绑定 UI
vm.analyze_video()  # 后台执行，完成后信号通知
```

### 3. 异步桥接

PyQt6 是同步的，LLM 调用是 async 的。`AsyncBridge` 解决这个矛盾：

```python
from app.core.async_bridge import get_async_bridge

bridge = get_async_bridge()
bridge.run_async(llm_manager.generate(request), callback=on_done)
```

### 4. 事件驱动

`EventBus` 用于模块间松耦合通信：

```python
event_bus.subscribe("video.analyzed", on_video_analyzed)
event_bus.publish("video.analyzed", {"result": analysis})
```

## 配置体系

统一配置加载器 `UnifiedConfig` 合并多源配置：

```python
from app.core.unified_config import get_config

config = get_config()
provider = config.get("LLM.default_provider")  # 点号路径
timeout = config.get("LLM.timeout", 30)
```

加载优先级：环境变量 > .env > config/*.yaml > 默认值

## LLM 多模型支持

| 提供者 | 文本生成 | 视觉分析 | 配音 |
|--------|---------|---------|------|
| 通义千问 | ✅ | ✅ (VL) | ❌ |
| Kimi | ✅ | ❌ | ❌ |
| GLM-5 | ✅ | ❌ | ❌ |
| Claude | ✅ | ❌ | ❌ |
| Gemini | ✅ | ✅ (Vision) | ❌ |
| OpenAI | ✅ | ✅ (GPT-5) | ✅ (TTS) |
| Edge TTS | ❌ | ❌ | ✅ (免费) |
| 本地 (Ollama) | ✅ | ❌ | ❌ |

## 导出格式支持

| 格式 | 文件 | 说明 |
|------|------|------|
| 剪映 | `.json` 草稿 | 完美适配剪映电脑版 |
| Premiere | `.prproj` XML | Adobe Premiere Pro |
| Final Cut | `.fcpxml` | Final Cut Pro X |
| 达芬奇 | `.fcpxml` | DaVinci Resolve（通过 FCPXML） |
| SRT 字幕 | `.srt` | 通用字幕格式 |
| ASS 字幕 | `.ass` | 高级字幕（支持样式） |
| 视频文件 | `.mp4` | 直接导出视频 |
