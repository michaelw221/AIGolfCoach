import numpy as np
from .. import utils # Import from our new module

# Define keypoint indices provided by MediaPipe documentation
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
LEFT_HIP, RIGHT_HIP = 23, 24
LEFT_WRIST, RIGHT_WRIST = 15, 16

def find_key_frames(landmarks_array):
    """
    Finds key frames using a robust, sequential, biomechanically-sound method.
    """
    hand_midpoints_3d = np.array([utils.get_midpoint(frame, LEFT_WRIST, RIGHT_WRIST) for frame in landmarks_array])
    hand_midpoints_y = hand_midpoints_3d[:, 1]

    # Step 1: Find Address
    address_idx = np.argmax(hand_midpoints_y[:30])
    address_hands_pos_3d = hand_midpoints_3d[address_idx]

    # Step 2: Find Backswing Trigger
    absolute_top_y = np.min(hand_midpoints_y)
    address_y = hand_midpoints_y[address_idx]
    swing_height = address_y - absolute_top_y
    trigger_y_level = address_y - (swing_height * 0.3)
    
    backswing_trigger_idx = address_idx
    for i in range(address_idx, len(hand_midpoints_y)):
        if hand_midpoints_y[i] < trigger_y_level:
            backswing_trigger_idx = i
            break
    
    # Step 3: Find Impact
    search_space = hand_midpoints_3d[backswing_trigger_idx:]
    distances_to_address = np.linalg.norm(search_space - address_hands_pos_3d, axis=1)
    impact_idx = backswing_trigger_idx + np.argmin(distances_to_address)

    # Step 4: Find Top of Swing
    swing_segment_y = hand_midpoints_y[address_idx : impact_idx + 1]
    top_idx = address_idx + np.argmin(swing_segment_y)

    return { 'address': address_idx, 'impact': impact_idx, 'top': top_idx }

def get_spine_angle(landmarks_frame):
    """
    Calculates the spine angle relative to a vertical line for a single frame.
    """
    hip_midpoint = utils.get_midpoint(landmarks_frame, LEFT_HIP, RIGHT_HIP)
    shoulder_midpoint = utils.get_midpoint(landmarks_frame, LEFT_SHOULDER, RIGHT_SHOULDER)
    torso_vector = shoulder_midpoint - hip_midpoint
    vertical_vector = np.array([0, -1, 0])
    return utils.calculate_angle_3d(torso_vector, vertical_vector)

def analyze_swing(landmarks_array):
    """
    Main function to run the full feature extraction on a landmark array.
    """
    # First, find the key moments in the swing
    key_frames = find_key_frames(landmarks_array)
    address_idx = key_frames['address']
    top_idx = key_frames['top']
    impact_idx = key_frames['impact']

    # Now, calculate the features at those moments
    spine_angle_address = get_spine_angle(landmarks_array[address_idx])
    spine_angle_top = get_spine_angle(landmarks_array[top_idx])
    spine_angle_impact = get_spine_angle(landmarks_array[impact_idx])
    
    # Calculate the diagnostic values
    change_at_impact = spine_angle_impact - spine_angle_address
    change_at_top = spine_angle_top - spine_angle_address
    
    # Return all the extracted data in a structured dictionary
    return {
        "key_frames": key_frames,
        "metrics": {
            "spine_angle_address": spine_angle_address,
            "spine_angle_top": spine_angle_top,
            "spine_angle_impact": spine_angle_impact,
            "spine_angle_change_at_impact": change_at_impact,
            "spine_angle_change_at_top": change_at_top
        }
    }

print("Feature extractor module is defined.")