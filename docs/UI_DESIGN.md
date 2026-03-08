# ClipFlowCut UI 设计规范

> 基于视频编辑软件最佳实践的设计系统

---

## 1. 设计原则

### 1.1 核心原则
- **简洁高效**: 减少视觉噪音，聚焦内容创作
- **一致可预期**: 相同元素保持一致的外观和行为
- **快速触达**: 常用功能一步到达
- **层级分明**: 重要信息优先，次要信息折叠

### 1.2 布局原则
- 左上角: Logo + 应用名称
- 左侧: 导航栏 (可折叠)
- 顶部: 页面标题 + 操作按钮
- 中央: 主内容区 (卡片式)
- 底部: 状态栏 (精简)

---

## 2. 色彩系统

### 2.1 深色主题 (默认)

```css
:root {
  /* 主色调 - 渐变紫蓝 */
  --primary: #6366F1;
  --primary-light: #818CF8;
  --primary-dark: #4F46E5;
  
  /* 强调色 */
  --accent: #06B6D4;
  --accent-light: #22D3EE;
  
  /* 功能色 */
  --success: #10B981;
  --warning: #F59E0B;
  --error: #EF4444;
  --info: #3B82F6;
  
  /* 背景层次 (从深到浅) */
  --bg-deepest: #0A0A0F;    /* 最深 - 窗口背景 */
  --bg-deep: #12121A;         /* 深 - 侧边栏 */
  --bg-surface: #1A1A24;     /* 表面 - 卡片背景 */
  --bg-elevated: #22222E;    /* 悬浮 - 弹窗/下拉 */
  --bg-hover: #2A2A38;       /* 悬停 */
  --bg-active: #363648;      /* 激活 */
  
  /* 文字颜色 */
  --text-primary: #FFFFFF;
  --text-secondary: #A1A1AA;
  --text-tertiary: #71717A;
  --text-disabled: #52525B;
  
  /* 边框 */
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-default: rgba(255, 255, 255, 0.1);
  --border-strong: rgba(255, 255, 255, 0.15);
  
  /* 圆角 */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-xl: 20px;
  
  /* 间距 */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
}
```

### 2.2 浅色主题

```css
:root {
  --bg-deepest: #F5F5F7;
  --bg-deep: #EAEAEC;
  --bg-surface: #FFFFFF;
  --bg-elevated: #F8F8F9;
  --bg-hover: #E8E8EC;
  --bg-active: #DEDEE2;
  
  --text-primary: #1D1D1F;
  --text-secondary: #6E6E73;
  --text-tertiary: #AEAEB2;
  
  --border-subtle: rgba(0, 0, 0, 0.06);
  --border-default: rgba(0, 0, 0, 0.1);
  --border-strong: rgba(0, 0, 0, 0.15);
}
```

---

## 3. 字体系统

```css
/* 字体家族 */
--font-family: "SF Pro Display", "Inter", "PingFang SC", "Microsoft YaHei", -apple-system, sans-serif;
--font-mono: "SF Mono", "JetBrains Mono", "Fira Code", monospace;

/* 字号层级 */
--text-xs: 11px;    /* 标签/徽章 */
--text-sm: 12px;    /* 次要文字 */
--text-base: 14px;  /* 正文 */
--text-lg: 16px;    /* 强调文字 */
--text-xl: 18px;    /* 页面标题 */
--text-2xl: 24px;   /* 章节标题 */
--text-3xl: 32px;   /* 页面主标题 */

/* 字重 */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;

/* 行高 */
--leading-tight: 1.2;
--leading-normal: 1.5;
--leading-relaxed: 1.75;
```

---

## 4. 组件规范

### 4.1 按钮

```css
/* 主要按钮 */
.btn-primary {
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: white;
  border: none;
  border-radius: var(--radius-md);
  padding: 10px 20px;
  font-size: var(--text-base);
  font-weight: var(--font-medium);
  transition: all 0.2s ease;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

/* 次要按钮 */
.btn-secondary {
  background: var(--bg-elevated);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 10px 20px;
}

.btn-secondary:hover {
  background: var(--bg-hover);
  border-color: var(--border-strong);
}

/* 文字按钮 */
.btn-text {
  background: transparent;
  color: var(--primary);
  border: none;
  padding: 8px 16px;
}

.btn-text:hover {
  background: rgba(99, 102, 241, 0.1);
}
```

### 4.2 输入框

```css
.input {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 10px 14px;
  color: var(--text-primary);
  font-size: var(--text-base);
  transition: all 0.2s ease;
}

.input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
  outline: none;
}

.input::placeholder {
  color: var(--text-tertiary);
}
```

### 4.3 卡片

```css
.card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  transition: all 0.2s ease;
}

.card:hover {
  border-color: var(--border-default);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

/* 玻璃拟态卡片 */
.card-glass {
  background: rgba(26, 26, 36, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-lg);
}
```

### 4.4 导航栏

