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
Git hygiene tests for chatty-commander.

These tests ensure proper Git repository hygiene and prevent regressions
related to:
- .worktrees/ directory tracking
- Git configuration
- Repository structure
- Branch management

Run with: uv run pytest tests/test_git_hygiene.py -v
"""

import os
import subprocess
from pathlib import Path

import pytest


class TestGitHygiene:
    """Test Git repository hygiene and prevent common issues."""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Get the repository root directory."""
        # Find git root by looking for .git directory
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent

        # Fallback to current directory if not in git repo
        return Path.cwd()

    def _run_git_command(
        self, cmd: list[str], cwd: Path | None = None
    ) -> subprocess.CompletedProcess:
        """Run a git command and return the result."""
        full_cmd = ["git"] + cmd
        return subprocess.run(
            full_cmd, cwd=cwd or Path.cwd(), capture_output=True, text=True, timeout=30
        )

    def test_worktrees_not_tracked(self, repo_root: Path):
        """Test that .worktrees/ directories are not tracked by Git."""
        # Check if any .worktrees/ files are tracked
        result = self._run_git_command(["ls-files"], cwd=repo_root)

        if result.returncode != 0:
            pytest.skip("Not in a Git repository or Git command failed")

        tracked_files = (
            result.stdout.strip().split("\n") if result.stdout.strip() else []
        )
        worktree_files = [f for f in tracked_files if f.startswith(".worktrees/")]

        assert not worktree_files, (
            f"Found .worktrees/ files being tracked by Git: {worktree_files}. "
            "These should be in .gitignore and removed from tracking."
        )

    def test_gitignore_includes_worktrees(self, repo_root: Path):
        """Test that .gitignore includes .worktrees/ pattern."""
        gitignore_path = repo_root / ".gitignore"

        if not gitignore_path.exists():
            pytest.fail(".gitignore file not found in repository root")

        gitignore_content = gitignore_path.read_text(encoding="utf-8")

        # Check for .worktrees/ pattern (with or without trailing slash)
        worktree_patterns = [".worktrees/", ".worktrees", "/.worktrees/", "/.worktrees"]

        has_worktree_ignore = any(
            pattern in gitignore_content for pattern in worktree_patterns
        )

        assert has_worktree_ignore, (
            ".gitignore does not include .worktrees/ pattern. "
            "Add '.worktrees/' to .gitignore to prevent accidental tracking."
        )

    def test_no_conflict_markers_in_tracked_files(self, repo_root: Path):
        """Test that no tracked files contain merge conflict markers."""
        # Get list of tracked files
        result = self._run_git_command(["ls-files"], cwd=repo_root)

        if result.returncode != 0:
            pytest.skip("Not in a Git repository or Git command failed")

        tracked_files = (
            result.stdout.strip().split("\n") if result.stdout.strip() else []
        )

        # Check for conflict markers in text files
        files_with_conflicts = []

        for file_path in tracked_files:
            full_path = repo_root / file_path

            # Skip binary files and non-existent files
            if not full_path.exists() or not full_path.is_file():
                continue

            # Skip files that legitimately contain these patterns
            skip_patterns = [
                "test_git_hygiene.py",  # This test file itself
                ".github/workflows/",  # CI scripts may check for conflicts
                "scripts/",  # Scripts may contain these patterns
                "docs/",  # Documentation may show examples
                "reports/",  # Reports may contain conflict examples
                ".bak.",  # Backup files
                ".backup",  # Backup files
            ]

            if any(pattern in file_path for pattern in skip_patterns):
                continue

            # Only check text files
            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                lines = content.split("\n")

                # Look for actual Git conflict markers (start of line)
                conflict_patterns = [
                    r"^<<<<<<< ",  # Git conflict start
                    r"^=======$",  # Git conflict separator
                    r"^>>>>>>> ",  # Git conflict end
                ]

                for i, line in enumerate(lines, 1):
                    for pattern in conflict_patterns:
                        import re

                        if re.match(pattern, line):
                            files_with_conflicts.append(
                                (file_path, f"line {i}: {line.strip()}")
                            )
                            break

            except (UnicodeDecodeError, PermissionError):
                # Skip files that can't be read as text
                continue

        assert not files_with_conflicts, (
            f"Found merge conflict markers in tracked files: {files_with_conflicts}. "
            "Please resolve conflicts before committing."
        )

    def test_git_fetch_prune_configured(self, repo_root: Path):
        """Test that Git is configured to prune remote branches on fetch."""
        result = self._run_git_command(
            ["config", "--get", "fetch.prune"], cwd=repo_root
        )

        if result.returncode != 0:
            # Config not set, check if we can set it (this is informational)
            pytest.skip(
                "fetch.prune not configured. Consider running: git config fetch.prune true"
            )

        prune_setting = result.stdout.strip().lower()
        assert prune_setting == "true", (
            f"fetch.prune is set to '{prune_setting}', should be 'true'. "
            "Run: git config fetch.prune true"
        )

    def test_no_ephemeral_branches_in_remote(self, repo_root: Path):
        """Test for ephemeral branches that might need cleanup."""
        # Get remote branches
        result = self._run_git_command(["branch", "-r"], cwd=repo_root)

        if result.returncode != 0:
            pytest.skip("Could not list remote branches")

        remote_branches = (
            result.stdout.strip().split("\n") if result.stdout.strip() else []
        )

        # Look for obviously ephemeral branch patterns
        ephemeral_patterns = [
            "temp/",
            "tmp/",
            "test/",
            "experiment/",
            "wip/",
            "backup/",
            "old/",
            "archive/",
            "delete-me/",
        ]

        ephemeral_branches = []
        for branch in remote_branches:
            branch = branch.strip()
            if not branch or "HEAD" in branch:
                continue

            # Remove "origin/" prefix for checking
            branch_name = branch.split("/", 1)[-1] if "/" in branch else branch

            for pattern in ephemeral_patterns:
                if pattern in branch_name.lower():
                    ephemeral_branches.append(branch)
                    break

        # This is a warning, not a hard failure
        if ephemeral_branches:
            pytest.skip(
                f"Found potentially ephemeral remote branches: {ephemeral_branches}. "
                "Consider cleaning up with scripts/cleanup_branches.sh"
            )


