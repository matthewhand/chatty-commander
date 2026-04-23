#!/usr/bin/env python3
"""
QA TIMING DASHBOARD
Quick timing measurements for all QA activities.

Shows:
- Test suite execution time
- Individual QA agent run times  
- Bottleneck identification
- Optimization recommendations
"""

import json
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TimingMeasurement:
    activity: str
    duration_seconds: float
    items_processed: int = 0
    rate_per_second: float = 0.0
    notes: str = ""


class TimingDashboard:
    """Measures and displays timing for all QA activities."""
    
    def __init__(self):
        self.measurements: list[TimingMeasurement] = []
    
    def measure(self, name: str, func, *args, **kwargs) -> Any:
        """Measure execution time of a function."""
        print(f"\n⏱️  TIMING: {name}...")
        start = time.perf_counter()
        
        try:
            result = func(*args, **kwargs)
            duration = time.perf_counter() - start
            print(f"   ✅ Completed in {duration:.2f}s")
            return result, duration
        except Exception as e:
            duration = time.perf_counter() - start
            print(f"   ❌ Failed after {duration:.2f}s: {e}")
            return None, duration
    
    def time_test_discovery(self) -> TimingMeasurement:
        """Time how long test discovery takes."""
        cmd = ['python', '-m', 'pytest', '--collect-only', '-q']
        
        start = time.perf_counter()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        duration = time.perf_counter() - start
        
        # Count tests
        test_count = len([l for l in result.stdout.split('\n') 
                         if 'test_' in l and '::' in l])
        
        return TimingMeasurement(
            activity="Test Discovery",
            duration_seconds=duration,
            items_processed=test_count,
            rate_per_second=test_count / max(duration, 0.001),
            notes=f"Found {test_count} tests"
        )
    
    def time_quick_test_run(self) -> TimingMeasurement:
        """Time a quick smoke test."""
        cmd = ['python', '-m', 'pytest', 
               'tests/test_version.py', 
               '-v', '--tb=short', '-x']
        
        start = time.perf_counter()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        duration = time.perf_counter() - start
        
        passed = result.stdout.count('PASSED')
        failed = result.stdout.count('FAILED')
        
        return TimingMeasurement(
            activity="Quick Test Run (test_version.py)",
            duration_seconds=duration,
            items_processed=passed + failed,
            rate_per_second=(passed + failed) / max(duration, 0.001),
            notes=f"Passed: {passed}, Failed: {failed}"
        )
    
    def time_qa_agent(self, agent_name: str, script_path: str) -> TimingMeasurement:
        """Time a single QA agent execution."""
        cmd = ['python', script_path]
        
        start = time.perf_counter()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        duration = time.perf_counter() - start
        
        success = result.returncode == 0
        
        return TimingMeasurement(
            activity=f"QA Agent: {agent_name}",
            duration_seconds=duration,
            items_processed=0,
            rate_per_second=0.0,
            notes="Success" if success else f"Exit code: {result.returncode}"
        )
    
    def time_all_qa_agents(self) -> list[TimingMeasurement]:
        """Time all 6 QA agents."""
        agents = [
            ("Code Quality", "qa/code_quality_agent.py"),
            ("Test Coverage", "qa/test_coverage_agent.py"),
            ("Security Audit", "qa/security_audit_agent.py"),
            ("Performance", "qa/performance_agent.py"),
            ("Documentation", "qa/documentation_agent.py"),
            ("Dependency Audit", "qa/dependency_audit_agent.py"),
        ]
        
        results = []
        for name, path in agents:
            measurement = self.time_qa_agent(name, path)
            results.append(measurement)
            self.measurements.append(measurement)
        
        return results
    
    def estimate_full_suite_time(self, sample_rate: float) -> TimingMeasurement:
        """Estimate time for full test suite."""
        # Get test count
        cmd = ['python', '-m', 'pytest', '--collect-only', '-q']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        test_count = len([l for l in result.stdout.split('\n') 
                         if 'test_' in l and '::' in l])
        
        # Estimate
        estimated_seconds = test_count * sample_rate
        
        return TimingMeasurement(
            activity="Estimated Full Suite",
            duration_seconds=estimated_seconds,
            items_processed=test_count,
            rate_per_second=1.0 / max(sample_rate, 0.001),
            notes=f"Based on {sample_rate:.3f}s per test average"
        )
    
    def display_dashboard(self) -> None:
        """Display timing dashboard."""
        print("\n" + "="*70)
        print("📊 QA TIMING DASHBOARD")
        print("="*70)
        
        if not self.measurements:
            print("\nNo measurements yet. Run timing functions first.")
            return
        
        # Table header
        print(f"\n{'Activity':<40} {'Time':>10} {'Rate':>12} {'Status':>10}")
        print("-"*70)
        
        # Sort by duration
        sorted_measurements = sorted(self.measurements, 
                                    key=lambda x: x.duration_seconds)
        
        for m in sorted_measurements:
            time_str = f"{m.duration_seconds:.2f}s"
            if m.duration_seconds > 60:
                minutes = int(m.duration_seconds // 60)
                secs = int(m.duration_seconds % 60)
                time_str = f"{minutes}m {secs}s"
            
            rate_str = ""
            if m.rate_per_second > 0:
                if m.rate_per_second >= 1:
                    rate_str = f"{m.rate_per_second:.1f}/s"
                else:
                    rate_str = f"{1/m.rate_per_second:.1f}s/item"
            
            status = "✓" if "Success" in m.notes or "Passed" in m.notes else "✗"
            
            print(f"{m.activity:<40} {time_str:>10} {rate_str:>12} {status:>10}")
        
        # Summary
        total_time = sum(m.duration_seconds for m in self.measurements)
        print("-"*70)
        print(f"{'TOTAL':<40} {total_time:>10.1f}s")
        
        # Bottlenecks
        print("\n🔴 BOTTLENECKS (slowest activities):")
        slowest = sorted(self.measurements, key=lambda x: -x.duration_seconds)[:3]
        for i, m in enumerate(slowest, 1):
            print(f"{i}. {m.activity}: {m.duration_seconds:.1f}s - {m.notes}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if any(m.duration_seconds > 60 for m in self.measurements):
            print("   • Consider running slow activities in parallel")
        if any("Failed" in m.notes or "Exit code" in m.notes for m in self.measurements):
            print("   • Some activities failed - check error logs")
        if total_time > 300:
            print("   • Total time > 5min - consider optimizing or parallelizing")
        else:
            print("   • Timing looks good - all activities under 5min total")
    
    def export_report(self, filename: str = "qa_timing_report.json") -> None:
        """Export timing report to JSON."""
        report = {
            'measurements': [
                {
                    'activity': m.activity,
                    'duration_seconds': m.duration_seconds,
                    'items_processed': m.items_processed,
                    'rate_per_second': m.rate_per_second,
                    'notes': m.notes
                }
                for m in self.measurements
            ],
            'total_duration': sum(m.duration_seconds for m in self.measurements),
            'count': len(self.measurements)
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Report saved to: {filename}")


def quick_time():
    """Quick timing run of key metrics."""
    print("⚡ QUICK TIMING RUN")
    print("="*60)
    
    dashboard = TimingDashboard()
    
    # Time test discovery
    m = dashboard.time_test_discovery()
    dashboard.measurements.append(m)
    print(f"   {m.notes}")
    
    # Time quick test
    m = dashboard.time_quick_test_run()
    dashboard.measurements.append(m)
    
    # Estimate full suite
    if m.items_processed > 0:
        rate = m.duration_seconds / m.items_processed
        m = dashboard.estimate_full_suite_time(rate)
        dashboard.measurements.append(m)
    
    # Display
    dashboard.display_dashboard()
    
    return dashboard


def full_time():
    """Full timing run including QA agents."""
    print("🔬 FULL TIMING RUN (including all QA agents)")
    print("="*60)
    print("This will take several minutes...")
    
    dashboard = TimingDashboard()
    
    # Test discovery
    m = dashboard.time_test_discovery()
    dashboard.measurements.append(m)
    
    # Quick test
    m = dashboard.time_quick_test_run()
    dashboard.measurements.append(m)
    
    # Estimate
    if m.items_processed > 0:
        rate = m.duration_seconds / m.items_processed
        m = dashboard.estimate_full_suite_time(rate)
        dashboard.measurements.append(m)
    
    # All QA agents
    print("\n⏱️  Running all QA agents...")
    dashboard.time_all_qa_agents()
    
    # Display
    dashboard.display_dashboard()
    dashboard.export_report()
    
    return dashboard


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--full':
        full_time()
    else:
        quick_time()
