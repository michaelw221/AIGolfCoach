import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from lib.python.featureExtraction.feature_extractor import SwingAnalysis

# --- HELPER FUNCTIONS ---
def create_dummy_frame(hand_y=100.0, head_x=0.0, shoulder_width=40.0, hip_y=50.0):
    """
    Creates a safe 17-point dummy array matching the YOLOv8-Pose COCO indices.
    Y increases DOWNWARDS (pixels).
    """
    frame = np.zeros((17, 3))
    
    # NOSE (0) for Sway
    frame[0] =[head_x, 10.0, 0.9] 
    
    # SHOULDERS (5, 6)
    frame[5] =[100.0 - (shoulder_width/2), 20.0, 0.9]
    frame[6] =[100.0 + (shoulder_width/2), 20.0, 0.9]
    
    # HIPS (11, 12)
    frame[11] =[90.0, hip_y, 0.9]
    frame[12] =[110.0, hip_y, 0.9]
    
    # WRISTS (9, 10) - Used for Frame Detection and Hand Path
    frame[9] = [100.0, hand_y, 0.9]
    frame[10] = [100.0, hand_y, 0.9]
    
    # KNEES (13, 14) and ANKLES (15, 16) - Used for Knee Flex
    frame[13] =[90.0, hip_y + 30, 0.9]
    frame[15] =[90.0, hip_y + 60, 0.9]
    
    return frame

@pytest.fixture
def dummy_swing_data():
    """Generates 50 frames simulating a swing."""
    frames =[]
    for i in range(50):
        # Hands start low (Y=100), go high to top of swing (Y=20 at frame 25), return low (Y=100)
        hand_y = 100.0 - (np.sin(np.pi * i / 49) * 80.0)
        frames.append(create_dummy_frame(hand_y=hand_y))
    return np.array(frames)


# --- 1. TEST INITIALIZATION & DATA CLEANING ---
def test_swing_analysis_init_validation():
    """Verify initialization fails properly if missing required arrays."""
    with pytest.raises(ValueError, match="Both DTL and FO landmark arrays are required."):
        SwingAnalysis(None, None, None, "", "")

def test_clean_landmarks_interpolation():
    """Verify that missing joints [0,0] are mathematically bridged."""
    # Create 50 frames to bypass the 'video too short' safety checks
    data = np.array([create_dummy_frame(hand_y=100.0)] * 50)
    
    # Change surrounding frames to test interpolation
    data[20, 9] =[100.0, 100.0, 0.9] # Before missing
    data[21, 9] = [0.0, 0.0, 0.0]     # MISSING DATA (YOLO lost tracking)
    data[22, 9] =[100.0, 80.0, 0.9]  # After missing
    
    # Initialize with dummy data
    analyzer = SwingAnalysis(data, data, data, "", "")
    
    # Interpolation should calculate exactly halfway between Y=100 and Y=80 -> Y=90
    assert analyzer.landmarks_dtl_2d[21, 9, 1] == 90.0


# --- 2. TEST KEY FRAME DETECTION ---
def test_find_key_frames_dtl(dummy_swing_data):
    """Verify DTL logic (using hand Y-height) successfully isolates phases."""
    analyzer = SwingAnalysis(dummy_swing_data, dummy_swing_data, dummy_swing_data, "", "")
    
    kf_dtl = analyzer.key_frames_dtl
    assert kf_dtl['address'] == 5 # Hardcoded in your logic
    # Top of swing should be near the middle (frame 25) where hand_y is lowest
    assert 20 < kf_dtl['top'] < 30
    # Impact should be after the top, when hands return to address height
    assert kf_dtl['impact'] > kf_dtl['top']

def test_find_key_frames_fo(dummy_swing_data):
    """Verify FO logic (using velocity) finds frames safely without crashing."""
    analyzer = SwingAnalysis(dummy_swing_data, dummy_swing_data, dummy_swing_data, "", "")
    
    kf_fo = analyzer.key_frames_fo
    assert kf_fo['address'] == 5
    assert kf_fo['top'] > kf_fo['address']
    assert kf_fo['impact'] > kf_fo['top']


# --- 3. TEST FAULT DETECTION LOGIC ---
def test_diagnose_faults_sway():
    """Verify a lateral head movement triggers the Sway fault."""
    data = np.array([create_dummy_frame() for _ in range(50)])
    
    # Move the head (Nose index 0) by 50 pixels to the right at the top of the swing
    data[25, 0, 0] = 50.0 
    
    analyzer = SwingAnalysis(data, data, data, "", "")
    # Force the key frames so we control the exact test environment
    analyzer.key_frames_fo = {'address': 0, 'top': 25, 'impact': 49}
    
    metrics = analyzer._calculate_fo_metrics()
    faults = analyzer._diagnose_faults(metrics)["faults"]
    
    fault_names = [f['name'] for f in faults]
    assert "Sway" in fault_names
    
    # Verify severity logic works (Sway is > threshold)
    sway_fault = next(f for f in faults if f['name'] == 'Sway')
    assert sway_fault['severity'] > 1.0


def test_diagnose_faults_early_extension():
    """Verify a change in the torso vector triggers Early Extension."""
    data = np.array([create_dummy_frame() for _ in range(50)])
    
    # Frame 49 (Impact): Move the hips significantly to change the spine angle
    data[49, 11] =[90.0, 10.0, 0] # Left Hip
    data[49, 12] = [110.0, 10.0, 0] # Right Hip
    
    analyzer = SwingAnalysis(data, data, data, "", "")
    analyzer.key_frames_dtl = {'address': 0, 'top': 25, 'impact': 49}
    
    metrics = analyzer._calculate_dtl_metrics()
    faults = analyzer._diagnose_faults(metrics)["faults"]
    
    fault_names = [f['name'] for f in faults]
    assert "Early Extension (Loss of Posture)" in fault_names


# --- 4. TEST INTEGRATION & OUTPUT STRUCTURE ---
@patch('lib.python.featureExtraction.feature_extractor.cv2.VideoCapture')
def test_run_full_analysis_structure(mock_video_capture, dummy_swing_data):
    """Verify the orchestrator returns the exact JSON structure expected by React."""
    
    # Mock OpenCV to pretend the video file doesn't exist to test fallback handling
    # (Extract phase images will safely return None for the base64 strings)
    mock_video_capture.return_value.isOpened.return_value = False
    
    analyzer = SwingAnalysis(dummy_swing_data, dummy_swing_data, dummy_swing_data, "fake/dtl.mp4", "fake/fo.mp4")
    result = analyzer.run_full_analysis()
    
    # 1. Check Root Keys
    assert "key_frames" in result
    assert "metrics" in result
    assert "diagnosed_faults" in result
    assert "keypoints_3d" in result
    assert "debug_images" in result
    
    # 2. Check Faults Output Structure
    assert "faults" in result["diagnosed_faults"]
    assert "recommended_drills" in result["diagnosed_faults"]
    
    # 3. Check Image Output Structure
    assert "dtl" in result["debug_images"]
    assert "fo" in result["debug_images"]