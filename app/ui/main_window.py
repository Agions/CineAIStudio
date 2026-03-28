"""
VideoForge 主窗口 - 全新设计

结构:
- 首页: 项目列表（增删改查）
- 设置: 主题/临时文件/API Key
- 编辑面板: 全屏对话框
"""

from PySide6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PySide6.QtGui import QAction, QKeySequence, QPalette, QColor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QToolBar, QMenuBar, QMenu, QStatusBar,
    QLabel, QPushButton, QFrame, QGroupBox,
    QLineEdit, QComboBox, QCheckBox,
    QDialog, QStackedWidget, QScrollArea, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QSlider,
)


class Theme:
    """VideoForge 主题 - 现代简洁风格"""
    BG = "#09090B"
    BG_2 = "#111113"
    BG_3 = "#18181B"
    BG_4 = "#27272A"
    BORDER = "#3F3F46"
    TEXT = "#FAFAFA"
    TEXT_2 = "#A1A1AA"
    TEXT_3 = "#71717A"
    ACCENT = "#10B981"  # 绿色
    ACCENT_DIM = "rgba(16, 185, 129, 0.15)"
    ACCENT_2 = "#6366F1"
    DANGER = "#EF4444"
    RADIUS = 8
    RADIUS_LG = 12


class HomePage(QWidget):
    """首页 - 项目列表"""
    
    new_clicked = pyqtSignal()
    edit_clicked = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # 标题栏
        header = QWidget()
        h_layout = QHBoxLayout(header)
        
        title = QLabel("我的项目")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        h_layout.addWidget(title)
        
        btn_new = QPushButton("+ 新建项目")
        btn_new.setObjectName("primary")
        btn_new.setStyleSheet(f"""
            QPushButton#primary {{
                background: {Theme.ACCENT};
                color: #000;
                border: none;
                border-radius: {Theme.RADIUS}px;
                padding: 10px 20px;
                font-weight: 600;
            }}
            QPushButton#primary:hover {{ background: #059669; }}
        """)
        btn_new.clicked.connect(self.new_clicked.emit)
        h_layout.addWidget(btn_new)
        
        layout.addWidget(header)
        
        # 项目列表
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
        """)
        layout.addWidget(self.list_widget)
    
    def load_projects(self, projects):
        self.list_widget.clear()
        for p in projects:
            self._add_project(p)
    
    def _add_project(self, project):
        item = QListWidgetItem()
        item.setData(Qt.UserRole, project["id"])
        
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {Theme.BG_2};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_LG}px;
                padding: 16px;
            }}
            QFrame:hover {{ border-color: {Theme.ACCENT}; }}
        """)
        
        layout = QVBoxLayout(card)
        
        # 缩略图
        thumb = QLabel("🎬")
        thumb.setStyleSheet(f"""
            font-size: 36px;
            background: {Theme.BG_3};
            border-radius: {Theme.RADIUS}px;
            min-height: 100px;
        """)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(thumb)
        
        # 信息
        name = QLabel(project.get("name", ""))
        name.setStyleSheet("font-size: 14px; font-weight: 600;")
        layout.addWidget(name)
        
        meta = QLabel(project.get("meta", ""))
        meta.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_3};")
        layout.addWidget(meta)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        btn_edit = QPushButton("编辑")
        btn_edit.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.BG_3};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{ border-color: {Theme.ACCENT}; }}
        """)
        btn_edit.clicked.connect(lambda: self.edit_clicked.emit(project["id"]))
        
        btn_del = QPushButton("删除")
        btn_del.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {Theme.DANGER};
                color: {Theme.DANGER};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background: {Theme.DANGER}; color: #fff; }}
        """)
        
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_del)
        layout.addLayout(btn_layout)
        
        item.setSizeHint(card.sizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, card)


