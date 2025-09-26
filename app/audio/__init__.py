"""
Professional Audio Processing System for CineAIStudio
Comprehensive audio editing, processing, and analysis capabilities
"""

from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from pathlib import Path
import logging

# Import all audio components
from .mixer.audio_mixer import (
    AudioMixer, AudioTrack, AudioBus, AudioTrackType, AutomationMode, AutomationPoint
)
from .analysis.audio_analyzer import (
    AudioAnalyzer, AudioMetrics, LevelMeter, SpectrumAnalyzer, PhaseMeter, AnalysisMode
)
from .effects.advanced_effects import (
    AdvancedEffectsProcessor, AudioEffect, EffectType, EffectParameter
)
from .processing.professional_audio_engine import (
    ProfessionalAudioEngine, ProcessingMode, AudioFormat, ChannelConfiguration,
    AudioQuality, ProcessingRequest, ProcessingResult, NoiseProfile, AudioRestorationEngine,
    RealTimeNoiseReduction, AudioDeclipper, HumReducer, SpatialAudioProcessor,
    AudioVideoSynchronizer, AudioProcessingThread, AudioCacheManager
)
from .processing.realtime_processor import (
    RealTimeAudioProcessor, LowLatencyBuffer, ProcessingChain, ProcessingPriority,
    LatencyMode, RealTimeEffect, RealTimeCompressor, RealTimeEqualizer,
    RealTimeLimiter, RealTimeNoiseGate, AudioProcessingPipeline
)
from .analysis.professional_analyzer import (
    ProfessionalAudioAnalyzer, AnalysisType, MetricCategory, SpectralFeatures,
    TemporalFeatures, PerceptualFeatures, TechnicalMetrics, AudioQualityAssessment,
    AdvancedSpectrumAnalyzer, PerceptualAnalyzer, TechnicalAnalyzer
)
from .synchronization.audio_video_sync import (
    AudioVideoSynchronizer as SyncSystem, SyncMethod, SyncQuality, SyncStatus, TimeCode,
    SyncPoint, SyncResult, AudioFeatureExtractor, VideoFeatureExtractor,
    CorrelationAnalyzer
)

