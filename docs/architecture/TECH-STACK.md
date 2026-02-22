# CineFlow AI 技术栈详解

> 回答 GitHub Issue #13: 特效字幕使用的技术栈

---

## 📐 技术栈概述

### 字幕渲染技术

#### 1. **PyQt6 QPainter + QStaticText**

**主要用途**:
- 静态字幕显示
- 实时字幕预览
- UI 内嵌字幕

**示例代码**:

```python
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QRectF

def draw_caption(self, painter, text, position):
    """绘制字幕"""
    # 设置字体
    font = QFont("Microsoft YaHei", 32)
    painter.setFont(font)

    # 设置文字颜色（白色 + 描边）
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(255, 255, 255))

    # 绘制描边效果（黑色外边框）
    painter.setPen(QColor(0, 0, 0))
    for offset in range(-2, 3):
        painter.drawText(
            position + offset,
            QRectF(0, 0, 1920, 100),
            Qt.AlignmentFlag.AlignHCenter,
            text
        )

    # 绘制主文字
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawText(position, QRectF(0, 0, 1920, 100), Qt.AlignmentFlag.AlignHCenter, text)
```

**优点**:
- ✅ 原生 PyQt6 支持
- ✅ 实时渲染流畅
- ✅ 文本清晰度高
- ✅ 支持自定义字体

---

#### 2. **OpenCV + PIL**

**主要用途**:
- 视频字幕渲染
- 字幕特效（发光、阴影、渐变）
- 高质量导出

**示例代码**:

```python
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def render_caption_to_video(frame, text, position):
    """渲染字幕到视频帧"""
    # 转换为 PIL Image
    pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_image)

    # 加载字体
    font = ImageFont.truetype("fonts/simhei.ttf", 48)

    # 绘制阴影
    draw.text(
        (position[0] + 3, position[1] + 3),
        text,
        font=font,
        fill=(0, 0, 0, 128)  # 半透明黑色
    )

    # 绘制发光效果
    for i in range(5, 0, -1):
        draw.text(
            (position[0] - i, position[1]),
            text,
            font=font,
            fill=(0, 100, 255, 30)  # 蓝色发光
        )

    # 绘制主文字（白色）
    draw.text(
        position,
        text,
        font=font,
        fill=(255, 255, 255)
    )

    # 转换回 OpenCV 格式
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
```

**优点**:
- ✅ 支持复杂特效
- ✅ 高质量渲染
- ✅ 易于集成到视频处理管线

---

#### 3. **FFmpeg 字幕烧录**

**主要用途**:
- 批量视频处理
- 硬烧字幕到视频
- 字幕格式转换

**示例代码**:

```python
import ffmpeg

def burn_subtitles(video_path, subtitle_path, output_path):
    """使用 FFmpeg 烧录字幕"""
    (
        ffmpeg
        .input(video_path)
        .output(
            output_path,
            vf=f"subtitles={subtitle_path}:force_style='FontName=Microsoft YaHei,FontSize=24,PrimaryColour=&HFFFFFF'",
            acodec="copy"
        )
        .run()
    )
```

**优点**:
- ✅ 批量处理效率高
- ✅ 支持所有字幕格式（SRT, ASS, VTT）
- ✅ GPU 加速支持

---

## ✨ 字幕特效实现

### 1. 描边效果

```python
def draw_stroked_text(painter, text, x, y, stroke_color=QColor(0, 0, 0), text_color=QColor(255, 255, 255)):
    """绘制描边文字"""
    # 绘制 8 个方向的描边
    for dx, dy in [(-1, -1), (0, -1), (1, -1),
                   (-1, 0),          (1, 0),
                   (-1, 1),  (0, 1),  (1, 1)]:
        painter.setPen(stroke_color)
        painter.drawText(x + dx, y + dy, text)

    # 绘制主文字
    painter.setPen(text_color)
    painter.drawText(x, y, text)
```

### 2. 发光效果

