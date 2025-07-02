#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon

from .theme_toggle import CompactThemeToggle


class NavigationButton(QPushButton):
    """导航按钮组件"""
    
    def __init__(self, text: str, icon: str = "", parent=None):
        super().__init__(parent)
        
        self.setText(text)
        self.setCheckable(True)
        self.setObjectName("nav_button")
        
        # 设置图标（如果提供）
        if icon:
            self.icon_text = icon
            self._update_display_text()
        
        # 设置按钮属性
        self.setMinimumHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # 设置样式
        self._apply_styles()
    
    def _update_display_text(self):
        """更新显示文本"""
        if hasattr(self, 'icon_text'):
            display_text = f"{self.icon_text}  {self.text()}"
            super().setText(display_text)
    
    def setText(self, text: str):
        """设置文本"""
        self._original_text = text
        if hasattr(self, 'icon_text'):
            self._update_display_text()
        else:
            super().setText(text)
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QPushButton#nav_button {
                background-color: transparent;
                border: none;
                border-radius: 8px;
                color: #262626;
                padding: 12px 16px;
                text-align: left;
                font-weight: 500;
                font-size: 14px;
                margin: 2px 8px;
            }
            
            QPushButton#nav_button:hover {
                background-color: #f5f5f5;
                color: #1890ff;
            }
            
            QPushButton#nav_button:checked {
                background-color: #e6f7ff;
                color: #1890ff;
                font-weight: 600;
                border-left: 3px solid #1890ff;
            }
        """)


class ModernNavigation(QWidget):
    """现代化导航组件"""
    
    # 信号
    navigation_changed = pyqtSignal(str)  # 导航变更信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_page = "home"
        self.nav_buttons = {}
        
        self._setup_ui()
        self._setup_navigation_items()
        self._apply_styles()
    
    def _setup_ui(self):
        """设置UI"""
        self.setObjectName("left_panel")
        self.setMinimumWidth(200)
        self.setMaximumWidth(250)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 应用标题区域
        self.header_widget = self._create_header()
        layout.addWidget(self.header_widget)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("QFrame { color: #f0f0f0; }")
        layout.addWidget(separator)
        
        # 导航区域
        self.nav_widget = QWidget()
        self.nav_layout = QVBoxLayout(self.nav_widget)
        self.nav_layout.setContentsMargins(0, 16, 0, 16)
        self.nav_layout.setSpacing(4)
        layout.addWidget(self.nav_widget)
        
        # 弹性空间
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layout.addItem(spacer)
        
        # 底部工具区域
        self.footer_widget = self._create_footer()
        layout.addWidget(self.footer_widget)
    
    def _create_header(self) -> QWidget:
        """创建头部区域"""
        header = QWidget()
        layout = QVBoxLayout(header)
        layout.setContentsMargins(16, 16, 16, 8)
        layout.setSpacing(4)
        
        # 应用标题
        title_label = QLabel("VideoEpicCreator")
        title_label.setObjectName("app_title")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # 副标题
        subtitle_label = QLabel("AI短剧视频编辑器")
        subtitle_label.setStyleSheet("color: #595959; font-size: 12px;")
        layout.addWidget(subtitle_label)
        
        return header
    
    def _create_footer(self) -> QWidget:
        """创建底部区域"""
        footer = QWidget()
        layout = QVBoxLayout(footer)
        layout.setContentsMargins(16, 8, 16, 16)
        layout.setSpacing(8)
        
        # 主题切换
        theme_toggle = CompactThemeToggle()
        theme_toggle_layout = QHBoxLayout()
        theme_toggle_layout.addWidget(QLabel("主题:"))
        theme_toggle_layout.addWidget(theme_toggle)
        theme_toggle_layout.addStretch()
        
        theme_widget = QWidget()
        theme_widget.setLayout(theme_toggle_layout)
        layout.addWidget(theme_widget)
        
        return footer
    
    def _setup_navigation_items(self):
        """设置导航项目"""
        nav_items = [
            ("home", "🏠", "首页"),
            ("projects", "🎬", "项目管理"),
            ("ai_features", "🤖", "AI功能"),
            ("settings", "⚙️", "设置")
        ]
        
        for item_id, icon, text in nav_items:
            button = NavigationButton(text, icon)
            button.clicked.connect(lambda checked, id=item_id: self._on_nav_clicked(id))
            
            self.nav_buttons[item_id] = button
            self.nav_layout.addWidget(button)
        
        # 默认选中首页
        self.nav_buttons["home"].setChecked(True)
    
    def _on_nav_clicked(self, item_id: str):
        """导航点击处理"""
        # 取消其他按钮的选中状态
        for btn_id, button in self.nav_buttons.items():
            button.setChecked(btn_id == item_id)
        
        # 更新当前页面
        self.current_page = item_id
        
        # 发射信号
        self.navigation_changed.emit(item_id)
    
    def set_current_page(self, page_id: str):
        """设置当前页面"""
        if page_id in self.nav_buttons:
            self._on_nav_clicked(page_id)
    
    def get_current_page(self) -> str:
        """获取当前页面"""
        return self.current_page
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QWidget#left_panel {
                background-color: #ffffff;
                border-right: 1px solid #f0f0f0;
            }
            
            QLabel#app_title {
                color: #1890ff;
                font-weight: 600;
            }
            
            QFrame {
                border: none;
                background-color: #f0f0f0;
                max-height: 1px;
            }
        """)
    
    def update_theme_styles(self, is_dark: bool):
        """更新主题样式"""
        if is_dark:
            # 深色主题样式
            self.setStyleSheet("""
                QWidget#left_panel {
                    background-color: #1f1f1f;
                    border-right: 1px solid #434343;
                }
                
                QLabel#app_title {
                    color: #177ddc;
                    font-weight: 600;
                }
                
                QFrame {
                    border: none;
                    background-color: #434343;
                    max-height: 1px;
                }
            """)
            
            # 更新导航按钮样式
            for button in self.nav_buttons.values():
                button.setStyleSheet("""
                    QPushButton#nav_button {
                        background-color: transparent;
                        border: none;
                        border-radius: 8px;
                        color: #ffffff;
                        padding: 12px 16px;
                        text-align: left;
                        font-weight: 500;
                        font-size: 14px;
                        margin: 2px 8px;
                    }
                    
                    QPushButton#nav_button:hover {
                        background-color: #262626;
                        color: #177ddc;
                    }
                    
                    QPushButton#nav_button:checked {
                        background-color: #111b26;
                        color: #177ddc;
                        font-weight: 600;
                        border-left: 3px solid #177ddc;
                    }
                """)
        else:
            # 浅色主题样式
            self._apply_styles()
            for button in self.nav_buttons.values():
                button._apply_styles()


