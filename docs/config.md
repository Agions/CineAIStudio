# Configuration

Learn how to configure ClipFlowCut for your needs.

## Configuration Files

ClipFlowCut uses multiple configuration sources:

| File | Purpose |
|------|---------|
| `.env` | API keys and secrets |
| `config/app.yaml` | Application settings |
| `config/ai.yaml` | AI provider settings |
| `config/export.yaml` | Export defaults |

## Environment Variables (.env)

Create a `.env` file from the example:

```bash
cp .env.example .env
```

### AI Providers

```env
# OpenAI
OPENAI_API_KEY=sk-your-key

# Anthropic
ANTHROPIC_API_KEY=sk-ant-your-key

# Google
GOOGLE_API_KEY=your-key

# 阿里云
QWEN_API_KEY=your-key

# DeepSeek
DEEPSEEK_API_KEY=sk-your-key

# 智谱AI
ZHIPU_API_KEY=your-key

# 月之暗面
KIMI_API_KEY=your-key

# Ollama (本地)
OLLAMA_BASE_URL=http://localhost:11434
```

### Application Settings

```env
# Logging
LOG_LEVEL=INFO
LOG_FILE=clipflow.log

# Theme
THEME=dark  # dark or light

# Language
LANGUAGE=zh-CN
```

## Application Config (config/app.yaml)

```yaml
application:
  name: ClipFlowCut
  version: 3.0.0
  debug: false

window:
  width: 1280
  height: 720
  theme: dark

cache:
  enabled: true
  directory: ~/.clipflow/cache
  max_size: 1GB

projects:
  default_directory: ~/Documents/ClipFlowCut
  auto_save: true
  auto_save_interval: 300  # seconds
```

## AI Config (config/ai.yaml)

```yaml
providers:
  default: openai

  openai:
    model: gpt-5.3
    temperature: 0.7
    max_tokens: 4000

  anthropic:
    model: claude-sonnet-4.5
    temperature: 0.7

  qwen:
    model: qwen-3.5
    temperature: 0.8

voice:
  default_provider: edge
  default_voice: en-US-AriaNeural
  speed: 1.0
  volume: 1.0
```

## Export Config (config/export.yaml)

```yaml
export:
  default_format: mp4
  default_codec: h264

  formats:
    mp4:
      video_codec: libx264
      audio_codec: aac
      quality: high

    jianying:
      version: "6.0"
      draft_format: json

    premiere:
      version: "2024"
      project_type: rec709

    fcpxml:
      version: "1.10"

    davinci:
      version: "19"
      color_space: rec709
```

## Video Processing

```yaml
video:
  # FFmpeg settings
  ffmpeg:
    threads: 0  # 0 = auto
    preset: medium
    crf: 23

  # Scene detection
  scene_detection:
    algorithm: histogram
    threshold: 30.0
    min_duration: 1.0

  # Resolution presets
  resolution:
    - 1920x1080  # Full HD
    - 1280x720   # HD
    - 854x480    # SD

  # Frame rates
    fps: [24, 25, 30, 60]
```

## Audio Settings

```yaml
audio:
  # Beat detection
  beat_detection:
    algorithm: librosa
    bpm_tolerance: 5

  # Voice settings
  voice:
    sample_rate: 44100
    bit_rate: 128k
    channels: 2
```

## Command Line Options

```bash
# Run with custom config
python main.py --config custom.yaml

# Debug mode
python main.py --debug

# Reset settings
python main.py --reset-config
```

## Advanced Configuration

### Custom FFmpeg Path

```yaml
ffmpeg:
  binary: /usr/local/bin/ffmpeg
  probe: /usr/local/bin/ffprobe
```

### Proxy Settings

```yaml
network:
  proxy:
    enabled: true
    http: http://proxy:8080
    https: https://proxy:8080
```

### Hardware Acceleration

```yaml
video:
  hardware_acceleration:
    enabled: true
    encoder: nvenc  # nvenc, amf, videotoolbox
```
