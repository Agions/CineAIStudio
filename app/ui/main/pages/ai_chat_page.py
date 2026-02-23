"""
AI对话页面 - macOS 设计系统优化版
重构为使用标准化组件，零内联样式
"""

from typing import Optional, Dict, Any, List
import json
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel,
    QTextEdit, QLineEdit, QPushButton, QFrame, QListWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from .base_page import BasePage
from app.core.icon_manager import get_icon
from app.services.ai_service.mock_ai_service import MockAIService

# 导入标准化 macOS 组件
from app.ui.common.macOS_components import (
    MacCard, MacPrimaryButton, MacSecondaryButton,
    MacIconButton, MacTitleLabel, MacLabel,
    MacScrollArea, MacEmptyState, MacSearchBox
)


class ChatBubble(QWidget):
    """聊天气泡 - 使用标准化样式"""

    def __init__(self, role: str, content: str, timestamp, parent=None):
        super().__init__(parent)
        self.setProperty("class", f"chat-bubble {role}")
        self._setup_ui(role, content, timestamp)

    def _setup_ui(self, role: str, content: str, timestamp):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # 内容
        content_label = MacLabel(content, "chat-content")
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(content_label)

        # 时间戳
        time_str = timestamp.strftime("%H:%M")
        time_label = MacLabel(time_str, "text-xs text-muted")
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight if role == "user" else Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(time_label)


class ChatInputArea(QWidget):
    """聊天输入区域"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "chat-input-area")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # 输入框容器
        input_container = MacCard()
        input_container.setProperty("class", "input-container")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(8, 8, 8, 8)
        input_layout.setSpacing(8)

        # 输入框
        self.input = QLineEdit()
        self.input.setProperty("class", "chat-input")
        self.input.setPlaceholderText("输入您的问题，按 Enter 发送...")
        input_layout.addWidget(self.input)

        # 发送按钮
        self.send_btn = MacPrimaryButton("发送")
        self.send_btn.setProperty("class", "button send")
        self.send_btn.setFixedWidth(80)
        input_layout.addWidget(self.send_btn)

        layout.addWidget(input_container)


class SuggestionBox(QWidget):
    """建议框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "suggestion-box")
        self.suggestion_clicked = pyqtSignal(str)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # 标题
        title = MacTitleLabel("💡 智能建议", 6)
        layout.addWidget(title)

        # 建议按钮网格
        suggestions_grid_layout = QHBoxLayout()
        suggestions_grid_layout.setSpacing(8)

        suggestions = [
            ("🎥 分析视频", "analyze"),
            ("📝 生成字幕", "subtitle"),
            ("🎨 优化画质", "enhance"),
            ("📢 创作解说", "commentary")
        ]

        for text, action in suggestions:
            btn = MacSecondaryButton(text)
            btn.setProperty("class", "button suggestion")
            btn.setMinimumHeight(32)
            btn.clicked.connect(lambda checked, a=action: self.suggestion_clicked.emit(a))
            suggestions_grid_layout.addWidget(btn)

        suggestions_grid_layout.addStretch()
        layout.addLayout(suggestions_grid_layout)


