#!/usr/bin/env python3
"""
Actual Missing Corner Test
Tests images with actual missing corners (like br-missing.jpeg) to verify
the pipeline can handle real-world scenarios where corners are truly absent.
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


def test_actual_missing_corner(image_name, expected_missing_corner=None):
    """Test an image with an actual missing corner."""
    input_dir = Path("tests/input")
    references_dir = Path("tests/references")

    # Find the image file
    image_path = input_dir / image_name

    if not image_path.exists():
        print(f"❌ Image {image_name} not found in tests/input/")
        return False

    print(f"📸 Testing: {image_name}")
    if expected_missing_corner:
        print(f"   🎯 Expected missing corner: {expected_missing_corner}")

    try:
        # Reset config - let the system automatically detect missing corners
        config.ENABLE_MISSING_CORNER_CALCULATION = False
        config.FORCE_MISSING_CORNER = None

        # Create pipeline instance
        pipeline = OMRPipeline(str(image_path), debug=config.DEBUG_MODE)

        # Process the image
        success = pipeline.run_pipeline()

        if success:
            # Extract base name for reference comparison
            base_name = image_name.split('.')[0]  # e.g., "br-missing" from "br-missing.jpeg"

            # Define paths for comparison
            expected_path = references_dir / f"{base_name}-cropped.jpg"
            actual_path = Path("tmp/output") / f"{base_name}_cropped.jpg"

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


def run_tests():
    """Run tests for images with actual missing corners."""
    # Test cases - easily editable for debugging
    test_cases = [
        {
            'image': 'br-missing.jpeg',
            'expected_missing': 'BR',
            'description': 'Bottom-right corner actually missing'
        }
        # Add more test cases here:
        # {
        #     'image': 'tl-missing.jpg',
        #     'expected_missing': 'TL',
        #     'description': 'Top-left corner actually missing'
        # }
    ]

    print(f"🧪 Starting Actual Missing Corner Tests")
    print("=" * 60)

    start_time = time.time()
    successful_tests = 0
    failed_tests = 0
    total_tests = len(test_cases)

    # Test each case
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔄 Test {i}/{total_tests} - {test_case['description']}:")

        if test_actual_missing_corner(test_case['image'], test_case['expected_missing']):
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

    if failed_tests == 0:
        print("\n🎉 All actual missing corner tests passed!")
        print("💡 The pipeline successfully handled real-world missing corner scenarios")
    else:
        print(f"\n⚠️  Some tests failed - check the debug images in tmp/steps/")

    return successful_tests == total_tests


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
