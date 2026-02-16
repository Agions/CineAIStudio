"""
CineFlow v3.0 主窗口
多Agent智能视频剪辑系统 - PyQt6 UI
"""

import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame,
    QScrollArea, QGridLayout, QProgressBar, QTextEdit,
    QFileDialog, QMessageBox, QSplitter, QTabWidget,
    QListWidget, QListWidgetItem, QMenuBar, QMenu,
    QStatusBar, QToolBar, QDockWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QAction, QIcon, QFont, QPalette, QColor

# 导入Agent系统
from app.agents import (
    AgentManager, DirectorAgent, EditorAgent,
    ColoristAgent, SoundAgent, VFXAgent, ReviewerAgent,
    AgentState
)
from app.core import ProjectManager, VideoProcessor, DraftExporter


class AgentCard(QFrame):
    """Agent状态卡片"""
    
    def __init__(self, name: str, agent_type: str, parent=None):
        super().__init__(parent)
        self.name = name
        self.agent_type = agent_type
        self.status = AgentState.IDLE
        
        self._setup_ui()
        
    def _setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            AgentCard {
                background-color: #1E1E1E;
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # 名称
        name_label = QLabel(self.name)
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        layout.addWidget(name_label)
        
        # 类型
        type_label = QLabel(self.agent_type)
        type_label.setStyleSheet("font-size: 12px; color: #888888;")
        layout.addWidget(type_label)
        
        layout.addSpacing(8)
        
        # 状态
        self.status_label = QLabel("空闲")
        self.status_label.setStyleSheet("""
            font-size: 12px;
            color: #00C853;
            padding: 4px 8px;
            background-color: #00C85322;
            border-radius: 4px;
        """)
        layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #333333;
                border-radius: 4px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #2962FF;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 消息
        self.message_label = QLabel("等待任务...")
        self.message_label.setStyleSheet("font-size: 11px; color: #666666;")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
        
    def update_status(self, state: AgentState, progress: int = 0, message: str = ""):
        """更新状态"""
        self.status = state
        
        status_text = {
            AgentState.IDLE: ("空闲", "#00C853", "#00C85322"),
            AgentState.WORKING: ("工作中", "#2962FF", "#2962FF22"),
            AgentState.PAUSED: ("暂停", "#FFD600", "#FFD60022"),
            AgentState.ERROR: ("错误", "#FF1744", "#FF174422"),
            AgentState.STOPPED: ("停止", "#888888", "#88888822"),
        }
        
        text, color, bg = status_text.get(state, ("未知", "#888888", "#88888822"))
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"""
            font-size: 12px;
            color: {color};
            padding: 4px 8px;
            background-color: {bg};
            border-radius: 4px;
        """)
        
        self.progress_bar.setValue(progress)
        if message:
            self.message_label.setText(message)


