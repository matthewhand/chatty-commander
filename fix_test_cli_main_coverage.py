import re
with open("tests/test_cli_main_coverage.py", "r") as f:
    content = f.read()

# Replace global import mocking with dictionary patching
content = content.replace('original_import = builtins.__import__\n', '')
content = content.replace('with patch("builtins.__import__", side_effect=mock_import):\n', 'with patch.dict("sys.modules", {"chatty_commander.web.web_mode": MagicMock()}):\n')

with open("tests/test_cli_main_coverage.py", "w") as f:
    f.write(content)
