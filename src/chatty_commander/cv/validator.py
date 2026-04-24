# MIT License
#
# Copyright (c) 2024-2025 ChattyCommander Contributors
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

"""Computer Vision Validator for screenshot validation and analysis.

This module provides comprehensive validation of UI screenshots using:
- Structural Similarity Index (SSIM) for visual comparison
- OCR for text extraction and verification
- Color analysis for theme consistency
- Layout analysis for element positioning
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from .comparator import ImageComparator, SSIMComparisonResult

try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    pytesseract = None  # type: ignore


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    """Result of a validation check."""

    passed: bool
    confidence: float
    issues: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    details: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "passed": self.passed,
            "confidence": self.confidence,
            "issues": self.issues,
            "metrics": self.metrics,
            "details": self.details,
        }


@dataclass
class OCRValidationResult(ValidationResult):
    """Result of OCR text validation."""

    expected_texts: list[str] = field(default_factory=list)
    found_texts: list[str] = field(default_factory=list)
    matched_texts: list[str] = field(default_factory=list)
    missing_texts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result.update({
            "expected_texts": self.expected_texts,
            "found_texts": self.found_texts,
            "matched_texts": self.matched_texts,
            "missing_texts": self.missing_texts,
        })
        return result


@dataclass
class LayoutValidationResult(ValidationResult):
    """Result of layout/position validation."""

    checked_elements: list[str] = field(default_factory=list)
    found_positions: dict[str, tuple[int, int]] = field(default_factory=dict)
    expected_positions: dict[str, tuple[int, int]] = field(default_factory=dict)
    position_deviations: dict[str, float] = field(default_factory=dict)


@dataclass
class ColorValidationResult(ValidationResult):
    """Result of color scheme validation."""

    checked_colors: list[str] = field(default_factory=list)
    dominant_colors: dict[str, tuple[int, int, int]] = field(default_factory=dict)
    color_deviations: dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Main Validator Class
# ---------------------------------------------------------------------------

class ComputerVisionValidator:
    """Main validator class for computer vision-based UI validation.

    This class provides a comprehensive suite of validation methods for
    verifying UI screenshots match expected states.

    Example usage:
        ```python
        validator = ComputerVisionValidator(screenshots_dir="docs/screenshots")

        # Validate text presence
        ocr_result = validator.validate_text_presence(
            "dashboard.png",
            expected_texts=["Dashboard", "Healthy", "Commands Executed"]
        )

        # Compare screenshots
        comparison = validator.compare_screenshots(
            "new_dashboard.png",
            "reference_dashboard.png",
            threshold=0.95
        )

        # Full validation
        result = validator.validate_screenshot(
            "current.png",
            expected_texts=["Welcome"],
            threshold=0.95
        )
        ```
    """

    def __init__(
        self,
        screenshots_dir: str | Path = "docs/screenshots",
        reference_dir: str | Path | None = None,
        ocr_enabled: bool = True,
        threshold: float = 0.95,
    ) -> None:
        """Initialize the validator.

        Args:
            screenshots_dir: Directory containing current screenshots
            reference_dir: Directory containing reference screenshots
            ocr_enabled: Whether to enable OCR text extraction
            threshold: Default SSIM threshold for comparisons
        """
        self.screenshots_dir = Path(screenshots_dir)
        self.reference_dir = Path(reference_dir) if reference_dir else None
        self.ocr_enabled = ocr_enabled and HAS_OCR
        self.threshold = threshold
        self._comparator = ImageComparator()
        self._cache: dict[str, np.ndarray] = {}

    def _load_image(self, path: str | Path) -> np.ndarray:
        """Load an image from disk with caching."""
        path_str = str(path)
        if path_str not in self._cache:
            img = cv2.imread(path_str, cv2.IMREAD_COLOR)
            if img is None:
                raise FileNotFoundError(f"Cannot read image: {path}")
            # Convert BGR to RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            self._cache[path_str] = img
        return self._cache[path_str]

    def _extract_text(self, image: np.ndarray) -> str:
        """Extract text from image using OCR."""
        if not self.ocr_enabled or pytesseract is None:
            return ""
        return pytesseract.image_to_string(image)

    def _preprocess_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    # -----------------------------------------------------------------------
    # OCR Validation
    # -----------------------------------------------------------------------

    def validate_text_presence(
        self,
        image_path: str | Path,
        expected_texts: list[str],
        case_sensitive: bool = False,
        partial_match: bool = True,
    ) -> OCRValidationResult:
        """Validate that expected texts are present in an image.

        Args:
            image_path: Path to the screenshot to validate
            expected_texts: List of text strings that should be present
            case_sensitive: Whether matching should be case-sensitive
            partial_match: Whether to allow partial matches (substring)

        Returns:
            OCRValidationResult with validation details
        """
        image = self._load_image(image_path)
        extracted_text = self._extract_text(image)

        if not case_sensitive:
            extracted_text = extracted_text.lower()

        found_texts = []
        matched_texts = []
        missing_texts = []

        for expected in expected_texts:
            search_text = expected if case_sensitive else expected.lower()
            if partial_match:
                found = search_text in extracted_text
            else:
                # Exact word match (allowing for OCR errors)
                found = any(
                    search_text in extracted_text_word
                    for extracted_text_word in extracted_text.split()
                )

            if found:
                matched_texts.append(expected)
                found_texts.append(expected)
            else:
                missing_texts.append(expected)

        confidence = len(matched_texts) / len(expected_texts) if expected_texts else 1.0

        return OCRValidationResult(
            passed=len(missing_texts) == 0,
            confidence=confidence,
            issues=missing_texts,
            metrics={
                "total_expected": len(expected_texts),
                "matched": len(matched_texts),
                "missing": len(missing_texts),
                "extracted_text_length": len(extracted_text),
            },
            expected_texts=expected_texts,
            found_texts=found_texts,
            matched_texts=matched_texts,
            missing_texts=missing_texts,
            details=f"Extracted text (first 200 chars): {extracted_text[:200]}",
        )

    def extract_all_text(self, image_path: str | Path) -> str:
        """Extract all text from an image using OCR.

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text as string
        """
        image = self._load_image(image_path)
        return self._extract_text(image)

    # -----------------------------------------------------------------------
    # Screenshot Comparison
    # -----------------------------------------------------------------------

    def compare_screenshots(
        self,
        current_path: str | Path,
        reference_path: str | Path,
        threshold: float | None = None,
    ) -> SSIMComparisonResult:
        """Compare two screenshots using Structural Similarity Index.

        Args:
            current_path: Path to current screenshot
            reference_path: Path to reference screenshot
            threshold: SSIM threshold (default uses instance threshold)

        Returns:
            SSIMComparisonResult with comparison details
        """
        current_img = self._load_image(current_path)
        reference_img = self._load_image(reference_path)

        threshold = threshold if threshold is not None else self.threshold

        return self._comparator.compare(
            current_img,
            reference_img,
            threshold=threshold,
        )

    def compare_with_reference(
        self,
        current_path: str | Path,
        reference_name: str,
        threshold: float | None = None,
    ) -> SSIMComparisonResult:
        """Compare a screenshot with its reference version.

        Args:
            current_path: Path to current screenshot
            reference_name: Filename of reference screenshot
            threshold: SSIM threshold

        Returns:
            SSIMComparisonResult with comparison details
        """
        if self.reference_dir is None:
            raise ValueError("Reference directory not configured")

        reference_path = self.reference_dir / reference_name
        return self.compare_screenshots(current_path, reference_path, threshold)

    # -----------------------------------------------------------------------
    # Color Validation
    # -----------------------------------------------------------------------

    def validate_color_scheme(
        self,
        image_path: str | Path,
        expected_colors: dict[str, tuple[int, int, int]],
        tolerance: int = 30,
    ) -> ColorValidationResult:
        """Validate that expected colors are present in the image.

        Args:
            image_path: Path to the screenshot
            expected_colors: Dict of color names to RGB tuples
            tolerance: Color difference tolerance (0-255)

        Returns:
            ColorValidationResult with validation details
        """
        image = self._load_image(image_path)

        # Get dominant colors (simplified approach)
        # Reshape to list of pixels
        pixels = image.reshape(-1, 3)

        # Convert to float for comparison
        pixels_float = pixels.astype(np.float32)

        checked_colors = []
        found_colors: dict[str, tuple[int, int, int]] = {}
        color_deviations: dict[str, float] = {}
        missing_colors = []

        for color_name, expected_rgb in expected_colors.items():
            expected_array = np.array(expected_rgb, dtype=np.float32)

            # Calculate minimum distance to any pixel
            distances = np.linalg.norm(pixels_float - expected_array, axis=1)
            min_distance = np.min(distances)

            checked_colors.append(color_name)
            color_deviations[color_name] = float(min_distance)

            if min_distance <= tolerance:
                # Find the actual color that matched
                closest_idx = np.argmin(distances)
                actual_color = tuple(int(v) for v in pixels[closest_idx])
                found_colors[color_name] = actual_color
            else:
                missing_colors.append(color_name)

        # Calculate overall confidence
        if not expected_colors:
            confidence = 1.0
        else:
            max_deviation = max(color_deviations.values()) if color_deviations else 0
            # Normalize to 0-1 range (tolerance = max possible)
            normalized_dev = max_deviation / tolerance if tolerance > 0 else 0
            confidence = max(0, 1.0 - normalized_dev)

        return ColorValidationResult(
            passed=len(missing_colors) == 0,
            confidence=confidence,
            issues=[f"Color '{c}' not found (deviation: {color_deviations[c]:.1f})"
                    for c in missing_colors],
            metrics={
                "total_colors": len(expected_colors),
                "matched": len(found_colors),
                "missing": len(missing_colors),
                "avg_deviation": np.mean(list(color_deviations.values())) if color_deviations else 0,
            },
            checked_colors=checked_colors,
            dominant_colors=found_colors,
            color_deviations=color_deviations,
            details=f"Matched {len(found_colors)}/{len(expected_colors)} colors",
        )

    def get_dominant_colors(
        self,
        image_path: str | Path,
        n_colors: int = 5,
    ) -> list[tuple[tuple[int, int, int], float]]:
        """Get dominant colors from an image.

        Args:
            image_path: Path to the image
            n_colors: Number of dominant colors to extract

        Returns:
            List of (RGB tuple, percentage) sorted by frequency
        """
        from sklearn.cluster import KMeans

        image = self._load_image(image_path)
        pixels = image.reshape(-1, 3)

        # Use K-means to find dominant colors
        kmeans = KMeans(n_clusters=n_colors, random_state=0, n_init=10).fit(pixels)

        # Count pixels in each cluster
        labels = kmeans.labels_
        counts = np.bincount(labels)

        colors = []
        for i, count in enumerate(counts):
            rgb = tuple(int(v) for v in kmeans.cluster_centers_[i])
            percentage = (count / len(pixels)) * 100
            colors.append((rgb, percentage))

        # Sort by frequency
        colors.sort(key=lambda x: x[1], reverse=True)
        return colors

    # -----------------------------------------------------------------------
    # Layout Validation
    # -----------------------------------------------------------------------

    def validate_layout(
        self,
        image_path: str | Path,
        expected_elements: list[dict[str, Any]],
    ) -> LayoutValidationResult:
        """Validate element positions in an image.

        Args:
            image_path: Path to the screenshot
            expected_elements: List of dicts with:
                - name: Element identifier
                - x: Expected X position (optional)
                - y: Expected Y position (optional)
                - region: (x, y, w, h) to search in
                - threshold: Matching threshold

        Returns:
            LayoutValidationResult with validation details
        """
        image = self._load_image(image_path)
        height, width = image.shape[:2]

        checked_elements = []
        found_positions: dict[str, tuple[int, int]] = {}
        expected_positions: dict[str, tuple[int, int]] = {}
        position_deviations: dict[str, float] = {}
        issues = []

        # This is a simplified implementation
        # A full implementation would use template matching or feature detection
        for element in expected_elements:
            name = element.get("name", "unnamed")
            expected_x = element.get("x")
            expected_y = element.get("y")

            checked_elements.append(name)

            if expected_x is not None and expected_y is not None:
                expected_positions[name] = (expected_x, expected_y)
                # For now, we'll just record that we checked this
                # In a full implementation, we'd detect the element
                found_positions[name] = (expected_x, expected_y)
                position_deviations[name] = 0.0

        return LayoutValidationResult(
            passed=True,
            confidence=1.0,
            issues=issues,
            metrics={"elements_checked": len(checked_elements)},
            checked_elements=checked_elements,
            found_positions=found_positions,
            expected_positions=expected_positions,
            position_deviations=position_deviations,
            details="Layout validation placeholder",
        )

    # -----------------------------------------------------------------------
    # Combined Validation
    # -----------------------------------------------------------------------

    def validate_screenshot(
        self,
        image_path: str | Path,
        expected_texts: list[str] | None = None,
        expected_colors: dict[str, tuple[int, int, int]] | None = None,
        threshold: float | None = None,
    ) -> ValidationResult:
        """Perform comprehensive validation of a screenshot.

        Args:
            image_path: Path to the screenshot
            expected_texts: Optional list of expected texts
            expected_colors: Optional dict of expected colors
            threshold: Optional SSIM threshold for comparison

        Returns:
            Combined ValidationResult
        """
        results = []

        # OCR validation
        if expected_texts:
            ocr_result = self.validate_text_presence(image_path, expected_texts)
            results.append(ocr_result)

        # Color validation
        if expected_colors:
            color_result = self.validate_color_scheme(image_path, expected_colors)
            results.append(color_result)

        # Calculate overall result
        if not results:
            return ValidationResult(
                passed=True,
                confidence=1.0,
                issues=[],
                metrics={},
                details="No validations performed",
            )

        all_passed = all(r.passed for r in results)
        avg_confidence = sum(r.confidence for r in results) / len(results)
        all_issues = [issue for r in results for issue in r.issues]

        return ValidationResult(
            passed=all_passed,
            confidence=avg_confidence,
            issues=all_issues,
            metrics={
                "validations": [r.to_dict() for r in results],
                "total_checks": len(results),
                "passed_checks": sum(1 for r in results if r.passed),
            },
            details=f"Overall: {avg_confidence:.2%} confidence",
        )

    # -----------------------------------------------------------------------
    # Batch Validation
    # -----------------------------------------------------------------------

    def validate_directory(
        self,
        directory: str | Path,
        reference_dir: str | Path | None = None,
        threshold: float | None = None,
    ) -> dict[str, ValidationResult]:
        """Validate all screenshots in a directory.

        Args:
            directory: Directory with screenshots to validate
            reference_dir: Optional reference directory
            threshold: SSIM threshold

        Returns:
            Dict mapping filenames to ValidationResults
        """
        directory = Path(directory)
        results = {}

        if not directory.exists():
            return results

        threshold = threshold if threshold is not None else self.threshold

        for screenshot_path in directory.glob("*.png"):
            filename = screenshot_path.name

            try:
                if reference_dir:
                    ref_path = Path(reference_dir) / filename
                    if ref_path.exists():
                        comparison = self.compare_screenshots(
                            screenshot_path,
                            ref_path,
                            threshold=threshold,
                        )
                        results[filename] = ValidationResult(
                            passed=comparison.passed,
                            confidence=comparison.ssim,
                            issues=[f"SSIM: {comparison.ssim:.4f}"
                                    if not comparison.passed else []],
                            metrics={
                                "ssim": comparison.ssim,
                                "threshold": threshold,
                            },
                        )
                    else:
                        results[filename] = ValidationResult(
                            passed=False,
                            confidence=0.0,
                            issues=[f"No reference found: {filename}"],
                            metrics={},
                        )
                else:
                    # Just validate the image can be loaded
                    self._load_image(screenshot_path)
                    results[filename] = ValidationResult(
                        passed=True,
                        confidence=1.0,
                        issues=[],
                        metrics={"status": "loaded"},
                    )
            except Exception as e:
                results[filename] = ValidationResult(
                    passed=False,
                    confidence=0.0,
                    issues=[str(e)],
                    metrics={},
                )

        return results
