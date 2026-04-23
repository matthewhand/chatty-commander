#!/usr/bin/env python3
"""
RUN IMPLEMENTATION FLEET
Executes all 5 implementation agents and reports results.
"""

import subprocess
import sys
from pathlib import Path


class ImplementationFleet:
    """Runs all implementation agents."""
    
    def __init__(self):
        self.results = {}
    
    def run_agent(self, name: str, script: str) -> dict:
        """Run a single agent and capture results."""
        print(f"\n{'='*60}")
        print(f"🚀 RUNNING: {name}")
        print('='*60)
        
        try:
            result = subprocess.run(
                [sys.executable, script],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Print output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr[:500])
            
            # Parse result
            success = result.returncode == 0
            
            # Try to extract count from output
            output = result.stdout + result.stderr
            
            return {
                'name': name,
                'success': success,
                'output': output,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            print(f"❌ TIMEOUT: {name}")
            return {'name': name, 'success': False, 'error': 'timeout'}
        except Exception as e:
            print(f"❌ ERROR: {name} - {e}")
            return {'name': name, 'success': False, 'error': str(e)}
    
    def deploy(self):
        """Deploy all implementation agents."""
        print("\n" + "="*60)
        print("🚀 DEPLOYING IMPLEMENTATION FLEET")
        print("="*60)
        
        agents = [
            ("Docstring Agent", "qa/agents/docstring_implementation_agent.py"),
            ("Test Coverage Agent", "qa/agents/test_coverage_agent.py"),
            ("Comments Agent", "qa/agents/comments_agent.py"),
            ("Refactor Agent", "qa/agents/refactor_agent.py"),
            ("README Agent", "qa/agents/readme_agent.py"),
        ]
        
        for name, script in agents:
            if Path(script).exists():
                result = self.run_agent(name, script)
                self.results[name] = result
            else:
                print(f"❌ Script not found: {script}")
                self.results[name] = {'name': name, 'success': False, 'error': 'not found'}
        
        self.print_summary()
    
    def print_summary(self):
        """Print final summary."""
        print("\n" + "="*60)
        print("📊 FLEET EXECUTION SUMMARY")
        print("="*60)
        
        for name, result in self.results.items():
            status = "✅" if result.get('success') else "❌"
            print(f"{status} {name}")
        
        successful = sum(1 for r in self.results.values() if r.get('success'))
        print(f"\n{successful}/{len(self.results)} agents completed successfully")


def main():
    fleet = ImplementationFleet()
    fleet.deploy()
    return 0


if __name__ == "__main__":
    sys.exit(main())
