#!/usr/bin/env python3
"""
Bad Corner Detection Test
Tests what happens when Step 3 corner verification detects bad corners
and triggers the recalculation process using bad-corner.jpg.
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

        # Create pipeline instance
        pipeline = OMRPipeline(image_path, debug=config.DEBUG_MODE)

        # Process the image
        start_time = time.time()
        success = pipeline.run_pipeline()
        processing_time = time.time() - start_time

        if success:
            print(f"   ⏱️  Processing time: {processing_time:.2f}s")

            # Check if recalculation occurred by looking for iteration 2 files
            steps_dir = Path("tmp/steps")
            iter2_files = list(steps_dir.glob("bad-corner_iter2*"))

            if iter2_files:
                print(f"   🔄 RECALCULATION DETECTED! Found {len(iter2_files)} iteration 2 files:")
                for file in sorted(iter2_files):
                    print(f"      - {file.name}")

                # Check if we have a reference for comparison
                expected_path = references_dir / "bad-corner-cropped.jpg"
                actual_path = Path("tmp/output") / "bad-corner_cropped.jpg"

                if expected_path.exists() and actual_path.exists():
                    if images_match(str(expected_path), str(actual_path)):
                        print(f"   ✅ PASSED - Bad corner detected, recalculated, and matched reference")
                        return True
                    else:
                        print(f"   ❌ FAILED - Recalculation occurred but images do not match")
                        return False
                else:
                    print(f"   ✅ PASSED - Bad corner detected and recalculation occurred")
                    print(f"   ℹ️  No reference image for comparison")
                    return True
            else:
                print(f"   ℹ️  No recalculation detected - all corners passed verification")

                # Still check against reference if available
                expected_path = references_dir / "bad-corner-cropped.jpg"
                actual_path = Path("tmp/output") / "bad-corner_cropped.jpg"

                if expected_path.exists() and actual_path.exists():
                    if images_match(str(expected_path), str(actual_path)):
                        print(f"   ✅ PASSED - Processing completed and matched reference")
                        return True
                    else:
                        print(f"   ❌ FAILED - Processing completed but images do not match")
                        return False
                else:
                    print(f"   ✅ PASSED - Processing completed successfully")
                    return True
        else:
            print(f"   ❌ FAILED - Pipeline processing failed")
            return False

    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False


def test_with_strict_settings():
    """Test with stricter verification settings to force bad corner detection."""
    print(f"\n🔧 Testing with strict verification settings:")

    # Backup original settings
    original_tolerance = config.CORNER_VERIFICATION_TOLERANCE
    original_min_lines = config.CORNER_VERIFICATION_MIN_LINES

    try:
        # Make verification stricter
        config.CORNER_VERIFICATION_TOLERANCE = 15  # Much stricter (was 50)
        config.CORNER_VERIFICATION_MIN_LINES = 2   # Require 2 lines instead of 1

        print(f"   - Tolerance: {original_tolerance} → {config.CORNER_VERIFICATION_TOLERANCE}")
        print(f"   - Min lines: {original_min_lines} → {config.CORNER_VERIFICATION_MIN_LINES}")

        result = test_bad_corner_image()

        return result

    finally:
        # Restore original settings
        config.CORNER_VERIFICATION_TOLERANCE = original_tolerance
        config.CORNER_VERIFICATION_MIN_LINES = original_min_lines


def run_tests():
    """Run bad corner detection tests."""
    print("🧪 Starting Bad Corner Detection Tests")
    print("=" * 60)

    start_time = time.time()
    tests_run = 0
    tests_passed = 0

    # Test 1: Normal verification settings
    print(f"\n🔄 Test 1/2 - Normal verification settings:")
    tests_run += 1
    if test_bad_corner_image():
        tests_passed += 1

    # Test 2: Strict verification settings
    print(f"\n🔄 Test 2/2 - Strict verification settings:")
    tests_run += 1
    if test_with_strict_settings():
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
