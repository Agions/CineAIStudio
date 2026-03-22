"""
ClipFlow 主窗口 - 重构版

结构:
- 首页: 项目列表
- 设置: 主题/临时文件/API Key
- 编辑面板: 在项目管理中内嵌，不单独页面
"""

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QPalette, QColor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QToolBar, QMenuBar, QMenu, QStatusBar,
    QLabel, QPushButton, QFrame, QGroupBox,
    QLineEdit, QComboBox, QCheckBox, QSpinBox,
    QDialog, QStackedWidget, QScrollArea,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
    QGridLayout as QtGridLayout,
)


class ClipFlowTheme:
    """ClipFlow 主题"""
    BG = "#0A0A0B"
    BG_ELEVATED = "#141416"
    BG_CARD = "#1A1A1D"
    BORDER = "#2A2A2E"
    TEXT = "#FAFAFA"
    TEXT_DIM = "#71717A"
    ACCENT = "#00D4FF"
    ACCENT_DIM = "rgba(0, 212, 255, 0.15)"
    SUCCESS = "#22C55E"
    ERROR = "#EF4444"
    RADIUS = 12


class HomePage(QWidget):
    """首页 - 项目列表"""
    
    new_project_clicked = pyqtSignal()
    edit_project_clicked = pyqtSignal(int)  # project_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        
        # 标题栏
        header = QWidget()
        header_layout = QHBoxLayout(header)
        
        title = QLabel("我的项目")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title)
        
        btn_new = QPushButton("+ 新建项目")
        btn_new.setObjectName("primary")
        btn_new.setStyleSheet(f"""
            QPushButton#primary {{
                background-color: {ClipFlowTheme.ACCENT};
                color: #000;
                border: none;
                border-radius: {ClipFlowTheme.RADIUS}px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton#primary:hover {{ opacity: 0.9; }}
        """)
        btn_new.clicked.connect(self.new_project_clicked.emit)
        header_layout.addWidget(btn_new)
        
        layout.addWidget(header)
        
        # 项目列表
        self.project_list = QListWidget()
        self.project_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}
        """)
        layout.addWidget(self.project_list)
    
    def load_projects(self, projects):
        """加载项目列表"""
        self.project_list.clear()
        for p in projects:
            self._add_project_item(p)
    
    def _add_project_item(self, project):
        """添加项目项"""
        item = QListWidgetItem()
        item.setData(Qt.UserRole, project["id"])
        
        widget = QFrame()
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: {ClipFlowTheme.BG_CARD};
                border: 1px solid {ClipFlowTheme.BORDER};
                border-radius: {ClipFlowTheme.RADIUS}px;
                padding: 16px;
            }}
            QFrame:hover {{
                border-color: {ClipFlowTheme.ACCENT};
            }}
        """)
        
        layout = QVBoxLayout(widget)
        
        # 项目信息
        info_layout = QHBoxLayout()
        
        thumb = QLabel("🎬")
        thumb.setStyleSheet("font-size: 24px;")
        info_layout.addWidget(thumb)
        
        info = QWidget()
        info_layout2 = QVBoxLayout(info)
        info_layout2.setContentsMargins(0, 0, 0, 0)
        
        name = QLabel(project.get("name", "未命名"))
        name.setStyleSheet("font-size: 14px; font-weight: 600;")
        info_layout2.addWidget(name)
        
        meta = QLabel(project.get("meta", ""))
        meta.setStyleSheet(f"font-size: 12px; color: {ClipFlowTheme.TEXT_DIM};")
        info_layout2.addWidget(meta)
        
        info_layout.addWidget(info, 1)
        
        # 操作按钮
        btn_edit = QPushButton("编辑")
        btn_edit.setStyleSheet(f"""
            QPushButton {{
                background: {ClipFlowTheme.BG_ELEVATED};
                border: 1px solid {ClipFlowTheme.BORDER};
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{ border-color: {ClipFlowTheme.ACCENT}; }}
        """)
        btn_edit.clicked.connect(lambda: self.edit_project_clicked.emit(project["id"]))
        
        btn_delete = QPushButton("删除")
        btn_delete.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {ClipFlowTheme.ERROR};
                color: {ClipFlowTheme.ERROR};
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background: {ClipFlowTheme.ERROR}; color: #fff; }}
        """)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)
        
        layout.addLayout(info_layout)
        layout.addLayout(btn_layout)
        
        item.setSizeHint(widget.sizeHint())
        self.project_list.addItem(item)
        self.project_list.setItemWidget(item, widget)


class SettingsPage(QWidget):
    """设置页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        
        # 外观设置
        section = self._create_section("外观")
        self._add_setting_item(section, "主题", "应用界面配色方案", 
                              QComboBox(), ["深色", "浅色", "跟随系统"])
        container_layout.addWidget(section)
        
        # 文件设置
        section = self._create_section("文件")
        self._add_setting_item(section, "临时文件位置", "缓存文件存放目录",
                              QLineEdit("/tmp/clipflow"))
        toggle = QCheckBox()
        toggle.setChecked(True)
        self._add_setting_item(section, "自动清理临时文件", "退出时自动删除缓存", toggle)
        container_layout.addWidget(section)
        
        # AI 服务设置
        section = self._create_section("AI 服务")
        self._add_setting_item(section, "大模型 API", "用于生成解说和字幕翻译",
                              QComboBox(), ["OpenAI GPT-4", "DeepSeek", "智谱 GLM", "阿里通义"])
        self._add_setting_item(section, "API Key", "你的 API 密钥",
                              QLineEdit())
        self._add_setting_item(section, "语音合成", "用于生成解说配音",
                              QComboBox(), ["Edge TTS（免费）", "Azure TTS"])
        container_layout.addWidget(section)
        
        # 导出设置
        section = self._create_section("导出")
        self._add_setting_item(section, "默认导出格式", "新建项目时的默认格式",
                              QComboBox(), ["MP4", "MOV", "SRT"])
        self._add_setting_item(section, "默认分辨率", "视频输出分辨率",
                              QComboBox(), ["1920×1080", "1280×720", "3840×2160"])
        container_layout.addWidget(section)
        
        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)
    
    def _create_section(self, title):
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 13px;
                color: {ClipFlowTheme.TEXT_DIM};
                border: 1px solid {ClipFlowTheme.BORDER};
                border-radius: {ClipFlowTheme.RADIUS}px;
                margin-top: 16px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }}
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        return group
    
    def _add_setting_item(self, group, label, desc, widget, items=None):
        item = QFrame()
        item.setStyleSheet(f"""
            QFrame {{
                border-bottom: 1px solid {ClipFlowTheme.BORDER};
                padding: 12px 16px;
            }}
            QFrame:last-child {{ border-bottom: none; }}
        """)
        layout = QHBoxLayout(item)
        
        info = QWidget()
        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        name = QLabel(label)
        name.setStyleSheet("font-size: 14px;")
        info_layout.addWidget(name)
        
        desc_label = QLabel(desc)
        desc_label.setStyleSheet(f"font-size: 12px; color: {ClipFlowTheme.TEXT_DIM};")
        info_layout.addWidget(desc_label)
        
        layout.addWidget(info, 1)
        
        if items and isinstance(widget, QComboBox):
            widget.addItems(items)
            widget.setStyleSheet(f"""
                QComboBox {{
                    background: {ClipFlowTheme.BG_ELEVATED};
                    border: 1px solid {ClipFlowTheme.BORDER};
                    border-radius: 8px;
                    padding: 8px 12px;
                    min-width: 150px;
                }}
            """)
        
        if isinstance(widget, QLineEdit):
            widget.setPlaceholderText(desc)
            widget.setStyleSheet(f"""
                QLineEdit {{
                    background: {ClipFlowTheme.BG_ELEVATED};
                    border: 1px solid {ClipFlowTheme.BORDER};
                    border-radius: 8px;
                    padding: 8px 12px;
                    min-width: 200px;
                }}
            """)
        
        if isinstance(widget, QCheckBox):
            widget.setFixedWidth(44)
            widget.setFixedHeight(24)
        
        layout.addWidget(widget)
        
        group.layout().addWidget(item)


