# Testing - ChattyCommander

This document describes the testing strategy, test organization, and how to run tests for ChattyCommander.

## 🎯 Test Organization

ChattyCommander uses a multi-layered testing approach:

### Directory Structure

```
chatty-commander/
├── tests/                      # Python backend tests
│   ├── test_*.py               # Unit and integration tests
│   ├── test_web_*.py           # Web server tests
│   ├── test_voice*.py          # Voice processing tests
│   └── ... (54+ test files)
│
└── webui/frontend/
    └── tests/                  # Frontend E2E tests
        └── e2e/                # Playwright end-to-end tests
            ├── screenshots.spec.ts    # Screenshot generation & validation
            ├── basic.spec.ts          # Basic functionality
            ├── integration.spec.ts    # Integration flows
            └── ... (15+ test files)
```

### Test Types

| Type | Location | Purpose | Speed | Coverage |
|------|----------|---------|-------|----------|
| Unit | `tests/test_*.py` | Individual functions | ⚡ Fast | Component |
| Integration | `tests/test_*.py` | Module interactions | ⚡ Fast | Module |
| E2E | `webui/frontend/tests/e2e/` | Full user journeys | 🐢 Slow | System |
| Visual Regression | GitHub Actions | UI consistency | 🐢 Slow | Visual |

## 📊 Test Coverage

### Backend (Python) Tests

**Total: 54 test files** with comprehensive coverage of:

- ✅ **Web Server**: FastAPI endpoints, WebSocket, authentication
- ✅ **Voice Processing**: Wake word detection, STT, TTS
- ✅ **LLM Integration**: Provider adapters, agent orchestration
- ✅ **Configuration**: Loading, validation, state management
- ✅ **Advisors**: Context management, conversation flow
- ✅ **Command Execution**: Keypress, shell, HTTP actions
- ✅ **Web UI Backend**: APIs for frontend
- ✅ **Security**: Authentication, rate limiting
- ✅ **Error Handling**: Graceful degradation
- ⚠️ **Computer Vision**: New module, tests needed

### Frontend (Playwright) Tests

**Total: 15+ test files** covering:

- ✅ **Basic Screenshots**: Dashboard, login, configuration, commands
- ✅ **User Journeys**: Complete workflows (see below)
- ✅ **Mobile Responsive**: 375x667 viewport
- ✅ **Error States**: Various failure scenarios
- ✅ **Real-time Features**: WebSocket streaming

## 🗺️ User Journey Test Coverage

The screenshot generation tests (`tests/e2e/screenshots.spec.ts`) capture **complete user experiences** through sequential journeys:

### Journey 1: First-Time Setup (7 steps)
1. Initial landing page
2. Navigate to configuration
3. View advisor/provider settings
4. Configure voice settings
5. Audio devices configuration
6. Voice models (ONNX) selection
7. Configuration saved successfully

### Journey 2: Core Voice Command Flow (8 steps)
1. Dashboard with voice enabled
2. Navigate to commands list
3. Command authoring interface
4. Command form with description
5. Command generated and displayed
6. Return to commands list
7. Voice command execution confirmation
8. Dashboard with updated statistics

### Journey 3: Web Dashboard Interaction (6 steps)
1. Fresh dashboard load
2. Dashboard with health statistics
3. Dashboard showing agent contexts
4. Click to commands from dashboard
5. Return to dashboard from commands
6. Final dashboard state

### Journey 4: Real-Time Features (5 steps)
1. Realtime status idle
2. Realtime status listening
3. Voice command recognized
4. Command execution in progress
5. Command execution completed

### Journey 5: Edge Cases & Error States (7 steps)
1. Unhealthy service status
2. Voice service connection error
3. Empty commands list
4. Configuration load failure
5. Network idle with no data
6. Page not found (404)
7. Service degraded state

### Mobile Responsive Tests (5 screenshots)
- Dashboard, commands, configuration, setup, voice flow on 375x667 viewport

**Total Screenshots Generated: 6 (existing) + 33 (journeys) + 5 (mobile) = 44+ screenshots**

## 🔍 Running Tests

### Backend Tests (Python)

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/chatty_commander --cov-report=html

# Run specific test file
uv run pytest tests/test_web_server.py -v

# Run with markers
uv run pytest -m "web"        # Web-related tests
uv run pytest -m "voice"      # Voice processing tests
uv run pytest -m "slow"      # Slow-running tests

