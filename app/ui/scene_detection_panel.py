#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QGroupBox, QProgressBar,
    QSlider, QFormLayout, QDoubleSpinBox, QTextEdit, QFrame,
    QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from app.core.video_manager import VideoClip
from app.ai.scene_detector import SceneDetector, SceneInfo


class SceneListWidget(QListWidget):
    """场景列表控件"""
    
    scene_selected = pyqtSignal(SceneInfo)
    scene_play_requested = pyqtSignal(SceneInfo)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        
        # 连接信号
        self.itemClicked.connect(self._on_item_clicked)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
    
    def add_scene(self, scene: SceneInfo):
        """添加场景到列表"""
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, scene)
        
        # 设置显示文本
        display_text = f"{scene.description}\n"
        display_text += f"类型: {scene.scene_type} | 置信度: {scene.confidence:.2f}"
        
        item.setText(display_text)
        
        # 根据场景类型设置颜色
        if scene.scene_type == "high_energy":
            item.setBackground(Qt.GlobalColor.lightGreen)
        elif scene.scene_type == "action":
            item.setBackground(Qt.GlobalColor.yellow)
        elif scene.scene_type == "emotional":
            item.setBackground(Qt.GlobalColor.lightBlue)
        elif scene.scene_type == "dialogue":
            item.setBackground(Qt.GlobalColor.lightGray)
        
        self.addItem(item)
    
    def clear_scenes(self):
        """清空场景列表"""
        self.clear()
    
    def _on_item_clicked(self, item):
        """场景点击"""
        scene = item.data(Qt.ItemDataRole.UserRole)
        if scene:
            self.scene_selected.emit(scene)
    
    def _on_item_double_clicked(self, item):
        """场景双击"""
        scene = item.data(Qt.ItemDataRole.UserRole)
        if scene:
            self.scene_play_requested.emit(scene)