class SettingsPanel(QWidget):
    """设置面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "settings-panel")
        self.current_provider = "openai"
        self.api_configured = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 标题
        title = MacTitleLabel("⚙️ AI 设置", 6)
        layout.addWidget(title)

        # 状态卡片
        status_card = MacCard()
        status_card.setProperty("class", "card status-card")
        status_layout = QVBoxLayout(status_card.layout())
        status_layout.setSpacing(8)

        # 当前服务
        provider_row = self._create_info_row("当前服务:", self.current_provider)
        status_layout.addWidget(provider_row)

        # API状态
        api_text = "✅ 已配置" if self.api_configured else "❌ 未配置"
        api_color = "success" if self.api_configured else "warning"
        api_row = self._create_info_row("API密钥:", api_text, api_color)
        status_layout.addWidget(api_row)

        layout.addWidget(status_card)

        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        settings_btn = MacSecondaryButton("🔧 详细设置")
        settings_btn.setProperty("class", "button settings")
        btn_layout.addWidget(settings_btn)

        clear_btn = MacSecondaryButton("🗑️ 清空对话")
        clear_btn.setProperty("class", "button danger")
        clear_btn.clicked.connect(self._on_clear_chat)
        btn_layout.addWidget(clear_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

    def _create_info_row(self, label: str, value: str, theme: str = "neutral"):
        """创建信息行"""
        row = QWidget()
        row.setProperty("class", "info-row")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        label_widget = MacLabel(label, "text-sm text-bold")
        value_widget = MacLabel(value, f"text-sm badge badge-{theme}")

        row_layout.addWidget(label_widget)
        row_layout.addWidget(value_widget)
        row_layout.addStretch()

        return row

    def _on_clear_chat(self):
        """清空聊天信号"""
        from PyQt6.QtWidgets import QMessageBox
        if QMessageBox.question(
            None, "确认清空", "确定要清空所有聊天记录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.parent().clear_chat()


class AIChatPage(BasePage):
    """AI对话页面 - macOS 设计系统"""

    def __init__(self, application):
        super().__init__("ai_chat", "AI对话", application)

        self.chat_history = None
        self.chat_input = None
        self.suggestion_box = None
        self.settings_panel = None

        self.messages = []
        self.is_processing = False
        self.ai_service = MockAIService("", "")

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 页面标题
        header = MacPageToolbar("💬 AI 对话", [
            ("🔄", "刷新", self._refresh),
            ("💾", "导出", self._export_chat),
        ])
        layout.addWidget(header)

        # 主内容区域
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setProperty("class", "splitter horizontal")

        # 左侧：聊天区域
        left_panel = self._create_chat_panel()
        self.main_splitter.addWidget(left_panel)

        # 右侧：设置面板
        right_panel = self._create_settings_panel()
        self.main_splitter.addWidget(right_panel)

        # 设置比例
        self.main_splitter.setStretchFactor(0, 7)
        self.main_splitter.setStretchFactor(1, 3)

        layout.addWidget(self.main_splitter)

        # 加载欢迎消息
        self._add_welcome_message()

    def initialize(self) -> bool:
        """初始化页面"""
        try:
            self.log_info("Initializing AI chat page")
            self._load_ai_config()
            return True
        except Exception as e:
            self.handle_error(e, "initialize")
            return False

    def create_content(self) -> None:
        """内容已在_init_ui中创建"""
        # 内容已在 _init_ui 中创建，这里可以刷新界面状态
        self._refresh_ui_state()

    def _create_chat_panel(self) -> QWidget:
        """创建聊天面板"""
        panel = QWidget()
        panel.setProperty("class", "chat-panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 聊天历史 - 滚动区域
        self.chat_history = MacScrollArea()
        self.chat_history.setProperty("class", "chat-scroll-area")
        self.chat_history.setWidgetResizable(True)

        # 聊天容器
        self.chat_container = QWidget()
        self.chat_container.setProperty("class", "chat-container")
        self.chat_container_layout = QVBoxLayout(self.chat_container)
        self.chat_container_layout.setContentsMargins(16, 16, 16, 16)
        self.chat_container_layout.setSpacing(12)
        self.chat_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.chat_history.setWidget(self.chat_container)
        layout.addWidget(self.chat_history, 1)

        # 建议框
        self.suggestion_box = SuggestionBox()
        self.suggestion_box.suggestion_clicked.connect(self._on_suggestion_clicked)
        layout.addWidget(self.suggestion_box)

        # 输入区域
        self.chat_input = ChatInputArea()
        self.chat_input.input.returnPressed.connect(self._on_send_message)
        self.chat_input.send_btn.clicked.connect(self._on_send_message)
        layout.addWidget(self.chat_input)

        return panel

    def _create_settings_panel(self) -> QWidget:
        """创建设置面板"""
        return SettingsPanel()

    def _load_ai_config(self):
        """加载AI配置"""
        if self.config_manager:
            provider = self.get_config_value("ai.provider", "openai")
            api_key = self.get_config_value("ai.api_key", "")
            self.settings_panel.current_provider = provider
            self.settings_panel.api_configured = bool(api_key)

    def _on_send_message(self):
        """发送消息"""
        if self.is_processing:
            return

        message = self.chat_input.input.text().strip()
        if not message:
            return

        # 添加用户消息
        self._add_message("user", message)
        self.chat_input.input.clear()

        # 设置处理状态
        self.set_processing_state(True)

        # 发送AI请求
        self._send_ai_request(message)

    def _on_suggestion_clicked(self, action: str):
        """建议按钮点击"""
        suggestions = {
            "analyze": "帮我分析视频的内容和特点",
            "subtitle": "为我生成视频字幕",
            "enhance": "如何提升视频画质？",
            "commentary": "为我创作视频解说"
        }

        if action in suggestions:
            self.chat_input.input.setText(suggestions[action])
            self.chat_input.input.setFocus()

    def _send_ai_request(self, message: str):
        """发送AI请求"""
        try:
            self._add_loading_indicator()

            if self.ai_service:
                self.ai_service.send_message(
                    message,
                    self.messages,
                    callback=self._on_ai_response_received,
                    error_callback=self._on_ai_error_received
                )

        except Exception as e:
            self.handle_error(e, "send_ai_request")
            self._handle_ai_error("发送AI请求失败")

    def _on_ai_response_received(self, response: str):
        """AI响应处理"""
        try:
            self._remove_loading_indicator()
            self._add_message("assistant", response)
            self.set_processing_state(False)
            self.emit_event("ai_response_received", {"response": response})
        except Exception as e:
            self.handle_error(e, "handle_response")
            self._handle_ai_error("处理AI响应失败")

    def _on_ai_error_received(self, error: str):
        """AI错误处理"""
        try:
            self._remove_loading_indicator()
            self._add_error_message(error)
            self.set_processing_state(False)
            self.emit_event("ai_error_occurred", {"error": error})
        except Exception as e:
            self.handle_error(e, "handle_error")

    def _add_message(self, role: str, content: str):
        """添加消息"""
        try:
            # 创建气泡
            bubble = ChatBubble(role, content, datetime.now())
            self.chat_container_layout.addWidget(bubble)

            # 添加到历史
            self.messages.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })

            # 滚动到底部
            QTimer.singleShot(50, self._scroll_to_bottom)
        except Exception as e:
            self.handle_error(e, "add_message")

    def _add_error_message(self, error: str):
        """添加错误消息"""
        self._add_message("assistant", f"❌ {error}")

    def _add_welcome_message(self):
        """添加欢迎消息"""
        welcome = (
            "👋 您好！我是您的AI视频助手。\\n\\n"
            "我可以帮您：\\n"
            "• 分析视频内容和特点\\n"
            "• 生成视频字幕和配音\\n"
            "• 优化视频画质和效果\\n"
            "• 创作视频解说和文案\\n\\n"
            "请告诉我您需要什么帮助！"
        )
        self._add_message("assistant", welcome)

    def _add_loading_indicator(self):
        """添加加载指示器"""
        if hasattr(self, "_loading"):
            return

        self._loading = MacEmptyState(
            icon="⏳",
            title="AI正在思考中...",
            description=""
        )
        self._loading.setProperty("class", "loading-indicator")
        self.chat_container_layout.addWidget(self._loading)
        self._scroll_to_bottom()

    def _remove_loading_indicator(self):
        """移除加载指示器"""
        if hasattr(self, "_loading"):
            self._loading.deleteLater()
            del self._loading

    def _scroll_to_bottom(self):
        """滚动到底部"""
        if self.chat_history:
            scrollbar = self.chat_history.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def set_processing_state(self, processing: bool):
        """设置处理状态"""
        self.is_processing = processing

        if self.chat_input:
            self.chat_input.send_btn.setEnabled(not processing)
            self.chat_input.input.setEnabled(not processing)
            self.chat_input.send_btn.setText("处理中..." if processing else "发送")

    def _handle_ai_error(self, error_message: str):
        """处理AI错误"""
        self.show_error(error_message)
        self.set_processing_state(False)

    def clear_chat(self):
        """清空聊天"""
        try:
            # 清空消息列表（保留第一条欢迎消息）
            if self.messages:
                welcome_msg = self.messages[0] if len(self.messages) > 0 else None
                self.messages.clear()
                if welcome_msg:
                    self.messages.append(welcome_msg)

            # 清空界面（保留欢迎消息）
            while self.chat_container_layout.count() > 1:
                item = self.chat_container_layout.takeAt(1)
                if item.widget():
                    item.widget().deleteLater()

            self.update_status("聊天记录已清空")
        except Exception as e:
            self.handle_error(e, "clear_chat")

    def _export_chat(self):
        """导出聊天记录"""
        try:
            import json
            from PyQt6.QtWidgets import QFileDialog

            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出聊天记录", "", "JSON文件 (*.json)"
            )

            if file_path:
                chat_data = {
                    "export_time": datetime.now().isoformat(),
                    "provider": self.settings_panel.current_provider,
                    "messages": self.messages
                }

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(chat_data, f, indent=2, ensure_ascii=False)

                self.update_status("聊天记录已导出")
        except Exception as e:
            self.handle_error(e, "export_chat")

    def _refresh(self):
        """刷新"""
        self.update_status("已刷新")
        self._scroll_to_bottom()


class MockAIService:
    """模拟AI服务 - 保留用于功能演示"""

    def __init__(self, api_key: str = "", base_url: str = ""):
        self.api_key = api_key
        self.base_url = base_url

    def send_message(self, message: str, history: List[Dict], callback, error_callback):
        """发送消息（模拟异步响应）"""
        import threading
        import time

        def mock_response():
            time.sleep(1)  # 模拟延迟
            response = self._generate_response(message)

            from PyQt6.QtCore import QMetaObject, Qt
            QMetaObject.invokeMethod(
                None,
                lambda: callback(response),
                Qt.ConnectionType.QueuedConnection
            )

        thread = threading.Thread(target=mock_response)
        thread.daemon = True
        thread.start()

    def _generate_response(self, message: str) -> str:
        """生成模拟响应"""
        msg = message.lower()

        if any(w in msg for w in ["分析", "analyze", "内容"]):
            return "我需要查看视频内容才能进行分析。请先导入视频，然后我可以帮您分析内容特点、关键场景和优化建议。"

        if any(w in msg for w in ["字幕", "subtitle", "生成"]):
            return "生成字幕需要：\\n1. 确保视频有清晰音频\\n2. 配置语音识别服务\\n3. 选择字幕样式\\n4. 点击生成"

        if any(w in msg for w in ["画质", "quality", "增强"]):
            return "画质增强可以：\\n• 提升分辨率\\n• 减少噪点\\n• 优化色彩\\n• 稳定画面\\n\\n建议预览后导出。"

        if any(w in msg for w in ["解说", "commentary", "创作"]):
            return "视频解说可以：\\n• 分析内容风格\\n• 生成文案\\n• 匹配音乐\\n• 制作配音\\n\\n请先选择视频片段。"

        return "我理解您的需求。作为AI视频助手，我可以帮您处理各种视频任务。请告诉我具体需要什么帮助！"

    def cleanup(self):
        """清理资源"""
        # 停止刷新定时器
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        # 清理聊天记录
        if hasattr(self, 'chat_history'):
            self.chat_history.clear()
        # 断开信号连接
        self.disconnect()
