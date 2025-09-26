#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio v2.0 AI对话页面
用户与AI助手交互的聊天界面，支持视频编辑相关咨询和操作建议
"""

from typing import List, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel,
    QScrollArea, QFrame, QComboBox, QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor

from ...core.application import Application
from ...ui.main.components.base_page import BasePage
from ...services.mock_ai_service import MockAIService


class MessageType:
    """消息类型"""
    USER = "user"
    AI = "ai"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """聊天消息"""
    type: str
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = None


class AIChatWidget(QTextEdit):
    """AI聊天窗口组件"""
    message_added = pyqtSignal(ChatMessage)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background: #1A1A1A;
                color: #FFFFFF;
                border: none;
                padding: 10px;
                font-family: 'Segoe UI', Arial;
                font-size: 14px;
                line-height: 1.5;
            }
            QTextEdit:focus {
                border: 1px solid #00A8FF;
            }
        """)
        self.messages: List[ChatMessage] = []

    def add_message(self, message_type: str, content: str, metadata: Dict[str, Any] = None):
        """添加消息"""
        timestamp = datetime.now()
        message = ChatMessage(type=message_type, content=content, timestamp=timestamp, metadata=metadata)

        # 格式化消息
        self._format_message(message)

        self.messages.append(message)
        self.message_added.emit(message)

        # 滚动到底部
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def _format_message(self, message: ChatMessage):
        """格式化并添加消息到聊天窗口"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # 时间戳
        time_format = QTextCharFormat()
        time_format.setForeground(QColor("#B0B0B0"))
        time_format.setFontPointSize(10)
        cursor.insertText(f"[{message.timestamp.strftime('%H:%M:%S')}] ", time_format)

        # 消息内容
        if message.type == MessageType.USER:
            content_format = QTextCharFormat()
            content_format.setForeground(QColor("#00A8FF"))
            content_format.setFontWeight(75)  # Bold
            cursor.insertText(f"你: {message.content}\n\n", content_format)
        elif message.type == MessageType.AI:
            content_format = QTextCharFormat()
            content_format.setForeground(QColor("#4CAF50"))
            cursor.insertText(f"AI: {message.content}\n\n", content_format)
        elif message.type == MessageType.SYSTEM:
            content_format = QTextCharFormat()
            content_format.setForeground(QColor("#FF9800"))
            cursor.insertText(f"系统: {message.content}\n\n", content_format)

        self.setTextCursor(cursor)

    def clear_chat(self):
        """清空聊天记录"""
        self.clear()
        self.messages.clear()

    def get_chat_history(self) -> List[ChatMessage]:
        """获取聊天历史"""
        return self.messages.copy()

    def export_chat(self, file_path: str) -> bool:
        """导出聊天记录"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for msg in self.messages:
                    f.write(f"[{msg.timestamp}] {msg.type.upper()}: {msg.content}\n")
            return True
        except Exception as e:
            QMessageBox.warning(self, "导出失败", f"无法导出聊天记录: {str(e)}")
            return False


class AIInputWidget(QWidget):
    """AI输入组件"""
    message_sent = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)

        # 输入框
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入你的问题或指令... (例如: '如何添加字幕?' 或 '分析这个视频')")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: #2A2A2A;
                color: #FFFFFF;
                border: 1px solid #3A3A3A;
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #00A8FF;
            }
        """)
        self.input_field.returnPressed.connect(self._send_message)

        # 发送按钮
        self.send_btn = QPushButton("发送")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: #00A8FF;
                color: #FFFFFF;
                border: none;
                padding: 10px 20px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #0090E6;
            }
            QPushButton:pressed {
                background: #007ACC;
            }
            QPushButton:disabled {
                background: #404040;
                color: #808080;
            }
        """)
        self.send_btn.clicked.connect(self._send_message)
        self.send_btn.setEnabled(False)

        # 连接输入变化
        self.input_field.textChanged.connect(self._on_input_changed)

        layout.addWidget(self.input_field, 1)
        layout.addWidget(self.send_btn)

    def _on_input_changed(self, text: str):
        """输入变化处理"""
        self.send_btn.setEnabled(len(text.strip()) > 0)

    def _send_message(self):
        """发送消息"""
        message = self.input_field.text().strip()
        if message:
            self.message_sent.emit(message)
            self.input_field.clear()

    def set_placeholder(self, text: str):
        """设置占位符文本"""
        self.input_field.setPlaceholderText(text)


class AIContextSelector(QWidget):
    """AI上下文选择器"""
    context_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(5)

        # 上下文标签
        self.context_label = QLabel("AI助手:")
        self.context_label.setStyleSheet("color: #B0B0B0; font-size: 12px;")

        # 上下文选择
        self.context_combo = QComboBox()
        self.context_combo.addItems([
            "通用助手",
            "视频编辑专家",
            "AI剪辑建议",
            "字幕生成助手",
            "画质优化专家"
        ])
        self.context_combo.setCurrentText("视频编辑专家")
        self.context_combo.setStyleSheet("""
            QComboBox {
                background: #2A2A2A;
                color: #FFFFFF;
                border: 1px solid #3A3A3A;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                min-width: 120px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #FFFFFF;
            }
        """)
        self.context_combo.currentTextChanged.connect(self.context_changed)

        layout.addWidget(self.context_label)
        layout.addWidget(self.context_combo)
        layout.addStretch()

    def get_current_context(self) -> str:
        """获取当前上下文"""
        return self.context_combo.currentText()


