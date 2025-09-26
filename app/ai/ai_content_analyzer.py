#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI内容分析器
提供深度学习模型用于视频内容理解、场景分类、情感分析等
"""

import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import threading
import queue
import time
from collections import defaultdict
import logging
import json

try:
    import torch
    import torch.nn as nn
    import torchvision.transforms as transforms
    from torchvision.models import resnet50, googlenet
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("警告: PyTorch未安装，将使用传统计算机视觉方法")

try:
    import tensorflow as tf
    from tensorflow.keras.applications import VGG16, ResNet50
    from tensorflow.keras.applications.vgg16 import preprocess_input as vgg_preprocess
    from tensorflow.keras.applications.resnet50 import preprocess_input as resnet_preprocess
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("警告: TensorFlow未安装，将使用传统计算机视觉方法")


class ContentType(Enum):
    """内容类型"""
    PERSON = "person"              # 人物
    VEHICLE = "vehicle"           # 车辆
    BUILDING = "building"         # 建筑
    NATURE = "nature"             # 自然
    TEXT = "text"                # 文本
    LOGO = "logo"                # 标志
    EMOTION = "emotion"          # 情感
    ACTION = "action"            # 动作
    SCENE = "scene"              # 场景


class EmotionType(Enum):
    """情感类型"""
    HAPPY = "happy"              # 开心
    SAD = "sad"                 # 悲伤
    ANGRY = "angry"             # 愤怒
    SURPRISED = "surprised"     # 惊讶
    FEAR = "fear"               # 恐惧
    DISGUST = "disgust"         # 厌恶
    NEUTRAL = "neutral"         # 中性


@dataclass
class ContentObject:
    """内容对象"""
    object_type: ContentType
    bbox: Tuple[int, int, int, int]  # (x, y, w, h)
    confidence: float
    attributes: Dict[str, Any]
    timestamp: float


@dataclass
class SceneAnalysis:
    """场景分析结果"""
    scene_type: str
    confidence: float
    objects: List[ContentObject]
    dominant_colors: List[Tuple[int, int, int]]
    composition_score: float
    aesthetic_score: float
    emotional_tone: EmotionType
    keywords: List[str]


class TraditionalFeatureExtractor:
    """传统特征提取器（不依赖深度学习框架）"""

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        self.body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')

        # 初始化SIFT特征提取器
        self.sift = cv2.SIFT_create()

        # 初始化背景减除器
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2()

    def extract_visual_features(self, frame: np.ndarray) -> Dict[str, Any]:
        """提取视觉特征"""
        features = {}
        height, width = frame.shape[:2]

        # 颜色特征
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        features['color_histogram'] = self._extract_color_histogram(hsv)
        features['dominant_colors'] = self._extract_dominant_colors(frame)

        # 纹理特征
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        features['texture_features'] = self._extract_texture_features(gray)

        # 边缘特征
        edges = cv2.Canny(gray, 50, 150)
        features['edge_density'] = np.sum(edges > 0) / edges.size
        features['edge_orientation'] = self._analyze_edge_orientation(edges)

        # 形状特征
        features['shape_features'] = self._extract_shape_features(frame)

        # 空间特征
        features['spatial_features'] = self._extract_spatial_features(frame)

        # 运动特征（需要多帧）
        features['motion_features'] = self._extract_motion_features(frame)

        return features

    def detect_objects_traditional(self, frame: np.ndarray) -> List[ContentObject]:
        """使用传统方法检测对象"""
        objects = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 检测人脸
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            obj = ContentObject(
                object_type=ContentType.PERSON,
                bbox=(x, y, w, h),
                confidence=0.8,
                attributes={"face": True},
                timestamp=time.time()
            )
            objects.append(obj)

        # 检测人体
        bodies = self.body_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in bodies:
            obj = ContentObject(
                object_type=ContentType.PERSON,
                bbox=(x, y, w, h),
                confidence=0.7,
                attributes={"full_body": True},
                timestamp=time.time()
            )
            objects.append(obj)

        # 检测车辆（基于轮廓）
        vehicles = self._detect_vehicles_contour_based(frame)
        objects.extend(vehicles)

        # 检测文本
        text_regions = self._detect_text_regions(frame)
        objects.extend(text_regions)

        return objects

    def _extract_color_histogram(self, hsv_frame: np.ndarray) -> np.ndarray:
        """提取颜色直方图"""
        hist_h = cv2.calcHist([hsv_frame], [0], None, [16], [0, 180])
        hist_s = cv2.calcHist([hsv_frame], [1], None, [8], [0, 256])
        hist_v = cv2.calcHist([hsv_frame], [2], None, [8], [0, 256])

        # 归一化
        hist_h = cv2.normalize(hist_h, hist_h).flatten()
        hist_s = cv2.normalize(hist_s, hist_s).flatten()
        hist_v = cv2.normalize(hist_v, hist_v).flatten()

        return np.concatenate([hist_h, hist_s, hist_v])

    def _extract_dominant_colors(self, frame: np.ndarray, k: int = 5) -> List[Tuple[int, int, int]]:
        """提取主要颜色"""
        # 使用K-means聚类提取主要颜色
        pixel_values = frame.reshape(-1, 3).astype(np.float32)

        # 定义停止条件
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)

        # 应用K-means
        _, labels, centers = cv2.kmeans(pixel_values, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        # 转换为整数RGB值
        dominant_colors = []
        for center in centers:
            color = tuple(map(int, center))
            dominant_colors.append(color)

        return dominant_colors

    def _extract_texture_features(self, gray_frame: np.ndarray) -> Dict[str, float]:
        """提取纹理特征"""
        features = {}

        # LBP特征
        features['lbp_variance'] = self._calculate_lbp_variance(gray_frame)

        # GLCM特征
        features['glcm_contrast'] = self._calculate_glcm_contrast(gray_frame)
        features['glcm_homogeneity'] = self._calculate_glcm_homogeneity(gray_frame)

        return features

    def _calculate_lbp_variance(self, gray_frame: np.ndarray) -> float:
        """计算LBP方差"""
        # 简化的LBP计算
        height, width = gray_frame.shape
        lbp = np.zeros((height-2, width-2), dtype=np.uint8)

        for i in range(1, height-1):
            for j in range(1, width-1):
                center = gray_frame[i, j]
                binary = ""

                # 8邻域
                neighbors = [
                    gray_frame[i-1, j-1], gray_frame[i-1, j], gray_frame[i-1, j+1],
                    gray_frame[i, j+1], gray_frame[i+1, j+1], gray_frame[i+1, j],
                    gray_frame[i+1, j-1], gray_frame[i, j-1]
                ]

                for neighbor in neighbors:
                    binary += "1" if neighbor >= center else "0"

                lbp[i-1, j-1] = int(binary, 2)

        return np.var(lbp)

    def _calculate_glcm_contrast(self, gray_frame: np.ndarray) -> float:
        """计算GLCM对比度"""
        # 简化的GLCM计算
        glcm = np.zeros((256, 256))

        for i in range(gray_frame.shape[0]-1):
            for j in range(gray_frame.shape[1]-1):
                current = gray_frame[i, j]
                next_pixel = gray_frame[i, j+1]
                glcm[current, next_pixel] += 1

        # 归一化
        glcm = glcm / np.sum(glcm)

        # 计算对比度
        contrast = 0
        for i in range(256):
            for j in range(256):
                contrast += (i - j) ** 2 * glcm[i, j]

        return contrast

    def _calculate_glcm_homogeneity(self, gray_frame: np.ndarray) -> float:
        """计算GLCM一致性"""
        glcm = np.zeros((256, 256))

        for i in range(gray_frame.shape[0]-1):
            for j in range(gray_frame.shape[1]-1):
                current = gray_frame[i, j]
                next_pixel = gray_frame[i, j+1]
                glcm[current, next_pixel] += 1

        glcm = glcm / np.sum(glcm)

        # 计算一致性
        homogeneity = 0
        for i in range(256):
            for j in range(256):
                homogeneity += glcm[i, j] / (1 + abs(i - j))

        return homogeneity

    def _analyze_edge_orientation(self, edges: np.ndarray) -> Dict[str, float]:
        """分析边缘方向"""
        # 使用Sobel算子计算梯度
        sobel_x = cv2.Sobel(edges, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(edges, cv2.CV_64F, 0, 1, ksize=3)

        # 计算梯度方向
        orientations = np.arctan2(sobel_y, sobel_x) * 180 / np.pi

        # 统计方向分布
        hist, _ = np.histogram(orientations, bins=8, range=(-180, 180))

        return {
            "orientation_histogram": hist.tolist(),
            "dominant_orientation": np.degrees(np.arctan2(np.mean(sobel_y), np.mean(sobel_x)))
        }

    def _extract_shape_features(self, frame: np.ndarray) -> Dict[str, Any]:
        """提取形状特征"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

        # 查找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        features = {
            "contour_count": len(contours),
            "max_contour_area": 0,
            "contour_complexity": []
        }

        for contour in contours:
            area = cv2.contourArea(contour)
            features["max_contour_area"] = max(features["max_contour_area"], area)

            # 计算轮廓复杂度
            perimeter = cv2.arcLength(contour, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter ** 2)
                features["contour_complexity"].append(circularity)

        return features

    def _extract_spatial_features(self, frame: np.ndarray) -> Dict[str, Any]:
        """提取空间特征"""
        height, width = frame.shape[:2]

        # 将画面分为九宫格
        grid_h, grid_w = 3, 3
        cell_h, cell_w = height // grid_h, width // grid_w

        features = {"grid_features": []}

        for i in range(grid_h):
            for j in range(grid_w):
                y1, y2 = i * cell_h, (i + 1) * cell_h
                x1, x2 = j * cell_w, (j + 1) * cell_w

                cell = frame[y1:y2, x1:x2]
                cell_features = self._extract_cell_features(cell)
                features["grid_features"].append(cell_features)

        return features

    def _extract_cell_features(self, cell: np.ndarray) -> Dict[str, float]:
        """提取单元格特征"""
        gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)

        return {
            "brightness": np.mean(gray),
            "contrast": np.std(gray),
            "edge_density": np.sum(cv2.Canny(gray, 50, 150) > 0) / gray.size
        }

    def _extract_motion_features(self, frame: np.ndarray) -> Dict[str, float]:
        """提取运动特征"""
        if not hasattr(self, 'prev_frame'):
            self.prev_frame = frame.copy()
            return {"motion_intensity": 0.0}

        # 计算帧差
        prev_gray = cv2.cvtColor(self.prev_frame, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        frame_diff = cv2.absdiff(prev_gray, curr_gray)
        motion_intensity = np.mean(frame_diff) / 255.0

        self.prev_frame = frame.copy()

        return {"motion_intensity": motion_intensity}

    def _detect_vehicles_contour_based(self, frame: np.ndarray) -> List[ContentObject]:
        """基于轮廓检测车辆"""
        objects = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 背景减除
        fg_mask = self.bg_subtractor.apply(gray)

        # 形态学操作
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)

        # 查找轮廓
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # 过滤小区域
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h

                # 车辆通常具有特定的长宽比
                if 0.5 < aspect_ratio < 3.0:
                    obj = ContentObject(
                        object_type=ContentType.VEHICLE,
                        bbox=(x, y, w, h),
                        confidence=0.6,
                        attributes={"contour_based": True},
                        timestamp=time.time()
                    )
                    objects.append(obj)

        return objects

    def _detect_text_regions(self, frame: np.ndarray) -> List[ContentObject]:
        """检测文本区域"""
        objects = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 使用MSER检测文本区域
        mser = cv2.MSER_create()
        regions, _ = mser.detectRegions(gray)

        for region in regions:
            x, y, w, h = cv2.boundingRect(region)
            area = w * h

            # 过滤小区域
            if area > 100:
                obj = ContentObject(
                    object_type=ContentType.TEXT,
                    bbox=(x, y, w, h),
                    confidence=0.5,
                    attributes={"mser_based": True},
                    timestamp=time.time()
                )
                objects.append(obj)

        return objects