```css
/* 导航按钮 */
.nav-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.nav-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.nav-btn.active {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.15));
  color: var(--text-primary);
  font-weight: var(--font-medium);
}

.nav-btn .icon {
  font-size: 20px;
  width: 24px;
  text-align: center;
}
```

---

## 5. 间距系统

### 5.1 组件间距

| 元素 | 间距 |
|------|------|
| 页面边距 | 24px |
| 卡片间距 | 16px |
| 卡片内边距 | 20px |
| 按钮组间距 | 12px |
| 表单项间距 | 16px |
| 列表项间距 | 8px |

### 5.2 响应式断点

```css
/* 断点 */
--breakpoint-sm: 640px;   /* 手机横屏 */
--breakpoint-md: 768px;    /* 平板 */
--breakpoint-lg: 1024px;   /* 小笔记本 */
--breakpoint-xl: 1280px;   /* 桌面 */
--breakpoint-2xl: 1536px;  /* 大屏 */
```

---

## 6. 动效系统

### 6.1 过渡时间

```css
--transition-fast: 0.15s ease;
--transition-normal: 0.25s ease;
--transition-slow: 0.35s ease;
```

### 6.2 常用动画

```css
/* 淡入 */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 上浮 */
@keyframes slideUp {
  from { 
    opacity: 0;
    transform: translateY(10px);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}

/* 缩放 */
@keyframes scaleIn {
  from { 
    opacity: 0;
    transform: scale(0.95);
  }
  to { 
    opacity: 1;
    transform: scale(1);
  }
}
```

---

## 7. 页面布局规范

### 7.1 首页布局

```
┌─────────────────────────────────────────────────┐
│  [Logo] ClipFlowCut              [新建] [导入]  │  ← 顶部标题栏 (56px)
├────────┬────────────────────────────────────────┤
│        │ ┌────────────────────────────────────┐ │
│ 🏠 首页 │ │        欢迎使用 ClipFlowCut        │ │
│        │ │                                    │ │
│ 📁 项目 │ │    🎬 AI 视频创作工具              │ │
│        │ │                                    │ │
│ 🎬 剪辑 │ │    快速开始 →                     │ │
│        │ └────────────────────────────────────┘ │
│ 🤖 AI  │                                        │
│        │ ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│ 💬 对话 │ │ 最近项目  │ │ AI 创作  │ │ 快捷入口 │ │
│        │ └──────────┘ └──────────┘ └─────────┘ │
│ ────── │                                        │
│ ⚙️ 设置 │                                        │
├────────┴────────────────────────────────────────┤
│  🟢 就绪    │ AI: 可用    │ 14:30            │  ← 状态栏 (28px)
└─────────────────────────────────────────────────┘
```

### 7.2 项目页布局

```
┌─────────────────────────────────────────────────┐
│  项目管理                        [新建] [导入]   │
├────────┬────────────────────────────────────────┤
│        │ [🔍 搜索...]              [排序 ▼]     │
│        ├────────────────────────────────────────┤
│        │ ┌────────┐ ┌────────┐ ┌────────┐      │
│        │ │  视频  │ │  视频  │ │  视频  │      │
│        │ │ 缩略图 │ │ 缩略图 │ │ 缩略图 │      │
│        │ │ 项目1  │ │ 项目2  │ │ 项目3  │      │
│        │ │ 2小时前│ │ 昨天   │ │ 3天前  │      │
│        │ └────────┘ └────────┘ └────────┘      │
│        │                                        │
│        │ ┌────────┐ ┌────────┐ ┌────────┐      │
│        │ │  视频  │ │  视频  │ │  视频  │      │
│        │ │ 缩略图 │ │ 缩略图 │ │ 缩略图 │      │
│        │ └────────┘ └────────┘ └────────┘      │
└────────┴────────────────────────────────────────┘
```

---

## 8. 状态指示

### 8.1 加载状态

```css
/* 骨架屏 */
.skeleton {
  background: linear-gradient(90deg, 
    var(--bg-surface) 25%, 
    var(--bg-hover) 50%, 
    var(--bg-surface) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

/* 旋转加载 */
.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-default);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
```

### 8.2 空状态

```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl);
  color: var(--text-secondary);
  text-align: center;
}

.empty-state .icon {
  font-size: 48px;
  margin-bottom: var(--space-md);
  opacity: 0.5;
}
```

---

## 9. 兼容性

### 9.1 浏览器
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### 9.2 平台
- macOS 11+ (Big Sur)
- Windows 10+
- (Linux 通过 WebKitGTK)

---

## 10. 快速参考表

| 元素 | 值 |
|------|-----|
| 主色 | #6366F1 |
| 背景深 | #0A0A0F |
| 卡片圆角 | 14px |
| 按钮圆角 | 10px |
| 间距基准 | 8px |
| 导航宽度 | 200px / 64px |
| 状态栏高 | 28px |
| 标题栏高 | 56px |

---

*更新于 2026-03-08*
