"""
Agent 基础类
定义所有 Agent 的通用接口和行为
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import asyncio
from PyQt6.QtCore import QObject, pyqtSignal, QThread

from .llm_client import LLMClient, LLMConfig


class AgentState(Enum):
    """Agent 状态"""
    IDLE = auto()           # 空闲
    WORKING = auto()        # 工作中
    WAITING = auto()        # 等待中
    ERROR = auto()          # 错误
    COMPLETED = auto()      # 完成


class AgentCapability(Enum):
    """Agent 能力类型"""
    EDITING = "editing"           # 剪辑
    COLOR_GRADING = "color"       # 调色
    SOUND_DESIGN = "sound"        # 音效
    VFX = "vfx"                   # 特效
    SCRIPT_WRITING = "script"     # 文案
    REVIEW = "review"             # 审核
    PLANNING = "planning"         # 规划


@dataclass
class AgentMessage:
    """Agent 间消息"""
    sender: str                    # 发送者ID
    receiver: str                  # 接收者ID
    message_type: str              # 消息类型
    content: Dict[str, Any]        # 消息内容
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 1              # 优先级 1-5


@dataclass
class AgentResult:
    """Agent 执行结果"""
    success: bool
    data: Dict[str, Any]
    message: str = ""
    errors: List[str] = field(default_factory=list)
    execution_time: float = 0.0


class BaseAgent(QObject, ABC):
    """
    Agent 基类
    
    所有专业 Agent 的父类，提供通用功能：
    - 状态管理
    - 消息通信
    - 任务执行
    - 进度报告
    """
    
    # 信号定义
    state_changed = pyqtSignal(str, str)      # agent_id, new_state
    progress_updated = pyqtSignal(str, int, str)  # agent_id, progress, message
    message_sent = pyqtSignal(str, str, dict)  # sender, receiver, content
    task_completed = pyqtSignal(str, object)   # agent_id, result
    error_occurred = pyqtSignal(str, str)      # agent_id, error
    
    def __init__(
        self,
        agent_id: str = None,
        name: str = "Agent",
        capabilities: List[AgentCapability] = None
    ):
        super().__init__()
        
        self.agent_id = agent_id or str(uuid.uuid4())[:8]
        self.name = name
        self.capabilities = capabilities or []
        self.state = AgentState.IDLE
        self.current_task = None
        self.message_queue = []
        self.history = []
        
        # 性能统计
        self.stats = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_execution_time': 0.0,
            'messages_sent': 0,
            'messages_received': 0,
        }
        
        # LLM客户端
        self.llm: Optional[LLMClient] = None
        self._llm_config: Optional[LLMConfig] = None
        
        # 回调函数
        self._message_handler: Optional[Callable] = None
        self._progress_handler: Optional[Callable] = None
        
    def set_message_handler(self, handler: Callable):
        """设置消息处理器"""
        self._message_handler = handler
        
    def set_progress_handler(self, handler: Callable):
        """设置进度处理器"""
        self._progress_handler = handler
        
    def init_llm(self, agent_type: str, config: LLMConfig = None):
        """
        初始化LLM客户端
        
        Args:
            agent_type: Agent类型标识 (director/editor/colorist/sound/vfx/reviewer)
            config: 可选的自定义配置
        """
        if config:
            self._llm_config = config
            self.llm = LLMClient(config)
        else:
            self.llm = LLMClient.for_agent(agent_type)
            
    async def call_llm(
        self,
        prompt: str,
        system_prompt: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用大模型
        
        Args:
            prompt: 提示词
            system_prompt: 系统提示
            **kwargs: 额外参数
            
        Returns:
            LLM响应结果
        """
        if not self.llm:
            return {
                'success': False,
                'content': '',
                'error': 'LLM未初始化'
            }
            
        return await self.llm.complete(prompt, system_prompt, **kwargs)
        
    def get_capabilities(self) -> List[AgentCapability]:
        """获取 Agent 能力列表"""
        return self.capabilities.copy()
        
    def has_capability(self, capability: AgentCapability) -> bool:
        """检查是否具备某能力"""
        return capability in self.capabilities
        
    def set_state(self, state: AgentState):
        """设置状态"""
        old_state = self.state
        self.state = state
        self.state_changed.emit(self.agent_id, state.name)
        
        # 记录历史
        self.history.append({
            'timestamp': datetime.now(),
            'event': 'state_change',
            'from': old_state.name,
            'to': state.name
        })
        
    def send_message(
        self,
        receiver: str,
        message_type: str,
        content: Dict[str, Any],
        priority: int = 1
    ):
        """发送消息给其他 Agent"""
        message = AgentMessage(
            sender=self.agent_id,
            receiver=receiver,
            message_type=message_type,
            content=content,
            priority=priority
        )
        
        self.message_queue.append(message)
        self.stats['messages_sent'] += 1
        self.message_sent.emit(self.agent_id, receiver, content)
        
        # 如果有消息处理器，调用它
        if self._message_handler:
            self._message_handler(message)
            
    def receive_message(self, message: AgentMessage):
        """接收消息"""
        self.stats['messages_received'] += 1
        
        # 记录历史
        self.history.append({
            'timestamp': datetime.now(),
            'event': 'message_received',
            'from': message.sender,
            'type': message.message_type
        })
        
        # 处理消息
        self._handle_message(message)
        
    @abstractmethod
    def _handle_message(self, message: AgentMessage):
        """子类实现消息处理逻辑"""
        pass
        
    def report_progress(self, progress: int, message: str = ""):
        """报告进度"""
        self.progress_updated.emit(self.agent_id, progress, message)
        
        if self._progress_handler:
            self._progress_handler(self.agent_id, progress, message)
            
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        """
        执行任务
        
        Args:
            task: 任务定义
            
        Returns:
            AgentResult: 执行结果
        """
        pass
        
    async def run(self, task: Dict[str, Any]) -> AgentResult:
        """
        运行任务（包装器）
        
        提供统一的任务执行流程：
        1. 设置状态为 WORKING
        2. 执行具体任务
        3. 处理结果
        4. 设置状态为 COMPLETED 或 ERROR
        """
        import time
        
        self.current_task = task
        self.set_state(AgentState.WORKING)
        start_time = time.time()
        
        try:
            # 执行具体任务
            result = await self.execute(task)
            
            # 更新统计
            execution_time = time.time() - start_time
            self.stats['total_execution_time'] += execution_time
            result.execution_time = execution_time
            
            if result.success:
                self.stats['tasks_completed'] += 1
                self.set_state(AgentState.COMPLETED)
                self.task_completed.emit(self.agent_id, result)
            else:
                self.stats['tasks_failed'] += 1
                self.set_state(AgentState.ERROR)
                self.error_occurred.emit(self.agent_id, result.message)
                
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.stats['tasks_failed'] += 1
            self.set_state(AgentState.ERROR)
            self.error_occurred.emit(self.agent_id, str(e))
            
            return AgentResult(
                success=False,
                data={},
                message=str(e),
                execution_time=execution_time
            )
            
        finally:
            self.current_task = None
            
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'state': self.state.name,
            'capabilities': [c.value for c in self.capabilities],
            **self.stats,
            'avg_execution_time': (
                self.stats['total_execution_time'] / max(self.stats['tasks_completed'], 1)
            )
        }
        
    def reset(self):
        """重置 Agent 状态"""
        self.state = AgentState.IDLE
        self.current_task = None
        self.message_queue.clear()
        
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'capabilities': [c.value for c in self.capabilities],
            'state': self.state.name,
            'stats': self.stats,
            'history_count': len(self.history)
        }
