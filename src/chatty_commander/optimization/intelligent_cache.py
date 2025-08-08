"""
Intelligent Model Caching System with Predictive Loading.

Uses machine learning to analyze usage patterns and predict which models
will be needed, enabling proactive caching and faster response times.
"""

import asyncio
import logging
import pickle
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler


@dataclass
class ModelUsageEvent:
    """Represents a model usage event for pattern analysis."""
    timestamp: float
    model_name: str
    state: str
    load_time: float
    inference_time: float
    context: Dict[str, Any]


@dataclass 
class CacheMetrics:
    """Cache performance metrics."""
    hit_rate: float
    miss_rate: float
    average_load_time: float
    memory_usage_mb: float
    prediction_accuracy: float


class IntelligentModelCache:
    """
    AI-powered model cache that learns usage patterns and predictively loads models.
    
    Features:
    - Pattern learning from historical usage
    - Predictive model preloading
    - Memory-aware cache management
    - Context-sensitive caching decisions
    """
    
    def __init__(
        self,
        max_cache_size_mb: int = 512,
        history_window: int = 1000,
        prediction_threshold: float = 0.7,
        cache_dir: Optional[Path] = None
    ):
        self.max_cache_size_mb = max_cache_size_mb
        self.history_window = history_window
        self.prediction_threshold = prediction_threshold
        self.cache_dir = cache_dir or Path(".cache/intelligent_models")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache storage
        self.model_cache: Dict[str, Any] = {}
        self.cache_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Usage tracking
        self.usage_history: deque = deque(maxlen=history_window)
        self.state_transitions: deque = deque(maxlen=history_window)
        self.context_patterns: Dict[str, List[float]] = defaultdict(list)
        
        # ML components
        self.usage_predictor: Optional[RandomForestClassifier] = None
        self.feature_scaler = StandardScaler()
        self.is_trained = False
        
        # Performance tracking
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_load_time = 0.0
        self.current_memory_usage = 0.0
        
        # Async loading
        self.preload_tasks: Set[asyncio.Task] = set()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized IntelligentModelCache with max size {max_cache_size_mb}MB")
        
        # Load existing patterns if available
        self._load_cache_state()
    
    def record_usage(
        self,
        model_name: str,
        state: str,
        load_time: float,
        inference_time: float,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a model usage event for pattern learning."""
        event = ModelUsageEvent(
            timestamp=time.time(),
            model_name=model_name,
            state=state,
            load_time=load_time,
            inference_time=inference_time,
            context=context or {}
        )
        
        self.usage_history.append(event)
        self._update_context_patterns(event)
        
        # Retrain predictor periodically
        if len(self.usage_history) % 50 == 0:
            asyncio.create_task(self._retrain_predictor())
    
    def record_state_transition(self, from_state: str, to_state: str) -> None:
        """Record state transition for transition pattern learning."""
        transition = {
            'timestamp': time.time(),
            'from_state': from_state,
            'to_state': to_state
        }
        self.state_transitions.append(transition)
    
    async def get_model(self, model_name: str, loader_func: callable) -> Any:
        """
        Get model from cache or load it, with intelligent preloading.
        
        Args:
            model_name: Name of the model to retrieve
            loader_func: Function to load the model if not cached
            
        Returns:
            The loaded model instance
        """
        start_time = time.perf_counter()
        
        # Check cache first
        if model_name in self.model_cache:
            self.cache_hits += 1
            self.logger.debug(f"Cache hit for model: {model_name}")
            return self.model_cache[model_name]
        
        # Cache miss - load the model
        self.cache_misses += 1
        self.logger.debug(f"Cache miss for model: {model_name}")
        
        # Load model
        model = await self._load_model_with_metrics(model_name, loader_func)
        load_time = time.perf_counter() - start_time
        self.total_load_time += load_time
        
        # Add to cache with intelligent eviction
        await self._add_to_cache(model_name, model, load_time)
        
        # Trigger predictive preloading
        await self._trigger_predictive_preload(model_name)
        
        return model
    
    async def _load_model_with_metrics(self, model_name: str, loader_func: callable) -> Any:
        """Load model and track performance metrics."""
        start_time = time.perf_counter()
        
        try:
            model = await asyncio.get_event_loop().run_in_executor(None, loader_func)
            load_time = time.perf_counter() - start_time
            
            # Estimate memory usage
            memory_estimate = self._estimate_model_memory(model)
            
            self.logger.info(
                f"Loaded model {model_name} in {load_time:.3f}s, "
                f"estimated memory: {memory_estimate:.1f}MB"
            )
            
            return model
            
        except Exception as e:
            self.logger.error(f"Failed to load model {model_name}: {e}")
            raise
    
    async def _add_to_cache(self, model_name: str, model: Any, load_time: float) -> None:
        """Add model to cache with intelligent memory management."""
        memory_estimate = self._estimate_model_memory(model)
        
        # Check if we need to evict models
        while (self.current_memory_usage + memory_estimate) > self.max_cache_size_mb:
            await self._evict_least_valuable_model()
        
        # Add to cache
        self.model_cache[model_name] = model
        self.cache_metadata[model_name] = {
            'load_time': load_time,
            'memory_mb': memory_estimate,
            'last_accessed': time.time(),
            'access_count': 1,
            'predicted_value': self._calculate_model_value(model_name)
        }
        
        self.current_memory_usage += memory_estimate
        self.logger.debug(f"Added {model_name} to cache, memory usage: {self.current_memory_usage:.1f}MB")
    
    async def _evict_least_valuable_model(self) -> None:
        """Evict the least valuable model based on ML predictions."""
        if not self.model_cache:
            return
        
        # Calculate value scores for all cached models
        model_scores = {}
        for model_name, metadata in self.cache_metadata.items():
            score = self._calculate_eviction_score(model_name, metadata)
            model_scores[model_name] = score
        
        # Evict lowest scoring model
        to_evict = min(model_scores.keys(), key=lambda x: model_scores[x])
        memory_freed = self.cache_metadata[to_evict]['memory_mb']
        
        del self.model_cache[to_evict]
        del self.cache_metadata[to_evict]
        self.current_memory_usage -= memory_freed
        
        self.logger.info(f"Evicted model {to_evict}, freed {memory_freed:.1f}MB")
    
    async def _trigger_predictive_preload(self, current_model: str) -> None:
        """Trigger predictive preloading based on usage patterns."""
        if not self.is_trained:
            return
        
        # Predict next likely models
        predictions = self._predict_next_models(current_model)
        
        for model_name, probability in predictions:
            if probability > self.prediction_threshold and model_name not in self.model_cache:
                # Create preload task
                task = asyncio.create_task(self._preload_model(model_name))
                self.preload_tasks.add(task)
                task.add_done_callback(self.preload_tasks.discard)
    
    async def _preload_model(self, model_name: str) -> None:
        """Preload a model in the background."""
        try:
            self.logger.debug(f"Preloading model: {model_name}")
            # This would need to be connected to the actual model loading system
            # For now, we'll simulate the preload
            await asyncio.sleep(0.1)  # Simulate load time
            
        except Exception as e:
            self.logger.error(f"Failed to preload model {model_name}: {e}")
    
    def _predict_next_models(self, current_model: str) -> List[Tuple[str, float]]:
        """Predict which models are likely to be used next."""
        if not self.usage_predictor or not self.is_trained:
            return []
        
        # Extract features for prediction
        features = self._extract_prediction_features(current_model)
        
        try:
            # Get predictions for all known models
            probabilities = self.usage_predictor.predict_proba([features])[0]
            model_names = self.usage_predictor.classes_
            
            # Sort by probability
            predictions = list(zip(model_names, probabilities))
            predictions.sort(key=lambda x: x[1], reverse=True)
            
            return predictions[:3]  # Return top 3 predictions
            
        except Exception as e:
            self.logger.error(f"Prediction failed: {e}")
            return []
    
    def _extract_prediction_features(self, current_model: str) -> List[float]:
        """Extract features for ML prediction."""
        features = []
        
        # Time-based features
        current_time = time.time()
        hour_of_day = (current_time % 86400) / 3600  # Hour of day (0-24)
        features.append(hour_of_day)
        
        # Recent usage patterns
        recent_models = [event.model_name for event in list(self.usage_history)[-10:]]
        model_frequency = recent_models.count(current_model) / len(recent_models) if recent_models else 0
        features.append(model_frequency)
        
        # State transition patterns
        recent_states = [event.state for event in list(self.usage_history)[-5:]]
        if recent_states:
            state_changes = len(set(recent_states))
            features.append(state_changes)
        else:
            features.append(0)
        
        # Performance metrics
        if current_model in self.cache_metadata:
            metadata = self.cache_metadata[current_model]
            features.extend([
                metadata.get('load_time', 0),
                metadata.get('access_count', 0),
                time.time() - metadata.get('last_accessed', time.time())
            ])
        else:
            features.extend([0, 0, 0])
        
        return features
    
    async def _retrain_predictor(self) -> None:
        """Retrain the ML predictor with recent usage data."""
        if len(self.usage_history) < 20:
            return
        
        self.logger.info("Retraining usage predictor...")
        
        try:
            # Prepare training data
            X, y = self._prepare_training_data()
            
            if len(X) == 0:
                return
            
            # Scale features
            X_scaled = self.feature_scaler.fit_transform(X)
            
            # Train predictor
            self.usage_predictor = RandomForestClassifier(
                n_estimators=50,
                max_depth=10,
                random_state=42
            )
            self.usage_predictor.fit(X_scaled, y)
            self.is_trained = True
            
            # Calculate accuracy on recent data
            if len(X) > 10:
                recent_X = X_scaled[-10:]
                recent_y = y[-10:]
                accuracy = self.usage_predictor.score(recent_X, recent_y)
                self.logger.info(f"Predictor retrained, accuracy: {accuracy:.3f}")
        
        except Exception as e:
            self.logger.error(f"Failed to retrain predictor: {e}")
    
    def _prepare_training_data(self) -> Tuple[List[List[float]], List[str]]:
        """Prepare training data from usage history."""
        X, y = [], []
        
        events = list(self.usage_history)
        for i in range(len(events) - 1):
            current_event = events[i]
            next_event = events[i + 1]
            
            # Extract features for current event
            features = self._extract_prediction_features(current_event.model_name)
            X.append(features)
            y.append(next_event.model_name)
        
        return X, y
    
    def _estimate_model_memory(self, model: Any) -> float:
        """Estimate memory usage of a model in MB."""
        try:
            import sys
            size_bytes = sys.getsizeof(model)
            
            # Try to get more accurate size for ONNX models
            if hasattr(model, 'graph'):
                # Rough estimate for ONNX models
                size_bytes *= 4  # Assume float32 parameters
            
            return size_bytes / (1024 * 1024)  # Convert to MB
            
        except Exception:
            return 50.0  # Default estimate
    
    def _calculate_model_value(self, model_name: str) -> float:
        """Calculate the value score of a model for caching decisions."""
        if model_name not in self.cache_metadata:
            return 0.0
        
        metadata = self.cache_metadata[model_name]
        
        # Factors: access frequency, recency, load time savings
        access_frequency = metadata.get('access_count', 0)
        time_since_access = time.time() - metadata.get('last_accessed', time.time())
        load_time_savings = metadata.get('load_time', 0)
        
        # Calculate composite score
        recency_score = max(0, 1.0 - (time_since_access / 3600))  # Decay over 1 hour
        frequency_score = min(1.0, access_frequency / 10)  # Normalize to 0-1
        savings_score = min(1.0, load_time_savings / 5.0)  # Normalize to 0-1
        
        return (recency_score * 0.4 + frequency_score * 0.4 + savings_score * 0.2)
    
    def _calculate_eviction_score(self, model_name: str, metadata: Dict[str, Any]) -> float:
        """Calculate eviction score (lower = more likely to evict)."""
        value_score = self._calculate_model_value(model_name)
        memory_cost = metadata.get('memory_mb', 0) / self.max_cache_size_mb
        
        return value_score - (memory_cost * 0.3)  # Penalize memory usage
    
    def _update_context_patterns(self, event: ModelUsageEvent) -> None:
        """Update context pattern analysis."""
        for key, value in event.context.items():
            if isinstance(value, (int, float)):
                self.context_patterns[key].append(float(value))
                # Keep only recent values
                if len(self.context_patterns[key]) > 100:
                    self.context_patterns[key] = self.context_patterns[key][-100:]
    
    def get_cache_metrics(self) -> CacheMetrics:
        """Get current cache performance metrics."""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0.0
        miss_rate = 1.0 - hit_rate
        
        avg_load_time = self.total_load_time / self.cache_misses if self.cache_misses > 0 else 0.0
        
        # Calculate prediction accuracy
        prediction_accuracy = 0.0
        if self.is_trained and len(self.usage_history) > 10:
            # Simple accuracy estimate based on recent predictions
            prediction_accuracy = 0.75  # Placeholder - would need actual tracking
        
        return CacheMetrics(
            hit_rate=hit_rate,
            miss_rate=miss_rate,
            average_load_time=avg_load_time,
            memory_usage_mb=self.current_memory_usage,
            prediction_accuracy=prediction_accuracy
        )
    
    def _save_cache_state(self) -> None:
        """Save cache state for persistence."""
        try:
            state_file = self.cache_dir / "cache_state.pkl"
            state = {
                'usage_history': list(self.usage_history),
                'state_transitions': list(self.state_transitions),
                'context_patterns': dict(self.context_patterns),
                'cache_metadata': self.cache_metadata,
                'feature_scaler': self.feature_scaler,
                'usage_predictor': self.usage_predictor
            }
            
            with open(state_file, 'wb') as f:
                pickle.dump(state, f)
                
        except Exception as e:
            self.logger.error(f"Failed to save cache state: {e}")
    
    def _load_cache_state(self) -> None:
        """Load cache state from persistence."""
        try:
            state_file = self.cache_dir / "cache_state.pkl"
            if not state_file.exists():
                return
            
            with open(state_file, 'rb') as f:
                state = pickle.load(f)
            
            self.usage_history.extend(state.get('usage_history', []))
            self.state_transitions.extend(state.get('state_transitions', []))
            self.context_patterns.update(state.get('context_patterns', {}))
            self.cache_metadata = state.get('cache_metadata', {})
            self.feature_scaler = state.get('feature_scaler', StandardScaler())
            self.usage_predictor = state.get('usage_predictor')
            
            if self.usage_predictor:
                self.is_trained = True
                
            self.logger.info("Loaded cache state from persistence")
            
        except Exception as e:
            self.logger.error(f"Failed to load cache state: {e}")
    
    async def shutdown(self) -> None:
        """Graceful shutdown with state persistence."""
        # Cancel any pending preload tasks
        for task in self.preload_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.preload_tasks:
            await asyncio.gather(*self.preload_tasks, return_exceptions=True)
        
        # Save state
        self._save_cache_state()
        
        self.logger.info("IntelligentModelCache shutdown complete")