class DeepLearningFeatureExtractor:
    """深度学习特征提取器"""

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.transform = None
        self.is_initialized = False

        if TORCH_AVAILABLE:
            self._initialize_torch_model()
        elif TF_AVAILABLE:
            self._initialize_tf_model()

    def _initialize_torch_model(self):
        """初始化PyTorch模型"""
        try:
            # 使用预训练的ResNet50
            self.model = resnet50(pretrained=True)
            self.model.eval()
            self.model.to(self.device)

            # 定义图像预处理
            self.transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                   std=[0.229, 0.224, 0.225])
            ])

            self.is_initialized = True
            print("PyTorch模型初始化成功")

        except Exception as e:
            print(f"PyTorch模型初始化失败: {e}")

    def _initialize_tf_model(self):
        """初始化TensorFlow模型"""
        try:
            # 使用预训练的VGG16
            self.model = VGG16(weights='imagenet', include_top=False, pooling='avg')
            self.is_initialized = True
            print("TensorFlow模型初始化成功")

        except Exception as e:
            print(f"TensorFlow模型初始化失败: {e}")

    def extract_deep_features(self, frame: np.ndarray) -> np.ndarray:
        """提取深度特征"""
        if not self.is_initialized:
            return np.array([])

        try:
            if TORCH_AVAILABLE and self.model is not None:
                return self._extract_torch_features(frame)
            elif TF_AVAILABLE and self.model is not None:
                return self._extract_tf_features(frame)
            else:
                return np.array([])

        except Exception as e:
            print(f"深度特征提取失败: {e}")
            return np.array([])

    def _extract_torch_features(self, frame: np.ndarray) -> np.ndarray:
        """使用PyTorch提取特征"""
        # 预处理图像
        input_tensor = self.transform(frame).unsqueeze(0).to(self.device)

        # 提取特征
        with torch.no_grad():
            features = self.model(input_tensor)

        return features.cpu().numpy().flatten()

    def _extract_tf_features(self, frame: np.ndarray) -> np.ndarray:
        """使用TensorFlow提取特征"""
        # 预处理图像
        img = cv2.resize(frame, (224, 224))
        img_array = vgg_preprocess(img)
        img_array = np.expand_dims(img_array, axis=0)

        # 提取特征
        features = self.model.predict(img_array)
        return features.flatten()

    def classify_scene(self, frame: np.ndarray) -> Tuple[str, float]:
        """分类场景类型"""
        features = self.extract_deep_features(frame)
        if len(features) == 0:
            return "unknown", 0.0

        # 简化的场景分类逻辑
        # 在实际应用中，这里应该使用训练好的分类器
        scene_types = ["indoor", "outdoor", "urban", "nature", "people", "vehicle"]
        scores = np.random.dirichlet(np.ones(len(scene_types)))  # 模拟分类分数

        best_idx = np.argmax(scores)
        return scene_types[best_idx], scores[best_idx]


