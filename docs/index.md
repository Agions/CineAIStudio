---
layout: home

title: NARRAFILM
titleTemplate: false

hero:
  name: NARRAFILM
  text: AI First-Person Video Narrator
  tagline: 上传视频，AI 代入画面主角视角，一键生成配音解说 — 免费开源跨平台
  image:
    src: /logo.png
    alt: NARRAFILM
  actions:
    - theme: brand
      text: 🚀 5 分钟快速开始
      link: /guide/quick-start
    - theme: alt
      text: 📖 详细文档
      link: /guide/getting-started
    - theme: alt
      text: ⭐ Star on GitHub
      link: https://github.com/Agions/NARRAFILM
---

<div class="features-grid">

<div class="feature-card">
<span class="icon">🎬</span>
<span class="title">第一人称代入</span>
<span class="desc">AI 分析画面主角视角，用"我"的口吻生成解说</span>
</div>

<div class="feature-card">
<span class="icon">🎙️</span>
<span class="title">情感配音</span>
<span class="desc">多风格旁白：治愈 / 悬疑 / 励志 / 怀旧 / 浪漫</span>
</div>

<div class="feature-card">
<span class="icon">✍️</span>
<span class="title">电影级字幕</span>
<span class="desc">ASS 精准字幕，音字完全同步，电影感样式</span>
</div>

<div class="feature-card">
<span class="icon">🖥️</span>
<span class="title">剪映导出</span>
<span class="desc">原生草稿格式，直达剪映继续精剪</span>
</div>

<div class="feature-card">
<span class="icon">🔒</span>
<span class="title">全本地运行</span>
<span class="desc">SenseVoice 本地 ASR，无需上传视频到云端</span>
</div>

<div class="feature-card">
<span class="icon">🌐</span>
<span class="title">多模型支持</span>
<span class="desc">Qwen2.5-VL / DeepSeek-V3 / GPT-4o 按需切换</span>
</div>

</div>

---

<div class="stats-row">

<a href="https://github.com/Agions/NARRAFILM/stargazers"><img src="https://img.shields.io/github/stars/Agions/NARRAFILM?style=for-the-badge&logo=github&color=10B981" alt="Stars" /></a>
<a href="https://github.com/Agions/NARRAFILM/network/members"><img src="https://img.shields.io/github/forks/Agions/NARRAFILM?style=for-the-badge&logo=github&color=10B981" alt="Forks" /></a>
<a href="https://github.com/Agions/NARRAFILM/issues"><img src="https://img.shields.io/github/issues/Agions/NARRAFILM?style=for-the-badge&color=10B981" alt="Issues" /></a>
<a href="https://github.com/Agions/NARRAFILM/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge&logo=opensource&color=10B981" alt="License" /></a>
<img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&color=6366F1" alt="Python" />
<img src="https://img.shields.io/badge/Qt-6.5+-41?style=for-the-badge&logo=qt&color=41CD53" alt="Qt" />
<img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-silver?style=for-the-badge&logo=linux&logoColor=white" alt="Platform" />

**免费 · 开源 · 跨平台**

</div>

---

## 🚀 开始使用

### 安装 NARRAFILM

<TipCard title="下载安装包" icon="📦">
访问 [GitHub Releases](https://github.com/Agions/NARRAFILM/releases/latest) 下载对应平台的最新版本。
</TipCard>

<TipCard title="配置 AI" icon="🤖">
只需一个 API Key 即可启动（推荐 DeepSeek），场景理解 + 解说生成全部本地可跑。
</TipCard>

<TipCard title="创建作品" icon="🎬">
导入视频 → 选择情感风格 → 一键生成配音解说 → 预览并导出。
</TipCard>

---

## 💡 技术架构

| 模块 | 模型 | 说明 |
|------|------|------|
| 场景理解 | **Qwen2.5-VL** (72B) | 阿里开源，视频理解 SOTA |
| 解说生成 | **DeepSeek-V3** | 最强开源 LLM |
| 语音识别 | **SenseVoice** | 阿里，中文 ASR + 说话人分离 |
| 配音合成 | **Edge-TTS** + **F5-TTS** | 优质旁白 + 零样本音色克隆 |
| 云端备选 | GPT-4o / Claude | 按需切换 |

---

## 📋 更新日志

### v3.2.0 (2026.04) — 当前版本

- 🏷️ **品牌重命名** — Narrafiilm → NARRAFILM，专注第一人称解说
- 🎬 **极简定位** — 裁剪全部冗余功能，只留第一人称解说核心
- 🏗️ **架构重构** — 依赖精简，MonologueMaker 为唯一核心
- 🤖 **模型升级** — Qwen2.5-VL / DeepSeek-V3 / SenseVoice 全链路更新

### v3.1.1 (2026.03)

- ✨ **全新 UI** — PySide6 迁移，深色科技感界面
- 🎭 **SenseVoice 框架** — 情感检测、说话人分离
- 🔧 **构建系统升级** — uv 依赖管理、CI 优化

### v3.0.0 (2026.02)

- ✨ **AI 第一人称独白模式** — 电影级字幕，情感分析驱动
- ✨ 支持剪映草稿导出
- 🔧 性能优化，内存占用降低 40%

---

## 🤝 参与贡献

| 贡献方式 | 说明 |
|----------|------|
| 🐛 报告 Bug | [GitHub Issues](https://github.com/Agions/NARRAFILM/issues) |
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
  display: flex !important;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
  margin: 1.5rem 0;
  justify-content: center;
}

.stats-row p {
  display: flex !important;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
  margin: 0 !important;
  padding: 0 !important;
}

.stats-row a,
.stats-row img {
  height: 28px;
  display: inline-block;
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
