---
layout: home

title: Voxplore
titleTemplate: false

hero:
  name: Voxplore
  text: AI First-Person Video Narrator
  tagline: 上传视频，AI 代入主角视角，一键生成电影感配音解说
  image:
    src: /logo.png
    alt: Voxplore
  actions:
    - theme: brand
      text: 快速开始 →
      link: /guide/quick-start
    - theme: alt
      text: 查看功能
      link: /features
    - theme: alt
      text: GitHub
      link: https://github.com/Agions/Voxplore

features:
  - icon:
      src: /icons/monologue.svg
    title: 第一人称代入
    details: Qwen2.5-VL 识别画面主角视角，DeepSeek-V3 代入"我"的口吻，生成自然沉浸的解说稿
  - icon:
      src: /icons/emotion.svg
    title: 情感配音合成
    details: 5 种情感风格（治愈/悬疑/励志/怀旧/浪漫），Edge-TTS 高保真合成，F5-TTS 音色克隆
  - icon:
      src: /icons/subtitle.svg
    title: 精准 ASS 字幕
    details: 基于 TTS word-level timing，音字同步精度 50ms 以内，电影级字幕样式
  - icon:
      src: /icons/export.svg
    title: 多格式导出
    details: H.264/H.265 MP4 直出，或原生剪映草稿 JSON，无缝继续精剪
  - icon:
      src: /icons/privacy.svg
    title: 隐私优先
    details: 视频不上传云端，API Key 自持，本地处理优先，MIT 完全开源
  - icon:
      src: /icons/speed.svg
    title: 高性能管线
    details: CUDA GPU 加速（10x 实时），无 GPU 自动回退 CPU，设计流畅
---

<div class="nf-home">

<!-- Social Proof Banner -->

<!-- Hero Tag Line Override -->
<div class="nf-hero-tag">
  <span class="nf-hero-tag-inner">AI First-Person Video Narrator</span>
</div>
<div class="nf-proof-bar">
  <span class="nf-proof-item">
    <svg class="nf-proof-dot" viewBox="0 0 8 8" xmlns="http://www.w3.org/2000/svg"><circle cx="4" cy="4" r="3.5" fill="#10B981"/></svg>
    v3.6.0 已发布
  </span>
  <span class="nf-proof-sep">·</span>
  <span class="nf-proof-item">
    <svg class="nf-proof-dot" viewBox="0 0 8 8" xmlns="http://www.w3.org/2000/svg"><circle cx="4" cy="4" r="3.5" fill="#0A84FF"/></svg>
    DeepSeek-V3 解说生成
  </span>
  <span class="nf-proof-sep">·</span>
  <span class="nf-proof-item">
    <svg class="nf-proof-dot" viewBox="0 0 8 8" xmlns="http://www.w3.org/2000/svg"><circle cx="4" cy="4" r="3.5" fill="#8B5CF6"/></svg>
    SenseVoice ASR
  </span>
  <span class="nf-proof-sep">·</span>
  <span class="nf-proof-item">
    <svg class="nf-proof-dot" viewBox="0 0 8 8" xmlns="http://www.w3.org/2000/svg"><circle cx="4" cy="4" r="3.5" fill="#F59E0B"/></svg>
    MIT 开源免费
  </span>
</div>

<!-- Comparison Table -->
<section class="nf-section">
  <h2 class="nf-section-title">与"传统视频解说"对比</h2>
  <div class="nf-compare-table">
    <div class="nf-compare-row nf-compare-header">
      <div></div>
      <div><strong>传统方式</strong></div>
      <div><strong>Voxplore</strong></div>
    </div>
    <div class="nf-compare-row">
      <div class="nf-compare-dim">制作时间</div>
      <div class="nf-compare-old">30–120 分钟</div>
      <div class="nf-compare-new"><span class="nf-compare-highlight">3–10 分钟</span></div>
    </div>
    <div class="nf-compare-row">
      <div class="nf-compare-dim">配音成本</div>
      <div class="nf-compare-old">专业配音 ¥50–500/分钟</div>
      <div class="nf-compare-new"><span class="nf-compare-highlight">&lt;¥0.01/视频</span></div>
    </div>
    <div class="nf-compare-row">
      <div class="nf-compare-dim">技术门槛</div>
      <div class="nf-compare-old">需专业剪辑 + 配音</div>
      <div class="nf-compare-new"><span class="nf-compare-highlight">上传视频，一键完成</span></div>
    </div>
    <div class="nf-compare-row">
      <div class="nf-compare-dim">隐私安全</div>
      <div class="nf-compare-old">素材上传第三方平台</div>
      <div class="nf-compare-new"><span class="nf-compare-highlight">视频永不上传云端</span></div>
    </div>
    <div class="nf-compare-row">
      <div class="nf-compare-dim">字幕同步</div>
      <div class="nf-compare-old">手动对齐，耗时费眼</div>
      <div class="nf-compare-new"><span class="nf-compare-highlight">TTS word-level，50ms 精度</span></div>
    </div>
    <div class="nf-compare-row">
      <div class="nf-compare-dim">导出格式</div>
      <div class="nf-compare-old">仅 MP4</div>
      <div class="nf-compare-new"><span class="nf-compare-highlight">MP4 + 剪映草稿 JSON</span></div>
    </div>
  </div>