class AIContentAnalyzer:
    """AI内容分析器主类"""

    def __init__(self, use_deep_learning: bool = True):
        self.traditional_extractor = TraditionalFeatureExtractor()
        self.deep_extractor = None

        if use_deep_learning and (TORCH_AVAILABLE or TF_AVAILABLE):
            self.deep_extractor = DeepLearningFeatureExtractor()

        self.use_deep_learning = use_deep_learning and self.deep_extractor is not None

    def analyze_frame(self, frame: np.ndarray) -> SceneAnalysis:
        """分析单帧内容"""
        # 传统特征提取
        traditional_features = self.traditional_extractor.extract_visual_features(frame)

        # 对象检测
        objects = self.traditional_extractor.detect_objects_traditional(frame)

        # 深度特征提取（如果可用）
        deep_features = None
        if self.use_deep_learning:
            deep_features = self.deep_extractor.extract_deep_features(frame)

        # 场景分类
        scene_type, confidence = self._classify_scene(
            traditional_features, deep_features, objects
        )

        # 美学评分
        aesthetic_score = self._calculate_aesthetic_score(
            traditional_features, objects
        )

        # 情感分析
        emotional_tone = self._analyze_emotion(
            traditional_features, objects, deep_features
        )

        # 生成关键词
        keywords = self._generate_keywords(
            traditional_features, objects, scene_type
        )

        # 获取主要颜色
        dominant_colors = traditional_features.get('dominant_colors', [])

        return SceneAnalysis(
            scene_type=scene_type,
            confidence=confidence,
            objects=objects,
            dominant_colors=dominant_colors,
            composition_score=traditional_features.get('spatial_features', {}).get('composition_score', 0.5),
            aesthetic_score=aesthetic_score,
            emotional_tone=emotional_tone,
            keywords=keywords
        )

    def _classify_scene(self, traditional_features: Dict[str, Any],
                       deep_features: np.ndarray, objects: List[ContentObject]) -> Tuple[str, float]:
        """分类场景类型"""
        # 基于传统特征的场景分类
        scene_scores = defaultdict(float)

        # 基于对象的线索
        object_counts = defaultdict(int)
        for obj in objects:
            object_counts[obj.object_type] += 1

        # 场景分类规则
        if object_counts[ContentType.PERSON] > 0:
            if object_counts[ContentType.BUILDING] > 0:
                scene_scores["urban"] += 0.7
            else:
                scene_scores["people"] += 0.8
        elif object_counts[ContentType.VEHICLE] > 0:
            scene_scores["urban"] += 0.6
        elif object_counts[ContentType.NATURE] > 0:
            scene_scores["nature"] += 0.9

        # 基于颜色特征的线索
        dominant_colors = traditional_features.get('dominant_colors', [])
        if dominant_colors:
            avg_green = np.mean([color[1] for color in dominant_colors])
            avg_blue = np.mean([color[2] for color in dominant_colors])

            if avg_green > avg_blue:
                scene_scores["nature"] += 0.3
            else:
                scene_scores["urban"] += 0.2

        # 基于纹理特征的线索
        texture_features = traditional_features.get('texture_features', {})
        if texture_features.get('glcm_contrast', 0) > 0.5:
            scene_scores["urban"] += 0.2
        elif texture_features.get('glcm_homogeneity', 0) > 0.7:
            scene_scores["nature"] += 0.2

        # 如果有深度特征，结合深度学习结果
        if self.use_deep_learning and deep_features is not None and len(deep_features) > 0:
            dl_scene_type, dl_confidence = self.deep_extractor.classify_scene(
                np.zeros((224, 224, 3), dtype=np.uint8)  # 需要重构frame
            )
            scene_scores[dl_scene_type] += dl_confidence * 0.5

        # 选择得分最高的场景类型
        if scene_scores:
            best_scene = max(scene_scores.items(), key=lambda x: x[1])
            return best_scene[0], best_scene[1]
        else:
            return "unknown", 0.0

    def _calculate_aesthetic_score(self, traditional_features: Dict[str, Any],
                                 objects: List[ContentObject]) -> float:
        """计算美学评分"""
        score = 0.0

        # 构图评分
        spatial_features = traditional_features.get('spatial_features', {})
        if spatial_features:
            # 检查三分法构图
            grid_features = spatial_features.get('grid_features', [])
            if grid_features:
                center_cell = grid_features[4]  # 九宫格中心
                edge_cells = [grid_features[i] for i in [0, 2, 6, 8]]  # 四角

                # 中心不应该过于突出，边缘应该有内容
                center_brightness = center_cell.get('brightness', 0)
                edge_avg_brightness = np.mean([cell.get('brightness', 0) for cell in edge_cells])

                if abs(center_brightness - edge_avg_brightness) < 50:
                    score += 0.3

        # 对象分布评分
        if objects:
            # 检查对象分布是否合理
            obj_positions = [(obj.bbox[0] + obj.bbox[2]/2, obj.bbox[1] + obj.bbox[3]/2) for obj in objects]
            if obj_positions:
                # 计算对象分布的方差
                x_variance = np.var([pos[0] for pos in obj_positions])
                y_variance = np.var([pos[1] for pos in obj_positions])

                if 1000 < x_variance < 50000 and 1000 < y_variance < 30000:
                    score += 0.3

        # 颜色和谐性评分
        dominant_colors = traditional_features.get('dominant_colors', [])
        if len(dominant_colors) >= 2:
            # 检查颜色是否和谐
            color_harmony = self._calculate_color_harmony(dominant_colors)
            score += color_harmony * 0.4

        return min(score, 1.0)

    def _calculate_color_harmony(self, colors: List[Tuple[int, int, int]]) -> float:
        """计算颜色和谐性"""
        if len(colors) < 2:
            return 0.0

        # 转换为HSV色彩空间
        hsv_colors = []
        for color in colors:
            rgb = np.float32([[color]]) / 255.0
            hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)[0][0]
            hsv_colors.append(hsv)

        # 计算色调差异
        hue_diffs = []
        for i in range(len(hsv_colors)):
            for j in range(i+1, len(hsv_colors)):
                hue_diff = abs(hsv_colors[i][0] - hsv_colors[j][0])
                hue_diff = min(hue_diff, 180 - hue_diff)  # 圆形色彩空间
                hue_diffs.append(hue_diff)

        # 和谐的颜色组合通常具有特定的色调差异
        harmony_scores = []
        for diff in hue_diffs:
            if 30 <= diff <= 60:  # 类似色
                harmony_scores.append(0.8)
            elif 120 <= diff <= 150:  # 互补色
                harmony_scores.append(0.9)
            elif 60 <= diff <= 120:  # 对比色
                harmony_scores.append(0.6)
            else:
                harmony_scores.append(0.3)

        return np.mean(harmony_scores) if harmony_scores else 0.0

    def _analyze_emotion(self, traditional_features: Dict[str, Any],
                        objects: List[ContentObject], deep_features: np.ndarray) -> EmotionType:
        """分析情感"""
        emotion_scores = defaultdict(float)

        # 基于颜色的情感分析
        dominant_colors = traditional_features.get('dominant_colors', [])
        if dominant_colors:
            avg_color = np.mean(dominant_colors, axis=0)

            # 暖色调vs冷色调
            if avg_color[0] > avg_color[2]:  # 红色 > 蓝色
                emotion_scores[EmotionType.HAPPY] += 0.3
                emotion_scores[EmotionType.ANGRY] += 0.2
            else:
                emotion_scores[EmotionType.SAD] += 0.3
                emotion_scores[EmotionType.NEUTRAL] += 0.2

        # 基于亮度的情感分析
        brightness = traditional_features.get('brightness', 128)
        if brightness > 180:
            emotion_scores[EmotionType.HAPPY] += 0.3
        elif brightness < 80:
            emotion_scores[EmotionType.SAD] += 0.3
            emotion_scores[EmotionType.FEAR] += 0.2

        # 基于对象的情感分析
        person_objects = [obj for obj in objects if obj.object_type == ContentType.PERSON]
        if person_objects:
            # 有人物在场，情感可能更复杂
            emotion_scores[EmotionType.NEUTRAL] += 0.2
            emotion_scores[EmotionType.SURPRISED] += 0.1

        # 基于运动强度的情感分析
        motion_intensity = traditional_features.get('motion_features', {}).get('motion_intensity', 0)
        if motion_intensity > 0.5:
            emotion_scores[EmotionType.ANGRY] += 0.3
            emotion_scores[EmotionType.SURPRISED] += 0.2
        elif motion_intensity < 0.1:
            emotion_scores[EmotionType.NEUTRAL] += 0.3
            emotion_scores[EmotionType.SAD] += 0.1

        # 选择得分最高的情感
        if emotion_scores:
            return max(emotion_scores.items(), key=lambda x: x[1])[0]
        else:
            return EmotionType.NEUTRAL

    def _generate_keywords(self, traditional_features: Dict[str, Any],
                          objects: List[ContentObject], scene_type: str) -> List[str]:
        """生成关键词"""
        keywords = []

        # 添加场景类型关键词
        keywords.append(scene_type)

        # 添加对象关键词
        object_types = [obj.object_type.value for obj in objects]
        keywords.extend(object_types)

        # 基于特征的关键词
        brightness = traditional_features.get('brightness', 128)
        if brightness > 180:
            keywords.append("bright")
        elif brightness < 80:
            keywords.append("dark")

        contrast = traditional_features.get('contrast', 50)
        if contrast > 60:
            keywords.append("high_contrast")
        elif contrast < 30:
            keywords.append("low_contrast")

        motion_intensity = traditional_features.get('motion_features', {}).get('motion_intensity', 0)
        if motion_intensity > 0.5:
            keywords.append("dynamic")
        elif motion_intensity < 0.1:
            keywords.append("static")

        # 去重
        return list(set(keywords))

    def batch_analyze(self, frames: List[np.ndarray]) -> List[SceneAnalysis]:
        """批量分析帧"""
        analyses = []
        for frame in frames:
            analysis = self.analyze_frame(frame)
            analyses.append(analysis)
        return analyses

    def export_analysis_results(self, analyses: List[SceneAnalysis], output_path: str):
        """导出分析结果"""
        export_data = []
        for i, analysis in enumerate(analyses):
            data = {
                "frame_index": i,
                "scene_type": analysis.scene_type,
                "confidence": analysis.confidence,
                "aesthetic_score": analysis.aesthetic_score,
                "emotional_tone": analysis.emotional_tone.value,
                "keywords": analysis.keywords,
                "object_count": len(analysis.objects),
                "dominant_colors": [list(color) for color in analysis.dominant_colors]
            }
            export_data.append(data)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)


# 工具函数
def create_content_analyzer(use_deep_learning: bool = True) -> AIContentAnalyzer:
    """创建内容分析器"""
    return AIContentAnalyzer(use_deep_learning)


def analyze_video_content(video_path: str, sample_rate: int = 30) -> List[SceneAnalysis]:
    """分析视频内容"""
    analyzer = create_content_analyzer()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"无法打开视频文件: {video_path}")

    analyses = []
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 按采样率分析帧
        if frame_count % sample_rate == 0:
            analysis = analyzer.analyze_frame(frame)
            analyses.append(analysis)

        frame_count += 1

    cap.release()
    return analyses


def main():
    """主函数 - 用于测试"""
    # 测试传统特征提取
    analyzer = create_content_analyzer(use_deep_learning=False)

    # 创建测试图像
    test_frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)

    # 分析测试图像
    analysis = analyzer.analyze_frame(test_frame)
    print(f"场景类型: {analysis.scene_type}")
    print(f"美学评分: {analysis.aesthetic_score:.2f}")
    print(f"情感: {analysis.emotional_tone.value}")
    print(f"关键词: {analysis.keywords}")


if __name__ == "__main__":
    main()