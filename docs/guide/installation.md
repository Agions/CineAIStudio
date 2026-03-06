# Installation Guide

This guide covers the complete installation process for ClipFlowCut.

## System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Python | 3.9+ | 3.11+ |
| FFmpeg | 4.0+ | Latest |
| RAM | 8GB | 16GB+ |
| Storage | 2GB | 10GB+ |

## ⚠️ Important: PyQt6 Requirement

ClipFlowCut is built on **PyQt6**, NOT PySide6!

If you see errors like:
```
QLabel(...): argument 1 has unexpected type 'str'
```

This means you have the wrong Qt library installed. Fix it with:
```bash
pip uninstall PySide6
pip install PyQt6
```

## Installation Steps

### 1. Install FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

Verify installation:
```bash
ffmpeg -version
```

### 2. Clone the Project

```bash
git clone https://github.com/Agions/ClipFlowCut.git
cd ClipFlowCut
```

### 3. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

### 4. Install Dependencies

```bash
# First, ensure PySide6 is NOT installed (if it is, remove it)
pip uninstall PySide6 2>/dev/null || true

# Install PyQt6 and other dependencies
pip install -r requirements.txt
```

### 5. Configure API Keys

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Choose your AI provider
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
QWEN_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
KIMI_API_KEY=sk-...
```

### 6. Run the Application

```bash
python main.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'PyQt6'` | Run `pip install PyQt6` |
| `QLabel argument error` | Uninstall PySide6: `pip uninstall PySide6` |
| FFmpeg not found | Add FFmpeg to system PATH |
| API errors | Check your API keys in `.env` file |

## Development Installation

For development:

```bash
git clone https://github.com/Agions/ClipFlowCut.git
cd ClipFlowCut
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .[dev]
```