```python
def draw_glowing_text(painter, text, x, y, glow_color=QColor(0, 100, 255), radius=10):
    """绘制发光文字"""
    for i in range(radius, 0, -1):
        # 颜色逐渐透明
        alpha = int(255 * (i / radius) * 0.3)
        color = QColor(glow_color)
        color.setAlpha(alpha)
        painter.setPen(color)
        painter.drawText(x - i, y - i, text)
        painter.drawText(x + i, y + i, text)

    # 绘制主文字
    painter.setPen(QColor(255, 255, 255))
    painter.drawText(x, y, text)
```

### 3. 渐变文字

```python
def draw_gradient_text(painter, text, x, y):
    """绘制渐变文字"""
    from PyQt6.QtGui import QLinearGradient, QTextDocument

    # 创建渐变
    gradient = QLinearGradient(0, 0, 500, 0)
    gradient.setColorAt(0, QColor(255, 0, 0))    # 红色
    gradient.setColorAt(0.5, QColor(0, 255, 0))  # 绿色
    gradient.setColorAt(1, QColor(0, 0, 255))    # 蓝色

    # 创建文本文档
    doc = QTextDocument()
    doc.setPlainText(text)

    # 绘制
    painter.setPen(gradient)
    painter.drawText(x, y, text)
```

---

## 🎬 字幕格式支持

### 支持的格式

| 格式 | 扩展名 | 用途 |
|------|--------|------|
| **SRT** | .srt | 最常用，兼容性好 |
| **ASS/SSA** | .ass | 高级特效字幕 |
| **VTT** | .vtt | Web 字幕 |
| **LRC** | .lrc | 歌词字幕 |
| **TXT** | .txt | 简单文本 |

### 字幕解析示例

```python
def parse_srt_file(srt_path):
    """解析 SRT 字幕文件"""
    captions = []

    with open(srt_path, 'r', encoding='utf-8') as f:
        blocks = f.read().split('\n\n')

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            # 时间轴: 00:00:00,000 --> 00:00:05,000
            timeline = lines[1]
            text = '\n'.join(lines[2:])

            captions.append({
                'timeline': timeline,
                'text': text
            })

    return captions
```

---

## 🔧 实际应用场景

### 场景 1: AI 视频解说

```python
def generate_commentary_with_captions():
    """生成解说视频并添加字幕"""
    # 1. 生成文案
    generator = ScriptGenerator(use_llm_manager=True)
    script = generator.generate_commentary("主题...", duration=60)

    # 2. 拆分字幕
    captions = generator.split_to_captions(script, max_chars=20)

    # 3. 渲染到视频
    for caption in captions:
        frame = get_video_frame(caption['start'])
        render_caption_to_video(frame, caption['text'], position=(100, 1000))
        write_frame(frame)
```

### 场景 2: 自动生成字幕

```python
def auto_generate_captions(audio_path):
    """从音频生成字幕"""
    # 1. 语音识别 (使用 API)
    transcript = transcribe_audio(audio_path)

    # 2. 生成 SRT 格式
    srt_content = convert_to_srt(transcript)

    # 3. 渲染到视频
    burn_subtitles(video_path, srt_path, output_path)
```

---

## 📦 依赖包

```python
# requirements.txt
PyQt6>=6.9.0              # QPainter 绘制
opencv-python>=4.8.1      # OpenCV 渲染
pillow>=10.1.0            # PIL 文字处理
ffmpeg-python==0.2.0      # FFmpeg 烧录
```

---

## 💡 总结

CineFlow AI 使用**多层技术栈**实现字幕和特效：

1. **PyQt6 QPainter** - 实时预览和 UI 集成
2. **OpenCV + PIL** - 高质量视频渲染和特效
3. **FFmpeg** - 批量处理和格式转换

这种多层架构确保了：
- ⚡ 实时预览流畅
- 🎨 特效丰富多样
- 📦 批量处理高效

---

**最后更新**: 2026-02-14
**版本**: v2.0.0-rc.1
