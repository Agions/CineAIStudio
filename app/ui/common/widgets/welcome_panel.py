"""
欢迎面板组件 - macOS 设计系统风格，使用 QSS 类名
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPixmap


class WelcomePanel(QWidget):
    """欢迎面板 - macOS 风格"""

    # 信号定义
    new_project_requested = pyqtSignal()
    open_project_requested = pyqtSignal()
    import_media_requested = pyqtSignal()
    learn_more_requested = pyqtSignal()

    def __init__(self):
        super().__init__()

        self._setup_ui()
        self._create_layout()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """设置UI - 使用 QSS 类名，零内联样式"""
        self.setObjectName("welcome_panel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # 应用 macOS 欢迎面板样式类
        self.setProperty("class", "welcome-panel")

        # 启用样式支持
        self.setAttribute(Qt.WA_StyledBackground, True)

    def _create_layout(self) -> None:
        """创建布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 创建标题区域
        title_layout = self._create_title_section()
        main_layout.addLayout(title_layout)

        # 创建功能区
        actions_layout = self._create_actions_section()
        main_layout.addLayout(actions_layout)

        # 创建特性展示区
        features_layout = self._create_features_section()
        main_layout.addLayout(features_layout)

        # 创建快速开始区
        quick_start_layout = self._create_quick_start_section()
        main_layout.addLayout(quick_start_layout)

        # 添加弹性空间
        main_layout.addStretch()

    def _create_title_section(self) -> QVBoxLayout:
        """创建标题区域 - 使用 QSS 类名"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo
        logo_label = QLabel("🎬")
        logo_label.setProperty("class", "welcome-logo")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        # 标题
        title_label = QLabel("欢迎使用 AI-EditX")
        title_label.setProperty("class", "welcome-title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 副标题
        subtitle_label = QLabel("专业AI视频编辑器 v2.0")
        subtitle_label.setProperty("class", "welcome-subtitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        return layout

    def _create_actions_section(self) -> QHBoxLayout:
        """创建功能区"""
        layout = QHBoxLayout()
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 创建操作按钮
        actions = [
            ("📄", "新建项目", "创建新的视频项目", self.new_project_requested),
            ("📂", "打开项目", "打开现有的视频项目", self.open_project_requested),
            ("📥", "导入媒体", "导入视频、音频或图片文件", self.import_media_requested),
            ("📚", "学习使用", "查看教程和文档", self.learn_more_requested)
        ]

        for icon, text, tooltip, signal in actions:
            button = self._create_action_button(icon, text, tooltip, signal)
            layout.addWidget(button)

        return layout

    def _create_action_button(self, icon: str, text: str, tooltip: str, signal) -> QPushButton:
        """创建操作按钮 - 使用 QSS 类名"""
        button = QPushButton()
        button.setFixedSize(120, 120)
        button.setToolTip(tooltip)
        button.clicked.connect(signal)

        # 应用 macOS 欢迎面板按钮样式类
        button.setProperty("class", "welcome-action-button")

        # 设置按钮布局
        button_layout = QVBoxLayout(button)
        button_layout.setContentsMargins(10, 10, 10, 10)
        button_layout.setSpacing(5)

        # 图标
        icon_label = QLabel(icon)
        icon_label.setProperty("class", "welcome-action-icon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.addWidget(icon_label)

        # 文本
        text_label = QLabel(text)
        text_label.setProperty("class", "welcome-action-text")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.addWidget(text_label)

        return button

    def _create_features_section(self) -> QVBoxLayout:
        """创建特性展示区 - 使用 QSS 类名"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        features_title = QLabel("✨ 主要功能")
        features_title.setProperty("class", "welcome-section-title")
        features_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(features_title)

        # 特性网格
        features_layout = self._create_features_grid()
        layout.addLayout(features_layout)

        return layout

    def _create_features_grid(self) -> QVBoxLayout:
        """创建特性网格"""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        features = [
            ("🤖", "AI驱动的视频处理", "智能分析、字幕生成、画质增强"),
            ("🎬", "专业级编辑功能", "多轨道时间线、特效、转场"),
            ("🎯", "剪映项目兼容", "完美支持剪映项目格式"),
            ("🌟", "国产大模型支持", "集成国内主流AI模型"),
            ("🎨", "现代化UI设计", "直观易用的用户界面"),
            ("⚡", "高性能渲染", "GPU加速，实时预览")
        ]

        for icon, title, description in features:
            feature_widget = self._create_feature_item(icon, title, description)
            layout.addWidget(feature_widget)

        return layout

    def _create_feature_item(self, icon: str, title: str, description: str) -> QWidget:
        """创建特性项 - 使用 QSS 类名"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        # 应用欢迎面板特性项样式
        widget.setProperty("class", "welcome-feature-item")

        # 图标
        icon_label = QLabel(icon)
        icon_label.setProperty("class", "welcome-feature-icon")
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # 文本区域
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        # 标题
        title_label = QLabel(title)
        title_label.setProperty("class", "welcome-feature-title")
        text_layout.addWidget(title_label)

        # 描述
        desc_label = QLabel(description)
        desc_label.setProperty("class", "welcome-feature-desc")
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)

        layout.addLayout(text_layout)
        layout.addStretch()

        return widget

    def _create_quick_start_section(self) -> QHBoxLayout:
        """创建快速开始区"""
        layout = QHBoxLayout()
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 快速开始按钮
        quick_actions = [
            ("📁", "打开文件夹", "浏览文件夹中的媒体文件"),
            ("🎥", "录制屏幕", "开始屏幕录制"),
            ("📷", "截图工具", "截取屏幕画面"),
            ("🎵", "音频编辑", "打开音频编辑器")
        ]

        for icon, text, tooltip in quick_actions:
            button = self._create_quick_button(icon, text, tooltip)
            layout.addWidget(button)

        return layout

    def _create_quick_button(self, icon: str, text: str, tooltip: str) -> QPushButton:
        """创建快速按钮 - 使用 QSS 类名"""
        button = QPushButton(text)
        button.setIconSize(QSize(16, 16))
        button.setToolTip(tooltip)

        # 应用 macOS 欢迎面板快速按钮样式类
        button.setProperty("class", "welcome-quick-button")

        return button

    def _connect_signals(self) -> None:
        """连接信号"""
        # 这里可以添加其他信号连接
        pass

    def update_theme(self, theme_name: str = "dark") -> None:
        """更新主题 - 使用 QSS 类名系统"""
        # 通过主题管理器更新主题样式
        self.setProperty("theme", theme_name)
        self.style().unpolish(self)
        self.style().polish(self)

        # 递归更新子组件主题
        for child in self.findChildren(QWidget):
            if hasattr(child, "update_theme"):
                child.update_theme(theme_name)

    def set_size_hint(self, width: int, height: int) -> None:
        """设置大小建议"""
        self.setMinimumSize(width, height)