</section>

<!-- Why Section -->
<section class="nf-section">
  <h2 class="nf-section-title">为什么选择 Voxplore</h2>
  <div class="nf-why-grid">
    <div class="nf-why-card">
      <div class="nf-why-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 6v6l4 2"/>
        </svg>
      </div>
      <div class="nf-why-content">
        <h3>3 分钟完成解说视频</h3>
        <p>从上传视频到导出成品，全流程自动化。AI 自动分析、自动写稿、自动配音，无需手动剪辑。</p>
      </div>
    </div>
    <div class="nf-why-card">
      <div class="nf-why-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
        </svg>
      </div>
      <div class="nf-why-content">
        <h3>不到一分钱一个视频</h3>
        <p>DeepSeek-V3 成本极低，约 $0.1 / 1M tokens。处理一个 5 分钟视频成本不足 <strong>1 分钱</strong>。</p>
      </div>
    </div>
    <div class="nf-why-card">
      <div class="nf-why-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
          <path d="M7 11V7a5 5 0 0110 0v4"/>
        </svg>
      </div>
      <div class="nf-why-content">
        <h3>视频永不上传云端</h3>
        <p>全部处理在本地完成。FFmpeg 本地合成，API 仅传输文字（解说稿），你的视频永远留在本机。</p>
      </div>
    </div>
    <div class="nf-why-card">
      <div class="nf-why-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
        </svg>
      </div>
      <div class="nf-why-content">
        <h3>5 种情感风格</h3>
        <p>治愈 · 悬疑 · 励志 · 怀旧 · 浪漫。AI 根据视频内容自动匹配最合适的解说语气。</p>
      </div>
    </div>
  </div>
</section>

<!-- Workflow -->
<section class="nf-section">
  <h2 class="nf-section-title">工作流程</h2>
  <div class="nf-workflow">
    <div class="nf-workflow-step" data-step="1">
      <div class="nf-workflow-num">1</div>
      <div class="nf-workflow-content">
        <div class="nf-workflow-title">导入视频</div>
        <div class="nf-workflow-desc">拖入 MP4 / MOV / AVI / MKV / WebM，系统自动分析</div>
      </div>
    </div>
    <div class="nf-workflow-arrow"><svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 8h8M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
    <div class="nf-workflow-step" data-step="2">
      <div class="nf-workflow-num">2</div>
      <div class="nf-workflow-content">
        <div class="nf-workflow-title">AI 场景理解</div>
        <div class="nf-workflow-desc">Qwen2.5-VL 逐帧分析，识别主角、地点、动作与氛围</div>
      </div>
    </div>
    <div class="nf-workflow-arrow"><svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 8h8M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
    <div class="nf-workflow-step" data-step="3">
      <div class="nf-workflow-num">3</div>
      <div class="nf-workflow-content">
        <div class="nf-workflow-title">生成解说稿</div>
        <div class="nf-workflow-desc">DeepSeek-V3 代入"我"视角，撰写自然流畅的解说词</div>
      </div>
    </div>
    <div class="nf-workflow-arrow"><svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 8h8M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
    <div class="nf-workflow-step" data-step="4">
      <div class="nf-workflow-num">4</div>
      <div class="nf-workflow-content">
        <div class="nf-workflow-title">配音 + 字幕</div>
        <div class="nf-workflow-desc">Edge-TTS 合成配音，ASS 字幕音字同步，电影感输出</div>
      </div>
    </div>
  </div>
</section>

<!-- Tech Stack -->
<section class="nf-section">
  <h2 class="nf-section-title">技术栈</h2>
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
      <div><code>Edge-TTS · F5-TTS</code></div>
      <div>Edge 主流低延迟，F5 零样本音色克隆（2026.03）</div>
    </div>
    <div class="nf-arch-row">
      <div><span class="nf-arch-module">字幕对齐</span></div>
      <div><code>TTS word-level timing</code></div>
      <div>音字精准同步，电影级 ASS 字幕，50ms 精度</div>
    </div>
    <div class="nf-arch-row">
      <div><span class="nf-arch-module">视频合成</span></div>
      <div><code>FFmpeg · H.264/H.265</code></div>
      <div>MP4 输出或原生剪映草稿 JSON</div>
    </div>
  </div>
