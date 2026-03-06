"""
主题管理器 - 管理应用程序主题
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QColor

from ...core.config_manager import ThemeConfig


@dataclass
class ThemeColors:
    """主题颜色 - ClipFlowCut 现代暗色 V2"""
    # 主色调渐变
    primary: str = "#6366F1"
    primary_end: str = "#8B5CF6"  # 渐变结束色
    primary_light: str = "#818CF8"
    
    # 强调色
    accent: str = "#06B6D4"  # 青色强调
    
    secondary: str = "#1F6FEB"
    background: str = "#0A0A0F"  # 最深背景
    surface: str = "#12121A"     # 第二层
    card: str = "#1A1A24"        # 卡片背景
    card_elevated: str = "#22222E"  # 悬浮卡片
    
    text: str = "#E6EDF3"
    text_secondary: str = "#C9D1D9"
    text_tertiary: str = "#8B949E"
    
    border: str = "#30363D"
    border_light: str = "#484F58"
    divider: str = "#21262D"
    
    # 状态色
    error: str = "#DA3633"
    warning: str = "#D29922"
    success: str = "#238636"
    info: str = "#388BFD"
    
    accent_purple: str = "#A371F7"
    tertiary: str = "#8B5CF6"
    light: str = "#DBEAFE"
    dark: str = "#1E40AF"


class ThemePreset:
    """主题预设"""
    def __init__(self, name: str, mode: str, colors: ThemeColors):
        self.name = name
        self.mode = mode
        self.colors = colors
        self.stylesheet_path = f"{mode}_theme.qss"


class ThemeManager(QObject):
    """主题管理器"""

    # 信号定义
    theme_changed = pyqtSignal(str)  # 主题模式变更信号
    theme_applied = pyqtSignal()  # 主题应用完成信号

    def __init__(self, theme_config: ThemeConfig):
        super().__init__()

        self.theme_config = theme_config
        self.current_mode = theme_config.mode
        self.colors = ThemeColors()
        self.theme_presets: List[ThemePreset] = []
        
        # 初始化主题预设
        self._initialize_theme_presets()
        
        # 更新颜色配置
        self._update_colors()

    def _initialize_theme_presets(self) -> None:
        """初始化主题预设"""
        # 深色主题预设 - ClipFlowCut 现代暗色 V2
        dark_colors = ThemeColors(
            primary="#6366F1",
            primary_end="#8B5CF6",
            primary_light="#818CF8",
            accent="#06B6D4",
            secondary="#1F6FEB",
            background="#0A0A0F",
            surface="#12121A",
            card="#1A1A24",
            card_elevated="#22222E",
            text="#E6EDF3",
            text_secondary="#C9D1D9",
            text_tertiary="#8B949E",
            border="#30363D",
            border_light="#484F58",
            divider="#21262D",
            error="#DA3633",
            warning="#D29922",
            success="#238636",
            info="#388BFD",
            accent_purple="#A371F7",
            tertiary="#8B5CF6",
            light="#DBEAFE",
            dark="#1E40AF"
        )

        # 浅色主题预设
        light_colors = ThemeColors(
            primary="#0969DA",
            secondary="#0550AE",
            background="#FFFFFF",
            surface="#F6F8FA",
            card="#FFFFFF",
            text="#1F2328",
            text_secondary="#656D76",
            border="#D0D7DE",
            divider="#D8DEE4",
            error="#CF222E",
            warning="#9A6700",
            success="#1A7F37",
            info="#0969DA",
            accent="#BF3989",
            tertiary="#8250DF",
            light="#F0F3F6",
            dark="#0550AE"
        )

        # 蓝调深色主题 - GitHub 风格
        blue_dark_colors = ThemeColors(
            primary="#388BFD",
            secondary="#1F6FEB",
            background="#0D1117",
            surface="#161B22",
            card="#161B22",
            text="#E6EDF3",
            text_secondary="#C9D1D9",
            border="#30363D",
            divider="#21262D",
            error="#DA3633",
            warning="#D29922",
            success="#238636",
            info="#388BFD",
            accent="#A371F7",
            tertiary="#8B5CF6",
            light="#DBEAFE",
            dark="#1E40AF"
        )
        
        # 森林绿色主题
        forest_colors = ThemeColors(
            primary="#22C55E",
            secondary="#16A34A",
            background="#064E3B",
            surface="#14532D",
            card="#14532D",
            text="#ECFDF5",
            text_secondary="#99F6E4",
            border="#16A34A",
            divider="#15803D",
            error="#EF4444",
            warning="#F59E0B",
            success="#22C55E",
            info="#3B82F6",
            accent="#8B5CF6",
            tertiary="#EC4899",
            light="#BBF7D0",
            dark="#052E16"
        )
        
        # 紫色主题
        purple_colors = ThemeColors(
            primary="#9C27B0",
            secondary="#7B1FA2",
            background="#121212",
            surface="#1E1B1E",
            card="#1E1B1E",
            text="#FFFFFF",
            text_secondary="#E0E0E0",
            border="#4A148C",
            divider="#311B92",
            error="#F44336",
            warning="#FFB300",
            success="#66BB6A",
            info="#2196F3",
            accent="#EC407A",
            tertiary="#5C6BC0",
            light="#E1BEE7",
            dark="#4A148C"
        )
        
        # 橙色主题
        orange_colors = ThemeColors(
            primary="#FF5722",
            secondary="#E64A19",
            background="#263238",
            surface="#37474F",
            card="#37474F",
            text="#FFFFFF",
            text_secondary="#CFD8DC",
            border="#546E7A",
            divider="#455A64",
            error="#F44336",
            warning="#FFB74D",
            success="#81C784",
            info="#4FC3F7",
            accent="#9575CD",
            tertiary="#FF8A65",
            light="#FFCCBC",
            dark="#BF360C"
        )
        
        # 添加主题预设
        self.theme_presets = [
            ThemePreset("深色主题", "dark", dark_colors),
            ThemePreset("浅色主题", "light", light_colors),
            ThemePreset("蓝调深色", "dark", blue_dark_colors),
            ThemePreset("森林绿色", "dark", forest_colors),
            ThemePreset("紫色主题", "dark", purple_colors),
            ThemePreset("橙色主题", "dark", orange_colors)
        ]

    def get_available_themes(self) -> List[str]:
        """获取可用主题列表"""
        return [preset.name for preset in self.theme_presets]
        
    def get_theme_preset(self, theme_name: str) -> Optional[ThemePreset]:
        """获取指定主题预设"""
        for preset in self.theme_presets:
            if preset.name == theme_name:
                return preset
        return None
        
    def apply_theme_by_name(self, theme_name: str) -> None:
        """通过主题名称应用主题"""
        preset = self.get_theme_preset(theme_name)
        if preset:
            self.set_theme_mode(preset.mode)
            # 应用主题颜色
            self.colors = preset.colors
            self._apply_to_application()
            self.theme_changed.emit(theme_name)
            self.theme_applied.emit()

    def _update_colors(self) -> None:
        """更新颜色配置"""
        if self.current_mode == "dark":
            self.colors = ThemeColors(
                primary=self.theme_config.primary_color,
                secondary=self.theme_config.secondary_color,
                background=self.theme_config.background_color,
                surface=self.theme_config.surface_color,
                text=self.theme_config.text_color,
                border="#404040",
                divider="#555555",
                accent="#FF4081",
                tertiary="#9C27B0",
                light="#E3F2FD",
                dark="#0D47A1"
            )
        else:
            self.colors = ThemeColors(
                primary=self.theme_config.primary_color,
                secondary=self.theme_config.secondary_color,
                background="#FFFFFF",
                surface="#F5F5F5",
                card="#FFFFFF",
                text="#000000",
                text_secondary="#666666",
                border="#E0E0E0",
                divider="#EEEEEE",
                accent="#FF4081",
                tertiary="#9C27B0",
                light="#E3F2FD",
                dark="#0D47A1"
            )

    def set_theme_mode(self, mode: str) -> None:
        """设置主题模式"""
        if mode != self.current_mode:
            self.current_mode = mode
            self._update_colors()
            self.theme_changed.emit(mode)
            # 应用主题到整个应用
            self._apply_to_application()
            self.theme_applied.emit()

    def get_theme_mode(self) -> str:
        """获取主题模式"""
        return self.current_mode

    def apply_theme(self, widget) -> None:
        """应用主题到窗口部件"""
        stylesheet = self.get_stylesheet()
        widget.setStyleSheet(stylesheet)

    def get_stylesheet(self) -> str:
        """获取样式表"""
        import os
        stylesheet_path = ""
        if self.current_mode == "dark":
            # 使用外部深色主题样式表
            stylesheet_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "resources", "styles", "dark_theme.qss")
        else:
            # 使用外部浅色主题样式表（如果存在）
            stylesheet_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "resources", "styles", "light_theme.qss")
        
        try:
            with open(stylesheet_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            # 如果外部样式表不存在，使用默认样式
            return self._get_default_stylesheet()

    def _get_default_stylesheet(self) -> str:
        """获取默认样式表"""
        return """/* 默认样式 */
        QMainWindow {
            background-color: #1E1E1E;
            color: white;
        }
        QPushButton {
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
        }
        QPushButton:hover {
            background-color: #1976D2;
        }
        QLineEdit, QTextEdit {
            background-color: #2D2D2D;
            color: white;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 8px;
        }
        QLabel {
            color: white;
        }
        """

    def get_colors(self) -> ThemeColors:
        """获取主题颜色"""
        return self.colors

    def set_color(self, color_type: str, color: str) -> None:
        """设置主题颜色"""
        if hasattr(self.colors, color_type):
            setattr(self.colors, color_type, color)

    def get_color(self, color_type: str) -> str:
        """获取主题颜色"""
        return getattr(self.colors, color_type, "#000000")

    def _apply_to_application(self) -> None:
        """将主题应用到整个应用程序"""
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            # 获取样式表
            stylesheet = self.get_stylesheet()
            # 应用样式到整个应用
            app.setStyleSheet(stylesheet)
            # 应用到所有顶级窗口
            for widget in app.allWidgets():
                widget.setStyleSheet(stylesheet)
        
    def apply_theme_instantly(self, theme_name: str) -> None:
        """立即应用主题，用于实时预览"""
        preset = self.get_theme_preset(theme_name)
        if preset:
            # 保存当前主题状态
            original_mode = self.current_mode
            
            # 保存当前颜色配置
            original_colors = ThemeColors(
                primary=self.colors.primary,
                secondary=self.colors.secondary,
                background=self.colors.background,
                surface=self.colors.surface,
                card=self.colors.card,
                text=self.colors.text,
                text_secondary=self.colors.text_secondary,
                border=self.colors.border,
                divider=self.colors.divider,
                error=self.colors.error,
                warning=self.colors.warning,
                success=self.colors.success,
                info=self.colors.info,
                accent=self.colors.accent,
                tertiary=self.colors.tertiary,
                light=self.colors.light,
                dark=self.colors.dark
            )
            
            # 应用新主题
            self.current_mode = preset.mode
            self.colors = preset.colors
            self._apply_to_application()
            self.theme_changed.emit(theme_name)
            self.theme_applied.emit()
            
            # 3秒后恢复原主题（仅用于预览）
            QTimer.singleShot(3000, lambda: self._restore_theme(original_mode, original_colors))
            
    def _restore_theme(self, original_mode: str, original_colors: ThemeColors) -> None:
        """恢复原始主题"""
        self.current_mode = original_mode
        self.colors = original_colors
        self._apply_to_application()
        self.theme_changed.emit(original_mode)
        self.theme_applied.emit()
        
    def get_current_theme_info(self) -> Dict[str, Any]:
        """获取当前主题信息"""
        return {
            "mode": self.current_mode,
            "colors": self.colors.__dict__,
            "available_themes": self.get_available_themes()
        }


# ============ 样式生成器 - 整合自 design_system.py ============

class StyleSheet:
    """样式生成器 - ClipFlowCut 现代暗色主题"""

    # 样式常量
    COLORS = {
        # 主色调渐变
        "primary": "#6366F1",
        "primary_end": "#8B5CF6",
        "primary_light": "#818CF8",
        
        # 强调色
        "accent": "#06B6D4",
        
        "primary_dark": "#4F46E5",
        "success": "#238636",
        "success_light": "#2EA043",
        "warning": "#D29922",
        "warning_light": "#E3B341",
        "error": "#DA3633",
        "error_light": "#F85149",
        
        # 背景层次
        "background": "#0A0A0F",
        "surface": "#12121A",
        "card": "#1A1A24",
        "card_elevated": "#22222E",
        "card_hover": "#282832",
        
        "border": "#30363D",
        "border_light": "#484F58",
        "divider": "#21262D",
        
        "text": "#E6EDF3",
        "text_secondary": "#C9D1D9",
        "text_tertiary": "#8B949E",
        "text_disabled": "#484F58",
        
        "accent_purple": "#A371F7",
        "accent_light": "#BC8CFF",
    }

    BORDER_RADIUS = {"sm": 4, "md": 8, "lg": 12, "xl": 16, "full": 9999}
    SPACING = {"xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32, "2xl": 48}
    FONT_SIZES = {"xs": 11, "sm": 12, "md": 14, "lg": 16, "xl": 18, "2xl": 24, "3xl": 32}

    @staticmethod
    def button(variant="primary"):
        radius = StyleSheet.BORDER_RADIUS
        spacing = StyleSheet.SPACING
        variants = {
            "primary": ("background-color: #238636;", "background-color: #2EA043;", "background-color: #238636;"),
            "secondary": ("background-color: transparent; border: 1px solid #30363D; color: #C9D1D9;",
                          "background-color: #21262D; border-color: #484F58;", "background-color: transparent;"),
            "danger": ("background-color: #DA3633; color: #FFFFFF;", "background-color: #F85149;", "background-color: #DA3633;"),
            "ghost": ("background-color: transparent; color: #8B949E;", "background-color: rgba(177, 186, 196, 0.08); color: #E6EDF3;", "background-color: transparent;"),
        }
        normal, hover, pressed = variants.get(variant, variants["primary"])
        return f"""
        QPushButton {{ {normal} border-radius: {radius['md']}px; padding: {spacing['sm'] + 2}px {spacing['md'] + 2}px; font-size: 13px; font-weight: 600; }}
        QPushButton:hover {{ {hover} }}
        QPushButton:pressed {{ {pressed} }}
        QPushButton:disabled {{ background-color: #21262D; color: #484F58; border: none; }}
        """

    @staticmethod
    def card():
        colors = StyleSheet.COLORS
        radius = StyleSheet.BORDER_RADIUS
        return f"""
        QWidget {{ background-color: {colors['card']}; border: 1px solid {colors['border']}; border-radius: {radius['lg']}px; }}
        QWidget:hover {{ border-color: {colors['border_light']}; }}
        """

    @staticmethod
    def input():
        colors = StyleSheet.COLORS
        radius = StyleSheet.BORDER_RADIUS
        spacing = StyleSheet.SPACING
        return f"""
        QLineEdit, QTextEdit {{ background-color: {colors['background']}; color: {colors['text']}; border: 1px solid {colors['border']}; border-radius: {radius['md']}px; padding: {spacing['sm'] + 2}px {spacing['sm'] + 4}px; font-size: 14px; }}
        QLineEdit:hover, QTextEdit:hover {{ border-color: {colors['border_light']}; }}
        QLineEdit:focus, QTextEdit:focus {{ border-color: {colors['primary']}; background-color: {colors['surface']}; }}
        """

    @staticmethod
    def label(secondary=False):
        colors = StyleSheet.COLORS
        color = colors["text_secondary"] if secondary else colors["text"]
        return f"QLabel {{ color: {color}; font-size: 14px; }}"

    @staticmethod
    def panel():
        colors = StyleSheet.COLORS
        return f"QWidget {{ background-color: {colors['surface']}; }}"

    @staticmethod
    def progress_bar():
        colors = StyleSheet.COLORS
        radius = StyleSheet.BORDER_RADIUS
        return f"""
        QProgressBar {{ background-color: {colors['divider']}; border: none; border-radius: {radius['md']}px; text-align: center; color: {colors['text']}; font-size: 12px; font-weight: 600; }}
        QProgressBar::chunk {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #388BFD, stop:1 #79C0FF); border-radius: {radius['md']}px; }}
        """

    @staticmethod
    def nav_button(selected=False):
        radius = StyleSheet.BORDER_RADIUS
        if selected:
            bg, color = "rgba(56, 139, 253, 0.15)", "#388BFD"
        else:
            bg, color = "transparent", "#8B949E"
        return f"""
        QPushButton {{ text-align: left; background-color: {bg}; border: none; border-radius: {radius['md']}px; color: {color}; padding: 12px 16px; font-size: 14px; font-weight: 500; }}
        QPushButton:hover {{ background-color: rgba(177, 186, 196, 0.08); color: #E6EDF3; }}
        """

    @staticmethod
    def card_elevated():
        colors = StyleSheet.COLORS
        radius = StyleSheet.BORDER_RADIUS
        return f"QWidget {{ background-color: {colors['card']}; border: 1px solid {colors['border']}; border-radius: {radius['lg']}px; }}"

    @staticmethod
    def tooltip():
        colors = StyleSheet.COLORS
        radius = StyleSheet.BORDER_RADIUS
        return f"QToolTip {{ background-color: {colors['surface']}; color: {colors['text']}; border: 1px solid {colors['border']}; border-radius: {radius['md']}px; padding: 6px 10px; font-size: 12px; }}"