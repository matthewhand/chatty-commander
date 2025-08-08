#!/usr/bin/env python3
"""
Integration Example: AI-Powered Optimization with ChattyCommander

This example shows how to integrate the optimization system with 
the existing ChattyCommander application architecture.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from .optimizer_orchestrator import OptimizationOrchestrator, OptimizationConfig
from .adaptive_audio import AdaptationMode
from .auto_tuner import OptimizationObjective


class OptimizedModelManager:
    """Enhanced ModelManager with AI-powered optimization integration."""
    
    def __init__(self, config: Any, optimization_orchestrator: OptimizationOrchestrator):
        self.config = config
        self.optimization_orchestrator = optimization_orchestrator
        self.models: Dict[str, Dict[str, Any]] = {'general': {}, 'system': {}, 'chat': {}}
        self.active_models: Dict[str, Any] = {}
        
        # Get intelligent cache from orchestrator
        self.intelligent_cache = optimization_orchestrator.cache_optimizer
        
        self.logger = logging.getLogger(__name__)
    
    async def load_model_with_optimization(self, model_name: str, model_path: str) -> Any:
        """Load model using intelligent caching and optimization."""
        if self.intelligent_cache:
            # Use intelligent cache with predictive loading
            def model_loader():
                # Simulate actual model loading
                import time
                time.sleep(0.1)  # Simulate load time
                return f"MockModel({model_name})"
            
            model = await self.intelligent_cache.get_model(model_name, model_loader)
            self.logger.info(f"Loaded model {model_name} with intelligent caching")
            return model
        else:
            # Fallback to standard loading
            return self._load_model_standard(model_path)
    
    def _load_model_standard(self, model_path: str) -> Any:
        """Standard model loading without optimization."""
        return f"StandardModel({model_path})"
    
    async def reload_models_optimized(self, state: str = None) -> Dict[str, Any]:
        """Reload models with optimization-aware strategy."""
        # Record state transition for intelligent caching
        if self.intelligent_cache and hasattr(self, '_last_state'):
            self.intelligent_cache.record_state_transition(self._last_state, state or 'idle')
        
        # Use optimization parameters for model loading
        auto_tuner = self.optimization_orchestrator.auto_tuner
        if auto_tuner:
            params = auto_tuner.get_current_parameters()
            # Apply optimized parameters to model loading
            self.logger.info(f"Using optimized parameters: {params}")
        
        # Load models with optimization
        models = {}
        model_paths = ['model1.onnx', 'model2.onnx', 'model3.onnx']
        
        for model_path in model_paths:
            model_name = model_path.replace('.onnx', '')
            model = await self.load_model_with_optimization(model_name, model_path)
            models[model_name] = model
        
        self._last_state = state or 'idle'
        return models


class OptimizedAudioProcessor:
    """Enhanced audio processor with adaptive optimization."""
    
    def __init__(self, optimization_orchestrator: OptimizationOrchestrator):
        self.optimization_orchestrator = optimization_orchestrator
        self.adaptive_processor = optimization_orchestrator.audio_processor
        self.logger = logging.getLogger(__name__)
    
    async def process_audio_with_adaptation(self, audio_data, ground_truth: Optional[bool] = None):
        """Process audio with adaptive thresholds and environmental awareness."""
        if self.adaptive_processor:
            # Use adaptive audio processing
            detection_result, confidence = await self.adaptive_processor.process_audio_frame(
                audio_data, ground_truth
            )
            
            # Get current environment status
            env_status = self.adaptive_processor.get_environment_status()
            
            self.logger.debug(
                f"Audio processed: detection={detection_result}, "
                f"confidence={confidence:.3f}, environment={env_status['current_environment']}"
            )
            
            return detection_result, confidence, env_status
        else:
            # Fallback to standard processing
            return self._process_audio_standard(audio_data)
    
    def _process_audio_standard(self, audio_data):
        """Standard audio processing without adaptation."""
        # Simulate basic processing
        import numpy as np
        confidence = np.random.uniform(0.6, 0.9)
        detection = confidence > 0.7
        return detection, confidence, {}


class OptimizedChattyCommander:
    """
    Main ChattyCommander application with integrated AI-powered optimization.
    
    This class demonstrates how to integrate the optimization system
    with the existing ChattyCommander architecture.
    """
    
    def __init__(self, config: Any):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize optimization system
        self.optimization_config = OptimizationConfig(
            enable_cache_optimization=True,
            enable_performance_monitoring=True,
            enable_audio_adaptation=True,
            enable_parameter_tuning=True,
            auto_optimization_interval=300.0,  # 5 minutes
            cache_memory_limit_mb=getattr(config, 'cache_memory_limit', 512),
            audio_adaptation_mode=AdaptationMode.BALANCED,
            tuning_objective=OptimizationObjective.BALANCED
        )
        
        self.optimization_orchestrator = OptimizationOrchestrator(self.optimization_config)
        
        # Initialize optimized components
        self.model_manager = OptimizedModelManager(config, self.optimization_orchestrator)
        self.audio_processor = OptimizedAudioProcessor(self.optimization_orchestrator)
        
        # Performance monitoring
        self.performance_monitor = None
        
        # Application state
        self.is_running = False
        self.current_state = "idle"
    
    async def initialize(self):
        """Initialize the optimized ChattyCommander application."""
        self.logger.info("Initializing ChattyCommander with AI-powered optimization...")
        
        # Initialize optimization orchestrator
        await self.optimization_orchestrator.initialize()
        await self.optimization_orchestrator.start_optimization()
        
        # Get performance monitor reference
        self.performance_monitor = self.optimization_orchestrator.performance_monitor
        
        # Load initial models with optimization
        await self.model_manager.reload_models_optimized(self.current_state)
        
        self.logger.info("✅ ChattyCommander initialized with optimization system")
        
        # Show optimization status
        status = self.optimization_orchestrator.get_optimization_status()
        self.logger.info(f"Active optimizations: {status.active_optimizations}")
        self.logger.info(f"Performance score: {status.overall_performance_score:.3f}")
    
    async def run_voice_recognition_loop(self):
        """Main voice recognition loop with optimization integration."""
        self.is_running = True
        self.logger.info("Starting optimized voice recognition loop...")
        
        import numpy as np
        frame_count = 0
        
        while self.is_running:
            try:
                # Simulate audio input
                audio_data = np.random.normal(0, 0.2, 1600)  # 100ms at 16kHz
                
                # Process audio with adaptive optimization
                detection_result, confidence, env_status = await self.audio_processor.process_audio_with_adaptation(
                    audio_data, ground_truth=np.random.choice([True, False], p=[0.05, 0.95])
                )
                
                # Handle detection
                if detection_result:
                    await self._handle_command_detection(confidence, env_status)
                
                # Periodic optimization reporting
                frame_count += 1
                if frame_count % 100 == 0:  # Every 10 seconds (at 10 FPS)
                    await self._report_optimization_status()
                
                await asyncio.sleep(0.1)  # 10 FPS
                
            except Exception as e:
                self.logger.error(f"Error in voice recognition loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _handle_command_detection(self, confidence: float, env_status: Dict[str, Any]):
        """Handle detected voice command with optimization context."""
        self.logger.info(f"Command detected! Confidence: {confidence:.3f}")
        
        # Use optimization context for better command handling
        if env_status:
            env = env_status.get('current_environment', 'unknown')
            self.logger.info(f"Audio environment: {env}")
            
            # Adjust command processing based on environment
            if env in ['noisy', 'very_noisy']:
                # Require higher confidence in noisy environments
                if confidence < 0.8:
                    self.logger.info("Ignoring command due to low confidence in noisy environment")
                    return
        
        # Simulate command execution with performance monitoring
        start_time = asyncio.get_event_loop().time()
        
        # Execute command (simulated)
        await asyncio.sleep(0.05)  # Simulate command execution time
        
        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time
        
        self.logger.info(f"Command executed in {execution_time:.3f}s")
    
    async def _report_optimization_status(self):
        """Report current optimization status and metrics."""
        status = self.optimization_orchestrator.get_optimization_status()
        
        self.logger.info("🔍 Optimization Status Report:")
        self.logger.info(f"   Overall performance: {status.overall_performance_score:.3f}")
        self.logger.info(f"   Active optimizations: {len(status.active_optimizations)}")
        
        # Cache metrics
        if self.optimization_orchestrator.cache_optimizer:
            cache_metrics = self.optimization_orchestrator.cache_optimizer.get_cache_metrics()
            self.logger.info(f"   Cache hit rate: {cache_metrics.hit_rate:.3f}")
            self.logger.info(f"   Cache memory: {cache_metrics.memory_usage_mb:.1f}MB")
        
        # Audio metrics
        if self.optimization_orchestrator.audio_processor:
            audio_status = self.optimization_orchestrator.audio_processor.get_environment_status()
            self.logger.info(f"   Audio environment: {audio_status['current_environment']}")
            self.logger.info(f"   Audio performance: {audio_status['performance_score']:.3f}")
        
        # Show recommendations
        if status.recommendations:
            self.logger.info("   Recommendations:")
            for rec in status.recommendations[:2]:  # Show top 2
                self.logger.info(f"     • {rec}")
    
    async def trigger_manual_optimization(self, optimization_type: str = "full"):
        """Manually trigger optimization for specific scenarios."""
        self.logger.info(f"Triggering manual optimization: {optimization_type}")
        
        success = await self.optimization_orchestrator.manual_optimization_trigger(optimization_type)
        
        if success:
            self.logger.info("✅ Manual optimization triggered successfully")
            
            # Wait for optimization to process
            await asyncio.sleep(2.0)
            
            # Report results
            await self._report_optimization_status()
        else:
            self.logger.warning("❌ Failed to trigger manual optimization")
    
    async def change_state(self, new_state: str):
        """Change application state with optimization awareness."""
        old_state = self.current_state
        self.current_state = new_state
        
        self.logger.info(f"State transition: {old_state} -> {new_state}")
        
        # Reload models for new state with optimization
        await self.model_manager.reload_models_optimized(new_state)
        
        # Trigger optimization for state change
        await self.trigger_manual_optimization("cache")
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        return self.optimization_orchestrator.get_performance_summary()
    
    async def shutdown(self):
        """Gracefully shutdown the optimized application."""
        self.logger.info("Shutting down ChattyCommander with optimization system...")
        
        self.is_running = False
        
        # Stop optimization orchestrator
        await self.optimization_orchestrator.stop_optimization()
        
        self.logger.info("✅ Shutdown complete")


# Example usage and integration demonstration
async def demo_integration():
    """Demonstrate the integration of optimization with ChattyCommander."""
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("🚀 ChattyCommander AI-Powered Optimization Integration Demo")
    print("=" * 60)
    
    # Mock configuration
    class MockConfig:
        cache_memory_limit = 256
    
    config = MockConfig()
    
    # Initialize optimized ChattyCommander
    app = OptimizedChattyCommander(config)
    await app.initialize()
    
    print("\n🎯 Testing optimization integration scenarios...")
    
    # Scenario 1: State transition optimization
    print("\n1. Testing state transition optimization...")
    await app.change_state("chatty")
    await asyncio.sleep(1)
    
    # Scenario 2: Manual optimization trigger
    print("\n2. Testing manual optimization trigger...")
    await app.trigger_manual_optimization("performance")
    await asyncio.sleep(1)
    
    # Scenario 3: Short voice recognition simulation
    print("\n3. Running voice recognition simulation (10 seconds)...")
    recognition_task = asyncio.create_task(app.run_voice_recognition_loop())
    await asyncio.sleep(10)
    await app.shutdown()
    recognition_task.cancel()
    
    # Show final performance summary
    print("\n📊 Final Performance Summary:")
    summary = await app.get_performance_summary()
    
    if summary:
        status = summary.get('orchestrator_status')
        if status:
            print(f"   Overall performance score: {status.overall_performance_score:.3f}")
            print(f"   Active optimizations: {status.active_optimizations}")
            if status.recommendations:
                print("   Top recommendations:")
                for rec in status.recommendations[:2]:
                    print(f"     • {rec}")
    
    print("\n✅ Integration demo complete!")


if __name__ == "__main__":
    asyncio.run(demo_integration())