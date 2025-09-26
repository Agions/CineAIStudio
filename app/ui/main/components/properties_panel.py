"""
属性面板组件 - 集成特效系统
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSlider,
    QGroupBox, QFormLayout, QPushButton, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt

from app.effects.effect_engine import effect_engine, EffectType, TransitionType
from PyQt6.QtCore import pyqtSignal


class PropertiesPanel(QWidget):
    """属性面板组件 - 支持特效、转场和多机位"""

    # 信号
    multicam_sync_requested = pyqtSignal()
    angle_switched = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.effect_engine = effect_engine
        self.current_effect = None
        self.current_transition = None
        self.current_angle = "wide"
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 工具箱
        from PyQt6.QtWidgets import QToolBox
        self.toolbox = QToolBox()
        self.toolbox.setStyleSheet("""
            QToolBox::tab {
                background: #2A2A2A;
                color: #B0B0B0;
                padding: 8px;
                border: 1px solid #3A3A3A;
            }
            QToolBox::tab:selected {
                background: #404040;
                color: #FFFFFF;
                border-bottom: 2px solid #00A8FF;
            }
        """)

        # 现有视频属性页（简化）
        self.video_props_page = QWidget()
        video_props_layout = QVBoxLayout(self.video_props_page)
        info_label = QLabel("视频属性面板\n分辨率: 1920x1080\n时长: 00:05:30\n帧率: 30 fps")
        info_label.setStyleSheet("color: #B0B0B0; padding: 10px;")
        video_props_layout.addWidget(info_label)
        video_props_layout.addStretch()
        self.toolbox.addItem(self.video_props_page, "视频属性")

        # 新增特效页
        self.effects_page = QWidget()
        effects_layout = QVBoxLayout(self.effects_page)
        effects_layout.setSpacing(10)

        # 特效组
        effects_group = QGroupBox("视频特效")
        effects_layout_inner = QFormLayout(effects_group)

        self.effect_combo = QComboBox()
        self.effect_combo.addItems([e.value for e in EffectType])
        self.effect_combo.currentTextChanged.connect(self._on_effect_changed)
        effects_layout_inner.addRow("选择特效:", self.effect_combo)

        # 参数滑块（示例：模糊半径）
        self.effect_radius_slider = QSlider(Qt.Orientation.Horizontal)
        self.effect_radius_slider.setRange(1, 50)
        self.effect_radius_slider.setValue(5)
        self.effect_radius_slider.valueChanged.connect(self._update_effect_params)
        effects_layout_inner.addRow("效果强度:", self.effect_radius_slider)

        self.apply_effect_btn = QPushButton("应用特效")
        self.apply_effect_btn.clicked.connect(self._apply_current_effect)
        effects_layout_inner.addRow(self.apply_effect_btn)

        effects_layout.addWidget(effects_group)

        # 转场组
        transitions_group = QGroupBox("转场效果")
        transitions_layout = QFormLayout(transitions_group)

        self.transition_combo = QComboBox()
        self.transition_combo.addItems([t.value for t in TransitionType])
        self.transition_combo.currentTextChanged.connect(self._on_transition_changed)
        transitions_layout.addRow("选择转场:", self.transition_combo)

        self.transition_progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.transition_progress_slider.setRange(0, 100)
        self.transition_progress_slider.setValue(50)
        transitions_layout.addRow("转场进度:", self.transition_progress_slider)

        self.apply_transition_btn = QPushButton("应用转场")
        self.apply_transition_btn.clicked.connect(self._apply_current_transition)
        transitions_layout.addRow(self.apply_transition_btn)

        effects_layout.addWidget(transitions_group)
        effects_layout.addStretch()

        self.toolbox.addItem(self.effects_page, "特效 & 转场")

        # 新增多机位页
        self.multicam_page = QWidget()
        multicam_layout = QVBoxLayout(self.multicam_page)
        multicam_layout.setSpacing(10)

        # 多机位组
        multicam_group = QGroupBox("多机位编辑")
        multicam_layout_inner = QFormLayout(multicam_group)

        self.angle_combo = QComboBox()
        self.angle_combo.addItems(["Wide (全景)", "Medium (中景)", "Close-up (特写)", "Over-shoulder (过肩)", "Low Angle (低角度)", "High Angle (高角度)"])
        self.angle_combo.setCurrentText("Wide (全景)")
        self.angle_combo.currentTextChanged.connect(self._on_angle_changed)
        multicam_layout_inner.addRow("当前角度:", self.angle_combo)

        self.sync_btn = QPushButton("同步源")
        self.sync_btn.clicked.connect(self.multicam_sync_requested.emit)
        multicam_layout_inner.addRow(self.sync_btn)

        self.switch_btn = QPushButton("切换角度")
        self.switch_btn.clicked.connect(self._switch_angle)
        multicam_layout_inner.addRow(self.switch_btn)

        multicam_layout.addWidget(multicam_group)
        multicam_layout.addStretch()

        self.toolbox.addItem(self.multicam_page, "多机位")

        # 新增导出页
        self.export_page = QWidget()
        export_layout = QVBoxLayout(self.export_page)
        export_layout.setSpacing(10)

        # 导出组
        export_group = QGroupBox("导出设置")
        export_layout_inner = QFormLayout(export_group)

        # 预设选择
        from app.export.export_system import ExportPresetManager, ExportSystem
        self.preset_manager = ExportPresetManager()
        self.export_system = ExportSystem()
        self.export_presets = self.preset_manager.get_all_presets()

        self.preset_combo = QComboBox()
        for preset in self.export_presets:
            self.preset_combo.addItem(preset.name, preset.id)
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        export_layout_inner.addRow("导出预设:", self.preset_combo)

        # 输出路径
        self.output_path_edit = QLineEdit("/exports/output.mp4")
        self.output_path_edit.setPlaceholderText("选择输出路径")
        export_layout_inner.addRow("输出路径:", self.output_path_edit)

        # 导出按钮
        self.export_btn = QPushButton("开始导出")
        self.export_btn.clicked.connect(self._start_export)
        export_layout_inner.addRow(self.export_btn)

        export_group.setLayout(export_layout_inner)
        export_layout.addWidget(export_group)

        # 进度条
        self.export_progress = QProgressBar()
        self.export_progress.setVisible(False)
        self.export_progress.setTextVisible(True)
        export_layout.addWidget(self.export_progress)

        export_layout.addStretch()

        self.toolbox.addItem(self.export_page, "导出")

        # 连接导出信号
        self.export_system.export_progress.connect(self._on_export_progress)
        self.export_system.export_completed.connect(self._on_export_completed)
        self.export_system.export_failed.connect(self._on_export_failed)

        layout.addWidget(self.toolbox)

    def _on_effect_changed(self, effect_name: str):
        """特效选择变化"""
        self.current_effect = effect_name
        # 更新参数控件基于效果类型
        if effect_name == "blur":
            self.effect_radius_slider.setToolTip("模糊半径 (1-50)")
        elif effect_name == "color_correction":
            self.effect_radius_slider.setToolTip("对比度调整 (-100 to 100)")
            self.effect_radius_slider.setRange(-100, 100)
        # 可以添加更多效果参数

    def _on_transition_changed(self, transition_name: str):
        """转场选择变化"""
        self.current_transition = transition_name

    def _update_effect_params(self, value: int):
        """更新特效参数"""
        if self.current_effect:
            # 这里可以emit信号到video_editor_page应用实时预览
            pass

    def _apply_current_effect(self):
        """应用当前特效"""
        if self.current_effect:
            params = {"radius": self.effect_radius_slider.value()}
            # emit信号或调用父组件方法应用效果
            print(f"应用特效: {self.current_effect} with params {params}")

    def _apply_current_transition(self):
        """应用当前转场"""
        if self.current_transition:
            progress = self.transition_progress_slider.value() / 100.0
            params = {"progress": progress}
            # emit信号或调用父组件方法应用转场
            print(f"应用转场: {self.current_transition} with progress {progress}")

    def _on_angle_changed(self, angle_text: str):
        """角度变化"""
        self.current_angle = angle_text.split(" (")[0].lower()

    def _switch_angle(self):
        """切换角度"""
        self.angle_switched.emit(self.current_angle)

    def get_current_effect_params(self) -> dict:
        """获取当前特效参数"""
        return {
            "effect": self.current_effect,
            "params": {"radius": self.effect_radius_slider.value()}
        }

    def get_current_transition_params(self) -> dict:
        """获取当前转场参数"""
        return {
            "transition": self.current_transition,
            "params": {"progress": self.transition_progress_slider.value() / 100.0}
        }

    def get_current_angle(self) -> str:
        """获取当前角度"""
        return self.current_angle