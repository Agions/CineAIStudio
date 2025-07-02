#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
专业UI系统 - 解决文字堆叠、界面不完整等问题
基于Material Design和Ant Design最佳实践
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QSplitter, QTabWidget,
    QStackedWidget, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPalette, QColor

from app.config.settings_manager import SettingsManager
from app.core.project_manager import ProjectManager
from app.ai import AIManager


class ProfessionalTheme:
    """专业主题系统 - 无CSS依赖"""
    
    # 浅色主题
    LIGHT = {
        'primary': '#1890ff',
        'primary_hover': '#40a9ff',
        'primary_active': '#096dd9',
        'background': '#ffffff',
        'surface': '#fafafa',
        'border': '#e8e8e8',
        'text_primary': '#262626',
        'text_secondary': '#595959',
        'text_disabled': '#bfbfbf',
        'success': '#52c41a',
        'warning': '#faad14',
        'error': '#ff4d4f',
        'shadow': 'rgba(0, 0, 0, 0.1)'
    }
    
    # 深色主题
    DARK = {
        'primary': '#177ddc',
        'primary_hover': '#3c9ae8',
        'primary_active': '#0958d9',
        'background': '#1f1f1f',
        'surface': '#262626',
        'border': '#434343',
        'text_primary': '#ffffff',
        'text_secondary': '#a6a6a6',
        'text_disabled': '#595959',
        'success': '#49aa19',
        'warning': '#d89614',
        'error': '#dc4446',
        'shadow': 'rgba(0, 0, 0, 0.3)'
    }
    
    @staticmethod
    def get_colors(is_dark=False):
        return ProfessionalTheme.DARK if is_dark else ProfessionalTheme.LIGHT


