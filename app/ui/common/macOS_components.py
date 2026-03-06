"""
macOS 设计系统 - 通用组件库
向后兼容层 - 从新模块导入
"""

# 从新模块导入所有组件，保持向后兼容
from app.ui.components.containers import MacCard, MacElevatedCard, MacSection
from app.ui.components.buttons import (
    MacButton, MacPrimaryButton, MacSecondaryButton,
    MacDangerButton, MacIconButton, MacButtonGroup
)
from app.ui.components.labels import MacLabel, MacTitleLabel, MacBadge, MacStatLabel
from app.ui.components.inputs import MacSearchBox
from app.ui.components.layout import MacScrollArea, MacGrid, MacPageToolbar, MacEmptyState

# 保留自定义辅助函数
from typing import Optional, List
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt


def create_icon_text_row(icon: str, text: str, parent: Optional[QWidget] = None) -> QWidget:
    """创建图标+文字行"""
    widget = QWidget(parent)
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    
    icon_label = QLabel(icon)
    text_label = MacLabel(text)
    
    layout.addWidget(icon_label)
    layout.addWidget(text_label)
    
    return widget


def create_status_badge_row(status: str, parent: Optional[QWidget] = None) -> QWidget:
    """创建状态徽章行"""
    widget = QWidget(parent)
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    
    status_badge = MacBadge(status)
    
    layout.addWidget(status_badge)
    layout.addStretch()
    
    return widget
