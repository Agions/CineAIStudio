"""
CineFlow 现代化设计系统 v3.0

设计理念：
- 简洁优雅的视觉层次
- 流畅的动画过渡
- 清晰的信息架构
- 深色模式优先
- 专业且富有创意
"""

# ========== 设计规范 ==========

# 颜色系统
COLOR_SYSTEM = {
    # 主色调 - 科技蓝
    "primary": "#00D4FF",
    "primary_dark": "#00A8CC",
    "primary_light": "#4DE8FF",

    # 辅助色调 - 渐变紫
    "secondary": "#8B5CF6",
    "secondary_dark": "#7C3AED",
    "secondary_light": "#A78BFA",

    # 中性色
    "bg": {
        # 背景色
        "primary": "#0A0E14",       # 主背景
        "secondary": "#111827",     # 次背景
        "tertiary": "#1F2937",      # 三级背景
        "elevated": "#1E293B",      # 悬浮卡片
        "overlay": "rgba(0, 0, 0, 0.75)",  # 遮罩层
    },

    # 文本色
    "text": {
        "primary": "#F9FAFB",
        "secondary": "#D1D5DB",
        "tertiary": "#9CA3AF",
        "muted": "#6B7280",
        "disabled": "#4B5563",
    },

    # 边框和分割线
    "border": {
        "subtle": "rgba(255, 255, 255, 0.08)",
        "default": "rgba(255, 255, 255, 0.12)",
        "strong": "rgba(255, 255, 255, 0.18)",
        "focus": "#00D4FF",
    },

    # 功能色
    "status": {
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "info": "#3B82F6",
    },

    # 渐变色
    "gradients": {
        "primary": "linear-gradient(135deg, #00D4FF 0%, #8B5CF6 100%)",
        "glass": "linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)",
        "shimmer": "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.1) 50%, transparent 100%)",
    },
}

# 字体系统
TYPOGRAPHY = {
    # 字体族
    "font_family": {
        "sans": ["SF Pro Display", "PingFang SC", "Microsoft YaHei", "Arial", "sans-serif"],
        "mono": ["SF Mono", "Monaco", "Consolas", "monospace"],
    },

    # 字号
    "font_size": {
        "xs": "0.75rem",    # 12px
        "sm": "0.875rem",   # 14px
        "base": "1rem",     # 16px
        "lg": "1.125rem",   # 18px
        "xl": "1.25rem",    # 20px
        "2xl": "1.5rem",    # 24px
        "3xl": "2rem",      # 32px
        "4xl": "2.5rem",    # 40px
    },

    # 字重
    "font_weight": {
        "light": 300,
        "normal": 400,
        "medium": 500,
        "semibold": 600,
        "bold": 700,
    },

    # 行高
    "line_height": {
        "tight": 1.25,
        "normal": 1.5,
        "relaxed": 1.75,
    },
}

# 间距系统
SPACING = {
    "xs": "4px",
    "sm": "8px",
    "md": "16px",
    "lg": "24px",
    "xl": "32px",
    "2xl": "48px",
    "3xl": "64px",
}

# 圆角系统
RADIUS = {
    "none": "0px",
    "sm": "4px",
    "md": "8px",
    "lg": "12px",
    "xl": "16px",
    "full": "9999px",
}

# 阴影系统
SHADOW = {
    "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.3)",
    "md": "0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3)",
    "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -2px rgba(0, 0, 0, 0.4)",
    "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.6), 0 10px 10px -5px rgba(0, 0, 0, 0.5)",
    "2xl": "0 25px 50px -12px rgba(0, 0, 0, 0.7)",
    "glow": "0 0 20px rgba(0, 212, 255, 0.3)",
}

# 过渡动画
TRANSITION = {
    "fast": "150ms cubic-bezier(0.4, 0, 0.2, 1)",
    "base": "250ms cubic-bezier(0.4, 0, 0.2, 1)",
    "slow": "350ms cubic-bezier(0.4, 0, 0.2, 1)",
}

# ========== 组件规范 ==========

 COMPONENT_SPEC = {
    # 按钮
    "button": {
        "height": {
            "sm": "32px",
            "md": "40px",
            "lg": "48px",
        },
        "padding": {
            "sm": "8px 16px",
            "md": "12px 24px",
            "lg": "16px 32px",
        },
    },

    # 卡片
    "card": {
        "padding": "24px",
        "gap": "16px",
    },

    # 输入框
    "input": {
        "height": "40px",
        "padding": "10px 14px",
    },

    # 模态框
    "dialog": {
        "max_width": "560px",
        "padding": "32px",
        "border_radius": "16px",
    },
}

