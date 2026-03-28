#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI 提示词模板系统

支持创建、管理和使用自定义的 AI 提示词模板。

功能：
- 预置多种风格的提示词模板
- 自定义模板变量
- 模板分类管理
- 模板预览和测试

使用示例:
    from app.services.core import PromptTemplateManager, PromptTemplate
    
    manager = PromptTemplateManager()
    
    # 使用预置模板
    template = manager.get_template("bilibili_explainer")
    prompt = template.render(
        topic="什么是人工智能",
        duration=180,
        style="专业"
    )
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum

# 获取 logger
logger = logging.getLogger(__name__)


class TemplateCategory(Enum):
    """模板分类"""
    COMMENTARY = "commentary"      # 解说类
    MASHUP = "mashup"            # 混剪类
    MONOLOGUE = "monologue"       # 独白类
    SOCIAL = "social"            # 社交媒体
    EDUCATIONAL = "educational"  # 教育类
    ENTERTAINMENT = "entertainment"  # 娱乐类
    CUSTOM = "custom"            # 自定义


@dataclass
class TemplateVariable:
    """模板变量"""
    name: str                    # 变量名
    type: str = "string"         # 类型: string/number/boolean/select
    description: str = ""        # 描述
    default: Any = None          # 默认值
    required: bool = True        # 是否必需
    options: List[str] = field(default_factory=list)  # 可选值（select类型）


@dataclass
class PromptTemplate:
    """
    AI 提示词模板
    
    Attributes:
        id: 模板唯一ID
        name: 模板名称
        category: 模板分类
        description: 模板描述
        system_prompt: 系统提示词
        user_template: 用户提示词模板（支持变量）
        variables: 模板变量定义
        tags: 标签
        is_builtin: 是否内置模板
    """
    id: str = ""
    name: str = ""
    category: str = "custom"
    description: str = ""
    
    # 提示词内容
    system_prompt: str = ""
    user_template: str = ""
    
    # 变量定义
    variables: List[TemplateVariable] = field(default_factory=list)
    
    # 元数据
    tags: List[str] = field(default_factory=list)
    is_builtin: bool = False
    
    # 统计
    use_count: int = 0
    rating: float = 0.0
    
    def __post_init__(self):
        if not self.id:
            import uuid
            self.id = str(uuid.uuid4())[:8]
    
    def render(self, **kwargs) -> Dict[str, str]:
        """
        渲染模板
        
        Args:
            **kwargs: 变量值
            
        Returns:
            {"system": "...", "user": "..."}
        """
        # 合并默认值
        values = {}
        for var in self.variables:
            if var.name in kwargs:
                values[var.name] = kwargs[var.name]
            elif var.default is not None:
                values[var.name] = var.default
            elif var.required:
                raise ValueError(f"缺少必需变量: {var.name}")
        
        # 渲染模板
        system = self._render_string(self.system_prompt, values)
        user = self._render_string(self.user_template, values)
        
        return {"system": system, "user": user}
    
    def _render_string(self, template: str, values: Dict) -> str:
        """渲染单个字符串模板"""
        result = template
        
        for key, value in values.items():
            # 支持 {{variable}} 和 $variable 格式
            # 替换 {{key}}
            double_brace = "{{" + key + "}}"
            result = result.replace(double_brace, str(value))
            
            # 替换 ${key} 或 ${key}
            result = re.sub(r"\$\{" + re.escape(key) + r"\}", str(value), result)
            result = re.sub(r"\$" + re.escape(key) + r"\b", str(value), result)
        
        return result


# ==================== 预置模板 ====================

