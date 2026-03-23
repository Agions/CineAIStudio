# 更新日志

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.1.0] - 2026-03-23

### Changed
- **UI 框架迁移**: PyQt6 → PySide6 (LGPL 授权，商业友好)
- **依赖更新**: 
  - PyQt6 → PySide6>=6.6.0
  - 新增 Shiboken6>=6.6.0

### Fixed
- **代码审核修复**:
  - `EventBus.subscribe()` bug (访问未定义变量)
  - `SecureKeyManager` 无限循环问题
  - `ServiceContainer` 无效异常处理
  - 所有 LLM Provider 添加 `response.raise_for_status()`
  - 修复 `LLMResponse` 字段错误 (`usage` → `tokens_used`)
  - 修复安全模块无效转义序列
  
- **合规化修复**:
  - 删除重复文件 (`macos_theme_manager.py`, `macos_components.py`)
  - 187 个文件添加 MIT 版权头
  - PBKDF2 迭代次数提升至 480,000 (OWASP 标准)
  - DEBUG print 语句替换为 `logger.debug()`

### Security
- PBKDF2HMAC iterations: 100,000 → 480,000
- 添加 `__slots__` 建议到文档
- 完善异常处理和安全验证

### Documentation
- 更新 README.md (PySide6)
- 更新 ARCHITECTURE.md
- 更新 docs/README_EN.md
- 更新 docs/getting-started.md
- 更新 docs/features.md
- 添加合规化检测报告

---

## [3.0.0] - 2026-03-08

### Added
- **AI 创作模式**
  - 🎙️ AI 视频解说 (Commentary Maker)
  - 🎵 AI 视频混剪 (Mashup Maker)
  - 🎭 AI 第一人称独白 (Monologue Maker)

- **AI 模型支持**
  - OpenAI GPT-4o / GPT-5
  - Anthropic Claude Sonnet 4.5
  - Google Gemini 3.1 Flash/Pro
  - 阿里云 Qwen 3.5 / Max
  - DeepSeek R1 / V3.2
  - 智谱 GLM-5
  - 月之暗面 Kimi K2.5
  - 字节豆包 Doubao Pro/Lite
  - 腾讯混元 Hunyuan Pro
  - Edge TTS / OpenAI TTS

- **导出预设**
  - B站 (1080P 60fps)
  - YouTube (4K 60fps)
  - Twitter (1080P 压缩)
  - TikTok (竖屏)
  - 微信 (压缩)

- **UI 组件库**
  - GradientButton 渐变按钮
  - GlassCard 玻璃卡片
  - StatCard 统计卡片
  - ProgressRing 环形进度条

- **工具模块**
  - 懒加载 (LazyLoader)
  - 内存缓存 (MemoryCache)
  - 性能监控 (PerformanceMonitor)
  - 国际化 (I18n)
  - 后台任务 (TaskManager)
  - 视频工具 (VideoUtils)
  - 统一配置 (ConfigManager)
  - 统一日志 (Logger)

- **测试**
  - E2E 集成测试
  - 性能基准测试

### Changed
- UI 升级到 V3.0 专业暗色主题
- 可折叠导航栏
- 主题切换修复
- 代码重构，减少重复

### Fixed
- GitHub Actions CI/CD
- GitHub Pages 部署

---

## [2.0.0] - 2025-XX-XX

### Added
- 基础 AI 功能
- 视频导出

---

## [1.0.0] - 2024-XX-XX

### Added
- 项目初始化
- 基础 UI 框架
