#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 帮助系统
提供用户引导、帮助文档和交互式教程
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser,
    QPushButton, QListWidget, QListWidgetItem, QSplitter,
    QStackedWidget, QFrame, QDialog, QScrollArea, QGroupBox,
    QProgressBar, QTreeWidget, QTreeWidgetItem, QApplication,
    QMessageBox, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer, QUrl
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPainter, QColor, QBrush

from ...core.icon_manager import get_icon
from ...utils.file_error_handler import FileOperationError


class HelpCategory(Enum):
    """帮助类别"""
    GETTING_STARTED = "getting_started"
    BASIC_TUTORIALS = "basic_tutorials"
    ADVANCED_FEATURES = "advanced_features"
    AI_FEATURES = "ai_features"
    EXPORT_GUIDES = "export_guides"
    TROUBLESHOOTING = "troubleshooting"
    FAQ = "faq"
    KEYBOARD_SHORTCUTS = "keyboard_shortcuts"


@dataclass
class HelpTopic:
    """帮助主题"""
    id: str
    title: str
    category: HelpCategory
    content: str
    difficulty: str = "beginner"  # beginner, intermediate, advanced
    estimated_time: int = 5  # 分钟
    related_topics: List[str] = None
    code_examples: List[Dict[str, str]] = None
    screenshots: List[str] = None

    def __post_init__(self):
        if self.related_topics is None:
            self.related_topics = []
        if self.code_examples is None:
            self.code_examples = []
        if self.screenshots is None:
            self.screenshots = []


