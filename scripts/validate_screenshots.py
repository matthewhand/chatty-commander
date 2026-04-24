#!/usr/bin/env python3
"""Visual regression validation script using Computer Vision.

This script compares screenshots between current and reference versions using:
- Structural Similarity Index (SSIM) for perceptual comparison
- OCR for text validation
- Generates diff images highlighting differences
- Produces HTML and JSON reports

Usage:
    python scripts/validate_screenshots.py \
        --current <current_dir> \
        --reference <reference_dir> \
        --threshold 0.95 \
        --output report \
        --generate-diff-images

Exit codes:
    0: All tests passed
    1: Visual regression detected
"""

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim
from skimage.transform import resize

try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    pytesseract = None


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def read_image(path: str | Path) -> np.ndarray:
    """Read image as numpy array (RGB format)."""
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def normalize_images(img1: np.ndarray, img2: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Ensure both images have the same dimensions."""
    if img1.shape != img2.shape:
        min_h = min(img1.shape[0], img2.shape[0])
        min_w = min(img1.shape[1], img2.shape[1])
        img1 = resize(img1, (min_h, min_w), anti_aliasing=True, preserve_range=True)
        img2 = resize(img2, (min_h, min_w), anti_aliasing=True, preserve_range=True)
    return img1, img2


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert RGB image to grayscale."""
    if len(image.shape) == 3 and image.shape[2] == 3:
        return cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float64)
    return image.astype(np.float64)


def compare_ssim(img1: np.ndarray, img2: np.ndarray, data_range: float = 255.0) -> float:
    """Compute Structural Similarity Index between two images."""
    img1_gray = to_grayscale(img1)
    img2_gray = to_grayscale(img2)
    
    # Scale to 0-1 if needed
    if img1_gray.max() > 1:
        img1_gray = img1_gray / 255.0
        img2_gray = img2_gray / 255.0
        data_range = 1.0
    
    try:
        score = ssim(img1_gray, img2_gray, data_range=data_range)
        return float(score)
    except Exception as e:
        print(f"SSIM comparison error: {e}", file=sys.stderr)
        return 0.0


def extract_text(image: np.ndarray) -> str:
    """Extract text from image using OCR."""
    if not HAS_OCR or pytesseract is None:
        return ""
    try:
        return pytesseract.image_to_string(image)
    except Exception as e:
        print(f"OCR error: {e}", file=sys.stderr)
        return ""


def generate_diff_image(
    img1: np.ndarray,
    img2: np.ndarray,
    output_path: str | Path,
    ssim_score: float,
    threshold: float,
) -> str:
    """Generate a visual difference image with highlighted differences."""
    img1, img2 = normalize_images(img1, img2)
    
    # Calculate absolute difference
    diff = cv2.absdiff(img1.astype(np.int16), img2.astype(np.int16))
    diff = diff.astype(np.uint8)
    
    # Create output image with differences highlighted
    img_out = img1.copy().astype(np.uint8)
    
    # Convert to grayscale for thresholding
    diff_gray = to_grayscale(diff)
    
    # Normalize difference to 0-255
    if diff_gray.max() > 0:
        diff_gray = (diff_gray / diff_gray.max() * 255).astype(np.uint8)
    
    # Apply threshold to find significant differences
    _, thresh = cv2.threshold(diff_gray, 30, 255, cv2.THRESH_BINARY)
    
    # Dilate to make differences more visible
    kernel = np.ones((5, 5), np.uint8)
    dilated = cv2.dilate(thresh.astype(np.uint8), kernel, iterations=2)
    
    # Create red overlay for differences
    overlay = np.zeros_like(img_out)
    overlay[dilated > 0] = [0, 0, 255]  # Red
    
    # Blend overlay with original
    img_out = cv2.addWeighted(img_out, 0.8, overlay, 0.2, 0)
    
    # Add status text
    status = "PASS" if ssim_score >= threshold else "FAIL"
    color = (0, 255, 0) if ssim_score >= threshold else (0, 0, 255)
    
    cv2.putText(
        img_out,
        f"SSIM: {ssim_score:.4f} {status}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        color,
        2,
    )
    
    # Save image
    os.makedirs(os.path.dirname(str(output_path)), exist_ok=True)
    cv2.imwrite(str(output_path), cv2.cvtColor(img_out, cv2.COLOR_RGB2BGR))
    
    return str(output_path)


# ---------------------------------------------------------------------------
# Main Validation Logic
# ---------------------------------------------------------------------------

