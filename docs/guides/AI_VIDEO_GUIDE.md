# 🎬 VideoForge - AI 视频创作工具

> 打造爆款短视频，一键生成剪映草稿

VideoForge 是一款 AI 驱动的视频创作工具，专注于**爆款短视频制作**，支持一键导出**剪映草稿**格式。

## ✨ 核心功能

| 功能                   | 说明                           | 状态 |
| ---------------------- | ------------------------------ | ---- |
| 🎙️ **AI 视频解说**     | 原视频 + AI解说配音 + 动态字幕 | ✅   |
| 🎵 **AI 视频混剪**     | 多素材智能剪辑 + 节奏匹配      | ✅   |
| 🎭 **AI 第一人称独白** | 原视频 + 情感独白 + 电影字幕   | ✅   |
| 📦 **剪映草稿导出**    | 完美适配剪映编辑               | ✅   |

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量（可选）

```bash
# 用于 AI 文案生成（如果不设置，可使用自定义文案）
export OPENAI_API_KEY="your-api-key"
```

### 3. 运行示例

```bash
python examples/quick_start.py
```

## 📖 使用指南

### AI 视频解说

将原视频转换为带有 AI 解说的视频：

```python
from app.services.video import CommentaryMaker, CommentaryStyle

# 创建制作器
maker = CommentaryMaker(voice_provider="edge")

# 创建项目
project = maker.create_project(
    source_video="movie_clip.mp4",
    topic="这部电影讲述了一个感人的故事",
    style=CommentaryStyle.STORYTELLING,
)

# 生成解说（可使用自定义文案）
custom_script = """
欢迎来到今天的影评。

这部电影讲述了一个关于勇气和牺牲的故事...

让我们一起深入分析它的精彩之处。
"""
maker.generate_script(project, custom_script=custom_script)

# 生成配音
maker.generate_voice(project)

# 生成字幕
maker.generate_captions(project)

# 导出到剪映
draft_path = maker.export_to_jianying(project, "/path/to/jianying/drafts")
print(f"剪映草稿已导出: {draft_path}")
```

### AI 视频混剪

将多个视频素材智能混剪：

```python
from app.services.video import MashupMaker, MashupStyle

maker = MashupMaker()

# 创建项目
project = maker.create_project(
    source_videos=["clip1.mp4", "clip2.mp4", "clip3.mp4"],
    background_music="bgm.mp3",
    target_duration=30.0,
    style=MashupStyle.FAST_PACED,  # 快节奏
)

# 自动混剪（智能选择片段、匹配节奏）
maker.auto_mashup(project)

# 导出
draft_path = maker.export_to_jianying(project, "/path/to/jianying/drafts")
```

**混剪风格选项：**

- `FAST_PACED` - 快节奏（适合动感音乐）
- `CINEMATIC` - 电影感（适合大气音乐）
- `VLOG` - Vlog 风格（自然过渡）
- `HIGHLIGHT` - 高光集锦（体育/游戏）
- `MONTAGE` - 蒙太奇（情感叙事）

### AI 第一人称独白

为视频添加沉浸式独白：

```python
from app.services.video import MonologueMaker, MonologueStyle

maker = MonologueMaker(voice_provider="edge")

# 创建项目
project = maker.create_project(
    source_video="night_walk.mp4",
    context="深夜独自走在下过雨的街道上",
    emotion="惆怅",
    style=MonologueStyle.MELANCHOLIC,
)

# 生成独白
custom_script = """
有些路，只能一个人走。

夜深了，霓虹灯还在闪烁，我的影子被拉得很长很长。

这座城市从不缺少热闹，只是热闹从来都不属于我。
"""
maker.generate_script(project, custom_script=custom_script)

# 生成配音
maker.generate_voice(project)

# 生成电影级字幕
maker.generate_captions(project, style="cinematic")

# 导出
draft_path = maker.export_to_jianying(project, "/path/to/jianying/drafts")
```

**独白风格选项：**

- `MELANCHOLIC` - 惆怅/忧郁
- `INSPIRATIONAL` - 励志/向上
- `ROMANTIC` - 浪漫/温馨
- `MYSTERIOUS` - 神秘/悬疑
- `NOSTALGIC` - 怀旧/追忆
- `PHILOSOPHICAL` - 哲思/沉思
- `HEALING` - 治愈/温暖

### 剪映草稿导出

直接创建剪映草稿：

