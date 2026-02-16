"""
协作仪表盘 - 简化版
显示多Agent协作状态和项目进度
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QProgressBar, QPushButton, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from ...agents.agent_manager import AgentManager


class CollaborationDashboard(QFrame):
    """协作仪表盘 - 简化版"""
    
    project_started = pyqtSignal(str)
    project_stopped = pyqtSignal(str)
    
    def __init__(self, agent_manager: AgentManager = None, parent=None):
        super().__init__(parent)
        self.agent_manager = agent_manager
        self._setup_ui()
        self._setup_style()
        self._start_update_timer()
        
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title = QLabel("🎬 Agent 协作状态")
        title.setFont(QFont("SF Pro Display", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 统计卡片
        stats_layout = QHBoxLayout()
        
        self.stat_labels = {}
        for key, label_text in [
            ('working', '工作中'),
            ('idle', '空闲'),
            ('error', '错误'),
            ('tasks', '任务')
        ]:
            card = QFrame()
            card.setFixedSize(100, 70)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 8, 8, 8)
            
            value = QLabel("0")
            value.setFont(QFont("SF Pro Display", 20, QFont.Weight.Bold))
            value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stat_labels[key] = value
            card_layout.addWidget(value)
            
            label = QLabel(label_text)
            label.setFont(QFont("SF Pro Text", 10))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #666;")
            card_layout.addWidget(label)
            
            card.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 8px;
                    border: 1px solid #e0e0e0;
                }
            """)
            stats_layout.addWidget(card)
            
        layout.addLayout(stats_layout)
        
        # 当前任务进度
        progress_frame = QFrame()
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(12, 12, 12, 12)
        
        self.current_task_label = QLabel("当前任务: 无")
        self.current_task_label.setFont(QFont("SF Pro Text", 12))
        progress_layout.addWidget(self.current_task_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        progress_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
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
        layout.addWidget(progress_frame)
        
        # 日志区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ 开始")
        self.start_btn.clicked.connect(self._start_collaboration)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️ 停止")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_collaboration)
        control_layout.addWidget(self.stop_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            QFrame {
                background-color: #f5f5f7;
            }
            QTextEdit {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
                padding: 8px;
                font-family: monospace;
                font-size: 11px;
            }
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        
    def _start_update_timer(self):
        """启动更新定时器"""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_dashboard)
        self.update_timer.start(1000)
        
    def _update_dashboard(self):
        """更新仪表盘"""
        if not self.agent_manager:
            return
            
        stats = self.agent_manager.get_system_stats()
        
        self.stat_labels['working'].setText(str(stats.get('working_agents', 0)))
        self.stat_labels['idle'].setText(str(stats.get('idle_agents', 0)))
        self.stat_labels['error'].setText(str(stats.get('error_agents', 0)))
        self.stat_labels['tasks'].setText(str(stats.get('running_tasks', 0)))
        
    def _start_collaboration(self):
        """开始协作"""
        if self.agent_manager:
            self.agent_manager.start()
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.add_log("[系统] Agent协作已启动")
            
    def _stop_collaboration(self):
        """停止协作"""
        if self.agent_manager:
            self.agent_manager.stop()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.add_log("[系统] Agent协作已停止")
            
    def set_agent_manager(self, agent_manager: AgentManager):
        """设置Agent管理器"""
        self.agent_manager = agent_manager
        agent_manager.task_completed.connect(lambda tid, r: self.add_log(f"[完成] {tid}"))
        agent_manager.task_failed.connect(lambda tid, e: self.add_log(f"[失败] {tid}: {e}"))
        
    def set_progress(self, task_name: str, progress: int):
        """设置进度"""
        self.current_task_label.setText(f"当前任务: {task_name}")
        self.progress_bar.setValue(progress)
        
    def add_log(self, message: str):
        """添加日志"""
        self.log_text.append(message)
