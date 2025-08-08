"""
Adaptive Audio Processing System with Environmental Intelligence.

This module provides intelligent audio processing that adapts to environmental
conditions, automatically adjusts thresholds, and optimizes for different acoustic scenarios.
"""

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


class AudioEnvironment(Enum):
    """Audio environment classification."""
    QUIET = "quiet"
    NORMAL = "normal"
    NOISY = "noisy"
    VERY_NOISY = "very_noisy"


class AdaptationMode(Enum):
    """Audio adaptation modes."""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


@dataclass
class AudioMetrics:
    """Audio processing metrics."""
    timestamp: float
    noise_level: float
    signal_strength: float
    snr_ratio: float
    false_positives: int
    false_negatives: int
    detection_confidence: float
    processing_latency: float
    environment: AudioEnvironment


@dataclass
class AudioThresholds:
    """Dynamic audio thresholds."""
    detection_threshold: float
    confidence_threshold: float
    noise_gate: float
    gain_adjustment: float
    timeout_duration: float
    sensitivity: float


@dataclass
class EnvironmentProfile:
    """Audio environment profile."""
    environment: AudioEnvironment
    avg_noise_level: float
    typical_snr: float
    optimal_thresholds: AudioThresholds
    adaptation_history: List[float]
    performance_score: float