class CompactNavigation(QWidget):
    """紧凑型导航组件（仅图标）"""
    
    navigation_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_page = "home"
        self.nav_buttons = {}
        
        self._setup_ui()
        self._setup_navigation_items()
        self._apply_styles()
    
    def _setup_ui(self):
        """设置UI"""
        self.setObjectName("compact_nav_panel")
        self.setFixedWidth(60)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(8)
        
        # 应用图标
        app_icon = QLabel("🎬")
        app_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_icon.setStyleSheet("font-size: 24px; padding: 8px;")
        layout.addWidget(app_icon)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # 导航按钮区域
        self.nav_layout = QVBoxLayout()
        self.nav_layout.setSpacing(4)
        layout.addLayout(self.nav_layout)
        
        # 弹性空间
        layout.addStretch()
        
        # 主题切换
        theme_toggle = CompactThemeToggle()
        layout.addWidget(theme_toggle)
    
    def _setup_navigation_items(self):
        """设置导航项目"""
        nav_items = [
            ("home", "🏠"),
            ("projects", "🎬"),
            ("ai_features", "🤖"),
            ("settings", "⚙️")
        ]
        
        for item_id, icon in nav_items:
            button = QPushButton(icon)
            button.setCheckable(True)
            button.setFixedSize(44, 44)
            button.setObjectName("compact_nav_button")
            button.clicked.connect(lambda checked, id=item_id: self._on_nav_clicked(id))
            
            self.nav_buttons[item_id] = button
            self.nav_layout.addWidget(button)
        
        # 默认选中首页
        self.nav_buttons["home"].setChecked(True)
    
    def _on_nav_clicked(self, item_id: str):
        """导航点击处理"""
        for btn_id, button in self.nav_buttons.items():
            button.setChecked(btn_id == item_id)
        
        self.current_page = item_id
        self.navigation_changed.emit(item_id)
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QWidget#compact_nav_panel {
                background-color: #ffffff;
                border-right: 1px solid #f0f0f0;
            }
            
            QPushButton#compact_nav_button {
                background-color: transparent;
                border: none;
                border-radius: 22px;
                font-size: 18px;
            }
            
            QPushButton#compact_nav_button:hover {
                background-color: #f5f5f5;
            }
            
            QPushButton#compact_nav_button:checked {
                background-color: #e6f7ff;
                color: #1890ff;
            }
        """)
