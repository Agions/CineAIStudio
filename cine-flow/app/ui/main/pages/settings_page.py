#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlow 设置页面
简洁实用，包含：API Key 配置、路径设置、快捷跳转
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QScrollArea, QFileDialog, QMessageBox,
    QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor

from .base_page import BasePage


class SettingRow(QFrame):
    """单行设置项"""

    def __init__(self, label: str, description: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame { background: transparent; padding: 8px 0; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(4)

        # 标签
        lbl = QLabel(label)
        lbl.setFont(QFont("", 14, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #DDD;")
        layout.addWidget(lbl)

        # 描述
        if description:
            desc = QLabel(description)
            desc.setStyleSheet("color: #777; font-size: 12px;")
            desc.setWordWrap(True)
            layout.addWidget(desc)

        # 内容区（子类填充）
        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(0, 4, 0, 0)
        self.content_layout.setSpacing(8)
        layout.addLayout(self.content_layout)


class SettingCard(QFrame):
    """设置卡片"""

    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame#settingCard {
                background: #1E1E1E;
                border: 1px solid #333;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        self.setObjectName("settingCard")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 16, 20, 16)
        self._layout.setSpacing(4)

        # 标题
        title_label = QLabel(f"{icon}  {title}" if icon else title)
        title_label.setFont(QFont("", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #FFF;")
        self._layout.addWidget(title_label)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #333;")
        self._layout.addWidget(line)

    def add_widget(self, widget):
        self._layout.addWidget(widget)


def _find_jianying_drafts() -> str:
    """自动查找剪映草稿目录"""
    candidates = [
        Path.home() / "Movies" / "JianyingPro" / "User Data" / "Projects" / "com.lveditor.draft",
        Path.home() / "Movies" / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft",
        Path.home() / "Documents" / "JianyingPro" / "User Data" / "Projects",
        # Windows
        Path.home() / "AppData" / "Local" / "JianyingPro" / "User Data" / "Projects" / "com.lveditor.draft",
        Path.home() / "AppData" / "Local" / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return str(Path.home() / "Movies" / "JianyingPro" / "User Data" / "Projects" / "com.lveditor.draft")


class SettingsPage(BasePage):
    """设置页面"""

    config_saved = pyqtSignal()

    def __init__(self, application):
        super().__init__("settings", "设置", application)
        self._inputs = {}  # type: Dict[str, QLineEdit]

    def initialize(self) -> bool:
        try:
            self.logger.info("[设置] Initializing settings page")
            return True
        except Exception as e:
            self.logger.error(f"初始化设置失败: {e}")
            return False

    def create_content(self) -> None:
        """创建设置页面内容"""
        layout = self.main_layout
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: #121212; }")

        content = QWidget()
        content.setStyleSheet("background: #121212;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(48, 40, 48, 40)
        content_layout.setSpacing(24)

        # ── 标题 ──
        title = QLabel("⚙️ 设置")
        title.setFont(QFont("", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFF;")
        content_layout.addWidget(title)

        # ── API Key 配置 ──
        api_card = SettingCard("API 密钥", "🔑")

        api_keys = [
            ("openai_key", "OpenAI API Key", "用于 GPT-5 画面分析、Whisper 语音转字幕", "sk-..."),
            ("qwen_key", "通义千问 API Key", "用于通义千问 VL 视觉分析", "sk-..."),
            ("gemini_key", "Gemini API Key", "用于 Gemini 视频直传理解", "AIza..."),
            ("kimi_key", "Kimi API Key", "月之暗面 Moonshot AI", "sk-..."),
            ("glm_key", "智谱 GLM API Key", "智谱清言 GLM-5", "..."),
        ]

        for key_id, name, desc, placeholder in api_keys:
            row = SettingRow(name, desc)
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            inp.setEchoMode(QLineEdit.EchoMode.Password)
            inp.setStyleSheet("""
                QLineEdit {
                    background: #1A1A1A; border: 1px solid #333;
                    border-radius: 6px; padding: 8px 12px;
                    color: #DDD; font-size: 13px;
                }
                QLineEdit:focus { border-color: #2962FF; }
            """)
            inp.setMinimumWidth(300)

            # 加载已有值
            env_map = {
                "openai_key": "OPENAI_API_KEY",
                "qwen_key": "QWEN_API_KEY",
                "gemini_key": "GEMINI_API_KEY",
                "kimi_key": "MOONSHOT_API_KEY",
                "glm_key": "GLM_API_KEY",
            }
            env_val = os.getenv(env_map.get(key_id, ""), "")
            if env_val:
                inp.setText(env_val)

            row.content_layout.addWidget(inp, 1)

            # 显示/隐藏按钮
            toggle_btn = QPushButton("👁")
            toggle_btn.setFixedSize(36, 36)
            toggle_btn.setStyleSheet("QPushButton { background: #333; border-radius: 6px; } QPushButton:hover { background: #444; }")

            def _make_toggle(input_field):
                def _toggle():
                    if input_field.echoMode() == QLineEdit.EchoMode.Password:
                        input_field.setEchoMode(QLineEdit.EchoMode.Normal)
                    else:
                        input_field.setEchoMode(QLineEdit.EchoMode.Password)
                return _toggle

            toggle_btn.clicked.connect(_make_toggle(inp))
            row.content_layout.addWidget(toggle_btn)

            self._inputs[key_id] = inp
            api_card.add_widget(row)

        content_layout.addWidget(api_card)

        # ── 路径配置 ──
        path_card = SettingCard("路径设置", "📂")

        # 1. 项目存储位置
        default_project_dir = str(Path.home() / "ClipFlow" / "Projects")
        row1 = SettingRow("项目文件存储位置", "ClipFlow 创建的项目文件保存位置")
        self._inputs["project_dir"] = self._create_path_input(
            row1, default_project_dir)
        path_card.add_widget(row1)

        # 2. 剪映草稿位置（自动检测）
        jianying_dir = _find_jianying_drafts()
        row2 = SettingRow("剪映草稿位置", "剪映/CapCut 草稿目录（已自动检测，可修改）")
        self._inputs["jianying_dir"] = self._create_path_input(
            row2, jianying_dir)
        path_card.add_widget(row2)

        content_layout.addWidget(path_card)

        # ── 快捷跳转 ──
        shortcut_card = SettingCard("快捷跳转", "🚀")

        shortcuts = [
            ("📂 打开项目目录", lambda: self._open_path(self._inputs["project_dir"].text())),
            ("🎬 打开剪映草稿目录", lambda: self._open_path(self._inputs["jianying_dir"].text())),
            ("📁 打开配置目录", lambda: self._open_path(
                str(Path(__file__).parent.parent.parent.parent.parent / "config"))),
            ("📄 查看日志", lambda: self._open_path(
                str(Path.home() / "ClipFlow" / "logs"))),
        ]

        for name, handler in shortcuts:
            btn = QPushButton(name)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent; border: 1px solid #333;
                    border-radius: 8px; padding: 10px 16px;
                    color: #DDD; font-size: 14px; text-align: left;
                }
                QPushButton:hover { background: #252525; border-color: #2962FF; }
            """)
            btn.clicked.connect(handler)
            shortcut_card.add_widget(btn)

        content_layout.addWidget(shortcut_card)

        # ── 保存按钮 ──
        save_row = QHBoxLayout()
        save_row.addStretch()

        save_btn = QPushButton("💾 保存设置")
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.setStyleSheet("""
            QPushButton {
                background: #2962FF; color: white;
                border-radius: 8px; padding: 12px 32px;
                font-size: 15px; font-weight: bold;
            }
            QPushButton:hover { background: #448AFF; }
        """)
        save_btn.clicked.connect(self._save_settings)
        save_row.addWidget(save_btn)
        content_layout.addLayout(save_row)

        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _create_path_input(self, row: SettingRow, default: str) -> QLineEdit:
        """创建路径输入框 + 浏览按钮"""
        inp = QLineEdit(default)
        inp.setStyleSheet("""
            QLineEdit {
                background: #1A1A1A; border: 1px solid #333;
                border-radius: 6px; padding: 8px 12px;
                color: #DDD; font-size: 13px;
            }
            QLineEdit:focus { border-color: #2962FF; }
        """)
        row.content_layout.addWidget(inp, 1)

        browse_btn = QPushButton("浏览")
        browse_btn.setStyleSheet("""
            QPushButton {
                background: #333; color: #DDD; border-radius: 6px;
                padding: 8px 16px; font-size: 13px;
            }
            QPushButton:hover { background: #444; }
        """)

        def _browse():
            path = QFileDialog.getExistingDirectory(self, "选择目录", inp.text())
            if path:
                inp.setText(path)

        browse_btn.clicked.connect(_browse)
        row.content_layout.addWidget(browse_btn)

        return inp

    def _save_settings(self):
        """保存设置"""
        config_manager = self.application.get_service_by_name("config_manager")

        # 保存 API keys 到 .env
        env_map = {
            "openai_key": "OPENAI_API_KEY",
            "qwen_key": "QWEN_API_KEY",
            "gemini_key": "GEMINI_API_KEY",
            "kimi_key": "MOONSHOT_API_KEY",
            "glm_key": "GLM_API_KEY",
        }

        env_lines = []
        for key_id, env_name in env_map.items():
            inp = self._inputs.get(key_id)
            if inp and inp.text().strip():
                val = inp.text().strip()
                env_lines.append(f"{env_name}={val}")
                os.environ[env_name] = val

        # 写入 .env
        env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
        try:
            env_path.write_text("\n".join(env_lines) + "\n", encoding="utf-8")
        except Exception as e:
            self.logger.error(f"保存 .env 失败: {e}")

        # 保存路径设置
        project_dir = self._inputs.get("project_dir")
        jianying_dir = self._inputs.get("jianying_dir")

        if config_manager:
            if project_dir:
                config_manager.set("project_dir", project_dir.text())
                # 确保目录存在
                Path(project_dir.text()).mkdir(parents=True, exist_ok=True)
            if jianying_dir:
                config_manager.set("jianying_draft_dir", jianying_dir.text())

        QMessageBox.information(self, "保存成功", "设置已保存 ✅\nAPI Key 已写入 .env 文件")
        self.config_saved.emit()

    def _open_path(self, path: str):
        """打开目录"""
        p = Path(path)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)

        if sys.platform == "darwin":
            subprocess.Popen(["open", str(p)])
        elif sys.platform == "win32":
            os.startfile(str(p))
        else:
            subprocess.Popen(["xdg-open", str(p)])

    def on_activated(self) -> None:
        pass

    def on_deactivated(self) -> None:
        pass
