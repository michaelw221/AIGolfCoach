import cv2
from ultralytics import YOLO

def check_keypoints(video_path):
    # Load model
    model = YOLO('yolov8s-pose.pt')
    
    cap = cv2.VideoCapture(video_path)
    success, frame = cap.read()
    
    if success:
        # Run inference
        results = model(frame)
        
        # Get keypoints
        if results[0].keypoints.shape[0] > 0:
            # Get (x, y) coordinates for the first person
            kps = results[0].keypoints.xy[0].cpu().numpy()
            
            # Draw the Index Number on the image
            for i, (x, y) in enumerate(kps):
                if x > 0 and y > 0: # Only draw if detected
                    # Draw a circle
                    cv2.circle(frame, (int(x), int(y)), 5, (0, 255, 0), -1)
                    # Draw the Index Number
                    cv2.putText(frame, str(i), (int(x)+5, int(y)-5), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            # Show the image
            cv2.imshow("Keypoint Indices", frame)
            print("Press any key to close the window...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
            # Also print to terminal for reference
            print("\n--- Keypoint Coordinates ---")
            for i, (x, y) in enumerate(kps):
                print(f"Index {i}: ({x:.1f}, {y:.1f})")
        else:
            print("No person detected in the first frame.")
    else:
        print("Could not read video.")

if __name__ == "__main__":
    # Replace with your video path
    check_keypoints("lib/swingVids/tiger-swing-dtl.mp4")