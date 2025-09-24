"""
Professional Audio Mixer Console UI Component for CineAIStudio
Provides a complete mixing interface with faders, meters, and routing
"""

from typing import Dict, List, Optional, Any
import numpy as np
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                           QLabel, QSlider, QPushButton, QComboBox, QFrame,
                           QSpinBox, QCheckBox, QGroupBox, QGridLayout,
                           QSplitter, QToolBar, QStatusBar, QMenu, QMenuBar)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPaintEvent, QPalette
import sys
import os

# Add the app directory to the path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from app.audio.mixer.audio_mixer import AudioMixer, AudioTrack, AudioBus, AutomationMode
from app.audio.analysis.audio_analyzer import AudioAnalyzer
from app.audio.effects.advanced_effects import AdvancedEffectsProcessor


class LevelMeterWidget(QWidget):
    """Professional level meter widget"""

    def __init__(self, orientation: str = "vertical", width: int = 20):
        super().__init__()
        self.orientation = orientation
        self.setFixedWidth(width)

        # Level data
        self.peak_level = -float('inf')
        self.rms_level = -float('inf')
        self.peak_hold = -float('inf')
        self.peak_hold_decay = 0.8

        # Meter ranges
        self.min_level = -60.0  # dB
        self.max_level = 0.0    # dB
        self.warning_level = -6.0  # dB
        self.clip_level = -0.1    # dB

        # Colors
        self.green_color = QColor(0, 255, 0)
        self.yellow_color = QColor(255, 255, 0)
        self.red_color = QColor(255, 0, 0)
        self.bg_color = QColor(30, 30, 30)

        # Peak hold timer
        self.peak_hold_timer = QTimer()
        self.peak_hold_timer.timeout.connect(self._decay_peak_hold)
        self.peak_hold_timer.start(1000)  # 1 second decay

    def update_levels(self, peak: float, rms: float):
        """Update meter levels"""
        self.peak_level = peak
        self.rms_level = rms

        # Update peak hold
        if peak > self.peak_hold:
            self.peak_hold = peak

        self.update()

    def _decay_peak_hold(self):
        """Decay peak hold level"""
        if self.peak_hold > self.min_level:
            self.peak_hold -= 1.0  # 1dB per second
            self.update()

    def _level_to_height(self, level: float, widget_height: int) -> int:
        """Convert dB level to pixel height"""
        if level <= self.min_level:
            return widget_height
        elif level >= self.max_level:
            return 0

        normalized = (level - self.min_level) / (self.max_level - self.min_level)
        return int(widget_height * (1 - normalized))

    def _get_level_color(self, level: float) -> QColor:
        """Get color based on level"""
        if level >= self.clip_level:
            return self.red_color
        elif level >= self.warning_level:
            return self.yellow_color
        else:
            return self.green_color

    def paintEvent(self, event: QPaintEvent):
        """Paint the level meter"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.fillRect(self.rect(), self.bg_color)

        if self.orientation == "vertical":
            self._paint_vertical_meter(painter)
        else:
            self._paint_horizontal_meter(painter)

    def _paint_vertical_meter(self, painter: QPainter):
        """Paint vertical level meter"""
        width = self.width()
        height = self.height()

        # Draw scale marks
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        for level in range(int(self.min_level), int(self.max_level) + 1, 10):
            y = self._level_to_height(level, height)
            painter.drawLine(0, y, width // 3, y)

            if level % 20 == 0:
                painter.setPen(QPen(QColor(150, 150, 150), 1))
                painter.drawText(width // 2, y + 5, f"{level}")

        # Draw RMS level
        rms_height = self._level_to_height(self.rms_level, height)
        rms_color = self._get_level_color(self.rms_level)
        painter.fillRect(QRect(0, rms_height, width, height - rms_height), rms_color)

        # Draw peak level
        peak_height = self._level_to_height(self.peak_level, height)
        peak_color = self._get_level_color(self.peak_level)
        painter.fillRect(QRect(width * 2 // 3, peak_height, width // 3, height - peak_height), peak_color)

        # Draw peak hold
        if self.peak_hold > self.min_level:
            hold_y = self._level_to_height(self.peak_hold, height)
            painter.setPen(QPen(self.red_color, 2))
            painter.drawLine(0, hold_y, width, hold_y)

    def _paint_horizontal_meter(self, painter: QPainter):
        """Paint horizontal level meter"""
        width = self.width()
        height = self.height()

        # Draw RMS level
        rms_width = int(width * (self.rms_level - self.min_level) / (self.max_level - self.min_level))
        rms_width = max(0, min(width, rms_width))
        rms_color = self._get_level_color(self.rms_level)
        painter.fillRect(QRect(0, 0, rms_width, height // 2), rms_color)

        # Draw peak level
        peak_width = int(width * (self.peak_level - self.min_level) / (self.max_level - self.min_level))
        peak_width = max(0, min(width, peak_width))
        peak_color = self._get_level_color(self.peak_level)
        painter.fillRect(QRect(0, height // 2, peak_width, height // 2), peak_color)


class TrackStrip(QWidget):
    """Single audio track strip in the mixer"""

    track_changed = pyqtSignal(str, str, object)  # track_id, parameter, value

    def __init__(self, track: AudioTrack, mixer: AudioMixer):
        super().__init__()
        self.track = track
        self.mixer = mixer
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Setup track strip UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Track header
        header = QLabel(self.track.name)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-weight: bold; background-color: #2c2c2c; padding: 5px;")
        layout.addWidget(header)

        # Level meters
        meters_widget = QWidget()
        meters_layout = QHBoxLayout(meters_layout)
        meters_layout.setContentsMargins(0, 0, 0, 0)

        # Left and right channel meters
        self.left_meter = LevelMeterWidget()
        self.right_meter = LevelMeterWidget()
        meters_layout.addWidget(self.left_meter)
        meters_layout.addWidget(self.right_meter)

        layout.addWidget(meters_widget)

        # Volume fader
        volume_group = QGroupBox("Volume")
        volume_layout = QVBoxLayout(volume_group)

        self.volume_slider = QSlider(Qt.Orientation.Vertical)
        self.volume_slider.setRange(0, 200)
        self.volume_slider.setValue(int(self.track.volume * 100))
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksRight)
        self.volume_slider.setTickInterval(25)
        volume_layout.addWidget(self.volume_slider)

        self.volume_label = QLabel(f"{self.track.volume:.2f}")
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        volume_layout.addWidget(self.volume_label)

        layout.addWidget(volume_group)

        # Pan control
        pan_group = QGroupBox("Pan")
        pan_layout = QHBoxLayout(pan_group)

        self.pan_slider = QSlider(Qt.Orientation.Horizontal)
        self.pan_slider.setRange(-100, 100)
        self.pan_slider.setValue(int(self.track.pan * 100))
        pan_layout.addWidget(self.pan_slider)

        self.pan_label = QLabel("C")
        self.pan_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pan_label.setFixedWidth(20)
        pan_layout.addWidget(self.pan_label)

        layout.addWidget(pan_group)

        # Mute/Solo buttons
        controls_layout = QHBoxLayout()

        self.mute_button = QPushButton("M")
        self.mute_button.setCheckable(True)
        self.mute_button.setChecked(self.track.muted)
        self.mute_button.setMaximumWidth(30)
        controls_layout.addWidget(self.mute_button)

        self.solo_button = QPushButton("S")
        self.solo_button.setCheckable(True)
        self.solo_button.setChecked(self.track.soloed)
        self.solo_button.setMaximumWidth(30)
        controls_layout.addWidget(self.solo_button)

        layout.addLayout(controls_layout)

        # Track armed button (for recording)
        self.arm_button = QPushButton("●")
        self.arm_button.setCheckable(True)
        self.arm_button.setChecked(self.track.armed)
        self.arm_button.setMaximumWidth(30)
        self.arm_button.setStyleSheet("""
            QPushButton:checked {
                background-color: red;
                color: white;
            }
        """)
        layout.addWidget(self.arm_button)

        # Add stretch to push everything up
        layout.addStretch()

        # Set track color
        self.setStyleSheet(f"""
            TrackStrip {{
                background-color: #1e1e1e;
                border: 1px solid {self.track.color};
                border-radius: 5px;
            }}
        """)

    def connect_signals(self):
        """Connect track strip signals"""
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.pan_slider.valueChanged.connect(self._on_pan_changed)
        self.mute_button.toggled.connect(self._on_mute_toggled)
        self.solo_button.toggled.connect(self._on_solo_toggled)
        self.arm_button.toggled.connect(self._on_arm_toggled)

    def _on_volume_changed(self, value: int):
        """Handle volume change"""
        volume = value / 100.0
        self.mixer.set_track_volume(self.track.id, volume)
        self.volume_label.setText(f"{volume:.2f}")
        self.track_changed.emit(self.track.id, "volume", volume)

    def _on_pan_changed(self, value: int):
        """Handle pan change"""
        pan = value / 100.0
        self.mixer.set_track_pan(self.track.id, pan)

        # Update pan label
        if pan < -0.1:
            self.pan_label.setText("L")
        elif pan > 0.1:
            self.pan_label.setText("R")
        else:
            self.pan_label.setText("C")

        self.track_changed.emit(self.track.id, "pan", pan)

    def _on_mute_toggled(self, checked: bool):
        """Handle mute toggle"""
        self.mixer.set_track_mute(self.track.id, checked)
        self.track_changed.emit(self.track.id, "mute", checked)

    def _on_solo_toggled(self, checked: bool):
        """Handle solo toggle"""
        self.mixer.set_track_solo(self.track.id, checked)
        self.track_changed.emit(self.track.id, "solo", checked)

    def _on_arm_toggled(self, checked: bool):
        """Handle arm toggle"""
        self.track.armed = checked
        self.track_changed.emit(self.track.id, "armed", checked)

    def update_levels(self, levels: Dict[str, float]):
        """Update track level meters"""
        peak = levels.get("peak", -float('inf'))
        rms = levels.get("rms", -float('inf'))

        self.left_meter.update_levels(peak, rms)
        self.right_meter.update_levels(peak, rms)


class BusStrip(QWidget):
    """Audio bus strip in the mixer"""

    bus_changed = pyqtSignal(str, str, object)  # bus_id, parameter, value

    def __init__(self, bus: AudioBus, mixer: AudioMixer):
        super().__init__()
        self.bus = bus
        self.mixer = mixer
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Setup bus strip UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Bus header
        header = QLabel(self.bus.name)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-weight: bold; background-color: #2c2c2c; padding: 5px;")
        layout.addWidget(header)

        # Level meters
        self.level_meter = LevelMeterWidget()
        layout.addWidget(self.level_meter)

        # Volume fader
        volume_group = QGroupBox("Volume")
        volume_layout = QVBoxLayout(volume_group)

        self.volume_slider = QSlider(Qt.Orientation.Vertical)
        self.volume_slider.setRange(0, 200)
        self.volume_slider.setValue(int(self.bus.volume * 100))
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksRight)
        self.volume_slider.setTickInterval(25)
        volume_layout.addWidget(self.volume_slider)

        self.volume_label = QLabel(f"{self.bus.volume:.2f}")
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        volume_layout.addWidget(self.volume_label)

        layout.addWidget(volume_group)

        # Mute/Solo buttons
        controls_layout = QHBoxLayout()

        self.mute_button = QPushButton("M")
        self.mute_button.setCheckable(True)
        self.mute_button.setChecked(self.bus.muted)
        self.mute_button.setMaximumWidth(30)
        controls_layout.addWidget(self.mute_button)

        self.solo_button = QPushButton("S")
        self.solo_button.setCheckable(True)
        self.solo_button.setChecked(self.bus.soloed)
        self.solo_button.setMaximumWidth(30)
        controls_layout.addWidget(self.solo_button)

        layout.addLayout(controls_layout)

        # Add stretch
        layout.addStretch()

        # Set bus style
        self.setStyleSheet("""
            BusStrip {
                background-color: #2a2a2a;
                border: 1px solid #4a4a4a;
                border-radius: 5px;
            }
        """)

    def connect_signals(self):
        """Connect bus strip signals"""
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.mute_button.toggled.connect(self._on_mute_toggled)
        self.solo_button.toggled.connect(self._on_solo_toggled)

    def _on_volume_changed(self, value: int):
        """Handle volume change"""
        volume = value / 100.0
        self.mixer.set_bus_volume(self.bus.id, volume)
        self.volume_label.setText(f"{volume:.2f}")
        self.bus_changed.emit(self.bus.id, "volume", volume)

    def _on_mute_toggled(self, checked: bool):
        """Handle mute toggle"""
        self.bus.muted = checked
        self.bus_changed.emit(self.bus.id, "mute", checked)

    def _on_solo_toggled(self, checked: bool):
        """Handle solo toggle"""
        self.bus.soloed = checked
        self.bus_changed.emit(self.bus.id, "solo", checked)

    def update_levels(self, levels: Dict[str, float]):
        """Update bus level meters"""
        peak = levels.get("peak", -float('inf'))
        rms = levels.get("rms", -float('inf'))

        self.level_meter.update_levels(peak, rms)


class MasterOutputWidget(QWidget):
    """Master output section"""

    master_changed = pyqtSignal(str, object)  # parameter, value

    def __init__(self, mixer: AudioMixer):
        super().__init__()
        self.mixer = mixer
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Setup master output UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Master header
        header = QLabel("MASTER")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-weight: bold; font-size: 14px; background-color: #1a1a1a; color: white; padding: 5px;")
        layout.addWidget(header)

        # Master level meters
        meters_widget = QWidget()
        meters_layout = QHBoxLayout(meters_widget)
        meters_layout.setContentsMargins(0, 0, 0, 0)

        self.left_meter = LevelMeterWidget()
        self.right_meter = LevelMeterWidget()
        meters_layout.addWidget(self.left_meter)
        meters_layout.addWidget(self.right_meter)

        layout.addWidget(meters_widget)

        # Master volume fader
        volume_group = QGroupBox("Master Volume")
        volume_layout = QVBoxLayout(volume_group)

        self.volume_slider = QSlider(Qt.Orientation.Vertical)
        self.volume_slider.setRange(0, 200)
        self.volume_slider.setValue(int(self.mixer.master_volume * 100))
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksRight)
        self.volume_slider.setTickInterval(25)
        volume_layout.addWidget(self.volume_slider)

        self.volume_label = QLabel(f"{self.mixer.master_volume:.2f}")
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        volume_layout.addWidget(self.volume_label)

        layout.addWidget(volume_group)

        # Master mute
        self.mute_button = QPushButton("Mute")
        self.mute_button.setCheckable(True)
        self.mute_button.setChecked(self.mixer.master_muted)
        layout.addWidget(self.mute_button)

        # Add stretch
        layout.addStretch()

        # Set master style
        self.setStyleSheet("""
            MasterOutputWidget {
                background-color: #1a1a1a;
                border: 2px solid #6a6a6a;
                border-radius: 5px;
                color: white;
            }
        """)

    def connect_signals(self):
        """Connect master output signals"""
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.mute_button.toggled.connect(self._on_mute_toggled)

    def _on_volume_changed(self, value: int):
        """Handle master volume change"""
        volume = value / 100.0
        self.mixer.set_master_volume(volume)
        self.volume_label.setText(f"{volume:.2f}")
        self.master_changed.emit("volume", volume)

    def _on_mute_toggled(self, checked: bool):
        """Handle master mute toggle"""
        self.mixer.set_master_mute(checked)
        self.master_changed.emit("mute", checked)

    def update_levels(self, levels: Dict[str, float]):
        """Update master level meters"""
        peak = levels.get("peak", -float('inf'))
        rms = levels.get("rms", -float('inf'))

        self.left_meter.update_levels(peak, rms)
        self.right_meter.update_levels(peak, rms)


class AudioMixerConsole(QWidget):
    """Professional audio mixer console"""

    def __init__(self, mixer: AudioMixer, analyzer: AudioAnalyzer):
        super().__init__()
        self.mixer = mixer
        self.analyzer = analyzer
        self.track_strips = {}
        self.bus_strips = {}

        self.setup_ui()
        self.connect_signals()

        # Setup level update timer
        self.level_update_timer = QTimer()
        self.level_update_timer.timeout.connect(self._update_levels)
        self.level_update_timer.start(50)  # 50ms update rate

    def setup_ui(self):
        """Setup mixer console UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = QToolBar()
        toolbar.setStyleSheet("QToolBar { background-color: #2a2a2a; }")

        # Add track button
        add_track_action = toolbar.addAction("Add Track")
        add_track_action.triggered.connect(self._add_track)

        # Add bus button
        add_bus_action = toolbar.addAction("Add Bus")
        add_bus_action.triggered.connect(self._add_bus)

        # Automation mode selector
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Automation:"))

        self.automation_combo = QComboBox()
        self.automation_combo.addItems([mode.value for mode in AutomationMode])
        self.automation_combo.setCurrentText(AutomationMode.OFF.value)
        self.automation_combo.currentTextChanged.connect(self._on_automation_changed)
        toolbar.addWidget(self.automation_combo)

        layout.addWidget(toolbar)

        # Main mixer area with scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarNever)

        # Main mixer widget
        mixer_widget = QWidget()
        mixer_layout = QHBoxLayout(mixer_widget)
        mixer_layout.setContentsMargins(10, 10, 10, 10)
        mixer_layout.setSpacing(10)

        # Track strips area
        self.tracks_widget = QWidget()
        self.tracks_layout = QHBoxLayout(self.tracks_widget)
        self.tracks_layout.setContentsMargins(0, 0, 0, 0)
        self.tracks_layout.setSpacing(5)

        # Bus strips area
        self.buses_widget = QWidget()
        self.buses_layout = QHBoxLayout(self.buses_widget)
        self.buses_layout.setContentsMargins(0, 0, 0, 0)
        self.buses_layout.setSpacing(5)

        # Master output
        self.master_widget = MasterOutputWidget(self.mixer)
        self.master_widget.setFixedWidth(100)

        # Add to layout
        mixer_layout.addWidget(self.tracks_widget)
        mixer_layout.addWidget(self.buses_widget)
        mixer_layout.addWidget(self.master_widget)

        scroll_area.setWidget(mixer_widget)
        layout.addWidget(scroll_area)

        # Set overall style
        self.setStyleSheet("""
            AudioMixerConsole {
                background-color: #1e1e1e;
                color: white;
            }
            QGroupBox {
                background-color: transparent;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                margin-top: 10px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QSlider::groove:vertical {
                border: 1px solid #4a4a4a;
                width: 6px;
                background: #3a3a3a;
                margin: 2px 0;
            }
            QSlider::handle:vertical {
                background: #6a6a6a;
                border: 1px solid #4a4a4a;
                height: 20px;
                margin: -2px 0;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #4a4a4a;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:checked {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #4a4a4a;
            }
        """)

        # Create initial strips
        self._create_initial_strips()

    def connect_signals(self):
        """Connect mixer console signals"""
        self.mixer.track_added.connect(self._on_track_added)
        self.mixer.track_removed.connect(self._on_track_removed)
        self.mixer.bus_added.connect(self._on_bus_added)
        self.mixer.bus_removed.connect(self._on_bus_removed)

    def _create_initial_strips(self):
        """Create initial track and bus strips"""
        # Create tracks for existing mixer tracks
        for track_id, track in self.mixer.tracks.items():
            self._add_track_strip(track)

        # Create bus strips for existing mixer buses
        for bus_id, bus in self.mixer.buses.items():
            self._add_bus_strip(bus)

    def _add_track_strip(self, track: AudioTrack):
        """Add a track strip"""
        strip = TrackStrip(track, self.mixer)
        self.tracks_layout.addWidget(strip)
        self.track_strips[track.id] = strip

    def _add_bus_strip(self, bus: AudioBus):
        """Add a bus strip"""
        strip = BusStrip(bus, self.mixer)
        self.buses_layout.addWidget(strip)
        self.bus_strips[bus.id] = strip

    def _add_track(self):
        """Add new track"""
        track_id = self.mixer.add_track(f"Track {len(self.mixer.tracks) + 1}")

    def _add_bus(self):
        """Add new bus"""
        bus_id = self.mixer.add_bus(f"Bus {len(self.mixer.buses)}")

    def _on_automation_changed(self, mode_text: str):
        """Handle automation mode change"""
        mode = AutomationMode(mode_text)
        self.mixer.set_automation_mode(mode)

    def _on_track_added(self, track_id: str):
        """Handle track added to mixer"""
        track = self.mixer.tracks.get(track_id)
        if track:
            self._add_track_strip(track)

    def _on_track_removed(self, track_id: str):
        """Handle track removed from mixer"""
        if track_id in self.track_strips:
            strip = self.track_strips[track_id]
            self.tracks_layout.removeWidget(strip)
            strip.deleteLater()
            del self.track_strips[track_id]

    def _on_bus_added(self, bus_id: str):
        """Handle bus added to mixer"""
        bus = self.mixer.buses.get(bus_id)
        if bus:
            self._add_bus_strip(bus)

    def _on_bus_removed(self, bus_id: str):
        """Handle bus removed from mixer"""
        if bus_id in self.bus_strips:
            strip = self.bus_strips[bus_id]
            self.buses_layout.removeWidget(strip)
            strip.deleteLater()
            del self.bus_strips[bus_id]

    def _update_levels(self):
        """Update all level meters"""
        # Update track levels
        for track_id, strip in self.track_strips.items():
            levels = self.mixer.get_track_levels(track_id)
            if levels:
                strip.update_levels(levels)

        # Update bus levels
        for bus_id, strip in self.bus_strips.items():
            levels = self.mixer.get_bus_levels(bus_id)
            if levels:
                strip.update_levels(levels)

        # Update master levels
        master_level = self.mixer.get_master_level()
        self.master_widget.update_levels({
            "peak": master_level,
            "rms": master_level * 0.7
        })

    def save_mixer_state(self, file_path: str) -> bool:
        """Save mixer state"""
        return self.mixer.save_mixer_state(file_path)

    def load_mixer_state(self, file_path: str) -> bool:
        """Load mixer state"""
        success = self.mixer.load_mixer_state(file_path)
        if success:
            # Clear existing strips
            for strip in self.track_strips.values():
                self.tracks_layout.removeWidget(strip)
                strip.deleteLater()
            self.track_strips.clear()

            for strip in self.bus_strips.values():
                self.buses_layout.removeWidget(strip)
                strip.deleteLater()
            self.bus_strips.clear()

            # Recreate strips
            self._create_initial_strips()

        return success

    def get_mixer_settings(self) -> Dict[str, Any]:
        """Get current mixer settings"""
        return self.mixer.export_mixer_settings()

    def set_mixer_settings(self, settings: Dict[str, Any]):
        """Apply mixer settings"""
        # Apply track settings
        for track_id, track_settings in settings.get("tracks", {}).items():
            if track_id in self.mixer.tracks:
                track = self.mixer.tracks[track_id]
                if "volume" in track_settings:
                    self.mixer.set_track_volume(track_id, track_settings["volume"])
                if "pan" in track_settings:
                    self.mixer.set_track_pan(track_id, track_settings["pan"])
                if "muted" in track_settings:
                    self.mixer.set_track_mute(track_id, track_settings["muted"])
                if "soloed" in track_settings:
                    self.mixer.set_track_solo(track_id, track_settings["soloed"])

        # Apply bus settings
        for bus_id, bus_settings in settings.get("buses", {}).items():
            if bus_id in self.mixer.buses:
                bus = self.mixer.buses[bus_id]
                if "volume" in bus_settings:
                    self.mixer.set_bus_volume(bus_id, bus_settings["volume"])
                if "muted" in bus_settings:
                    bus.muted = bus_settings["muted"]
                if "soloed" in bus_settings:
                    bus.soloed = bus_settings["soloed"]

        # Apply master settings
        master = settings.get("master", {})
        if "volume" in master:
            self.mixer.set_master_volume(master["volume"])
        if "muted" in master:
            self.mixer.set_master_mute(master["muted"])