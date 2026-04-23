#!/usr/bin/env python3
"""
AGENT #4: PERFORMANCE AGENT
Benchmarks critical paths and identifies performance bottlenecks.

Scores:
- Startup Time (0-100): Application initialization speed
- Memory Efficiency (0-100): Memory usage patterns
- Algorithmic Complexity (0-100): Big O analysis
- I/O Efficiency (0-100): File/network operation patterns
- Overall: Weighted average

Priority Issues:
- Critical: O(n^2+) algorithms on large data
- High: Memory leaks, blocking I/O
- Medium: Excessive object creation
- Low: Micro-optimizations
"""

from __future__ import annotations

import ast
import re
import time
from pathlib import Path
from typing import Any


class PerformanceAgent:
    """Analyzes performance characteristics."""
    
    PRIORITY_CRITICAL = "CRITICAL"
    PRIORITY_HIGH = "HIGH"
    PRIORITY_MEDIUM = "MEDIUM"
    PRIORITY_LOW = "LOW"
    
    def __init__(self, src_path: str = "src") -> None:
        self.src_path = Path(src_path)
        self.issues: list[dict] = []
        self.metrics: dict[str, Any] = {}
    
    def analyze(self) -> dict[str, Any]:
        """Run performance analysis."""
        print("⚡ AGENT #4: PERFORMANCE ANALYSIS")
        print("=" * 60)
        
        self._analyze_algorithmic_complexity()
        self._analyze_memory_patterns()
        self._analyze_io_patterns()
        self._analyze_startup_time()
        self._calculate_scores()
        
        return {
            'scores': self.metrics,
            'issues': self.issues,
            'priority_optimizations': self._get_priority_optimizations()
        }
    
    def _analyze_algorithmic_complexity(self) -> None:
        """Analyze algorithmic complexity patterns."""
        print("\n📊 Algorithmic Complexity Analysis...")
        
        problematic_patterns = []
        
        for py_file in self.src_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    # Nested loops (potential O(n^2))
                    if re.search(r'^\s+for.*:$', line):
                        # Check for nested loops in context
                        indent = len(line) - len(line.lstrip())
                        next_lines = lines[line_num:line_num+20]
                        for nl in next_lines:
                            if re.search(r'^\s+for.*:$', nl):
                                nl_indent = len(nl) - len(nl.lstrip())
                                if nl_indent > indent:
                                    problematic_patterns.append({
                                        'file': str(py_file),
                                        'line': line_num,
                                        'pattern': 'Nested loop',
                                        'complexity': 'O(n^2) or worse'
                                    })
                                    break
                    
                    # String concatenation in loops
                    if 'for' in line and line_num > 1:
                        context = '\n'.join(lines[line_num-1:line_num+5])
                        if re.search(r'\w+\s*\+\s*=\s*', context) and '"' in context:
                            problematic_patterns.append({
                                'file': str(py_file),
                                'line': line_num,
                                'pattern': 'String concatenation in loop',
                                'complexity': 'O(n^2)'
                            })
                    
                    # List/dict lookups in loops
                    if 'for' in line and 'keys()' in line:
                        problematic_patterns.append({
                            'file': str(py_file),
                            'line': line_num,
                            'pattern': 'Unnecessary .keys() in iteration',
                            'complexity': 'Inefficient'
                        })
            except Exception:
                continue
        
        for issue in problematic_patterns[:10]:
            priority = self.PRIORITY_HIGH if 'n^2' in issue['complexity'] else self.PRIORITY_MEDIUM
            self.issues.append({
                'priority': priority,
                'category': 'ALGORITHM',
                'file': issue['file'],
                'line': issue['line'],
                'pattern': issue['pattern'],
                'complexity': issue['complexity'],
                'suggestion': 'Consider more efficient data structures or algorithms'
            })
        
        score = max(0, 100 - len(problematic_patterns) * 5)
        self.metrics['algorithmic'] = {
            'issues': len(problematic_patterns),
            'score': score
        }
        
        print(f"  {'✓' if len(problematic_patterns) < 5 else '⚠️'} {len(problematic_patterns)} complexity issues")
    
    def _analyze_memory_patterns(self) -> None:
        """Analyze memory usage patterns."""
        print("\n📊 Memory Pattern Analysis...")
        
        issues = []
        
        for py_file in self.src_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Large list comprehensions
                if re.search(r'\[.*for.*in.*if.*\]', content):
                    if len(re.findall(r'for.*in.*if', content)) > 3:
                        issues.append({
                            'file': str(py_file),
                            'issue': 'Complex list comprehension',
                            'suggestion': 'Consider generator expression'
                        })
                
                # Loading large files into memory
                if 'read()' in content and 'open(' in content:
                    issues.append({
                        'file': str(py_file),
                        'issue': 'Potential large file loading',
                        'suggestion': 'Use chunking or streaming for large files'
                    })
                
                # Creating large data structures
                if re.search(r'range\(\s*\d{5,}\s*\)', content):
                    issues.append({
                        'file': str(py_file),
                        'issue': 'Large range operation',
                        'suggestion': 'Consider lazy evaluation'
                    })
            except Exception:
                continue
        
        for issue in issues[:5]:
            self.issues.append({
                'priority': self.PRIORITY_MEDIUM,
                'category': 'MEMORY',
                'file': issue['file'],
                'issue': issue['issue'],
                'suggestion': issue['suggestion']
            })
        
        score = max(0, 100 - len(issues) * 5)
        self.metrics['memory'] = {
            'issues': len(issues),
            'score': score
        }
        
        print(f"  {'✓' if len(issues) < 5 else '⚠️'} {len(issues)} memory concerns")
    
    def _analyze_io_patterns(self) -> None:
        """Analyze I/O patterns."""
        print("\n📊 I/O Pattern Analysis...")
        
        issues = []
        sync_ops = []
        
        for py_file in self.src_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    # Synchronous I/O in async context
                    if 'async def' in line:
                        # Check context for blocking calls
                        context = '\n'.join(lines[line_num:line_num+50])
                        if 'requests.get' in context or 'urllib' in context:
                            issues.append({
                                'file': str(py_file),
                                'line': line_num,
                                'issue': 'Blocking I/O in async function',
                                'suggestion': 'Use aiohttp or httpx.AsyncClient'
                            })
                
                # File operations without context managers
                if 'open(' in content and 'with open' not in content:
                    sync_ops.append(str(py_file))
            except Exception:
                continue
        
        for issue in issues[:5]:
            self.issues.append({
                'priority': self.PRIORITY_HIGH,
                'category': 'I/O',
                'file': issue['file'],
                'line': issue['line'],
                'issue': issue['issue'],
                'suggestion': issue['suggestion']
            })
        
        score = max(0, 100 - len(issues) * 10)
        self.metrics['io'] = {
            'blocking_issues': len(issues),
            'sync_operations': len(sync_ops),
            'score': score
        }
        
        print(f"  {'✓' if len(issues) == 0 else '⚠️'} {len(issues)} blocking I/O issues")
        print(f"  ℹ️ {len(sync_ops)} files with sync operations")
    
    def _analyze_startup_time(self) -> None:
        """Estimate startup time impact."""
        print("\n📊 Startup Time Analysis...")
        
        heavy_imports = []
        global_state = []
        
        for py_file in self.src_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for heavy imports at module level
                heavy_modules = ['torch', 'tensorflow', 'numpy', 'pandas', 'transformers']
                for mod in heavy_modules:
                    if f'import {mod}' in content or f'from {mod}' in content:
                        heavy_imports.append((mod, str(py_file)))
                
                # Global state initialization
                if re.search(r'^[A-Z_]+\s*=\s*', content, re.MULTILINE):
                    global_state.append(str(py_file))
            except Exception:
                continue
        
        score = max(0, 100 - len(heavy_imports) * 5 - len(global_state) * 2)
        
        self.metrics['startup'] = {
            'heavy_imports': len(heavy_imports),
            'global_init': len(global_state),
            'score': score
        }
        
        print(f"  ℹ️ {len(heavy_imports)} heavy imports detected")
        print(f"  ℹ️ {len(global_state)} files with global state")
    
    def _calculate_scores(self) -> None:
        """Calculate overall performance score."""
        scores = [
            self.metrics.get('algorithmic', {}).get('score', 0),
            self.metrics.get('memory', {}).get('score', 0),
            self.metrics.get('io', {}).get('score', 0),
            self.metrics.get('startup', {}).get('score', 0),
        ]
        
        overall = int(sum(scores) / len(scores))
        
        self.metrics['overall'] = overall
        self.metrics['rating'] = self._score_to_rating(overall)
        
        print(f"\n📈 PERFORMANCE SCORES:")
        print(f"  Algorithmic: {scores[0]}/100")
        print(f"  Memory: {scores[1]}/100")
        print(f"  I/O: {scores[2]}/100")
        print(f"  Startup: {scores[3]}/100")
        print(f"  OVERALL: {overall}/100 ({self.metrics['rating']})")
    
    def _get_priority_optimizations(self) -> list[dict]:
        """Get sorted priority optimizations."""
        priority_order = {
            self.PRIORITY_CRITICAL: 0,
            self.PRIORITY_HIGH: 1,
            self.PRIORITY_MEDIUM: 2,
            self.PRIORITY_LOW: 3
        }
        return sorted(self.issues, key=lambda x: priority_order.get(x['priority'], 4))
    
    def _score_to_rating(self, score: int) -> str:
        if score >= 90: return 'A (Excellent)'
        if score >= 80: return 'B (Good)'
        if score >= 70: return 'C (Acceptable)'
        if score >= 60: return 'D (Needs Optimization)'
        return 'F (Critical)'
    
    def print_report(self) -> None:
        """Print formatted report."""
        report = self.analyze()
        
        print(f"\n🎯 PERFORMANCE PRIORITIES (Top 10):")
        print("-" * 60)
        
        for i, issue in enumerate(report['priority_optimizations'][:10], 1):
            priority_emoji = {
                self.PRIORITY_CRITICAL: '🔴',
                self.PRIORITY_HIGH: '🟠',
                self.PRIORITY_MEDIUM: '🟡',
                self.PRIORITY_LOW: '🔵'
            }.get(issue['priority'], '⚪')
            
            print(f"\n{i}. {priority_emoji} [{issue['priority']}] {issue['category']}")
            if 'file' in issue:
                print(f"   📍 {issue['file']}:{issue.get('line', 'N/A')}")
            print(f"   📝 {issue.get('pattern', issue.get('issue', 'Issue'))}")
            print(f"   💡 {issue['suggestion']}")
        
        print(f"\n{'=' * 60}")


def main():
    agent = PerformanceAgent(src_path="src/chatty_commander")
    agent.print_report()
    return 0 if agent.metrics.get('overall', 0) >= 60 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
