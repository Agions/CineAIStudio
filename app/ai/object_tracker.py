#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI驱动的对象跟踪和遮罩系统
提供多目标跟踪、智能遮罩生成、对象识别、轨迹分析等功能
"""

import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import threading
import queue
import time
from collections import defaultdict, deque
import logging
import json
from concurrent.futures import ThreadPoolExecutor

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


class TrackingMethod(Enum):
    """跟踪方法"""
    KCF = "kcf"                         # Kernelized Correlation Filters
    CSRT = "csrt"                       # Channel and Spatial Reliability Tracking
    MOSSE = "mosse"                     # Minimum Output Sum of Squared Error
    BOOSTING = "boosting"               # Boosting Tracker
    MIL = "mil"                         # Multiple Instance Learning
    TLD = "tld"                         # Tracking, Learning and Detection
    MEDIANFLOW = "medianflow"           # Median Flow Tracker
    GOTURN = "goturn"                   # Generic Object Tracking Using Regression Networks
    DEEPSORT = "deepsort"               # DeepSORT Tracking
    FAIRMOT = "fairmot"                 # FairMOT Multi-Object Tracking


class ObjectType(Enum):
    """对象类型"""
    PERSON = "person"                   # 人物
    VEHICLE = "vehicle"                 # 车辆
    ANIMAL = "animal"                   # 动物
    OBJECT = "object"                   # 物体
    FACE = "face"                       # 人脸
    LICENSE_PLATE = "license_plate"      # 车牌
    TEXT = "text"                       # 文本
    CUSTOM = "custom"                    # 自定义


@dataclass
class BoundingBox:
    """边界框"""
    x: int
    y: int
    width: int
    height: int
    confidence: float = 1.0

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def area(self) -> int:
        return self.width * self.height

    def to_tuple(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)

    def to_cv2_rect(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)


@dataclass
class TrackedObject:
    """跟踪对象"""
    object_id: int
    object_type: ObjectType
    bbox: BoundingBox
    trajectory: List[Tuple[int, int]]
    velocity: Tuple[float, float]
    confidence: float
    age: int
    last_seen: float
    attributes: Dict[str, Any]
    mask: Optional[np.ndarray] = None

    def update_position(self, new_bbox: BoundingBox):
        """更新位置"""
        self.bbox = new_bbox
        self.trajectory.append(new_bbox.center)

        # 保持轨迹长度
        if len(self.trajectory) > 100:
            self.trajectory.pop(0)

        # 计算速度
        if len(self.trajectory) >= 2:
            prev_pos = self.trajectory[-2]
            curr_pos = self.trajectory[-1]
            dt = 1.0  # 假设时间间隔为1帧
            self.velocity = (
                (curr_pos[0] - prev_pos[0]) / dt,
                (curr_pos[1] - prev_pos[1]) / dt
            )

    def is_alive(self, max_age: int = 30) -> bool:
        """检查对象是否还活着"""
        return self.age <= max_age


@dataclass
class TrackingResult:
    """跟踪结果"""
    frame_number: int
    timestamp: float
    tracked_objects: List[TrackedObject]
    processing_time: float
    fps: float


class ObjectDetector:
    """对象检测器"""

    def __init__(self, detector_type: str = "yolo"):
        self.detector_type = detector_type
        self.detector = self._create_detector()
        self.class_names = self._load_class_names()

    def _create_detector(self):
        """创建检测器"""
        if self.detector_type == "yolo":
            return self._create_yolo_detector()
        elif self.detector_type == "hog":
            return cv2.HOGDescriptor()
        elif self.detector_type == "haar":
            return self._create_haar_cascade()
        else:
            return self._create_yolo_detector()

    def _create_yolo_detector(self):
        """创建YOLO检测器"""
        try:
            # 加载YOLO模型
            net = cv2.dnn.readNet("yolov4.weights", "yolov4.cfg")
            with open("coco.names", "r") as f:
                self.class_names = [line.strip() for line in f.readlines()]
            return net
        except Exception:
            # 如果YOLO不可用，使用HOG检测器
            print("YOLO模型不可用，使用HOG检测器")
            hog = cv2.HOGDescriptor()
            hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            return hog

    def _create_haar_cascade(self):
        """创建Haar级联检测器"""
        try:
            return cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        except Exception:
            return None

    def _load_class_names(self) -> List[str]:
        """加载类别名称"""
        if hasattr(self, 'class_names'):
            return self.class_names

        # 默认类别名称
        return ["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
                "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
                "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
                "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
                "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
                "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
                "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
                "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
                "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
                "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
                "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier",
                "toothbrush"]

    def detect_objects(self, frame: np.ndarray) -> List[Tuple[BoundingBox, ObjectType, float]]:
        """检测对象"""
        if self.detector_type == "yolo":
            return self._detect_with_yolo(frame)
        elif self.detector_type == "hog":
            return self._detect_with_hog(frame)
        elif self.detector_type == "haar":
            return self._detect_with_haar(frame)
        else:
            return []

    def _detect_with_yolo(self, frame: np.ndarray) -> List[Tuple[BoundingBox, ObjectType, float]]:
        """使用YOLO检测对象"""
        try:
            height, width = frame.shape[:2]

            # 创建输入blob
            blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
            self.detector.setInput(blob)
            outputs = self.detector.forward()

            # 处理检测结果
            detections = []
            for output in outputs:
                for detection in output:
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]

                    if confidence > 0.5:
                        # 获取边界框坐标
                        center_x = int(detection[0] * width)
                        center_y = int(detection[1] * height)
                        w = int(detection[2] * width)
                        h = int(detection[3] * height)

                        x = int(center_x - w / 2)
                        y = int(center_y - h / 2)

                        bbox = BoundingBox(x, y, w, h, confidence)
                        obj_type = self._map_class_to_object_type(class_id)
                        detections.append((bbox, obj_type, confidence))

            return detections

        except Exception as e:
            logging.error(f"YOLO检测失败: {e}")
            return []

    def _detect_with_hog(self, frame: np.ndarray) -> List[Tuple[BoundingBox, ObjectType, float]]:
        """使用HOG检测对象"""
        try:
            (rects, weights) = self.detector.detectMultiScale(
                frame, winStride=(8, 8), padding=(32, 32), scale=1.05
            )

            detections = []
            for (x, y, w, h), weight in zip(rects, weights):
                if weight > 0.5:  # 置信度阈值
                    bbox = BoundingBox(x, y, w, h, float(weight))
                    detections.append((bbox, ObjectType.PERSON, float(weight)))

            return detections

        except Exception as e:
            logging.error(f"HOG检测失败: {e}")
            return []

    def _detect_with_haar(self, frame: np.ndarray) -> List[Tuple[BoundingBox, ObjectType, float]]:
        """使用Haar级联检测对象"""
        if self.detector is None:
            return []

        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.detector.detectMultiScale(gray, 1.3, 5)

            detections = []
            for (x, y, w, h) in faces:
                bbox = BoundingBox(x, y, w, h, 0.8)  # 固定置信度
                detections.append((bbox, ObjectType.FACE, 0.8))

            return detections

        except Exception as e:
            logging.error(f"Haar检测失败: {e}")
            return []

    def _map_class_to_object_type(self, class_id: int) -> ObjectType:
        """映射类别ID到对象类型"""
        if class_id < len(self.class_names):
            class_name = self.class_names[class_id]
            if class_name == "person":
                return ObjectType.PERSON
            elif class_name in ["car", "truck", "bus", "motorcycle", "bicycle"]:
                return ObjectType.VEHICLE
            elif class_name in ["cat", "dog", "horse", "sheep", "cow", "elephant", "bear"]:
                return ObjectType.ANIMAL
            else:
                return ObjectType.OBJECT
        return ObjectType.OBJECT


class ObjectTracker:
    """对象跟踪器"""

    def __init__(self, tracking_method: TrackingMethod = TrackingMethod.CSRT):
        self.tracking_method = tracking_method
        self.trackers = {}
        self.next_id = 1
        self.max_disappeared = 30

    def initialize_tracker(self, frame: np.ndarray, bbox: BoundingBox, object_id: int = None) -> int:
        """初始化跟踪器"""
        if object_id is None:
            object_id = self.next_id
            self.next_id += 1

        try:
            tracker = self._create_tracker()
            rect = bbox.to_cv2_rect()
            success = tracker.init(frame, rect)

            if success:
                self.trackers[object_id] = {
                    'tracker': tracker,
                    'bbox': bbox,
                    'trajectory': [bbox.center],
                    'last_seen': time.time(),
                    'age': 0
                }
                return object_id
            else:
                return -1

        except Exception as e:
            logging.error(f"初始化跟踪器失败: {e}")
            return -1

    def _create_tracker(self):
        """创建跟踪器"""
        if self.tracking_method == TrackingMethod.KCF:
            return cv2.legacy.TrackerKCF_create()
        elif self.tracking_method == TrackingMethod.CSRT:
            return cv2.legacy.TrackerCSRT_create()
        elif self.tracking_method == TrackingMethod.MOSSE:
            return cv2.legacy.TrackerMOSSE_create()
        elif self.tracking_method == TrackingMethod.BOOSTING:
            return cv2.legacy.TrackerBoosting_create()
        elif self.tracking_method == TrackingMethod.MIL:
            return cv2.legacy.TrackerMIL_create()
        else:
            return cv2.legacy.TrackerCSRT_create()

    def update_trackers(self, frame: np.ndarray) -> Dict[int, BoundingBox]:
        """更新所有跟踪器"""
        results = {}
        disappeared = []

        for object_id, tracker_data in self.trackers.items():
            tracker = tracker_data['tracker']

            try:
                success, bbox = tracker.update(frame)

                if success:
                    x, y, w, h = [int(v) for v in bbox]
                    new_bbox = BoundingBox(x, y, w, h)

                    # 更新跟踪器数据
                    tracker_data['bbox'] = new_bbox
                    tracker_data['trajectory'].append(new_bbox.center)
                    tracker_data['last_seen'] = time.time()
                    tracker_data['age'] += 1

                    # 限制轨迹长度
                    if len(tracker_data['trajectory']) > 100:
                        tracker_data['trajectory'].pop(0)

                    results[object_id] = new_bbox
                else:
                    # 跟踪失败
                    tracker_data['age'] += 1
                    if tracker_data['age'] > self.max_disappeared:
                        disappeared.append(object_id)

            except Exception as e:
                logging.error(f"更新跟踪器 {object_id} 失败: {e}")
                disappeared.append(object_id)

        # 移除消失的跟踪器
        for object_id in disappeared:
            del self.trackers[object_id]

        return results

    def get_trajectories(self) -> Dict[int, List[Tuple[int, int]]]:
        """获取所有轨迹"""
        return {object_id: data['trajectory'] for object_id, data in self.trackers.items()}

    def remove_tracker(self, object_id: int):
        """移除跟踪器"""
        if object_id in self.trackers:
            del self.trackers[object_id]

    def clear_all(self):
        """清除所有跟踪器"""
        self.trackers.clear()
        self.next_id = 1


class MaskGenerator:
    """遮罩生成器"""

    def __init__(self):
        self.segmentator = None
        self._init_segmentator()

    def _init_segmentator(self):
        """初始化分割器"""
        try:
            # 尝试加载DeepLab分割模型
            self.segmentator = cv2.dnn.readNetFromTensorflow(
                "deeplabv3_mnv2_tf.pb", "deeplabv3_mnv2_pbtxt"
            )
        except Exception:
            # 如果DeepLab不可用，使用传统方法
            self.segmentator = None

    def generate_mask(self, frame: np.ndarray, bbox: BoundingBox) -> np.ndarray:
        """生成对象遮罩"""
        if self.segmentator is not None:
            return self._generate_mask_with_segmentation(frame, bbox)
        else:
            return self._generate_mask_with_traditional(frame, bbox)

    def _generate_mask_with_segmentation(self, frame: np.ndarray, bbox: BoundingBox) -> np.ndarray:
        """使用分割生成遮罩"""
        try:
            height, width = frame.shape[:2]

            # 创建blob
            blob = cv2.dnn.blobFromImage(frame, 1/255.0, (513, 513), (0, 0, 0), swapRB=True, crop=False)
            self.segmentator.setInput(blob)
            output = self.segmentator.forward()

            # 获取分割结果
            mask = np.squeeze(output)
            mask = cv2.resize(mask, (width, height))

            # 在边界框区域内提取遮罩
            x, y, w, h = bbox.to_cv2_rect()
            roi_mask = mask[y:y+h, x:x+w]

            # 二值化遮罩
            roi_mask = (roi_mask > 0.5).astype(np.uint8) * 255

            # 创建完整尺寸的遮罩
            full_mask = np.zeros((height, width), dtype=np.uint8)
            full_mask[y:y+h, x:x+w] = roi_mask

            return full_mask

        except Exception as e:
            logging.error(f"分割遮罩生成失败: {e}")
            return self._generate_mask_with_traditional(frame, bbox)

    def _generate_mask_with_traditional(self, frame: np.ndarray, bbox: BoundingBox) -> np.ndarray:
        """使用传统方法生成遮罩"""
        height, width = frame.shape[:2]
        x, y, w, h = bbox.to_cv2_rect()

        # 提取ROI
        roi = frame[y:y+h, x:x+w]

        # 转换为HSV色彩空间
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # 使用GrabCut算法
        mask = np.zeros(roi.shape[:2], np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)

        # 定义矩形区域
        rect = (1, 1, w-2, h-2)

        # 运行GrabCut
        cv2.grabCut(roi, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)

        # 获取前景遮罩
        mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')

        # 形态学操作改善遮罩
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernel)
        mask2 = cv2.morphologyEx(mask2, cv2.MORPH_OPEN, kernel)

        # 创建完整尺寸的遮罩
        full_mask = np.zeros((height, width), dtype=np.uint8)
        full_mask[y:y+h, x:x+w] = mask2 * 255

        return full_mask


class AIObjectTracker(QObject):
    """AI对象跟踪器主类"""

    # 信号定义
    tracking_started = Signal(str)  # 跟踪开始
    tracking_updated = Signal(TrackingResult)  # 跟踪更新
    tracking_stopped = Signal()  # 跟踪停止
    tracking_error = Signal(str)  # 跟踪错误
    object_detected = Signal(TrackedObject)  # 对象检测
    object_lost = Signal(int)  # 对象丢失

    def __init__(self, detection_method: str = "yolo", tracking_method: TrackingMethod = TrackingMethod.CSRT):
        super().__init__()
        self.detector = ObjectDetector(detection_method)
        self.tracker = ObjectTracker(tracking_method)
        self.mask_generator = MaskGenerator()

        self.is_tracking = False
        self.tracking_thread = None
        self.frame_queue = queue.Queue(maxsize=10)

        self.tracked_objects = {}
        self.object_type_mapping = {}
        self.next_object_id = 1

    def start_tracking(self, video_source: Union[str, int] = 0):
        """开始跟踪"""
        if self.is_tracking:
            self.tracking_error.emit("正在跟踪中，请先停止当前跟踪")
            return

        self.is_tracking = True
        self.tracking_started.emit(str(video_source))

        # 创建跟踪线程
        self.tracking_thread = TrackingThread(
            self, video_source, self.detector, self.tracker, self.mask_generator
        )
        self.tracking_thread.tracking_updated.connect(self.tracking_updated.emit)
        self.tracking_thread.object_detected.connect(self.object_detected.emit)
        self.tracking_thread.object_lost.connect(self.object_lost.emit)
        self.tracking_thread.error_occurred.connect(self.tracking_error.emit)
        self.tracking_thread.start()

    def stop_tracking(self):
        """停止跟踪"""
        if self.tracking_thread and self.tracking_thread.isRunning():
            self.tracking_thread.stop()
            self.tracking_thread.wait()
            self.is_tracking = False
            self.tracking_stopped.emit()

    def add_object_to_track(self, frame: np.ndarray, bbox: BoundingBox, object_type: ObjectType = ObjectType.CUSTOM):
        """添加对象到跟踪"""
        try:
            object_id = self.tracker.initialize_tracker(frame, bbox)
            if object_id != -1:
                self.object_type_mapping[object_id] = object_type

                tracked_object = TrackedObject(
                    object_id=object_id,
                    object_type=object_type,
                    bbox=bbox,
                    trajectory=[bbox.center],
                    velocity=(0, 0),
                    confidence=1.0,
                    age=0,
                    last_seen=time.time(),
                    attributes={}
                )

                self.tracked_objects[object_id] = tracked_object
                self.object_detected.emit(tracked_object)

        except Exception as e:
            self.tracking_error.emit(f"添加跟踪对象失败: {str(e)}")

    def remove_object_from_track(self, object_id: int):
        """从跟踪中移除对象"""
        if object_id in self.tracked_objects:
            del self.tracked_objects[object_id]
            self.tracker.remove_tracker(object_id)
            if object_id in self.object_type_mapping:
                del self.object_type_mapping[object_id]

    def get_tracked_objects(self) -> Dict[int, TrackedObject]:
        """获取跟踪对象"""
        return self.tracked_objects.copy()

    def get_object_trajectory(self, object_id: int) -> List[Tuple[int, int]]:
        """获取对象轨迹"""
        if object_id in self.tracked_objects:
            return self.tracked_objects[object_id].trajectory
        return []

    def export_tracking_data(self, output_path: str):
        """导出跟踪数据"""
        export_data = {
            "tracked_objects": {},
            "trajectories": {}
        }

        for object_id, obj in self.tracked_objects.items():
            export_data["tracked_objects"][object_id] = {
                "object_type": obj.object_type.value,
                "bbox": obj.bbox.to_tuple(),
                "confidence": obj.confidence,
                "age": obj.age,
                "velocity": obj.velocity,
                "attributes": obj.attributes
            }
            export_data["trajectories"][object_id] = obj.trajectory

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

    def clear_all_tracking(self):
        """清除所有跟踪"""
        self.tracked_objects.clear()
        self.object_type_mapping.clear()
        self.tracker.clear_all()

    def process_frame(self, frame: np.ndarray) -> TrackingResult:
        """处理单帧"""
        start_time = time.time()

        # 检测对象
        detections = self.detector.detect_objects(frame)

        # 更新跟踪器
        tracking_results = self.tracker.update_trackers(frame)

        # 更新跟踪对象
        current_time = time.time()
        for object_id, bbox in tracking_results.items():
            if object_id in self.tracked_objects:
                self.tracked_objects[object_id].update_position(bbox)
                self.tracked_objects[object_id].last_seen = current_time

        # 生成遮罩
        for object_id, obj in self.tracked_objects.items():
            if obj.mask is None:
                obj.mask = self.mask_generator.generate_mask(frame, obj.bbox)

        # 检查丢失的对象
        lost_objects = []
        for object_id, obj in list(self.tracked_objects.items()):
            if not obj.is_alive():
                lost_objects.append(object_id)
                del self.tracked_objects[object_id]

        # 发送丢失信号
        for object_id in lost_objects:
            self.object_lost.emit(object_id)

        processing_time = time.time() - start_time
        fps = 1.0 / processing_time if processing_time > 0 else 0

        result = TrackingResult(
            frame_number=0,  # 需要从外部传入
            timestamp=current_time,
            tracked_objects=list(self.tracked_objects.values()),
            processing_time=processing_time,
            fps=fps
        )

        return result


class TrackingThread(QThread):
    """跟踪线程"""

    tracking_updated = Signal(TrackingResult)
    object_detected = Signal(TrackedObject)
    object_lost = Signal(int)
    error_occurred = Signal(str)

    def __init__(self, tracker: AIObjectTracker, video_source: Union[str, int],
                 detector: ObjectDetector, object_tracker: ObjectTracker,
                 mask_generator: MaskGenerator):
        super().__init__()
        self.tracker = tracker
        self.video_source = video_source
        self.detector = detector
        self.object_tracker = object_tracker
        self.mask_generator = mask_generator
        self._is_running = True

    def run(self):
        """运行跟踪"""
        try:
            cap = cv2.VideoCapture(self.video_source)
            if not cap.isOpened():
                self.error_occurred.emit(f"无法打开视频源: {self.video_source}")
                return

            frame_number = 0
            while cap.isOpened() and self._is_running:
                ret, frame = cap.read()
                if not ret:
                    break

                # 处理帧
                result = self.tracker.process_frame(frame)
                result.frame_number = frame_number

                self.tracking_updated.emit(result)
                frame_number += 1

                # 控制帧率
                self.msleep(30)  # 约30 FPS

            cap.release()

        except Exception as e:
            self.error_occurred.emit(f"跟踪过程中发生错误: {str(e)}")

    def stop(self):
        """停止线程"""
        self._is_running = False


# 工具函数
def create_object_tracker(detection_method: str = "yolo",
                        tracking_method: TrackingMethod = TrackingMethod.CSRT) -> AIObjectTracker:
    """创建对象跟踪器"""
    return AIObjectTracker(detection_method, tracking_method)


def quick_track_objects(video_path: str, output_path: str = None) -> List[TrackingResult]:
    """快速对象跟踪（同步版本）"""
    tracker = create_object_tracker()
    results = []

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"无法打开视频文件: {video_path}")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        result = tracker.process_frame(frame)
        results.append(result)

    cap.release()

    if output_path:
        tracker.export_tracking_data(output_path)

    return results


def main():
    """主函数 - 用于测试"""
    # 创建对象跟踪器
    tracker = create_object_tracker()

    # 测试跟踪功能
    print("AI对象跟踪器创建成功")
    print(f"检测方法: {tracker.detector.detector_type}")
    print(f"跟踪方法: {tracker.tracker.tracking_method.value}")


if __name__ == "__main__":
    main()