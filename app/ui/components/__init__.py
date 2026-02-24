"""
CineFlow UI 组件库

模块化组件设计:
- containers: 容器组件 (Card, Section, ElevatedCard)
- buttons: 按钮组件 (MacButton, PrimaryButton, SecondaryButton, etc.)
- labels: 标签组件 (MacLabel, TitleLabel, Badge, StatLabel)
- inputs: 输入组件 (SearchBox)
- layout: 布局组件 (Grid, PageToolbar, EmptyState, ScrollArea)
- design_system: 设计系统 (DesignSystem, StyleSheet)
"""

# 容器组件
from .containers import MacCard, MacElevatedCard, MacSection

# 按钮组件
from .buttons import (
    MacButton, MacPrimaryButton, MacSecondaryButton,
    MacDangerButton, MacIconButton, MacButtonGroup
)

# 标签组件
from .labels import MacLabel, MacTitleLabel, MacBadge, MacStatLabel

# 输入组件
from .inputs import MacSearchBox

# 布局组件
from .layout import (
    MacScrollArea, MacGrid, MacPageToolbar, MacEmptyState
)

# 设计系统
from .design_system import (
    DesignSystem, StyleSheet,
    CFButton, CFLabel, CFCard, CFPanel,
    CFInput, CFProgressBar, CFNavButton
)

__all__ = [
    # 容器
    "MacCard", "MacElevatedCard", "MacSection",
    # 按钮
    "MacButton", "MacPrimaryButton", "MacSecondaryButton",
    "MacDangerButton", "MacIconButton", "MacButtonGroup",
    # 标签
    "MacLabel", "MacTitleLabel", "MacBadge", "MacStatLabel",
    # 输入
    "MacSearchBox",
    # 布局
    "MacScrollArea", "MacGrid", "MacPageToolbar", "MacEmptyState",
    # 设计系统
    "DesignSystem", "StyleSheet",
    "CFButton", "CFLabel", "CFCard", "CFPanel",
    "CFInput", "CFProgressBar", "CFNavButton",
]