```python
from app.services.export import (
    JianyingExporter, JianyingConfig,
    Track, TrackType, Segment, TimeRange,
    VideoMaterial, AudioMaterial, TextMaterial,
)

# 创建导出器
exporter = JianyingExporter(JianyingConfig(
    canvas_ratio="9:16",  # 竖屏短视频
    copy_materials=True,   # 复制素材到草稿目录
))

# 创建草稿
draft = exporter.create_draft("我的视频项目")

# 添加视频轨道
video_track = Track(type=TrackType.VIDEO, attribute=1)
draft.add_track(video_track)

# 添加视频素材
video_material = VideoMaterial(path="/path/to/video.mp4")
draft.add_video(video_material)

# 添加片段
segment = Segment(
    material_id=video_material.id,
    source_timerange=TimeRange.from_seconds(0, 10),
    target_timerange=TimeRange.from_seconds(0, 10),
)
video_track.add_segment(segment)

# 导出
draft_path = exporter.export(draft, "/path/to/jianying/drafts")
```

### 转场效果

应用视频转场效果：

```python
from app.services.video import TransitionEffects, TransitionType, TransitionConfig

effects = TransitionEffects()

# 应用淡入淡出
effects.apply_transition(
    video1="clip1.mp4",
    video2="clip2.mp4",
    output_path="output.mp4",
    config=TransitionConfig(
        type=TransitionType.FADE,
        duration=0.5,
    )
)

# 批量应用转场
effects.apply_batch_transitions(
    videos=["clip1.mp4", "clip2.mp4", "clip3.mp4"],
    output_path="final.mp4",
    transition_type=TransitionType.DISSOLVE,
    transition_duration=0.8,
)
```

**可用转场类型：**

- `CUT` - 硬切
- `FADE` / `FADE_BLACK` / `FADE_WHITE` - 淡入淡出
- `DISSOLVE` - 交叉溶解
- `WIPE_LEFT` / `WIPE_RIGHT` / `WIPE_UP` / `WIPE_DOWN` - 擦除
- `SLIDE_LEFT` / `SLIDE_RIGHT` - 滑动
- `ZOOM_IN` / `ZOOM_OUT` - 缩放
- `BLUR` - 模糊过渡
- `CIRCLE_OPEN` - 圆形展开

### 并行处理

加速批量任务：

```python
from app.services.video import ParallelProcessor

processor = ParallelProcessor(max_workers=4)

# 进度回调
def on_progress(completed, total, desc):
    print(f"[{desc}] {completed}/{total}")

processor.set_progress_callback(on_progress)

# 并行生成配音
results = processor.parallel_generate_voice(
    texts=["你好", "世界", "测试"],
    output_dir="./audio"
)

# 并行分析场景
results = processor.parallel_analyze_scenes(
    video_paths=["video1.mp4", "video2.mp4"]
)

# 查看统计
processor.print_stats()
```

## 📁 项目结构

```
VideoForge/
├── app/
│   └── services/
│       ├── ai/                      # AI 服务
│       │   ├── scene_analyzer.py    # 场景分析
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
├── examples/
│   └── quick_start.py              # 快速开始示例
│
├── requirements.txt                 # 依赖文件
└── PROJECT_PLAN.md                  # 项目规划
```

## 🔧 技术栈

- **配音**: Edge TTS (免费) / OpenAI TTS
- **视频处理**: FFmpeg
- **场景分析**: FFmpeg + 自定义算法
- **节拍检测**: librosa
- **文案生成**: OpenAI GPT-4 (可选)

## 📋 环境要求

- Python 3.10+
- FFmpeg (必需)
- 可选: librosa (用于音乐节拍检测)

## 🎯 剪映草稿兼容性

导出的草稿完全兼容剪映电脑版：

- ✅ 视频轨道正确显示
- ✅ 音频轨道正确显示
- ✅ 字幕轨道正确显示
- ✅ 时间轴准确
- ✅ 素材路径正确

## 📝 使用建议

1. **准备优质素材**：视频清晰度至少 720p
2. **选择合适风格**：根据内容选择解说/混剪/独白风格
3. **自定义文案**：如果没有 OpenAI API，可使用自定义文案
4. **使用免费配音**：Edge TTS 完全免费，质量也很好
5. **剪映精修**：导出草稿后可在剪映中进一步编辑

## 🔗 相关技能

本项目参考了以下技能：

- `video-viral-creator` - 爆款视频标准
- `video-ffmpeg-expert` - FFmpeg 最佳实践
- `video-performance` - 性能优化
- `video-api-patterns` - API 设计模式

---

**版本**: v1.5  
**最后更新**: 2026-02-02