def get_builtin_templates() -> List[PromptTemplate]:
    """获取所有预置模板"""
    return [
        # ========== 解说类 ==========
        PromptTemplate(
            id="bilibili_explainer",
            name="B站知识解说",
            category=TemplateCategory.COMMENTARY.value,
            description="适合B站知识区up主的视频解说模板",
            system_prompt="你是一位专业的知识类视频创作者，擅长用通俗易懂的语言讲解复杂概念。你的解说风格幽默风趣但不失专业性。",
            user_template="请为以下主题创作一段{duration}秒的视频解说词：\n\n主题：{topic}\n风格：{style}\n目标观众：{audience}\n\n要求：\n1. 开场要有吸引力，能抓住观众\n2. 内容要有信息量，干货满满\n3. 结尾要有互动性，引导点赞投币\n4. 语言口语化，适合视频表达",
            variables=[
                TemplateVariable(name="topic", description="视频主题", default="人工智能"),
                TemplateVariable(name="duration", type="number", description="时长（秒）", default=180),
                TemplateVariable(name="style", description="风格", default="专业", options=["专业", "幽默", "通俗", "严谨"]),
                TemplateVariable(name="audience", description="目标观众", default="科普爱好者"),
            ],
            tags=["B站", "知识区", "解说", "教程"],
            is_builtin=True,
        ),
        
        PromptTemplate(
            id="movie_review",
            name="电影解说",
            category=TemplateCategory.COMMENTARY.value,
            description="电影/影评类视频解说模板",
            system_prompt="你是一位资深影评人，擅长分析电影剧情、镜头语言和导演意图。你的解说要有深度，能让观众对电影产生兴趣。",
            user_template="为电影《{movie_name}》创作一段{duration}秒的影评解说。\n\n电影类型：{genre}\n解说角度：{angle}\n\n要求：\n1. 开头设置悬念，吸引观众\n2. 不剧透关键情节\n3. 分析电影的亮点和特色\n4. 结尾给出观影建议",
            variables=[
                TemplateVariable(name="movie_name", description="电影名称", default="肖申克的救赎"),
                TemplateVariable(name="duration", type="number", description="时长（秒）", default=120),
                TemplateVariable(name="genre", description="电影类型", default="剧情"),
                TemplateVariable(name="angle", description="解说角度", default="剧情分析", options=["剧情分析", "镜头语言", "导演风格", "主题思想"]),
            ],
            tags=["电影", "影评", "解说"],
            is_builtin=True,
        ),
        
        PromptTemplate(
            id="product_review",
            name="产品测评",
            category=TemplateCategory.COMMENTARY.value,
            description="3C产品/数码产品测评解说模板",
            system_prompt="你是一位专业的产品测评博主，测评风格客观公正，既肯定优点也不回避缺点。",
            user_template="为产品「{product_name}」创作一段{duration}秒的测评解说。\n\n产品类型：{product_type}\n测评重点：{focus}\n\n要求：\n1. 客观描述产品外观和基本参数\n2. 重点讲述使用体验\n3. 对比同类产品的优缺点\n4. 给出购买建议",
            variables=[
                TemplateVariable(name="product_name", description="产品名称", default="iPhone 15"),
                TemplateVariable(name="duration", type="number", description="时长（秒）", default=180),
                TemplateVariable(name="product_type", description="产品类型", default="手机"),
                TemplateVariable(name="focus", description="测评重点", default="拍照", options=["拍照", "性能", "续航", "系统", "性价比"]),
            ],
            tags=["测评", "数码", "3C"],
            is_builtin=True,
        ),
        
        # ========== 社交媒体 ==========
        PromptTemplate(
            id="tiktok_script",
            name="抖音短视频",
            category=TemplateCategory.SOCIAL.value,
            description="适合抖音的短平快内容模板",
            system_prompt="你是一位抖音内容创作者，擅长创作爆款短视频内容。风格要接地气、有看点、能引发共鸣。",
            user_template="创作一条{length}秒的抖音短视频脚本。\n\n主题：{topic}\n内容形式：{format}\n\n要求：\n1. 前3秒必须有爆点\n2. 内容紧凑，节奏快\n3. 有反转或亮点\n4. 引导互动（评论、点赞）",
            variables=[
                TemplateVariable(name="topic", description="视频主题", default="生活小技巧"),
                TemplateVariable(name="length", type="number", description="时长（秒）", default=30),
                TemplateVariable(name="format", description="内容形式", default="剧情", options=["剧情", "口播", "展示", "教程", "搞笑"]),
            ],
            tags=["抖音", "短视频", "爆款"],
            is_builtin=True,
        ),
        
        PromptTemplate(
            id="xiaohongshu_post",
            name="小红书种草",
            category=TemplateCategory.SOCIAL.value,
            description="小红书图文/视频种草模板",
            system_prompt="你是一位小红书博主，擅长创作种草内容。文风要真实、有代入感、让人想购买。",
            user_template="为产品「{product}」创作一篇小红书种草内容。\n\n种草角度：{angle}\n目标人群：{target}\n\n要求：\n1. 标题要吸引人\n2. 内容真实可信\n3. 突出产品亮点\n4. 引导收藏和购买",
            variables=[
                TemplateVariable(name="product", description="产品名称", default="某品牌护肤品"),
                TemplateVariable(name="angle", description="种草角度", default="使用体验", options=["使用体验", "成分分析", "对比测评", "选购指南"]),
                TemplateVariable(name="target", description="目标人群", default="年轻女性"),
            ],
            tags=["小红书", "种草", "好物推荐"],
            is_builtin=True,
        ),
        
        # ========== 教育类 ==========
        PromptTemplate(
            id="online_course",
            name="在线课程讲解",
            category=TemplateCategory.EDUCATIONAL.value,
            description="适合网课/教程视频的讲解模板",
            system_prompt="你是一位经验丰富的在线课程讲师，擅长将复杂知识分解成易于理解的模块。讲解要有条理，重点突出。",
            user_template="创作一节关于「{topic}」的在线课程讲解。\n\n课程类型：{course_type}\n难度级别：{level}\n课程时长：{duration}分钟\n\n要求：\n1. 开场自我介绍+课程介绍\n2. 知识点要模块化\n3. 配合案例讲解\n4. 结尾总结+课后作业",
            variables=[
                TemplateVariable(name="topic", description="课程主题", default="Python基础"),
                TemplateVariable(name="course_type", description="课程类型", default="编程教学"),
                TemplateVariable(name="level", description="难度级别", default="入门", options=["入门", "进阶", "高级"]),
                TemplateVariable(name="duration", type="number", description="时长（分钟）", default=15),
            ],
            tags=["教程", "课程", "教育", "教学"],
            is_builtin=True,
        ),
        
        PromptTemplate(
            id="science_explain",
            name="科普讲解",
            category=TemplateCategory.EDUCATIONAL.value,
            description="科普类视频讲解模板",
            system_prompt="你是一位科普作家，擅长用生动的语言讲解科学知识，让普通人也能理解前沿科技。",
            user_template="创作一段关于「{topic}」的科普讲解。\n\n科学领域：{field}\n讲解深度：{depth}\n时长：约{duration}秒\n\n要求：\n1. 从生活现象切入\n2. 解释科学原理\n3. 举出实际应用\n4. 激发探索兴趣",
            variables=[
                TemplateVariable(name="topic", description="科普主题", default="量子计算"),
                TemplateVariable(name="field", description="科学领域", default="物理学"),
                TemplateVariable(name="depth", description="讲解深度", default="入门", options=["入门", "中等", "深入"]),
                TemplateVariable(name="duration", type="number", description="时长（秒）", default=180),
            ],
            tags=["科普", "科学", "知识"],
            is_builtin=True,
        ),
        
        # ========== 混剪类 ==========
        PromptTemplate(
            id="mashup_commentary",
            name="混剪解说",
            category=TemplateCategory.MASHUP.value,
            description="视频混剪的解说模板",
            system_prompt="你是一位混剪视频创作者，擅长为混剪视频创作串联性的解说词。",
            user_template="为「{theme}」主题的混剪视频创作解说词。\n\n素材类型：{source_type}\n目标时长：{duration}秒\n解说风格：{style}\n\n要求：\n1. 能串联不同素材\n2. 配合画面节奏\n3. 情感递进\n4. 主题升华",
            variables=[
                TemplateVariable(name="theme", description="混剪主题", default="热血动漫燃向"),
                TemplateVariable(name="source_type", description="素材类型", default="动漫剪辑"),
                TemplateVariable(name="duration", type="number", description="时长（秒）", default=120),
                TemplateVariable(name="style", description="解说风格", default="热血", options=["热血", "感人", "史诗", "搞笑"]),
            ],
            tags=["混剪", "剪辑", "解说"],
            is_builtin=True,
        ),
        
        # ========== 娱乐类 ==========
        PromptTemplate(
            id="vlog_script",
            name="Vlog脚本",
            category=TemplateCategory.ENTERTAINMENT.value,
            description="日常 Vlog 拍摄脚本模板",
            system_prompt="你是一位生活类Vlogger，擅长用镜头记录生活，讲述故事。",
            user_template="创作一个关于「{topic}」的Vlog脚本。\n\nVlog类型：{vlog_type}\n预计时长：{duration}分钟\n\n结构要求：\n1. 开头（吸引眼球的片段）\n2. 发展（主要内容）\n3. 结尾（总结/感想）\n\n包含：镜头建议、台词、口白",
            variables=[
                TemplateVariable(name="topic", description="Vlog主题", default="周末的一天"),
                TemplateVariable(name="vlog_type", description="Vlog类型", default="日常", options=["日常", "旅行", "美食", "探店", "开箱"]),
                TemplateVariable(name="duration", type="number", description="时长（分钟）", default=5),
            ],
            tags=["Vlog", "生活", "记录"],
            is_builtin=True,
        ),
        
        PromptTemplate(
            id="gaming_commentary",
            name="游戏解说",
            category=TemplateCategory.ENTERTAINMENT.value,
            description="游戏实况/解说模板",
            system_prompt="你是一位游戏主播，风格幽默有趣，能让观众看得开心。",
            user_template="创作一段游戏「{game_name}」的实况解说。\n\n游戏类型：{game_type}\n解说风格：{style}\n时长：约{duration}分钟\n\n要求：\n1. 有趣的即兴解说\n2. 对游戏事件的反应\n3. 与观众互动\n4. 适当的节目效果",
            variables=[
                TemplateVariable(name="game_name", description="游戏名称", default="原神"),
                TemplateVariable(name="game_type", description="游戏类型", default="RPG"),
                TemplateVariable(name="style", description="解说风格", default="幽默", options=["幽默", "技术", "剧情向", "搞笑"]),
                TemplateVariable(name="duration", type="number", description="时长（分钟）", default=10),
            ],
            tags=["游戏", "直播", "实况"],
            is_builtin=True,
        ),
    ]


