"""
导演 Agent
负责整体把控视频剪辑项目，协调其他 Agent 工作
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio

from .base_agent import BaseAgent, AgentCapability, AgentMessage, AgentResult, AgentState


@dataclass
class EditingPlan:
    """剪辑计划"""
    project_id: str
    project_name: str
    video_path: str
    target_duration: float
    style: str
    
    # 任务分配
    tasks: List[Dict[str, Any]] = None
    
    # 时间线
    timeline: Dict[str, Any] = None
    
    # 质量要求
    quality_requirements: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tasks is None:
            self.tasks = []
        if self.timeline is None:
            self.timeline = {}
        if self.quality_requirements is None:
            self.quality_requirements = {
                'min_resolution': '1080p',
                'target_bitrate': '10Mbps',
                'audio_quality': 'high',
                'color_profile': 'rec709'
            }


class DirectorAgent(BaseAgent):
    """
    导演 Agent
    
    职责：
    1. 接收用户项目需求
    2. 制定剪辑计划
    3. 分配任务给专业 Agent
    4. 监控进度和质量
    5. 整合最终输出
    
    工作流程：
        接收项目 → 分析需求 → 制定计划 → 分配任务 → 监控执行 → 整合输出
    """
    
    def __init__(self):
        super().__init__(
            name="Director",
            capabilities=[
                AgentCapability.PLANNING,
                AgentCapability.REVIEW
            ]
        )
        
        # 初始化LLM - Director使用GPT-4进行规划
        self.init_llm('director')
        
        # 管理的 Agent
        self.agents: Dict[str, BaseAgent] = {}
        
        # 项目状态
        self.projects: Dict[str, Dict[str, Any]] = {}
        
        # 任务队列
        self.task_queue: List[Dict[str, Any]] = []
        
        # 回调
        self._project_callback: Optional[callable] = None
        
    def register_agent(self, agent: BaseAgent):
        """注册专业 Agent"""
        self.agents[agent.agent_id] = agent
        
        # 设置消息处理器
        agent.set_message_handler(self._handle_agent_message)
        agent.set_progress_handler(self._handle_agent_progress)
        
        # 连接信号
        agent.task_completed.connect(self._on_agent_task_completed)
        agent.error_occurred.connect(self._on_agent_error)
        
    def set_project_callback(self, callback: callable):
        """设置项目进度回调"""
        self._project_callback = callback
        
    def _handle_agent_message(self, message: AgentMessage):
        """处理 Agent 消息"""
        # 转发消息
        if message.receiver in self.agents:
            self.agents[message.receiver].receive_message(message)
            
    def _handle_agent_progress(self, agent_id: str, progress: int, message: str):
        """处理 Agent 进度"""
        self.report_progress(progress, f"[{agent_id}] {message}")
        
    def _on_agent_task_completed(self, agent_id: str, result: AgentResult):
        """Agent 任务完成回调"""
        # 检查项目状态
        for project_id, project in self.projects.items():
            if agent_id in project.get('assigned_agents', {}):
                self._check_project_completion(project_id)
                break
                
    def _on_agent_error(self, agent_id: str, error: str):
        """Agent 错误回调"""
        # 通知用户
        self.error_occurred.emit(self.agent_id, f"Agent {agent_id} 错误: {error}")
        
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        """
        执行导演任务
        
        Args:
            task: {
                'type': 'create_project' | 'monitor_project',
                'project': EditingPlan,
                'agents': List[str]  # Agent IDs
            }
        """
        task_type = task.get('type', 'create_project')
        
        if task_type == 'create_project':
            return await self._create_project(task)
        elif task_type == 'monitor_project':
            return await self._monitor_project(task)
        else:
            return AgentResult(
                success=False,
                data={},
                message=f"未知任务类型: {task_type}"
            )
            
    async def _create_project(self, task: Dict[str, Any]) -> AgentResult:
        """创建并执行项目"""
        plan: EditingPlan = task.get('project')
        agent_ids: List[str] = task.get('agents', [])
        
        if not plan:
            return AgentResult(
                success=False,
                data={},
                message="缺少项目计划"
            )
            
        # 注册项目
        self.projects[plan.project_id] = {
            'plan': plan,
            'status': 'planning',
            'assigned_agents': {},
            'completed_agents': set(),
            'results': {},
            'start_time': datetime.now(),
            'errors': []
        }
        
        self.report_progress(5, "制定剪辑计划...")
        
        # 1. 分析项目需求（使用LLM）
        analysis = await self._analyze_project(plan)
        
        # 2. 制定详细计划
        editing_plan = self._create_editing_plan(plan, analysis)
        self.projects[plan.project_id]['plan'] = editing_plan
        
        self.report_progress(15, "分配任务给专业 Agent...")
        
        # 3. 分配任务给 Agent
        await self._assign_tasks(plan.project_id, editing_plan, agent_ids)
        
        self.report_progress(25, "开始执行...")
        
        # 4. 监控执行
        result = await self._monitor_execution(plan.project_id)
        
        return result
        
    async def _analyze_project(self, plan: EditingPlan) -> Dict[str, Any]:
        """分析项目需求 - 使用LLM智能分析"""
        # 基础分析
        analysis = {
            'duration': plan.target_duration,
            'style': plan.style,
            'complexity': 'medium',
            'required_agents': [],
            'estimated_time': 0
        }
        
        # 使用LLM进行智能分析
        prompt = f"""
