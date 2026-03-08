import os
import sys
import json
import numpy as np
from pathlib import Path
from celery.signals import worker_process_init

# --- Path Setup ---
current_file = Path(__file__).resolve()
# Go up: tasks.py -> worker/ -> backend/ -> AIGolfCoach/ (Project Root)
project_root = current_file.parent.parent.parent
vp3d_path = project_root / 'VideoPose3dRepo' / 'VideoPose3D'

if str(vp3d_path) not in sys.path:
    sys.path.append(str(vp3d_path))

# --- Local Imports ---
# We need to add the 'backend' directory to sys.path to import from db
backend_dir = current_file.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

from .celery_config import celery_app
from lib.python.videoProcessing.pipeline import run_pose_estimation_pipeline
from lib.python.featureExtraction.feature_extractor import SwingAnalysis
from lib.python.videoProcessing.poseEstimation.detector_2d import get_model as load_yolo
from lib.python.videoProcessing.poseEstimation.lifter_3d import get_lifter_model as load_videopose3d

# Database Imports
from db.database import SessionLocal
import db.models as models

# Helper for JSON serialization of NumPy types
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, np.bool_): return bool(obj)
        return super(NpEncoder, self).default(obj)
    
@worker_process_init.connect
def setup_models(sender=None, **kwargs):
    """
    This runs once when the worker starts.
    It loads the heavy AI models into RAM/VRAM immediately.
    """
    print("\n[Worker Init] Warming up AI models...")
    
    try:
        # 1. Load YOLO
        print("  -> Loading YOLOv8...")
        load_yolo() 
        
        # 2. Load VideoPose3D
        print("  -> Loading VideoPose3D...")
        load_videopose3d()
        
        print("[Worker Init] Models loaded and ready! 🚀\n")
    except Exception as e:
        print(f"[Worker Init] Error loading models: {e}")

@celery_app.task(bind=True)
def process_swing_video(self, job_id, dtl_video_path, fo_video_path):
    """
    Celery task to run the AI pipeline and save results to PostgreSQL.
    """
    # Create a new database session for this task
    db = SessionLocal()
    
    try:
        # Retrieve the job from the database
        job = db.query(models.SwingJob).filter(models.SwingJob.id == job_id).first()
        if not job:
            print(f"Worker Error: Job {job_id} not found in database.")
            return

        # --- Part 1: Pose Estimation & Validation ---
        self.update_state(state='PROCESSING', meta={'status': 'Validating DTL video...'})
        result_dtl_2d, result_dtl_3d= run_pose_estimation_pipeline(dtl_video_path, "Down-the-Line")
        
        # Check if DTL pipeline returned an error dictionary (e.g. Invalid Angle)
        if isinstance(result_dtl_2d, dict) and "error" in result_dtl_2d:
            _handle_failure(db, job, result_dtl_2d["error"], [dtl_video_path, fo_video_path])
            return

        self.update_state(state='PROCESSING', meta={'status': 'Validating FO video...'})
        result_fo_2d, result_fo_3d = run_pose_estimation_pipeline(fo_video_path, "Face-On")

        # Check if FO pipeline returned an error dictionary
        if isinstance(result_fo_2d, dict) and "error" in result_fo_2d:
            _handle_failure(db, job, result_fo_2d["error"], [dtl_video_path, fo_video_path])
            return

        # --- Part 2: Biomechanical Analysis ---
        self.update_state(state='PROCESSING', meta={'status': 'Extracting Metrics...'})
        
        swing_analyzer = SwingAnalysis(landmarks_dtl=result_dtl_2d, landmarks_fo=result_fo_2d)
        analysis_results = swing_analyzer.run_full_analysis()

        # --- Part 3: Success & Database Update ---
        # We must serialize numpy data to standard JSON before saving to JSONB
        sanitized_results = json.loads(json.dumps(analysis_results, cls=NpEncoder))
        
        job.analysis_results = sanitized_results
        job.status = "complete"
        db.commit()
        
        print(f"Worker: Job {job_id} completed successfully.")
        _cleanup([dtl_video_path, fo_video_path])
        return sanitized_results

    except Exception as e:
        # Catch any unexpected crashes (technical errors)
        print(f"Worker Exception: {str(e)}")
        if db and job:
            _handle_failure(db, job, f"Technical Failure: {str(e)}", [dtl_video_path, fo_video_path])
        else:
            _cleanup([dtl_video_path, fo_video_path])
            
    finally:
        # Always close the DB session
        db.close()

def _handle_failure(db, job, error_msg, paths):
    """Update DB status to failed and clean up files"""
    job.status = "failed"
    job.error_message = error_msg
    db.commit()
    _cleanup(paths)

def _cleanup(paths):
    """Helper to remove temp files"""
    for path in paths:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"Worker: Cleaned up {path}")
            except Exception as e:
                print(f"Worker: Error deleting {path}: {e}")