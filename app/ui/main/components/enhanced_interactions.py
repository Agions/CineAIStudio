"""
增强交互组件 - 拖拽、视觉反馈和交互优化
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QSlider, QGroupBox, QFormLayout, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QDragEnterEvent, QDropEvent, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QDrag, QPainter, QColor, QPen
from typing import List, Dict, Any, Optional


class DragDropManager:
    """拖拽管理器 - 优化媒体拖拽到时间线/预览"""
    
    drag_started = pyqtSignal(str)  # 拖拽开始信号
    item_dropped = pyqtSignal(str, float)  # 物品放下信号 (file_path, timeline_position)
    
    def __init__(self, parent_widget: QWidget):
        self.parent = parent_widget
        self.parent.setAcceptDrops(True)
        self.drag_data: Optional[str] = None
        self.drop_zone_active = False
        self._setup_events()
    
    def _setup_events(self):
        """设置拖拽事件"""
        self.parent.dragEnterEvent = self._drag_enter_event
        self.parent.dropEvent = self._drop_event
        self.parent.dragMoveEvent = self._drag_move_event
        self.parent.dragLeaveEvent = self._drag_leave_event
    
    def _drag_enter_event(self, event: QDragEnterEvent):
        """拖拽进入"""
        if event.mimeData().hasUrls():
            self.drag_data = event.mimeData().urls()[0].toLocalFile()
            self.drop_zone_active = True
            self._show_drop_zone()
            event.acceptProposedAction()
            self.drag_started.emit(self.drag_data)
        else:
            event.ignore()
    
    def _drag_move_event(self, event):
        """拖拽移动"""
        if self.drop_zone_active:
            event.acceptProposedAction()
    
    def _drag_leave_event(self, event):
        """拖拽离开"""
        self.drop_zone_active = False
        self._hide_drop_zone()
        event.accept()
    
    def _drop_event(self, event: QDropEvent):
        """拖拽放下"""
        if self.drag_data:
            # 计算时间线位置 (假设时间线宽度对应视频时长)
            timeline_pos = event.position().x() / self.parent.width() * 100.0  # 百分比
            self.item_dropped.emit(self.drag_data, timeline_pos)
            self.drop_zone_active = False
            self._hide_drop_zone()
            event.acceptProposedAction()
    
    def _show_drop_zone(self):
        """显示放下区域视觉反馈"""
        # 添加阴影效果或高亮
        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(10)
        effect.setColor(QColor(0, 150, 255, 100))
        effect.setOffset(0, 0)
        self.parent.setGraphicsEffect(effect)
    
    def _hide_drop_zone(self):
        """隐藏放下区域"""
        self.parent.setGraphicsEffect(None)


class VisualFeedbackWidget(QFrame):
    """视觉反馈组件 - 拖拽高亮、动画反馈"""
    
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background: rgba(0, 150, 255, 50);
                border: 2px dashed #00A8FF;
                border-radius: 8px;
            }
        """)
        self.hide()
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._animate_feedback)
        self.is_animating = False
    
    def show_drag_feedback(self):
        """显示拖拽反馈"""
        self.show()
        self.is_animating = True
        self.animation_timer.start(100)  # 动画间隔
    
    def hide_drag_feedback(self):
        """隐藏拖拽反馈"""
        self.is_animating = False
        self.animation_timer.stop()
        self.hide()
    
    def _animate_feedback(self):
        """动画反馈"""
        if self.is_animating:
            # 简单脉冲动画：改变透明度
            current_style = self.styleSheet()
            # 可以扩展为更复杂的动画
            pass


class QuickAIConfig(QWidget):
    """一键AI配置 - 快速AI设置面板"""
    
    config_changed = pyqtSignal(dict)  # 配置变化信号
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.current_config = {
            'model': 'spark-large-v3.5',
            'quality': 'medium',
            'language': 'zh-CN',
            'auto_subtitle': True
        }
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # 标题
        title = QLabel("🚀 一键AI配置")
        title.setStyleSheet("font-weight: bold; color: #00A8FF; font-size: 14px;")
        layout.addWidget(title)
        
        # 模型选择
        model_group = QGroupBox("AI模型")
        model_layout = QFormLayout(model_group)
        self.model_combo = QComboBox()
        self.model_combo.addItems(['spark-large-v3.5', 'qwen-max', 'glm-4', 'wenxin-2.0'])
        self.model_combo.setCurrentText(self.current_config['model'])
        self.model_combo.currentTextChanged.connect(self._update_model)
        model_layout.addRow(self.model_combo)
        layout.addWidget(model_group)
        
        # 质量设置
        quality_group = QGroupBox("质量设置")
        quality_layout = QFormLayout(quality_group)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(['low', 'medium', 'high', 'ultra'])
        self.quality_combo.setCurrentText(self.current_config['quality'])
        self.quality_combo.currentTextChanged.connect(self._update_quality)
        quality_layout.addRow(self.quality_combo)
        layout.addWidget(quality_group)
        
        # 语言设置
        lang_group = QGroupBox("语言设置")
        lang_layout = QFormLayout(lang_group)
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(['zh-CN', 'en-US', 'zh-TW'])
        self.lang_combo.setCurrentText(self.current_config['language'])
        self.lang_combo.currentTextChanged.connect(self._update_language)
        lang_layout.addRow(self.lang_combo)
        layout.addWidget(lang_group)
        
        # 自动字幕开关
        self.auto_subtitle_cb = QCheckBox("自动生成字幕")
        self.auto_subtitle_cb.setChecked(self.current_config['auto_subtitle'])
        self.auto_subtitle_cb.stateChanged.connect(self._update_auto_subtitle)
        layout.addWidget(self.auto_subtitle_cb)
        
        # 应用按钮
        apply_btn = QPushButton("应用配置")
        apply_btn.setStyleSheet("""
            QPushButton {
                background: #00A8FF;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #0090E6;
            }
        """)
        apply_btn.clicked.connect(self._apply_config)
        layout.addWidget(apply_btn)
        
        layout.addStretch()
    
    def _update_model(self, model: str):
        self.current_config['model'] = model
    
    def _update_quality(self, quality: str):
        self.current_config['quality'] = quality
    
    def _update_language(self, lang: str):
        self.current_config['language'] = lang
    
    def _update_auto_subtitle(self, state: int):
        self.current_config['auto_subtitle'] = bool(state)
    
    def _apply_config(self):
        """应用配置"""
        self.config_changed.emit(self.current_config)
    
    def get_config(self) -> dict:
        """获取当前配置"""
        return self.current_config.copy()
    
    def set_config(self, config: dict):
        """设置配置"""
        self.current_config.update(config)
        self.model_combo.setCurrentText(config.get('model', 'spark-large-v3.5'))
        self.quality_combo.setCurrentText(config.get('quality', 'medium'))
        self.lang_combo.setCurrentText(config.get('language', 'zh-CN'))
        self.auto_subtitle_cb.setChecked(config.get('auto_subtitle', True))