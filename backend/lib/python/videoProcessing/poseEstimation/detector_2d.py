# lib/python/videoProcessing/detector_2d.py
import cv2
import numpy as np
from ultralytics import YOLO

_POSE_MODEL = None  # Global variable to hold the model

def get_model():
    """Lazy loader for the YOLO model"""
    global _POSE_MODEL
    if _POSE_MODEL is None:
        print("Worker: Loading YOLOv8-Pose model...")
        _POSE_MODEL = YOLO('yolov8s-pose.pt')
    return _POSE_MODEL

def validate_video_file(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return False, "Could not open video file."
    
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    cap.release()
    
    if frame_count < 30: # If less than 0.5 seconds of video
        return False, f"Video is too short or corrupted. Frames detected: {frame_count}"
        
    return True, f"Valid video, {frame_count} frames found."

def detect_2d_poses(video_path: str):
    model = _POSE_MODEL

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file at {video_path}")
        return None, None

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    resolution = (width, height)
    
    all_frames_keypoints = []
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        results = model(frame, verbose=False)
        
        # Check if keypoints AND bounding boxes exist
        if hasattr(results[0], 'keypoints') and results[0].keypoints is not None and len(results[0].keypoints.data) > 0:
            
            # 1. Get all keypoints and all bounding boxes for everyone in the frame
            kps_data = results[0].keypoints.data.cpu().numpy()  # Shape: (num_people, 17, 3)
            boxes_data = results[0].boxes.xywh.cpu().numpy()    # Shape: (num_people, 4) -> [x, y, width, height]
            
            # 2. Calculate the area (width * height) of every person detected
            areas = boxes_data[:, 2] * boxes_data[:, 3]
            
            # 3. Find the index of the person with the largest area (The Golfer)
            largest_person_idx = np.argmax(areas)
            
            # 4. Extract ONLY the golfer's keypoints
            golfer_keypoints = kps_data[largest_person_idx]
            
            all_frames_keypoints.append(golfer_keypoints)
        else:
            # No one detected
            all_frames_keypoints.append(np.zeros((17, 3)))

    cap.release()
    
    if not all_frames_keypoints:
        return None, None

    return np.array(all_frames_keypoints), resolution