class AIDialogPage(BasePage):
    """AI对话页面"""

    def __init__(self, application: Application):
        super().__init__("ai_dialog", "AI助手", application)

        # 组件
        self.chat_widget: Optional[AIChatWidget] = None
        self.input_widget: Optional[AIInputWidget] = None
        self.context_selector: Optional[AIContextSelector] = None

        # AI服务
        self.ai_service: Optional[MockAIService] = None
        self.current_context: str = "视频编辑专家"

        # 聊天状态
        self.is_typing: bool = False
        self.typing_timer = QTimer()
        self.typing_timer.setSingleShot(True)
        self.typing_timer.timeout.connect(self._stop_typing_indicator)

        # 初始化
        self._init_ai_service()
        self._connect_signals()

    def initialize(self) -> bool:
        """初始化页面"""
        try:
            self.log_info("Initializing AI dialog page")
            self._welcome_message()
            return True
        except Exception as e:
            self.handle_error(e, "initialize")
            return False

    def create_content(self) -> None:
        """创建页面内容"""
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        self.setLayout(main_layout)

        # 上下文选择器
        self.context_selector = AIContextSelector()
        self.context_selector.context_changed.connect(self._on_context_changed)
        main_layout.addWidget(self.context_selector)

        # 聊天滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2A2A2A;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #404040;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #505050;
            }
        """)
        main_layout.addWidget(scroll_area, 1)

        # 聊天窗口
        self.chat_widget = AIChatWidget()
        self.chat_widget.message_added.connect(self._on_message_added)
        scroll_area.setWidget(self.chat_widget)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #3A3A3A;")
        main_layout.addWidget(separator)

        # 输入区域
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background: #2A2A2A;
                border: 1px solid #3A3A3A;
                border-radius: 8px;
            }
        """)
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 5, 10, 5)

        self.input_widget = AIInputWidget()
        self.input_widget.message_sent.connect(self._on_message_sent)
        input_layout.addWidget(self.input_widget)

        # 功能按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        clear_btn = QPushButton("清空对话")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #FF5722;
                color: #FFFFFF;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #E64A19;
            }
        """)
        clear_btn.clicked.connect(self._clear_chat)

        export_btn = QPushButton("导出对话")
        export_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: #FFFFFF;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #45A049;
            }
        """)
        export_btn.clicked.connect(self._export_chat)

        button_layout.addStretch()
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(export_btn)
        input_layout.addLayout(button_layout)

        main_layout.addWidget(input_frame)

        self.log_info("AI dialog page content created")

    def _init_ai_service(self):
        """初始化AI服务"""
        try:
            self.ai_service = MockAIService()
            self.ai_service.processing_started.connect(self._on_ai_processing_started)
            self.ai_service.processing_progress.connect(self._on_ai_processing_progress)
            self.ai_service.processing_completed.connect(self._on_ai_processing_completed)
            self.ai_service.processing_error.connect(self._on_ai_processing_error)
            self.log_info("AI服务初始化完成")
        except Exception as e:
            self.handle_error(e, "_init_ai_service")
            self.ai_service = None

    def _connect_signals(self):
        """连接信号"""
        # 页面信号
        self.page_activated.connect(self._on_page_activated)
        self.page_deactivated.connect(self._on_page_deactivated)

    def _welcome_message(self):
        """欢迎消息"""
        welcome_msg = """
欢迎使用CineAIStudio AI助手！我是你的视频编辑专家，可以帮助你：

• 分析视频内容和场景
• 生成智能剪辑建议
• 创建自动字幕和配音
• 优化视频画质和效果
• 解答视频编辑问题

请告诉我你需要什么帮助，或者描述你的视频项目！
        """
        self.chat_widget.add_message(MessageType.SYSTEM, welcome_msg)

    def _on_message_sent(self, message: str):
        """消息发送处理"""
        # 添加用户消息
        self.chat_widget.add_message(MessageType.USER, message)

        # 显示输入指示器
        self._show_typing_indicator()

        # 处理消息
        self._process_message(message)

    def _process_message(self, message: str):
        """处理用户消息"""
        if not self.ai_service:
            self.chat_widget.add_message(MessageType.AI, "抱歉，AI服务暂时不可用。请检查网络连接或稍后重试。")
            self._stop_typing_indicator()
            return

        # 根据上下文和消息内容调用AI服务
        context = self.current_context.lower()
        if "剪辑" in message or "edit" in message or "视频编辑专家" in context:
            # 智能剪辑相关
            self.ai_service.smart_edit("sample_video.mp4", self._on_ai_response)
        elif "字幕" in message or "subtitle" in message or "字幕生成助手" in context:
            # 字幕生成
            self.ai_service.generate_subtitle("sample_video.mp4", "zh", self._on_ai_response)
        elif "画质" in message or "quality" in message or "画质优化专家" in context:
            # 画质增强
            self.ai_service.enhance_quality("sample_video.mp4", "high", self._on_ai_response)
        else:
            # 通用响应
            self.ai_service.analyze_video("sample_video.mp4", self._on_ai_response)

    def _on_ai_response(self, result: Any):
        """AI响应回调"""
        if isinstance(result, dict) and "error" in result:
            self.chat_widget.add_message(MessageType.AI, f"抱歉，处理出错: {result['error']}")
        else:
            # 格式化AI响应
            if isinstance(result, dict):
                response = self._format_ai_response(result)
            else:
                response = str(result)
            self.chat_widget.add_message(MessageType.AI, response)
        self._stop_typing_indicator()

    def _format_ai_response(self, result: Dict[str, Any]) -> str:
        """格式化AI响应"""
        if "highlights" in result:
            highlights = "\n".join([f"- {h.get('description', '未知')}: {h['start']}s - {h['end']}s" for h in result["highlights"]])
            return f"智能剪辑完成！推荐高光片段：\n{highlights}\n\n输出文件: {result.get('output_path', '未指定')}"
        elif "output_path" in result:
            return f"处理完成！输出文件: {result['output_path']}\n处理时间: {result.get('processing_time', 0):.2f}秒"
        else:
            return f"分析完成！视频质量评分: {result.get('quality_score', 'N/A')}/100\n推荐操作: {', '.join(result.get('recommended_actions', []))}"

    def _show_typing_indicator(self):
        """显示输入指示器"""
        self.is_typing = True
        self.typing_timer.start(2000)  # 2秒后停止指示器

        # 添加输入指示器消息
        indicator_msg = "AI正在思考中..."
        self.chat_widget.add_message(MessageType.AI, indicator_msg, {"temporary": True})

    def _stop_typing_indicator(self):
        """停止输入指示器"""
        self.is_typing = False
        # 移除临时输入指示器消息（简化实现，实际可滚动移除最后消息）
        pass

    def _on_context_changed(self, context: str):
        """上下文变化处理"""
        self.current_context = context
        self.log_info(f"AI上下文切换到: {context}")

        # 添加系统消息
        context_msg = f"AI助手已切换到 {context} 模式"
        self.chat_widget.add_message(MessageType.SYSTEM, context_msg)

    def _on_ai_processing_started(self, task_name: str):
        """AI处理开始"""
        self.log_info(f"AI处理开始: {task_name}")
        self._show_typing_indicator()

    def _on_ai_processing_progress(self, task_name: str, progress: int):
        """AI处理进度"""
        self.log_info(f"AI处理进度 {task_name}: {progress}%")

    def _on_ai_processing_completed(self, task_name: str, result: Any):
        """AI处理完成"""
        self.log_info(f"AI处理完成 {task_name}")
        self._on_ai_response(result)

    def _on_ai_processing_error(self, task_name: str, error: str):
        """AI处理错误"""
        self.log_error(f"AI处理错误 {task_name}: {error}")
        self.chat_widget.add_message(MessageType.AI, f"处理出错: {error}")
        self._stop_typing_indicator()

    def _on_message_added(self, message: ChatMessage):
        """消息添加处理"""
        self.log_info(f"聊天消息添加: {message.type} - {message.content[:50]}...")

    def _clear_chat(self):
        """清空聊天"""
        reply = QMessageBox.question(self, "确认清空", "确定要清空所有对话记录吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.chat_widget.clear_chat()
            self._welcome_message()

    def _export_chat(self):
        """导出聊天"""
        file_path, _ = QFileDialog.getSaveFileName(self, "导出聊天记录", "chat_history.txt", "Text Files (*.txt)")
        if file_path:
            if self.chat_widget.export_chat(file_path):
                self.show_info("导出成功", f"聊天记录已导出到: {file_path}")

    def _on_page_activated(self):
        """页面激活处理"""
        self.input_widget.input_field.setFocus()
        self.log_info("AI对话页面已激活")

    def _on_page_deactivated(self):
        """页面失活处理"""
        self.log_info("AI对话页面已失活")

    def save_state(self) -> None:
        """保存状态"""
        self.page_state = {
            "current_context": self.current_context,
            "chat_history": [msg.__dict__ for msg in self.chat_widget.messages],
            "input_text": self.input_widget.input_field.text()
        }

    def restore_state(self) -> None:
        """恢复状态"""
        if "current_context" in self.page_state:
            self.current_context = self.page_state["current_context"]
            if self.context_selector:
                self.context_selector.context_combo.setCurrentText(self.current_context)

        if "chat_history" in self.page_state:
            for msg_dict in self.page_state["chat_history"]:
                msg = ChatMessage(**msg_dict)
                self.chat_widget.add_message(msg.type, msg.content, msg.metadata)

        if "input_text" in self.page_state:
            self.input_widget.input_field.setText(self.page_state["input_text"])

    def cleanup(self) -> None:
        """清理资源"""
        if self.ai_service:
            self.ai_service.cancel_processing()
        self.chat_widget.clear_chat()
        self.log_info("AI对话页面清理完成")