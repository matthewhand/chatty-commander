from unittest.mock import MagicMock
import sys

# Mock FastAPI since it's not installed in the environment
mock_fastapi = MagicMock()
sys.modules["fastapi"] = mock_fastapi
sys.modules["fastapi.middleware.cors"] = MagicMock()
sys.modules["fastapi.openapi.docs"] = MagicMock()

from chatty_commander.web.auth import apply_cors

def test_apply_cors_no_auth_new():
    app = MagicMock()
    app.user_middleware = []
    apply_cors(app, no_auth=True)

    # Check that add_middleware was called
    app.add_middleware.assert_called()
    args, kwargs = app.add_middleware.call_args

    # Verify that allow_origins does NOT contain "*"
    allow_origins = kwargs["allow_origins"]
    assert "*" not in allow_origins
    assert "http://localhost:3000" in allow_origins
    assert "http://localhost:5173" in allow_origins

    # Credentials should be allowed when not using wildcard
    # The fix ensures "*" is removed, so allow_credentials becomes True
    assert kwargs["allow_credentials"] is True

def test_apply_cors_with_auth_default():
    app = MagicMock()
    app.user_middleware = []
    apply_cors(app, no_auth=False)

    args, kwargs = app.add_middleware.call_args
    assert kwargs["allow_origins"] == ["http://localhost:3000"]
    assert kwargs["allow_credentials"] is True

def test_apply_cors_custom_origins():
    app = MagicMock()
    app.user_middleware = []
    apply_cors(app, no_auth=False, origins=["http://example.com"])

    args, kwargs = app.add_middleware.call_args
    assert kwargs["allow_origins"] == ["http://example.com"]

if __name__ == "__main__":
    test_apply_cors_no_auth_new()
    test_apply_cors_with_auth_default()
    test_apply_cors_custom_origins()
    print("All tests passed!")
