import numpy as np
from .. import utils # Import from our new module

# Define keypoint indices provided by MediaPipe documentation
NOSE, LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_ELBOW, LEFT_WRIST, RIGHT_WRIST, LEFT_HIP, RIGHT_HIP = 0, 11, 12, 13, 15, 16, 23, 24

class SwingAnalysis:
    def __init__(self, landmarks_dtl, landmarks_fo):
        """
        Initializes the analysis object with landmark data from both views.
        """
        if landmarks_dtl is None or landmarks_fo is None:
            raise ValueError("Both DTL and FO landmark arrays are required.")
        
        self.landmarks_dtl = landmarks_dtl
        self.landmarks_fo = landmarks_fo
        
        self.key_frames = self._find_key_frames(self.landmarks_fo)

    def run_full_analysis(self):
        """
        Orchestrates the full analysis and returns the final results.
        """
        metrics = {}
        # Calculate view-specific metrics
        metrics.update(self._calculate_dtl_metrics())
        metrics.update(self._calculate_fo_metrics())

        faults = self._diagnose_faults(metrics)

        return {
            "key_frames": self.key_frames,
            "metrics": metrics,
            "diagnosed_faults": faults
        }

    def _find_key_frames(self, landmarks_array):
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
    
    def _calculate_dtl_metrics(self):
        """Calculates metrics that require the Down-the-Line view."""
        address_idx = self.key_frames['address']
        impact_idx = self.key_frames['impact']
        
        spine_angle_address = self._get_spine_angle(self.landmarks_dtl[address_idx])
        spine_angle_impact = self._get_spine_angle(self.landmarks_dtl[impact_idx])
        
        return {
            "spine_angle_change_at_impact": spine_angle_impact - spine_angle_address,
            "spine_angle_address": spine_angle_address,
            "spine_angle_impact": spine_angle_impact,
        }
    
    def _calculate_fo_metrics(self):
        """Calculates metrics that require the Face-On view."""
        address_idx = self.key_frames['address']
        top_idx = self.key_frames['top']
        impact_idx = self.key_frames['impact']
        
        head_sway = self._get_head_sway(self.landmarks_fo, address_idx, top_idx)
        backswing_len = self._get_backswing_length(self.landmarks_fo, top_idx)
        impact_arm_angle = self._get_lead_arm_angle_at_impact(self.landmarks_fo, impact_idx)
        
        return {
            "max_head_sway_cm": head_sway,
            "backswing_length_angle": backswing_len,
            "lead_arm_angle_impact": impact_arm_angle
        }
    
    def _diagnose_faults(self, metrics):
        """Runs the rule engine based on the calculated metrics."""
        faults = []
        if metrics.get("spine_angle_change_at_impact", 0) > 5:
            faults.append({
                "name": "Early Extension (Loss of Posture)",
                # Use single quotes for the key inside the f-string
                "detail": f"Your spine angle increased by {metrics.get('spine_angle_change_at_impact', 0):.1f} degrees at impact."
            })
            
        if metrics.get("max_head_sway_cm", 0) > 10:
            faults.append({
                "name": "Sway",
                # Use single quotes for the key inside the f-string
                "detail": f"Your head moved laterally by {metrics.get('max_head_sway_cm', 0):.1f} cm during the backswing."
            })
            
        if metrics.get("backswing_length_angle", 0) > 100:
            faults.append({
                "name": "Over-swinging",
                # Use single quotes for the key inside the f-string
                "detail": f"Your lead arm went to {metrics.get('backswing_length_angle', 0):.1f} degrees, which is past parallel."
            })
            
        if metrics.get("lead_arm_angle_impact", 180) < 160:
            faults.append({
                "name": "Bent Lead Arm at Impact (Chicken Wing)",
                # Use single quotes for the key inside the f-string
                "detail": f"Your lead arm was bent to {metrics.get('lead_arm_angle_impact', 180):.1f} degrees at impact."
            })
        return faults

    def _get_spine_angle(self, landmarks_frame):
        """
        Calculates the spine angle relative to a vertical line for a single frame.
        """
        hip_midpoint = utils.get_midpoint(landmarks_frame, LEFT_HIP, RIGHT_HIP)
        shoulder_midpoint = utils.get_midpoint(landmarks_frame, LEFT_SHOULDER, RIGHT_SHOULDER)
        torso_vector = shoulder_midpoint - hip_midpoint
        vertical_vector = np.array([0, -1, 0])
        return utils.calculate_angle_3d(torso_vector, vertical_vector)

    def _get_head_sway(self, landmarks_array, address_idx, top_idx):
        """
        Calculates the maximum lateral head movement (Sway) during the backswing.
        Assumes a Face-On (FO) view.
        A positive value indicates movement away from the target (for a right-handed golfer).
        """
        # Get the head's horizontal position at address
        head_x_address = landmarks_array[address_idx, NOSE, 0] # 0 corresponds to the X-axis
        
        # Get all head X positions during the backswing (from address to top)
        backswing_head_x = landmarks_array[address_idx:top_idx + 1, NOSE, 0]
        
        # Sway is the maximum displacement from the starting position
        sway_in_meters = np.max(np.abs(backswing_head_x - head_x_address))
        
        # Convert to centimeters for a more intuitive number
        return sway_in_meters * 100

    def _get_backswing_length(self, landmarks_array, top_idx):
        """
        Calculates the lead arm angle at the top of the swing to measure backswing length.
        Returns the angle in degrees relative to vertical.
        """
        top_frame_landmarks = landmarks_array[top_idx]
        
        # Define the lead arm vector (shoulder to wrist)
        lead_shoulder = top_frame_landmarks[LEFT_SHOULDER]
        lead_wrist = top_frame_landmarks[LEFT_WRIST]
        lead_arm_vector = lead_wrist - lead_shoulder
        
        # Define the vertical "down" vector
        vertical_vector = np.array([0, 1, 0])
        
        angle = utils.calculate_angle_3d(lead_arm_vector, vertical_vector)
        return angle

    def _get_lead_arm_angle_at_impact(self, landmarks_array, impact_idx):
        """
        Calculates the internal angle of the lead arm's elbow at impact.
        An angle close to 180 degrees is a straight arm. A smaller angle is a "chicken wing".
        """
        impact_frame_landmarks = landmarks_array[impact_idx]
        
        # Get the 3D coordinates of the three joints forming the elbow angle
        shoulder = impact_frame_landmarks[LEFT_SHOULDER]
        elbow = impact_frame_landmarks[LEFT_ELBOW]
        wrist = impact_frame_landmarks[LEFT_WRIST]
        
        # Create the two vectors for the angle calculation
        # Vector 1: Elbow to Shoulder
        # Vector 2: Elbow to Wrist
        v1 = shoulder - elbow
        v2 = wrist - elbow
        
        angle = utils.calculate_angle_3d(v1, v2)
        return angle