class HelpSystem(QWidget):
    """帮助系统主界面"""

    help_requested = pyqtSignal(str)
    tutorial_started = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_topic: Optional[HelpTopic] = None
        self.help_topics: Dict[str, HelpTopic] = {}
        self.tutorial_progress: Dict[str, float] = {}
        self.setup_ui()
        self.load_help_content()

    def setup_ui(self):
        """设置用户界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # 左侧导航面板
        left_panel = self.create_navigation_panel()
        splitter.addWidget(left_panel)

        # 右侧内容面板
        right_panel = self.create_content_panel()
        splitter.addWidget(right_panel)

        # 设置分割器比例
        splitter.setSizes([300, 700])

        # 设置样式
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
            }

            QListWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }

            QListWidget::item {
                padding: 8px;
                margin: 2px;
                border-radius: 4px;
            }

            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }

            QTextBrowser {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 15px;
                font-size: 14px;
                line-height: 1.6;
            }

            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #106ebe;
            }

            QPushButton:pressed {
                background-color: #005a9e;
            }

            QTreeWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
            }

            QTreeWidget::item {
                padding: 5px;
            }

            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
                background-color: #f0f0f0;
            }

            QProgressBar::chunk {
                background-color: #0078d4;
            }
        """)

    def create_navigation_panel(self) -> QWidget:
        """创建导航面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # 搜索框
        search_label = QLabel("搜索帮助:")
        search_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(search_label)

        # 搜索框占位符
        search_placeholder = QLabel("🔍 输入关键词搜索...")
        search_placeholder.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(search_placeholder)

        # 帮助分类树
        category_tree = QTreeWidget()
        category_tree.setHeaderLabel("帮助分类")
        category_tree.setMaximumHeight(300)
        layout.addWidget(category_tree)

        # 快速访问
        quick_access_label = QLabel("快速访问:")
        quick_access_label.setStyleSheet("font-weight: bold; margin-top: 10px; margin-bottom: 5px;")
        layout.addWidget(quick_access_label)

        # 快速访问列表
        self.quick_access_list = QListWidget()
        self.quick_access_list.setMaximumHeight(200)
        self.quick_access_list.itemClicked.connect(self.on_quick_access_clicked)
        layout.addWidget(self.quick_access_list)

        # 学习进度
        progress_label = QLabel("学习进度:")
        progress_label.setStyleSheet("font-weight: bold; margin-top: 10px; margin-bottom: 5px;")
        layout.addWidget(progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # 展开/折叠按钮
        expand_button = QPushButton("展开所有")
        expand_button.clicked.connect(lambda: category_tree.expandAll())
        layout.addWidget(expand_button)

        collapse_button = QPushButton("折叠所有")
        collapse_button.clicked.connect(lambda: category_tree.collapseAll())
        layout.addWidget(collapse_button)

        layout.addStretch()

        # 初始化分类树
        self.init_category_tree(category_tree)

        return panel

    def create_content_panel(self) -> QWidget:
        """创建内容面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题栏
        title_bar = QHBoxLayout()

        self.topic_title = QLabel("欢迎使用 CineAIStudio 帮助")
        self.topic_title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
            }
        """)
        title_bar.addWidget(self.topic_title)
        title_bar.addStretch()

        # 难度和时间标签
        self.difficulty_label = QLabel()
        self.difficulty_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                color: #1976d2;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        title_bar.addWidget(self.difficulty_label)

        self.time_label = QLabel()
        self.time_label.setStyleSheet("""
            QLabel {
                background-color: #f3e5f5;
                color: #7b1fa2;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        title_bar.addWidget(self.time_label)

        layout.addLayout(title_bar)

        # 工具栏
        toolbar = QHBoxLayout()

        back_button = QPushButton("← 返回")
        back_button.clicked.connect(self.go_back)
        toolbar.addWidget(back_button)

        forward_button = QPushButton("前进 →")
        forward_button.clicked.connect(self.go_forward)
        toolbar.addWidget(forward_button)

        toolbar.addStretch()

        home_button = QPushButton("🏠 首页")
        home_button.clicked.connect(self.go_home)
        toolbar.addWidget(home_button)

        tutorial_button = QPushButton("🎯 开始教程")
        tutorial_button.clicked.connect(self.start_tutorial)
        toolbar.addWidget(tutorial_button)

        layout.addLayout(toolbar)

        # 内容浏览器
        self.content_browser = QTextBrowser()
        self.content_browser.setOpenLinks(False)
        self.content_browser.anchorClicked.connect(self.on_link_clicked)
        layout.addWidget(self.content_browser)

        # 相关主题
        related_label = QLabel("相关主题:")
        related_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(related_label)

        self.related_list = QListWidget()
        self.related_list.setMaximumHeight(100)
        self.related_list.itemClicked.connect(self.on_related_topic_clicked)
        layout.addWidget(self.related_list)

        return panel

    def init_category_tree(self, tree: QTreeWidget):
        """初始化分类树"""
        # 添加根节点
        categories = {
            "新手入门": HelpCategory.GETTING_STARTED,
            "基础教程": HelpCategory.BASIC_TUTORIALS,
            "高级功能": HelpCategory.ADVANCED_FEATURES,
            "AI功能": HelpCategory.AI_FEATURES,
            "导出指南": HelpCategory.EXPORT_GUIDES,
            "故障排除": HelpCategory.TROUBLESHOOTING,
            "常见问题": HelpCategory.FAQ,
            "快捷键": HelpCategory.KEYBOARD_SHORTCUTS
        }

        self.category_items = {}

        for category_name, category_enum in categories.items():
            item = QTreeWidgetItem([category_name])
            item.setIcon(0, get_icon("help"))
            self.category_items[category_enum] = item
            tree.addTopLevelItem(item)

        tree.itemClicked.connect(self.on_category_clicked)

    def load_help_content(self):
        """加载帮助内容"""
        # 创建基础帮助主题
        help_topics_data = [
            {
                "id": "welcome",
                "title": "欢迎使用 CineAIStudio",
                "category": HelpCategory.GETTING_STARTED,
                "content": self.get_welcome_content(),
                "difficulty": "beginner",
                "estimated_time": 3
            },
            {
                "id": "first_project",
                "title": "创建第一个项目",
                "category": HelpCategory.GETTING_STARTED,
                "content": self.get_first_project_content(),
                "difficulty": "beginner",
                "estimated_time": 5
            },
            {
                "id": "import_media",
                "title": "导入媒体文件",
                "category": HelpCategory.BASIC_TUTORIALS,
                "content": self.get_import_media_content(),
                "difficulty": "beginner",
                "estimated_time": 8
            },
            {
                "id": "timeline_editing",
                "title": "时间线编辑基础",
                "category": HelpCategory.BASIC_TUTORIALS,
                "content": self.get_timeline_editing_content(),
                "difficulty": "intermediate",
                "estimated_time": 15
            },
            {
                "id": "ai_features",
                "title": "AI智能功能使用",
                "category": HelpCategory.AI_FEATURES,
                "content": self.get_ai_features_content(),
                "difficulty": "intermediate",
                "estimated_time": 12
            },
            {
                "id": "export_projects",
                "title": "项目导出设置",
                "category": HelpCategory.EXPORT_GUIDES,
                "content": self.get_export_content(),
                "difficulty": "intermediate",
                "estimated_time": 10
            },
            {
                "id": "troubleshooting",
                "title": "常见问题解决",
                "category": HelpCategory.TROUBLESHOOTING,
                "content": self.get_troubleshooting_content(),
                "difficulty": "beginner",
                "estimated_time": 8
            },
            {
                "id": "keyboard_shortcuts",
                "title": "键盘快捷键",
                "category": HelpCategory.KEYBOARD_SHORTCUTS,
                "content": self.get_keyboard_shortcuts_content(),
                "difficulty": "beginner",
                "estimated_time": 5
            }
        ]

        # 创建帮助主题对象
        for topic_data in help_topics_data:
            topic = HelpTopic(**topic_data)
            self.help_topics[topic.id] = topic

        # 更新快速访问列表
        self.update_quick_access()

        # 显示欢迎页面
        self.show_topic("welcome")

    def update_quick_access(self):
        """更新快速访问列表"""
        self.quick_access_list.clear()

        # 添加常用主题
        common_topics = [
            "welcome", "first_project", "import_media",
            "timeline_editing", "ai_features", "export_projects"
        ]

        for topic_id in common_topics:
            if topic_id in self.help_topics:
                topic = self.help_topics[topic_id]
                item = QListWidgetItem(topic.title)
                item.setData(Qt.ItemDataRole.UserRole, topic_id)
                self.quick_access_list.addItem(item)

    def get_welcome_content(self) -> str:
        """获取欢迎内容"""
        return """
        <h1>🎬 欢迎使用 CineAIStudio v2.0</h1>

        <p>CineAIStudio 是一款专业级的人工智能视频编辑软件，集成了先进的AI技术和直观的用户界面，让您能够轻松创建专业品质的视频内容。</p>

        <h2>✨ 主要特性</h2>
        <ul>
            <li><strong>智能AI辅助</strong>：集成多种AI模型，提供智能剪辑、字幕生成、内容优化等功能</li>
            <li><strong>专业时间线</strong>：多轨道时间线编辑，支持视频、音频、图像等多种媒体类型</li>
            <li><strong>丰富的效果</strong>：内置专业级转场、滤镜、特效和动画效果</li>
            <li><strong>高性能导出</strong>：支持多种格式导出，GPU加速，批量处理</li>
            <li><strong>项目管理</strong>：完整的项目保存、加载、版本控制功能</li>
        </ul>

        <h2>🚀 快速开始</h2>
        <ol>
            <li>点击"新建项目"创建您的第一个视频项目</li>
            <li>导入您的媒体文件（视频、音频、图像）</li>
            <li>在时间线上排列和编辑您的素材</li>
            <li>添加转场、效果和AI增强功能</li>
            <li>预览并导出您的最终作品</li>
        </ol>

        <h2>📚 学习路径</h2>
        <p>我们建议您按照以下顺序学习使用 CineAIStudio：</p>
        <ol>
            <li><a href="#first_project">创建第一个项目</a></li>
            <li><a href="#import_media">导入媒体文件</a></li>
            <li><a href="#timeline_editing">时间线编辑基础</a></li>
            <li><a href="#ai_features">AI功能使用</a></li>
            <li><a href="#export_projects">导出设置</a></li>
        </ol>

        <div style="background-color: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3>💡 提示</h3>
            <p>随时可以按 F1 键或点击帮助按钮打开此帮助系统。如果您在使用过程中遇到问题，请查看<a href="#troubleshooting">故障排除</a>部分。</p>
        </div>
        """

    def get_first_project_content(self) -> str:
        """获取第一个项目内容"""
        return """
        <h1>🎯 创建第一个项目</h1>

        <p>本教程将指导您创建第一个 CineAIStudio 项目。</p>

        <h2>📝 步骤 1：创建新项目</h2>
        <ol>
            <li>启动 CineAIStudio</li>
            <li>在欢迎界面点击"新建项目"按钮</li>
            <li>或者使用菜单：<strong>文件 → 新建项目</strong></li>
            <li>项目设置：
                <ul>
                    <li><strong>项目名称</strong>：为您的项目起一个描述性的名称</li>
                    <li><strong>项目位置</strong>：选择保存项目的文件夹</li>
                    <li><strong>视频设置</strong>：选择分辨率（如 1920x1080）</li>
                    <li><strong>帧率</strong>：通常选择 24、25、30 或 60 fps</li>
                </ul>
            </li>
            <li>点击"创建"按钮</li>
        </ol>

        <h2>📁 项目结构</h2>
        <p>创建项目后，CineAIStudio 会自动创建以下文件夹结构：</p>
        <pre>
        MyProject/
        ├── MyProject.cineproj     # 项目文件
        ├── media/                # 媒体文件
        ├── cache/                # 缓存文件
        ├── exports/              # 导出文件
        └── autosave/            # 自动保存文件
        </pre>

        <h2>⚙️ 项目设置</h2>
        <p>您可以通过以下方式修改项目设置：</p>
        <ul>
            <li><strong>项目 → 项目设置</strong></li>
            <li>右键点击项目面板中的项目名称</li>
            <li>使用快捷键 <kbd>Ctrl+Shift+P</kbd>（Windows）或 <kbd>Cmd+Shift+P</kbd>（Mac）</li>
        </ul>

        <h2>💾 保存和自动保存</h2>
        <p>CineAIStudio 提供多种保存选项：</p>
        <ul>
            <li><strong>手动保存</strong>：<kbd>Ctrl+S</kbd> 或 <kbd>Cmd+S</kbd></li>
            <li><strong>另存为</strong>：<kbd>Ctrl+Shift+S</kbd> 或 <kbd>Cmd+Shift+S</kbd></li>
            <li><strong>自动保存</strong>：每 5 分钟自动保存一次</li>
            <li><strong>版本控制</strong>：支持保存项目版本快照</li>
        </ul>

        <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3>⚠️ 注意</h3>
            <p>定期保存您的工作！虽然 CineAIStudio 有自动保存功能，但建议您在重要操作后手动保存项目。</p>
        </div>

        <h2>🎉 恭喜！</h2>
        <p>您已经成功创建了第一个项目！接下来，让我们学习如何<a href="#import_media">导入媒体文件</a>。</p>
        """

    def get_import_media_content(self) -> str:
        """获取导入媒体文件内容"""
        return """
        <h1>📥 导入媒体文件</h1>

        <p>导入媒体文件是视频编辑的第一步。CineAIStudio 支持多种媒体格式。</p>

        <h2>🎬 支持的格式</h2>

        <h3>视频格式</h3>
        <ul>
            <li><strong>MP4</strong>：H.264/H.265 编码，推荐格式</li>
            <li><strong>MOV</strong>：Apple QuickTime 格式</li>
            <li><strong>AVI</strong>：标准视频格式</li>
            <li><strong>WMV</strong>：Windows Media Video</li>
            <li><strong>FLV</strong>：Flash 视频</li>
            <li><strong>WebM</strong>：网页视频格式</li>
        </ul>

        <h3>音频格式</h3>
        <ul>
            <li><strong>MP3</strong>：常用音频格式</li>
            <li><strong>WAV</strong>：无损音频格式</li>
            <li><strong>FLAC</strong>：无损压缩音频</li>
            <li><strong>AAC</strong>：高级音频编码</li>
            <li><strong>OGG</strong>：开放音频格式</li>
        </ul>

        <h3>图像格式</h3>
        <ul>
            <li><strong>JPG/JPEG</strong>：常用图像格式</li>
            <li><strong>PNG</strong>：支持透明度的图像格式</li>
            <li><strong>BMP</strong>：位图格式</li>
            <li><strong>TIFF</strong>：高质量图像格式</li>
            <li><strong>WebP</strong>：现代图像格式</li>
        </ul>

        <h2>📂 导入方法</h2>

        <h3>方法 1：拖放导入</h3>
        <ol>
            <li>打开文件管理器</li>
            <li>选择要导入的文件</li>
            <li>直接拖放到 CineAIStudio 的媒体库面板中</li>
        </ol>

        <h3>方法 2：菜单导入</h3>
        <ol>
            <li>点击菜单：<strong>文件 → 导入媒体</strong></li>
            <li>选择要导入的文件</li>
            <li>点击"打开"按钮</li>
        </ol>

        <h3>方法 3：工具栏导入</h3>
        <ol>
            <li>点击媒体库面板中的"导入"按钮</li>
            <li>选择要导入的文件</li>
            <li>点击"打开"按钮</li>
        </ol>

        <h3>方法 4：文件夹导入</h3>
        <ol>
            <li>右键点击媒体库面板</li>
            <li>选择"导入文件夹"</li>
            <li>选择包含媒体文件的文件夹</li>
            <li>点击"确定"按钮</li>
        </ol>

        <h2>🗂️ 媒体管理</h2>

        <h3>媒体库组织</h3>
        <p>导入的文件会自动分类到媒体库中：</p>
        <ul>
            <li><strong>视频</strong>：所有视频文件</li>
            <li><strong>音频</strong>：所有音频文件</li>
            <li><strong>图像</strong>：所有图像文件</li>
            <li><strong>序列</strong>：图像序列文件</li>
        </ul>

        <h3>媒体预览</h3>
        <p>在媒体库中：</p>
        <ul>
            <li>双击文件可以在预览窗口中播放</li>
            <li>悬停鼠标可以查看文件信息</li>
            <li>右键点击可以查看更多选项</li>
        </ul>

        <h3>文件操作</h3>
        <ul>
            <li><strong>重命名</strong>：右键点击 → 重命名</li>
            <li><strong>删除</strong>：右键点击 → 删除</li>
            <li><strong>复制</strong>：右键点击 → 复制</li>
            <li><strong>移动到文件夹</strong>：拖放到文件夹中</li>
        </ul>

        <div style="background-color: #d1ecf1; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3>💡 专业提示</h3>
            <ul>
                <li>在导入前组织好您的文件结构</li>
                <li>使用有意义的文件名</li>
                <li>大型项目建议按场景或类型组织文件</li>
                <li>定期清理不需要的媒体文件以节省空间</li>
            </ul>
        </div>

        <h2>🔧 高级导入选项</h2>

        <h3>批量导入设置</h3>
        <p>在导入对话框中可以设置：</p>
        <ul>
            <li><strong>创建代理</strong>：为高分辨率文件创建低分辨率代理</li>
            <li><strong>生成缩略图</strong>：自动生成文件缩略图</li>
            <li><strong>音频波形</strong>：为音频文件生成波形图</li>
            <li><strong>颜色分析</strong>：自动分析视频颜色信息</li>
        </ul>

        <h3>导入预设</h3>
        <p>可以保存常用的导入设置为预设，方便下次使用。</p>

        <h2>🎉 下一步</h2>
        <p>现在您已经导入了媒体文件，让我们学习<a href="#timeline_editing">时间线编辑基础</a>。</p>
        """

    def get_timeline_editing_content(self) -> str:
        """获取时间线编辑内容"""
        return """
        <h1>⏱️ 时间线编辑基础</h1>

        <p>时间线是视频编辑的核心区域，在这里您可以排列、修剪和组合您的媒体素材。</p>

        <h2>🎬 时间线界面</h2>

        <h3>主要组件</h3>
        <ul>
            <li><strong>时间标尺</strong>：显示时间刻度和标记</li>
            <li><strong>轨道区域</strong>：包含视频、音频、图像等轨道</li>
            <li><strong>播放头</strong>：指示当前播放位置</li>
            <li><strong>轨道控制</strong>：管理轨道的显示和锁定</li>
            <li><strong>缩放控制</strong>：调整时间线显示比例</li>
        </ul>

        <h3>轨道类型</h3>
        <ul>
            <li><strong>视频轨道</strong>：用于放置视频和图像素材</li>
            <li><strong>音频轨道</strong>：用于放置音频素材</li>
            <li><strong>字幕轨道</strong>：用于添加字幕和文本</li>
            <li><strong>效果轨道</strong>：用于应用全局效果</li>
        </ul>

        <h2>🎯 基本编辑操作</h2>

        <h3>添加素材到时间线</h3>
        <ol>
            <li>从媒体库中选择素材</li>
            <li>拖放到时间线的合适轨道上</li>
            <li>或者双击素材自动添加到时间线</li>
        </ol>

        <h3>移动素材</h3>
        <ul>
            <li>点击并拖动素材到新位置</li>
            <li>按住 <kbd>Shift</kbd> 键可以水平移动</li>
            <li>按住 <kbd>Ctrl</kbd> 键可以复制素材</li>
        </ul>

        <h3>修剪素材</h3>
        <ul>
            <li><strong>开始修剪</strong>：拖动素材的左边缘</li>
            <li><strong>结束修剪</strong>：拖动素材的右边缘</li>
            <li><strong>精确修剪</strong>：使用修剪工具或快捷键</li>
            <li><strong>波纹编辑</strong>：按住 <kbd>Ctrl</kbd> 键修剪会移动后续素材</li>
        </ul>

        <h3>分割素材</h3>
        <ol>
            <li>将播放头移动到要分割的位置</li>
            <li>选择要分割的素材</li>
            <li>点击分割工具或按 <kbd>C</kbd> 键</li>
            <li>或者右键点击选择"分割"</li>
        </ol>

        <h2>🔧 高级编辑技巧</h2>

        <h3>三点和四点编辑</h3>
        <p><strong>三点编辑</strong>：定义源素材的开始和结束，以及时间线上的插入点。</p>
        <p><strong>四点编辑</strong>：同时定义源素材和时间线的开始和结束点。</p>

        <h3>嵌套序列</h3>
        <ul>
            <li>将多个素材组合成序列</li>
            <li>序列可以像普通素材一样使用</li>
            <li>支持复杂的多层嵌套</li>
        </ul>

        <h3>标记和注释</h3>
        <ul>
            <li>添加标记：按 <kbd>M</kbd> 键</li>
            <li>标记类型：章节、注释、重要点</li>
            <li>标记导航：使用 <kbd>Shift</kbd> + <kbd>M</kbd></li>
        </ul>

        <h2>⌨️ 常用快捷键</h2>
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr>
                <th>功能</th>
                <th>Windows</th>
                <th>Mac</th>
            </tr>
            <tr>
                <td>播放/暂停</td>
                <td>空格</td>
                <td>空格</td>
            </tr>
            <tr>
                <td>分割</td>
                <td>C</td>
                <td>C</td>
            </tr>
            <tr>
                <td>选择工具</td>
                <td>V</td>
                <td>V</td>
            </tr>
            <tr>
                <td>修剪工具</td>
                <td>T</td>
                <td>T</td>
            </tr>
            <tr>
                <td>波纹编辑</td>
                <td>B</td>
                <td>B</td>
            </tr>
            <tr>
                <td>添加标记</td>
                <td>M</td>
                <td>M</td>
            </tr>
            <tr>
                <td>撤销</td>
                <td>Ctrl+Z</td>
                <td>Cmd+Z</td>
            </tr>
            <tr>
                <td>重做</td>
                <td>Ctrl+Y</td>
                <td>Cmd+Shift+Z</td>
            </tr>
        </table>

        <div style="background-color: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3>💡 专业建议</h3>
            <ul>
                <li>使用键盘快捷键可以大大提高编辑效率</li>
                <li>养成定期保存工作的习惯</li>
                <li>在复杂编辑前先创建项目备份</li>
                <li>利用标记功能标记重要的编辑点</li>
            </ul>
        </div>

        <h2>🎉 继续学习</h2>
        <p>掌握了时间线编辑基础后，您可以学习<a href="#ai_features">AI功能使用</a>来提升您的编辑效率。</p>
        """

    def get_ai_features_content(self) -> str:
        """获取AI功能内容"""
        return """
        <h1>🤖 AI智能功能使用</h1>

        <p>CineAIStudio 集成了强大的AI功能，可以显著提升您的视频编辑效率和质量。</p>

        <h2>🎯 可用的AI功能</h2>

        <h3>1. 智能字幕生成</h3>
        <ul>
            <li><strong>语音识别</strong>：自动识别视频中的语音内容</li>
            <li><strong>字幕生成</strong>：将识别的语音转换为字幕文本</li>
            <li><strong>时间同步</strong>：自动同步字幕时间轴</li>
            <li><strong>多语言支持</strong>：支持中文、英文等多种语言</li>
        </ul>

        <h3>2. 智能剪辑</h3>
        <ul>
            <li><strong>场景检测</strong>：自动检测视频场景变化</li>
            <li><strong>内容分析</strong>：分析视频内容和主题</li>
            <li><strong>自动剪辑</strong>：基于内容自动生成剪辑建议</li>
            <li><strong>智能排序</strong>：根据内容逻辑优化素材排列</li>
        </ul>

        <h3>3. 图像增强</h3>
        <ul>
            <li><strong>超分辨率</strong>：提升低分辨率视频质量</li>
            <li><strong>去噪</strong>：减少视频噪声和颗粒</li>
            <li><strong>色彩增强</strong>：自动优化色彩和对比度</li>
            <li><strong>人脸优化</strong>：智能美颜和人脸增强</li>
        </ul>

        <h3>4. 音频处理</h3>
        <ul>
            <li><strong>语音增强</strong>：提升语音清晰度</li>
            <li><strong>背景音降噪</strong>：减少背景噪音</li>
            <li><strong>音频均衡</strong>：自动调整音频平衡</li>
            <li><strong>音乐分析</strong>：分析音乐节奏和节拍</li>
        </ul>

        <h2>🚀 使用AI功能</h2>

        <h3>启动AI工具</h3>
        <ol>
            <li>在菜单中选择：<strong>AI工具</strong></li>
            <li>或者点击工具栏中的AI按钮</li>
            <li>选择需要的AI功能</li>
            <li>按照向导完成设置</li>
        </ol>

        <h3>AI字幕生成示例</h3>
        <ol>
            <li>选择要添加字幕的视频素材</li>
            <li>右键点击选择"AI字幕生成"</li>
            <li>设置语言和字幕样式</li>
            <li>点击"开始生成"</li>
            <li>等待处理完成，自动添加到字幕轨道</li>
        </ol>

        <h3>智能剪辑示例</h3>
        <ol>
            <li>选择多个视频素材</li>
            <li>点击"智能剪辑"按钮</li>
            <li>选择剪辑风格和目标时长</li>
            <li>点击"生成剪辑"</li>
            <li>预览并调整生成的剪辑</li>
        </ol>

        <h2>⚙️ AI设置</h2>

        <h3>AI模型选择</h3>
        <p>CineAIStudio 支持多种AI模型：</p>
        <ul>
            <li><strong>本地模型</strong>：在本地运行，保护隐私</li>
            <li><strong>云端模型</strong>：功能更强大，需要网络连接</li>
            <li><strong>混合模式</strong>：根据需求自动选择最佳模型</li>
        </ul>

        <h3>性能设置</h3>
        <ul>
            <li><strong>GPU加速</strong>：使用显卡加速AI处理</li>
            <li><strong>批处理</strong>：同时处理多个任务</li>
            <li><strong>质量优先级</strong>：平衡处理速度和质量</li>
        </ul>

        <h2>💡 使用技巧</h2>

        <h3>优化AI处理</h3>
        <ul>
            <li>使用GPU加速可以大幅提升处理速度</li>
            <li>对于长视频，可以分段处理</li>
            <li>提前整理好素材，减少AI处理的复杂度</li>
            <li>保存常用的AI设置为预设</li>
        </ul>

        <h3>质量控制</h3>
        <ul>
            <li>AI处理后需要人工检查和调整</li>
            <li>使用预览功能查看处理效果</li>
            <li>可以多次应用AI功能进行叠加优化</li>
            <li>保存原始素材，以便重新处理</li>
        </ul>

        <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3>⚠️ 注意事项</h3>
            <ul>
                <li>AI功能需要较高的系统配置</li>
                <li>处理时间取决于素材大小和复杂度</li>
                <li>云端AI功能需要稳定的网络连接</li>
                <li>建议在处理前备份重要项目</li>
            </ul>
        </div>

        <h2>🔧 故障排除</h2>

        <h3>常见问题</h3>
        <ul>
            <li><strong>AI功能无响应</strong>：检查网络连接和AI服务状态</li>
            <li><strong>处理速度慢</strong>：尝试使用本地模型或降低处理质量</li>
            <li><strong>结果不理想</strong>：调整参数或尝试不同的AI模型</li>
            <li><strong>内存不足</strong>：关闭其他程序或增加虚拟内存</li>
        </ul>

        <h2>🎉 总结</h2>
        <p>AI功能是 CineAIStudio 的核心特色，合理使用这些功能可以显著提升您的编辑效率和视频质量。</p>
        """

    def get_export_content(self) -> str:
        """获取导出内容"""
        return """
        <h1>📤 项目导出设置</h1>

        <p>导出是视频编辑的最后一步，CineAIStudio 提供了强大的导出功能和多种格式支持。</p>

        <h2>🎬 导出格式</h2>

        <h3>视频格式</h3>
        <ul>
            <li><strong>MP4 (H.264)</strong>：最常用的视频格式，兼容性最好</li>
            <li><strong>MP4 (H.265/HEVC)</strong>：更高压缩率，适合4K视频</li>
            <li><strong>MOV</strong>：Apple设备兼容格式</li>
            <li><strong>AVI</strong>：无损质量，文件较大</li>
            <li><strong>WMV</strong>：Windows平台格式</li>
            <li><strong>WebM</strong>：网页优化格式</li>
        </ul>

        <h3>音频格式</h3>
        <ul>
            <li><strong>AAC</strong>：高质量音频压缩</li>
            <li><strong>MP3</strong>：通用音频格式</li>
            <li><strong>WAV</strong>：无损音频</li>
            <li><strong>FLAC</strong>：无损压缩音频</li>
        </ul>

        <h2>📱 预设配置</h2>

        <h3>设备预设</h3>
        <ul>
            <li><strong>YouTube</strong>：优化的YouTube上传格式</li>
            <li><strong>社交媒体</strong>：Instagram、TikTok、微博等</li>
            <li><strong>移动设备</strong>：iPhone、Android手机</li>
            <li><strong>平板设备</strong>：iPad、Android平板</li>
            <li><strong>游戏主机</strong>：PS5、Xbox Series X</li>
        </ul>

        <h3>质量预设</h3>
        <ul>
            <li><strong>4K Ultra HD</strong>：3840×2160，最高质量</li>
            <li><strong>1080p Full HD</strong>：1920×1080，标准高清</li>
            <li><strong>720p HD</strong>：1280×720，流畅高清</li>
            <li><strong>480p SD</strong>：854×480，标准清晰度</li>
        </ul>

        <h2>⚙️ 导出设置</h2>

        <h3>基本设置</h3>
        <ul>
            <li><strong>分辨率</strong>：输出视频的像素尺寸</li>
            <li><strong>帧率</strong>：每秒帧数（24/25/30/60）</li>
            <li><strong>比特率</strong>：影响视频质量和文件大小</li>
            <li><strong>编码器</strong>：H.264、H.265、ProRes等</li>
        </ul>

        <h3>高级设置</h3>
        <ul>
            <li><strong>关键帧间隔</strong>：影响视频的压缩效率</li>
            <li><strong>B帧数量</strong>：提高压缩效率</li>
            <li><strong>参考帧数量</strong>：影响视频质量</li>
            <li><strong>色彩空间</strong>：Rec.709、Rec.2020等</li>
        </ul>

        <h3>音频设置</h3>
        <ul>
            <li><strong>采样率</strong>：44.1kHz、48kHz等</li>
            <li><strong>比特率</strong>：128kbps、256kbps、320kbps</li>
            <li><strong>声道</strong>：立体声、5.1环绕声</li>
        </ul>

        <h2>🚀 导出流程</h2>

        <h3>方法 1：快速导出</h3>
        <ol>
            <li>点击工具栏中的"导出"按钮</li>
            <li>选择预设（如"YouTube 1080p"）</li>
            <li>选择输出位置</li>
            <li>点击"开始导出"</li>
        </ol>

        <h3>方法 2：自定义导出</h3>
        <ol>
            <li>选择<strong>文件 → 导出 → 自定义导出</strong></li>
            <li>设置视频格式和参数</li>
            <li>配置音频设置</li>
            <li>添加元数据（标题、作者等）</li>
            <li>选择输出位置和文件名</li>
            <li>点击"开始导出"</li>
        </ol>

        <h3>方法 3：批量导出</h3>
        <ol>
            <li>选择多个项目或序列</li>
            <li>右键点击选择"批量导出"</li>
            <li>设置导出参数（可单独设置）</li>
            <li>选择输出位置</li>
            <li>点击"开始批量导出"</li>
        </ol>

        <h2>📊 导出监控</h2>

        <h3>导出进度</h3>
        <ul>
            <li>实时显示导出进度</li>
            <li>显示剩余时间估算</li>
            <li>显示当前处理速度</li>
            <li>显示系统资源使用情况</li>
        </ul>

        <h3>导出队列</h3>
        <ul>
            <li>可以添加多个导出任务</li>
            <li>支持暂停和继续</li>
            <li>可以调整任务优先级</li>
            <li>支持后台导出</li>
        </ul>

        <h2>⚡ 性能优化</h2>

        <h3>硬件加速</h3>
        <ul>
            <li><strong>GPU加速</strong>：使用显卡编码器</li>
            <li><strong>多线程</strong>：利用多核CPU</li>
            <li><strong>内存优化</strong>：智能内存管理</li>
            <li><strong>缓存优化</strong>：减少重复渲染</li>
        </ul>

        <h3>优化建议</h3>
        <ul>
            <li>关闭不必要的应用程序</li>
            <li>确保足够的磁盘空间</li>
            <li>使用SSD存储输出文件</li>
            <li>定期清理临时文件</li>
        </ul>

        <div style="background-color: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3>💡 专业建议</h3>
            <ul>
                <li>在导出前预览项目确保没有错误</li>
                <li>导出小片段测试设置</li>
                <li>保存导出设置为预设供下次使用</li>
                <li>重要项目建议保留多个版本</li>
            </ul>
        </div>

        <h2>🔧 故障排除</h2>

        <h3>常见问题</h3>
        <ul>
            <li><strong>导出失败</strong>：检查磁盘空间和文件权限</li>
            <li><strong>视频卡顿</strong>：降低比特率或分辨率</li>
            <li><strong>音频不同步</strong>：检查音频采样率设置</li>
            <li><strong>颜色异常</strong>：确认色彩空间设置</li>
        </ul>

        <h2>🎉 完成</h2>
        <p>恭喜！您已经掌握了 CineAIStudio 的导出功能。现在您可以创建和导出专业的视频作品了。</p>
        """

    def get_troubleshooting_content(self) -> str:
        """获取故障排除内容"""
        return """
        <h1>🔧 常见问题解决</h1>

        <p>这里收集了用户在使用 CineAIStudio 时遇到的常见问题和解决方案。</p>

        <h2>🚀 启动和安装问题</h2>

        <h3>应用程序无法启动</h3>
        <ul>
            <li><strong>问题</strong>：双击图标无反应</li>
            <li><strong>解决方案</strong>：
                <ul>
                    <li>检查系统是否满足最低要求</li>
                    <li>重新安装应用程序</li>
                    <li>检查防火墙设置</li>
                    <li>以管理员身份运行</li>
                </ul>
            </li>
        </ul>

        <h3>启动时崩溃</h3>
        <ul>
            <li><strong>问题</strong>：启动过程中程序崩溃</li>
            <li><strong>解决方案</strong>：
                <ul>
                    <li>更新显卡驱动程序</li>
                    <li>检查系统完整性</li>
                    <li>删除配置文件重新启动</li>
                    <li>查看崩溃日志文件</li>
                </ul>
            </li>
        </ul>

        <h2>📥 导入和媒体问题</h2>

        <h3>媒体文件无法导入</h3>
        <ul>
            <li><strong>问题</strong>：拖放文件无反应或提示错误</li>
            <li><strong>解决方案</strong>：
                <ul>
                    <li>检查文件格式是否支持</li>
                    <li>确认文件没有损坏</li>
                    <li>尝试重新编码文件</li>
                    <li>检查文件权限</li>
                </ul>
            </li>
        </ul>

        <h3>视频播放卡顿</h3>
        <ul>
            <li><strong>问题</strong>：预览时视频不流畅</li>
            <li><strong>解决方案</strong>：
                <ul>
                    <li>降低预览质量</li>
                    <li>创建代理文件</li>
                    <li>关闭其他应用程序</li>
                    <li>更新显卡驱动</li>
                </ul>
            </li>
        </ul>

        <h2>⏱️ 时间线编辑问题</h2>

        <h3>时间线响应缓慢</h3>
        <ul>
            <li><strong>问题</strong>：拖动素材时延迟严重</li>
            <li><strong>解决方案</strong>：
                <ul>
                    <li>减少时间线上的素材数量</li>
                    <li>使用代理文件</li>
                    <li>降低预览分辨率</li>
                    <li>增加系统内存</li>
                </ul>
            </li>
        </ul>

        <h3>音频不同步</h3>
        <ul>
            <li><strong>问题</strong>：音频和视频不同步</li>
            <li><strong>解决方案</strong>：
                <ul>
                    <li>检查原始文件是否同步</li>
                    <li>重新导入媒体文件</li>
                    <li>手动调整音频轨道位置</li>
                    <li>使用音频同步工具</li>
                </ul>
            </li>
        </ul>

        <h2>🤖 AI功能问题</h2>

        <h3>AI功能无响应</h3>
        <ul>
            <li><strong>问题</strong>：点击AI功能没有反应</li>
            <li><strong>解决方案</strong>：
                <ul>
                    <li>检查网络连接</li>
                    <li>确认AI服务可用</li>
                    <li>重新启动应用程序</li>
                    <li>检查AI服务配置</li>
                </ul>
            </li>
        </ul>

        <h3>AI处理失败</h3>
        <ul>
            <li><strong>问题</strong>：AI处理过程中出错</li>
            <li><strong>解决方案</strong>：
                <ul>
                    <li>检查文件格式和大小</li>
                    <li>尝试使用其他AI模型</li>
                    <li>降低处理质量设置</li>
                    <li>清理磁盘空间</li>
                </ul>
            </li>
        </ul>

        <h2>📤 导出问题</h2>

        <h3>导出失败</h3>
        <ul>
            <li><strong>问题</strong>：导出过程中出现错误</li>
            <li><strong>解决方案</strong>：
                <ul>
                    <li>检查输出路径权限</li>
                    <li>确保足够的磁盘空间</li>
                    <li>尝试不同的导出格式</li>
                    <li>检查项目文件完整性</li>
                </ul>
            </li>
        </ul>

        <h3>导出的视频有质量问题</h3>
        <ul>
            <li><strong>问题</strong>：输出的视频模糊或有瑕疵</li>
            <li><strong>解决方案</strong>：
                <ul>
                    <li>提高导出比特率</li>
                    <li>使用更好的编码器</li>
                    <li>检查原始素材质量</li>
                    <li>调整色彩空间设置</li>
                </ul>
            </li>
        </ul>

        <h2>💾 项目和文件问题</h2>

        <h3>项目文件损坏</h3>
        <ul>
            <li><strong>问题</strong>：无法打开项目文件</li>
            <li><strong>解决方案</strong>：
                <ul>
                    <li>检查自动保存文件</li>
                    <li>使用项目恢复工具</li>
                    <li>重新创建项目</li>
                    <li>联系技术支持</li>
                </ul>
            </li>
        </ul>

        <h3>文件丢失</h3>
        <ul>
            <li><strong>问题</strong>：项目提示媒体文件丢失</li>
            <li><strong>解决方案</strong>：
                <ul>
                    <li>重新链接媒体文件</li>
                    <li>检查文件路径是否改变</li>
                    <li>搜索丢失的文件</li>
                    <li>使用离线媒体功能</li>
                </ul>
            </li>
        </ul>

        <h2>⚡ 性能优化问题</h2>

        <h3>系统运行缓慢</h3>
        <ul>
            <li><strong>问题</strong>：整体性能不佳</li>
            <li><strong>解决方案</strong>：
                <ul>
                    <li>关闭不必要的应用程序</li>
                    <li>增加虚拟内存</li>
                    <li>升级硬件配置</li>
                    <li>优化系统设置</li>
                </ul>
            </li>
        </ul>

        <h3>内存不足</h3>
        <ul>
            <li><strong>问题</strong>：提示内存不足</li>
            <li><strong>解决方案</strong>：
                <ul>
                    <li>关闭其他应用程序</li>
                    <li>使用代理文件</li>
                    <li>减少时间线复杂度</li>
                    <li>增加物理内存</li>
                </ul>
            </li>
        </ul>

        <div style="background-color: #f8d7da; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3>🆘 获取更多帮助</h3>
            <p>如果您的问题没有在这里找到解决方案，可以通过以下方式获取帮助：</p>
            <ul>
                <li>查看在线文档和教程</li>
                <li>访问用户社区论坛</li>
                <li>联系技术支持团队</li>
                <li>观看视频教程</li>
            </ul>
        </div>

        <h2>📞 联系技术支持</h2>
        <p>如果以上解决方案都无法解决您的问题，请准备好以下信息联系技术支持：</p>
        <ul>
            <li>CineAIStudio 版本号</li>
            <li>操作系统版本</li>
            <li>硬件配置信息</li>
            <li>错误信息和截图</li>
            <li>重现问题的步骤</li>
        </ul>
        """

    def get_keyboard_shortcuts_content(self) -> str:
        """获取键盘快捷键内容"""
        return """
        <h1>⌨️ 键盘快捷键</h1>

        <p>掌握键盘快捷键可以大幅提高您的编辑效率。以下是 CineAIStudio 的主要快捷键。</p>

        <h2>🎬 基本操作</h2>

        <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
            <tr>
                <th>功能</th>
                <th>Windows</th>
                <th>Mac</th>
                <th>描述</th>
            </tr>
            <tr>
                <td>新建项目</td>
                <td>Ctrl+N</td>
                <td>Cmd+N</td>
                <td>创建新项目</td>
            </tr>
            <tr>
                <td>打开项目</td>
                <td>Ctrl+O</td>
                <td>Cmd+O</td>
                <td>打开已有项目</td>
            </tr>
            <tr>
                <td>保存项目</td>
                <td>Ctrl+S</td>
                <td>Cmd+S</td>
                <td>保存当前项目</td>
            </tr>
            <tr>
                <td>另存为</td>
                <td>Ctrl+Shift+S</td>
                <td>Cmd+Shift+S</td>
                <td>项目另存为</td>
            </tr>
            <tr>
                <td>导出</td>
                <td>Ctrl+E</td>
                <td>Cmd+E</td>
                <td>导出项目</td>
            </tr>
            <tr>
                <td>撤销</td>
                <td>Ctrl+Z</td>
                <td>Cmd+Z</td>
                <td>撤销上一步操作</td>
            </tr>
            <tr>
                <td>重做</td>
                <td>Ctrl+Y</td>
                <td>Cmd+Shift+Z</td>
                <td>重做撤销的操作</td>
            </tr>
            <tr>
                <td>帮助</td>
                <td>F1</td>
                <td>F1</td>
                <td>打开帮助系统</td>
            </tr>
        </table>

        <h2>⏱️ 时间线操作</h2>

        <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
            <tr>
                <th>功能</th>
                <th>Windows</th>
                <th>Mac</th>
                <th>描述</th>
            </tr>
            <tr>
                <td>播放/暂停</td>
                <td>空格</td>
                <td>空格</td>
                <td>播放或暂停时间线</td>
            </tr>
            <tr>
                <td>停止</td>
                <td>K</td>
                <td>K</td>
                <td>停止播放</td>
            </tr>
            <tr>
                <td>前进一帧</td>
                <td>→</td>
                <td>→</td>
                <td>向前移动一帧</td>
            </tr>
            <tr>
                <td>后退一帧</td>
                <td>←</td>
                <td>←</td>
                <td>向后移动一帧</td>
            </tr>
            <tr>
                <td>前进10帧</td>
                <td>Shift+→</td>
                <td>Shift+→</td>
                <td>向前移动10帧</td>
            </tr>
            <tr>
                <td>后退10帧</td>
                <td>Shift+←</td>
                <td>Shift+←</td>
                <td>向后移动10帧</td>
            </tr>
            <tr>
                <td>跳转到开头</td>
                <td>Home</td>
                <td>Home</td>
                <td>跳转到时间线开头</td>
            </tr>
            <tr>
                <td>跳转到结尾</td>
                <td>End</td>
                <td>End</td>
                <td>跳转到时间线结尾</td>
            </tr>
            <tr>
                <td>添加标记</td>
                <td>M</td>
                <td>M</td>
                <td>在当前位置添加标记</td>
            </tr>
            <tr>
                <td>下一标记</td>
                <td>Shift+M</td>
                <td>Shift+M</td>
                <td>跳转到下一个标记</td>
            </tr>
        </table>

        <h2>🔧 编辑工具</h2>

        <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
            <tr>
                <th>功能</th>
                <th>Windows</th>
                <th>Mac</th>
                <th>描述</th>
            </tr>
            <tr>
                <td>选择工具</td>
                <td>V</td>
                <td>V</td>
                <td>选择和移动素材</td>
            </tr>
            <tr>
                <td>修剪工具</td>
                <td>T</td>
                <td>T</td>
                <td>修剪素材边缘</td>
            </tr>
            <tr>
                <td>波纹编辑</td>
                <td>B</td>
                <td>B</td>
                <td>波纹编辑模式</td>
            </tr>
            <tr>
                <td>滚动工具</td>
                <td>H</td>
                <td>H</td>
                <td>滚动时间线</td>
            </tr>
            <tr>
                <td>抓手工具</td>
                <td>N</td>
                <td>N</td>
                <td>平移时间线视图</td>
            </tr>
            <tr>
                <td>分割</td>
                <td>C</td>
                <td>C</td>
                <td>分割选中的素材</td>
            </tr>
            <tr>
                <td>删除</td>
                <td>Delete</td>
                <td>Delete</td>
                <td>删除选中的素材</td>
            </tr>
            <tr>
                <td>波纹删除</td>
                <td>Shift+Delete</td>
                <td>Shift+Delete</td>
                <td>删除并闭合间隙</td>
            </tr>
        </table>

        <h2>📦 素材操作</h2>

        <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
            <tr>
                <th>功能</th>
                <th>Windows</th>
                <th>Mac</th>
                <th>描述</th>
            </tr>
            <tr>
                <td>导入媒体</td>
                <td>Ctrl+I</td>
                <td>Cmd+I</td>
                <td>导入媒体文件</td>
            </tr>
            <tr>
                <td>新建序列</td>
                <td>Ctrl+N</td>
                <td>Cmd+N</td>
                <td>创建新序列</td>
            </tr>
            <tr>
                <td>嵌套</td>
                <td>Ctrl+Shift+N</td>
                <td>Cmd+Shift+N</td>
                <td>嵌套选中的素材</td>
            </tr>
            <tr>
                <td>链接/取消链接</td>
                <td>Ctrl+L</td>
                <td>Cmd+L</td>
                <td>链接或取消链接音视频</td>
            </tr>
            <tr>
                <td>组/取消组</td>
                <td>Ctrl+G</td>
                <td>Cmd+G</td>
                <td>组合或取消组合素材</td>
            </tr>
            <tr>
                <td>复制</td>
                <td>Ctrl+C</td>
                <td>Cmd+C</td>
                <td>复制选中的素材</td>
            </tr>
            <tr>
                <td>粘贴</td>
                <td>Ctrl+V</td>
                <td>Cmd+V</td>
                <td>粘贴素材</td>
            </tr>
            <tr>
                <td>剪切</td>
                <td>Ctrl+X</td>
                <td>Cmd+X</td>
                <td>剪切选中的素材</td>
            </tr>
        </table>

        <h2>🎬 视图控制</h2>

        <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
            <tr>
                <th>功能</th>
                <th>Windows</th>
                <th>Mac</th>
                <th>描述</th>
            </tr>
            <tr>
                <td>放大</td>
                <td>=</td>
                <td>=</td>
                <td>放大时间线视图</td>
            </tr>
            <tr>
                <td>缩小</td>
                <td>-</td>
                <td>-</td>
                <td>缩小时间线视图</td>
            </tr>
            <tr>
                <td>适配时间线</td>
                <td>\\</td>
                <td>\\</td>
                <td>自适应时间线视图</td>
            </tr>
            <tr>
                <td>显示/隐藏轨道</td>
                <td>Ctrl+T</td>
                <td>Cmd+T</td>
                <td>显示或隐藏轨道</td>
            </tr>
            <tr>
                <td>切换全屏</td>
                <td>F11</td>
                <td>F11</td>
                <td>切换全屏模式</td>
            </tr>
            <tr>
                <td>切换安全框</td>
                <td>Ctrl+'</td>
                <td>Cmd+'</td>
                <td>显示/隐藏安全框</td>
            </tr>
        </table>

        <h2>🎨 效果和过渡</h2>

        <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
            <tr>
                <th>功能</th>
                <th>Windows</th>
                <th>Mac</th>
                <th>描述</th>
            </tr>
            <tr>
                <td>添加过渡</td>
                <td>Ctrl+D</td>
                <td>Cmd+D</td>
                <td>添加默认过渡</td>
            </tr>
            <tr>
                <td>添加视频效果</td>
                <td>Ctrl+Shift+E</td>
                <td>Cmd+Shift+E</td>
                <td>添加视频效果</td>
            </tr>
            <tr>
                <td>添加音频效果</td>
                <td>Ctrl+Shift+A</td>
                <td>Cmd+Shift+A</td>
                <td>添加音频效果</td>
            </tr>
            <tr>
                <td>效果控件</td>
                <td>Shift+5</td>
                <td>Shift+5</td>
                <td>打开效果控件面板</td>
            </tr>
        </table>

        <h2>🎵 音频控制</h2>

        <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
            <tr>
                <th>功能</th>
                <th>Windows</th>
                <th>Mac</th>
                <th>描述</th>
            </tr>
            <tr>
                <td>音频轨静音</td>
                <td>Ctrl+M</td>
                <td>Cmd+M</td>
                <td>静音/取消静音音频轨</td>
            </tr>
            <tr>
                <td>音频轨独奏</td>
                <td>Ctrl+Alt+M</td>
                <td>Cmd+Option+M</td>
                <td>独奏/取消独奏音频轨</td>
            </tr>
            <tr>
                <td>显示音频波形</td>
                <td>Ctrl+Shift+W</td>
                <td>Cmd+Shift+W</td>
                <td>显示/隐藏音频波形</td>
            </tr>
            <tr>
                <td>标准化音频</td>
                <td>Ctrl+Shift+N</td>
                <td>Cmd+Shift+N</td>
                <td>标准化音频级别</td>
            </tr>
        </table>

        <h2>🤖 AI功能快捷键</h2>

        <table border="1" style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
            <tr>
                <th>功能</th>
                <th>Windows</th>
                <th>Mac</th>
                <th>描述</th>
            </tr>
            <tr>
                <td>AI字幕生成</td>
                <td>Ctrl+Shift+C</td>
                <td>Cmd+Shift+C</td>
                <td>生成AI字幕</td>
            </tr>
            <tr>
                <td>智能剪辑</td>
                <td>Ctrl+Shift+I</td>
                <td>Cmd+Shift+I</td>
                <td>启动智能剪辑</td>
            </tr>
            <tr>
                <td>图像增强</td>
                <td>Ctrl+Shift+P</td>
                <td>Cmd+Shift+P</td>
                <td>增强图像质量</td>
            </tr>
            <tr>
                <td>音频增强</td>
                <td>Ctrl+Shift+A</td>
                <td>Cmd+Shift+A</td>
                <td>增强音频质量</td>
            </tr>
        </table>

        <div style="background-color: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3>💡 自定义快捷键</h3>
            <p>您可以根据个人习惯自定义快捷键：</p>
            <ol>
                <li>打开 <strong>编辑 → 键盘快捷键</strong></li>
                <li>选择要修改的功能</li>
                <li>点击快捷键栏并按下新的组合键</li>
                <li>点击"应用"保存更改</li>
            </ol>
        </div>

        <h2>📚 学习建议</h2>
        <ul>
            <li>建议每天学习几个快捷键，逐步掌握</li>
            <li>将最常用的快捷键制作成备忘录</li>
            <li>在实际编辑中有意识地使用快捷键</li>
            <li>定期复习不常用的快捷键</li>
        </ul>

        <p>掌握这些快捷键将大幅提高您的编辑效率，让您能够更专注于创意工作。</p>
        """

    def show_topic(self, topic_id: str):
        """显示指定主题"""
        if topic_id not in self.help_topics:
            return

        topic = self.help_topics[topic_id]
        self.current_topic = topic

        # 更新标题
        self.topic_title.setText(topic.title)

        # 更新难度和时间标签
        difficulty_colors = {
            "beginner": "#4caf50",
            "intermediate": "#ff9800",
            "advanced": "#f44336"
        }

        difficulty_texts = {
            "beginner": "初级",
            "intermediate": "中级",
            "advanced": "高级"
        }

        self.difficulty_label.setText(f"难度: {difficulty_texts[topic.difficulty]}")
        self.difficulty_label.setStyleSheet(f"""
            QLabel {{
                background-color: {difficulty_colors[topic.difficulty]};
                color: white;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: bold;
            }}
        """)

        self.time_label.setText(f"⏱️ {topic.estimated_time} 分钟")

        # 显示内容
        self.content_browser.setHtml(topic.content)

        # 更新相关主题
        self.update_related_topics(topic.related_topics)

        # 更新学习进度
        self.update_progress(topic_id)

    def update_related_topics(self, related_topic_ids: List[str]):
        """更新相关主题列表"""
        self.related_list.clear()

        for topic_id in related_topic_ids:
            if topic_id in self.help_topics:
                topic = self.help_topics[topic_id]
                item = QListWidgetItem(topic.title)
                item.setData(Qt.ItemDataRole.UserRole, topic_id)
                self.related_list.addItem(item)

    def update_progress(self, topic_id: str):
        """更新学习进度"""
        if topic_id not in self.tutorial_progress:
            self.tutorial_progress[topic_id] = 100.0

        # 计算总体进度
        total_topics = len(self.help_topics)
        completed_topics = len(self.tutorial_progress)
        progress = (completed_topics / total_topics) * 100

        self.progress_bar.setValue(int(progress))

    def on_category_clicked(self, item: QTreeWidgetItem, column: int):
        """处理分类点击"""
        # 找到对应的帮助主题
        category_name = item.text(0)
        category_map = {
            "新手入门": "welcome",
            "基础教程": "first_project",
            "高级功能": "ai_features",
            "AI功能": "ai_features",
            "导出指南": "export_projects",
            "故障排除": "troubleshooting",
            "常见问题": "troubleshooting",
            "快捷键": "keyboard_shortcuts"
        }

        if category_name in category_map:
            topic_id = category_map[category_name]
            self.show_topic(topic_id)

    def on_quick_access_clicked(self, item: QListWidgetItem):
        """处理快速访问点击"""
        topic_id = item.data(Qt.ItemDataRole.UserRole)
        if topic_id:
            self.show_topic(topic_id)

    def on_related_topic_clicked(self, item: QListWidgetItem):
        """处理相关主题点击"""
        topic_id = item.data(Qt.ItemDataRole.UserRole)
        if topic_id:
            self.show_topic(topic_id)

    def on_link_clicked(self, url: QUrl):
        """处理链接点击"""
        url_str = url.toString()
        if url_str.startswith("#"):
            topic_id = url_str[1:]  # 移除#号
            self.show_topic(topic_id)

    def go_back(self):
        """返回上一个主题"""
        # 这里可以实现历史记录功能
        self.show_topic("welcome")

    def go_forward(self):
        """前进到下一个主题"""
        # 这里可以实现历史记录功能
        pass

    def go_home(self):
        """返回首页"""
        self.show_topic("welcome")

    def start_tutorial(self):
        """开始教程"""
        if self.current_topic:
            self.tutorial_started.emit(self.current_topic.id)

            # 显示教程开始提示
            QMessageBox.information(
                self,
                "教程开始",
                f"正在开始教程：{self.current_topic.title}\n\n按照教程内容操作，完成后记得回来继续学习！"
            )


class InteractiveTutorial(QDialog):
    """交互式教程对话框"""

    def __init__(self, tutorial_id: str, help_system: HelpSystem, parent=None):
        super().__init__(parent)
        self.tutorial_id = tutorial_id
        self.help_system = help_system
        self.current_step = 0
        self.setup_ui()

    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("交互式教程")
        self.setModal(True)
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        # 标题
        title = QLabel(f"教程: {self.tutorial_id}")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # 内容区域
        self.content_area = QTextBrowser()
        layout.addWidget(self.content_area)

        # 进度条
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.prev_button = QPushButton("← 上一步")
        self.prev_button.clicked.connect(self.previous_step)
        button_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("下一步 →")
        self.next_button.clicked.connect(self.next_step)
        button_layout.addWidget(self.next_button)

        self.finish_button = QPushButton("完成")
        self.finish_button.clicked.connect(self.finish_tutorial)
        self.finish_button.hide()
        button_layout.addWidget(self.finish_button)

        layout.addLayout(button_layout)

        # 开始教程
        self.load_step(0)

    def load_step(self, step: int):
        """加载教程步骤"""
        self.current_step = step
        # 这里可以实现具体的教程步骤逻辑
        # 现在显示占位内容
        self.content_area.setHtml(f"""
        <h2>教程步骤 {step + 1}</h2>
        <p>这里是教程步骤 {step + 1} 的详细说明。</p>
        <p>请按照提示完成相关操作。</p>
        """)

        # 更新按钮状态
        self.prev_button.setEnabled(step > 0)

        # 更新进度
        total_steps = 5  # 假设有5个步骤
        progress = ((step + 1) / total_steps) * 100
        self.progress_bar.setValue(int(progress))

        # 检查是否完成
        if step >= total_steps - 1:
            self.next_button.hide()
            self.finish_button.show()

    def previous_step(self):
        """上一步"""
        if self.current_step > 0:
            self.load_step(self.current_step - 1)

    def next_step(self):
        """下一步"""
        self.load_step(self.current_step + 1)

    def finish_tutorial(self):
        """完成教程"""
        QMessageBox.information(
            self,
            "教程完成",
            "恭喜！您已完成本教程。继续加油学习其他功能吧！"
        )
        self.accept()


# 帮助系统工厂函数
def get_help_system() -> HelpSystem:
    """获取帮助系统实例"""
    return HelpSystem()