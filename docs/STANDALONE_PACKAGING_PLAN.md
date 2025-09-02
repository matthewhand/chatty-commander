# Standalone Packaging Plan

Goal

- Provide cross-platform standalone executables for ChattyCommander so end users can run `chatty` without Python preinstalled.

Deliverables

- Single-file (one EXE/app) and single-folder builds for:
  - Windows (x64)
  - macOS (x64/arm64)
  - Linux (x64)
- Artifacts published from CI for tagged releases.

Primary toolchain

- PyInstaller (primary) for broad compatibility and ease of setup.
- Alternatives to evaluate (optional):
  - Nuitka (performance-focused)
  - PyOxidizer (smaller size, faster startup, more complex)

Entrypoints

- CLI: `chatty_commander.cli.cli:cli_main` (console application)
- Optional GUI wrapper: `chatty_commander.gui:main` (if a GUI entry becomes first-class)
- Web server entry (if packaged separately): `chatty_commander.web.server:main`

Packaging considerations

- Hidden imports: ensure dynamic imports are listed if needed (e.g., for FastAPI/Uvicorn, websockets).
- Data files:
  - Include minimal static assets if required at runtime (webui HTML, CSS/JS for local demo only). Production web frontend is separate.
  - Exclude tests, cache, and dev-only content.
- On Windows, ensure console vs windowed mode is appropriate (console for CLI, windowed for GUI build).
- Versioning: embed version info from `pyproject.toml`.

Sample PyInstaller spec (CLI)

```
# file: packaging/chatty_cli.spec
# Generate baseline with: pyinstaller --name chatty --onefile -F -p src -c -i icon.ico -s run_cli.py
# Then customize as needed.
# Example program script wrapper (run_cli.py) simply imports and runs cli_main.

block_cipher = None

a = Analysis(
    ['run_cli.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        # (src, dest) tuples for any runtime files if needed
        # ('src/chatty_commander/webui/avatar/index.html', 'webui/avatar'),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tests', 'htmlcov', 'webui/frontend'],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='chatty',
    debug=False,
    strip=False,
    upx=True,
    console=True,
)
```

Wrapper script for CLI (run_cli.py)

```
# packaging/run_cli.py
from chatty_commander.cli.cli import cli_main

if __name__ == '__main__':
    cli_main()
```

Makefile targets (proposed)

- `make build-exe` (current OS)
- `make build-exe-all` (matrix via CI)
- `make dist-clean` (remove build artifacts)

CI/CD plan

- GitHub Actions matrix: {ubuntu-latest, windows-latest, macos-latest}
- Steps:
  1. Checkout
  1. Setup Python 3.11
  1. pip install .\[dev\] pyinstaller
  1. Build using spec
  1. Upload artifacts on push tags
- Optional: code signing and notarization (macOS), Authenticode (Windows)

Smoke tests for artifacts

- Run `chatty --help` and `chatty gui --help`
- Run a minimal CLI command: `chatty list`
- Ensure exit codes correct and no missing imports.

Documentation updates

- README: Installation via pip vs standalone binaries
- docs/DEVELOPER_SETUP.md: developer flow for building local executables

Open questions / future enhancements

- Add Nuitka recipe for performance-sensitive users
- Bundle minimal models or fetch on first run?
- Optional plugin system to reduce bundled size