分析以下视频剪辑项目需求：

项目信息：
- 名称: {plan.project_name}
- 时长: {plan.target_duration}秒
- 风格: {plan.style}
- 视频路径: {plan.video_path}

请分析：
1. 项目复杂度 (low/medium/high)
2. 需要哪些专业Agent (editor/colorist/sound/vfx/reviewer)
3. 预估处理时间（秒）
4. 关键注意事项

以JSON格式返回：
{{
    "complexity": "medium",
    "required_agents": ["editor", "colorist", "sound"],
    "estimated_time": 180,
    "notes": "注意事项"
}}
"""
        
        try:
            llm_result = await self.call_llm(
                prompt=prompt,
                system_prompt="你是一个专业的视频制作导演，擅长分析项目需求并制定制作计划。只返回JSON格式。"
            )
            
            if llm_result.get('success'):
                import json
                content = llm_result['content']
                # 提取JSON
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0]
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0]
                    
                llm_analysis = json.loads(content.strip())
                
                analysis['complexity'] = llm_analysis.get('complexity', 'medium')
                analysis['required_agents'] = llm_analysis.get('required_agents', ['editor', 'sound'])
                analysis['estimated_time'] = llm_analysis.get('estimated_time', 180)
                analysis['llm_notes'] = llm_analysis.get('notes', '')
            else:
                # LLM失败使用默认规则
                self._apply_default_rules(analysis, plan)
                
        except Exception as e:
            # 异常时使用默认规则
            self._apply_default_rules(analysis, plan)
            analysis['llm_error'] = str(e)
            
        return analysis
        
    def _apply_default_rules(self, analysis: Dict, plan: EditingPlan):
        """应用默认规则"""
        if plan.style in ['cinematic', 'professional']:
            analysis['required_agents'] = ['editor', 'colorist', 'sound', 'vfx']
            analysis['complexity'] = 'high'
            analysis['estimated_time'] = 300
        elif plan.style in ['vlog', 'simple']:
            analysis['required_agents'] = ['editor', 'sound']
            analysis['complexity'] = 'low'
            analysis['estimated_time'] = 120
        else:
            analysis['required_agents'] = ['editor', 'colorist', 'sound']
            analysis['complexity'] = 'medium'
            analysis['estimated_time'] = 180
        
    def _create_editing_plan(
        self,
        plan: EditingPlan,
        analysis: Dict[str, Any]
    ) -> EditingPlan:
        """创建详细剪辑计划"""
        # 创建任务列表
        tasks = []
        
        # 剪辑任务
        tasks.append({
            'id': 'edit_001',
            'type': 'editing',
            'agent': 'editor',
            'description': '粗剪和精剪',
            'dependencies': [],
            'estimated_time': 120
        })
        
        # 调色任务（依赖剪辑）
        if 'colorist' in analysis['required_agents']:
            tasks.append({
                'id': 'color_001',
                'type': 'color_grading',
                'agent': 'colorist',
                'description': '调色和风格化',
                'dependencies': ['edit_001'],
                'estimated_time': 60
            })
            
        # 音效任务（依赖剪辑）
        tasks.append({
            'id': 'sound_001',
            'type': 'sound_design',
            'agent': 'sound',
            'description': '音频处理和混音',
            'dependencies': ['edit_001'],
            'estimated_time': 90
        })
        
        # 特效任务（依赖剪辑和调色）
        if 'vfx' in analysis['required_agents']:
            deps = ['edit_001']
            if 'colorist' in analysis['required_agents']:
                deps.append('color_001')
            tasks.append({
                'id': 'vfx_001',
                'type': 'vfx',
                'agent': 'vfx',
                'description': '视觉特效',
                'dependencies': deps,
                'estimated_time': 120
            })
            
        # 审核任务（依赖所有）
        all_task_ids = [t['id'] for t in tasks]
        tasks.append({
            'id': 'review_001',
            'type': 'review',
            'agent': 'reviewer',
            'description': '质量审核',
            'dependencies': all_task_ids,
            'estimated_time': 30
        })
        
        plan.tasks = tasks
        return plan
        
    async def _assign_tasks(
        self,
        project_id: str,
        plan: EditingPlan,
        agent_ids: List[str]
    ):
        """分配任务给 Agent"""
        project = self.projects[project_id]
        
        for task in plan.tasks:
            agent_type = task['agent']
            
            # 找到对应类型的 Agent
            assigned_agent = None
            for agent_id in agent_ids:
                if agent_id in self.agents:
                    agent = self.agents[agent_id]
                    if any(c.value == task['type'] for c in agent.capabilities):
                        assigned_agent = agent
                        break
                        
            if assigned_agent:
                project['assigned_agents'][task['id']] = assigned_agent.agent_id
                
                # 发送任务消息
                assigned_agent.send_message(
                    receiver=assigned_agent.agent_id,
                    message_type='task_assigned',
                    content={
                        'project_id': project_id,
                        'task': task,
                        'plan': plan
                    }
                )
            else:
                project['errors'].append(f"找不到 {agent_type} 类型的 Agent")
                
    async def _monitor_execution(self, project_id: str) -> AgentResult:
        """监控项目执行"""
        project = self.projects[project_id]
        plan: EditingPlan = project['plan']
        
        # 并行执行所有任务
        tasks_to_run = []
        
        for task in plan.tasks:
            agent_id = project['assigned_agents'].get(task['id'])
            if agent_id and agent_id in self.agents:
                agent = self.agents[agent_id]
                
                # 创建任务
                agent_task = {
                    'type': task['type'],
                    'project_id': project_id,
                    'task_id': task['id'],
                    'video_path': plan.video_path,
                    'requirements': plan.quality_requirements,
                    **task
                }
                
                # 运行任务
                tasks_to_run.append(agent.run(agent_task))
                
        # 等待所有任务完成
        if tasks_to_run:
            results = await asyncio.gather(*tasks_to_run, return_exceptions=True)
            
            # 处理结果
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    project['errors'].append(str(result))
                elif isinstance(result, AgentResult):
                    task_id = plan.tasks[i]['id']
                    project['results'][task_id] = result
                    
                    if result.success:
                        project['completed_agents'].add(task_id)
                    else:
                        project['errors'].append(result.message)
                        
        # 检查完成状态
        success = len(project['errors']) == 0
        
        # 整合最终输出
        final_output = self._integrate_output(project_id)
        
        project['status'] = 'completed' if success else 'failed'
        
        return AgentResult(
            success=success,
            data={
                'project_id': project_id,
                'output': final_output,
                'completed_tasks': len(project['completed_agents']),
                'total_tasks': len(plan.tasks),
                'errors': project['errors']
            },
            message="项目完成" if success else f"项目失败: {project['errors']}",
            errors=project['errors']
        )
        
    def _integrate_output(self, project_id: str) -> Dict[str, Any]:
        """整合最终输出"""
        project = self.projects[project_id]
        
        output = {
            'project_id': project_id,
            'video_segments': [],
            'audio_tracks': [],
            'effects': [],
            'color_profile': None,
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'agents_involved': list(project['assigned_agents'].values()),
                'processing_time': (
                    datetime.now() - project['start_time']
                ).total_seconds()
            }
        }
        
        # 收集各 Agent 的输出
        for task_id, result in project['results'].items():
            if result.success:
                data = result.data
                
                if 'video_segments' in data:
                    output['video_segments'].extend(data['video_segments'])
                if 'audio_tracks' in data:
                    output['audio_tracks'].extend(data['audio_tracks'])
                if 'effects' in data:
                    output['effects'].extend(data['effects'])
                if 'color_profile' in data:
                    output['color_profile'] = data['color_profile']
                    
        return output
        
    def _check_project_completion(self, project_id: str):
        """检查项目完成状态"""
        project = self.projects[project_id]
        plan: EditingPlan = project['plan']
        
        completed = len(project['completed_agents'])
        total = len(plan.tasks)
        
        progress = int((completed / total) * 100)
        self.report_progress(progress, f"进度: {completed}/{total}")
        
        if completed == total:
            self.report_progress(100, "所有 Agent 任务完成")
            
    async def _monitor_project(self, task: Dict[str, Any]) -> AgentResult:
        """监控现有项目"""
        project_id = task.get('project_id')
        
        if project_id not in self.projects:
            return AgentResult(
                success=False,
                data={},
                message=f"项目 {project_id} 不存在"
            )
            
        project = self.projects[project_id]
        
        return AgentResult(
            success=True,
            data={
                'project_id': project_id,
                'status': project['status'],
                'progress': len(project['completed_agents']) / len(project['plan'].tasks),
                'errors': project['errors']
            },
            message=f"项目状态: {project['status']}"
        )
        
    def get_project_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """获取项目状态"""
        if project_id not in self.projects:
            return None
            
        project = self.projects[project_id]
        plan: EditingPlan = project['plan']
        
        return {
            'project_id': project_id,
            'name': plan.project_name,
            'status': project['status'],
            'progress': {
                'completed': len(project['completed_agents']),
                'total': len(plan.tasks),
                'percentage': int(
                    len(project['completed_agents']) / len(plan.tasks) * 100
                ) if plan.tasks else 0
            },
            'agents': {
                task_id: agent_id
                for task_id, agent_id in project['assigned_agents'].items()
            },
            'errors': project['errors'],
            'elapsed_time': (
                datetime.now() - project['start_time']
            ).total_seconds()
        }
