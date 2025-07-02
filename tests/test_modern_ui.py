#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
现代化UI测试脚本
展示全新的大气时尚界面效果
"""

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QProgressBar, QListWidget, QListWidgetItem,
    QTabWidget, QLineEdit, QComboBox, QCheckBox, QSlider, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPixmap

class ModernUIDemo(QMainWindow):
    """现代化UI演示窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VideoEpicCreator - 现代化UI演示")
        self.setGeometry(100, 100, 1200, 800)
        
        # 加载现代化样式
        self.load_modern_style()
        
        # 创建界面
        self.create_ui()
        
        # 启动动画
        self.start_animations()
    
    def load_modern_style(self):
        """加载现代化样式"""
        style_path = "resources/styles/modern_style.qss"
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
            print("✅ 现代化样式加载成功")
        else:
            print("❌ 现代化样式文件不存在")
    
    def create_ui(self):
        """创建演示界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 左侧面板
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel)
        
        # 右侧面板
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel)
        
        # 设置比例
        main_layout.setStretch(0, 1)
        main_layout.setStretch(1, 4)
    
    def create_left_panel(self):
        """创建左侧演示面板"""
        panel = QWidget()
        panel.setObjectName("left_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 标题
        title = QLabel("现代化UI")
        title.setObjectName("app_title")
        layout.addWidget(title)
        
        # 导航按钮
        nav_buttons = ["项目管理", "视频编辑", "AI助手", "设置"]
        for i, btn_text in enumerate(nav_buttons):
            btn = QPushButton(btn_text)
            btn.setObjectName("nav_button")
            if i == 0:
                btn.setChecked(True)
            btn.setCheckable(True)
            layout.addWidget(btn)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("QFrame { background-color: #e5e7eb; height: 1px; }")
        layout.addWidget(separator)
        
        # 状态信息
        status_label = QLabel("AI模型: 智谱AI ✅\n讯飞星火 ✅\n腾讯混元 ✅")
        status_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        layout.addWidget(status_label)
        
        layout.addStretch()
        return panel
    
    def create_right_panel(self):
        """创建右侧演示面板"""
        panel = QWidget()
        panel.setObjectName("right_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题栏
        header = QHBoxLayout()
        title = QLabel("现代化界面演示")
        title.setStyleSheet("font-size: 24px; font-weight: 700; color: #1e40af;")
        header.addWidget(title)
        header.addStretch()
        
        action_btn = QPushButton("开始体验")
        action_btn.setObjectName("primary_button")
        header.addWidget(action_btn)
        
        layout.addLayout(header)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("QFrame { background-color: #e5e7eb; height: 1px; }")
        layout.addWidget(separator)
        
        # 标签页演示
        tab_widget = QTabWidget()
        
        # 组件演示标签页
        components_tab = self.create_components_demo()
        tab_widget.addTab(components_tab, "组件演示")
        
        # 列表演示标签页
        list_tab = self.create_list_demo()
        tab_widget.addTab(list_tab, "列表演示")
        
        # 表单演示标签页
        form_tab = self.create_form_demo()
        tab_widget.addTab(form_tab, "表单演示")
        
        layout.addWidget(tab_widget)
        
        return panel
    
    def create_components_demo(self):
        """创建组件演示"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # 按钮组
        btn_group = QGroupBox("按钮样式")
        btn_layout = QHBoxLayout(btn_group)
        
        primary_btn = QPushButton("主要按钮")
        primary_btn.setObjectName("primary_button")
        btn_layout.addWidget(primary_btn)
        
        secondary_btn = QPushButton("次要按钮")
        btn_layout.addWidget(secondary_btn)
        
        btn_layout.addStretch()
        layout.addWidget(btn_group)
        
        # 进度条
        progress_group = QGroupBox("进度条")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(65)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_group)
        
        # 滑块
        slider_group = QGroupBox("滑块控件")
        slider_layout = QVBoxLayout(slider_group)
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setValue(75)
        slider_layout.addWidget(slider)
        
        layout.addWidget(slider_group)
        
        layout.addStretch()
        return widget
    
    def create_list_demo(self):
        """创建列表演示"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        list_widget = QListWidget()
        
        items = [
            "🎬 项目1: 短剧制作",
            "🎥 项目2: 产品宣传片", 
            "📱 项目3: 社交媒体内容",
            "🎭 项目4: 教育视频",
            "🎪 项目5: 娱乐短片"
        ]
        
        for item_text in items:
            item = QListWidgetItem(item_text)
            list_widget.addItem(item)
        
        layout.addWidget(list_widget)
        return widget
    
    def create_form_demo(self):
        """创建表单演示"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        # 输入框
        input_group = QGroupBox("输入控件")
        input_layout = QVBoxLayout(input_group)
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("请输入项目名称...")
        input_layout.addWidget(name_input)
        
        # 下拉框
        combo = QComboBox()
        combo.addItems(["智谱AI", "讯飞星火", "腾讯混元", "DeepSeek"])
        input_layout.addWidget(combo)
        
        # 复选框
        checkbox = QCheckBox("启用AI自动优化")
        checkbox.setChecked(True)
        input_layout.addWidget(checkbox)
        
        layout.addWidget(input_group)
        layout.addStretch()
        
        return widget
    
    def start_animations(self):
        """启动动画效果"""
        # 进度条动画
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(100)
    
    def update_progress(self):
        """更新进度条"""
        current = self.progress_bar.value()
        if current >= 100:
            self.progress_bar.setValue(0)
        else:
            self.progress_bar.setValue(current + 1)

def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("VideoEpicCreator Modern UI Demo")
    
    # 创建演示窗口
    demo = ModernUIDemo()
    demo.show()
    
    print("🎨 现代化UI演示启动成功!")
    print("✨ 特色功能:")
    print("  • 大气时尚的渐变色设计")
    print("  • 现代化的组件样式")
    print("  • 流畅的交互体验")
    print("  • 紧凑精致的布局")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
