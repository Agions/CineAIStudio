"""
卡片组件

提供各种卡片布局组件。
"""

from typing import Optional, List, Callable, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont


class Card(QFrame):
    """
    基础卡片组件
    
    提供统一的卡片样式。
    """
    
    clicked = pyqtSignal()
    
    def __init__(self, parent: Optional[QWidget] = None, clickable: bool = False):
        """
        初始化
        
        Args:
            parent: 父组件
            clickable: 是否可点击
        """
        super().__init__(parent)
        
        self._clickable = clickable
        self._setup_style()
        self._setup_layout()
        
        if clickable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def _setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            Card {
                background-color: #1E1E1E;
                border: 1px solid #333333;
                border-radius: 12px;
            }
            Card:hover {
                border-color: #4A4A4A;
            }
        """)
        self.setFrameShape(QFrame.Shape.StyledPanel)
    
    def _setup_layout(self):
        """设置布局"""
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(12)
    
    def layout(self) -> QVBoxLayout:
        """
        获取布局
        
        Returns:
            布局
        """
        return self._layout
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if self._clickable:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def set_content_margins(self, left: int, top: int, right: int, bottom: int):
        """
        设置内容边距
        
        Args:
            left: 左边距
            top: 上边距
            right: 右边距
            bottom: 下边距
        """
        self._layout.setContentsMargins(left, top, right, bottom)


class ElevatedCard(Card):
    """
    提升卡片
    
    带有阴影效果的卡片。
    """
    
    def __init__(self, parent: Optional[QWidget] = None, clickable: bool = False):
        """初始化"""
        super().__init__(parent, clickable)
        
        self.setStyleSheet("""
            ElevatedCard {
                background-color: #1E1E1E;
                border: 1px solid #333333;
                border-radius: 12px;
            }
            ElevatedCard:hover {
                background-color: #262626;
                border-color: #4A4A4A;
            }
        """)


class OutlinedCard(Card):
    """
    轮廓卡片
    
    只有边框的卡片。
    """
    
    def __init__(self, parent: Optional[QWidget] = None, clickable: bool = False):
        """初始化"""
        super().__init__(parent, clickable)
        
        self.setStyleSheet("""
            OutlinedCard {
                background-color: transparent;
                border: 1px solid #333333;
                border-radius: 12px;
            }
            OutlinedCard:hover {
                border-color: #4A4A4A;
                background-color: rgba(255, 255, 255, 0.02);
            }
        """)


class MediaCard(Card):
    """
    媒体卡片
    
    显示媒体内容的卡片。
    """
    
    def __init__(self, parent: Optional[QWidget] = None, clickable: bool = True):
        """初始化"""
        super().__init__(parent, clickable)
        
        self._image_label: Optional[QLabel] = None
        self._title_label: Optional[QLabel] = None
        self._subtitle_label: Optional[QLabel] = None
        
        self._setup_media_ui()
    
    def _setup_media_ui(self):
        """设置媒体UI"""
        # 图片区域
        self._image_label = QLabel()
        self._image_label.setFixedHeight(120)
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setStyleSheet("""
            QLabel {
                background-color: #2C2C2C;
                border-radius: 8px;
            }
        """)
        self._layout.addWidget(self._image_label)
        
        # 标题
        self._title_label = QLabel()
        self._title_label.setStyleSheet("""
            color: #FFFFFF;
            font-size: 14px;
            font-weight: 500;
        """)
        self._title_label.setWordWrap(True)
        self._layout.addWidget(self._title_label)
        
        # 副标题
        self._subtitle_label = QLabel()
        self._subtitle_label.setStyleSheet("""
            color: #808080;
            font-size: 12px;
        """)
        self._subtitle_label.setWordWrap(True)
        self._layout.addWidget(self._subtitle_label)
    
    def set_image(self, pixmap: QPixmap):
        """
        设置图片
        
        Args:
            pixmap: 图片
        """
        scaled = pixmap.scaled(
            self._image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        self._image_label.setPixmap(scaled)
    
    def set_image_path(self, path: str):
        """
        设置图片路径
        
        Args:
            path: 图片路径
        """
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.set_image(pixmap)
    
    def set_title(self, title: str):
        """
        设置标题
        
        Args:
            title: 标题
        """
        self._title_label.setText(title)
    
    def set_subtitle(self, subtitle: str):
        """
        设置副标题
        
        Args:
            subtitle: 副标题
        """
        self._subtitle_label.setText(subtitle)


class ActionCard(Card):
    """
    操作卡片
    
    带有操作按钮的卡片。
    """
    
    action_triggered = pyqtSignal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        """初始化"""
        super().__init__(parent)
        
        self._actions: List[dict] = []
        self._actions_widget: Optional[QWidget] = None
    
    def add_action(self, action_id: str, label: str, 
                   icon: Optional[str] = None,
                   primary: bool = False):
        """
        添加操作
        
        Args:
            action_id: 操作ID
            label: 标签
            icon: 图标
            primary: 是否为主要操作
        """
        self._actions.append({
            'id': action_id,
            'label': label,
            'icon': icon,
            'primary': primary
        })
        self._update_actions()
    
    def _update_actions(self):
        """更新操作按钮"""
        # 移除旧的操作区域
        if self._actions_widget:
            self._layout.removeWidget(self._actions_widget)
            self._actions_widget.deleteLater()
        
        if not self._actions:
            return
        
        # 创建操作区域
        self._actions_widget = QWidget()
        actions_layout = QHBoxLayout(self._actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)
        
        actions_layout.addStretch()
        
        for action in self._actions:
            btn = QPushButton(action['label'])
            
            if action['primary']:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2962FF;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                        font-weight: 500;
                    }
                    QPushButton:hover {
                        background-color: #448AFF;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #E0E0E0;
                        border: 1px solid #333333;
                        border-radius: 6px;
                        padding: 8px 16px;
                    }
                    QPushButton:hover {
                        background-color: #2C2C2C;
                    }
                """)
            
            action_id = action['id']
            btn.clicked.connect(lambda checked, aid=action_id: self.action_triggered.emit(aid))
            
            actions_layout.addWidget(btn)
        
        self._layout.addWidget(self._actions_widget)
    
    def clear_actions(self):
        """清除所有操作"""
        self._actions.clear()
        self._update_actions()


