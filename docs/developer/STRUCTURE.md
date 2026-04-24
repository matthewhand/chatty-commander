# Project Structure

This document provides a quick reference for the Chatty Commander project organization.

## 📁 Current Directory Structure

```
chatty-commander/
├── config.json                 # Main configuration file
├── config.json.example         # Example configuration
├── pyproject.toml              # Project metadata and dependencies
├── README.md                   # Project overview
├── models-chatty/             # Conversational AI models and prompts
├── models-computer/           # Wake word detection models
├── models-idle/               # Idle state models
├── deploy/                    # Deployment configurations
│   └── Dockerfile              # Container definition
├── docs/                      # Documentation
│   ├── developer/             # Developer guides (ARCHITECTURE.md, etc.)
│   ├── user-guide/            # End-user documentation
│   └── screenshots/           # UI screenshots (auto-generated)
├── scripts/                   # Utility scripts
│   └── validate_screenshots.py # Visual regression script (NEW!)
├── src/chatty_commander/      # Main Python package
│   ├── ai/                    # AI core and intelligence
│   ├── app/                   # Application logic, config, state
│   ├── advisors/              # Advisor services and conversation context
│   ├── avatars/               # Voice avatar configurations
│   ├── cli/                   # Command-line interface
│   ├── cv/                    # ⭐ Computer Vision module (NEW!)
│   │   ├── __init__.py
│   │   ├── comparator.py       # Image comparison algorithms
│   │   └── validator.py        # Validation logic
│   ├── gui/                   # GUI components (tray, webview)
│   ├── llm/                   # LLM provider adapters
│   ├── models/                # Model management
│   ├── obs/                   # Observability and metrics
│   ├── providers/             # External service providers
│   ├── tools/                 # Utility tools
│   ├── voice/                 # Voice processing (STT, TTS, wake word)
│   └── web/                   # FastAPI web server and routes
│   └── webui/                 # Web frontend components
├── tests/                     # Python backend tests (54+ files)
│   ├── test_web_server.py      # FastAPI server tests
│   ├── test_voice.py           # Voice processing tests
│   ├── test_cv_validator.py    # ⭐ Computer Vision tests (NEW!)
│   └── ... (50+ more test files)
├── webui/frontend/            # React + Vite frontend application
│   └── tests/e2e/             # Playwright E2E tests
│       ├── screenshots.spec.ts # Screenshot journeys (NEW!)
│       ├── basic.spec.ts       # Basic functionality tests
│       └── ... (15+ test files)
└── .github/workflows/         # CI/CD pipelines
    ├── screenshots.yml         # Documentation screenshot generation
    └── visual-regression.yml  # Visual regression testing (NEW!)
```

## ✨ What's NEW in This Version

### Computer Vision Module (`src/chatty_commander/cv/`)
- **Status**: ✅ **IMPLEMENTED** (previously placeholder)
- **Purpose**: Visual validation of screenshots
- **Features**:
  - SSIM-based image comparison
  - OCR text extraction and validation
  - Color scheme validation
  - Layout/element position validation
  - Visual regression testing

### Enhanced Screenshot Testing
- **5 Sequential User Journeys** capturing full UX flows
- **44+ Screenshots** (was 6, now includes mobile responsive)
- **Visual Regression CI/CD** via `.github/workflows/visual-regression.yml`
- **Validation Script** at `scripts/validate_screenshots.py`

### Documentation Updates
- `docs/TESTING.md` - Comprehensive testing guide
- Updated `docs/developer/ARCHITECTURE.md` - Corrected module status
- This file - Now accurate to actual structure

## 🎯 Quick Navigation

### Development

| Purpose | Location |
|---------|----------|
| **Core Logic** | `src/chatty_commander/` |
| **Configuration** | `config.json`, `config.json.example` |
| **Tests (Python)** | `tests/` |
| **Tests (E2E)** | `webui/frontend/tests/e2e/` |
| **Documentation** | `docs/` |
| **Scripts** | `scripts/` |

### Frontend Development

| Component | Location |
|-----------|----------|
| **Web UI (React)** | `webui/frontend/` |
| **Web Backend (FastAPI)** | `src/chatty_commander/web/` |
| **GUI (tray, webview)** | `src/chatty_commander/gui/` |

### Backend Development

