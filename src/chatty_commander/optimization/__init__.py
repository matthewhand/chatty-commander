"""
AI-Powered Performance Optimization & Auto-Tuning System for ChattyCommander.

This package provides intelligent performance optimization including:
- Predictive model caching based on usage patterns
- Real-time performance monitoring with ML-based anomaly detection
- Adaptive audio processing with automatic threshold adjustment
- Auto-tuning system for inference parameter optimization
"""

from .intelligent_cache import IntelligentModelCache
from .performance_monitor import AIPerformanceMonitor
from .adaptive_audio import AdaptiveAudioProcessor
from .auto_tuner import PerformanceAutoTuner
from .optimizer_orchestrator import OptimizationOrchestrator

__all__ = [
    'IntelligentModelCache',
    'AIPerformanceMonitor', 
    'AdaptiveAudioProcessor',
    'PerformanceAutoTuner',
    'OptimizationOrchestrator'
]