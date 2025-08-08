"""
AI-Powered Performance Monitor with Real-time Anomaly Detection.

This module provides intelligent performance monitoring that uses machine learning
to detect performance anomalies, predict system health, and trigger optimization actions.
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler


class PerformanceLevel(Enum):
    """Performance level classification."""
    EXCELLENT = "excellent"
    GOOD = "good"
    DEGRADED = "degraded"
    CRITICAL = "critical"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """Individual performance metric."""
    name: str
    value: float
    timestamp: float
    unit: str = ""
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceSnapshot:
    """Complete performance snapshot at a point in time."""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    inference_latency: float
    model_load_time: float
    cache_hit_rate: float
    audio_processing_time: float
    queue_depth: int
    error_rate: float
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceAlert:
    """Performance alert notification."""
    severity: AlertSeverity
    message: str
    timestamp: float
    metric_name: str
    current_value: float
    expected_range: Tuple[float, float]
    anomaly_score: float
    suggested_actions: List[str] = field(default_factory=list)


@dataclass
class PerformanceReport:
    """Comprehensive performance report."""
    period_start: float
    period_end: float
    overall_level: PerformanceLevel
    total_snapshots: int
    anomalies_detected: int
    average_latency: float
    peak_memory_usage: float
    cache_efficiency: float
    error_rate: float
    alerts: List[PerformanceAlert] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class AIPerformanceMonitor:
    """
    AI-powered performance monitoring with ML-based anomaly detection.
    
    Features:
    - Real-time performance metric collection
    - Machine learning anomaly detection
    - Predictive performance analysis
    - Automated alert generation
    - Performance trend analysis
    - Optimization recommendations
    """
    
    def __init__(
        self,
        collection_interval: float = 1.0,
        history_window: int = 1000,
        anomaly_threshold: float = 0.1,
        alert_callbacks: Optional[List[Callable]] = None
    ):
        self.collection_interval = collection_interval
        self.history_window = history_window
        self.anomaly_threshold = anomaly_threshold
        self.alert_callbacks = alert_callbacks or []
        
        # Data storage
        self.performance_history: deque = deque(maxlen=history_window)
        self.metric_streams: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.anomaly_history: List[PerformanceAlert] = []
        
        # ML components
        self.anomaly_detector: Optional[IsolationForest] = None
        self.metric_scaler = RobustScaler()
        self.is_trained = False
        self.training_data: List[List[float]] = []
        
        # Baseline metrics
        self.baseline_metrics: Dict[str, Dict[str, float]] = {}
        self.performance_trends: Dict[str, List[float]] = defaultdict(list)
        
        # Monitoring state
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.last_alert_times: Dict[str, float] = {}
        self.alert_cooldown = 60.0  # seconds
        
        # Performance thresholds
        self.thresholds = {
            'cpu_usage': {'warning': 70.0, 'critical': 90.0},
            'memory_usage': {'warning': 75.0, 'critical': 95.0},
            'inference_latency': {'warning': 0.5, 'critical': 1.0},
            'model_load_time': {'warning': 5.0, 'critical': 10.0},
            'cache_hit_rate': {'warning': 0.7, 'critical': 0.5},
            'error_rate': {'warning': 0.05, 'critical': 0.1},
            'queue_depth': {'warning': 50, 'critical': 100}
        }
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialized AIPerformanceMonitor")
    
    async def start_monitoring(self) -> None:
        """Start real-time performance monitoring."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Started performance monitoring")
    
    async def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Stopped performance monitoring")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop that collects and analyzes performance data."""
        while self.is_monitoring:
            try:
                # Collect current performance snapshot
                snapshot = await self._collect_performance_snapshot()
                self.performance_history.append(snapshot)
                
                # Update metric streams
                self._update_metric_streams(snapshot)
                
                # Analyze for anomalies
                await self._analyze_anomalies(snapshot)
                
                # Update baselines and trends
                self._update_baselines(snapshot)
                
                # Check thresholds and generate alerts
                await self._check_thresholds(snapshot)
                
                # Retrain anomaly detector periodically
                if len(self.performance_history) % 100 == 0:
                    await self._retrain_anomaly_detector()
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
            
            await asyncio.sleep(self.collection_interval)
    
    async def _collect_performance_snapshot(self) -> PerformanceSnapshot:
        """Collect current performance metrics."""
        import psutil
        
        # System metrics
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # Application-specific metrics (these would be provided by the app)
        inference_latency = self._get_current_inference_latency()
        model_load_time = self._get_current_model_load_time()
        cache_hit_rate = self._get_current_cache_hit_rate()
        audio_processing_time = self._get_current_audio_processing_time()
        queue_depth = self._get_current_queue_depth()
        error_rate = self._get_current_error_rate()
        
        return PerformanceSnapshot(
            timestamp=time.time(),
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            inference_latency=inference_latency,
            model_load_time=model_load_time,
            cache_hit_rate=cache_hit_rate,
            audio_processing_time=audio_processing_time,
            queue_depth=queue_depth,
            error_rate=error_rate,
            context=self._get_performance_context()
        )
    
    def _get_current_inference_latency(self) -> float:
        """Get current inference latency (would be provided by model manager)."""
        # Placeholder - would be connected to actual metrics
        return 0.1  # 100ms baseline
    
    def _get_current_model_load_time(self) -> float:
        """Get current model load time (would be provided by model manager)."""
        # Placeholder - would be connected to actual metrics
        return 2.0  # 2s baseline
    
    def _get_current_cache_hit_rate(self) -> float:
        """Get current cache hit rate (would be provided by cache)."""
        # Placeholder - would be connected to actual metrics
        return 0.8  # 80% baseline
    
    def _get_current_audio_processing_time(self) -> float:
        """Get current audio processing time (would be provided by audio system)."""
        # Placeholder - would be connected to actual metrics
        return 0.05  # 50ms baseline
    
    def _get_current_queue_depth(self) -> int:
        """Get current processing queue depth."""
        # Placeholder - would be connected to actual metrics
        return 5  # 5 items baseline
    
    def _get_current_error_rate(self) -> float:
        """Get current error rate."""
        # Placeholder - would be connected to actual metrics
        return 0.01  # 1% baseline
    
    def _get_performance_context(self) -> Dict[str, Any]:
        """Get additional performance context."""
        return {
            'active_models': 3,
            'current_state': 'idle',
            'concurrent_users': 1,
            'time_of_day': time.strftime('%H:%M:%S')
        }
    
    def _update_metric_streams(self, snapshot: PerformanceSnapshot) -> None:
        """Update individual metric streams for trend analysis."""
        metrics = {
            'cpu_usage': snapshot.cpu_usage,
            'memory_usage': snapshot.memory_usage,
            'inference_latency': snapshot.inference_latency,
            'model_load_time': snapshot.model_load_time,
            'cache_hit_rate': snapshot.cache_hit_rate,
            'audio_processing_time': snapshot.audio_processing_time,
            'queue_depth': float(snapshot.queue_depth),
            'error_rate': snapshot.error_rate
        }
        
        for metric_name, value in metrics.items():
            self.metric_streams[metric_name].append(
                PerformanceMetric(
                    name=metric_name,
                    value=value,
                    timestamp=snapshot.timestamp
                )
            )
    
    async def _analyze_anomalies(self, snapshot: PerformanceSnapshot) -> None:
        """Analyze snapshot for anomalies using ML."""
        if not self.is_trained or self.anomaly_detector is None:
            return
        
        try:
            # Extract features for anomaly detection
            features = self._extract_anomaly_features(snapshot)
            features_scaled = self.metric_scaler.transform([features])
            
            # Detect anomalies
            anomaly_score = self.anomaly_detector.decision_function(features_scaled)[0]
            is_anomaly = self.anomaly_detector.predict(features_scaled)[0] == -1
            
            if is_anomaly and abs(anomaly_score) > self.anomaly_threshold:
                await self._handle_anomaly_detection(snapshot, anomaly_score)
                
        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {e}")
    
    def _extract_anomaly_features(self, snapshot: PerformanceSnapshot) -> List[float]:
        """Extract features for anomaly detection."""
        return [
            snapshot.cpu_usage,
            snapshot.memory_usage,
            snapshot.inference_latency * 1000,  # Convert to ms
            snapshot.model_load_time,
            snapshot.cache_hit_rate,
            snapshot.audio_processing_time * 1000,  # Convert to ms
            float(snapshot.queue_depth),
            snapshot.error_rate * 100  # Convert to percentage
        ]
    
    async def _handle_anomaly_detection(
        self,
        snapshot: PerformanceSnapshot,
        anomaly_score: float
    ) -> None:
        """Handle detected performance anomaly."""
        # Determine most problematic metric
        problematic_metric = self._identify_problematic_metric(snapshot)
        
        # Create alert
        alert = PerformanceAlert(
            severity=AlertSeverity.WARNING if abs(anomaly_score) < 0.5 else AlertSeverity.CRITICAL,
            message=f"Performance anomaly detected in {problematic_metric}",
            timestamp=snapshot.timestamp,
            metric_name=problematic_metric,
            current_value=getattr(snapshot, problematic_metric),
            expected_range=self._get_expected_range(problematic_metric),
            anomaly_score=anomaly_score,
            suggested_actions=self._get_anomaly_suggestions(problematic_metric, snapshot)
        )
        
        await self._emit_alert(alert)
    
    def _identify_problematic_metric(self, snapshot: PerformanceSnapshot) -> str:
        """Identify which metric is most likely causing the anomaly."""
        metric_scores = {}
        
        for metric_name in ['cpu_usage', 'memory_usage', 'inference_latency', 'error_rate']:
            current_value = getattr(snapshot, metric_name)
            baseline = self.baseline_metrics.get(metric_name, {}).get('mean', 0)
            
            if baseline > 0:
                deviation = abs(current_value - baseline) / baseline
                metric_scores[metric_name] = deviation
        
        return max(metric_scores.keys(), key=lambda x: metric_scores[x]) if metric_scores else 'cpu_usage'
    
    def _get_expected_range(self, metric_name: str) -> Tuple[float, float]:
        """Get expected range for a metric based on historical data."""
        baseline = self.baseline_metrics.get(metric_name, {})
        mean = baseline.get('mean', 0)
        std = baseline.get('std', 0)
        
        return (max(0, mean - 2 * std), mean + 2 * std)
    
    def _get_anomaly_suggestions(self, metric_name: str, snapshot: PerformanceSnapshot) -> List[str]:
        """Get suggestions for handling specific anomalies."""
        suggestions = {
            'cpu_usage': [
                "Reduce model complexity or batch size",
                "Optimize inference algorithms",
                "Consider model quantization"
            ],
            'memory_usage': [
                "Clear model cache",
                "Reduce cache size limits",
                "Implement more aggressive garbage collection"
            ],
            'inference_latency': [
                "Check model optimization",
                "Verify hardware acceleration",
                "Review model cache efficiency"
            ],
            'error_rate': [
                "Check model integrity",
                "Verify input data quality", 
                "Review error logs for patterns"
            ]
        }
        
        return suggestions.get(metric_name, ["Monitor system closely", "Check logs for details"])
    
    async def _check_thresholds(self, snapshot: PerformanceSnapshot) -> None:
        """Check performance thresholds and generate alerts."""
        metrics_to_check = {
            'cpu_usage': snapshot.cpu_usage,
            'memory_usage': snapshot.memory_usage,
            'inference_latency': snapshot.inference_latency,
            'model_load_time': snapshot.model_load_time,
            'cache_hit_rate': snapshot.cache_hit_rate,
            'error_rate': snapshot.error_rate,
            'queue_depth': float(snapshot.queue_depth)
        }
        
        for metric_name, current_value in metrics_to_check.items():
            await self._check_metric_threshold(metric_name, current_value, snapshot.timestamp)
    
    async def _check_metric_threshold(
        self,
        metric_name: str,
        current_value: float,
        timestamp: float
    ) -> None:
        """Check if a specific metric exceeds thresholds."""
        thresholds = self.thresholds.get(metric_name, {})
        
        # Check for alert cooldown
        last_alert = self.last_alert_times.get(metric_name, 0)
        if timestamp - last_alert < self.alert_cooldown:
            return
        
        severity = None
        if current_value > thresholds.get('critical', float('inf')):
            severity = AlertSeverity.CRITICAL
        elif current_value > thresholds.get('warning', float('inf')):
            severity = AlertSeverity.WARNING
        
        # Special handling for metrics where lower is worse
        if metric_name == 'cache_hit_rate':
            if current_value < thresholds.get('critical', 0):
                severity = AlertSeverity.CRITICAL
            elif current_value < thresholds.get('warning', 0):
                severity = AlertSeverity.WARNING
        
        if severity:
            alert = PerformanceAlert(
                severity=severity,
                message=f"{metric_name} threshold exceeded: {current_value:.2f}",
                timestamp=timestamp,
                metric_name=metric_name,
                current_value=current_value,
                expected_range=(0, thresholds.get('warning', 0)),
                anomaly_score=0.0,
                suggested_actions=self._get_threshold_suggestions(metric_name, severity)
            )
            
            await self._emit_alert(alert)
            self.last_alert_times[metric_name] = timestamp
    
    def _get_threshold_suggestions(self, metric_name: str, severity: AlertSeverity) -> List[str]:
        """Get suggestions for threshold violations."""
        base_suggestions = {
            'cpu_usage': ["Scale down operations", "Optimize algorithms"],
            'memory_usage': ["Clear caches", "Restart service if critical"],
            'inference_latency': ["Check model optimization", "Verify hardware"],
            'error_rate': ["Check system health", "Review recent changes"]
        }
        
        suggestions = base_suggestions.get(metric_name, ["Monitor closely"])
        
        if severity == AlertSeverity.CRITICAL:
            suggestions.append("Consider immediate intervention")
        
        return suggestions
    
    async def _emit_alert(self, alert: PerformanceAlert) -> None:
        """Emit performance alert to registered callbacks."""
        self.anomaly_history.append(alert)
        
        # Call registered alert callbacks
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback failed: {e}")
        
        self.logger.warning(f"Performance Alert [{alert.severity.value}]: {alert.message}")
    
    def _update_baselines(self, snapshot: PerformanceSnapshot) -> None:
        """Update baseline performance metrics."""
        metrics = {
            'cpu_usage': snapshot.cpu_usage,
            'memory_usage': snapshot.memory_usage,
            'inference_latency': snapshot.inference_latency,
            'model_load_time': snapshot.model_load_time,
            'cache_hit_rate': snapshot.cache_hit_rate,
            'audio_processing_time': snapshot.audio_processing_time,
            'error_rate': snapshot.error_rate
        }
        
        for metric_name, value in metrics.items():
            if metric_name not in self.baseline_metrics:
                self.baseline_metrics[metric_name] = {'values': [], 'mean': 0, 'std': 0}
            
            baseline = self.baseline_metrics[metric_name]
            baseline['values'].append(value)
            
            # Keep only recent values for baseline
            if len(baseline['values']) > 200:
                baseline['values'] = baseline['values'][-200:]
            
            # Update statistics
            values = baseline['values']
            baseline['mean'] = np.mean(values)
            baseline['std'] = np.std(values)
            
            # Update trends
            self.performance_trends[metric_name].append(value)
            if len(self.performance_trends[metric_name]) > 100:
                self.performance_trends[metric_name] = self.performance_trends[metric_name][-100:]
    
    async def _retrain_anomaly_detector(self) -> None:
        """Retrain the anomaly detection model."""
        if len(self.performance_history) < 50:
            return
        
        self.logger.info("Retraining anomaly detector...")
        
        try:
            # Prepare training data
            training_data = []
            for snapshot in list(self.performance_history)[-200:]:  # Use recent data
                features = self._extract_anomaly_features(snapshot)
                training_data.append(features)
            
            if len(training_data) == 0:
                return
            
            # Scale features
            self.training_data = training_data
            training_data_scaled = self.metric_scaler.fit_transform(training_data)
            
            # Train anomaly detector
            self.anomaly_detector = IsolationForest(
                contamination=0.1,  # Expect 10% anomalies
                random_state=42,
                n_estimators=100
            )
            self.anomaly_detector.fit(training_data_scaled)
            self.is_trained = True
            
            self.logger.info("Anomaly detector retrained successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to retrain anomaly detector: {e}")
    
    def get_performance_report(self, period_hours: float = 1.0) -> PerformanceReport:
        """Generate comprehensive performance report."""
        period_start = time.time() - (period_hours * 3600)
        period_end = time.time()
        
        # Filter snapshots to period
        period_snapshots = [
            s for s in self.performance_history
            if period_start <= s.timestamp <= period_end
        ]
        
        if not period_snapshots:
            return PerformanceReport(
                period_start=period_start,
                period_end=period_end,
                overall_level=PerformanceLevel.GOOD,
                total_snapshots=0,
                anomalies_detected=0,
                average_latency=0.0,
                peak_memory_usage=0.0,
                cache_efficiency=0.0,
                error_rate=0.0
            )
        
        # Calculate aggregate metrics
        latencies = [s.inference_latency for s in period_snapshots]
        memory_usages = [s.memory_usage for s in period_snapshots]
        cache_rates = [s.cache_hit_rate for s in period_snapshots]
        error_rates = [s.error_rate for s in period_snapshots]
        
        avg_latency = np.mean(latencies)
        peak_memory = max(memory_usages)
        cache_efficiency = np.mean(cache_rates)
        avg_error_rate = np.mean(error_rates)
        
        # Count period anomalies
        period_alerts = [
            a for a in self.anomaly_history
            if period_start <= a.timestamp <= period_end
        ]
        
        # Determine overall performance level
        overall_level = self._calculate_overall_performance_level(
            avg_latency, peak_memory, cache_efficiency, avg_error_rate
        )
        
        # Generate recommendations
        recommendations = self._generate_performance_recommendations(period_snapshots)
        
        return PerformanceReport(
            period_start=period_start,
            period_end=period_end,
            overall_level=overall_level,
            total_snapshots=len(period_snapshots),
            anomalies_detected=len(period_alerts),
            average_latency=avg_latency,
            peak_memory_usage=peak_memory,
            cache_efficiency=cache_efficiency,
            error_rate=avg_error_rate,
            alerts=period_alerts,
            recommendations=recommendations
        )
    
    def _calculate_overall_performance_level(
        self,
        avg_latency: float,
        peak_memory: float,
        cache_efficiency: float,
        error_rate: float
    ) -> PerformanceLevel:
        """Calculate overall performance level from metrics."""
        score = 100.0
        
        # Latency impact
        if avg_latency > 1.0:
            score -= 30
        elif avg_latency > 0.5:
            score -= 15
        
        # Memory impact
        if peak_memory > 90:
            score -= 25
        elif peak_memory > 75:
            score -= 10
        
        # Cache efficiency impact
        if cache_efficiency < 0.5:
            score -= 20
        elif cache_efficiency < 0.7:
            score -= 10
        
        # Error rate impact
        if error_rate > 0.1:
            score -= 25
        elif error_rate > 0.05:
            score -= 10
        
        if score >= 85:
            return PerformanceLevel.EXCELLENT
        elif score >= 70:
            return PerformanceLevel.GOOD
        elif score >= 50:
            return PerformanceLevel.DEGRADED
        else:
            return PerformanceLevel.CRITICAL
    
    def _generate_performance_recommendations(self, snapshots: List[PerformanceSnapshot]) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        if not snapshots:
            return recommendations
        
        # Analyze trends
        avg_cpu = np.mean([s.cpu_usage for s in snapshots])
        avg_memory = np.mean([s.memory_usage for s in snapshots])
        avg_latency = np.mean([s.inference_latency for s in snapshots])
        avg_cache_rate = np.mean([s.cache_hit_rate for s in snapshots])
        
        if avg_cpu > 70:
            recommendations.append("Consider CPU optimization or scaling")
        
        if avg_memory > 75:
            recommendations.append("Implement more aggressive memory management")
        
        if avg_latency > 0.5:
            recommendations.append("Optimize model inference pipeline")
        
        if avg_cache_rate < 0.7:
            recommendations.append("Improve model caching strategy")
        
        return recommendations
    
    def add_alert_callback(self, callback: Callable) -> None:
        """Add callback for performance alerts."""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable) -> None:
        """Remove alert callback."""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    def get_metric_trend(self, metric_name: str, window: int = 50) -> List[float]:
        """Get recent trend for a specific metric."""
        trend = self.performance_trends.get(metric_name, [])
        return trend[-window:] if len(trend) >= window else trend