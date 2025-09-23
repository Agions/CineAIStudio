"""
AI对话页面 - AI助手对话功能
"""

from typing import Optional, Dict, Any, List
import json
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel,
    QTextEdit, QLineEdit, QPushButton, QScrollArea, QFrame,
    QProgressBar, QListWidget, QListWidgetItem, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize, QThread
from PyQt6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor

from .base_page import BasePage
from ...common.widgets.chat_message import ChatMessage
from ...common.widgets.ai_suggestion import AISuggestion
from ...common.widgets.loading_indicator import LoadingIndicator


class AIChatPage(BasePage):
    """AI对话页面"""

    def __init__(self, application):
        super().__init__("ai_chat", "AI对话", application)

        # 页面组件
        self.chat_history = None
        self.message_input = None
        self.send_button = None
        self.suggestion_panel = None
        self.loading_indicator = None
        self.ai_settings_panel = None

        # AI配置
        self.ai_provider = "openai"
        self.ai_model = "gpt-4"
        self.api_key = ""
        self.base_url = ""

        # 聊天历史
        self.messages = []
        self.is_processing = False

        # AI服务
        self.ai_service = None

    def initialize(self) -> bool:
        """初始化页面"""
        try:
            self.log_info("Initializing AI chat page")

            # 加载AI配置
            self._load_ai_config()

            # 初始化AI服务
            self._initialize_ai_service()

            return True

        except Exception as e:
            self.handle_error(e, "initialize")
            return False

    def create_content(self) -> None:
        """创建页面内容"""
        # 创建主分割器
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.add_widget_to_main_layout(main_splitter)

        # 创建左侧聊天区域
        left_panel = self._create_chat_panel()
        main_splitter.addWidget(left_panel)

        # 创建右侧设置区域
        right_panel = self._create_settings_panel()
        main_splitter.addWidget(right_panel)

        # 设置分割器比例
        main_splitter.setStretchFactor(0, 7)  # 聊天区域
        main_splitter.setStretchFactor(1, 3)  # 设置区域

        # 连接信号
        self._connect_signals()

        self.log_info("AI chat page content created")

    def _create_chat_panel(self) -> QWidget:
        """创建聊天面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建聊天历史区域
        self.chat_history = self._create_chat_history()
        layout.addWidget(self.chat_history)

        # 创建AI建议面板
        self.suggestion_panel = self._create_suggestion_panel()
        layout.addWidget(self.suggestion_panel)

        # 创建输入区域
        input_area = self._create_input_area()
        layout.addWidget(input_area)

        return panel

    def _create_chat_history(self) -> QScrollArea:
        """创建聊天历史区域"""
        scroll_area = QScrollArea()
        scroll_area.setObjectName("chat_history")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 创建聊天历史容器
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        history_layout.setContentsMargins(10, 10, 10, 10)
        history_layout.setSpacing(10)
        history_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_area.setWidget(history_widget)
        self.chat_history_container = history_widget

        # 设置样式
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #1E1E1E;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)

        return scroll_area

    def _create_suggestion_panel(self) -> QWidget:
        """创建AI建议面板"""
        panel = QWidget()
        panel.setMaximumHeight(120)
        panel.setObjectName("suggestion_panel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)

        # 标题
        title_label = QLabel("💡 AI建议")
        title_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title_label)

        # 建议按钮区域
        suggestions_layout = QHBoxLayout()
        suggestions_layout.setSpacing(8)

        # 创建建议按钮
        suggestions = [
            ("帮我分析视频", "analyze_video"),
            ("生成字幕", "generate_subtitle"),
            ("优化画质", "enhance_quality"),
            ("创作解说", "create_commentary")
        ]

        for text, action in suggestions:
            suggestion_btn = AISuggestion(text, action)
            suggestion_btn.clicked.connect(lambda checked, a=action: self._on_suggestion_clicked(a))
            suggestions_layout.addWidget(suggestion_btn)

        layout.addLayout(suggestions_layout)

        # 设置样式
        panel.setStyleSheet("""
            QWidget#suggestion_panel {
                background-color: #2D2D2D;
                border-top: 1px solid #404040;
            }
        """)

        return panel

    def _create_input_area(self) -> QWidget:
        """创建输入区域"""
        panel = QWidget()
        panel.setMaximumHeight(80)
        panel.setObjectName("input_area")

        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 创建输入框
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("输入您的问题...")
        self.message_input.setMaxLength(1000)
        self.message_input.returnPressed.connect(self._on_send_message)

        layout.addWidget(self.message_input)

        # 创建发送按钮
        self.send_button = QPushButton("发送")
        self.send_button.setFixedSize(80, 35)
        self.send_button.clicked.connect(self._on_send_message)

        layout.addWidget(self.send_button)

        # 设置样式
        panel.setStyleSheet("""
            QWidget#input_area {
                background-color: #2D2D2D;
                border-top: 1px solid #404040;
            }
            QLineEdit {
                background-color: #3D3D3D;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
        """)

        return panel

    def _create_settings_panel(self) -> QWidget:
        """创建设置面板"""
        panel = QWidget()
        panel.setMaximumWidth(300)
        panel.setObjectName("settings_panel")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # 标题
        title_label = QLabel("⚙️ AI设置")
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title_label)

        # AI服务选择
        service_label = QLabel("AI服务:")
        service_label.setStyleSheet("color: #CCCCCC; font-size: 12px;")
        layout.addWidget(service_label)

        # 这里可以添加AI服务选择的下拉框等组件
        # 暂时使用简单的标签
        current_service = QLabel(f"当前: {self.ai_provider}")
        current_service.setStyleSheet("color: #999999; font-size: 11px;")
        layout.addWidget(current_service)

        layout.addStretch()

        # API密钥状态
        api_status = QLabel("🔑 API密钥: " + ("已配置" if self.api_key else "未配置"))
        api_status.setStyleSheet("color: #4CAF50; font-size: 11px;")
        layout.addWidget(api_status)

        # 设置按钮
        settings_btn = QPushButton("⚙️ 详细设置")
        settings_btn.clicked.connect(self._on_open_settings)
        layout.addWidget(settings_btn)

        # 设置样式
        panel.setStyleSheet("""
            QWidget#settings_panel {
                background-color: #1E1E1E;
                border-left: 1px solid #404040;
            }
        """)

        return panel

    def _connect_signals(self) -> None:
        """连接信号"""
        # 监听AI事件
        self.on_event("ai_response_received", self._on_ai_response)
        self.on_event("ai_error_occurred", self._on_ai_error)

    def _on_ai_response(self, data) -> None:
        """AI响应处理"""
        # 处理AI响应事件
        if hasattr(data, 'response'):
            self._add_message_to_chat("AI", data.response)
        self.update_status("AI响应已接收")

    def _on_ai_error(self, data) -> None:
        """AI错误处理"""
        # 处理AI错误事件
        error_message = getattr(data, 'error', 'Unknown AI error')
        self.show_error(f"AI错误: {error_message}")
        self.update_status("AI发生错误")

    def _load_ai_config(self) -> None:
        """加载AI配置"""
        if self.config_manager:
            self.ai_provider = self.get_config_value("ai.provider", "openai")
            self.ai_model = self.get_config_value("ai.model", "gpt-4")
            self.api_key = self.get_config_value("ai.api_key", "")
            self.base_url = self.get_config_value("ai.base_url", "")

    def _initialize_ai_service(self) -> None:
        """初始化AI服务"""
        # 这里可以初始化各种AI服务的客户端
        # 由于依赖问题，这里暂时使用模拟服务
        self.ai_service = MockAIService(self.api_key, self.base_url)

    def _on_send_message(self) -> None:
        """发送消息"""
        if self.is_processing:
            return

        message = self.message_input.text().strip()
        if not message:
            return

        # 添加用户消息到聊天历史
        self._add_message("user", message)

        # 清空输入框
        self.message_input.clear()

        # 禁用发送按钮
        self.set_processing_state(True)

        # 发送AI请求
        self._send_ai_request(message)

    def _on_suggestion_clicked(self, action: str) -> None:
        """建议按钮点击"""
        suggestions = {
            "analyze_video": "帮我分析这段视频的内容和特点",
            "generate_subtitle": "为这个视频生成字幕",
            "enhance_quality": "如何优化这个视频的画质？",
            "create_commentary": "为这个视频创作一个解说"
        }

        if action in suggestions:
            self.message_input.setText(suggestions[action])
            self.message_input.setFocus()

    def _on_open_settings(self) -> None:
        """打开设置"""
        self.request_action("open_ai_settings")

    def _send_ai_request(self, message: str) -> None:
        """发送AI请求"""
        try:
            # 添加加载指示器
            self._add_loading_indicator()

            # 发送请求到AI服务
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

    def _on_ai_response_received(self, response: str) -> None:
        """AI响应处理"""
        try:
            # 移除加载指示器
            self._remove_loading_indicator()

            # 添加AI响应到聊天历史
            self._add_message("assistant", response)

            # 更新处理状态
            self.set_processing_state(False)

            # 发送事件
            self.emit_event("ai_response_received", {"response": response})

        except Exception as e:
            self.handle_error(e, "handle_ai_response")
            self._handle_ai_error("处理AI响应失败")

    def _on_ai_error_received(self, error: str) -> None:
        """AI错误处理"""
        try:
            # 移除加载指示器
            self._remove_loading_indicator()

            # 添加错误消息
            self._add_error_message(error)

            # 更新处理状态
            self.set_processing_state(False)

            # 发送事件
            self.emit_event("ai_error_occurred", {"error": error})

        except Exception as e:
            self.handle_error(e, "handle_ai_error")

    def _add_message(self, role: str, content: str) -> None:
        """添加消息到聊天历史"""
        try:
            # 创建消息组件
            message_widget = ChatMessage(role, content, datetime.now())

            # 添加到聊天历史
            self.chat_history_container.layout().addWidget(message_widget)

            # 添加到消息列表
            self.messages.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })

            # 滚动到底部
            QTimer.singleShot(100, self._scroll_to_bottom)

        except Exception as e:
            self.handle_error(e, "add_message")

    def _add_error_message(self, error: str) -> None:
        """添加错误消息"""
        error_message = f"❌ {error}"
        self._add_message("assistant", error_message)

    def _add_loading_indicator(self) -> None:
        """添加加载指示器"""
        if hasattr(self, '_current_loading_indicator'):
            return

        self._current_loading_indicator = LoadingIndicator()
        self.chat_history_container.layout().addWidget(self._current_loading_indicator)
        self._scroll_to_bottom()

    def _remove_loading_indicator(self) -> None:
        """移除加载指示器"""
        if hasattr(self, '_current_loading_indicator'):
            self._current_loading_indicator.deleteLater()
            del self._current_loading_indicator

    def _scroll_to_bottom(self) -> None:
        """滚动到底部"""
        if self.chat_history:
            scrollbar = self.chat_history.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def set_processing_state(self, processing: bool) -> None:
        """设置处理状态"""
        self.is_processing = processing

        if self.send_button:
            self.send_button.setEnabled(not processing)
            self.send_button.setText("处理中..." if processing else "发送")

        if self.message_input:
            self.message_input.setEnabled(not processing)

    def _handle_ai_error(self, error_message: str) -> None:
        """处理AI错误"""
        self.show_error(error_message)
        self.set_processing_state(False)

    def clear_chat(self) -> None:
        """清空聊天"""
        try:
            # 清空消息列表
            self.messages.clear()

            # 清空聊天历史界面
            while self.chat_history_container.layout().count():
                item = self.chat_history_container.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # 添加欢迎消息
            welcome_message = "👋 您好！我是您的AI视频助手。我可以帮您：\n\n" \
                            "• 分析视频内容和特点\n" \
                            "• 生成视频字幕和配音\n" \
                            "• 优化视频画质和效果\n" \
                            "• 创作视频解说和文案\n\n" \
                            "请告诉我您需要什么帮助！"

            self._add_message("assistant", welcome_message)

        except Exception as e:
            self.handle_error(e, "clear_chat")

    def export_chat(self, file_path: str) -> bool:
        """导出聊天记录"""
        try:
            chat_data = {
                "export_time": datetime.now().isoformat(),
                "ai_provider": self.ai_provider,
                "ai_model": self.ai_model,
                "messages": self.messages
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(chat_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            self.handle_error(e, "export_chat")
            return False

    def import_chat(self, file_path: str) -> bool:
        """导入聊天记录"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)

            if "messages" in chat_data:
                self.messages = chat_data["messages"]

                # 重新构建聊天界面
                self.clear_chat()
                for message in self.messages[1:]:  # 跳过欢迎消息
                    self._add_message(message["role"], message["content"])

                return True

            return False

        except Exception as e:
            self.handle_error(e, "import_chat")
            return False

    def save_state(self) -> None:
        """保存页面状态"""
        self.page_state = {
            'messages': self.messages,
            'ai_provider': self.ai_provider,
            'ai_model': self.ai_model
        }

    def restore_state(self) -> None:
        """恢复页面状态"""
        if 'messages' in self.page_state:
            self.messages = self.page_state['messages']

        if 'ai_provider' in self.page_state:
            self.ai_provider = self.page_state['ai_provider']

        if 'ai_model' in self.page_state:
            self.ai_model = self.page_state['ai_model']

        # 重建聊天界面
        if self.messages:
            while self.chat_history_container.layout().count():
                item = self.chat_history_container.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            for message in self.messages:
                self._add_message(message["role"], message["content"])

    def cleanup(self) -> None:
        """清理资源"""
        # 清理AI服务
        if self.ai_service and hasattr(self.ai_service, 'cleanup'):
            self.ai_service.cleanup()

        # 清理消息列表
        self.messages.clear()


