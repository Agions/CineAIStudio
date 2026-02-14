#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineFlow v3.0 主窗口 - 现代化UI升级

全新的现代化界面设计
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..common.widgets.modern_navigation import ModernNavigationBar, ModernTopBar, ModernStatusBar
from ..common.widgets.modern_cards import ModernCard, FeatureCard, ActionCard, CardGrid
from ..common.widgets.modern_buttons import ModernButton
from ..theme.design_system import COLOR_SYSTEM, SPACING


class ModernHomePage(QWidget):
    """
    现代化首页

    欢迎页面，展示主要功能
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        self.setLayout(layout)

        # 欢迎标题
        title = QLabel("欢迎使用 CineFlow")
        title.setStyleSheet("""
            font-size: 32px;
            font-weight: 700;
            color: #F9FAFB;
        """)
        layout.addWidget(title)

        subtitle = QLabel("AI 驱动的专业视频创作平台")
        subtitle.setStyleSheet("""
            font-size: 16px;
            color: #9CA3AF;
        """)
        layout.addWidget(subtitle)

        layout.addSpacing(32)

        # 功能卡片网格
        cards = [
            FeatureCard(
                "AI 视频生成",
                "使用 AI 自动生成脚本、配音、字幕，一键创建专业视频",
                icon="🎬",
            ),
            FeatureCard(
                "智能剪辑",
                "AI 辅助剪辑，自动识别镜头、生成转场、智能配乐",
                icon="✂️",
            ),
            FeatureCard(
                "多模态理解",
                "国产 LLM + 视觉分析，深度理解视频内容",
                icon="👁️",
            ),
            FeatureCard(
                "本地模型",
                "支持 Ollama 本地 LLM，离线推理，完全隐私",
                icon="🏠",
            ),
        ]

        card_grid = CardGrid(columns=2, spacing=16)
        for card in cards:
            card_grid.add_card(card)

        layout.addWidget(card_grid)
        layout.addStretch()


class ModernAIPage(QWidget):
    """
    现代化 AI 页面

    AI 功能和工具集
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)
        self.setLayout(layout)

        # 标题
        title = QLabel("AI 生成工具")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: 600;
            color: #F9FAFB;
        """)
        layout.addWidget(title)

        # AI 功能卡片
        func_card = FeatureCard(
            "文案创作",
            "使用国产大模型生成视频脚本、台词、旁白等文案内容",
            "✍️",
        )
        layout.addWidget(func_card)

        vision_card = FeatureCard(
            "画面理解",
            "千问 VL 分析视频内容，生成标签、描述、字幕建议",
            "👁️",
        )
        layout.addWidget(vision_card)

        voice_card = FeatureCard(
            "语音合成",
            "阿里云 TTS 提供 15+ 种语音风格，支持方言和情感",
            "🎙️",
        )
        layout.addWidget(voice_card)

        layout.addStretch()


class ModernMainWindow(QMainWindow):
    """
    CineFlow v3.0 现代化主窗口

    设计特点:
    - 玻璃拟态设计
    - 流畅的导航体验
    - 深色优先的主题
    - 专业而不失创意
    """

    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_ui()

    def _setup_window(self):
        """设置窗口属性"""
        self.setWindowTitle("CineFlow v3.0")
        self.resize(1400, 900)

        # 应用现代化主题
        self._apply_modern_theme()

    def _setup_ui(self):
        """设置UI"""
        # 主容器
        self.main_container = QWidget()
        self.main_container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0A0E14,
                    stop:1 #111827);
            }
        """)
        self.setCentralWidget(self.main_container)

        # 主布局
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.main_container.setLayout(main_layout)

        # 侧边导航
        self.nav_bar = ModernNavigationBar(
            width=240,
            collapsible=True,
        )
        self.nav_bar.nav_item_clicked.connect(self._on_nav_changed)
        main_layout.addWidget(self.nav_bar)

        # 右侧内容区
        self.content_area = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        self.content_area.setLayout(content_layout)
        main_layout.addWidget(self.content_area)

        # 顶部栏
        self.top_bar = ModernTopBar(title="首页")
        content_layout.addWidget(self.top_bar)

        # 页面堆栈
        self.pages_stack = QStackedWidget()
        content_layout.addWidget(self.pages_stack)

        # 创建页面
        self._create_pages()

        # 欢迎页面
        self.pages_stack.addWidget(ModernHomePage())
        # AI 页面
        self.pages_stack.addWidget(ModernAIPage())

        # 状态栏
        self.status_bar = ModernStatusBar()
        content_layout.addWidget(self.status_bar)

    def _create_pages(self):
        """创建页面（空容器，后续填充）"""
        # 项目页面
        self.projects_page = QWidget()
        self.pages_stack.addWidget(self.projects_page)

        # 编辑器页面
        self.editor_page = QWidget()
        self.pages_stack.addWidget(self.editor_page)

        # 导出页面
        self.export_page = QWidget()
        self.pages_stack.addWidget(self.export_page)

        # 设置页面
        self.settings_page = QWidget()
        self.pages_stack.addWidget(self.settings_page)

    def _on_nav_changed(self, nav_id: str):
        """导航切换事件"""
        page_map = {
            "home": 0,
            "projects": 2,
            "ai": 1,
            "editor": 3,
            "export": 4,
            "settings": 5,
        }

        index = page_map.get(nav_id, 0)
        self.pages_stack.setCurrentIndex(index)

        # 更新顶部栏标题
        title_map = {
            "home": "首页",
            "projects": "项目管理",
            "ai": "AI 生成",
            "editor": "视频编辑器",
            "export": "导出",
            "settings": "设置",
        }
        self.top_bar.set_title(title_map.get(nav_id, ""))

        # 更新状态栏
        self.status_bar.set_status(f"已切换到: {title_map.get(nav_id, '')}")

    def _apply_modern_theme(self):
        """应用现代化主题"""
        import os

        # 加载现代化QSS样式表
        qss_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "resources", "styles", "modern_theme.qss"
        )

        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                stylesheet = f.read()
                self.setStyleSheet(stylesheet)
        except FileNotFoundError:
            print(f"警告: 未找到样式表: {qss_path}")


def main():
    """启动应用程序"""
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # 设置应用信息
    app.setApplicationName("CineFlow")
    app.setApplicationVersion("3.0.0")
    app.setOrganizationName("CineFlow Studio")

    # 创建主窗口
    window = ModernMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
