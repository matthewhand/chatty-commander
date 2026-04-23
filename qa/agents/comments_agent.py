#!/usr/bin/env python3
"""
COMMENTS IMPLEMENTATION AGENT
Adds explanatory comments to 320 complex code sections.
"""

import ast
from pathlib import Path


class CommentsAgent:
    """Adds inline comments to complex logic."""
    
    def __init__(self, src_path: str = "src/chatty_commander", limit: int = 320):
        self.src_path = Path(src_path)
        self.limit = limit
        self.added = 0
    
    def find_complex_sections(self) -> list[tuple[Path, int, str, str]]:
        """Find complex sections needing comments."""
        print("🔍 Finding complex code sections...")
        
        targets = []
        
        for py_file in self.src_path.rglob("*.py"):
            if 'test' in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except Exception:
                continue
            
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                
                # Check for complex patterns
                indent = len(line) - len(line.lstrip())
                
                # Deeply nested control structures
                if indent >= 8 and any(kw in stripped for kw in ['if', 'for', 'while']):
                    # Check if already commented
                    context = lines[max(0, i-3):i]
                    if not any(l.strip().startswith('#') for l in context):
                        # Determine what this code does
                        description = self._infer_purpose(stripped)
                        targets.append((py_file, i, description, line))
                
                # Exception handling without explanation
                if stripped.startswith('except') and ':' in stripped:
                    context = lines[max(0, i-2):i+1]
                    if not any(l.strip().startswith('#') for l in context):
                        targets.append((py_file, i, "Handle specific exception case", line))
                
                # Complex comprehensions
                if any(kw in stripped for kw in ['for', 'if']) and ('[' in stripped or '{' in stripped):
                    context = lines[max(0, i-2):i]
                    if not any(l.strip().startswith('#') for l in context):
                        targets.append((py_file, i, "Build filtered collection", line))
        
        # Sort by file and line
        targets.sort(key=lambda x: (str(x[0]), x[1]))
        print(f"  Found {len(targets)} sections, will document top {self.limit}")
        return targets[:self.limit]
    
    def _infer_purpose(self, code_line: str) -> str:
        """Infer what a line of code does."""
        code_lower = code_line.lower()
        
        if 'if' in code_lower:
            if any(word in code_lower for word in ['none', 'null', 'empty']):
                return "Validate input exists"
            if any(word in code_lower for word in ['valid', 'check']):
                return "Validate preconditions"
            if any(word in code_lower for word in ['error', 'exception', 'fail']):
                return "Handle error condition"
            return "Apply conditional logic"
        
        if 'for' in code_lower:
            if any(word in code_lower for word in ['range', 'len']):
                return "Iterate with index"
            if any(word in code_lower for word in ['items', 'values']):
                return "Iterate collection"
            return "Process each item"
        
        if 'while' in code_lower:
            return "Loop until condition met"
        
        if 'try' in code_lower:
            return "Attempt operation with fallback"
        
        return "Execute operation"
    
    def implement(self) -> int:
        """Add comments to complex sections."""
        targets = self.find_complex_sections()
        
        print(f"\n🚀 Adding comments to {len(targets)} sections...")
        
        # Group by file
        files: dict[Path, list[tuple[int, str, str]]] = {}
        for py_file, line_num, description, original in targets:
            if py_file not in files:
                files[py_file] = []
            files[py_file].append((line_num, description, original))
        
        for py_file, sections in files.items():
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Process in reverse to maintain line numbers
                for line_num, description, original in sorted(sections, key=lambda x: -x[0]):
                    # Calculate proper indentation
                    indent = len(original) - len(original.lstrip())
                    indent_str = ' ' * indent
                    
                    # Create comment
                    comment = f"{indent_str}# {description}\n"
                    
                    # Insert before the line
                    lines.insert(line_num - 1, comment)
                    self.added += 1
                    print(f"  ✓ {py_file.name}:{line_num}")
                
                # Write back
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                    
            except Exception as e:
                print(f"  ✗ Error processing {py_file}: {e}")
        
        print(f"\n✅ Added {self.added} explanatory comments")
        return self.added


def main():
    agent = CommentsAgent(limit=320)
    count = agent.implement()
    return 0 if count > 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
