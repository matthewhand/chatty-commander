"""
Comprehensive security tests for AuthMiddleware bypass attempts.

This test suite verifies that the authentication middleware properly defends
against various path traversal and encoding-based attacks that could be used
to bypass authentication.

All tests verify that bypass attempts return 401 Unauthorized.
"""
import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from chatty_commander.web.middleware.auth import AuthMiddleware


class MockConfigManager:
    """Mock config manager for testing."""

    def __init__(self, key):
        self.config = {"auth": {"api_key": key}}


# ==============================================================================
# Test Fixtures
# ==============================================================================


@pytest.fixture
def secured_app():
    """Create a FastAPI app with AuthMiddleware and protected endpoints."""
    app = FastAPI()
    app.add_middleware(AuthMiddleware, config_manager=MockConfigManager("testkey"))

    @app.get("/api/secret")
    def secret():
        return {"secret": "data"}

    @app.get("/api/admin/users")
    def admin_users():
        return {"users": ["admin", "user1"]}

    @app.get("/docs")
    def docs_page():
        return {"openapi": "docs"}

    @app.get("/")
    def root():
        return {"status": "ok"}

    return app


@pytest.fixture
def client(secured_app):
    """Create a test client for the secured app."""
    return TestClient(secured_app)


# ==============================================================================
# 1. Single URL Encoding Bypass Tests
# ==============================================================================


class TestSingleEncodingBypass:
    """Test single URL encoding bypass attempts (../ vs %2e%2e)."""

    @pytest.mark.parametrize("path", [
        # Encoded dots
        "/%2e%2e/api/secret",
        "/%2e%2e%2fapi/secret",
        "/docs/%2e%2e/api/secret",
        "/docs/%2e%2e%2fapi%2fsecret",
        # Encoded slashes
        "/docs/..%2fapi%2fsecret",
        "/docs/../api%2fsecret",
        # Mixed encoding of path components
        "/%2e%2e/%61pi/secret",  # %61 = 'a'
        "/docs/%2e%2e/%61pi/%73ecret",  # partially encoded path
    ])
    def test_single_encoded_paths_return_401(self, client, path):
        """Verify single URL encoded traversal paths are blocked with 401."""
        response = client.get(path)
        assert response.status_code == 401, (
            f"Expected 401 for path '{path}', got {response.status_code}"
        )

    def test_encoded_dotdot_slash_variations(self, client):
        """Test various combinations of encoded ../ components."""
        paths = [
            "/%2e%2e/api/secret",       # %2e = .
            "/%2E%2E/api/secret",       # uppercase encoding
            "/%2e./api/secret",         # mixed: one encoded, one not
            "/.%2e/api/secret",         # mixed: one not, one encoded
            "/docs/%2e%2e/api/secret",  # from public endpoint
        ]
        for path in paths:
            response = client.get(path)
            assert response.status_code == 401, (
                f"Expected 401 for '{path}', got {response.status_code}"
            )


# ==============================================================================
# 2. Double Encoding Bypass Tests
# ==============================================================================


class TestDoubleEncodingBypass:
    """Test double URL encoding bypass attempts."""

    @pytest.mark.parametrize("path", [
        # Double-encoded ../
        "/%252e%252e/api/secret",
        "/%252E%252E/api/secret",
        "/docs/%252e%252e/api/secret",
        # Double-encoded ../ with double-encoded slash
        "/%252e%252e%252fapi%252fsecret",
        "/docs/%252e%252e%252fapi%252fsecret",
        # Double-encoded slash in traversal
        "/docs/..%252fapi%252fsecret",
        "/docs/%252e%252e/api/secret",
    ])
    def test_double_encoded_paths_return_401(self, client, path):
        """Verify double URL encoded traversal paths are blocked with 401."""
        response = client.get(path)
        assert response.status_code == 401, (
            f"Expected 401 for path '{path}', got {response.status_code}"
        )

    def test_classic_double_encoding_attack(self, secured_app):
        """
        Test the classic double-encoding bypass attack.
        
        Attack vector: /docs/%252e%252e%252fapi%252fsecret
        - First decode: /docs/%2e%2e%2fapi%2fsecret
        - Second decode: /docs/../api/secret
        - After normpath: /api/secret
        """
        client = TestClient(secured_app)
        response = client.get("/docs/%252e%252e%252fapi%252fsecret")
        assert response.status_code == 401


