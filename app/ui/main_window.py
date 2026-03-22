"""
ClipFlow 主窗口 UI - 简化版

AI 优先的极简界面设计
"""

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QPalette, QColor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QDockWidget, QToolBar, QMenuBar, QMenu,
    QStatusBar, QLabel, QPushButton,
    QFrame, QGroupBox, QTabWidget, QListWidget,
    QFileDialog, QMessageBox, QLineEdit,
    QComboBox, QCheckBox, QSpinBox, QSlider, QProgressBar,
    QStackedWidget, QScrollArea,
)


class ClipFlowTheme:
    """ClipFlow 主题 - 极简深色"""
    
    BG = "#0A0A0B"
    BG_ELEVATED = "#141416"
    BG_CARD = "#1A1A1D"
    BORDER = "#2A2A2E"
    TEXT = "#FAFAFA"
    TEXT_DIM = "#71717A"
    ACCENT = "#00D4FF"
    ACCENT_DIM = "rgba(0, 212, 255, 0.15)"
    SUCCESS = "#22C55E"
    RADIUS = 12


class ClipFlowMainWindow(QMainWindow):
    """
    ClipFlow 主窗口 - 简化版
    
    布局:
    ┌──────────────────────────────────────────────────┐
    │  Logo   [AI创作] [项目] [设置]              保存  │
    ├─────────────────────────────┬────────────────────┤
    │                             │                    │
    │     视频预览/拖拽区         │   AI 功能卡片       │
    │                             │                    │
    │     [拖拽视频到这里]        │   🎙️ AI解说       │
    │                             │   📝 字幕生成      │
    │                             │   🎵 Beat-Sync     │
    │                             │   🔍 质量分析      │
    │                             │                    │
    │                             │   [模板] [配音]     │
    │                             │                    │
    │                             │   [导出按钮]       │
    └─────────────────────────────┴────────────────────┘
    """
    
    # 信号
    media_imported = pyqtSignal(list)
    ai_task_started = pyqtSignal(str)
    ai_task_finished = pyqtSignal(str, bool)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ClipFlow - AI 视频创作")
        self.setMinimumSize(1000, 600)
        self.resize(1200, 700)
        
        self._apply_theme()
        self._init_ui()
        self._init_menu()
        self._init_connections()
        
        self.current_file = None
        self.is_processing = False
    
    def _apply_theme(self):
        """应用极简深色主题"""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(self.BG))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(self.TEXT))
        palette.setColor(QPalette.ColorRole.Base, QColor(self.BG_ELEVATED))
        palette.setColor(QPalette.ColorRole.Text, QColor(self.TEXT))
        palette.setColor(QPalette.ColorRole.Button, QColor(self.BG_CARD))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(self.TEXT))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(self.ACCENT))
        self.setPalette(palette)
        
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {self.BG}; }}
            QMenuBar {{ background-color: {self.BG}; color: {self.TEXT}; border-bottom: 1px solid {self.BORDER}; }}
            QMenuBar::item:selected {{ background-color: {self.BG_ELEVATED}; }}
            QMenu {{ background-color: {self.BG_ELEVATED}; color: {self.TEXT}; border: 1px solid {self.BORDER}; }}
            QMenu::item:selected {{ background-color: {self.BG_CARD}; }}
            QPushButton {{ background-color: {self.BG_CARD}; color: {self.TEXT}; border: 1px solid {self.BORDER}; border-radius: {self.RADIUS}px; padding: 10px 20px; }}
            QPushButton:hover {{ border-color: {self.ACCENT}; }}
            QPushButton#primary {{ background-color: {self.ACCENT}; color: #000; border: none; font-weight: bold; }}
            QPushButton#primary:hover {{ opacity: 0.9; }}
            QLabel {{ color: {self.TEXT}; }}
            QDockWidget {{ color: {self.TEXT}; border: 1px solid {self.BORDER}; }}
            QDockWidget::title {{ background-color: {self.BG_ELEVATED}; padding: 8px; }}
            QStatusBar {{ background-color: {self.BG}; color: {self.TEXT_DIM}; border-top: 1px solid {self.BORDER}; }}
            QGroupBox {{ color: {self.TEXT_DIM}; border: 1px solid {self.BORDER}; border-radius: {self.RADIUS}px; margin-top: 12px; font-size: 13px; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 4px; }}
            QLineEdit, QComboBox, QSpinBox {{ background-color: {self.BG_ELEVATED}; color: {self.TEXT}; border: 1px solid {self.BORDER}; border-radius: 8px; padding: 8px 12px; }}
            QLineEdit:focus, QComboBox:focus {{ border-color: {self.ACCENT}; }}
        """)
    
    def _init_ui(self):
        """初始化UI"""
        # 中央部件 - 工作区
        self.central = self._create_workspace()
        self.setCentralWidget(self.central)
        
        # 右侧面板 - AI 功能
        self.ai_panel = self._create_ai_panel()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.ai_panel)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
    
    def _create_workspace(self) -> QWidget:
        """创建工作区"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # 拖拽区域
        self.drop_zone = QFrame()
        self.drop_zone.setMinimumSize(600, 400)
        self.drop_zone.setStyleSheet(f"""
            QFrame {{
                background-color: {self.BG_ELEVATED};
                border: 2px dashed {self.BORDER};
                border-radius: {self.RADIUS}px;
            }}
            QFrame:hover {{
                border-color: {self.ACCENT};
                background-color: {self.ACCENT_DIM};
            }}
        """)
        
        drop_layout = QVBoxLayout(self.drop_zone)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.drop_icon = QLabel("📹")
        self.drop_icon.setStyleSheet("font-size: 48px; opacity: 0.5;")
        drop_layout.addWidget(self.drop_icon)
        
        self.drop_text = QLabel("拖拽视频到这里\n或点击选择文件")
        self.drop_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_text.setStyleSheet(f"color: {self.TEXT_DIM}; font-size: 14px;")
        drop_layout.addWidget(self.drop_text)
        
        # 文件信息（隐藏直到选择文件）
        self.file_info = QWidget()
        self.file_info.setVisible(False)
        file_layout = QVBoxLayout(self.file_info)
        file_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.file_name = QLabel("video.mp4")
        self.file_name.setStyleSheet("font-size: 16px; font-weight: bold;")
        file_layout.addWidget(self.file_name)
        
        self.file_meta = QLabel("1920×1080 • 02:34 • 45MB")
        self.file_meta.setStyleSheet(f"color: {self.TEXT_DIM}; font-size: 13px;")
        file_layout.addWidget(self.file_meta)
        
        drop_layout.addWidget(self.file_info)
        
        # 点击选择文件
        self.drop_zone.mousePressEvent = lambda e: self._import_media()
        
        layout.addWidget(self.drop_zone, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return widget
    
    def _create_ai_panel(self) -> QDockWidget:
        """创建AI功能面板"""
        dock = QDockWidget("AI 功能", self)
        dock.setMinimumWidth(320)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # AI 功能卡片
        self.ai_cards = QWidget()
        cards_layout = QVBoxLayout(self.ai_cards)
        cards_layout.setSpacing(12)
        
        # AI 解说
        self.card_commentary = self._create_ai_card("🎙️", "AI 解说", "分析视频内容，自动生成解说词并配音")
        cards_layout.addWidget(self.card_commentary)
        
        # 字幕生成
        self.card_subtitle = self._create_ai_card("📝", "字幕生成", "Whisper 语音识别，自动生成字幕")
        cards_layout.addWidget(self.card_subtitle)
        
        # Beat-Sync
        self.card_beatsync = self._create_ai_card("🎵", "Beat-Sync 混剪", "自动对齐节拍，制作节奏感强的混剪")
        cards_layout.addWidget(self.card_beatsync)
        
        # 质量分析
        self.card_analysis = self._create_ai_card("🔍", "质量分析", "检测分辨率、亮度、音频等问题")
        cards_layout.addWidget(self.card_analysis)
        
        layout.addWidget(self.ai_cards)
        
        # 设置区域
        settings_group = QGroupBox("设置")
        settings_layout = QGridLayout()
        
        settings_layout.addWidget(QLabel("模板"), 0, 0)
        self.template_combo = QComboBox()
        self.template_combo.addItems(["B站知识解说", "电影解说", "产品测评", "自定义"])
        settings_layout.addWidget(self.template_combo, 0, 1)
        
        settings_layout.addWidget(QLabel("配音"), 1, 0)
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["晓雅（女声）", "云飞（男声）"])
        settings_layout.addWidget(self.voice_combo, 1, 1)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        layout.addStretch()
        
        # 导出选项
        export_group = QGroupBox("导出")
        export_layout = QVBoxLayout(export_group)
        
        format_layout = QHBoxLayout()
        self.format_btns = []
        for fmt in ["MP4", "SRT", "TXT", "剪映"]:
            btn = QPushButton(fmt)
            btn.setCheckable(True)
            if fmt == "MP4":
                btn.setChecked(True)
            btn.setStyleSheet(f"""
                QPushButton {{ background-color: {self.BG_ELEVATED}; 
                              border: 1px solid {self.BORDER}; 
                              border-radius: 6px; padding: 8px; min-width: 0; }}
                QPushButton:checked {{ background-color: {self.ACCENT_DIM}; 
                                      border-color: {self.ACCENT}; color: {self.ACCENT}; }}
            """)
            self.format_btns.append(btn)
            format_layout.addWidget(btn)
        
        export_layout.addLayout(format_layout)
        
        self.btn_export = QPushButton("导出视频")
        self.btn_export.setObjectName("primary")
        self.btn_export.setStyleSheet(f"""
            QPushButton#primary {{ 
                background-color: {self.ACCENT}; color: #000; border: none; 
                border-radius: {self.RADIUS}px; padding: 12px; font-weight: bold; 
            }}
            QPushButton#primary:hover {{ opacity: 0.9; }}
        """)
        export_layout.addWidget(self.btn_export)
        
        layout.addWidget(export_group)
        
        dock.setWidget(widget)
        return dock
    
    def _create_ai_card(self, icon: str, title: str, desc: str) -> QFrame:
        """创建AI功能卡片"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.BG_CARD};
                border: 1px solid {self.BORDER};
                border-radius: {self.RADIUS}px;
                padding: 16px;
            }}
            QFrame:hover {{
                border-color: {self.ACCENT};
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20px;")
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        header.addWidget(title_label)
        
        header.addStretch()
        layout.addLayout(header)
        
        desc_label = QLabel(desc)
        desc_label.setStyleSheet(f"color: {self.TEXT_DIM}; font-size: 12px;")
        layout.addWidget(desc_label)
        
        return frame
    
    def _init_menu(self):
        """初始化菜单"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        file_menu.addAction("导入媒体", self._import_media, QKeySequence("Ctrl+I"))
        file_menu.addAction("保存项目", self._save_project, QKeySequence("Ctrl+S"))
        file_menu.addSeparator()
        file_menu.addAction("退出", self.close)
        
        # AI 菜单
        ai_menu = menubar.addMenu("AI 功能")
        ai_menu.addAction("AI 解说", lambda: self._run_ai_task("commentary"))
        ai_menu.addAction("字幕生成", lambda: self._run_ai_task("subtitle"))
        ai_menu.addAction("Beat-Sync", lambda: self._run_ai_task("beatsync"))
        ai_menu.addAction("质量分析", lambda: self._run_ai_task("analysis"))
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        help_menu.addAction("关于", self._show_about)
    
    def _init_connections(self):
        """初始化连接"""
        self.btn_export.clicked.connect(self._export)
        
        # AI 卡片点击
        self.card_commentary.mousePressEvent = lambda e: self._run_ai_task("commentary")
        self.card_subtitle.mousePressEvent = lambda e: self._run_ai_task("subtitle")
        self.card_beatsync.mousePressEvent = lambda e: self._run_ai_task("beatsync")
        self.card_analysis.mousePressEvent = lambda e: self._run_ai_task("analysis")
    
    def _import_media(self):
        """导入媒体"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择视频",
            "", "视频文件 (*.mp4 *.mov *.avi *.mkv);;所有文件 (*.*)"
        )
        
        if path:
            self.current_file = path
            from pathlib import Path
            name = Path(path).name
            
            self.drop_zone.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.BG_ELEVATED};
                    border: 2px solid {self.SUCCESS};
                    border-radius: {self.RADIUS}px;
                }}
            """)
            self.drop_icon.setVisible(False)
            self.drop_text.setVisible(False)
            
            self.file_name.setText(name)
            self.file_meta.setText("1920×1080 • 02:34 • 45MB")
            self.file_info.setVisible(True)
            
            self.status_bar.showMessage(f"已导入: {name}")
    
    def _run_ai_task(self, task: str):
        """运行AI任务"""
        if not self.current_file:
            QMessageBox.information(self, "提示", "请先导入视频文件")
            return
        
        task_names = {
            "commentary": "AI 解说生成",
            "subtitle": "字幕生成",
            "beatsync": "Beat-Sync 混剪",
            "analysis": "质量分析"
        }
        
        self.status_bar.showMessage(f"正在处理: {task_names.get(task, task)}...")
        self.ai_task_started.emit(task)
    
    def _export(self):
        """导出"""
        if not self.current_file:
            QMessageBox.information(self, "提示", "请先导入视频并处理")
            return
        
        # 获取选中的格式
        selected_fmt = "MP4"
        for btn in self.format_btns:
            if btn.isChecked():
                selected_fmt = btn.text()
                break
        
        self.status_bar.showMessage(f"正在导出 {selected_fmt}...")
    
    def _save_project(self):
        """保存项目"""
        self.status_bar.showMessage("项目已保存")
    
    def _show_about(self):
        """显示关于"""
        QMessageBox.about(
            self, "关于 ClipFlow",
            "<h3>ClipFlow</h3>"
            "<p>AI 驱动的视频创作工具</p>"
            "<p>版本 2.0.0</p>"
        )


def demo():
    """演示"""
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    window = ClipFlowMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    demo()
