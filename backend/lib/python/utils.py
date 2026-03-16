import numpy as np
import cv2

def get_midpoint(landmarks_frame, p1_index, p2_index):
    """Calculates the 3D midpoint between two keypoints in a single frame."""
    p1 = landmarks_frame[p1_index]
    p2 = landmarks_frame[p2_index]
    return (p1 + p2) / 2

def calculate_angle_2d(v1, v2):
    """
    Calculates the SIGNED angle between two 2D vectors.
    Returns a value between -180 and 180 degrees.
    """
    # Angle of vector 1 and vector 2 relative to the X-axis
    angle1 = np.arctan2(v1[1], v1[0])
    angle2 = np.arctan2(v2[1], v2[0])
    
    # Difference in radians
    angle = np.degrees(angle1 - angle2)
    
    # Normalize to [-180, 180]
    angle = (angle + 180) % 360 - 180
    return angle

def calculate_angle_3d(v1, v2):
    """Calculates the angle in degrees between two 3D vectors."""
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0 # Return 0 instead of crashing/returning NaN
    
    # Clip the value to the valid range [-1.0, 1.0] to prevent floating point errors
    cos_theta = np.clip(dot_product / (norm_v1 * norm_v2), -1.0, 1.0)
    
    angle_rad = np.arccos(cos_theta)
    return np.degrees(angle_rad)

def normalize_screen_coordinates(X, w, h):
    """
    Normalizes 2D keypoint coordinates to be in a [-1, 1] range.
    This is a direct replication of the function from the VideoPose3D repository.
    """
    assert X.shape[-1] == 2
    
    # Normalize so that [0, w] is mapped to [-1, 1], while preserving the aspect ratio
    return X / w * 2 - [1, h / w]

# YOLOv8-Pose COCO connections (the lines that connect the dots)
POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), # Hip/Legs
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10) # Shoulders/Arms
]

def draw_skeleton(frame, keypoints, color=(0, 255, 0)):
    """Draws skeleton lines on a frame."""
    frame_copy = frame.copy()
    # Draw joints (dots)
    for kp in keypoints:
        cv2.circle(frame_copy, (int(kp[0]), int(kp[1])), 5, color, -1)
    
    # Draw connections (lines)
    for p1, p2 in POSE_CONNECTIONS:
        if p1 < len(keypoints) and p2 < len(keypoints):
            pt1 = (int(keypoints[p1][0]), int(keypoints[p1][1]))
            pt2 = (int(keypoints[p2][0]), int(keypoints[p2][1]))
            if pt1 != (0,0) and pt2 != (0,0):
                cv2.line(frame_copy, pt1, pt2, color, 2)
    return frame_copy