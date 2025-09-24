"""
Audio Analysis Panel UI Component for CineAIStudio
Provides real-time audio analysis and visualization
"""

from typing import Dict, List, Optional, Any
import numpy as np
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                           QLabel, QComboBox, QPushButton, QGroupBox, QTabWidget,
                           QFrame, QSpinBox, QCheckBox, QSlider, QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygonF
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from app.audio.analysis.audio_analyzer import AudioAnalyzer, AnalysisMode, AudioMetrics


class SpectrumDisplay(QWidget):
    """Real-time spectrum analyzer display"""

    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 200)

        # Spectrum data
        self.frequencies = np.array([])
        self.spectrum = np.array([])
        self.peak_hold = np.array([])
        self.average = np.array([])

        # Display settings
        self.min_freq = 20
        self.max_freq = 20000
        self.min_level = -60
        self.max_level = 0
        self.log_freq_scale = True

        # Colors
        self.bg_color = QColor(20, 20, 20)
        self.grid_color = QColor(60, 60, 60)
        self.spectrum_color = QColor(0, 255, 0)
        self.peak_hold_color = QColor(255, 255, 0)
        self.average_color = QColor(0, 150, 255)
        self.text_color = QColor(200, 200, 200)

    def update_spectrum(self, spectrum_data: Dict[str, np.ndarray]):
        """Update spectrum display"""
        self.frequencies = spectrum_data.get("frequencies", np.array([]))
        self.spectrum = spectrum_data.get("spectrum", np.array([]))
        self.peak_hold = spectrum_data.get("peak_hold", np.array([]))
        self.average = spectrum_data.get("average", np.array([]))

        self.update()

    def paintEvent(self, event):
        """Paint spectrum display"""
        if len(self.frequencies) == 0 or len(self.spectrum) == 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.fillRect(self.rect(), self.bg_color)

        # Draw grid
        self._draw_grid(painter)

        # Draw spectrum
        self._draw_spectrum(painter)

        # Draw labels
        self._draw_labels(painter)

    def _draw_grid(self, painter: QPainter):
        """Draw frequency and level grid"""
        painter.setPen(QPen(self.grid_color, 1))

        # Frequency grid lines
        freq_lines = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000]

        for freq in freq_lines:
            if self.min_freq <= freq <= self.max_freq:
                x = self._freq_to_x(freq)
                painter.drawLine(int(x), 0, int(x), self.height())

        # Level grid lines
        for level in range(self.min_level, self.max_level + 1, 10):
            y = self._level_to_y(level)
            painter.drawLine(0, int(y), self.width(), int(y))

    def _draw_spectrum(self, painter: QPainter):
        """Draw spectrum curve"""
        if len(self.spectrum) == 0:
            return

        # Filter frequency range
        freq_mask = (self.frequencies >= self.min_freq) & (self.frequencies <= self.max_freq)
        filtered_freqs = self.frequencies[freq_mask]
        filtered_spectrum = self.spectrum[freq_mask]

        # Draw average spectrum
        if len(self.average) > 0:
            painter.setPen(QPen(self.average_color, 2))
            self._draw_curve(painter, filtered_freqs, self.average[freq_mask])

        # Draw current spectrum
        painter.setPen(QPen(self.spectrum_color, 1))
        self._draw_curve(painter, filtered_freqs, filtered_spectrum)

        # Draw peak hold
        if len(self.peak_hold) > 0:
            painter.setPen(QPen(self.peak_hold_color, 1))
            self._draw_curve(painter, filtered_freqs, self.peak_hold[freq_mask])

    def _draw_curve(self, painter: QPainter, frequencies: np.ndarray, levels: np.ndarray):
        """Draw spectrum curve"""
        points = []
        for freq, level in zip(frequencies, levels):
            x = self._freq_to_x(freq)
            y = self._level_to_y(level)
            points.append(QPointF(x, y))

        if len(points) > 1:
            painter.drawPolyline(QPolygonF(points))

    def _draw_labels(self, painter: QPainter):
        """Draw frequency and level labels"""
        painter.setPen(QPen(self.text_color, 1))
        painter.setFont(QFont("Arial", 8))

        # Frequency labels
        freq_labels = [(20, "20Hz"), (100, "100Hz"), (1000, "1kHz"), (10000, "10kHz"), (20000, "20kHz")]

        for freq, label in freq_labels:
            if self.min_freq <= freq <= self.max_freq:
                x = self._freq_to_x(freq)
                painter.drawText(int(x) - 20, self.height() - 5, label)

        # Level labels
        for level in range(self.min_level, self.max_level + 1, 20):
            y = self._level_to_y(level)
            painter.drawText(5, int(y) + 3, f"{level}dB")

    def _freq_to_x(self, freq: float) -> float:
        """Convert frequency to x coordinate"""
        if self.log_freq_scale:
            log_min = np.log10(self.min_freq)
            log_max = np.log10(self.max_freq)
            log_freq = np.log10(freq)
            return self.width() * (log_freq - log_min) / (log_max - log_min)
        else:
            return self.width() * (freq - self.min_freq) / (self.max_freq - self.min_freq)

    def _level_to_y(self, level: float) -> float:
        """Convert level to y coordinate"""
        return self.height() * (1 - (level - self.min_level) / (self.max_level - self.min_level))


