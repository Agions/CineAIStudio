# Voice Generator

The Voice Generator provides AI-powered text-to-speech synthesis.

## Overview

`VoiceGenerator` converts text scripts into natural-sounding speech audio.

## Supported Providers

| Provider | Description |
|----------|-------------|
| Edge TTS | Microsoft Edge text-to-speech |
| OpenAI TTS | OpenAI's voice synthesis |

## Usage

```python
from app.services.ai.voice_generator import VoiceGenerator

# Initialize
generator = VoiceGenerator(provider="edge")

# Generate speech
audio_path = generator.generate(
    text="Hello, welcome to our video!",
    voice="en-US-AriaNeural",
    output="output.mp3"
)
```

## Methods

### `generate(text, voice, output, **kwargs)`

Generates speech from text.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | str | Text to synthesize |
| `voice` | str | Voice identifier |
| `output` | str | Output audio file path |
| `speed` | float | Speech speed (0.5-2.0, default: 1.0) |
| `pitch` | float | Pitch adjustment (-10 to 10) |

**Returns:**

```python
{
    "audio_path": "output.mp3",
    "duration": 3.5,
    "format": "mp3"
}
```

### `get_available_voices()`

List available voices.

```python
voices = generator.get_available_voices()
# Returns list of voice options
```

### `generate_batch(segments, output_dir)`

Generate speech for multiple segments.

```python
segments = [
    {"text": "Hello!", "voice": "en-US-AriaNeural"},
    {"text": "Welcome!", "voice": "en-US-GuyNeural"}
]
generator.generate_batch(segments, "output/")
```

## Available Voices

### Edge TTS Voices

| Voice ID | Language | Gender |
|----------|----------|--------|
| `en-US-AriaNeural` | English (US) | Female |
| `en-US-GuyNeural` | English (US) | Male |
| `en-GB-SoniaNeural` | English (UK) | Female |
| `zh-CN-XiaoxiaoNeural` | Chinese | Female |
| `zh-CN-YunxiNeural` | Chinese | Male |
| `ja-JP-NanamiNeural` | Japanese | Female |
| `ko-KR-SunHiNeural` | Korean | Female |

### OpenAI TTS Voices

| Voice ID | Description |
|----------|-------------|
| `alloy` | Versatile, neutral |
| `echo` | Warm, friendly |
| `fable` | Expressive storytelling |
| `onyx` | Deep, authoritative |
| `nova` | Energetic |
| `shimmer` | Soft, gentle |

## Audio Settings

### Format Options

```python
generator.generate(
    text="Hello!",
    voice="en-US-AriaNeural",
    output="output.mp3",
    format="mp3",  # mp3, wav, ogg
    quality="high"  # low, medium, high
)
```

### Speed and Pitch

```python
generator.generate(
    text="Hello!",
    voice="en-US-AriaNeural",
    output="output.mp3",
    speed=1.2,  # 20% faster
    pitch=2.0   # Slightly higher
)
```

## SSML Support

For advanced control, use SSML:

```python
ssml_text = """
<speak>
    <prosody rate="1.2">This text is faster.</prosody>
    <break time="500ms"/>
    <prosody pitch="+2st">This is higher pitched.</prosody>
</speak>
"""
generator.generate_ssml(ssml_text, "output.mp3")
```

## Batch Processing

For long scripts, process in batches:

```python
# Split long text into segments
segments = generator.split_text(long_text, max_length=1000)

# Generate each segment
for i, segment in enumerate(segments):
    generator.generate(
        text=segment,
        voice="en-US-AriaNeural",
        output=f"output/segment_{i}.mp3"
    )

# Merge audio files
generator.merge_audio("output/", "final.mp3")
```