class CardGrid(QWidget):
    """
    卡片网格
    
    响应式卡片网格布局。
    """
    
    def __init__(self, parent: Optional[QWidget] = None, 
                 min_card_width: int = 280,
                 spacing: int = 16):
        """
        初始化
        
        Args:
            parent: 父组件
            min_card_width: 最小卡片宽度
            spacing: 间距
        """
        super().__init__(parent)
        
        self._min_card_width = min_card_width
        self._spacing = spacing
        self._cards: List[Card] = []
        
        self._setup_layout()
    
    def _setup_layout(self):
        """设置布局"""
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(self._spacing)
    
    def add_card(self, card: Card):
        """
        添加卡片
        
        Args:
            card: 卡片
        """
        self._cards.append(card)
        self._relayout()
    
    def remove_card(self, card: Card):
        """
        移除卡片
        
        Args:
            card: 卡片
        """
        if card in self._cards:
            self._cards.remove(card)
            self._relayout()
    
    def clear(self):
        """清空所有卡片"""
        self._cards.clear()
        # 清除布局
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
    
    def _relayout(self):
        """重新布局"""
        # 清除现有布局
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        if not self._cards:
            return
        
        # 计算每行卡片数
        available_width = self.width() - 32  # 减去边距
        cards_per_row = max(1, available_width // (self._min_card_width + self._spacing))
        
        # 创建行
        current_row: List[Card] = []
        for card in self._cards:
            current_row.append(card)
            
            if len(current_row) >= cards_per_row:
                self._add_row(current_row)
                current_row = []
        
        # 添加最后一行
        if current_row:
            self._add_row(current_row)
    
    def _add_row(self, cards: List[Card]):
        """
        添加一行卡片
        
        Args:
            cards: 卡片列表
        """
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(self._spacing)
        
        for card in cards:
            card.setMinimumWidth(self._min_card_width)
            row_layout.addWidget(card)
        
        row_layout.addStretch()
        self._layout.addWidget(row_widget)
    
    def resizeEvent(self, event):
        """调整大小事件"""
        super().resizeEvent(event)
        self._relayout()
