"""
Audio Integration Module for CineAIStudio
Integrates the professional audio system with the existing timeline and video processing
"""

from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal

# Import audio components
from app.audio import AudioMixer, AudioAnalyzer, AdvancedEffectsProcessor
from app.core.timeline_engine import TimelineEngine, AudioTrack as TimelineAudioTrack
from app.core.video_processor import VideoProcessor
from app.effects.effects_system import EffectsEngine


class AudioIntegrationManager(QObject):
    """Integrates audio system with timeline and video processing"""

    # Signals
    audio_processed = pyqtSignal(str, np.ndarray)  # track_id, audio_data
    mixer_updated = pyqtSignal(dict)  # mixer state
    analysis_complete = pyqtSignal(dict)  # analysis results
    effects_applied = pyqtSignal(str, str)  # track_id, effect_id

    def __init__(self):
        super().__init__()

        # Audio processing components
        self.mixer = AudioMixer()
        self.analyzer = AudioAnalyzer()
        self.effects_processor = AdvancedEffectsProcessor()

        # Reference to other systems
        self.timeline_engine = None
        self.video_processor = None
        self.effects_engine = None

        # Audio processing state
        self.sample_rate = 48000
        self.buffer_size = 1024
        self.audio_tracks = {}
        self.processed_audio = {}

        # Connect audio system signals
        self._connect_audio_signals()

    def _connect_audio_signals(self):
        """Connect signals between audio components"""
        # Mixer signals
        self.mixer.track_added.connect(self._on_track_added)
        self.mixer.track_removed.connect(self._on_track_removed)
        self.mixer.levels_updated.connect(self._on_levels_updated)

        # Analyzer signals
        self.analyzer.metrics_updated.connect(self._on_metrics_updated)
        self.analyzer.warning_detected.connect(self._on_warning_detected)

    def set_timeline_engine(self, timeline_engine: TimelineEngine):
        """Set reference to timeline engine"""
        self.timeline_engine = timeline_engine
        self._sync_with_timeline()

    def set_video_processor(self, video_processor: VideoProcessor):
        """Set reference to video processor"""
        self.video_processor = video_processor

    def set_effects_engine(self, effects_engine: EffectsEngine):
        """Set reference to effects engine"""
        self.effects_engine = effects_engine

    def _sync_with_timeline(self):
        """Sync audio mixer with timeline audio tracks"""
        if not self.timeline_engine:
            return

        # Clear existing mixer tracks
        for track_id in list(self.mixer.tracks.keys()):
            self.mixer.remove_track(track_id)

        # Add timeline audio tracks to mixer
        for track_id, track in self.timeline_engine.tracks.items():
            if track.track_type == "audio":
                mixer_track_id = self.mixer.add_track(
                    name=track.name,
                    track_type=getattr(self.mixer.AudioTrackType, "STEREO")
                )

                # Set initial volume from timeline
                self.mixer.set_track_volume(mixer_track_id, track.volume)

                # Store mapping
                self.audio_tracks[track_id] = mixer_track_id

    def _on_track_added(self, mixer_track_id: str):
        """Handle mixer track added"""
        self.mixer_updated.emit(self.mixer.export_mixer_settings())

    def _on_track_removed(self, mixer_track_id: str):
        """Handle mixer track removed"""
        self.mixer_updated.emit(self.mixer.export_mixer_settings())

    def _on_levels_updated(self, levels: Dict[str, float]):
        """Handle level updates"""
        # Update timeline with new levels
        if self.timeline_engine:
            for track_id, mixer_id in self.audio_tracks.items():
                if f"track_{mixer_id}" in levels:
                    level = levels[f"track_{mixer_id}"]
                    # Update timeline track levels
                    pass

    def _on_metrics_updated(self, metrics):
        """Handle analysis metrics updated"""
        analysis_data = {
            "timestamp": __import__('time').time(),
            "peak_level": metrics.peak_level,
            "rms_level": metrics.rms_level,
            "lufs_level": metrics.lufs_level,
            "true_peak": metrics.max_true_peak,
            "crest_factor": metrics.crest_factor,
            "phase_correlation": metrics.phase_correlation,
            "stereo_width": metrics.stereo_width
        }

        if hasattr(metrics, 'spectral_centroid'):
            analysis_data["spectral_centroid"] = metrics.spectral_centroid

        self.analysis_complete.emit(analysis_data)

    def _on_warning_detected(self, warning: str):
        """Handle audio warnings"""
        print(f"Audio Warning: {warning}")

    def process_timeline_audio(self) -> Dict[str, np.ndarray]:
        """Process all audio from timeline tracks"""
        if not self.timeline_engine:
            return {}

        processed_audio = {}

        for track_id, track in self.timeline_engine.tracks.items():
            if track.track_type == "audio" and track.audio_file:
                try:
                    # Load audio file
                    import librosa
                    audio_data, sr = librosa.load(track.audio_file, sr=self.sample_rate)

                    # Apply track volume
                    audio_data = audio_data * track.volume

                    # Apply mixer processing if track is mapped
                    if track_id in self.audio_tracks:
                        mixer_track_id = self.audio_tracks[track_id]
                        audio_data = self.mixer.process_audio(audio_data, mixer_track_id)

                    processed_audio[track_id] = audio_data

                except Exception as e:
                    print(f"Error processing audio track {track_id}: {e}")

        return processed_audio

    def mix_down_audio(self, audio_tracks: Dict[str, np.ndarray]) -> np.ndarray:
        """Mix down multiple audio tracks"""
        return self.mixer.mix_down(audio_tracks)

    def apply_audio_effects(self, track_id: str, effect_chain: List[Dict[str, Any]]) -> np.ndarray:
        """Apply audio effects to a track"""
        if track_id not in self.processed_audio:
            return np.array([])

        audio_data = self.processed_audio[track_id]
        processed_audio = self.effects_processor.apply_effect_chain(audio_data, effect_chain)

        self.processed_audio[track_id] = processed_audio
        self.effects_applied.emit(track_id, "chain_applied")

        return processed_audio

    def analyze_audio_track(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Analyze specific audio track"""
        if not self.timeline_engine or track_id not in self.timeline_engine.tracks:
            return None

        track = self.timeline_engine.tracks[track_id]
        if track.track_type != "audio" or not track.audio_file:
            return None

        try:
            # Use analyzer to process file
            metrics = self.analyzer.analyze_file(track.audio_file)

            return {
                "track_id": track_id,
                "track_name": track.name,
                "duration": track.duration,
                "peak_level": metrics.peak_level,
                "rms_level": metrics.rms_level,
                "lufs_level": metrics.lufs_level,
                "true_peak": metrics.max_true_peak,
                "crest_factor": metrics.crest_factor,
                "dynamic_range": metrics.dynamic_range
            }

        except Exception as e:
            print(f"Error analyzing track {track_id}: {e}")
            return None

    def get_audio_recommendations(self, track_id: str) -> Dict[str, Any]:
        """Get audio processing recommendations for a track"""
        if track_id not in self.processed_audio:
            return {}

        audio_data = self.processed_audio[track_id]
        recommendations = self.effects_processor.get_effect_recommendations(audio_data)

        return {
            "track_id": track_id,
            "recommendations": recommendations,
            "timestamp": __import__('time').time()
        }

    def export_audio_stems(self, output_dir: str) -> Dict[str, str]:
        """Export individual audio stems"""
        if not self.timeline_engine:
            return {}

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        exported_files = {}

        for track_id, track in self.timeline_engine.tracks.items():
            if track.track_type == "audio" and track.audio_file:
                try:
                    # Process track audio
                    audio_data = self.process_timeline_audio().get(track_id)
                    if audio_data is not None:
                        stem_filename = f"{track.name.replace(' ', '_')}_stem.wav"
                        stem_path = output_path / stem_filename

                        # Export stem
                        import soundfile as sf
                        sf.write(str(stem_path), audio_data.T if len(audio_data.shape) > 1 else audio_data,
                               self.sample_rate)

                        exported_files[track_id] = str(stem_path)

                except Exception as e:
                    print(f"Error exporting stem for track {track_id}: {e}")

        return exported_files

    def export_mixdown(self, output_path: str) -> bool:
        """Export final audio mixdown"""
        try:
            # Process and mix all timeline audio
            audio_tracks = self.process_timeline_audio()
            if not audio_tracks:
                return False

            # Mix down
            final_mix = self.mix_down(audio_tracks)

            # Apply master processing
            if not self.mixer.master_muted:
                final_mix = final_mix * self.mixer.master_volume

            # Export
            import soundfile as sf
            sf.write(output_path, final_mix.T if len(final_mix.shape) > 1 else final_mix,
                   self.sample_rate)

            return True

        except Exception as e:
            print(f"Error exporting mixdown: {e}")
            return False

    def create_audio_bus(self, name: str, track_ids: List[str] = None) -> str:
        """Create audio bus and optionally assign tracks"""
        bus_id = self.mixer.add_bus(name)

        # Assign tracks to bus
        if track_ids:
            for track_id in track_ids:
                if track_id in self.audio_tracks:
                    mixer_track_id = self.audio_tracks[track_id]
                    self.mixer.add_track_send(mixer_track_id, bus_id, 1.0)

        return bus_id

    def apply_effect_to_track(self, track_id: str, effect_id: str, parameters: Dict[str, float]):
        """Apply specific effect to audio track"""
        if track_id not in self.processed_audio:
            return

        audio_data = self.processed_audio[track_id]
        processed_audio = self.effects_processor.apply_effect(audio_data, effect_id, parameters)

        self.processed_audio[track_id] = processed_audio
        self.effects_applied.emit(track_id, effect_id)

    def get_mixer_state(self) -> Dict[str, Any]:
        """Get current mixer state"""
        return self.mixer.export_mixer_settings()

    def set_mixer_state(self, state: Dict[str, Any]):
        """Apply mixer state"""
        # This would involve parsing the state and applying it to the mixer
        # Implementation depends on the state format
        pass

    def start_realtime_analysis(self):
        """Start real-time audio analysis"""
        self.analyzer.start_analysis()

    def stop_realtime_analysis(self):
        """Stop real-time audio analysis"""
        self.analyzer.stop_analysis()

    def process_audio_chunk(self, audio_chunk: np.ndarray, track_id: str = None):
        """Process audio chunk in real-time"""
        # Process through mixer
        processed = self.mixer.process_audio(audio_chunk, track_id)

        # Send to analyzer
        self.analyzer.set_audio_data(processed)

        # Store processed audio
        if track_id:
            if track_id not in self.processed_audio:
                self.processed_audio[track_id] = []
            self.processed_audio[track_id].append(processed)

        return processed

    def get_audio_levels(self) -> Dict[str, Dict[str, float]]:
        """Get current audio levels for all tracks"""
        levels = {"master": {"peak": self.mixer.get_master_level(), "rms": self.mixer.get_master_level() * 0.7}}

        # Get track levels
        for track_id, mixer_id in self.audio_tracks.items():
            track_levels = self.mixer.get_track_levels(mixer_id)
            if track_levels:
                levels[track_id] = track_levels

        return levels

    def reset_audio_processing(self):
        """Reset audio processing state"""
        self.processed_audio.clear()
        self.analyzer.reset_analysis()

        # Reset mixer (except configuration)
        for track_id in self.mixer.tracks:
            self.mixer.tracks[track_id].volume = 1.0
            self.mixer.tracks[track_id].pan = 0.0
            self.mixer.tracks[track_id].muted = False

        self.mixer.master_volume = 1.0
        self.mixer.master_muted = False