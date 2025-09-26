#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
导出预设优化器
智能导出预设管理和优化系统
"""

import os
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path
import hashlib

from .export_system import ExportPreset, ExportFormat, ExportQuality
from .enhanced_export_formats import EnhancedExportFormat, EnhancedExportPresets, FormatSpecification
from ..core.logger import Logger


class PresetCategory(Enum):
    """预设类别"""
    SOCIAL_MEDIA = "social_media"      # 社交媒体
    BROADCAST = "broadcast"            # 广播
    CINEMA = "cinema"                 # 影院
    WEB = "web"                       # 网络媒体
    MOBILE = "mobile"                 # 移动设备
    ARCHIVE = "archive"               # 归档存储
    STREAMING = "streaming"           # 流媒体
    PROFESSIONAL = "professional"     # 专业制作
    CUSTOM = "custom"                 # 自定义


@dataclass
class PresetUsageStats:
    """预设使用统计"""
    usage_count: int = 0
    last_used: float = 0.0
    success_rate: float = 100.0
    average_export_time: float = 0.0
    user_rating: float = 5.0
    feedback: List[str] = field(default_factory=list)


@dataclass
class PresetPerformance:
    """预设性能指标"""
    quality_score: float = 0.0      # 质量评分 (0-100)
    speed_score: float = 0.0        # 速度评分 (0-100)
    efficiency_score: float = 0.0   # 效率评分 (0-100)
    compatibility_score: float = 0.0  # 兼容性评分 (0-100)
    overall_score: float = 0.0      # 总体评分 (0-100)


@dataclass
class SmartPreset:
    """智能预设"""
    base_preset: ExportPreset
    category: PresetCategory
    usage_stats: PresetUsageStats
    performance: PresetPerformance
    auto_optimize: bool = True
    smart_adaptations: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    description: str = ""
    version: str = "1.0"


class PresetOptimizer:
    """预设优化器"""

    def __init__(self):
        self.logger = Logger(__name__)
        self.presets: Dict[str, SmartPreset] = {}
        self.learning_data: Dict[str, Any] = {}
        self.user_preferences: Dict[str, Any] = {}
        self.format_specs = EnhancedExportPresets.get_format_specifications()

        # 初始化预设
        self._initialize_default_presets()
        self._load_user_data()

    def _initialize_default_presets(self):
        """初始化默认预设"""
        default_presets = [
            # 社交媒体类别
            SmartPreset(
                base_preset=ExportPreset(
                    id="instagram_reel",
                    name="Instagram Reel",
                    format=ExportFormat.MP4_H264,
                    quality=ExportQuality.MEDIUM,
                    resolution=(1080, 1920),
                    bitrate=4000,
                    fps=30,
                    audio_bitrate=128
                ),
                category=PresetCategory.SOCIAL_MEDIA,
                usage_stats=PresetUsageStats(),
                performance=PresetPerformance(
                    quality_score=85,
                    speed_score=90,
                    efficiency_score=88,
                    compatibility_score=95,
                    overall_score=90
                ),
                tags=["instagram", "reel", "vertical", "social"],
                description="优化的Instagram Reel格式，1080x1920竖版视频"
            ),

            SmartPreset(
                base_preset=ExportPreset(
                    id="tiktok_video",
                    name="TikTok Video",
                    format=ExportFormat.MP4_H264,
                    quality=ExportQuality.MEDIUM,
                    resolution=(1080, 1920),
                    bitrate=3000,
                    fps=30,
                    audio_bitrate=128
                ),
                category=PresetCategory.SOCIAL_MEDIA,
                usage_stats=PresetUsageStats(),
                performance=PresetPerformance(
                    quality_score=80,
                    speed_score=95,
                    efficiency_score=92,
                    compatibility_score=90,
                    overall_score=89
                ),
                tags=["tiktok", "vertical", "short", "social"],
                description="适用于TikTok的竖版视频格式"
            ),

            # 广播类别
            SmartPreset(
                base_preset=ExportPreset(
                    id="broadcast_1080p",
                    name="广播1080p",
                    format=ExportFormat.MOV_PRORES,
                    quality=ExportQuality.HIGH,
                    resolution=(1920, 1080),
                    bitrate=22000,
                    fps=29.97,
                    audio_bitrate=320
                ),
                category=PresetCategory.BROADCAST,
                usage_stats=PresetUsageStats(),
                performance=PresetPerformance(
                    quality_score=95,
                    speed_score=70,
                    efficiency_score=75,
                    compatibility_score=85,
                    overall_score=81
                ),
                tags=["broadcast", "1080p", "professional", "tv"],
                description="适用于电视广播的高质量1080p格式"
            ),

            # Web媒体类别
            SmartPreset(
                base_preset=ExportPreset(
                    id="web_streaming",
                    name="Web流媒体",
                    format=ExportFormat.WEBM_VP9,
                    quality=ExportQuality.HIGH,
                    resolution=(1920, 1080),
                    bitrate=6000,
                    fps=30,
                    audio_bitrate=128
                ),
                category=PresetCategory.WEB,
                usage_stats=PresetUsageStats(),
                performance=PresetPerformance(
                    quality_score=85,
                    speed_score=85,
                    efficiency_score=90,
                    compatibility_score=80,
                    overall_score=85
                ),
                tags=["web", "streaming", "vp9", "online"],
                description="适用于Web播放的流媒体优化格式"
            ),

            # 专业制作类别
            SmartPreset(
                base_preset=ExportPreset(
                    id="cinema_4k",
                    name="影院4K",
                    format=ExportFormat.MOV_PRORES,
                    quality=ExportQuality.ULTRA,
                    resolution=(3840, 2160),
                    bitrate=50000,
                    fps=24,
                    audio_bitrate=320
                ),
                category=PresetCategory.CINEMA,
                usage_stats=PresetUsageStats(),
                performance=PresetPerformance(
                    quality_score=98,
                    speed_score=60,
                    efficiency_score=65,
                    compatibility_score=75,
                    overall_score=75
                ),
                tags=["cinema", "4k", "professional", "film"],
                description="适用于影院放映的4K高质量格式"
            )
        ]

        for preset in default_presets:
            self.presets[preset.base_preset.id] = preset

        self.logger.info(f"Initialized {len(self.presets)} default smart presets")

    def get_recommended_presets(self,
                               source_info: Dict[str, Any],
                               target_platform: Optional[str] = None,
                               user_preferences: Optional[Dict[str, Any]] = None) -> List[SmartPreset]:
        """获取推荐预设"""
        recommendations = []

        # 分析源信息
        source_analysis = self._analyze_source(source_info)

        # 基于平台推荐
        if target_platform:
            platform_presets = self._get_platform_presets(target_platform)
            recommendations.extend(platform_presets)

        # 基于内容类型推荐
        content_presets = self._get_content_based_presets(source_analysis)
        recommendations.extend(content_presets)

        # 基于用户偏好推荐
        if user_preferences:
            preference_presets = self._get_preference_based_presets(user_preferences)
            recommendations.extend(preference_presets)

        # 去重并排序
        unique_presets = list({preset.base_preset.id: preset for preset in recommendations}.values())
        sorted_presets = sorted(unique_presets,
                               key=lambda x: self._calculate_recommendation_score(x, source_analysis),
                               reverse=True)

        return sorted_presets[:5]  # 返回前5个推荐

    def optimize_preset(self,
                       preset: SmartPreset,
                       source_info: Dict[str, Any],
                       constraints: Optional[Dict[str, Any]] = None) -> SmartPreset:
        """优化预设"""
        if not preset.auto_optimize:
            return preset

        optimized_preset = self._create_copy(preset)

        # 应用智能优化
        optimizations = self._generate_optimizations(optimized_preset, source_info, constraints)

        for optimization in optimizations:
            self._apply_optimization(optimized_preset, optimization)

        # 更新性能评分
        optimized_preset.performance = self._evaluate_performance(optimized_preset, source_info)

        return optimized_preset

    def adapt_preset_for_device(self,
                                preset: SmartPreset,
                                device_info: Dict[str, Any]) -> SmartPreset:
        """为特定设备适配预设"""
        adapted_preset = self._create_copy(preset)

        # 基于设备信息调整参数
        if device_info.get("screen_size"):
            # 根据屏幕大小调整分辨率
            screen_size = device_info["screen_size"]
            if screen_size < 6:  # 小屏幕设备
                adapted_preset.base_preset.resolution = (1280, 720)
                adapted_preset.base_preset.bitrate = max(2000, adapted_preset.base_preset.bitrate // 2)

        if device_info.get("network_type"):
            # 根据网络类型调整比特率
            network_type = device_info["network_type"]
            if network_type == "mobile":
                adapted_preset.base_preset.bitrate = max(1000, adapted_preset.base_preset.bitrate // 3)
            elif network_type == "wifi":
                adapted_preset.base_preset.bitrate = max(2000, adapted_preset.base_preset.bitrate // 2)

        # 记录适配信息
        adapted_preset.smart_adaptations["device_adaptation"] = {
            "device_info": device_info,
            "adaptation_time": time.time()
        }

        return adapted_preset

    def create_custom_preset(self,
                           name: str,
                           base_preset_id: str,
                           customizations: Dict[str, Any],
                           category: PresetCategory = PresetCategory.CUSTOM) -> SmartPreset:
        """创建自定义预设"""
        if base_preset_id not in self.presets:
            raise ValueError(f"Base preset not found: {base_preset_id}")

        base_preset = self.presets[base_preset_id]
        custom_preset = self._create_copy(base_preset)

        # 应用自定义设置
        custom_preset.base_preset.name = name
        custom_preset.base_preset.id = f"custom_{int(time.time() * 1000)}"
        custom_preset.category = category

        # 应用自定义参数
        for key, value in customizations.items():
            if hasattr(custom_preset.base_preset, key):
                setattr(custom_preset.base_preset, key, value)

        # 设置自定义标签
        custom_preset.tags.extend(customizations.get("tags", []))
        custom_preset.description = customizations.get("description", "")

        # 添加到预设库
        self.presets[custom_preset.base_preset.id] = custom_preset

        # 保存到用户数据
        self._save_user_data()

        return custom_preset

    def update_preset_usage(self, preset_id: str, usage_data: Dict[str, Any]):
        """更新预设使用统计"""
        if preset_id not in self.presets:
            return

        preset = self.presets[preset_id]
        stats = preset.usage_stats

        # 更新使用统计
        stats.usage_count += 1
        stats.last_used = time.time()

        if usage_data.get("success", True):
            # 更新成功率
            total_uses = stats.usage_count
            successful_uses = total_uses - len([f for f in stats.feedback if "failed" in f.lower()])
            stats.success_rate = (successful_uses / total_uses) * 100

            # 更新平均导出时间
            export_time = usage_data.get("export_time", 0)
            if export_time > 0:
                if stats.average_export_time == 0:
                    stats.average_export_time = export_time
                else:
                    stats.average_export_time = (stats.average_export_time * 0.9 + export_time * 0.1)

        # 添加用户反馈
        if "feedback" in usage_data:
            stats.feedback.append(usage_data["feedback"])

        # 更新用户评分
        if "rating" in usage_data:
            stats.user_rating = usage_data["rating"]

        # 学习用户偏好
        self._learn_user_preference(preset_id, usage_data)

        # 保存数据
        self._save_user_data()

    def get_preset_insights(self, preset_id: str) -> Dict[str, Any]:
        """获取预设洞察信息"""
        if preset_id not in self.presets:
            return {}

        preset = self.presets[preset_id]
        insights = {
            "preset_info": {
                "name": preset.base_preset.name,
                "category": preset.category.value,
                "usage_count": preset.usage_stats.usage_count,
                "success_rate": preset.usage_stats.success_rate,
                "user_rating": preset.usage_stats.user_rating
            },
            "performance": {
                "quality_score": preset.performance.quality_score,
                "speed_score": preset.performance.speed_score,
                "efficiency_score": preset.performance.efficiency_score,
                "compatibility_score": preset.performance.compatibility_score,
                "overall_score": preset.performance.overall_score
            },
            "usage_trends": self._analyze_usage_trends(preset_id),
            "optimization_suggestions": self._generate_optimization_suggestions(preset)
        }

        return insights

    def get_presets_by_category(self, category: PresetCategory) -> List[SmartPreset]:
        """按类别获取预设"""
        return [preset for preset in self.presets.values() if preset.category == category]

    def search_presets(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[SmartPreset]:
        """搜索预设"""
        results = []

        for preset in self.presets.values():
            # 检查搜索词匹配
            if self._matches_search_query(preset, query):
                # 应用过滤器
                if self._passes_filters(preset, filters or {}):
                    results.append(preset)

        # 按相关性排序
        results.sort(key=lambda x: self._calculate_search_relevance(x, query), reverse=True)

        return results

    def _analyze_source(self, source_info: Dict[str, Any]) -> Dict[str, Any]:
        """分析源信息"""
        analysis = {
            "resolution": source_info.get("resolution", (1920, 1080)),
            "duration": source_info.get("duration", 0),
            "bitrate": source_info.get("bitrate", 0),
            "fps": source_info.get("fps", 30),
            "audio_channels": source_info.get("audio_channels", 2),
            "content_type": source_info.get("content_type", "general"),
            "has_hdr": source_info.get("has_hdr", False),
            "file_size": source_info.get("file_size", 0)
        }

        # 添加分析结果
        analysis["quality_level"] = self._assess_quality_level(analysis)
        analysis["complexity"] = self._assess_complexity(analysis)

        return analysis

    def _assess_quality_level(self, analysis: Dict[str, Any]) -> str:
        """评估质量水平"""
        width, height = analysis["resolution"]
        bitrate = analysis["bitrate"]

        if width >= 3840 and height >= 2160:
            return "4k"
        elif width >= 1920 and height >= 1080:
            return "1080p"
        elif width >= 1280 and height >= 720:
            return "720p"
        else:
            return "sd"

    def _assess_complexity(self, analysis: Dict[str, Any]) -> str:
        """评估复杂度"""
        duration = analysis["duration"]
        fps = analysis["fps"]

        if duration > 600 and fps > 30:
            return "high"
        elif duration > 300 or fps > 30:
            return "medium"
        else:
            return "low"

    def _get_platform_presets(self, platform: str) -> List[SmartPreset]:
        """获取平台特定预设"""
        platform_mapping = {
            "youtube": ["youtube_1080p", "youtube_4k"],
            "instagram": ["instagram_reel", "instagram_post"],
            "tiktok": ["tiktok_video"],
            "vimeo": ["vimeo_1080p", "vimeo_4k"],
            "facebook": ["facebook_video", "facebook_story"]
        }

        preset_ids = platform_mapping.get(platform.lower(), [])
        return [self.presets[pid] for pid in preset_ids if pid in self.presets]

    def _get_content_based_presets(self, source_analysis: Dict[str, Any]) -> List[SmartPreset]:
        """基于内容类型获取预设"""
        content_type = source_analysis["content_type"]
        quality_level = source_analysis["quality_level"]

        content_mapping = {
            "screen_recording": ["web_streaming", "screen_recording_optimized"],
            "animation": ["animation_high_quality", "web_streaming"],
            "film": ["cinema_4k", "broadcast_1080p"],
            "music_video": ["music_video_1080p", "social_media_high_quality"],
            "general": ["web_streaming", "social_media_high_quality"]
        }

        preset_ids = content_mapping.get(content_type, ["web_streaming"])
        return [self.presets[pid] for pid in preset_ids if pid in self.presets]

    def _get_preference_based_presets(self, preferences: Dict[str, Any]) -> List[SmartPreset]:
        """基于用户偏好获取预设"""
        preferred_categories = preferences.get("preferred_categories", [])
        preferred_formats = preferences.get("preferred_formats", [])

        results = []
        for preset in self.presets.values():
            if preset.category.value in preferred_categories:
                results.append(preset)
            elif any(fmt in preset.tags for fmt in preferred_formats):
                results.append(preset)

        return results

    def _calculate_recommendation_score(self, preset: SmartPreset, source_analysis: Dict[str, Any]) -> float:
        """计算推荐分数"""
        score = 0.0

        # 基于性能评分
        score += preset.performance.overall_score * 0.3

        # 基于使用统计
        if preset.usage_stats.usage_count > 0:
            usage_weight = min(preset.usage_stats.usage_count / 10, 1.0) * 0.2
            score += usage_weight * 100

        # 基于用户评分
        score += preset.usage_stats.user_rating * 10 * 0.2

        # 基于内容匹配度
        content_match = self._calculate_content_match(preset, source_analysis)
        score += content_match * 30

        # 基于成功率
        score += preset.usage_stats.success_rate * 0.3

        return min(score, 100.0)

    def _calculate_content_match(self, preset: SmartPreset, source_analysis: Dict[str, Any]) -> float:
        """计算内容匹配度"""
        match_score = 0.0

        # 分辨率匹配
        source_width, source_height = source_analysis["resolution"]
        preset_width, preset_height = preset.base_preset.resolution

        if preset_width > 0 and preset_height > 0:
            resolution_ratio = min(preset_width / source_width, preset_height / source_height)
            if 0.8 <= resolution_ratio <= 1.2:
                match_score += 30
            elif 0.5 <= resolution_ratio <= 2.0:
                match_score += 15

        # 质量匹配
        source_quality = source_analysis["quality_level"]
        preset_quality_map = {
            "4k": ExportQuality.ULTRA,
            "1080p": ExportQuality.HIGH,
            "720p": ExportQuality.MEDIUM,
            "sd": ExportQuality.LOW
        }

        expected_quality = preset_quality_map.get(source_quality, ExportQuality.MEDIUM)
        if preset.base_preset.quality == expected_quality:
            match_score += 20

        return match_score

    def _generate_optimizations(self,
                               preset: SmartPreset,
                               source_info: Dict[str, Any],
                               constraints: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """生成优化建议"""
        optimizations = []

        # 基于源内容的优化
        source_analysis = self._analyze_source(source_info)

        # 分辨率优化
        if source_analysis["resolution"] != preset.base_preset.resolution:
            optimizations.append({
                "type": "resolution",
                "value": self._optimize_resolution(source_analysis, constraints),
                "reason": "Optimized for source content"
            })

        # 比特率优化
        optimizations.append({
            "type": "bitrate",
            "value": self._optimize_bitrate(preset, source_analysis, constraints),
            "reason": "Optimized bitrate for quality and file size"
        })

        # 编码参数优化
        optimizations.append({
            "type": "codec_params",
            "value": self._optimize_codec_params(preset, source_analysis),
            "reason": "Optimized encoding parameters"
        })

        return optimizations

    def _optimize_resolution(self, source_analysis: Dict[str, Any],
                            constraints: Optional[Dict[str, Any]]) -> Tuple[int, int]:
        """优化分辨率"""
        source_width, source_height = source_analysis["resolution"]

        # 保持宽高比
        aspect_ratio = source_width / source_height

        # 根据约束调整
        if constraints and "max_resolution" in constraints:
            max_width, max_height = constraints["max_resolution"]
            if source_width > max_width or source_height > max_height:
                if source_width / max_width > source_height / max_height:
                    return (max_width, int(max_width / aspect_ratio))
                else:
                    return (int(max_height * aspect_ratio), max_height)

        # 默认保持源分辨率
        return (source_width, source_height)

    def _optimize_bitrate(self, preset: SmartPreset,
                          source_analysis: Dict[str, Any],
                          constraints: Optional[Dict[str, Any]]) -> int:
        """优化比特率"""
        base_bitrate = preset.base_preset.bitrate

        # 基于内容复杂度调整
        complexity = source_analysis["complexity"]
        if complexity == "high":
            base_bitrate = int(base_bitrate * 1.2)
        elif complexity == "low":
            base_bitrate = int(base_bitrate * 0.8)

        # 基于分辨率调整
        source_width, source_height = source_analysis["resolution"]
        total_pixels = source_width * source_height
        if total_pixels > 1920 * 1080:
            base_bitrate = int(base_bitrate * 1.5)

        # 应用约束
        if constraints:
            if "max_bitrate" in constraints:
                base_bitrate = min(base_bitrate, constraints["max_bitrate"])
            if "min_bitrate" in constraints:
                base_bitrate = max(base_bitrate, constraints["min_bitrate"])

        return base_bitrate

    def _optimize_codec_params(self, preset: SmartPreset,
                               source_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """优化编码参数"""
        params = preset.base_preset.codec_params.copy()

        # 基于内容类型优化
        content_type = source_analysis["content_type"]
        if content_type == "screen_recording":
            params.update({
                "tune": "animation",
                "preset": "slow"
            })
        elif content_type == "film":
            params.update({
                "tune": "film",
                "preset": "medium"
            })

        # 基于HDR优化
        if source_analysis["has_hdr"]:
            params.update({
                "pix_fmt": "yuv420p10le",
                "colorspace": "bt2020",
                "color_primaries": "bt2020",
                "color_trc": "smpte2084"
            })

        return params

    def _apply_optimization(self, preset: SmartPreset, optimization: Dict[str, Any]):
        """应用优化"""
        opt_type = optimization["type"]
        value = optimization["value"]

        if opt_type == "resolution":
            preset.base_preset.resolution = value
        elif opt_type == "bitrate":
            preset.base_preset.bitrate = value
        elif opt_type == "codec_params":
            preset.base_preset.codec_params.update(value)

        # 记录优化历史
        if "optimization_history" not in preset.smart_adaptations:
            preset.smart_adaptations["optimization_history"] = []

        preset.smart_adaptations["optimization_history"].append({
            "type": opt_type,
            "value": value,
            "reason": optimization.get("reason", ""),
            "timestamp": time.time()
        })

    def _evaluate_performance(self, preset: SmartPreset, source_info: Dict[str, Any]) -> PresetPerformance:
        """评估预设性能"""
        performance = PresetPerformance()

        # 质量评分
        quality_score = self._calculate_quality_score(preset, source_info)
        performance.quality_score = quality_score

        # 速度评分
        speed_score = self._calculate_speed_score(preset, source_info)
        performance.speed_score = speed_score

        # 效率评分
        efficiency_score = self._calculate_efficiency_score(preset, source_info)
        performance.efficiency_score = efficiency_score

        # 兼容性评分
        compatibility_score = self._calculate_compatibility_score(preset)
        performance.compatibility_score = compatibility_score

        # 总体评分
        performance.overall_score = (
            quality_score * 0.4 +
            speed_score * 0.3 +
            efficiency_score * 0.2 +
            compatibility_score * 0.1
        )

        return performance

    def _calculate_quality_score(self, preset: SmartPreset, source_info: Dict[str, Any]) -> float:
        """计算质量评分"""
        score = 50.0  # 基础分数

        # 分辨率评分
        width, height = preset.base_preset.resolution
        if width >= 3840 and height >= 2160:
            score += 30
        elif width >= 1920 and height >= 1080:
            score += 20
        elif width >= 1280 and height >= 720:
            score += 10

        # 比特率评分
        bitrate = preset.base_preset.bitrate
        if bitrate > 10000:
            score += 20
        elif bitrate > 5000:
            score += 15
        elif bitrate > 2000:
            score += 10

        # 编码器评分
        format_type = preset.base_preset.format
        if format_type in [ExportFormat.MOV_PRORES]:
            score += 20
        elif format_type in [ExportFormat.MP4_H265]:
            score += 15

        return min(score, 100.0)

    def _calculate_speed_score(self, preset: SmartPreset, source_info: Dict[str, Any]) -> float:
        """计算速度评分"""
        score = 80.0  # 基础分数

        # 基于格式调整
        format_type = preset.base_preset.format
        if format_type in [ExportFormat.MOV_PRORES]:
            score -= 20  # ProRes编码较慢
        elif format_type in [ExportFormat.MP4_H264]:
            score += 10  # H.264编码较快

        # 基于比特率调整
        bitrate = preset.base_preset.bitrate
        if bitrate > 20000:
            score -= 15
        elif bitrate < 5000:
            score += 10

        return max(score, 0.0)

    def _calculate_efficiency_score(self, preset: SmartPreset, source_info: Dict[str, Any]) -> float:
        """计算效率评分"""
        quality_score = self._calculate_quality_score(preset, source_info)
        speed_score = self._calculate_speed_score(preset, source_info)

        # 效率是质量和速度的平衡
        return (quality_score + speed_score) / 2

    def _calculate_compatibility_score(self, preset: SmartPreset) -> float:
        """计算兼容性评分"""
        score = 70.0  # 基础分数

        format_type = preset.base_preset.format
        if format_type in [ExportFormat.MP4_H264, ExportFormat.MP4_H265]:
            score += 25  # MP4格式兼容性最好
        elif format_type in [ExportFormat.WEBM_VP9]:
            score += 15  # WebM兼容性良好
        elif format_type in [ExportFormat.MOV_PRORES]:
            score += 5   # ProRes兼容性较差

        return min(score, 100.0)

    def _create_copy(self, preset: SmartPreset) -> SmartPreset:
        """创建预设副本"""
        import copy

        # 创建基础预设的深拷贝
        new_base_preset = ExportPreset(
            id=preset.base_preset.id + "_copy",
            name=preset.base_preset.name + " (Copy)",
            format=preset.base_preset.format,
            quality=preset.base_preset.quality,
            resolution=preset.base_preset.resolution,
            bitrate=preset.base_preset.bitrate,
            fps=preset.base_preset.fps,
            audio_bitrate=preset.base_preset.audio_bitrate,
            codec_params=preset.base_preset.codec_params.copy(),
            description=preset.base_preset.description
        )

        # 创建智能预设
        new_preset = SmartPreset(
            base_preset=new_base_preset,
            category=preset.category,
            usage_stats=copy.deepcopy(preset.usage_stats),
            performance=copy.deepcopy(preset.performance),
            auto_optimize=preset.auto_optimize,
            smart_adaptations=copy.deepcopy(preset.smart_adaptations),
            tags=preset.tags.copy(),
            description=preset.description,
            version=preset.version
        )

        return new_preset

    def _matches_search_query(self, preset: SmartPreset, query: str) -> bool:
        """检查是否匹配搜索查询"""
        query_lower = query.lower()

        # 检查名称
        if query_lower in preset.base_preset.name.lower():
            return True

        # 检查描述
        if query_lower in preset.description.lower():
            return True

        # 检查标签
        if any(query_lower in tag.lower() for tag in preset.tags):
            return True

        # 检查类别
        if query_lower in preset.category.value:
            return True

        return False

    def _passes_filters(self, preset: SmartPreset, filters: Dict[str, Any]) -> bool:
        """检查是否通过过滤器"""
        # 类别过滤器
        if "category" in filters:
            if preset.category != filters["category"]:
                return False

        # 格式过滤器
        if "format" in filters:
            if preset.base_preset.format != filters["format"]:
                return False

        # 质量过滤器
        if "min_quality" in filters:
            min_quality = filters["min_quality"]
            quality_order = [ExportQuality.LOW, ExportQuality.MEDIUM, ExportQuality.HIGH, ExportQuality.ULTRA]
            preset_quality_index = quality_order.index(preset.base_preset.quality)
            min_quality_index = quality_order.index(min_quality)
            if preset_quality_index < min_quality_index:
                return False

        return True

    def _calculate_search_relevance(self, preset: SmartPreset, query: str) -> float:
        """计算搜索相关性"""
        relevance = 0.0
        query_lower = query.lower()

        # 名称匹配权重最高
        if query_lower in preset.base_preset.name.lower():
            relevance += 50

        # 描述匹配
        if query_lower in preset.description.lower():
            relevance += 30

        # 标签匹配
        for tag in preset.tags:
            if query_lower in tag.lower():
                relevance += 20

        # 使用频率加分
        if preset.usage_stats.usage_count > 0:
            relevance += min(preset.usage_stats.usage_count, 10)

        return relevance

    def _analyze_usage_trends(self, preset_id: str) -> Dict[str, Any]:
        """分析使用趋势"""
        preset = self.presets[preset_id]

        return {
            "usage_frequency": preset.usage_stats.usage_count,
            "last_used_ago": time.time() - preset.usage_stats.last_used if preset.usage_stats.last_used > 0 else 0,
            "success_rate": preset.usage_stats.success_rate,
            "average_export_time": preset.usage_stats.average_export_time,
            "user_satisfaction": preset.usage_stats.user_rating
        }

    def _generate_optimization_suggestions(self, preset: SmartPreset) -> List[str]:
        """生成优化建议"""
        suggestions = []

        # 基于性能评分生成建议
        if preset.performance.quality_score < 80:
            suggestions.append("考虑提高比特率或使用更高质量的编码器")

        if preset.performance.speed_score < 70:
            suggestions.append("考虑使用硬件加速或优化编码参数")

        if preset.performance.efficiency_score < 70:
            suggestions.append("调整质量和速度的平衡以获得更好的效率")

        if preset.performance.compatibility_score < 80:
            suggestions.append("考虑使用更通用的格式以提高兼容性")

        return suggestions

    def _learn_user_preference(self, preset_id: str, usage_data: Dict[str, Any]):
        """学习用户偏好"""
        if preset_id not in self.presets:
            return

        preset = self.presets[preset_id]

        # 更新类别偏好
        category = preset.category.value
        if "category_preferences" not in self.user_preferences:
            self.user_preferences["category_preferences"] = {}

        self.user_preferences["category_preferences"][category] = \
            self.user_preferences["category_preferences"].get(category, 0) + 1

        # 更新格式偏好
        format_type = preset.base_preset.format.value
        if "format_preferences" not in self.user_preferences:
            self.user_preferences["format_preferences"] = {}

        self.user_preferences["format_preferences"][format_type] = \
            self.user_preferences["format_preferences"].get(format_type, 0) + 1

    def _load_user_data(self):
        """加载用户数据"""
        try:
            user_data_path = Path.home() / ".cineai_studio" / "preset_optimizer_data.json"
            if user_data_path.exists():
                with open(user_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.user_preferences = data.get("user_preferences", {})
                    self.learning_data = data.get("learning_data", {})
        except Exception as e:
            self.logger.warning(f"Failed to load user data: {e}")

    def _save_user_data(self):
        """保存用户数据"""
        try:
            user_data_dir = Path.home() / ".cineai_studio"
            user_data_dir.mkdir(exist_ok=True)

            user_data_path = user_data_dir / "preset_optimizer_data.json"
            data = {
                "user_preferences": self.user_preferences,
                "learning_data": self.learning_data,
                "saved_at": time.time()
            }

            with open(user_data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.warning(f"Failed to save user data: {e}")

    def export_presets(self, file_path: str) -> bool:
        """导出预设"""
        try:
            export_data = {
                "presets": {},
                "user_preferences": self.user_preferences,
                "exported_at": time.time()
            }

            for preset_id, preset in self.presets.items():
                export_data["presets"][preset_id] = {
                    "base_preset": {
                        "id": preset.base_preset.id,
                        "name": preset.base_preset.name,
                        "format": preset.base_preset.format.value,
                        "quality": preset.base_preset.quality.value,
                        "resolution": preset.base_preset.resolution,
                        "bitrate": preset.base_preset.bitrate,
                        "fps": preset.base_preset.fps,
                        "audio_bitrate": preset.base_preset.audio_bitrate,
                        "codec_params": preset.base_preset.codec_params,
                        "description": preset.base_preset.description
                    },
                    "category": preset.category.value,
                    "tags": preset.tags,
                    "description": preset.description,
                    "version": preset.version
                }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Exported {len(self.presets)} presets to {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export presets: {e}")
            return False

    def import_presets(self, file_path: str) -> bool:
        """导入预设"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            imported_count = 0
            for preset_id, preset_data in data.get("presets", {}).items():
                try:
                    # 创建基础预设
                    base_preset = ExportPreset(
                        id=preset_data["base_preset"]["id"],
                        name=preset_data["base_preset"]["name"],
                        format=ExportFormat(preset_data["base_preset"]["format"]),
                        quality=ExportQuality(preset_data["base_preset"]["quality"]),
                        resolution=tuple(preset_data["base_preset"]["resolution"]),
                        bitrate=preset_data["base_preset"]["bitrate"],
                        fps=preset_data["base_preset"]["fps"],
                        audio_bitrate=preset_data["base_preset"]["audio_bitrate"],
                        codec_params=preset_data["base_preset"]["codec_params"],
                        description=preset_data["base_preset"]["description"]
                    )

                    # 创建智能预设
                    smart_preset = SmartPreset(
                        base_preset=base_preset,
                        category=PresetCategory(preset_data["category"]),
                        usage_stats=PresetUsageStats(),
                        performance=PresetPerformance(),
                        tags=preset_data.get("tags", []),
                        description=preset_data.get("description", ""),
                        version=preset_data.get("version", "1.0")
                    )

                    self.presets[preset_id] = smart_preset
                    imported_count += 1

                except Exception as e:
                    self.logger.warning(f"Failed to import preset {preset_id}: {e}")

            # 更新用户偏好
            if "user_preferences" in data:
                self.user_preferences.update(data["user_preferences"])

            self.logger.info(f"Imported {imported_count} presets from {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to import presets: {e}")
            return False


# 全局预设优化器实例
preset_optimizer = PresetOptimizer()