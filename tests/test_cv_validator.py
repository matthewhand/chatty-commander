"""Tests for Computer Vision module.

Comprehensive test coverage for:
- ImageComparator class (SSIM, MSE, pixel diff, histogram)
- ComputerVisionValidator class (text, color, layout validation)
- Data classes (ValidationResult, OCRValidationResult, etc.)
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image

from chatty_commander.cv.comparator import (
    ImageComparator,
    SSIMComparisonResult,
)
from chatty_commander.cv.validator import (
    ColorValidationResult,
    ComputerVisionValidator,
    LayoutValidationResult,
    OCRValidationResult,
    ValidationResult,
)

# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def comparator():
    """ImageComparator instance."""
    return ImageComparator()


@pytest.fixture
def validator(tmp_path):
    """ComputerVisionValidator instance."""
    return ComputerVisionValidator(
        screenshots_dir=tmp_path,
        reference_dir=tmp_path / "reference",
        ocr_enabled=False,  # Faster tests without OCR
        threshold=0.95,
    )


@pytest.fixture
def tmp_path_with_images(tmp_path):
    """Create temporary directory with test images."""
    # Create reference directory
    ref_dir = tmp_path / "reference"
    ref_dir.mkdir()

    # Create identical images
    img_data = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)

    # Save test images
    for name, data in [
        ("test1.png", img_data),
        ("test2.png", img_data * 0.8),
        ("identical1.png", img_data),
        ("identical2.png", img_data.copy()),
    ]:
        Image.fromarray(data.astype(np.uint8)).save(tmp_path / name)
        Image.fromarray(data.astype(np.uint8)).save(ref_dir / name)

    return tmp_path


# =============================================================================
# ImageComparator Tests
# =============================================================================

class TestImageComparator:
    """Tests for ImageComparator class."""

    def test_compare_identical_images(self, comparator):
        """Identical images should have SSIM of approximately 1.0."""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = comparator.compare(img, img.copy(), threshold=0.95)

        assert result.passed is True
        assert result.ssim >= 0.99
        assert result.threshold == 0.95
        assert result.difference_map is not None

    def test_compare_different_images(self, comparator):
        """Different images should have lower SSIM."""
        img1 = np.zeros((100, 100, 3), dtype=np.uint8)
        img2 = np.full((100, 100, 3), 255, dtype=np.uint8)

        result = comparator.compare(img1, img2, threshold=0.95)

        assert result.passed is False
        assert result.ssim < 0.5
        assert result.threshold == 0.95

    def test_compare_with_different_sizes(self, comparator):
        """Images of different sizes should be normalized."""
        img1 = np.random.randint(0, 255, (100, 80, 3), dtype=np.uint8)
        img2 = np.random.randint(0, 255, (120, 100, 3), dtype=np.uint8)

        result = comparator.compare(img1, img2, threshold=0.1)

        assert result is not None
        assert isinstance(result.ssim, float)

    def test_compare_mse_zero_for_identical(self, comparator):
        """MSE should be 0 for identical images."""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        mse = comparator.compare_mse(img, img.copy())

        assert mse == 0.0

    def test_compare_mse_positive_for_different(self, comparator):
        """MSE should be positive for different images."""
        img1 = np.zeros((100, 100, 3), dtype=np.uint8)
        img2 = np.full((100, 100, 3), 255, dtype=np.uint8)

        mse = comparator.compare_mse(img1, img2)

        assert mse > 0

    def test_compare_pixel_diff_identical(self, comparator):
        """Pixel diff of identical images should show no differences."""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = comparator.compare_pixel_diff(img, img.copy())

        assert result.diff_pixels == 0
        assert result.diff_percentage == 0.0

    def test_compare_histogram_identical(self, comparator):
        """Histogram correlation should be 1 for identical images."""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        corr = comparator.compare_histogram(img, img.copy())

        assert corr >= 0.99

    def test_compare_histogram_different(self, comparator):
        """Histogram correlation should be low for very different images."""
        img1 = np.zeros((100, 100, 3), dtype=np.uint8)
        img2 = np.full((100, 100, 3), 255, dtype=np.uint8)

        corr = comparator.compare_histogram(img1, img2)

        # Should be low but not necessarily 0
        assert corr < 0.5

    def test_generate_diff_image(self, comparator, tmp_path):
        """Should generate a difference image."""
        img1 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img2 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        output_path = tmp_path / "diff.png"
        result_path = comparator.generate_diff_image(
            img1, img2, output_path, 0.5, 0.95
        )

        assert output_path.exists()
        assert str(output_path) == result_path

    def test_resize_image_maintain_aspect_ratio(self, comparator):
        """Resizing should maintain aspect ratio by default."""
        img = np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)

        resized = comparator.resize_image(img, target_width=100)

        assert resized.shape[1] == 100
        assert resized.shape[0] == 50  # 100/2 to maintain 2:1 ratio


# =============================================================================
# ComputerVisionValidator Tests
# =============================================================================

class TestComputerVisionValidator:
    """Tests for ComputerVisionValidator class."""

    def test_init_default_values(self, tmp_path):
        """Should initialize with default values."""
        validator = ComputerVisionValidator(screenshots_dir=tmp_path)

        assert validator.screenshots_dir == Path(tmp_path)
        assert validator.reference_dir is None
        assert validator.threshold == 0.95

    def test_load_image(self, validator, tmp_path_with_images):
        """Should load image from path."""
        img_path = tmp_path_with_images / "test1.png"
        img = validator._load_image(img_path)

        assert img.shape == (50, 50, 3)
        assert img.dtype == np.float64

    def test_load_image_caching(self, validator, tmp_path_with_images):
        """Should cache loaded images."""
        img_path = tmp_path_with_images / "test1.png"

        img1 = validator._load_image(img_path)
        img2 = validator._load_image(img_path)

        assert img1 is img2  # Same object from cache

    def test_compare_screenshots_pass(self, validator, tmp_path_with_images):
        """Should pass comparison for identical screenshots."""
        current = tmp_path_with_images / "identical1.png"
        reference = tmp_path_with_images / "reference" / "identical1.png"

        result = validator.compare_screenshots(current, reference, threshold=0.95)

        assert result.passed is True
        assert result.ssim >= 0.99

    def test_compare_screenshots_fail(self, validator, tmp_path_with_images):
        """Should fail comparison for different screenshots."""
        current = tmp_path_with_images / "test1.png"
        reference = tmp_path_with_images / "reference" / "test2.png"

        result = validator.compare_screenshots(current, reference, threshold=0.99)

        assert result.passed is False
        assert result.ssim < 0.99

    def test_compare_with_reference_no_ref_dir(self, validator):
        """Should raise error if reference_dir not configured."""
        validator.reference_dir = None

        with pytest.raises(ValueError, match="Reference directory not configured"):
            validator.compare_with_reference("test.png", "test.png")

    def test_validate_text_presence_disabled_ocr(self, validator, tmp_path_with_images):
        """OCR validation should return empty text when disabled."""
        img_path = tmp_path_with_images / "test1.png"
        result = validator.validate_text_presence(
            img_path,
            expected_texts=["any text"],
        )

        assert isinstance(result, OCRValidationResult)
        assert result.expected_texts == ["any text"]
        # Without OCR, no text found
        assert len(result.found_texts) == 0

    @patch("chatty_commander.cv.validator.HAS_OCR", True)
    @patch("chatty_commander.cv.validator.pytesseract")
    def test_validate_text_presence_with_ocr(self, mock_pytesseract, validator, tmp_path_with_images):
        """OCR validation should work with OCR enabled."""
        mock_pytesseract.image_to_string.return_value = "Test Text Found"

        img_path = tmp_path_with_images / "test1.png"
        validator.ocr_enabled = True

        result = validator.validate_text_presence(
            img_path,
            expected_texts=["Test", "Text"],
            case_sensitive=False,
            partial_match=True,
        )

        assert result.passed is True
        assert "Test" in result.matched_texts or "Text" in result.matched_texts

    def test_extract_all_text(self, validator, tmp_path_with_images):
        """Should extract text from image."""
        img_path = tmp_path_with_images / "test1.png"
        text = validator.extract_all_text(img_path)

        # Without OCR, returns empty
        assert text == ""

    def test_validate_color_scheme(self, validator, tmp_path_with_images):
        """Should validate color scheme."""
        img_path = tmp_path_with_images / "test1.png"

        red = (255, 0, 0)
        blue = (0, 0, 255)

        result = validator.validate_color_scheme(
            img_path,
            expected_colors={"red": red, "blue": blue},
            tolerance=30,
        )

        assert isinstance(result, ColorValidationResult)
        assert result.checked_colors == ["red", "blue"]

    def test_get_dominant_colors(self, validator, tmp_path_with_images):
        """Should extract dominant colors."""
        img_path = tmp_path_with_images / "test1.png"
        colors = validator.get_dominant_colors(img_path, n_colors=3)

        assert len(colors) == 3
        assert all(isinstance(rgb, tuple) and len(rgb) == 3 for rgb, _ in colors)
        assert all(isinstance(pct, float) for _, pct in colors)
        # Percentages should sum to ~100
        total_pct = sum(pct for _, pct in colors)
        assert 99 <= total_pct <= 101

    def test_validate_layout(self, validator, tmp_path_with_images):
        """Should validate layout (placeholder implementation)."""
        img_path = tmp_path_with_images / "test1.png"

        result = validator.validate_layout(
            img_path,
            expected_elements=[
                {"name": "element1", "x": 10, "y": 20},
                {"name": "element2", "x": 30, "y": 40},
            ],
        )

        assert isinstance(result, LayoutValidationResult)
        assert result.passed is True
        assert len(result.checked_elements) == 2

    def test_validate_screenshot_combined(self, validator, tmp_path_with_images):
        """Should perform combined validation."""
        img_path = tmp_path_with_images / "identical1.png"

        result = validator.validate_screenshot(
            img_path,
            expected_texts=[],  # No text validation
            expected_colors={},  # No color validation
        )

        assert isinstance(result, ValidationResult)
        assert result.passed is True

    def test_validate_directory(self, validator, tmp_path_with_images):
        """Should validate all images in a directory."""
        results = validator.validate_directory(
            tmp_path_with_images,
            reference_dir=tmp_path_with_images / "reference",
        )

        assert len(results) >= 4  # We created 4 test images
        assert all(isinstance(v, ValidationResult) for v in results.values())


# =============================================================================
# Data Class Tests
# =============================================================================

class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_to_dict(self):
        """Should serialize to dictionary."""
        result = ValidationResult(
            passed=True,
            confidence=0.98,
            issues=["test issue"],
            metrics={"metric1": "value1"},
            details="Test details",
        )

        d = result.to_dict()

        assert d["passed"] is True
        assert d["confidence"] == 0.98
        assert d["issues"] == ["test issue"]
        assert d["metrics"] == {"metric1": "value1"}
        assert d["details"] == "Test details"


class TestOCRValidationResult:
    """Tests for OCRValidationResult dataclass."""

    def test_to_dict_extended(self):
        """Should include OCR-specific fields in serialization."""
        result = OCRValidationResult(
            passed=True,
            confidence=1.0,
            expected_texts=["expected1", "expected2"],
            found_texts=["found1"],
            matched_texts=["expected1"],
            missing_texts=["expected2"],
        )

        d = result.to_dict()

        assert d["expected_texts"] == ["expected1", "expected2"]
        assert d["found_texts"] == ["found1"]
        assert d["matched_texts"] == ["expected1"]
        assert d["missing_texts"] == ["expected2"]


class TestColorValidationResult:
    """Tests for ColorValidationResult dataclass."""

    def test_to_dict_extended(self):
        """Should include color-specific fields in serialization."""
        result = ColorValidationResult(
            passed=True,
            confidence=0.95,
            checked_colors=["red", "blue"],
            dominant_colors={"red": (255, 0, 0)},
            color_deviations={"red": 0.0, "blue": 5.0},
        )

        d = result.to_dict()

        assert d["checked_colors"] == ["red", "blue"]
        assert d["dominant_colors"] == {"red": (255, 0, 0)}
        assert d["color_deviations"] == {"red": 0.0, "blue": 5.0}


class TestSSIMComparisonResult:
    """Tests for SSIMComparisonResult dataclass."""

    def test_to_dict(self):
        """Should serialize to dictionary."""
        result = SSIMComparisonResult(
            passed=True,
            ssim=0.98,
            threshold=0.95,
            difference_map=None,
            difference_image_path="/path/to/diff.png",
        )

        d = result.to_dict()

        assert d["passed"] is True
        assert d["ssim"] == 0.98
        assert d["threshold"] == 0.95
        assert d["difference_image_path"] == "/path/to/diff.png"


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for CV module."""

    def test_full_validation_workflow(self, tmp_path):
        """Test complete validation workflow."""
        # Create reference images
        ref_dir = tmp_path / "reference"
        ref_dir.mkdir()

        # Create test image
        img_data = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img_path = tmp_path / "test.png"
        ref_path = ref_dir / "test.png"

        Image.fromarray(img_data).save(img_path)
        Image.fromarray(img_data).save(ref_path)

        # Create validator
        validator = ComputerVisionValidator(
            screenshots_dir=tmp_path,
            reference_dir=ref_dir,
            ocr_enabled=False,
        )

        # Compare
        result = validator.compare_screenshots(img_path, ref_path)

        assert result.passed is True
        assert result.ssim >= 0.99

        # Batch validate
        results = validator.validate_directory(tmp_path, ref_dir)

        assert len(results) == 1
        assert "test.png" in results
        assert results["test.png"].passed is True

    def test_detect_visual_regression(self, tmp_path):
        """Test detection of visual regression."""
        # Create reference image
        ref_dir = tmp_path / "reference"
        ref_dir.mkdir()

        img_data = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        ref_path = ref_dir / "test.png"
        Image.fromarray(img_data).save(ref_path)

        # Create modified current image (different)
        modified_data = img_data.copy()
        modified_data[50:60, 50:60] = 255  # Add a white square
        current_path = tmp_path / "test.png"
        Image.fromarray(modified_data).save(current_path)

        # Validate
        validator = ComputerVisionValidator(
            screenshots_dir=tmp_path,
            reference_dir=ref_dir,
            ocr_enabled=False,
            threshold=0.95,
        )

        result = validator.compare_screenshots(current_path, ref_path)

        # Should detect the difference
        assert result.passed is False or result.ssim < 1.0

    def test_cross_platform_image_handling(self, tmp_path, comparator):
        """Test handling of images from different sources."""
        # Create PIL Image
        pil_img = Image.new("RGB", (100, 100), color=(128, 128, 128))

        # Convert to numpy
        np_img = np.array(pil_img)

        # Compare with itself
        result = comparator.compare(np_img, np_img.copy())

        assert result.passed is True
        assert result.ssim >= 0.99
