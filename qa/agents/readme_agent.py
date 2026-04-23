#!/usr/bin/env python3
"""
README IMPLEMENTATION AGENT
Completes missing README sections identified by Documentation Agent.
"""

import re
from pathlib import Path


class ReadmeAgent:
    """Enhances README with missing sections."""
    
    REQUIRED_SECTIONS = [
        ('installation', '## Installation', '''## Installation

```bash
# Clone the repository
git clone https://github.com/mhand/chatty-commander.git
cd chatty-commander

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### Prerequisites

- Python 3.10+
- pip or poetry
'''),
        ('usage', '## Usage', '''## Usage

### CLI Mode

```bash
# Run with default settings
chatty-commander

# Run in web mode
chatty-commander web --port 8080

# Run with specific config
chatty-commander --config my_config.json
```

### Python API

```python
from chatty_commander.app.orchestrator import main_loop

# Start the voice assistant
main_loop()
```
'''),
        ('configuration', '## Configuration', '''## Configuration

ChattyCommander uses JSON configuration files:

```json
{
  "wake_words": ["hey computer", "ok chatty"],
  "model_actions": {
    "open_browser": {
      "type": "url",
      "url": "https://google.com"
    }
  }
}
```

See `config.example.json` for full options.
'''),
    ]
    
    def __init__(self, project_path: str = "/home/matthewh/chatty-commander"):
        self.project_path = Path(project_path)
        self.readme_path = self.project_path / "README.md"
    
    def analyze_readme(self) -> tuple[bool, list[str], str]:
        """Analyze current README and find missing sections."""
        print("🔍 Analyzing README...")
        
        if not self.readme_path.exists():
            print("  ✗ README.md not found!")
            return False, [s[0] for s in self.REQUIRED_SECTIONS], ""
        
        with open(self.readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content_lower = content.lower()
        
        missing = []
        for keyword, header, template in self.REQUIRED_SECTIONS:
            if keyword not in content_lower:
                missing.append((keyword, header, template))
        
        print(f"  Current README: {len(content)} characters")
        print(f"  Missing sections: {len(missing)}")
        
        return True, missing, content
    
    def _find_insertion_point(self, content: str) -> int:
        """Find best place to insert new sections."""
        # Look for existing headers
        headers = list(re.finditer(r'^## ', content, re.MULTILINE))
        
        if not headers:
            # No headers, append at end
            return len(content)
        
        # Find a good position - after first couple sections
        if len(headers) >= 2:
            # Insert after second header
            return headers[1].start()
        
        # Insert after first header
        return headers[0].start()
    
    def implement(self) -> int:
        """Add missing sections to README."""
        exists, missing, content = self.analyze_readme()
        
        if not missing:
            print("\n✅ README is complete!")
            return 0
        
        print(f"\n🚀 Adding {len(missing)} missing sections...")
        
        added_count = 0
        
        for keyword, header, template in missing:
            # Check if section still missing
            if keyword in content.lower():
                print(f"  ⚠️ {keyword} section already added")
                continue
            
            # Find insertion point
            insert_pos = self._find_insertion_point(content)
            
            # Insert the new section
            new_section = f"\n\n{template}\n"
            
            content = content[:insert_pos] + new_section + content[insert_pos:]
            
            added_count += 1
            print(f"  ✓ Added {keyword} section")
        
        # Write back
        if added_count > 0:
            with open(self.readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"\n✅ Enhanced README with {added_count} sections")
        print(f"   New length: {len(content)} characters")
        
        return added_count


def main():
    agent = ReadmeAgent()
    count = agent.implement()
    return 0 if count >= 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
