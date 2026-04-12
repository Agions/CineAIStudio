import{_ as n,o as s,c as e,ag as t}from"./chunks/framework.uOkKsJ4G.js";const g=JSON.parse('{"title":"架构概览","description":"Narrafiilm 系统架构和技术设计的核心要点速查。","frontmatter":{"title":"架构概览","description":"Narrafiilm 系统架构和技术设计的核心要点速查。"},"headers":[],"relativePath":"architecture.md","filePath":"architecture.md","lastUpdated":1776004292000}'),p={name:"architecture.md"};function i(l,a,d,r,c,o){return s(),e("div",null,[...a[0]||(a[0]=[t(`<h1 id="架构概览" tabindex="-1">架构概览 <a class="header-anchor" href="#架构概览" aria-label="Permalink to &quot;架构概览&quot;">​</a></h1><p>本文档帮助你快速理解 Narrafiilm 的核心系统架构。</p><hr><h2 id="系统架构" tabindex="-1">系统架构 <a class="header-anchor" href="#系统架构" aria-label="Permalink to &quot;系统架构&quot;">​</a></h2><p>Narrafiilm 采用 <strong>三层模块化架构</strong>：</p><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>┌──────────────────────────────────────────────────────────────┐</span></span>
<span class="line"><span>│                         UI 层 (PySide6)                      │</span></span>
<span class="line"><span>│     主窗口 · 素材面板 · 预览区域 · 时间线面板 · 状态栏         │</span></span>
<span class="line"><span>├──────────────────────────────────────────────────────────────┤</span></span>
<span class="line"><span>│                        服务层 (Services)                      │</span></span>
<span class="line"><span>│   AI 服务 · 视频处理服务 · 音频服务 · 导出服务                 │</span></span>
<span class="line"><span>├──────────────────────────────────────────────────────────────┤</span></span>
<span class="line"><span>│                         核心层 (Core)                         │</span></span>
<span class="line"><span>│   配置管理 · 事件总线 · 依赖注入 · 安全密钥管理               │</span></span>
<span class="line"><span>├──────────────────────────────────────────────────────────────┤</span></span>
<span class="line"><span>│                        外部依赖层                              │</span></span>
<span class="line"><span>│        FFmpeg · OpenCV · Qwen2.5-VL · DeepSeek-V3 · Edge-TTS │</span></span>
<span class="line"><span>└──────────────────────────────────────────────────────────────┘</span></span></code></pre></div><p><strong>设计原则</strong>：UI 层与业务逻辑完全解耦，可以独立替换 UI 框架而不影响核心功能。</p><hr><h2 id="目录结构" tabindex="-1">目录结构 <a class="header-anchor" href="#目录结构" aria-label="Permalink to &quot;目录结构&quot;">​</a></h2><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>Narrafiilm/</span></span>
<span class="line"><span>├── app/</span></span>
<span class="line"><span>│   ├── core/                    # 核心模块</span></span>
<span class="line"><span>│   │   ├── application.py       # 应用生命周期</span></span>
<span class="line"><span>│   │   ├── config_manager.py    # 配置管理（YAML + .env）</span></span>
<span class="line"><span>│   │   ├── event_bus.py        # 事件总线（发布/订阅，解耦通信）</span></span>
<span class="line"><span>│   │   ├── service_container.py # 依赖注入容器（按需懒加载）</span></span>
<span class="line"><span>│   │   └── secure_key_manager.py # API 密钥安全管理</span></span>
<span class="line"><span>│   │</span></span>
<span class="line"><span>│   ├── services/                # 业务服务层</span></span>
<span class="line"><span>│   │   ├── ai/                  # AI 服务</span></span>
<span class="line"><span>│   │   │   ├── providers/       # LLM 提供商抽象（OpenAI 兼容接口）</span></span>
<span class="line"><span>│   │   │   ├── llm_manager.py   # LLM 统一管理器</span></span>
<span class="line"><span>│   │   │   ├── scene_analyzer.py # Qwen2.5-VL 场景理解</span></span>
<span class="line"><span>│   │   │   ├── script_generator.py # DeepSeek-V3 解说生成</span></span>
<span class="line"><span>│   │   │   └── voice_generator.py  # Edge-TTS / F5-TTS 语音合成</span></span>
<span class="line"><span>│   │   ├── video/               # 视频处理服务</span></span>
<span class="line"><span>│   │   │   └── monologue_maker.py  # AI 第一人称解说制作（核心）</span></span>
<span class="line"><span>│   │   └── export/              # 导出服务</span></span>
<span class="line"><span>│   │       └── jianying_exporter.py  # 剪映草稿 JSON 导出</span></span>
<span class="line"><span>│   │</span></span>
<span class="line"><span>│   ├── plugins/                 # 插件系统（Plugin Manifest v1）</span></span>
<span class="line"><span>│   └── ui/                      # 界面层 (PySide6)</span></span>
<span class="line"><span>│       ├── main_window.py         # 主窗口</span></span>
<span class="line"><span>│       ├── panels/                # 面板组件</span></span>
<span class="line"><span>│       ├── widgets/               # 通用组件</span></span>
<span class="line"><span>│       └── pages/                # 页面组件</span></span>
<span class="line"><span>│</span></span>
<span class="line"><span>├── tests/                       # 测试（pytest + pytest-asyncio）</span></span>
<span class="line"><span>├── docs/                        # VitePress 文档</span></span>
<span class="line"><span>└── resources/                   # 静态资源</span></span></code></pre></div><hr><h2 id="核心模块" tabindex="-1">核心模块 <a class="header-anchor" href="#核心模块" aria-label="Permalink to &quot;核心模块&quot;">​</a></h2><h3 id="application-应用生命周期" tabindex="-1">Application（应用生命周期） <a class="header-anchor" href="#application-应用生命周期" aria-label="Permalink to &quot;Application（应用生命周期）&quot;">​</a></h3><table tabindex="0"><thead><tr><th>组件</th><th>职责</th></tr></thead><tbody><tr><td><code>ApplicationLauncher</code></td><td>命令行参数处理、早期初始化</td></tr><tr><td><code>Application</code></td><td>管理应用状态、服务容器、事件总线</td></tr><tr><td><code>ServiceContainer</code></td><td>依赖注入容器，按需懒加载服务</td></tr><tr><td><code>EventBus</code></td><td>模块间解耦通信（发布/订阅模式）</td></tr></tbody></table><h3 id="llmmanager-ai-统一管理器" tabindex="-1">LLMManager（AI 统一管理器） <a class="header-anchor" href="#llmmanager-ai-统一管理器" aria-label="Permalink to &quot;LLMManager（AI 统一管理器）&quot;">​</a></h3><table tabindex="0"><thead><tr><th>方法</th><th>说明</th></tr></thead><tbody><tr><td><code>complete(prompt, model?)</code></td><td>文本补全</td></tr><tr><td><code>analyze_video(video_path)</code></td><td>Qwen2.5-VL 视频内容分析</td></tr><tr><td><code>generate_script(context, emotion)</code></td><td>DeepSeek-V3 生成解说文案</td></tr></tbody></table><h3 id="securekeymanager-密钥安全" tabindex="-1">SecureKeyManager（密钥安全） <a class="header-anchor" href="#securekeymanager-密钥安全" aria-label="Permalink to &quot;SecureKeyManager（密钥安全）&quot;">​</a></h3><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>API Key 存储优先级:</span></span>
<span class="line"><span>1. OS Keychain (macOS Keychain / Windows Credential Manager / Linux Secret Service)</span></span>
<span class="line"><span>2. 加密文件 (Fernet + PBKDF2)</span></span></code></pre></div><hr><h2 id="视频处理流程" tabindex="-1">视频处理流程 <a class="header-anchor" href="#视频处理流程" aria-label="Permalink to &quot;视频处理流程&quot;">​</a></h2><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>视频 → 场景检测（PySceneDetect）</span></span>
<span class="line"><span>      → AI 内容分析（Qwen2.5-VL）</span></span>
<span class="line"><span>      → 解说生成（DeepSeek-V3）</span></span>
<span class="line"><span>      → 配音合成（Edge-TTS / F5-TTS）</span></span>
<span class="line"><span>      → 字幕生成（ASS + TTS word-level timing）</span></span>
<span class="line"><span>      → 视频合成（FFmpeg）</span></span>
<span class="line"><span>      → 导出（MP4 / 剪映草稿 JSON）</span></span></code></pre></div><table tabindex="0"><thead><tr><th>步骤</th><th>核心技术</th></tr></thead><tbody><tr><td>场景检测</td><td>PySceneDetect</td></tr><tr><td>内容分析</td><td>Qwen2.5-VL（阿里云百炼 API）</td></tr><tr><td>文案生成</td><td>DeepSeek-V3.2（API）</td></tr><tr><td>语音合成</td><td>Edge-TTS（本地）/ F5-TTS（本地）</td></tr><tr><td>字幕生成</td><td>TTS word-level timing → ASS 格式</td></tr><tr><td>视频合成</td><td>FFmpeg（H.264 / H.265）</td></tr></tbody></table><hr><h2 id="插件系统" tabindex="-1">插件系统 <a class="header-anchor" href="#插件系统" aria-label="Permalink to &quot;插件系统&quot;">​</a></h2><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>Plugin Interface (抽象基类)</span></span>
<span class="line"><span>       │</span></span>
<span class="line"><span>       ├── VideoProcessorPlugin</span></span>
<span class="line"><span>       ├── ExportPlugin</span></span>
<span class="line"><span>       ├── AIGeneratorPlugin</span></span>
<span class="line"><span>       └── UIExtensionPlugin</span></span></code></pre></div><p>插件加载流程：</p><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>扫描 plugins/ 目录 → 验证 manifest.json → 实例化 → 注册服务</span></span></code></pre></div><p>详见 <a href="./guide/plugin-development.html">插件开发指南</a>。</p><hr><h2 id="技术栈" tabindex="-1">技术栈 <a class="header-anchor" href="#技术栈" aria-label="Permalink to &quot;技术栈&quot;">​</a></h2><table tabindex="0"><thead><tr><th>层级</th><th>技术选型</th></tr></thead><tbody><tr><td>GUI 框架</td><td><strong>PySide6</strong> (LGPL)</td></tr><tr><td>视频处理</td><td>FFmpeg、opencv-python</td></tr><tr><td>AI 分析</td><td>Qwen2.5-VL（阿里云百炼 API）</td></tr><tr><td>AI 文案</td><td>DeepSeek-V3.2（API）</td></tr><tr><td>语音合成</td><td>Edge-TTS（本地）、F5-TTS（本地）</td></tr><tr><td>加密</td><td>cryptography (Fernet / AES-128)</td></tr><tr><td>配置</td><td>YAML、python-dotenv</td></tr><tr><td>测试</td><td>pytest、pytest-asyncio</td></tr></tbody></table><hr><h2 id="相关文档" tabindex="-1">相关文档 <a class="header-anchor" href="#相关文档" aria-label="Permalink to &quot;相关文档&quot;">​</a></h2><ul><li><a href="./security.html">安全设计</a> — API 密钥安全和文件操作安全</li><li><a href="./guide/plugin-development.html">插件开发指南</a> — 如何编写插件</li><li><a href="./guide/ai-configuration.html">AI 配置指南</a> — AI 服务配置</li></ul>`,34)])])}const u=n(p,[["render",i]]);export{g as __pageData,u as default};
