#!/usr/bin/env python3
"""
AGENT #1: CODE QUALITY AGENT
Analyzes code complexity, type coverage, and style compliance.

Scores:
- Complexity Score (0-100): Based on cyclomatic complexity
- Type Safety Score (0-100): Type annotation coverage
- Style Score (0-100): PEP8 compliance
- Overall: Weighted average

Priority Issues:
- Critical: Functions with complexity > 15
- High: Functions with complexity > 10
- Medium: Missing type annotations
- Low: Style violations
"""

from __future__ import annotations

import ast
import os
import re
import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any


class ComplexityAnalyzer(ast.NodeVisitor):
    """Analyze cyclomatic complexity of functions."""
    
    def __init__(self) -> None:
        self.functions: list[dict] = []
        self.current_function: str | None = None
        self.complexity: int = 0
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        old_function = self.current_function
        old_complexity = self.complexity
        
        self.current_function = node.name
        self.complexity = 1  # Base complexity
        
        # Count branches
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                self.complexity += 1
            elif isinstance(child, ast.BoolOp):
                self.complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                self.complexity += 1
        
        self.functions.append({
            'name': node.name,
            'line': node.lineno,
            'complexity': self.complexity
        })
        
        # Visit nested functions
        self.generic_visit(node)
        
        self.current_function = old_function
        self.complexity = old_complexity
    
    visit_AsyncFunctionDef = visit_FunctionDef


