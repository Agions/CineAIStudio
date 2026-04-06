# Narrafiilm 项目规划

> 版本：v3.3.0 | 日期：2026-04-06 | 作者：Agions

---

## 1. 产品定位

**Narrafiilm** — AI First-Person Video Narrator

> 上传视频，AI 代入画面主角视角，一键生成配音解说。

核心场景：vlog 叙事化改造、教学实操视频、游戏录屏解说、会议录制叙事、纪录片风格改造。

---

## 2. 市场定位

| 维度 | 描述 |
|------|------|
| **赛道** | AI Video Narration / First-Person Commentary |
| **差异化** | 专注第一人称沉浸感，非通用解说 |
| **目标用户** | 内容创作者、Vlogger、教育工作者、游戏主播 |
| **当前阶段** | 功能验证 → 增长准备 |

---

## 3. 竞品分析

| 竞品 | 特点 | Narrafiilm 对策 |
|------|------|----------------|
| **剪映** | 成熟但 AI 功能浅，收费 | 免费 + 深度 AI |
| **腾讯智影** | 数字人 + 配音，通用 | 专注第一人称沉浸感 |
| **HeyGen** | 数字人视频 | 不做数字人，做真实视频改造 |
| **F5-TTS / CosyVoice** | 开源 TTS 能力强 | 已集成 Edge-TTS + F5-TTS |
| **通义万象** | AI 视频生成 | 不做生成，做真实视频叙事化 |

---

## 4. 技术架构（现状）

```
视频 → SceneAnalyzer → Qwen2.5-VL 抽帧理解
                    ↓
         ScriptGenerator + DeepSeek-V3 文案生成
                    ↓
         VoiceGenerator + Edge-TTS / F5-TTS 配音
                    ↓
         CaptionGenerator（基于 TTS word-level timing）
                    ↓
         JianyingExporter 剪映草稿 / DirectVideoExporter MP4
```

### 当前核心问题

| 问题 | 优先级 | 说明 |
|------|--------|------|
| TTS word-level timing 精度不足 | 🔴 高 | 字幕与配音同步依赖估算，非真实时长 |
| 单次调用链路慢 | 🔴 高 | 串行为主，无流式输出 |
| 缺少用户输入风格预设 | 🟡 中 | 只能选 emotion，无法精细控制文案风格 |
| 导出格式单一 | 🟡 中 | 仅支持剪映草稿 + MP4 |
| 国际化缺失 | 🟡 中 | 仅中文，英文场景文本硬编码 |
| 本地模型支持弱 | 🟡 中 | SenseVoice 依赖网络，无本地 Whisper fallback |

---

## 5. 版本规划

### v3.3.0 — 体验升级 ✅

**状态：已完成（2026-04-06）**

**目标：让 demo 可运行，消除致命体验问题**

| 功能 | 负责人 | 状态 |
|------|--------|------|
| ~~GPT-4.1 → GPT-5.4 文档更新~~ | AI | ✅ |
| ~~VideoForge → Narrafiilm 品牌重命名~~ | AI | ✅ |
| ~~MonologueMaker 核心 bug 修复~~ | AI | ✅ |
| ~~F5-TTS 零样本克隆集成~~ | AI | ✅ |
| TTS word-level timing 精确化 | AI | ✅ |
| F5-TTS 零样本克隆集成 | AI | ✅ |
| 字幕对齐精度评估工具 | AI | 🔲 |

### v3.4.0 — 性能与稳定性

| 功能 | 状态 |
|------|------|
| SenseVoice 本地 ASR（离线降级）| 🔲 |
| 流式 LLM 输出（减少等待感）| 🔲 |
| 导出进度可视化 | 🔲 |
| 项目文件持久化（.narrafiilm 格式）| 🔲 |

### v4.0.0 — 增长准备

| 功能 | 状态 |
|------|------|
| 预设模板市场（情感/场景分类）| 🔲 |
| 多语言支持（英/日/韩）| 🔲 |
| 直接导出 Premiere / DaVinci | 🔲 |
| API Server 模式（CLI + HTTP）| 🔲 |
| 插件系统（自定义 LLM Provider）| 🔲 |

---

## 6. 核心数据流（v3.3 目标）

```
用户输入
├── source_video: str          # 视频路径
├── context: str              # 场景描述（AI 参考）
├── emotion: str              # 情感基调
└── style: MonologueStyle    # 风格枚举

Pipeline
Step 1. SceneAnalyzer.analyze()
        输入: video_path
        输出: List[SceneInfo] (start, end, description)

Step 2. ScriptGenerator.generate_monologue()
        输入: context, emotion, duration
        输出: str (full_script) + List[ScriptSegment]

Step 3. VoiceGenerator.generate() [并行]
        输入: List[ScriptSegment]
        输出: List[GeneratedVoice] (audio_path, duration)

Step 4. CaptionGenerator.from_tts_timing()
        输入: audio + TTS word timestamps
        输出: List[Caption] (text, start, end)

Step 5. JianyingExporter / DirectVideoExporter
        输入: video + audio + captions
        输出: .draft.json | MP4
```

---

## 7. 关键依赖版本

| 组件 | 当前 | 目标 | 说明 |
|------|------|------|------|
| **DeepSeek-V3** | ✅ | ✅ | 主力文案模型 |
| **Qwen2.5-VL** | ✅ | ✅ | 视频理解 |
| **Edge-TTS** | 7.2.8 | 7.3+ | 主流配音 |
| **F5-TTS** | latest | v0.2+ | 音色克隆 |
| **SenseVoice** | ✅ | ✅ | ASR（待离线化）|
| **FFmpeg** | ✅ | ✅ | 视频处理 |
| **PySide6** | ✅ | ✅ | UI |

---

## 8. 技术债务

| 债务 | 影响 | 清理计划 |
|------|------|---------|
| `services/ai/_legacy/` ~7500 行 | 维护成本 | v3.4 前评审，可删则删 |
| `services/video/_legacy/` ~5300 行 | 维护成本 | v3.4 前评审，可删则删 |
| `orchestration/` 3个孤立模块 | 未来扩展 | v4.0 再评估 |
| `config/` 目录未梳理 | 配置混乱 | v3.4 统一 |
| 硬编码字符串（文案/UI）| 国际化 | v4.0 |

---

## 9. 下一步行动

### 立即执行（本周）

1. **F5-TTS 集成** — 音色克隆对齐 `VoiceGenerator`
2. **TTS word-level timing 修复** — 从估算改为 Edge-TTS 真实 timestamps
3. **CLI demo 可运行** — 消除任何运行时 import 错误

### 短期（两周内）

4. 项目文件持久化（`.narrafiilm` 项目格式）
5. 单元测试覆盖率 ≥ 85%
6. VitePress 文档更新（brand rename 后）

---

*本规划每版本发布前更新，最后更新：2026-04-06*
