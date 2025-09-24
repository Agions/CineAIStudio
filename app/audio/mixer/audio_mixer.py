"""
Professional Audio Mixer Module for CineAIStudio
Provides comprehensive multi-track audio mixing capabilities with professional features
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtMultimedia import QAudioOutput, QAudioFormat
import librosa
import soundfile as sf
from scipy import signal
import matplotlib.pyplot as plt


class AudioTrackType(Enum):
    """Audio track types"""
    MONO = "mono"
    STEREO = "stereo"
    SURROUND_5_1 = "surround_5.1"
    SURROUND_7_1 = "surround_7_1"


class AutomationMode(Enum):
    """Automation recording modes"""
    OFF = "off"
    READ = "read"
    WRITE = "write"
    LATCH = "latch"
    TOUCH = "touch"


@dataclass
class AudioTrack:
    """Audio track configuration"""
    id: str
    name: str
    track_type: AudioTrackType
    volume: float = 1.0
    pan: float = 0.0  # -1.0 (left) to 1.0 (right)
    muted: bool = False
    soloed: bool = False
    armed: bool = False
    input_channels: int = 2
    output_channels: int = 2
    color: str = "#4CAF50"
    height: int = 100
    effects: List[str] = None
    sends: Dict[str, float] = None
    automation_data: Dict[str, List[Tuple[float, float]]] = None

    def __post_init__(self):
        if self.effects is None:
            self.effects = []
        if self.sends is None:
            self.sends = {}
        if self.automation_data is None:
            self.automation_data = {}


@dataclass
class AudioBus:
    """Audio bus configuration"""
    id: str
    name: str
    volume: float = 1.0
    muted: bool = False
    soloed: bool = False
    input_channels: int = 2
    output_channels: int = 2
    effects: List[str] = None
    sends: Dict[str, float] = None

    def __post_init__(self):
        if self.effects is None:
            self.effects = []
        if self.sends is None:
            self.sends = {}


@dataclass
class AutomationPoint:
    """Automation data point"""
    time: float  # Time in seconds
    value: float  # Parameter value
    curve_type: str = "linear"  # linear, logarithmic, exponential


class AudioMixer(QObject):
    """Professional audio mixing console"""

    # Signals
    track_added = pyqtSignal(str)  # Track ID
    track_removed = pyqtSignal(str)  # Track ID
    track_volume_changed = pyqtSignal(str, float)  # Track ID, volume
    track_pan_changed = pyqtSignal(str, float)  # Track ID, pan
    track_mute_changed = pyqtSignal(str, bool)  # Track ID, muted
    track_solo_changed = pyqtSignal(str, bool)  # Track ID, soloed
    bus_added = pyqtSignal(str)  # Bus ID
    bus_removed = pyqtSignal(str)  # Bus ID
    bus_volume_changed = pyqtSignal(str, float)  # Bus ID, volume
    master_volume_changed = pyqtSignal(float)  # Master volume
    master_mute_changed = pyqtSignal(bool)  # Master muted
    levels_updated = pyqtSignal(dict)  # Level data
    automation_recorded = pyqtSignal(str, str, list)  # Track ID, parameter, points
    solo_changed = pyqtSignal()  # Solo state changed

    def __init__(self):
        super().__init__()

        # Audio tracks and buses
        self.tracks: Dict[str, AudioTrack] = {}
        self.buses: Dict[str, AudioBus] = {}

        # Master output
        self.master_volume = 1.0
        self.master_muted = False
        self.master_effects = []

        # Audio format
        self.sample_rate = 48000
        self.buffer_size = 1024
        self.bit_depth = 32

        # Automation
        self.automation_mode = AutomationMode.OFF
        self.automation_write_threshold = 0.01  # Minimum change to record

        # Solo logic
        self.soloed_tracks = set()
        self.soloed_buses = set()

        # Audio processing
        self.audio_format = QAudioFormat()
        self.audio_format.setSampleRate(self.sample_rate)
        self.audio_format.setChannelCount(2)
        self.audio_format.setSampleFormat(QAudioFormat.SampleFormat.Float)

        # Analysis
        self.level_meter_interval = 50  # ms
        self.level_timer = QTimer()
        self.level_timer.timeout.connect(self._update_levels)
        self.level_timer.start(self.level_meter_interval)

        # Current levels
        self.track_levels = {}
        self.bus_levels = {}
        self.master_level = 0.0

        # Initialize default buses
        self._create_default_buses()

    def _create_default_buses(self):
        """Create default audio buses"""
        # Main mix bus
        main_bus = AudioBus(
            id="main",
            name="Main Mix",
            volume=1.0,
            input_channels=2,
            output_channels=2
        )
        self.buses["main"] = main_bus
        self.bus_added.emit("main")

    def add_track(self, name: str, track_type: AudioTrackType = AudioTrackType.STEREO,
                  color: str = "#4CAF50") -> str:
        """Add a new audio track"""
        track_id = f"track_{len(self.tracks) + 1}"

        track = AudioTrack(
            id=track_id,
            name=name,
            track_type=track_type,
            color=color,
            input_channels=2 if track_type == AudioTrackType.STEREO else 1,
            output_channels=2 if track_type == AudioTrackType.STEREO else 1
        )

        self.tracks[track_id] = track
        self.track_levels[track_id] = {"peak": 0.0, "rms": 0.0}

        self.track_added.emit(track_id)
        return track_id

    def remove_track(self, track_id: str) -> bool:
        """Remove an audio track"""
        if track_id in self.tracks:
            del self.tracks[track_id]
            if track_id in self.track_levels:
                del self.track_levels[track_id]

            # Update solo state
            self.soloed_tracks.discard(track_id)
            self.solo_changed.emit()

            self.track_removed.emit(track_id)
            return True
        return False

    def add_bus(self, name: str, input_channels: int = 2, output_channels: int = 2) -> str:
        """Add a new audio bus"""
        bus_id = f"bus_{len(self.buses) + 1}"

        bus = AudioBus(
            id=bus_id,
            name=name,
            input_channels=input_channels,
            output_channels=output_channels
        )

        self.buses[bus_id] = bus
        self.bus_levels[bus_id] = {"peak": 0.0, "rms": 0.0}

        self.bus_added.emit(bus_id)
        return bus_id

    def remove_bus(self, bus_id: str) -> bool:
        """Remove an audio bus"""
        if bus_id in self.buses and bus_id != "main":  # Can't remove main bus
            del self.buses[bus_id]
            if bus_id in self.bus_levels:
                del self.bus_levels[bus_id]

            # Update solo state
            self.soloed_buses.discard(bus_id)
            self.solo_changed.emit()

            self.bus_removed.emit(bus_id)
            return True
        return False

    def set_track_volume(self, track_id: str, volume: float) -> bool:
        """Set track volume (0.0 to 2.0)"""
        if track_id not in self.tracks:
            return False

        volume = max(0.0, min(2.0, volume))
        self.tracks[track_id].volume = volume

        # Record automation if in write mode
        if self.automation_mode == AutomationMode.WRITE:
            self._record_automation(track_id, "volume", volume)

        self.track_volume_changed.emit(track_id, volume)
        return True

    def set_track_pan(self, track_id: str, pan: float) -> bool:
        """Set track pan (-1.0 to 1.0)"""
        if track_id not in self.tracks:
            return False

        pan = max(-1.0, min(1.0, pan))
        self.tracks[track_id].pan = pan

        # Record automation if in write mode
        if self.automation_mode == AutomationMode.WRITE:
            self._record_automation(track_id, "pan", pan)

        self.track_pan_changed.emit(track_id, pan)
        return True

    def set_track_mute(self, track_id: str, muted: bool) -> bool:
        """Set track mute state"""
        if track_id not in self.tracks:
            return False

        self.tracks[track_id].muted = muted
        self.track_mute_changed.emit(track_id, muted)
        return True

    def set_track_solo(self, track_id: str, soloed: bool) -> bool:
        """Set track solo state"""
        if track_id not in self.tracks:
            return False

        self.tracks[track_id].soloed = soloed

        if soloed:
            self.soloed_tracks.add(track_id)
        else:
            self.soloed_tracks.discard(track_id)

        self.solo_changed.emit()
        self.track_solo_changed.emit(track_id, soloed)
        return True

    def set_bus_volume(self, bus_id: str, volume: float) -> bool:
        """Set bus volume (0.0 to 2.0)"""
        if bus_id not in self.buses:
            return False

        volume = max(0.0, min(2.0, volume))
        self.buses[bus_id].volume = volume
        self.bus_volume_changed.emit(bus_id, volume)
        return True

    def set_master_volume(self, volume: float):
        """Set master volume (0.0 to 2.0)"""
        volume = max(0.0, min(2.0, volume))
        self.master_volume = volume
        self.master_volume_changed.emit(volume)

    def set_master_mute(self, muted: bool):
        """Set master mute state"""
        self.master_muted = muted
        self.master_mute_changed.emit(muted)

    def set_automation_mode(self, mode: AutomationMode):
        """Set automation recording mode"""
        self.automation_mode = mode

    def _record_automation(self, track_id: str, parameter: str, value: float):
        """Record automation data"""
        if track_id not in self.tracks:
            return

        track = self.tracks[track_id]
        if parameter not in track.automation_data:
            track.automation_data[parameter] = []

        current_time = 0.0  # Get actual time from timeline
        last_point = track.automation_data[parameter][-1] if track.automation_data[parameter] else None

        # Only record if value changed significantly
        if last_point is None or abs(value - last_point[1]) >= self.automation_write_threshold:
            track.automation_data[parameter].append((current_time, value))
            self.automation_recorded.emit(track_id, parameter, track.automation_data[parameter])

    def _update_levels(self):
        """Update audio level meters"""
        # Simulate level updates (in real implementation, this would process actual audio)
        levels = {}

        # Update track levels
        for track_id in self.tracks:
            if not self.tracks[track_id].muted:
                # Simulate audio levels
                import random
                peak = random.uniform(0.1, 0.8) * self.tracks[track_id].volume
                rms = peak * 0.7
                self.track_levels[track_id] = {"peak": peak, "rms": rms}
                levels[track_id] = {"peak": peak, "rms": rms}

        # Update bus levels
        for bus_id in self.buses:
            import random
            peak = random.uniform(0.2, 0.9) * self.buses[bus_id].volume
            rms = peak * 0.7
            self.bus_levels[bus_id] = {"peak": peak, "rms": rms}
            levels[f"bus_{bus_id}"] = {"peak": peak, "rms": rms}

        # Update master level
        import random
        self.master_level = random.uniform(0.3, 0.95) * self.master_volume
        levels["master"] = {"peak": self.master_level, "rms": self.master_level * 0.7}

        self.levels_updated.emit(levels)

    def get_track_levels(self, track_id: str) -> Optional[Dict[str, float]]:
        """Get current track levels"""
        return self.track_levels.get(track_id)

    def get_bus_levels(self, bus_id: str) -> Optional[Dict[str, float]]:
        """Get current bus levels"""
        return self.bus_levels.get(bus_id)

    def get_master_level(self) -> float:
        """Get current master level"""
        return self.master_level

    def is_any_solo(self) -> bool:
        """Check if any track or bus is soloed"""
        return len(self.soloed_tracks) > 0 or len(self.soloed_buses) > 0

    def should_play_track(self, track_id: str) -> bool:
        """Check if track should play considering solo/mute logic"""
        track = self.tracks.get(track_id)
        if not track:
            return False

        # Track is muted
        if track.muted:
            return False

        # If no solo, play if not muted
        if not self.is_any_solo():
            return True

        # If solo active, only play if this track is soloed
        return track.soloed

    def should_play_bus(self, bus_id: str) -> bool:
        """Check if bus should play considering solo/mute logic"""
        bus = self.buses.get(bus_id)
        if not bus:
            return False

        # Bus is muted
        if bus.muted:
            return False

        # If no solo, play if not muted
        if not self.is_any_solo():
            return True

        # If solo active, only play if this bus is soloed
        return bus.soloed

    def add_track_send(self, track_id: str, bus_id: str, level: float = 0.0) -> bool:
        """Add a send from track to bus"""
        if track_id not in self.tracks or bus_id not in self.buses:
            return False

        self.tracks[track_id].sends[bus_id] = max(0.0, min(1.0, level))
        return True

    def remove_track_send(self, track_id: str, bus_id: str) -> bool:
        """Remove a send from track to bus"""
        if track_id not in self.tracks:
            return False

        if bus_id in self.tracks[track_id].sends:
            del self.tracks[track_id].sends[bus_id]
            return True
        return False

    def set_send_level(self, track_id: str, bus_id: str, level: float) -> bool:
        """Set send level from track to bus"""
        if track_id not in self.tracks or bus_id not in self.buses:
            return False

        if bus_id not in self.tracks[track_id].sends:
            return False

        self.tracks[track_id].sends[bus_id] = max(0.0, min(1.0, level))
        return True

    def get_automation_data(self, track_id: str, parameter: str) -> List[Tuple[float, float]]:
        """Get automation data for a track parameter"""
        track = self.tracks.get(track_id)
        if not track:
            return []

        return track.automation_data.get(parameter, [])

    def clear_automation(self, track_id: str, parameter: str = None):
        """Clear automation data"""
        if track_id not in self.tracks:
            return

        if parameter:
            if parameter in self.tracks[track_id].automation_data:
                del self.tracks[track_id].automation_data[parameter]
        else:
            self.tracks[track_id].automation_data.clear()

    def save_mixer_state(self, file_path: str) -> bool:
        """Save mixer state to file"""
        try:
            state = {
                "tracks": {},
                "buses": {},
                "master": {
                    "volume": self.master_volume,
                    "muted": self.master_muted
                },
                "sample_rate": self.sample_rate,
                "buffer_size": self.buffer_size
            }

            # Save tracks
            for track_id, track in self.tracks.items():
                state["tracks"][track_id] = {
                    "name": track.name,
                    "track_type": track.track_type.value,
                    "volume": track.volume,
                    "pan": track.pan,
                    "muted": track.muted,
                    "soloed": track.soloed,
                    "armed": track.armed,
                    "input_channels": track.input_channels,
                    "output_channels": track.output_channels,
                    "color": track.color,
                    "height": track.height,
                    "effects": track.effects,
                    "sends": track.sends,
                    "automation_data": track.automation_data
                }

            # Save buses
            for bus_id, bus in self.buses.items():
                state["buses"][bus_id] = {
                    "name": bus.name,
                    "volume": bus.volume,
                    "muted": bus.muted,
                    "soloed": bus.soloed,
                    "input_channels": bus.input_channels,
                    "output_channels": bus.output_channels,
                    "effects": bus.effects,
                    "sends": bus.sends
                }

            with open(file_path, 'w') as f:
                json.dump(state, f, indent=2)

            return True

        except Exception as e:
            print(f"Error saving mixer state: {e}")
            return False

    def load_mixer_state(self, file_path: str) -> bool:
        """Load mixer state from file"""
        try:
            with open(file_path, 'r') as f:
                state = json.load(f)

            # Clear existing state
            self.tracks.clear()
            self.buses.clear()
            self.track_levels.clear()
            self.bus_levels.clear()
            self.soloed_tracks.clear()
            self.soloed_buses.clear()

            # Load master settings
            master = state.get("master", {})
            self.master_volume = master.get("volume", 1.0)
            self.master_muted = master.get("muted", False)
            self.sample_rate = state.get("sample_rate", 48000)
            self.buffer_size = state.get("buffer_size", 1024)

            # Load tracks
            for track_id, track_data in state.get("tracks", {}).items():
                track = AudioTrack(
                    id=track_id,
                    name=track_data["name"],
                    track_type=AudioTrackType(track_data["track_type"]),
                    volume=track_data.get("volume", 1.0),
                    pan=track_data.get("pan", 0.0),
                    muted=track_data.get("muted", False),
                    soloed=track_data.get("soloed", False),
                    armed=track_data.get("armed", False),
                    input_channels=track_data.get("input_channels", 2),
                    output_channels=track_data.get("output_channels", 2),
                    color=track_data.get("color", "#4CAF50"),
                    height=track_data.get("height", 100),
                    effects=track_data.get("effects", []),
                    sends=track_data.get("sends", {}),
                    automation_data=track_data.get("automation_data", {})
                )
                self.tracks[track_id] = track
                self.track_levels[track_id] = {"peak": 0.0, "rms": 0.0}

                if track.soloed:
                    self.soloed_tracks.add(track_id)

                self.track_added.emit(track_id)

            # Load buses
            for bus_id, bus_data in state.get("buses", {}).items():
                bus = AudioBus(
                    id=bus_id,
                    name=bus_data["name"],
                    volume=bus_data.get("volume", 1.0),
                    muted=bus_data.get("muted", False),
                    soloed=bus_data.get("soloed", False),
                    input_channels=bus_data.get("input_channels", 2),
                    output_channels=bus_data.get("output_channels", 2),
                    effects=bus_data.get("effects", []),
                    sends=bus_data.get("sends", {})
                )
                self.buses[bus_id] = bus
                self.bus_levels[bus_id] = {"peak": 0.0, "rms": 0.0}

                if bus.soloed:
                    self.soloed_buses.add(bus_id)

                self.bus_added.emit(bus_id)

            self.solo_changed.emit()
            return True

        except Exception as e:
            print(f"Error loading mixer state: {e}")
            return False

    def process_audio(self, audio_data: np.ndarray, track_id: str = None) -> np.ndarray:
        """Process audio through the mixer"""
        if track_id and track_id in self.tracks:
            track = self.tracks[track_id]

            # Apply volume
            audio_data = audio_data * track.volume

            # Apply pan for stereo
            if audio_data.shape[0] == 2 and track.pan != 0:
                left_gain = 1.0 - max(0, track.pan)
                right_gain = 1.0 - max(0, -track.pan)
                audio_data[0] *= left_gain
                audio_data[1] *= right_gain

            # Apply sends to buses
            for bus_id, send_level in track.sends.items():
                if bus_id in self.buses:
                    # In real implementation, this would route to the bus
                    pass

        return audio_data

    def mix_down(self, tracks_data: Dict[str, np.ndarray]) -> np.ndarray:
        """Mix down multiple tracks"""
        if not tracks_data:
            return np.array([])

        # Determine output format
        sample_count = max(data.shape[1] if len(data.shape) > 1 else len(data)
                          for data in tracks_data.values())
        output = np.zeros((2, sample_count))  # Stereo output

        # Mix each track
        for track_id, audio_data in tracks_data.items():
            if self.should_play_track(track_id):
                processed = self.process_audio(audio_data, track_id)

                # Ensure same length
                if len(processed.shape) == 1:
                    processed = processed.reshape(1, -1)

                if processed.shape[1] < sample_count:
                    padded = np.zeros((processed.shape[0], sample_count))
                    padded[:, :processed.shape[1]] = processed
                    processed = padded

                # Mix to output
                output += processed[:, :sample_count]

        # Apply master volume
        output = output * self.master_volume

        return output

    def export_mixer_settings(self) -> Dict[str, Any]:
        """Export mixer settings as dictionary"""
        return {
            "tracks": {
                track_id: {
                    "name": track.name,
                    "volume": track.volume,
                    "pan": track.pan,
                    "muted": track.muted,
                    "soloed": track.soloed,
                    "sends": track.sends
                }
                for track_id, track in self.tracks.items()
            },
            "buses": {
                bus_id: {
                    "name": bus.name,
                    "volume": bus.volume,
                    "muted": bus.muted,
                    "soloed": bus.soloed
                }
                for bus_id, bus in self.buses.items()
            },
            "master": {
                "volume": self.master_volume,
                "muted": self.master_muted
            }
        }