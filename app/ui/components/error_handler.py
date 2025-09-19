#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
错误提示机制组件 - 提供优雅的错误处理和用户反馈
支持多种提示类型、动画效果和用户交互
"""

from typing import Optional, Dict, Any, List, Callable
from enum import Enum
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy, QGraphicsOpacityEffect,
    QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QPoint, QParallelAnimationGroup
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QIcon
from PyQt6.QtCore import QPointF

from .base_component import BaseComponent, ComponentConfig


class MessageType(Enum):
    """消息类型枚举"""
    ERROR = "error"              # 错误
    WARNING = "warning"          # 警告
    INFO = "info"                # 信息
    SUCCESS = "success"          # 成功
    QUESTION = "question"        # 询问


class MessageDuration(Enum):
    """消息持续时间枚举"""
    SHORT = 2000                # 短暂 (2秒)
    MEDIUM = 4000               # 中等 (4秒)
    LONG = 6000                 # 长时间 (6秒)
    INFINITE = -1               # 无限 (直到用户关闭)


class ToastMessage(QWidget):
    """Toast消息组件"""
    
    message_clicked = pyqtSignal(str)  # 消息被点击信号
    message_closed = pyqtSignal(str)  # 消息关闭信号
    
    def __init__(self, title: str, message: str, 
                 message_type: MessageType = MessageType.INFO,
                 duration: MessageDuration = MessageDuration.MEDIUM,
                 parent=None):
        super().__init__(parent)
        
        self.title = title
        self.message = message
        self.message_type = message_type
        self.duration = duration
        self.message_id = f"toast_{id(self)}"
        
        self._setup_ui()
        self._apply_styles()
        self._setup_animations()
    
    def _setup_ui(self):
        """设置UI"""
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        
        # 主布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # 图标
        self.icon_label = QLabel(self._get_icon())
        self.icon_label.setFixedSize(24, 24)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)
        
        # 内容区域
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        # 标题
        self.title_label = QLabel(self.title)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(self.title_label)
        
        # 消息
        self.message_label = QLabel(self.message)
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("font-size: 12px;")
        content_layout.addWidget(self.message_label)
        
        layout.addLayout(content_layout)
        
        # 关闭按钮
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.clicked.connect(self.close)
        layout.addWidget(self.close_btn)
        
        # 设置鼠标样式
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 设置固定宽度
        self.setFixedWidth(350)
    
    def _apply_styles(self):
        """应用样式"""
        colors = self._get_colors()
        
        self.setStyleSheet(f"""
            ToastMessage {{
                background-color: {colors['background']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                color: {colors['text']};
            }}
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {colors['text']};
                font-size: 16px;
                font-weight: bold;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: {colors['hover']};
            }}
        """)
    
    def _get_colors(self) -> Dict[str, str]:
        """获取颜色方案"""
        color_schemes = {
            MessageType.ERROR: {
                'background': '#ffebee',
                'border': '#f44336',
                'text': '#c62828',
                'hover': 'rgba(244, 67, 54, 0.1)'
            },
            MessageType.WARNING: {
                'background': '#fff8e1',
                'border': '#ffc107',
                'text': '#f57c00',
                'hover': 'rgba(255, 193, 7, 0.1)'
            },
            MessageType.INFO: {
                'background': '#e3f2fd',
                'border': '#2196f3',
                'text': '#1565c0',
                'hover': 'rgba(33, 150, 243, 0.1)'
            },
            MessageType.SUCCESS: {
                'background': '#e8f5e8',
                'border': '#4caf50',
                'text': '#2e7d32',
                'hover': 'rgba(76, 175, 80, 0.1)'
            },
            MessageType.QUESTION: {
                'background': '#f3e5f5',
                'border': '#9c27b0',
                'text': '#6a1b9a',
                'hover': 'rgba(156, 39, 176, 0.1)'
            }
        }
        return color_schemes.get(self.message_type, color_schemes[MessageType.INFO])
    
    def _get_icon(self) -> str:
        """获取图标"""
        icons = {
            MessageType.ERROR: "❌",
            MessageType.WARNING: "⚠️",
            MessageType.INFO: "ℹ️",
            MessageType.SUCCESS: "✅",
            MessageType.QUESTION: "❓"
        }
        return icons.get(self.message_type, "ℹ️")
    
    def _setup_animations(self):
        """设置动画"""
        # 透明度效果
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        # 设置自动关闭
        if self.duration.value > 0:
            QTimer.singleShot(self.duration.value, self._start_close_animation)
    
    def show_event(self, event):
        """显示事件 - 触发显示动画"""
        self._start_show_animation()
        super().show_event(event)
    
    def _start_show_animation(self):
        """开始显示动画"""
        # 淡入动画
        fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_in.setDuration(300)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        # 滑入动画
        if self.parent():
            parent_rect = self.parent().rect()
            start_pos = QPoint(parent_rect.width() - self.width() - 20, -self.height())
            end_pos = QPoint(parent_rect.width() - self.width() - 20, 20)
        else:
            start_pos = QPoint(100, -self.height())
            end_pos = QPoint(100, 100)
        
        self.move(start_pos)
        
        slide_in = QPropertyAnimation(self, b"pos")
        slide_in.setDuration(300)
        slide_in.setStartValue(start_pos)
        slide_in.setEndValue(end_pos)
        slide_in.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        # 并行动画
        animation_group = QParallelAnimationGroup()
        animation_group.addAnimation(fade_in)
        animation_group.addAnimation(slide_in)
        animation_group.start()
    
    def _start_close_animation(self):
        """开始关闭动画"""
        # 淡出动画
        fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_out.setDuration(200)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InQuad)
        
        # 滑出动画
        current_pos = self.pos()
        end_pos = QPoint(current_pos.x(), current_pos.y() - self.height())
        
        slide_out = QPropertyAnimation(self, b"pos")
        slide_out.setDuration(200)
        slide_out.setStartValue(current_pos)
        slide_out.setEndValue(end_pos)
        slide_out.setEasingCurve(QEasingCurve.Type.InQuad)
        
        # 动画完成后关闭
        fade_out.finished.connect(self.close)
        slide_out.finished.connect(self.close)
        
        # 并行动画
        animation_group = QParallelAnimationGroup()
        animation_group.addAnimation(fade_out)
        animation_group.addAnimation(slide_out)
        animation_group.start()
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        self.message_clicked.emit(self.message_id)
        super().mousePressEvent(event)
    
    def closeEvent(self, event):
        """关闭事件"""
        self.message_closed.emit(self.message_id)
        super().closeEvent(event)


class ToastManager(BaseComponent):
    """Toast消息管理器"""
    
    def __init__(self, parent=None, config: Optional[ComponentConfig] = None):
        if config is None:
            config = ComponentConfig(
                name="ToastManager",
                theme_support=True,
                auto_save=False
            )
        super().__init__(parent, config)
        
        self.active_toasts: List[ToastMessage] = []
        self.max_toasts = 5
        self.toast_spacing = 10
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 管理器本身不需要UI，只是管理Toast消息
        pass
    
    def show_toast(self, title: str, message: str, 
                  message_type: MessageType = MessageType.INFO,
                  duration: MessageDuration = MessageDuration.MEDIUM,
                  position: str = "top_right") -> str:
        """显示Toast消息"""
        
        # 如果超过最大数量，移除最旧的消息
        if len(self.active_toasts) >= self.max_toasts:
            oldest_toast = self.active_toasts.pop(0)
            oldest_toast.close()
        
        # 创建Toast消息
        toast = ToastMessage(title, message, message_type, duration, self.parent())
        
        # 设置位置
        self._position_toast(toast, position)
        
        # 连接信号
        toast.message_closed.connect(self._on_toast_closed)
        
        # 显示消息
        toast.show()
        
        # 添加到活动列表
        self.active_toasts.append(toast)
        
        # 重新排列现有消息
        self._rearrange_toasts(position)
        
        return toast.message_id
    
    def _position_toast(self, toast: ToastMessage, position: str):
        """定位Toast消息"""
        if not self.parent():
            return
        
        parent_rect = self.parent().rect()
        
        if position == "top_right":
            x = parent_rect.width() - toast.width() - 20
            y = 20
        elif position == "top_left":
            x = 20
            y = 20
        elif position == "bottom_right":
            x = parent_rect.width() - toast.width() - 20
            y = parent_rect.height() - toast.height() - 20
        elif position == "bottom_left":
            x = 20
            y = parent_rect.height() - toast.height() - 20
        else:  # center
            x = (parent_rect.width() - toast.width()) // 2
            y = (parent_rect.height() - toast.height()) // 2
        
        toast.move(x, y)
    
    def _rearrange_toasts(self, position: str):
        """重新排列Toast消息"""
        if not self.parent():
            return
        
        parent_rect = self.parent().rect()
        
        for i, toast in enumerate(self.active_toasts):
            if position == "top_right":
                x = parent_rect.width() - toast.width() - 20
                y = 20 + i * (toast.height() + self.toast_spacing)
            elif position == "top_left":
                x = 20
                y = 20 + i * (toast.height() + self.toast_spacing)
            elif position == "bottom_right":
                x = parent_rect.width() - toast.width() - 20
                y = parent_rect.height() - (i + 1) * (toast.height() + self.toast_spacing) - 20
            elif position == "bottom_left":
                x = 20
                y = parent_rect.height() - (i + 1) * (toast.height() + self.toast_spacing) - 20
            else:  # center
                x = (parent_rect.width() - toast.width()) // 2
                y = (parent_rect.height() - toast.height()) // 2
            
            # 动画移动到新位置
            current_pos = toast.pos()
            if current_pos != QPoint(x, y):
                animation = QPropertyAnimation(toast, b"pos")
                animation.setDuration(200)
                animation.setStartValue(current_pos)
                animation.setEndValue(QPoint(x, y))
                animation.setEasingCurve(QEasingCurve.Type.OutQuad)
                animation.start()
    
    def _on_toast_closed(self, message_id: str):
        """Toast关闭事件处理"""
        # 从活动列表中移除
        self.active_toasts = [toast for toast in self.active_toasts 
                           if toast.message_id != message_id]
        
        # 重新排列剩余的消息
        if self.active_toasts:
            # 确定位置（基于第一个消息的位置）
            first_toast = self.active_toasts[0]
            parent_rect = self.parent().rect() if self.parent() else QRect(0, 0, 800, 600)
            
            if first_toast.x() > parent_rect.width() // 2:
                position = "top_right"
            else:
                position = "top_left"
            
            self._rearrange_toasts(position)
    
    def show_error(self, title: str, message: str, duration: MessageDuration = MessageDuration.LONG) -> str:
        """显示错误消息"""
        return self.show_toast(title, message, MessageType.ERROR, duration)
    
    def show_warning(self, title: str, message: str, duration: MessageDuration = MessageDuration.MEDIUM) -> str:
        """显示警告消息"""
        return self.show_toast(title, message, MessageType.WARNING, duration)
    
    def show_info(self, title: str, message: str, duration: MessageDuration = MessageDuration.MEDIUM) -> str:
        """显示信息消息"""
        return self.show_toast(title, message, MessageType.INFO, duration)
    
    def show_success(self, title: str, message: str, duration: MessageDuration = MessageDuration.SHORT) -> str:
        """显示成功消息"""
        return self.show_toast(title, message, MessageType.SUCCESS, duration)
    
    def show_question(self, title: str, message: str, duration: MessageDuration = MessageDuration.INFINITE) -> str:
        """显示询问消息"""
        return self.show_toast(title, message, MessageType.QUESTION, duration)
    
    def clear_all_toasts(self):
        """清除所有Toast消息"""
        for toast in self.active_toasts[:]:
            toast.close()
        self.active_toasts.clear()


class ErrorDialog(QWidget):
    """错误对话框"""
    
    def __init__(self, title: str, message: str, 
                 details: Optional[str] = None,
                 parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(500, 350)
        
        self._setup_ui(title, message, details)
        self._apply_styles()
    
    def _setup_ui(self, title: str, message: str, details: Optional[str]):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 标题和图标
        header_layout = QHBoxLayout()
        
        icon_label = QLabel("❌")
        icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #d32f2f;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 消息
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(message_label)
        
        # 详细信息（如果有）
        if details:
            details_group = QFrame()
            details_group.setFrameStyle(QFrame.Shape.StyledPanel)
            details_layout = QVBoxLayout(details_group)
            
            details_title = QLabel("详细信息:")
            details_title.setStyleSheet("font-weight: bold; font-size: 12px;")
            details_layout.addWidget(details_title)
            
            details_text = QLabel(details)
            details_text.setWordWrap(True)
            details_text.setStyleSheet("font-size: 11px; color: #666; font-family: monospace;")
            details_layout.addWidget(details_text)
            
            layout.addWidget(details_group)
        
        layout.addStretch()
        
        # 按钮
        button_layout = QHBoxLayout()
        
        copy_btn = QPushButton("复制错误信息")
        copy_btn.clicked.connect(self._copy_error_info)
        button_layout.addWidget(copy_btn)
        
        button_layout.addStretch()
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.close)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                color: #333333;
            }
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #007acc;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
    
    def _copy_error_info(self):
        """复制错误信息到剪贴板"""
        from PyQt6.QtGui import QGuiApplication
        from PyQt6.QtCore import QMimeData
        
        clipboard = QGuiApplication.clipboard()
        mime_data = QMimeData()
        
        error_text = f"错误: {self.windowTitle()}\n消息: {self.findChild(QLabel).text()}"
        
        # 添加详细信息
        details_label = self.findChild(QFrame)
        if details_label:
            details_text = details_label.findChild(QLabel).text()
            if details_text != "详细信息:":
                error_text += f"\n详细信息: {details_text}"
        
        mime_data.setText(error_text)
        clipboard.setMimeData(mime_data)
        
        # 显示复制成功提示
        from .loading_indicator import ToastManager
        if self.parent():
            toast_manager = ToastManager(self.parent())
            toast_manager.show_success("复制成功", "错误信息已复制到剪贴板")


# 工厂函数
def create_toast_manager(parent=None) -> ToastManager:
    """创建Toast管理器"""
    return ToastManager(parent)


def create_error_dialog(title: str, message: str, 
                       details: Optional[str] = None,
                       parent=None) -> ErrorDialog:
    """创建错误对话框"""
    return ErrorDialog(title, message, details, parent)


# 全局实例
_global_toast_manager = None


def get_global_toast_manager() -> ToastManager:
    """获取全局Toast管理器"""
    global _global_toast_manager
    if _global_toast_manager is None:
        _global_toast_manager = create_toast_manager()
    return _global_toast_manager


def show_error(title: str, message: str, duration: MessageDuration = MessageDuration.LONG) -> str:
    """显示错误消息（全局）"""
    return get_global_toast_manager().show_error(title, message, duration)


def show_warning(title: str, message: str, duration: MessageDuration = MessageDuration.MEDIUM) -> str:
    """显示警告消息（全局）"""
    return get_global_toast_manager().show_warning(title, message, duration)


def show_info(title: str, message: str, duration: MessageDuration = MessageDuration.MEDIUM) -> str:
    """显示信息消息（全局）"""
    return get_global_toast_manager().show_info(title, message, duration)


def show_success(title: str, message: str, duration: MessageDuration = MessageDuration.SHORT) -> str:
    """显示成功消息（全局）"""
    return get_global_toast_manager().show_success(title, message, duration)


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
    
    app = QApplication(sys.argv)
    
    # 测试窗口
    window = QWidget()
    window.setWindowTitle("错误提示机制测试")
    window.resize(600, 400)
    
    layout = QVBoxLayout(window)
    
    # 创建Toast管理器
    toast_manager = create_toast_manager(window)
    
    # 创建测试按钮
    error_btn = QPushButton("显示错误消息")
    warning_btn = QPushButton("显示警告消息")
    info_btn = QPushButton("显示信息消息")
    success_btn = QPushButton("显示成功消息")
    question_btn = QPushButton("显示询问消息")
    dialog_btn = QPushButton("显示错误对话框")
    
    layout.addWidget(error_btn)
    layout.addWidget(warning_btn)
    layout.addWidget(info_btn)
    layout.addWidget(success_btn)
    layout.addWidget(question_btn)
    layout.addWidget(dialog_btn)
    
    def test_error():
        toast_manager.show_error("操作失败", "文件保存失败，请检查磁盘空间")
    
    def test_warning():
        toast_manager.show_warning("注意", "此操作不可撤销，请谨慎操作")
    
    def test_info():
        toast_manager.show_info("提示", "您的设置已保存")
    
    def test_success():
        toast_manager.show_success("成功", "文件上传完成")
    
    def test_question():
        toast_manager.show_question("确认", "您确定要删除此文件吗？")
    
    def test_dialog():
        dialog = create_error_dialog(
            "网络错误",
            "无法连接到服务器，请检查网络连接",
            "Error Code: 503\nService Unavailable\nURL: https://api.example.com/data\nTimestamp: 2024-01-15 10:30:45",
            window
        )
        dialog.show()
    
    error_btn.clicked.connect(test_error)
    warning_btn.clicked.connect(test_warning)
    info_btn.clicked.connect(test_info)
    success_btn.clicked.connect(test_success)
    question_btn.clicked.connect(test_question)
    dialog_btn.clicked.connect(test_dialog)
    
    window.show()
    sys.exit(app.exec())