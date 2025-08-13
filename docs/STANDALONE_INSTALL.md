# Standalone Install

This guide explains how to build and run the standalone ChattyCommander CLI using PyInstaller.

## Build

```
uv run pyinstaller --clean -y packaging/chatty_cli.spec
```

Artifacts are produced under `dist/`:
- Linux/macOS: `dist/chatty`
- Windows: `dist/chatty.exe`

## Smoke Test

```
./dist/chatty --help
./dist/chatty list
```

## Notes
- Use the Python packaging build in CI for tagged releases (prebuilt artifacts uploaded per OS).
- For advanced packaging (size optimization, data files), extend `packaging/chatty_cli.spec`.
