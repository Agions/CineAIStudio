#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
项目模板系统
提供预设的视频创作模板，快速启动项目
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum


class TemplateCategory(Enum):
    """模板分类"""
    COMMENTARY = "commentary"        # 视频解说
    MASHUP = "mashup"                # 混剪
    MONOLOGUE = "monologue"          # 独白
    VLOG = "vlog"                    # Vlog
    SHORT_DRAMA = "short_drama"      # 短剧
    TUTORIAL = "tutorial"            # 教程
    PROMOTION = "promotion"          # 推广
    CUSTOM = "custom"                # 自定义


@dataclass
class VoicePreset:
    """配音预设"""
    provider: str = "edge"
    voice_id: str = "zh-CN-XiaoxiaoNeural"
    rate: float = 1.0
    style: str = "narration"


@dataclass
class ExportPreset:
    """导出预设"""
    format: str = "jianying"          # jianying/premiere/davinci/fcpxml
    resolution: str = "1080p"
    fps: int = 30
    include_subtitles: bool = True
    subtitle_format: str = "srt"


@dataclass
class AIPreset:
    """AI 分析预设"""
    keyframe_interval: float = 2.0
    use_vision_api: bool = True
    vision_provider: str = "openai"
    script_style: str = "informative"
    script_length: str = "medium"      # short/medium/long


@dataclass
class ProjectTemplate:
    """项目模板"""
    id: str
    name: str
    description: str
    category: TemplateCategory
    icon: str = "🎬"
    tags: List[str] = field(default_factory=list)

    # 预设
    voice: VoicePreset = field(default_factory=VoicePreset)
    export: ExportPreset = field(default_factory=ExportPreset)
    ai: AIPreset = field(default_factory=AIPreset)

    # 元数据
    author: str = "ClipFlow"
    version: str = "1.0"
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectTemplate":
        data["category"] = TemplateCategory(data["category"])
        data["voice"] = VoicePreset(**data.get("voice", {}))
        data["export"] = ExportPreset(**data.get("export", {}))
        data["ai"] = AIPreset(**data.get("ai", {}))
        return cls(**data)


# ========== 内置模板 ==========

BUILTIN_TEMPLATES = [
    ProjectTemplate(
        id="movie_commentary",
        name="🎬 电影解说",
        description="AI 分析电影画面 → 生成解说文案 → 配音 → 导出剪映草稿",
        category=TemplateCategory.COMMENTARY,
        icon="🎬",
        tags=["电影", "解说", "热门"],
        voice=VoicePreset(voice_id="zh-CN-YunxiNeural", rate=1.05, style="narration"),
        export=ExportPreset(format="jianying", include_subtitles=True),
        ai=AIPreset(keyframe_interval=3.0, script_style="storytelling",
                    script_length="long"),
    ),
    ProjectTemplate(
        id="music_mashup",
        name="🎵 音乐混剪",
        description="多段素材 → 节拍分析 → 智能匹配 → 自动转场",
        category=TemplateCategory.MASHUP,
        icon="🎵",
        tags=["混剪", "音乐", "节奏"],
        voice=VoicePreset(provider="none"),
        export=ExportPreset(format="jianying", fps=30),
        ai=AIPreset(keyframe_interval=1.0, script_style="none"),
    ),
    ProjectTemplate(
        id="emotional_monologue",
        name="🎭 情感独白",
        description="画面情感分析 → 第一人称独白 → 电影级字幕",
        category=TemplateCategory.MONOLOGUE,
        icon="🎭",
        tags=["独白", "情感", "文艺"],
        voice=VoicePreset(voice_id="zh-CN-XiaomoNeural", rate=0.9,
                         style="sad"),
        export=ExportPreset(format="jianying", include_subtitles=True,
                           subtitle_format="ass"),
        ai=AIPreset(keyframe_interval=2.0, script_style="emotional",
                    script_length="medium"),
    ),
    ProjectTemplate(
        id="short_drama_clip",
        name="📺 短剧切片",
        description="识别高能片段 → 自动切片 → 加字幕 → 导出",
        category=TemplateCategory.SHORT_DRAMA,
        icon="📺",
        tags=["短剧", "切片", "爆款"],
        voice=VoicePreset(provider="none"),
        export=ExportPreset(format="jianying", resolution="1080p",
                           include_subtitles=True),
        ai=AIPreset(keyframe_interval=1.5, use_vision_api=True),
    ),
    ProjectTemplate(
        id="product_promo",
        name="🛍️ 产品推广",
        description="产品画面分析 → 卖点提取 → 推广文案 → 活力配音",
        category=TemplateCategory.PROMOTION,
        icon="🛍️",
        tags=["推广", "产品", "带货"],
        voice=VoicePreset(voice_id="zh-CN-XiaoxuanNeural", rate=1.1,
                         style="cheerful"),
        export=ExportPreset(format="jianying"),
        ai=AIPreset(script_style="promotional", script_length="short"),
    ),
]


class TemplateManager:
    """
    模板管理器

    管理内置模板和用户自定义模板
    """

    def __init__(self, user_template_dir: Optional[str] = None):
        self._builtin = {t.id: t for t in BUILTIN_TEMPLATES}
        self._user_templates = {}  # type: Dict[str, ProjectTemplate]
        self._user_dir = Path(user_template_dir) if user_template_dir else None

        if self._user_dir:
            self._load_user_templates()

    def list_templates(self, category: Optional[TemplateCategory] = None,
                       tag: Optional[str] = None) -> List[ProjectTemplate]:
        """列出模板"""
        all_templates = list(self._builtin.values()) + list(
            self._user_templates.values())

        if category:
            all_templates = [t for t in all_templates
                           if t.category == category]
        if tag:
            all_templates = [t for t in all_templates
                           if tag in t.tags]

        return all_templates

    def get_template(self, template_id: str) -> Optional[ProjectTemplate]:
        """获取模板"""
        return (self._builtin.get(template_id)
                or self._user_templates.get(template_id))

    def save_as_template(self, template: ProjectTemplate) -> str:
        """保存为用户模板"""
        self._user_templates[template.id] = template

        if self._user_dir:
            self._user_dir.mkdir(parents=True, exist_ok=True)
            path = self._user_dir / f"{template.id}.json"
            path.write_text(
                json.dumps(template.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

        return template.id

    def delete_template(self, template_id: str) -> bool:
        """删除用户模板（不能删内置模板）"""
        if template_id in self._builtin:
            return False

        if template_id in self._user_templates:
            del self._user_templates[template_id]
            if self._user_dir:
                path = self._user_dir / f"{template_id}.json"
                if path.exists():
                    path.unlink()
            return True
        return False

    def get_categories(self) -> List[Dict[str, str]]:
        """获取所有分类"""
        return [
            {"id": c.value, "name": {
                "commentary": "视频解说",
                "mashup": "混剪",
                "monologue": "独白",
                "vlog": "Vlog",
                "short_drama": "短剧",
                "tutorial": "教程",
                "promotion": "推广",
                "custom": "自定义",
            }.get(c.value, c.value)}
            for c in TemplateCategory
        ]

    def _load_user_templates(self):
        """加载用户模板"""
        if not self._user_dir or not self._user_dir.exists():
            return

        for path in self._user_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                template = ProjectTemplate.from_dict(data)
                self._user_templates[template.id] = template
            except Exception as e:
                print(f"加载模板 {path} 失败: {e}")