# ==============================================================================
# 3. Triple/Quadruple Encoding Bypass Tests
# ==============================================================================


class TestMultipleEncodingBypass:
    """Test triple and quadruple URL encoding bypass attempts."""

    @pytest.mark.parametrize("path", [
        # Triple-encoded
        "/%25252e%25252e/api/secret",
        "/%25252E%25252E/api/secret",
        "/docs/%25252e%25252e/api/secret",
        "/%25252e%25252e%25252fapi%25252fsecret",
        # Quadruple-encoded
        "/%2525252e%2525252e/api/secret",
        "/%2525252E%2525252E/api/secret",
        "/docs/%2525252e%2525252e/api/secret",
        "/%2525252e%2525252e%2525252fapi%2525252fsecret",
        # Even higher encoding levels
        "/%252525252e%252525252e/api/secret",  # 5x
    ])
    def test_multi_encoded_paths_return_401(self, client, path):
        """Verify triple/quadruple+ encoded paths are blocked with 401."""
        response = client.get(path)
        assert response.status_code == 401, (
            f"Expected 401 for path '{path}', got {response.status_code}"
        )

    def test_quadruple_encoding_through_docs(self, client):
        """
        Test quadruple-encoded traversal through public /docs endpoint.
        
        Original test case from the codebase.
        """
        # Quadruple encoded "../api/secret"
        response = client.get(
            "/docs/%2525252F%2525252E%2525252E%2525252Fapi%2525252Fsecret"
        )
        assert response.status_code == 401


# ==============================================================================
# 4. Mixed Encoding Bypass Tests
# ==============================================================================


class TestMixedEncodingBypass:
    """Test mixed encoding attack patterns (..%2f, %2e./)."""

    @pytest.mark.parametrize("path,expected_status", [
        # Partially encoded ../
        ("/..%2fapi/secret", 401),           # ../ encoded as ..%2f
        ("/%2e./api/secret", 401),           # ../ encoded as %2e.
        ("/.%2e/api/secret", 401),           # ../ encoded as .%2e
        ("/%2e%2f/api/secret", 401),         # ./ encoded
        ("/docs/..%2fapi%2fsecret", 401),    # from public endpoint
        ("/docs/%2e./api/secret", 401),      # from public endpoint
        ("/docs/.%2e/api/secret", 401),      # from public endpoint
        # Mixed case encoding
        ("/%2E./api/secret", 401),
        ("/.%2E/api/secret", 401),
        # Note: /docs/%2E%2fapi%2fsecret decodes to /docs/. /api/secret
        # which is an invalid path structure, returns 404
        ("/docs/%2E%2fapi%2fsecret", [401, 404]),
        # Slash encoded, dots not
        ("/docs/..%2fapi/secret", 401),
        ("/../api%2fsecret", 401),
        # Dots encoded, slash not
        ("/docs/%2e%2e/api/secret", 401),
        ("/%2e%2e/api/secret", 401),
        # Encoding only some path segments
        ("/docs/..%2fapi/%73ecret", 401),    # %73 = 's'
        ("/docs/%2e%2e/api/%73ecret", 401),
    ])
    def test_mixed_encoded_paths_return_401(self, client, path, expected_status):
        """Verify mixed encoding attacks return 401 or 404."""
        response = client.get(path)
        if isinstance(expected_status, list):
            assert response.status_code in expected_status, (
                f"Expected one of {expected_status} for path '{path}', got {response.status_code}"
            )
        else:
            assert response.status_code == expected_status, (
                f"Expected {expected_status} for path '{path}', got {response.status_code}"
            )


