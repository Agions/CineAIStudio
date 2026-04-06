---
layout: home

title: Narrafiilm
titleTemplate: false

hero:
  name: NARRAFILM
  text: AI First-Person Video Narrator
  tagline: 上传视频，AI 代入主角视角，一键生成电影感配音解说
  image:
    src: https://img.shields.io/badge/NARRAFILM-AI%20Narrator-0A84FF?style=for-the-badge&logo=cinema5&logoColor=white
    alt: NARRAFILM
  actions:
    - theme: brand
      text: 🚀 快速开始
      link: /guide/quick-start
    - theme: alt
      text: 📖 功能介绍
      link: /features
    - theme: alt
      text: ⭐ Star on GitHub
      link: https://github.com/Agions/Narrafiilm

features:
  - icon: 🎬
    title: 第一人称代入
    details: AI 分析画面主角视角，用"我"的口吻生成解说，自然沉浸
  - icon: 🎙️
    title: 情感配音
    details: 多风格旁白：治愈 / 悬疑 / 励志 / 怀旧 / 浪漫，Edge-TTS 高保真合成
  - icon: ✍️
    title: 精准字幕
    details: ASS 电影级字幕，基于 TTS word-level timing，音字完全同步
  - icon: 🖥️
    title: 剪映导出
    details: 原生草稿格式，直达剪映继续精剪，零门槛工作流
  - icon: 🔒
    title: 隐私优先
    details: 视频不上传云端，API Key 自持，本地处理优先
  - icon: 🌐
    title: 开源免费
    details: MIT 协议，代码完全透明，任意场景免费使用
---

<div class="nf-home">

<section class="nf-section">
  <h2 class="nf-section-title">🔄 工作流程</h2>
  <div class="nf-workflow">
    <div class="nf-workflow-step">
      <div class="nf-workflow-num">1</div>
      <div class="nf-workflow-content">
        <div class="nf-workflow-title">上传视频</div>
        <div class="nf-workflow-desc">拖入 MP4 / MOV / AVI / MKV，系统自动抽帧分析</div>
      </div>
    </div>
    <div class="nf-workflow-arrow">→</div>
    <div class="nf-workflow-step">
      <div class="nf-workflow-num">2</div>
      <div class="nf-workflow-content">
        <div class="nf-workflow-title">AI 场景理解</div>
        <div class="nf-workflow-desc">Qwen2.5-VL 逐帧分析，识别主角、地点、动作、氛围</div>
      </div>
    </div>
    <div class="nf-workflow-arrow">→</div>
    <div class="nf-workflow-step">
      <div class="nf-workflow-num">3</div>
      <div class="nf-workflow-content">
        <div class="nf-workflow-title">生成解说稿</div>
        <div class="nf-workflow-desc">DeepSeek-V3 代入"我"的视角，撰写自然流畅的解说词</div>
      </div>
    </div>
    <div class="nf-workflow-arrow">→</div>
    <div class="nf-workflow-step">
      <div class="nf-workflow-num">4</div>
      <div class="nf-workflow-content">
        <div class="nf-workflow-title">配音 + 字幕</div>
        <div class="nf-workflow-desc">Edge-TTS 合成旁白，ASS 字幕音字同步，电影感输出</div>
      </div>
    </div>
  </div>
</section>

<section class="nf-section">
  <h2 class="nf-section-title">🧠 技术栈</h2>
  <div class="nf-arch-table">
    <div class="nf-arch-row nf-arch-header">
      <div>模块</div><div>模型 / 技术</div><div>说明</div>
    </div>
    <div class="nf-arch-row">
      <div><span class="nf-arch-module">场景理解</span></div>
      <div><code>Qwen2.5-VL (72B)</code></div>
      <div>阿里开源，视频帧抽帧分析，主角视角识别</div>
    </div>
    <div class="nf-arch-row">
      <div><span class="nf-arch-module">解说生成</span></div>
      <div><code>DeepSeek-V3</code></div>
      <div>代入"我"视角的生活化解说稿，支持多种情感风格</div>
    </div>
    <div class="nf-arch-row">
      <div><span class="nf-arch-module">配音合成</span></div>
      <div><code>Edge-TTS / F5-TTS</code></div>
      <div>Edge 主流低延迟，F5 零样本音色克隆（2026.03）</div>
    </div>
    <div class="nf-arch-row">
      <div><span class="nf-arch-module">字幕对齐</span></div>
      <div><code>TTS word-level timing</code></div>
      <div>音字精准同步，电影级 ASS 字幕</div>
    </div>
    <div class="nf-arch-row">
      <div><span class="nf-arch-module">视频合成</span></div>
      <div><code>FFmpeg</code></div>
      <div>H.264/H.265 编码，MP4 输出或剪映草稿 JSON</div>
    </div>
  </div>
</section>

<section class="nf-section">
  <h2 class="nf-section-title">🚀 开始使用</h2>
  <div class="nf-start-cards">
    <a href="/guide/quick-start" class="nf-start-card">
      <div class="nf-start-card-icon">📦</div>
      <div class="nf-start-card-title">下载安装包</div>
      <div class="nf-start-card-desc">GitHub Releases 提供 Windows / macOS / Linux 一键安装包</div>
      <span class="nf-start-card-arrow">→</span>
    </a>
    <a href="/guide/quick-start#配置-api-key" class="nf-start-card">
      <div class="nf-start-card-icon">🤖</div>
      <div class="nf-start-card-title">配置 AI 能力</div>
      <div class="nf-start-card-desc">只需一个 DeepSeek API Key，最低成本启动完整流程</div>
      <span class="nf-start-card-arrow">→</span>
    </a>
    <a href="/features" class="nf-start-card">
      <div class="nf-start-card-icon">🎬</div>
      <div class="nf-start-card-title">了解功能细节</div>
      <div class="nf-start-card-desc">情感风格、字幕样式、导出格式等详细说明</div>
      <span class="nf-start-card-arrow">→</span>
    </a>
  </div>
</section>

<div class="nf-stats">
  <div class="nf-stat"><div class="nf-stat-value">v3.4.0</div><div class="nf-stat-label">最新版本</div></div>
  <div class="nf-stat-sep">|</div>
  <div class="nf-stat"><div class="nf-stat-value">MIT</div><div class="nf-stat-label">开源协议</div></div>
  <div class="nf-stat-sep">|</div>
  <div class="nf-stat"><div class="nf-stat-value">Python 3.10+</div><div class="nf-stat-label">跨平台</div></div>
  <div class="nf-stat-sep">|</div>
  <div class="nf-stat"><div class="nf-stat-value">PySide6</div><div class="nf-stat-label">Qt 6.5+</div></div>
</div>

<footer class="nf-footer">
  <p>
    <a href="https://github.com/Agions/Narrafiilm">GitHub</a>
    · <a href="/guide/quick-start">快速开始</a>
    · <a href="/faq">FAQ</a>
    · <a href="https://github.com/Agions/Narrafiilm/issues">反馈问题</a>
  </p>
  <p class="nf-footer-copy">Narrafiilm © 2025–2026 · Built with AI · Released under MIT License</p>
</footer>

</div>
