#!/usr/bin/env python3
"""
AGENT #5: DOCUMENTATION AGENT
Analyzes documentation completeness and quality.

Scores:
- API Documentation (0-100): Docstring coverage for public APIs
- README Quality (0-100): Installation, usage, examples
- Code Comments (0-100): Inline documentation quality
- Architecture Docs (0-100): Design and architecture documentation
- Overall: Weighted average

Priority Issues:
- Critical: Public functions with no documentation
- High: Missing installation/setup docs
- Medium: Undocumented complex logic
- Low: Typo, formatting issues
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any


class DocumentationAgent:
    """Analyzes documentation quality."""
    
    PRIORITY_CRITICAL = "CRITICAL"
    PRIORITY_HIGH = "HIGH"
    PRIORITY_MEDIUM = "MEDIUM"
    PRIORITY_LOW = "LOW"
    
    def __init__(self, src_path: str = "src", docs_path: str = ".") -> None:
        self.src_path = Path(src_path)
        self.docs_path = Path(docs_path)
        self.issues: list[dict] = []
        self.metrics: dict[str, Any] = {}
    
    def analyze(self) -> dict[str, Any]:
        """Run documentation analysis."""
        print("📚 AGENT #5: DOCUMENTATION ANALYSIS")
        print("=" * 60)
        
        self._analyze_docstrings()
        self._analyze_readme()
        self._analyze_code_comments()
        self._analyze_architecture_docs()
        self._calculate_scores()
        
        return {
            'scores': self.metrics,
            'issues': self.issues,
            'priority_docs': self._get_priority_docs()
        }
    
    def _analyze_docstrings(self) -> None:
        """Analyze docstring coverage."""
        print("\n📊 Docstring Analysis...")
        
        total_public = 0
        documented = 0
        undocumented: list[dict] = []
        
        for py_file in self.src_path.rglob("*.py"):
            # Skip private modules and tests
            if '/_' in str(py_file) or 'test' in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        # Skip private
                        if node.name.startswith('_'):
                            continue
                        
                        total_public += 1
                        
                        if ast.get_docstring(node):
                            documented += 1
                        else:
                            undocumented.append({
                                'file': str(py_file),
                                'line': node.lineno,
                                'name': node.name,
                                'type': 'function' if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else 'class'
                            })
            except SyntaxError:
                continue
        
        coverage = (documented / total_public * 100) if total_public else 0
        
        for item in undocumented[:15]:
            priority = self.PRIORITY_CRITICAL if item['type'] == 'class' else self.PRIORITY_HIGH
            self.issues.append({
                'priority': priority,
                'category': 'DOCSTRINGS',
                'file': item['file'],
                'line': item['line'],
                'name': item['name'],
                'type': item['type'],
                'issue': f"Missing docstring for {item['type']} '{item['name']}'",
                'suggestion': 'Add docstring with description, parameters, returns'
            })
        
        self.metrics['docstrings'] = {
            'total_public': total_public,
            'documented': documented,
            'coverage': round(coverage, 1),
            'score': int(coverage)
        }
        
        print(f"  ✓ {total_public} public symbols found")
        print(f"  ✓ {documented} have docstrings ({coverage:.1f}%)")
        print(f"  ⚠️  {len(undocumented)} missing docstrings")
    
    def _analyze_readme(self) -> None:
        """Analyze README completeness."""
        print("\n📊 README Analysis...")
        
        readme_files = list(self.docs_path.glob('README*'))
        
        if not readme_files:
            self.issues.append({
                'priority': self.PRIORITY_CRITICAL,
                'category': 'README',
                'issue': 'No README file found',
                'suggestion': 'Create README.md with project description'
            })
            self.metrics['readme'] = {'exists': False, 'score': 0}
            return
        
        readme = readme_files[0]
        
        with open(readme, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
        
        # Check for key sections
        required_sections = [
            ('installation', 'install', 'setup'),
            ('usage', 'how to use', 'getting started'),
            ('example', 'examples', 'quick start'),
        ]
        
        missing_sections = []
        for keywords in required_sections:
            if not any(kw in content for kw in keywords):
                missing_sections.append(keywords[0])
        
        for section in missing_sections:
            self.issues.append({
                'priority': self.PRIORITY_HIGH,
                'category': 'README',
                'issue': f'Missing {section} section',
                'suggestion': f'Add {section} documentation to README'
            })
        
        # Check length
        word_count = len(content.split())
        length_score = min(30, word_count / 100)
        
        completeness = (len(required_sections) - len(missing_sections)) / len(required_sections)
        score = int(completeness * 70 + length_score)
        
        self.metrics['readme'] = {
            'exists': True,
            'word_count': word_count,
            'missing_sections': missing_sections,
            'score': score
        }
        
        print(f"  ✓ README exists ({word_count} words)")
        print(f"  {'✓' if len(missing_sections) == 0 else '⚠️'} {len(missing_sections)} sections missing")
    
    def _analyze_code_comments(self) -> None:
        """Analyze inline code comments."""
        print("\n📊 Code Comment Analysis...")
        
        total_lines = 0
        comment_lines = 0
        complex_undocumented: list[dict] = []
        
        for py_file in self.src_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    total_lines += 1
                    
                    if stripped.startswith('#'):
                        comment_lines += 1
                    
                    # Check for complex logic without comments
                    if any(kw in line for kw in ['try:', 'except', 'if', 'for', 'while']):
                        # Check if there's a comment in nearby lines
                        context = lines[max(0, i-2):min(len(lines), i+3)]
                        if not any(l.strip().startswith('#') for l in context):
                            # Check complexity
                            indent = len(line) - len(line.lstrip())
                            if indent > 8:  # Nested logic
                                complex_undocumented.append({
                                    'file': str(py_file),
                                    'line': i,
                                    'code': line.strip()[:50]
                                })
            except Exception:
                continue
        
        comment_ratio = comment_lines / total_lines * 100 if total_lines else 0
        score = min(100, int(comment_ratio * 3))  # 30% comments = 100 score
        
        self.metrics['comments'] = {
            'total_lines': total_lines,
            'comment_lines': comment_lines,
            'ratio': round(comment_ratio, 2),
            'score': score
        }
        
        for item in complex_undocumented[:5]:
            self.issues.append({
                'priority': self.PRIORITY_MEDIUM,
                'category': 'COMMENTS',
                'file': item['file'],
                'line': item['line'],
                'issue': 'Complex logic without explanation',
                'code': item['code'],
                'suggestion': 'Add inline comment explaining logic'
            })
        
        print(f"  ✓ {comment_lines}/{total_lines} lines are comments ({comment_ratio:.1f}%)")
        print(f"  ⚠️  {len(complex_undocumented)} complex sections without comments")
    
    def _analyze_architecture_docs(self) -> None:
        """Check for architecture/design documentation."""
        print("\n📊 Architecture Documentation Analysis...")
        
        doc_files = [
            ('ARCHITECTURE.md', 'Architecture overview'),
            ('DESIGN.md', 'Design principles'),
            ('CONTRIBUTING.md', 'Contribution guidelines'),
            ('docs/', 'Documentation directory'),
        ]
        
        found = []
        missing = []
        
        for filename, description in doc_files:
            paths = list(self.docs_path.glob(filename))
            if paths:
                found.append((filename, description))
            else:
                missing.append((filename, description))
        
        for filename, description in missing:
            priority = self.PRIORITY_MEDIUM if 'ARCHITECTURE' in filename else self.PRIORITY_LOW
            self.issues.append({
                'priority': priority,
                'category': 'ARCHITECTURE',
                'issue': f'Missing {description}',
                'suggestion': f'Create {filename}'
            })
        
        score = int(len(found) / len(doc_files) * 100)
        
        self.metrics['architecture'] = {
            'found': len(found),
            'missing': len(missing),
            'score': score
        }
        
        print(f"  ✓ {len(found)}/{len(doc_files)} architecture docs present")
    
    def _calculate_scores(self) -> None:
        """Calculate overall documentation score."""
        scores = [
            self.metrics.get('docstrings', {}).get('score', 0),
            self.metrics.get('readme', {}).get('score', 0),
            self.metrics.get('comments', {}).get('score', 0),
            self.metrics.get('architecture', {}).get('score', 0),
        ]
        
        # Weight: Docstrings 40%, README 30%, Comments 20%, Architecture 10%
        overall = int(
            scores[0] * 0.4 +
            scores[1] * 0.3 +
            scores[2] * 0.2 +
            scores[3] * 0.1
        )
        
        self.metrics['overall'] = overall
        self.metrics['grade'] = self._score_to_grade(overall)
        
        print(f"\n📈 DOCUMENTATION SCORES:")
        print(f"  Docstrings: {scores[0]}/100")
        print(f"  README: {scores[1]}/100")
        print(f"  Code Comments: {scores[2]}/100")
        print(f"  Architecture: {scores[3]}/100")
        print(f"  OVERALL: {overall}/100 ({self.metrics['grade']})")
    
    def _get_priority_docs(self) -> list[dict]:
        """Get sorted priority documentation tasks."""
        priority_order = {
            self.PRIORITY_CRITICAL: 0,
            self.PRIORITY_HIGH: 1,
            self.PRIORITY_MEDIUM: 2,
            self.PRIORITY_LOW: 3
        }
        return sorted(self.issues, key=lambda x: priority_order.get(x['priority'], 4))
    
    def _score_to_grade(self, score: int) -> str:
        if score >= 90: return 'A (Excellent)'
        if score >= 80: return 'B (Good)'
        if score >= 70: return 'C (Acceptable)'
        if score >= 60: return 'D (Needs Documentation)'
        return 'F (Undocumented)'
    
    def print_report(self) -> None:
        """Print formatted report."""
        report = self.analyze()
        
        print(f"\n🎯 DOCUMENTATION PRIORITIES (Top 10):")
        print("-" * 60)
        
        for i, issue in enumerate(report['priority_docs'][:10], 1):
            priority_emoji = {
                self.PRIORITY_CRITICAL: '🔴',
                self.PRIORITY_HIGH: '🟠',
                self.PRIORITY_MEDIUM: '🟡',
                self.PRIORITY_LOW: '🔵'
            }.get(issue['priority'], '⚪')
            
            print(f"\n{i}. {priority_emoji} [{issue['priority']}] {issue['category']}")
            if 'file' in issue:
                print(f"   📍 {issue['file']}:{issue.get('line', 'N/A')}")
            if 'name' in issue:
                print(f"   📝 {issue['name']}")
            else:
                print(f"   📝 {issue['issue']}")
            print(f"   💡 {issue['suggestion']}")
        
        print(f"\n{'=' * 60}")


def main():
    agent = DocumentationAgent(
        src_path="src/chatty_commander",
        docs_path="/home/matthewh/chatty-commander"
    )
    agent.print_report()
    return 0 if agent.metrics.get('overall', 0) >= 60 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
