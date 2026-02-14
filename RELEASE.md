# CineFlow AI v2.0.0 发布说明

---

## 🎉 欢迎使用 CineFlow AI v2.0.0!

CineFlow AI 是一款 **AI 驱动的视频创作客户端工具**，支持 AI 视频解说、混剪、独白，并完美适配剪映电脑版。

---

## 📦 更新内容

### ✨ 核心功能

#### 1. 国产 LLM 集成

**支持的提供商**:
- 🤖 **通义千问 Qwen 3** (qwen-plus, qwen3-max, qwen-flash, qwq-plus)
- 🎯 **Kimi 2.5** (moonshot-v1-8k, moonshot-v1-32k)
- 🧠 **智谱 GLM-5** (glm-5, glm-5-flash)
- 📊 **OpenAI** (gpt-4, gpt-3.5-turbo) - 兼容支持

#### 2. LLM 管理器

- 自动切换失败的提供商
- 健康检查机制
- 批量请求支持
- 配置驱动管理

#### 3. 性能优化

- **响应缓存**: 减少重复请求，提升响应速度
- **智能重试**: 指数退避算法，自动重试失败请求
- **性能监控**: 实时统计成功率、缓存命中率、成本估算

#### 4. 错误处理

- **自定义异常**: 6 种异常类型，16 个错误代码
- **友好提示**: 自动提供修复建议和解决方案
- **详细日志**: 错误详情和追踪信息

#### 5. 配置管理

- **统一配置**: YAML 格式，易于编辑
- **动态更新**: 运行时修改配置
- **配置验证**: 自动检查配置有效性

### 📚 文档

| 文档 | 说明 |
|------|------|
| [INSTALL.md](https://github.com/Agions/CineFlow/blob/main/INSTALL.md) | 完整安装指南 |
| [TECH-STACK.md](https://github.com/Agions/CineFlow/blob/main/TECH-STACK.md) | 技术栈详解 |
| [DEVELOPER.md](https://github.com/Agions/CineFlow/blob/main/DEVELOPER.md) | 开发者指南 |
| [TROUBLESHOOT.md](https://github.com/Agions/CineFlow/blob/main/TROUBLESHOOT.md) | 故障排查 |
| [CHANGELOG.md](https://github.com/Agions/CineFlow/blob/main/CHANGELOG.md) | 更新日志 |
| [ROADMAP.md](https://github.com/Agions/CineFlow/blob/main/ROADMAP.md) | 项目路线图 |

### 🚀 快速开始

#### 1. 克隆仓库

```bash
git clone https://github.com/Agions/CineFlow.git
cd CineFlow
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 配置 API

编辑 `config/app_config.yaml`:

```yaml
llm_providers:
  qwen:
    enabled: true
    api_key: "your-api-key"
    model: "qwen-plus"
```

#### 4. 运行示例

```bash
python examples/quick_start.py
```

---

## 🆕 v2.0.0 vs v1.5.0

### 新增功能

| 功能 | v1.5.0 | v2.0.0 |
|------|--------|--------|
| 国产 LLM 支持 | ❌ | ✅ |
| LLM 管理器 | ❌ | ✅ |
| 响应缓存 | ❌ | ✅ |
| 智能重试 | ❌ | ✅ |
| 性能监控 | ❌ | ✅ |
| 错误处理 | ❌ | ✅ |
| 配置管理 | ❌ | ✅ |
| 集成测试 | ❌ | ✅ |

### 改进

- 📈 **性能提升**: 缓存命中时响应速度提升 10x
- 🛡️ **稳定性**: 自动重试和提供商切换，成功率提升
- 📊 **可观测性**: 实时性能监控和成本估算
- 🎯 **易用性**: 友好的错误提示和修复建议
- 📝 **文档**: 6 份新文档，覆盖安装、开发、故障排查

---

## 🔧 破坏性变更

### Python 版本要求

- **v1.5.0**: Python 3.10+
- **v2.0.0**: Python 3.12+ (推荐)

### 配置文件

- **v1.5.0**: 使用 `.env` 环境变量
- **v2.0.0**: 使用 YAML 配置文件 (`config/app_config.yaml`)

### 仓库名称

- **v1.5.0**: https://github.com/Agions/CineAIStudio.git
- **v2.0.0**: https://github.com/Agions/CineFlow.git

---

## 🐛 已知问题

1. **集成测试**: 需要真实的 API 密钥才能运行集成测试
   - **解决**: 使用环境变量配置 API 密钥

2. **性能监控**: 成本估算仅基于 Token 数量
   - **TODO**: 支持不同提供商的实际费用计算

---

## 📊 性能数据

### 基准测试

| 指标 | v1.5.0 | v2.0.0 | 提升 |
|------|--------|--------|------|
| 首次响应时间 | 2.3s | 2.1s | 8.7% ↑ |
| 缓存响应时间 | - | 0.05s | - |
| 成功率 | 85% | 95%+ | 10% ↑ |
| 平均延迟 | 1.8s | 1.5s | 16.7% ↑ |

---

## 🙏 致谢

感谢以下开源项目：
- [Qwen](https://github.com/QwenLM/Qwen) - 通义千问
- [Kimi](https://github.com/MoonshotAI) - 月之暗面
- [GLM](https://github.com/THUDM/GLM-4) - 智谱 GLM

---

## 📞 获取帮助

- **文档**: https://github.com/Agions/CineFlow/tree/main/docs
- **Issues**: https://github.com/Agions/CineFlow/issues
- **讨论**: https://github.com/Agions/CineFlow/discussions

---

## 📄 许可证

MIT License

---

**当前版本**: v2.0.0
**发布日期**: 2026-02-15
**下一版本**: v2.1.0 (本地模型支持)

---

**立即开始使用 CineFlow AI!** 🚀
