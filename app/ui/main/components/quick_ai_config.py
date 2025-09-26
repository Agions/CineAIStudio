"""
一键AI配置组件 - 快速AI设置面板
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QPushButton, QGroupBox, QFormLayout
)
from PyQt6.QtCore import pyqtSignal
from typing import Dict, Any


class QuickAIConfig(QWidget):
    """一键AI配置 - 快速AI设置面板"""
    
    config_changed = pyqtSignal(dict)  # 配置变化信号
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.current_config = {
            'model': 'spark-large-v3.5',
            'quality': 'medium',
            'language': 'zh-CN',
            'auto_subtitle': True,
            'enhance_quality': True
        }
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # 标题
        title = QLabel("🚀 一键AI配置")
        title.setStyleSheet("font-weight: bold; color: #00A8FF; font-size: 14px; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # AI模型选择
        model_group = QGroupBox("AI模型")
        model_layout = QFormLayout(model_group)
        self.model_combo = QComboBox()
        self.model_combo.addItems(['spark-large-v3.5', 'qwen-max', 'glm-4', 'wenxin-2.0'])
        self.model_combo.setCurrentText(self.current_config['model'])
        self.model_combo.currentTextChanged.connect(self._update_model)
        model_layout.addRow("模型:", self.model_combo)
        layout.addWidget(model_group)
        
        # 处理质量
        quality_group = QGroupBox("处理质量")
        quality_layout = QFormLayout(quality_group)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(['low', 'medium', 'high', 'ultra'])
        self.quality_combo.setCurrentText(self.current_config['quality'])
        self.quality_combo.currentTextChanged.connect(self._update_quality)
        quality_layout.addRow("质量:", self.quality_combo)
        layout.addWidget(quality_group)
        
        # 语言设置
        lang_group = QGroupBox("语言设置")
        lang_layout = QFormLayout(lang_group)
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(['zh-CN', 'en-US', 'zh-TW'])
        self.lang_combo.setCurrentText(self.current_config['language'])
        self.lang_combo.currentTextChanged.connect(self._update_language)
        lang_layout.addRow("语言:", self.lang_combo)
        layout.addWidget(lang_group)
        
        # 开关选项
        options_layout = QHBoxLayout()
        self.auto_subtitle_cb = QCheckBox("自动字幕")
        self.auto_subtitle_cb.setChecked(self.current_config['auto_subtitle'])
        self.auto_subtitle_cb.stateChanged.connect(self._update_auto_subtitle)
        options_layout.addWidget(self.auto_subtitle_cb)
        
        self.enhance_quality_cb = QCheckBox("画质增强")
        self.enhance_quality_cb.setChecked(self.current_config['enhance_quality'])
        self.enhance_quality_cb.stateChanged.connect(self._update_enhance_quality)
        options_layout.addWidget(self.enhance_quality_cb)
        layout.addLayout(options_layout)
        
        # 应用按钮
        self.apply_btn = QPushButton("应用AI配置")
        self.apply_btn.setStyleSheet("""
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
            QPushButton:pressed {
                background: #007ACC;
            }
        """)
        self.apply_btn.clicked.connect(self._apply_config)
        layout.addWidget(self.apply_btn)
        
        layout.addStretch()
    
    def _update_model(self, model: str):
        """更新模型"""
        self.current_config['model'] = model
    
    def _update_quality(self, quality: str):
        """更新质量"""
        self.current_config['quality'] = quality
    
    def _update_language(self, lang: str):
        """更新语言"""
        self.current_config['language'] = lang
    
    def _update_auto_subtitle(self, state: int):
        """更新自动字幕"""
        self.current_config['auto_subtitle'] = bool(state)
    
    def _update_enhance_quality(self, state: int):
        """更新画质增强"""
        self.current_config['enhance_quality'] = bool(state)
    
    def _apply_config(self):
        """应用配置"""
        self.config_changed.emit(self.current_config)
        # 可以添加应用动画或状态反馈
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.current_config.copy()
    
    def set_config(self, config: Dict[str, Any]):
        """设置配置"""
        self.current_config.update(config)
        self.model_combo.setCurrentText(config.get('model', 'spark-large-v3.5'))
        self.quality_combo.setCurrentText(config.get('quality', 'medium'))
        self.lang_combo.setCurrentText(config.get('language', 'zh-CN'))
        self.auto_subtitle_cb.setChecked(config.get('auto_subtitle', True))
        self.enhance_quality_cb.setChecked(config.get('enhance_quality', True))
    
    def reset_to_default(self):
        """重置为默认配置"""
        default_config = {
            'model': 'spark-large-v3.5',
            'quality': 'medium',
            'language': 'zh-CN',
            'auto_subtitle': True,
            'enhance_quality': True
        }
        self.set_config(default_config)