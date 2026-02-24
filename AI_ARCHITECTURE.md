# CineFlow AI 剪辑系统架构

## 核心定位
**AI 驱动的智能视频创作工具**，区别于传统剪辑软件（如 Premiere、Final Cut）的手动操作，CineFlow 通过 AI 实现自动化创作。

---

## 3 大创作模式

| 模式 | 英文 | 说明 | 核心模块 |
|------|------|------|----------|
| 🎙️ **AI视频解说** | Commentary | 原视频 + AI 配音 + 动态字幕 | CommentaryMaker |
| 🎵 **AI视频混剪** | Mashup | 多素材 + 节拍匹配 + 自动转场 | MashupMaker |
| 🎭 **AI第一人称独白** | Monologue | 画面情感分析 + 情感独白 + 电影字幕 | MonologueMaker |

---

## 9 步标准化工作流

```
导入 → AI分析 → 模式选择 → 脚本生成 → 脚本编辑 → 时间轴 → 配音 → 预览 → 导出
```

### 步骤详解

| 步骤 | 说明 | 核心功能 |
|------|------|----------|
| 1. IMPORT | 导入素材 | 视频文件、图片、音频 |
| 2. ANALYZE | AI 分析 | 场景分析、内容理解 |
| 3. MODE_SELECT | 模式选择 | 选择创作模式 |
| 4. SCRIPT_GENERATE | 脚本生成 | LLM 生成文案 |
| 5. SCRIPT_EDIT | 脚本编辑 | 用户修改文案 |
| 6. TIMELINE | 时间轴编排 | 自动对齐时间轴 |
| 7. VOICEOVER | AI 配音 | TTS 生成配音 |
| 8. PREVIEW | 预览 | 实时预览效果 |
| 9. EXPORT | 导出 | 输出到剪映/PR/达芬奇 |

---

## 核心 AI 能力

### 1. 场景分析 (SceneAnalyzer)
```python
analyzer = SceneAnalyzer()
scenes = analyzer.analyze('video.mp4')
# 输出: 场景列表 + 关键帧 + 适用性评分
```

### 2. 文案生成 (ScriptGenerator)
```python
generator = ScriptGenerator()
script = generator.generate(
    topic="电影解说",
    style=ScriptStyle.COMMENTARY,
    duration=60
)
```
- 支持: Qwen3, Kimi, GLM-5, OpenAI

### 3. 语音合成 (VoiceGenerator)
```python
voice = VoiceGenerator()
audio = voice.generate(script, voice_config)
```
- Edge TTS (免费)
- OpenAI TTS

### 4. 字幕生成 (CaptionGenerator)
```python
captions = CaptionGenerator().generate(audio)
# 动态字幕 + 样式风格
```

### 5. 音画同步 (BeatDetector + SyncEngine)
```python
beats = BeatDetector().detect(bgm_path)
timeline = SyncEngine().sync(beats, clips)
# 4 种同步策略
```

---

## 导出格式

| 格式 | 说明 | 用途 |
|------|------|------|
| 📱 **剪映** | Draft JSON | 导入剪映继续编辑 |
| 🎬 **Premiere** | XML | 导入 Pr |
| 🍎 **Final Cut** | FCPXML | 导入 FCPX |
| 🎞️ **DaVinci** | DaVinci | 导入达芬奇 |
| 🎥 **MP4** | 直接导出 | 直接输出视频 |
| 📄 **SRT/ASS** | 字幕文件 | 字幕投稿 |

---

## 技术栈

- **UI**: PyQt6
- **AI**: OpenAI, Anthropic, Google, 阿里 Qwen, 月之 Kimi, 智谱 GLM
- **音视频**: FFmpeg, OpenCV, librosa
- **导出**: 剪映草稿、Pr XML、FCP XML、DaVinci
