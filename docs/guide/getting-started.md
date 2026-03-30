# Getting Started

Welcome to VideoForge! This guide will help you get up and running with the AI-powered video creation application.

## Prerequisites

Before you begin, ensure you have the following:

- **Python 3.9+** - Required runtime
- **FFmpeg** - Video processing engine (must be in system PATH)
- **macOS 10.15+** or **Windows 10+** - Supported platforms

## Quick Installation

```bash
# Clone the repository
git clone https://github.com/Agions/VideoForge.git
cd VideoForge

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Run the application
python app/main.py
```

## First Launch

1. Launch the application: `python main.py`
2. Configure your AI provider API keys in the settings
3. Import your video素材
4. Choose an AI creation mode
5. Let VideoForge do the magic! ✨

## AI Creation Modes

| Mode | Use Case |
|------|----------|
| **AI Commentary** | Create narrated videos with AI voiceovers |
| **AI Mashup** | Combine multiple clips with beat-synced transitions |
| **AI Monologue** | Generate emotional first-person narratives |

## Next Steps

- [Installation Guide](./installation) - Detailed installation instructions
- [AI Video Guide](./ai-video-guide) - Learn about AI video creation
- [Configuration](./ai-configuration) - Configure AI providers
