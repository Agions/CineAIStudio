<div align="center">

# 🎬 ClipFlowCut

**AI-Powered Video Creation Desktop App**

*From raw footage to final cut, fully AI-automated*

<p align="center">
  <a href="https://github.com/Agions/ClipFlowCut/stargazers"><img src="https://img.shields.io/github/stars/Agions/ClipFlowCut?style=for-the-badge&logo=github&color=FFD700" alt="Stars"></a>
  <a href="https://github.com/Agions/ClipFlowCut/forks"><img src="https://img.shields.io/github/forks/Agions/ClipFlowCut?style=for-the-badge&logo=github&color=4CAF50" alt="Forks"></a>
  <a href="https://github.com/Agions/ClipFlowCut/releases"><img src="https://img.shields.io/github/v/release/Agions/ClipFlowCut?style=for-the-badge&color=blue" alt="Release"></a>
  <img src="https://img.shields.io/badge/Python-3.9+-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

<p align="center">
  <a href="../README.md">中文</a> · <b>English</b> · <a href="https://agions.github.io/ClipFlowCut">Docs</a> · <a href="https://github.com/Agions/ClipFlowCut/releases">Download</a>
</p>

</div>

---

## 🤔 Why ClipFlowCut?

> Traditional video editing requires you to do everything manually. ClipFlowCut lets AI do it for you.

| What ClipFlowCut Offers | |
|---------|:---:|
| 🤖 AI auto commentary & voiceover — one click to professional narration | ✅ |
| 🔀 Switch freely between 9+ LLMs — no vendor lock-in | ✅ |
| 📤 Export to all major formats — fits any professional workflow | ✅ |
| 🏠 Local Ollama support — your data never leaves your machine | ✅ |
| 🆓 MIT open source & free — no subscription, no limits | ✅ |
| 💻 Native desktop app — macOS & Windows | ✅ |
| 🎵 AI beat-sync for mashups — zero manual alignment | ✅ |

---

## ✨ Core Features

### 🎙️ AI Video Commentary
Upload video → AI analyzes scenes → Auto-generates commentary → AI voiceover → Dynamic subtitles

Turn any video into a professional narrated video with one click.

### 🎵 AI Video Mashup
Import multiple clips → BPM beat detection → Smart cut points → Auto transitions → Export

Beat-synced mashups without manual alignment — AI handles it all.

### 🎭 AI First-Person Monologue
Emotion analysis → Monologue generation → AI voiceover → Cinematic subtitles

Give your Vlog a cinematic inner-voice feel.

---

## 🤖 Supported AI Models

| Provider | Model | Text | Vision | TTS |
|----------|-------|:----:|:------:|:---:|
| **OpenAI** | GPT-4o / GPT-5 | ✅ | ✅ | ✅ |
| **Anthropic** | Claude Sonnet 4.5 | ✅ | ✅ | — |
| **Google** | Gemini 2.0 Flash | ✅ | ✅ | — |
| **Alibaba** | Qwen 3.5 | ✅ | ✅ | — |
| **DeepSeek** | R1 / V3 | ✅ | — | — |
| **Zhipu AI** | GLM-5 | ✅ | — | — |
| **Moonshot** | Kimi K2.5 | ✅ | ✅ | — |
| **Local** | Ollama (any model) | ✅ | — | — |
| **Microsoft** | Edge TTS | — | — | ✅ Free |

---

## 📤 Export Formats

```
✅ CapCut Draft (JSON)     ✅ Adobe Premiere (XML)
✅ Final Cut Pro (FCPXML)  ✅ DaVinci Resolve
✅ MP4 (H.264/H.265)       ✅ SRT / ASS Subtitles
```

---

## 🚀 Quick Start

**Requirements:** Python 3.9+ · FFmpeg · macOS 10.15+ / Windows 10+

```bash
# Clone the repo
git clone https://github.com/Agions/ClipFlowCut.git
cd ClipFlowCut

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env and add at least one AI service API key

# Run
python main.py
```

> 💡 **Only one API key is needed to get started.** Edge TTS voiceover is completely free.

---

## 🗺️ Roadmap

- [x] AI Video Commentary (v1.0)
- [x] AI Video Mashup + Beat Detection (v2.0)
- [x] AI First-Person Monologue (v2.0)
- [x] Multi-LLM Support (v2.0)
- [x] Professional Format Export (v3.0)
- [x] PyQt6 Fluent UI Redesign (v3.0)
- [ ] 🔄 Web Version
- [ ] 🔄 Batch Processing Mode
- [ ] 🔄 Custom AI Prompt Template Marketplace
- [ ] 🔄 Multi-language Subtitle Translation
- [ ] 🔄 Plugin System

---

## 🤝 Contributing

Contributions are welcome! Bug fixes, new features, docs improvements, translations — all appreciated.

👉 Please read [CONTRIBUTING.md](../CONTRIBUTING.md) first.

---

## 📄 License

[MIT License](../LICENSE) © 2026 [Agions](https://github.com/Agions)

---

<div align="center">
  <sub>If this project helps you, please give it a ⭐ Star!</sub>
</div>
