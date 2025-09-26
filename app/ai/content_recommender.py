#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能内容推荐和素材管理系统
提供内容分析、智能推荐、素材管理、标签系统等功能
"""

import os
import json
import time
import hashlib
import mimetypes
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import threading
import queue
import logging
from collections import defaultdict, deque
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import pickle
from pathlib import Path

try:
    from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
    from PyQt6.QtCore import pyqtSignal as Signal
except ImportError:
    try:
        from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread
        from PyQt5.QtCore import pyqtSignal as Signal
    except ImportError:
        try:
            from PySide2.QtCore import QObject, Signal, QTimer, QThread
        except ImportError:
            try:
                from PySide6.QtCore import QObject, Signal, QTimer, QThread
            except ImportError:
                class Signal:
                    def __init__(self, *args, **kwargs):
                        pass
                class QObject:
                    def __init__(self):
                        pass
                class QTimer:
                    def __init__(self):
                        pass
                class QThread:
                    def __init__(self):
                        pass


class ContentType(Enum):
    """内容类型"""
    VIDEO = "video"              # 视频
    AUDIO = "audio"              # 音频
    IMAGE = "image"              # 图像
    DOCUMENT = "document"        # 文档
    PROJECT = "project"          # 项目
    EFFECT = "effect"            # 特效
    TRANSITION = "transition"    # 转场
    TEMPLATE = "template"        # 模板
    PRESET = "preset"            # 预设


class RecommendationType(Enum):
    """推荐类型"""
    SIMILAR_CONTENT = "similar_content"        # 相似内容
    TRENDING = "trending"                     # 热门内容
    RECENTLY_USED = "recently_used"           # 最近使用
    FREQUENTLY_USED = "frequently_used"       # 常用内容
    BASED_ON_PROJECT = "based_on_project"      # 基于项目
    PERSONALIZED = "personalized"              # 个性化推荐


@dataclass
class MediaAsset:
    """媒体素材"""
    asset_id: str
    name: str
    path: str
    content_type: ContentType
    file_size: int
    duration: Optional[float] = None
    resolution: Optional[Tuple[int, int]] = None
    format: str = ""
    bitrate: Optional[int] = None
    codec: str = ""
    created_at: float = None
    modified_at: float = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    thumbnail_path: Optional[str] = None
    rating: float = 0.0
    usage_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.modified_at is None:
            self.modified_at = time.time()
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}

    @property
    def file_hash(self) -> str:
        """文件哈希"""
        if not hasattr(self, '_hash'):
            self._hash = self._calculate_file_hash()
        return self._hash

    def _calculate_file_hash(self) -> str:
        """计算文件哈希"""
        if not os.path.exists(self.path):
            return ""

        hash_md5 = hashlib.md5()
        with open(self.path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


@dataclass
class Recommendation:
    """推荐结果"""
    recommendation_id: str
    recommendation_type: RecommendationType
    assets: List[MediaAsset]
    confidence: float
    reason: str
    context: Dict[str, Any]
    created_at: float = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


@dataclass
class ProjectContext:
    """项目上下文"""
    project_id: str
    project_name: str
    current_timeline: Dict[str, Any]
    used_assets: List[str]
    project_tags: List[str]
    created_at: float = None
    modified_at: float = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.modified_at is None:
            self.modified_at = time.time()


class ContentAnalyzer:
    """内容分析器"""

    def __init__(self):
        self.analysis_cache = {}

    def analyze_content(self, asset: MediaAsset) -> Dict[str, Any]:
        """分析内容"""
        cache_key = f"{asset.path}_{asset.modified_at}"

        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]

        analysis_result = {}

        try:
            if asset.content_type == ContentType.VIDEO:
                analysis_result = self._analyze_video(asset)
            elif asset.content_type == ContentType.AUDIO:
                analysis_result = self._analyze_audio(asset)
            elif asset.content_type == ContentType.IMAGE:
                analysis_result = self._analyze_image(asset)
            else:
                analysis_result = self._analyze_generic(asset)

            self.analysis_cache[cache_key] = analysis_result
            return analysis_result

        except Exception as e:
            logging.error(f"内容分析失败: {e}")
            return {}

    def _analyze_video(self, asset: MediaAsset) -> Dict[str, Any]:
        """分析视频内容"""
        try:
            import cv2

            cap = cv2.VideoCapture(asset.path)
            if not cap.isOpened():
                return {}

            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # 分析样本帧
            sample_frames = []
            for i in range(0, frame_count, max(1, frame_count // 10)):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if ret:
                    sample_frames.append(frame)

            cap.release()

            # 分析视觉特征
            visual_features = self._extract_visual_features(sample_frames)

            return {
                "fps": fps,
                "frame_count": frame_count,
                "resolution": (width, height),
                "visual_features": visual_features,
                "motion_level": self._calculate_motion_level(sample_frames),
                "brightness": self._calculate_brightness(sample_frames),
                "color_palette": self._extract_color_palette(sample_frames)
            }

        except Exception as e:
            logging.error(f"视频分析失败: {e}")
            return {}

    def _analyze_audio(self, asset: MediaAsset) -> Dict[str, Any]:
        """分析音频内容"""
        try:
            import librosa

            y, sr = librosa.load(asset.path, sr=None)

            # 提取音频特征
            mfccs = librosa.feature.mfcc(y=y, sr=sr)
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)

            # 计算统计特征
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

            return {
                "sample_rate": sr,
                "duration": len(y) / sr,
                "tempo": tempo,
                "mfcc_mean": mfccs.mean(axis=1).tolist(),
                "chroma_mean": chroma.mean(axis=1).tolist(),
                "spectral_centroid_mean": float(np.mean(spectral_centroid)),
                "zero_crossing_rate_mean": float(np.mean(zero_crossing_rate)),
                "energy": float(np.sum(y ** 2) / len(y))
            }

        except Exception as e:
            logging.error(f"音频分析失败: {e}")
            return {}

    def _analyze_image(self, asset: MediaAsset) -> Dict[str, Any]:
        """分析图像内容"""
        try:
            import cv2

            image = cv2.imread(asset.path)
            if image is None:
                return {}

            # 分析视觉特征
            visual_features = self._extract_image_features(image)

            return {
                "resolution": (image.shape[1], image.shape[0]),
                "channels": image.shape[2] if len(image.shape) > 2 else 1,
                "visual_features": visual_features,
                "color_palette": self._extract_image_color_palette(image),
                "brightness": float(np.mean(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))),
                "contrast": float(np.std(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)))
            }

        except Exception as e:
            logging.error(f"图像分析失败: {e}")
            return {}

    def _analyze_generic(self, asset: MediaAsset) -> Dict[str, Any]:
        """分析通用内容"""
        return {
            "file_size": asset.file_size,
            "format": asset.format,
            "created_at": asset.created_at,
            "modified_at": asset.modified_at
        }

    def _extract_visual_features(self, frames: List[np.ndarray]) -> Dict[str, float]:
        """提取视觉特征"""
        if not frames:
            return {}

        features = {}
        total_frames = len(frames)

        # 计算平均亮度
        brightness_values = []
        for frame in frames:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness_values.append(np.mean(gray))

        features["avg_brightness"] = np.mean(brightness_values)
        features["brightness_variance"] = np.var(brightness_values)

        # 计算边缘密度
        edge_densities = []
        for frame in frames:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            edge_densities.append(edge_density)

        features["avg_edge_density"] = np.mean(edge_densities)

        return features

    def _calculate_motion_level(self, frames: List[np.ndarray]) -> float:
        """计算运动水平"""
        if len(frames) < 2:
            return 0.0

        motion_levels = []
        for i in range(1, len(frames)):
            prev_gray = cv2.cvtColor(frames[i-1], cv2.COLOR_BGR2GRAY)
            curr_gray = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)

            # 计算帧差
            diff = cv2.absdiff(prev_gray, curr_gray)
            motion_level = np.mean(diff) / 255.0
            motion_levels.append(motion_level)

        return np.mean(motion_levels)

    def _calculate_brightness(self, frames: List[np.ndarray]) -> float:
        """计算平均亮度"""
        if not frames:
            return 0.0

        brightness_values = []
        for frame in frames:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness_values.append(np.mean(gray))

        return np.mean(brightness_values)

    def _extract_color_palette(self, frames: List[np.ndarray]) -> List[Tuple[int, int, int]]:
        """提取调色板"""
        if not frames:
            return []

        # 使用K-means聚类提取主要颜色
        all_pixels = []
        for frame in frames:
            pixels = frame.reshape(-1, 3)
            all_pixels.extend(pixels)

        all_pixels = np.array(all_pixels, dtype=np.float32)

        # 应用K-means
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        k = 5
        _, labels, centers = cv2.kmeans(all_pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        # 转换为整数RGB值
        palette = []
        for center in centers:
            color = tuple(map(int, center))
            palette.append(color)

        return palette

    def _extract_image_features(self, image: np.ndarray) -> Dict[str, float]:
        """提取图像特征"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        return {
            "brightness": float(np.mean(gray)),
            "contrast": float(np.std(gray)),
            "edge_density": float(np.sum(cv2.Canny(gray, 50, 150) > 0) / gray.size)
        }

    def _extract_image_color_palette(self, image: np.ndarray) -> List[Tuple[int, int, int]]:
        """提取图像调色板"""
        pixels = image.reshape(-1, 3).astype(np.float32)

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        k = 5
        _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        palette = []
        for center in centers:
            color = tuple(map(int, center))
            palette.append(color)

        return palette


