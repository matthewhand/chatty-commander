import unittest
from unittest.mock import MagicMock
import sys
import os

# The environment lacks FastAPI and Pydantic.
# We mock them to allow importing the module under test.
class MockHTTPException(Exception):
    def __init__(self, status_code, detail=None):
        self.status_code = status_code
        self.detail = detail

mock_fastapi = MagicMock()
mock_fastapi.HTTPException = MockHTTPException
mock_pydantic = MagicMock()
sys.modules["fastapi"] = mock_fastapi
sys.modules["pydantic"] = mock_pydantic

from src.chatty_commander.web.validation import sanitize_config_data

class TestConfigSanitization(unittest.TestCase):
    def test_sanitize_config_data_benign(self):
        data = {
            "key1": "value1",
            "nested": {"key2": "value2"},
            "list": ["item1", 123, True]
        }
        result = sanitize_config_data(data)
        self.assertEqual(result, {
            "key1": "value1",
            "nested": {"key2": "value2"},
            "list": ["item1", 123, True]
        })

    def test_sanitize_config_data_dangerous_key(self):
        dangerous_data = {"__proto__": "evil"}
        with self.assertRaises(MockHTTPException) as cm:
            sanitize_config_data(dangerous_data)
        self.assertEqual(cm.exception.status_code, 400)
        self.assertIn("potentially dangerous key", cm.exception.detail)

    def test_sanitize_config_data_dangerous_key_case_insensitive(self):
        dangerous_data = {"CONSTRUCTOR": "evil"}
        with self.assertRaises(MockHTTPException) as cm:
            sanitize_config_data(dangerous_data)
        self.assertEqual(cm.exception.status_code, 400)
        self.assertIn("potentially dangerous key", cm.exception.detail)

    def test_sanitize_config_data_dangerous_value(self):
        dangerous_data = {"key": "<script>alert(1)</script>"}
        with self.assertRaises(MockHTTPException) as cm:
            sanitize_config_data(dangerous_data)
        self.assertEqual(cm.exception.status_code, 400)
        self.assertIn("potentially dangerous script content", cm.exception.detail)

    def test_sanitize_config_data_dangerous_value_nested(self):
        dangerous_data = {"nested": {"key": "javascript:alert(1)"}}
        with self.assertRaises(MockHTTPException) as cm:
            sanitize_config_data(dangerous_data)
        self.assertEqual(cm.exception.status_code, 400)
        self.assertIn("potentially dangerous script content", cm.exception.detail)

    def test_sanitize_config_data_whitespace_trimming(self):
        data = {"key": "  trimmed  "}
        result = sanitize_config_data(data)
        self.assertEqual(result["key"], "trimmed")

    def test_sanitize_config_data_not_dict(self):
        with self.assertRaises(MockHTTPException) as cm:
            sanitize_config_data(["not", "a", "dict"])
        self.assertEqual(cm.exception.status_code, 400)
        self.assertIn("must be a dictionary", cm.exception.detail)

if __name__ == "__main__":
    unittest.main()
