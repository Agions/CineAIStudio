"""
Agent 工作空间页面
集成多Agent协同剪辑功能的主界面
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSplitter, QStackedWidget,
    QFileDialog, QMessageBox, QProgressBar, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent

from ....agents.agent_manager import AgentManager
from ....agents.director_agent import DirectorAgent
from ....agents.editor_agent import EditorAgent
from ....agents.colorist_agent import ColoristAgent
from ....agents.sound_agent import SoundAgent
from ....agents.vfx_agent import VFXAgent
from ....agents.reviewer_agent import ReviewerAgent
from ...agents.agent_monitor_panel import AgentMonitorPanel
from ...agents.collaboration_dashboard import CollaborationDashboard
from ....services.video.commentary_maker_agent import (
    AgentCommentaryMaker, AgentCommentaryConfig
)
from ....services.video.commentary_maker import CommentaryProject, CommentaryStyle


class AgentWorker(QThread):
    """Agent工作线程"""
    
    progress = pyqtSignal(str, int)
    completed = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, maker: AgentCommentaryMaker, project: CommentaryProject):
        super().__init__()
        self.maker = maker
        self.project = project
        
    def run(self):
        """运行Agent制作"""
        try:
            import asyncio
            
            # 设置进度回调
            def on_progress(stage: str, progress: float):
                self.progress.emit(stage, int(progress))
                
            self.maker.set_progress_callback(on_progress)
            
            # 运行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.maker.create_with_agents(self.project)
            )
            loop.close()
            
            if result.get('success'):
                self.completed.emit(result)
            else:
                self.error.emit(result.get('message', '制作失败'))
                
        except Exception as e:
            self.error.emit(str(e))


class AgentWorkspacePage(QFrame):
    """Agent工作空间页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.agent_manager = None
        self.current_project = None
        self.worker = None
        
        self._setup_ui()
        self._setup_style()
        self._init_agents()
        
        # 启用拖放
        self.setAcceptDrops(True)
        
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题栏
        title_layout = QHBoxLayout()
        
        title = QLabel("🎬 Agent 协同工作空间")
        title.setFont(QFont("SF Pro Display", 20, QFont.Weight.Bold))
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        # 新建项目按钮
        self.new_btn = QPushButton("➕ 新建项目")
        self.new_btn.setFixedHeight(36)
        self.new_btn.clicked.connect(self._new_project)
        title_layout.addWidget(self.new_btn)
        
        layout.addLayout(title_layout)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：Agent监控面板
        self.agent_panel = AgentMonitorPanel()
        self.agent_panel.setFixedWidth(380)
        splitter.addWidget(self.agent_panel)
        
        # 右侧：主工作区
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 项目信息区
        self.project_frame = QFrame()
        self.project_frame.setFixedHeight(120)
        project_layout = QHBoxLayout(self.project_frame)
        
        # 视频预览/拖放区
        self.drop_zone = QLabel("📁 拖拽视频到这里\n或点击选择文件")
        self.drop_zone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_zone.setFixedSize(160, 100)
        self.drop_zone.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 2px dashed #ccc;
                border-radius: 8px;
                color: #666;
            }
        """)
        self.drop_zone.mousePressEvent = lambda e: self._select_video()
        project_layout.addWidget(self.drop_zone)
        
        # 项目信息
        info_layout = QVBoxLayout()
        
        self.project_name_label = QLabel("未选择项目")
        self.project_name_label.setFont(QFont("SF Pro Display", 14, QFont.Weight.Bold))
        info_layout.addWidget(self.project_name_label)
        
        self.video_info_label = QLabel("请拖拽或选择视频文件")
        self.video_info_label.setStyleSheet("color: #666;")
        info_layout.addWidget(self.video_info_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)
        info_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        info_layout.addWidget(self.status_label)
        
        project_layout.addLayout(info_layout, stretch=1)
        
        # 操作按钮
        btn_layout = QVBoxLayout()
        
        self.start_btn = QPushButton("▶️ 开始制作")
        self.start_btn.setFixedHeight(40)
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._start_production)
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️ 停止")
        self.stop_btn.setFixedHeight(40)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_production)
        btn_layout.addWidget(self.stop_btn)
        
        project_layout.addLayout(btn_layout)
        
        right_layout.addWidget(self.project_frame)
        
        # 协作仪表盘
        self.dashboard = CollaborationDashboard()
        right_layout.addWidget(self.dashboard)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([380, 800])
        
        layout.addWidget(splitter)
        
    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            QFrame {
                background-color: white;
            }
            QLabel {
                color: #1a1a1a;
            }
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #e0e0e0;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #007AFF;
                border-radius: 4px;
            }
        """)
        
    def _init_agents(self):
        """初始化Agent系统"""
        self.agent_manager = AgentManager()
        
        # 创建并注册所有Agent
        director = DirectorAgent()
        self.agent_manager.register_agent(director)
        
        editor = EditorAgent()
        self.agent_manager.register_agent(editor)
        
        colorist = ColoristAgent()
        self.agent_manager.register_agent(colorist)
        
        sound = SoundAgent()
        self.agent_manager.register_agent(sound)
        
        vfx = VFXAgent()
        self.agent_manager.register_agent(vfx)
        
        reviewer = ReviewerAgent()
        self.agent_manager.register_agent(reviewer)
        
        # 绑定到UI
        self.agent_panel.set_agent_manager(self.agent_manager)
        self.dashboard.set_agent_manager(self.agent_manager)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event: QDropEvent):
        """拖拽放下"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                self._load_video(file_path)
                
    def _select_video(self):
        """选择视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.mov *.avi *.mkv)"
        )
        if file_path:
            self._load_video(file_path)
            
    def _load_video(self, file_path: str):
        """加载视频"""
        from pathlib import Path
        
        self.current_video_path = file_path
        file_name = Path(file_path).name
        
        self.project_name_label.setText(f"项目: {file_name}")
        self.video_info_label.setText(f"文件: {file_path}")
        
        self.drop_zone.setText(f"✅\n{file_name}")
        self.drop_zone.setStyleSheet("""
            QLabel {
                background-color: #e8f5e9;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                color: #2e7d32;
            }
        """)
        
        self.start_btn.setEnabled(True)
        
    def _new_project(self):
        """新建项目"""
        self._select_video()
        
    def _start_production(self):
        """开始制作"""
        if not hasattr(self, 'current_video_path'):
            QMessageBox.warning(self, "警告", "请先选择视频文件")
            return
            
        # 创建项目
        config = AgentCommentaryConfig(
            use_editor=True,
            use_colorist=True,
            use_sound=True,
            use_vfx=False,
            use_reviewer=True
        )
        
        maker = AgentCommentaryMaker(config=config)
        
        project = CommentaryProject(
            name="Agent协同解说项目",
            source_video=self.current_video_path,
            topic="AI视频解说",
            style=CommentaryStyle.STORYTELLING,
            output_dir=str(Path.home() / "CineFlow" / "Output")
        )
        
        # 启动工作线程
        self.worker = AgentWorker(maker, project)
        self.worker.progress.connect(self._on_progress)
        self.worker.completed.connect(self._on_completed)
        self.worker.error.connect(self._on_error)
        
        self.worker.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        
        # 启动Agent管理器
        self.agent_manager.start()
        
    def _stop_production(self):
        """停止制作"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            
        self.agent_manager.stop()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("已停止")
        
    def _on_progress(self, stage: str, progress: int):
        """进度更新"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"{stage} ({progress}%)")
        
    def _on_completed(self, result: dict):
        """制作完成"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(100)
        self.status_label.setText("✅ 制作完成")
        
        QMessageBox.information(
            self,
            "完成",
            f"Agent协同制作完成！\n\n{result.get('message', '')}"
        )
        
    def _on_error(self, error: str):
        """制作错误"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText(f"❌ 错误: {error}")
        
        QMessageBox.critical(self, "错误", f"制作失败:\n{error}")
