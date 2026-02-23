"""
聊天消息组件
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QTextDocument


class ChatMessage(QWidget):
    """聊天消息组件"""

    def __init__(self, role: str, content: str, timestamp: datetime):
        super().__init__()

        self.role = role
        self.content = content
        self.timestamp = timestamp

        self._setup_ui()
        self._create_layout()

    def _setup_ui(self) -> None:
        """设置UI"""
        self.setObjectName(f"chat_message_{self.role}")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def _create_layout(self) -> None:
        """创建布局"""
        if self.role == "user":
            self._create_user_message()
        else:
            self._create_assistant_message()

    def _create_user_message(self) -> None:
        """创建用户消息"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 右侧对齐
        main_layout.addStretch()

        # 消息容器
        message_container = QWidget()
        message_container.setMaximumWidth(600)
        message_layout = QVBoxLayout(message_container)
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(5)

        # 消息内容
        content_label = QLabel(self.content)
        content_label.setWordWrap(True)
        content_label.setTextFormat(Qt.TextFormat.PlainText)
        content_label.setStyleSheet("""
            QLabel {
                background-color: #2196F3;
                color: white;
                padding: 12px 16px;
                border-radius: 18px;
                font-size: 14px;
                line-height: 1.4;
            }
        """)
        message_layout.addWidget(content_label)

        # 时间戳
        time_label = QLabel(self._format_time(self.timestamp))
        time_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 11px;
                padding-right: 5px;
            }
        """)
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        message_layout.addWidget(time_label)

        main_layout.addWidget(message_container)

    def _create_assistant_message(self) -> None:
        """创建AI助手消息"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 消息容器
        message_container = QWidget()
        message_container.setMaximumWidth(600)
        message_layout = QVBoxLayout(message_container)
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(5)

        # 头像
        avatar_label = QLabel("🤖")
        avatar_label.setStyleSheet("font-size: 20px;")
        avatar_label.setFixedSize(30, 30)
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 消息内容
        content_label = QLabel(self.content)
        content_label.setWordWrap(True)
        content_label.setTextFormat(Qt.TextFormat.PlainText)
        content_label.setStyleSheet("""
            QLabel {
                background-color: #2D2D2D;
                color: #FFFFFF;
                padding: 12px 16px;
                border-radius: 18px;
                font-size: 14px;
                line-height: 1.4;
            }
        """)
        message_layout.addWidget(content_label)

        # 时间戳
        time_label = QLabel(self._format_time(self.timestamp))
        time_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 11px;
                padding-left: 5px;
            }
        """)
        message_layout.addWidget(time_label)

        # 创建左侧布局
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)
        left_layout.addWidget(avatar_label)
        left_layout.addStretch()

        main_layout.addLayout(left_layout)
        main_layout.addWidget(message_container)
        main_layout.addStretch()

    def _format_time(self, timestamp: datetime) -> str:
        """格式化时间"""
        now = datetime.now()
        diff = now - timestamp

        if diff.days == 0:
            if diff.seconds < 60:
                return "刚刚"
            elif diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f"{minutes}分钟前"
            else:
                hours = diff.seconds // 3600
                return f"{hours}小时前"
        elif diff.days == 1:
            return "昨天"
        elif diff.days < 7:
            return f"{diff.days}天前"
        else:
            return timestamp.strftime("%Y-%m-%d")

    def update_theme(self, is_dark: bool = True) -> None:
        """更新主题"""
        if is_dark:
            user_bg = "#2196F3"
            assistant_bg = "#2D2D2D"
            user_text = "white"
            assistant_text = "#FFFFFF"
            time_color = "#666666"
        else:
            user_bg = "#E3F2FD"
            assistant_bg = "#F5F5F5"
            user_text = "#000000"
            assistant_text = "#000000"
            time_color = "#999999"

        # 更新样式
        self.setStyleSheet(f"""
            QWidget#chat_message_user QLabel[style="message_content"] {{
                background-color: {user_bg};
                color: {user_text};
            }}
            QWidget#chat_message_assistant QLabel[style="message_content"] {{
                background-color: {assistant_bg};
                color: {assistant_text};
            }}
            QLabel[style="timestamp"] {{
                color: {time_color};
            }}
        """)

    def get_content(self) -> str:
        """获取消息内容"""
        return self.content

    def get_role(self) -> str:
        """获取消息角色"""
        return self.role

    def get_timestamp(self) -> datetime:
        """获取时间戳"""
        return self.timestamp