class AssetDatabase:
    """素材数据库"""

    def __init__(self, db_path: str = "media_assets.db"):
        self.db_path = db_path
        self.conn = None
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()

    def _create_tables(self):
        """创建数据表"""
        cursor = self.conn.cursor()

        # 素材表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_assets (
                asset_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                path TEXT UNIQUE NOT NULL,
                content_type TEXT NOT NULL,
                file_size INTEGER,
                duration REAL,
                resolution_width INTEGER,
                resolution_height INTEGER,
                format TEXT,
                bitrate INTEGER,
                codec TEXT,
                created_at REAL,
                modified_at REAL,
                tags TEXT,
                metadata TEXT,
                thumbnail_path TEXT,
                rating REAL,
                usage_count INTEGER,
                file_hash TEXT
            )
        ''')

        # 项目表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                project_name TEXT NOT NULL,
                created_at REAL,
                modified_at REAL,
                project_tags TEXT,
                timeline_data TEXT
            )
        ''')

        # 项目-素材关联表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_assets (
                project_id TEXT,
                asset_id TEXT,
                usage_count INTEGER,
                FOREIGN KEY (project_id) REFERENCES projects (project_id),
                FOREIGN KEY (asset_id) REFERENCES media_assets (asset_id),
                PRIMARY KEY (project_id, asset_id)
            )
        ''')

        # 用户偏好表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                preference_key TEXT PRIMARY KEY,
                preference_value TEXT,
                updated_at REAL
            )
        ''')

        self.conn.commit()

    def add_asset(self, asset: MediaAsset) -> bool:
        """添加素材"""
        try:
            cursor = self.conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO media_assets (
                    asset_id, name, path, content_type, file_size, duration,
                    resolution_width, resolution_height, format, bitrate, codec,
                    created_at, modified_at, tags, metadata, thumbnail_path,
                    rating, usage_count, file_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                asset.asset_id, asset.name, asset.path, asset.content_type.value,
                asset.file_size, asset.duration,
                asset.resolution[0] if asset.resolution else None,
                asset.resolution[1] if asset.resolution else None,
                asset.format, asset.bitrate, asset.codec,
                asset.created_at, asset.modified_at,
                json.dumps(asset.tags), json.dumps(asset.metadata),
                asset.thumbnail_path, asset.rating, asset.usage_count, asset.file_hash
            ))

            self.conn.commit()
            return True

        except Exception as e:
            logging.error(f"添加素材失败: {e}")
            return False

    def get_asset(self, asset_id: str) -> Optional[MediaAsset]:
        """获取素材"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM media_assets WHERE asset_id = ?', (asset_id,))
            row = cursor.fetchone()

            if row:
                return self._row_to_asset(row)
            return None

        except Exception as e:
            logging.error(f"获取素材失败: {e}")
            return None

    def search_assets(self, query: str = "", content_type: ContentType = None,
                    tags: List[str] = None, limit: int = 100) -> List[MediaAsset]:
        """搜索素材"""
        try:
            cursor = self.conn.cursor()

            sql = "SELECT * FROM media_assets WHERE 1=1"
            params = []

            if query:
                sql += " AND (name LIKE ? OR path LIKE ?)"
                params.extend([f"%{query}%", f"%{query}%"])

            if content_type:
                sql += " AND content_type = ?"
                params.append(content_type.value)

            if tags:
                for tag in tags:
                    sql += " AND tags LIKE ?"
                    params.append(f"%{tag}%")

            sql += " ORDER BY usage_count DESC, rating DESC LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            return [self._row_to_asset(row) for row in rows]

        except Exception as e:
            logging.error(f"搜索素材失败: {e}")
            return []

    def _row_to_asset(self, row) -> MediaAsset:
        """将数据库行转换为素材对象"""
        resolution = None
        if row[6] and row[7]:  # resolution_width, resolution_height
            resolution = (row[6], row[7])

        return MediaAsset(
            asset_id=row[0],
            name=row[1],
            path=row[2],
            content_type=ContentType(row[3]),
            file_size=row[4],
            duration=row[5],
            resolution=resolution,
            format=row[8],
            bitrate=row[9],
            codec=row[10],
            created_at=row[11],
            modified_at=row[12],
            tags=json.loads(row[13]) if row[13] else [],
            metadata=json.loads(row[14]) if row[14] else {},
            thumbnail_path=row[15],
            rating=row[16],
            usage_count=row[17]
        )

    def update_asset_usage(self, asset_id: str):
        """更新素材使用次数"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('UPDATE media_assets SET usage_count = usage_count + 1 WHERE asset_id = ?',
                         (asset_id,))
            self.conn.commit()
        except Exception as e:
            logging.error(f"更新素材使用次数失败: {e}")

    def get_frequently_used_assets(self, limit: int = 20) -> List[MediaAsset]:
        """获取常用素材"""
        return self.search_assets(limit=limit)

    def get_recently_used_assets(self, limit: int = 20) -> List[MediaAsset]:
        """获取最近使用的素材"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT ma.* FROM media_assets ma
                JOIN project_assets pa ON ma.asset_id = pa.asset_id
                ORDER BY pa.usage_count DESC, ma.modified_at DESC
                LIMIT ?
            ''', (limit,))

            rows = cursor.fetchall()
            return [self._row_to_asset(row) for row in rows]

        except Exception as e:
            logging.error(f"获取最近使用素材失败: {e}")
            return []

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()


class RecommendationEngine:
    """推荐引擎"""

    def __init__(self, database: AssetDatabase, analyzer: ContentAnalyzer):
        self.database = database
        self.analyzer = analyzer
        self.user_history = defaultdict(list)
        self.preferences = {}

    def get_recommendations(self, context: ProjectContext = None,
                          recommendation_type: RecommendationType = RecommendationType.PERSONALIZED,
                          limit: int = 10) -> List[Recommendation]:
        """获取推荐"""
        recommendations = []

        if recommendation_type == RecommendationType.SIMILAR_CONTENT:
            recommendations = self._get_similar_content_recommendations(context, limit)
        elif recommendation_type == RecommendationType.RECENTLY_USED:
            recommendations = self._get_recently_used_recommendations(limit)
        elif recommendation_type == RecommendationType.FREQUENTLY_USED:
            recommendations = self._get_frequently_used_recommendations(limit)
        elif recommendation_type == RecommendationType.BASED_ON_PROJECT:
            recommendations = self._get_project_based_recommendations(context, limit)
        else:
            recommendations = self._get_personalized_recommendations(context, limit)

        return recommendations

    def _get_similar_content_recommendations(self, context: ProjectContext,
                                           limit: int) -> List[Recommendation]:
        """获取相似内容推荐"""
        if not context or not context.used_assets:
            return []

        recommendations = []
        reference_assets = []

        # 获取参考素材
        for asset_id in context.used_assets:
            asset = self.database.get_asset(asset_id)
            if asset:
                reference_assets.append(asset)

        if not reference_assets:
            return []

        # 分析参考素材特征
        reference_features = []
        for asset in reference_assets:
            analysis = self.analyzer.analyze_content(asset)
            if analysis:
                reference_features.append(analysis)

        # 搜索相似素材
        all_assets = self.database.search_assets(limit=100)

        for asset in all_assets:
            if asset.asset_id in context.used_assets:
                continue

            # 计算相似度
            similarity = self._calculate_similarity(asset, reference_features)
            if similarity > 0.5:  # 相似度阈值
                recommendation = Recommendation(
                    recommendation_id=f"similar_{asset.asset_id}",
                    recommendation_type=RecommendationType.SIMILAR_CONTENT,
                    assets=[asset],
                    confidence=similarity,
                    reason="与项目中的素材相似",
                    context={"similarity_score": similarity}
                )
                recommendations.append(recommendation)

        return recommendations[:limit]

    def _get_recently_used_recommendations(self, limit: int) -> List[Recommendation]:
        """获取最近使用推荐"""
        recent_assets = self.database.get_recently_used_assets(limit)

        recommendations = []
        for asset in recent_assets:
            recommendation = Recommendation(
                recommendation_id=f"recent_{asset.asset_id}",
                recommendation_type=RecommendationType.RECENTLY_USED,
                assets=[asset],
                confidence=0.8,
                reason="最近使用的素材",
                context={"usage_count": asset.usage_count}
            )
            recommendations.append(recommendation)

        return recommendations

    def _get_frequently_used_recommendations(self, limit: int) -> List[Recommendation]:
        """获取常用素材推荐"""
        frequent_assets = self.database.get_frequently_used_assets(limit)

        recommendations = []
        for asset in frequent_assets:
            confidence = min(asset.usage_count / 10.0, 1.0)  # 基于使用次数计算置信度

            recommendation = Recommendation(
                recommendation_id=f"frequent_{asset.asset_id}",
                recommendation_type=RecommendationType.FREQUENTLY_USED,
                assets=[asset],
                confidence=confidence,
                reason="常用素材",
                context={"usage_count": asset.usage_count}
            )
            recommendations.append(recommendation)

        return recommendations

    def _get_project_based_recommendations(self, context: ProjectContext,
                                         limit: int) -> List[Recommendation]:
        """获取基于项目的推荐"""
        if not context:
            return []

        # 分析项目特征
        project_features = self._analyze_project_context(context)

        # 搜索匹配的素材
        matching_assets = self.database.search_assets(limit=50)

        recommendations = []
        for asset in matching_assets:
            if asset.asset_id in context.used_assets:
                continue

            # 计算匹配度
            match_score = self._calculate_project_match(asset, project_features, context)
            if match_score > 0.3:
                recommendation = Recommendation(
                    recommendation_id=f"project_{asset.asset_id}",
                    recommendation_type=RecommendationType.BASED_ON_PROJECT,
                    assets=[asset],
                    confidence=match_score,
                    reason="符合项目需求",
                    context={"match_score": match_score}
                )
                recommendations.append(recommendation)

        return recommendations[:limit]

    def _get_personalized_recommendations(self, context: ProjectContext,
                                         limit: int) -> List[Recommendation]:
        """获取个性化推荐"""
        # 综合多种推荐策略
        all_recommendations = []

        # 获取相似内容推荐
        similar_recs = self._get_similar_content_recommendations(context, limit // 2)
        all_recommendations.extend(similar_recs)

        # 获取项目推荐
        project_recs = self._get_project_based_recommendations(context, limit // 2)
        all_recommendations.extend(project_recs)

        # 按置信度排序
        all_recommendations.sort(key=lambda x: x.confidence, reverse=True)

        return all_recommendations[:limit]

    def _calculate_similarity(self, asset: MediaAsset,
                           reference_features: List[Dict[str, Any]]) -> float:
        """计算相似度"""
        if not reference_features:
            return 0.0

        # 分析当前素材
        current_analysis = self.analyzer.analyze_content(asset)
        if not current_analysis:
            return 0.0

        # 计算特征相似度
        similarities = []
        for ref_features in reference_features:
            similarity = self._calculate_feature_similarity(current_analysis, ref_features)
            similarities.append(similarity)

        return np.mean(similarities) if similarities else 0.0

    def _calculate_feature_similarity(self, features1: Dict[str, Any],
                                   features2: Dict[str, Any]) -> float:
        """计算特征相似度"""
        common_keys = set(features1.keys()) & set(features2.keys())
        if not common_keys:
            return 0.0

        similarities = []
        for key in common_keys:
            val1 = features1[key]
            val2 = features2[key]

            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # 数值特征
                diff = abs(val1 - val2)
                max_val = max(abs(val1), abs(val2), 1e-10)
                similarity = 1.0 - (diff / max_val)
                similarities.append(similarity)

        return np.mean(similarities) if similarities else 0.0

    def _analyze_project_context(self, context: ProjectContext) -> Dict[str, Any]:
        """分析项目上下文"""
        project_features = {
            "project_tags": context.project_tags,
            "used_asset_count": len(context.used_assets),
            "project_duration": time.time() - context.created_at
        }

        # 分析使用的素材类型
        asset_types = defaultdict(int)
        for asset_id in context.used_assets:
            asset = self.database.get_asset(asset_id)
            if asset:
                asset_types[asset.content_type.value] += 1

        project_features["asset_types"] = dict(asset_types)

        return project_features

    def _calculate_project_match(self, asset: MediaAsset,
                               project_features: Dict[str, Any],
                               context: ProjectContext) -> float:
        """计算项目匹配度"""
        match_score = 0.0

        # 检查素材类型是否匹配项目需求
        asset_types = project_features.get("asset_types", {})
        if asset.content_type.value in asset_types:
            match_score += 0.3

        # 检查标签匹配
        if context.project_tags:
            asset_tags = asset.tags or []
            common_tags = set(context.project_tags) & set(asset_tags)
            if common_tags:
                match_score += 0.3 * (len(common_tags) / len(context.project_tags))

        # 检查素材评级
        if asset.rating > 3.0:
            match_score += 0.2

        return min(match_score, 1.0)


class ContentRecommender(QObject):
    """内容推荐器主类"""

    # 信号定义
    asset_added = Signal(MediaAsset)  # 素材添加
    asset_updated = Signal(MediaAsset)  # 素材更新
    recommendations_generated = Signal(list)  # 推荐生成
    analysis_completed = Signal(str, dict)  # 分析完成

    def __init__(self, db_path: str = "media_assets.db"):
        super().__init__()
        self.database = AssetDatabase(db_path)
        self.analyzer = ContentAnalyzer()
        self.recommendation_engine = RecommendationEngine(self.database, self.analyzer)

        self.is_processing = False
        self.scan_thread = None

    def scan_directory(self, directory_path: str, recursive: bool = True):
        """扫描目录"""
        if self.is_processing:
            return

        self.is_processing = True

        # 创建扫描线程
        self.scan_thread = DirectoryScanThread(
            self.database, self.analyzer, directory_path, recursive
        )
        self.scan_thread.asset_found.connect(self._on_asset_found)
        self.scan_thread.scan_completed.connect(self._on_scan_completed)
        self.scan_thread.start()

    def _on_asset_found(self, asset: MediaAsset):
        """素材发现回调"""
        # 添加到数据库
        self.database.add_asset(asset)
        self.asset_added.emit(asset)

    def _on_scan_completed(self):
        """扫描完成回调"""
        self.is_processing = False
        print("目录扫描完成")

    def add_asset(self, file_path: str) -> Optional[MediaAsset]:
        """添加素材"""
        try:
            # 创建素材对象
            asset = self._create_asset_from_file(file_path)
            if asset:
                # 分析内容
                analysis = self.analyzer.analyze_content(asset)
                asset.metadata = analysis

                # 添加到数据库
                self.database.add_asset(asset)
                self.asset_added.emit(asset)

                return asset

        except Exception as e:
            logging.error(f"添加素材失败: {e}")

        return None

    def _create_asset_from_file(self, file_path: str) -> Optional[MediaAsset]:
        """从文件创建素材对象"""
        if not os.path.exists(file_path):
            return None

        # 获取文件信息
        file_stat = os.stat(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)

        # 确定内容类型
        content_type = self._determine_content_type(mime_type, file_path)

        # 生成素材ID
        asset_id = hashlib.md5(file_path.encode()).hexdigest()

        # 创建素材对象
        asset = MediaAsset(
            asset_id=asset_id,
            name=os.path.basename(file_path),
            path=file_path,
            content_type=content_type,
            file_size=file_stat.st_size,
            format=os.path.splitext(file_path)[1].lower(),
            created_at=file_stat.st_ctime,
            modified_at=file_stat.st_mtime
        )

        # 提取额外信息
        if content_type == ContentType.VIDEO:
            self._extract_video_info(asset)
        elif content_type == ContentType.AUDIO:
            self._extract_audio_info(asset)
        elif content_type == ContentType.IMAGE:
            self._extract_image_info(asset)

        return asset

    def _determine_content_type(self, mime_type: str, file_path: str) -> ContentType:
        """确定内容类型"""
        if mime_type:
            if mime_type.startswith('video/'):
                return ContentType.VIDEO
            elif mime_type.startswith('audio/'):
                return ContentType.AUDIO
            elif mime_type.startswith('image/'):
                return ContentType.IMAGE

        # 基于文件扩展名判断
        ext = os.path.splitext(file_path)[1].lower()
        video_exts = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        audio_exts = ['.mp3', '.wav', '.flac', '.aac', '.ogg']
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']

        if ext in video_exts:
            return ContentType.VIDEO
        elif ext in audio_exts:
            return ContentType.AUDIO
        elif ext in image_exts:
            return ContentType.IMAGE
        else:
            return ContentType.DOCUMENT

    def _extract_video_info(self, asset: MediaAsset):
        """提取视频信息"""
        try:
            import cv2

            cap = cv2.VideoCapture(asset.path)
            if cap.isOpened():
                asset.duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
                asset.resolution = (
                    int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                )
                asset.codec = "h264"  # 简化处理
                cap.release()

        except Exception:
            pass

    def _extract_audio_info(self, asset: MediaAsset):
        """提取音频信息"""
        try:
            import librosa

            y, sr = librosa.load(asset.path, sr=None, duration=1.0)  # 只加载1秒来获取信息
            asset.duration = len(y) / sr
            asset.codec = "pcm"

        except Exception:
            pass

    def _extract_image_info(self, asset: MediaAsset):
        """提取图像信息"""
        try:
            import cv2

            image = cv2.imread(asset.path)
            if image is not None:
                asset.resolution = (image.shape[1], image.shape[0])
                asset.codec = "jpeg"

        except Exception:
            pass

    def search_assets(self, query: str = "", content_type: ContentType = None,
                    tags: List[str] = None, limit: int = 100) -> List[MediaAsset]:
        """搜索素材"""
        return self.database.search_assets(query, content_type, tags, limit)

    def get_recommendations(self, context: ProjectContext = None,
                          recommendation_type: RecommendationType = RecommendationType.PERSONALIZED,
                          limit: int = 10) -> List[Recommendation]:
        """获取推荐"""
        recommendations = self.recommendation_engine.get_recommendations(
            context, recommendation_type, limit
        )

        self.recommendations_generated.emit(recommendations)
        return recommendations

    def update_asset_usage(self, asset_id: str):
        """更新素材使用次数"""
        self.database.update_asset_usage(asset_id)

    def analyze_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """分析素材"""
        asset = self.database.get_asset(asset_id)
        if asset:
            analysis = self.analyzer.analyze_content(asset)
            self.analysis_completed.emit(asset_id, analysis)
            return analysis
        return None

    def close(self):
        """关闭推荐器"""
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.stop()
        self.database.close()


class DirectoryScanThread(QThread):
    """目录扫描线程"""

    asset_found = Signal(MediaAsset)
    scan_completed = Signal()

    def __init__(self, database: AssetDatabase, analyzer: ContentAnalyzer,
                 directory_path: str, recursive: bool):
        super().__init__()
        self.database = database
        self.analyzer = analyzer
        self.directory_path = directory_path
        self.recursive = recursive
        self._is_running = True

    def run(self):
        """运行扫描"""
        try:
            self._scan_directory(self.directory_path)
            self.scan_completed.emit()
        except Exception as e:
            logging.error(f"目录扫描失败: {e}")

    def _scan_directory(self, directory_path: str):
        """扫描目录"""
        for root, dirs, files in os.walk(directory_path):
            if not self._is_running:
                break

            for filename in files:
                if not self._is_running:
                    break

                file_path = os.path.join(root, filename)

                # 跳过隐藏文件和系统文件
                if filename.startswith('.') or filename.startswith('~'):
                    continue

                try:
                    # 创建素材对象
                    asset = self._create_asset_from_file(file_path)
                    if asset:
                        # 分析内容
                        analysis = self.analyzer.analyze_content(asset)
                        asset.metadata = analysis

                        # 发送信号
                        self.asset_found.emit(asset)

                except Exception as e:
                    logging.warning(f"处理文件失败 {file_path}: {e}")

            if not self.recursive:
                break

    def _create_asset_from_file(self, file_path: str) -> Optional[MediaAsset]:
        """从文件创建素材对象"""
        if not os.path.exists(file_path):
            return None

        file_stat = os.stat(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        content_type = self._determine_content_type(mime_type, file_path)

        asset_id = hashlib.md5(file_path.encode()).hexdigest()

        asset = MediaAsset(
            asset_id=asset_id,
            name=os.path.basename(file_path),
            path=file_path,
            content_type=content_type,
            file_size=file_stat.st_size,
            format=os.path.splitext(file_path)[1].lower(),
            created_at=file_stat.st_ctime,
            modified_at=file_stat.st_mtime
        )

        return asset

    def _determine_content_type(self, mime_type: str, file_path: str) -> ContentType:
        """确定内容类型"""
        if mime_type:
            if mime_type.startswith('video/'):
                return ContentType.VIDEO
            elif mime_type.startswith('audio/'):
                return ContentType.AUDIO
            elif mime_type.startswith('image/'):
                return ContentType.IMAGE

        ext = os.path.splitext(file_path)[1].lower()
        video_exts = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        audio_exts = ['.mp3', '.wav', '.flac', '.aac', '.ogg']
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']

        if ext in video_exts:
            return ContentType.VIDEO
        elif ext in audio_exts:
            return ContentType.AUDIO
        elif ext in image_exts:
            return ContentType.IMAGE
        else:
            return ContentType.DOCUMENT

    def stop(self):
        """停止扫描"""
        self._is_running = False


# 工具函数
def create_content_recommender(db_path: str = "media_assets.db") -> ContentRecommender:
    """创建内容推荐器"""
    return ContentRecommender(db_path)


def main():
    """主函数 - 用于测试"""
    # 创建内容推荐器
    recommender = create_content_recommender()

    # 测试推荐功能
    print("内容推荐器创建成功")
    print("数据库初始化完成")


if __name__ == "__main__":
    main()