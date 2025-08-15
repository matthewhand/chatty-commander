import pathlib
import py_compile
import re

SERVER = pathlib.Path("src/chatty_commander/web/server.py")

def test_server_compiles():
    py_compile.compile(str(SERVER), doraise=True)

def test_optional_router_includes_are_guarded():
    text = SERVER.read_text()
    # No direct include_router(version_router|metrics_router|agents_router)
    # unless preceded nearby by our globals().get guard.
    danger = re.compile(r'app\\.include_router\\((version_router|metrics_router|agents_router)\\)')
    lines = text.splitlines()
    violations = []
    for i, ln in enumerate(lines):
        if danger.search(ln):
            window = "\n".join(lines[max(0, i-6):i+1])
            if "globals().get(" not in window or "_r =" not in window:
                violations.append((i+1, ln.strip()))
    assert not violations, f"unguarded router includes: {violations}"
