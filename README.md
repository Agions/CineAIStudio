# Voxplore

<div align="center">

![Voxplore Logo](docs/public/logo-200.png)

### AI First-Person Video Narrator

**批量上传视频 · AI 自动分组选段 · 一键生成电影感配音解说**

[![Stars](https://img.shields.io/github/stars/Agions/Voxplore?style=for-the-badge&logo=github&color=F59E0B)](https://github.com/Agions/Voxplore/stargazers)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge&logo=opensource)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Qt](https://img.shields.io/badge/Qt-6.5+-41?style=for-the-badge&logo=qt)](https://www.qt.io/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-silver?style=for-the-badge&logo=linux&logoColor=white)](https://github.com/Agions/Voxplore)
[![v4.0.0](https://img.shields.io/badge/v4.0.0-10B981?style=for-the-badge)](https://github.com/Agions/Voxplore/releases)

**免费 · 开源 · 跨平台**

</div>

---

## 🎯 一句话定位

> **Voxplore** v4.0 — 多视频智能合并解说专家。批量上传 → AI 视觉+声纹混合分组 → 第一人称片段提取 → 模块化成品输出，让短剧/影视/vlog 一键变成"我在现场"的专业叙事视频。

---

## 4 步创作流程

```
批量上传视频（文件夹 / Ctrl多选）
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│  Step 1 · 场景理解                                         │
│  AI 逐帧分析，判断"我"的主体视角，提取高光片段               │
└──────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│  Step 2 · 智能分组                                         │
│  视觉 embedding（0.7）+ 声纹（0.3）混合相似度               │
│  → 同一人物避免重复解说                                    │
└──────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│  Step 3 · 叙事选段                                         │
│  叙事完整优先 + 情感峰值驱动                               │
│  悬疑铺垫 → 剧情高潮 → 情感共鸣                           │
└──────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│  Step 4 · 解说生成 + 导出                                  │
│  7 种预设风格 + 角色设定                                   │
│  MP4 / 剪映草稿 JSON 双格式输出                            │
└──────────────────────────────────────────────────────────┘
```

---

## ✨ 核心能力

| 能力 | 说明 |
|------|------|
| 🎬 **多视频智能合并** | 批量上传，AI 自动分组选段，避免重复解说 |
| 👤 **第一人称片段提取** | 逐帧分析，Qwen2.5-VL 判断"我"的视角 |
| 💡 **情感峰值驱动** | 叙事完整优先 + 情感峰值加权排序 |
| 🎙️ **7 种情感风格** | 治愈/悬疑/励志/怀旧/浪漫/幽默/纪录片 |
| ✍️ **精准字幕** | TTS word-level，音字同步 50ms 精度 |
| 📦 **模块化成品** | 合并版（完整叙事）+ 高光片段（单独分发）|
| 🖥️ **剪映导出** | 原生草稿 JSON，无缝导入剪映精剪 |
| 🌐 **全本地运行** | 视频永不上传云端 |

---

## 🖥️ 全新 UI（v4.0 新设计）

简约科技风桌面端，基于 **PySide6 + OKLCH Design System**：

```
项目列表（ProjectsWindow）
    │ 新建 / 打开 / 删除
    ▼
步骤 1 · 上传  →  拖拽批量上传文件
步骤 2 · 场景理解  →  AI 分析进度 + 场景卡片
步骤 3 · 配音编辑  →  解说词编辑 + 情感风格 + TTS 进度
步骤 4 · 导出  →  格式/质量选择 + 导出进度
```

> 全新 UI 默认**未启用**。编辑 `app/main.py`，取消注释 `launch_new_ui()` 即可体验。

---

## 🚀 快速开始

### 下载安装包

访问 [Releases](https://github.com/Agions/Voxplore/releases/latest) 下载 Windows `.exe` / macOS `.dmg` / Linux `.AppImage`。

### 从源码构建

```bash
git clone https://github.com/Agions/Voxplore.git
cd Voxplore
pip install -r requirements.txt
python app/main.py
```

### 配置 AI（最低只需一个 Key）

```bash
# DeepSeek（解说生成主力，推荐）
export DEEPSEEK_API_KEY="sk-..."

# 通义千问（场景理解，备选）
export QWEN_API_KEY="..."

# 不配置时：Edge-TTS 配音合成等基础功能仍可正常使用
```

---

## 🤖 技术栈（2026 最新模型）

| 模块 | 模型 | 说明 |
|------|------|------|
| 智能分组 | **Qwen2.5-VL** + 声纹识别 | 视觉 0.7 + 音频 0.3 混合相似度 |
| 第一人称提取 | **Qwen2.5-VL** | 逐帧分析，主体视角判断，9–60 秒片段 |
| 解说生成 | **DeepSeek-V3** | 代入"我"视角，7 种预设风格 |
| 语音识别 | **SenseVoice** | 阿里 FunAudioLLM，中文 ASR + 说话人分离 |
| 配音合成 | **Edge-TTS** · **F5-TTS** | Edge 主流低延迟，F5 零样本音色克隆 |
| 字幕 | TTS word-level timing | 50ms 以内精度 |
| 云端备选 | GPT-4o / Claude Sonnet | 按需切换 |

---

## 📖 文档导航

| 文档 | 说明 |
|------|------|
| [快速开始](docs/guide/quick-start.md) | 5 分钟上手 |
| [功能详解](docs/features.md) | 全部功能说明 |
| [AI 模型](docs/ai-models.md) | 各模型配置指南 |
| [FAQ & 疑难排查](docs/faq.md) | 常见问题 |

---

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| UI 框架 | PySide6 (Qt 6.5+) · OKLCH Design System |
| 编程语言 | Python 3.10+ |
| 视频处理 | FFmpeg + OpenCV |
| 本地 ASR | SenseVoice / Faster-Whisper |
| 云端 AI | OpenAI SDK（多厂商兼容）|
| 字幕格式 | SRT / ASS（电影级样式）|
| 导出格式 | MP4（H.264/H.265）/ 剪映草稿 |

---

## 📄 许可证

[MIT License](LICENSE) · Copyright © 2025-2026 [Agions](https://github.com/Agions)

---

<div align="center">

⭐ 如果 Voxplore 对你有帮助，请给一个 Star

</div>