class SceneDetectionPanel(QWidget):
    """场景检测面板"""
    
    scene_detected = pyqtSignal(SceneInfo)
    detection_completed = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.scene_detector = SceneDetector()
        self.current_video = None
        self.detected_scenes = []
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("智能场景检测")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 检测控制区域
        control_group = QGroupBox("检测控制")
        control_layout = QVBoxLayout(control_group)
        
        # 视频选择
        video_layout = QHBoxLayout()
        video_layout.addWidget(QLabel("当前视频:"))
        self.video_label = QLabel("未选择视频")
        self.video_label.setStyleSheet("color: #666;")
        video_layout.addWidget(self.video_label)
        video_layout.addStretch()
        control_layout.addLayout(video_layout)
        
        # 检测参数
        params_group = QGroupBox("检测参数")
        params_layout = QFormLayout(params_group)
        
        # 场景变化阈值
        self.scene_threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.scene_threshold_slider.setRange(10, 90)
        self.scene_threshold_slider.setValue(50)
        self.scene_threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.scene_threshold_slider.setTickInterval(10)
        params_layout.addRow("场景变化阈值:", self.scene_threshold_slider)
        
        # 运动检测阈值
        self.motion_threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.motion_threshold_slider.setRange(10, 90)
        self.motion_threshold_slider.setValue(30)
        self.motion_threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.motion_threshold_slider.setTickInterval(10)
        params_layout.addRow("运动检测阈值:", self.motion_threshold_slider)
        
        # 最小场景时长
        self.min_duration_spin = QDoubleSpinBox()
        self.min_duration_spin.setRange(0.5, 10.0)
        self.min_duration_spin.setValue(1.0)
        self.min_duration_spin.setSuffix(" 秒")
        params_layout.addRow("最小场景时长:", self.min_duration_spin)
        
        control_layout.addWidget(params_group)
        
        # 检测按钮
        button_layout = QHBoxLayout()
        
        self.detect_all_btn = QPushButton("检测所有场景")
        self.detect_all_btn.clicked.connect(self._detect_all_scenes)
        button_layout.addWidget(self.detect_all_btn)
        
        self.detect_highlights_btn = QPushButton("检测精彩片段")
        self.detect_highlights_btn.clicked.connect(self._detect_highlights)
        button_layout.addWidget(self.detect_highlights_btn)
        
        self.detect_emotional_btn = QPushButton("检测情感时刻")
        self.detect_emotional_btn.clicked.connect(self._detect_emotional_moments)
        button_layout.addWidget(self.detect_emotional_btn)
        
        control_layout.addLayout(button_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        layout.addWidget(control_group)
        
        # 结果显示区域
        results_group = QGroupBox("检测结果")
        results_layout = QVBoxLayout(results_group)
        
        # 统计信息
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("场景数量: 0")
        stats_layout.addWidget(self.stats_label)
        
        # 筛选器
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("筛选:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "全部场景", "高能场景", "动作场景", "情感场景", 
            "对话场景", "安静场景", "转场场景"
        ])
        self.filter_combo.currentTextChanged.connect(self._filter_scenes)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()
        
        stats_layout.addLayout(filter_layout)
        results_layout.addLayout(stats_layout)
        
        # 场景列表
        self.scene_list = SceneListWidget()
        results_layout.addWidget(self.scene_list)
        
        # 操作按钮
        action_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("清空结果")
        self.clear_btn.clicked.connect(self._clear_results)
        action_layout.addWidget(self.clear_btn)
        
        self.export_btn = QPushButton("导出场景")
        self.export_btn.clicked.connect(self._export_scenes)
        action_layout.addWidget(self.export_btn)
        
        action_layout.addStretch()
        
        results_layout.addLayout(action_layout)
        
        layout.addWidget(results_group)
    
    def _connect_signals(self):
        """连接信号"""
        self.scene_detector.scene_detected.connect(self._on_scene_detected)
        self.scene_detector.detection_progress.connect(self._on_detection_progress)
        self.scene_detector.detection_completed.connect(self._on_detection_completed)
        
        self.scene_list.scene_selected.connect(self._on_scene_selected)
        self.scene_list.scene_play_requested.connect(self._on_scene_play_requested)
    
    def set_video(self, video: VideoClip):
        """设置当前视频"""
        self.current_video = video
        if video:
            self.video_label.setText(video.name)
            self.video_label.setStyleSheet("color: black;")
        else:
            self.video_label.setText("未选择视频")
            self.video_label.setStyleSheet("color: #666;")
        
        # 清空之前的结果
        self._clear_results()
    
    def _detect_all_scenes(self):
        """检测所有场景"""
        if not self.current_video:
            QMessageBox.warning(self, "警告", "请先选择一个视频文件")
            return
        
        self._start_detection("all")
    
    def _detect_highlights(self):
        """检测精彩片段"""
        if not self.current_video:
            QMessageBox.warning(self, "警告", "请先选择一个视频文件")
            return
        
        self._start_detection("highlights")
    
    def _detect_emotional_moments(self):
        """检测情感时刻"""
        if not self.current_video:
            QMessageBox.warning(self, "警告", "请先选择一个视频文件")
            return
        
        self._start_detection("emotional")
    
    def _start_detection(self, detection_type: str):
        """开始检测"""
        # 更新检测参数
        self.scene_detector.set_detection_parameters(
            scene_change_threshold=self.scene_threshold_slider.value() / 100.0,
            motion_threshold=self.motion_threshold_slider.value() / 100.0,
            min_scene_duration=self.min_duration_spin.value()
        )
        
        # 禁用按钮
        self.detect_all_btn.setEnabled(False)
        self.detect_highlights_btn.setEnabled(False)
        self.detect_emotional_btn.setEnabled(False)
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 清空之前的结果
        self._clear_results()
        
        # 异步执行检测
        if detection_type == "all":
            asyncio.create_task(self.scene_detector.detect_scenes(self.current_video))
        elif detection_type == "highlights":
            asyncio.create_task(self.scene_detector.detect_highlights(self.current_video))
        elif detection_type == "emotional":
            asyncio.create_task(self.scene_detector.detect_emotional_moments(self.current_video))
    
    def _on_scene_detected(self, scene: SceneInfo):
        """场景检测回调"""
        self.detected_scenes.append(scene)
        self.scene_list.add_scene(scene)
        self._update_stats()
        self.scene_detected.emit(scene)
    
    def _on_detection_progress(self, progress: int):
        """检测进度回调"""
        self.progress_bar.setValue(progress)
    
    def _on_detection_completed(self, scenes: list):
        """检测完成回调"""
        # 恢复按钮
        self.detect_all_btn.setEnabled(True)
        self.detect_highlights_btn.setEnabled(True)
        self.detect_emotional_btn.setEnabled(True)
        
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        
        self.detection_completed.emit(scenes)
        
        if scenes:
            QMessageBox.information(self, "完成", f"场景检测完成，共检测到 {len(scenes)} 个场景")
        else:
            QMessageBox.information(self, "完成", "场景检测完成，未检测到场景")
    
    def _on_scene_selected(self, scene: SceneInfo):
        """场景选中回调"""
        # 这里可以显示场景详细信息
        pass
    
    def _on_scene_play_requested(self, scene: SceneInfo):
        """场景播放请求回调"""
        # 这里可以跳转到视频播放器的指定时间
        QMessageBox.information(self, "播放", f"播放场景: {scene.description}")
    
    def _filter_scenes(self, filter_text: str):
        """筛选场景"""
        filter_map = {
            "全部场景": None,
            "高能场景": "high_energy",
            "动作场景": "action",
            "情感场景": "emotional",
            "对话场景": "dialogue",
            "安静场景": "quiet",
            "转场场景": "transition"
        }
        
        scene_type = filter_map.get(filter_text)
        
        # 重新填充列表
        self.scene_list.clear_scenes()
        for scene in self.detected_scenes:
            if scene_type is None or scene.scene_type == scene_type:
                self.scene_list.add_scene(scene)
        
        self._update_stats()
    
    def _update_stats(self):
        """更新统计信息"""
        visible_count = self.scene_list.count()
        total_count = len(self.detected_scenes)
        
        if visible_count == total_count:
            self.stats_label.setText(f"场景数量: {total_count}")
        else:
            self.stats_label.setText(f"场景数量: {visible_count}/{total_count}")
    
    def _clear_results(self):
        """清空结果"""
        self.detected_scenes.clear()
        self.scene_list.clear_scenes()
        self._update_stats()
    
    def _export_scenes(self):
        """导出场景"""
        if not self.detected_scenes:
            QMessageBox.warning(self, "警告", "没有可导出的场景")
            return
        
        # 这里可以实现导出功能
        QMessageBox.information(self, "导出", "场景导出功能正在开发中...")
