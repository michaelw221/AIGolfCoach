import numpy as np
import cv2
import base64
from .. import utils # Import from our new module

# Define keypoint indices provided by YoloV8 documentation
HIP_ROOT = 0
RIGHT_HIP = 1
RIGHT_KNEE = 2
RIGHT_FOOT = 3
LEFT_HIP = 4
LEFT_KNEE = 5
LEFT_FOOT = 6
SPINE = 7
THORAX = 8
NECK = 9
HEAD = 10
LEFT_SHOULDER = 11
LEFT_ELBOW = 12
LEFT_WRIST = 13
RIGHT_SHOULDER = 14
RIGHT_ELBOW = 15
RIGHT_WRIST = 16

class SwingAnalysis:
    def __init__(self, landmarks_dtl, landmarks_fo, dtl_video_path, fo_video_path):
        """
        Initializes the analysis object with landmark data from both views.
        """
        if landmarks_dtl is None or landmarks_fo is None:
            raise ValueError("Both DTL and FO landmark arrays are required.")
        
        self.landmarks_dtl = self._clean_landmarks(landmarks_dtl)
        self.landmarks_fo = self._clean_landmarks(landmarks_fo)
        self.dtl_path = dtl_video_path
        self.fo_path = fo_video_path
        
        self.key_frames_dtl = self._find_key_frames(self.landmarks_dtl)
        self.key_frames_fo = self._find_key_frames(self.landmarks_fo)

    def _get_frame_as_base64(self, video_path, frame_idx, landmarks):
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        success, frame = cap.read()
        cap.release()
        if success:
            annotated = utils.draw_skeleton(frame, landmarks[frame_idx, :, :2])
            _, buffer = cv2.imencode('.jpg', annotated)
            return base64.b64encode(buffer).decode('utf-8')
        return None

    def run_full_analysis(self):
        """
        Orchestrates the full analysis and returns the final results.
        """
        metrics = {}
        # Calculate view-specific metrics
        metrics.update(self._calculate_dtl_metrics())
        metrics.update(self._calculate_fo_metrics())

        faults = self._diagnose_faults(metrics)

        debug_images = {"dtl": {}, "fo": {}}
        
        # Capture DTL frames
        for phase in ['address', 'top', 'impact']:
            debug_images['dtl'][phase] = self._get_frame_as_base64(self.dtl_path, self.key_frames_dtl[phase], self.landmarks_dtl)
        
        # Capture FO frames
        for phase in ['address', 'top', 'impact']:
            debug_images['fo'][phase] = self._get_frame_as_base64(self.fo_path, self.key_frames_fo[phase], self.landmarks_fo)

        return {
            "key_frames": {"dtl": self.key_frames_dtl, "fo": self.key_frames_fo},
            "metrics": metrics,
            "diagnosed_faults": faults,
            "debug_images": debug_images
        }

    def _find_key_frames(self, landmarks_array):
        """
        Robust 2D Key Frame Detection.
        Y increases DOWNWARDS (Bottom of screen is high Y).
        """
        hand_midpoints = np.array([utils.get_midpoint(frame[:, :2], LEFT_WRIST, RIGHT_WRIST) for frame in landmarks_array])
        hand_y = hand_midpoints[:, 1]
        num_total_frames = len(hand_y)

        # 1. Address: Max Y (lowest point of hands) in first 60 frames
        search_limit = min(60, num_total_frames)
        address_idx = np.argmax(hand_y[:search_limit])

        # 2. Top of Swing: Min Y (highest point of hands) 
        # Search from address to the end
        top_idx = address_idx + np.argmin(hand_y[address_idx:])

        # 3. Impact: The lowest point of hands AFTER the Top of Swing
        # We search from the top_idx + a buffer, but stop well before the end 
        # to ensure we don't pick the finish pose
        impact_search_start = top_idx + 5
        impact_search_end = int(top_idx + (num_total_frames - top_idx) * 0.7) # Look only in the next 70% of the remaining video
        
        # Impact is the LOWEST hand position (Max Y) in that downswing window
        impact_idx = impact_search_start + np.argmax(hand_y[impact_search_start:impact_search_end])

        print(f"--- 2D Key Frame Detection ---")
        print(f"Detected -> Address: {address_idx}, Top: {top_idx}, Impact: {impact_idx}")
        
        return { 
            'address': int(address_idx), 
            'top': int(top_idx), 
            'impact': int(impact_idx) 
        }

    def _calculate_dtl_metrics(self):
        """Calculates metrics using DTL key frames."""
        kf = self.key_frames_dtl
        
        spine_addr = self._get_spine_angle(self.landmarks_dtl[kf['address']])
        spine_impact = self._get_spine_angle(self.landmarks_dtl[kf['impact']])
        knee_addr = self._get_knee_angle(self.landmarks_dtl[kf['address']], LEFT_HIP, LEFT_KNEE, LEFT_FOOT)
        knee_impact = self._get_knee_angle(self.landmarks_dtl[kf['impact']], LEFT_HIP, LEFT_KNEE, LEFT_FOOT)
        hand_path = self._get_hand_path_angle(self.landmarks_dtl, kf['address'], kf['top'], kf['impact'])

        return {
            "spine_angle_change_at_impact": spine_addr - spine_impact,
            "knee_flex_change": knee_impact - knee_addr,
            "initial_hand_path_angle": hand_path
        }
    
    def _calculate_fo_metrics(self):
        """Calculates metrics using FO key frames."""
        kf = self.key_frames_fo
        
        head_sway = self._get_head_sway(self.landmarks_fo, kf['address'], kf['top'])
        backswing_len = self._get_backswing_length(self.landmarks_fo, kf['top'])
        impact_arm_angle = self._get_lead_arm_angle_at_impact(self.landmarks_fo, kf['impact'])
        hip_slide = self._get_hip_slide(self.landmarks_fo, kf['address'], kf['impact'])
        x_factor = self._get_x_factor(self.landmarks_fo, kf['address'], kf['top'])
        
        return {
            "max_head_sway_cm": head_sway,
            "backswing_length_angle": backswing_len,
            "lead_arm_angle_impact": impact_arm_angle,
            "max_hip_slide_cm": hip_slide,
            "x_factor_angle": x_factor
        }

    def _diagnose_faults(self, metrics):
        """Runs the rule engine based on the calculated metrics."""
        faults = []
        if metrics.get("spine_angle_change_at_impact", 0) > 5:
            faults.append({
                "name": "Early Extension (Loss of Posture)",
                "detail": f"Your spine angle increased by {metrics.get('spine_angle_change_at_impact', 0):.1f} degrees at impact."
            })
            
        if metrics.get("max_head_sway_cm", 0) > 10:
            faults.append({
                "name": "Sway",
                "detail": f"Your head moved laterally by {metrics.get('max_head_sway_cm', 0):.1f} cm during the backswing."
            })
            
        if metrics.get("backswing_length_angle", 0) > 100:
            faults.append({
                "name": "Over-swinging",
                "detail": f"Your lead arm went to {metrics.get('backswing_length_angle', 0):.1f} degrees, which is past parallel."
            })
            
        if metrics.get("lead_arm_angle_impact", 180) < 160:
            faults.append({
                "name": "Bent Lead Arm at Impact (Chicken Wing)",
                "detail": f"Your lead arm was bent to {metrics.get('lead_arm_angle_impact', 180):.1f} degrees at impact."
            })

        if metrics.get("max_hip_slide_cm", 0) > 15:
            faults.append({
                "name": "Excessive Slide", 
                "detail": "Hips moved too far toward the target, preventing rotation."
            })

        if metrics.get("x_factor_angle", 0) < 25:
            faults.append({
                "name": "Poor Separation", 
                "detail": "Hips and shoulders turned together. Work on X-Factor."
            })

        if metrics.get("knee_flex_change", 0) > 20:
            faults.append({
                "name": "Loss of Knee Flex", 
                "detail": "Your lead leg straightened too much, causing you to stand up."
            })

        hand_angle = metrics.get("initial_hand_path_angle", 0)
        if hand_angle > 40:
            faults.append({
                "name": "Over the Top", 
                "detail": f"Your hands moved outward toward the ball at a {hand_angle:.1f}° angle instead of dropping straight down."
            })
            
        return faults

    def _get_spine_angle(self, landmarks_frame):
        # 1. Get vectors
        hip = utils.get_midpoint(landmarks_frame[:, :2], LEFT_HIP, RIGHT_HIP)
        neck = landmarks_frame[NECK, :2]
        spine_vector = neck - hip
        
        # 2. Get the angle relative to the vertical line
        angle_rad = np.arctan2(spine_vector[0], -spine_vector[1])
        angle_deg = np.degrees(angle_rad)
        
        return float(angle_deg)

    def _get_backswing_length(self, landmarks_array, top_idx):
        top_frame = landmarks_array[top_idx]
        
        lead_shoulder = top_frame[LEFT_SHOULDER, :2]
        lead_wrist = top_frame[LEFT_WRIST, :2]
        
        lead_arm_vector = lead_wrist - lead_shoulder
        # Vertical down is [0, 1] in 2D space
        vertical_vector = np.array([0, 1])
        
        return utils.calculate_angle_2d(lead_arm_vector, vertical_vector)

    def _get_lead_arm_angle_at_impact(self, landmarks_array, impact_idx):
        impact_frame = landmarks_array[impact_idx]
        
        shoulder = impact_frame[LEFT_SHOULDER, :2]
        elbow = impact_frame[LEFT_ELBOW, :2]
        wrist = impact_frame[LEFT_WRIST, :2]
        
        v1 = shoulder - elbow
        v2 = wrist - elbow
        return utils.calculate_angle_2d(v1, v2)

    def _get_knee_angle(self, frame, hip_idx, knee_idx, foot_idx):
        v1 = frame[hip_idx, :2] - frame[knee_idx, :2]
        v2 = frame[foot_idx, :2] - frame[knee_idx, :2]
        return utils.calculate_angle_2d(v1, v2)

    def _get_head_sway(self, landmarks_array, address_idx, top_idx):
        head_x_address = landmarks_array[address_idx, HEAD, 0]
        backswing_head_x = landmarks_array[address_idx:top_idx + 1, HEAD, 0]
        
        pixel_sway = np.max(np.abs(backswing_head_x - head_x_address))
        
        # Use the safe reference width
        pixel_shldr_width = self._get_reference_shoulder_width(landmarks_array, address_idx)
        return float((pixel_sway / pixel_shldr_width) * 40)

    def _get_hip_slide(self, landmarks, addr_idx, impact_idx):
        addr_hip_x = (landmarks[addr_idx, LEFT_HIP, 0] + landmarks[addr_idx, RIGHT_HIP, 0]) / 2
        hips_x_seq = landmarks[addr_idx:impact_idx+1, [LEFT_HIP, RIGHT_HIP], 0].mean(axis=1)
        
        pixel_slide = np.max(addr_hip_x - hips_x_seq) 
        if pixel_slide < 0: pixel_slide = 0 
        
        # Use the safe reference width
        pixel_shldr_width = self._get_reference_shoulder_width(landmarks, addr_idx)
        return float((pixel_slide / pixel_shldr_width) * 40)

    def _get_x_factor(self, landmarks_array, addr_idx, top_idx):
        """
        2D X-Factor Proxy: Measures the foreshortening of shoulder width vs hip width.
        At address, width is MAX. At 90-degree turn, width is MIN.
        """
        addr_frame = landmarks_array[addr_idx]
        top_frame = landmarks_array[top_idx]

        # Max projected widths (at address)
        shldr_w_addr = np.linalg.norm(addr_frame[LEFT_SHOULDER, :2] - addr_frame[RIGHT_SHOULDER, :2])
        hip_w_addr = np.linalg.norm(addr_frame[LEFT_HIP, :2] - addr_frame[RIGHT_HIP, :2])

        # Current projected widths (at top)
        shldr_w_top = np.linalg.norm(top_frame[LEFT_SHOULDER, :2] - top_frame[RIGHT_SHOULDER, :2])
        hip_w_top = np.linalg.norm(top_frame[LEFT_HIP, :2] - top_frame[RIGHT_HIP, :2])

        if shldr_w_addr < 10 or hip_w_addr < 10: return 0.0

        # Ratio of top / address (Clipped to prevent math domain errors)
        shldr_ratio = np.clip(shldr_w_top / shldr_w_addr, 0.0, 1.0)
        hip_ratio = np.clip(hip_w_top / hip_w_addr, 0.0, 1.0)

        # Arccos converts the ratio back into an estimated rotation angle
        shldr_turn = np.degrees(np.arccos(shldr_ratio))
        hip_turn = np.degrees(np.arccos(hip_ratio))

        return float(abs(shldr_turn - hip_turn))

    def _get_hand_path_angle(self, landmarks_array, addr_idx, top_idx, impact_idx):
        """
        Calculates the angle of the hands' initial downward movement from the top.
        0 degrees = dropping straight down into the slot.
        90 degrees = throwing hands straight out towards the ball.
        """
        # 1. Determine Facing Direction (Accommodating Left & Right Handed)
        # At Address, hands are closer to the ball than the hips.
        addr_frame = landmarks_array[addr_idx]
        addr_hands_x = utils.get_midpoint(addr_frame[:, :2], LEFT_WRIST, RIGHT_WRIST)[0]
        addr_hips_x = utils.get_midpoint(addr_frame[:, :2], LEFT_HIP, RIGHT_HIP)[0]
        
        # If hands X > hips X, they face Right (+1). If hands X < hips X, they face Left (-1).
        facing_direction = 1 if addr_hands_x > addr_hips_x else -1
        
        # 2. Define the measurement window (e.g., 5 frames into the downswing)
        # We don't want to measure all the way to impact, only the initial transition!
        downswing_idx = min(top_idx + 5, impact_idx)
        if downswing_idx <= top_idx: 
            return 0.0 # Safety check if video is too short
            
        # 3. Get Hand Midpoints
        top_hands = utils.get_midpoint(landmarks_array[top_idx, :, :2], LEFT_WRIST, RIGHT_WRIST)
        down_hands = utils.get_midpoint(landmarks_array[downswing_idx, :, :2], LEFT_WRIST, RIGHT_WRIST)
        
        # 4. Calculate Vector Deltas
        dx = down_hands[0] - top_hands[0]
        dy = down_hands[1] - top_hands[1] # In 2D, +Y is DOWNwards on the screen
        
        # Normalize the horizontal movement so "outward" is always a positive number
        # regardless of whether they face left or right.
        dx_outward = dx * facing_direction
        
        # If dy is negative, YOLO glitched and thought hands went UP to the sky. 
        if dy <= 0:
            return 0.0 
            
        # 5. Calculate Angle from Vertical
        # We use arctan2(Opposite, Adjacent) -> arctan2(dx, dy)
        angle_rad = np.arctan2(dx_outward, dy)
        angle_deg = np.degrees(angle_rad)
        
        return float(angle_deg)

    def _get_reference_shoulder_width(self, landmarks_array, address_idx):
        """Finds a reliable shoulder width near the address frame."""
        for offset in range(0, 15): # Check up to 15 frames ahead
            idx = min(address_idx + offset, len(landmarks_array) - 1)
            shldr_l = landmarks_array[idx, LEFT_SHOULDER, :2]
            shldr_r = landmarks_array[idx, RIGHT_SHOULDER, :2]
            width = np.linalg.norm(shldr_l - shldr_r)
            if width > 20: # Valid width found
                return width
        return 40.0

    def _clean_landmarks(self, landmarks_array):
        """
        Fixes 'lost tracking' frames (where YOLO outputs [0, 0]) by 
        interpolating the position from surrounding valid frames.
        """
        cleaned = np.copy(landmarks_array)
        frames, joints, dims = cleaned.shape
        
        for j in range(joints):
            # A joint is "missing" if both X and Y are exactly 0
            missing = (cleaned[:, j, 0] == 0) & (cleaned[:, j, 1] == 0)
            
            # If the joint is missing in SOME frames, but not ALL frames
            if np.any(missing) and not np.all(missing):
                valid_idx = np.where(~missing)[0]
                missing_idx = np.where(missing)[0]
                
                # Mathematically fill in the missing X and Y coordinates
                # using numpy's linear interpolation (np.interp)
                cleaned[missing_idx, j, 0] = np.interp(missing_idx, valid_idx, cleaned[valid_idx, j, 0])
                cleaned[missing_idx, j, 1] = np.interp(missing_idx, valid_idx, cleaned[valid_idx, j, 1])
                
        return cleaned