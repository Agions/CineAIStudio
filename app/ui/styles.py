"""
UI 样式系统
集中管理所有样式定义，便于维护和主题切换
"""

from PyQt6.QtGui import QColor


class Colors:
    """颜色系统"""
    # 主色调
    PRIMARY = "#2962FF"
    PRIMARY_HOVER = "#448AFF"
    PRIMARY_PRESSED = "#0039CB"
    
    # 辅助色
    SUCCESS = "#00C853"
    SUCCESS_BG = "#00C85322"
    WARNING = "#FFD600"
    WARNING_BG = "#FFD60022"
    ERROR = "#FF1744"
    ERROR_BG = "#FF174422"
    INFO = "#2979FF"
    
    # 暗色主题背景
    BG_DARK = "#121212"
    SURFACE_DARK = "#1E1E1E"
    SURFACE_LIGHT = "#2C2C2C"
    BORDER = "#333333"
    BORDER_LIGHT = "#444444"
    
    # 文字颜色
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#B0B0B0"
    TEXT_DISABLED = "#6E6E6E"
    
    # 状态颜色
    STATE_IDLE = "#00C853"
    STATE_WORKING = "#2962FF"
    STATE_PAUSED = "#FFD600"
    STATE_ERROR = "#FF1744"
    STATE_STOPPED = "#888888"


class Dimens:
    """尺寸系统"""
    # 间距
    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32
    
    # 圆角
    RADIUS_SM = 4
    RADIUS_MD = 8
    RADIUS_LG = 12
    RADIUS_XL = 16
    
    # 导航宽度
    NAV_WIDTH = 240
    
    # 卡片
    CARD_PADDING = 16
    CARD_SPACING = 16


class Styles:
    """样式集合"""
    
    @staticmethod
    def get_agent_card_style() -> str:
        """Agent卡片样式"""
        return f"""
            AgentCard {{
                background-color: {Colors.SURFACE_DARK};
                border: 1px solid {Colors.BORDER};
                border-radius: {Dimens.RADIUS_MD}px;
                padding: {Dimens.CARD_PADDING}px;
            }}
        """
    
    @staticmethod
    def get_progress_bar_style(color: str = Colors.PRIMARY) -> str:
        """进度条样式"""
        return f"""
            QProgressBar {{
                border: 1px solid {Colors.BORDER};
                border-radius: {Dimens.RADIUS_SM}px;
                text-align: center;
                color: {Colors.TEXT_PRIMARY};
                background-color: {Colors.SURFACE_DARK};
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: {Dimens.RADIUS_SM}px;
            }}
        """
    
    @staticmethod
    def get_button_primary_style() -> str:
        """主按钮样式"""
        return f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: white;
                border: none;
                border-radius: {Dimens.RADIUS_MD}px;
                padding: 10px 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRIMARY_PRESSED};
            }}
            QPushButton:disabled {{
                background-color: {Colors.SURFACE_LIGHT};
                color: {Colors.TEXT_DISABLED};
            }}
        """
    
    @staticmethod
    def get_button_ghost_style() -> str:
        """幽灵按钮样式"""
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: {Dimens.RADIUS_MD}px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {Colors.SURFACE_LIGHT};
                border-color: {Colors.TEXT_SECONDARY};
            }}
        """
    
    @staticmethod
    def get_nav_button_style() -> str:
        """导航按钮样式"""
        return f"""
            QPushButton {{
                text-align: left;
                padding: 12px 16px;
                border: none;
                border-radius: {Dimens.RADIUS_MD}px;
                color: {Colors.TEXT_SECONDARY};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {Colors.SURFACE_LIGHT};
                color: {Colors.TEXT_PRIMARY};
            }}
            QPushButton:checked {{
                background-color: {Colors.PRIMARY}22;
                color: {Colors.PRIMARY};
            }}
        """
    
    @staticmethod
    def get_list_widget_style() -> str:
        """列表样式"""
        return f"""
            QListWidget {{
                background-color: {Colors.SURFACE_DARK};
                border: 1px solid {Colors.BORDER};
                border-radius: {Dimens.RADIUS_MD}px;
                color: {Colors.TEXT_PRIMARY};
                outline: none;
            }}
            QListWidget::item {{
                padding: 12px 16px;
                border-bottom: 1px solid {Colors.BORDER};
            }}
            QListWidget::item:hover {{
                background-color: {Colors.SURFACE_LIGHT};
            }}
            QListWidget::item:selected {{
                background-color: {Colors.PRIMARY}22;
                color: {Colors.PRIMARY};
            }}
        """
    
    @staticmethod
    def get_scrollbar_style() -> str:
        """滚动条样式"""
        return f"""
            QScrollBar:vertical {{
                background-color: {Colors.SURFACE_DARK};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #444444;
                border-radius: 6px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #555555;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """
    
    @staticmethod
    def get_main_window_style() -> str:
        """主窗口样式"""
        return f"""
            QMainWindow {{
                background-color: {Colors.BG_DARK};
            }}
            QWidget {{
                background-color: {Colors.BG_DARK};
                color: {Colors.TEXT_PRIMARY};
                font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
            }}
        """
    
    @staticmethod
    def get_nav_frame_style() -> str:
        """导航栏样式"""
        return f"""
            QFrame {{
                background-color: {Colors.SURFACE_DARK};
                border-right: 1px solid {Colors.BORDER};
            }}
        """
    
    @staticmethod
    def get_status_label_style(color: str, bg_color: str) -> str:
        """状态标签样式"""
        return f"""
            font-size: 12px;
            color: {color};
            padding: 4px 8px;
            background-color: {bg_color};
            border-radius: {Dimens.RADIUS_SM}px;
        """
    
    @staticmethod
    def get_status_summary_style() -> str:
        """状态概览样式"""
        return f"""
            font-size: 14px;
            color: {Colors.TEXT_SECONDARY};
            padding: 12px;
            background-color: {Colors.SURFACE_DARK};
            border-radius: {Dimens.RADIUS_MD}px;
        """
    
    @staticmethod
    def get_agent_status_style(state: str) -> str:
        """获取Agent状态样式"""
        state_colors = {
            'IDLE': (Colors.STATE_IDLE, Colors.SUCCESS_BG),
            'WORKING': (Colors.STATE_WORKING, f"{Colors.STATE_WORKING}22"),
            'PAUSED': (Colors.STATE_PAUSED, Colors.WARNING_BG),
            'ERROR': (Colors.STATE_ERROR, Colors.ERROR_BG),
            'STOPPED': (Colors.STATE_STOPPED, f"{Colors.STATE_STOPPED}22"),
        }
        color, bg = state_colors.get(state, (Colors.TEXT_SECONDARY, Colors.SURFACE_LIGHT))
        return Styles.get_status_label_style(color, bg)


class StyleHelper:
    """样式辅助类"""
    
    @staticmethod
    def apply_dark_theme(app):
        """应用暗色主题"""
        from PyQt6.QtGui import QFont
        
        # 设置字体
        font = QFont("Inter", 10)
        font.setStyleHint(QFont.StyleHint.SansSerif)
        app.setFont(font)
        
        # 应用样式
        app.setStyleSheet(Styles.get_main_window_style() + Styles.get_scrollbar_style())
    
    @staticmethod
    def create_status_label(parent, text: str, state: str) -> "QLabel":
        """创建状态标签"""
        from PyQt6.QtWidgets import QLabel
        
        label = QLabel(text, parent)
        label.setStyleSheet(Styles.get_agent_status_style(state))
        return label