class MockAIService:
    """模拟AI服务"""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url

    def send_message(self, message: str, history: List[Dict],
                   callback, error_callback) -> None:
        """发送消息（模拟）"""
        # 模拟网络延迟
        import threading
        import time

        def mock_response():
            time.sleep(1)  # 模拟处理时间

            # 简单的关键词匹配回复
            response = self._generate_mock_response(message)

            # 在主线程中调用回调
            from PyQt6.QtCore import QMetaObject, Qt
            QMetaObject.invokeMethod(
                None,
                lambda: callback(response),
                Qt.ConnectionType.QueuedConnection
            )

        thread = threading.Thread(target=mock_response)
        thread.daemon = True
        thread.start()

    def _generate_mock_response(self, message: str) -> str:
        """生成模拟响应"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["分析", "analyze", "内容"]):
            return "我需要查看视频内容才能进行分析。请先在视频编辑页面导入视频，然后我可以帮您分析视频的内容特点、关键场景和优化建议。"

        elif any(word in message_lower for word in ["字幕", "subtitle", "生成"]):
            return "生成字幕需要访问视频的音频内容。建议您：\n1. 确保视频包含清晰的音频\n2. 在AI设置中配置语音识别服务\n3. 选择字幕语言和样式\n4. 点击生成按钮开始处理"

        elif any(word in message_lower for word in ["画质", "quality", "增强"]):
            return "画质增强功能可以：\n• 提升视频分辨率\n• 减少噪点和模糊\n• 优化色彩和对比度\n• 稳定视频画面\n\n建议在导出前进行预览，选择最适合的增强级别。"

        elif any(word in message_lower for word in ["解说", "commentary", "创作"]):
            return "视频解说创作需要了解视频内容。我可以帮您：\n• 分析视频主题和风格\n• 生成解说文案\n• 匹配背景音乐\n• 制作配音脚本\n\n请先选择要解说的视频片段。"

        else:
            return "我理解您的问题。作为您的AI视频助手，我可以帮您处理各种视频编辑和分析任务。请告诉我您的具体需求，我会提供详细的指导和建议。"

    def cleanup(self) -> None:
        """清理资源"""
        pass