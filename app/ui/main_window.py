"""
CineFlow v3.0 主窗口
多Agent智能视频剪辑系统 - PyQt6 UI

优化点:
- 样式系统分离
- 异步加载
- 性能优化
- 更好的错误处理
"""

import sys
from pathlib import Path
from typing import Optional, Dict

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame,
    QScrollArea, QGridLayout, QProgressBar,
    QFileDialog, QMessageBox,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont

# 导入Agent系统
from app.agents import (
    AgentManager, DirectorAgent, EditorAgent,
    ColoristAgent, SoundAgent, VFXAgent, ReviewerAgent,
    AgentState
)
from app.core import ProjectManager

# 导入样式系统
from .styles import Styles, StyleHelper, Colors, Dimens


class AsyncInitThread(QThread):
    """异步初始化线程"""
    
    init_progress = pyqtSignal(int, str)
    init_complete = pyqtSignal(object, object)  # agent_manager, project_manager
    init_error = pyqtSignal(str)
    
    def run(self):
        """后台初始化"""
        try:
            self.init_progress.emit(10, "初始化Agent系统...")
            
            # Agent系统
            agent_manager = AgentManager()
            
            self.init_progress.emit(30, "注册Director...")
            agent_manager.register_agent(DirectorAgent())
            
            self.init_progress.emit(40, "注册Editor...")
            agent_manager.register_agent(EditorAgent())
            
            self.init_progress.emit(50, "注册Colorist...")
            agent_manager.register_agent(ColoristAgent())
            
            self.init_progress.emit(60, "注册Sound...")
            agent_manager.register_agent(SoundAgent())
            
            self.init_progress.emit(70, "注册VFX...")
            agent_manager.register_agent(VFXAgent())
            
            self.init_progress.emit(80, "注册Reviewer...")
            agent_manager.register_agent(ReviewerAgent())
            
            self.init_progress.emit(90, "启动Agent管理器...")
            agent_manager.start()
            
            self.init_progress.emit(95, "初始化项目管理...")
            project_manager = ProjectManager()
            
            self.init_progress.emit(100, "完成")
            self.init_complete.emit(agent_manager, project_manager)
            
        except Exception as e:
            self.init_error.emit(str(e))


class AgentCard(QFrame):
    """Agent状态卡片 - 优化版"""
    
    def __init__(self, name: str, agent_type: str, model: str, parent=None):
        super().__init__(parent)
        self.name = name
        self.agent_type = agent_type
        self.model = model
        self._status = AgentState.IDLE
        self._progress = 0
        self._message = "等待任务..."
        
        self._setup_ui()
        self._update_style()
        
    def _setup_ui(self):
        """设置UI"""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setMinimumWidth(280)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimens.SM)
        layout.setContentsMargins(Dimens.MD, Dimens.MD, Dimens.MD, Dimens.MD)
        
        # 头部：名称和模型
        header = QHBoxLayout()
        
        self.name_label = QLabel(self.name)
        self.name_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Colors.TEXT_PRIMARY};")
        header.addWidget(self.name_label)
        
        header.addStretch()
        
        self.model_label = QLabel(self.model)
        self.model_label.setStyleSheet(f"font-size: 10px; color: {Colors.TEXT_DISABLED}; padding: 2px 6px; background-color: {Colors.SURFACE_LIGHT}; border-radius: 4px;")
        header.addWidget(self.model_label)
        
        layout.addLayout(header)
        
        # Agent类型
        self.type_label = QLabel(self.agent_type)
        self.type_label.setStyleSheet(f"font-size: 12px; color: {Colors.TEXT_SECONDARY};")
        layout.addWidget(self.type_label)
        
        layout.addSpacing(Dimens.SM)
        
        # 状态
        self.status_label = QLabel("空闲")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(Styles.get_progress_bar_style())
        layout.addWidget(self.progress_bar)
        
        # 消息
        self.message_label = QLabel("等待任务...")
        self.message_label.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT_DISABLED};")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
        
    def _update_style(self):
        """更新卡片样式"""
        self.setStyleSheet(Styles.get_agent_card_style())
        
    def update_status(self, state: AgentState, progress: int = 0, message: str = ""):
        """更新状态"""
        self._status = state
        self._progress = progress
        if message:
            self._message = message
            
        # 状态映射
        state_info = {
            AgentState.IDLE: ("空闲", Colors.STATE_IDLE, Colors.SUCCESS_BG),
            AgentState.WORKING: ("工作中", Colors.STATE_WORKING, f"{Colors.STATE_WORKING}22"),
            AgentState.WAITING: ("等待中", Colors.WARNING, Colors.WARNING_BG),
            AgentState.ERROR: ("错误", Colors.STATE_ERROR, Colors.ERROR_BG),
            AgentState.COMPLETED: ("完成", Colors.STATE_IDLE, Colors.SUCCESS_BG),
        }
        
        text, color, bg = state_info.get(state, ("未知", Colors.TEXT_SECONDARY, Colors.SURFACE_LIGHT))
        
        self.status_label.setText(text)
        self.status_label.setStyleSheet(Styles.get_status_label_style(color, bg))
        
        self.progress_bar.setValue(progress)
        self.message_label.setText(self._message)
        
        # 根据状态调整进度条颜色
        if state == AgentState.ERROR:
            self.progress_bar.setStyleSheet(Styles.get_progress_bar_style(Colors.ERROR))
        elif state == AgentState.WORKING:
            self.progress_bar.setStyleSheet(Styles.get_progress_bar_style(Colors.PRIMARY))
        else:
            self.progress_bar.setStyleSheet(Styles.get_progress_bar_style(Colors.STATE_IDLE))


