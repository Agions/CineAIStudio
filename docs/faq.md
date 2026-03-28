# 常见问题

## 安装问题

### Q: 安装依赖失败怎么办？

A: 确保您的 Python 版本 >= 3.9，并使用以下命令安装：

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Q: FFmpeg 找不到怎么办？

A: 确保 FFmpeg 已安装并加入系统 PATH：

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows (使用 winget)
winget install ffmpeg
```

### Q: PySide6 和 PyQt6 有什么区别？

A: 主要区别在于许可证：

| 框架 | 许可证 | 商业使用 |
|------|--------|----------|
| PyQt6 | GPL v3 | ❌ 需购买商业授权 |
| **PySide6** | **LGPL v3** | ✅ **免费商业使用** |

VideoForge 已迁移至 PySide6，您可以自由用于商业项目。

---

## AI 配置问题

### Q: 需要配置哪些 AI API？

A: **只需要一个 API Key 即可使用全部功能！** Edge TTS 配音完全免费。

| 提供商 | 用途 | 费用 |
|--------|------|------|
| Edge TTS | 配音 | ✅ 免费 |
| OpenAI | 文本/视觉/配音 | 付费 |
| Claude | 文本/视觉 | 付费 |
| Qwen (阿里云) | 文本/视觉 | 付费 |
| DeepSeek | 文本 | 付费 |

### Q: API Key 安全吗？

A: **非常安全！** VideoForge 采用企业级安全措施：

1. API 密钥存储在系统 Keychain (macOS Keychain / Windows Credential Manager)
2. 降级方案使用 AES-256 加密
3. PBKDF2 密钥派生 (480,000 次迭代)
4. 不存在任何硬编码密钥

### Q: API Key 如何获取？

A: 访问各 AI 提供商官网注册账号：

- OpenAI: https://platform.openai.com
- 阿里云 (Qwen): https://dashscope.console.aliyun.com
- Anthropic (Claude): https://www.anthropic.com
- DeepSeek: https://platform.deepseek.com

---

## 使用问题

### Q: 视频导出支持哪些格式？

A: 支持多平台全格式：

**视频格式:**
- MP4 (H.264) - 通用兼容性
- MP4 (H.265) - 更小体积

**字幕格式:**
- SRT - 通用字幕
- ASS - 高级特效字幕

**专业软件格式:**
- 剪映 Draft JSON
- Adobe Premiere Pro XML
- Apple Final Cut Pro FCPXML
- DaVinci Resolve EDL

### Q: 支持本地模型吗？

A: **支持！** 使用 Ollama 可以完全本地运行：

```bash
# 安装 Ollama
brew install ollama  # macOS
# 或从 ollama.com 下载 Windows 版

# 运行模型
ollama pull llama3.2
ollama pull qwen2.5

# 在 VideoForge 设置中选择 "本地" 提供商
```

### Q: 项目文件在哪里查看？

A: 默认位置：
- macOS: `~/VideoForge/Projects`
- Windows: `C:\Users\用户名\VideoForge\Projects`

### Q: 如何更新到最新版本？

```bash
cd VideoForge
git pull origin main
pip install -r requirements.txt --upgrade
```

---

## 性能问题

### Q: 处理速度慢怎么办？

A: 尝试以下优化：

1. **使用更快的模型**: GPT-4o 比 GPT-4 更快
2. **降低输出质量**: 减小输出分辨率
3. **使用 SSD**: 项目文件放在 SSD 上
4. **关闭其他程序**: 释放内存和 CPU

### Q: 内存不足怎么办？

A: 减少同时处理的任务数量，或关闭其他应用程序。

---

## 许可证问题

### Q: VideoForge 可以商业使用吗？

A: **可以！** VideoForge 使用 MIT 许可证，PySide6 使用 LGPL 许可证，均允许商业使用。

唯一需要注意的是 FFmpeg (LGPL)，如果需要闭源定制，请联系 FFmpeg 获得商业授权。

---

## 获取帮助

- [GitHub Issues](https://github.com/Agions/VideoForge/issues)
- [问题反馈](https://github.com/Agions/VideoForge/discussions)
