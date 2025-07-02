#!/usr/bin/env python3
"""
OMR Sheet Marker Detection & Cropping System - Main Pipeline Runner

This script orchestrates the 4-step pipeline to process OMR sheets:
1. Preprocess (margin crop, grayscale, blur, threshold)
2. Corner Detection (grid-based analysis to find corner markers)
3. Corner Verification (verify corners by drawing lines from adjacent corners)
4. Cropping (perspective transformation and final crop)

Usage:
    python main.py input/sheet.jpg
    python main.py input/  # Process all images in folder
"""

import os
import sys
import argparse
import time
from pathlib import Path
import cv2

# Import pipeline steps
from pipeline.step_1_preprocess import preprocess_image
from pipeline.step_2_corner_detection import find_markers
from pipeline.step_3_corner_verification import verify_corners
from pipeline.step_4_cropping import detect_markers

import config


class OMRPipeline:
    """Main pipeline orchestrator for OMR sheet processing."""

    def __init__(self, input_path, debug=True):
        """Initialize pipeline with input path and debug settings."""
        self.input_path = Path(input_path)
        self.debug = debug
        self.base_name = self.input_path.stem

        # Setup directory structure
        self._setup_directories()

    def _setup_directories(self):
        """Create necessary directories for pipeline output with proper error handling."""
        self.tmp_dir = Path("tmp")
        self.output_dir = self.tmp_dir / "output"
        self.steps_dir = self.tmp_dir / "steps"

        # Always create directories (handles existing directories gracefully)
        try:
            for directory in [self.tmp_dir, self.output_dir, self.steps_dir]:
                directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"⚠️  Warning: Could not create directories: {e}")
            # Continue anyway - individual steps will try to create dirs as needed

    def run_pipeline(self):
        """Execute the complete 4-step pipeline."""
        print(f"🚀 Starting OMR pipeline for: {self.input_path}")
        start_time = time.time()

        try:
            # Load and validate input image
            original_image = self._load_image()
            print(f"📸 Loaded image: {original_image.shape}")

            # Determine base name for outputs
            step_base_name = self._get_step_base_name()

            # Execute pipeline steps
            binary_image, cropped_image = self._run_preprocessing(original_image, step_base_name)
            contours = self._run_corner_detection(binary_image, cropped_image, step_base_name)
            verified_contours = self._run_corner_verification(contours, cropped_image, step_base_name)
            final_image = self._run_cropping(verified_contours, cropped_image, step_base_name)

            # Save final output
            self._save_final_output(final_image, step_base_name)

            # Report completion
            elapsed = time.time() - start_time
            print(f"✅ Pipeline completed successfully in {elapsed:.2f}s")

            return True

        except Exception as e:
            print(f"❌ Pipeline failed: {str(e)}")
            return False

    def _load_image(self):
        """Load and validate input image."""
        image = cv2.imread(str(self.input_path))
        if image is None:
            raise ValueError(f"Could not load image: {self.input_path}")
        return image

    def _get_step_base_name(self):
        """Get base name for step outputs, including missing corner test mode."""
        if config.FORCE_MISSING_CORNER:
            step_base_name = f"{self.base_name}_missing_{config.FORCE_MISSING_CORNER.lower()}"
            print(f"🔧 Missing corner test mode: Using base name '{step_base_name}'")
            return step_base_name
        return self.base_name

    def _run_preprocessing(self, original_image, step_base_name):
        """Execute Step 1: Preprocessing and thresholding."""
        print("🔄 Step 1: Preprocessing + Thresholding...")

        # Run preprocessing pipeline
        preprocessed_vis, binary_image, crop_info = preprocess_image(original_image)

        # Save debug visualization if enabled
        if self.debug:
            self._save_step_image(preprocessed_vis, f"{step_base_name}_step_1_preprocessed_thresholded.jpg")

        # Create cropped color image for visualization
        cropped_image = self._apply_margin_crop_to_original(original_image)

        return binary_image, cropped_image

    def _apply_margin_crop_to_original(self, original_image):
        """Apply same margin crop to original color image for visualization."""
        margin_x = int(original_image.shape[1] * config.MARGIN_CROP_RATIO)
        margin_y = int(original_image.shape[0] * config.MARGIN_CROP_RATIO)
        return original_image[margin_y:original_image.shape[0]-margin_y,
                            margin_x:original_image.shape[1]-margin_x]

    def _run_corner_detection(self, binary_image, cropped_image, step_base_name):
        """Execute Step 2: Corner detection with potential recalculation."""
        print("🔄 Step 2: Finding markers...")

        # Initial corner detection
        _, contours = find_markers(binary_image, cropped_image.copy(), step_base_name)

        return contours

    def _run_corner_verification(self, contours, cropped_image, step_base_name):
        """Execute Step 3: Corner verification with recalculation if needed."""
        print("🔄 Step 3: Verifying corners...")

        # Verify corners
        _, verified_contours, needs_recalculation = verify_corners(
            contours, cropped_image.copy(), step_base_name
        )

        # Handle recalculation if needed
        if needs_recalculation:
            verified_contours = self._handle_recalculation(cropped_image, step_base_name)

        return verified_contours

    def _handle_recalculation(self, cropped_image, step_base_name):
        """Handle corner recalculation when verification fails."""
        print("🔄 Step 2 (Iteration 2): Recalculating with missing corners...")

        # Get binary image for recalculation
        binary_image = self._get_binary_for_recalculation(cropped_image)

        # Run corner detection again
        _, recalculated_contours = find_markers(
            binary_image, cropped_image.copy(), f"{step_base_name}_iter2"
        )

        # Reset missing corner flag and skip verification
        config.FORCE_MISSING_CORNER = None
        print("⏭️  Step 3: Skipped in iteration 2 (corners already verified)")

        return recalculated_contours

    def _get_binary_for_recalculation(self, cropped_image):
        """Get binary image for recalculation by reprocessing cropped image."""
        # Quick preprocessing for recalculation
        gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, config.GAUSSIAN_BLUR_KERNEL, 0)
        _, binary = cv2.threshold(blurred, config.THRESHOLD_VALUE, 255, cv2.THRESH_BINARY_INV)
        return binary

    def _run_cropping(self, verified_contours, cropped_image, step_base_name):
        """Execute Step 4: Final cropping and perspective transformation."""
        print("🔄 Step 4: Detecting markers and cropping...")

        # Perform cropping
        _, cropped_img = detect_markers(
            verified_contours, cropped_image.copy(), None, step_base_name
        )

        return cropped_img

    def _save_final_output(self, final_image, step_base_name):
        """Save the final cropped image with automatic overwrite."""
        # Always ensure output directory exists (handles existing directories gracefully)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        output_filename = f"{step_base_name}_cropped.jpg"
        output_path = self.output_dir / output_filename

        # cv2.imwrite automatically overwrites existing files
        success = cv2.imwrite(str(output_path), final_image)
        if success:
            print(f"📁 Final cropped image saved to: {output_path}")
        else:
            print(f"❌ Failed to save final image to: {output_path}")

    def _save_step_image(self, image, filename):
        """Save intermediate step image for debugging with automatic overwrite."""
        # Always ensure steps directory exists (handles existing directories gracefully)
        self.steps_dir.mkdir(parents=True, exist_ok=True)

        step_path = self.steps_dir / filename
        # cv2.imwrite automatically overwrites existing files
        success = cv2.imwrite(str(step_path), image)
        if not success:
            print(f"   ⚠️  Warning: Failed to save step image: {step_path}")


