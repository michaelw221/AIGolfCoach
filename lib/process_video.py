import cv2
import mediapipe as mp
import json
import argparse

# Setup argument parser
parser = argparse.ArgumentParser(description='Process a video to extract pose landmarks.')
parser.add_argument('video_path', type=str, help='Path to the input video file.')
args = parser.parse_args()

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)

# Open the video file
cap = cv2.VideoCapture(args.video_path)
if not cap.isOpened():
    print(f"Error: Could not open video file at {args.video_path}")
    exit()

all_frames_landmarks = [] # This list will hold the landmark data for the entire video

while cap.isOpened():
    success, image = cap.read()
    if not success:
        break # End of video

    # 1. Convert the image color from BGR to RGB (MediaPipe expects RGB)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # 2. Process the image and get the pose landmarks
    results = pose.process(image_rgb)
    
    # 3. Extract and store the landmarks for the current frame
    if results.pose_world_landmarks: # Use world_landmarks for 3D-like data
        current_frame_landmarks = []
        for landmark in results.pose_world_landmarks.landmark:
            current_frame_landmarks.append({
                'x': landmark.x,
                'y': landmark.y,
                'z': landmark.z,
                'visibility': landmark.visibility
            })
        all_frames_landmarks.append(current_frame_landmarks)

# Clean up resources
cap.release()

# Save the collected data to a JSON file
output_path = 'swing_landmarks.json'
with open(output_path, 'w') as f:
    json.dump(all_frames_landmarks, f, indent=4)

print(f"Successfully processed video. Landmark data saved to {output_path}")