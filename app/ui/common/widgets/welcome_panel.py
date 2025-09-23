"""
欢迎面板组件
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPixmap


class WelcomePanel(QWidget):
    """欢迎面板"""

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
        """设置UI"""
        self.setObjectName("welcome_panel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # 设置背景色
        self.setStyleSheet("""
            QWidget#welcome_panel {
                background-color: #1E1E1E;
                border-radius: 8px;
            }
        """)

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
        """创建标题区域"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo
        logo_label = QLabel("🎬")
        logo_label.setStyleSheet("font-size: 64px;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        # 标题
        title_label = QLabel("欢迎使用 CineAIStudio")
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 28px;
                font-weight: bold;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 副标题
        subtitle_label = QLabel("专业AI视频编辑器 v2.0")
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-size: 16px;
            }
        """)
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
        """创建操作按钮"""
        button = QPushButton()
        button.setFixedSize(120, 120)
        button.setToolTip(tooltip)
        button.clicked.connect(signal)

        # 设置按钮样式
        button.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 2px solid #404040;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
                border-color: #2196F3;
            }
            QPushButton:pressed {
                background-color: #2196F3;
            }
        """)

        # 设置按钮布局
        button_layout = QVBoxLayout(button)
        button_layout.setContentsMargins(10, 10, 10, 10)
        button_layout.setSpacing(5)

        # 图标
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 32px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.addWidget(icon_label)

        # 文本
        text_label = QLabel(text)
        text_label.setStyleSheet("color: #FFFFFF; font-size: 12px;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.addWidget(text_label)

        return button

    def _create_features_section(self) -> QVBoxLayout:
        """创建特性展示区"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        features_title = QLabel("✨ 主要功能")
        features_title.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 20px;
                font-weight: bold;
            }
        """)
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
        """创建特性项"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        # 图标
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # 文本区域
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        text_layout.addWidget(title_label)

        # 描述
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-size: 12px;
            }
        """)
        desc_label.setWordWrap(True)
        text_layout.addWidget(desc_label)

        layout.addLayout(text_layout)
        layout.addStretch()

        # 设置样式
        widget.setStyleSheet("""
            QWidget {
                background-color: #2D2D2D;
                border-radius: 6px;
            }
            QWidget:hover {
                background-color: #3D3D3D;
            }
        """)

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
        """创建快速按钮"""
        button = QPushButton(text)
        button.setIconSize(QSize(16, 16))
        button.setToolTip(tooltip)

        button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #2196F3;
                border: 1px solid #2196F3;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(33, 150, 243, 0.1);
                color: #FFFFFF;
            }
        """)

        return button

    def _connect_signals(self) -> None:
        """连接信号"""
        # 这里可以添加其他信号连接
        pass

    def update_theme(self, is_dark: bool = True) -> None:
        """更新主题"""
        if is_dark:
            bg_color = "#1E1E1E"
            text_color = "#FFFFFF"
            secondary_color = "#CCCCCC"
        else:
            bg_color = "#FFFFFF"
            text_color = "#000000"
            secondary_color = "#666666"

        self.setStyleSheet(f"""
            QWidget#welcome_panel {{
                background-color: {bg_color};
                border-radius: 8px;
            }}
        """)

        # 更新标题颜色
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if isinstance(item.widget(), QLabel):
                label = item.widget()
                if "欢迎使用" in label.text():
                    label.setStyleSheet(f"color: {text_color}; font-size: 28px; font-weight: bold;")
                elif "CineAIStudio" in label.text():
                    label.setStyleSheet(f"color: {secondary_color}; font-size: 16px;")
                elif "主要功能" in label.text():
                    label.setStyleSheet(f"color: {text_color}; font-size: 20px; font-weight: bold;")

    def set_size_hint(self, width: int, height: int) -> None:
        """设置大小建议"""
        self.setMinimumSize(width, height)