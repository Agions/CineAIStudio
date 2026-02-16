"""
Agent 卡片组件
显示单个Agent的状态和信息
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from ...agents.base_agent import BaseAgent, AgentState


class AgentCard(QFrame):
    """Agent 状态卡片"""
    
    # 信号
    clicked = pyqtSignal(str)  # agent_id
    action_triggered = pyqtSignal(str, str)  # agent_id, action
    
    # 状态颜色映射
    STATE_COLORS = {
        AgentState.IDLE: ("#4CAF50", "#E8F5E9"),      # 绿色
        AgentState.WORKING: ("#2196F3", "#E3F2FD"),   # 蓝色
        AgentState.WAITING: ("#FF9800", "#FFF3E0"),   # 橙色
        AgentState.ERROR: ("#F44336", "#FFEBEE"),     # 红色
        AgentState.COMPLETED: ("#9C27B0", "#F3E5F5"), # 紫色
    }
    
    def __init__(self, agent: BaseAgent, parent=None):
        super().__init__(parent)
        
        self.agent = agent
        self.agent_id = agent.agent_id
        self.agent_name = agent.name
        
        self._setup_ui()
        self._setup_style()
        self._connect_signals()
        self._start_update_timer()
        
    def _setup_ui(self):
        """设置UI"""
        self.setFixedSize(280, 180)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 头部：名称和状态
        header_layout = QHBoxLayout()
        
        self.name_label = QLabel(self.agent_name)
        self.name_label.setFont(QFont("SF Pro Display", 14, QFont.Weight.Bold))
        header_layout.addWidget(self.name_label)
        
        header_layout.addStretch()
        
        self.status_badge = QLabel("IDLE")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setFixedSize(60, 24)
        header_layout.addWidget(self.status_badge)
        
        layout.addLayout(header_layout)
        
        # Agent ID
        self.id_label = QLabel(f"ID: {self.agent_id}")
        self.id_label.setFont(QFont("SF Pro Text", 10))
        layout.addWidget(self.id_label)
        
        # 能力标签
        capabilities = [c.value for c in self.agent.get_capabilities()]
        self.cap_label = QLabel(f"能力: {', '.join(capabilities) if capabilities else '通用'}")
        self.cap_label.setFont(QFont("SF Pro Text", 10))
        layout.addWidget(self.cap_label)
        
        layout.addStretch()
        
        # 进度条
        self.progress_label = QLabel("进度: 0%")
        self.progress_label.setFont(QFont("SF Pro Text", 11))
        layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        layout.addWidget(self.progress_bar)
        
        # 统计信息
        stats_layout = QHBoxLayout()
        
        self.task_count_label = QLabel("任务: 0")
        self.task_count_label.setFont(QFont("SF Pro Text", 10))
        stats_layout.addWidget(self.task_count_label)
        
        stats_layout.addStretch()
        
        self.time_label = QLabel("耗时: 0s")
        self.time_label.setFont(QFont("SF Pro Text", 10))
        stats_layout.addWidget(self.time_label)
        
        layout.addLayout(stats_layout)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("重置")
        self.reset_btn.setFixedHeight(32)
        self.reset_btn.clicked.connect(lambda: self.action_triggered.emit(self.agent_id, "reset"))
        btn_layout.addWidget(self.reset_btn)
        
        self.details_btn = QPushButton("详情")
        self.details_btn.setFixedHeight(32)
        self.details_btn.clicked.connect(lambda: self.clicked.emit(self.agent_id))
        btn_layout.addWidget(self.details_btn)
        
        layout.addLayout(btn_layout)
        
    def _setup_style(self):
        """设置样式"""
        self.setObjectName("agentCard")
        
        # 阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        # 初始状态样式
        self._update_status_style(AgentState.IDLE)
        
    def _connect_signals(self):
        """连接信号"""
        # 连接Agent信号
        self.agent.state_changed.connect(self._on_state_changed)
        self.agent.progress_updated.connect(self._on_progress_updated)
        self.agent.task_completed.connect(self._on_task_completed)
        self.agent.error_occurred.connect(self._on_error)
        
    def _start_update_timer(self):
        """启动更新定时器"""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_stats)
        self.update_timer.start(1000)  # 每秒更新
        
    def _update_status_style(self, state: AgentState):
        """更新状态样式"""
        border_color, bg_color = self.STATE_COLORS.get(state, ("#757575", "#F5F5F5"))
        
        self.setStyleSheet(f"""
            QFrame#agentCard {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 12px;
            }}
            QLabel {{
                color: #1a1a1a;
                background: transparent;
            }}
            QProgressBar {{
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {border_color};
                border-radius: 3px;
            }}
            QPushButton {{
                background-color: {border_color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {border_color};
                opacity: 0.8;
            }}
        """)
        
        # 更新状态标签
        self.status_badge.setText(state.name)
        self.status_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {border_color};
                color: white;
                border-radius: 12px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: bold;
            }}
        """)
        
    def _on_state_changed(self, agent_id: str, new_state: str):
        """状态变化回调"""
        try:
            state = AgentState[new_state]
            self._update_status_style(state)
        except KeyError:
            pass
            
    def _on_progress_updated(self, agent_id: str, progress: int, message: str):
        """进度更新回调"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(f"进度: {progress}% - {message}")
        
    def _on_task_completed(self, agent_id: str, result):
        """任务完成回调"""
        self._update_stats()
        
    def _on_error(self, agent_id: str, error: str):
        """错误回调"""
        self.progress_label.setText(f"错误: {error[:30]}...")
        
    def _update_stats(self):
        """更新统计信息"""
        stats = self.agent.get_stats()
        
        self.task_count_label.setText(
            f"任务: {stats.get('tasks_completed', 0)}/{stats.get('tasks_completed', 0) + stats.get('tasks_failed', 0)}"
        )
        
        avg_time = stats.get('avg_execution_time', 0)
        self.time_label.setText(f"耗时: {avg_time:.1f}s")
        
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.agent_id)
        super().mousePressEvent(event)
        
    def update_agent(self, agent: BaseAgent):
        """更新Agent引用"""
        self.agent = agent
        self._connect_signals()
        self._update_stats()
