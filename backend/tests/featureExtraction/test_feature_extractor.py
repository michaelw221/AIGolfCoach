import pytest
import numpy as np
from lib.python.featureExtraction.feature_extractor import SwingAnalysis

# Helper to create a dummy skeleton (17 joints, 3 coordinates)
def create_dummy_frame(hand_y=0.5, hand_x=0.0, shoulder_y=-0.5, shoulder_z=0.0, hip_y=0.0, hip_z=0.0):
    frame = np.zeros((17, 3))

    frame[13] = [hand_x, hand_y, 0] # LEFT_WRIST
    frame[16] = [hand_x, hand_y, 0] # RIGHT_WRIST
    
    frame[11] = [-0.1, shoulder_y, shoulder_z] # LEFT_SHOULDER
    frame[14] = [0.1, shoulder_y, shoulder_z]  # RIGHT_SHOULDER
    frame[4] = [-0.1, hip_y, hip_z]             # LEFT_HIP
    frame[1] = [0.1, hip_y, hip_z]              # RIGHT_HIP
    
    frame[12] = [-0.1, 0, shoulder_z] # LEFT_ELBOW
    
    frame[10] = [0.0, -0.8, shoulder_z] # HEAD
    return frame

@pytest.fixture
def perfect_swing_data():
    """Generates 100 frames of a 'perfect' swing."""
    frames = []
    for i in range(100):
        # Simulating a basic arc: Hands start low, go high, return to start
        progress = np.sin(np.pi * i / 100) # 0 to 1 back to 0
        h_y = 0.8 - (progress * 1.5) # Starts at 0.8, peaks at -0.7
        frames.append(create_dummy_frame(hand_y=h_y))
    return np.array(frames)

def test_swing_analysis_init_validation():
    """M1: Test that it fails if data is missing."""
    with pytest.raises(ValueError, match="Both DTL and FO landmark arrays are required"):
        SwingAnalysis(None, None)

def test_find_key_frames(perfect_swing_data):
    """M2: Test the sequential logic for finding Address, Top, and Impact."""
    analyzer = SwingAnalysis(perfect_swing_data, perfect_swing_data)
    keys = analyzer.key_frames
    
    assert "address" in keys
    assert "top" in keys
    assert "impact" in keys
    # Address should be at the very start
    assert keys["address"] < 10
    # Top should be around the middle
    assert 40 < keys["top"] < 60
    # Impact should be after the top
    assert keys["impact"] > keys["top"]

def test_diagnose_faults_early_extension():
    """M3: Test if the rule engine catches losing forward tilt (standing up)."""
    data = [create_dummy_frame() for _ in range(50)]
    data = np.array(data)
    
    # Frame 0 (Address): Tilted forward 45 degrees
    data[0] = create_dummy_frame(shoulder_y=-0.5, shoulder_z=-0.5, hip_y=0.0, hip_z=0.0) 
    
    # Frame 49 (Impact): Standing perfectly straight
    data[49] = create_dummy_frame(shoulder_y=-0.5, shoulder_z=0.0, hip_y=0.0, hip_z=0.0) 
    
    analyzer = SwingAnalysis(data, data)
    analyzer.key_frames = {'address': 0, 'top': 25, 'impact': 49}
    
    results = analyzer.run_full_analysis()
    fault_names = [f['name'] for f in results['diagnosed_faults']]
    
    assert "Early Extension (Loss of Posture)" in fault_names

def test_diagnose_faults_sway():
    """M4: Test if horizontal head movement triggers a fault."""
    data = [create_dummy_frame() for _ in range(50)]
    data = np.array(data)
    
    # Address
    data[0][10] = [0.0, -0.8, 0] # Head at center
    # Top: Head moved far to the right (Sway)
    data[25][10] = [0.2, -0.8, 0] # Moved 20cm (0.2m)
    
    analyzer = SwingAnalysis(data, data)
    analyzer.key_frames = {'address': 0, 'top': 25, 'impact': 49}
    
    results = analyzer.run_full_analysis()
    fault_names = [f['name'] for f in results['diagnosed_faults']]
    assert "Sway" in fault_names

def test_full_analysis_structure(perfect_swing_data):
    """M5: Verify the final JSON output format matches requirements."""
    analyzer = SwingAnalysis(perfect_swing_data, perfect_swing_data)
    output = analyzer.run_full_analysis()
    
    assert "metrics" in output
    assert "diagnosed_faults" in output
    assert "spine_angle_change_at_impact" in output["metrics"]
    assert isinstance(output["diagnosed_faults"], list)