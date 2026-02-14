# CineFlow v3.0 现代化 UI 升级文档

## 概述

CineFlow v3.0 引入了全新的现代化设计系统，提供专业、优雅、流畅的用户界面体验。

## 设计理念

### 1. 玻璃拟态 (Glassmorphism)
- 半透明背景 + 模糊效果
- 渐变边框
- 层次感强

### 2. 渐变美学
- 科技蓝 (#00D4FF) 到 渐变紫 (#8B5CF6)
- 主色调清晰且富有创意
- 避免过度饱和

### 3. 深色优先
- 深蓝灰背景 (#0A0E14, #111827)
- 高对比度保证可读性
- 重点内容用亮色突出

### 4. 流畅动画
- 悬停、点击有明确反馈
- 过渡效果自然流畅
- 加载状态清晰可见

## 组件库

### 核心组件

#### ModernCard - 玻璃拟态卡片
```python
from app.ui.common.widgets.modern_cards import ModernCard

card = ModernCard(
    title="卡片标题",
    clickable=True,
    padding=24
)
card.clicked.connect(on_card_clicked)
```

#### StatCard - 统计卡片
```python
from app.ui.common.widgets.modern_cards import StatCard

card = StatCard(
    title="项目数",
    value="128",
    subtitle="+12 本周"
)
```

#### FeatureCard - 功能卡片
```python
from app.ui.common.widgets.modern_cards import FeatureCard

card = FeatureCard(
    title="AI 生成",
    description="使用 AI 自动创建视频",
    icon="🤖"
)
```

#### ModernButton - 现代按钮
```python
from app.ui.common.widgets.modern_buttons import ModernButton

# 主按钮
btn = ModernButton("开始", style="primary", size="medium")

# 危险按钮
danger_btn = ModernButton("删除", style="danger")

# 图标按钮
icon_btn = IconButton("❤️", tooltip="收藏", size=32)
```

#### ModernNavigationBar - 导航栏
```python
from app.ui.common.widgets.modern_navigation import ModernNavigationBar

nav = ModernNavigationBar(
    width=240,
    collapsible=True
)
nav.nav_item_clicked.connect(on_nav_changed)
```

## 快速开始

### 1. 使用现代主窗口

```python
from app.ui.main.modern_main_window import ModernMainWindow

# 创建并显示窗口
window = ModernMainWindow()
window.show()
```

### 2. 创建自定义页面

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout

class MyPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 添加组件
        # ...
```

### 3. 应用主题样式

```python
import os
from PyQt6.QtWidgets import QApplication

# 获取样式表路径
qss_path = "resources/styles/modern_theme.qss"

# 读取并应用
with open(qss_path, "r", encoding="utf-8") as f:
    stylesheet = f.read()
    QApplication.instance().setStyleSheet(stylesheet)
```

## 设计系统变量

### 颜色系统

| 变量名 | 值 | 用途 |
|--------|-----|------|
| `--color-primary` | #00D4FF | 主色调 |
| `--color-secondary` | #8B5CF6 | 辅助色调 |
| `--bg-primary` | #0A0E14 | 主背景 |
| `--bg-secondary` | #111827 | 次背景 |
| `--bg-elevated` | #1E293B | 悬浮卡片 |
| `--text-primary` | #F9FAFB | 主文本 |
| `--text-secondary` | #D1D5DB | 次文本 |

### 间距系统

| 变量名 | 值 | 用途 |
|--------|-----|------|
| `--spacing-xs` | 4px | 超小间距 |
| `--spacing-sm` | 8px | 小间距 |
| `--spacing-md` | 16px | 中间距 |
| `--spacing-lg` | 24px | 大间距 |
| `--spacing-xl` | 32px | 超大间距 |

### 圆角系统

| 变量名 | 值 | 用途 |
|--------|-----|------|
| `--radius-sm` | 4px | 小圆角 |
| `--radius-md` | 8px | 中圆角 |
| `--radius-lg` | 12px | 大圆角 |
| `--radius-xl` | 16px | 超大圆角 |

## 样式迁移指南

### 从旧 UI 迁移

#### 1. 按钮样式迁移

**旧样式:**
```python
btn = QPushButton("确定")
btn.setStyleSheet("""
    QPushButton {
        background: #2196F3;
        border-radius: 4px;
    }
""")
```

**新样式:**
```python
btn = ModernButton("确定", style="primary", size="medium")
```

#### 2. 卡片样式迁移

**旧样式:**
```python
widget = QWidget()
widget.setStyleSheet("""
    background: #2D2D2D;
    border: 1px solid #404040;
    border-radius: 4px;
    padding: 16px;
""")
```

**新样式:**
```python
card = ModernCard(title="标题", padding=20)
card.add_widget(content_widget)
```

#### 3. 导航栏迁移

**旧样式:**
```python
# 需要手写布局和样式
```

**新样式:**
```python
nav = ModernNavigationBar(
    items=[...],
    width=240,
    collapsible=True
)
nav.nav_item_clicked.connect(handler)
```

## 最佳实践

### 1. 组件组合

```python
from PyQt6.QtWidgets import QVBoxLayout

# 组合多个卡片
container = QWidget()
layout = QVBoxLayout()
layout.setSpacing(16)

layout.addWidget(StatCard("用户", "1,024"))
layout.addWidget(FeatureCard("功能", "描述"))

container.setLayout(layout)
```

### 2. 响应式布局

```python
from PyQt6.QtWidgets import QGridLayout

# 使用网格布局自适应
grid = CardGrid(columns=2, spacing=16)
grid.add_card(card1)
grid.add_card(card2)
grid.add_card(card3)
grid.add_card(card4)
```

### 3. 状态管理

```python
class MyPage(QWidget):
    def __init__(self):
        super().__init__()
        self.state = {
            "loading": False,
            "data": None,
        }
        self._setup_ui()

    def refresh_data(self):
        self.state["loading"] = True
        self._update_ui()

        # 异步加载数据
        # ...

        self.state["loading"] = False
        self.state["data"] = data
        self._update_ui()
```

## 性能优化

### 1. 样式表优化
- 使用类名选择器 (`QWidget[class="card"]`)
- 避免过度使用 ID 选择器
- 合并相似样式规则

### 2. 组件复用
- 创建自定义组件
- 避免重复创建相同组件
- 使用对象池模式

### 3. 异步加载
- 使用 QThread 进行耗时操作
- 显示加载状态
- 避免阻塞主线程

## 故障排查

### 样式不生效
1. 确认 QSS 路径正确
2. 检查样式表语法
3. 清除 PyQt 缓存

### 组件显示异常
1. 检查父容器布局
2. 确认组件可见性
3. 验证尺寸设置

### 性能问题
1. 减少不必要的样式重绘
2. 优化布局层级
3. 使用异步加载

## 未来计划

- [ ] 浅色主题支持
- [ ] 自定义主题编辑器
- [ ] 动画效果增强
- [ ] 无障碍支持
- [ ] 国际化支持

## 资源

- 设计系统: `app/ui/theme/design_system.py`
- 样式表: `resources/styles/modern_theme.qss`
- 组件库: `app/ui/common/widgets/`
- 示例代码: `examples/`

## 反馈

如有问题或建议，请提交 Issue 或 Pull Request。
