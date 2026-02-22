"""
CineAI Design System V2.0 (2026)
基于最新 UI/UX 趋势的现代化设计系统
- 更高对比度和可访问性 (WCAG AAA)
- 流畅的微交互动画
- 自适应布局系统
- 专业视频编辑器风格
"""

from PyQt6.QtGui import QColor, QFont, QLinearGradient, QGradient
from PyQt6.QtCore import QEasingCurve, QPropertyAnimation
from typing import Dict, Tuple


class ColorsV2:
    """2026 现代色彩系统 - 更高对比度，更好可访问性"""
    
    # 品牌色 - 渐变支持
    Primary = "#2962FF"
    PrimaryHover = "#448AFF"
    PrimaryPressed = "#0039CB"
    PrimaryLight = "#82B1FF"
    
    # 语义色 - 增强对比度
    Success = "#00E676"
    SuccessDark = "#00C853"
    Warning = "#FFD740"
    WarningDark = "#FFC400"
    Error = "#FF5252"
    ErrorDark = "#FF1744"
    Info = "#40C4FF"
    InfoDark = "#00B0FF"
    
    # 暗色模式背景 - 更深的层次
    BackgroundDark = "#0A0A0A"
    SurfaceDark = "#1A1A1A"
    SurfaceLight = "#242424"
    SurfaceHover = "#2E2E2E"
    BorderDark = "#3A3A3A"
    BorderLight = "#4A4A4A"
    
    # 文字颜色 - WCAG AAA 级别
    TextPrimary = "#FFFFFF"
    TextSecondary = "#B8B8B8"
    TextTertiary = "#8A8A8A"
    TextDisabled = "#5A5A5A"
    
    # 功能色 - 视频编辑器专用
    VideoTrack = "#FF6B6B"
    AudioTrack = "#4ECDC4"
    SubtitleTrack = "#FFE66D"
    AIGenerated = "#A78BFA"
    
    # 状态色
    Online = "#00E676"
    Offline = "#757575"
    Processing = "#FFD740"
    
    @staticmethod
    def get_gradient(start_color: str, end_color: str, angle: int = 135) -> QLinearGradient:
        """创建渐变色"""
        gradient = QLinearGradient(0, 0, 1, 1)
        gradient.setColorAt(0, QColor(start_color))
        gradient.setColorAt(1, QColor(end_color))
        gradient.setCoordinateMode(QGradient.CoordinateMode.ObjectBoundingMode)
        return gradient


class TypographyV2:
    """2026 现代排版系统"""
    
    # 字体族 - 优先使用可变字体
    FontFamily = "'Inter Variable', 'SF Pro Display', -apple-system, system-ui, sans-serif"
    FontFamilyChinese = "'PingFang SC', 'Microsoft YaHei', 'Noto Sans CJK SC', sans-serif"
    CodeFamily = "'JetBrains Mono', 'Fira Code', 'SF Mono', monospace"
    
    # 字体大小 - 使用 Type Scale
    FontSize = {
        "xs": 11,
        "sm": 13,
        "base": 15,
        "lg": 17,
        "xl": 20,
        "2xl": 24,
        "3xl": 30,
        "4xl": 36,
    }
    
    # 行高
    LineHeight = {
        "tight": 1.25,
        "normal": 1.5,
        "relaxed": 1.75,
    }
    
    # 字重
    FontWeight = {
        "regular": 400,
        "medium": 500,
        "semibold": 600,
        "bold": 700,
    }
    
    @staticmethod
    def get_font(size: str = "base", weight: str = "regular", family: str = "default") -> QFont:
        """获取字体对象"""
        font = QFont()
        
        # 设置字体族
        if family == "code":
            font.setFamily(TypographyV2.CodeFamily)
        elif family == "chinese":
            font.setFamily(TypographyV2.FontFamilyChinese)
        else:
            font.setFamily(TypographyV2.FontFamily)
        
        # 设置字体大小
        font.setPixelSize(TypographyV2.FontSize.get(size, 15))
        
        # 设置字重
        font.setWeight(TypographyV2.FontWeight.get(weight, 400))
        
        return font