class PromptTemplateManager:
    """
    提示词模板管理器
    
    负责模板的加载、保存和检索
    """
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Args:
            template_dir: 自定义模板存储目录
        """
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            self.template_dir = Path.home() / ".videoforge" / "templates"
        
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载所有模板
        self._templates: Dict[str, PromptTemplate] = {}
        self._load_templates()
    
    def _load_templates(self):
        """加载所有模板"""
        # 加载预置模板
        for template in get_builtin_templates():
            self._templates[template.id] = template
        
        # 加载自定义模板
        custom_dir = self.template_dir / "custom"
        if custom_dir.exists():
            for file in custom_dir.glob("*.json"):
                try:
                    template = self._load_template_file(file)
                    self._templates[template.id] = template
                except Exception as e:
                    logger.warning(f"加载模板失败 {file}: {e}")
    
    def _load_template_file(self, path: Path) -> PromptTemplate:
        """从文件加载模板"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 转换 variables
        if 'variables' in data:
            data['variables'] = [TemplateVariable(**v) for v in data['variables']]
        
        return PromptTemplate(**data)
    
    def _save_template_file(self, template: PromptTemplate):
        """保存模板到文件"""
        if not template.is_builtin:
            custom_dir = self.template_dir / "custom"
            custom_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = custom_dir / f"{template.id}.json"
            
            data = asdict(template)
            # 转换 variables
            data['variables'] = [vars(v) if isinstance(v, TemplateVariable) else v 
                               for v in data['variables']]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """获取模板"""
        return self._templates.get(template_id)
    
    def get_all_templates(self) -> List[PromptTemplate]:
        """获取所有模板"""
        return list(self._templates.values())
    
    def get_templates_by_category(self, category: TemplateCategory) -> List[PromptTemplate]:
        """按分类获取模板"""
        return [t for t in self._templates.values() if t.category == category.value]
    
    def search_templates(self, keyword: str) -> List[PromptTemplate]:
        """搜索模板"""
        keyword = keyword.lower()
        results = []
        
        for template in self._templates.values():
            # 搜索名称、描述、标签
            if (keyword in template.name.lower() or
                keyword in template.description.lower() or
                any(keyword in tag.lower() for tag in template.tags)):
                results.append(template)
        
        return results
    
    def create_template(
        self,
        name: str,
        category: TemplateCategory,
        description: str = "",
        system_prompt: str = "",
        user_template: str = "",
        variables: Optional[List[TemplateVariable]] = None,
        tags: Optional[List[str]] = None,
    ) -> PromptTemplate:
        """
        创建新模板
        
        Args:
            name: 模板名称
            category: 分类
            description: 描述
            system_prompt: 系统提示词
            user_template: 用户提示词模板
            variables: 变量定义
            tags: 标签
            
        Returns:
            创建的模板
        """
        template = PromptTemplate(
            name=name,
            category=category.value,
            description=description,
            system_prompt=system_prompt,
            user_template=user_template,
            variables=variables or [],
            tags=tags or [],
            is_builtin=False,
        )
        
        self._templates[template.id] = template
        self._save_template_file(template)
        
        return template
    
    def update_template(self, template: PromptTemplate) -> bool:
        """
        更新模板
        
        Args:
            template: 模板对象
            
        Returns:
            是否成功
        """
        if template.is_builtin:
            return False
        
        self._templates[template.id] = template
        self._save_template_file(template)
        return True
    
    def delete_template(self, template_id: str) -> bool:
        """
        删除模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            是否成功
        """
        template = self._templates.get(template_id)
        if not template or template.is_builtin:
            return False
        
        # 删除文件
        file_path = self.template_dir / "custom" / f"{template_id}.json"
        if file_path.exists():
            file_path.unlink()
        
        # 删除内存中的模板
        del self._templates[template_id]
        return True
    
    def duplicate_template(
        self,
        template_id: str,
        new_name: str = ""
    ) -> Optional[PromptTemplate]:
        """
        复制模板
        
        Args:
            template_id: 源模板ID
            new_name: 新模板名称（为空则自动生成）
            
        Returns:
            新模板
        """
        source = self._templates.get(template_id)
        if not source:
            return None
        
        import copy
        new_template = copy.deepcopy(source)
        new_template.id = ""
        new_template.is_builtin = False
        new_template.use_count = 0
        
        if new_name:
            new_template.name = new_name
        else:
            new_template.name = f"{source.name} (副本)"
        
        # 保存
        self._templates[new_template.id] = new_template
        self._save_template_file(new_template)
        
        return new_template
    
    def render_prompt(
        self,
        template_id: str,
        **kwargs
    ) -> Dict[str, str]:
        """
        渲染提示词
        
        Args:
            template_id: 模板ID
            **kwargs: 变量值
            
        Returns:
            {"system": "...", "user": "..."}
        """
        template = self._templates.get(template_id)
        if not template:
            raise ValueError(f"模板不存在: {template_id}")
        
        # 更新使用计数
        template.use_count += 1
        
        return template.render(**kwargs)
    
    def export_templates(self, output_path: str, template_ids: List[str] = None):
        """
        导出模板
        
        Args:
            output_path: 输出文件路径
            template_ids: 要导出的模板ID列表（None表示全部）
        """
        templates = self._templates.values()
        
        if template_ids:
            templates = [t for t in templates if t.id in template_ids]
        
        # 排除内置模板
        templates = [t for t in templates if not t.is_builtin]
        
        data = {
            "version": "1.0",
            "templates": [asdict(t) for t in templates]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def import_templates(self, file_path: str) -> int:
        """
        导入模板
        
        Args:
            file_path: 导入文件路径
            
        Returns:
            导入的模板数量
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = 0
        for template_data in data.get("templates", []):
            try:
                # 确保不是内置模板
                template_data['is_builtin'] = False
                template_data['use_count'] = 0
                
                # 转换 variables
                if 'variables' in template_data:
                    template_data['variables'] = [
                        TemplateVariable(**v) for v in template_data['variables']
                    ]
                
                template = PromptTemplate(**template_data)
                self._templates[template.id] = template
                self._save_template_file(template)
                count += 1
            except Exception as e:
                logger.warning(f"导入模板失败: {e}")
        
        return count


# ========== 便捷函数 ==========

def get_template_manager() -> PromptTemplateManager:
    """获取模板管理器单例"""
    global _template_manager
    if _template_manager is None:
        _template_manager = PromptTemplateManager()
    return _template_manager


_template_manager: Optional[PromptTemplateManager] = None


def render_template(template_id: str, **kwargs) -> Dict[str, str]:
    """
    便捷函数：渲染模板
    
    Args:
        template_id: 模板ID
        **kwargs: 变量值
        
    Returns:
        {"system": "...", "user": "..."}
    """
    return get_template_manager().render_prompt(template_id, **kwargs)


# ========== 使用示例 ==========

def demo_templates():
    """演示提示词模板"""
    print("=" * 50)
    print("VideoForge 提示词模板演示")
    print("=" * 50)
    
    manager = PromptTemplateManager()
    
    # 获取所有模板
    all_templates = manager.get_all_templates()
    print(f"\n共有 {len(all_templates)} 个模板")
    
    # 按分类显示
    for category in TemplateCategory:
        templates = manager.get_templates_by_category(category)
        if templates:
            print(f"\n【{category.value}】({len(templates)}个)")
            for t in templates:
                print(f"  - {t.id}: {t.name}")
    
    # 使用模板
    print("\n" + "=" * 50)
    print("使用 B站知识解说 模板:")
    print("=" * 50)
    
    template = manager.get_template("bilibili_explainer")
    if template:
        result = template.render(
            topic="人工智能的未来发展",
            duration=180,
            style="专业",
            audience="科技爱好者"
        )
        print(f"\n【System】\n{result['system']}")
        print(f"\n【User】\n{result['user']}")


if __name__ == '__main__':
    demo_templates()