class CodeQualityAgent:
    """Analyzes code quality metrics."""
    
    PRIORITY_CRITICAL = "CRITICAL"
    PRIORITY_HIGH = "HIGH"
    PRIORITY_MEDIUM = "MEDIUM"
    PRIORITY_LOW = "LOW"
    
    def __init__(self, src_path: str = "src") -> None:
        self.src_path = Path(src_path)
        self.issues: list[dict] = []
        self.metrics: dict[str, Any] = {}
    
    def analyze(self) -> dict[str, Any]:
        """Run full analysis and return report."""
        print("🔍 AGENT #1: CODE QUALITY ANALYSIS")
        print("=" * 60)
        
        self._analyze_complexity()
        self._analyze_type_coverage()
        self._analyze_style()
        self._calculate_scores()
        
        return {
            'scores': self.metrics,
            'issues': self.issues,
            'priority_actions': self._get_priority_actions()
        }
    
    def _analyze_complexity(self) -> None:
        """Analyze cyclomatic complexity."""
        print("\n📊 Complexity Analysis...")
        
        high_complexity: list[dict] = []
        total_functions = 0
        total_complexity = 0
        
        for py_file in self.src_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                
                analyzer = ComplexityAnalyzer()
                analyzer.visit(tree)
                
                for func in analyzer.functions:
                    total_functions += 1
                    total_complexity += func['complexity']
                    
                    if func['complexity'] > 15:
                        high_complexity.append({
                            'file': str(py_file),
                            'function': func['name'],
                            'line': func['line'],
                            'complexity': func['complexity'],
                            'severity': 'CRITICAL'
                        })
                    elif func['complexity'] > 10:
                        high_complexity.append({
                            'file': str(py_file),
                            'function': func['name'],
                            'line': func['line'],
                            'complexity': func['complexity'],
                            'severity': 'HIGH'
                        })
            except SyntaxError:
                continue
        
        avg_complexity = total_complexity / total_functions if total_functions else 0
        
        self.metrics['complexity'] = {
            'total_functions': total_functions,
            'avg_complexity': round(avg_complexity, 2),
            'high_complexity_count': len(high_complexity),
            'score': max(0, 100 - len(high_complexity) * 5 - int(avg_complexity))
        }
        
        for item in high_complexity[:10]:  # Top 10
            self.issues.append({
                'priority': self.PRIORITY_CRITICAL if item['severity'] == 'CRITICAL' else self.PRIORITY_HIGH,
                'category': 'COMPLEXITY',
                'message': f"{item['function']}() has complexity {item['complexity']}",
                'file': item['file'],
                'line': item['line'],
                'suggestion': 'Refactor into smaller functions'
            })
        
        print(f"  ✓ Analyzed {total_functions} functions")
        print(f"  ⚠️  {len(high_complexity)} high-complexity functions found")
    
    def _analyze_type_coverage(self) -> None:
        """Analyze type annotation coverage."""
        print("\n📊 Type Coverage Analysis...")
        
        total_params = 0
        typed_params = 0
        total_returns = 0
        typed_returns = 0
        
        for py_file in self.src_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        total_returns += 1
                        if node.returns:
                            typed_returns += 1
                        
                        # Count parameters
                        args = node.args
                        for arg in args.args + args.kwonlyargs:
                            total_params += 1
                            if arg.annotation:
                                typed_params += 1
                        
                        if args.vararg and args.vararg.annotation:
                            typed_params += 1
                        if args.kwarg and args.kwarg.annotation:
                            typed_params += 1
            except SyntaxError:
                continue
        
        param_coverage = (typed_params / total_params * 100) if total_params else 0
        return_coverage = (typed_returns / total_returns * 100) if total_returns else 0
        overall = (param_coverage + return_coverage) / 2
        
        self.metrics['type_coverage'] = {
            'param_coverage': round(param_coverage, 1),
            'return_coverage': round(return_coverage, 1),
            'overall': round(overall, 1),
            'score': int(overall)
        }
        
        if overall < 70:
            self.issues.append({
                'priority': self.PRIORITY_MEDIUM,
                'category': 'TYPES',
                'message': f'Type coverage is {overall:.1f}%, target is 80%+',
                'suggestion': 'Add type annotations to public APIs'
            })
        
        print(f"  ✓ Parameter coverage: {param_coverage:.1f}%")
        print(f"  ✓ Return type coverage: {return_coverage:.1f}%")
        print(f"  ⚠️  Overall: {overall:.1f}%")
    
    def _analyze_style(self) -> None:
        """Analyze PEP8 style compliance."""
        print("\n📊 Style Analysis...")
        
        # Check for common style issues
        style_issues = []
        
        for py_file in self.src_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Lines > 100 chars
                    if len(line) > 100:
                        style_issues.append({
                            'file': str(py_file),
                            'line': i,
                            'issue': 'Line too long',
                            'detail': f'{len(line)} characters'
                        })
                    
                    # Trailing whitespace
                    if line.rstrip() != line.rstrip(' \t'):
                        style_issues.append({
                            'file': str(py_file),
                            'line': i,
                            'issue': 'Trailing whitespace',
                            'detail': ''
                        })
            except Exception:
                continue
        
        total_lines = sum(1 for f in self.src_path.rglob("*.py")
                         for _ in open(f, 'r', encoding='utf-8', errors='ignore'))
        
        score = max(0, 100 - len(style_issues))
        
        self.metrics['style'] = {
            'issues_found': len(style_issues),
            'score': score
        }
        
        for issue in style_issues[:5]:
            self.issues.append({
                'priority': self.PRIORITY_LOW,
                'category': 'STYLE',
                'message': f"{issue['issue']}: {issue.get('detail', '')}",
                'file': issue['file'],
                'line': issue['line'],
                'suggestion': 'Fix style violation'
            })
        
        print(f"  ✓ Analyzed {total_lines} lines")
        print(f"  ⚠️  {len(style_issues)} style issues found")
    
    def _calculate_scores(self) -> None:
        """Calculate overall quality score."""
        complexity_score = self.metrics['complexity']['score']
        type_score = self.metrics['type_coverage']['score']
        style_score = self.metrics['style']['score']
        
        # Weight: Complexity 40%, Types 40%, Style 20%
        overall = int(complexity_score * 0.4 + type_score * 0.4 + style_score * 0.2)
        
        self.metrics['overall'] = overall
        self.metrics['grade'] = self._score_to_grade(overall)
        
        print(f"\n📈 SCORES:")
        print(f"  Complexity Score: {complexity_score}/100")
        print(f"  Type Safety Score: {type_score}/100")
        print(f"  Style Score: {style_score}/100")
        print(f"  OVERALL: {overall}/100 ({self.metrics['grade']})")
    
    def _score_to_grade(self, score: int) -> str:
        if score >= 90: return 'A (Excellent)'
        if score >= 80: return 'B (Good)'
        if score >= 70: return 'C (Acceptable)'
        if score >= 60: return 'D (Needs Improvement)'
        return 'F (Critical)'
    
    def _get_priority_actions(self) -> list[dict]:
        """Get sorted priority actions."""
        priority_order = {
            self.PRIORITY_CRITICAL: 0,
            self.PRIORITY_HIGH: 1,
            self.PRIORITY_MEDIUM: 2,
            self.PRIORITY_LOW: 3
        }
        return sorted(self.issues, key=lambda x: priority_order.get(x['priority'], 4))
    
    def print_report(self) -> None:
        """Print formatted report."""
        report = self.analyze()
        
        print(f"\n🎯 PRIORITY ACTIONS (Top 10):")
        print("-" * 60)
        
        for i, issue in enumerate(report['priority_actions'][:10], 1):
            priority_emoji = {
                self.PRIORITY_CRITICAL: '🔴',
                self.PRIORITY_HIGH: '🟠',
                self.PRIORITY_MEDIUM: '🟡',
                self.PRIORITY_LOW: '🔵'
            }.get(issue['priority'], '⚪')
            
            print(f"\n{i}. {priority_emoji} [{issue['priority']}] {issue['category']}")
            print(f"   📍 {issue.get('file', 'N/A')}:{issue.get('line', 'N/A')}")
            print(f"   📝 {issue['message']}")
            print(f"   💡 {issue['suggestion']}")
        
        print(f"\n{'=' * 60}")


def main() -> int:
    agent = CodeQualityAgent(src_path="src/chatty_commander")
    agent.print_report()
    return 0 if agent.metrics.get('overall', 0) >= 60 else 1


if __name__ == "__main__":
    sys.exit(main())