class DimensV2:
    """2026 现代间距系统 - 8px 基准"""
    
    # 间距 (8px 倍数)
    Space = {
        "0": 0,
        "1": 4,
        "2": 8,
        "3": 12,
        "4": 16,
        "5": 20,
        "6": 24,
        "8": 32,
        "10": 40,
        "12": 48,
        "16": 64,
    }
    
    # 圆角 - 更柔和的曲线
    Radius = {
        "none": 0,
        "sm": 6,
        "md": 10,
        "lg": 14,
        "xl": 18,
        "2xl": 24,
        "full": 9999,
    }
    
    # 阴影 - 更自然的深度
    Shadow = {
        "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.3)",
        "md": "0 4px 6px -1px rgba(0, 0, 0, 0.4)",
        "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.5)",
        "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.6)",
        "2xl": "0 25px 50px -12px rgba(0, 0, 0, 0.7)",
    }
    
    # 控件尺寸
    Control = {
        "xs": 24,
        "sm": 32,
        "md": 40,
        "lg": 48,
        "xl": 56,
    }


class AnimationsV2:
    """流畅的微交互动画"""
    
    # 动画时长 (ms)
    Duration = {
        "fast": 150,
        "normal": 250,
        "slow": 350,
    }
    
    # 缓动函数
    Easing = {
        "ease_in_out": QEasingCurve.Type.InOutCubic,
        "ease_out": QEasingCurve.Type.OutCubic,
        "ease_in": QEasingCurve.Type.InCubic,
        "bounce": QEasingCurve.Type.OutBounce,
        "elastic": QEasingCurve.Type.OutElastic,
    }
    
    @staticmethod
    def create_fade_animation(widget, duration: int = 250, start: float = 0.0, end: float = 1.0):
        """创建淡入淡出动画"""
        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(start)
        animation.setEndValue(end)
        animation.setEasingCurve(AnimationsV2.Easing["ease_in_out"])
        return animation


class LayoutV2:
    """响应式布局系统"""
    
    # 窗口尺寸
    MinWidth = 1024
    MinHeight = 768
    RecommendedWidth = 1920
    RecommendedHeight = 1080
    
    # 布局断点
    Breakpoints = {
        "sm": 1024,
        "md": 1440,
        "lg": 1920,
        "xl": 2560,
    }
    
    # 侧边栏宽度
    Sidebar = {
        "collapsed": 60,
        "normal": 200,
        "wide": 280,
    }
    
    # 面板尺寸
    Panel = {
        "min": 200,
        "default": 300,
        "max": 500,
    }


