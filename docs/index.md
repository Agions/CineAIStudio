---
layout: home

title: Narrafiilm
titleTemplate: false

hero:
  name: NARRAFILM
  text: AI First-Person Video Narrator
  tagline: 上传视频，AI 代入画面主角视角，一键生成配音解说 — 免费 · 开源 · 跨平台
  image:
    src: https://img.shields.io/badge/NARRAFILM-AI%20Narrator-0A84FF?style=for-the-badge&logo=cinema5&logoColor=white
    alt: NARRAFILM
  actions:
    - theme: brand
      text: 🚀 快速开始
      link: /guide/quick-start.html
    - theme: alt
      text: 📖 功能介绍
      link: /features.html
    - theme: alt
      text: ⭐ Star on GitHub
      link: https://github.com/Agions/Narrafiilm

features:
  - icon: 🎬
    title: 第一人称代入
    details: AI 分析画面主角视角，用"我"的口吻生成解说，自然沉浸
  - icon: 🎙️
    title: 情感配音
    details: 多风格旁白：治愈 / 悬疑 / 励志 / 浪漫 / 哲思，Edge-TTS 高保真合成
  - icon: ✍️
    title: 精准字幕
    details: ASS 电影级字幕，基于 TTS word-level timing，音字完全同步
  - icon: 🖥️
    title: 剪映导出
    details: 原生草稿格式，直达剪映继续精剪，零门槛工作流
  - icon: 🔒
    title: 全本地运行
    details: SenseVoice 本地 ASR，视频不上传云端，隐私安全无忧
  - icon: 🌐
    title: 多模型支持
    details: Qwen2.5-VL / DeepSeek-V3 / GPT-4o 按需切换，灵活适配各类场景
---

<div class="nf-home">

<!-- WORKFLOW SECTION -->
<section class="nf-section">
  <h2 class="nf-section-title">🔄 工作流程</h2>
  <div class="nf-workflow">
    <div class="nf-workflow-step">
      <div class="nf-workflow-num">1</div>
      <div class="nf-workflow-content">
        <div class="nf-workflow-title">上传视频</div>
        <div class="nf-workflow-desc">支持 MP4 / MOV / AVI / MKV，拖拽即上传</div>
      </div>
    </div>
    <div class="nf-workflow-arrow">→</div>
    <div class="nf-workflow-step">
      <div class="nf-workflow-num">2</div>
      <div class="nf-workflow-content">
        <div class="nf-workflow-title">AI 场景理解</div>
        <div class="nf-workflow-desc">Qwen2.5-VL 逐帧分析，主角视角 + 环境氛围</div>
      </div>
    </div>
    <div class="nf-workflow-arrow">→</div>
    <div class="nf-workflow-step">
      <div class="nf-workflow-num">3</div>
      <div class="nf-workflow-content">
        <div class="nf-workflow-title">生成解说</div>
        <div class="nf-workflow-desc">DeepSeek-V3 代入"我"的口吻，撰写解说稿</div>
      </div>
    </div>
    <div class="nf-workflow-arrow">→</div>
    <div class="nf-workflow-step">
      <div class="nf-workflow-num">4</div>
      <div class="nf-workflow-content">
        <div class="nf-workflow-title">合成输出</div>
        <div class="nf-workflow-desc">Edge-TTS 配音 + 电影级字幕，导出 MP4</div>
      </div>
    </div>
  </div>
</section>

<!-- TECH ARCH TABLE -->
<section class="nf-section">
  <h2 class="nf-section-title">🧠 技术架构</h2>
  <div class="nf-arch-table">
    <div class="nf-arch-row nf-arch-header">
      <div>模块</div><div>模型</div><div>说明</div>
    </div>
    <div class="nf-arch-row">
      <div><span class="nf-arch-module">场景理解</span></div>
      <div><code>Qwen2.5-VL (72B)</code></div>
      <div>阿里开源，视频理解 SOTA，Native 视频输入</div>
    </div>
    <div class="nf-arch-row">
      <div><span class="nf-arch-module">解说生成</span></div>
      <div><code>DeepSeek-V3</code></div>
      <div>最强开源 LLM，第一人称视角提示词执行最优</div>
    </div>
    <div class="nf-arch-row">
      <div><span class="nf-arch-module">ASR 识别</span></div>
      <div><code>SenseVoice</code></div>
      <div>阿里 FunAudioLLM，中文 ASR + 说话人分离</div>
    </div>
    <div class="nf-arch-row">
      <div><span class="nf-arch-module">配音合成</span></div>
      <div><code>Edge-TTS / F5-TTS</code></div>
      <div>Edge 主流优质低延迟，F5 零样本音色克隆</div>
    </div>
    <div class="nf-arch-row">
      <div><span class="nf-arch-module">云端备选</span></div>
      <div><code>GPT-4o / Claude</code></div>
      <div>按需切换，兼容 OpenAI SDK 多厂商 API</div>
    </div>
  </div>
</section>

<!-- GETTING STARTED -->
<section class="nf-section">
  <h2 class="nf-section-title">🚀 开始使用</h2>
  <div class="nf-start-cards">
    <a href="/guide/quick-start.html" class="nf-start-card">
      <div class="nf-start-card-icon">📦</div>
      <div class="nf-start-card-title">下载安装包</div>
      <div class="nf-start-card-desc">访问 GitHub Releases 下载最新版本，支持 Windows / macOS / Linux</div>
      <span class="nf-start-card-arrow">→</span>
    </a>
    <a href="/guide/installation.html" class="nf-start-card">
      <div class="nf-start-card-icon">🤖</div>
      <div class="nf-start-card-title">配置 AI 能力</div>
      <div class="nf-start-card-desc">只需一个 DeepSeek API Key，最低成本启动完整 AI 流程</div>
      <span class="nf-start-card-arrow">→</span>
    </a>
    <a href="/features.html" class="nf-start-card">
      <div class="nf-start-card-icon">🎬</div>
      <div class="nf-start-card-title">创建你的作品</div>
      <div class="nf-start-card-desc">导入视频 → 选择情感风格 → 一键生成配音解说 → 预览导出</div>
      <span class="nf-start-card-arrow">→</span>
    </a>
  </div>
</section>

<!-- STATS BAR -->
<div class="nf-stats">
  <div class="nf-stat"><div class="nf-stat-value">v3.2.0</div><div class="nf-stat-label">最新版本</div></div>
  <div class="nf-stat-sep">|</div>
  <div class="nf-stat"><div class="nf-stat-value">MIT</div><div class="nf-stat-label">开源协议</div></div>
  <div class="nf-stat-sep">|</div>
  <div class="nf-stat"><div class="nf-stat-value">Python 3.10+</div><div class="nf-stat-label">跨平台</div></div>
  <div class="nf-stat-sep">|</div>
  <div class="nf-stat"><div class="nf-stat-value">PySide6</div><div class="nf-stat-label">Qt 6.5+</div></div>
</div>

<!-- FOOTER -->
<footer class="nf-footer">
  <p>
    <a href="https://github.com/Agions/Narrafiilm">GitHub</a>
    · <a href="/guide/quick-start.html">快速开始</a>
    · <a href="/faq.html">FAQ</a>
    · <a href="https://github.com/Agions/Narrafiilm/issues">反馈问题</a>
  </p>
  <p class="nf-footer-copy">Narrafiilm © 2025–2026 · Built with AI · Released under MIT License</p>
</footer>

</div>
