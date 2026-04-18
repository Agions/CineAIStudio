import{_ as a,o as i,c as n,ag as p}from"./chunks/framework.8qlNDhri.js";const g=JSON.parse('{"title":"Voxplore 架构升级方案","description":"","frontmatter":{},"headers":[],"relativePath":"ARCHITECTURE_UPGRADE.md","filePath":"ARCHITECTURE_UPGRADE.md","lastUpdated":1776522580000}'),l={name:"ARCHITECTURE_UPGRADE.md"};function t(e,s,h,k,r,d){return i(),n("div",null,[...s[0]||(s[0]=[p(`<h1 id="voxplore-架构升级方案" tabindex="-1">Voxplore 架构升级方案 <a class="header-anchor" href="#voxplore-架构升级方案" aria-label="Permalink to &quot;Voxplore 架构升级方案&quot;">​</a></h1><h2 id="一、现状分析" tabindex="-1">一、现状分析 <a class="header-anchor" href="#一、现状分析" aria-label="Permalink to &quot;一、现状分析&quot;">​</a></h2><h3 id="当前架构" tabindex="-1">当前架构 <a class="header-anchor" href="#当前架构" aria-label="Permalink to &quot;当前架构&quot;">​</a></h3><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>┌──────────────────────────────────────────────────────────────┐</span></span>
<span class="line"><span>│                         UI 层 (PySide6)                      │</span></span>
<span class="line"><span>├──────────────────────────────────────────────────────────────┤</span></span>
<span class="line"><span>│                        服务层 (Services)                     │</span></span>
<span class="line"><span>│   AI服务 · 视频处理服务 · 音频服务 · 导出服务                  │</span></span>
<span class="line"><span>├──────────────────────────────────────────────────────────────┤</span></span>
<span class="line"><span>│                         核心层 (Core)                         │</span></span>
<span class="line"><span>│   配置管理 · 事件总线 · 依赖注入 · 安全密钥管理                 │</span></span>
<span class="line"><span>├──────────────────────────────────────────────────────────────┤</span></span>
<span class="line"><span>│                        外部依赖层                              │</span></span>
<span class="line"><span>│        FFmpeg · OpenCV · Qwen2.5-VL · DeepSeek-V3 · Edge-TTS │</span></span>
<span class="line"><span>└──────────────────────────────────────────────────────────────┘</span></span></code></pre></div><h3 id="当前痛点" tabindex="-1">当前痛点 <a class="header-anchor" href="#当前痛点" aria-label="Permalink to &quot;当前痛点&quot;">​</a></h3><table tabindex="0"><thead><tr><th>问题</th><th>影响</th></tr></thead><tbody><tr><td>无插件系统</td><td>无法扩展功能</td></tr><tr><td>无 Web API</td><td>无法远程调用/二次开发</td></tr><tr><td>AI Provider 硬编码</td><td>新增模型需改源码</td></tr><tr><td>视频穿插逻辑缺失</td><td>核心功能不完整</td></tr><tr><td>无视角映射</td><td>第一人称代入感弱</td></tr><tr><td>缓存策略简单</td><td>多实例无法共享</td></tr></tbody></table><hr><h2 id="二、升级后架构" tabindex="-1">二、升级后架构 <a class="header-anchor" href="#二、升级后架构" aria-label="Permalink to &quot;二、升级后架构&quot;">​</a></h2><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>┌─────────────────────────────────────────────────────────────────────────────┐</span></span>
<span class="line"><span>│                            表 现 层 (Presentation)                            │</span></span>
<span class="line"><span>│  ┌─────────────────┐  ┌──────────────────────┐  ┌────────────────────────┐  │</span></span>
<span class="line"><span>│  │   PySide6       │  │   FastAPI + Vue3     │  │   CLI (TUI/Pure)       │  │</span></span>
<span class="line"><span>│  │   桌面客户端     │  │   Web 界面            │  │   命令行工具            │  │</span></span>
<span class="line"><span>│  └─────────────────┘  └──────────────────────┘  └────────────────────────┘  │</span></span>
<span class="line"><span>├─────────────────────────────────────────────────────────────────────────────┤</span></span>
<span class="line"><span>│                            OpenAPI / GraphQL 网关                            │</span></span>
<span class="line"><span>│                    认证 · 限流 · 缓存 · 监控                                  │</span></span>
<span class="line"><span>├─────────────────────────────────────────────────────────────────────────────┤</span></span>
<span class="line"><span>│                            应 用 层 (Application)                            │</span></span>
<span class="line"><span>│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐   │</span></span>
<span class="line"><span>│  │  Pipeline        │  │  Plugin Manager  │  │  Task Queue (Celery)     │   │</span></span>
<span class="line"><span>│  │  Orchestrator    │  │  插件生命周期管理  │  │  后台异步任务             │   │</span></span>
<span class="line"><span>│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘   │</span></span>
<span class="line"><span>├─────────────────────────────────────────────────────────────────────────────┤</span></span>
<span class="line"><span>│                            服 务 层 (Services)                               │</span></span>
<span class="line"><span>│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │</span></span>
<span class="line"><span>│  │ Scene       │  │ Perspective  │  │ Video        │  │ Subtitle       │  │</span></span>
<span class="line"><span>│  │ Analyzer    │  │ Mapper ⭐NEW  │  │ Interleaver  │  │ Generator      │  │</span></span>
<span class="line"><span>│  │ 场景分析     │  │ 视角映射     │  │ ⭐NEW穿插逻辑 │  │ 字幕生成       │  │</span></span>
<span class="line"><span>│  └─────────────┘  └──────────────┘  └──────────────┘  └────────────────┘  │</span></span>
<span class="line"><span>│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │</span></span>
<span class="line"><span>│  │ Script      │  │ Voice        │  │ Export       │  │ Cache          │  │</span></span>
<span class="line"><span>│  │ Generator   │  │ Synthesizer  │  │ Manager      │  │ (Redis)        │  │</span></span>
<span class="line"><span>│  └─────────────┘  └──────────────┘  └──────────────┘  └────────────────┘  │</span></span>
<span class="line"><span>├─────────────────────────────────────────────────────────────────────────────┤</span></span>
<span class="line"><span>│                            核 心 层 (Domain)                                 │</span></span>
<span class="line"><span>│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────────┐    │</span></span>
<span class="line"><span>│  │ Event Bus      │  │ Service        │  │ Security                   │    │</span></span>
<span class="line"><span>│  │ (内存+MQ可选)   │  │ Container (DI) │  │ Key Manager               │    │</span></span>
<span class="line"><span>│  └────────────────┘  └────────────────┘  └────────────────────────────┘    │</span></span>
<span class="line"><span>├─────────────────────────────────────────────────────────────────────────────┤</span></span>
<span class="line"><span>│                            基 础 层 (Infrastructure)                         │</span></span>
<span class="line"><span>│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │</span></span>
<span class="line"><span>│  │ FFmpeg      │  │ Redis        │  │ SQLite       │  │ File System  │   │</span></span>
<span class="line"><span>│  │ 视频处理     │  │ 缓存层       │  │ 项目存储     │  │ 素材管理     │   │</span></span>
<span class="line"><span>│  └─────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │</span></span>
<span class="line"><span>└─────────────────────────────────────────────────────────────────────────────┘</span></span></code></pre></div><hr><h2 id="三、核心模块设计" tabindex="-1">三、核心模块设计 <a class="header-anchor" href="#三、核心模块设计" aria-label="Permalink to &quot;三、核心模块设计&quot;">​</a></h2><h3 id="_3-1-perspective-mapper-视角映射器-⭐-新增" tabindex="-1">3.1 Perspective Mapper（视角映射器）⭐ 新增 <a class="header-anchor" href="#_3-1-perspective-mapper-视角映射器-⭐-新增" aria-label="Permalink to &quot;3.1 Perspective Mapper（视角映射器）⭐ 新增&quot;">​</a></h3><p><strong>职责</strong>：建立&quot;解说-画面&quot;的视角映射关系</p><div class="language-python vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang">python</span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># app/services/video/perspective_mapper.py</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">from</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> dataclasses </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">import</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> dataclass</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">from</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> enum </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">import</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> Enum</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">from</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> typing </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">import</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> List, Dict, Optional</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">from</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> .models.perspective_models </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">import</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> (</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    SubjectRole, PerspectiveShot, ViewpointAnchor</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">)</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">class</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> PerspectiveMapper</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">:</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    &quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    第一人称视角映射器</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    </span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    将画面中的主体与解说视角建立映射关系：</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    - 识别画面中的主角位置（我/他/旁观者）</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    - 建立&quot;我&quot;的视觉坐标系</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    - 决定何时切入第一人称画面</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    &quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    </span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> map_scenes_to_perspective</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        self,</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        scenes: List[SceneSegment],</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        script: </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">,</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        video_keyframes: List[KeyFrame]</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    ) -&gt; List[PerspectiveShot]:</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        &quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        将场景与第一人称视角映射</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        </span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        Args:</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">            scenes: 场景分段列表</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">            script: 解说文本</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">            video_keyframes: 视频关键帧</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">            </span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        Returns:</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">            PerspectiveShot 列表，每个片段的视角信息</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        &quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">        ...</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        </span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> determine_viewpoint_anchor</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        self,</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        frame,</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        subject_positions: List[SubjectPosition]</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    ) -&gt; ViewpointAnchor:</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        &quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        确定视角锚点——&quot;我&quot;在画面中的位置</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        </span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        Returns:</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">            ViewpointAnchor: 包含空间位置和情感倾向</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        &quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">        ...</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        </span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> should_show_original_clip</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        self,</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        narration_segment: NarrationSegment,</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        emotional_intensity: </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">float</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    ) -&gt; InterleaveDecision:</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        &quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        决定是否展示原片画面</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        </span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        规则：</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        - 高情绪强度 → 展示原片刻画沉浸感</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        - 关键信息 → 画中画/高亮放大</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        - 叙事留白 → 纯解说无画面</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        &quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">        ...</span></span></code></pre></div><h3 id="_3-2-video-interleaver-视频穿插器-⭐-新增" tabindex="-1">3.2 Video Interleaver（视频穿插器）⭐ 新增 <a class="header-anchor" href="#_3-2-video-interleaver-视频穿插器-⭐-新增" aria-label="Permalink to &quot;3.2 Video Interleaver（视频穿插器）⭐ 新增&quot;">​</a></h3><p><strong>职责</strong>：智能决定何时展示原片、如何与解说穿插</p><div class="language-python vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang">python</span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># app/services/video/video_interleaver.py</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">from</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> dataclasses </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">import</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> dataclass</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">from</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> enum </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">import</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> Enum</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">from</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> typing </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">import</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> List, Tuple, Optional</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">from</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> .models.interleave_models </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">import</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> (</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    InterleaveMode, InterleaveDecision, ClipSegment</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">)</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">class</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> VideoInterleaver</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">:</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    &quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    视频穿插逻辑处理器</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    </span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    核心算法：解说与原片的穿插策略</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    - 解说为主模式：原片作为解说佐证</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    - 原片为主模式：解说作为画外音</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    - 交织模式：解说与原片交替出现</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    &quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    </span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> decide_interleave</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        self,</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        narration_timeline: List[NarrationSegment],</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        original_clips: List[ClipSegment],</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        perspective_shots: List[PerspectiveShot],</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        emotion_curve: List[</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">float</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">]</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    ) -&gt; InterleaveTimeline:</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        &quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        生成最终穿插时间线</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        </span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        Args:</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">            narration_timeline: 解说时间轴</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">            original_clips: 原片片段</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">            perspective_shots: 视角映射结果</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">            emotion_curve: 情感强度曲线</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">            </span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        Returns:</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">            InterleaveTimeline: 包含所有片段的排列和转场</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        &quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">        ...</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        </span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> apply_interleave_mode</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        self,</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        mode: InterleaveMode,</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        context: InterleaveContext</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    ) -&gt; InterleaveDecision:</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        &quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        根据模式应用穿插策略</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        </span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        Modes:</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        - NARRATION_PRIORITY: 解说优先，原片点缀</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        - ORIGINAL_PRIORITY: 原片优先，解说为辅</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        - EMOTIONAL_BURST: 情绪高潮时切入原片</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        - MINIMALIST: 纯解说，最小化原片</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        &quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">        ...</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        </span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> generate_transition</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        self,</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        from_clip: Optional[ClipSegment],</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        to_clip: Optional[ClipSegment],</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        transition_type: TransitionType</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    ) -&gt; TransitionEffect:</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        &quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        生成转场效果</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        </span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        Types:</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        - CUT: 硬切</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        - FADE: 淡入淡出</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        - DISSOLVE: 叠化</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        - ZOOM_HIGHLIGHT: 放大高亮</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        &quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">        ...</span></span></code></pre></div><h3 id="_3-3-plugin-system-插件系统-⭐-新增" tabindex="-1">3.3 Plugin System（插件系统）⭐ 新增 <a class="header-anchor" href="#_3-3-plugin-system-插件系统-⭐-新增" aria-label="Permalink to &quot;3.3 Plugin System（插件系统）⭐ 新增&quot;">​</a></h3><p><strong>职责</strong>：支持插件扩展核心功能</p><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>voxplore/</span></span>
<span class="line"><span>├── plugins/</span></span>
<span class="line"><span>│   ├── __init__.py</span></span>
<span class="line"><span>│   ├── manifest.schema.json       # 插件清单规范</span></span>
<span class="line"><span>│   ├── loader.py                  # 插件加载器</span></span>
<span class="line"><span>│   ├── registry.py                # 插件注册表</span></span>
<span class="line"><span>│   └── interfaces/</span></span>
<span class="line"><span>│       ├── __init__.py</span></span>
<span class="line"><span>│       ├── base.py                # BasePlugin 基类</span></span>
<span class="line"><span>│       ├── ai_generator.py        # AI 生成器接口</span></span>
<span class="line"><span>│       ├── export_plugin.py       # 导出插件接口</span></span>
<span class="line"><span>│       └── ui_extension.py         # UI 扩展接口</span></span>
<span class="line"><span>│   └── examples/</span></span>
<span class="line"><span>│       ├── wordstrike_plugin/     # 示例：字幕效果插件</span></span>
<span class="line"><span>│       └── custom_voice_plugin/     # 示例：自定义音色</span></span></code></pre></div><div class="language-python vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang">python</span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># app/plugins/interfaces/base.py</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">from</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> abc </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">import</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;"> ABC</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">, abstractmethod</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">from</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> dataclasses </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">import</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> dataclass</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">from</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> typing </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">import</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> Dict, Any, Optional</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">from</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> enum </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">import</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> Enum</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">class</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> PluginType</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;">Enum</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">):</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">    AI_GENERATOR</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;"> =</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> &quot;ai_generator&quot;</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">    EXPORT</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;"> =</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> &quot;export&quot;</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">    UI_EXTENSION</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;"> =</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> &quot;ui_extension&quot;</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">    VOICE_CLONE</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;"> =</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> &quot;voice_clone&quot;</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">    SUBTITLE_STYLE</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;"> =</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;"> &quot;subtitle_style&quot;</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;">@dataclass</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">class</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> PluginManifest</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">:</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">    id</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">: </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    name: </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    version: </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    author: </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    description: </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    plugin_type: PluginType</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    dependencies: Dict[</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">, </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">]  </span><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># package: version_spec</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    entry_point: </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;">  # module.path:class_name</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    permissions: list[</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">]</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">class</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> BasePlugin</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">ABC</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">):</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    &quot;&quot;&quot;所有插件的基类&quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    </span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    def</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;"> __init__</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(self, manifest: PluginManifest):</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">        self</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">.manifest </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> manifest</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">        self</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">._enabled </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;"> False</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        </span></span>
<span class="line"><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;">    @abstractmethod</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> initialize</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(self, app_context: </span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">&quot;AppContext&quot;</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">) -&gt; </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">None</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">:</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        &quot;&quot;&quot;初始化插件&quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">        ...</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        </span></span>
<span class="line"><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;">    @abstractmethod</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> enable</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(self) -&gt; </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">None</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">:</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        &quot;&quot;&quot;启用插件&quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">        self</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">._enabled </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;"> True</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        </span></span>
<span class="line"><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;">    @abstractmethod</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> disable</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(self) -&gt; </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">None</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">:</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        &quot;&quot;&quot;禁用插件&quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">        self</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">._enabled </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;"> False</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        </span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> is_enabled</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(self) -&gt; </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">bool</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">:</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">        return</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;"> self</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">._enabled</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        </span></span>
<span class="line"><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;">    @abstractmethod</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> get_metadata</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(self) -&gt; Dict[</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">, Any]:</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">        &quot;&quot;&quot;获取插件元数据&quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">        ...</span></span></code></pre></div><h3 id="_3-4-web-api-layer-web-api-层-⭐-新增" tabindex="-1">3.4 Web API Layer（Web API 层）⭐ 新增 <a class="header-anchor" href="#_3-4-web-api-layer-web-api-层-⭐-新增" aria-label="Permalink to &quot;3.4 Web API Layer（Web API 层）⭐ 新增&quot;">​</a></h3><p><strong>职责</strong>：提供 REST API 支持远程调用</p><div class="language-python vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang">python</span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># app/api/</span></span>
<span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># ├── __init__.py</span></span>
<span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># ├── main.py                 # FastAPI 入口</span></span>
<span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># ├── deps.py                 # 依赖注入</span></span>
<span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># ├── routers/</span></span>
<span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># │   ├── projects.py         # 项目管理</span></span>
<span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># │   ├── pipeline.py          # 流水线</span></span>
<span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># │   ├── export.py            # 导出</span></span>
<span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># │   └── health.py            # 健康检查</span></span>
<span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># └── schemas/                 # Pydantic 模型</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># app/api/main.py 示例</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">from</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> fastapi </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">import</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> FastAPI</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">from</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> fastapi.middleware.cors </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">import</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> CORSMiddleware</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">app </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> FastAPI(</span></span>
<span class="line"><span style="--shiki-light:#E36209;--shiki-dark:#FFAB70;">    title</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">&quot;Voxplore API&quot;</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">,</span></span>
<span class="line"><span style="--shiki-light:#E36209;--shiki-dark:#FFAB70;">    description</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">&quot;AI 第一人称视频解说 API&quot;</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">,</span></span>
<span class="line"><span style="--shiki-light:#E36209;--shiki-dark:#FFAB70;">    version</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">&quot;1.0.0&quot;</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">,</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">)</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">app.add_middleware(</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    CORSMiddleware,</span></span>
<span class="line"><span style="--shiki-light:#E36209;--shiki-dark:#FFAB70;">    allow_origins</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">[</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">&quot;*&quot;</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">],</span></span>
<span class="line"><span style="--shiki-light:#E36209;--shiki-dark:#FFAB70;">    allow_credentials</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">True</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">,</span></span>
<span class="line"><span style="--shiki-light:#E36209;--shiki-dark:#FFAB70;">    allow_methods</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">[</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">&quot;*&quot;</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">],</span></span>
<span class="line"><span style="--shiki-light:#E36209;--shiki-dark:#FFAB70;">    allow_headers</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">[</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">&quot;*&quot;</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">],</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">)</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;">@app.post</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">&quot;/v1/pipeline/narrate&quot;</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">)</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">async</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;"> def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> create_narration</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(request: NarrationRequest):</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    &quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    创建视频解说任务</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    </span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    上传视频文件，AI 生成第一人称解说</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    &quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    task_id </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;"> await</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> pipeline.submit(</span></span>
<span class="line"><span style="--shiki-light:#E36209;--shiki-dark:#FFAB70;">        source_video</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">request.video_url,</span></span>
<span class="line"><span style="--shiki-light:#E36209;--shiki-dark:#FFAB70;">        emotion</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">request.emotion,</span></span>
<span class="line"><span style="--shiki-light:#E36209;--shiki-dark:#FFAB70;">        style</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">request.style,</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    )</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    return</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> {</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">&quot;task_id&quot;</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">: task_id, </span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">&quot;status&quot;</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">: </span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">&quot;processing&quot;</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">}</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;">@app.get</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">&quot;/v1/pipeline/</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">{task_id}</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">/status&quot;</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">)</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">async</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;"> def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> get_task_status</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(task_id: </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">):</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    &quot;&quot;&quot;获取任务状态&quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    return</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> pipeline.get_status(task_id)</span></span></code></pre></div><h3 id="_3-5-ai-provider-adapter-ai-适配器-⭐-重构" tabindex="-1">3.5 AI Provider Adapter（AI 适配器）⭐ 重构 <a class="header-anchor" href="#_3-5-ai-provider-adapter-ai-适配器-⭐-重构" aria-label="Permalink to &quot;3.5 AI Provider Adapter（AI 适配器）⭐ 重构&quot;">​</a></h3><p><strong>现状</strong>：硬编码 10 个 Provider <strong>改进</strong>：插件化 Adapter 模式</p><div class="language-python vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang">python</span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># app/services/ai/adapters/</span></span>
<span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># ├── __init__.py</span></span>
<span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># ├── base.py              # BaseLLMAdapter</span></span>
<span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># ├── openai_adapter.py</span></span>
<span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># ├── deepseek_adapter.py</span></span>
<span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># ├── qwen_adapter.py</span></span>
<span class="line"><span style="--shiki-light:#6A737D;--shiki-dark:#6A737D;"># └── local_adapter.py     # Ollama/LM Studio</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">class</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> BaseLLMAdapter</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">ABC</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">):</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    &quot;&quot;&quot;LLM 适配器基类&quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    </span></span>
<span class="line"><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;">    @</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">property</span></span>
<span class="line"><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;">    @abstractmethod</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> provider_name</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(self) -&gt; </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">:</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">        ...</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        </span></span>
<span class="line"><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;">    @abstractmethod</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    async</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;"> def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> complete</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(self, prompt: </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">, </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">**</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">kwargs) -&gt; </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">:</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">        ...</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        </span></span>
<span class="line"><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;">    @abstractmethod</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    async</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;"> def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> analyze_video</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(self, video_path: </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">) -&gt; VideoAnalysis:</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">        ...</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        </span></span>
<span class="line"><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;">    @abstractmethod</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    async</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;"> def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> generate_script</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        self, </span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        context: </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">, </span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        emotion: </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">,</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">        **</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">kwargs</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    ) -&gt; ScriptOutput:</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">        ...</span></span>
<span class="line"></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">class</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> LLMProviderRegistry</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">:</span></span>
<span class="line"><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">    &quot;&quot;&quot;LLM Provider 注册中心&quot;&quot;&quot;</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">    </span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    def</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;"> __init__</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(self):</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">        self</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">._adapters: Dict[</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">, BaseLLMAdapter] </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> {}</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        </span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> register</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(self, adapter: BaseLLMAdapter) -&gt; </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">None</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">:</span></span>
<span class="line"><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">        self</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">._adapters[adapter.provider_name] </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> adapter</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        </span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> get</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(self, name: </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">) -&gt; Optional[BaseLLMAdapter]:</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">        return</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;"> self</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">._adapters.get(name)</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        </span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> list_providers</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(self) -&gt; List[</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">]:</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">        return</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;"> list</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">self</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">._adapters.keys())</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        </span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">    async</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;"> def</span><span style="--shiki-light:#6F42C1;--shiki-dark:#B392F0;"> complete</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(self, provider: </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">, prompt: </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">, </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">**</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">kwargs) -&gt; </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">str</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">:</span></span>
<span class="line"><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">        adapter </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">=</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;"> self</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">.get(provider)</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">        if</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;"> not</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> adapter:</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">            raise</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;"> ValueError</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">(</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">f</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">&quot;Unknown provider: </span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">{</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">provider</span><span style="--shiki-light:#005CC5;--shiki-dark:#79B8FF;">}</span><span style="--shiki-light:#032F62;--shiki-dark:#9ECBFF;">&quot;</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">)</span></span>
<span class="line"><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">        return</span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;"> await</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;"> adapter.complete(prompt, </span><span style="--shiki-light:#D73A49;--shiki-dark:#F97583;">**</span><span style="--shiki-light:#24292E;--shiki-dark:#E1E4E8;">kwargs)</span></span></code></pre></div><hr><h2 id="四、技术栈确认" tabindex="-1">四、技术栈确认 <a class="header-anchor" href="#四、技术栈确认" aria-label="Permalink to &quot;四、技术栈确认&quot;">​</a></h2><table tabindex="0"><thead><tr><th>层级</th><th>技术选型</th><th>说明</th></tr></thead><tbody><tr><td><strong>桌面 GUI</strong></td><td>PySide6</td><td>现有，保留</td></tr><tr><td><strong>Web 界面</strong></td><td>FastAPI + Vue3</td><td>新增</td></tr><tr><td><strong>任务队列</strong></td><td>Celery + Redis</td><td>新增</td></tr><tr><td><strong>消息总线</strong></td><td>EventBus（内存）<br>+ RabbitMQ（可选）</td><td>增强</td></tr><tr><td><strong>缓存</strong></td><td>Redis</td><td>新增</td></tr><tr><td><strong>数据库</strong></td><td>SQLite（本地）<br>+ PostgreSQL（远程 API）</td><td>增强</td></tr><tr><td><strong>AI 分析</strong></td><td>Qwen2.5-VL</td><td>现有</td></tr><tr><td><strong>AI 文案</strong></td><td>DeepSeek-V3 / Qwen-Plus</td><td>现有</td></tr><tr><td><strong>语音合成</strong></td><td>Edge-TTS / F5-TTS</td><td>现有</td></tr><tr><td><strong>视频处理</strong></td><td>FFmpeg</td><td>现有</td></tr></tbody></table><hr><h2 id="五、实施路线图" tabindex="-1">五、实施路线图 <a class="header-anchor" href="#五、实施路线图" aria-label="Permalink to &quot;五、实施路线图&quot;">​</a></h2><h3 id="phase-1-基础重构-1-2-周" tabindex="-1">Phase 1: 基础重构（1-2 周） <a class="header-anchor" href="#phase-1-基础重构-1-2-周" aria-label="Permalink to &quot;Phase 1: 基础重构（1-2 周）&quot;">​</a></h3><ul><li>[ ] Plugin System 框架搭建</li><li>[ ] AI Adapter 重构为注册模式</li><li>[ ] EventBus 增强（支持插件订阅）</li><li>[ ] 本地缓存层抽象</li></ul><h3 id="phase-2-核心功能-2-3-周" tabindex="-1">Phase 2: 核心功能（2-3 周） <a class="header-anchor" href="#phase-2-核心功能-2-3-周" aria-label="Permalink to &quot;Phase 2: 核心功能（2-3 周）&quot;">​</a></h3><ul><li>[ ] Perspective Mapper 实现</li><li>[ ] Video Interleaver 实现</li><li>[ ] Pipeline Orchestrator 重构</li><li>[ ] 多轨字幕增强</li></ul><h3 id="phase-3-web-api-2-周" tabindex="-1">Phase 3: Web API（2 周） <a class="header-anchor" href="#phase-3-web-api-2-周" aria-label="Permalink to &quot;Phase 3: Web API（2 周）&quot;">​</a></h3><ul><li>[ ] FastAPI 框架搭建</li><li>[ ] 项目管理 API</li><li>[ ] 流水线触发 API</li><li>[ ] 导出 API</li><li>[ ] Web 前端原型</li></ul><h3 id="phase-4-ui-ux-升级-2-3-周" tabindex="-1">Phase 4: UI/UX 升级（2-3 周） <a class="header-anchor" href="#phase-4-ui-ux-升级-2-3-周" aria-label="Permalink to &quot;Phase 4: UI/UX 升级（2-3 周）&quot;">​</a></h3><ul><li>[ ] 视觉风格全面升级</li><li>[ ] 解说编辑器组件</li><li>[ ] 时间线穿梭器</li><li>[ ] 情感调节器</li></ul><h3 id="phase-5-生态完善-持续" tabindex="-1">Phase 5: 生态完善（持续） <a class="header-anchor" href="#phase-5-生态完善-持续" aria-label="Permalink to &quot;Phase 5: 生态完善（持续）&quot;">​</a></h3><ul><li>[ ] 插件市场文档</li><li>[ ] SDK (Python / JS)</li><li>[ ] Docker 部署</li><li>[ ] CI/CD 优化</li></ul><hr><h2 id="六、文件变更清单" tabindex="-1">六、文件变更清单 <a class="header-anchor" href="#六、文件变更清单" aria-label="Permalink to &quot;六、文件变更清单&quot;">​</a></h2><h3 id="新增文件" tabindex="-1">新增文件 <a class="header-anchor" href="#新增文件" aria-label="Permalink to &quot;新增文件&quot;">​</a></h3><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>app/</span></span>
<span class="line"><span>├── plugins/</span></span>
<span class="line"><span>│   ├── __init__.py</span></span>
<span class="line"><span>│   ├── manifest.schema.json</span></span>
<span class="line"><span>│   ├── loader.py</span></span>
<span class="line"><span>│   ├── registry.py</span></span>
<span class="line"><span>│   └── interfaces/</span></span>
<span class="line"><span>│       ├── __init__.py</span></span>
<span class="line"><span>│       ├── base.py</span></span>
<span class="line"><span>│       ├── ai_generator.py</span></span>
<span class="line"><span>│       ├── export_plugin.py</span></span>
<span class="line"><span>│       └── ui_extension.py</span></span>
<span class="line"><span>├── api/</span></span>
<span class="line"><span>│   ├── __init__.py</span></span>
<span class="line"><span>│   ├── main.py</span></span>
<span class="line"><span>│   ├── deps.py</span></span>
<span class="line"><span>│   ├── routers/</span></span>
<span class="line"><span>│   │   ├── __init__.py</span></span>
<span class="line"><span>│   │   ├── projects.py</span></span>
<span class="line"><span>│   │   ├── pipeline.py</span></span>
<span class="line"><span>│   │   ├── export.py</span></span>
<span class="line"><span>│   │   └── health.py</span></span>
<span class="line"><span>│   └── schemas/</span></span>
<span class="line"><span>│       ├── __init__.py</span></span>
<span class="line"><span>│       └── models.py</span></span>
<span class="line"><span>└── services/</span></span>
<span class="line"><span>    └── video/</span></span>
<span class="line"><span>        ├── perspective_mapper.py    # ⭐ 新增</span></span>
<span class="line"><span>        ├── perspective_models.py     # ⭐ 新增</span></span>
<span class="line"><span>        ├── video_interleaver.py      # ⭐ 新增</span></span>
<span class="line"><span>        └── interleave_models.py      # ⭐ 新增</span></span></code></pre></div><h3 id="修改文件" tabindex="-1">修改文件 <a class="header-anchor" href="#修改文件" aria-label="Permalink to &quot;修改文件&quot;">​</a></h3><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>app/</span></span>
<span class="line"><span>├── core/</span></span>
<span class="line"><span>│   ├── service_container.py        # 插件支持</span></span>
<span class="line"><span>│   └── event_bus.py                # 分布式支持</span></span>
<span class="line"><span>├── services/</span></span>
<span class="line"><span>│   ├── ai/</span></span>
<span class="line"><span>│   │   ├── llm_manager.py          # Adapter 模式重构</span></span>
<span class="line"><span>│   │   └── providers/              # 适配器迁移</span></span>
<span class="line"><span>│   └── video/</span></span>
<span class="line"><span>│       └── monologue_maker.py      # 集成 Interleaver</span></span>
<span class="line"><span>└── ui/</span></span>
<span class="line"><span>    └── ...                         # UI 优化</span></span></code></pre></div><h3 id="删除文件" tabindex="-1">删除文件 <a class="header-anchor" href="#删除文件" aria-label="Permalink to &quot;删除文件&quot;">​</a></h3><div class="language- vp-adaptive-theme"><button title="Copy Code" class="copy"></button><span class="lang"></span><pre class="shiki shiki-themes github-light github-dark vp-code" tabindex="0"><code><span class="line"><span>app/</span></span>
<span class="line"><span>├── plugins/                        # 空目录，待实现</span></span></code></pre></div><hr><h2 id="七、向后兼容性" tabindex="-1">七、向后兼容性 <a class="header-anchor" href="#七、向后兼容性" aria-label="Permalink to &quot;七、向后兼容性&quot;">​</a></h2><ul><li>所有新增接口均通过 <code>@abstractmethod</code> 定义</li><li>现有 Provider 通过 Adapter 封装，不影响现有代码</li><li>Plugin System 通过 opt-in 方式启用，不影响默认行为</li><li>API 通过 <code>/v1/</code> 版本前缀，与现有 CLI 模式共存</li></ul>`,53)])])}const y=a(l,[["render",t]]);export{g as __pageData,y as default};
