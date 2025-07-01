"""
OMR Sheet Marker Detection & Cropping System - Pipeline Package

This package contains the 7-step pipeline for processing OMR sheets:
1. Preprocessing (grayscale, blur)
2. Thresholding (binary conversion)
3. Find contours
4. Detect markers
5. Sort markers (TL, TR, BR, BL)
6. Warp and crop
7. Validate and repair

Each step is modular and can be used independently or as part of the complete pipeline.
"""

__version__ = "1.0.0"
__author__ = "tneerr"
