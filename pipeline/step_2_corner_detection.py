"""
Step 2: Corner Detection
Grid-based analysis to detect corner marker locations.
"""

import cv2
import numpy as np
import os
import config


def find_markers(binary_image, original_image, base_name="1"):
    """
    Detect corner markers using grid-based analysis.

    Args:
        binary_image: Input binary image
        original_image: Original color image for visualization
        base_name: Base name for output files

    Returns:
        tuple: (visualization_image, synthetic_contours)
    """
    height, width = binary_image.shape

    # Define corner regions
    corner_regions = _define_corner_regions(width, height)
    cell_size = max(1, int(width * config.CELL_SIZE_RATIO))

    print(f"   📐 Corner grid: {corner_regions['TL'][2]}x{corner_regions['TL'][3]} regions")

    # Create grid visualization
    grid_vis = _create_grid_visualization(binary_image, corner_regions, cell_size)
    _save_step_image(grid_vis, f"{base_name}_step_2a_grid.jpg")

    # Detect white cells in each corner
    corner_results = _analyze_corners(binary_image, corner_regions, cell_size)

    # Create white cell visualization
    white_vis = _create_white_cell_visualization(grid_vis, corner_results)
    _save_step_image(white_vis, f"{base_name}_step_2b_white_cells.jpg")

    # Select best cells
    best_cells = _select_best_cells(corner_results, corner_regions, width, height)

    # Create best cell visualization
    best_vis = _create_best_cell_visualization(grid_vis, best_cells)
    _save_step_image(best_vis, f"{base_name}_step_2d_best_cells.jpg")

    # Handle missing corners
    final_cells = _handle_missing_corners(best_cells, width, height, base_name, grid_vis)

    # Create synthetic contours
    contours = _create_synthetic_contours(final_cells, binary_image.shape)

    print(f"   ✅ Found {len(final_cells)} corners")
    return white_vis, contours


def _define_corner_regions(width, height):
    """Define corner regions for analysis."""
    corner_size_x = width // config.CORNER_REGION_RATIO_X
    corner_size_y = height // config.CORNER_REGION_RATIO_Y

    return {
        'TL': (0, 0, corner_size_x, corner_size_y),
        'TR': (width - corner_size_x, 0, corner_size_x, corner_size_y),
        'BL': (0, height - corner_size_y, corner_size_x, corner_size_y),
        'BR': (width - corner_size_x, height - corner_size_y, corner_size_x, corner_size_y)
    }


def _create_grid_visualization(binary_image, corner_regions, cell_size):
    """Create grid visualization on binary image."""
    vis_image = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    height, width = vis_image.shape[:2]

    corner_colors = {
        'TL': config.COLOR_RED,
        'TR': config.COLOR_GREEN,
        'BL': config.COLOR_BLUE,
        'BR': config.COLOR_CYAN
    }

    for corner_name, (x, y, w, h) in corner_regions.items():
        color = corner_colors[corner_name]
        thickness = max(1, int(width * config.CORNER_BOUNDARY_THICKNESS_RATIO))
        dash_length = max(1, int(width * config.DASH_LENGTH_RATIO))

        x_end = width if corner_name in ['TR', 'BR'] else x + w
        y_end = height if corner_name in ['BL', 'BR'] else y + h

        # Draw dashed boundaries
        _draw_dashed_lines(vis_image, x, y, x_end, y_end, color, thickness, dash_length)

        # Draw cell grid
        _draw_cell_grid(vis_image, x, y, x_end, y_end, cell_size)

    return vis_image


def _draw_dashed_lines(image, x1, y1, x2, y2, color, thickness, dash_length):
    """Draw dashed rectangle."""
    # Top and bottom lines
    for i in range(x1, x2, dash_length * 2):
        end_x = min(i + dash_length, x2)
        cv2.line(image, (i, y1), (end_x, y1), color, thickness)
        cv2.line(image, (i, y2 - 1), (end_x, y2 - 1), color, thickness)

    # Left and right lines
    for i in range(y1, y2, dash_length * 2):
        end_y = min(i + dash_length, y2)
        cv2.line(image, (x1, i), (x1, end_y), color, thickness)
        cv2.line(image, (x2 - 1, i), (x2 - 1, end_y), color, thickness)