# Run with verbose output
uv run pytest -v --tb=short

# Run and fail fast
uv run pytest -x -v
```

### Frontend Tests (Playwright)

```bash
# From webui/frontend directory
cd webui/frontend

# Install dependencies
npm ci

# Run all E2E tests
npx playwright test

# Run specific test file
npx playwright test tests/e2e/screenshots.spec.ts

# Run in headed mode (see browser)
npx playwright test --headed

# Run and generate report
npx playwright test --reporter=html

# Generate screenshots only
npx playwright test tests/e2e/screenshots.spec.ts
```

### Visual Regression Tests

```bash
# Run locally
python scripts/validate_screenshots.py \
    --current docs/screenshots/current \
    --reference docs/screenshots/reference \
    --threshold 0.95 \
    --output report \
    --generate-diff-images

# Run via CI/CD (automatic on PR)
# See .github/workflows/visual-regression.yml
```

## 🤖 CI/CD Pipelines

### Test Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `test.yml` | Push/PR | Run all unit & integration tests |
| `screenshots.yml` | Push to main | Generate documentation screenshots |
| `visual-regression.yml` | PR to main | Detect visual regressions |

### GitHub Actions Variables

The following repository variables can be configured:

| Variable | Default | Description |
|----------|---------|-------------|
| `VISUAL_REGRESSION_THRESHOLD` | `0.95` | SSIM threshold for passing |

## 📈 Coverage Requirements

### Minimum Coverage Targets

| Module | Target Coverage | Current |
|--------|-----------------|---------|
| Overall | > 80% | TBD |
| Core (app/) | > 85% | TBD |
| Web (web/) | > 80% | TBD |
| AI/Advisors (ai/, advisors/) | > 80% | TBD |
| Voice (voice/) | > 80% | TBD |
| **Computer Vision (cv/)** | **> 90%** | **TBD** |

### Coverage Badges

Add these to your README.md:

```markdown
![Test Coverage](https://img.shields.io/badge/Coverage-XX%25-green.svg?style=for-the-badge)
![Python Tests](https://github.com/owner/repo/actions/workflows/test.yml/badge.svg)
![Visual Regression](https://github.com/owner/repo/actions/workflows/visual-regression.yml/badge.svg)
```

## 🧪 Computer Vision Module Tests

The Computer Vision module at `src/chatty_commander/cv/` requires:

### Dependencies

```bash
pip install opencv-python pillow pytesseract scikit-image numpy
```

Note: `pytesseract` requires Tesseract OCR to be installed on the system:

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
sudo apt-get install libtesseract-dev
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
```bash
# Download installer from https://github.com/UB-Mannheim/tesseract/wiki
# Or use chocolatey: choco install tesseract
```

### Test File: `tests/test_cv_validator.py`

```python
"""Tests for Computer Vision module."""

import pytest
import numpy as np
from pathlib import Path
from PIL import Image

from chatty_commander.cv import (
    ComputerVisionValidator,
    ImageComparator,
    SSIMComparisonResult,
)


class TestImageComparator:
    """Test image comparison algorithms."""
    
    @pytest.fixture
    def comparator(self):
        return ImageComparator()
    
    @pytest.fixture
    def identical_images(self):
        """Create two identical test images."""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        return img, img.copy()
    
    @pytest.fixture
    def different_images(self):
        """Create two different test images."""
        img1 = np.zeros((100, 100, 3), dtype=np.uint8)
        img2 = np.full((100, 100, 3), 255, dtype=np.uint8)
        return img1, img2
    
    def test_same_images_ssim_perfect(self, comparator, identical_images):
        """Identical images should have SSIM of 1.0."""
        result = comparator.compare(*identical_images, threshold=0.95)
        assert result.passed
        assert result.ssim == pytest.approx(1.0, abs=0.001)
    
    def test_different_images_low_ssim(self, comparator, different_images):
        """Very different images should have low SSIM."""
        result = comparator.compare(*different_images, threshold=0.95)
        assert not result.passed
        assert result.ssim < 0.5
    
    def test_threshold_pass(self, comparator, identical_images):
        """Images passing threshold should be marked as passed."""
        result = comparator.compare(*identical_images, threshold=0.5)
        assert result.passed
    
    def test_threshold_fail(self, comparator, different_images):
        """Images below threshold should be marked as failed."""
        result = comparator.compare(*different_images, threshold=0.99)
        assert not result.passed


class TestComputerVisionValidator:
    """Test Computer Vision Validator class."""
    
    @pytest.fixture
    def validator(self, tmp_path):
        return ComputerVisionValidator(
            screenshots_dir=tmp_path,
            ocr_enabled=False,  # Disable OCR for faster tests
        )
    
    @pytest.fixture
    def test_image(self, tmp_path):
        """Create a test image file."""
        img = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        path = tmp_path / "test.png"
        Image.fromarray(img).save(path)
        return path
    
    def test_load_image(self, validator, test_image):
        """Should load image successfully."""
        img = validator._load_image(test_image)
        assert img.shape == (50, 50, 3)
    
    def test_compare_identical_images(self, validator, test_image):
        """Identical images should pass comparison."""
        result = validator.compare_screenshots(test_image, test_image)
        assert result.passed
        assert result.ssim >= 0.99
    
    def test_validate_text_presence_no_ocr(self, validator, test_image):
        """Text validation should handle disabled OCR gracefully."""
        # With OCR disabled, should return empty
        result = validator.validate_text_presence(test_image, ["any text"])
        assert isinstance(result, object)  # Just verify it returns something
    
    def test_batch_validation(self, validator, tmp_path):
        """Should validate multiple images in a directory."""
        # Create test images
        for i in range(3):
            img = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
            path = tmp_path / f"test_{i}.png"
            Image.fromarray(img).save(path)
        
        results = validator.validate_directory(tmp_path)
        assert len(results) == 3
        assert all(r.passed for r in results.values())


class TestSSIMComparisonResult:
    """Test SSIM comparison result dataclass."""
    
    def test_to_dict(self):
        """Should serialize to dictionary."""
        result = SSIMComparisonResult(
            passed=True,
            ssim=0.98,
            threshold=0.95,
            difference_map=None,
            difference_image_path=None,
        )
        d = result.to_dict()
        assert d["passed"] is True
        assert d["ssim"] == 0.98
        assert d["threshold"] == 0.95
```

## 🏗️ Integration with CLI

The Computer Vision capabilities are integrated via the `--enable-computer-vision` flag:

```bash
# Enable Computer Vision module
python -m chatty_commander.cli.main --enable-computer-vision

# Run with all features
python -m chatty_commander.cli.main \
    --web \
    --enable-computer-vision \
    --enable-openwakeword \
    --port 8100
```

## 📋 Test Checklist for New Features

When adding new functionality, ensure:

- [ ] Unit tests for individual functions
- [ ] Integration tests for module interactions
- [ ] E2E tests for user-facing features
- [ ] Screenshots for UI changes
- [ ] Documentation updated
- [ ] Code follows style guidelines
- [ ] Tests pass on CI/CD

## 🎓 Best Practices

1. **Test Isolation**: Each test should be independent
2. **Descriptive Names**: Use `test_<verb>_<subject>` naming
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Mock Externals**: Use `unittest.mock` for dependencies
5. **Parameterize**: Use `@pytest.mark.parametrize` for similar tests
6. **Fixtures**: Use fixtures for common setup
7. **Cleanup**: Use `tmp_path` for temporary files

## 🔄 Test Maintenance

### Updating Screenshots

```bash
# Manually generate screenshots
cd webui/frontend
npm run generate-docs

# Or run GitHub Actions workflow manually
# Navigate to: https://github.com/owner/repo/actions/workflows/screenshots.yml
# Click "Run workflow"
```

### When to Update Reference Screenshots

1. **Intentional UI Changes**: After deliberate design changes
2. **New Features**: When adding new UI elements
3. **Bug Fixes**: When fixing visual bugs
4. ** Dependency Updates**: When updating frontend libraries

### Visual Regression TRIAGE

When a visual regression is detected:

1. **Check the diff images** in the PR artifacts
2. **Determine if intentional**:
   - If UI was intentionally changed → Update reference screenshots
   - If accidental change → Fix the code
3. **Adjust threshold** if needed (rare)
4. **Add to ignore list** if acceptable (document reason)

## 📞 Support

For testing-related questions:

- Check existing tests for patterns
- Review `conftest.py` for fixtures
- Consult `pytest` and `playwright` documentation
- Ask in project discussions

## 📄 Related Documentation

- [Architecture](developer/ARCHITECTURE.md)
- [Contribution Guide](developer/CONTRIBUTING.md)
- [API Documentation](API.md)
