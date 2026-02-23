#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
项目设置管理器
提供项目设置的统一管理和配置功能
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import logging

from PyQt6.QtCore import QObject, pyqtSignal

from .config_manager import ConfigManager
from .secure_key_manager import get_secure_key_manager


class SettingType(Enum):
    """设置类型枚举"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    COLOR = "color"
    PATH = "path"
    RESOLUTION = "resolution"


@dataclass
class SettingDefinition:
    """设置定义"""
    key: str
    name: str
    description: str
    setting_type: SettingType
    default_value: Any
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    options: Optional[List[str]] = None
    category: str = "general"
    subcategory: str = ""
    advanced: bool = False
    restart_required: bool = False
    validator: Optional[str] = None  # 验证函数名


@dataclass
class ProjectSettingsProfile:
    """项目设置配置文件"""
    name: str
    description: str
    settings: Dict[str, Any]
    created_at: str
    modified_at: str
    tags: List[str] = field(default_factory=list)
    is_builtin: bool = False


class ProjectSettingsManager(QObject):
    """项目设置管理器"""

    # 信号定义
    settings_changed = pyqtSignal(str, object)  # 设置变更信号
    profile_created = pyqtSignal(str)            # 配置文件创建信号
    profile_applied = pyqtSignal(str)            # 配置文件应用信号
    settings_reset = pyqtSignal()               # 设置重置信号
    error_occurred = pyqtSignal(str, str)       # 错误发生信号

    def __init__(self, config_manager: ConfigManager):
        super().__init__()

        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.secure_key_manager = get_secure_key_manager()

        # 设置存储
        self.settings: Dict[str, Any] = {}
        self.settings_definitions: Dict[str, SettingDefinition] = {}
        self.profiles: Dict[str, ProjectSettingsProfile] = {}

        # 设置文件路径
        self.settings_file = os.path.expanduser("~/ClipFlow/settings/project_settings.json")
        self.profiles_file = os.path.expanduser("~/ClipFlow/settings/profiles.json")

        # 初始化
        self._init_settings_definitions()
        self._load_settings()
        self._load_profiles()

    def _init_settings_definitions(self) -> None:
        """初始化设置定义"""
        # 视频设置
        self.settings_definitions.update({
            'video.resolution': SettingDefinition(
                key='video.resolution',
                name='视频分辨率',
                description='输出视频的分辨率',
                setting_type=SettingType.RESOLUTION,
                default_value='1920x1080',
                options=['3840x2160', '2560x1440', '1920x1080', '1280x720', '854x480'],
                category='video',
                subcategory='basic'
            ),
            'video.fps': SettingDefinition(
                key='video.fps',
                name='帧率',
                description='视频的帧率（每秒帧数）',
                setting_type=SettingType.INTEGER,
                default_value=30,
                min_value=1,
                max_value=120,
                category='video',
                subcategory='basic'
            ),
            'video.bitrate': SettingDefinition(
                key='video.bitrate',
                name='视频比特率',
                description='视频编码比特率',
                setting_type=SettingType.STRING,
                default_value='8000k',
                options=['4000k', '6000k', '8000k', '12000k', '16000k', '20000k'],
                category='video',
                subcategory='advanced'
            ),
            'video.codec': SettingDefinition(
                key='video.codec',
                name='视频编码器',
                description='视频编码器类型',
                setting_type=SettingType.STRING,
                default_value='h264',
                options=['h264', 'h265', 'vp9', 'av1'],
                category='video',
                subcategory='advanced',
                restart_required=True
            ),
            'video.colorspace': SettingDefinition(
                key='video.colorspace',
                name='色彩空间',
                description='视频色彩空间',
                setting_type=SettingType.STRING,
                default_value='bt709',
                options=['bt709', 'bt2020', 'smpte240m'],
                category='video',
                subcategory='advanced'
            )
        })

        # 音频设置
        self.settings_definitions.update({
            'audio.sample_rate': SettingDefinition(
                key='audio.sample_rate',
                name='采样率',
                description='音频采样率',
                setting_type=SettingType.INTEGER,
                default_value=44100,
                options=[22050, 44100, 48000, 96000],
                category='audio',
                subcategory='basic'
            ),
            'audio.bitrate': SettingDefinition(
                key='audio.bitrate',
                name='音频比特率',
                description='音频编码比特率',
                setting_type=SettingType.STRING,
                default_value='192k',
                options=['128k', '192k', '256k', '320k'],
                category='audio',
                subcategory='basic'
            ),
            'audio.channels': SettingDefinition(
                key='audio.channels',
                name='声道数',
                description='音频声道数',
                setting_type=SettingType.INTEGER,
                default_value=2,
                min_value=1,
                max_value=8,
                category='audio',
                subcategory='basic'
            ),
            'audio.codec': SettingDefinition(
                key='audio.codec',
                name='音频编码器',
                description='音频编码器类型',
                setting_type=SettingType.STRING,
                default_value='aac',
                options=['aac', 'mp3', 'opus', 'flac'],
                category='audio',
                subcategory='advanced'
            )
        })

        # 自动保存设置
        self.settings_definitions.update({
            'auto_save.enabled': SettingDefinition(
                key='auto_save.enabled',
                name='启用自动保存',
                description='自动保存项目更改',
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category='auto_save',
                subcategory='basic'
            ),
            'auto_save.interval': SettingDefinition(
                key='auto_save.interval',
                name='自动保存间隔',
                description='自动保存的时间间隔（秒）',
                setting_type=SettingType.INTEGER,
                default_value=300,
                min_value=60,
                max_value=3600,
                category='auto_save',
                subcategory='basic'
            ),
            'auto_save.max_backups': SettingDefinition(
                key='auto_save.max_backups',
                name='最大备份数',
                description='保留的最大备份文件数',
                setting_type=SettingType.INTEGER,
                default_value=10,
                min_value=1,
                max_value=50,
                category='auto_save',
                subcategory='advanced'
            )
        })

        # AI设置
        self.settings_definitions.update({
            'ai.default_model': SettingDefinition(
                key='ai.default_model',
                name='默认AI模型',
                description='默认使用的AI模型',
                setting_type=SettingType.STRING,
                default_value='gpt-3.5-turbo',
                options=['gpt-5', 'gpt-5-mini', 'claude-opus-4-6', 'gemini-3-pro'],
                category='ai',
                subcategory='models'
            ),
            'ai.max_tokens': SettingDefinition(
                key='ai.max_tokens',
                name='最大令牌数',
                description='AI响应的最大令牌数',
                setting_type=SettingType.INTEGER,
                default_value=2000,
                min_value=100,
                max_value=8000,
                category='ai',
                subcategory='models'
            ),
            'ai.temperature': SettingDefinition(
                key='ai.temperature',
                name='创造性程度',
                description='AI响应的创造性程度',
                setting_type=SettingType.FLOAT,
                default_value=0.7,
                min_value=0.0,
                max_value=2.0,
                category='ai',
                subcategory='models'
            ),
            'ai.enable_cache': SettingDefinition(
                key='ai.enable_cache',
                name='启用AI缓存',
                description='缓存AI响应以提高性能',
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category='ai',
                subcategory='performance'
            )
        })

        # 界面设置
        self.settings_definitions.update({
            'ui.theme': SettingDefinition(
                key='ui.theme',
                name='主题',
                description='应用程序主题',
                setting_type=SettingType.STRING,
                default_value='dark',
                options=['light', 'dark', 'auto'],
                category='ui',
                subcategory='appearance',
                restart_required=True
            ),
            'ui.language': SettingDefinition(
                key='ui.language',
                name='语言',
                description='界面语言',
                setting_type=SettingType.STRING,
                default_value='zh-CN',
                options=['zh-CN', 'en-US', 'ja-JP', 'ko-KR'],
                category='ui',
                subcategory='appearance',
                restart_required=True
            ),
            'ui.font_size': SettingDefinition(
                key='ui.font_size',
                name='字体大小',
                description='界面字体大小',
                setting_type=SettingType.INTEGER,
                default_value=12,
                min_value=8,
                max_value=24,
                category='ui',
                subcategory='appearance'
            ),
            'ui.show_tips': SettingDefinition(
                key='ui.show_tips',
                name='显示提示',
                description='显示操作提示和教程',
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category='ui',
                subcategory='behavior'
            )
        })

        # 性能设置
        self.settings_definitions.update({
            'performance.enable_gpu': SettingDefinition(
                key='performance.enable_gpu',
                name='启用GPU加速',
                description='使用GPU进行视频处理',
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category='performance',
                subcategory='hardware'
            ),
            'performance.memory_limit': SettingDefinition(
                key='performance.memory_limit',
                name='内存限制',
                description='最大内存使用量（MB）',
                setting_type=SettingType.INTEGER,
                default_value=4096,
                min_value=1024,
                max_value=16384,
                category='performance',
                subcategory='hardware'
            ),
            'performance.thread_count': SettingDefinition(
                key='performance.thread_count',
                name='线程数',
                description='并行处理的线程数',
                setting_type=SettingType.INTEGER,
                default_value=4,
                min_value=1,
                max_value=16,
                category='performance',
                subcategory='processing'
            )
        })

        # 导出设置
        self.settings_definitions.update({
            'export.default_format': SettingDefinition(
                key='export.default_format',
                name='默认导出格式',
                description='默认的导出文件格式',
                setting_type=SettingType.STRING,
                default_value='mp4',
                options=['mp4', 'mov', 'avi', 'mkv', 'webm'],
                category='export',
                subcategory='format'
            ),
            'export.quality': SettingDefinition(
                key='export.quality',
                name='导出质量',
                description='导出视频的质量级别',
                setting_type=SettingType.STRING,
                default_value='high',
                options=['low', 'medium', 'high', 'ultra'],
                category='export',
                subcategory='quality'
            ),
            'export.metadata.enabled': SettingDefinition(
                key='export.metadata.enabled',
                name='包含元数据',
                description='导出时包含项目元数据',
                setting_type=SettingType.BOOLEAN,
                default_value=True,
                category='export',
                subcategory='metadata'
            )
        })

    def _load_settings(self) -> None:
        """加载设置"""
        try:
            # 首先设置默认值
            for key, definition in self.settings_definitions.items():
                self.settings[key] = definition.default_value

            # 从文件加载设置
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    self._update_settings(loaded_settings)

            self.logger.info("Project settings loaded successfully")

        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")

    def _load_profiles(self) -> None:
        """加载配置文件"""
        try:
            if os.path.exists(self.profiles_file):
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    profiles_data = json.load(f)
                    for name, profile_data in profiles_data.items():
                        profile = ProjectSettingsProfile(**profile_data)
                        self.profiles[name] = profile

            # 创建默认配置文件
            self._create_default_profiles()

            self.logger.info("Project profiles loaded successfully")

        except Exception as e:
            self.logger.error(f"Failed to load profiles: {e}")

    def _create_default_profiles(self) -> None:
        """创建默认配置文件"""
        default_profiles = [
            ProjectSettingsProfile(
                name="高性能",
                description="针对高性能设备的优化配置",
                settings={
                    'performance.enable_gpu': True,
                    'performance.memory_limit': 8192,
                    'performance.thread_count': 8,
                    'video.resolution': '3840x2160',
                    'video.bitrate': '16000k',
                    'audio.sample_rate': 48000,
                    'audio.bitrate': '320k'
                },
                created_at=datetime.now().isoformat(),
                modified_at=datetime.now().isoformat(),
                tags=['性能', '高质量'],
                is_builtin=True
            ),
            ProjectSettingsProfile(
                name="标准配置",
                description="平衡性能和质量的标准配置",
                settings={
                    'performance.enable_gpu': True,
                    'performance.memory_limit': 4096,
                    'performance.thread_count': 4,
                    'video.resolution': '1920x1080',
                    'video.bitrate': '8000k',
                    'audio.sample_rate': 44100,
                    'audio.bitrate': '192k'
                },
                created_at=datetime.now().isoformat(),
                modified_at=datetime.now().isoformat(),
                tags=['标准', '平衡'],
                is_builtin=True
            ),
            ProjectSettingsProfile(
                name="节省资源",
                description="针对低性能设备的优化配置",
                settings={
                    'performance.enable_gpu': False,
                    'performance.memory_limit': 2048,
                    'performance.thread_count': 2,
                    'video.resolution': '1280x720',
                    'video.bitrate': '4000k',
                    'audio.sample_rate': 44100,
                    'audio.bitrate': '128k'
                },
                created_at=datetime.now().isoformat(),
                modified_at=datetime.now().isoformat(),
                tags=['省资源', '兼容'],
                is_builtin=True
            )
        ]

        for profile in default_profiles:
            if profile.name not in self.profiles:
                self.profiles[profile.name] = profile

    def _update_settings(self, new_settings: Dict[str, Any]) -> None:
        """更新设置"""
        for key, value in new_settings.items():
            if key in self.settings_definitions:
                if self._validate_setting(key, value):
                    self.settings[key] = value
                else:
                    self.logger.warning(f"Invalid value for setting {key}: {value}")

    def _validate_setting(self, key: str, value: Any) -> bool:
        """验证设置值"""
        if key not in self.settings_definitions:
            return False

        definition = self.settings_definitions[key]

        # 类型检查
        try:
            if definition.setting_type == SettingType.STRING:
                if not isinstance(value, str):
                    return False
            elif definition.setting_type == SettingType.INTEGER:
                if not isinstance(value, int):
                    return False
            elif definition.setting_type == SettingType.FLOAT:
                if not isinstance(value, (int, float)):
                    return False
            elif definition.setting_type == SettingType.BOOLEAN:
                if not isinstance(value, bool):
                    return False
            elif definition.setting_type == SettingType.LIST:
                if not isinstance(value, list):
                    return False
            elif definition.setting_type == SettingType.DICT:
                if not isinstance(value, dict):
                    return False
        except Exception:
            return False

        # 范围检查
        if definition.min_value is not None:
            if value < definition.min_value:
                return False

        if definition.max_value is not None:
            if value > definition.max_value:
                return False

        # 选项检查
        if definition.options:
            if value not in definition.options:
                return False

        # 自定义验证
        if definition.validator:
            try:
                validator_func = getattr(self, definition.validator)
                if not validator_func(value):
                    return False
            except Exception:
                return False

        return True

    def get_setting(self, key: str, default: Any = None) -> Any:
        """获取设置值"""
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any) -> bool:
        """设置值"""
        if key not in self.settings_definitions:
            self.error_occurred.emit("SETTING_ERROR", f"未知的设置项: {key}")
            return False

        if not self._validate_setting(key, value):
            self.error_occurred.emit("SETTING_ERROR", f"无效的设置值: {value}")
            return False

        old_value = self.settings.get(key)
        if old_value != value:
            self.settings[key] = value
            self.settings_changed.emit(key, value)
            self._save_settings()

        return True

    def get_settings_by_category(self, category: str) -> Dict[str, Any]:
        """按类别获取设置"""
        category_settings = {}
        for key, definition in self.settings_definitions.items():
            if definition.category == category:
                category_settings[key] = {
                    'value': self.settings.get(key, definition.default_value),
                    'definition': definition
                }
        return category_settings

    def get_all_settings(self) -> Dict[str, Any]:
        """获取所有设置"""
        return self.settings.copy()

    def reset_settings(self) -> None:
        """重置设置为默认值"""
        for key, definition in self.settings_definitions.items():
            self.settings[key] = definition.default_value

        self._save_settings()
        self.settings_reset.emit()
        self.logger.info("Settings reset to defaults")

    def reset_setting(self, key: str) -> bool:
        """重置单个设置为默认值"""
        if key not in self.settings_definitions:
            return False

        default_value = self.settings_definitions[key].default_value
        return self.set_setting(key, default_value)

    def _save_settings(self) -> None:
        """保存设置"""
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")

    def create_profile(self, name: str, description: str,
                     settings_filter: List[str] = None) -> bool:
        """创建配置文件"""
        try:
            if name in self.profiles and not self.profiles[name].is_builtin:
                self.error_occurred.emit("PROFILE_ERROR", f"配置文件已存在: {name}")
                return False

            # 确定要包含的设置
            if settings_filter:
                profile_settings = {k: v for k, v in self.settings.items() if k in settings_filter}
            else:
                profile_settings = self.settings.copy()

            profile = ProjectSettingsProfile(
                name=name,
                description=description,
                settings=profile_settings,
                created_at=datetime.now().isoformat(),
                modified_at=datetime.now().isoformat()
            )

            self.profiles[name] = profile
            self._save_profiles()

            self.profile_created.emit(name)
            self.logger.info(f"Created profile: {name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create profile {name}: {e}")
            return False

    def apply_profile(self, profile_name: str) -> bool:
        """应用配置文件"""
        try:
            if profile_name not in self.profiles:
                self.error_occurred.emit("PROFILE_ERROR", f"配置文件不存在: {profile_name}")
                return False

            profile = self.profiles[profile_name]
            changes_made = []

            for key, value in profile.settings.items():
                if key in self.settings_definitions:
                    if self._validate_setting(key, value):
                        old_value = self.settings.get(key)
                        if old_value != value:
                            self.settings[key] = value
                            changes_made.append((key, old_value, value))

            if changes_made:
                self._save_settings()
                for key, old_value, new_value in changes_made:
                    self.settings_changed.emit(key, new_value)

            self.profile_applied.emit(profile_name)
            self.logger.info(f"Applied profile: {profile_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to apply profile {profile_name}: {e}")
            return False

    def delete_profile(self, profile_name: str) -> bool:
        """删除配置文件"""
        try:
            if profile_name not in self.profiles:
                return False

            profile = self.profiles[profile_name]

            # 不能删除内置配置文件
            if profile.is_builtin:
                self.error_occurred.emit("PROFILE_ERROR", "不能删除内置配置文件")
                return False

            del self.profiles[profile_name]
            self._save_profiles()

            self.logger.info(f"Deleted profile: {profile_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete profile {profile_name}: {e}")
            return False

    def get_profile(self, profile_name: str) -> Optional[ProjectSettingsProfile]:
        """获取配置文件"""
        return self.profiles.get(profile_name)

    def get_all_profiles(self) -> List[ProjectSettingsProfile]:
        """获取所有配置文件"""
        return list(self.profiles.values())

    def get_builtin_profiles(self) -> List[ProjectSettingsProfile]:
        """获取内置配置文件"""
        return [p for p in self.profiles.values() if p.is_builtin]

    def _save_profiles(self) -> None:
        """保存配置文件"""
        try:
            os.makedirs(os.path.dirname(self.profiles_file), exist_ok=True)
            profiles_data = {name: asdict(profile) for name, profile in self.profiles.items()}
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(profiles_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save profiles: {e}")

    def export_settings(self, export_path: str, profile_name: str = None) -> bool:
        """导出设置"""
        try:
            if profile_name:
                if profile_name not in self.profiles:
                    return False
                settings_to_export = self.profiles[profile_name].settings
            else:
                settings_to_export = self.settings

            export_data = {
                'settings': settings_to_export,
                'exported_at': datetime.now().isoformat(),
                'cineai_version': '2.0.0',
                'profile_name': profile_name
            }

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Exported settings to {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export settings: {e}")
            return False

    def import_settings(self, import_path: str, merge: bool = True) -> bool:
        """导入设置"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            imported_settings = import_data.get('settings', {})

            if merge:
                # 合并设置
                for key, value in imported_settings.items():
                    if key in self.settings_definitions:
                        self.set_setting(key, value)
            else:
                # 替换设置
                self._update_settings(imported_settings)
                self._save_settings()

            self.logger.info(f"Imported settings from {import_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to import settings: {e}")
            return False

    def get_setting_definition(self, key: str) -> Optional[SettingDefinition]:
        """获取设置定义"""
        return self.settings_definitions.get(key)

    def get_all_setting_definitions(self) -> Dict[str, SettingDefinition]:
        """获取所有设置定义"""
        return self.settings_definitions.copy()

    def get_categories(self) -> List[str]:
        """获取所有设置类别"""
        categories = set()
        for definition in self.settings_definitions.values():
            categories.add(definition.category)
        return sorted(list(categories))

    def search_settings(self, query: str) -> List[Dict[str, Any]]:
        """搜索设置"""
        results = []
        query_lower = query.lower()

        for key, definition in self.settings_definitions.items():
            if (query_lower in definition.name.lower() or
                query_lower in definition.description.lower() or
                query_lower in key.lower()):
                results.append({
                    'key': key,
                    'value': self.settings.get(key, definition.default_value),
                    'definition': definition
                })

        return results

    def validate_settings(self) -> Dict[str, List[str]]:
        """验证所有设置"""
        validation_result = {}

        for key, value in self.settings.items():
            if key in self.settings_definitions:
                if not self._validate_setting(key, value):
                    validation_result[key] = [f"Invalid value: {value}"]
            else:
                validation_result[key] = ["Unknown setting"]

        return validation_result

    def get_settings_summary(self) -> Dict[str, Any]:
        """获取设置摘要"""
        try:
            # 按类别统计设置
            category_stats = {}
            for definition in self.settings_definitions.values():
                category = definition.category
                if category not in category_stats:
                    category_stats[category] = {
                        'total': 0,
                        'advanced': 0,
                        'modified': 0
                    }
                category_stats[category]['total'] += 1
                if definition.advanced:
                    category_stats[category]['advanced'] += 1

            # 统计修改的设置
            for key, value in self.settings.items():
                if key in self.settings_definitions:
                    definition = self.settings_definitions[key]
                    if value != definition.default_value:
                        category_stats[definition.category]['modified'] += 1

            return {
                'total_settings': len(self.settings_definitions),
                'modified_settings': sum(1 for k, v in self.settings.items()
                                       if k in self.settings_definitions and
                                       v != self.settings_definitions[k].default_value),
                'category_stats': category_stats,
                'profiles_count': len(self.profiles),
                'builtin_profiles_count': len([p for p in self.profiles.values() if p.is_builtin])
            }

        except Exception as e:
            self.logger.error(f"Failed to get settings summary: {e}")
            return {}

    # 自定义验证器
    def _validate_resolution(self, value: str) -> bool:
        """验证分辨率格式"""
        try:
            parts = value.split('x')
            if len(parts) != 2:
                return False
            width, height = int(parts[0]), int(parts[1])
            return width > 0 and height > 0
        except ValueError:
            return False

    def _validate_path(self, value: str) -> bool:
        """验证路径"""
        try:
            path = Path(value)
            return path.exists() or path.parent.exists()
        except Exception:
            return False

    def _validate_color(self, value: str) -> bool:
        """验证颜色格式"""
        try:
            # 支持十六进制颜色格式
            if value.startswith('#'):
                return len(value) in [4, 7, 9]  # #RGB, #RRGGBB, #RRGGBBAA
            # 支持RGB/RGBA格式
            return value in ['red', 'green', 'blue', 'white', 'black', 'transparent']
        except Exception:
            return False