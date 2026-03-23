# Script Generator

The Script Generator creates AI-powered video scripts using large language models.

## Overview

`ScriptGenerator` generates scripts for different video creation modes:
- Commentary (解说)
- Mashup (混剪)
- Monologue (独白)

## Usage

```python
from app.services.ai.script_generator import ScriptGenerator

# Initialize with provider
generator = ScriptGenerator(provider="openai")

# Generate commentary script
script = generator.generate(
    video_path="input.mp4",
    mode="commentary",
    style="educational",
    duration=60  # Target duration in seconds
)
```

## Supported Providers

| Provider | Models |
|----------|--------|
| OpenAI | gpt-5.3 |
| Anthropic | claude-sonnet-4.5 |
| Google | gemini-3.1-flash |
| 阿里云 | qwen-3.5 |
| DeepSeek | r1, v3.2 |
| 智谱AI | glm-5 |
| 月之暗面 | kimi-k2.5 |

## Methods

### `generate(video_path, mode, style, duration)`

Generates a script based on video analysis.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `video_path` | str | Path to video file |
| `mode` | str | Creation mode: `commentary`, `mashup`, `monologue` |
| `style` | str | Script style |
| `duration` | int | Target duration in seconds |

**Returns:**

```python
{
    "script": [
        {
            "start": 0.0,
            "end": 5.0,
            "text": "Welcome to this tutorial...",
            "scene": "intro"
        },
        # ... more segments
    ],
    "total_duration": 60,
    "word_count": 150
}
```

### `generate_with_prompt(prompt, context)`

Generate with custom prompt.

```python
script = generator.generate_with_prompt(
    prompt="Write a compelling intro for a tech product review",
    context={"product": "Smartphone X", "audience": "tech enthusiasts"}
)
```

## Script Modes

### Commentary Mode

Creates narration scripts synchronized to video content.

```python
script = generator.generate(
    video_path="input.mp4",
    mode="commentary",
    style="friendly",
    duration=120
)
```

### Mashup Mode

Generates short, punchy segments for video mashups.

```python
script = generator.generate(
    video_path="input.mp4",
    mode="mashup",
    style="energetic",
    duration=60
)
```

### Monologue Mode

Creates first-person narrative scripts.

```python
script = generator.generate(
    video_path="input.mp4",
    mode="monologue",
    style="emotional",
    duration=180
)
```

## Customization

### Custom Prompts

Edit prompts in `config/prompts/`:

```yaml
commentary:
  system: "You are a professional video narrator..."
  user_template: "Create a {{style}} commentary for this video..."
```

### Temperature Settings

Adjust creativity level:

```python
generator = ScriptGenerator(
    provider="openai",
    temperature=0.7  # 0.0 = factual, 1.0 = creative
)
```
