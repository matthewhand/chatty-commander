#!/usr/bin/env python3
"""
TEST TIMING RUNNER
Measures how long tests take and identifies slow tests.

Usage:
    python tests/perf/timing_runner.py [options]
    
Options:
    --unit-only        Time only unit tests
    --integration-only Time only integration tests  
    --e2e-only         Time only E2E tests
    --agents           Time QA agent execution
    --all              Time everything (default)
    --threshold N      Flag tests slower than N seconds (default: 1.0)
    --json             Output as JSON for CI
    --html             Generate HTML report
"""

import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TimingResult:
    """Result from timing a test suite."""
    name: str
    duration_seconds: float
    tests_run: int
    tests_passed: int
    tests_failed: int
    slow_tests: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    
    @property
    def avg_test_time(self) -> float:
        return self.duration_seconds / max(self.tests_run, 1)
    
    @property
    def success_rate(self) -> float:
        if self.tests_run == 0:
            return 0.0
        return self.tests_passed / self.tests_run * 100


class TestTimer:
    """Times test execution and reports results."""
    
    def __init__(self, threshold: float = 1.0, json_output: bool = False):
        self.threshold = threshold
        self.json_output = json_output
        self.results: list[TimingResult] = []
    
    def run_with_timing(self, name: str, command: list[str]) -> TimingResult:
        """Run a command and time it."""
        print(f"\n{'='*60}")
        print(f"⏱️  TIMING: {name}")
        print(f"{'='*60}")
        print(f"Command: {' '.join(command)}")
        print(f"Threshold: {self.threshold}s per test\n")
        
        start = time.perf_counter()
        
        try:
            # Run with pytest's timing output
            cmd = command + [
                '--durations=50',  # Show 50 slowest tests
                '-v' if not self.json_output else '-q'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            duration = time.perf_counter() - start
            
            # Parse results
            output = result.stdout + result.stderr
            tests_run, passed, failed = self._parse_test_counts(output)
            slow_tests = self._parse_slow_tests(output)
            
            timing = TimingResult(
                name=name,
                duration_seconds=round(duration, 2),
                tests_run=tests_run,
                tests_passed=passed,
                tests_failed=failed,
                slow_tests=slow_tests[:10],  # Top 10 slowest
                errors=[] if result.returncode == 0 else [f"Exit code: {result.returncode}"]
            )
            
            self._print_timing(timing)
            return timing
            
        except subprocess.TimeoutExpired:
            duration = time.perf_counter() - start
            print(f"❌ TIMEOUT after {duration:.1f}s")
            return TimingResult(
                name=name,
                duration_seconds=round(duration, 2),
                tests_run=0,
                tests_passed=0,
                tests_failed=0,
                errors=["TIMEOUT (>600s)"]
            )
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return TimingResult(
                name=name,
                duration_seconds=0.0,
                tests_run=0,
                tests_passed=0,
                tests_failed=0,
                errors=[str(e)]
            )
    
    def _parse_test_counts(self, output: str) -> tuple[int, int, int]:
        """Parse test counts from pytest output."""
        # Look for patterns like "25 passed, 3 failed" or "50 passed"
        import re
        
        total = 0
        passed = 0
        failed = 0
        
        # Count passed
        passed_match = re.search(r'(\d+) passed', output)
        if passed_match:
            passed = int(passed_match.group(1))
            total += passed
        
        # Count failed
        failed_match = re.search(r'(\d+) failed', output)
        if failed_match:
            failed = int(failed_match.group(1))
            total += failed
        
        # If no matches found, try to find total
        if total == 0:
            total_match = re.search(r'collected (\d+) items', output)
            if total_match:
                total = int(total_match.group(1))
        
        return total, passed, failed
    
    def _parse_slow_tests(self, output: str) -> list[dict]:
        """Parse slow test information from pytest durations output."""
        import re
        
        slow_tests = []
        # Look for "10.23s test_name"
        pattern = r'([\d.]+)s\s+(.+)'
        
        # Find durations section
        lines = output.split('\n')
        in_durations = False
        
        for line in lines:
            if 'slowest durations' in line.lower():
                in_durations = True
                continue
            
            if in_durations:
                match = re.match(pattern, line.strip())
                if match:
                    duration = float(match.group(1))
                    test_name = match.group(2).strip()
                    if duration >= self.threshold:
                        slow_tests.append({
                            'name': test_name,
                            'duration': duration
                        })
        
        return slow_tests
    
    def _print_timing(self, result: TimingResult) -> None:
        """Print formatted timing results."""
        print(f"\n📊 RESULTS: {result.name}")
        print(f"   Duration: {result.duration_seconds:.2f}s")
        print(f"   Tests: {result.tests_run} run, {result.tests_passed} passed, {result.tests_failed} failed")
        print(f"   Avg/test: {result.avg_test_time:.3f}s")
        print(f"   Success: {result.success_rate:.1f}%")
        
        if result.slow_tests:
            print(f"\n🐌 SLOW TESTS (>{self.threshold}s):")
            for test in result.slow_tests[:5]:
                print(f"   {test['duration']:>6.2f}s  {test['name'][:50]}")
        
        if result.errors:
            print(f"\n❌ ERRORS:")
            for err in result.errors:
                print(f"   {err}")
    
    def time_unit_tests(self) -> TimingResult:
        """Time unit test suite."""
        return self.run_with_timing(
            "Unit Tests",
            ['python', '-m', 'pytest', 'tests/unit/', '-x', '--tb=short']
        )
    
    def time_integration_tests(self) -> TimingResult:
        """Time integration test suite."""
        return self.run_with_timing(
            "Integration Tests",
            ['python', '-m', 'pytest', 'tests/', '-m', 'integration', '-x', '--tb=short']
        )
    
    def time_e2e_tests(self) -> TimingResult:
        """Time E2E test suite."""
        return self.run_with_timing(
            "E2E Tests",
            ['python', '-m', 'pytest', 'tests/e2e/', '-x', '--tb=short']
        )
    
    def time_all_tests(self) -> TimingResult:
        """Time complete test suite."""
        return self.run_with_timing(
            "All Tests",
            ['python', '-m', 'pytest', 'tests/', '-x', '--tb=short', '--ignore=tests/perf']
        )
    
    def time_qa_agents(self) -> list[TimingResult]:
        """Time QA agent execution."""
        agents = [
            ('Code Quality Agent', ['python', '-m', 'qa.code_quality_agent']),
            ('Test Coverage Agent', ['python', '-m', 'qa.test_coverage_agent']),
            ('Security Audit Agent', ['python', '-m', 'qa.security_audit_agent']),
            ('Performance Agent', ['python', '-m', 'qa.performance_agent']),
            ('Documentation Agent', ['python', '-m', 'qa.documentation_agent']),
            ('Dependency Audit Agent', ['python', '-m', 'qa.dependency_audit_agent']),
        ]
        
        results = []
        for name, cmd in agents:
            # Modify command to run as script
            cmd = ['python', f'qa/{name.lower().replace(" ", "_")}.py']
            result = self.run_with_timing(name, cmd)
            results.append(result)
        
        return results
    
    def generate_summary(self) -> dict[str, Any]:
        """Generate summary of all timing results."""
        if not self.results:
            return {}
        
        total_duration = sum(r.duration_seconds for r in self.results)
        total_tests = sum(r.tests_run for r in self.results)
        total_passed = sum(r.tests_passed for r in self.results)
        
        all_slow_tests = []
        for r in self.results:
            all_slow_tests.extend(r.slow_tests)
        
        # Sort by duration descending
        all_slow_tests.sort(key=lambda x: -x['duration'])
        
        return {
            'total_duration_seconds': round(total_duration, 2),
            'total_duration_formatted': self._format_duration(total_duration),
            'total_tests': total_tests,
            'total_passed': total_passed,
            'success_rate': round(total_passed / max(total_tests, 1) * 100, 1),
            'slowest_tests': all_slow_tests[:10],
            'results': [asdict(r) for r in self.results]
        }
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable form."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    
    def print_summary(self) -> None:
        """Print final summary."""
        summary = self.generate_summary()
        
        print(f"\n{'='*60}")
        print("📊 FINAL TIMING SUMMARY")
        print('='*60)
        print(f"Total Duration: {summary.get('total_duration_formatted', 'N/A')}")
        print(f"Total Tests: {summary.get('total_tests', 0)}")
        print(f"Passed: {summary.get('total_passed', 0)} ({summary.get('success_rate', 0)}%)")
        
        if summary.get('slowest_tests'):
            print(f"\n🐌 TOP 10 SLOWEST TESTS:")
            for i, test in enumerate(summary['slowest_tests'][:10], 1):
                print(f"{i:>2}. {test['duration']:>6.2f}s  {test['name'][:45]}")
        
        # Speed grade
        avg_time = summary.get('total_duration_seconds', 0) / max(summary.get('total_tests', 1), 1)
        if avg_time < 0.01:
            grade = "A+ (Excellent)"
        elif avg_time < 0.1:
            grade = "A (Fast)"
        elif avg_time < 0.5:
            grade = "B (Good)"
        elif avg_time < 1.0:
            grade = "C (Acceptable)"
        else:
            grade = "D (Slow - needs optimization)"
        
        print(f"\n🏆 SPEED GRADE: {grade}")
        print(f"   Avg test time: {avg_time:.3f}s")
    
    def export_json(self, filename: str = "timing_report.json") -> None:
        """Export timing results to JSON."""
        summary = self.generate_summary()
        
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📄 Report exported to: {filename}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Time test execution')
    parser.add_argument('--unit-only', action='store_true', help='Time only unit tests')
    parser.add_argument('--integration-only', action='store_true', help='Time only integration tests')
    parser.add_argument('--e2e-only', action='store_true', help='Time only E2E tests')
    parser.add_argument('--agents', action='store_true', help='Time QA agent execution')
    parser.add_argument('--all', action='store_true', help='Time everything')
    parser.add_argument('--threshold', type=float, default=1.0, help='Slow test threshold in seconds')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--export', type=str, help='Export to JSON file')
    
    args = parser.parse_args()
    
    timer = TestTimer(threshold=args.threshold, json_output=args.json)
    
    # If no specific option, time all tests
    if not any([args.unit_only, args.integration_only, args.e2e_only, args.agents]):
        args.all = True
    
    if args.all or args.unit_only:
        result = timer.time_unit_tests()
        timer.results.append(result)
    
    if args.all or args.integration_only:
        result = timer.time_integration_tests()
        timer.results.append(result)
    
    if args.all or args.e2e_only:
        result = timer.time_e2e_tests()
        timer.results.append(result)
    
    if args.agents:
        agent_results = timer.time_qa_agents()
        timer.results.extend(agent_results)
    
    # Print summary
    timer.print_summary()
    
    # Export if requested
    if args.export:
        timer.export_json(args.export)
    
    # Return exit code based on success
    failed = sum(r.tests_failed for r in timer.results)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
