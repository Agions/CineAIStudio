# API Overview

This section provides detailed API documentation for VideoForge's core modules.

## Core Modules

VideoForge is organized into several core modules:

| Module | Description |
|--------|-------------|
| `app.core` | Application core, configuration, and project management |
| `app.services.ai` | AI-powered services (scene analysis, script generation, voice synthesis) |
| `app.services.video` | Video processing (commentary, mashup, monologue) |
| `app.services.audio` | Audio processing (beat detection, sync) |
| `app.services.export` | Export engines for various formats |

## Service Architecture

```
┌─────────────────────────────────────────────────┐
│                  UI Layer                        │
│              (PyQt6 Components)                  │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│                Service Layer                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ AI       │ │ Video    │ │ Export           │ │
│  │ Services │ │ Services │ │ Services         │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│                Core Layer                         │
│   Application │ Config │ Project Manager        │
└─────────────────────────────────────────────────┘
```

## Common Use Cases

### 1. Scene Analysis

```python
from app.services.ai.scene_analyzer import SceneAnalyzer

analyzer = SceneAnalyzer()
scenes = analyzer.analyze_video("input.mp4")
```

### 2. Script Generation

```python
from app.services.ai.script_generator import ScriptGenerator

generator = ScriptGenerator(provider="openai")
script = generator.generate(
    video_path="input.mp4",
    mode="commentary",
    style="educational"
)
```

### 3. Voice Synthesis

```python
from app.services.ai.voice_generator import VoiceGenerator

generator = VoiceGenerator(provider="edge")
audio_path = generator.generate(
    text="Hello world!",
    voice="en-US-AriaNeural",
    output="output.mp3"
)
```

### 4. Video Export

```python
from app.services.export.jianying_exporter import JianYingExporter

exporter = JianYingExporter()
exporter.export(project, "output.json")
```

## API Reference

- [Scene Analyzer](./scene-analyzer) - Video scene detection
- [Script Generator](./script-generator) - AI script creation
- [Voice Generator](./voice-generator) - Text-to-speech
