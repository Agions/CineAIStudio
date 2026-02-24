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

# Windows
# 下载 ffmpeg 并将 bin 目录加入 PATH
```

## AI 配置问题

### Q: 需要配置哪些 AI API？

A: ClipFlowCut 支持多种 AI 提供商：

| 提供商 | 用途 | 必填 |
|--------|------|------|
| OpenAI | 文本/视觉/配音 | 可选 |
| Claude | 文本/视觉 | 可选 |
| Qwen (阿里云) | 文本/视觉 | 可选 |
| Edge TTS | 配音 | 推荐 |

### Q: API Key 如何获取？

A: 访问各 AI 提供商官网注册账号：

- OpenAI: https://platform.openai.com
- 阿里云: https://dashscope.console.aliyun.com
- Anthropic: https://www.anthropic.com

## 使用问题

### Q: 视频导出支持哪些格式？

A: 支持：
- MP4 (H.264/H.265)
- 剪映 Draft JSON
- Adobe Premiere XML
- Apple Final Cut FCPXML
- DaVinci Resolve
- SRT/ASS 字幕

### Q: 项目文件在哪里查看？

A: 默认位置：
- macOS: `~/ClipFlowCut/Projects`
- Windows: `C:\Users\用户名\ClipFlowCut\Projects`

### Q: 如何更新到最新版本？

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

## 性能问题

### Q: 处理速度慢怎么办？

A: 尝试以下优化：

1. 使用更快的 AI 模型
2. 降低输出质量以提高速度
3. 使用 SSD 存储项目文件
4. 关闭其他占用资源的程序

### Q: 内存不足怎么办？

A: 减少同时处理的任务数量，或关闭其他应用程序。

## 获取帮助

- [GitHub Issues](https://github.com/Agions/clip-flow-cut/issues)
- [问题反馈](https://github.com/Agions/clip-flow-cut/discussions)
