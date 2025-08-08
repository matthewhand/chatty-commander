"""
Performance Auto-Tuner with ML-Based Parameter Optimization.

This module provides intelligent parameter tuning that uses machine learning
to optimize inference parameters based on performance feedback and system conditions.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
from sklearn.preprocessing import StandardScaler


class OptimizationObjective(Enum):
    """Optimization objectives."""
    LATENCY = "latency"
    ACCURACY = "accuracy"
    BALANCED = "balanced"
    MEMORY = "memory"
    THROUGHPUT = "throughput"


class ParameterType(Enum):
    """Parameter types for optimization."""
    CONTINUOUS = "continuous"
    DISCRETE = "discrete"
    CATEGORICAL = "categorical"


@dataclass
class ParameterSpace:
    """Defines the search space for a parameter."""
    name: str
    param_type: ParameterType
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    discrete_values: Optional[List[Any]] = None
    current_value: Any = None


@dataclass
class OptimizationResult:
    """Result of parameter optimization."""
    parameters: Dict[str, Any]
    performance_score: float
    latency: float
    accuracy: float
    memory_usage: float
    throughput: float
    improvement_over_baseline: float


@dataclass
class TuningSession:
    """Represents a complete tuning session."""
    session_id: str
    start_time: float
    end_time: Optional[float]
    objective: OptimizationObjective
    parameter_spaces: List[ParameterSpace]
    evaluations: List[Dict[str, Any]] = field(default_factory=list)
    best_result: Optional[OptimizationResult] = None
    convergence_history: List[float] = field(default_factory=list)


class PerformanceAutoTuner:
    """
    Intelligent parameter auto-tuner using Bayesian optimization.
    
    Features:
    - Bayesian optimization for parameter search
    - Multi-objective optimization
    - Adaptive search space exploration
    - Performance-driven parameter adjustment
    - Historical data learning
    - Context-aware optimization
    """
    
    def __init__(
        self,
        optimization_objective: OptimizationObjective = OptimizationObjective.BALANCED,
        max_evaluations: int = 50,
        convergence_threshold: float = 0.01,
        exploration_factor: float = 0.1
    ):
        self.optimization_objective = optimization_objective
        self.max_evaluations = max_evaluations
        self.convergence_threshold = convergence_threshold
        self.exploration_factor = exploration_factor
        
        # Parameter spaces
        self.parameter_spaces: Dict[str, ParameterSpace] = {}
        self._initialize_parameter_spaces()
        
        # Optimization state
        self.current_session: Optional[TuningSession] = None
        self.is_tuning = False
        self.baseline_performance: Optional[Dict[str, float]] = None
        
        # ML components
        self.surrogate_model: Optional[GaussianProcessRegressor] = None
        self.parameter_scaler = StandardScaler()
        self.performance_scaler = StandardScaler()
        self.is_trained = False
        
        # Historical data
        self.evaluation_history: List[Dict[str, Any]] = []
        self.best_known_parameters: Dict[str, Any] = {}
        self.performance_history: List[float] = []
        
        # Adaptive parameters
        self.acquisition_function = "expected_improvement"
        self.kernel = C(1.0, (1e-3, 1e3)) * RBF(1.0, (1e-2, 1e2))
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized PerformanceAutoTuner with {optimization_objective.value} objective")
    
    def _initialize_parameter_spaces(self) -> None:
        """Initialize parameter search spaces for optimization."""
        # Model inference parameters
        self.parameter_spaces = {
            'batch_size': ParameterSpace(
                name='batch_size',
                param_type=ParameterType.DISCRETE,
                discrete_values=[1, 2, 4, 8, 16, 32],
                current_value=1
            ),
            'inference_timeout': ParameterSpace(
                name='inference_timeout',
                param_type=ParameterType.CONTINUOUS,
                min_value=0.1,
                max_value=5.0,
                current_value=1.0
            ),
            'model_precision': ParameterSpace(
                name='model_precision',
                param_type=ParameterType.CATEGORICAL,
                discrete_values=['float32', 'float16', 'int8'],
                current_value='float32'
            ),
            'cache_size_mb': ParameterSpace(
                name='cache_size_mb',
                param_type=ParameterType.CONTINUOUS,
                min_value=64,
                max_value=2048,
                current_value=512
            ),
            'preload_threshold': ParameterSpace(
                name='preload_threshold',
                param_type=ParameterType.CONTINUOUS,
                min_value=0.1,
                max_value=0.9,
                current_value=0.7
            ),
            'gc_frequency': ParameterSpace(
                name='gc_frequency',
                param_type=ParameterType.DISCRETE,
                discrete_values=[10, 25, 50, 100, 200],
                current_value=100
            ),
            'worker_threads': ParameterSpace(
                name='worker_threads',
                param_type=ParameterType.DISCRETE,
                discrete_values=[1, 2, 4, 8],
                current_value=2
            ),
            'audio_chunk_size': ParameterSpace(
                name='audio_chunk_size',
                param_type=ParameterType.DISCRETE,
                discrete_values=[512, 1024, 2048, 4096],
                current_value=1024
            )
        }
    
    async def start_tuning_session(
        self,
        objective: Optional[OptimizationObjective] = None,
        parameter_subset: Optional[List[str]] = None
    ) -> str:
        """Start a new parameter tuning session."""
        if self.is_tuning:
            raise RuntimeError("Tuning session already in progress")
        
        objective = objective or self.optimization_objective
        session_id = f"tune_{int(time.time())}"
        
        # Select parameter spaces
        if parameter_subset:
            spaces = [self.parameter_spaces[name] for name in parameter_subset 
                     if name in self.parameter_spaces]
        else:
            spaces = list(self.parameter_spaces.values())
        
        self.current_session = TuningSession(
            session_id=session_id,
            start_time=time.time(),
            end_time=None,
            objective=objective,
            parameter_spaces=spaces
        )
        
        self.is_tuning = True
        
        # Initialize surrogate model
        self._initialize_surrogate_model()
        
        # Record baseline performance
        await self._record_baseline_performance()
        
        self.logger.info(f"Started tuning session {session_id} with {len(spaces)} parameters")
        return session_id
    
    async def _record_baseline_performance(self) -> None:
        """Record baseline performance with current parameters."""
        # Get current parameter values
        current_params = {
            name: space.current_value 
            for name, space in self.parameter_spaces.items()
        }
        
        # Evaluate current performance
        performance = await self._evaluate_performance(current_params)
        self.baseline_performance = performance
        
        self.logger.info(f"Baseline performance recorded: {performance}")
    
    async def run_optimization(self) -> OptimizationResult:
        """Run the optimization process."""
        if not self.current_session:
            raise RuntimeError("No active tuning session")
        
        session = self.current_session
        best_score = float('-inf')
        convergence_count = 0
        
        for iteration in range(self.max_evaluations):
            # Generate candidate parameters
            candidate_params = await self._generate_candidate_parameters()
            
            # Evaluate performance
            performance = await self._evaluate_performance(candidate_params)
            score = self._calculate_objective_score(performance)
            
            # Record evaluation
            evaluation = {
                'iteration': iteration,
                'parameters': candidate_params.copy(),
                'performance': performance.copy(),
                'score': score,
                'timestamp': time.time()
            }
            session.evaluations.append(evaluation)
            self.evaluation_history.append(evaluation)
            
            # Update best result
            if score > best_score:
                best_score = score
                convergence_count = 0
                
                improvement = self._calculate_improvement(performance)
                session.best_result = OptimizationResult(
                    parameters=candidate_params.copy(),
                    performance_score=score,
                    latency=performance['latency'],
                    accuracy=performance['accuracy'],
                    memory_usage=performance['memory_usage'],
                    throughput=performance['throughput'],
                    improvement_over_baseline=improvement
                )
                
                # Update current parameter values
                await self._apply_parameters(candidate_params)
            else:
                convergence_count += 1
            
            # Update surrogate model
            self._update_surrogate_model(session.evaluations)
            
            # Record convergence
            session.convergence_history.append(best_score)
            
            # Check convergence
            if self._check_convergence(session.convergence_history) or convergence_count >= 10:
                self.logger.info(f"Optimization converged at iteration {iteration}")
                break
            
            await asyncio.sleep(0.1)  # Prevent blocking
        
        session.end_time = time.time()
        self.is_tuning = False
        
        self.logger.info(f"Optimization completed. Best score: {best_score:.4f}")
        return session.best_result
    
    async def _generate_candidate_parameters(self) -> Dict[str, Any]:
        """Generate candidate parameters using acquisition function."""
        if not self.current_session:
            raise RuntimeError("No active session")
        
        session = self.current_session
        
        if len(session.evaluations) < 3:
            # Random exploration for initial evaluations
            return self._generate_random_parameters(session.parameter_spaces)
        
        # Use surrogate model for informed search
        return await self._bayesian_optimization_step(session.parameter_spaces)
    
    def _generate_random_parameters(self, spaces: List[ParameterSpace]) -> Dict[str, Any]:
        """Generate random parameters within the search space."""
        params = {}
        
        for space in spaces:
            if space.param_type == ParameterType.CONTINUOUS:
                value = np.random.uniform(space.min_value, space.max_value)
            elif space.param_type in [ParameterType.DISCRETE, ParameterType.CATEGORICAL]:
                value = np.random.choice(space.discrete_values)
            else:
                value = space.current_value
            
            params[space.name] = value
        
        return params
    
    async def _bayesian_optimization_step(self, spaces: List[ParameterSpace]) -> Dict[str, Any]:
        """Perform Bayesian optimization step to find next candidate."""
        if not self.surrogate_model or not self.is_trained:
            return self._generate_random_parameters(spaces)
        
        # Generate candidate points
        n_candidates = 1000
        candidates = []
        
        for _ in range(n_candidates):
            candidate = self._generate_random_parameters(spaces)
            candidates.append(candidate)
        
        # Convert to feature vectors
        candidate_features = [self._parameters_to_features(c, spaces) for c in candidates]
        candidate_features_scaled = self.parameter_scaler.transform(candidate_features)
        
        # Predict with uncertainty
        mean_pred, std_pred = self.surrogate_model.predict(candidate_features_scaled, return_std=True)
        
        # Calculate acquisition function (Expected Improvement)
        acquisition_scores = self._calculate_acquisition_function(mean_pred, std_pred)
        
        # Select best candidate
        best_idx = np.argmax(acquisition_scores)
        return candidates[best_idx]
    
    def _calculate_acquisition_function(self, mean_pred: np.ndarray, std_pred: np.ndarray) -> np.ndarray:
        """Calculate Expected Improvement acquisition function."""
        if not self.performance_history:
            return std_pred  # Pure exploration
        
        best_so_far = max(self.performance_history)
        
        # Expected Improvement
        improvement = mean_pred - best_so_far - self.exploration_factor
        Z = improvement / (std_pred + 1e-6)
        
        from scipy.stats import norm
        ei = improvement * norm.cdf(Z) + std_pred * norm.pdf(Z)
        return ei
    
    def _parameters_to_features(self, params: Dict[str, Any], spaces: List[ParameterSpace]) -> List[float]:
        """Convert parameter dictionary to feature vector."""
        features = []
        
        for space in spaces:
            value = params.get(space.name, space.current_value)
            
            if space.param_type == ParameterType.CONTINUOUS:
                # Normalize continuous values
                normalized = (value - space.min_value) / (space.max_value - space.min_value)
                features.append(normalized)
            
            elif space.param_type == ParameterType.DISCRETE:
                # One-hot encode discrete values
                for discrete_val in space.discrete_values:
                    features.append(1.0 if value == discrete_val else 0.0)
            
            elif space.param_type == ParameterType.CATEGORICAL:
                # One-hot encode categorical values
                for cat_val in space.discrete_values:
                    features.append(1.0 if value == cat_val else 0.0)
        
        return features
    
    async def _evaluate_performance(self, parameters: Dict[str, Any]) -> Dict[str, float]:
        """Evaluate performance with given parameters."""
        # Apply parameters temporarily
        original_params = {}
        for name, value in parameters.items():
            if name in self.parameter_spaces:
                original_params[name] = self.parameter_spaces[name].current_value
                self.parameter_spaces[name].current_value = value
        
        try:
            # Simulate performance evaluation
            # In practice, this would run actual inference tests
            performance = await self._simulate_performance_evaluation(parameters)
            
        finally:
            # Restore original parameters
            for name, value in original_params.items():
                self.parameter_spaces[name].current_value = value
        
        return performance
    
    async def _simulate_performance_evaluation(self, parameters: Dict[str, Any]) -> Dict[str, float]:
        """Simulate performance evaluation (replace with actual testing)."""
        # Simulate realistic performance based on parameters
        base_latency = 0.1
        base_accuracy = 0.85
        base_memory = 256
        base_throughput = 100
        
        # Parameter effects (simplified model)
        batch_size = parameters.get('batch_size', 1)
        model_precision = parameters.get('model_precision', 'float32')
        cache_size = parameters.get('cache_size_mb', 512)
        worker_threads = parameters.get('worker_threads', 2)
        
        # Latency effects
        latency = base_latency * (1 + 0.1 * np.log(batch_size))
        latency *= (0.8 if model_precision == 'float16' else 1.0)
        latency *= (0.6 if model_precision == 'int8' else 1.0)
        latency /= np.sqrt(worker_threads)
        
        # Accuracy effects
        accuracy = base_accuracy
        accuracy *= (0.95 if model_precision == 'float16' else 1.0)
        accuracy *= (0.85 if model_precision == 'int8' else 1.0)
        
        # Memory effects
        memory = base_memory + cache_size
        memory *= (1.2 if model_precision == 'float32' else 1.0)
        memory *= (0.8 if model_precision == 'float16' else 1.0)
        memory *= (0.5 if model_precision == 'int8' else 1.0)
        
        # Throughput effects
        throughput = base_throughput * batch_size / latency
        throughput *= worker_threads * 0.8  # Threading efficiency
        
        # Add some noise
        latency += np.random.normal(0, 0.01)
        accuracy += np.random.normal(0, 0.02)
        memory += np.random.normal(0, 10)
        throughput += np.random.normal(0, 5)
        
        return {
            'latency': max(0.01, latency),
            'accuracy': max(0.0, min(1.0, accuracy)),
            'memory_usage': max(1.0, memory),
            'throughput': max(1.0, throughput)
        }
    
    def _calculate_objective_score(self, performance: Dict[str, float]) -> float:
        """Calculate objective score based on optimization goal."""
        latency = performance['latency']
        accuracy = performance['accuracy']
        memory = performance['memory_usage']
        throughput = performance['throughput']
        
        if self.optimization_objective == OptimizationObjective.LATENCY:
            return 1.0 / latency  # Lower latency is better
        
        elif self.optimization_objective == OptimizationObjective.ACCURACY:
            return accuracy  # Higher accuracy is better
        
        elif self.optimization_objective == OptimizationObjective.MEMORY:
            return 1.0 / memory  # Lower memory is better
        
        elif self.optimization_objective == OptimizationObjective.THROUGHPUT:
            return throughput  # Higher throughput is better
        
        elif self.optimization_objective == OptimizationObjective.BALANCED:
            # Balanced objective considering multiple factors
            latency_score = 1.0 / latency
            accuracy_score = accuracy
            memory_score = 1.0 / (memory / 100)  # Normalize memory
            throughput_score = throughput / 100   # Normalize throughput
            
            return (latency_score * 0.3 + accuracy_score * 0.3 + 
                   memory_score * 0.2 + throughput_score * 0.2)
        
        return 0.0
    
    def _calculate_improvement(self, performance: Dict[str, float]) -> float:
        """Calculate improvement over baseline performance."""
        if not self.baseline_performance:
            return 0.0
        
        current_score = self._calculate_objective_score(performance)
        baseline_score = self._calculate_objective_score(self.baseline_performance)
        
        return (current_score - baseline_score) / baseline_score * 100
    
    def _initialize_surrogate_model(self) -> None:
        """Initialize Gaussian Process surrogate model."""
        self.surrogate_model = GaussianProcessRegressor(
            kernel=self.kernel,
            alpha=1e-6,
            normalize_y=True,
            n_restarts_optimizer=5,
            random_state=42
        )
    
    def _update_surrogate_model(self, evaluations: List[Dict[str, Any]]) -> None:
        """Update surrogate model with new evaluations."""
        if len(evaluations) < 2:
            return
        
        if not self.current_session:
            return
        
        # Prepare training data
        X_features = []
        y_scores = []
        
        for eval_data in evaluations:
            features = self._parameters_to_features(
                eval_data['parameters'], 
                self.current_session.parameter_spaces
            )
            X_features.append(features)
            y_scores.append(eval_data['score'])
        
        # Scale features
        X_scaled = self.parameter_scaler.fit_transform(X_features)
        y_scaled = self.performance_scaler.fit_transform(np.array(y_scores).reshape(-1, 1)).flatten()
        
        # Fit surrogate model
        try:
            self.surrogate_model.fit(X_scaled, y_scaled)
            self.is_trained = True
            self.performance_history = y_scores
        except Exception as e:
            self.logger.error(f"Failed to update surrogate model: {e}")
    
    def _check_convergence(self, convergence_history: List[float]) -> bool:
        """Check if optimization has converged."""
        if len(convergence_history) < 10:
            return False
        
        recent_scores = convergence_history[-10:]
        score_range = max(recent_scores) - min(recent_scores)
        
        return score_range < self.convergence_threshold
    
    async def _apply_parameters(self, parameters: Dict[str, Any]) -> None:
        """Apply optimized parameters to the system."""
        for name, value in parameters.items():
            if name in self.parameter_spaces:
                self.parameter_spaces[name].current_value = value
                self.best_known_parameters[name] = value
        
        self.logger.info(f"Applied optimized parameters: {parameters}")
    
    def get_current_parameters(self) -> Dict[str, Any]:
        """Get current parameter values."""
        return {
            name: space.current_value 
            for name, space in self.parameter_spaces.items()
        }
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status."""
        status = {
            'is_tuning': self.is_tuning,
            'current_session': None,
            'best_known_parameters': self.best_known_parameters.copy(),
            'total_evaluations': len(self.evaluation_history),
            'baseline_performance': self.baseline_performance
        }
        
        if self.current_session:
            status['current_session'] = {
                'session_id': self.current_session.session_id,
                'objective': self.current_session.objective.value,
                'evaluations_count': len(self.current_session.evaluations),
                'best_score': self.current_session.best_result.performance_score if self.current_session.best_result else None,
                'convergence_history': self.current_session.convergence_history[-10:] if self.current_session.convergence_history else []
            }
        
        return status
    
    async def stop_tuning_session(self) -> Optional[OptimizationResult]:
        """Stop current tuning session."""
        if not self.is_tuning or not self.current_session:
            return None
        
        self.current_session.end_time = time.time()
        self.is_tuning = False
        
        result = self.current_session.best_result
        self.logger.info(f"Tuning session stopped. Best result: {result}")
        
        return result
    
    def set_optimization_objective(self, objective: OptimizationObjective) -> None:
        """Set optimization objective."""
        self.optimization_objective = objective
        self.logger.info(f"Optimization objective set to: {objective.value}")
    
    def add_parameter_space(self, space: ParameterSpace) -> None:
        """Add new parameter space for optimization."""
        self.parameter_spaces[space.name] = space
        self.logger.info(f"Added parameter space: {space.name}")
    
    def remove_parameter_space(self, name: str) -> None:
        """Remove parameter space from optimization."""
        if name in self.parameter_spaces:
            del self.parameter_spaces[name]
            self.logger.info(f"Removed parameter space: {name}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance optimization summary."""
        if not self.evaluation_history:
            return {'message': 'No evaluations performed yet'}
        
        scores = [eval_data['score'] for eval_data in self.evaluation_history]
        improvements = []
        
        if self.baseline_performance:
            baseline_score = self._calculate_objective_score(self.baseline_performance)
            improvements = [(score - baseline_score) / baseline_score * 100 for score in scores]
        
        return {
            'total_evaluations': len(self.evaluation_history),
            'best_score': max(scores),
            'average_score': np.mean(scores),
            'score_improvement': max(improvements) if improvements else 0.0,
            'convergence_rate': len([i for i in improvements if i > 0]) / len(improvements) if improvements else 0.0,
            'best_parameters': self.best_known_parameters.copy()
        }