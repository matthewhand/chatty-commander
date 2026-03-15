import re
from pathlib import Path

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    if 'from __future__ import annotations' not in content:
        return

    # Remove the import
    content = content.replace('from __future__ import annotations\n', '')

    # Replace new typing hints with old ones where needed if pydantic models exist
    if 'class ' in content and '(BaseModel):' in content:
        content = content.replace('list[', 'List[')
        content = content.replace('dict[', 'Dict[')
        content = content.replace(' | None', ' | None') # We need Union or Optional but actually Python 3.10+ supports | None, the issue is that stringified annotations from __future__ break it in FastAPI's lenient_issubclass. So removing __future__ is enough if we run on 3.11. But wait, `list[str]` will throw an error if used as a type annotation in Python 3.8. But we are on Python 3.11 here.
        # So removing `from __future__ import annotations` is the real fix.

        # Let's make sure `List` and `Dict` are imported if we replaced them.
        if 'List[' in content and 'List' not in content:
            content = content.replace('from typing import ', 'from typing import List, ')
            if 'from typing import List, \n' in content:
                 content = content.replace('from typing import List, \n', 'from typing import List\n')
        if 'Dict[' in content and 'Dict' not in content:
            if 'from typing import ' in content:
                content = content.replace('from typing import ', 'from typing import Dict, ')
            else:
                content = 'from typing import Dict\n' + content

    with open(filepath, 'w') as f:
        f.write(content)

for p in Path('src/chatty_commander/web/routes').glob('*.py'):
    process_file(p)