</section>

<!-- Getting Started -->
<section class="nf-section">
  <h2 class="nf-section-title">快速开始</h2>
  <div class="nf-start-cards">
    <a href="/guide/quick-start" class="nf-start-card">
      <div class="nf-start-card-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
        </svg>
      </div>
      <div class="nf-start-card-title">5 分钟快速上手</div>
      <div class="nf-start-card-desc">下载安装包 / Homebrew / 源码运行，三种方式任选</div>
      <span class="nf-start-card-arrow">→</span>
    </a>
    <a href="/guide/quick-start#配置-api-key" class="nf-start-card">
      <div class="nf-start-card-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2a10 10 0 0 1 0 20 10 10 0 0 1 0-20"/>
          <path d="M12 8v4l3 3"/>
        </svg>
      </div>
      <div class="nf-start-card-title">配置 DeepSeek API</div>
      <div class="nf-start-card-desc">每月约 $1 足够，处理一个 5 分钟视频成本不足 1 分钱</div>
      <span class="nf-start-card-arrow">→</span>
    </a>
    <a href="/features" class="nf-start-card">
      <div class="nf-start-card-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 16v-4M12 8h.01"/>
        </svg>
      </div>
      <div class="nf-start-card-title">了解功能详情</div>
      <div class="nf-start-card-desc">情感风格、字幕样式、导出格式、硬件要求全解析</div>
      <span class="nf-start-card-arrow">→</span>
    </a>
  </div>
</section>

<!-- Stats -->
<div class="nf-stats">
  <div class="nf-stat">
    <div class="nf-stat-value">v3.6.0</div>
    <div class="nf-stat-label">最新版本</div>
  </div>
  <div class="nf-stat-sep">|</div>
  <div class="nf-stat">
    <div class="nf-stat-value">MIT</div>
    <div class="nf-stat-label">开源协议</div>
  </div>
  <div class="nf-stat-sep">|</div>
  <div class="nf-stat">
    <div class="nf-stat-value">Python 3.10+</div>
    <div class="nf-stat-label">跨平台</div>
  </div>
  <div class="nf-stat-sep">|</div>
  <div class="nf-stat">
    <div class="nf-stat-value">PySide6</div>
    <div class="nf-stat-label">Qt 桌面端</div>
  </div>
  <div class="nf-stat-sep">|</div>
  <div class="nf-stat">
    <div class="nf-stat-value">&lt;¥0.01</div>
    <div class="nf-stat-label">单视频成本</div>
  </div>
</div>

</div>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  // Staggered entrance for workflow steps
  const steps = document.querySelectorAll('.nf-workflow-step')
  steps.forEach((step, i) => {
    step.style.opacity = '0'
    step.style.transform = 'translateY(16px)'
    step.style.transition = `opacity 0.4s ease ${i * 0.12}s, transform 0.4s ease ${i * 0.12}s`
    requestAnimationFrame(() => {
      step.style.opacity = '1'
      step.style.transform = 'translateY(0)'
    })
  })

  // Staggered entrance for why cards
  const cards = document.querySelectorAll('.nf-why-card')
  cards.forEach((card, i) => {
    card.style.opacity = '0'
    card.style.transform = 'translateY(12px)'
    card.style.transition = `opacity 0.35s ease ${0.15 + i * 0.08}s, transform 0.35s ease ${0.15 + i * 0.08}s`
    requestAnimationFrame(() => {
      card.style.opacity = '1'
      card.style.transform = 'translateY(0)'
    })
  })

  // Staggered entrance for start cards
  const startCards = document.querySelectorAll('.nf-start-card')
  startCards.forEach((card, i) => {
    card.style.opacity = '0'
    card.style.transform = 'translateY(10px)'
    card.style.transition = `opacity 0.35s ease ${0.2 + i * 0.07}s, transform 0.35s ease ${0.2 + i * 0.07}s`
    requestAnimationFrame(() => {
      card.style.opacity = '1'
      card.style.transform = 'translateY(0)'
    })
  })

  // Stats bar entrance
  const stats = document.querySelector('.nf-stats')
  if (stats) {
    stats.style.opacity = '0'
    stats.style.transition = 'opacity 0.4s ease 0.5s'
    requestAnimationFrame(() => {
      stats.style.opacity = '1'
    })
  }

  // Proof bar entrance
  const proofBar = document.querySelector('.nf-proof-bar')
  if (proofBar) {
    proofBar.style.opacity = '0'
    proofBar.style.transition = 'opacity 0.4s ease 0.1s'
    requestAnimationFrame(() => {
      proofBar.style.opacity = '1'
    })
  }
})
</script>
