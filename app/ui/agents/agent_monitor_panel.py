"""
Agent 监控面板
显示所有Agent的状态和协作情况
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton, QGridLayout,
    QSplitter, QTabWidget, QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from ...agents.base_agent import BaseAgent
from ...agents.agent_manager import AgentManager
from .agent_card import AgentCard


class AgentMonitorPanel(QFrame):
    """Agent 监控面板"""
    
    # 信号
    agent_selected = pyqtSignal(str)  # agent_id
    task_requested = pyqtSignal(dict)  # task
    
    def __init__(self, agent_manager: AgentManager = None, parent=None):
        super().__init__(parent)
        
        self.agent_manager = agent_manager
        self.agent_cards = {}  # agent_id -> AgentCard
        
        self._setup_ui()
        self._setup_style()
        self._start_update_timer()
        
    def _setup_ui(self):
        """设置UI"""
        self.setMinimumWidth(350)
        self.setMaximumWidth(450)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # 标题
        title_layout = QHBoxLayout()
        
        title = QLabel("🎬 Agent 协作监控")
        title.setFont(QFont("SF Pro Display", 18, QFont.Weight.Bold))
        title_layout.addWidget(title)
        
        title_layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(32, 32)
        refresh_btn.setToolTip("刷新")
        refresh_btn.clicked.connect(self._refresh_agents)
        title_layout.addWidget(refresh_btn)
        
        layout.addLayout(title_layout)
        
        # 统计信息
        self.stats_frame = QFrame()
        stats_layout = QHBoxLayout(self.stats_frame)
        stats_layout.setContentsMargins(12, 12, 12, 12)
        
        self.total_label = QLabel("总Agent: 0")
        self.active_label = QLabel("工作中: 0")
        self.idle_label = QLabel("空闲: 0")
        self.error_label = QLabel("错误: 0")
        
        for label in [self.total_label, self.active_label, self.idle_label, self.error_label]:
            label.setFont(QFont("SF Pro Text", 11))
            stats_layout.addWidget(label)
            
        stats_layout.addStretch()
        layout.addWidget(self.stats_frame)
        
        # Agent卡片区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(12)
        self.cards_layout.addStretch()
        
        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll)
        
        # 底部控制
        control_layout = QHBoxLayout()
        
        self.start_all_btn = QPushButton("▶️ 全部启动")
        self.start_all_btn.clicked.connect(self._start_all_agents)
        control_layout.addWidget(self.start_all_btn)
        
        self.stop_all_btn = QPushButton("⏹️ 全部停止")
        self.stop_all_btn.clicked.connect(self._stop_all_agents)
        control_layout.addWidget(self.stop_all_btn)
        
        control_layout.addStretch()
        
        self.reset_all_btn = QPushButton("🔄 重置全部")
        self.reset_all_btn.clicked.connect(self._reset_all_agents)
        control_layout.addWidget(self.reset_all_btn)
        
        layout.addLayout(control_layout)
        
    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            QFrame {
                background-color: #f5f5f7;
                border-radius: 16px;
            }
            QLabel {
                color: #1a1a1a;
                background: transparent;
            }
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        self.stats_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        
    def set_agent_manager(self, agent_manager: AgentManager):
        """设置Agent管理器"""
        self.agent_manager = agent_manager
        self._refresh_agents()
        
    def _refresh_agents(self):
        """刷新Agent列表"""
        if not self.agent_manager:
            return
            
        # 清除现有卡片
        for card in self.agent_cards.values():
            card.deleteLater()
        self.agent_cards.clear()
        
        # 获取所有Agent
        agents = self.agent_manager.get_all_agents()
        
        # 创建卡片
        for agent in agents:
            card = AgentCard(agent)
            card.clicked.connect(self._on_agent_clicked)
            card.action_triggered.connect(self._on_agent_action)
            
            self.agent_cards[agent.agent_id] = card
            self.cards_layout.insertWidget(
                self.cards_layout.count() - 1,
                card
            )
            
        # 更新统计
        self._update_stats()
        
    def _update_stats(self):
        """更新统计信息"""
        if not self.agent_manager:
            return
            
        stats = self.agent_manager.get_system_stats()
        
        self.total_label.setText(f"总Agent: {stats.get('total_agents', 0)}")
        self.active_label.setText(f"工作中: {stats.get('working_agents', 0)}")
        self.idle_label.setText(f"空闲: {stats.get('idle_agents', 0)}")
        self.error_label.setText(f"错误: {stats.get('error_agents', 0)}")
        
    def _start_update_timer(self):
        """启动更新定时器"""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_stats)
        self.update_timer.start(2000)  # 每2秒更新
        
    def _on_agent_clicked(self, agent_id: str):
        """Agent卡片点击"""
        self.agent_selected.emit(agent_id)
        
    def _on_agent_action(self, agent_id: str, action: str):
        """Agent操作"""
        if not self.agent_manager:
            return
            
        if action == "reset":
            self.agent_manager.reset_agent(agent_id)
            
    def _start_all_agents(self):
        """启动所有Agent"""
        if self.agent_manager:
            self.agent_manager.start_all()
            
    def _stop_all_agents(self):
        """停止所有Agent"""
        if self.agent_manager:
            self.agent_manager.stop_all()
            
    def _reset_all_agents(self):
        """重置所有Agent"""
        if self.agent_manager:
            self.agent_manager.reset_all()
            
    def add_agent_card(self, agent: BaseAgent):
        """添加Agent卡片"""
        if agent.agent_id in self.agent_cards:
            return
            
        card = AgentCard(agent)
        card.clicked.connect(self._on_agent_clicked)
        card.action_triggered.connect(self._on_agent_action)
        
        self.agent_cards[agent.agent_id] = card
        self.cards_layout.insertWidget(
            self.cards_layout.count() - 1,
            card
        )
        
        self._update_stats()
        
    def remove_agent_card(self, agent_id: str):
        """移除Agent卡片"""
        if agent_id in self.agent_cards:
            self.agent_cards[agent_id].deleteLater()
            del self.agent_cards[agent_id]
            self._update_stats()
            
    def update_agent_progress(self, agent_id: str, progress: int, message: str):
        """更新Agent进度"""
        if agent_id in self.agent_cards:
            self.agent_cards[agent_id].agent.report_progress(progress, message)
