"""
Step 1: Preprocessing
Complete image preprocessing including margin crop, grayscale, blur, and threshold.
"""

import cv2
import numpy as np
import config


# =============================================================================
# MAIN PREPROCESSING FUNCTION
# =============================================================================

def preprocess_image(image):
    """
    Complete preprocessing pipeline: margin crop → grayscale → blur → threshold.

    Args:
        image (numpy.ndarray): Input BGR image

    Returns:
        tuple: (visualization_image, binary_image, crop_info)
    """
    original_image = image.copy()

    # Step 1: Apply margin crop
    cropped_image, crop_info = apply_margin_crop(image, config.MARGIN_CROP_RATIO)

    # Step 2: Convert to grayscale
    gray_image = convert_to_grayscale(cropped_image)

    # Step 3: Apply blur
    blurred_image = apply_gaussian_blur(gray_image)

    # Step 4: Apply threshold
    binary_image = apply_threshold(blurred_image)

    # Create visualization
    visualization = create_preprocessing_visualization(
        original_image, cropped_image, gray_image, blurred_image, binary_image
    )

    # Print summary
    _print_preprocessing_summary(original_image, cropped_image, crop_info)

    return visualization, binary_image, crop_info


# =============================================================================
# CORE PROCESSING FUNCTIONS
# =============================================================================

def apply_margin_crop(image, margin_ratio):
    """
    Remove margins from all sides to eliminate scan artifacts.

    Args:
        image (numpy.ndarray): Input image
        margin_ratio (float): Ratio to crop from each side (e.g., 0.02 = 2%)

    Returns:
        tuple: (cropped_image, crop_info)
    """
    if margin_ratio <= 0 or margin_ratio >= 0.5:
        return image, _create_no_crop_info(image, margin_ratio)

    height, width = image.shape[:2]

    # Calculate margins
    margin_y = max(1, min(int(height * margin_ratio), height // 4))
    margin_x = max(1, min(int(width * margin_ratio), width // 4))

    # Apply crop
    cropped = image[margin_y:height-margin_y, margin_x:width-margin_x]

    # Create crop info
    crop_info = {
        'applied': True,
        'margin_ratio': margin_ratio,
        'original_size': image.shape,
        'cropped_size': cropped.shape,
        'margins': (margin_x, margin_y, margin_x, margin_y),
        'pixels_removed': {
            'left': margin_x,
            'top': margin_y,
            'right': margin_x,
            'bottom': margin_y,
            'total': 2 * margin_x * height + 2 * margin_y * (width - 2 * margin_x)
        }
    }

    return cropped, crop_info


def convert_to_grayscale(image):
    """
    Convert image to grayscale.

    Args:
        image (numpy.ndarray): Input image

    Returns:
        numpy.ndarray: Grayscale image
    """
    if len(image.shape) == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image.copy()


def apply_gaussian_blur(image):
    """
    Apply Gaussian blur to reduce noise.

    Args:
        image (numpy.ndarray): Input grayscale image

    Returns:
        numpy.ndarray: Blurred image
    """
    return cv2.GaussianBlur(image, config.GAUSSIAN_BLUR_KERNEL, 0)


def apply_threshold(image):
    """
    Apply inverted binary threshold (black markers become white).

    Args:
        image (numpy.ndarray): Input grayscale image

    Returns:
        numpy.ndarray: Binary thresholded image
    """
    _, thresh = cv2.threshold(image, config.THRESHOLD_VALUE, 255, cv2.THRESH_BINARY_INV)
    return thresh


# =============================================================================
# VISUALIZATION FUNCTIONS
# =============================================================================

def create_preprocessing_visualization(original, cropped, gray, blurred, binary):
    """
    Create 5-step visualization: Original → Cropped → Grayscale → Blurred → Thresholded.

    Args:
        original (numpy.ndarray): Original color image
        cropped (numpy.ndarray): Margin-cropped image
        gray (numpy.ndarray): Grayscale image
        blurred (numpy.ndarray): Blurred image
        binary (numpy.ndarray): Binary thresholded image

    Returns:
        numpy.ndarray: Combined visualization
    """
    vis_height = config.VISUALIZATION_HEIGHT

    # Resize all images to same height
    images = [
        _resize_to_height(original, vis_height),
        _resize_to_height(cropped, vis_height),
        _resize_to_height(_to_bgr(gray), vis_height),
        _resize_to_height(_to_bgr(blurred), vis_height),
        _resize_to_height(_to_bgr(binary), vis_height)
    ]

    # Combine horizontally
    combined = np.hstack(images)

    # Add labels
    return _add_visualization_labels(combined,
        ["ORIGINAL", "CROPPED", "GRAYSCALE", "BLURRED", "THRESHOLDED"])


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def _create_no_crop_info(image, margin_ratio):
    """Create crop info when no cropping is applied."""
    return {
        'applied': False,
        'margin_ratio': margin_ratio,
        'original_size': image.shape,
        'margins': (0, 0, 0, 0)
    }


def _print_preprocessing_summary(original, cropped, crop_info):
    """Print preprocessing summary."""
    print(f"   ✓ Applied permanent margin crop: {original.shape} -> {cropped.shape}")
    if crop_info['applied']:
        print(f"   ✓ Removed {crop_info['pixels_removed']['total']} pixels from margins")
    print(f"   ✓ Converted to grayscale: {cropped.shape[:2]}")
    print(f"   ✓ Applied Gaussian blur with kernel: {config.GAUSSIAN_BLUR_KERNEL}")
    print(f"   ✓ Applied inverted threshold at value: {config.THRESHOLD_VALUE}")


def _resize_to_height(image, target_height):
    """Resize image to specific height maintaining aspect ratio."""
    h, w = image.shape[:2]
    aspect_ratio = w / h
    target_width = int(target_height * aspect_ratio)
    return cv2.resize(image, (target_width, target_height))


def _to_bgr(image):
    """Convert grayscale image to BGR for visualization."""
    if len(image.shape) == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return image


def _add_visualization_labels(combined_image, labels):
    """Add text labels to combined visualization."""
    label_height = 30
    total_height = combined_image.shape[0] + label_height
    total_width = combined_image.shape[1]

    # Create labeled image
    labeled = np.zeros((total_height, total_width, 3), dtype=np.uint8)
    labeled[label_height:, :] = combined_image

    # Add labels
    font = cv2.FONT_HERSHEY_SIMPLEX
    img_width = total_width // len(labels)

    for i, label in enumerate(labels):
        x_pos = i * img_width + img_width // 2 - len(label) * 4
        cv2.putText(labeled, label, (x_pos, 20), font, 0.6, (255, 255, 255), 2)

    return labeled