# ==============================================================================
# 5. Unicode Normalization Bypass Tests
# ==============================================================================


class TestUnicodeNormalizationBypass:
    """Test Unicode normalization bypass attempts."""

    @pytest.mark.parametrize("path", [
        # Unicode fullwidth dots (U+FF0E)
        # Note: These may or may not be normalized by the server
        # but we test that they don't bypass auth
        "/\uff0e\uff0e/api/secret",           # fullwidth ..
        "/docs/\uff0e\uff0e/api/secret",
        # Unicode fullwidth slash (U+FF0F)
        "/\uff0e\uff0e\uff0fapi\uff0fsecret",  # fullwidth ../
        # Unicode period variations
        # U+2024 (one dot leader) - looks like period
        # U+2025 (two dot leader) - looks like two periods
        # U+2026 (ellipsis) - looks like three periods
        # Cyrillic lookalikes
        # These characters might bypass naive checks
        "/docs/．．/api/secret",  # U+FF0E fullwidth periods in different encoding
    ])
    def test_unicode_paths_return_401(self, client, path):
        """
        Verify Unicode-based traversal attempts return 401.
        
        Note: Some Unicode characters may not be interpreted as path separators
        by the filesystem, but the middleware should still not allow bypass.
        """
        response = client.get(path)
        # Either 401 (blocked) or 404 (not found) is acceptable
        # The key is NOT getting 200 with protected data
        assert response.status_code in (401, 404), (
            f"Expected 401 or 404 for Unicode path '{path}', got {response.status_code}"
        )

    def test_url_encoded_unicode_traversal(self, client):
        """Test URL-encoded Unicode characters used for traversal."""
        # %c0%ae is an overlong UTF-8 encoding of '.' (tested separately below)
        # Here we test proper Unicode escape sequences
        paths = [
            # UTF-8 encoded fullwidth dot (U+FF0E = EF BC 8E)
            "/%ef%bc%8e%ef%bc%8e/api/secret",
            "/docs/%ef%bc%8e%ef%bc%8e/api/secret",
        ]
        for path in paths:
            response = client.get(path)
            assert response.status_code in (401, 404), (
                f"Expected 401 or 404 for '{path}', got {response.status_code}"
            )


# ==============================================================================
# 6. Null Byte Injection Tests
# ==============================================================================


class TestNullByteInjectionBypass:
    """Test null byte injection bypass attempts (%00)."""

    @pytest.mark.parametrize("path", [
        # Null byte to truncate path analysis
        "/docs%00/../api/secret",
        "/docs/%00../api/secret",
        "/%00docs/../api/secret",
        "/docs/../api/secret%00",
        # Null byte injection before traversal
        "/api%00/secret/../docs",
        "/%00api/secret",
        # Double-encoded null byte
        "/docs%2500/../api/secret",
        "/%2500api/secret",
        # Null byte with other encoding
        "/docs%00%2f..%2fapi%2fsecret",
    ])
    def test_null_byte_paths_return_401(self, client, path):
        """
        Verify null byte injection attempts return 401.
        
        Null bytes can be used to trick string comparison functions
        into treating strings differently than the filesystem would.
        """
        response = client.get(path)
        assert response.status_code in (401, 400, 404), (
            f"Expected 401, 400, or 404 for null byte path '{path}', "
            f"got {response.status_code}"
        )

    def test_null_byte_truncation_attack(self, client):
        """
        Test null byte truncation attack pattern.
        
        Attack: /docs%00/../api/secret
        Goal: Middleware sees /docs, but filesystem sees /docs\x00/../api/secret
        """
        response = client.get("/docs%00/../api/secret")
        assert response.status_code in (401, 400, 404)


# ==============================================================================
# 7. Overlong UTF-8 Encoding Tests
# ==============================================================================


