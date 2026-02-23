"""
UI组件库

提供统一的UI组件，确保一致的视觉风格和交互体验。
"""

from .loading import (
    LoadingSpinner, LoadingOverlay, SkeletonScreen,
    ProgressIndicator, CircularProgress, LinearProgress
)
from .error_boundary import ErrorBoundaryWidget, ErrorDisplay
from .cards import (
    Card, ElevatedCard, OutlinedCard,
    MediaCard, ActionCard
)
from .buttons import (
    PrimaryButton, SecondaryButton, GhostButton,
    IconButton, ActionButton
)
from .inputs import (
    TextInput, TextArea, SearchInput,
    FileInput, NumberInput
)
from .feedback import (
    Toast, ToastManager, Alert, AlertType,
    Badge, StatusIndicator
)
from .layout import (
    ResponsiveGrid, FlexRow, FlexColumn,
    Spacer, Divider
)
from .media import (
    VideoThumbnail, VideoPlayer, MediaGrid
)

__all__ = [
    # 加载组件
    'LoadingSpinner',
    'LoadingOverlay',
    'SkeletonScreen',
    'ProgressIndicator',
    'CircularProgress',
    'LinearProgress',
    # 错误边界
    'ErrorBoundaryWidget',
    'ErrorDisplay',
    # 卡片
    'Card',
    'ElevatedCard',
    'OutlinedCard',
    'MediaCard',
    'ActionCard',
    # 按钮
    'PrimaryButton',
    'SecondaryButton',
    'GhostButton',
    'IconButton',
    'ActionButton',
    # 输入
    'TextInput',
    'TextArea',
    'SearchInput',
    'FileInput',
    'NumberInput',
    # 反馈
    'Toast',
    'ToastManager',
    'Alert',
    'AlertType',
    'Badge',
    'StatusIndicator',
    # 布局
    'ResponsiveGrid',
    'FlexRow',
    'FlexColumn',
    'Spacer',
    'Divider',
    # 媒体
    'VideoThumbnail',
    'VideoPlayer',
    'MediaGrid',
]
