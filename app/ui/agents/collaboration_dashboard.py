"""
协作仪表盘
显示多Agent协作的整体状态和项目进度
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QProgressBar, QPushButton, QScrollArea,
    QGridLayout, QSplitter, QTextEdit, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush

from ...agents.agent_manager import AgentManager
from ...agents.base_agent import BaseAgent, AgentState


class ProjectTimelineWidget(QFrame):
    """项目时间线组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)
        self.tasks = []
        
    def set_tasks(self, tasks):
        """设置任务列表"""
        self.tasks = tasks
        self.update()
        
    def paintEvent(self, event):
        """绘制时间线"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # 绘制背景
        painter.fillRect(self.rect(), QColor("#f5f5f7"))
        
        if not self.tasks:
            return
            
        # 计算位置
        task_width = width / len(self.tasks)
        
        for i, task in enumerate(self.tasks):
            x = i * task_width + 10
            y = 20
            w = task_width - 20
            h = height - 40
            
            # 根据状态设置颜色
            status = task.get('status', 'pending')
            colors = {
                'pending': ('#e0e0e0', '#9e9e9e'),
                'running': ('#2196F3', '#1976D2'),
                'completed': ('#4CAF50', '#388E3C'),
                'failed': ('#f44336', '#d32f2f')
            }
            bg_color, border_color = colors.get(status, colors['pending'])
            
            # 绘制任务块
            painter.setBrush(QBrush(QColor(bg_color)))
            painter.setPen(QPen(QColor(border_color), 2))
            painter.drawRoundedRect(int(x), y, int(w), h, 8, 8)
            
            # 绘制任务名
            painter.setPen(QPen(QColor("#1a1a1a")))
            painter.setFont(QFont("SF Pro Text", 10))
            painter.drawText(int(x) + 8, y + 20, task.get('name', 'Task'))
            
            # 绘制进度
            progress = task.get('progress', 0)
            if progress > 0:
                painter.fillRect(
                    int(x) + 2, y + h - 10,
                    int((w - 4) * progress / 100), 6,
                    QColor(border_color)
                )


class CollaborationDashboard(QFrame):
    """协作仪表盘"""
    
    # 信号
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
        title = QLabel("🎬 Agent 协作仪表盘")
        title.setFont(QFont("SF Pro Display", 20, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 顶部统计卡片
        stats_layout = QHBoxLayout()
        
        self.stat_cards = {}
        for key, label, icon in [
            ('active', '活跃项目', '📊'),
            ('agents', '工作Agent', '🤖'),
            ('progress', '总进度', '📈'),
            ('queue', '待处理', '⏳')
        ]:
            card = self._create_stat_card(icon, label, "0")
            self.stat_cards[key] = card
            stats_layout.addWidget(card)
            
        layout.addLayout(stats_layout)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 上半部分：项目时间线
        timeline_widget = QWidget()
        timeline_layout = QVBoxLayout(timeline_widget)
        
        timeline_title = QLabel("项目时间线")
        timeline_title.setFont(QFont("SF Pro Display", 14, QFont.Weight.Bold))
        timeline_layout.addWidget(timeline_title)
        
        self.timeline = ProjectTimelineWidget()
        timeline_layout.addWidget(self.timeline)
        
        splitter.addWidget(timeline_widget)
        
        # 下半部分：标签页
        tabs = QTabWidget()
        
        # Agent状态页
        self.agent_status_text = QTextEdit()
        self.agent_status_text.setReadOnly(True)
        tabs.addTab(self.agent_status_text, "Agent状态")
        
        # 任务队列页
        self.task_queue_text = QTextEdit()
        self.task_queue_text.setReadOnly(True)
        tabs.addTab(self.task_queue_text, "任务队列")
        
        # 日志页
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        tabs.addTab(self.log_text, "运行日志")
        
        splitter.addWidget(tabs)
        splitter.setSizes([200, 300])
        
        layout.addWidget(splitter)
        
        # 底部控制
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ 开始协作")
        self.start_btn.setFixedHeight(40)
        self.start_btn.clicked.connect(self._start_collaboration)
        control_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("⏸️ 暂停")
        self.pause_btn.setFixedHeight(40)
        self.pause_btn.setEnabled(False)
        control_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("⏹️ 停止")
        self.stop_btn.setFixedHeight(40)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_collaboration)
        control_layout.addWidget(self.stop_btn)
        
        control_layout.addStretch()
        
        self.new_project_btn = QPushButton("➕ 新建项目")
        self.new_project_btn.setFixedHeight(40)
        control_layout.addWidget(self.new_project_btn)
        
        layout.addLayout(control_layout)
        
    def _create_stat_card(self, icon: str, label: str, value: str) -> QFrame:
        """创建统计卡片"""
        card = QFrame()
        card.setFixedSize(150, 80)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("SF Pro", 20))
        layout.addWidget(icon_label)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("SF Pro Display", 18, QFont.Weight.Bold))
        value_label.setObjectName(f"stat_value_{label}")
        self.stat_cards[label] = value_label
        layout.addWidget(value_label)
        
        label_widget = QLabel(label)
        label_widget.setFont(QFont("SF Pro Text", 11))
        label_widget.setStyleSheet("color: #666;")
        layout.addWidget(label_widget)
        
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        return card
        
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
                padding: 12px;
                font-family: "SF Mono", "Consolas", monospace;
                font-size: 12px;
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
            QTabWidget::pane {
                border: none;
                background-color: white;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 4px;
                border-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #007AFF;
                color: white;
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
        
        # 更新统计卡片
        if 'active' in self.stat_cards:
            self.stat_cards['active'].setText(str(stats.get('running_tasks', 0)))
        if 'agents' in self.stat_cards:
            self.stat_cards['agents'].setText(str(stats.get('working_agents', 0)))
        if 'queue' in self.stat_cards:
            self.stat_cards['queue'].setText(str(stats.get('pending_tasks', 0)))
            
        # 更新Agent状态
        self._update_agent_status()
        
        # 更新任务队列
        self._update_task_queue()
        
    def _update_agent_status(self):
        """更新Agent状态显示"""
        if not self.agent_manager:
            return
            
        text = []
        for agent in self.agent_manager.get_all_agents():
            stats = agent.get_stats()
            text.append(f"[{agent.name}] {agent.state.name}")
            text.append(f"  任务: {stats['tasks_completed']}/{stats['tasks_completed'] + stats['tasks_failed']}")
            text.append(f"  耗时: {stats['avg_execution_time']:.1f}s")
            text.append("")
            
        self.agent_status_text.setText("\n".join(text))
        
    def _update_task_queue(self):
        """更新任务队列显示"""
        if not self.agent_manager:
            return
            
        text = []
        for task in self.agent_manager.get_all_tasks():
            text.append(f"[{task.task_id}] {task.task_type}")
            text.append(f"  状态: {task.status.name}")
            text.append(f"  Agent: {task.assigned_agent or '未分配'}")
            text.append("")
            
        self.task_queue_text.setText("\n".join(text))
        
    def _start_collaboration(self):
        """开始协作"""
        if self.agent_manager:
            self.agent_manager.start()
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.log_text.append("[系统] 协作已启动")
            
    def _stop_collaboration(self):
        """停止协作"""
        if self.agent_manager:
            self.agent_manager.stop()
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.log_text.append("[系统] 协作已停止")
            
    def set_agent_manager(self, agent_manager: AgentManager):
        """设置Agent管理器"""
        self.agent_manager = agent_manager
        
        # 连接信号
        agent_manager.task_completed.connect(self._on_task_completed)
        agent_manager.task_failed.connect(self._on_task_failed)
        
    def _on_task_completed(self, task_id: str, result):
        """任务完成回调"""
        self.log_text.append(f"[完成] 任务 {task_id}")
        
    def _on_task_failed(self, task_id: str, error: str):
        """任务失败回调"""
        self.log_text.append(f"[失败] 任务 {task_id}: {error}")
        
    def add_log(self, message: str):
        """添加日志"""
        self.log_text.append(message)