class ProfessionalButton(QPushButton):
    """专业按钮组件 - 解决可见性问题"""
    
    def __init__(self, text="", button_type="default", parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self.is_dark_theme = False
        
        # 设置基本属性
        self.setMinimumHeight(36)
        self.setFont(QFont("Arial", 12, QFont.Weight.Medium))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 应用样式
        self._apply_styles()
    
    def _apply_styles(self):
        """应用按钮样式"""
        colors = ProfessionalTheme.get_colors(self.is_dark_theme)
        
        if self.button_type == "primary":
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['primary']};
                    color: white;
                    border: 1px solid {colors['primary']};
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-family: Arial, sans-serif;
                    font-size: 12px;
                    font-weight: 500;
                    min-height: 36px;
                    min-width: 100px;
                    text-align: center;
                }}
                QPushButton:hover {{
                    background-color: {colors['primary_hover']};
                    border-color: {colors['primary_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {colors['primary_active']};
                    border-color: {colors['primary_active']};
                }}
                QPushButton:disabled {{
                    background-color: {colors['text_disabled']};
                    border-color: {colors['text_disabled']};
                    color: white;
                }}
            """)
        elif self.button_type == "danger":
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['error']};
                    color: white;
                    border: 1px solid {colors['error']};
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-family: Arial, sans-serif;
                    font-size: 12px;
                    font-weight: 500;
                    min-height: 36px;
                    min-width: 100px;
                    text-align: center;
                }}
                QPushButton:hover {{
                    background-color: #ff7875;
                    border-color: #ff7875;
                }}
                QPushButton:pressed {{
                    background-color: #d9363e;
                    border-color: #d9363e;
                }}
            """)
        else:  # default
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['background']};
                    color: {colors['text_primary']};
                    border: 1px solid {colors['border']};
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-family: Arial, sans-serif;
                    font-size: 12px;
                    font-weight: 500;
                    min-height: 36px;
                    min-width: 100px;
                    text-align: center;
                }}
                QPushButton:hover {{
                    border-color: {colors['primary']};
                    color: {colors['primary']};
                }}
                QPushButton:pressed {{
                    border-color: {colors['primary_active']};
                    color: {colors['primary_active']};
                }}
                QPushButton:disabled {{
                    background-color: {colors['surface']};
                    border-color: {colors['border']};
                    color: {colors['text_disabled']};
                }}
            """)
    
    def set_theme(self, is_dark):
        """设置主题"""
        self.is_dark_theme = is_dark
        self._apply_styles()


class ProfessionalCard(QFrame):
    """专业卡片组件 - 解决布局问题"""
    
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.is_dark_theme = False
        
        # 设置基本属性
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # 创建布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 16, 20, 16)
        self.main_layout.setSpacing(12)
        
        # 标题
        if title:
            self.title_label = QLabel(title)
            title_font = QFont("Arial", 14, QFont.Weight.Bold)
            self.title_label.setFont(title_font)
            self.title_label.setWordWrap(True)
            self.title_label.setMinimumHeight(24)
            self.title_label.setContentsMargins(4, 4, 4, 4)
            self.main_layout.addWidget(self.title_label)
        
        # 内容区域
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)
        self.main_layout.addWidget(self.content_widget)
        
        # 应用样式
        self._apply_styles()
    
    def add_content(self, widget):
        """添加内容"""
        self.content_layout.addWidget(widget)

    def clear_content(self):
        """清空内容"""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
    
    def _apply_styles(self):
        """应用卡片样式"""
        colors = ProfessionalTheme.get_colors(self.is_dark_theme)
        
        self.setStyleSheet(f"""
            ProfessionalCard {{
                background-color: {colors['background']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
            }}
        """)
        
        if hasattr(self, 'title_label'):
            self.title_label.setStyleSheet(f"""
                color: {colors['text_primary']};
                font-family: Arial, sans-serif;
                font-size: 14px;
                font-weight: bold;
                padding: 4px;
            """)
    
    def set_theme(self, is_dark):
        """设置主题"""
        self.is_dark_theme = is_dark
        self._apply_styles()


class ProfessionalNavigation(QWidget):
    """专业导航组件 - 解决导航问题"""
    
    navigation_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark_theme = False
        self.current_page = "home"
        self.nav_buttons = {}
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """设置UI"""
        self.setFixedWidth(200)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(8)
        
        # 应用标题
        title_label = QLabel("VideoEpicCreator")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        
        # 导航按钮 - 移除视频编辑入口，整合到项目管理中
        nav_items = [
            ("home", "🏠 首页"),
            ("projects", "📁 项目管理"),
            ("settings", "⚙️ 设置")
        ]
        
        for item_id, text in nav_items:
            btn = ProfessionalButton(text, "default")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, id=item_id: self._on_nav_clicked(id))
            
            self.nav_buttons[item_id] = btn
            layout.addWidget(btn)
        
        # 弹性空间
        layout.addStretch()
        
        # 默认选中首页
        self.nav_buttons["home"].setChecked(True)
    
    def _on_nav_clicked(self, item_id):
        """导航点击处理"""
        # 取消其他按钮选中状态
        for btn_id, button in self.nav_buttons.items():
            button.setChecked(btn_id == item_id)
        
        self.current_page = item_id
        self.navigation_changed.emit(item_id)
    
    def _apply_styles(self):
        """应用导航样式"""
        colors = ProfessionalTheme.get_colors(self.is_dark_theme)
        
        self.setStyleSheet(f"""
            ProfessionalNavigation {{
                background-color: {colors['surface']};
                border-right: 1px solid {colors['border']};
            }}
            QLabel {{
                color: {colors['primary']};
                margin-bottom: 16px;
            }}
            QFrame {{
                background-color: {colors['border']};
                margin-bottom: 16px;
            }}
        """)
        
        # 更新按钮主题
        for button in self.nav_buttons.values():
            button.set_theme(self.is_dark_theme)
    
    def set_theme(self, is_dark):
        """设置主题"""
        self.is_dark_theme = is_dark
        self._apply_styles()
    
    def set_current_page(self, page_id):
        """设置当前页面"""
        if page_id in self.nav_buttons:
            self._on_nav_clicked(page_id)


class ProfessionalHomePage(QWidget):
    """专业首页 - 重新设计"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark_theme = False
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """设置UI"""
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 主内容
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(32)
        
        # 欢迎区域
        welcome_card = ProfessionalCard("欢迎使用 VideoEpicCreator")
        
        welcome_desc = QLabel("AI驱动的短剧视频编辑器，让创作更简单、更高效")
        welcome_desc.setFont(QFont("Arial", 14))
        welcome_desc.setWordWrap(True)
        welcome_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_card.add_content(welcome_desc)
        
        layout.addWidget(welcome_card)
        
        # 快速开始区域
        quick_start_card = ProfessionalCard("快速开始")
        
        # 快速操作按钮
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(16)
        
        new_project_btn = ProfessionalButton("📝 新建项目", "primary")
        import_video_btn = ProfessionalButton("📹 导入视频", "default")
        open_ai_btn = ProfessionalButton("🤖 AI功能", "default")
        
        actions_layout.addWidget(new_project_btn)
        actions_layout.addWidget(import_video_btn)
        actions_layout.addWidget(open_ai_btn)
        actions_layout.addStretch()
        
        actions_widget = QWidget()
        actions_widget.setLayout(actions_layout)
        quick_start_card.add_content(actions_widget)
        
        layout.addWidget(quick_start_card)
        
        # 功能介绍区域
        features_card = ProfessionalCard("核心功能")
        
        features_layout = QVBoxLayout()
        features_layout.setSpacing(16)
        
        features = [
            ("🎬 AI短剧解说", "智能生成适合短剧的解说内容"),
            ("⚡ AI高能混剪", "自动检测精彩片段并生成混剪"),
            ("🎭 AI第一人称独白", "生成第一人称叙述内容")
        ]
        
        for title, desc in features:
            feature_widget = QWidget()
            feature_layout = QVBoxLayout(feature_widget)
            feature_layout.setContentsMargins(16, 12, 16, 12)
            feature_layout.setSpacing(4)
            
            title_label = QLabel(title)
            title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            feature_layout.addWidget(title_label)
            
            desc_label = QLabel(desc)
            desc_label.setFont(QFont("Arial", 12))
            desc_label.setWordWrap(True)
            feature_layout.addWidget(desc_label)
            
            features_layout.addWidget(feature_widget)
        
        features_widget = QWidget()
        features_widget.setLayout(features_layout)
        features_card.add_content(features_widget)
        
        layout.addWidget(features_card)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
    
    def _apply_styles(self):
        """应用样式"""
        colors = ProfessionalTheme.get_colors(self.is_dark_theme)
        
        self.setStyleSheet(f"""
            ProfessionalHomePage {{
                background-color: {colors['surface']};
            }}
            QLabel {{
                color: {colors['text_primary']};
            }}
            QScrollArea {{
                border: none;
                background-color: {colors['surface']};
            }}
        """)
    
    def set_theme(self, is_dark):
        """设置主题"""
        self.is_dark_theme = is_dark
        self._apply_styles()
        
        # 更新所有卡片主题
        for card in self.findChildren(ProfessionalCard):
            card.set_theme(is_dark)
        
        # 更新所有按钮主题
        for button in self.findChildren(ProfessionalButton):
            button.set_theme(is_dark)
