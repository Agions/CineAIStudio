# AI Configuration

 powerConfigure AI providers to VideoForge's intelligent features.

## Supported AI Providers

### Text & Vision Models

| Provider | Models | Vision | Text |
|----------|--------|--------|------|
| OpenAI | GPT-5.3 | ✅ | ✅ |
| Anthropic | Claude Sonnet 4.5 | ✅ | ✅ |
| Google | Gemini 3.1 Flash | ✅ | ✅ |
| 阿里云 | Qwen 3.5 | ✅ | ✅ |
| DeepSeek | R1, V3.2 | ✅ | ✅ |
| 智谱AI | GLM-5 | ✅ | ✅ |
| 月之暗面 | Kimi K2.5 | ✅ | ✅ |
| 本地 | Ollama | ❌ | ✅ |

### Voice Synthesis

| Provider | Voices |
|----------|--------|
| Edge TTS | Multiple Microsoft voices |
| OpenAI TTS | All OpenAI voices |

## Environment Configuration

Create a `.env` file in the project root:

```env
# OpenAI
OPENAI_API_KEY=sk-your-key-here

# Anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Google Gemini
GOOGLE_API_KEY=your-key-here

# 阿里云 Qwen
QWEN_API_KEY=your-key-here

# DeepSeek
DEEPSEEK_API_KEY=sk-your-key-here

# 智谱AI
ZHIPU_API_KEY=your-key-here

# 月之暗面 Kimi
KIMI_API_KEY=your-key-here

# Ollama (本地)
OLLAMA_BASE_URL=http://localhost:11434
```

## Using Multiple Providers

VideoForge supports multiple AI providers simultaneously. You can:

1. Set keys for all providers you want to use
2. Select your preferred provider in the UI
3. Fall back to alternative providers if one fails

## Local Models with Ollama

For offline or private AI processing:

```bash
# Install Ollama
brew install ollama  # macOS
# or download from ollama.ai

# Pull a model
ollama pull qwen2.5
ollama pull llama3

# Start the service
ollama serve
```

Then set in `.env`:
```env
OLLAMA_BASE_URL=http://localhost:11434
```

## Voice Configuration

Configure AI voice synthesis in the settings:

```env
# Default voice settings
DEFAULT_VOICE=alloy
EDGE_VOICE=en-US-AriaNeural
```

### Available Edge TTS Voices

| Voice | Language | Gender |
|-------|----------|--------|
| en-US-AriaNeural | English | Female |
| en-US-GuyNeural | English | Male |
| zh-CN-XiaoxiaoNeural | Chinese | Female |
| zh-CN-YunxiNeural | Chinese | Male |

## API Key Security

- **Never commit** `.env` to version control
- The `.env.example` file shows required keys without real values
- Use keyring for enhanced security in production
