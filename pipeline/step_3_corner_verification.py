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
    Verify a single corner by drawing lines from adjacent corners.

    For each corner:
    - TL: lines from TR and BL
    - TR: lines from TL and BR
    - BR: lines from TR and BL
    - BL: lines from TL and BR
    """
    x, y = corner

    # Define adjacent corners for each position
    adjacent_map = {
        "TL": ["TR", "BL"],
        "TR": ["TL", "BR"],
        "BR": ["TR", "BL"],
        "BL": ["TL", "BR"]
    }

    if current_label not in adjacent_map:
        return False

    adjacent_labels = adjacent_map[current_label]

    # Find adjacent corners
    adjacent_corners = []
    for i, label in enumerate(corner_labels):
        if label in adjacent_labels and i != corner_index:
            adjacent_corners.append(all_corners[i])

    if len(adjacent_corners) < 2:
        # Not enough adjacent corners found
        cv2.circle(vis_image, corner, config.CORNER_VERIFICATION_CIRCLE_RADIUS, config.COLOR_RED, config.CORNER_VERIFICATION_CIRCLE_THICKNESS)
        cv2.putText(vis_image, f"{current_label}-FAIL", (x+config.CORNER_VERIFICATION_TEXT_OFFSET_X, y+config.CORNER_VERIFICATION_TEXT_OFFSET_Y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.COLOR_RED, 2)
        return False

    # Draw lines from adjacent corners and check if they pass through current corner
    lines_passing = 0
    tolerance = config.CORNER_VERIFICATION_TOLERANCE

    for i, adj_corner in enumerate(adjacent_corners[:2]):  # Only use first 2 adjacent corners
        adj_x, adj_y = adj_corner

        # Determine if line should be horizontal or vertical
        if current_label == "TL":
            if abs(adj_y - y) < abs(adj_x - x):  # More horizontal difference
                # Draw horizontal line from TR
                line_color = config.COLOR_ORANGE
                cv2.line(vis_image, (0, adj_y), (vis_image.shape[1], adj_y), line_color, config.CORNER_VERIFICATION_LINE_THICKNESS)
                if abs(y - adj_y) <= tolerance:
                    lines_passing += 1
            else:
                # Draw vertical line from BL
                line_color = config.COLOR_LIGHT_BLUE
                cv2.line(vis_image, (adj_x, 0), (adj_x, vis_image.shape[0]), line_color, config.CORNER_VERIFICATION_LINE_THICKNESS)
                if abs(x - adj_x) <= tolerance:
                    lines_passing += 1

        elif current_label == "TR":
            if abs(adj_y - y) < abs(adj_x - x):  # More horizontal difference
                # Draw horizontal line from TL
                line_color = config.COLOR_ORANGE
                cv2.line(vis_image, (0, adj_y), (vis_image.shape[1], adj_y), line_color, config.CORNER_VERIFICATION_LINE_THICKNESS)
                if abs(y - adj_y) <= tolerance:
                    lines_passing += 1
            else:
                # Draw vertical line from BR
                line_color = config.COLOR_LIGHT_BLUE
                cv2.line(vis_image, (adj_x, 0), (adj_x, vis_image.shape[0]), line_color, config.CORNER_VERIFICATION_LINE_THICKNESS)
                if abs(x - adj_x) <= tolerance:
                    lines_passing += 1

        elif current_label == "BR":
            if abs(adj_y - y) < abs(adj_x - x):  # More horizontal difference
                # Draw horizontal line from BL
                line_color = config.COLOR_ORANGE
                cv2.line(vis_image, (0, adj_y), (vis_image.shape[1], adj_y), line_color, config.CORNER_VERIFICATION_LINE_THICKNESS)
                if abs(y - adj_y) <= tolerance:
                    lines_passing += 1
            else:
                # Draw vertical line from TR
                line_color = config.COLOR_LIGHT_BLUE
                cv2.line(vis_image, (adj_x, 0), (adj_x, vis_image.shape[0]), line_color, config.CORNER_VERIFICATION_LINE_THICKNESS)
                if abs(x - adj_x) <= tolerance:
                    lines_passing += 1

        elif current_label == "BL":
            if abs(adj_y - y) < abs(adj_x - x):  # More horizontal difference
                # Draw horizontal line from BR
                line_color = config.COLOR_ORANGE
                cv2.line(vis_image, (0, adj_y), (vis_image.shape[1], adj_y), line_color, config.CORNER_VERIFICATION_LINE_THICKNESS)
                if abs(y - adj_y) <= tolerance:
                    lines_passing += 1
            else:
                # Draw vertical line from TL
                line_color = config.COLOR_LIGHT_BLUE
                cv2.line(vis_image, (adj_x, 0), (adj_x, vis_image.shape[0]), line_color, config.CORNER_VERIFICATION_LINE_THICKNESS)
                if abs(x - adj_x) <= tolerance:
                    lines_passing += 1

    # A corner passes if at least 1 line passes through it
    is_valid = lines_passing >= config.CORNER_VERIFICATION_MIN_LINES

    # Draw corner marker
    if is_valid:
        cv2.circle(vis_image, corner, config.CORNER_VERIFICATION_CIRCLE_RADIUS, config.COLOR_GREEN, config.CORNER_VERIFICATION_CIRCLE_THICKNESS)
        cv2.putText(vis_image, f"{current_label}-OK", (x+config.CORNER_VERIFICATION_TEXT_OFFSET_X, y+config.CORNER_VERIFICATION_TEXT_OFFSET_Y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.COLOR_GREEN, 2)
    else:
        cv2.circle(vis_image, corner, config.CORNER_VERIFICATION_CIRCLE_RADIUS, config.COLOR_RED, config.CORNER_VERIFICATION_CIRCLE_THICKNESS)
        cv2.putText(vis_image, f"{current_label}-FAIL", (x+config.CORNER_VERIFICATION_TEXT_OFFSET_X, y+config.CORNER_VERIFICATION_TEXT_OFFSET_Y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.COLOR_RED, 2)

    # Draw arrows showing incoming/outgoing directions
    _draw_direction_arrows(vis_image, corner, adjacent_corners, current_label)

    return is_valid


def _draw_direction_arrows(vis_image, corner, adjacent_corners, corner_label):
    """Draw arrows showing incoming and outgoing line directions."""
    x, y = corner
    arrow_length = config.CORNER_VERIFICATION_ARROW_LENGTH

    for adj_corner in adjacent_corners:
        adj_x, adj_y = adj_corner

        # Calculate direction vector
        dx = adj_x - x
        dy = adj_y - y

        # Normalize
        length = np.sqrt(dx*dx + dy*dy)
        if length > 0:
            dx /= length
            dy /= length

            # Draw incoming arrow (from adjacent to current)
            start_x = int(x + dx * arrow_length)
            start_y = int(y + dy * arrow_length)
            cv2.arrowedLine(vis_image, (start_x, start_y), (x, y), config.COLOR_YELLOW, 2, tipLength=0.3)

            # Draw outgoing arrow (from current to adjacent)
            end_x = int(x - dx * arrow_length)
            end_y = int(y - dy * arrow_length)
            cv2.arrowedLine(vis_image, (x, y), (end_x, end_y), config.COLOR_CYAN_ARROWS, 2, tipLength=0.3)


def _save_step_image(image, filename):
    """Save step image to tmp/steps directory."""
    steps_dir = "tmp/steps"
    os.makedirs(steps_dir, exist_ok=True)
    output_path = os.path.join(steps_dir, filename)
    cv2.imwrite(output_path, image)
    print(f"   💾 Saved: {output_path}")
