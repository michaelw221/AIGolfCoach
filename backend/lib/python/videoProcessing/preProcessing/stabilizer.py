import cv2
import numpy as np

def stabilize_video(video_path, output_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    success, prev_frame = cap.read()
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    
    # Cumulative transformation matrix
    curr_transform = np.eye(2, 3, dtype=np.float32)
    
    out.write(prev_frame)

    while True:
        success, curr_frame = cap.read()
        if not success: break
        
        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
        
        # 1. Find features to track in the previous frame
        prev_pts = cv2.goodFeaturesToTrack(prev_gray, maxCorners=200, qualityLevel=0.01, minDistance=30)
        
        # 2. Track them in the current frame
        curr_pts, status, err = cv2.calcOpticalFlowPyrLK(prev_gray, curr_gray, prev_pts, None)
        
        # Filter only valid points
        idx = np.where(status == 1)[0]
        prev_pts = prev_pts[idx]
        curr_pts = curr_pts[idx]

        # 3. Estimate transformation (Translation + Rotation only)
        m, _ = cv2.estimateAffinePartial2D(prev_pts, curr_pts)
        
        if m is not None:
            # 4. Warp the frame to stabilize it
            # We invert the motion to keep the background still
            stabilized_frame = cv2.warpAffine(curr_frame, m, (w, h), flags=cv2.INTER_LINEAR + cv2.WARP_INVERSE_MAP)
            out.write(stabilized_frame)
            prev_gray = cv2.cvtColor(stabilized_frame, cv2.COLOR_BGR2GRAY)
        else:
            out.write(curr_frame)
            prev_gray = curr_gray

    cap.release()
    out.release()
    return output_path