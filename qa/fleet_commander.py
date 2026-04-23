#!/usr/bin/env python3
"""
🚀 FLEET COMMANDER
Orchestrates all 6 QA Agents and produces a prioritized final report.

Usage:
    python -m qa.fleet_commander

This commander:
1. Launches all 6 specialized agents
2. Collects scores and findings from each
3. Prioritizes issues across all domains
4. Presents a final selection for implementation

Agents in Fleet:
1. Code Quality Agent    - Complexity, types, style
2. Test Coverage Agent    - Coverage gaps, test quality
3. Security Audit Agent   - Vulnerabilities, secrets
4. Performance Agent      - Optimization opportunities
5. Documentation Agent    - Docs completeness
6. Dependency Audit Agent - Package health
"""

from __future__ import annotations

import json
import sys
import traceback
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResult:
    """Result from a single agent."""
    name: str
    score: int
    rating: str
    issues: list[dict] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class PrioritizedIssue:
    """Cross-agent prioritized issue."""
    rank: int
    agent: str
    priority: str
    category: str
    issue: str
    file: str | None
    line: int | None
    recommendation: str
    impact: str
    effort: str


class FleetCommander:
    """Orchestrates the QA agent fleet."""
    
    def __init__(self, src_path: str = "src/chatty_commander") -> None:
        self.src_path = src_path
        self.results: list[AgentResult] = []
        self.global_score: int = 0
        self.global_rating: str = ""
        
        # Impact multipliers by category
        self.impact_weights = {
            'SECRETS': 10,
            'VULNERABILITY': 10,
            'CRITICAL': 9,
            'COMPLEXITY': 7,
            'AUTH': 7,
            'INPUT_VALIDATION': 6,
            'CRYPTO': 6,
            'DOCSTRINGS': 5,
            'HIGH': 5,
            'COVERAGE': 4,
            'ALGORITHM': 4,
            'MEMORY': 3,
            'I/O': 3,
            'README': 3,
            'OUTDATED': 2,
            'UNPINNED': 2,
            'STYLE': 1,
            'COMMENTS': 1,
            'MEDIUM': 2,
            'LOW': 1,
        }
    
    def deploy_fleet(self) -> None:
        """Deploy all agents and collect results."""
        print("\n" + "=" * 80)
        print("🚀 DEPLOYING QA AGENT FLEET")
        print("=" * 80)
        
        agents = [
            ('Code Quality Agent', 'code_quality_agent', 'CodeQualityAgent'),
            ('Test Coverage Agent', 'test_coverage_agent', 'CoverageAnalyzer'),
            ('Security Audit Agent', 'security_audit_agent', 'SecurityAuditAgent'),
            ('Performance Agent', 'performance_agent', 'PerformanceAgent'),
            ('Documentation Agent', 'documentation_agent', 'DocumentationAgent'),
            ('Dependency Audit Agent', 'dependency_audit_agent', 'DependencyAuditAgent'),
        ]
        
        for name, module, agent_class in agents:
            print(f"\n{'─' * 60}")
            print(f"📡 Deploying {name}...")
            print('─' * 60)
            
            try:
                result = self._run_agent(module, agent_class)
                self.results.append(result)
                
                status = "✅ COMPLETE" if not result.error else "❌ FAILED"
                print(f"\n{status} - Score: {result.score}/100 ({result.rating})")
                
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                print(f"\n❌ FAILED - {error_msg}")
                self.results.append(AgentResult(
                    name=name,
                    score=0,
                    rating="ERROR",
                    error=error_msg
                ))
    
    def _run_agent(self, module_name: str, agent_class: str) -> AgentResult:
        """Run a single agent and return result."""
        # Import dynamically
        module = __import__(f'qa.{module_name}', fromlist=[agent_class])
        AgentClass = getattr(module, agent_class)
        
        # Instantiate and run
        agent = AgentClass(src_path=self.src_path)
        
        # Run analysis (agents print their own output)
        report = agent.analyze()
        
        return AgentResult(
            name=agent_class.replace('Agent', '').replace('Analyzer', ''),
            score=report['scores'].get('overall', 0),
            rating=report['scores'].get('grade', report['scores'].get('rating', 'N/A')),
            issues=report.get('issues', report.get('gaps', report.get('findings', []))),
            metrics=report['scores']
        )
    
    def calculate_global_score(self) -> None:
        """Calculate weighted global quality score."""
        # Valid results only
        valid_results = [r for r in self.results if not r.error]
        
        if not valid_results:
            self.global_score = 0
            self.global_rating = "ERROR"
            return
        
        # Weight by importance
        weights = {
            'SecurityAudit': 0.25,  # Security is critical
            'CodeQuality': 0.20,    # Code quality is essential
            'TestCoverage': 0.20,   # Testing is essential
            'Documentation': 0.15,  # Docs are important
            'DependencyAudit': 0.12,  # Deps matter
            'Performance': 0.08,    # Performance is nice-to-have
        }
        
        weighted_sum = 0
        total_weight = 0
        
        for result in valid_results:
            weight = weights.get(result.name, 0.10)
            weighted_sum += result.score * weight
            total_weight += weight
        
        self.global_score = int(weighted_sum / total_weight) if total_weight else 0
        
        # Determine rating
        if self.global_score >= 90:
            self.global_rating = "A (Excellent)"
        elif self.global_score >= 80:
            self.global_rating = "B (Good)"
        elif self.global_score >= 70:
            self.global_rating = "C (Acceptable)"
        elif self.global_score >= 60:
            self.global_rating = "D (Needs Work)"
        else:
            self.global_rating = "F (Critical)"
    
    def prioritize_issues(self) -> list[PrioritizedIssue]:
        """Create cross-agent prioritized issue list."""
        all_issues = []
        
        for result in self.results:
            for issue in result.issues:
                # Calculate impact score
                priority = issue.get('priority', issue.get('risk', 'LOW'))
                category = issue.get('category', 'GENERAL')
                
                impact_score = self.impact_weights.get(category, 1)
                impact_score += self.impact_weights.get(priority, 1)
                
                # Estimate effort
                effort = self._estimate_effort(issue, category)
                
                # Impact description
                impact = self._describe_impact(priority, category)
                
                all_issues.append({
                    'impact_score': impact_score,
                    'agent': result.name,
                    'priority': priority,
                    'category': category,
                    'issue': issue.get('issue', issue.get('message', 'Unknown')),
                    'file': issue.get('file'),
                    'line': issue.get('line'),
                    'recommendation': issue.get('suggestion', issue.get('recommendation', 'Review and fix')),
                    'impact': impact,
                    'effort': effort,
                })
        
        # Sort by impact score (descending)
        sorted_issues = sorted(all_issues, key=lambda x: -x['impact_score'])
        
        # Create prioritized list
        prioritized = []
        for i, issue in enumerate(sorted_issues[:50], 1):  # Top 50
            prioritized.append(PrioritizedIssue(
                rank=i,
                agent=issue['agent'],
                priority=issue['priority'],
                category=issue['category'],
                issue=issue['issue'],
                file=issue['file'],
                line=issue['line'],
                recommendation=issue['recommendation'],
                impact=issue['impact'],
                effort=issue['effort']
            ))
        
        return prioritized
    
    def _estimate_effort(self, issue: dict, category: str) -> str:
        """Estimate implementation effort."""
        effort_map = {
            'SECRETS': 'Low (hours)',
            'VULNERABILITY': 'Medium (days)',
            'COMPLEXITY': 'High (weeks)',
            'DOCSTRINGS': 'Low (hours)',
            'README': 'Low (hours)',
            'STYLE': 'Low (hours)',
            'COMMENTS': 'Low (hours)',
            'CRYPTO': 'Medium (days)',
            'INPUT_VALIDATION': 'Medium (days)',
            'ALGORITHM': 'High (weeks)',
            'OUTDATED': 'Low (hours)',
            'UNPINNED': 'Low (hours)',
            'AUTH': 'Medium (days)',
        }
        return effort_map.get(category, 'Medium (days)')
    
    def _describe_impact(self, priority: str, category: str) -> str:
        """Describe business/technical impact."""
        impacts = {
            'SECRETS': 'Security breach risk',
            'VULNERABILITY': 'Exploitable weakness',
            'CRITICAL': 'System failure risk',
            'COMPLEXITY': 'Maintenance burden',
            'DOCSTRINGS': 'Developer productivity',
            'CRYPTO': 'Data protection',
            'INPUT_VALIDATION': 'Data integrity',
            'AUTH': 'Access control',
            'COVERAGE': 'Regression risk',
            'OUTDATED': 'Security/update risk',
        }
        return impacts.get(category, f'{priority} priority improvement')
    
    def generate_executive_summary(self) -> dict[str, Any]:
        """Generate executive summary."""
        # Category breakdown
        categories = {}
        for result in self.results:
            for issue in result.issues:
                cat = issue.get('category', 'OTHER')
                if cat not in categories:
                    categories[cat] = 0
                categories[cat] += 1
        
        # Agent summaries
        agent_summaries = []
        for result in self.results:
            agent_summaries.append({
                'name': result.name,
                'score': result.score,
                'rating': result.rating,
                'issues': len(result.issues),
                'status': '✅' if not result.error else '❌'
            })
        
        return {
            'global_score': self.global_score,
            'global_rating': self.global_rating,
            'agents_deployed': len(self.results),
            'agents_successful': len([r for r in self.results if not r.error]),
            'total_issues': sum(len(r.issues) for r in self.results),
            'category_breakdown': categories,
            'agent_summaries': agent_summaries,
        }
    
    def print_final_report(self) -> None:
        """Print final prioritized report."""
        print("\n" + "=" * 80)
        print("📊 FLEET COMMANDER - FINAL REPORT")
        print("=" * 80)
        
        # Executive Summary
        summary = self.generate_executive_summary()
        
        print(f"\n🏆 GLOBAL QUALITY SCORE: {summary['global_score']}/100")
        print(f"   Rating: {summary['global_rating']}")
        print(f"\n📡 Agents Deployed: {summary['agents_deployed']}")
        print(f"   Successful: {summary['agents_successful']}")
        print(f"   Total Issues: {summary['total_issues']}")
        
        # Agent Scorecard
        print(f"\n{'─' * 80}")
        print("📋 AGENT SCORECARD")
        print('─' * 80)
        
        for agent in summary['agent_summaries']:
            status = agent['status']
            score_bar = '█' * (agent['score'] // 10) + '░' * (10 - agent['score'] // 10)
            print(f"{status} {agent['name']:<20} {score_bar} {agent['score']:>3}/100 ({agent['rating']})")
        
        # Prioritized Action Items
        print(f"\n{'─' * 80}")
        print("🎯 PRIORITIZED ACTION ITEMS (Top 20)")
        print('─' * 80)
        print(f"{'Rank':<6} {'Agent':<15} {'Priority':<10} {'Category':<15} {'Impact':<20} {'Effort':<15}")
        print('-' * 80)
        
        prioritized = self.prioritize_issues()
        for issue in prioritized[:20]:
            priority_emoji = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🔵'
            }.get(issue.priority, '⚪')
            
            print(f"{issue.rank:<6} {issue.agent:<15} {priority_emoji} {issue.priority:<8} "
                  f"{issue.category:<15} {issue.impact:<20} {issue.effort:<15}")
        
        # Detailed Top 10
        print(f"\n{'─' * 80}")
        print("📖 TOP 10 ISSUES - DETAILED")
        print('─' * 80)
        
        for issue in prioritized[:10]:
            priority_emoji = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🔵'
            }.get(issue.priority, '⚪')
            
            print(f"\n{priority_emoji} #{issue.rank} [{issue.priority}] {issue.category}")
            print(f"   🤖 From: {issue.agent}")
            if issue.file:
                print(f"   📍 Location: {issue.file}:{issue.line or 'N/A'}")
            print(f"   📝 Issue: {issue.issue}")
            print(f"   💡 Recommendation: {issue.recommendation}")
            print(f"   📊 Impact: {issue.impact}")
            print(f"   ⏱️  Effort: {issue.effort}")
        
        # Final recommendations
        print(f"\n{'=' * 80}")
        print("📋 FINAL RECOMMENDATIONS")
        print('=' * 80)
        
        critical_count = sum(1 for i in prioritized if i.priority == 'CRITICAL')
        high_count = sum(1 for i in prioritized if i.priority == 'HIGH')
        
        if critical_count > 0:
            print(f"\n🚨 IMMEDIATE ACTION REQUIRED:")
            print(f"   Address {critical_count} CRITICAL issues before next release")
            
        if high_count > 0:
            print(f"\n⚠️  HIGH PRIORITY:")
            print(f"   Plan {high_count} HIGH priority issues for next sprint")
        
        if self.global_score >= 80:
            print(f"\n✅ QUALITY STATUS: Good - maintain current standards")
        elif self.global_score >= 60:
            print(f"\n⚠️  QUALITY STATUS: Acceptable - improvement needed")
        else:
            print(f"\n🚨 QUALITY STATUS: Critical - immediate intervention required")
        
        print(f"\n{'=' * 80}")
        print("🚀 READY FOR FINAL SELECTION")
        print("=" * 80)
    
    def export_json(self, filename: str = "qa_report.json") -> None:
        """Export full report to JSON."""
        report = {
            'executive_summary': self.generate_executive_summary(),
            'agent_results': [
                {
                    'name': r.name,
                    'score': r.score,
                    'rating': r.rating,
                    'metrics': r.metrics,
                    'issue_count': len(r.issues),
                }
                for r in self.results
            ],
            'prioritized_issues': [
                {
                    'rank': i.rank,
                    'agent': i.agent,
                    'priority': i.priority,
                    'category': i.category,
                    'issue': i.issue,
                    'file': i.file,
                    'line': i.line,
                    'recommendation': i.recommendation,
                    'impact': i.impact,
                    'effort': i.effort,
                }
                for i in self.prioritize_issues()
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Full report exported to: {filename}")


def main():
    """Main entry point."""
    commander = FleetCommander(src_path="src/chatty_commander")
    
    # Deploy fleet
    commander.deploy_fleet()
    
    # Calculate scores
    commander.calculate_global_score()
    
    # Print final report
    commander.print_final_report()
    
    # Export detailed report
    commander.export_json("/home/matthewh/chatty-commander/qa_report.json")
    
    return 0 if commander.global_score >= 60 else 1


if __name__ == "__main__":
    sys.exit(main())