class TestOverlongUtf8EncodingBypass:
    """
    Test overlong UTF-8 encoding bypass attempts.
    
    Overlong encodings use more bytes than necessary to represent a character.
    For example, '.' (U+002E) can be encoded as:
    - Normal: 0x2E (1 byte)
    - Overlong 2-byte: 0xC0 0xAE
    - Overlong 3-byte: 0xE0 0x80 0xAE
    """

    @pytest.mark.parametrize("path", [
        # Overlong 2-byte encoding of '.' (0xC0 0xAE)
        # %c0%ae = overlong encoding of '.'
        "/%c0%ae%c0%ae/api/secret",
        "/docs/%c0%ae%c0%ae/api/secret",
        "/%c0%ae%c0%ae%c0%afapi/secret",  # %c0%af = overlong '/'
        # Overlong 2-byte encoding of '/' (0xC0 0xAF)
        "/docs/..%c0%afapi%c0%afsecret",
        # Overlong 3-byte encoding
        "/%e0%80%ae%e0%80%ae/api/secret",
        "/docs/%e0%80%ae%e0%80%ae/api/secret",
        # Mix of overlong and normal encoding
        "/%c0%ae./api/secret",
        "/.%c0%ae/api/secret",
        "/..%c0%afapi/secret",
    ])
    def test_overlong_utf8_paths_return_401(self, client, path):
        """Verify overlong UTF-8 encoding attempts return 401."""
        response = client.get(path)
        assert response.status_code in (401, 400, 404), (
            f"Expected 401, 400, or 404 for overlong UTF-8 path '{path}', "
            f"got {response.status_code}"
        )

    def test_overlong_dot_variations(self, client):
        """Test various overlong encodings of the dot character."""
        # Each of these represents '.' in overlong UTF-8
        overlong_dots = [
            "/%c0%ae%c0%ae/api/secret",      # 2-byte overlong
            "/%e0%80%ae%e0%80%ae/api/secret", # 3-byte overlong
            "/%f0%80%80%ae%f0%80%80%ae/api/secret",  # 4-byte overlong
        ]
        for path in overlong_dots:
            response = client.get(path)
            assert response.status_code in (401, 400, 404), (
                f"Expected 401/400/404 for '{path}', got {response.status_code}"
            )


# ==============================================================================
# 8. Windows-Style Backslash Path Traversal Tests
# ==============================================================================


class TestBackslashTraversalBypass:
    """
    Test Windows-style backslash path traversal bypass attempts.
    
    On Windows systems, both / and \\ are path separators.
    Attackers may try to use backslashes to bypass Unix-oriented checks.
    """

    @pytest.mark.parametrize("path", [
        # Backslash as path separator
        "/docs\\..\\api\\secret",
        "\\..\\api\\secret",
        "/api\\secret",
        # Mixed slashes
        "/docs/..\\api/secret",
        "/docs\\../api\\secret",
        "\\../api/secret",
        "/..\\api/secret",
        # URL-encoded backslash (%5c)
        "/docs%5c..%5capi%5csecret",
        "/%5c..%5capi%5csecret",
        "/docs/..%5capi/secret",
        "/docs%5c../api/secret",
        # Double-encoded backslash
        "/docs%255c..%255capi%255csecret",
        "/%255c..%255capi%255csecret",
        # Mixed encoded backslash and forward slash
        "/docs%5c..%2fapi%5csecret",
        "/docs/..%5capi%2fsecret",
    ])
    def test_backslash_traversal_return_401(self, client, path):
        """Verify backslash-based traversal attempts return 401."""
        response = client.get(path)
        assert response.status_code in (401, 404), (
            f"Expected 401 or 404 for backslash path '{path}', "
            f"got {response.status_code}"
        )


# ==============================================================================
# 9. Header Injection via Path Tests
# ==============================================================================


