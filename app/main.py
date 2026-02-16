"""
CineFlow v3.0 主入口
多Agent智能视频剪辑系统
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QIcon

from app.agents import (
    AgentManager,
    DirectorAgent,
    EditorAgent,
    ColoristAgent,
    SoundAgent,
    VFXAgent,
    ReviewerAgent
)
from app.core import (
    VideoProcessor,
    AudioEngine,
    DraftExporter,
    ProjectManager
)


class CineFlowApp(QMainWindow):
    """CineFlow主应用"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("CineFlow v3.0 - 多Agent智能视频剪辑")
        self.setMinimumSize(1400, 900)
        
        # 初始化核心组件
        self._init_core()
        
        # 初始化Agent系统
        self._init_agents()
        
        # 初始化UI
        self._init_ui()
        
    def _init_core(self):
        """初始化核心服务"""
        # 查找FFmpeg
        ffmpeg_path = self._find_ffmpeg()
        
        self.video_processor = VideoProcessor(ffmpeg_path)
        self.audio_engine = AudioEngine(ffmpeg_path)
        self.draft_exporter = DraftExporter()
        self.project_manager = ProjectManager()
        
        print("✅ 核心服务初始化完成")
        
    def _find_ffmpeg(self) -> str:
        """查找FFmpeg路径"""
        # 1. 检查内置FFmpeg
        bundled = Path(__file__).parent / "ffmpeg" / "ffmpeg"
        if bundled.exists():
            return str(bundled)
            
        # 2. 检查系统PATH
        import shutil
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg:
            return ffmpeg
            
        # 3. 默认
        return "ffmpeg"
        
    def _init_agents(self):
        """初始化Agent系统"""
        self.agent_manager = AgentManager()
        
        # 注册所有Agent
        self.agent_manager.register_agent(DirectorAgent())
        self.agent_manager.register_agent(EditorAgent())
        self.agent_manager.register_agent(ColoristAgent())
        self.agent_manager.register_agent(SoundAgent())
        self.agent_manager.register_agent(VFXAgent())
        self.agent_manager.register_agent(ReviewerAgent())
        
        # 启动管理器
        self.agent_manager.start()
        
        print("✅ Agent系统初始化完成")
        print(f"   已注册 {len(self.agent_manager.agents)} 个Agent")
        
    def _init_ui(self):
        """初始化UI"""
        # 主窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # TODO: 实现完整UI
        # 临时显示状态
        from PyQt6.QtWidgets import QLabel, QPushButton, QTextEdit
        
        title = QLabel("🎬 CineFlow v3.0 - 多Agent智能视频剪辑")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Agent状态
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(200)
        layout.addWidget(self.status_text)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新状态")
        refresh_btn.clicked.connect(self._refresh_status)
        layout.addWidget(refresh_btn)
        
        # 初始状态
        self._refresh_status()
        
    def _refresh_status(self):
        """刷新状态显示"""
        stats = self.agent_manager.get_system_stats()
        
        status = f"""
系统状态:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Agent数量: {stats['total_agents']}
  - 工作中: {stats['working_agents']}
  - 空闲: {stats['idle_agents']}
  - 错误: {stats['error_agents']}

任务状态:
  - 待处理: {stats['pending_tasks']}
  - 运行中: {stats['running_tasks']}
  - 已完成: {stats['completed_tasks']}

Director: {'✅' if stats['has_director'] else '❌'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        self.status_text.setText(status)
        
    def closeEvent(self, event):
        """关闭事件"""
        # 停止Agent管理器
        self.agent_manager.stop()
        
        # 停止所有Agent
        for agent in self.agent_manager.agents.values():
            if hasattr(agent, 'stop'):
                agent.stop()
                
        event.accept()


def main():
    """主函数"""
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("CineFlow")
    app.setApplicationVersion("3.0.0")
    
    # 设置样式
    app.setStyle('Fusion')
    
    # 创建主窗口
    window = CineFlowApp()
    window.show()
    
    # 运行
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
