#!/usr/bin/env python3
"""
DOCSTRING IMPLEMENTATION AGENT
Adds missing docstrings to top 50% of undocumented public symbols.
"""

import ast
import re
from pathlib import Path


class DocstringAgent:
    """Automatically adds docstrings to undocumented code."""
    
    def __init__(self, src_path: str = "src/chatty_commander", limit: int = 125):
        self.src_path = Path(src_path)
        self.limit = limit
        self.added = 0
        self.targets: list[tuple[Path, ast.AST, str]] = []
    
    def find_targets(self) -> None:
        """Find all public symbols needing docstrings."""
        print("🔍 Finding undocumented public symbols...")
        
        for py_file in self.src_path.rglob("*.py"):
            if '/_' in str(py_file) or 'test' in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not node.name.startswith('_') and not ast.get_docstring(node):
                            # Get function signature for context
                            args = self._format_args(node)
                            self.targets.append((py_file, node, args))
                    
                    elif isinstance(node, ast.ClassDef):
                        if not node.name.startswith('_') and not ast.get_docstring(node):
                            self.targets.append((py_file, node, None))
            except SyntaxError:
                continue
        
        # Sort by file path for consistent ordering
        self.targets.sort(key=lambda x: str(x[0]))
        print(f"  Found {len(self.targets)} targets, will process top {self.limit}")
    
    def _format_args(self, node) -> str:
        """Format function arguments for context."""
        args = []
        for arg in node.args.args:
            arg_name = arg.arg
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    arg_name += f": {arg.annotation.id}"
                elif isinstance(arg.annotation, ast.Constant):
                    arg_name += f": {arg.annotation.value}"
            args.append(arg_name)
        return f"({', '.join(args)})"
    
    def _generate_docstring(self, node, args_str: str | None) -> str:
        """Generate appropriate docstring based on node type."""
        if isinstance(node, ast.ClassDef):
            return f'"""{node.name} class.\n\nTODO: Add class description.\n"""'
        
        # Function docstring
        func_name = node.name
        
        # Infer purpose from name
        if func_name.startswith(('get_', 'fetch_')):
            action = "Retrieve"
        elif func_name.startswith(('set_', 'update_')):
            action = "Update"
        elif func_name.startswith(('create_', 'new_')):
            action = "Create"
        elif func_name.startswith(('delete_', 'remove_')):
            action = "Remove"
        elif func_name.startswith(('is_', 'has_', 'can_')):
            action = "Check"
        elif func_name.startswith(('process_', 'handle_')):
            action = "Process"
        else:
            action = func_name.replace('_', ' ').title()
        
        doc = f'"""{action} '
        
        if args_str and args_str != '()':
            doc += f"with {args_str}."
        else:
            doc += "operation."
        
        doc += '\n\nTODO: Add detailed description and parameters.\n"""'
        return doc
    
    def implement(self) -> int:
        """Add docstrings to targets."""
        self.find_targets()
        
        print(f"\n🚀 Implementing docstrings for top {self.limit} targets...")
        
        current_file: Path | None = None
        current_content: str = ""
        current_tree = None
        
        # Group by file for efficiency
        files_to_process: dict[Path, list[tuple[ast.AST, str]]] = {}
        for py_file, node, args in self.targets[:self.limit]:
            if py_file not in files_to_process:
                files_to_process[py_file] = []
            files_to_process[py_file].append((node, args))
        
        for py_file, nodes in files_to_process.items():
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Process nodes in reverse order (bottom-up to preserve line numbers)
                for node, args in sorted(nodes, key=lambda x: -x[0].lineno):
                    docstring = self._generate_docstring(node, args)
                    
                    # Find insertion point (after def/class line)
                    insert_line = node.lineno  # 1-indexed
                    
                    # Calculate indentation
                    def_line = lines[insert_line - 1]
                    indent = len(def_line) - len(def_line.lstrip())
                    indent_str = ' ' * (indent + 4)
                    
                    # Format docstring with proper indentation
                    formatted_doc = '\n'.join(
                        indent_str + line if line.strip() else line
                        for line in docstring.split('\n')
                    )
                    
                    # Insert after definition line
                    lines.insert(insert_line, formatted_doc + '\n' + indent_str + '\n')
                    self.added += 1
                    print(f"  ✓ {py_file.name}:{insert_line} - {node.name}")
                
                # Write back
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                    
            except Exception as e:
                print(f"  ✗ Error processing {py_file}: {e}")
        
        print(f"\n✅ Added {self.added} docstrings")
        return self.added


def main():
    agent = DocstringAgent(limit=125)
    count = agent.implement()
    return 0 if count > 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