def _draw_cell_grid(image, x1, y1, x2, y2, cell_size):
    """Draw cell grid lines."""
    cell_color = (128, 128, 128)

    # Vertical lines
    for cell_x in range(x1, x2, cell_size):
        cv2.line(image, (cell_x, y1), (cell_x, y2), cell_color, config.CELL_GRID_THICKNESS)

    # Horizontal lines
    for cell_y in range(y1, y2, cell_size):
        cv2.line(image, (x1, cell_y), (x2, cell_y), cell_color, config.CELL_GRID_THICKNESS)


def _analyze_corners(binary_image, corner_regions, cell_size):
    """Analyze corners to find white cells."""
    corner_results = {}

    for corner_name, (x, y, w, h) in corner_regions.items():
        if config.FORCE_MISSING_CORNER and corner_name == config.FORCE_MISSING_CORNER:
            corner_results[corner_name] = []
            continue

        corner_roi = binary_image[y:y+h, x:x+w]
        white_cells = []

        for cell_y in range(0, h, cell_size):
            for cell_x in range(0, w, cell_size):
                cell_roi = corner_roi[cell_y:cell_y+cell_size, cell_x:cell_x+cell_size]

                if cell_roi.size > 0:
                    white_percentage = (np.sum(cell_roi == 255) / cell_roi.size) * 100

                    if white_percentage > config.WHITE_CELL_THRESHOLD:
                        white_cells.append({
                            'center': (x + cell_x + cell_size//2, y + cell_y + cell_size//2),
                            'white_percentage': white_percentage,
                            'corner': corner_name
                        })

        corner_results[corner_name] = white_cells

    return corner_results


def _create_white_cell_visualization(base_image, corner_results):
    """Add green markers for white cells."""
    vis_image = base_image.copy()
    green_color = (0, 255, 0)
    cell_size = 6

    for corner_cells in corner_results.values():
        for cell in corner_cells:
            center_x, center_y = cell['center']
            top_left = (center_x - cell_size//2, center_y - cell_size//2)
            bottom_right = (center_x + cell_size//2, center_y + cell_size//2)
            cv2.rectangle(vis_image, top_left, bottom_right, green_color, 1)

    return vis_image


def _select_best_cells(corner_results, corner_regions, width, height):
    """Select best cell from each corner based on edge proximity."""
    best_cells = []

    for corner_name, cells in corner_results.items():
        if not cells or (config.FORCE_MISSING_CORNER and corner_name == config.FORCE_MISSING_CORNER):
            continue

        if corner_name in ['TL', 'BL']:
            # Select closest to left edge
            best_cell = min(cells, key=lambda c: c['center'][0])
        else:
            # Select closest to right edge
            best_cell = max(cells, key=lambda c: c['center'][0])

        best_cells.append(best_cell)

    return best_cells


def _create_best_cell_visualization(base_image, best_cells):
    """Highlight best cells with red circles."""
    vis_image = base_image.copy()
    height, width = vis_image.shape[:2]

    red_color = config.COLOR_RED
    radius = max(1, int(width * config.BEST_CELL_CIRCLE_RADIUS_RATIO))
    thickness = max(1, int(width * config.BEST_CELL_CIRCLE_THICKNESS_RATIO))

    for cell in best_cells:
        center = cell['center']
        cv2.circle(vis_image, center, radius, red_color, thickness)
        cv2.circle(vis_image, center, 2, red_color, -1)

    return vis_image


def _handle_missing_corners(best_cells, width, height, base_name, grid_vis):
    """Handle missing corner calculation."""
    final_cells = best_cells.copy()

    if len(best_cells) == 3:
        calculated = _calculate_missing_corner(best_cells, width, height)
        if calculated:
            if config.FORCE_MISSING_CORNER:
                calculated['corner'] = config.FORCE_MISSING_CORNER
            final_cells.append(calculated)

            # Create calculated corner visualization
            calc_vis = _create_calculated_corner_visualization(grid_vis, best_cells, calculated)
            _save_step_image(calc_vis, f"{base_name}_step_2e_calculated_corner.jpg")

    return final_cells


def _calculate_missing_corner(detected_corners, width, height):
    """Calculate missing 4th corner from 3 detected corners."""
    if len(detected_corners) != 3:
        return None

    corners_by_name = {c['corner']: c['center'] for c in detected_corners}
    detected_names = set(corners_by_name.keys())
    missing_name = list({'TL', 'TR', 'BL', 'BR'} - detected_names)[0]

    # Calculate using geometric relationships
    if missing_name == 'TL':
        tr, bl, br = corners_by_name['TR'], corners_by_name['BL'], corners_by_name['BR']
        pos = (tr[0] + bl[0] - br[0], tr[1] + bl[1] - br[1])
    elif missing_name == 'TR':
        tl, br, bl = corners_by_name['TL'], corners_by_name['BR'], corners_by_name['BL']
        pos = (tl[0] + br[0] - bl[0], tl[1] + br[1] - bl[1])
    elif missing_name == 'BL':
        tl, br, tr = corners_by_name['TL'], corners_by_name['BR'], corners_by_name['TR']
        pos = (tl[0] + br[0] - tr[0], tl[1] + br[1] - tr[1])
    else:  # BR
        tl, tr, bl = corners_by_name['TL'], corners_by_name['TR'], corners_by_name['BL']
        pos = (tr[0] + bl[0] - tl[0], tr[1] + bl[1] - tl[1])

    # Clamp to image bounds
    x = max(0, min(int(pos[0]), width - 1))
    y = max(0, min(int(pos[1]), height - 1))

    return {
        'center': (x, y),
        'corner': missing_name,
        'white_percentage': 100.0,
        'is_calculated': True
    }


def _create_calculated_corner_visualization(base_image, detected_corners, calculated_corner):
    """Show detected corners (red) and calculated corner (blue)."""
    vis_image = base_image.copy()
    height, width = vis_image.shape[:2]

    radius = max(1, int(width * config.BEST_CELL_CIRCLE_RADIUS_RATIO))
    thickness = max(1, int(width * config.BEST_CELL_CIRCLE_THICKNESS_RATIO))

    # Draw detected corners in red
    for corner in detected_corners:
        center = corner['center']
        cv2.circle(vis_image, center, radius, config.COLOR_RED, thickness)
        cv2.circle(vis_image, center, 2, config.COLOR_RED, -1)

    # Draw calculated corner in blue
    if calculated_corner:
        center = calculated_corner['center']
        square_size = radius
        top_left = (center[0] - square_size, center[1] - square_size)
        bottom_right = (center[0] + square_size, center[1] + square_size)
        cv2.rectangle(vis_image, top_left, bottom_right, config.COLOR_BLUE, thickness)
        cv2.circle(vis_image, center, 2, config.COLOR_BLUE, -1)

    return vis_image


def _create_synthetic_contours(cells, image_shape):
    """Create synthetic contours from cell centers."""
    contours = []

    for cell in cells:
        center_x, center_y = cell['center']
        size = max(1, int(image_shape[1] * config.SYNTHETIC_MARKER_SIZE_RATIO))

        points = np.array([
            [center_x - size, center_y - size],
            [center_x + size, center_y - size],
            [center_x + size, center_y + size],
            [center_x - size, center_y + size]
        ], dtype=np.int32)

        # Clamp to image bounds
        points[:, 0] = np.clip(points[:, 0], 0, image_shape[1] - 1)
        points[:, 1] = np.clip(points[:, 1], 0, image_shape[0] - 1)

        contours.append(points.reshape(-1, 1, 2))

    return contours


def _save_step_image(image, filename):
    """Save step image to configured directory with automatic overwrite."""
    steps_path = os.path.join(config.tmp_dir, config.steps_dir)
    # Always create directory structure (handles existing directories gracefully)
    os.makedirs(steps_path, exist_ok=True)
    path = os.path.join(steps_path, filename)
    # cv2.imwrite automatically overwrites existing files
    success = cv2.imwrite(path, image)
    if success:
        print(f"   💾 Step 2: Saved {path}")
    else:
        print(f"   ❌ Step 2: Failed to save {path}")
