# 配置参考

VideoForge 支持灵活的配置文件和环境变量配置。

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
  name: VideoForge
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
  output_dir: ~/Videos/VideoForge
  
  # 导出质量预设
  quality_preset: high
  
  # 包含字幕
  include_subtitles: true

security:
  # 加密存储 API Key
  encrypt_keys: true
  
  # 允许远程模型
  allow_remote: true
```

## 环境变量

### AI 相关

| 变量 | 说明 | 示例 |
|------|------|------|
| `OPENAI_API_KEY` | OpenAI API Key | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API Key | `sk-ant-...` |
| `GOOGLE_API_KEY` | Google API Key | `...` |
| `DASHSCOPE_API_KEY` | 阿里云 API Key | `...` |
| `ZHIPU_API_KEY` | 智谱 API Key | `...` |
| `MOONSHOT_API_KEY` | Moonshot API Key | `...` |

### 应用配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `VIDEOFORGE_HOME` | 配置目录 | `~/.videoforge` |
| `VIDEOFORGE_LANG` | 语言 | `zh-CN` |
| `VIDEOFORGE_THEME` | 主题 | `system` |
| `VIDEOFORGE_DEBUG` | 调试模式 | `false` |

## 命令行参数

```bash
# 启动应用
videoforge

# 指定配置目录
videoforge --home /path/to/config

# 调试模式
videoforge --debug

# 禁用 GPU
videoforge --no-gpu

# 指定端口（Web 模式）
videoforge --port 8080
```

## 高级配置

### 代理设置

```yaml
network:
  proxy:
    enabled: true
    http: http://proxy:8080
    https: https://proxy:8080
    # 跳过代理的域名
    no_proxy:
      - localhost
      - 127.0.0.1
```

### 缓存设置

```yaml
cache:
  # 启用缓存
  enabled: true
  
  # 缓存目录
  cache_dir: ~/.videoforge/cache
  
  # 最大缓存大小 (MB)
  max_size: 1024
  
  # 缓存过期时间 (天)
  expire_days: 7
```

### 日志配置

```yaml
logging:
  level: INFO  # DEBUG / INFO / WARNING / ERROR
  
  # 日志文件
  file: ~/.videoforge/logs/app.log
  
  # 日志轮转
  rotation:
    max_bytes: 10485760  # 10MB
    backup_count: 5
```

## 故障排除

### 配置文件不生效

1. 检查配置文件路径
2. 验证 YAML 语法
3. 使用 `--debug` 查看加载日志

### 环境变量不生效

确保在启动应用前设置环境变量，或创建 `.env` 文件：

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```
