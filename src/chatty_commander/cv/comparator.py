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

"""Image comparison utilities using Structural Similarity Index (SSIM).

This module provides image comparison algorithms for visual regression testing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from skimage.transform import resize


@dataclass
class SSIMComparisonResult:
    """Result of an SSIM comparison between two images."""
    
    passed: bool
    ssim: float
    threshold: float
    difference_map: Optional[np.ndarray] = None
    difference_image_path: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "passed": self.passed,
            "ssim": self.ssim,
            "threshold": self.threshold,
            "difference_image_path": self.difference_image_path,
        }


@dataclass
class PixelDiffResult:
    """Result of pixel-by-pixel comparison."""
    
    total_pixels: int
    diff_pixels: int
    diff_percentage: float
    max_diff: float
    mean_diff: float
    diff_map: Optional[np.ndarray] = None


class ImageComparator:
    """Compares images using various algorithms.
    
    This class provides multiple comparison methods for visual regression testing:
    - Structural Similarity Index (SSIM) - perceptually accurate
    - Mean Squared Error (MSE) - simple pixel difference
    - Pixel-by-pixel comparison - exact matching
    - Histogram comparison - color distribution
    
    Example usage:
        ```python
        comparator = ImageComparator()
        
        # Load images
        img1 = cv2.imread("reference.png")
        img2 = cv2.imread("current.png")
        
        # Compare using SSIM
        result = comparator.compare(img1, img2, threshold=0.95)
        print(f"SSIM: {result.ssim:.4f}, Passed: {result.passed}")
        ```
    """
    
    def __init__(self) -> None:
        """Initialize the comparator."""
        pass
    
    def _normalize_images(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Normalize two images to the same size and format.
        
        Args:
            img1: First image (RGB format)
            img2: Second image (RGB format)
        
        Returns:
            Tuple of normalized images
        """
        # Ensure both images have the same dimensions
        if img1.shape != img2.shape:
            min_h = min(img1.shape[0], img2.shape[0])
            min_w = min(img1.shape[1], img2.shape[1])
            img1 = resize(img1, (min_h, min_w), anti_aliasing=True, preserve_range=True)
            img2 = resize(img2, (min_h, min_w), anti_aliasing=True, preserve_range=True)
        
        return img1, img2
    
    def _to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convert RGB image to grayscale.
        
        Args:
            image: RGB image array
        
        Returns:
            Grayscale image array
        """
        if len(image.shape) == 3 and image.shape[2] == 3:
            # Convert RGB to grayscale
            return cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float64)
        return image.astype(np.float64)
    
    def compare(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        threshold: float = 0.95,
        generate_diff: bool = True,
    ) -> SSIMComparisonResult:
        """Compare two images using Structural Similarity Index (SSIM).
        
        SSIM measures the similarity between two images. A value of 1 indicates
        identical images, 0 indicates no similarity.
        
        Args:
            img1: First image (RGB format, uint8 or float)
            img2: Second image (RGB format, uint8 or float)
            threshold: Minimum SSIM score to pass (default: 0.95)
            generate_diff: Whether to generate difference map
        
        Returns:
            SSIMComparisonResult with comparison details
        """
        # Normalize images
        img1, img2 = self._normalize_images(img1, img2)
        
        # Convert to grayscale for SSIM
        img1_gray = self._to_grayscale(img1)
        img2_gray = self._to_grayscale(img2)
        
        # SSIM expects values in range [0, 255]
        if img1_gray.max() > 1:
            img1_gray = img1_gray / 255.0
            img2_gray = img2_gray / 255.0
        
        # Compute SSIM
        ssim_score = ssim(img1_gray, img2_gray, data_range=255 if img1_gray.max() > 1 else 1.0)
        
        # Generate difference map if requested
        diff_map: Optional[np.ndarray] = None
        if generate_diff:
            # Calculate absolute difference
            if img1.dtype != img2.dtype:
                img1_float = img1.astype(np.float64)
                img2_float = img2.astype(np.float64)
            else:
                img1_float = img1.astype(np.float64)
                img2_float = img2.astype(np.float64)
            
            diff_map = cv2.absdiff(img1_float, img2_float)
            if diff_map.max() > 0:
                diff_map = (diff_map / diff_map.max()) * 255
            diff_map = diff_map.astype(np.uint8)
        
        return SSIMComparisonResult(
            passed=float(ssim_score) >= threshold,
            ssim=float(ssim_score),
            threshold=threshold,
            difference_map=diff_map,
        )
    
    def compare_mse(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        threshold: Optional[float] = None,
    ) -> float:
        """Compare two images using Mean Squared Error.
        
        Lower MSE indicates more similar images. A value of 0 means identical.
        
        Args:
            img1: First image (RGB format)
            img2: Second image (RGB format)
            threshold: Optional MSE threshold (not used for comparison, just for reference)
        
        Returns:
            MSE value (lower is better)
        """
        # Normalize images
        img1, img2 = self._normalize_images(img1, img2)
        
        # Calculate MSE
        mse = np.mean((img1 - img2) ** 2)
        
        return float(mse)
    
    def compare_pixel_diff(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
    ) -> PixelDiffResult:
        """Compare two images pixel by pixel.
        
        Args:
            img1: First image (RGB format)
            img2: Second image (RGB format)
        
        Returns:
            PixelDiffResult with detailed difference information
        """
        # Normalize images
        img1, img2 = self._normalize_images(img1, img2)
        
        # Calculate differences
        diff_map = cv2.absdiff(img1.astype(np.int16), img2.astype(np.int16))
        
        # Calculate statistics
        total_pixels = diff_map.size // diff_map.shape[2] if len(diff_map.shape) == 3 else diff_map.size
        diff_pixels = np.count_nonzero(diff_map)
        diff_percentage = (diff_pixels / total_pixels * 100) if total_pixels > 0 else 0
        max_diff = float(diff_map.max())
        mean_diff = float(diff_map.mean())
        
        return PixelDiffResult(
            total_pixels=total_pixels,
            diff_pixels=int(diff_pixels),
            diff_percentage=float(diff_percentage),
            max_diff=max_diff,
            mean_diff=mean_diff,
            diff_map=diff_map,
        )
    
    def compare_histogram(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        bins: int = 256,
    ) -> float:
        """Compare two images using histogram correlation.
        
        Args:
            img1: First image (RGB format)
            img2: Second image (RGB format)
            bins: Number of histogram bins
        
        Returns:
            Correlation score between histograms (0-1, higher is better)
        """
        # Normalize images
        img1, img2 = self._normalize_images(img1, img2)
        
        # Convert to grayscale
        img1_gray = self._to_grayscale(img1)
        img2_gray = self._to_grayscale(img2)
        
        # Scale to 0-255
        img1_gray = ((img1_gray - img1_gray.min()) / (img1_gray.max() - img1_gray.min()) * 255).astype(np.uint8)
        img2_gray = ((img2_gray - img2_gray.min()) / (img2_gray.max() - img2_gray.min()) * 255).astype(np.uint8)
        
        # Compute histograms
        hist1 = cv2.calcHist([img1_gray], [0], None, [bins], [0, 256])
        hist2 = cv2.calcHist([img2_gray], [0], None, [bins], [0, 256])
        
        # Normalize histograms
        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()
        
        # Calculate correlation
        correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        
        return float(correlation)
    
    def generate_diff_image(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        output_path: str | Path,
        highlight_diff: bool = True,
    ) -> str:
        """Generate a visual difference image between two images.
        
        Args:
            img1: First image (RGB format)
            img2: Second image (RGB format)
            output_path: Path to save the difference image
            highlight_diff: Whether to highlight differences in red
        
        Returns:
            Path to the generated difference image
        """
        # Normalize images
        img1, img2 = self._normalize_images(img1, img2)
        
        # Calculate difference
        diff = cv2.absdiff(img1.astype(np.int16), img2.astype(np.int16))
        
        # Convert to 8-bit
        diff = diff.astype(np.uint8)
        
        if highlight_diff:
            # Create a copy of img1 to draw on
            img_out = img1.copy().astype(np.uint8)
            
            # Find where there are significant differences
            # Convert to grayscale for thresholding
            diff_gray = self._to_grayscale(diff)
            _, thresh = cv2.threshold(diff_gray, 30, 255, cv2.THRESH_BINARY)
            
            # Create red mask for differences
            kernel = np.ones((5, 5), np.uint8)
            dilated = cv2.dilate(thresh.astype(np.uint8), kernel, iterations=2)
            
            # Create red overlay
            overlay = np.zeros_like(img_out)
            overlay[dilated > 0] = [0, 0, 255]  # Red
            
            # Blend with original
            img_out = cv2.addWeighted(img_out, 0.8, overlay, 0.2, 0)
            
            # Add text annotation
            ssim_score = self.compare(img1, img2).ssim
            cv2.putText(
                img_out,
                f"SSIM: {ssim_score:.4f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )
            diff = img_out
        else:
            # Simple grayscale difference
            diff_gray = self._to_grayscale(diff)
            diff = cv2.cvtColor(diff_gray, cv2.COLOR_GRAY2RGB)
        
        # Save image
        cv2.imwrite(str(output_path), cv2.cvtColor(diff, cv2.COLOR_RGB2BGR))
        
        return str(output_path)
    
    def resize_image(
        self,
        image: np.ndarray,
        target_width: Optional[int] = None,
        target_height: Optional[int] = None,
        maintain_aspect_ratio: bool = True,
    ) -> np.ndarray:
        """Resize an image while maintaining aspect ratio.
        
        Args:
            image: Input image
            target_width: Target width in pixels
            target_height: Target height in pixels
            maintain_aspect_ratio: Whether to maintain aspect ratio
        
        Returns:
            Resized image
        """
        h, w = image.shape[:2]
        
        if target_width is None and target_height is None:
            return image
        
        if target_width is not None and target_height is not None:
            return resize(image, (target_height, target_width), anti_aliasing=True, preserve_range=True)
        
        if target_width is not None:
            ratio = target_width / w
            new_h = int(h * ratio) if maintain_aspect_ratio else target_height
            return resize(image, (new_h, target_width), anti_aliasing=True, preserve_range=True)
        
        if target_height is not None:
            ratio = target_height / h
            new_w = int(w * ratio) if maintain_aspect_ratio else target_width
            return resize(image, (target_height, new_w), anti_aliasing=True, preserve_range=True)
        
        return image