class AgentMonitorPage(QWidget):
    """Agent监控页面 - 优化版"""
    
    def __init__(self, agent_manager: AgentManager, parent=None):
        super().__init__(parent)
        self.agent_manager = agent_manager
        self.agent_cards: Dict[str, AgentCard] = {}
        
        self._setup_ui()
        self._setup_timer()
        self._connect_signals()
        
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimens.LG)
        layout.setContentsMargins(Dimens.LG, Dimens.LG, Dimens.LG, Dimens.LG)
        
        # 标题
        title = QLabel("🤖 Agent 监控中心")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(title)
        
        # 系统状态概览
        self.status_summary = QLabel()
        self.status_summary.setStyleSheet(Styles.get_status_summary_style())
        layout.addWidget(self.status_summary)
        
        # Agent卡片网格
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(Dimens.MD)
        
        # Agent配置
        agents_config = [
            ("Director", "导演 - 规划", "DeepSeek-V3", "director"),
            ("Editor", "剪辑 - 粗剪精剪", "Kimi K2.5", "editor"),
            ("Colorist", "调色 - 视觉分析", "Kimi K2.5", "colorist"),
            ("Sound", "音效 - 音频理解", "Qwen 2.5", "sound"),
            ("VFX", "特效 - 画面理解", "Kimi K2.5", "vfx"),
            ("Reviewer", "审核 - 质量检查", "DeepSeek-Coder", "reviewer"),
        ]
        
        for i, (name, agent_type, model, key) in enumerate(agents_config):
            card = AgentCard(name, agent_type, model)
            self.agent_cards[key] = card
            grid.addWidget(card, i // 3, i % 3)
            
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # 任务队列
        layout.addSpacing(Dimens.MD)
        task_title = QLabel("📋 任务队列")
        task_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(task_title)
        
        self.task_list = QListWidget()
        self.task_list.setStyleSheet(Styles.get_list_widget_style())
        layout.addWidget(self.task_list)
        
    def _setup_timer(self):
        """设置定时刷新"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_status)
        self.timer.start(1000)  # 每秒刷新
        
    def _connect_signals(self):
        """连接信号"""
        # 连接Agent信号
        for agent_id, agent in self.agent_manager.agents.items():
            key = agent_id.split('_')[0].lower()
            if key in self.agent_cards:
                card = self.agent_cards[key]
                agent.progress_updated.connect(
                    lambda aid, prog, msg, c=card: c.update_status(
                        AgentState.WORKING, prog, msg
                    )
                )
                agent.state_changed.connect(
                    lambda aid, state, c=card: c.update_status(
                        AgentState[state], c._progress, c._message
                    )
                )
                
    def _refresh_status(self):
        """刷新状态"""
        try:
            stats = self.agent_manager.get_system_stats()
            
            # 更新概览
            summary = f"""
            <b>系统状态</b> | 
            Agent: <b>{stats['total_agents']}</b> 个 | 
            工作中: <b style='color:{Colors.STATE_WORKING}'>{stats['working_agents']}</b> | 
            空闲: <b style='color:{Colors.STATE_IDLE}'>{stats['idle_agents']}</b> | 
            任务: <b>{stats['pending_tasks']}</b> 待处理 / <b>{stats['running_tasks']}</b> 运行中 / <b>{stats['completed_tasks']}</b> 已完成
            """
            self.status_summary.setText(summary)
            
            # 更新Agent卡片
            for agent_id, agent in self.agent_manager.agents.items():
                key = agent_id.split('_')[0].lower()
                if key in self.agent_cards:
                    card = self.agent_cards[key]
                    progress = getattr(agent, 'progress', 0)
                    message = getattr(agent, 'current_task', "")
                    if isinstance(message, dict):
                        message = message.get('description', str(message))
                    card.update_status(agent.state, progress, str(message) if message else "等待任务...")
                    
            # 更新任务列表
            self.task_list.clear()
            for task in self.agent_manager.task_queue:
                item_text = f"[{task.status.name}] {task.task_type} - {task.task_id[:8]}"
                item = QListWidgetItem(item_text)
                
                # 根据状态设置颜色
                if task.status.name == 'RUNNING':
                    item.setForeground(QColor(Colors.PRIMARY))
                elif task.status.name == 'FAILED':
                    item.setForeground(QColor(Colors.ERROR))
                elif task.status.name == 'COMPLETED':
                    item.setForeground(QColor(Colors.SUCCESS))
                    
                self.task_list.addItem(item)
                
        except Exception as e:
            print(f"刷新状态失败: {e}")


class ProjectPage(QWidget):
    """项目管理页面 - 优化版"""
    
    project_created = pyqtSignal(str)
    
    def __init__(self, project_manager: ProjectManager, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self._setup_ui()
        
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(Dimens.LG)
        layout.setContentsMargins(Dimens.LG, Dimens.LG, Dimens.LG, Dimens.LG)
        
        # 标题
        title = QLabel("🎬 项目管理")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(title)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        self.new_btn = QPushButton("➕ 新建项目")
        self.new_btn.setStyleSheet(Styles.get_button_primary_style())
        self.new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_btn.clicked.connect(self._create_project)
        btn_layout.addWidget(self.new_btn)
        
        self.import_btn = QPushButton("📥 导入项目")
        self.import_btn.setStyleSheet(Styles.get_button_ghost_style())
        self.import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_layout.addWidget(self.import_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 项目列表
        self.project_list = QListWidget()
        self.project_list.setStyleSheet(Styles.get_list_widget_style())
        layout.addWidget(self.project_list)
        
        self._refresh_projects()
        
    def _create_project(self):
        """创建新项目"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择视频素材", "",
            "视频文件 (*.mp4 *.mov *.avi *.mkv *.flv);;所有文件 (*.*)"
        )
        
        if files:
            try:
                project = self.project_manager.create_project(
                    name=f"项目_{len(self.project_manager.get_all_projects()) + 1}",
                    source_files=files
                )
                self.project_created.emit(project.id)
                self._refresh_projects()
                
                QMessageBox.information(
                    self, "创建成功",
                    f"项目 '{project.name}' 创建成功！\n包含 {len(files)} 个素材文件。"
                )
            except Exception as e:
                QMessageBox.critical(self, "创建失败", f"项目创建失败: {e}")
            
    def _refresh_projects(self):
        """刷新项目列表"""
        self.project_list.clear()
        
        try:
            for project in self.project_manager.get_all_projects():
                item_text = f"📁 {project.name} | 状态: {project.status.name} | 创建于: {project.created_at.strftime('%Y-%m-%d %H:%M')}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, project.id)
                self.project_list.addItem(item)
        except Exception as e:
            print(f"刷新项目列表失败: {e}")