def validate_image_pair(
    current_path: Path,
    reference_path: Path,
    threshold: float,
    diff_dir: Path,
    generate_diff: bool = True,
) -> dict:
    """Compare a pair of images and return validation result."""
    try:
        current_img = read_image(current_path)
        reference_img = read_image(reference_path)
        
        # Calculate SSIM
        ssim_score = compare_ssim(current_img, reference_img)
        passed = ssim_score >= threshold
        
        # Extract text for OCR comparison
        current_text = extract_text(current_img)
        reference_text = extract_text(reference_img)
        
        # Simple text similarity check
        if current_text and reference_text:
            current_words = set(current_text.lower().split())
            reference_words = set(reference_text.lower().split())
            intersection = len(current_words & reference_words)
            union = len(current_words | reference_words)
            text_similarity = intersection / union if union > 0 else 0.0
        else:
            text_similarity = 1.0 if not current_text and not reference_text else 0.0
        
        # Generate diff image if requested
        diff_path = None
        if generate_diff:
            diff_filename = f"diff_{current_path.name}"
            diff_path = diff_dir / diff_filename
            generate_diff_image(
                current_img, reference_img,
                diff_path, ssim_score, threshold
            )
            diff_path = str(diff_path) if diff_path.exists() else None
        
        return {
            "filename": current_path.name,
            "ssim": ssim_score,
            "passed": passed,
            "threshold": threshold,
            "text_similarity": text_similarity,
            "current_text_length": len(current_text),
            "reference_text_length": len(reference_text),
            "diff_path": diff_path,
        }
    except Exception as e:
        return {
            "filename": current_path.name,
            "ssim": 0.0,
            "passed": False,
            "threshold": threshold,
            "error": str(e),
        }


