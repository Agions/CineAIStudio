---
title: 配置参考
description: Narrafiilm 配置文件详解和环境变量参考。
---

# 配置参考

Narrafiilm 支持灵活的配置文件和环境变量配置。

## 配置文件

### 目录结构

```
~/.videoforge/
├── config.yaml          # 主配置文件
├── providers/           # AI 提供商配置
│   ├── openai.yaml
│   ├── claude.yaml
│   └── ...
├── projects/            # 项目文件
└── logs/                # 日志文件
```

### 主配置文件

```yaml
# ~/.videoforge/config.yaml

app:
  name: Narrafiilm
  version: "1.0.0"
  language: zh-CN
  
  # UI 主题: light / dark / system
  theme: system
  
  # 自动保存间隔（秒）
  auto_save_interval: 60

ai:
  # 默认提供商
  default_provider: openai
  
  # 默认模型
  default_model: gpt-5.4
  
  # 请求超时（秒）
  timeout: 60
  
  # 最大重试次数
  max_retries: 3
  
  # 速率限制 (请求/分钟)
  rate_limit: 60

video:
  # 默认导出格式
  default_format: mp4
  
  # 默认视频编码
  default_codec: h264
  
  # 临时文件目录
  temp_dir: /tmp/videoforge
  
  # FFmpeg 路径
  ffmpeg_path: ffmpeg

export:
  # 默认导出目录
  output_dir: ~/Videos/Narrafiilm
  
  # 导出质量预设
  quality_preset: high
  
  # 包含字幕
  include_subtitles: true
```

## 环境变量

### AI 相关

| 变量 | 说明 | 示例 |
|------|------|------|
| `OPENAI_API_KEY` | OpenAI API Key | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API Key | `sk-ant-...` |
| `GOOGLE_API_KEY` | Google API Key | `...` |

## 故障排除

### 配置文件不生效

1. 检查配置文件路径
2. 验证 YAML 语法
3. 使用 `--debug` 查看加载日志
