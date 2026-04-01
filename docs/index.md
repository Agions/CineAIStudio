---
layout: home

title: VideoForge
titleTemplate: false

hero:
  name: VideoForge
  text: AI 驱动，专业视频创作
  tagline: 从素材到成片，AI 全流程自动化处理 — 免费开源跨平台
  image:
    src: /logo.png
    alt: VideoForge
  actions:
    - theme: brand
      text: 🚀 5 分钟快速开始
      link: /guide/quick-start
    - theme: alt
      text: 📖 详细文档
      link: /guide/getting-started
    - theme: alt
      text: ⭐ Star on GitHub
      link: https://github.com/Agions/VideoForge
---

<div class="features-grid">

<div class="feature-card">
<span class="icon">🎬</span>
<span class="title">剧情分析</span>
<span class="desc">智能分析叙事结构，生成剪辑建议</span>
</div>

<div class="feature-card">
<span class="icon">🎙️</span>
<span class="title">AI 解说</span>
<span class="desc">一键生成旁白配音 + 动态字幕</span>
</div>

<div class="feature-card">
<span class="icon">🎵</span>
<span class="title">智能混剪</span>
<span class="desc">BPM 自动卡点，多素材一键合成</span>
</div>

<div class="feature-card">
<span class="icon">🎭</span>
<span class="title">AI 独白</span>
<span class="desc">电影级字幕，情感分析驱动的叙事</span>
</div>

<div class="feature-card">
<span class="icon">📱</span>
<span class="title">短视频切片</span>
<span class="desc">直播/长视频一键转高光片段</span>
</div>

<div class="feature-card">
<span class="icon">🌐</span>
<span class="title">视频翻译</span>
<span class="desc">100+ 语言支持，配音 + 字幕本地化</span>
</div>

</div>

---

<div class="stats-row">

![Stars](https://img.shields.io/github/stars/Agions/VideoForge?style=for-the-badge&logo=github&color=10B981)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge&logo=opensource&color=10B981)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&color=6366F1)
![Qt](https://img.shields.io/badge/Qt-6.5+-41?style=for-the-badge&logo=qt&color=41CD53)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-silver?style=for-the-badge&logo=linux&logoColor=white)

**免费 · 开源 · 跨平台**

</div>

---

## 🚀 开始使用

### 安装 VideoForge

<TipCard title="下载安装包" icon="📦">
访问 [GitHub Releases](https://github.com/Agions/VideoForge/releases/latest) 下载对应平台的最新版本。
</TipCard>

<TipCard title="配置 AI" icon="🤖">
在设置中配置一个 API Key（如 DeepSeek / OpenAI / 通义千问），推荐从免费额度开始。
</TipCard>

<TipCard title="创建作品" icon="🎬">
导入视频素材，选择 AI 创作模式，等待 AI 处理完成，预览并导出。
</TipCard>

---

## 💡 支持的 AI 模型

| 提供商 | 代表模型 | 特点 |
|--------|----------|------|
| OpenAI | GPT-5.4 | 最强通用能力 |
| Claude | Sonnet 4.6 | 超长上下文、安全性强 |
| Gemini | 3.1 Pro | 1M 超长上下文 |
| DeepSeek | V3.2 | 🏆 性价比最高 |
| 通义千问 | Qwen 2.5-Max | 中文优化 |
| Kimi | K2.5 | 超长上下文 |
| Ollama | 本地模型 | 🔒 完全私有离线 |

> 💡 **只需配置一个 API Key 即可使用全部 AI 功能。**

---

## 📋 更新日志

### v1.2.1 (2026.03) — 当前版本

- ⚡ **GPU 加速** — Faster-Whisper 自动检测 CUDA/GPU，推理速度提升 3-4x
- 🏗️ **Nuitka 打包** — 更小体积、更快启动（可选构建方式）
- 🎭 **SenseVoice 框架** — 情感检测、说话人分离基础架构
- 🔧 **构建系统升级** — uv 依赖管理、CI 优化

### v1.2.0 (2026.03)

- ✨ **全新 UI** — PySide6 迁移，深色科技感界面
- 🎨 **模板市场** — 预设工作流模板一键启动
- ⚡ **批量处理 2.0** — 全新队列管理面板
- 🔒 **安全增强** — SecureKeyManager 重构，API Key 加密存储
- 🤖 **AI 模型更新** — GPT-5.4、Claude Sonnet 4.6、Gemini 3.1 Pro

### v1.1.0 (2026.02)

- ✨ 新增 AI 智能混剪功能（BPM 自动卡点）
- ✨ 新增 AI 第一人称独白模式
- ✨ 支持 10+ AI 模型接入
- 🔧 性能优化，内存占用降低 40%

### v1.0.0 (2025.12)

- ✨ 全新 AI 解说制作流程
- ✨ 支持剪映 / Premiere / DaVinci Resolve 格式导出
- ✨ 完整的插件系统

---

## 🤝 参与贡献

VideoForge 是开源项目，欢迎所有形式的贡献：

| 贡献方式 | 说明 |
|----------|------|
| 🐛 报告 Bug | [GitHub Issues](https://github.com/Agions/VideoForge/issues) |
| 📝 完善文档 | 直接提交 PR |
| 🔧 提交代码 | 提交 Pull Request |

---

<style>
.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin: 2.5rem 0;
}

@media (max-width: 768px) {
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .features-grid {
    grid-template-columns: 1fr;
  }
}

.feature-card {
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-border);
  border-radius: 16px;
  padding: 1.5rem 1rem;
  text-align: center;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.feature-card:hover {
  border-color: var(--vf-green);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.15);
}

.feature-card .icon {
  font-size: 2rem;
  line-height: 1;
}

.feature-card .title {
  font-weight: 700;
  font-size: 0.95rem;
  color: var(--vp-c-text-1);
  margin: 0;
}

.feature-card .desc {
  font-size: 0.8rem;
  color: var(--vp-c-text-3);
  margin: 0;
  line-height: 1.4;
}

.stats-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
  margin: 1.5rem 0;
  justify-content: center;
}

.stats-row img {
  height: 28px;
}

.stats-row strong {
  color: var(--vp-c-text-2);
  font-size: 0.9rem;
  margin-left: 0.5rem;
}

.VPHero .name {
  font-size: 3.5rem;
}

@media (max-width: 640px) {
  .VPHero .name {
    font-size: 2.5rem;
  }
}
</style>
