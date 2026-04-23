#!/usr/bin/env python3
"""
AGENT #2: TEST COVERAGE AGENT
Analyzes test coverage gaps and prioritizes testing needs.

Scores:
- Line Coverage Score (0-100): % of lines covered
- Branch Coverage Score (0-100): % of branches covered
- Module Coverage Score (0-100): % of modules with tests
- Test Quality Score (0-100): Assorted quality metrics

Priority Gaps:
- Critical: Core business logic with 0% coverage
- High: Modules with <50% coverage
- Medium: Modules with <80% coverage
- Low: Missing edge case tests
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


class CoverageAnalyzer:
    """Analyzes test coverage across the codebase."""
    
    PRIORITY_CRITICAL = "CRITICAL"
    PRIORITY_HIGH = "HIGH"
    PRIORITY_MEDIUM = "MEDIUM"
    PRIORITY_LOW = "LOW"
    
    def __init__(self, src_path: str = "src", test_path: str = "tests") -> None:
        self.src_path = Path(src_path)
        self.test_path = Path(test_path)
        self.gaps: list[dict] = []
        self.metrics: dict[str, Any] = {}
    
    def analyze(self) -> dict[str, Any]:
        """Run full coverage analysis."""
        print("🧪 AGENT #2: TEST COVERAGE ANALYSIS")
        print("=" * 60)
        
        self._analyze_module_coverage()
        self._analyze_test_quality()
        self._analyze_coverage_depth()
        self._identify_gaps()
        self._calculate_scores()
        
        return {
            'scores': self.metrics,
            'gaps': self.gaps,
            'priority_tests': self._get_priority_tests()
        }
    
    def _analyze_module_coverage(self) -> None:
        """Analyze which modules have corresponding tests."""
        print("\n📊 Module Coverage Analysis...")
        
        # Find all source modules
        src_modules: dict[str, Path] = {}
        for py_file in self.src_path.rglob("*.py"):
            if py_file.name.startswith('_'):
                continue
            module_name = self._path_to_module(py_file)
            src_modules[module_name] = py_file
        
        # Find tested modules
        test_modules: set[str] = set()
        test_patterns = ['test_', 'test']
        
        for py_file in self.test_path.rglob("*.py"):
            if any(py_file.name.startswith(p) for p in test_patterns):
                # Parse test file to find what's being tested
                tested = self._extract_tested_modules(py_file)
                test_modules.update(tested)
        
        # Calculate coverage
        total_modules = len(src_modules)
        tested_count = len(set(src_modules.keys()) & test_modules)
        
        self.metrics['module_coverage'] = {
            'total': total_modules,
            'tested': tested_count,
            'percentage': round(tested_count / total_modules * 100, 1) if total_modules else 0,
            'score': int(tested_count / total_modules * 100) if total_modules else 0
        }
        
        # Identify untested modules
        for module, path in src_modules.items():
            if module not in test_modules:
                # Determine priority based on module importance
                priority = self._determine_module_priority(path)
                self.gaps.append({
                    'priority': priority,
                    'module': module,
                    'file': str(path),
                    'issue': 'No tests found',
                    'suggestion': f'Create tests/test_{path.stem}.py'
                })
        
        print(f"  ✓ {total_modules} source modules found")
        print(f"  ✓ {tested_count} modules have tests ({self.metrics['module_coverage']['percentage']}%)")
        print(f"  ⚠️  {total_modules - tested_count} modules need tests")
    
    def _analyze_test_quality(self) -> None:
        """Analyze test file quality metrics."""
        print("\n📊 Test Quality Analysis...")
        
        total_tests = 0
        test_classes = 0
        test_functions = 0
        fixtures = 0
        mocks = 0
        assertions = 0
        
        for py_file in self.test_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if node.name.startswith('Test'):
                            test_classes += 1
                            total_tests += len([n for n in node.body 
                                              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                                              and n.name.startswith('test_')])
                    elif isinstance(node, ast.FunctionDef):
                        if node.name.startswith('test_'):
                            test_functions += 1
                            total_tests += 1
                    
                    # Count fixtures
                    if isinstance(node, ast.FunctionDef):
                        if any(decorator.id == 'pytest_fixture' if isinstance(decorator, ast.Name) else 
                               (decorator.attr == 'fixture' if hasattr(decorator, 'attr') else False)
                               for decorator in node.decorator_list):
                            fixtures += 1
                
                # Count mocks and assertions (approximate)
                mocks += content.count('Mock(') + content.count('MagicMock')
                assertions += content.count('assert ')
            except SyntaxError:
                continue
        
        # Calculate quality score
        # Factors: tests per class, assertion density, mock usage
        avg_tests_per_class = total_tests / test_classes if test_classes else 0
        assertion_density = assertions / total_tests if total_tests else 0
        
        quality_score = min(100, int(
            30 +  # Base score
            min(30, avg_tests_per_class * 5) +  # Tests per class
            min(30, assertion_density * 10) +  # Assertions per test
            min(10, fixtures)  # Fixture usage
        ))
        
        self.metrics['test_quality'] = {
            'total_tests': total_tests,
            'test_classes': test_classes,
            'test_functions': test_functions,
            'fixtures': fixtures,
            'mocks': mocks,
            'assertions': assertions,
            'avg_tests_per_class': round(avg_tests_per_class, 1),
            'assertion_density': round(assertion_density, 2),
            'score': quality_score
        }
        
        print(f"  ✓ {total_tests} total tests")
        print(f"  ✓ {test_classes} test classes")
        print(f"  ✓ {fixtures} fixtures defined")
        print(f"  ✓ {assertions} assertions")
        print(f"  ✓ {mocks} mock usages")
    
    def _analyze_coverage_depth(self) -> None:
        """Analyze depth of test coverage."""
        print("\n📊 Coverage Depth Analysis...")
        
        test_types = {
            'unit': 0,
            'integration': 0,
            'e2e': 0,
            'property': 0,
            'parametrized': 0
        }
        
        for py_file in self.test_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                path_str = str(py_file)
                if '/e2e/' in path_str or 'e2e' in py_file.name:
                    test_types['e2e'] += content.count('def test_')
                elif '/integration/' in path_str or 'integration' in py_file.name:
                    test_types['integration'] += content.count('def test_')
                elif 'property' in py_file.name:
                    test_types['property'] += content.count('def test_')
                else:
                    test_types['unit'] += content.count('def test_')
                
                # Check for parametrized tests
                if '@pytest.mark.parametrize' in content:
                    test_types['parametrized'] += content.count('@pytest.mark.parametrize')
            except Exception:
                continue
        
        # Calculate depth score
        # Ideal: 70% unit, 20% integration, 10% e2e, 10% property/parametrized
        total = sum(test_types.values())
        if total > 0:
            balance_score = 100 - abs(70 - test_types['unit'] / total * 100) * 0.5
        else:
            balance_score = 0
        
        depth_score = min(100, test_types['parametrized'] * 5 + test_types['property'] * 10 + 50)
        
        self.metrics['coverage_depth'] = {
            'by_type': test_types,
            'balance_score': round(balance_score, 1),
            'depth_score': depth_score,
            'score': int((balance_score + depth_score) / 2)
        }
        
        print(f"  ✓ Unit tests: {test_types['unit']}")
        print(f"  ✓ Integration tests: {test_types['integration']}")
        print(f"  ✓ E2E tests: {test_types['e2e']}")
        print(f"  ✓ Parametrized tests: {test_types['parametrized']}")
        print(f"  ⚠️  Balance score: {balance_score:.1f}")
    
    def _identify_gaps(self) -> None:
        """Identify specific test coverage gaps."""
        print("\n📊 Gap Identification...")
        
        # Check for common missing test patterns
        critical_patterns = [
            ('error_handling', 'Error handling paths'),
            ('concurrent', 'Concurrency/thread safety'),
            ('security', 'Security controls'),
            ('boundary', 'Boundary conditions'),
            ('performance', 'Performance characteristics')
        ]
        
        for pattern, description in critical_patterns:
            found = False
            for py_file in self.test_path.rglob("*.py"):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        if pattern in f.read().lower():
                            found = True
                            break
                except Exception:
                    continue
            
            if not found:
                priority = self.PRIORITY_HIGH if pattern in ['error_handling', 'security'] else self.PRIORITY_MEDIUM
                self.gaps.append({
                    'priority': priority,
                    'category': 'MISSING_PATTERN',
                    'issue': f'{description} tests',
                    'suggestion': f'Add {pattern} test cases'
                })
    
    def _calculate_scores(self) -> None:
        """Calculate overall coverage score."""
        module_score = self.metrics['module_coverage']['score']
        quality_score = self.metrics['test_quality']['score']
        depth_score = self.metrics['coverage_depth']['score']
        
        # Weight: Module 40%, Quality 30%, Depth 30%
        overall = int(module_score * 0.4 + quality_score * 0.3 + depth_score * 0.3)
        
        self.metrics['overall'] = overall
        self.metrics['grade'] = self._score_to_grade(overall)
        
        print(f"\n📈 SCORES:")
        print(f"  Module Coverage: {module_score}/100")
        print(f"  Test Quality: {quality_score}/100")
        print(f"  Coverage Depth: {depth_score}/100")
        print(f"  OVERALL: {overall}/100 ({self.metrics['grade']})")
    
    def _get_priority_tests(self) -> list[dict]:
        """Get sorted priority test recommendations."""
        priority_order = {
            self.PRIORITY_CRITICAL: 0,
            self.PRIORITY_HIGH: 1,
            self.PRIORITY_MEDIUM: 2,
            self.PRIORITY_LOW: 3
        }
        return sorted(self.gaps, key=lambda x: priority_order.get(x['priority'], 4))
    
    def _path_to_module(self, path: Path) -> str:
        """Convert path to module name."""
        rel = path.relative_to(self.src_path)
        return str(rel.with_suffix('')).replace('/', '.').replace('\\', '.')
    
    def _extract_tested_modules(self, test_file: Path) -> set[str]:
        """Extract module names tested by a test file."""
        tested = set()
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for import patterns
            for line in content.split('\n'):
                if 'from chatty_commander' in line or 'from src.chatty_commander' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part in ['from', 'import'] and i + 1 < len(parts):
                            module = parts[i + 1].rstrip(',;')
                            if '.' in module:
                                tested.add(module)
        except Exception:
            pass
        
        return tested
    
    def _determine_module_priority(self, path: Path) -> str:
        """Determine test priority for a module."""
        path_str = str(path)
        
        # Critical: Core business logic
        if any(x in path_str for x in ['cli.py', 'command_executor.py', 'state_manager.py']):
            return self.PRIORITY_CRITICAL
        
        # High: Important modules
        if any(x in path_str for x in ['llm/', 'voice/', 'web/']):
            return self.PRIORITY_HIGH
        
        # Medium: Other functionality
        return self.PRIORITY_MEDIUM
    
    def _score_to_grade(self, score: int) -> str:
        if score >= 90: return 'A (Excellent)'
        if score >= 80: return 'B (Good)'
        if score >= 70: return 'C (Acceptable)'
        if score >= 60: return 'D (Needs Improvement)'
        return 'F (Critical)'
    
    def print_report(self) -> None:
        """Print formatted report."""
        report = self.analyze()
        
        print(f"\n🎯 PRIORITY TESTS (Top 10):")
        print("-" * 60)
        
        for i, gap in enumerate(report['priority_tests'][:10], 1):
            priority_emoji = {
                self.PRIORITY_CRITICAL: '🔴',
                self.PRIORITY_HIGH: '🟠',
                self.PRIORITY_MEDIUM: '🟡',
                self.PRIORITY_LOW: '🔵'
            }.get(gap['priority'], '⚪')
            
            print(f"\n{i}. {priority_emoji} [{gap['priority']}] {gap.get('module', gap.get('category', 'TEST'))}")
            if 'file' in gap:
                print(f"   📍 {gap['file']}")
            print(f"   📝 {gap['issue']}")
            print(f"   💡 {gap['suggestion']}")
        
        print(f"\n{'=' * 60}")


def main() -> int:
    agent = CoverageAnalyzer(
        src_path="src/chatty_commander",
        test_path="tests"
    )
    agent.print_report()
    return 0 if agent.metrics.get('overall', 0) >= 60 else 1


if __name__ == "__main__":
    sys.exit(main())
