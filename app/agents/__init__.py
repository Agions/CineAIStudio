"""
CineFlow 多 Agent 协同剪辑系统

实现专业视频剪辑工作室的协作模式，多个 AI Agent 分工合作完成复杂剪辑任务。

架构:
    - AgentManager: Agent 管理器，负责任务分配和协调
    - BaseAgent: 基础 Agent 类
    - 专业 Agent:
        - DirectorAgent: 导演 Agent，整体把控
        - EditorAgent: 剪辑 Agent，负责剪辑
        - ColoristAgent: 调色 Agent，负责调色
        - SoundAgent: 音效 Agent，负责音频
        - VFXAgent: 特效 Agent，负责特效
        - ReviewerAgent: 审核 Agent，质量检查

工作流程:
    1. Director 接收任务，制定剪辑计划
    2. Director 分配任务给各个专业 Agent
    3. 各 Agent 并行工作
    4. Reviewer 检查质量
    5. Director 整合输出
"""

from .agent_manager import AgentManager, AgentTask, TaskStatus
from .base_agent import BaseAgent, AgentState, AgentCapability, AgentResult
from .director_agent import DirectorAgent
from .editor_agent import EditorAgent
from .colorist_agent import ColoristAgent
from .sound_agent import SoundAgent
from .vfx_agent import VFXAgent
from .reviewer_agent import ReviewerAgent
from .llm_client import LLMClient

__all__ = [
    'AgentManager',
    'AgentTask',
    'TaskStatus',
    'BaseAgent',
    'AgentState',
    'AgentCapability',
    'AgentResult',
    'DirectorAgent',
    'EditorAgent',
    'ColoristAgent',
    'SoundAgent',
    'VFXAgent',
    'ReviewerAgent',
    'LLMClient',
]
