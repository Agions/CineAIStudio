"""
剪辑模板管理器 (Cut Template Manager)

管理剪辑模板的创建、编辑、存储和应用。
支持预设模板和用户自定义模板。
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TemplateStyle(Enum):
    """模板风格"""
    NARRATIVE = "narrative"           # 叙事完整
    HIGHLIGHT = "highlight"           # 高光集锦
    TRAILER = "trailer"               # 悬念预告
    CUSTOM = "custom"                 # 自定义


class SegmentRule(Enum):
    """片段规则"""
    KEEP = "keep"                    # 保留
    REMOVE = "remove"                # 删除
    SHRINK = "shrink"                # 缩短


@dataclass
class SegmentConfig:
    """片段配置"""
    scene_type: str                   # 场景类型
    rule: SegmentRule                 # 处理规则
    min_duration: float = 0.0       # 最小保留时长
    max_duration: float = 0.0        # 最大保留时长（0表示不限制）
    priority: int = 0                # 优先级（越高越优先保留）


@dataclass
class CutTemplate:
    """剪辑模板"""
    id: str
    name: str
    description: str
    style: TemplateStyle

    # 时间约束
    target_duration: float = 0.0     # 目标时长（秒），0表示保持原长
    min_segment_duration: float = 3.0 # 最小片段时长
    max_segment_duration: float = 0.0 # 最大片段时长，0表示不限制

    # 片段规则
    segment_rules: List[SegmentConfig] = None

    # 风格设置
    keep_opening: bool = True         # 保留开场
    keep_ending: bool = True          # 保留结局
    keep_climax: bool = True           # 保留高潮

    # 情感约束
    min_emotion_intensity: float = 0.0 # 最小情感强度
    max_emotion_intensity: float = 1.0 # 最大情感强度

    # 高级设置
    transition_duration: float = 0.5   # 转场时长
    smooth_cuts: bool = True           # 平滑剪辑
    preserve_audio_sync: bool = True   # 保持音频同步

    # 元数据
    is_preset: bool = False           # 是否为预设模板
    created_at: str = ""              # 创建时间
    updated_at: str = ""               # 更新时间
    author: str = ""                  # 作者

    def __post_init__(self):
        if self.segment_rules is None:
            self.segment_rules = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['style'] = self.style.value
        data['segment_rules'] = [
            {**asdict(rule), 'rule': rule.rule.value}
            for rule in self.segment_rules
        ]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CutTemplate':
        """从字典创建"""
        style = TemplateStyle(data.get('style', 'custom'))
        segment_rules = []
        for rule_data in data.get('segment_rules', []):
            rule_data = dict(rule_data)
            rule_data['rule'] = SegmentRule(rule_data.get('rule', 'keep'))
            segment_rules.append(SegmentConfig(**rule_data))

        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            description=data.get('description', ''),
            style=style,
            target_duration=data.get('target_duration', 0.0),
            min_segment_duration=data.get('min_segment_duration', 3.0),
            max_segment_duration=data.get('max_segment_duration', 0.0),
            segment_rules=segment_rules,
            keep_opening=data.get('keep_opening', True),
            keep_ending=data.get('keep_ending', True),
            keep_climax=data.get('keep_climax', True),
            min_emotion_intensity=data.get('min_emotion_intensity', 0.0),
            max_emotion_intensity=data.get('max_emotion_intensity', 1.0),
            transition_duration=data.get('transition_duration', 0.5),
            smooth_cuts=data.get('smooth_cuts', True),
            preserve_audio_sync=data.get('preserve_audio_sync', True),
            is_preset=data.get('is_preset', False),
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            author=data.get('author', '')
        )


class CutTemplateManager:
    """剪辑模板管理器"""

    # 预设模板
    PRESET_TEMPLATES = [
        {
            "id": "narrative_full",
            "name": "叙事完整版",
            "description": "保留故事完整性，按叙事结构完整剪辑",
            "style": "narrative",
            "target_duration": 0,
            "min_segment_duration": 5.0,
            "keep_opening": True,
            "keep_ending": True,
            "keep_climax": True,
            "segment_rules": [],
            "is_preset": True
        },
        {
            "id": "highlight_compilation",
            "name": "高光集锦",
            "description": "只保留精彩片段，删除平淡内容",
            "style": "highlight",
            "target_duration": 60,
            "min_segment_duration": 3.0,
            "keep_opening": False,
            "keep_ending": False,
            "keep_climax": True,
            "segment_rules": [
                {"scene_type": "climax", "rule": "keep", "priority": 100},
                {"scene_type": "highlight", "rule": "keep", "priority": 90},
                {"scene_type": "rising_action", "rule": "keep", "priority": 50},
                {"scene_type": "opening", "rule": "remove", "priority": 0},
                {"scene_type": "conclusion", "rule": "remove", "priority": 0},
            ],
            "is_preset": True
        },
        {
            "id": "trailer_style",
            "name": "悬念预告",
            "description": "制造悬念和期待，适合做预告片",
            "style": "trailer",
            "target_duration": 45,
            "min_segment_duration": 2.0,
            "keep_opening": True,
            "keep_ending": False,
            "keep_climax": True,
            "segment_rules": [
                {"scene_type": "opening", "rule": "keep", "min_duration": 3, "priority": 80},
                {"scene_type": "climax", "rule": "keep", "priority": 100},
                {"scene_type": "rising_action", "rule": "shrink", "max_duration": 5, "priority": 60},
            ],
            "is_preset": True
        },
        {
            "id": "viral_short",
            "name": "病毒式短视频",
            "description": "开头即高潮，快速抓住观众注意力",
            "style": "highlight",
            "target_duration": 30,
            "min_segment_duration": 1.0,
            "max_segment_duration": 10.0,
            "keep_opening": False,
            "keep_ending": False,
            "keep_climax": True,
            "segment_rules": [
                {"scene_type": "climax", "rule": "keep", "priority": 100},
                {"scene_type": "highlight", "rule": "keep", "priority": 90},
                {"scene_type": "rising_action", "rule": "shrink", "max_duration": 5, "priority": 50},
            ],
            "is_preset": True
        },
        {
            "id": "documentary_style",
            "name": "纪录片风格",
            "description": "保持叙事连贯，适合知识类内容",
            "style": "narrative",
            "target_duration": 0,
            "min_segment_duration": 10.0,
            "keep_opening": True,
            "keep_ending": True,
            "keep_climax": True,
            "segment_rules": [],
            "is_preset": True
        }
    ]

    def __init__(self, template_dir: Optional[str] = None):
        """
        初始化模板管理器

        Args:
            template_dir: 自定义模板存储目录
        """
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            self.template_dir = Path.home() / ".videoforge" / "templates"

        self.template_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"CutTemplateManager initialized, template_dir: {self.template_dir}")

    def get_all_templates(self) -> List[CutTemplate]:
        """获取所有模板（预设 + 自定义）"""
        templates = []

        # 加载预设模板
        for preset_data in self.PRESET_TEMPLATES:
            templates.append(CutTemplate.from_dict(preset_data))

        # 加载自定义模板
        custom_templates = self._load_custom_templates()
        templates.extend(custom_templates)

        return templates

    def get_templates_by_style(self, style: TemplateStyle) -> List[CutTemplate]:
        """获取指定风格的模板"""
        return [t for t in self.get_all_templates() if t.style == style]

    def get_template_by_id(self, template_id: str) -> Optional[CutTemplate]:
        """根据 ID 获取模板"""
        # 先检查预设
        for preset in self.PRESET_TEMPLATES:
            if preset['id'] == template_id:
                return CutTemplate.from_dict(preset)

        # 检查自定义模板
        custom_file = self.template_dir / f"{template_id}.json"
        if custom_file.exists():
            try:
                with open(custom_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return CutTemplate.from_dict(data)
            except Exception as e:
                logger.error(f"Failed to load template {template_id}: {e}")

        return None

    def save_template(self, template: CutTemplate) -> bool:
        """保存自定义模板"""
        if template.is_preset:
            logger.warning("Cannot modify preset templates")
            return False

        try:
            template.updated_at = datetime.now().isoformat()
            template_file = self.template_dir / f"{template.id}.json"

            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)

            logger.info(f"Saved custom template: {template.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to save template {template.id}: {e}")
            return False

    def delete_template(self, template_id: str) -> bool:
        """删除自定义模板"""
        # 检查是否为预设模板
        for preset in self.PRESET_TEMPLATES:
            if preset['id'] == template_id:
                logger.warning("Cannot delete preset templates")
                return False

        template_file = self.template_dir / f"{template_id}.json"
        if template_file.exists():
            try:
                template_file.unlink()
                logger.info(f"Deleted template: {template_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete template {template_id}: {e}")
                return False

        return False

    def create_template(
        self,
        name: str,
        description: str = "",
        style: TemplateStyle = TemplateStyle.CUSTOM,
        **kwargs
    ) -> CutTemplate:
        """创建新模板"""
        import uuid

        template = CutTemplate(
            id=str(uuid.uuid4())[:8],
            name=name,
            description=description,
            style=style,
            is_preset=False,
            **kwargs
        )

        self.save_template(template)
        return template

    def _load_custom_templates(self) -> List[CutTemplate]:
        """加载自定义模板"""
        templates = []

        if not self.template_dir.exists():
            return templates

        for template_file in self.template_dir.glob("*.json"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                templates.append(CutTemplate.from_dict(data))
            except Exception as e:
                logger.warning(f"Failed to load custom template {template_file}: {e}")

        return templates

    def apply_template(
        self,
        template: CutTemplate,
        analysis_result: 'StoryAnalysisResult'  # noqa: F821
    ) -> List[Dict[str, Any]]:
        """
        应用模板到分析结果，生成剪辑点

        Args:
            template: 剪辑模板
            analysis_result: 剧情分析结果

        Returns:
            剪辑点列表
        """
        cuts = []
        segments = analysis_result.segments

        if not segments:
            # 如果没有分段，按时间均匀分割
            return self._generate_uniform_cuts(analysis_result, template)

        # 处理每个片段
        for segment in segments:
            cut = self._process_segment(segment, template, analysis_result)
            if cut:
                cuts.append(cut)

        # 应用时间约束
        if template.target_duration > 0:
            cuts = self._adjust_to_duration(cuts, template.target_duration)

        # 平滑剪辑
        if template.smooth_cuts:
            cuts = self._smooth_cuts(cuts)

        return cuts

    def _process_segment(
        self,
        segment: 'SceneSegment',  # noqa: F821
        template: CutTemplate,
        analysis_result: 'StoryAnalysisResult'  # noqa: F821
    ) -> Optional[Dict[str, Any]]:
        """处理单个片段"""
        scene_type = segment.scene_type.value

        # 检查片段规则
        for rule_config in template.segment_rules:
            if rule_config.scene_type == scene_type:
                if rule_config.rule == SegmentRule.REMOVE:
                    return None
                elif rule_config.rule == SegmentRule.SHRINK:
                    max_dur = rule_config.max_duration
                    if max_dur > 0 and segment.duration > max_dur:
                        return {
                            "type": "keep",
                            "start": segment.start_time,
                            "end": segment.start_time + max_dur,
                            "duration": max_dur,
                            "title": segment.title,
                            "reason": f"缩短至 {max_dur}秒",
                            "scene_type": scene_type,
                            "priority": rule_config.priority
                        }

        # 检查特殊处理
        if scene_type == "opening" and not template.keep_opening:
            return None
        if scene_type == "conclusion" and not template.keep_ending:
            return None
        if scene_type == "climax" and not template.keep_climax:
            return None

        # 检查时长约束
        duration = segment.duration
        if template.max_segment_duration > 0 and duration > template.max_segment_duration:
            duration = template.max_segment_duration

        if duration < template.min_segment_duration:
            return None

        return {
            "type": "keep",
            "start": segment.start_time,
            "end": segment.start_time + duration,
            "duration": duration,
            "title": segment.title,
            "reason": f"保留{segment.scene_type.display_name}：{segment.title}",
            "scene_type": scene_type,
            "priority": 50
        }

    def _generate_uniform_cuts(
        self,
        analysis_result: 'StoryAnalysisResult',  # noqa: F821
        template: CutTemplate
    ) -> List[Dict[str, Any]]:
        """生成均匀分割的剪辑"""
        cuts = []
        duration = template.target_duration if template.target_duration > 0 else analysis_result.duration
        clip_duration = max(template.min_segment_duration, 5.0)
        current_time = 0.0

        while current_time < duration:
            end_time = min(current_time + clip_duration, duration)
            cuts.append({
                "type": "keep",
                "start": current_time,
                "end": end_time,
                "duration": end_time - current_time,
                "title": f"片段 {len(cuts) + 1}",
                "reason": "自动分割",
                "scene_type": "segment",
                "priority": 50
            })
            current_time = end_time

        return cuts

    def _adjust_to_duration(
        self,
        cuts: List[Dict[str, Any]],
        target_duration: float
    ) -> List[Dict[str, Any]]:
        """调整剪辑以达到目标时长"""
        current_duration = sum(c.get("duration", 0) for c in cuts)

        if current_duration <= target_duration:
            return cuts

        # 按优先级排序，从低优先级开始裁剪
        sorted_cuts = sorted(cuts, key=lambda x: x.get("priority", 0))

        for cut in sorted_cuts:
            if current_duration <= target_duration:
                break

            excess = current_duration - target_duration
            cut_duration = cut.get("duration", 0)

            if cut_duration > excess:
                # 部分裁剪
                cut["duration"] -= excess
                cut["end"] = cut["start"] + cut["duration"]
                current_duration -= excess
            else:
                # 整个片段删除
                cuts.remove(cut)
                current_duration -= cut_duration

        return cuts

    def _smooth_cuts(
        self,
        cuts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """平滑剪辑点"""
        if not cuts:
            return cuts

        # 确保片段之间平滑过渡
        cuts.sort(key=lambda x: x["start"])

        smoothed = [cuts[0]]

        for cut in cuts[1:]:
            last = smoothed[-1]
            gap = cut["start"] - last["end"]

            if gap < 0.1:  # 几乎重叠，合并
                last["end"] = max(last["end"], cut["end"])
                last["duration"] = last["end"] - last["start"]
            else:
                smoothed.append(cut)

        return smoothed