# ========== 设计原则 ==========

DESIGN_PRINCIPLES = """
1. 渐变与玻璃拟态
   - 使用微妙的渐变创造深度
   - 玻璃拟态营造现代感
   - 避免过度使用，保持克制

2. 清晰的信息层次
   - 使用粗细和字号区分重要性
   - 间距创造呼吸感
   - 留白不等于浪费

3. 流畅的交互反馈
   - 悬停、点击有明确反馈
   - 过渡动画自然流畅
   - 加载状态清晰可见

4. 深色友好
   - 高对比度保证可读性
   - 避免纯黑，使用深蓝灰
   - 重点内容用亮色强调

5. 专业且富有创意
   - 风格统一不杂乱
   - 亮点用渐变色
   - 保持视觉趣味性
"""


# ========== CSS 变量映射 ==========

CSS_VARIABLES = f"""
/* CineFlow Design System Variables */

:root {{
    /* Colors */
    --color-primary: {COLOR_SYSTEM['primary']};
    --color-primary-hover: {COLOR_SYSTEM['primary_dark']};
    --color-secondary: {COLOR_SYSTEM['secondary']};

    --bg-primary: {COLOR_SYSTEM['bg']['primary']};
    --bg-secondary: {COLOR_SYSTEM['bg']['secondary']};
    --bg-tertiary: {COLOR_SYSTEM['bg']['tertiary']};
    --bg-elevated: {COLOR_SYSTEM['bg']['elevated']};

    --text-primary: {COLOR_SYSTEM['text']['primary']};
    --text-secondary: {COLOR_SYSTEM['text']['secondary']};
    --text-tertiary: {COLOR_SYSTEM['text']['tertiary']};
    --text-muted: {COLOR_SYSTEM['text']['muted']};

    --border-subtle: {COLOR_SYSTEM['border']['subtle']};
    --border-default: {COLOR_SYSTEM['border']['default']};
    --border-focus: {COLOR_SYSTEM['border']['focus']};

    --success: {COLOR_SYSTEM['status']['success']};
    --warning: {COLOR_SYSTEM['status']['warning']};
    --error: {COLOR_SYSTEM['status']['error']};
    --info: {COLOR_SYSTEM['status']['info']};

    /* Spacing */
    --spacing-xs: {SPACING['xs']};
    --spacing-sm: {SPACING['sm']};
    --spacing-md: {SPACING['md']};
    --spacing-lg: {SPACING['lg']};
    --spacing-xl: {SPACING['xl']};

    /* Radius */
    --radius-sm: {RADIUS['sm']};
    --radius-md: {RADIUS['md']};
    --radius-lg: {RADIUS['lg']};
    --radius-xl: {RADIUS['xl']};
    --radius-full: {RADIUS['full']};

    /* Transitions */
    --transition-fast: {TRANSITION['fast']};
    --transition-base: {TRANSITION['base']};
    --transition-slow: {TRANSITION['slow']};

    /* Shadows */
    --shadow-md: {SHADOW['md']};
    --shadow-lg: {SHADOW['lg']};
    --shadow-glow: {SHADOW['glow']};

    /* Gradients */
    --gradient-primary: {COLOR_SYSTEM['gradients']['primary']};
    --gradient-glass: {COLOR_SYSTEM['gradients']['glass']};
}}
"""


# ========== 使用示例 ==========

USAGE_EXAMPLES = """
# Python 中使用
from app.ui.theme.design_system import (
    COLOR_SYSTEM,
    TYPOGRAPHY,
    SPACING,
    CSS_VARIABLES
)

# 获取颜色
primary_color = COLOR_SYSTEM['primary']

# 应用样式
widget.setStyleSheet(f"""
    background: {COLOR_SYSTEM['bg']['elevated']};
    border: 1px solid {COLOR_SYSTEM['border']['subtle']};
    border-radius: {RADIUS['md']};
""")

# QSS 中使用
/* 直接复制 CSS_VARIABLES 到样式表或引用 */
QPushButton {{
    background-color: var(--color-primary);
    border-radius: var(--radius-md);
    transition: var(--transition-base);
}}
"""


if __name__ == "__main__":
    print("=" * 60)
    print("CineFlow 设计系统 v3.0")
    print("=" * 60)
    print("\n" + DESIGN_PRINCIPLES)
    print("\n" + CSS_VARIABLES)
    print("\n使用示例:" + USAGE_EXAMPLES)
