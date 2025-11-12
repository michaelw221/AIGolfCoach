from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import json
import numpy as np

# Import the core components of our AI pipeline
from lib.videoProcessing.pose_estimator import extract_landmarks_from_video
from lib.featureExtraction.feature_extractor import SwingAnalysis

app = FastAPI(title="AI Golf Coach API")

# --- Add CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TEMP_DIR = "/tmp/golf_swings"
os.makedirs(TEMP_DIR, exist_ok=True)


# --- Helper Class for JSON Encoding (from your old script) ---
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return super(NpEncoder, self).default(obj)


@app.post("/api/swings")
async def analyze_swing_endpoint(
    video_file_dtl: UploadFile = File(..., description="The Down-the-Line (DTL) view of the swing."),
    video_file_fo: UploadFile = File(..., description="The Face-On (FO) view of the swing.")
):
    """
    Accepts DTL and FO video files, runs the full synchronous analysis pipeline,
    and returns the results as a JSON response.
    """

    # Use a unique filename to avoid conflicts if multiple users upload at once
    unique_id = uuid.uuid4()
    temp_video_path_dtl = os.path.join(TEMP_DIR, f"{unique_id}_dtl_{video_file_dtl.filename}")
    temp_video_path_fo = os.path.join(TEMP_DIR, f"{unique_id}_fo_{video_file_fo.filename}")
    
    temp_paths = [temp_video_path_dtl, temp_video_path_fo]
    
    try:
        with open(temp_video_path_dtl, "wb") as buffer:
            buffer.write(video_file_dtl.file.read())
        print(f"DTL video saved temporarily to: {temp_video_path_dtl}")

        with open(temp_video_path_fo, "wb") as buffer:
            buffer.write(video_file_fo.file.read())
        print(f"FO video saved temporarily to: {temp_video_path_fo}")

        landmarks_array_dtl = extract_landmarks_from_video(temp_video_path_dtl)
        landmarks_array_fo = extract_landmarks_from_video(temp_video_path_fo)

        
        if landmarks_array_dtl is None or landmarks_array_fo is None:
            raise HTTPException(status_code=400, detail="Could not detect a person in one or both of the videos.")

        swing_analyzer = SwingAnalysis(landmarks_dtl=landmarks_array_dtl, landmarks_fo=landmarks_array_fo)
        analysis_results = swing_analyzer.run_full_analysis()


        return json.loads(json.dumps(analysis_results, cls=NpEncoder))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Analysis Error: {e}")
    finally:
        for path in temp_paths:
            if os.path.exists(path):
                os.remove(path)
                print(f"Cleaned up temporary file: {path}")

@app.get("/")
def read_root():
    return {"message": "AI Golf Coach API is running."}