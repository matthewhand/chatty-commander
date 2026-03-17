with open("tests/test_cli_cli_coverage.py", "r") as f:
    content = f.read()

content = content.replace('original_import = builtins.__import__\n', '')
content = content.replace('with patch("builtins.__import__", side_effect=mock_import):\n', 'with patch.dict("sys.modules", {"chatty_commander.web.web_mode": MagicMock()}):\n')

with open("tests/test_cli_cli_coverage.py", "w") as f:
    f.write(content)
