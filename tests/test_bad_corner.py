#!/usr/bin/env python3
"""
Bad Corner Detection Test
Simple test that runs bad-corner.jpg through the main pipeline
and compares the output with the expected reference image.
"""

import os
import sys
import time
import cv2
import numpy as np
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import OMRPipeline
import config


def images_match(img1_path, img2_path):
    """Check if two images match exactly."""
    if not os.path.exists(img1_path) or not os.path.exists(img2_path):
        return False

    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)

    if img1 is None or img2 is None:
        return False

    # Check if dimensions match
    if img1.shape != img2.shape:
        return False

    # Check if images are identical
    return np.array_equal(img1, img2)


def test_bad_corner_image():
    """Test bad corner detection using bad-corner.jpg."""
    input_dir = Path("tests/input")
    references_dir = Path("tests/references")

    # Look for bad-corner image
    image_path = None
    for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        test_path = input_dir / f"bad-corner{ext}"
        if test_path.exists():
            image_path = str(test_path)
            break

    if not image_path:
        print(f"❌ bad-corner.* not found in tests/input/")
        return False

    print(f"📸 Testing: {os.path.basename(image_path)}")

    try:
        # Reset config to default
        config.ENABLE_MISSING_CORNER_CALCULATION = False
        config.FORCE_MISSING_CORNER = None

        # Create pipeline instance and run
        pipeline = OMRPipeline(image_path, debug=config.DEBUG_MODE)
        start_time = time.time()
        success = pipeline.run_pipeline()
        processing_time = time.time() - start_time

        if not success:
            print(f"   ❌ FAILED - Pipeline processing failed")
            return False

        print(f"   ⏱️  Processing time: {processing_time:.2f}s")

        # Compare with reference image
        expected_path = references_dir / "bad-corner-cropped.jpg"
        actual_path = Path("tmp/output") / "bad-corner_cropped.jpg"

        if not expected_path.exists():
            print(f"   ⚠️  No reference image found at {expected_path}")
            print(f"   ✅ PASSED - Pipeline completed successfully (no reference to compare)")
            return True

        if not actual_path.exists():
            print(f"   ❌ FAILED - No output image generated at {actual_path}")
            return False

        if images_match(str(expected_path), str(actual_path)):
            print(f"   ✅ PASSED - Output matches reference image")
            return True
        else:
            print(f"   ❌ FAILED - Output does not match reference image")
            print(f"   📁 Expected: {expected_path}")
            print(f"   📁 Actual:   {actual_path}")
            return False

    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False


def run_tests():
    """Run bad corner detection tests."""
    print("🧪 Starting Bad Corner Detection Tests")
    print("=" * 60)

    start_time = time.time()
    tests_run = 0
    tests_passed = 0

    # Test: Normal verification settings
    print(f"\n🔄 Testing bad-corner.jpg:")
    tests_run += 1
    if test_bad_corner_image():
        tests_passed += 1

    # Print summary
    total_time = time.time() - start_time
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Successful tests: {tests_passed}/{tests_run}")
    print(f"❌ Failed tests: {tests_run - tests_passed}/{tests_run}")
    print(f"⏱️  Total time: {total_time:.2f} seconds")

    if tests_passed > 0:
        print(f"⚡ Average time per test: {total_time/tests_run:.2f} seconds")

    return tests_passed == tests_run


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
