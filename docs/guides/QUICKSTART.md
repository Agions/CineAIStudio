# ClipFlowCut AI 快速上手

## 环境要求

- Python 3.9+
- FFmpeg（必须）
- 可选：OpenAI API Key（用于 AI 画面分析和文案生成）

## 安装

```bash
# 克隆项目
git clone https://github.com/Agions/clip-flow-cut.git
cd clip-flow-cut

# 安装依赖
pip install -r requirements.txt

# macOS 安装 FFmpeg
brew install ffmpeg

# Windows 安装 FFmpeg
# 下载 https://ffmpeg.org/download.html 并添加到 PATH
```

## 配置（可选）

```bash
# 方式一：环境变量
export OPENAI_API_KEY="sk-xxx"

# 方式二：.env 文件
echo 'OPENAI_API_KEY=sk-xxx' > .env

# 方式三：编辑 config/llm.yaml
```

> 💡 没有 API Key 也能用！配音使用免费的 Edge TTS，文案可以手动输入。

## 运行

```bash
# 启动 GUI
python app/main.py

# 命令行快速演示
python examples/quick_start.py
```

## 使用流程

### 1. 选择模板

启动后在首页选择创作模板：
- 🎬 电影解说 — AI 分析画面 → 生成解说 → 配音
- 🎵 音乐混剪 — 多段素材 → 节拍匹配 → 自动转场
- 🎭 情感独白 — 画面情感分析 → 第一人称独白
- 📺 短剧切片 — 识别高能片段 → 切片 → 加字幕
- 🛍️ 产品推广 — 画面分析 → 卖点提取 → 推广文案

### 2. 导入视频

拖拽或选择视频文件，支持 mp4、mov、avi、mkv 等主流格式。

### 3. AI 分析

点击「分析」，AI 会：
1. 提取关键帧
2. 分析画面内容（需要 Vision API）
3. 识别情感氛围
4. 生成文案建议

### 4. 编辑文案

可以使用 AI 生成的文案，也可以手动编辑。

### 5. 配音

选择配音风格和声音，点击「生成配音」。

### 6. 导出

选择导出格式：
- **剪映** — 直接导入剪映电脑版继续编辑
- **Premiere** — Adobe Premiere Pro 项目
- **Final Cut** — FCPXML 格式
- **达芬奇** — DaVinci Resolve（FCPXML）
- **字幕** — SRT 或 ASS 格式

## LLM 配置

编辑 `config/llm.yaml` 配置 AI 模型：

```yaml
LLM:
  default_provider: qwen
  
  qwen:
    enabled: true
    api_key: ${QWEN_API_KEY}
    
  openai:
    enabled: true
    api_key: ${OPENAI_API_KEY}
    vision_model: gpt-4o
    
  gemini:
    enabled: true
    api_key: ${GEMINI_API_KEY}
```

支持的模型详见 [架构文档](../ARCHITECTURE.md)。

## 打包

```bash
# macOS
python build/build_app.py --dmg

# Windows
python build/build_app.py
```

## 常见问题

详见 [故障排除](TROUBLESHOOT.md)