class SettingsPage(QWidget):
    """设置页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        
        # 外观
        container_layout.addWidget(self._make_section("外观", [
            ("主题", "应用界面配色方案", "select", ["深色", "浅色", "跟随系统"]),
        ]))
        
        # 文件
        container_layout.addWidget(self._make_section("文件", [
            ("临时文件位置", "缓存和临时文件存放目录", "text", ["/tmp/clipflow"]),
            ("自动清理临时文件", "退出时自动删除缓存", "toggle", [True]),
        ]))
        
        # AI 服务
        container_layout.addWidget(self._make_section("AI 服务", [
            ("大模型", "用于生成解说和字幕翻译", "select", ["GPT-4 (OpenAI)", "DeepSeek", "智谱 GLM"]),
            ("API Key", "你的 API 密钥", "password", []),
            ("语音合成", "用于生成解说配音", "select", ["Edge TTS（免费）", "Azure TTS"]),
        ]))
        
        # 导出
        container_layout.addWidget(self._make_section("导出", [
            ("默认格式", "新建项目时的导出格式", "select", ["MP4", "MOV", "SRT"]),
            ("默认分辨率", "视频输出分辨率", "select", ["1920×1080 (1080P)", "1280×720", "3840×2160"]),
        ]))
        
        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)
    
    def _make_section(self, title, items):
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 12px;
                color: {Theme.TEXT_3};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS_LG}px;
                margin-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }}
        """)
        
        layout = QVBoxLayout(group)
        
        for label, desc, widget_type, options in items:
            item = QFrame()
            item.setStyleSheet(f"""
                QFrame {{
                    border-bottom: 1px solid {Theme.BORDER};
                    padding: 12px 16px;
                }}
                QFrame:last-child {{ border-bottom: none; }}
            """)
            item_layout = QHBoxLayout(item)
            
            info = QWidget()
            info_layout = QVBoxLayout(info)
            info_layout.setContentsMargins(0, 0, 0, 0)
            
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 14px;")
            info_layout.addWidget(lbl)
            
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_3};")
            info_layout.addWidget(desc_lbl)
            
            item_layout.addWidget(info, 1)
            
            if widget_type == "select":
                combo = QComboBox()
                combo.addItems(options)
                combo.setStyleSheet(f"""
                    QComboBox {{
                        background: {Theme.BG_3};
                        border: 1px solid {Theme.BORDER};
                        border-radius: {Theme.RADIUS}px;
                        padding: 8px 12px;
                        min-width: 140px;
                    }}
                """)
                item_layout.addWidget(combo)
            elif widget_type == "text":
                inp = QLineEdit()
                inp.setText(options[0] if options else "")
                inp.setStyleSheet(f"""
                    QLineEdit {{
                        background: {Theme.BG_3};
                        border: 1px solid {Theme.BORDER};
                        border-radius: {Theme.RADIUS}px;
                        padding: 8px 12px;
                        min-width: 200px;
                    }}
                """)
                item_layout.addWidget(inp)
            elif widget_type == "password":
                inp = QLineEdit()
                inp.setPlaceholderText("sk-...")
                inp.setEchoMode(QLineEdit.EchoMode.Password)
                inp.setStyleSheet(f"""
                    QLineEdit {{
                        background: {Theme.BG_3};
                        border: 1px solid {Theme.BORDER};
                        border-radius: {Theme.RADIUS}px;
                        padding: 8px 12px;
                        min-width: 200px;
                    }}
                """)
                item_layout.addWidget(inp)
            elif widget_type == "toggle":
                toggle = QCheckBox()
                toggle.setChecked(options[0] if options else False)
                toggle.setStyleSheet(f"""
                    QCheckBox {{
                        width: 44px;
                        height: 24px;
                    }}
                """)
                item_layout.addWidget(toggle)
            
            layout.addWidget(item)
        
        return group


