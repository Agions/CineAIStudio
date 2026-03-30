# 常见问题

## 安装问题

### Q: 安装失败怎么办？

**A:** 尝试以下步骤：

1. 确认系统满足最低要求
2. 关闭杀毒软件后重试
3. 以管理员权限运行安装程序

### Q: macOS 提示"无法打开"？

**A:** 
1. 系统偏好设置 → 安全性与隐私 → 通用
2. 点击"仍要打开"

## AI 功能问题

### Q: AI 功能不工作？

**A:** 检查以下内容：

1. **API Key 配置** - 设置 → AI 配置 → 检查 API Key 是否正确
2. **网络连接** - 确认网络连接正常
3. **余额检查** - 确认 API 账户有足够余额

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

## 获取帮助

| 渠道 | 链接 |
|------|------|
| GitHub Issues | [报告 Bug](https://github.com/Agions/VideoForge/issues) |
