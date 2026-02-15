import os
import json
import numpy as np
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
        # Update state to processing
        self.update_state(state='PROCESSING', meta={'status': 'Running Pose Estimation...'})

        # --- Part 1: Pose Estimation ---
        print(f"Worker: Processing DTL: {dtl_video_path}")
        landmarks_dtl = run_pose_estimation_pipeline(dtl_video_path)
        
        print(f"Worker: Processing FO: {fo_video_path}")
        landmarks_fo = run_pose_estimation_pipeline(fo_video_path)

        if landmarks_dtl is None or landmarks_fo is None:
            return {"error": "Pose estimation failed on one or both videos."}

        # Update state
        self.update_state(state='PROCESSING', meta={'status': 'Running Biomechanical Analysis...'})

        # --- Part 2: Biomechanical Analysis ---
        swing_analyzer = SwingAnalysis(landmarks_dtl=landmarks_dtl, landmarks_fo=landmarks_fo)
        analysis_results = swing_analyzer.run_full_analysis()

        # Clean up temp files now that we are done
        if os.path.exists(dtl_video_path): os.remove(dtl_video_path)
        if os.path.exists(fo_video_path): os.remove(fo_video_path)

        # Convert to JSON-compatible dict (handling NumPy types)
        # We dump to string and load back to dict to ensure purity for Celery result backend
        return json.loads(json.dumps(analysis_results, cls=NpEncoder))

    except Exception as e:
        # Cleanup on failure
        if os.path.exists(dtl_video_path): os.remove(dtl_video_path)
        if os.path.exists(fo_video_path): os.remove(fo_video_path)
        return {"error": str(e)}