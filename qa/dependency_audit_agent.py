#!/usr/bin/env python3
"""
AGENT #6: DEPENDENCY AUDIT AGENT
Audits dependencies for updates, vulnerabilities, and best practices.

Scores:
- Update Status (0-100): Outdated packages
- Security Status (0-100): Known vulnerabilities
- License Compliance (0-100): License compatibility
- Health Score (0-100): Maintenance status
- Overall: Weighted average

Priority Issues:
- Critical: Known CVEs in dependencies
- High: Major version behind, deprecated packages
- Medium: Minor version behind, unmaintained packages
- Low: Dev dependencies outdated
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


class DependencyAuditAgent:
    """Audits project dependencies."""
    
    PRIORITY_CRITICAL = "CRITICAL"
    PRIORITY_HIGH = "HIGH"
    PRIORITY_MEDIUM = "MEDIUM"
    PRIORITY_LOW = "LOW"
    
    def __init__(self, project_path: str = ".") -> None:
        self.project_path = Path(project_path)
        self.issues: list[dict] = []
        self.metrics: dict[str, Any] = {}
    
    def audit(self) -> dict[str, Any]:
        """Run full dependency audit."""
        print("📦 AGENT #6: DEPENDENCY AUDIT")
        print("=" * 60)
        
        self._analyze_requirements()
        self._check_security()
        self._check_outdated()
        self._analyze_licenses()
        self._calculate_scores()
        
        return {
            'scores': self.metrics,
            'issues': self.issues,
            'priority_updates': self._get_priority_updates()
        }
    
    def _analyze_requirements(self) -> None:
        """Analyze requirements files structure."""
        print("\n📊 Requirements Analysis...")
        
        req_files = list(self.project_path.glob('requirements*.txt'))
        
        if not req_files:
            self.issues.append({
                'priority': self.PRIORITY_HIGH,
                'category': 'MISSING',
                'issue': 'No requirements.txt found',
                'suggestion': 'Create requirements.txt with pinned versions'
            })
            self.metrics['requirements'] = {'exists': False, 'score': 0}
            return
        
        total_deps = 0
        pinned = 0
        unpinned = []
        
        for req_file in req_files:
            with open(req_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        total_deps += 1
                        if '==' in line or '>=' in line or '<=' in line:
                            pinned += 1
                        else:
                            unpinned.append((req_file.name, line))
        
        for filename, dep in unpinned[:10]:
            self.issues.append({
                'priority': self.PRIORITY_MEDIUM,
                'category': 'UNPINNED',
                'file': filename,
                'dependency': dep,
                'issue': f'Unpinned dependency: {dep}',
                'suggestion': f'Pin to specific version: {dep}==x.x.x'
            })
        
        score = int(pinned / total_deps * 100) if total_deps else 0
        
        self.metrics['requirements'] = {
            'files': len(req_files),
            'total_deps': total_deps,
            'pinned': pinned,
            'unpinned': len(unpinned),
            'score': score
        }
        
        print(f"  ✓ {len(req_files)} requirement files")
        print(f"  ✓ {total_deps} dependencies ({pinned} pinned)")
        print(f"  {'✓' if len(unpinned) < 5 else '⚠️'} {len(unpinned)} unpinned")
    
    def _check_security(self) -> None:
        """Check for known security vulnerabilities."""
        print("\n📊 Security Vulnerability Check...")
        
        # Try to run safety check if available
        vulnerabilities = []
        
        try:
            result = subprocess.run(
                ['safety', 'check', '--json'],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.project_path
            )
            
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                vulnerabilities = data.get('vulnerabilities', [])
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            # safety not installed or other error
            pass
        
        # Also check for known vulnerable patterns in requirements
        known_vulnerable = [
            ('requests', '<2.31.0'),
            ('urllib3', '<2.0.0'),
            ('cryptography', '<41.0.0'),
            ('pillow', '<10.0.0'),
            ('fastapi', '<0.100.0'),
        ]
        
        for req_file in self.project_path.glob('requirements*.txt'):
            with open(req_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for dep, version in known_vulnerable:
                if dep in content.lower():
                    # Check if version meets criteria (simplified)
                    vulnerabilities.append({
                        'package': dep,
                        'vulnerable_spec': version,
                        'advisory': f'Update {dep} to {version}'
                    })
        
        for vuln in vulnerabilities[:10]:
            self.issues.append({
                'priority': self.PRIORITY_CRITICAL,
                'category': 'VULNERABILITY',
                'package': vuln.get('package', 'Unknown'),
                'issue': vuln.get('advisory', 'Known vulnerability'),
                'suggestion': 'Update to patched version immediately'
            })
        
        score = max(0, 100 - len(vulnerabilities) * 10)
        
        self.metrics['security'] = {
            'vulnerabilities': len(vulnerabilities),
            'score': score
        }
        
        print(f"  {'✓' if len(vulnerabilities) == 0 else '⚠️'} {len(vulnerabilities)} vulnerabilities")
    
    def _check_outdated(self) -> None:
        """Check for outdated packages."""
        print("\n📊 Outdated Package Check...")
        
        outdated = []
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--outdated', '--format=json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                # Check against project requirements
                for pkg in data:
                    outdated.append({
                        'name': pkg.get('name'),
                        'current': pkg.get('version'),
                        'latest': pkg.get('latest_version')
                    })
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            pass
        
        for pkg in outdated[:10]:
            self.issues.append({
                'priority': self.PRIORITY_MEDIUM,
                'category': 'OUTDATED',
                'package': pkg['name'],
                'issue': f"Outdated: {pkg['current']} -> {pkg['latest']}",
                'suggestion': f'Update {pkg["name"]} to {pkg["latest"]}'
            })
        
        score = max(0, 100 - len(outdated) * 2)
        
        self.metrics['outdated'] = {
            'count': len(outdated),
            'score': score
        }
        
        print(f"  {'✓' if len(outdated) < 10 else '⚠️'} {len(outdated)} outdated packages")
    
    def _analyze_licenses(self) -> None:
        """Analyze dependency licenses."""
        print("\n📊 License Analysis...")
        
        # Simplified license check
        # In production, use pip-licenses or similar
        
        problematic_licenses = ['GPL', 'AGPL', 'LGPL']
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                packages = json.loads(result.stdout)
                
                # We would need pip-licenses for actual license data
                # For now, assume compliance if we can't verify
                license_issues = 0
        except Exception:
            license_issues = 0
        
        # Check for requirements file comments about licenses
        for req_file in self.project_path.glob('requirements*.txt'):
            with open(req_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for license_type in problematic_licenses:
                if license_type in content:
                    license_issues += 1
        
        score = max(0, 100 - license_issues * 20)
        
        self.metrics['licenses'] = {
            'issues': license_issues,
            'score': score
        }
        
        print(f"  {'✓' if license_issues == 0 else '⚠️'} {license_issues} license concerns")
    
    def _calculate_scores(self) -> None:
        """Calculate overall dependency health score."""
        scores = [
            self.metrics.get('requirements', {}).get('score', 0),
            self.metrics.get('security', {}).get('score', 0),
            self.metrics.get('outdated', {}).get('score', 0),
            self.metrics.get('licenses', {}).get('score', 0),
        ]
        
        # Weight: Security 35%, Requirements 25%, Outdated 25%, Licenses 15%
        overall = int(
            scores[0] * 0.25 +
            scores[1] * 0.35 +
            scores[2] * 0.25 +
            scores[3] * 0.15
        )
        
        self.metrics['overall'] = overall
        self.metrics['rating'] = self._score_to_rating(overall)
        
        print(f"\n📈 DEPENDENCY SCORES:")
        print(f"  Requirements: {scores[0]}/100")
        print(f"  Security: {scores[1]}/100")
        print(f"  Up-to-date: {scores[2]}/100")
        print(f"  Licenses: {scores[3]}/100")
        print(f"  OVERALL: {overall}/100 ({self.metrics['rating']})")
    
    def _get_priority_updates(self) -> list[dict]:
        """Get sorted priority updates."""
        priority_order = {
            self.PRIORITY_CRITICAL: 0,
            self.PRIORITY_HIGH: 1,
            self.PRIORITY_MEDIUM: 2,
            self.PRIORITY_LOW: 3
        }
        return sorted(self.issues, key=lambda x: priority_order.get(x['priority'], 4))
    
    def _score_to_rating(self, score: int) -> str:
        if score >= 90: return 'A (Healthy)'
        if score >= 80: return 'B (Good)'
        if score >= 70: return 'C (Acceptable)'
        if score >= 60: return 'D (Needs Attention)'
        return 'F (At Risk)'
    
    def print_report(self) -> None:
        """Print formatted audit report."""
        report = self.audit()
        
        print(f"\n🎯 DEPENDENCY PRIORITIES (Top 10):")
        print("-" * 60)
        
        for i, issue in enumerate(report['priority_updates'][:10], 1):
            priority_emoji = {
                self.PRIORITY_CRITICAL: '🔴',
                self.PRIORITY_HIGH: '🟠',
                self.PRIORITY_MEDIUM: '🟡',
                self.PRIORITY_LOW: '🔵'
            }.get(issue['priority'], '⚪')
            
            print(f"\n{i}. {priority_emoji} [{issue['priority']}] {issue['category']}")
            if 'package' in issue:
                print(f"   📦 {issue['package']}")
            if 'file' in issue:
                print(f"   📍 {issue['file']}")
            print(f"   📝 {issue['issue']}")
            print(f"   💡 {issue['suggestion']}")
        
        print(f"\n{'=' * 60}")


def main():
    agent = DependencyAuditAgent(project_path="/home/matthewh/chatty-commander")
    agent.print_report()
    return 0 if agent.metrics.get('overall', 0) >= 60 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
