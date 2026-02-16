"""
Agent 工作空间页面 - 简化版
聚焦核心功能：选择视频 -> Agent协同制作 -> 完成
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSplitter, QFileDialog,
    QMessageBox, QProgressBar, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent
from pathlib import Path

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
    log = pyqtSignal(str)
    
    def __init__(self, video_path: str, output_dir: str):
        super().__init__()
        self.video_path = video_path
        self.output_dir = output_dir
        
    def run(self):
        """运行Agent制作"""
        try:
            import asyncio
            
            # 创建项目
            config = AgentCommentaryConfig(
                use_editor=True,
                use_colorist=True,
                use_sound=True,
                use_vfx=False,
                use_reviewer=True
            )
            
            maker = AgentCommentaryMaker(config=config)
            
            # 设置进度回调
            def on_progress(stage: str, progress: float):
                self.progress.emit(stage, int(progress))
                
            maker.set_progress_callback(on_progress)
            
            # 创建项目
            project = CommentaryProject(
                name=Path(self.video_path).stem,
                source_video=self.video_path,
                topic="AI视频解说",
                style=CommentaryStyle.STORYTELLING,
                output_dir=self.output_dir
            )
            
            self.log.emit("[系统] 开始Agent协同制作...")
            
            # 运行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                maker.create_with_agents(project)
            )
            loop.close()
            
            if result.get('success'):
                self.completed.emit(result)
            else:
                self.error.emit(result.get('message', '制作失败'))
                
        except Exception as e:
            self.error.emit(str(e))


class AgentWorkspacePage(QFrame):
    """Agent工作空间页面 - 简化版"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.agent_manager = None
        self.worker = None
        self._setup_ui()
        self._setup_style()
        self._init_agents()
        self.setAcceptDrops(True)
        
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title = QLabel("🎬 Agent 协同剪辑")
        title.setFont(QFont("SF Pro Display", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：Agent监控
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Agent监控面板
        self.agent_panel = AgentMonitorPanel()
        left_layout.addWidget(self.agent_panel)
        
        splitter.addWidget(left_widget)
        
        # 右侧：核心工作区
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)
        
        # 1. 视频选择区
        self.drop_zone = QFrame()
        self.drop_zone.setFixedHeight(100)
        drop_layout = QVBoxLayout(self.drop_zone)
        
        self.drop_label = QLabel("📁 拖拽视频到这里\n或点击选择文件")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setFont(QFont("SF Pro Text", 12))
        self.drop_label.mousePressEvent = lambda e: self._select_video()
        drop_layout.addWidget(self.drop_label)
        
        self.drop_zone.setStyleSheet("""
            QFrame {
                background-color: #f5f5f7;
                border: 2px dashed #ccc;
                border-radius: 12px;
            }
            QFrame:hover {
                border-color: #007AFF;
                background-color: #e3f2fd;
            }
        """)
        right_layout.addWidget(self.drop_zone)
        
        # 2. 文件信息
        self.file_info = QLabel("未选择文件")
        self.file_info.setStyleSheet("color: #666;")
        right_layout.addWidget(self.file_info)
        
        # 3. 协作仪表盘
        self.dashboard = CollaborationDashboard()
        right_layout.addWidget(self.dashboard)
        
        # 4. 控制按钮
        btn_layout = QHBoxLayout()
        
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
        
        btn_layout.addStretch()
        right_layout.addLayout(btn_layout)
        
        splitter.addWidget(right_widget)
        splitter.setSizes([350, 600])
        
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
                background-color: #ccc;
            }
        """)
        
    def _init_agents(self):
        """初始化Agent系统"""
        self.agent_manager = AgentManager()
        
        # 注册Agent
        for agent_class in [DirectorAgent, EditorAgent, ColoristAgent, 
                           SoundAgent, VFXAgent, ReviewerAgent]:
            self.agent_manager.register_agent(agent_class())
            
        self.agent_panel.set_agent_manager(self.agent_manager)
        self.dashboard.set_agent_manager(self.agent_manager)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                self._load_video(file_path)
                
    def _select_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频", "", "视频文件 (*.mp4 *.mov *.avi *.mkv)"
        )
        if file_path:
            self._load_video(file_path)
            
    def _load_video(self, file_path: str):
        """加载视频"""
        self.current_video_path = file_path
        file_name = Path(file_path).name
        
        self.file_info.setText(f"📹 {file_name}")
        self.drop_label.setText(f"✅ 已选择: {file_name}\n点击更换文件")
        self.drop_zone.setStyleSheet("""
            QFrame {
                background-color: #e8f5e9;
                border: 2px solid #4CAF50;
                border-radius: 12px;
            }
        """)
        
        self.start_btn.setEnabled(True)
        self.dashboard.add_log(f"[系统] 已加载视频: {file_name}")
        
    def _start_production(self):
        """开始制作"""
        if not hasattr(self, 'current_video_path'):
            QMessageBox.warning(self, "提示", "请先选择视频文件")
            return
            
        output_dir = str(Path.home() / "CineFlow" / "Output")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 启动工作线程
        self.worker = AgentWorker(self.current_video_path, output_dir)
        self.worker.progress.connect(self._on_progress)
        self.worker.completed.connect(self._on_completed)
        self.worker.error.connect(self._on_error)
        self.worker.log.connect(self.dashboard.add_log)
        
        self.worker.start()
        self.agent_manager.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
    def _stop_production(self):
        """停止制作"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            
        self.agent_manager.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.dashboard.add_log("[系统] 已停止")
        
    def _on_progress(self, stage: str, progress: int):
        """进度更新"""
        self.dashboard.set_progress(stage, progress)
        
    def _on_completed(self, result: dict):
        """制作完成"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.dashboard.set_progress("完成", 100)
        
        export_path = result.get('export_result', {}).get('draft_path', '')
        QMessageBox.information(
            self, "完成",
            f"✅ Agent协同制作完成！\n\n"
            f"导出路径: {export_path or '见输出目录'}"
        )
        
    def _on_error(self, error: str):
        """制作错误"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        QMessageBox.critical(self, "错误", f"制作失败:\n{error}")