class EditPanel(QDialog):
    """编辑面板 - 全屏对话框"""
    
    saved = pyqtSignal(dict)  # project data
    closed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑项目")
        self.resize(1200, 700)
        self.setModal(True)
        self._init_ui()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 顶部栏
        header = QWidget()
        header.setStyleSheet(f"background: {ClipFlowTheme.BG}; border-bottom: 1px solid {ClipFlowTheme.BORDER};")
        header_layout = QHBoxLayout(header)
        
        self.title = QLabel("新建项目")
        self.title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.title)
        
        header_layout.addStretch()
        
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        header_layout.addWidget(btn_cancel)
        
        main_layout.addWidget(header)
        
        # 内容区
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # 左侧预览
        preview = QWidget()
        preview.setStyleSheet(f"background: {ClipFlowTheme.BG_ELEVATED}; border-right: 1px solid {ClipFlowTheme.BORDER};")
        preview_layout = QVBoxLayout(preview)
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.preview_box = QFrame()
        self.preview_box.setMinimumSize(600, 400)
        self.preview_box.setStyleSheet(f"""
            QFrame {{
                background: {ClipFlowTheme.BG_CARD};
                border: 2px dashed {ClipFlowTheme.BORDER};
                border-radius: {ClipFlowTheme.RADIUS}px;
            }}
        """)
        preview_box_layout = QVBoxLayout(self.preview_box)
        preview_box_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.preview_icon = QLabel("📹")
        self.preview_icon.setStyleSheet("font-size: 48px;")
        preview_box_layout.addWidget(self.preview_icon)
        
        self.preview_text = QLabel("点击选择视频")
        self.preview_text.setStyleSheet(f"color: {ClipFlowTheme.TEXT_DIM};")
        preview_box_layout.addWidget(self.preview_text)
        
        preview_layout.addWidget(self.preview_box)
        
        # 右侧AI功能
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(24, 24, 24, 24)
        
        # AI功能卡片
        self._create_ai_card("🎙️", "AI 解说", "分析视频生成解说词并配音")
        self._create_ai_card("📝", "字幕生成", "Whisper语音识别生成字幕")
        self._create_ai_card("🎵", "Beat-Sync", "自动对齐节拍制作混剪")
        self._create_ai_card("🔍", "质量分析", "检测视频问题")
        
        sidebar_layout.addStretch()
        
        # 表单
        form_group = QGroupBox("项目设置")
        form_layout = QVBoxLayout(form_group)
        
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("项目名称"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入项目名称")
        name_layout.addWidget(self.name_input)
        form_layout.addLayout(name_layout)
        
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("解说模板"))
        self.template_combo = QComboBox()
        self.template_combo.addItems(["B站知识解说", "电影解说", "产品测评", "自定义"])
        template_layout.addWidget(self.template_combo)
        form_layout.addLayout(template_layout)
        
        sidebar_layout.addWidget(form_group)
        
        content_layout.addWidget(preview, 1)
        content_layout.addWidget(sidebar, 400)
        
        main_layout.addWidget(content)
        
        # 底部栏
        footer = QWidget()
        footer.setStyleSheet(f"background: {ClipFlowTheme.BG}; border-top: 1px solid {ClipFlowTheme.BORDER};")
        footer_layout = QHBoxLayout(footer)
        footer_layout.addStretch()
        
        btn_save = QPushButton("保存项目")
        btn_save.setObjectName("primary")
        btn_save.setStyleSheet(f"""
            QPushButton#primary {{
                background: {ClipFlowTheme.ACCENT};
                color: #000;
                border: none;
                border-radius: {ClipFlowTheme.RADIUS}px;
                padding: 10px 24px;
                font-weight: bold;
            }}
        """)
        btn_save.clicked.connect(self._on_save)
        footer_layout.addWidget(btn_save)
        
        main_layout.addWidget(footer)
    
    def _create_ai_card(self, icon, title, desc):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {ClipFlowTheme.BG_CARD};
                border: 1px solid {ClipFlowTheme.BORDER};
                border-radius: {ClipFlowTheme.RADIUS}px;
                padding: 12px;
            }}
            QFrame:hover {{ border-color: {ClipFlowTheme.ACCENT}; }}
        """)
        
        layout = QVBoxLayout(card)
        
        header = QHBoxLayout()
        header.addWidget(QLabel(icon))
        header.addWidget(QLabel(title))
        layout.addLayout(header)
        
        desc_label = QLabel(desc)
        desc_label.setStyleSheet(f"font-size: 12px; color: {ClipFlowTheme.TEXT_DIM};")
        layout.addWidget(desc_label)
        
        self.parent().findChild(QWidget).parent().findChild(QWidget).layout().insertWidget(0, card)


class ClipFlowMainWindow(QMainWindow):
    """
    ClipFlow 主窗口
    
    结构:
    - 首页: 项目列表
    - 设置: 主题/临时文件/API Key
    - 编辑面板: 在项目管理中内嵌（对话框形式）
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ClipFlow - AI 视频创作")
        self.setMinimumSize(1000, 600)
        self.resize(1200, 700)
        
        self._apply_theme()
        self._init_ui()
        self._init_menu()
        
        # 加载示例项目
        self._load_demo_projects()
    
    def _apply_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(ClipFlowTheme.BG))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(ClipFlowTheme.TEXT))
        palette.setColor(QPalette.ColorRole.Base, QColor(ClipFlowTheme.BG_ELEVATED))
        palette.setColor(QPalette.ColorRole.Text, QColor(ClipFlowTheme.TEXT))
        self.setPalette(palette)
    
    def _init_ui(self):
        # 堆叠窗口
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # 首页
        self.home_page = HomePage()
        self.home_page.new_project_clicked.connect(self._show_new_project)
        self.home_page.edit_project_clicked.connect(self._show_edit_project)
        self.stack.addWidget(self.home_page)
        
        # 设置页
        self.settings_page = SettingsPage()
        self.stack.addWidget(self.settings_page)
        
        # 底部导航（用工具栏模拟）
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, toolbar)
        
        btn_home = QPushButton("首页")
        btn_home.setCheckable(True)
        btn_home.setChecked(True)
        btn_home.clicked.connect(lambda: self._show_page(0))
        toolbar.addWidget(btn_home)
        
        btn_settings = QPushButton("设置")
        btn_settings.setCheckable(True)
        btn_settings.clicked.connect(lambda: self._show_page(1))
        toolbar.addWidget(btn_settings)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
    
    def _show_page(self, index):
        self.stack.setCurrentIndex(index)
    
    def _init_menu(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("文件")
        file_menu.addAction("新建项目", self._show_new_project, QKeySequence("Ctrl+N"))
        file_menu.addSeparator()
        file_menu.addAction("退出", self.close)
        
        help_menu = menubar.addMenu("帮助")
        help_menu.addAction("关于", self._show_about)
    
    def _show_new_project(self):
        dialog = EditPanel(self)
        dialog.title.setText("新建项目")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.status_bar.showMessage("项目已创建")
    
    def _show_edit_project(self, project_id):
        dialog = EditPanel(self)
        dialog.title.setText("编辑项目")
        dialog.name_input.setText(f"项目 {project_id}")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.status_bar.showMessage("项目已保存")
    
    def _show_about(self):
        QMessageBox.about(self, "关于", "<h3>ClipFlow</h3><p>AI 驱动的视频创作工具</p><p>版本 2.0.0</p>")
    
    def _load_demo_projects(self):
        """加载示例项目"""
        projects = [
            {"id": 1, "name": "B站知识解说模板", "meta": "2024-01-15 • 视频: 1个"},
            {"id": 2, "name": "Beat-Sync 混剪", "meta": "2024-01-14 • 视频: 5个"},
            {"id": 3, "name": "字幕翻译项目", "meta": "2024-01-13 • 视频: 3个"},
        ]
        self.home_page.load_projects(projects)


def demo():
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    window = ClipFlowMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    demo()