class EditDialog(QDialog):
    """编辑对话框"""
    
    saved = pyqtSignal(dict)
    
    def __init__(self, parent=None, mode="new", project_id=None):
        super().__init__(parent)
        self.mode = mode
        self.project_id = project_id
        self.setWindowTitle("编辑项目")
        self.resize(1200, 700)
        self.setModal(True)
        self._init_ui()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 顶部栏
        header = QWidget()
        header.setStyleSheet(f"background: {Theme.BG_2}; border-bottom: 1px solid {Theme.BORDER};")
        header_layout = QHBoxLayout(header)
        
        title = QLabel("新建项目" if self.mode == "new" else "编辑项目")
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        btn_cancel = QPushButton("取消")
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.BG_3};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS}px;
                padding: 8px 16px;
            }}
        """)
        btn_cancel.clicked.connect(self.reject)
        header_layout.addWidget(btn_cancel)
        
        main_layout.addWidget(header)
        
        # 内容区
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # 左侧预览
        preview = QWidget()
        preview.setStyleSheet(f"background: #000; border-right: 1px solid {Theme.BORDER};")
        preview_layout = QVBoxLayout(preview)
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.dropzone = QFrame()
        self.dropzone.setMinimumSize(600, 400)
        self.dropzone.setStyleSheet(f"""
            QFrame {{
                background: {Theme.BG_3};
                border: 2px dashed {Theme.BORDER};
                border-radius: {Theme.RADIUS_LG}px;
            }}
        """)
        drop_layout = QVBoxLayout(self.dropzone)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.drop_icon = QLabel("📹")
        self.drop_icon.setStyleSheet("font-size: 48px;")
        drop_layout.addWidget(self.drop_icon)
        
        self.drop_text = QLabel("点击选择视频")
        self.drop_text.setStyleSheet(f"color: {Theme.TEXT_3}; font-size: 14px;")
        drop_layout.addWidget(self.drop_text)
        
        preview_layout.addWidget(self.dropzone)
        
        # 右侧工具
        sidebar = QWidget()
        sidebar.setStyleSheet(f"background: {Theme.BG_2};")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        
        # AI 工具卡片
        tools_label = QLabel("AI 工具")
        tools_label.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_3}; margin-bottom: 8px;")
        sidebar_layout.addWidget(tools_label)
        
        self._add_tool_card(sidebar_layout, "🎙️", "AI 解说", "分析视频生成解说词并配音")
        self._add_tool_card(sidebar_layout, "📝", "字幕生成", "Whisper 语音识别生成字幕")
        self._add_tool_card(sidebar_layout, "🎵", "Beat-Sync", "自动对齐节拍制作混剪")
        self._add_tool_card(sidebar_layout, "🔍", "质量分析", "检测视频问题")
        
        sidebar_layout.addStretch()
        
        # 表单
        form_label = QLabel("项目设置")
        form_label.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_3}; margin-bottom: 8px;")
        sidebar_layout.addWidget(form_label)
        
        form_group = QGroupBox()
        form_group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS}px;
                padding: 16px;
            }}
        """)
        form_layout = QVBoxLayout(form_group)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("项目名称")
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                background: {Theme.BG_3};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS}px;
                padding: 10px 12px;
            }}
        """)
        form_layout.addWidget(self.name_input)
        
        self.template_combo = QComboBox()
        self.template_combo.addItems(["B站知识解说", "电影解说", "产品测评", "自定义"])
        self.template_combo.setStyleSheet(f"""
            QComboBox {{
                background: {Theme.BG_3};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS}px;
                padding: 10px 12px;
            }}
        """)
        form_layout.addWidget(self.template_combo)
        
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["晓雅（女声）", "云飞（男声）"])
        self.voice_combo.setStyleSheet(f"""
            QComboBox {{
                background: {Theme.BG_3};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS}px;
                padding: 10px 12px;
            }}
        """)
        form_layout.addWidget(self.voice_combo)
        
        sidebar_layout.addWidget(form_group)
        
        content_layout.addWidget(preview, 1)
        content_layout.addWidget(sidebar, 360)
        
        main_layout.addWidget(content)
        
        # 底部栏
        footer = QWidget()
        footer.setStyleSheet(f"background: {Theme.BG_2}; border-top: 1px solid {Theme.BORDER};")
        footer_layout = QHBoxLayout(footer)
        footer_layout.addStretch()
        
        btn_save = QPushButton("保存项目")
        btn_save.setObjectName("primary")
        btn_save.setStyleSheet(f"""
            QPushButton#primary {{
                background: {Theme.ACCENT};
                color: #000;
                border: none;
                border-radius: {Theme.RADIUS}px;
                padding: 10px 24px;
                font-weight: 600;
            }}
            QPushButton#primary:hover {{ background: #059669; }}
        """)
        btn_save.clicked.connect(self._on_save)
        footer_layout.addWidget(btn_save)
        
        main_layout.addWidget(footer)
    
    def _add_tool_card(self, parent, icon, title, desc):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {Theme.BG_3};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.RADIUS}px;
                padding: 12px;
                margin-bottom: 8px;
            }}
            QFrame:hover {{ border-color: {Theme.ACCENT}; }}
        """)
        layout = QVBoxLayout(card)
        
        header = QHBoxLayout()
        header.addWidget(QLabel(icon))
        header.addWidget(QLabel(title))
        layout.addLayout(header)
        
        desc_label = QLabel(desc)
        desc_label.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_3};")
        layout.addWidget(desc_label)
        
        parent.addWidget(card)
    
    def _on_save(self):
        self.accept()


