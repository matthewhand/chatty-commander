import secrets
from unittest.mock import patch, MagicMock

import pytest

# Testing chatty_commander.web.middleware.auth
from chatty_commander.web.middleware.auth import AuthMiddleware

class DummyConfig:
    def __init__(self, auth):
        self.auth = auth

@patch('secrets.compare_digest', wraps=secrets.compare_digest)
def test_auth_middleware_compare_digest(mock_compare_digest):
    app = MagicMock()
    config_manager = DummyConfig(auth={'api_key': 'secret123'})
    middleware = AuthMiddleware(app, config_manager, no_auth=False)

    import asyncio

    # We will mock the next call to return a success response
    async def call_next(request):
        return MagicMock(status_code=200)

    request = MagicMock()
    request.url.path = '/api/v1/something'
    request.method = 'GET'

    # Valid key
    request.headers.get.return_value = 'secret123'
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(middleware.dispatch(request, call_next))
    assert res.status_code == 200
    assert mock_compare_digest.call_count == 1
    mock_compare_digest.assert_called_with('secret123', 'secret123')

    # Invalid key
    request.headers.get.return_value = 'wrong'
    res = loop.run_until_complete(middleware.dispatch(request, call_next))
    assert res.status_code == 401
    assert mock_compare_digest.call_count == 2
    mock_compare_digest.assert_called_with('wrong', 'secret123')

    # Null key
    request.headers.get.return_value = None
    res = loop.run_until_complete(middleware.dispatch(request, call_next))
    assert res.status_code == 401
    assert mock_compare_digest.call_count == 2 # Not called because of null check