def generate_html_report(
    results: list[dict],
    output_dir: Path,
    threshold: float,
    current_dir: Path,
    reference_dir: Path,
) -> None:
    """Generate HTML visualization of validation results."""
    passed = sum(1 for r in results if r.get("passed", False))
    failed = len(results) - passed
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visual Regression Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0; font-size: 2em; }}
        .summary {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
                     margin-bottom: 20px; display: flex; gap: 30px; }}
        .stat {{ text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; font-size: 0.9em; text-transform: uppercase; }}
        .comparison {{ background: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; 
                       box-shadow: 0 1px 5px rgba(0,0,0,0.1); border-left: 4px solid #444; }}
        .comparison.pass {{ border-left-color: #28a745; }}
        .comparison.fail {{ border-left-color: #dc3545; }}
        .comparison h3 {{ margin-top: 0; margin-bottom: 10px; color: #333; }}
        .images {{ display: flex; gap: 15px; flex-wrap: wrap; margin: 15px 0; }}
        .image-wrapper {{ flex: 1; min-width: 200px; }}
        .image-wrapper img {{ width: 100%; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }}
        .image-label {{ text-align: center; margin-top: 5px; font-size: 0.85em; color: #666; }}
        .score {{ display: inline-block; padding: 3px 8px; border-radius: 4px; 
                   font-size: 0.85em; font-weight: bold; }}
        .score.pass {{ background: #d4edda; color: #155724; }}
        .score.fail {{ background: #f8d7da; color: #721c24; }}
        .metrics {{ font-size: 0.85em; color: #666; margin-top: 10px; }}
        .error {{ color: #dc3545; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 Visual Regression Report</h1>
        </div>
        
        <div class="summary">
            <div class="stat">
                <div class="stat-value">{len(results)}</div>
                <div class="stat-label">Total Tests</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: #28a745;">{passed}</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: #dc3545;">{failed}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat">
                <div class="stat-value">{threshold:.2f}</div>
                <div class="stat-label">Threshold</div>
            </div>
        </div>
"""
    
    for r in sorted(results, key=lambda x: (not x.get("passed", True), x["filename"])):
        cls = "pass" if r.get("passed", False) else "fail"
        status = "✅" if r.get("passed", False) else "❌"
        ssim = r.get("ssim", 0)
        
        html += f"""
        <div class="comparison {cls}">
            <h3>{status} {r["filename"]}</h3>
            <span class="score {cls}">SSIM: {ssim:.4f}</span>
            """
        
        if "error" in r:
            html += f'<p class="error">Error: {r["error"]}</p>'
        elif r.get("diff_path"):
            diff_url = f"image/{Path(r['diff_path']).name}"
            current_url = f"image/current_{r['filename']}"
            reference_url = f"image/reference_{r['filename']}"
            
            # Copy images to output directory
            try:
                if current_dir and reference_dir:
                    current_img = read_image(current_dir / r["filename"])
                    ref_img = read_image(reference_dir / r["filename"])
                    Image.fromarray(current_img.astype(np.uint8)).save(output_dir / "image" / f"current_{r['filename']}")
                    Image.fromarray(ref_img.astype(np.uint8)).save(output_dir / "image" / f"reference_{r['filename']}")
            except Exception:
                pass
            
            html += f"""
            <div class="images">
                <div class="image-wrapper">
                    <img src="{reference_url}" alt="Reference">
                    <div class="image-label">Reference</div>
                </div>
                <div class="image-wrapper">
                    <img src="{current_url}" alt="Current">
                    <div class="image-label">Current</div>
                </div>
                <div class="image-wrapper">
                    <img src="{diff_url}" alt="Diff">
                    <div class="image-label">Difference</div>
                </div>
            </div>
            """
        
        if "text_similarity" in r:
            html += f'<div class="metrics">Text Similarity: {r["text_similarity"]:.4f}</div>'
        
        html += "</div>\n"
    
    html += """
    </div>
</body>
</html>
"""
    
    # Save HTML report
    os.makedirs(output_dir / "image", exist_ok=True)
    with open(output_dir / "index.html", "w") as f:
        f.write(html)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Visual regression validation using Computer Vision"
    )
    parser.add_argument(
        "--current", 
        type=Path,
        required=True,
        help="Directory containing current screenshots"
    )
    parser.add_argument(
        "--reference", 
        type=Path,
        required=True,
        help="Directory containing reference screenshots"
    )
    parser.add_argument(
        "--threshold", 
        type=float,
        default=0.95,
        help="SSIM threshold for passing (default: 0.95)"
    )
    parser.add_argument(
        "--output", 
        type=Path,
        default="report",
        help="Output directory for reports (default: report)"
    )
    parser.add_argument(
        "--generate-diff-images",
        action="store_true",
        help="Generate diff images highlighting differences"
    )
    parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        default=True,
        help="Exit with code 1 if regression detected (default: True)"
    )
    
    args = parser.parse_args()
    
    # Validate paths
    if not args.current.exists():
        print(f"Error: Current directory not found: {args.current}", file=sys.stderr)
        sys.exit(1)
    
    if not args.reference.exists():
        print(f"Error: Reference directory not found: {args.reference}", file=sys.stderr)
        sys.exit(1)
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    os.makedirs(args.output / "image", exist_ok=True)
    
    if args.generate_diff_images:
        diff_dir = args.output / "diff"
        os.makedirs(diff_dir, exist_ok=True)
    else:
        diff_dir = None
    
    # Find all PNG files in current directory
    current_files = sorted(args.current.glob("*.png"))
    
    if not current_files:
        print(f"Warning: No PNG files found in {args.current}", file=sys.stderr)
    
    # Validate each file
    results = []
    
    for current_path in current_files:
        reference_path = args.reference / current_path.name
        
        if not reference_path.exists():
            results.append({
                "filename": current_path.name,
                "ssim": 0.0,
                "passed": False,
                "threshold": args.threshold,
                "error": f"No reference found: {current_path.name}",
            })
            print(f"❌ {current_path.name}: No reference found")
        else:
            result = validate_image_pair(
                current_path,
                reference_path,
                args.threshold,
                diff_dir if args.generate_diff_images else None,
                generate_diff=args.generate_diff_images,
            )
            results.append(result)
            
            status = "✅" if result["passed"] else "❌"
            print(f"{status} {current_path.name}: SSIM={result['ssim']:.4f}, "
                  f"TextSim={result.get('text_similarity', 0):.4f}")
    
    # Check for deleted files
    reference_files = sorted(args.reference.glob("*.png"))
    current_filenames = {f.name for f in current_files}
    
    for ref_path in reference_files:
        if ref_path.name not in current_filenames:
            results.append({
                "filename": ref_path.name,
                "ssim": 0.0,
                "passed": False,
                "threshold": args.threshold,
                "error": "File deleted",
            })
            print(f"❌ {ref_path.name}: Deleted")
    
    # Generate reports
    summary = {
        "status": "PASS" if all(r.get("passed", False) for r in results) else "FAIL",
        "threshold": args.threshold,
        "total": len(results),
        "passed": sum(1 for r in results if r.get("passed", False)),
        "failed": sum(1 for r in results if not r.get("passed", False)),
        "failures": [
            {"filename": r["filename"], "ssim": r["ssim"], "error": r.get("error")}
            for r in results
            if not r.get("passed", False)
        ],
    }
    
    # Save JSON summary
    with open(args.output / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    # Generate HTML report if diff images were generated
    if args.generate_diff_images:
        generate_html_report(
            results, args.output, args.threshold, args.current, args.reference
        )
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Visual Regression Summary")
    print(f"{'='*60}")
    print(f"Status:    {summary['status']}")
    print(f"Threshold: {summary['threshold']}")
    print(f"Total:     {summary['total']}")
    print(f"Passed:    {summary['passed']}")
    print(f"Failed:    {summary['failed']}")
    
    if summary["failed"] > 0:
        print(f"\nFailed Tests:")
        for failure in summary["failures"]:
            print(f"  - {failure['filename']}: SSIM={failure.get('ssim', 'N/A')}")
    
    print(f"\nReports saved to: {args.output}")
    
    # Exit with appropriate code
    if args.fail_on_regression and summary["failed"] > 0:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
