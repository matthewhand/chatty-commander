"""
Optimization Orchestrator - Unified AI-Powered Performance Optimization.

This module coordinates all optimization components to provide intelligent,
comprehensive performance optimization for the ChattyCommander system.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .adaptive_audio import AdaptiveAudioProcessor, AudioEnvironment, AdaptationMode
from .auto_tuner import PerformanceAutoTuner, OptimizationObjective, OptimizationResult
from .intelligent_cache import IntelligentModelCache, CacheMetrics
from .performance_monitor import AIPerformanceMonitor, PerformanceAlert, PerformanceReport


@dataclass
class OptimizationStatus:
    """Overall optimization system status."""
    is_active: bool
    cache_optimization: bool
    performance_monitoring: bool
    audio_adaptation: bool
    parameter_tuning: bool
    overall_performance_score: float
    active_optimizations: List[str]
    recommendations: List[str]


@dataclass
class OptimizationConfig:
    """Configuration for optimization orchestrator."""
    enable_cache_optimization: bool = True
    enable_performance_monitoring: bool = True
    enable_audio_adaptation: bool = True
    enable_parameter_tuning: bool = True
    auto_optimization_interval: float = 300.0  # 5 minutes
    performance_alert_threshold: float = 0.7
    cache_memory_limit_mb: int = 512
    audio_adaptation_mode: AdaptationMode = AdaptationMode.BALANCED
    tuning_objective: OptimizationObjective = OptimizationObjective.BALANCED


class OptimizationOrchestrator:
    """
    Unified orchestrator for AI-powered performance optimization.
    
    Coordinates and manages all optimization components:
    - IntelligentModelCache for predictive model caching
    - AIPerformanceMonitor for real-time anomaly detection
    - AdaptiveAudioProcessor for environmental adaptation
    - PerformanceAutoTuner for parameter optimization
    
    Features:
    - Unified optimization control
    - Cross-component coordination
    - Intelligent optimization triggers
    - Performance correlation analysis
    - Automated optimization workflows
    - Comprehensive reporting
    """
    
    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or OptimizationConfig()
        
        # Initialize optimization components
        self.cache_optimizer: Optional[IntelligentModelCache] = None
        self.performance_monitor: Optional[AIPerformanceMonitor] = None
        self.audio_processor: Optional[AdaptiveAudioProcessor] = None
        self.auto_tuner: Optional[PerformanceAutoTuner] = None
        
        # Orchestrator state
        self.is_active = False
        self.optimization_task: Optional[asyncio.Task] = None
        self.last_optimization_time = 0.0
        
        # Performance tracking
        self.optimization_history: List[Dict[str, Any]] = []
        self.performance_baseline: Optional[Dict[str, float]] = None
        self.current_performance: Dict[str, float] = {}
        
        # Inter-component coordination
        self.component_callbacks: Dict[str, List[Callable]] = {
            'cache': [],
            'performance': [],
            'audio': [],
            'tuning': []
        }
        
        # Optimization triggers
        self.optimization_triggers: Dict[str, bool] = {
            'performance_degradation': False,
            'cache_efficiency_low': False,
            'audio_environment_change': False,
            'parameter_optimization_due': False
        }
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialized OptimizationOrchestrator")
    
    async def initialize(self) -> None:
        """Initialize all optimization components."""
        if self.config.enable_cache_optimization:
            self.cache_optimizer = IntelligentModelCache(
                max_cache_size_mb=self.config.cache_memory_limit_mb
            )
            self.logger.info("Initialized IntelligentModelCache")
        
        if self.config.enable_performance_monitoring:
            self.performance_monitor = AIPerformanceMonitor()
            self.performance_monitor.add_alert_callback(self._handle_performance_alert)
            self.logger.info("Initialized AIPerformanceMonitor")
        
        if self.config.enable_audio_adaptation:
            self.audio_processor = AdaptiveAudioProcessor(
                adaptation_mode=self.config.audio_adaptation_mode
            )
            self.audio_processor.add_environment_change_callback(self._handle_audio_environment_change)
            self.logger.info("Initialized AdaptiveAudioProcessor")
        
        if self.config.enable_parameter_tuning:
            self.auto_tuner = PerformanceAutoTuner(
                optimization_objective=self.config.tuning_objective
            )
            self.logger.info("Initialized PerformanceAutoTuner")
        
        # Record baseline performance
        await self._record_baseline_performance()
    
    async def start_optimization(self) -> None:
        """Start the optimization orchestrator."""
        if self.is_active:
            self.logger.warning("Optimization already active")
            return
        
        self.is_active = True
        
        # Start performance monitoring
        if self.performance_monitor:
            await self.performance_monitor.start_monitoring()
        
        # Start optimization loop
        self.optimization_task = asyncio.create_task(self._optimization_loop())
        
        self.logger.info("Started optimization orchestrator")
    
    async def stop_optimization(self) -> None:
        """Stop the optimization orchestrator."""
        if not self.is_active:
            return
        
        self.is_active = False
        
        # Stop optimization loop
        if self.optimization_task:
            self.optimization_task.cancel()
            try:
                await self.optimization_task
            except asyncio.CancelledError:
                pass
        
        # Stop performance monitoring
        if self.performance_monitor:
            await self.performance_monitor.stop_monitoring()
        
        # Graceful shutdown of components
        if self.cache_optimizer:
            await self.cache_optimizer.shutdown()
        
        # Stop any active tuning
        if self.auto_tuner and self.auto_tuner.is_tuning:
            await self.auto_tuner.stop_tuning_session()
        
        self.logger.info("Stopped optimization orchestrator")
    
    async def _optimization_loop(self) -> None:
        """Main optimization coordination loop."""
        while self.is_active:
            try:
                current_time = time.time()
                
                # Update current performance metrics
                await self._update_performance_metrics()
                
                # Check optimization triggers
                await self._check_optimization_triggers()
                
                # Execute coordinated optimization if triggered
                if any(self.optimization_triggers.values()):
                    await self._execute_coordinated_optimization()
                
                # Periodic full optimization
                if (current_time - self.last_optimization_time 
                    > self.config.auto_optimization_interval):
                    await self._execute_periodic_optimization()
                    self.last_optimization_time = current_time
                
            except Exception as e:
                self.logger.error(f"Error in optimization loop: {e}")
            
            await asyncio.sleep(1.0)  # Check every second
    
    async def _update_performance_metrics(self) -> None:
        """Update current performance metrics from all components."""
        metrics = {}
        
        # Performance monitor metrics
        if self.performance_monitor:
            report = self.performance_monitor.get_performance_report(period_hours=0.1)
            metrics.update({
                'overall_performance': report.overall_level.value,
                'average_latency': report.average_latency,
                'peak_memory_usage': report.peak_memory_usage,
                'cache_efficiency': report.cache_efficiency,
                'error_rate': report.error_rate,
                'anomalies_detected': report.anomalies_detected
            })
        
        # Cache metrics
        if self.cache_optimizer:
            cache_metrics = self.cache_optimizer.get_cache_metrics()
            metrics.update({
                'cache_hit_rate': cache_metrics.hit_rate,
                'cache_memory_usage': cache_metrics.memory_usage_mb,
                'cache_prediction_accuracy': cache_metrics.prediction_accuracy
            })
        
        # Audio processor metrics
        if self.audio_processor:
            audio_status = self.audio_processor.get_environment_status()
            metrics.update({
                'audio_environment': audio_status['current_environment'],
                'audio_performance_score': audio_status['performance_score'],
                'audio_false_positive_rate': audio_status['false_positive_rate']
            })
        
        # Auto-tuner metrics
        if self.auto_tuner:
            tuner_status = self.auto_tuner.get_optimization_status()
            metrics.update({
                'parameter_optimization_active': tuner_status['is_tuning'],
                'best_parameters': tuner_status['best_known_parameters']
            })
        
        self.current_performance = metrics
    
    async def _check_optimization_triggers(self) -> None:
        """Check for optimization triggers across components."""
        # Performance degradation trigger
        if self.performance_monitor:
            report = self.performance_monitor.get_performance_report(period_hours=0.1)
            performance_score = self._calculate_performance_score(report)
            
            if performance_score < self.config.performance_alert_threshold:
                self.optimization_triggers['performance_degradation'] = True
                self.logger.info(f"Performance degradation trigger: score={performance_score:.3f}")
        
        # Cache efficiency trigger
        if self.cache_optimizer:
            cache_metrics = self.cache_optimizer.get_cache_metrics()
            if cache_metrics.hit_rate < 0.6:  # Low cache hit rate
                self.optimization_triggers['cache_efficiency_low'] = True
                self.logger.info(f"Cache efficiency trigger: hit_rate={cache_metrics.hit_rate:.3f}")
        
        # Audio environment change trigger (handled by callback)
        
        # Parameter optimization due trigger
        if (self.auto_tuner and not self.auto_tuner.is_tuning and 
            time.time() - self.last_optimization_time > 1800):  # 30 minutes
            self.optimization_triggers['parameter_optimization_due'] = True
            self.logger.info("Parameter optimization due trigger")
    
    async def _execute_coordinated_optimization(self) -> None:
        """Execute coordinated optimization based on triggers."""
        active_triggers = [k for k, v in self.optimization_triggers.items() if v]
        self.logger.info(f"Executing coordinated optimization for triggers: {active_triggers}")
        
        optimization_tasks = []
        
        # Performance-based optimizations
        if self.optimization_triggers['performance_degradation']:
            if self.auto_tuner and not self.auto_tuner.is_tuning:
                optimization_tasks.append(self._optimize_parameters_for_performance())
        
        # Cache-based optimizations
        if self.optimization_triggers['cache_efficiency_low']:
            optimization_tasks.append(self._optimize_cache_strategy())
        
        # Audio-based optimizations
        if self.optimization_triggers['audio_environment_change']:
            optimization_tasks.append(self._optimize_audio_settings())
        
        # Parameter optimization
        if self.optimization_triggers['parameter_optimization_due']:
            if self.auto_tuner and not self.auto_tuner.is_tuning:
                optimization_tasks.append(self._run_parameter_optimization())
        
        # Execute optimizations
        if optimization_tasks:
            await asyncio.gather(*optimization_tasks, return_exceptions=True)
        
        # Clear triggers
        self.optimization_triggers = {k: False for k in self.optimization_triggers}
    
    async def _execute_periodic_optimization(self) -> None:
        """Execute periodic comprehensive optimization."""
        self.logger.info("Executing periodic optimization")
        
        # Record optimization session
        optimization_start = time.time()
        
        try:
            # Comprehensive parameter tuning if not already running
            if self.auto_tuner and not self.auto_tuner.is_tuning:
                result = await self._run_comprehensive_parameter_optimization()
                
                if result:
                    self.logger.info(
                        f"Periodic optimization completed. "
                        f"Performance improvement: {result.improvement_over_baseline:.2f}%"
                    )
        
        except Exception as e:
            self.logger.error(f"Periodic optimization failed: {e}")
        
        # Record optimization history
        optimization_duration = time.time() - optimization_start
        self.optimization_history.append({
            'timestamp': optimization_start,
            'duration': optimization_duration,
            'type': 'periodic',
            'performance_before': self.current_performance.copy(),
            'triggers': []
        })
    
    async def _optimize_parameters_for_performance(self) -> None:
        """Optimize parameters specifically for performance improvement."""
        if not self.auto_tuner:
            return
        
        self.logger.info("Optimizing parameters for performance")
        
        # Set optimization objective to latency
        self.auto_tuner.set_optimization_objective(OptimizationObjective.LATENCY)
        
        # Run focused optimization
        session_id = await self.auto_tuner.start_tuning_session(
            objective=OptimizationObjective.LATENCY,
            parameter_subset=['batch_size', 'inference_timeout', 'worker_threads']
        )
        
        # Run short optimization session
        result = await self.auto_tuner.run_optimization()
        
        if result and result.improvement_over_baseline > 5.0:  # 5% improvement
            self.logger.info(f"Performance optimization successful: {result.improvement_over_baseline:.2f}% improvement")
    
    async def _optimize_cache_strategy(self) -> None:
        """Optimize cache strategy and parameters."""
        if not self.cache_optimizer:
            return
        
        self.logger.info("Optimizing cache strategy")
        
        # This would trigger cache-specific optimizations
        # For now, we'll just log the action
        cache_metrics = self.cache_optimizer.get_cache_metrics()
        self.logger.info(f"Current cache metrics: hit_rate={cache_metrics.hit_rate:.3f}")
    
    async def _optimize_audio_settings(self) -> None:
        """Optimize audio processing settings."""
        if not self.audio_processor:
            return
        
        self.logger.info("Optimizing audio settings")
        
        # Reset performance metrics to allow for fresh adaptation
        self.audio_processor.reset_performance_metrics()
    
    async def _run_parameter_optimization(self) -> Optional[OptimizationResult]:
        """Run standard parameter optimization."""
        if not self.auto_tuner or self.auto_tuner.is_tuning:
            return None
        
        self.logger.info("Running parameter optimization")
        
        session_id = await self.auto_tuner.start_tuning_session()
        return await self.auto_tuner.run_optimization()
    
    async def _run_comprehensive_parameter_optimization(self) -> Optional[OptimizationResult]:
        """Run comprehensive parameter optimization with all parameters."""
        if not self.auto_tuner or self.auto_tuner.is_tuning:
            return None
        
        self.logger.info("Running comprehensive parameter optimization")
        
        session_id = await self.auto_tuner.start_tuning_session(
            objective=self.config.tuning_objective
        )
        return await self.auto_tuner.run_optimization()
    
    def _calculate_performance_score(self, report: PerformanceReport) -> float:
        """Calculate overall performance score from performance report."""
        # Map performance levels to scores
        level_scores = {
            'excellent': 1.0,
            'good': 0.8,
            'degraded': 0.6,
            'critical': 0.3
        }
        
        base_score = level_scores.get(report.overall_level.value, 0.5)
        
        # Adjust based on specific metrics
        latency_factor = max(0.5, 1.0 - (report.average_latency - 0.1) / 0.5)
        memory_factor = max(0.5, 1.0 - (report.peak_memory_usage - 50) / 50)
        cache_factor = report.cache_efficiency
        error_factor = max(0.0, 1.0 - report.error_rate * 10)
        
        return base_score * (latency_factor + memory_factor + cache_factor + error_factor) / 4
    
    async def _record_baseline_performance(self) -> None:
        """Record baseline performance metrics."""
        # Wait a moment for components to initialize
        await asyncio.sleep(1.0)
        
        await self._update_performance_metrics()
        self.performance_baseline = self.current_performance.copy()
        
        self.logger.info("Recorded baseline performance")
    
    async def _handle_performance_alert(self, alert: PerformanceAlert) -> None:
        """Handle performance alerts from the monitor."""
        self.logger.warning(f"Performance alert received: {alert.message}")
        
        # Trigger immediate optimization for critical alerts
        if alert.severity.value == 'critical':
            self.optimization_triggers['performance_degradation'] = True
    
    async def _handle_audio_environment_change(self, old_env: AudioEnvironment, new_env: AudioEnvironment) -> None:
        """Handle audio environment changes."""
        self.logger.info(f"Audio environment changed: {old_env.value} -> {new_env.value}")
        self.optimization_triggers['audio_environment_change'] = True
    
    def get_optimization_status(self) -> OptimizationStatus:
        """Get current optimization status."""
        active_optimizations = []
        
        if self.cache_optimizer:
            active_optimizations.append("intelligent_caching")
        
        if self.performance_monitor and self.performance_monitor.is_monitoring:
            active_optimizations.append("performance_monitoring")
        
        if self.audio_processor:
            active_optimizations.append("audio_adaptation")
        
        if self.auto_tuner and self.auto_tuner.is_tuning:
            active_optimizations.append("parameter_tuning")
        
        # Calculate overall performance score
        overall_score = 0.8  # Default
        if self.current_performance:
            # Use composite scoring based on available metrics
            scores = []
            
            if 'cache_hit_rate' in self.current_performance:
                scores.append(self.current_performance['cache_hit_rate'])
            
            if 'audio_performance_score' in self.current_performance:
                scores.append(self.current_performance['audio_performance_score'])
            
            if scores:
                overall_score = sum(scores) / len(scores)
        
        # Generate recommendations
        recommendations = self._generate_optimization_recommendations()
        
        return OptimizationStatus(
            is_active=self.is_active,
            cache_optimization=self.cache_optimizer is not None,
            performance_monitoring=self.performance_monitor is not None and self.performance_monitor.is_monitoring,
            audio_adaptation=self.audio_processor is not None,
            parameter_tuning=self.auto_tuner is not None and self.auto_tuner.is_tuning,
            overall_performance_score=overall_score,
            active_optimizations=active_optimizations,
            recommendations=recommendations
        )
    
    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on current state."""
        recommendations = []
        
        # Cache recommendations
        if self.cache_optimizer:
            cache_metrics = self.cache_optimizer.get_cache_metrics()
            if cache_metrics.hit_rate < 0.7:
                recommendations.append("Consider increasing cache size or improving prediction algorithms")
        
        # Performance recommendations
        if 'average_latency' in self.current_performance:
            if self.current_performance['average_latency'] > 0.5:
                recommendations.append("High latency detected - consider parameter optimization")
        
        # Memory recommendations
        if 'peak_memory_usage' in self.current_performance:
            if self.current_performance['peak_memory_usage'] > 80:
                recommendations.append("High memory usage - consider reducing cache size or model complexity")
        
        # Audio recommendations
        if 'audio_false_positive_rate' in self.current_performance:
            if self.current_performance['audio_false_positive_rate'] > 0.1:
                recommendations.append("High false positive rate - audio threshold adaptation may help")
        
        return recommendations
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        summary = {
            'orchestrator_status': self.get_optimization_status(),
            'current_performance': self.current_performance.copy(),
            'baseline_performance': self.performance_baseline.copy() if self.performance_baseline else {},
            'optimization_history_count': len(self.optimization_history)
        }
        
        # Add component-specific summaries
        if self.cache_optimizer:
            summary['cache_metrics'] = self.cache_optimizer.get_cache_metrics()
        
        if self.performance_monitor:
            summary['performance_report'] = self.performance_monitor.get_performance_report()
        
        if self.audio_processor:
            summary['audio_status'] = self.audio_processor.get_environment_status()
        
        if self.auto_tuner:
            summary['tuning_summary'] = self.auto_tuner.get_performance_summary()
        
        return summary
    
    async def manual_optimization_trigger(self, optimization_type: str) -> bool:
        """Manually trigger specific optimization."""
        if optimization_type == 'cache':
            self.optimization_triggers['cache_efficiency_low'] = True
        elif optimization_type == 'performance':
            self.optimization_triggers['performance_degradation'] = True
        elif optimization_type == 'audio':
            self.optimization_triggers['audio_environment_change'] = True
        elif optimization_type == 'parameters':
            self.optimization_triggers['parameter_optimization_due'] = True
        elif optimization_type == 'full':
            # Trigger all optimizations
            for key in self.optimization_triggers:
                self.optimization_triggers[key] = True
        else:
            return False
        
        self.logger.info(f"Manually triggered {optimization_type} optimization")
        return True
    
    def update_config(self, new_config: OptimizationConfig) -> None:
        """Update optimization configuration."""
        old_config = self.config
        self.config = new_config
        
        # Update component configurations
        if self.audio_processor and old_config.audio_adaptation_mode != new_config.audio_adaptation_mode:
            self.audio_processor.set_adaptation_mode(new_config.audio_adaptation_mode)
        
        if self.auto_tuner and old_config.tuning_objective != new_config.tuning_objective:
            self.auto_tuner.set_optimization_objective(new_config.tuning_objective)
        
        self.logger.info("Updated optimization configuration")