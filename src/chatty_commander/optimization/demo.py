#!/usr/bin/env python3
"""
AI-Powered Performance Optimization System Demo

This script demonstrates the complete AI-powered optimization system
with all its intelligent components working together.
"""

import asyncio
import logging
import numpy as np
import time
from typing import Dict, Any

from .optimizer_orchestrator import OptimizationOrchestrator, OptimizationConfig
from .adaptive_audio import AdaptationMode
from .auto_tuner import OptimizationObjective


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OptimizationDemo:
    """Comprehensive demonstration of AI-powered optimization features."""
    
    def __init__(self):
        self.orchestrator: OptimizationOrchestrator = None
        self.demo_audio_data = self._generate_demo_audio_data()
        
    def _generate_demo_audio_data(self) -> Dict[str, np.ndarray]:
        """Generate synthetic audio data for testing."""
        sample_rate = 16000
        duration = 0.1  # 100ms frames
        samples = int(sample_rate * duration)
        
        # Generate different audio environments
        return {
            'quiet': np.random.normal(0, 0.05, samples),  # Low noise
            'normal': np.random.normal(0, 0.15, samples),  # Medium noise
            'noisy': np.random.normal(0, 0.4, samples),   # High noise
            'very_noisy': np.random.normal(0, 0.8, samples)  # Very high noise
        }
    
    async def run_complete_demo(self):
        """Run the complete optimization system demonstration."""
        print("🚀 Starting AI-Powered Performance Optimization Demo")
        print("=" * 60)
        
        # Initialize the optimization orchestrator
        await self._initialize_orchestrator()
        
        # Demo each component
        await self._demo_intelligent_caching()
        await self._demo_performance_monitoring()
        await self._demo_adaptive_audio()
        await self._demo_parameter_optimization()
        await self._demo_coordinated_optimization()
        
        # Show final results
        await self._show_optimization_results()
        
        # Cleanup
        await self._cleanup()
        
        print("\n✅ AI-Powered Performance Optimization Demo Complete!")
    
    async def _initialize_orchestrator(self):
        """Initialize the optimization orchestrator."""
        print("\n🔧 Initializing Optimization Orchestrator...")
        
        config = OptimizationConfig(
            enable_cache_optimization=True,
            enable_performance_monitoring=True,
            enable_audio_adaptation=True,
            enable_parameter_tuning=True,
            auto_optimization_interval=60.0,  # Faster for demo
            cache_memory_limit_mb=256,
            audio_adaptation_mode=AdaptationMode.BALANCED,
            tuning_objective=OptimizationObjective.BALANCED
        )
        
        self.orchestrator = OptimizationOrchestrator(config)
        await self.orchestrator.initialize()
        await self.orchestrator.start_optimization()
        
        print("✅ Orchestrator initialized with all components")
        
        # Show initial status
        status = self.orchestrator.get_optimization_status()
        print(f"   Active optimizations: {status.active_optimizations}")
        print(f"   Overall performance score: {status.overall_performance_score:.3f}")
    
    async def _demo_intelligent_caching(self):
        """Demonstrate intelligent model caching with predictive loading."""
        print("\n🧠 Demonstrating Intelligent Model Caching...")
        
        cache_optimizer = self.orchestrator.cache_optimizer
        if not cache_optimizer:
            print("❌ Cache optimizer not available")
            return
        
        # Simulate model loading patterns
        models = ['hey_chat_tee', 'hey_khum_puter', 'okay_stop', 'wax_poetic']
        
        print("   Simulating model usage patterns...")
        for i in range(20):
            # Simulate realistic usage patterns
            if i < 5:
                model = models[0]  # Heavy use of first model
            elif i < 10:
                model = models[1]  # Switch to second model
            elif i < 15:
                model = np.random.choice(models[:2])  # Mix of first two
            else:
                model = np.random.choice(models)  # Random usage
            
            # Record usage with simulated metrics
            load_time = np.random.uniform(0.1, 2.0)
            inference_time = np.random.uniform(0.05, 0.3)
            context = {'state': 'idle' if i < 10 else 'chatty', 'confidence': np.random.uniform(0.7, 0.95)}
            
            cache_optimizer.record_usage(model, context['state'], load_time, inference_time, context)
            await asyncio.sleep(0.1)  # Small delay for realism
        
        # Show cache performance
        metrics = cache_optimizer.get_cache_metrics()
        print(f"   Cache hit rate: {metrics.hit_rate:.3f}")
        print(f"   Memory usage: {metrics.memory_usage_mb:.1f} MB")
        print(f"   Prediction accuracy: {metrics.prediction_accuracy:.3f}")
        print("✅ Intelligent caching demonstrated")
    
    async def _demo_performance_monitoring(self):
        """Demonstrate AI-powered performance monitoring and anomaly detection."""
        print("\n📊 Demonstrating AI Performance Monitoring...")
        
        performance_monitor = self.orchestrator.performance_monitor
        if not performance_monitor:
            print("❌ Performance monitor not available")
            return
        
        # Let monitoring run and collect baseline data
        print("   Collecting baseline performance data...")
        await asyncio.sleep(3)
        
        # Generate some performance alerts by manual trigger
        print("   Triggering performance optimization scenarios...")
        await self.orchestrator.manual_optimization_trigger('performance')
        await asyncio.sleep(2)
        
        # Get performance report
        report = performance_monitor.get_performance_report(period_hours=0.1)
        print(f"   Overall performance level: {report.overall_level.value}")
        print(f"   Average latency: {report.average_latency:.3f}s")
        print(f"   Peak memory usage: {report.peak_memory_usage:.1f}%")
        print(f"   Cache efficiency: {report.cache_efficiency:.3f}")
        print(f"   Anomalies detected: {report.anomalies_detected}")
        print("✅ Performance monitoring demonstrated")
    
    async def _demo_adaptive_audio(self):
        """Demonstrate adaptive audio processing with environmental adaptation."""
        print("\n🎤 Demonstrating Adaptive Audio Processing...")
        
        audio_processor = self.orchestrator.audio_processor
        if not audio_processor:
            print("❌ Audio processor not available")
            return
        
        # Simulate different audio environments
        environments = ['quiet', 'normal', 'noisy', 'very_noisy']
        
        print("   Testing adaptive audio in different environments...")
        for env_name in environments:
            print(f"     Processing {env_name} environment...")
            audio_data = self.demo_audio_data[env_name]
            
            # Process multiple audio frames
            for _ in range(5):
                detection_result, confidence = await audio_processor.process_audio_frame(
                    audio_data, ground_truth=np.random.choice([True, False], p=[0.1, 0.9])
                )
                await asyncio.sleep(0.1)
            
            # Show environment status
            status = audio_processor.get_environment_status()
            print(f"       Environment: {status['current_environment']}")
            print(f"       Performance score: {status['performance_score']:.3f}")
            print(f"       Noise level: {status['recent_noise_level']:.3f}")
        
        print("✅ Adaptive audio processing demonstrated")
    
    async def _demo_parameter_optimization(self):
        """Demonstrate AI-powered parameter optimization."""
        print("\n⚙️ Demonstrating Parameter Optimization...")
        
        auto_tuner = self.orchestrator.auto_tuner
        if not auto_tuner:
            print("❌ Auto-tuner not available")
            return
        
        print("   Running focused parameter optimization...")
        
        # Start a focused tuning session
        session_id = await auto_tuner.start_tuning_session(
            objective=OptimizationObjective.BALANCED,
            parameter_subset=['batch_size', 'cache_size_mb', 'worker_threads']
        )
        
        print(f"   Started tuning session: {session_id}")
        
        # Run a short optimization (limited iterations for demo)
        auto_tuner.max_evaluations = 10  # Reduce for demo speed
        result = await auto_tuner.run_optimization()
        
        if result:
            print(f"   Optimization completed!")
            print(f"     Performance improvement: {result.improvement_over_baseline:.2f}%")
            print(f"     Best latency: {result.latency:.3f}s")
            print(f"     Best accuracy: {result.accuracy:.3f}")
            print(f"     Memory usage: {result.memory_usage:.1f}MB")
            print(f"     Optimized parameters: {result.parameters}")
        
        print("✅ Parameter optimization demonstrated")
    
    async def _demo_coordinated_optimization(self):
        """Demonstrate coordinated optimization across all components."""
        print("\n🎯 Demonstrating Coordinated Optimization...")
        
        print("   Triggering full system optimization...")
        
        # Trigger comprehensive optimization
        success = await self.orchestrator.manual_optimization_trigger('full')
        
        if success:
            print("   Full optimization triggered successfully")
            
            # Wait for optimizations to process
            await asyncio.sleep(5)
            
            # Show optimization triggers and responses
            status = self.orchestrator.get_optimization_status()
            print(f"   Current optimizations active: {status.active_optimizations}")
            print(f"   Performance score: {status.overall_performance_score:.3f}")
            
            if status.recommendations:
                print("   System recommendations:")
                for rec in status.recommendations:
                    print(f"     • {rec}")
        
        print("✅ Coordinated optimization demonstrated")
    
    async def _show_optimization_results(self):
        """Show comprehensive optimization results."""
        print("\n📈 Optimization Results Summary")
        print("-" * 40)
        
        summary = self.orchestrator.get_performance_summary()
        
        # Orchestrator status
        status = summary['orchestrator_status']
        print(f"System Status: {'🟢 Active' if status.is_active else '🔴 Inactive'}")
        print(f"Overall Performance Score: {status.overall_performance_score:.3f}")
        
        # Component status
        components = {
            'Intelligent Caching': status.cache_optimization,
            'Performance Monitoring': status.performance_monitoring,
            'Audio Adaptation': status.audio_adaptation,
            'Parameter Tuning': status.parameter_tuning,
        }
        
        print("\nComponent Status:")
        for name, active in components.items():
            icon = "✅" if active else "❌"
            print(f"  {icon} {name}")
        
        # Performance metrics
        current = summary['current_performance']
        baseline = summary['baseline_performance']
        
        if current and baseline:
            print("\nPerformance Comparison (Current vs Baseline):")
            for metric, current_val in current.items():
                if metric in baseline and isinstance(current_val, (int, float)):
                    baseline_val = baseline[metric]
                    if baseline_val != 0:
                        improvement = ((current_val - baseline_val) / baseline_val) * 100
                        trend = "📈" if improvement > 0 else "📉" if improvement < 0 else "➡️"
                        print(f"  {trend} {metric}: {current_val:.3f} ({improvement:+.1f}%)")
        
        # Recommendations
        if status.recommendations:
            print("\nSystem Recommendations:")
            for i, rec in enumerate(status.recommendations, 1):
                print(f"  {i}. {rec}")
    
    async def _cleanup(self):
        """Clean up the optimization system."""
        print("\n🧹 Cleaning up optimization system...")
        await self.orchestrator.stop_optimization()
        print("✅ Cleanup complete")


