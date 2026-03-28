# Change Log

> VideoForge AI 版本更新日志

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.0.2] - 2026-03-27

### Added

- 🔧 **日志系统优化** - 添加懒加载日志、EventBus 线程安全
- 📁 **模块化重构** - projects_page.py 拆分为组件模块

### Changed

- 🐛 修复 v3.0.2 两个 bug (issue #18)
  - `application.py`: ServiceRegistry.register 调用错误
  - `projects_page.py`: QVBoxLayout 重复包装问题
- 🔄 重构 projects_page.py: 1610行 → 789行 (-51%)
- 🔄 核心模块添加 proper logging

### Removed

- 🗑️ 删除重复的 macos_ 文件，统一使用 macOS_ 命名

---

## [3.0.1] - 2026-03-20

### Added

- 🌐 macOS 设计系统支持
- 📱 PySide6 Fluent UI 重构

---

## [3.0.0] - 2026-02-24

### Changed

#### 项目重命名

- 🎉 **项目更名** - CineFlow → VideoForge
- 📝 更新 README.md
- 📝 更新所有文档

#### 导航优化

- 🚀 **简化导航** - 只保留三个核心导航：首页、项目管理、设置
- 🎨 统一 macOS 风格设计

#### 文档

- 📖 **docsify 文档** - 创建专业的在线文档系统
- 📝 新增快速开始指南
- 📝 新增功能指南
- 📝 新增工作流程说明
- 📝 新增常见问题解答

---

## [2.0.0] - 2026-02-15

### Added

#### 核心功能

- 🤖 **国产 LLM 集成** - 支持通义千问、Kimi、智谱 GLM-5
- 🎮 **LLM 管理器** - 自动切换提供商、健康检查
- ⚡ **响应缓存** - 减少 API 调用，提升性能
- 🔄 **智能重试** - 指数退避算法
- 📊 **性能监控** - 成功率、缓存命中率，成本估算
- 🛡️ **错误处理** - 自定义异常、友好提示
- ⚙️ **配置管理** - YAML 配置文件

### Performance

- 缓存命中响应: 50ms (vs 2.3s without cache)
- 成功率: 95%+ (vs 85% in v1.5.0)
- 平均延迟: 1.5s (vs 1.8s in v1.5.0)

---

## [1.5.0] - 2025-11-01

### Added

- AI 视频解说功能
- AI 视频混剪功能
- AI 第一人称独白功能
- 剪映草稿导出

---

## Version History

| Version | Date | Status |
| ------- | ---- | ------ |
| 3.0.2 | 2026-03-27 | ✅ 当前版本 |
| 3.0.1 | 2026-03-20 | ✅ |
| 3.0.0 | 2026-02-24 | ✅ |
| 2.0.0 | 2026-02-15 | ✅ |
| 1.5.0 | 2025-11-01 | 📜 历史版本 |

---

**当前版本**: v3.0.2
