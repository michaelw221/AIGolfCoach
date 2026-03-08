import pytest
import numpy as np
from lib.python.videoProcessing.preProcessing.viewpoint_validator import (
    validate_viewpoint, 
    L_SHOULDER, R_SHOULDER, 
    L_HIP, R_HIP
)

def create_mock_keypoints(shldr_l_x, shldr_r_x, shldr_y, hip_y):
    """
    Helper function to generate a valid 2D keypoint array 
    matching the expected YOLO/COCO output shape: (frames, keypoints, xy)
    """
    # Create a sequence with 1 frame, 17 keypoints, and 2 coordinates (x, y)
    kps = np.zeros((1, 17, 2))
    
    # Assign the coordinates based on the parameters
    # Note: Y increases as you go down the screen in standard image coordinates
    kps[0, L_SHOULDER] = [shldr_l_x, shldr_y]
    kps[0, R_SHOULDER] = [shldr_r_x, shldr_y]
    
    # We use the same X coordinates for hips to simulate a straight standing posture
    kps[0, L_HIP] = [shldr_l_x, hip_y]
    kps[0, R_HIP] = [shldr_r_x, hip_y]
    
    return kps

def test_validate_viewpoint_face_on():
    """Verify detection of a Face-On (FO) swing (Ratio > 0.8)."""
    # Shoulders are wide apart (100 pixels), torso is short (100 pixels) -> Ratio = 1.0
    mock_kps = create_mock_keypoints(shldr_l_x=100, shldr_r_x=200, shldr_y=50, hip_y=150)
    
    label, ratio = validate_viewpoint(mock_kps)
    
    assert label == "Face-On"
    assert ratio == 1.0


def test_validate_viewpoint_down_the_line():
    """Verify detection of a Down-the-Line (DTL) swing (Ratio < 0.4)."""
    # Shoulders overlap visually (20 pixels), torso is normal (100 pixels) -> Ratio = 0.2
    mock_kps = create_mock_keypoints(shldr_l_x=140, shldr_r_x=160, shldr_y=50, hip_y=150)
    
    label, ratio = validate_viewpoint(mock_kps)
    
    assert label == "Down-the-Line"
    assert ratio == 0.2


def test_validate_viewpoint_unsuitable():
    """Verify detection of an ambiguous diagonal angle (0.4 <= Ratio <= 0.8)."""
    # Shoulders are at a 45-degree angle (60 pixels), torso is normal (100 pixels) -> Ratio = 0.6
    mock_kps = create_mock_keypoints(shldr_l_x=120, shldr_r_x=180, shldr_y=50, hip_y=150)
    
    label, ratio = validate_viewpoint(mock_kps)
    
    assert label == "Unsuitable"
    assert ratio == 0.6


def test_validate_viewpoint_zero_division():
    """Verify that a zero-length torso prevents a crash (Division by Zero)."""
    # Shoulders and Hips share the exact same Y coordinate (Torso length = 0)
    mock_kps = create_mock_keypoints(shldr_l_x=100, shldr_r_x=200, shldr_y=100, hip_y=100)
    
    label, ratio = validate_viewpoint(mock_kps)
    
    assert label == "Unsuitable"
    assert ratio == 0