async def run_focused_demo(component: str):
    """Run a focused demo of a specific optimization component."""
    demo = OptimizationDemo()
    await demo._initialize_orchestrator()
    
    if component == "cache":
        await demo._demo_intelligent_caching()
    elif component == "performance":
        await demo._demo_performance_monitoring()
    elif component == "audio":
        await demo._demo_adaptive_audio()
    elif component == "tuning":
        await demo._demo_parameter_optimization()
    else:
        print(f"Unknown component: {component}")
        return
    
    await demo._cleanup()


async def run_benchmark_test():
    """Run a performance benchmark test."""
    print("🏃‍♂️ Running Performance Benchmark Test")
    print("=" * 50)
    
    demo = OptimizationDemo()
    
    # Test optimization system performance
    start_time = time.perf_counter()
    
    await demo._initialize_orchestrator()
    
    # Simulate heavy workload
    print("Simulating heavy workload...")
    for i in range(50):
        # Simulate model cache operations
        if demo.orchestrator.cache_optimizer:
            demo.orchestrator.cache_optimizer.record_usage(
                f"model_{i % 5}", "idle", 
                np.random.uniform(0.1, 1.0), 
                np.random.uniform(0.05, 0.2)
            )
        
        # Simulate audio processing
        if demo.orchestrator.audio_processor:
            audio_data = np.random.normal(0, 0.2, 1600)  # 100ms at 16kHz
            await demo.orchestrator.audio_processor.process_audio_frame(audio_data)
        
        await asyncio.sleep(0.01)  # 10ms delay
    
    end_time = time.perf_counter()
    duration = end_time - start_time
    
    print(f"Benchmark completed in {duration:.2f} seconds")
    print(f"Average processing time per iteration: {(duration/50)*1000:.2f}ms")
    
    # Show final metrics
    if demo.orchestrator.cache_optimizer:
        cache_metrics = demo.orchestrator.cache_optimizer.get_cache_metrics()
        print(f"Cache hit rate: {cache_metrics.hit_rate:.3f}")
    
    await demo._cleanup()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command in ["cache", "performance", "audio", "tuning"]:
            asyncio.run(run_focused_demo(command))
        elif command == "benchmark":
            asyncio.run(run_benchmark_test())
        elif command == "full":
            demo = OptimizationDemo()
            asyncio.run(demo.run_complete_demo())
        else:
            print("Usage: python demo.py [full|cache|performance|audio|tuning|benchmark]")
    else:
        # Run full demo by default
        demo = OptimizationDemo()
        asyncio.run(demo.run_complete_demo())