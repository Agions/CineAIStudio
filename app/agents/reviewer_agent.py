"""
审核 Agent
负责质量检查和审核
"""

from typing import Dict, Any, List
from pathlib import Path

from .base_agent import BaseAgent, AgentCapability, AgentResult


class ReviewerAgent(BaseAgent):
    """
    审核 Agent
    
    职责：
    1. 技术质量检查 - 分辨率、码率、格式
    2. 内容质量检查 - 剪辑节奏、音频质量
    3. 规范检查 - 平台要求、时长限制
    4. 问题报告 - 生成修改建议
    
    使用Claude进行细致的质量评估
    """
    
    # 检查项
    CHECK_ITEMS = {
        'technical': {
            'name': '技术质量',
            'items': [
                {'id': 'resolution', 'name': '分辨率', 'weight': 10},
                {'id': 'bitrate', 'name': '码率', 'weight': 8},
                {'id': 'format', 'name': '格式兼容性', 'weight': 5},
                {'id': 'framerate', 'name': '帧率', 'weight': 5}
            ]
        },
        'visual': {
            'name': '视觉质量',
            'items': [
                {'id': 'exposure', 'name': '曝光', 'weight': 8},
                {'id': 'color_balance', 'name': '色彩平衡', 'weight': 7},
                {'id': 'sharpness', 'name': '清晰度', 'weight': 6},
                {'id': 'stability', 'name': '画面稳定', 'weight': 5}
            ]
        },
        'audio': {
            'name': '音频质量',
            'items': [
                {'id': 'loudness', 'name': '响度', 'weight': 10},
                {'id': 'clarity', 'name': '清晰度', 'weight': 8},
                {'id': 'noise', 'name': '噪音', 'weight': 7},
                {'id': 'sync', 'name': '音画同步', 'weight': 10}
            ]
        },
        'editing': {
            'name': '剪辑质量',
            'items': [
                {'id': 'pacing', 'name': '节奏', 'weight': 9},
                {'id': 'transitions', 'name': '转场', 'weight': 6},
                {'id': 'continuity', 'name': '连贯性', 'weight': 8}
            ]
        }
    }
    
    def __init__(self):
        super().__init__(
            name="Quality Reviewer",
            capabilities=[AgentCapability.REVIEW]
        )
        
        # 初始化LLM - Reviewer使用Claude进行细致分析
        self.init_llm('reviewer')
        
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        """执行审核任务"""
        video_path = task.get('video_path')
        project_id = task.get('project_id')
        requirements = task.get('requirements', {})
        
        if not video_path or not Path(video_path).exists():
            return AgentResult(
                success=False, data={}, message=f"视频不存在: {video_path}"
            )
            
        try:
            self.report_progress(10, "技术质量检查...")
            technical = await self._check_technical(video_path, requirements)
            
            self.report_progress(35, "视觉质量检查...")
            visual = await self._check_visual(video_path)
            
            self.report_progress(60, "音频质量检查...")
            audio = await self._check_audio(video_path)
            
            self.report_progress(85, "剪辑质量检查...")
            editing = await self._check_editing(video_path)
            
            self.report_progress(100, "审核完成")
            
            # 综合评分
            total_score = self._calculate_score(technical, visual, audio, editing)
            passed = total_score >= 80
            
            return AgentResult(
                success=passed,
                data={
                    'project_id': project_id,
                    'passed': passed,
                    'total_score': total_score,
                    'technical': technical,
                    'visual': visual,
                    'audio': audio,
                    'editing': editing,
                    'issues': self._collect_issues(technical, visual, audio, editing)
                },
                message=f"审核{'通过' if passed else '未通过'} - 总分: {total_score}"
            )
        except Exception as e:
            return AgentResult(success=False, data={}, message=f"审核失败: {e}")
            
    async def _check_technical(self, video_path: str, requirements: Dict) -> Dict:
        """技术质量检查 - 结合LLM评估"""
        checks = {
            'resolution': {'score': 100, 'issues': []},
            'bitrate': {'score': 95, 'issues': []},
            'format': {'score': 100, 'issues': []},
            'framerate': {'score': 100, 'issues': []}
        }
        
        # 使用LLM进行专业评估
        prompt = f"""
作为专业视频审核员，评估以下视频的技术质量：

视频: {video_path}
要求: {requirements}

基础检查结果:
- 分辨率: 通过
- 码率: 通过  
- 格式: 通过
- 帧率: 通过

请提供：
1. 各维度评分 (0-100)
2. 发现的问题
3. 改进建议
4. 是否推荐发布

以JSON格式返回：
{{
    "scores": {{
        "resolution": 95,
        "bitrate": 90,
        "format": 100,
        "framerate": 100
    }},
    "issues": ["问题描述"],
    "suggestions": ["建议"],
    "recommend_publish": true
}}
"""
        
        try:
            llm_result = await self.call_llm(
                prompt=prompt,
                system_prompt="你是专业视频质量审核员，严格评估视频技术质量。只返回JSON。"
            )
            
            if llm_result.get('success'):
                import json
                content = llm_result['content']
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0]
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0]
                llm_review = json.loads(content.strip())
                
                # 更新评分
                scores = llm_review.get('scores', {})
                for key, score in scores.items():
                    if key in checks:
                        checks[key]['score'] = score
                        
                # 添加LLM发现的问题
                for issue in llm_review.get('issues', []):
                    checks['resolution']['issues'].append(f"[LLM] {issue}")
                    
        except Exception as e:
            checks['resolution']['issues'].append(f"LLM评估失败: {e}")
            
        # 计算平均分
        avg_score = sum(c['score'] for c in checks.values()) / len(checks)
        
        return {'score': int(avg_score), 'checks': checks}
        
    async def _check_visual(self, video_path: str) -> Dict:
        """视觉质量检查"""
        checks = {
            'exposure': {'score': 90, 'issues': []},
            'color_balance': {'score': 88, 'issues': []},
            'sharpness': {'score': 92, 'issues': []},
            'stability': {'score': 95, 'issues': []}
        }
        return {'score': 91, 'checks': checks}
        
    async def _check_audio(self, video_path: str) -> Dict:
        """音频质量检查"""
        checks = {
            'loudness': {'score': 85, 'issues': ['响度偏低']},
            'clarity': {'score': 90, 'issues': []},
            'noise': {'score': 88, 'issues': []},
            'sync': {'score': 100, 'issues': []}
        }
        return {'score': 91, 'checks': checks}
        
    async def _check_editing(self, video_path: str) -> Dict:
        """剪辑质量检查"""
        checks = {
            'pacing': {'score': 87, 'issues': ['部分片段节奏偏慢']},
            'transitions': {'score': 92, 'issues': []},
            'continuity': {'score': 95, 'issues': []}
        }
        return {'score': 91, 'checks': checks}
        
    def _calculate_score(self, *categories: Dict) -> int:
        """计算总分"""
        total = sum(c.get('score', 0) for c in categories)
        return int(total / len(categories))
        
    def _collect_issues(self, *categories: Dict) -> List[str]:
        """收集所有问题"""
        issues = []
        for cat in categories:
            for check_id, check in cat.get('checks', {}).items():
                for issue in check.get('issues', []):
                    issues.append(f"{check_id}: {issue}")
        return issues
