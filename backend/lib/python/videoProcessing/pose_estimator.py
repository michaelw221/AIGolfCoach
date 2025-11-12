import cv2
import mediapipe as mp
import numpy as np

def extract_landmarks_from_video(video_path):
    """
    Processes a video file to extract 3D pose landmarks using MediaPipe.

    Args:
        video_path (str): The path to the input video file.

    Returns:
        np.ndarray: A NumPy array of shape (num_frames, 33, 3) containing the
                    x, y, z coordinates of the 33 pose landmarks for each frame.
                    Returns None if no person is detected.
    """
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file at {video_path}")
        return None

    all_frames_landmarks = []
    print("-> Running Pose Estimation...")
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            break
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)
        
        if results.pose_world_landmarks:
            frame_lms = [{'x': lm.x, 'y': lm.y, 'z': lm.z} 
                         for lm in results.pose_world_landmarks.landmark]
            all_frames_landmarks.append(frame_lms)
    cap.release()

    if not all_frames_landmarks:
        print("Error: Could not detect a person in the video.")
        return None
    
    print("-> Pose Estimation complete.")
    # Convert list to NumPy array before returning
    return np.array([[[lm['x'], lm['y'], lm['z']] for lm in frame] for frame in all_frames_landmarks])