class VideoForgeMainWindow(QMainWindow):
    """VideoForge 主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VideoForge - AI 视频创作")
        self.setMinimumSize(1000, 600)
        self.resize(1200, 700)
        
        self._apply_theme()
        self._init_ui()
        self._init_menu()
        self._load_projects()
    
    def _apply_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(Theme.BG))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(Theme.TEXT))
        self.setPalette(palette)
    
    def _init_ui(self):
        # 堆叠窗口
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # 首页
        self.home_page = HomePage()
        self.home_page.new_clicked.connect(lambda: self._open_edit("new"))
        self.home_page.edit_clicked.connect(lambda id: self._open_edit("edit", id))
        self.stack.addWidget(self.home_page)
        
        # 设置页
        self.settings_page = SettingsPage()
        self.stack.addWidget(self.settings_page)
        
        # 底部标签栏
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setStyleSheet(f"""
            QToolBar {{
                background: {Theme.BG_2};
                border-top: 1px solid {Theme.BORDER};
                padding: 8px 16px;
            }}
        """)
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, toolbar)
        
        btn_home = QPushButton("首页")
        btn_home.setCheckable(True)
        btn_home.setChecked(True)
        btn_home.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.ACCENT_DIM};
                color: {Theme.ACCENT};
                border: none;
                border-radius: {Theme.RADIUS}px;
                padding: 8px 16px;
            }}
        """)
        btn_home.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        toolbar.addWidget(btn_home)
        
        btn_settings = QPushButton("设置")
        btn_settings.setCheckable(True)
        btn_settings.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.TEXT_2};
                border: none;
                border-radius: {Theme.RADIUS}px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ background: {Theme.BG_3}; }}
        """)
        btn_settings.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        toolbar.addWidget(btn_settings)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background: {Theme.BG_2};
                color: {Theme.TEXT_3};
                border-top: 1px solid {Theme.BORDER};
                font-size: 12px;
            }}
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
    
    def _init_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet(f"""
            QMenuBar {{
                background: {Theme.BG_2};
                color: {Theme.TEXT};
                border-bottom: 1px solid {Theme.BORDER};
            }}
            QMenuBar::item:selected {{ background: {Theme.BG_3}; }}
        """)
        
        file_menu = menubar.addMenu("文件")
        file_menu.addAction("新建项目", lambda: self._open_edit("new"), QKeySequence("Ctrl+N"))
        file_menu.addSeparator()
        file_menu.addAction("退出", self.close)
        
        help_menu = menubar.addMenu("帮助")
        help_menu.addAction("关于", self._show_about)
    
    def _open_edit(self, mode, project_id=None):
        dialog = EditDialog(self, mode, project_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_projects()
            self.status_bar.showMessage("项目已保存")
    
    def _show_about(self):
        QMessageBox.about(self, "关于", "<h3>VideoForge</h3><p>AI 驱动的视频创作工具</p><p>版本 2.0.0</p>")
    
    def _load_projects(self):
        projects = [
            {"id": 1, "name": "B站知识解说", "meta": "2024-01-15 • 视频: 1个"},
            {"id": 2, "name": "Beat-Sync 混剪", "meta": "2024-01-14 • 视频: 5个"},
            {"id": 3, "name": "字幕翻译", "meta": "2024-01-13 • 视频: 3个"},
        ]
        self.home_page.load_projects(projects)


def main():
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = VideoForgeMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