class MainWindow(QMainWindow):
    """CineFlow v3.0 主窗口 - 优化版"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("CineFlow v3.0 - 多Agent智能视频剪辑")
        self.setMinimumSize(1600, 1000)
        
        # 显示加载界面
        self._show_loading()
        
        # 开始异步初始化
        self._start_async_init()
        
    def _show_loading(self):
        """显示加载界面"""
        self.loading_widget = QWidget()
        self.setCentralWidget(self.loading_widget)
        
        layout = QVBoxLayout(self.loading_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo
        logo = QLabel("🎬")
        logo.setStyleSheet("font-size: 72px;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)
        
        # 标题
        title = QLabel("CineFlow v3.0")
        title.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {Colors.TEXT_PRIMARY};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 副标题
        subtitle = QLabel("多Agent智能视频剪辑系统")
        subtitle.setStyleSheet(f"font-size: 16px; color: {Colors.TEXT_SECONDARY};")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(40)
        
        # 进度条
        self.loading_progress = QProgressBar()
        self.loading_progress.setRange(0, 100)
        self.loading_progress.setValue(0)
        self.loading_progress.setMaximumWidth(400)
        self.loading_progress.setStyleSheet(Styles.get_progress_bar_style())
        layout.addWidget(self.loading_progress, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 状态文本
        self.loading_status = QLabel("正在初始化...")
        self.loading_status.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        self.loading_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.loading_status)
        
    def _start_async_init(self):
        """开始异步初始化"""
        self.init_thread = AsyncInitThread()
        self.init_thread.init_progress.connect(self._on_init_progress)
        self.init_thread.init_complete.connect(self._on_init_complete)
        self.init_thread.init_error.connect(self._on_init_error)
        self.init_thread.start()
        
    def _on_init_progress(self, progress: int, message: str):
        """初始化进度"""
        self.loading_progress.setValue(progress)
        self.loading_status.setText(message)
        
    def _on_init_complete(self, agent_manager, project_manager):
        """初始化完成"""
        self.agent_manager = agent_manager
        self.project_manager = project_manager
        
        # 初始化主UI
        self._init_ui()
        
        print(f"✅ 系统初始化完成 - {len(self.agent_manager.agents)} 个Agent已就绪")
        
    def _on_init_error(self, error: str):
        """初始化错误"""
        QMessageBox.critical(
            self, "初始化失败",
            f"系统初始化失败:\n{error}\n\n请检查配置后重试。"
        )
        
    def _init_ui(self):
        """初始化主UI"""
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
        
        # 创作页面
        self.creator_page = QLabel("✨ 创作中心 - 开发中")
        self.creator_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.creator_page.setStyleSheet(f"font-size: 24px; color: {Colors.TEXT_DISABLED};")
        self.stack.addWidget(self.creator_page)
        
        # 导出页面
        self.export_page = QLabel("📦 导出中心 - 开发中")
        self.export_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.export_page.setStyleSheet(f"font-size: 24px; color: {Colors.TEXT_DISABLED};")
        self.stack.addWidget(self.export_page)
        
        layout.addWidget(self.stack, 1)
        
        # 状态栏
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")
        
        # 定时刷新状态栏
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_status_bar)
        self.status_timer.start(2000)
        
    def _create_navigation(self) -> QWidget:
        """创建导航栏"""
        nav = QFrame()
        nav.setFixedWidth(Dimens.NAV_WIDTH)
        nav.setStyleSheet(Styles.get_nav_frame_style())
        
        layout = QVBoxLayout(nav)
        layout.setSpacing(Dimens.SM)
        layout.setContentsMargins(Dimens.MD, Dimens.LG, Dimens.MD, Dimens.LG)
        
        # Logo
        logo = QLabel("🎬 CineFlow")
        logo.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(logo)
        
        version = QLabel("v3.0.0")
        version.setStyleSheet(f"font-size: 12px; color: {Colors.TEXT_DISABLED};")
        layout.addWidget(version)
        
        layout.addSpacing(Dimens.XL)
        
        # 导航按钮
        self.nav_buttons = []
        nav_items = [
            ("🤖 Agent监控", 0),
            ("🎬 项目管理", 1),
            ("✨ 创作中心", 2),
            ("📦 导出中心", 3),
        ]
        
        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setStyleSheet(Styles.get_nav_button_style())
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=index: self._switch_page(i))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)
            
            if index == 0:
                btn.setChecked(True)
                
        layout.addStretch()
        
        return nav
        
    def _switch_page(self, index: int):
        """切换页面"""
        self.stack.setCurrentIndex(index)
        
        # 更新按钮状态
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
            
    def _on_project_created(self, project_id: str):
        """项目创建回调"""
        self.status_bar.showMessage(f"项目创建成功: {project_id[:8]}...", 3000)
        
    def _update_status_bar(self):
        """更新状态栏"""
        try:
            stats = self.agent_manager.get_system_stats()
            text = f"Agent: {stats['working_agents']}/{stats['total_agents']} 工作中 | 任务: {stats['pending_tasks']} 待处理"
            self.status_bar.showMessage(text)
        except:
            pass
        
    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(
            self, "确认退出",
            "确定要退出 CineFlow 吗?\n正在运行的任务将被取消。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 停止Agent管理器
            if hasattr(self, 'agent_manager'):
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
    app.setApplicationDisplayName("CineFlow")
    
    # 应用暗色主题
    StyleHelper.apply_dark_theme(app)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
