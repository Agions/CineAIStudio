# ClipFlowCut Architecture

> Architecture Overview for ClipFlowCut

## System Architecture

ClipFlowCut uses a modular architecture with the following main components:

### Core Modules

- **Scene Analyzer**: Analyzes video content using PySceneDetect
- **Script Generator**: AI-powered script generation
- **Voice Generator**: Text-to-speech voice synthesis
- **Video Processor**: Video editing and rendering

### UI Layer

- **Main Window**: PyQt6-based main interface
- **Project Manager**: Project file management
- **Preview Panel**: Real-time video preview

## Data Flow

```
Input Video → Scene Detection → AI Analysis → Script Generation → Video Assembly → Output
```

## Technology Stack

- **Frontend**: PyQt6
- **AI/ML**: OpenAI API, local Whisper model
- **Video Processing**: FFmpeg, PySceneDetect
