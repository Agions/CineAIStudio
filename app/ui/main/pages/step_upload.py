"""
Step 1: 上传配置页
视频拖放 + 元数据显示 + 快速 AI 配置
"""

import os
import json
import subprocess
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QFrame, QGridLayout, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QDragEnterEvent, QDropEvent

from app.ui.components import (
    MacCard, MacTitleLabel, MacPrimaryButton, MacSecondaryButton,
    MacLabel, MacScrollArea
)
from app.services.video.monologue_maker import MonologueStyle, EmotionType


class VideoDropZone(QFrame):
    """
    视频拖放区域
    支持拖放文件或点击选择
    """

    file_selected = Signal(str)  # 选中视频路径

    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path: str = ""
        self._setup_ui()
        self.setAcceptDrops(True)
        self.setMinimumHeight(160)

    def _setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #30363D;
                border-radius: 12px;
                background: #161B22;
            }
            QFrame:hover {
                border-color: #388BFD;
                background: #1C2128;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        self.icon_label = QLabel("📹")
        self.icon_label.setFont(QFont("", 48))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)

        self.text_label = QLabel("拖放视频到这里\n或点击选择文件")
        self.text_label.setFont(QFont("", 14))
        self.text_label.setStyleSheet("color: #8B949E;")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self.text_label)

        self.select_btn = QPushButton("选择视频")
        self.select_btn.setObjectName("secondary_button")
        self.select_btn.setFixedSize(120, 36)
        self.select_btn.clicked.connect(self._select_file)
        layout.addWidget(self.select_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setMinimumWidth(400)

    def _select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择视频文件",
            "",
            "视频文件 (*.mp4 *.mov *.avi *.mkv *.webm);;所有文件 (*)"
        )
        if file_path:
            self._set_file(file_path)

    def _set_file(self, path: str):
        self.file_path = path
        name = Path(path).name
        self.text_label.setText(f"✅ {name}")
        self.text_label.setStyleSheet("color: #3FB950; font-weight: 600;")
        self.icon_label.setText("🎬")
        self.file_selected.emit(path)

    # ---- Drag & Drop ----
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and self._is_video(urls[0].toLocalFile()):
                event.acceptProposedAction()
                self._highlight(True)

    def dragLeaveEvent(self, event):
        self._highlight(False)

    def dropEvent(self, event):
        self._highlight(False)
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if self._is_video(path):
                self._set_file(path)

    def _is_video(self, path: str) -> bool:
        return Path(path).suffix.lower() in {
            ".mp4", ".mov", ".avi", ".mkv", ".webm"
        }

    def _highlight(self, on: bool):
        color = "#388BFD" if on else "#30363D"
        border = f"2px dashed {color}"
        self.setStyleSheet(
            f"QFrame {{ border: {border}; border-radius: 12px; background: #161B22; }}"
            + ("QFrame:hover { background: #1C2128; }" if on else "")
        )


class VideoMetadataPanel(QFrame):
    """视频元数据展示面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: #161B22;
                border-radius: 8px;
                border: 1px solid #21262D;
            }
        """)
        layout = QGridLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setHorizontalSpacing(24)
        layout.setVerticalSpacing(8)

        self.labels = {}
        items = [
            ("duration", "时长"),
            ("resolution", "分辨率"),
            ("size", "文件大小"),
            ("format", "格式"),
        ]
        for i, (key, label_text) in enumerate(items):
            lbl_name = QLabel(label_text)
            lbl_name.setStyleSheet("color: #8B949E; font-size: 12px;")
            layout.addWidget(lbl_name, i, 0)

            lbl_value = QLabel("—")
            lbl_value.setStyleSheet("color: #E6EDF3; font-size: 12px; font-weight: 600;")
            layout.addWidget(lbl_value, i, 1)
            self.labels[key] = lbl_value

    def set_metadata(self, path: str):
        """从视频文件路径提取元数据"""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet", "-print_format", "json",
                    "-show_format", "-show_streams", path
                ],
                capture_output=True, text=True, timeout=10
            )
            data = json.loads(result.stdout)
            fmt = data.get("format", {})

            # 时长
            dur = float(fmt.get("duration", 0))
            self.labels["duration"].setText(f"{int(dur//60)}:{int(dur%60):02d}")

            # 分辨率
            streams = data.get("streams", [])
            for s in streams:
                if s.get("codec_type") == "video":
                    w = s.get("width", "?")
                    h = s.get("height", "?")
                    self.labels["resolution"].setText(f"{w}×{h}")
                    break

            # 文件大小
            size = int(fmt.get("size", 0))
            if size > 1024**3:
                self.labels["size"].setText(f"{size/1024**3:.1f} GB")
            elif size > 1024**2:
                self.labels["size"].setText(f"{size/1024**2:.0f} MB")
            else:
                self.labels["size"].setText(f"{size/1024:.0f} KB")

            # 格式
            fmt_name = fmt.get("format_name", "")
            self.labels["format"].setText(fmt_name.split(",")[0])
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError, KeyError):
            # ffprobe 不可用或解析失败，静默跳过（元数据保持显示 "—"）
            pass