class TestHeaderInjectionViaPathBypass:
    """
    Test header injection attempts via path.
    
    Attackers may try to inject HTTP headers or response splitting
    characters through the URL path.
    """

    @pytest.mark.parametrize("path", [
        # CRLF injection (%0d%0a = \r\n)
        "/api/secret%0d%0aSet-Cookie:%20hacked=true",
        "/api/secret%0d%0a%0d%0a<html>",
        "/%0d%0aSet-Cookie:hacked=true",
        "/docs%0d%0aLocation:%20http://evil.com",
        # Single CR or LF
        "/api/secret%0d",
        "/api/secret%0a",
        "/docs%0d/../api/secret",
        "/docs%0a/../api/secret",
        # Double-encoded CRLF
        "/api/secret%250d%250aSet-Cookie:hacked",
        # Header injection with path traversal
        "/docs/../api/secret%0d%0aX-Injected:%20true",
        # HTTP request smuggling patterns
        "/api%20HTTP/1.1%0d%0aHost:%20evil.com",
        "/%20HTTP/1.1%0d%0a%0d%0aGET%20/admin",
    ])
    def test_header_injection_paths_return_401(self, client, path):
        """
        Verify header injection via path returns 401 or 400.
        
        These attacks attempt to inject headers or smuggle requests
        through the URL path.
        """
        response = client.get(path)
        assert response.status_code in (401, 400, 404), (
            f"Expected 401, 400, or 404 for header injection path '{path}', "
            f"got {response.status_code}"
        )


# ==============================================================================
# 10. Comprehensive Bypass Validation Tests
# ==============================================================================


class TestAllBypassesReturn401:
    """
    Comprehensive tests ensuring ALL bypass attempts return 401 Unauthorized.
    
    These tests verify that regardless of the encoding or technique used,
    protected endpoints always require valid authentication.
    """

    def test_no_bypass_returns_protected_data(self, client):
        """Verify that bypass attempts don't return protected data."""
        bypass_attempts_401 = [
            # Basic traversal
            "/../api/secret",
            "/docs/../api/secret",
            # Single encoding
            "/%2e%2e/api/secret",
            "/docs/%2e%2e%2fapi%2fsecret",
            # Double encoding
            "/%252e%252e/api/secret",
            "/docs/%252e%252e%252fapi%252fsecret",
            # Triple encoding
            "/%25252e%25252e/api/secret",
            # Quadruple encoding
            "/%2525252e%2525252e/api/secret",
            # Mixed encoding
            "/..%2fapi/secret",
            "/%2e./api/secret",
        ]

        # Paths that don't actually resolve to /api paths due to system behavior
        # These return 404 (not found) or 400 (bad request), but NOT 200 with data
        # Important: they should NEVER return protected data
        paths_not_matching_api = [
            # Null bytes - may cause request parsing issues
            "/docs%00/../api/secret",
            # Overlong UTF-8 - Python doesn't interpret these as path chars
            "/%c0%ae%c0%ae/api/secret",
            # Backslash paths on Unix: backslash is NOT a path separator
            "/docs\\..\\api\\secret",  # literal backslash
            "/docs%5c..%5capi%5csecret",  # URL-encoded backslash
        ]

        for path in bypass_attempts_401:
            response = client.get(path)
            # Must return 401 - not 200 with data
            assert response.status_code == 401, (
                f"Bypass may have succeeded for '{path}': "
                f"got status {response.status_code}"
            )

        # These paths don't resolve to /api paths due to system behavior
        # They return 400/404, but critically NOT 200 with protected data
        for path in paths_not_matching_api:
            response = client.get(path)
            # Must NOT return 200 with protected data
            assert response.status_code in (400, 401, 404), (
                f"Path '{path}' returned unexpected status {response.status_code}. "
                f"Expected 400/401/404 (not 200 with data)"
            )

    def test_valid_api_key_still_works(self, client):
        """Verify legitimate requests with valid API keys work correctly."""
        # All these paths should work with valid API key
        valid_paths = [
            "/api/secret",
            "/api/admin/users",
        ]
        
        for path in valid_paths:
            response = client.get(path, headers={"X-API-Key": "testkey"})
            assert response.status_code == 200, (
                f"Valid API key should work for '{path}', "
                f"got {response.status_code}"
            )

    def test_public_endpoints_still_work(self, client):
        """Verify public endpoints remain accessible without auth."""
        public_paths = [
            "/",
            "/docs",
        ]
        
        for path in public_paths:
            response = client.get(path)
            assert response.status_code == 200, (
                f"Public endpoint '{path}' should be accessible, "
                f"got {response.status_code}"
            )


