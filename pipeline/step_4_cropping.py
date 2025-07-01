"""
Step 4: Cropping
Apply perspective transformation and crop the image based on verified corners.
"""

import cv2
import numpy as np
import os
import config


def detect_markers(contours, original_image, crop_info=None, base_name="1"):
    """
    Apply perspective transformation and crop the image.

    Args:
        contours: List of synthetic contours from Step 2
        original_image: Color image for cropping
        crop_info: Not used (kept for compatibility)
        base_name: Base name for output files

    Returns:
        tuple: (visualization_image, cropped_image)
    """
    if len(contours) < 3:
        print(f"   ⚠️  Warning: Only {len(contours)} contours found, need at least 3 for cropping")
        vis_image = original_image.copy()
        _save_step_image(vis_image, f"{base_name}_step_4a_crop_process.jpg")
        return vis_image, original_image

    # Extract corner points from contours
    corners = _extract_corners_from_contours(contours)

    if len(corners) < 4:
        print(f"   ⚠️  Warning: Could only extract {len(corners)} corner points, need 4")
        vis_image = original_image.copy()
        _save_step_image(vis_image, f"{base_name}_step_4a_crop_process.jpg")
        return vis_image, original_image

    print(f"   ✓ Extracted {len(corners)} corner points from Step 3")

    # Ensure we have exactly 4 corners for processing
    working_corners = _ensure_four_corners(corners)

    # Sort corners in clockwise order: TL, TR, BR, BL
    sorted_corners = _sort_corners_clockwise(working_corners)

    # Create cropped image using perspective transformation
    cropped_image = _crop_with_perspective(original_image, sorted_corners)

    # Create visualization showing the cropping process
    vis_image = _create_crop_visualization(original_image, sorted_corners)

    # Save step images
    _save_step_image(vis_image, f"{base_name}_step_4a_crop_process.jpg")
    _save_step_image(cropped_image, f"{base_name}_step_4b_cropped_deskewed.jpg")

    print(f"   ✓ Cropped image using {len(sorted_corners)} corner points from Step 3 verified corners")
    return vis_image, cropped_image


def _extract_corners_from_contours(contours):
    """Extract center points from contours."""
    corners = []
    for contour in contours:
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            corners.append((cx, cy))
    return corners


def _ensure_four_corners(corners):
    """Ensure we have exactly 4 corners for processing."""
    working_corners = corners.copy()
    if len(working_corners) == 3:
        # Duplicate one corner to make sorting algorithms work
        working_corners.append(working_corners[-1])
        print(f"   🔧 Padded to 4 corners for processing (last corner duplicated)")
    return working_corners


def _sort_corners_clockwise(corners):
    """Sort corner points in clockwise order: TL, TR, BR, BL."""
    points = np.array(corners)
    center_x = np.mean(points[:, 0])
    center_y = np.mean(points[:, 1])

    # Group points by quadrant
    quadrants = {'TL': [], 'TR': [], 'BR': [], 'BL': []}

    for point in corners:
        x, y = point
        if x <= center_x and y <= center_y:
            quadrants['TL'].append(point)
        elif x > center_x and y <= center_y:
            quadrants['TR'].append(point)
        elif x > center_x and y > center_y:
            quadrants['BR'].append(point)
        else:
            quadrants['BL'].append(point)

    # Select best candidate from each quadrant
    sorted_corners = []

    # Top-left: minimize distance to (0,0)
    if quadrants['TL']:
        tl = min(quadrants['TL'], key=lambda p: p[0] + p[1])
        sorted_corners.append(tl)

    # Top-right: maximize x, minimize y
    if quadrants['TR']:
        tr = max(quadrants['TR'], key=lambda p: p[0] - p[1])
        sorted_corners.append(tr)

    # Bottom-right: maximize distance from (0,0)
    if quadrants['BR']:
        br = max(quadrants['BR'], key=lambda p: p[0] + p[1])
        sorted_corners.append(br)

    # Bottom-left: minimize x, maximize y
    if quadrants['BL']:
        bl = min(quadrants['BL'], key=lambda p: p[1] - p[0])
        sorted_corners.append(bl)

    # Fill with remaining points if needed
    if len(sorted_corners) < 4:
        for point in corners:
            if point not in sorted_corners:
                sorted_corners.append(point)
                if len(sorted_corners) == 4:
                    break

    return sorted_corners[:4]


def _crop_with_perspective(image, corners):
    """Apply perspective transformation to crop the image."""
    if len(corners) < 4:
        return image

    # Source points (from detected corners)
    src_points = np.array(corners, dtype=np.float32)

    # Destination points (output rectangle)
    dst_points = np.array([
        [0, 0],                                    # Top-left
        [config.OUTPUT_WIDTH - 1, 0],             # Top-right
        [config.OUTPUT_WIDTH - 1, config.OUTPUT_HEIGHT - 1],  # Bottom-right
        [0, config.OUTPUT_HEIGHT - 1]             # Bottom-left
    ], dtype=np.float32)

    # Calculate and apply perspective transformation
    transform_matrix = cv2.getPerspectiveTransform(src_points, dst_points)
    cropped = cv2.warpPerspective(image, transform_matrix, (config.OUTPUT_WIDTH, config.OUTPUT_HEIGHT))

    return cropped


def _create_crop_visualization(original_image, corners):
    """Create visualization showing the cropping process."""
    vis_image = original_image.copy()

    # Draw corner points with different colors
    colors = [config.COLOR_RED, config.COLOR_GREEN, config.COLOR_BLUE, config.COLOR_PINK]
    labels = ["TL", "TR", "BR", "BL"]

    for i, (corner, color, label) in enumerate(zip(corners, colors, labels)):
        x, y = int(corner[0]), int(corner[1])

        # Draw corner point
        cv2.circle(vis_image, (x, y), 10, color, -1)
        cv2.circle(vis_image, (x, y), 15, color, 3)

        # Add label
        cv2.putText(vis_image, label, (x + 20, y - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    # Draw quadrilateral connecting the corners
    if len(corners) >= 4:
        unique_corners = []
        for corner in corners:
            if not unique_corners or corner != unique_corners[-1]:
                unique_corners.append(corner)

        if len(unique_corners) >= 3:
            pts = np.array(unique_corners + [unique_corners[0]], dtype=np.int32)
            cv2.polylines(vis_image, [pts], False, config.COLOR_CYAN, 4)

    return vis_image


def _save_step_image(image, filename):
    """Save step image to configured directory."""
    path = os.path.join(config.tmp_dir, config.steps_dir, filename)
    cv2.imwrite(path, image)
    print(f"   💾 Step 3{'a' if 'process' in filename else 'b'}: {'Crop process visualization' if 'process' in filename else 'Final cropped result'} saved to {path}")
