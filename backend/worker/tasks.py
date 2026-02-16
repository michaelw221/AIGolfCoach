import os
import sys
import json
import numpy as np
from pathlib import Path

current_file = Path(__file__).resolve()
# Go up: tasks.py -> worker/ -> backend/ -> AIGolfCoach/ (Project Root)
project_root = current_file.parent.parent.parent
vp3d_path = project_root / 'VideoPose3dRepo' / 'VideoPose3D'

if str(vp3d_path) not in sys.path:
    sys.path.append(str(vp3d_path))

from .celery_config import celery_app
from lib.python.videoProcessing.pipeline import run_pose_estimation_pipeline
from lib.python.featureExtraction.feature_extractor import SwingAnalysis

# Helper for JSON serialization of NumPy types inside Celery
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return super(NpEncoder, self).default(obj)

@celery_app.task(bind=True)
def process_swing_video(self, dtl_video_path, fo_video_path):
    """
    Celery task to run the AI pipeline in the background.
    """
    try:
        # --- Part 1: Pose Estimation & Validation ---
        self.update_state(state='PROCESSING', meta={'status': 'Validating DTL video...'})
        result_dtl = run_pose_estimation_pipeline(dtl_video_path, "Down-the-Line")
        
        # Check if DTL pipeline returned an error dictionary
        if isinstance(result_dtl, dict) and "error" in result_dtl:
            _cleanup([dtl_video_path, fo_video_path])
            return result_dtl # Return the specific "Invalid Angle" error

        self.update_state(state='PROCESSING', meta={'status': 'Validating FO video...'})
        result_fo = run_pose_estimation_pipeline(fo_video_path, "Face-On")

        # Check if FO pipeline returned an error dictionary
        if isinstance(result_fo, dict) and "error" in result_fo:
            _cleanup([dtl_video_path, fo_video_path])
            return result_fo # Return the specific "Invalid Angle" error

        # --- Part 2: Biomechanical Analysis ---
        self.update_state(state='PROCESSING', meta={'status': 'Extracting Metrics...'})
        
        # If we reached here, results are definitely NumPy arrays
        swing_analyzer = SwingAnalysis(landmarks_dtl=result_dtl, landmarks_fo=result_fo)
        analysis_results = swing_analyzer.run_full_analysis()

        _cleanup([dtl_video_path, fo_video_path])
        
        # Return success payload
        return json.loads(json.dumps(analysis_results, cls=NpEncoder))

    except Exception as e:
        _cleanup([dtl_video_path, fo_video_path])
        return {"error": f"Technical Crash: {str(e)}"}

def _cleanup(paths):
    """Helper to remove temp files"""
    for path in paths:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"Worker: Cleaned up {path}")
            except Exception as e:
                print(f"Worker: Error deleting {path}: {e}")