class StylesV2:
    """现代化样式片段"""
    
    @staticmethod
    def get_card_style(elevated: bool = False) -> str:
        """卡片样式"""
        shadow = DimensV2.Shadow["lg"] if elevated else DimensV2.Shadow["sm"]
        return f"""
            background-color: {ColorsV2.SurfaceDark};
            border: 1px solid {ColorsV2.BorderDark};
            border-radius: {DimensV2.Radius["lg"]}px;
            box-shadow: {shadow};
        """
    
    @staticmethod
    def get_button_style(variant: str = "primary") -> str:
        """按钮样式"""
        if variant == "primary":
            return f"""
                QPushButton {{
                    background-color: {ColorsV2.Primary};
                    color: white;
                    border: none;
                    border-radius: {DimensV2.Radius["md"]}px;
                    padding: {DimensV2.Space["2"]}px {DimensV2.Space["4"]}px;
                    font-weight: {TypographyV2.FontWeight["semibold"]};
                    min-height: {DimensV2.Control["md"]}px;
                }}
                QPushButton:hover {{
                    background-color: {ColorsV2.PrimaryHover};
                }}
                QPushButton:pressed {{
                    background-color: {ColorsV2.PrimaryPressed};
                }}
                QPushButton:disabled {{
                    background-color: {ColorsV2.SurfaceLight};
                    color: {ColorsV2.TextDisabled};
                }}
            """
        elif variant == "secondary":
            return f"""
                QPushButton {{
                    background-color: {ColorsV2.SurfaceLight};
                    color: {ColorsV2.TextPrimary};
                    border: 1px solid {ColorsV2.BorderDark};
                    border-radius: {DimensV2.Radius["md"]}px;
                    padding: {DimensV2.Space["2"]}px {DimensV2.Space["4"]}px;
                    font-weight: {TypographyV2.FontWeight["medium"]};
                    min-height: {DimensV2.Control["md"]}px;
                }}
                QPushButton:hover {{
                    background-color: {ColorsV2.SurfaceHover};
                    border-color: {ColorsV2.BorderLight};
                }}
            """
        elif variant == "ghost":
            return f"""
                QPushButton {{
                    background-color: transparent;
                    color: {ColorsV2.TextPrimary};
                    border: none;
                    border-radius: {DimensV2.Radius["md"]}px;
                    padding: {DimensV2.Space["2"]}px {DimensV2.Space["4"]}px;
                    min-height: {DimensV2.Control["md"]}px;
                }}
                QPushButton:hover {{
                    background-color: {ColorsV2.SurfaceLight};
                }}
            """
        return ""
    
    @staticmethod
    def get_input_style() -> str:
        """输入框样式"""
        return f"""
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {ColorsV2.SurfaceDark};
                border: 1px solid {ColorsV2.BorderDark};
                border-radius: {DimensV2.Radius["md"]}px;
                color: {ColorsV2.TextPrimary};
                padding: {DimensV2.Space["2"]}px {DimensV2.Space["3"]}px;
                selection-background-color: {ColorsV2.Primary};
                min-height: {DimensV2.Control["md"]}px;
            }}
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border: 1px solid {ColorsV2.Primary};
                background-color: {ColorsV2.SurfaceLight};
            }}
            QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
                background-color: {ColorsV2.SurfaceLight};
                color: {ColorsV2.TextDisabled};
            }}
        """
    
    @staticmethod
    def get_nav_button_style() -> str:
        """导航按钮样式"""
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {ColorsV2.TextSecondary};
                border: none;
                border-radius: {DimensV2.Radius["md"]}px;
                padding: {DimensV2.Space["2"]}px {DimensV2.Space["3"]}px;
                text-align: left;
                min-height: {DimensV2.Control["md"]}px;
            }}
            QPushButton:hover {{
                background-color: {ColorsV2.SurfaceLight};
                color: {ColorsV2.TextPrimary};
            }}
            QPushButton:checked {{
                background-color: {ColorsV2.Primary};
                color: white;
            }}
        """


class ShortcutsV2:
    """全局快捷键定义"""
    
    Global = {
        "Cmd+N": "新建项目",
        "Cmd+O": "打开项目",
        "Cmd+S": "保存项目",
        "Cmd+Shift+S": "另存为",
        "Cmd+E": "导出视频",
        "Cmd+Z": "撤销",
        "Cmd+Shift+Z": "重做",
        "Cmd+W": "关闭窗口",
        "Cmd+Q": "退出应用",
        "Cmd+,": "打开设置",
    }
    
    Editor = {
        "Space": "播放/暂停",
        "Cmd+K": "分割片段",
        "Cmd+D": "复制片段",
        "Delete": "删除片段",
        "Cmd+C": "复制",
        "Cmd+V": "粘贴",
        "Cmd+X": "剪切",
        "Cmd+A": "全选",
        "Cmd+[": "缩小时间轴",
        "Cmd+]": "放大时间轴",
    }
    
    Navigation = {
        "Cmd+1": "切换到首页",
        "Cmd+2": "切换到项目",
        "Cmd+3": "切换到设置",
        "Cmd+Tab": "切换页面",
    }


# 导出所有类
__all__ = [
    "ColorsV2",
    "TypographyV2",
    "DimensV2",
    "AnimationsV2",
    "LayoutV2",
    "StylesV2",
    "ShortcutsV2",
]