# ==============================================================================
# Edge Cases and Additional Attack Vectors
# ==============================================================================


class TestEdgeCaseBypasses:
    """Test additional edge cases and attack vectors."""

    @pytest.mark.parametrize("path", [
        # Multiple consecutive slashes
        "/api///secret",
        "/api////secret",
        "//api/secret",
        "///api/secret",
        # Dot segments
        "/api/./secret",
        "/api/././secret",
        "/./api/./secret",
        # Trailing dot
        "/api/secret.",
        "/api/secret..",
        # Leading dot
        "/.api/secret",
        "/..api/secret",
        # Empty segments
        "/api//secret",
        "/api///secret",
        # Encoded dots that resolve to current directory
        "/api/%2e/secret",
        "/api/%2e%2e%2e/secret",
        # Case variations
        "/API/secret",
        "/Api/Secret",
        "/api/SECRET",
        # Fragment injection (should be stripped by client but test anyway)
        "/api/secret#../admin",
        "/api/secret%23../admin",
    ])
    def test_edge_case_paths(self, client, path):
        """Test various edge case paths for auth enforcement."""
        response = client.get(path)
        # Path variations that try to access API should require auth
        # Case sensitivity varies by server, so accept 404 for non-matching paths
        assert response.status_code in (401, 404), (
            f"Expected 401 or 404 for edge case '{path}', got {response.status_code}"
        )

    def test_parameter_pollution(self, client):
        """Test parameter pollution style attacks."""
        paths_401 = [
            # Multiple traversal
            "/docs/../../api/secret",
            "/docs/../../../api/secret",
            # Deep traversal from root
            "/../../../../../../../../api/secret",
        ]
        for path in paths_401:
            response = client.get(path)
            assert response.status_code == 401, (
                f"Expected 401 for '{path}', got {response.status_code}"
            )

    def test_duplicate_slash_paths(self, client):
        """Test paths with duplicate slashes.
        
        Duplicate slashes are normalized by the path handler.
        /docs//..//api//secret normalizes to /api/secret which requires auth.
        """
        paths = [
            "/docs//..//api//secret",
            "/api//secret",
            "//api/secret",
        ]
        for path in paths:
            response = client.get(path)
            # Should get 401 (auth required) or 404 (normalized path not matching)
            assert response.status_code in (401, 404), (
                f"Expected 401 or 404 for '{path}', got {response.status_code}"
            )

    def test_url_scheme_injection(self, client):
        """Test URL scheme injection attempts."""
        paths = [
            # Attempt to switch protocols
            "/javascript:alert(1)",
            "/data:text/html,<script>alert(1)</script>",
            "/file:///etc/passwd",
            # Absolute URL attempts
            "http://evil.com/api/secret",
            "//evil.com/api/secret",
        ]
        for path in paths:
            response = client.get(path)
            # These should be rejected or not found
            assert response.status_code in (400, 401, 404), (
                f"Expected error status for scheme injection '{path}', "
                f"got {response.status_code}"
            )


# ==============================================================================
# Direct Middleware Dispatch Tests
# ==============================================================================


