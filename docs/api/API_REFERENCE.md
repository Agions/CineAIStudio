# CineFlow AI API 参考

## AI 服务

### LLMManager — LLM 管理器

```python
from app.services.ai.llm_manager import LLMManager, load_llm_config

config = load_llm_config("config/llm.yaml")
manager = LLMManager(config)

# 异步生成文本
response = await manager.generate(LLMRequest(
    prompt="根据画面描述生成解说文案",
    system_prompt="你是专业的视频解说文案编辑",
    max_tokens=500,
))
print(response.content)
```

### VisionAnalyzerFactory — 多模型视觉分析

```python
from app.services.ai.vision_providers import VisionAnalyzerFactory

factory = VisionAnalyzerFactory(config)
result = factory.analyze_with_fallback(image_base64)
# 自动 fallback: OpenAI → 通义千问 → Gemini
```

### VideoContentAnalyzer — 视频内容分析

```python
from app.services.ai.video_content_analyzer import VideoContentAnalyzer

analyzer = VideoContentAnalyzer(vision_api_key="sk-xxx")
result = analyzer.analyze("video.mp4")

print(f"摘要: {result.summary}")
print(f"情感: {result.main_emotion.value}")
print(f"关键帧: {len(result.keyframes)} 个")
```

### VoiceGenerator — AI 配音

```python
from app.services.ai.voice_generator import VoiceGenerator, VoiceConfig

# 免费 Edge TTS
gen = VoiceGenerator(provider="edge")
result = gen.generate(
    text="欢迎观看这个视频",
    output_path="voice.mp3",
    config=VoiceConfig(voice_id="zh-CN-XiaoxiaoNeural", rate=1.05),
)
print(f"时长: {result.duration:.1f}s")
```

## 导出服务

### 剪映导出

```python
from app.services.export.jianying_exporter import JianyingDraftGenerator
exporter = JianyingDraftGenerator()
exporter.export(project, "output/draft.json")
```

### 达芬奇导出

```python
from app.services.export.davinci_exporter import DaVinciExporter, DaVinciTimeline

timeline = DaVinciTimeline(name="My Project", fps=30)
timeline.video_clips.append(DaVinciClip(...))

exporter = DaVinciExporter()
exporter.export(timeline, "output/project.fcpxml")
```

### 字幕独立导出

```python
from app.services.export.davinci_exporter import SubtitleExporter

subs = [
    {"start": 0.0, "end": 3.5, "text": "第一句话"},
    {"start": 4.0, "end": 7.0, "text": "第二句话"},
]

SubtitleExporter.export_srt(subs, "output/sub.srt")
SubtitleExporter.export_ass(subs, "output/sub.ass", font="PingFang SC")
```

## 核心模块

### TaskQueue — 任务队列

```python
from app.core.task_queue import get_task_queue, TaskPriority

queue = get_task_queue()
task_id = queue.submit(
    my_heavy_function, arg1, arg2,
    name="视频渲染",
    priority=TaskPriority.HIGH,
)

queue.task_completed.connect(lambda tid, result: print(f"完成: {tid}"))
```

### AsyncBridge — 异步桥接

```python
from app.core.async_bridge import get_async_bridge

bridge = get_async_bridge()

# 在 PyQt UI 中调用 async 函数
bridge.run_async(
    llm_manager.generate(request),
    callback=lambda result: label.setText(result.content),
)
```

### UnifiedConfig — 统一配置

```python
from app.core.unified_config import get_config

config = get_config()
provider = config.get("LLM.default_provider", "qwen")
config.set("video.cache_enabled", False)
```

### BatchVideoProcessor — 批量处理

```python
from app.services.video_service.batch_processor import BatchVideoProcessor

processor = BatchVideoProcessor()
job_id = processor.create_job(
    video_paths=["a.mp4", "b.mp4", "c.mp4"],
    output_dir="output/",
)

processor.job_completed.connect(lambda jid, summary: print(summary))
processor.start_job(job_id, process_func=my_process_func)
```

### TemplateManager — 项目模板

```python
from app.core.templates.project_templates import TemplateManager

mgr = TemplateManager(user_template_dir="~/.cineflow/templates")

# 列出所有模板
for t in mgr.list_templates():
    print(f"{t.icon} {t.name} - {t.description}")

# 获取模板
template = mgr.get_template("movie_commentary")
print(f"配音: {template.voice.voice_id}")
print(f"导出: {template.export.format}")
```