class StepUpload(QWidget):
    """
    向导 Step 1：上传与配置

    Signals:
        config_ready(video_path, context, emotion, style, output_dir)
        next_requested()
    """

    config_ready = Signal(str, str, str, object, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._video_path: str = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)

        # 标题
        title = MacTitleLabel("上传视频")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #E6EDF3;")
        layout.addWidget(title)

        # 副标题
        hint = QLabel("选择要制作解说视频的源文件")
        hint.setStyleSheet("color: #8B949E; font-size: 14px;")
        layout.addWidget(hint)

        # 视频拖放区
        self.drop_zone = VideoDropZone()
        self.drop_zone.file_selected.connect(self._on_video_selected)
        layout.addWidget(self.drop_zone)

        # 元数据面板
        self.meta_panel = VideoMetadataPanel()
        self.meta_panel.setVisible(False)
        layout.addWidget(self.meta_panel)

        # 配置区
        config_card = MacCard()
        config_layout = QGridLayout(config_card)
        config_layout.setContentsMargins(20, 20, 20, 20)
        config_layout.setSpacing(16)

        # 场景描述
        ctx_label = QLabel("场景描述")
        ctx_label.setStyleSheet("color: #C9D1D9; font-size: 13px;")
        config_layout.addWidget(ctx_label, 0, 0)

        self.ctx_input = QLineEdit()
        self.ctx_input.setPlaceholderText("例如：深夜独自走在街头，回忆涌上心头...")
        self.ctx_input.setMinimumHeight(40)
        self.ctx_input.setStyleSheet("""
            QLineEdit {
                background: #0D1117;
                border: 1px solid #30363D;
                border-radius: 8px;
                color: #E6EDF3;
                padding: 0 12px;
                font-size: 14px;
            }
            QLineEdit:focus { border-color: #388BFD; }
            QLineEdit::placeholder { color: #484F58; }
        """)
        config_layout.addWidget(self.ctx_input, 0, 1, 1, 2)

        # 情感基调
        emotion_label = QLabel("情感基调")
        emotion_label.setStyleSheet("color: #C9D1D9; font-size: 13px;")
        config_layout.addWidget(emotion_label, 1, 0)

        self.emotion_combo = QComboBox()
        self.emotion_combo.addItems([
            "惆怅", "励志", "浪漫", "神秘", "怀旧", "哲思", "治愈"
        ])
        self._style_combobox(self.emotion_combo)
        config_layout.addWidget(self.emotion_combo, 1, 1)

        # 风格
        style_label = QLabel("解说风格")
        style_label.setStyleSheet("color: #C9D1D9; font-size: 13px;")
        config_layout.addWidget(style_label, 1, 2)

        self.style_combo = QComboBox()
        self.style_combo.addItems([
            "melancholic / 惆怅",
            "inspirational / 励志",
            "romantic / 浪漫",
            "mysterious / 神秘",
            "nostalgic / 怀旧",
            "philosophical / 哲思",
            "healing / 治愈",
        ])
        self._style_combobox(self.style_combo)
        config_layout.addWidget(self.style_combo, 2, 2)

        # 输出目录
        out_label = QLabel("输出目录")
        out_label.setStyleSheet("color: #C9D1D9; font-size: 13px;")
        config_layout.addWidget(out_label, 2, 0)

        out_layout = QHBoxLayout()
        self.out_input = QLineEdit()
        self.out_input.setReadOnly(True)
        self.out_input.setPlaceholderText("默认保存在项目目录下")
        self.out_input.setStyleSheet("""
            QLineEdit {
                background: #0D1117; border: 1px solid #30363D;
                border-radius: 8px; color: #8B949E;
                padding: 0 12px; font-size: 13px;
            }
        """)
        out_layout.addWidget(self.out_input)

        browse_btn = QPushButton("浏览")
        browse_btn.setObjectName("secondary_button")
        browse_btn.setFixedSize(64, 32)
        browse_btn.clicked.connect(self._browse_output)
        out_layout.addWidget(browse_btn)
        config_layout.addWidget(out_layout, 2, 1, 1, 2)

        layout.addWidget(config_card)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.next_btn = MacPrimaryButton("开始创作 →")
        self.next_btn.setFixedSize(140, 44)
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self._on_next)
        btn_layout.addWidget(self.next_btn)
        layout.addLayout(btn_layout)

        layout.addStretch()

    def _style_combobox(self, combo: QComboBox):
        combo.setStyleSheet("""
            QComboBox {
                background: #0D1117;
                border: 1px solid #30363D;
                border-radius: 8px;
                color: #E6EDF3;
                padding: 0 12px;
                font-size: 13px;
                min-height: 32px;
            }
            QComboBox:focus { border-color: #388BFD; }
            QComboBox::dropDown { border: none; color: #8B949E; }
            QComboBox QAbstractItemView {
                background: #161B22;
                border: 1px solid #30363D;
                color: #E6EDF3;
                selection-background-color: #1C2128;
            }
        """)

    def _on_video_selected(self, path: str):
        self._video_path = path
        self.meta_panel.setVisible(True)
        self.meta_panel.set_metadata(path)
        self.next_btn.setEnabled(bool(path and self.ctx_input.text()))

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(
            self, "选择输出目录", ""
        )
        if path:
            self.out_input.setText(path)

    def _on_next(self):
        if not self._video_path or not self.ctx_input.text():
            return

        # 解析风格
        style_map = {
            "melancholic / 惆怅": MonologueStyle.MELANCHOLIC,
            "inspirational / 励志": MonologueStyle.INSPIRATIONAL,
            "romantic / 浪漫": MonologueStyle.ROMANTIC,
            "mysterious / 神秘": MonologueStyle.MYSTERIOUS,
            "nostalgic / 怀旧": MonologueStyle.NOSTALGIC,
            "philosophical / 哲思": MonologueStyle.PHILOSOPHICAL,
            "healing / 治愈": MonologueStyle.HEALING,
        }
        style = style_map.get(
            self.style_combo.currentText(),
            MonologueStyle.MELANCHOLIC
        )

        from datetime import date
        default_dir = os.path.join(
            os.path.expanduser("~"), "Narrafiilm", str(date.today())
        )
        output_dir = self.out_input.text() or default_dir
        self.config_ready.emit(
            self._video_path,
            self.ctx_input.text(),
            self.emotion_combo.currentText(),
            style,
            output_dir,
        )