def create_argument_parser():
    """Create and configure command line argument parser."""
    parser = argparse.ArgumentParser(
        description="OMR Sheet Marker Detection & Cropping System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py input/sheet.jpg                     # Process single file
  python main.py input/                              # Process all images in folder
  python main.py sheet.jpg --no-debug                # Process without debug images
  python main.py sheet.jpg --missing-corner TL       # Force top-left corner as missing
  python main.py sheet.jpg --missing-corner BR       # Force bottom-right corner as missing
        """
    )

    # Required argument
    parser.add_argument("input", help="Input image file or directory")

    # Optional arguments
    parser.add_argument("--no-debug", action="store_true",
                       help="Disable debug image generation")
    parser.add_argument("--output", default="output",
                       help="Output directory (default: output)")
    parser.add_argument("--steps", default="steps",
                       help="Steps directory for debug images (default: steps)")
    parser.add_argument("--missing-corner", choices=['TL', 'TR', 'BL', 'BR'],
                       help="Force a specific corner as missing for testing")

    return parser


def configure_from_args(args):
    """Configure global settings based on command line arguments."""
    # Configure debug mode
    if args.no_debug:
        config.DEBUG_MODE = False

    # Configure missing corner testing
    if args.missing_corner:
        config.ENABLE_MISSING_CORNER_CALCULATION = True
        config.FORCE_MISSING_CORNER = args.missing_corner
        print(f"🔧 Forcing {args.missing_corner} corner as missing for testing")
    else:
        config.FORCE_MISSING_CORNER = None


def process_single_file(file_path):
    """Process a single image file."""
    pipeline = OMRPipeline(file_path, debug=config.DEBUG_MODE)
    return pipeline.run_pipeline()


def process_directory(input_dir):
    """Process all images in a directory."""
    input_path = Path(input_dir)

    if not input_path.is_dir():
        print(f"❌ Directory not found: {input_dir}")
        return False

    # Find all supported image files
    image_files = []
    for ext in config.SUPPORTED_EXTENSIONS:
        image_files.extend(input_path.glob(f"*{ext}"))
        image_files.extend(input_path.glob(f"*{ext.upper()}"))

    if not image_files:
        print(f"❌ No image files found in: {input_dir}")
        return False

    print(f"📂 Found {len(image_files)} image(s) to process")

    # Process each file
    success_count = 0
    for file_path in image_files:
        print(f"\n{'='*50}")
        if process_single_file(file_path):
            success_count += 1

    # Report results
    print(f"\n🎯 Processing complete: {success_count}/{len(image_files)} successful")
    return success_count == len(image_files)


def validate_input_path(input_path):
    """Validate that input path exists and is accessible."""
    path = Path(input_path)

    if not path.exists():
        print(f"❌ Input path not found: {input_path}")
        return False

    if not (path.is_file() or path.is_dir()):
        print(f"❌ Invalid input path: {input_path}")
        return False

    return True


def main():
    """Main entry point for the application."""
    # Parse command line arguments
    parser = create_argument_parser()
    args = parser.parse_args()

    # Configure settings from arguments
    configure_from_args(args)

    # Validate input path
    if not validate_input_path(args.input):
        sys.exit(1)

    # Process based on input type
    input_path = Path(args.input)
    if input_path.is_file():
        success = process_single_file(input_path)
    else:  # is_dir() already validated
        success = process_directory(input_path)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