class AdaptiveAudioProcessor:
    """
    Intelligent audio processor that adapts to environmental conditions.
    
    Features:
    - Real-time environmental noise analysis
    - Automatic threshold adjustment
    - False positive/negative reduction
    - Environment-specific optimization
    - Performance-driven adaptation
    - Context-aware processing
    """
    
    def __init__(
        self,
        adaptation_mode: AdaptationMode = AdaptationMode.BALANCED,
        learning_rate: float = 0.1,
        environment_detection_window: int = 50,
        performance_window: int = 100
    ):
        self.adaptation_mode = adaptation_mode
        self.learning_rate = learning_rate
        self.environment_detection_window = environment_detection_window
        self.performance_window = performance_window
        
        # Current audio state
        self.current_environment = AudioEnvironment.NORMAL
        self.current_thresholds = self._get_default_thresholds()
        self.base_thresholds = self._get_default_thresholds()
        
        # Data collection
        self.audio_history: deque = deque(maxlen=1000)
        self.environment_history: deque = deque(maxlen=200)
        self.performance_history: deque = deque(maxlen=performance_window)
        
        # Environment profiles
        self.environment_profiles: Dict[AudioEnvironment, EnvironmentProfile] = {}
        self._initialize_environment_profiles()
        
        # ML components
        self.environment_classifier: Optional[KMeans] = None
        self.feature_scaler = StandardScaler()
        self.is_trained = False
        
        # Adaptation state
        self.is_adapting = False
        self.last_adaptation_time = 0.0
        self.adaptation_interval = 5.0  # seconds
        self.confidence_buffer: deque = deque(maxlen=20)
        
        # Performance tracking
        self.total_detections = 0
        self.false_positives = 0
        self.false_negatives = 0
        self.avg_processing_time = 0.0
        
        # Callbacks
        self.threshold_change_callbacks: List[Callable] = []
        self.environment_change_callbacks: List[Callable] = []
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized AdaptiveAudioProcessor in {adaptation_mode.value} mode")
    
    def _get_default_thresholds(self) -> AudioThresholds:
        """Get default audio processing thresholds."""
        return AudioThresholds(
            detection_threshold=0.5,
            confidence_threshold=0.7,
            noise_gate=0.1,
            gain_adjustment=1.0,
            timeout_duration=2.0,
            sensitivity=0.8
        )
    
    def _initialize_environment_profiles(self) -> None:
        """Initialize default environment profiles."""
        environments = {
            AudioEnvironment.QUIET: AudioThresholds(
                detection_threshold=0.3,
                confidence_threshold=0.6,
                noise_gate=0.05,
                gain_adjustment=1.2,
                timeout_duration=1.5,
                sensitivity=0.9
            ),
            AudioEnvironment.NORMAL: AudioThresholds(
                detection_threshold=0.5,
                confidence_threshold=0.7,
                noise_gate=0.1,
                gain_adjustment=1.0,
                timeout_duration=2.0,
                sensitivity=0.8
            ),
            AudioEnvironment.NOISY: AudioThresholds(
                detection_threshold=0.7,
                confidence_threshold=0.8,
                noise_gate=0.2,
                gain_adjustment=0.8,
                timeout_duration=2.5,
                sensitivity=0.6
            ),
            AudioEnvironment.VERY_NOISY: AudioThresholds(
                detection_threshold=0.8,
                confidence_threshold=0.85,
                noise_gate=0.3,
                gain_adjustment=0.6,
                timeout_duration=3.0,
                sensitivity=0.4
            )
        }
        
        for env, thresholds in environments.items():
            self.environment_profiles[env] = EnvironmentProfile(
                environment=env,
                avg_noise_level=0.0,
                typical_snr=10.0,
                optimal_thresholds=thresholds,
                adaptation_history=[],
                performance_score=0.8
            )
    
    async def process_audio_frame(
        self,
        audio_data: np.ndarray,
        ground_truth: Optional[bool] = None
    ) -> Tuple[bool, float]:
        """
        Process audio frame with adaptive thresholds.
        
        Args:
            audio_data: Audio frame data
            ground_truth: Optional ground truth for training (True if wake word present)
            
        Returns:
            Tuple of (detection_result, confidence)
        """
        start_time = time.perf_counter()
        
        # Extract audio features
        features = self._extract_audio_features(audio_data)
        
        # Analyze environmental conditions
        env_metrics = self._analyze_environment(features)
        self.audio_history.append(env_metrics)
        
        # Adaptive processing
        detection_result, confidence = await self._adaptive_detection(features, env_metrics)
        
        # Record performance metrics
        processing_time = time.perf_counter() - start_time
        await self._record_performance(detection_result, confidence, processing_time, ground_truth)
        
        # Trigger adaptation if needed
        await self._check_adaptation_trigger()
        
        return detection_result, confidence
    
    def _extract_audio_features(self, audio_data: np.ndarray) -> Dict[str, float]:
        """Extract features from audio frame."""
        # Calculate basic audio features
        rms_energy = np.sqrt(np.mean(audio_data ** 2))
        zero_crossings = np.sum(np.diff(np.sign(audio_data)) != 0) / len(audio_data)
        spectral_centroid = self._calculate_spectral_centroid(audio_data)
        spectral_rolloff = self._calculate_spectral_rolloff(audio_data)
        
        return {
            'rms_energy': float(rms_energy),
            'zero_crossings': float(zero_crossings),
            'spectral_centroid': float(spectral_centroid),
            'spectral_rolloff': float(spectral_rolloff),
            'peak_amplitude': float(np.max(np.abs(audio_data))),
            'dynamic_range': float(np.max(audio_data) - np.min(audio_data))
        }
    
    def _calculate_spectral_centroid(self, audio_data: np.ndarray) -> float:
        """Calculate spectral centroid of audio signal."""
        # Simplified spectral centroid calculation
        fft = np.fft.fft(audio_data)
        magnitude = np.abs(fft)
        frequencies = np.fft.fftfreq(len(audio_data))
        
        # Avoid division by zero
        total_magnitude = np.sum(magnitude)
        if total_magnitude == 0:
            return 0.0
        
        return np.sum(frequencies * magnitude) / total_magnitude
    
    def _calculate_spectral_rolloff(self, audio_data: np.ndarray, rolloff_percent: float = 0.85) -> float:
        """Calculate spectral rolloff point."""
        fft = np.fft.fft(audio_data)
        magnitude = np.abs(fft)
        
        # Calculate cumulative energy
        cumulative_energy = np.cumsum(magnitude)
        total_energy = cumulative_energy[-1]
        
        if total_energy == 0:
            return 0.0
        
        # Find rolloff point
        rolloff_threshold = rolloff_percent * total_energy
        rolloff_index = np.where(cumulative_energy >= rolloff_threshold)[0]
        
        if len(rolloff_index) == 0:
            return 0.0
        
        return rolloff_index[0] / len(audio_data)
    
    def _analyze_environment(self, features: Dict[str, float]) -> AudioMetrics:
        """Analyze current audio environment."""
        # Calculate noise level
        noise_level = features['rms_energy']
        signal_strength = features['peak_amplitude']
        
        # Estimate SNR
        snr_ratio = signal_strength / (noise_level + 1e-8)
        
        # Classify environment
        environment = self._classify_environment(noise_level, snr_ratio)
        
        return AudioMetrics(
            timestamp=time.time(),
            noise_level=noise_level,
            signal_strength=signal_strength,
            snr_ratio=snr_ratio,
            false_positives=0,  # Will be updated based on feedback
            false_negatives=0,  # Will be updated based on feedback
            detection_confidence=0.0,  # Will be updated after detection
            processing_latency=0.0,  # Will be updated after processing
            environment=environment
        )
    
    def _classify_environment(self, noise_level: float, snr_ratio: float) -> AudioEnvironment:
        """Classify current audio environment."""
        # Simple rule-based classification (could be enhanced with ML)
        if noise_level < 0.1 and snr_ratio > 15:
            return AudioEnvironment.QUIET
        elif noise_level < 0.3 and snr_ratio > 8:
            return AudioEnvironment.NORMAL
        elif noise_level < 0.6 and snr_ratio > 3:
            return AudioEnvironment.NOISY
        else:
            return AudioEnvironment.VERY_NOISY
    
    async def _adaptive_detection(
        self,
        features: Dict[str, float],
        env_metrics: AudioMetrics
    ) -> Tuple[bool, float]:
        """Perform detection with adaptive thresholds."""
        # Apply current thresholds
        thresholds = self.current_thresholds
        
        # Adjust for current environment
        adjusted_thresholds = self._adjust_thresholds_for_environment(thresholds, env_metrics)
        
        # Simulate wake word detection (would be replaced with actual model inference)
        detection_score = self._calculate_detection_score(features, env_metrics)
        
        # Apply thresholds
        detection_result = detection_score > adjusted_thresholds.detection_threshold
        confidence = min(1.0, detection_score / adjusted_thresholds.confidence_threshold)
        
        # Update metrics
        env_metrics.detection_confidence = confidence
        
        return detection_result, confidence
    
    def _adjust_thresholds_for_environment(
        self,
        base_thresholds: AudioThresholds,
        env_metrics: AudioMetrics
    ) -> AudioThresholds:
        """Dynamically adjust thresholds based on current environment."""
        # Get environment-specific baseline
        env_profile = self.environment_profiles.get(env_metrics.environment)
        if not env_profile:
            return base_thresholds
        
        # Apply adaptation mode
        adaptation_factor = self._get_adaptation_factor(env_metrics)
        
        return AudioThresholds(
            detection_threshold=base_thresholds.detection_threshold * adaptation_factor,
            confidence_threshold=base_thresholds.confidence_threshold * adaptation_factor,
            noise_gate=max(0.01, base_thresholds.noise_gate * (1 + env_metrics.noise_level)),
            gain_adjustment=base_thresholds.gain_adjustment / max(0.1, env_metrics.noise_level + 0.1),
            timeout_duration=base_thresholds.timeout_duration * (1 + env_metrics.noise_level * 0.5),
            sensitivity=base_thresholds.sensitivity * (1 - env_metrics.noise_level * 0.3)
        )
    
    def _get_adaptation_factor(self, env_metrics: AudioMetrics) -> float:
        """Calculate adaptation factor based on environment and mode."""
        base_factor = 1.0
        
        # Environment-based adjustment
        env_adjustments = {
            AudioEnvironment.QUIET: 0.8,
            AudioEnvironment.NORMAL: 1.0,
            AudioEnvironment.NOISY: 1.2,
            AudioEnvironment.VERY_NOISY: 1.4
        }
        
        env_factor = env_adjustments.get(env_metrics.environment, 1.0)
        
        # Mode-based adjustment
        mode_multipliers = {
            AdaptationMode.CONSERVATIVE: 0.9,
            AdaptationMode.BALANCED: 1.0,
            AdaptationMode.AGGRESSIVE: 1.1
        }
        
        mode_factor = mode_multipliers.get(self.adaptation_mode, 1.0)
        
        # SNR-based fine-tuning
        snr_factor = 1.0
        if env_metrics.snr_ratio < 5:
            snr_factor = 1.3  # Increase thresholds for low SNR
        elif env_metrics.snr_ratio > 15:
            snr_factor = 0.9  # Decrease thresholds for high SNR
        
        return base_factor * env_factor * mode_factor * snr_factor
    
    def _calculate_detection_score(
        self,
        features: Dict[str, float],
        env_metrics: AudioMetrics
    ) -> float:
        """Calculate detection score (simplified wake word detection simulation)."""
        # This would be replaced with actual model inference
        # For now, simulate based on energy and spectral features
        
        energy_score = min(1.0, features['rms_energy'] * 5.0)
        spectral_score = min(1.0, abs(features['spectral_centroid']) * 2.0)
        dynamic_score = min(1.0, features['dynamic_range'] * 2.0)
        
        # Combine scores
        raw_score = (energy_score * 0.4 + spectral_score * 0.3 + dynamic_score * 0.3)
        
        # Apply SNR adjustment
        snr_adjustment = min(1.5, env_metrics.snr_ratio / 10.0)
        
        return raw_score * snr_adjustment
    
    async def _record_performance(
        self,
        detection_result: bool,
        confidence: float,
        processing_time: float,
        ground_truth: Optional[bool] = None
    ) -> None:
        """Record performance metrics for adaptation."""
        self.total_detections += 1
        
        # Update processing time
        self.avg_processing_time = (
            (self.avg_processing_time * (self.total_detections - 1) + processing_time)
            / self.total_detections
        )
        
        # Track false positives/negatives if ground truth available
        if ground_truth is not None:
            if detection_result and not ground_truth:
                self.false_positives += 1
            elif not detection_result and ground_truth:
                self.false_negatives += 1
        
        # Add to confidence buffer
        self.confidence_buffer.append(confidence)
        
        # Record performance snapshot
        performance_metrics = {
            'timestamp': time.time(),
            'detection_result': detection_result,
            'confidence': confidence,
            'processing_time': processing_time,
            'environment': self.current_environment,
            'false_positive_rate': self.false_positives / max(1, self.total_detections),
            'false_negative_rate': self.false_negatives / max(1, self.total_detections)
        }
        
        self.performance_history.append(performance_metrics)
    
    async def _check_adaptation_trigger(self) -> None:
        """Check if adaptation should be triggered."""
        current_time = time.time()
        
        # Rate limiting
        if current_time - self.last_adaptation_time < self.adaptation_interval:
            return
        
        # Check adaptation triggers
        should_adapt = False
        
        # Performance-based trigger
        if len(self.performance_history) >= 20:
            recent_performance = list(self.performance_history)[-20:]
            avg_confidence = np.mean([p['confidence'] for p in recent_performance])
            
            if avg_confidence < 0.6:  # Low confidence trigger
                should_adapt = True
                self.logger.info(f"Triggering adaptation due to low confidence: {avg_confidence:.3f}")
        
        # Environment change trigger
        if len(self.audio_history) >= 10:
            recent_environments = [m.environment for m in list(self.audio_history)[-10:]]
            if len(set(recent_environments)) > 1:  # Environment instability
                should_adapt = True
                self.logger.info("Triggering adaptation due to environment changes")
        
        if should_adapt:
            await self._perform_adaptation()
            self.last_adaptation_time = current_time
    
    async def _perform_adaptation(self) -> None:
        """Perform threshold adaptation based on recent performance."""
        if not self.performance_history:
            return
        
        self.is_adapting = True
        self.logger.info("Performing audio threshold adaptation...")
        
        try:
            # Analyze recent performance
            recent_metrics = list(self.performance_history)[-50:]
            performance_score = self._calculate_performance_score(recent_metrics)
            
            # Detect current environment trend
            recent_audio = list(self.audio_history)[-20:]
            if recent_audio:
                env_counts = {}
                for metrics in recent_audio:
                    env = metrics.environment
                    env_counts[env] = env_counts.get(env, 0) + 1
                
                # Update current environment to most common recent environment
                dominant_env = max(env_counts.keys(), key=lambda x: env_counts[x])
                
                if dominant_env != self.current_environment:
                    await self._switch_environment(dominant_env)
            
            # Adaptive threshold adjustment
            await self._adjust_thresholds_based_on_performance(performance_score)
            
            # Update environment profile
            self._update_environment_profile(performance_score)
            
        except Exception as e:
            self.logger.error(f"Adaptation failed: {e}")
        finally:
            self.is_adapting = False
    
    def _calculate_performance_score(self, metrics: List[Dict]) -> float:
        """Calculate overall performance score."""
        if not metrics:
            return 0.5
        
        # Confidence score
        confidences = [m['confidence'] for m in metrics]
        avg_confidence = np.mean(confidences)
        confidence_stability = 1.0 - np.std(confidences)
        
        # Processing time score
        processing_times = [m['processing_time'] for m in metrics]
        avg_processing_time = np.mean(processing_times)
        time_score = max(0.0, 1.0 - (avg_processing_time - 0.05) / 0.1)  # Penalty after 50ms
        
        # Error rate score
        fp_rate = metrics[-1]['false_positive_rate'] if metrics else 0.0
        fn_rate = metrics[-1]['false_negative_rate'] if metrics else 0.0
        error_score = 1.0 - (fp_rate + fn_rate)
        
        # Combine scores
        overall_score = (
            avg_confidence * 0.4 +
            confidence_stability * 0.2 +
            time_score * 0.2 +
            error_score * 0.2
        )
        
        return max(0.0, min(1.0, overall_score))
    
    async def _switch_environment(self, new_environment: AudioEnvironment) -> None:
        """Switch to new environment profile."""
        old_environment = self.current_environment
        self.current_environment = new_environment
        
        # Load optimal thresholds for new environment
        env_profile = self.environment_profiles[new_environment]
        self.current_thresholds = env_profile.optimal_thresholds
        
        self.logger.info(f"Environment switch: {old_environment.value} -> {new_environment.value}")
        
        # Notify callbacks
        for callback in self.environment_change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(old_environment, new_environment)
                else:
                    callback(old_environment, new_environment)
            except Exception as e:
                self.logger.error(f"Environment change callback failed: {e}")
    
    async def _adjust_thresholds_based_on_performance(self, performance_score: float) -> None:
        """Adjust thresholds based on performance feedback."""
        # Calculate adjustment magnitude
        target_score = 0.8
        score_diff = performance_score - target_score
        adjustment_magnitude = abs(score_diff) * self.learning_rate
        
        # Determine adjustment direction
        if performance_score < target_score:
            # Performance below target - relax thresholds
            adjustment_factor = 1.0 - adjustment_magnitude
        else:
            # Performance above target - tighten thresholds slightly
            adjustment_factor = 1.0 + (adjustment_magnitude * 0.5)
        
        # Apply adjustments
        old_thresholds = self.current_thresholds
        
        self.current_thresholds = AudioThresholds(
            detection_threshold=old_thresholds.detection_threshold * adjustment_factor,
            confidence_threshold=old_thresholds.confidence_threshold * adjustment_factor,
            noise_gate=old_thresholds.noise_gate,  # Keep noise gate stable
            gain_adjustment=old_thresholds.gain_adjustment,  # Keep gain stable
            timeout_duration=old_thresholds.timeout_duration,  # Keep timeout stable
            sensitivity=max(0.1, min(1.0, old_thresholds.sensitivity * adjustment_factor))
        )
        
        self.logger.info(
            f"Threshold adaptation: score={performance_score:.3f}, "
            f"detection={old_thresholds.detection_threshold:.3f}->{self.current_thresholds.detection_threshold:.3f}, "
            f"confidence={old_thresholds.confidence_threshold:.3f}->{self.current_thresholds.confidence_threshold:.3f}"
        )
        
        # Notify callbacks
        for callback in self.threshold_change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(old_thresholds, self.current_thresholds)
                else:
                    callback(old_thresholds, self.current_thresholds)
            except Exception as e:
                self.logger.error(f"Threshold change callback failed: {e}")
    
    def _update_environment_profile(self, performance_score: float) -> None:
        """Update the current environment profile based on recent performance."""
        profile = self.environment_profiles[self.current_environment]
        
        # Update performance score with exponential moving average
        alpha = 0.1
        profile.performance_score = (
            alpha * performance_score + (1 - alpha) * profile.performance_score
        )
        
        # Update adaptation history
        profile.adaptation_history.append(performance_score)
        if len(profile.adaptation_history) > 100:
            profile.adaptation_history = profile.adaptation_history[-100:]
        
        # Update optimal thresholds if performance improved
        if performance_score > profile.performance_score:
            profile.optimal_thresholds = self.current_thresholds
    
    def get_current_thresholds(self) -> AudioThresholds:
        """Get current audio processing thresholds."""
        return self.current_thresholds
    
    def get_environment_status(self) -> Dict[str, Any]:
        """Get current environment status and metrics."""
        recent_audio = list(self.audio_history)[-10:] if self.audio_history else []
        
        return {
            'current_environment': self.current_environment.value,
            'current_thresholds': self.current_thresholds,
            'is_adapting': self.is_adapting,
            'recent_noise_level': np.mean([m.noise_level for m in recent_audio]) if recent_audio else 0.0,
            'recent_snr': np.mean([m.snr_ratio for m in recent_audio]) if recent_audio else 0.0,
            'performance_score': self.environment_profiles[self.current_environment].performance_score,
            'total_detections': self.total_detections,
            'false_positive_rate': self.false_positives / max(1, self.total_detections),
            'false_negative_rate': self.false_negatives / max(1, self.total_detections),
            'avg_processing_time': self.avg_processing_time
        }
    
    def add_threshold_change_callback(self, callback: Callable) -> None:
        """Add callback for threshold changes."""
        self.threshold_change_callbacks.append(callback)
    
    def add_environment_change_callback(self, callback: Callable) -> None:
        """Add callback for environment changes."""
        self.environment_change_callbacks.append(callback)
    
    def set_adaptation_mode(self, mode: AdaptationMode) -> None:
        """Set adaptation mode."""
        old_mode = self.adaptation_mode
        self.adaptation_mode = mode
        self.logger.info(f"Adaptation mode changed: {old_mode.value} -> {mode.value}")
    
    def reset_performance_metrics(self) -> None:
        """Reset performance counters."""
        self.total_detections = 0
        self.false_positives = 0
        self.false_negatives = 0
        self.avg_processing_time = 0.0
        self.performance_history.clear()
        self.logger.info("Performance metrics reset")