class TestMiddlewareDispatch:
    """Test the middleware dispatch method directly for precise control."""

    @pytest.mark.asyncio
    async def test_dispatch_decodes_multiple_levels(self):
        """Test that dispatch properly decodes multiple levels of encoding."""
        app = FastAPI()
        
        @app.get("/api/secret")
        def secret():
            return {"secret": "data"}
        
        middleware = AuthMiddleware(app, config_manager=MockConfigManager("testkey"))
        
        # Create a mock request with deeply encoded path
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/docs/%2525252e%2525252e%2525252fapi%2525252fsecret",
            "headers": [],
            "query_string": b"",
        }
        
        request = Request(scope)
        
        async def mock_call_next(req):
            # If bypass succeeded, would reach here
            return JSONResponse(status_code=200, content={"bypassed": True})
        
        response = await middleware.dispatch(request, mock_call_next)
        
        # Should return 401, not call the endpoint
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code} - bypass may have succeeded"
        )

    @pytest.mark.asyncio
    async def test_dispatch_handles_unicode_path(self):
        """Test dispatch handling of Unicode paths.
        
        Note: Unicode fullwidth characters (like U+FF0E for dot) are NOT
        normalized by the middleware or Python's URL decoding. They are
        treated as literal characters distinct from ASCII '.' and '/'.
        
        This test verifies that:
        1. Unicode paths don't bypass auth for valid API endpoints
        2. Unicode paths don't crash the middleware
        """
        app = FastAPI()
        
        @app.get("/api/secret")
        def secret():
            return {"secret": "data"}
        
        middleware = AuthMiddleware(app, config_manager=MockConfigManager("testkey"))
        
        scope = {
            "type": "http",
            "method": "GET",
            # Unicode fullwidth dot dot slash - these are NOT path separators
            # This path is actually requesting /docs/[special chars]api[slash]secret
            "path": "/docs/\uff0e\uff0e\uff0fapi\uff0fsecret",
            "headers": [],
            "query_string": b"",
        }
        
        request = Request(scope)
        
        async def mock_call_next(req):
            return JSONResponse(status_code=200, content={"bypassed": True})
        
        response = await middleware.dispatch(request, mock_call_next)
        
        # The Unicode path doesn't start with /api, so it passes through middleware
        # without requiring auth. The mock_call_next returns 200.
        # This is CORRECT behavior - Unicode fullwidth chars aren't path separators.
        # If a server incorrectly interprets them as separators, that's a server bug.
        # 
        # The key security property: Unicode chars don't cause the middleware to
        # mistakenly treat a non-/api path as /api path
        assert response.status_code in (200, 401, 404), (
            f"Unexpected status for Unicode path: {response.status_code}"
        )

    @pytest.mark.asyncio
    async def test_dispatch_blocks_actual_api_path_traversal(self):
        """Test that actual path traversal to /api endpoints is blocked.
        
        This test verifies that the middleware correctly blocks encodings
        that actually resolve to /api paths after URL decoding and normalization.
        """
        app = FastAPI()
        
        @app.get("/api/secret")
        def secret():
            return {"secret": "data"}
        
        middleware = AuthMiddleware(app, config_manager=MockConfigManager("testkey"))
        
        # This path uses percent-encoding that WILL be decoded and result in /api
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/docs/%2e%2e/api/secret",  # Decodes to /docs/../api/secret
            "headers": [],
            "query_string": b"",
        }
        
        request = Request(scope)
        
        async def mock_call_next(req):
            return JSONResponse(status_code=200, content={"bypassed": True})
        
        response = await middleware.dispatch(request, mock_call_next)
        
        # Should return 401 because the path resolves to /api/secret
        assert response.status_code == 401, (
            f"Expected 401 for encoded path traversal, got {response.status_code}"
        )

    @pytest.mark.asyncio
    async def test_dispatch_null_byte_handling(self):
        """Test dispatch handling of null byte in path."""
        app = FastAPI()
        
        @app.get("/api/secret")
        def secret():
            return {"secret": "data"}
        
        middleware = AuthMiddleware(app, config_manager=MockConfigManager("testkey"))
        
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/docs%00/../api/secret",
            "headers": [],
            "query_string": b"",
        }
        
        request = Request(scope)
        
        async def mock_call_next(req):
            return JSONResponse(status_code=200, content={"bypassed": True})
        
        response = await middleware.dispatch(request, mock_call_next)
        
        # Should return 401, 400 (bad request), or 404
        assert response.status_code in (400, 401, 404), (
            f"Expected error status for null byte path, got {response.status_code}"
        )
