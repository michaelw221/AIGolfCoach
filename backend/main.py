from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult
import os
import sys
import uuid
import shutil

# --- 1. SETUP PATHS FOR VIDEOPOSE3D (CRITICAL FIX) ---
# We need to do this BEFORE importing tasks, so lifter_3d can find 'common'
try:
    # Get directory of main.py (backend/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to project root (AIGolfCoach/)
    project_root = os.path.dirname(current_dir)
    # Define path to VideoPose3D
    vp3d_path = os.path.join(project_root, 'VideoPose3dRepo', 'VideoPose3D')
    
    if os.path.exists(vp3d_path):
        sys.path.append(vp3d_path)
    else:
        print(f"WARNING: VideoPose3D path not found at: {vp3d_path}")
except Exception as e:
    print(f"Error setting up paths: {e}")

# Import the Celery task and config
from worker.tasks import process_swing_video

app = FastAPI(title="AI Golf Coach API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure this directory exists and is accessible by both API and Worker
# For production, this should be S3. For local dev, a shared folder works.
TEMP_DIR = os.path.join(os.getcwd(), "temp_uploads")
os.makedirs(TEMP_DIR, exist_ok=True)

@app.post("/api/swings")
async def analyze_swing_endpoint(
    video_file_dtl: UploadFile = File(...),
    video_file_fo: UploadFile = File(...)
):
    """
    Asynchronous Endpoint: Uploads videos and enqueues a processing job.
    Returns a Task ID immediately.
    """
    unique_id = uuid.uuid4()
    
    # Save files with absolute paths so the worker can find them
    dtl_path = os.path.join(TEMP_DIR, f"{unique_id}_dtl_{video_file_dtl.filename}")
    fo_path = os.path.join(TEMP_DIR, f"{unique_id}_fo_{video_file_fo.filename}")

    try:
        # Save DTL
        with open(dtl_path, "wb") as buffer:
            shutil.copyfileobj(video_file_dtl.file, buffer)
        
        # Save FO
        with open(fo_path, "wb") as buffer:
            shutil.copyfileobj(video_file_fo.file, buffer)

        # --- Enqueue the Task ---
        # .delay() is the Celery command to send to Redis
        task = process_swing_video.delay(dtl_path, fo_path)

        return {
            "task_id": task.id,
            "status": "pending",
            "message": "Analysis started. Poll /api/swings/{task_id} for results."
        }

    except Exception as e:
        # Clean up if upload fails before queuing
        if os.path.exists(dtl_path): os.remove(dtl_path)
        if os.path.exists(fo_path): os.remove(fo_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/swings/{task_id}")
async def get_swing_result(task_id: str):
    """
    Check the status of a specific task.
    """
    task_result = AsyncResult(task_id)

    if task_result.state == 'PENDING':
        return {"task_id": task_id, "status": "pending"}
    
    elif task_result.state == 'PROCESSING':
        return {
            "task_id": task_id, 
            "status": "processing", 
            "info": task_result.info # Contains 'meta' we set in the worker
        }
    
    elif task_result.state == 'SUCCESS':
        return {
            "task_id": task_id,
            "status": "completed",
            "result": task_result.result
        }
    
    elif task_result.state == 'FAILURE':
        return {
            "task_id": task_id,
            "status": "failed",
            "error": str(task_result.result)
        }
    
    return {"task_id": task_id, "status": task_result.state}