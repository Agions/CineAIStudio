# Change Log

> CineFlow AI 版本更新日志

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0-rc.1] - 2026-02-14

### Added

#### Core Features
- 🎯 **版本统一系统** - 单一来源版本管理 (pyproject.toml)
  - `app/utils/version.py` - 版本管理模块
  - `scripts/check_version.py` - 版本一致性检查工具

- 🤖 **国产 LLM 集成** - 支持多个国产大模型
  - **通义千问 Qwen 3** (qwen-plus, qwen3-max, qwen-flash, qwq-plus)
  - **Kimi 2.5** (moonshot-v1-8k, moonshot-v1-32k)
  - **智谱 GLM-5** (glm-5, glm-5-flash)
  - **百度文心 ERNIE 4.5**
  - **OpenAI** (保留兼容)

- 🎮 **LLM 管理器** - 自动切换失败提供商
  - 健康检查机制
  - 批量请求支持
  - 配置驱动的提供商管理

- 🧪 **测试框架**
  - pytest 测试框架
  - 单元测试覆盖 (Version, LLM providers, ScriptGenerator)
  - 集成测试支持

#### Documentation
- 📖 **安装指南** (`INSTALL.md`)
  - 完整的安装步骤
  - API 配置指南
  - 故障排查

- 📦 **技术栈文档** (`TECH-STACK.md`)
  - 字幕渲染技术 (PyQt6, OpenCV, FFmpeg)
  - 特效实现说明
  - 代码示例

- 👨‍💻 **开发者指南** (`DEVELOPER.md`)
  - 开发环境设置
  - 测试运行
  - 添加新 LLM 提供商步骤

- 🗺️ **项目路线图** (`ROADMAP.md`)
  - 版本规划 (v2.0.0 → v3.0.0)
  - 功能详情
  - 里程碑计划

- 🔧 **故障排查手册** (`TROUBLESHOOT.md`)
  - Windows dataclass 错误修复
  - 常见问题解决
  - 调试技巧

#### Configuration
- `config/llm.yaml` - LLM 配置文件
- `pytest.ini` - pytest 配置

#### Scripts
- `scripts/check_version.py` - 版本检查
- `scripts/check_dataclass.py` - dataclass 问题检查

### Changed

#### Renamed
- 项目名称从 **CineAIStudio** 重命名为 **CineFlow AI**

#### Updated
- `ScriptGenerator` - 支持使用 LLMManager
- `README.md` - 更新为 CineFlow AI 名称
- `requirements.txt` - 更新依赖配置

### Fixed

#### GitHub Issues
- ✅ **Issue #13** - 特效字幕技术栈询问
  - 创建 `TECH-STACK.md` 详细说明技术栈

- ✅ **Issue #12** - 功能不可用，需要配置 API
  - 创建 `INSTALL.md` 提供配置指南

- ✅ **Issue #11** - 安装验证问题
  - 创建 `INSTALL.md` 提供验证步骤

- ✅ **Issue #9** - README 克隆地址错误
  - 更新 `README.md` 中的克隆地址

- ✅ **Issue #10** - Windows dataclass 错误
  - **v2.0.0-rc.1 已修复**
  - 创建 `TROUBLESHOOT.md` 提供修复方案
  - 添加 `check_dataclass.py` 检查工具

### Technical Details

#### Architecture Changes
```
Previous (OpenAI Only):
  ScriptGenerator → OpenAI API

New (Multi-Provider):
  ScriptGenerator → LLMManager → Qwen/Kimi/GLM5
                           ↓
                     (Auto-switch on failure)
```

#### Version Management
```
Before: 1.5.0 / 2.0.0 / 3.0.0 (confusing)
After:  v2.0.0-rc.1 (unified)
Single Source: pyproject.toml
```

### Breaking Changes

None (backward compatible)

---

## [1.5.0] - 2025-11-01

### Added
- AI 视频解说功能
- AI 视频混剪功能
- AI 第一人称独白功能
- 剪映草稿导出

### Known Issues
- 版本混乱 (multiple versions in different files)
- 仅支持 OpenAI API
- 缺少单元测试

---

## [Unreleased]

### Planned for v2.0.0
- [ ] 集成测试覆盖率 >70%
- [ ] 性能优化
- [ ] 更新 CHANGELOG.md
- [ ] 发布说明

### Planned for v2.1.0
- [ ] 本地 LLM 支持 (Ollama)
- [ ] 本地 TTS (PyTorch TTS)
- [ ] 离线模式支持

### Planned for v2.2.0
- [ ] 更多语音风格 (10+ 种)
- [ ] 语音调节 (语速、音调)
- [ ] 多语言支持

### Planned for v2.3.0
- [ ] 更多字幕特效
- [ ] 动态文本动画
- [ ] 自动字幕编辑

### Planned for v3.0.0
- [ ] 多用户协作
- [ ] 云端同步
- [ ] 项目模板库
- [ ] 插件系统

---

## Version History

| Version | Date | Status |
|---------|------|--------|
| 3.0.0 | 2026-06-15 | 🗓️ 计划中 |
| 2.3.0 | 2026-05-10 | 🗓️ 计划中 |
| 2.2.0 | 2026-04-10 | 🗓️ 计划中 |
| 2.1.0 | 2026-03-10 | 🗓️ 计划中 |
| 2.0.0-rc.1 | 2026-02-14 | ✅ 发布 |
| 2.0.0 | 2026-02-20 | 🏃 开发中 |
| 1.5.0 | 2025-11-01 | 📜 历史版本 |

---

**当前版本**: v2.0.0-rc.1
**下个版本**: v2.0.0 正式版 (预计 2026-02-20)

---

## Contributing

欢迎贡献！请参考 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## License

MIT License