class AgentMonitorPage(QWidget):
    """Agent监控页面"""
    
    def __init__(self, agent_manager: AgentManager, parent=None):
        super().__init__(parent)
        self.agent_manager = agent_manager
        self.agent_cards: dict = {}
        
        self._setup_ui()
        self._setup_timer()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # 标题
        title = QLabel("🤖 Agent 监控中心")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        # 系统状态概览
        self.status_summary = QLabel()
        self.status_summary.setStyleSheet("""
            font-size: 14px;
            color: #888888;
            padding: 12px;
            background-color: #1E1E1E;
            border-radius: 8px;
        """)
        layout.addWidget(self.status_summary)
        
        # Agent卡片网格
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(16)
        
        # 创建Agent卡片
        agents = [
            ("Director", "导演 - DeepSeek-V3", "director"),
            ("Editor", "剪辑 - Kimi K2.5", "editor"),
            ("Colorist", "调色 - Kimi K2.5", "colorist"),
            ("Sound", "音效 - Qwen 2.5", "sound"),
            ("VFX", "特效 - Kimi K2.5", "vfx"),
            ("Reviewer", "审核 - DeepSeek-Coder", "reviewer"),
        ]
        
        for i, (name, agent_type, key) in enumerate(agents):
            card = AgentCard(name, agent_type)
            self.agent_cards[key] = card
            grid.addWidget(card, i // 3, i % 3)
            
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # 任务队列
        layout.addSpacing(16)
        task_title = QLabel("📋 任务队列")
        task_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        layout.addWidget(task_title)
        
        self.task_list = QListWidget()
        self.task_list.setStyleSheet("""
            QListWidget {
                background-color: #1E1E1E;
                border: 1px solid #333333;
                border-radius: 8px;
                color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #333333;
            }
        """)
        layout.addWidget(self.task_list)
        
    def _setup_timer(self):
        """设置定时刷新"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_status)
        self.timer.start(1000)  # 每秒刷新
        
    def _refresh_status(self):
        """刷新状态"""
        stats = self.agent_manager.get_system_stats()
        
        # 更新概览
        summary = f"""
        <b>系统状态</b> | 
        Agent: {stats['total_agents']} 个 | 
        工作中: {stats['working_agents']} | 
        空闲: {stats['idle_agents']} | 
        任务: {stats['pending_tasks']} 待处理 / {stats['running_tasks']} 运行中 / {stats['completed_tasks']} 已完成
        """
        self.status_summary.setText(summary)
        
        # 更新Agent卡片
        for agent_id, agent in self.agent_manager.agents.items():
            key = agent_id.split('_')[0].lower()
            if key in self.agent_cards:
                card = self.agent_cards[key]
                progress = agent.progress if hasattr(agent, 'progress') else 0
                message = agent.current_task if hasattr(agent, 'current_task') else ""
                card.update_status(agent.state, progress, message)
                
        # 更新任务列表
        self.task_list.clear()
        for task in self.agent_manager.task_queue:
            item_text = f"[{task.status.name}] {task.task_type} - {task.task_id}"
            item = QListWidgetItem(item_text)
            self.task_list.addItem(item)


class ProjectPage(QWidget):
    """项目管理页面"""
    
    project_created = pyqtSignal(str)  # project_id
    
    def __init__(self, project_manager: ProjectManager, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # 标题
        title = QLabel("🎬 项目管理")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        self.new_btn = QPushButton("➕ 新建项目")
        self.new_btn.setStyleSheet(self._button_style())
        self.new_btn.clicked.connect(self._create_project)
        btn_layout.addWidget(self.new_btn)
        
        self.import_btn = QPushButton("📥 导入项目")
        self.import_btn.setStyleSheet(self._button_style())
        btn_layout.addWidget(self.import_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 项目列表
        self.project_list = QListWidget()
        self.project_list.setStyleSheet("""
            QListWidget {
                background-color: #1E1E1E;
                border: 1px solid #333333;
                border-radius: 8px;
                color: white;
            }
            QListWidget::item {
                padding: 16px;
                border-bottom: 1px solid #333333;
            }
            QListWidget::item:hover {
                background-color: #2C2C2C;
            }
        """)
        layout.addWidget(self.project_list)
        
        self._refresh_projects()
        
    def _button_style(self):
        return """
            QPushButton {
                background-color: #2962FF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #448AFF;
            }
        """
        
    def _create_project(self):
        """创建新项目"""
        # 选择视频文件
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择视频素材", "",
            "视频文件 (*.mp4 *.mov *.avi *.mkv);;所有文件 (*.*)"
        )
        
        if files:
            project = self.project_manager.create_project(
                name=f"项目_{len(self.project_manager.get_all_projects()) + 1}",
                source_files=files
            )
            self.project_created.emit(project.id)
            self._refresh_projects()
            
    def _refresh_projects(self):
        """刷新项目列表"""
        self.project_list.clear()
        for project in self.project_manager.get_all_projects():
            item_text = f"{project.name} | 状态: {project.status.name} | 创建于: {project.created_at.strftime('%Y-%m-%d %H:%M')}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, project.id)
            self.project_list.addItem(item)


class MainWindow(QMainWindow):
    """CineFlow v3.0 主窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("CineFlow v3.0 - 多Agent智能视频剪辑")
        self.setMinimumSize(1600, 1000)
        
        # 初始化核心组件
        self._init_core()
        
        # 初始化UI
        self._init_ui()
        
        # 应用暗色主题
        self._apply_dark_theme()
        
    def _init_core(self):
        """初始化核心组件"""
        # Agent系统
        self.agent_manager = AgentManager()
        self.agent_manager.register_agent(DirectorAgent())
        self.agent_manager.register_agent(EditorAgent())
        self.agent_manager.register_agent(ColoristAgent())
        self.agent_manager.register_agent(SoundAgent())
        self.agent_manager.register_agent(VFXAgent())
        self.agent_manager.register_agent(ReviewerAgent())
        self.agent_manager.start()
        
        # 项目管理
        self.project_manager = ProjectManager()
        
        print(f"✅ 系统初始化完成 - {len(self.agent_manager.agents)} 个Agent已就绪")
        
    def _init_ui(self):
        """初始化UI"""
        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QHBoxLayout(central)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 左侧导航
        nav = self._create_navigation()
        layout.addWidget(nav)
        
        # 主内容区
        self.stack = QStackedWidget()
        
        # Agent监控页面
        self.agent_page = AgentMonitorPage(self.agent_manager)
        self.stack.addWidget(self.agent_page)
        
        # 项目管理页面
        self.project_page = ProjectPage(self.project_manager)
        self.project_page.project_created.connect(self._on_project_created)
        self.stack.addWidget(self.project_page)
        
        # 创作页面 (占位)
        self.creator_page = QLabel("🎨 创作中心 - 开发中")
        self.creator_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.creator_page.setStyleSheet("font-size: 24px; color: #666666;")
        self.stack.addWidget(self.creator_page)
        
        # 导出页面 (占位)
        self.export_page = QLabel("📦 导出中心 - 开发中")
        self.export_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.export_page.setStyleSheet("font-size: 24px; color: #666666;")
        self.stack.addWidget(self.export_page)
        
        layout.addWidget(self.stack, 1)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 定时刷新状态栏
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_status_bar)
        self.status_timer.start(2000)
        
    def _create_navigation(self) -> QWidget:
        """创建导航栏"""
        nav = QFrame()
        nav.setFixedWidth(240)
        nav.setStyleSheet("""
            QFrame {
                background-color: #1E1E1E;
                border-right: 1px solid #333333;
            }
        """)
        
        layout = QVBoxLayout(nav)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 24, 16, 24)
        
        # Logo
        logo = QLabel("🎬 CineFlow")
        logo.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        layout.addWidget(logo)
        
        version = QLabel("v3.0.0")
        version.setStyleSheet("font-size: 12px; color: #666666;")
        layout.addWidget(version)
        
        layout.addSpacing(32)
        
        # 导航按钮
        nav_items = [
            ("🤖 Agent监控", 0),
            ("🎬 项目管理", 1),
            ("✨ 创作中心", 2),
            ("📦 导出中心", 3),
        ]
        
        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 12px 16px;
                    border: none;
                    border-radius: 6px;
                    color: #B0B0B0;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2C2C2C;
                    color: white;
                }
                QPushButton:checked {
                    background-color: #2962FF22;
                    color: #2962FF;
                }
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=index: self._switch_page(i))
            layout.addWidget(btn)
            
            if index == 0:
                btn.setChecked(True)
                
        layout.addStretch()
        
        return nav
        
    def _switch_page(self, index: int):
        """切换页面"""
        self.stack.setCurrentIndex(index)
        
        # 更新按钮状态
        for i in range(self.stack.count()):
            btn = self.sender().parent().findChildren(QPushButton)[i + 2]  # 跳过logo和version
            btn.setChecked(i == index)
            
    def _on_project_created(self, project_id: str):
        """项目创建回调"""
        self.status_bar.showMessage(f"项目创建成功: {project_id}", 3000)
        
    def _update_status_bar(self):
        """更新状态栏"""
        stats = self.agent_manager.get_system_stats()
        text = f"Agent: {stats['working_agents']}/{stats['total_agents']} 工作中 | 任务: {stats['pending_tasks']} 待处理"
        self.status_bar.showMessage(text)
        
    def _apply_dark_theme(self):
        """应用暗色主题"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QWidget {
                background-color: #121212;
                color: #FFFFFF;
                font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
            }
            QScrollBar:vertical {
                background-color: #1E1E1E;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #444444;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #555555;
            }
        """)
        
    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(
            self, "确认退出",
            "确定要退出 CineFlow 吗?\n正在运行的任务将被取消。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 停止Agent管理器
            self.agent_manager.stop()
            event.accept()
        else:
            event.ignore()


def main():
    """主入口"""
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setApplicationName("CineFlow")
    app.setApplicationVersion("3.0.0")
    
    # 设置字体
    font = QFont("Inter", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
