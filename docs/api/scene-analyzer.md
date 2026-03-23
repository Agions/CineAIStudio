# Scene Analyzer

The Scene Analyzer module detects and segments video scenes using FFmpeg and OpenCV.

## Overview

`SceneAnalyzer` processes video files to identify scene boundaries, extract keyframes, and analyze visual content.

## Usage

```python
from app.services.ai.scene_analyzer import SceneAnalyzer

# Initialize analyzer
analyzer = SceneAnalyzer()

# Analyze video
scenes = analyzer.analyze_video(
    video_path="input.mp4",
    threshold=30.0  # Scene change threshold
)
```

## Methods

### `analyze_video(video_path, threshold=30.0)`

Analyzes a video file and returns scene information.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `video_path` | str | Path to input video file |
| `threshold` | float | Scene change detection threshold (default: 30.0) |

**Returns:**

```python
{
    "scenes": [
        {
            "start": 0.0,
            "end": 5.5,
            "duration": 5.5,
            "keyframes": [0.0, 2.5, 5.0]
        },
        # ... more scenes
    ],
    "total_scenes": 10,
    "duration": 120.5
}
```

### `extract_keyframes(video_path, timestamps)`

Extracts keyframes at specified timestamps.

```python
keyframes = analyzer.extract_keyframes(
    video_path="input.mp4",
    timestamps=[0.0, 5.5, 10.0]
)
# Returns list of image paths
```

## Scene Detection Algorithm

1. **Frame Extraction**: Extract frames at regular intervals
2. **Histogram Comparison**: Compare color histograms between frames
3. **Threshold Detection**: Mark scene changes when difference exceeds threshold
4. **Boundary Refinement**: Refine boundaries using motion analysis

## Configuration

Configure scene detection in `config/scene_analyzer.yaml`:

```yaml
scene_detection:
  algorithm: histogram  # histogram or motion
  threshold: 30.0
  min_scene_duration: 1.0
  frame_interval: 0.5
```

## Performance Tips

- Use SSD storage for faster processing
- Adjust threshold based on video content
- For fast videos, increase frame interval
