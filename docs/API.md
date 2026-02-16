# CineFlow API 文档

> 多Agent智能视频剪辑系统接口文档

## 目录

- [Agent API](#agent-api)
- [核心服务 API](#核心服务-api)
- [LLM 客户端 API](#llm-客户端-api)
- [UI 组件 API](#ui-组件-api)

---

## Agent API

### BaseAgent

所有Agent的基类。

```python
from app.agents import BaseAgent, AgentCapability, AgentResult

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="my_agent_001",
            name="My Agent",
            capabilities=[AgentCapability.EDITING]
        )
        self.init_llm('editor')
        
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        # 实现任务逻辑
        return AgentResult(
            success=True,
            data={'result': 'done'},
            message='任务完成'
        )
```

#### 方法

| 方法 | 说明 | 参数 | 返回 |
|------|------|------|------|
| `init_llm(agent_type)` | 初始化LLM | `agent_type: str` | `None` |
| `call_llm(prompt, **kwargs)` | 调用大模型 | `prompt: str` | `Dict[str, Any]` |
| `send_message(receiver, type, content)` | 发送消息 | `receiver: str, type: str, content: dict` | `None` |
| `report_progress(progress, message)` | 报告进度 | `progress: int, message: str` | `None` |
| `execute(task)` | 执行任务（抽象） | `task: dict` | `AgentResult` |
| `run(task)` | 运行任务（包装） | `task: dict` | `AgentResult` |
| `get_stats()` | 获取统计 | - | `dict` |

#### 信号

| 信号 | 参数 | 说明 |
|------|------|------|
| `state_changed` | `(agent_id, state)` | 状态变化 |
| `progress_updated` | `(agent_id, progress, message)` | 进度更新 |
| `task_completed` | `(agent_id, result)` | 任务完成 |
| `error_occurred` | `(agent_id, error)` | 发生错误 |

### AgentManager

管理所有Agent的生命周期和任务调度。

```python
from app.agents import AgentManager

manager = AgentManager()
manager.register_agent(MyAgent())
manager.start()

# 创建任务
task_id = manager.create_task('editing', {
    'video_path': '/path/to/video.mp4',
    'cuts': [(0, 10), (20, 30)]
})
```

#### 方法

| 方法 | 说明 | 参数 | 返回 |
|------|------|------|------|
| `register_agent(agent)` | 注册Agent | `agent: BaseAgent` | `str` (agent_id) |
| `unregister_agent(agent_id)` | 注销Agent | `agent_id: str` | `bool` |
| `get_agent(agent_id)` | 获取Agent | `agent_id: str` | `BaseAgent \| None` |
| `create_task(type, params)` | 创建任务 | `type: str, params: dict` | `str` (task_id) |
| `cancel_task(task_id)` | 取消任务 | `task_id: str` | `bool` |
| `get_system_stats()` | 获取系统统计 | - | `dict` |
| `start()` | 启动管理器 | - | `None` |
| `stop()` | 停止管理器 | - | `None` |

---

## 核心服务 API

### VideoProcessor

视频处理服务。

```python
from app.core import VideoProcessor

processor = VideoProcessor()

# 获取视频信息
info = processor.get_video_info('/path/to/video.mp4')
print(f"分辨率: {info.width}x{info.height}, 时长: {info.duration}s")

# 提取关键帧
frames = processor.extract_keyframes(
    video_path='/path/to/video.mp4',
    output_dir='/output/frames',
    interval=1.0
)
```

#### 方法

| 方法 | 说明 | 参数 | 返回 |
|------|------|------|------|
| `get_video_info(path)` | 获取视频信息 | `path: str` | `VideoInfo` |
| `process_video(input, config, callback)` | 处理视频 | `input: str, config: ProcessingConfig, callback: callable` | `str` (output_path) |
| `extract_keyframes(video, output, interval, max_frames)` | 提取关键帧 | `video: str, output: str, interval: float, max_frames: int` | `List[str]` |
| `cut_video(video, start, end, output, reencode)` | 剪辑视频 | `video: str, start: float, end: float, output: str, reencode: bool` | `str` |
| `merge_videos(videos, output, transition)` | 合并视频 | `videos: List[str], output: str, transition: str` | `str` |
| `detect_scenes(video, threshold)` | 场景检测 | `video: str, threshold: float` | `List[dict]` |
| `apply_lut(video, lut, output, intensity)` | 应用LUT | `video: str, lut: str, output: str, intensity: float` | `str` |
| `batch_process(videos, config, callback)` | 批量处理 | `videos: List[str], config: ProcessingConfig, callback: callable` | `List[str]` |

#### VideoInfo

| 属性 | 类型 | 说明 |
|------|------|------|
| `path` | `str` | 文件路径 |
| `duration` | `float` | 时长（秒） |
| `width` | `int` | 宽度 |
| `height` | `int` | 高度 |
| `fps` | `float` | 帧率 |
| `bitrate` | `int` | 码率 |
| `codec` | `str` | 视频编码 |
| `frame_count` | `int` | 帧数 |

### AudioEngine

音频处理服务。

```python
from app.core import AudioEngine

engine = AudioEngine()

# 生成配音
audio_path = engine.generate_tts(
    text="这是一段测试文案",
    output_path='/output/audio.mp3',
    voice='zh-CN-XiaoxiaoNeural'
)

# 检测节拍
beats = engine.detect_beats('/path/to/music.mp3')
```

#### 方法

| 方法 | 说明 | 参数 | 返回 |
|------|------|------|------|
| `extract_audio(video, output)` | 提取音频 | `video: str, output: str` | `str` |
| `merge_audio_video(video, audio, output)` | 合并音视频 | `video: str, audio: str, output: str` | `str` |
| `generate_tts(text, output, voice, speed)` | TTS配音 | `text: str, output: str, voice: str, speed: float` | `str` |
| `detect_beats(audio_path)` | 检测节拍 | `audio_path: str` | `List[float]` |
| `normalize_audio(input_path, output_path)` | 音频标准化 | `input_path: str, output_path: str` | `str` |
| `mix_audios(audio_paths, output_path, volumes)` | 混音 | `audio_paths: List[str], output_path: str, volumes: List[float]` | `str` |

### DraftExporter

剪映草稿导出服务。

```python
from app.core import DraftExporter

exporter = DraftExporter()

# 导出剪映草稿
draft_path = exporter.export_to_jianying(
    project_name='我的项目',
    video_files=['/path/video1.mp4', '/path/video2.mp4'],
    output_dir='/output'
)
```

#### 方法

| 方法 | 说明 | 参数 | 返回 |
|------|------|------|------|
| `export_to_jianying(name, videos, output, platform)` | 导出剪映草稿 | `name: str, videos: List[str], output: str, platform: str` | `str` |
| `add_track(draft, track_type, media_path)` | 添加轨道 | `draft: dict, track_type: str, media_path: str` | `dict` |
| `add_segment(track, start, duration, media_path)` | 添加片段 | `track: dict, start: float, duration: float, media_path: str` | `dict` |
| `add_text(draft, text, start, duration, position)` | 添加文字 | `draft: dict, text: str, start: float, duration: float, position: str` | `dict` |

### ProjectManager

项目管理服务。

```python
from app.core import ProjectManager, ProjectStatus

manager = ProjectManager()

# 创建项目
project = manager.create_project(
    name='我的视频项目',
    source_files=['/path/video1.mp4', '/path/video2.mp4'],
    config={'resolution': '1080p'}
)

# 更新状态
manager.update_project_status(project.id, ProjectStatus.EDITING)
```

#### 方法

| 方法 | 说明 | 参数 | 返回 |
|------|------|------|------|
| `create_project(name, source_files, config)` | 创建项目 | `name: str, source_files: List[str], config: dict` | `Project` |
| `get_project(project_id)` | 获取项目 | `project_id: str` | `Project \| None` |
| `get_all_projects()` | 获取所有项目 | - | `List[Project]` |
| `update_project_status(id, status)` | 更新状态 | `id: str, status: ProjectStatus` | `bool` |
| `update_agent_result(id, agent, result)` | 更新Agent结果 | `id: str, agent: str, result: dict` | `bool` |
| `delete_project(project_id)` | 删除项目 | `project_id: str` | `bool` |
| `export_project(project_id, export_path)` | 导出项目 | `project_id: str, export_path: str` | `str` |
| `get_project_stats()` | 获取统计 | - | `dict` |

---

## LLM 客户端 API

### LLMClient

统一的大模型客户端。

```python
from app.agents import LLMClient

# 为特定Agent创建客户端
client = LLMClient.for_agent('editor')

# 调用大模型
response = await client.complete(
    prompt="分析这段视频的内容",
    system_prompt="你是一个专业的视频剪辑师",
    temperature=0.7,
    max_tokens=2000
)

if response.success:
    print(response.content)
```

#### 方法

| 方法 | 说明 | 参数 | 返回 |
|------|------|------|------|
| `for_agent(agent_type)` | 为Agent创建客户端（类方法） | `agent_type: str` | `LLMClient` |
| `complete(prompt, system_prompt, temperature, max_tokens, stream)` | 文本生成 | `prompt: str, system_prompt: str, temperature: float, max_tokens: int, stream: bool` | `LLMResponse` |
| `analyze_image(image_path, prompt)` | 图像分析 | `image_path: str, prompt: str` | `LLMResponse` |
| `analyze_video_frame(video_path, timestamp, prompt)` | 视频帧分析 | `video_path: str, timestamp: float, prompt: str` | `LLMResponse` |
| `get_stats()` | 获取统计 | - | `dict` |

#### LLMResponse

| 属性 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 是否成功 |
| `content` | `str` | 生成内容 |
| `usage` | `dict` | Token用量 |
| `latency` | `float` | 延迟（秒） |
| `error` | `str \| None` | 错误信息 |
| `model` | `str` | 使用的模型 |

---

## UI 组件 API

### MainWindow

主窗口。

```python
from app.ui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication

app = QApplication([])
window = MainWindow()
window.show()
app.exec()
```

#### 信号

| 信号 | 参数 | 说明 |
|------|------|------|
| `project_created` | `(project_id: str)` | 项目创建 |

### AgentCard

Agent状态卡片。

```python
from app.ui.main_window import AgentCard
from app.agents import AgentState

card = AgentCard(
    name="Editor",
    agent_type="剪辑 - 粗剪精剪",
    model="Kimi K2.5"
)

# 更新状态
card.update_status(
    state=AgentState.WORKING,
    progress=50,
    message="正在分析视频..."
)
```

---

## 配置

### 环境变量

| 变量 | 说明 | 必需 |
|------|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API密钥 | 是 |
| `MOONSHOT_API_KEY` | Moonshot API密钥 | 是 |
| `DASHSCOPE_API_KEY` | 阿里云DashScope密钥 | 是 |
| `BAIDU_API_KEY` | 百度API密钥 | 否 |
| `BAIDU_SECRET_KEY` | 百度Secret密钥 | 否 |
| `FFMPEG_PATH` | FFmpeg路径 | 否 |

---

## 示例

### 完整工作流示例

```python
import asyncio
from app.agents import AgentManager, DirectorAgent, EditorAgent
from app.core import ProjectManager

async def main():
    # 初始化
    manager = AgentManager()
    manager.register_agent(DirectorAgent())
    manager.register_agent(EditorAgent())
    manager.start()
    
    project_manager = ProjectManager()
    
    # 创建项目
    project = project_manager.create_project(
        name="测试项目",
        source_files=["/path/video.mp4"]
    )
    
    # 创建剪辑任务
    task_id = manager.create_task('editing', {
        'project_id': project.id,
        'video_path': '/path/video.mp4',
        'style': 'vlog'
    })
    
    # 等待任务完成
    while True:
        task = manager.get_task(task_id)
        if task.status.name in ['COMPLETED', 'FAILED']:
            break
        await asyncio.sleep(1)
    
    print(f"任务结果: {task.result}")
    
    # 清理
    manager.stop()

if __name__ == '__main__':
    asyncio.run(main())
```

---

## 更多信息

- [项目主页](../README.md)
- [安装指南](../INSTALL.md)
- [开发路线](../ROADMAP.md)
