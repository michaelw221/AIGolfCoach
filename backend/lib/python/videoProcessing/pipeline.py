# lib/python/videoProcessing/pipeline.py
from .detector_2d import detect_2d_poses
from .lifter_3d import lift_2d_to_3d

def run_pose_estimation_pipeline(video_path: str):
    """
    The main orchestrator for the high-accuracy 2D->3D pipeline.

    Args:
        video_path (str): The path to the input video file.
    
    Returns:
        np.ndarray or None: Final 3D pose landmarks, or None if any stage fails.
    """
    print("--- Starting Full Pose Estimation Pipeline ---")
    
    # --- Stage 1: 2D Detection ---
    keypoints_2d = detect_2d_poses(video_path)
    if keypoints_2d is None:
        print("Pipeline halted: 2D detection failed.")
        return None
    
    # --- Stage 2: 3D Lifting ---
    keypoints_3d = lift_2d_to_3d(keypoints_2d)
    if keypoints_3d is None:
        print("Pipeline halted: 3D lifting failed.")
        return None
    
    print("--- Pose Estimation Pipeline Complete ---")
    return keypoints_3d
