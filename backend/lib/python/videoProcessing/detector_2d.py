# lib/python/videoProcessing/detector_2d.py
import cv2
import numpy as np
from ultralytics import YOLO

# Initialize the model once when the module is imported
POSE_MODEL = YOLO('yolov8s-pose.pt')

def detect_2d_poses(video_path: str):
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

        results = POSE_MODEL(frame, verbose=False)
        
        # Check if any results were returned and if the keypoints attribute exists
        if hasattr(results[0], 'keypoints') and results[0].keypoints.shape[0] > 0:
            # 1. Get the Keypoints object
            keypoints_object = results[0].keypoints
            
            # 2. Extract the numerical data. The .data attribute is a PyTorch tensor.
            #    Move it to the CPU and convert it to a NumPy array.
            keypoints_data_np = keypoints_object.data.cpu().numpy()
            
            # 3. Select the first person from the batch. The shape is now (17, 3).
            first_person_keypoints = keypoints_data_np[0]
            
            all_frames_keypoints.append(first_person_keypoints)
        else:
            # No person was detected. Append a placeholder of the correct shape.
            all_frames_keypoints.append(np.zeros((17, 3)))

    cap.release()
    
    if not all_frames_keypoints:
        return None, None

    return np.array(all_frames_keypoints), resolution