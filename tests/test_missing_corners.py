#!/usr/bin/env python3
"""
Missing Corners Test
Tests missing corner scenarios for image 1 only and compares against reference images.
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


def test_missing_corner(image_number, missing_corner):
    """Test a single image with a specific missing corner."""
    input_dir = Path("tests/input")
    references_dir = Path("tests/references")

    # Find the image file - look for {number}.{extension} pattern
    image_path = None
    for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
        test_path = input_dir / f"{image_number}{ext}"
        if test_path.exists():
            image_path = str(test_path)
            break

    if not image_path:
        print(f"❌ Image {image_number}.* not found in tests/input/")
        return False

    print(f"📸 Testing: {os.path.basename(image_path)} (Missing {missing_corner})")

    try:
        # Configure for missing corner
        config.ENABLE_MISSING_CORNER_CALCULATION = True
        config.FORCE_MISSING_CORNER = missing_corner

        # Create pipeline instance
        pipeline = OMRPipeline(image_path, debug=config.DEBUG_MODE)

        # Process the image
        success = pipeline.run_pipeline()

        if success:
            # Define paths for comparison
            expected_path = references_dir / f"{image_number}-{missing_corner.lower()}-missing-cropped.jpg"
            actual_path = Path("tmp/output") / f"{image_number}_missing_{missing_corner.lower()}_cropped.jpg"

            print(f"   📁 Expected: {expected_path}")
            print(f"   📁 Actual:   {actual_path}")

            # Check if both files exist
            if not expected_path.exists():
                print(f"   ❌ FAILED - No reference image found: {expected_path}")
                print(f"   💡 Generate reference by running: python tests/generate_references.py")
                return False

            if not actual_path.exists():
                print(f"   ❌ FAILED - Output image not found: {actual_path}")
                return False

            # Compare images
            if images_match(str(expected_path), str(actual_path)):
                print(f"   ✅ PASSED - Images match exactly")
                return True
            else:
                print(f"   ❌ FAILED - Images do not match")
                return False
        else:
            print(f"   ❌ FAILED - Pipeline processing failed")
            return False

    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False
    finally:
        # Reset config
        config.ENABLE_MISSING_CORNER_CALCULATION = False
        config.FORCE_MISSING_CORNER = None


def run_tests():
    """Run missing corner tests for image 1."""
    # Test image number - easily editable for debugging
    test_image = 1  # Change this to test different images

    # Missing corner scenarios to test
    missing_corners = ['TL', 'TR', 'BL', 'BR']

    print(f"🧪 Starting Missing Corner Tests (Image {test_image})")
    print("=" * 60)

    start_time = time.time()
    successful_tests = 0
    failed_tests = 0
    total_tests = len(missing_corners)

    # Test each missing corner scenario
    for i, corner in enumerate(missing_corners, 1):
        print(f"\n🔄 Test {i}/{total_tests} - Missing {corner}:")

        if test_missing_corner(test_image, corner):
            successful_tests += 1
        else:
            failed_tests += 1

    # Print summary
    total_time = time.time() - start_time
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Successful tests: {successful_tests}/{total_tests}")
    print(f"❌ Failed tests: {failed_tests}/{total_tests}")
    print(f"⏱️  Total time: {total_time:.2f} seconds")

    if successful_tests > 0:
        print(f"⚡ Average time per test: {total_time/total_tests:.2f} seconds")

    return successful_tests == total_tests


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
