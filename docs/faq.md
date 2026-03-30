# 常见问题

## 安装问题

### Q: 安装失败怎么办？

**A:** 尝试以下步骤：

1. 确认系统满足 [最低要求](/guide/installation#系统要求)
2. 关闭杀毒软件后重试
3. 以管理员权限运行安装程序
4. 查看安装日志获取详细错误

### Q: macOS 提示"无法打开"？

**A:** 
1. 系统偏好设置 → 安全性与隐私 → 通用
2. 点击"仍要打开"

### Q: Linux 缺少依赖？

**A:** 
```bash
sudo apt install python3-pip ffmpeg libgl1 libglib2.0-0
```

## AI 功能问题

### Q: AI 功能不工作？

**A:** 检查以下内容：

1. **API Key 配置**
   - 设置 → AI 配置 → 检查 API Key 是否正确
   
2. **网络连接**
   ```bash
   curl https://api.openai.com/v1/models
   ```
   
3. **余额检查**
   - 确认 API 账户有足够余额

4. **查看日志**
   ```bash
   tail -f ~/.videoforge/logs/app.log
   ```

### Q: AI 响应很慢？

**A:** 优化建议：

- 使用更快的模型（如 GPT-4o-mini）
- 启用请求缓存
- 检查网络延迟
- 使用本地模型（Ollama）

### Q: 怎么节省 API 费用？

**A:** 技巧：

- 启用结果缓存
- 使用更小的模型处理简单任务
- 本地部署 Ollama + Llama3

## 视频处理问题

### Q: FFmpeg 报错？

**A:** 
```bash
# 确认 FFmpeg 已安装
ffmpeg -version

# 如果未安装
brew install ffmpeg  # macOS
sudo apt install ffmpeg  # Ubuntu
```

### Q: 视频导出失败？

**A:** 
1. 检查磁盘空间是否充足
2. 确认输出路径有写入权限
3. 尝试降低输出质量
4. 检查视频文件是否损坏

### Q: 剪辑后音画不同步？

**A:** 
1. 重新导入素材
2. 检查原始素材是否有音画同步问题
3. 在设置中调整同步偏移

## 性能问题

### Q: 内存占用过高？

**A:** 
1. 关闭不必要的后台程序
2. 降低预览质量
3. 使用代理编辑
4. 增加系统内存

### Q: GPU 不被使用？

**A:** 
1. 确认 NVIDIA 驱动已安装
2. 在设置中启用 GPU 加速
3. 检查 CUDA 是否可用：
   ```bash
   nvidia-smi
   ```

## 其他问题

### Q: 如何导出项目？

**A:** 
- **剪映格式**: 文件 → 导出 → 剪映草稿
- **Adobe PR**: 文件 → 导出 → Premiere Pro
- **FCP**: 文件 → 导出 → Final Cut Pro

### Q: 快捷键不生效？

**A:** 
1. 确认没有其他软件占用快捷键
2. 重置快捷键为默认
3. 重启应用

### Q: 崩溃或卡死怎么办？

**A:** 
1. 查看错误日志
2. 提交 [Issue](https://github.com/Agions/VideoForge/issues)
3. 提供复现步骤

## 获取帮助

| 渠道 | 链接 |
|------|------|
| GitHub Issues | [报告 Bug](https://github.com/Agions/VideoForge/issues) |
| 讨论区 | [GitHub Discussions](https://github.com/Agions/VideoForge/discussions) |
| 文档 | [docs.videoforge.ai](https://docs.videoforge.ai) |