| Component | Location |
|-----------|----------|
| **Application Core** | `src/chatty_commander/app/` |
| **AI/Advisors** | `src/chatty_commander/advisors/` and `src/chatty_commander/ai/` |
| **LLM Providers** | `src/chatty_commander/llm/` |
| **Voice Processing** | `src/chatty_commander/voice/` |
| **Computer Vision** | `src/chatty_commander/cv/` ⭐ |

### AI/ML Development

| Models | Location |
|--------|----------|
| **Conversational AI** | `models-chatty/` |
| **Wake Words** | `models-computer/` |
| **Idle State** | `models-idle/` |
| **Model Adapters** | `src/chatty_commander/llm/` |

## 📝 Notes on Structure Evolution

### What Was Documented vs. What Was Implemented

The previous version of this document described a **planned** structure that included:
- `frontend/desktop-app/` - ❌ **Not implemented**
- `frontend/web-app/` - ❌ **Not implemented** (actual: `webui/frontend/`)
- `models/` - ❌ **Not implemented** (actual: `models-*` dirs)
- `server/` - ❌ **Not implemented**
- `server/workers/` - ❌ **Not implemented**

### Current Reality

The project has evolved with a **pragmatic, working structure**:

1. **`src/chatty_commander/`** - All Python backend code
2. **`webui/frontend/`** - React frontend (not `frontend/web-app/`)
3. **`models-*` directories** - Model files at project root
4. **No `server/` directory** - Server logic in `src/chatty_commander/web/`
5. **`cv/` module** - NEW: Computer Vision capabilities

This structure is **proven by extensive tests** and **actively used in production**.

## 🔧 Key Directories Explained

### `src/chatty_commander/` - Core Package

| Directory | Purpose | Test Coverage |
|-----------|---------|---------------|
| `ai/` | AI intelligence, intent detection | ✅ Yes |
| `app/` | Configuration, state management | ✅ Yes |
| `advisors/` | Conversation context, personas | ✅ Yes |
| `cli/` | Command-line interface | ✅ Yes |
| `cv/` | **Computer Vision** (NEW!) | ✅ `test_cv_validator.py` |
| `gui/` | System tray, webview | ✅ Yes |
| `llm/` | LLM provider adapters | ✅ Yes |
| `voice/` | Wake word, STT, TTS | ✅ Yes |
| `web/` | FastAPI server | ✅ Yes |
| `webui/` | Frontend components | ✅ Yes |

### `tests/` - Comprehensive Test Suite

- **54 Python test files** with high coverage
- **15+ Playwright E2E tests**
- **44+ Screenshots** for documentation and visual regression
- All tests run automatically in CI/CD

### `webui/frontend/tests/e2e/` - Playwright Tests

- **screenshots.spec.ts** - 5 user journeys + mobile tests
- **Integration tests** - API and WebSocket testing
- **Accessibility tests** - a11y compliance
- **Functional tests** - User workflows

## 🎨 User Journey Coverage

The Computer Vision system validates **complete user experiences** through these journeys:

1. **First-Time Setup** (7 steps) - Configuration workflow
2. **Voice Command Flow** (8 steps) - Voice interaction
3. **Dashboard Interaction** (6 steps) - UI navigation
4. **Real-Time Features** (5 steps) - Streaming and WebSocket
5. **Error States** (7 steps) - Edge cases and failures
6. **Mobile Responsive** (5 screenshots) - 375x667 viewport

**Total: 43+ sequential screenshots** capturing all happy paths and edge cases.

## 🚀 Getting Started with Development

### Backend
```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/chatty_commander --cov-report=html
```

### Frontend
```bash
cd webui/frontend
npm install
npm run dev

# Run E2E tests
npx playwright test

# Generate documentation screenshots
npx playwright test tests/e2e/screenshots.spec.ts
```

### Computer Vision
```bash
# Install CV dependencies (optional)
uv sync --optional-group cv

# Or manually
pip install opencv-python-headless pillow scikit-image numpy pytesseract

# Run validation
python scripts/validate_screenshots.py --current docs/screenshots/current --reference docs/screenshots/reference
```

## 📄 Related Documentation

- [Architecture](ARCHITECTURE.md) - System design and components
- [Testing Guide](../TESTING.md) - Testing strategy and how to run tests
- [API Documentation](../API.md) - REST API and WebSocket interface
- [Contribution Guide](CONTRIBUTING.md) - How to contribute
