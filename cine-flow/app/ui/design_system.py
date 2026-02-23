"""
CineAI Design System (CDS)
核心设计规范定义，包含色彩、排版、间距和阴影系统
"""

from PyQt6.QtGui import QColor, QFont

class Colors:
    """色彩系统"""
    # 品牌色
    Primary = "#2962FF"       # 核心蓝
    PrimaryHover = "#448AFF"
    PrimaryPressed = "#0039CB"
    
    # 辅助色
    Secondary = "#6200EA"     # 深紫
    Accent = "#00B0FF"        # 亮蓝
    
    # 功能色
    Success = "#00C853"
    Warning = "#FFD600"
    Error = "#FF1744"
    Info = "#2979FF"
    
    # 暗色模式背景
    BackgroundDark = "#121212"    # 主背景
    SurfaceDark = "#1E1E1E"       # 卡片/面板背景
    SurfaceLight = "#2C2C2C"      # 悬浮/输入框背景
    BorderDark = "#333333"        # 边框颜色
    
    # 文字颜色
    TextPrimary = "#FFFFFF"       # 主要文字 (87%)
    TextSecondary = "#B0B0B0"     # 次要文字 (60%)
    TextDisabled = "#6E6E6E"      # 禁用文字 (38%)
    
    # 亮色模式映射 (如果需要可扩展)

class Typography:
    """排版系统"""
    # 字体族 (优先使用系统现代字体)
    FontFamily = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    CodeFamily = "'JetBrains Mono', 'Fira Code', Consolas, monospace"
    
    @staticmethod
    def get_header_font(size=24, bold=True):
        font = QFont()
        font.setFamily(Typography.FontFamily)
        font.setPixelSize(size)
        font.setBold(bold)
        return font
        
    @staticmethod
    def get_body_font(size=14):
        font = QFont()
        font.setFamily(Typography.FontFamily)
        font.setPixelSize(size)
        return font

class Dimens:
    """尺寸系统"""
    # 间距
    SpacingXS = 4
    SpacingS = 8
    SpacingM = 16
    SpacingL = 24
    SpacingXL = 32
    
    # 圆角
    RadiusS = 4
    RadiusM = 8
    RadiusL = 12
    RadiusXL = 16
    
    # 控件高度
    BtnHeightS = 28
    BtnHeightM = 36
    BtnHeightL = 44
    InputHeight = 36

class Styles:
    """样式片段"""
    
    # 卡片样式
    Card = f"""
        background-color: {Colors.SurfaceDark};
        border: 1px solid {Colors.BorderDark};
        border-radius: {Dimens.RadiusL}px;
    """
    
    # 主按钮样式
    ButtonPrimary = f"""
        QPushButton {{
            background-color: {Colors.Primary};
            color: white;
            border: none;
            border-radius: {Dimens.RadiusM}px;
            padding: 8px 16px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {Colors.PrimaryHover};
        }}
        QPushButton:pressed {{
            background-color: {Colors.PrimaryPressed};
        }}
        QPushButton:disabled {{
            background-color: {Colors.SurfaceLight};
            color: {Colors.TextDisabled};
        }}
    """
    
    # 次要/幽灵按钮
    ButtonGhost = f"""
        QPushButton {{
            background-color: transparent;
            color: {Colors.TextPrimary};
            border: 1px solid {Colors.BorderDark};
            border-radius: {Dimens.RadiusM}px;
            padding: 8px 16px;
        }}
        QPushButton:hover {{
            background-color: {Colors.SurfaceLight};
            border-color: {Colors.TextSecondary};
        }}
    """
    
    # 输入框样式
    Input = f"""
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {Colors.SurfaceDark};
            border: 1px solid {Colors.BorderDark};
            border-radius: {Dimens.RadiusM}px;
            color: {Colors.TextPrimary};
            padding: 8px;
            selection-background-color: {Colors.Primary};
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border: 1px solid {Colors.Primary};
            background-color: {Colors.SurfaceLight};
        }}
    """