class PhaseMeterWidget(QWidget):
    """Phase correlation meter"""

    def __init__(self):
        super().__init__()
        self.setMinimumSize(100, 100)
        self.setMaximumSize(150, 150)

        # Phase data
        self.correlation = 1.0
        self.stereo_width = 0.0

        # Colors
        self.bg_color = QColor(20, 20, 20)
        self.good_color = QColor(0, 255, 0)
        self.warning_color = QColor(255, 255, 0)
        self.bad_color = QColor(255, 0, 0)
        self.text_color = QColor(200, 200, 200)

    def update_phase(self, phase_data: Dict[str, float]):
        """Update phase meter"""
        self.correlation = phase_data.get("correlation", 1.0)
        self.stereo_width = phase_data.get("stereo_width", 0.0)
        self.update()

    def paintEvent(self, event):
        """Paint phase meter"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.fillRect(self.rect(), self.bg_color)

        # Draw phase circle
        self._draw_phase_circle(painter)

        # Draw correlation bar
        self._draw_correlation_bar(painter)

        # Draw labels
        self._draw_labels(painter)

    def _draw_phase_circle(self, painter: QPainter):
        """Draw phase correlation circle"""
        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = min(self.width(), self.height()) // 3

        # Draw circle
        painter.setPen(QPen(self.text_color, 2))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

        # Draw correlation indicator
        angle = self.correlation * np.pi  # -1 to 1 maps to 0 to π
        x = center_x + radius * 0.8 * np.cos(angle + np.pi)
        y = center_y + radius * 0.8 * np.sin(angle + np.pi)

        # Color based on correlation
        if abs(self.correlation) > 0.8:
            color = self.good_color
        elif abs(self.correlation) > 0.5:
            color = self.warning_color
        else:
            color = self.bad_color

        painter.setPen(QPen(color, 3))
        painter.drawLine(center_x, center_y, int(x), int(y))

    def _draw_correlation_bar(self, painter: QPainter):
        """Draw correlation level bar"""
        bar_width = 20
        bar_height = self.height() - 40
        bar_x = self.width() - bar_width - 10
        bar_y = 20

        # Background
        painter.fillRect(bar_x, bar_y, bar_width, bar_height, QColor(40, 40, 40))

        # Correlation level
        correlation_normalized = (self.correlation + 1) / 2  # -1 to 1 -> 0 to 1
        fill_height = int(bar_height * correlation_normalized)

        if self.correlation > 0.8:
            color = self.good_color
        elif self.correlation > 0.5:
            color = self.warning_color
        else:
            color = self.bad_color

        painter.fillRect(bar_x, bar_y + bar_height - fill_height, bar_width, fill_height, color)

        # Border
        painter.setPen(QPen(self.text_color, 1))
        painter.drawRect(bar_x, bar_y, bar_width, bar_height)

    def _draw_labels(self, painter: QPainter):
        """Draw phase meter labels"""
        painter.setPen(QPen(self.text_color, 1))
        painter.setFont(QFont("Arial", 8))

        # Correlation value
        painter.drawText(10, 20, f"Correlation: {self.correlation:.2f}")

        # Stereo width
        painter.drawText(10, 35, f"Width: {self.stereo_width:.2f}")

        # Phase warnings
        if self.correlation < -0.5:
            painter.setPen(QPen(self.bad_color, 1))
            painter.drawText(10, 50, "Phase Inversion")


class LevelDisplayWidget(QWidget):
    """Multi-channel level display"""

    def __init__(self):
        super().__init__()
        self.setMinimumSize(200, 100)

        # Level data
        self.levels = {
            "peak": -float('inf'),
            "rms": -float('inf'),
            "lufs": -float('inf'),
            "true_peak": -float('inf')
        }

        # Colors
        self.bg_color = QColor(20, 20, 20)
        self.text_color = QColor(200, 200, 200)
        self.level_colors = {
            "peak": QColor(0, 255, 0),
            "rms": QColor(0, 150, 255),
            "lufs": QColor(255, 255, 0),
            "true_peak": QColor(255, 0, 255)
        }

    def update_levels(self, levels: Dict[str, float]):
        """Update level display"""
        self.levels.update(levels)
        self.update()

    def paintEvent(self, event):
        """Paint level display"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.fillRect(self.rect(), self.bg_color)

        # Draw level bars
        self._draw_level_bars(painter)

        # Draw level values
        self._draw_level_values(painter)

    def _draw_level_bars(self, painter: QPainter):
        """Draw level bar graphs"""
        bar_width = self.width() // len(self.levels) - 10
        x = 5

        for level_type, level_value in self.levels.items():
            # Calculate bar height
            level_normalized = max(0, min(1, (level_value + 60) / 60))  # -60 to 0 dB
            bar_height = int(self.height() * 0.8 * level_normalized)

            # Draw bar
            color = self.level_colors.get(level_type, self.text_color)
            painter.fillRect(x, self.height() - bar_height - 20, bar_width, bar_height, color)

            # Draw bar outline
            painter.setPen(QPen(self.text_color, 1))
            painter.drawRect(x, self.height() - 20, bar_width, -int(self.height() * 0.8))

            x += bar_width + 10

    def _draw_level_values(self, painter: QPainter):
        """Draw level text values"""
        painter.setPen(QPen(self.text_color, 1))
        painter.setFont(QFont("Arial", 8))

        bar_width = self.width() // len(self.levels) - 10
        x = 5

        for level_type, level_value in self.levels.items():
            # Level type label
            painter.drawText(x, self.height() - 15, level_type.upper())

            # Level value
            value_text = f"{level_value:.1f}dB" if level_value > -float('inf') else "-∞"
            painter.drawText(x, self.height() - 2, value_text)

            x += bar_width + 10


