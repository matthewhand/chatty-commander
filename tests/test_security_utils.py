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

try:
    import pytest
except ImportError:
    pytest = None
from chatty_commander.utils.security import mask_sensitive_data

def test_mask_sensitive_data():
    """Test that sensitive configuration data is correctly masked."""
    test_data = {
        "api_key": "sk-sensitive-key",
        "OPENAI_API_TOKEN": "token-123",
        "db_password": "mypassword",
        "database_url": "postgresql://user:pass@host/db",
        "normal_field": "visible-value",
        "nested": {
            "bridge_token": "secret-bridge",
            "count": 10
        },
        "auth": {
            "username": "admin",
            "password": "hidden-password"
        },
        "secrets_list": [
            {"secret": "val1"},
            {"public": "val2"}
        ]
    }

    masked = mask_sensitive_data(test_data)

    # Check top-level masking
    assert masked["api_key"] == "********"
    assert masked["OPENAI_API_TOKEN"] == "********"
    assert masked["db_password"] == "********"
    assert masked["database_url"] == "********"
    assert masked["normal_field"] == "visible-value"

    # Check nested masking
    assert masked["nested"]["bridge_token"] == "********"
    assert masked["nested"]["count"] == 10

    # Check auth special case
    assert masked["auth"]["username"] == "admin"
    assert masked["auth"]["password"] == "********"

    # Check list masking - the whole list is masked because the key contains 'secret'
    assert masked["secrets_list"] == "********"

def test_mask_sensitive_data_non_dict():
    """Test masking logic with non-dictionary inputs."""
    assert mask_sensitive_data("string") == "string"
    assert mask_sensitive_data(123) == 123
    assert mask_sensitive_data([1, 2, 3]) == [1, 2, 3]

    # List of dicts
    data_list = [{"api_key": "secret"}, {"other": "public"}]
    masked_list = mask_sensitive_data(data_list)
    assert masked_list[0]["api_key"] == "********"
    assert masked_list[1]["other"] == "public"

if __name__ == "__main__":
    test_mask_sensitive_data()
    test_mask_sensitive_data_non_dict()
    print("Security utils tests passed!")
