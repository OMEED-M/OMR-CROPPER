"""
Step 3: Corner Verification
Verify detected corners by drawing horizontal and vertical lines from adjacent corners.
"""

import cv2
import numpy as np
import os
import config


def verify_corners(contours, original_image, base_name="1"):
    """
    Verify corner markers by drawing lines from adjacent corners.

    Args:
        contours: List of synthetic contours from Step 2
        original_image: Color image for visualization
        base_name: Base name for output files

    Returns:
        tuple: (visualization_image, verified_contours, needs_recalculation)
    """
    if len(contours) < 3:
        print(f"   ⚠️  Warning: Only {len(contours)} contours found, need at least 3 for verification")
        vis_image = original_image.copy()
        _save_step_image(vis_image, f"{base_name}_step_3a_corner_verification.jpg")
        return vis_image, contours, False

    # Extract corner points from contours
    corners = _extract_corners_from_contours(contours)

    if len(corners) < 3:
        print(f"   ⚠️  Warning: Could only extract {len(corners)} corner points")
        vis_image = original_image.copy()
        _save_step_image(vis_image, f"{base_name}_step_3a_corner_verification.jpg")
        return vis_image, contours, False

    print(f"   ✓ Verifying {len(corners)} corner points")

    # Create visualization image
    vis_image = original_image.copy()

    # Identify corner positions (TL, TR, BR, BL)
    corner_labels = _identify_corner_positions(corners)

    # Verify each corner by drawing lines from adjacent corners
    verified_corners = []
    failed_corner_labels = []

    for i, (corner, label) in enumerate(zip(corners, corner_labels)):
        is_valid = _verify_single_corner(vis_image, corner, corners, corner_labels, label, i)

        if is_valid:
            verified_corners.append(contours[i])
            print(f"   ✓ Corner {label} at {corner} passed verification")
        else:
            failed_corner_labels.append(label)
            print(f"   ❌ Corner {label} at {corner} failed verification - marking as missing")

    # If we have failed corners, mark them as missing and request recalculation
    if failed_corner_labels:
        print(f"   🔧 Marking {len(failed_corner_labels)} corner(s) as missing: {', '.join(failed_corner_labels)}")

        # Mark the first failed corner as missing for recalculation
        # (We only handle one missing corner at a time for stability)
        import config as config_module
        config_module.FORCE_MISSING_CORNER = failed_corner_labels[0]
        print(f"   ↩️  Requesting recalculation with missing corner: {failed_corner_labels[0]}")

        # Save visualization and return with recalculation request
        _save_step_image(vis_image, f"{base_name}_step_3a_corner_verification.jpg")
        print(f"   📊 Verification result: {len(verified_corners)}/{len(contours)} corners passed - RECALCULATION NEEDED")
        return vis_image, verified_corners, True

    # Save visualization
    _save_step_image(vis_image, f"{base_name}_step_3a_corner_verification.jpg")

    print(f"   📊 Verification result: {len(verified_corners)}/{len(contours)} corners passed")

    return vis_image, verified_corners, False


def _extract_corners_from_contours(contours):
    """Extract corner points from synthetic contours."""
    corners = []
    for contour in contours:
        # Each synthetic contour represents a corner region
        # Get the centroid of the contour
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            corners.append((cx, cy))
    return corners


def _identify_corner_positions(corners):
    """Identify which corner is TL, TR, BR, BL based on coordinates."""
    if len(corners) < 4:
        # If we have less than 4 corners, try to identify what we have
        corners_array = np.array(corners)
        center_x = np.mean(corners_array[:, 0])
        center_y = np.mean(corners_array[:, 1])

        labels = []
        for corner in corners:
            x, y = corner
            if x < center_x and y < center_y:
                labels.append("TL")
            elif x > center_x and y < center_y:
                labels.append("TR")
            elif x > center_x and y > center_y:
                labels.append("BR")
            else:
                labels.append("BL")
        return labels

    # Sort corners to identify TL, TR, BR, BL
    corners_array = np.array(corners)

    # Find centroid
    center_x = np.mean(corners_array[:, 0])
    center_y = np.mean(corners_array[:, 1])

    # Classify corners based on position relative to center
    labels = []
    for corner in corners:
        x, y = corner
        if x < center_x and y < center_y:
            labels.append("TL")
        elif x > center_x and y < center_y:
            labels.append("TR")
        elif x > center_x and y > center_y:
            labels.append("BR")
        else:
            labels.append("BL")

    return labels


def _verify_single_corner(vis_image, corner, all_corners, corner_labels, current_label, corner_index):
    """
    Verify a single corner by checking if lines from adjacent corners pass through it.
    """
    x, y = corner
    img_height, img_width = vis_image.shape[:2]
    diagonal = np.sqrt(img_width**2 + img_height**2)

    # Calculate relative tolerance and circle radius
    tolerance = int(diagonal * config.CORNER_VERIFICATION_TOLERANCE_RATIO)
    circle_radius = int(diagonal * config.CORNER_VERIFICATION_CIRCLE_RADIUS_RATIO)

    # Define adjacent corners for each position
    adjacent_map = {
        "TL": ["TR", "BL"],
        "TR": ["TL", "BR"],
        "BR": ["TR", "BL"],
        "BL": ["TL", "BR"]
    }

    if current_label not in adjacent_map:
        return False

    # Find adjacent corners
    adjacent_corners = []
    for i, label in enumerate(corner_labels):
        if label in adjacent_map[current_label] and i != corner_index:
            adjacent_corners.append(all_corners[i])

    if len(adjacent_corners) < 2:
        cv2.circle(vis_image, corner, circle_radius, config.COLOR_RED, 2)
        return False

    # Draw both horizontal and vertical lines from adjacent corners
    lines_passing = 0

    for adj_corner in adjacent_corners:
        adj_x, adj_y = adj_corner

        # Always draw horizontal line from adjacent corner
        cv2.line(vis_image, (0, adj_y), (img_width, adj_y), config.COLOR_ORANGE, 1)
        # Check if horizontal line passes through current corner
        if abs(y - adj_y) <= tolerance:
            lines_passing += 1

        # Always draw vertical line from adjacent corner
        cv2.line(vis_image, (adj_x, 0), (adj_x, img_height), config.COLOR_LIGHT_BLUE, 1)
        # Check if vertical line passes through current corner
        if abs(x - adj_x) <= tolerance:
            lines_passing += 1

    # Corner passes if minimum lines pass through it
    is_valid = lines_passing >= config.CORNER_VERIFICATION_MIN_LINES

    # Draw simple corner marker
    color = config.COLOR_GREEN if is_valid else config.COLOR_RED
    cv2.circle(vis_image, corner, circle_radius, color, 2)

    return is_valid


def _save_step_image(image, filename):
    """Save step image to configured directory with automatic overwrite."""
    steps_path = os.path.join(config.tmp_dir, config.steps_dir)
    # Always create directory structure (handles existing directories gracefully)
    os.makedirs(steps_path, exist_ok=True)
    output_path = os.path.join(steps_path, filename)
    # cv2.imwrite automatically overwrites existing files
    success = cv2.imwrite(output_path, image)
    if success:
        print(f"   💾 Saved: {output_path}")
    else:
        print(f"   ❌ Failed to save: {output_path}")
