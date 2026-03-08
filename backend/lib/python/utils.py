import numpy as np

def get_midpoint(landmarks_frame, p1_index, p2_index):
    """Calculates the 3D midpoint between two keypoints in a single frame."""
    p1 = landmarks_frame[p1_index]
    p2 = landmarks_frame[p2_index]
    return (p1 + p2) / 2

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