__all__ = [
    # Core Components
    'AudioMixer', 'AudioTrack', 'AudioBus', 'AudioTrackType', 'AutomationMode', 'AutomationPoint',
    'AudioAnalyzer', 'AudioMetrics', 'LevelMeter', 'SpectrumAnalyzer', 'PhaseMeter', 'AnalysisMode',
    'AdvancedEffectsProcessor', 'AudioEffect', 'EffectType', 'EffectParameter',

    # Professional Engine
    'ProfessionalAudioEngine', 'ProcessingMode', 'AudioFormat', 'ChannelConfiguration',
    'AudioQuality', 'ProcessingRequest', 'ProcessingResult', 'NoiseProfile', 'AudioRestorationEngine',
    'RealTimeNoiseReduction', 'AudioDeclipper', 'HumReducer', 'SpatialAudioProcessor',
    'AudioProcessingThread', 'AudioCacheManager',

    # Real-time Processing
    'RealTimeAudioProcessor', 'LowLatencyBuffer', 'ProcessingChain', 'ProcessingPriority',
    'LatencyMode', 'RealTimeEffect', 'RealTimeCompressor', 'RealTimeEqualizer',
    'RealTimeLimiter', 'RealTimeNoiseGate', 'AudioProcessingPipeline',

    # Professional Analysis
    'ProfessionalAudioAnalyzer', 'AnalysisType', 'MetricCategory', 'SpectralFeatures',
    'TemporalFeatures', 'PerceptualFeatures', 'TechnicalMetrics', 'AudioQualityAssessment',
    'AdvancedSpectrumAnalyzer', 'PerceptualAnalyzer', 'TechnicalAnalyzer',

    # Synchronization
    'SyncSystem', 'SyncMethod', 'SyncQuality', 'SyncStatus', 'TimeCode',
    'SyncPoint', 'SyncResult', 'AudioFeatureExtractor', 'VideoFeatureExtractor',
    'CorrelationAnalyzer',

    # Main System Interface
    'AudioSystem'
]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioSystem:
    """Main audio system interface for CineAIStudio"""

    def __init__(self, sample_rate: int = 48000, buffer_size: int = 1024):
        """Initialize the complete audio system"""
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size

        # Core components
        self.mixer = AudioMixer()
        self.analyzer = ProfessionalAudioAnalyzer(sample_rate, buffer_size)
        self.effects_processor = AdvancedEffectsProcessor(sample_rate)
        self.realtime_processor = RealTimeAudioProcessor(sample_rate, buffer_size)
        self.sync_system = SyncSystem(sample_rate)
        self.engine = ProfessionalAudioEngine(sample_rate)

        # System state
        self.is_initialized = True
        self.current_project = None
        self.settings = self._load_default_settings()

        logger.info("Audio System initialized successfully")

    def _load_default_settings(self) -> Dict[str, Any]:
        """Load default audio system settings"""
        return {
            "sample_rate": self.sample_rate,
            "buffer_size": self.buffer_size,
            "output_format": AudioFormat.WAV,
            "quality": AudioQuality.HIGH,
            "processing_mode": ProcessingMode.OFFLINE,
            "sync_tolerance": 0.02,  # 20ms
            "monitoring_enabled": True,
            "auto_save": True,
            "backup_enabled": True
        }

    def initialize_audio_hardware(self) -> bool:
        """Initialize audio hardware and devices"""
        try:
            # Get available devices
            devices = self.realtime_processor.get_available_devices()
            logger.info(f"Found {len(devices['input'])} input and {len(devices['output'])} output devices")

            # Try to initialize default devices
            if devices['output']:
                self.realtime_processor.start_streaming()
                logger.info("Audio hardware initialized successfully")
                return True
            else:
                logger.warning("No audio output devices found")
                return False

        except Exception as e:
            logger.error(f"Failed to initialize audio hardware: {e}")
            return False

    def create_audio_track(self, name: str, track_type: AudioTrackType = AudioTrackType.STEREO) -> str:
        """Create a new audio track"""
        track_id = self.mixer.add_track(name, track_type)
        logger.info(f"Created audio track '{name}' with ID: {track_id}")
        return track_id

    def create_audio_bus(self, name: str, input_channels: int = 2, output_channels: int = 2) -> str:
        """Create a new audio bus"""
        bus_id = self.mixer.add_bus(name, input_channels, output_channels)
        logger.info(f"Created audio bus '{name}' with ID: {bus_id}")
        return bus_id

    def process_audio_file(self, file_path: str, operations: List[Dict[str, Any]]) -> str:
        """Process audio file with specified operations"""
        return self.engine.process_audio_file(file_path, operations)

    def analyze_audio_file(self, file_path: str) -> str:
        """Analyze audio file comprehensively"""
        return self.analyzer.analyze_audio_file(file_path)

    def synchronize_audio_video(self, audio_path: str, video_path: str, method: SyncMethod = SyncMethod.AUTOMATIC) -> str:
        """Synchronize audio with video"""
        return self.sync_system.synchronize_audio_video(audio_path, video_path, method)

    def start_realtime_monitoring(self):
        """Start real-time audio monitoring"""
        self.realtime_processor.start_realtime_monitoring()
        self.analyzer.start_realtime_monitoring()
        logger.info("Real-time monitoring started")

    def stop_realtime_monitoring(self):
        """Stop real-time audio monitoring"""
        self.realtime_processor.stop_realtime_monitoring()
        self.analyzer.stop_realtime_monitoring()
        logger.info("Real-time monitoring stopped")

    def export_audio(self, audio_data: np.ndarray, output_path: str, quality: AudioQuality = AudioQuality.HIGH) -> bool:
        """Export audio with specified quality"""
        return self.engine.export_audio(audio_data, output_path, quality)

    def apply_effect_chain(self, audio_data: np.ndarray, effect_chain: List[Dict[str, Any]]) -> np.ndarray:
        """Apply chain of audio effects"""
        return self.effects_processor.apply_effect_chain(audio_data, effect_chain)

    def get_system_performance(self) -> Dict[str, Any]:
        """Get comprehensive system performance metrics"""
        engine_perf = self.engine.get_system_performance()
        realtime_perf = self.realtime_processor.get_performance_metrics()
        mixer_state = self.mixer.get_mixer_state()
        sync_status = self.sync_system.get_sync_status()

        return {
            "engine": engine_perf,
            "realtime_processor": realtime_perf,
            "mixer": mixer_state,
            "synchronization": sync_status,
            "timestamp": __import__('time').time()
        }

    def save_project(self, project_path: str) -> bool:
        """Save current audio project"""
        try:
            project_data = {
                "settings": self.settings,
                "mixer_state": self.mixer.export_mixer_settings(),
                "sync_data": self.sync_system.get_sync_status(),
                "timestamp": __import__('time').time(),
                "version": "1.0"
            }

            import json
            with open(project_path, 'w') as f:
                json.dump(project_data, f, indent=2)

            logger.info(f"Project saved to: {project_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save project: {e}")
            return False

    def load_project(self, project_path: str) -> bool:
        """Load audio project from file"""
        try:
            import json
            with open(project_path, 'r') as f:
                project_data = json.load(f)

            # Load settings
            self.settings.update(project_data.get("settings", {}))

            # Load mixer state
            if "mixer_state" in project_data:
                self.mixer.load_mixer_state_from_dict(project_data["mixer_state"])

            # Load sync data
            if "sync_data" in project_data:
                sync_file = project_path.replace('.json', '_sync.json')
                self.sync_system.import_sync_data(sync_file)

            logger.info(f"Project loaded from: {project_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load project: {e}")
            return False

    def shutdown(self):
        """Shutdown audio system cleanly"""
        try:
            self.realtime_processor.stop_streaming()
            self.engine.stop_processing()
            logger.info("Audio system shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    def get_available_effects(self) -> Dict[str, AudioEffect]:
        """Get all available audio effects"""
        return self.effects_processor.get_available_effects()

    def get_analysis_types(self) -> List[str]:
        """Get available analysis types"""
        return [analysis_type.value for analysis_type in AnalysisType]

    def get_sync_methods(self) -> List[str]:
        """Get available synchronization methods"""
        return [method.value for method in SyncMethod]

    def get_quality_presets(self) -> List[str]:
        """Get available quality presets"""
        return [quality.value for quality in AudioQuality]

    def get_format_options(self) -> List[str]:
        """Get available audio formats"""
        return [format_option.value for format_option in AudioFormat]

    def create_preset(self, name: str, effect_chain: List[Dict[str, Any]]) -> bool:
        """Create and save audio processing preset"""
        try:
            preset_path = Path("presets") / f"{name}.json"
            preset_path.parent.mkdir(exist_ok=True)

            import json
            preset_data = {
                "name": name,
                "effect_chain": effect_chain,
                "created_time": __import__('time').time(),
                "version": "1.0"
            }

            with open(preset_path, 'w') as f:
                json.dump(preset_data, f, indent=2)

            logger.info(f"Preset '{name}' saved successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to create preset: {e}")
            return False

    def load_preset(self, name: str) -> Optional[List[Dict[str, Any]]]:
        """Load audio processing preset"""
        try:
            preset_path = Path("presets") / f"{name}.json"

            if not preset_path.exists():
                logger.error(f"Preset '{name}' not found")
                return None

            import json
            with open(preset_path, 'r') as f:
                preset_data = json.load(f)

            logger.info(f"Preset '{name}' loaded successfully")
            return preset_data.get("effect_chain", [])

        except Exception as e:
            logger.error(f"Failed to load preset: {e}")
            return None

    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        import psutil
        import platform

        return {
            "system": {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version()
            },
            "hardware": {
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_total": psutil.disk_usage('/').total,
                "disk_free": psutil.disk_usage('/').free
            },
            "audio": {
                "sample_rate": self.sample_rate,
                "buffer_size": self.buffer_size,
                "is_initialized": self.is_initialized,
                "available_effects": len(self.get_available_effects()),
                "analysis_types": len(self.get_analysis_types()),
                "sync_methods": len(self.get_sync_methods())
            }
        }

    def diagnose_system(self) -> Dict[str, Any]:
        """Run system diagnostics and return results"""
        diagnostics = {
            "status": "healthy",
            "warnings": [],
            "errors": [],
            "recommendations": []
        }

        try:
            # Check audio hardware
            devices = self.realtime_processor.get_available_devices()
            if not devices['output']:
                diagnostics["errors"].append("No audio output devices found")
                diagnostics["status"] = "error"

            # Check system resources
            import psutil
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent

            if cpu_usage > 80:
                diagnostics["warnings"].append(f"High CPU usage: {cpu_usage}%")
                diagnostics["recommendations"].append("Consider closing other applications")

            if memory_usage > 80:
                diagnostics["warnings"].append(f"High memory usage: {memory_usage}%")
                diagnostics["recommendations"].append("Consider freeing up memory")

            # Check audio system performance
            performance = self.get_system_performance()
            engine_perf = performance.get("engine", {})

            if engine_perf.get("cpu_usage", 0) > 70:
                diagnostics["warnings"].append("Audio processing CPU usage is high")

            # Check buffer sizes
            if self.buffer_size > 2048:
                diagnostics["warnings"].append(f"Large buffer size ({self.buffer_size}) may increase latency")
                diagnostics["recommendations"].append("Consider reducing buffer size for lower latency")

            if self.buffer_size < 256:
                diagnostics["warnings"].append(f"Small buffer size ({self.buffer_size}) may cause glitches")
                diagnostics["recommendations"].append("Consider increasing buffer size for stability")

        except Exception as e:
            diagnostics["errors"].append(f"Diagnostic error: {str(e)}")
            diagnostics["status"] = "error"

        return diagnostics


# Global audio system instance
_audio_system = None


def get_audio_system() -> AudioSystem:
    """Get the global audio system instance"""
    global _audio_system
    if _audio_system is None:
        _audio_system = AudioSystem()
    return _audio_system


def initialize_audio_system(sample_rate: int = 48000, buffer_size: int = 1024) -> AudioSystem:
    """Initialize the global audio system"""
    global _audio_system
    _audio_system = AudioSystem(sample_rate, buffer_size)
    return _audio_system


# Convenience functions for common operations
def process_audio(file_path: str, operations: List[Dict[str, Any]]) -> str:
    """Process audio file using global audio system"""
    system = get_audio_system()
    return system.process_audio_file(file_path, operations)


def analyze_audio(file_path: str) -> str:
    """Analyze audio file using global audio system"""
    system = get_audio_system()
    return system.analyze_audio_file(file_path)


def synchronize_audio_video(audio_path: str, video_path: str, method: SyncMethod = SyncMethod.AUTOMATIC) -> str:
    """Synchronize audio with video using global audio system"""
    system = get_audio_system()
    return system.synchronize_audio_video(audio_path, video_path, method)


def export_audio(audio_data: np.ndarray, output_path: str, quality: AudioQuality = AudioQuality.HIGH) -> bool:
    """Export audio using global audio system"""
    system = get_audio_system()
    return system.export_audio(audio_data, output_path, quality)


def create_preset(name: str, effect_chain: List[Dict[str, Any]]) -> bool:
    """Create audio processing preset"""
    system = get_audio_system()
    return system.create_preset(name, effect_chain)


def load_preset(name: str) -> Optional[List[Dict[str, Any]]]:
    """Load audio processing preset"""
    system = get_audio_system()
    return system.load_preset(name)


def get_system_info() -> Dict[str, Any]:
    """Get system information"""
    system = get_audio_system()
    return system.get_system_info()


def run_diagnostics() -> Dict[str, Any]:
    """Run system diagnostics"""
    system = get_audio_system()
    return system.diagnose_system()


# Example usage and demonstrations
def demonstrate_audio_system():
    """Demonstrate audio system capabilities"""
    print("=== CineAIStudio Professional Audio System ===")
    print()

    # Get system information
    system_info = get_system_info()
    print("System Information:")
    print(f"  Platform: {system_info['system']['platform']}")
    print(f"  CPU: {system_info['hardware']['cpu_count']} cores")
    print(f"  Memory: {system_info['hardware']['memory_total'] / (1024**3):.1f} GB")
    print()

    # Initialize audio system
    audio_system = get_audio_system()
    print("Audio System Components:")
    print(f"  Sample Rate: {audio_system.sample_rate} Hz")
    print(f"  Buffer Size: {audio_system.buffer_size} samples")
    print(f"  Available Effects: {len(audio_system.get_available_effects())}")
    print(f"  Analysis Types: {len(audio_system.get_analysis_types())}")
    print(f"  Sync Methods: {len(audio_system.get_sync_methods())}")
    print()

    # Show available options
    print("Available Audio Formats:")
    for format_option in audio_system.get_format_options():
        print(f"  - {format_option}")

    print("\nAvailable Quality Presets:")
    for quality in audio_system.get_quality_presets():
        print(f"  - {quality}")

    print("\nAvailable Analysis Types:")
    for analysis_type in audio_system.get_analysis_types():
        print(f"  - {analysis_type}")

    print("\nAvailable Synchronization Methods:")
    for sync_method in audio_system.get_sync_methods():
        print(f"  - {sync_method}")

    print("\n=== Usage Examples ===")
    print("# Process audio file with noise reduction and EQ")
    print("operations = [")
    print("    {'type': 'noise_reduction', 'strength': 0.8},")
    print("    {'type': 'equalization', 'preset': 'vocal_enhancement'},")
    print("    {'type': 'compression', 'threshold': -18, 'ratio': 3.0}")
    print("]")
    print("process_audio('input.wav', operations)")
    print()

    print("# Analyze audio quality")
    print("analyze_audio('input.wav')")
    print()

    print("# Synchronize audio with video")
    print("synchronize_audio_video('audio.wav', 'video.mp4')")
    print()

    print("# Create audio track")
    print("audio_system.create_audio_track('Vocals', AudioTrackType.STEREO)")
    print()

    print("# Export high-quality audio")
    print("export_audio(processed_audio, 'output.wav', AudioQuality.STUDIO)")
    print()

    # Run diagnostics
    print("Running system diagnostics...")
    diagnostics = run_diagnostics()
    print(f"System Status: {diagnostics['status'].upper()}")

    if diagnostics['warnings']:
        print("Warnings:")
        for warning in diagnostics['warnings']:
            print(f"  - {warning}")

    if diagnostics['recommendations']:
        print("Recommendations:")
        for recommendation in diagnostics['recommendations']:
            print(f"  - {recommendation}")

    if diagnostics['errors']:
        print("Errors:")
        for error in diagnostics['errors']:
            print(f"  - {error}")

    print("\n=== Audio System Ready ===")


if __name__ == "__main__":
    demonstrate_audio_system()