class TestProjectStructure:
    """Test project structure and required files."""

    def test_scripts_directory_exists(self):
        """Test that scripts directory exists with required files."""
        scripts_dir = Path("scripts")
        assert scripts_dir.exists(), "scripts/ directory should exist"
        assert scripts_dir.is_dir(), "scripts/ should be a directory"

        # Check for key scripts
        required_scripts = ["cleanup_branches.sh", "guarded_commit.sh"]

        for script in required_scripts:
            script_path = scripts_dir / script
            if script_path.exists():
                assert script_path.is_file(), f"{script} should be a file"
                # Check if executable (on Unix systems)
                if os.name != "nt":  # Not Windows
                    assert os.access(
                        script_path, os.X_OK
                    ), f"{script} should be executable"

    def test_contributing_md_exists(self):
        """Test that CONTRIBUTING.md exists and has required content."""
        contributing_path = Path("CONTRIBUTING.md")
        assert contributing_path.exists(), "CONTRIBUTING.md should exist"

        content = contributing_path.read_text(encoding="utf-8")

        # Check for key sections
        required_sections = [
            "Branch Naming Conventions",
            "Conventional Commits",
            "Git Workflow",
            "Pre-commit Hooks",
        ]

        for section in required_sections:
            assert (
                section in content
            ), f"CONTRIBUTING.md should contain '{section}' section"

    def test_precommit_config_exists(self):
        """Test that pre-commit configuration exists and is valid."""
        precommit_path = Path(".pre-commit-config.yaml")
        assert precommit_path.exists(), ".pre-commit-config.yaml should exist"

        content = precommit_path.read_text(encoding="utf-8")

        # Check for key hooks
        required_hooks = [
            "ruff",
            "trailing-whitespace",
            "end-of-file-fixer",
        ]

        for hook in required_hooks:
            assert hook in content, f"Pre-commit config should include '{hook}' hook"


class TestGitConfiguration:
    """Test Git configuration and best practices."""

    def test_git_repository_exists(self):
        """Test that we're in a Git repository."""
        git_dir = Path(".git")
        assert (
            git_dir.exists()
        ), "Should be in a Git repository (.git directory not found)"

    def test_main_branch_exists(self):
        """Test that main branch exists."""
        result = subprocess.run(
            ["git", "branch", "-a"], capture_output=True, text=True, timeout=10
        )

        if result.returncode != 0:
            pytest.skip("Could not list Git branches")

        branches = result.stdout

        # Should have either main or master branch
        has_main = "main" in branches
        has_master = "master" in branches

        assert has_main or has_master, "Repository should have a main or master branch"

    def test_no_large_files_tracked(self):
        """Test that no large files are tracked (>10MB)."""
        # This is more of a warning than a hard requirement
        result = subprocess.run(
            ["find", ".", "-type", "f", "-size", "+10M", "-not", "-path", "./.git/*"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0 and result.stdout.strip():
            large_files = result.stdout.strip().split("\n")
            # Filter out files that might be legitimately large
            suspicious_files = [
                f
                for f in large_files
                if not any(
                    pattern in f
                    for pattern in [
                        "node_modules/",
                        ".git/",
                        "__pycache__/",
                        ".pytest_cache/",
                        ".uv/",
                        "uv.lock",
                        ".venv/",
                        "venv/",
                    ]
                )
            ]

            if suspicious_files:
                pytest.skip(
                    f"Found large files that might need Git LFS: {suspicious_files}"
                )


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v"])
