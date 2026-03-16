from .poseEstimation.detector_2d import detect_2d_poses, validate_video_file
from .poseEstimation.lifter_3d import lift_2d_to_3d
from .preProcessing.viewpoint_validator import validate_viewpoint
from .preProcessing.stabilizer import stabilize_video
import os

def run_pose_estimation_pipeline(video_path: str, expected_view: str):
    is_valid, msg = validate_video_file(video_path)
    if not is_valid:
        return {"error": msg}, None
    
    # --- 1. Stabilization ---
    stab_path = video_path.replace(".mp4", "_stab.mp4")
    stabilize_video(video_path, stab_path)

    # --- 2. 2D Detection ---
    keypoints_2d, res = detect_2d_poses(stab_path)
    
    # --- 3. Viewpoint Validation ---
    actual_view, ratio = validate_viewpoint(keypoints_2d)
    print(f"Validation: Expected {expected_view}, Detected {actual_view} (Ratio: {ratio:.2f})")
    
    if actual_view != expected_view:
        return {"error": f"Invalid Camera Angle. This slot expects {expected_view}, but we detected {actual_view}."}

    # --- 4. 3D Lifting ---
    keypoints_3d = lift_2d_to_3d(keypoints_2d, res)
    
    # Cleanup stabilized file
    if os.path.exists(stab_path): os.remove(stab_path)
    
    return keypoints_2d, keypoints_3d