# ClipFlowCut 组件化设计指南

## 概述

ClipFlowCut UI 采用模块化、组件化设计，确保代码可维护、可扩展。

---

## 目录结构

```
app/ui/components/
├── __init__.py           # 统一导出
├── design_system.py       # 设计系统基础
├── containers/           # 容器组件
│   └── __init__.py
├── buttons/             # 按钮组件
│   └── __init__.py
├── labels/              # 标签组件
│   └── __init__.py
├── inputs/              # 输入组件
│   └── __init__.py
└── layout/              # 布局组件
    └── __init__.py
```

---

## 组件清单

### 容器组件 (containers)

| 组件 | 说明 |
|------|------|
| `MacCard` | 基础卡片容器 |
| `MacElevatedCard` | 带阴影的卡片 |
| `MacSection` | 带标题的区域 |

### 按钮组件 (buttons)

| 组件 | 说明 |
|------|------|
| `MacButton` | 基础按钮 |
| `MacPrimaryButton` | 主要按钮 |
| `MacSecondaryButton` | 次要按钮 |
| `MacDangerButton` | 危险操作按钮 |
| `MacIconButton` | 图标按钮 |
| `MacButtonGroup` | 按钮组 |

### 标签组件 (labels)

| 组件 | 说明 |
|------|------|
| `MacLabel` | 基础标签 |
| `MacTitleLabel` | 标题标签 |
| `MacBadge` | 徽章 |
| `MacStatLabel` | 统计标签 |

### 输入组件 (inputs)

| 组件 | 说明 |
|------|------|
| `MacSearchBox` | 搜索框 |

### 布局组件 (layout)

| 组件 | 说明 |
|------|------|
| `MacScrollArea` | 滚动区域 |
| `MacGrid` | 网格布局 |
| `MacPageToolbar` | 页面工具栏 |
| `MacEmptyState` | 空状态显示 |

---

## 使用示例

```python
from app.ui.components import (
    MacCard, MacPrimaryButton, MacTitleLabel,
    MacGrid, MacEmptyState
)

# 创建卡片
card = MacCard()
card.set_interactive(True)

# 创建按钮
btn = MacPrimaryButton("点击我")

# 创建网格
grid = MacGrid(columns=3)
grid.add_widget(MacCard())

# 空状态
empty = MacEmptyState(
    icon="📭",
    title="暂无内容",
    description="请先导入视频素材"
)
```

---

## 设计原则

1. **单一职责** - 每个组件只做一件事
2. **可复用** - 通用组件放在 components/ 目录
3. **可组合** - 组件之间通过组合实现复杂功能
4. **样式分离** - 样式通过 QSS 类名管理

---

## 样式规范

组件使用 `class` 属性来应用样式：

```python
self.setProperty("class", "card")
self.setProperty("class", "primary")
```

对应的 QSS：

```css
QFrame[class="card"] {
    background-color: #2D2D2D;
    border-radius: 12px;
}

QPushButton[class="primary"] {
    background-color: #2196F3;
}
```
