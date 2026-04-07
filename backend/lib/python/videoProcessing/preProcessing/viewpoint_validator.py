import numpy as np

# Indices from COCO/YOLO format
L_SHOULDER, R_SHOULDER = 5, 6
L_HIP, R_HIP = 11, 12

def validate_viewpoint(keypoints_2d: np.ndarray):
    """
    Analyzes the 'Address' frame to determine if the angle is FO or DTL.
    Logic: Uses the ratio of Shoulder Width to Torso Length.
    """
    # Use the first frame
    kps = keypoints_2d[0] 
    
    # 1. Calculate Shoulder Width (Horizontal)
    shldr_width = abs(kps[L_SHOULDER][0] - kps[R_SHOULDER][0])
    
    # 2. Calculate Torso Length (Average Vertical distance from shoulder to hip)
    l_torso = abs(kps[L_SHOULDER][1] - kps[L_HIP][1])
    r_torso = abs(kps[R_SHOULDER][1] - kps[R_HIP][1])
    torso_len = (l_torso + r_torso) / 2
    
    if torso_len == 0: return "Unsuitable", 0

    # 3. Calculate Ratio
    ratio = shldr_width / torso_len
    
    # Thresholds (Tuned for standard 16:9 or 4:3 mobile video)
    if ratio > 0.5:
        return "Face-On", ratio
    elif ratio < 0.4:
        return "Down-the-Line", ratio
    else:
        return "Unsuitable", ratio