class AudioAnalyzerPanel(QWidget):
    """Complete audio analysis panel"""

    analysis_started = pyqtSignal()
    analysis_stopped = pyqtSignal()
    analysis_exported = pyqtSignal(str)

    def __init__(self, analyzer: AudioAnalyzer):
        super().__init__()
        self.analyzer = analyzer
        self.is_analyzing = False

        self.setup_ui()
        self.connect_signals()

        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_analysis)
        self.update_timer.start(100)  # 100ms update rate

    def setup_ui(self):
        """Setup analyzer panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Control toolbar
        control_widget = QGroupBox("Analysis Controls")
        control_layout = QHBoxLayout(control_widget)

        # Start/Stop button
        self.start_stop_button = QPushButton("Start Analysis")
        self.start_stop_button.setCheckable(True)
        control_layout.addWidget(self.start_stop_button)

        # Analysis mode
        control_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([mode.value for mode in AnalysisMode])
        self.mode_combo.setCurrentText(AnalysisMode.REALTIME.value)
        control_layout.addWidget(self.mode_combo)

        # Update rate
        control_layout.addWidget(QLabel("Rate:"))
        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(10, 1000)
        self.rate_spin.setValue(100)
        self.rate_spin.setSuffix("ms")
        control_layout.addWidget(self.rate_spin)

        # Export button
        self.export_button = QPushButton("Export Report")
        control_layout.addWidget(self.export_button)

        layout.addWidget(control_widget)

        # Main analysis display
        analysis_widget = QTabWidget()

        # Spectrum analyzer tab
        spectrum_tab = QWidget()
        spectrum_layout = QVBoxLayout(spectrum_tab)

        self.spectrum_display = SpectrumDisplay()
        spectrum_layout.addWidget(self.spectrum_display)

        analysis_widget.addTab(spectrum_tab, "Spectrum")

        # Phase meter tab
        phase_tab = QWidget()
        phase_layout = QVBoxLayout(phase_tab)

        self.phase_meter = PhaseMeterWidget()
        phase_layout.addWidget(self.phase_meter, alignment=Qt.AlignmentFlag.AlignCenter)

        analysis_widget.addTab(phase_tab, "Phase")

        # Level meters tab
        level_tab = QWidget()
        level_layout = QVBoxLayout(level_tab)

        self.level_display = LevelDisplayWidget()
        level_layout.addWidget(self.level_display)

        analysis_widget.addTab(level_tab, "Levels")

        # Metrics tab
        metrics_tab = QWidget()
        metrics_layout = QVBoxLayout(metrics_tab)

        self.metrics_display = QLabel("No analysis data")
        self.metrics_display.setWordWrap(True)
        self.metrics_display.setStyleSheet("background-color: #2a2a2a; padding: 10px;")
        metrics_layout.addWidget(self.metrics_display)

        analysis_widget.addTab(metrics_tab, "Metrics")

        layout.addWidget(analysis_widget)

        # Status bar
        self.status_label = QLabel("Analysis stopped")
        self.status_label.setStyleSheet("background-color: #2a2a2a; padding: 5px;")
        layout.addWidget(self.status_label)

        # Set style
        self.setStyleSheet("""
            AudioAnalyzerPanel {
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
            QComboBox, QSpinBox {
                background-color: #3a3a3a;
                border: 1px solid #4a4a4a;
                padding: 3px;
                border-radius: 3px;
            }
            QLabel {
                color: white;
            }
        """)

    def connect_signals(self):
        """Connect analyzer panel signals"""
        self.start_stop_button.toggled.connect(self._on_start_stop_toggled)
        self.rate_spin.valueChanged.connect(self._on_rate_changed)
        self.export_button.clicked.connect(self._on_export_clicked)

        # Connect to analyzer signals
        self.analyzer.levels_updated.connect(self._on_levels_updated)
        self.analyzer.spectrum_updated.connect(self._on_spectrum_updated)
        self.analyzer.phase_updated.connect(self._on_phase_updated)
        self.analyzer.metrics_updated.connect(self._on_metrics_updated)
        self.analyzer.warning_detected.connect(self._on_warning_detected)

    def _on_start_stop_toggled(self, checked: bool):
        """Handle start/stop button toggle"""
        if checked:
            self._start_analysis()
        else:
            self._stop_analysis()

    def _on_rate_changed(self, rate: int):
        """Handle update rate change"""
        self.update_timer.setInterval(rate)

    def _on_export_clicked(self):
        """Handle export button click"""
        from PyQt6.QtWidgets import QFileDialog
        import time

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Analysis Report",
            f"audio_analysis_{timestamp}.json",
            "JSON Files (*.json)"
        )

        if file_path:
            metrics = self.analyzer.get_average_metrics()
            if self.analyzer.export_analysis_report(file_path, metrics):
                self.analysis_exported.emit(file_path)
                self.status_label.setText(f"Report exported to: {file_path}")
            else:
                self.status_label.setText("Export failed")

    def _start_analysis(self):
        """Start audio analysis"""
        mode = AnalysisMode(self.mode_combo.currentText())
        self.analyzer.start_analysis(mode)
        self.is_analyzing = True
        self.start_stop_button.setText("Stop Analysis")
        self.status_label.setText("Analysis running...")
        self.analysis_started.emit()

    def _stop_analysis(self):
        """Stop audio analysis"""
        self.analyzer.stop_analysis()
        self.is_analyzing = False
        self.start_stop_button.setText("Start Analysis")
        self.status_label.setText("Analysis stopped")
        self.analysis_stopped.emit()

    def _update_analysis(self):
        """Update analysis display"""
        if not self.is_analyzing:
            return

        # Get current metrics and update displays
        metrics = self.analyzer.get_current_metrics()
        if metrics:
            self._update_metrics_display(metrics)

    def _on_levels_updated(self, levels: Dict[str, float]):
        """Handle level updates"""
        self.level_display.update_levels(levels)

    def _on_spectrum_updated(self, spectrum_data: Dict[str, np.ndarray]):
        """Handle spectrum updates"""
        self.spectrum_display.update_spectrum(spectrum_data)

    def _on_phase_updated(self, phase_data: Dict[str, float]):
        """Handle phase updates"""
        self.phase_meter.update_phase(phase_data)

    def _on_metrics_updated(self, metrics: AudioMetrics):
        """Handle metrics updates"""
        self._update_metrics_display(metrics)

    def _on_warning_detected(self, warning: str):
        """Handle warning detection"""
        self.status_label.setText(f"Warning: {warning}")
        self.status_label.setStyleSheet("background-color: #8B4513; color: white; padding: 5px;")

    def _update_metrics_display(self, metrics: AudioMetrics):
        """Update metrics text display"""
        metrics_text = f"""
        <b>Audio Metrics</b><br>
        Peak Level: {metrics.peak_level:.1f} dBFS<br>
        RMS Level: {metrics.rms_level:.1f} dBFS<br>
        LUFS Level: {metrics.lufs_level:.1f} LUFS<br>
        True Peak: {metrics.max_true_peak:.1f} dBTP<br>
        Crest Factor: {metrics.crest_factor:.1f} dB<br>
        Dynamic Range: {metrics.dynamic_range:.1f} dB<br>
        Phase Correlation: {metrics.phase_correlation:.2f}<br>
        Stereo Width: {metrics.stereo_width:.2f}
        """

        if hasattr(metrics, 'spectral_centroid'):
            metrics_text += f"<br>Spectral Centroid: {metrics.spectral_centroid:.0f} Hz"

        if hasattr(metrics, 'spectral_entropy'):
            metrics_text += f"<br>Spectral Entropy: {metrics.spectral_entropy:.2f}"

        self.metrics_display.setText(metrics_text)

    def set_audio_data(self, audio_data: np.ndarray):
        """Set audio data for analysis"""
        self.analyzer.set_audio_data(audio_data)

    def reset_analysis(self):
        """Reset analysis state"""
        self.analyzer.reset_analysis()
        self.status_label.setText("Analysis reset")
        self.status_label.setStyleSheet("background-color: #2a2a2a; color: white; padding: 5px;")

    def get_analysis_settings(self) -> Dict[str, Any]:
        """Get current analysis settings"""
        return {
            "mode": self.mode_combo.currentText(),
            "update_rate": self.rate_spin.value(),
            "is_analyzing": self.is_analyzing
        }

    def set_analysis_settings(self, settings: Dict[str, Any]):
        """Apply analysis settings"""
        if "mode" in settings:
            self.mode_combo.setCurrentText(settings["mode"])
        if "update_rate" in settings:
            self.rate_spin.setValue(settings["update_rate"])
        if "is_analyzing" in settings and settings["is_analyzing"]:
            self.start_stop_button.setChecked(True)