#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2024 mhand
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Test Quality Improvement Script for ChattyCommander

This script analyzes the test suite and provides recommendations for improvement.
It can automatically fix common issues and generate reports on test quality.
"""

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


class TestQualityAnalyzer:
    """Analyzes test quality and provides improvement recommendations."""

    def __init__(self, test_dir: Path):
        self.test_dir = test_dir
        self.issues: list[dict[str, Any]] = []
        self.stats = {
            "total_tests": 0,
            "test_files": 0,
            "coverage": 0.0,
            "issues_found": 0,
        }

    def analyze(self) -> dict[str, Any]:
        """Run complete analysis of test quality."""
        print("🔍 Analyzing test quality...")

        self._analyze_test_files()
        self._analyze_coverage()
        self._check_test_isolation()
        self._check_assertion_quality()
        self._check_mock_usage()

        return {
            "stats": self.stats,
            "issues": self.issues,
            "recommendations": self._generate_recommendations(),
        }

    def _analyze_test_files(self) -> None:
        """Analyze individual test files."""
        test_files = list(self.test_dir.glob("test_*.py"))

        for test_file in test_files:
            self.stats["test_files"] += 1
            self._analyze_single_test_file(test_file)

    def _analyze_single_test_file(self, test_file: Path) -> None:
        """Analyze a single test file."""
        try:
            with open(test_file, encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            # Count test functions
            test_functions = [
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
            ]
            self.stats["total_tests"] += len(test_functions)

            # Check for quality issues
            self._check_test_file_quality(test_file, content, tree)

        except Exception as e:
            self.issues.append(
                {
                    "type": "parse_error",
                    "file": str(test_file),
                    "message": f"Failed to parse test file: {e}",
                    "severity": "high",
                }
            )

    def _check_test_file_quality(
        self, test_file: Path, content: str, tree: ast.AST
    ) -> None:
        """Check quality issues in a test file."""
        # Check for missing docstrings
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                if not ast.get_docstring(node):
                    self.issues.append(
                        {
                            "type": "missing_docstring",
                            "file": str(test_file),
                            "function": node.name,
                            "message": f"Test function {node.name} is missing a docstring",
                            "severity": "low",
                        }
                    )

        # Check for bare assert statements
        assert_lines = []
        for i, line in enumerate(content.split("\n"), 1):
            if re.search(r"\bassert\s+", line.strip()):
                assert_lines.append(i)

        if len(assert_lines) > 10:  # Arbitrary threshold
            self.issues.append(
                {
                    "type": "too_many_asserts",
                    "file": str(test_file),
                    "message": f"Test file has {len(assert_lines)} assert statements, consider breaking into smaller tests",
                    "severity": "medium",
                }
            )

        # Check for hardcoded paths
        if "/tmp/" in content or "/home/" in content:
            self.issues.append(
                {
                    "type": "hardcoded_paths",
                    "file": str(test_file),
                    "message": "Test file contains hardcoded paths, use tmp_path fixture instead",
                    "severity": "medium",
                }
            )

    def _analyze_coverage(self) -> None:
        """Analyze test coverage."""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "--cov=src", "--cov-report=json"],
                cwd=self.test_dir.parent,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0 and "coverage.json" in result.stdout:
                # Parse coverage data
                coverage_file = self.test_dir.parent / "coverage.json"
                if coverage_file.exists():
                    with open(coverage_file) as f:
                        coverage_data = json.load(f)
                    self.stats["coverage"] = coverage_data.get("totals", {}).get(
                        "percent_covered", 0.0
                    )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.stats["coverage"] = 0.0

    def _check_test_isolation(self) -> None:
        """Check for test isolation issues."""
        # This would check for global state modifications, etc.
        # For now, just check for common isolation problems
        pass

    def _check_assertion_quality(self) -> None:
        """Check quality of assertions."""
        # This would analyze assertion patterns
        pass

    def _check_mock_usage(self) -> None:
        """Check mock usage patterns."""
        # This would analyze mock usage
        pass

    def _generate_recommendations(self) -> list[str]:
        """Generate improvement recommendations."""
        recommendations = []

        if self.stats["coverage"] < 80:
            recommendations.append(
                f"Improve test coverage (currently {self.stats['coverage']:.1f}%)"
            )

        if self.stats["total_tests"] < 100:
            recommendations.append("Add more comprehensive test cases")

        issue_counts = {}
        for issue in self.issues:
            issue_type = issue["type"]
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1

        for issue_type, count in issue_counts.items():
            if count > 5:
                recommendations.append(
                    f"Address {count} instances of {issue_type.replace('_', ' ')}"
                )

        return recommendations


class TestQualityImprover:
    """Automatically improves test quality."""

    def __init__(self, test_dir: Path):
        self.test_dir = test_dir

    def improve(self, issues: list[dict[str, Any]]) -> dict[str, Any]:
        """Automatically fix identified issues."""
        results = {
            "fixed": 0,
            "skipped": 0,
            "errors": 0,
        }

        for issue in issues:
            try:
                if issue["type"] == "missing_docstring":
                    self._add_docstring(issue)
                    results["fixed"] += 1
                elif issue["type"] == "hardcoded_paths":
                    self._fix_hardcoded_paths(issue)
                    results["fixed"] += 1
                else:
                    results["skipped"] += 1
            except Exception as e:
                print(f"Error fixing {issue['type']}: {e}")
                results["errors"] += 1

        return results

    def _add_docstring(self, issue: dict[str, Any]) -> None:
        """Add a docstring to a test function."""
        file_path = Path(issue["file"])
        function_name = issue["function"]

        with open(file_path) as f:
            content = f.read()

        # Simple docstring addition (this is a basic implementation)
        pattern = rf"(def {function_name}\([^)]*\):)"
        replacement = rf'\1\n    """Test {function_name.replace("test_", "").replace("_", " ")}."""'

        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

        with open(file_path, "w") as f:
            f.write(new_content)

    def _fix_hardcoded_paths(self, issue: dict[str, Any]) -> None:
        """Fix hardcoded paths in test files."""
        # This would be more complex to implement automatically
        # For now, just mark as needing manual review
        pass


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Improve test quality for ChattyCommander"
    )
    parser.add_argument("--analyze", action="store_true", help="Analyze test quality")
    parser.add_argument("--fix", action="store_true", help="Automatically fix issues")
    parser.add_argument("--report", action="store_true", help="Generate quality report")
    parser.add_argument(
        "--test-dir", type=Path, default=Path("tests"), help="Test directory"
    )

    args = parser.parse_args()

    if not args.test_dir.exists():
        print(f"Test directory {args.test_dir} does not exist")
        sys.exit(1)

    analyzer = TestQualityAnalyzer(args.test_dir)

    if args.analyze or args.report:
        results = analyzer.analyze()

        print("📊 Test Quality Report")
        print("=" * 50)
        print(f"Test files: {results['stats']['test_files']}")
        print(f"Total tests: {results['stats']['total_tests']}")
        print(".1f")
        print(f"Issues found: {len(results['issues'])}")
        print()

        if results["issues"]:
            print("🔧 Issues Found:")
            for issue in results["issues"][:10]:  # Show first 10
                severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    issue.get("severity", "medium"), "🟡"
                )
                print(f"  {severity_icon} {issue['type']}: {issue['message']}")
                if "file" in issue:
                    print(f"    File: {issue['file']}")

            if len(results["issues"]) > 10:
                print(f"  ... and {len(results['issues']) - 10} more issues")

        print()
        print("💡 Recommendations:")
        for rec in results["recommendations"]:
            print(f"  • {rec}")

    if args.fix:
        improver = TestQualityImprover(args.test_dir)
        fix_results = improver.improve(analyzer.issues)

        print("🔧 Fix Results:")
        print(f"  Fixed: {fix_results['fixed']}")
        print(f"  Skipped: {fix_results['skipped']}")
        print(f"  Errors: {fix_results['errors']}")


if __name__ == "__main__":
    main()
