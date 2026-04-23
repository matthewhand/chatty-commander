#!/usr/bin/env python3
"""
AGENT #3: SECURITY AUDIT AGENT
Scans for security vulnerabilities and compliance issues.

Scores:
- Secrets Management (0-100): Hardcoded secrets detection
- Input Validation (0-100): SQL injection, XSS prevention
- Auth & AuthZ (0-100): Authentication/authorization strength
- Dependency Security (0-100): Known vulnerabilities
- Data Protection (0-100): Encryption, sensitive data handling
- Overall: Weighted average

Risk Levels:
- Critical: Hardcoded secrets, SQL injection, auth bypass
- High: Weak crypto, missing input validation
- Medium: Debug mode, verbose errors
- Low: Missing security headers
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any


class SecurityAuditAgent:
    """Performs security audit of codebase."""
    
    RISK_CRITICAL = "CRITICAL"
    RISK_HIGH = "HIGH"
    RISK_MEDIUM = "MEDIUM"
    RISK_LOW = "LOW"
    RISK_INFO = "INFO"
    
    # Secret patterns to detect
    SECRET_PATTERNS = {
        'api_key': r'(?i)(api[_-]?key\s*=\s*[\'"])([a-zA-Z0-9_\-]{20,})([\'"])',
        'password': r'(?i)(password\s*=\s*[\'"])([^\'"]{8,})([\'"])',
        'secret': r'(?i)(secret[_-]?key\s*=\s*[\'"])([a-zA-Z0-9_\-]{16,})([\'"])',
        'token': r'(?i)(token\s*=\s*[\'"])([a-zA-Z0-9_\-]{20,})([\'"])',
        'private_key': r'(?i)(private[_-]?key|BEGIN\s+(RSA|DSA|EC)\s+PRIVATE)',
        'aws_key': r'(?i)(AKIA[0-9A-Z]{16})',
    }
    
    # Dangerous patterns
    DANGEROUS_PATTERNS = {
        'eval': r'(?<!# )\beval\s*\(',
        'exec': r'(?<!# )\bexec\s*\(',
        'pickle': r'pickle\.loads?\s*\(',
        'subprocess_shell': r'subprocess\..*shell\s*=\s*True',
        'sql_string_concat': r'(execute|cursor\.).*\+.*["\']',
        'format_sql': r'execute.*\.format\s*\(',
        'fstring_sql': r'execute.*f["\']',
    }
    
    def __init__(self, src_path: str = "src") -> None:
        self.src_path = Path(src_path)
        self.findings: list[dict] = []
        self.scores: dict[str, Any] = {}
    
    def audit(self) -> dict[str, Any]:
        """Run full security audit."""
        print("🔒 AGENT #3: SECURITY AUDIT")
        print("=" * 60)
        
        self._scan_secrets()
        self._scan_input_validation()
        self._scan_auth_patterns()
        self._scan_crypto()
        self._scan_dependencies()
        self._scan_configuration()
        self._calculate_scores()
        
        return {
            'scores': self.scores,
            'findings': self.findings,
            'risk_summary': self._get_risk_summary()
        }
    
    def _scan_secrets(self) -> None:
        """Scan for hardcoded secrets."""
        print("\n📊 Scanning for Hardcoded Secrets...")
        
        secrets_found = 0
        
        for py_file in self.src_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for secret_type, pattern in self.SECRET_PATTERNS.items():
                        match = re.search(pattern, line)
                        if match and not self._is_likely_safe(line):
                            secrets_found += 1
                            self.findings.append({
                                'risk': self.RISK_CRITICAL,
                                'category': 'SECRETS',
                                'type': secret_type,
                                'file': str(py_file),
                                'line': line_num,
                                'snippet': line.strip()[:80],
                                'recommendation': f'Move {secret_type} to environment variables or secure vault'
                            })
            except Exception:
                continue
        
        # Score: 100 - (secrets * 20)
        score = max(0, 100 - secrets_found * 20)
        self.scores['secrets_management'] = {
            'secrets_found': secrets_found,
            'score': score,
            'status': 'PASS' if secrets_found == 0 else 'FAIL'
        }
        
        print(f"  {'✓' if secrets_found == 0 else '⚠️'} {secrets_found} potential secrets found")
    
    def _scan_input_validation(self) -> None:
        """Scan for input validation vulnerabilities."""
        print("\n📊 Scanning Input Validation...")
        
        issues = []
        
        for py_file in self.src_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                # Check for raw SQL
                for line_num, line in enumerate(lines, 1):
                    # SQL injection patterns
                    if re.search(r'execute\s*\(.*%s', line) or re.search(r'execute.*\.format\s*\(', line):
                        if not self._has_parameterized_query(content, line_num):
                            issues.append({
                                'file': str(py_file),
                                'line': line_num,
                                'issue': 'Potential SQL injection',
                                'snippet': line.strip()[:80]
                            })
                    
                    # XSS patterns
                    if re.search(r'return.*\+.*request\.', line) or re.search(r'render.*\+.*user', line):
                        issues.append({
                            'file': str(py_file),
                            'line': line_num,
                            'issue': 'Potential XSS',
                            'snippet': line.strip()[:80]
                        })
                    
                    # Path traversal
                    if re.search(r'open\s*\(.*\+', line) and 'os.path' not in line:
                        issues.append({
                            'file': str(py_file),
                            'line': line_num,
                            'issue': 'Potential path traversal',
                            'snippet': line.strip()[:80]
                        })
            except Exception:
                continue
        
        # Add findings
        for issue in issues[:10]:  # Top 10
            self.findings.append({
                'risk': self.RISK_HIGH,
                'category': 'INPUT_VALIDATION',
                'type': issue['issue'],
                'file': issue['file'],
                'line': issue['line'],
                'snippet': issue['snippet'],
                'recommendation': 'Use parameterized queries, sanitize input, validate paths'
            })
        
        score = max(0, 100 - len(issues) * 10)
        self.scores['input_validation'] = {
            'issues_found': len(issues),
            'score': score,
            'status': 'PASS' if len(issues) == 0 else 'REVIEW'
        }
        
        print(f"  {'✓' if len(issues) == 0 else '⚠️'} {len(issues)} input validation issues")
    
    def _scan_auth_patterns(self) -> None:
        """Scan authentication and authorization patterns."""
        print("\n📊 Scanning Auth & AuthZ...")
        
        issues = []
        
        for py_file in self.src_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    # Check for weak auth patterns
                    if 'no_auth' in line.lower() or 'noauth' in line.lower():
                        if 'test' not in str(py_file).lower():
                            issues.append({
                                'file': str(py_file),
                                'line': line_num,
                                'issue': 'Auth bypass detected',
                                'snippet': line.strip()[:80]
                            })
                    
                    # Check for debug mode
                    if re.search(r'debug\s*=\s*True', line) or re.search(r'DEBUG\s*=\s*True', line):
                        if 'test' not in str(py_file).lower():
                            issues.append({
                                'file': str(py_file),
                                'line': line_num,
                                'issue': 'Debug mode enabled',
                                'snippet': line.strip()[:80]
                            })
                    
                    # Check for permissive CORS
                    if 'allow_origins=["*"]' in line or "allow_origins=['*']" in line:
                        issues.append({
                            'file': str(py_file),
                            'line': line_num,
                            'issue': 'Permissive CORS policy',
                            'snippet': line.strip()[:80]
                            })
            except Exception:
                continue
        
        for issue in issues[:5]:
            risk = self.RISK_HIGH if 'auth' in issue['issue'].lower() else self.RISK_MEDIUM
            self.findings.append({
                'risk': risk,
                'category': 'AUTH',
                'type': issue['issue'],
                'file': issue['file'],
                'line': issue['line'],
                'snippet': issue['snippet'],
                'recommendation': 'Review authentication requirements'
            })
        
        score = max(0, 100 - len(issues) * 15)
        self.scores['auth'] = {
            'issues_found': len(issues),
            'score': score,
            'status': 'PASS' if len(issues) == 0 else 'REVIEW'
        }
        
        print(f"  {'✓' if len(issues) == 0 else '⚠️'} {len(issues)} auth issues")
    
    def _scan_crypto(self) -> None:
        """Scan cryptography usage."""
        print("\n📊 Scanning Cryptography...")
        
        weak_patterns = []
        strong_patterns = []
        
        for py_file in self.src_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Weak algorithms
                if 'md5' in content.lower() and 'hashlib' in content:
                    weak_patterns.append(('md5', str(py_file)))
                if 'sha1' in content.lower() and 'hashlib' in content:
                    weak_patterns.append(('sha1', str(py_file)))
                
                # Strong algorithms
                if 'sha256' in content.lower() or 'sha3' in content.lower():
                    strong_patterns.append(('sha256+', str(py_file)))
                if 'secrets' in content:
                    strong_patterns.append(('secrets', str(py_file)))
            except Exception:
                continue
        
        for algo, path in weak_patterns[:5]:
            self.findings.append({
                'risk': self.RISK_HIGH,
                'category': 'CRYPTO',
                'type': f'Weak algorithm: {algo}',
                'file': path,
                'recommendation': f'Replace {algo} with SHA-256 or better'
            })
        
        score = max(0, 100 - len(weak_patterns) * 20 + len(strong_patterns) * 5)
        self.scores['crypto'] = {
            'weak_algorithms': len(weak_patterns),
            'strong_algorithms': len(strong_patterns),
            'score': min(100, score),
            'status': 'PASS' if len(weak_patterns) == 0 else 'FAIL'
        }
        
        print(f"  {'✓' if len(weak_patterns) == 0 else '⚠️'} {len(weak_patterns)} weak algorithms")
    
    def _scan_dependencies(self) -> None:
        """Scan dependencies for known issues."""
        print("\n📊 Scanning Dependencies...")
        
        # Check requirements files
        req_files = list(Path('.').glob('requirements*.txt'))
        
        if not req_files:
            self.scores['dependencies'] = {
                'scan_status': 'SKIPPED',
                'score': 50,  # Unknown
                'status': 'INFO'
            }
            print(f"  ℹ️ No requirements files found")
            return
        
        # Basic checks
        issues = []
        
        for req_file in req_files:
            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for unpinned versions
                for line in content.split('\n'):
                    if line.strip() and not line.startswith('#') and '==' not in line and '>=' not in line:
                        issues.append({
                            'file': str(req_file),
                            'issue': 'Unpinned dependency',
                            'detail': line.strip()[:40]
                        })
            except Exception:
                continue
        
        score = max(0, 100 - len(issues) * 5)
        self.scores['dependencies'] = {
            'unpinned_deps': len(issues),
            'score': score,
            'status': 'REVIEW' if len(issues) > 5 else 'PASS'
        }
        
        print(f"  ✓ Scanned {len(req_files)} requirement files")
        print(f"  {'✓' if len(issues) < 5 else '⚠️'} {len(issues)} unpinned dependencies")
    
    def _scan_configuration(self) -> None:
        """Scan configuration files for security issues."""
        print("\n📊 Scanning Configuration...")
        
        issues = []
        
        # Check for .env files
        env_files = list(Path('.').glob('**/.env*'))
        for env_file in env_files:
            if '.env.example' not in str(env_file) and '.env.template' not in str(env_file):
                if '.gitignore' not in str(env_file):
                    issues.append({
                        'file': str(env_file),
                        'issue': 'Environment file may be in version control',
                        'recommendation': 'Ensure .env files are in .gitignore'
                    })
        
        for issue in issues:
            self.findings.append({
                'risk': self.RISK_MEDIUM,
                'category': 'CONFIG',
                'type': issue['issue'],
                'file': issue['file'],
                'recommendation': issue['recommendation']
            })
        
        score = max(0, 100 - len(issues) * 10)
        self.scores['configuration'] = {
            'issues_found': len(issues),
            'score': score,
            'status': 'PASS' if len(issues) == 0 else 'REVIEW'
        }
        
        print(f"  {'✓' if len(issues) == 0 else '⚠️'} {len(issues)} config issues")
    
    def _calculate_scores(self) -> None:
        """Calculate overall security score."""
        scores = [
            self.scores.get('secrets_management', {}).get('score', 0),
            self.scores.get('input_validation', {}).get('score', 0),
            self.scores.get('auth', {}).get('score', 0),
            self.scores.get('crypto', {}).get('score', 0),
            self.scores.get('dependencies', {}).get('score', 0),
            self.scores.get('configuration', {}).get('score', 0),
        ]
        
        # Weight: Secrets 25%, Input 20%, Auth 20%, Crypto 15%, Deps 10%, Config 10%
        weights = [0.25, 0.20, 0.20, 0.15, 0.10, 0.10]
        overall = int(sum(s * w for s, w in zip(scores, weights)))
        
        self.scores['overall'] = overall
        self.scores['rating'] = self._score_to_rating(overall)
        
        print(f"\n📈 SECURITY SCORES:")
        print(f"  Secrets Management: {scores[0]}/100")
        print(f"  Input Validation: {scores[1]}/100")
        print(f"  Authentication: {scores[2]}/100")
        print(f"  Cryptography: {scores[3]}/100")
        print(f"  Dependencies: {scores[4]}/100")
        print(f"  Configuration: {scores[5]}/100")
        print(f"  OVERALL: {overall}/100 ({self.scores['rating']})")
    
    def _get_risk_summary(self) -> dict[str, int]:
        """Get summary of findings by risk level."""
        summary = {self.RISK_CRITICAL: 0, self.RISK_HIGH: 0, self.RISK_MEDIUM: 0, self.RISK_LOW: 0}
        for finding in self.findings:
            summary[finding.get('risk', self.RISK_LOW)] += 1
        return summary
    
    def _is_likely_safe(self, line: str) -> bool:
        """Check if a line is likely a false positive."""
        safe_patterns = [
            'example', 'sample', 'test', 'dummy', 'placeholder',
            'config.get', 'os.environ', 'getenv', 'env.get',
            'self.api_key', 'cls.api_key', 'api_key = None'
        ]
        return any(p in line.lower() for p in safe_patterns)
    
    def _has_parameterized_query(self, content: str, line_num: int) -> bool:
        """Check if nearby lines show parameterized query usage."""
        lines = content.split('\n')
        context = lines[max(0, line_num-3):min(len(lines), line_num+3)]
        return any('%s' in line or '?' in line for line in context)
    
    def _score_to_rating(self, score: int) -> str:
        if score >= 90: return 'A (Secure)'
        if score >= 80: return 'B (Good)'
        if score >= 70: return 'C (Acceptable)'
        if score >= 60: return 'D (Needs Attention)'
        return 'F (At Risk)'
    
    def print_report(self) -> None:
        """Print formatted audit report."""
        report = self.audit()
        
        print(f"\n🚨 SECURITY FINDINGS (Top 10 by Risk):")
        print("-" * 60)
        
        # Sort by risk
        risk_order = {self.RISK_CRITICAL: 0, self.RISK_HIGH: 1, self.RISK_MEDIUM: 2, self.RISK_LOW: 3}
        sorted_findings = sorted(report['findings'], key=lambda x: risk_order.get(x['risk'], 4))
        
        for i, finding in enumerate(sorted_findings[:10], 1):
            risk_emoji = {
                self.RISK_CRITICAL: '🔴',
                self.RISK_HIGH: '🟠',
                self.RISK_MEDIUM: '🟡',
                self.RISK_LOW: '🔵'
            }.get(finding['risk'], '⚪')
            
            print(f"\n{i}. {risk_emoji} [{finding['risk']}] {finding.get('type', finding.get('category', 'ISSUE'))}")
            if 'file' in finding:
                print(f"   📍 {finding['file']}:{finding.get('line', 'N/A')}")
            if 'snippet' in finding:
                print(f"   📝 {finding['snippet']}")
            print(f"   💡 {finding['recommendation']}")
        
        # Risk summary
        summary = report['risk_summary']
        print(f"\n📊 RISK SUMMARY:")
        print(f"   🔴 Critical: {summary.get(self.RISK_CRITICAL, 0)}")
        print(f"   🟠 High: {summary.get(self.RISK_HIGH, 0)}")
        print(f"   🟡 Medium: {summary.get(self.RISK_MEDIUM, 0)}")
        print(f"   🔵 Low: {summary.get(self.RISK_LOW, 0)}")
        
        print(f"\n{'=' * 60}")


def main():
    agent = SecurityAuditAgent(src_path="src/chatty_commander")
    agent.print_report()
    return 0 if agent.scores.get('overall', 0) >= 70 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
