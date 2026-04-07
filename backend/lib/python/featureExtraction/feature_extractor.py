import numpy as np
import cv2
import base64
import os
from .. import utils # Import from our new module
from .drill_db import DRILL_DATA

# Define keypoint indices provided by YoloV8 documentation
NOSE = 0
LEFT_EYE = 1
RIGHT_EYE = 2
LEFT_EAR = 3
RIGHT_EAR = 4
LEFT_SHOULDER = 5
RIGHT_SHOULDER = 6
LEFT_ELBOW = 7
RIGHT_ELBOW = 8
LEFT_WRIST = 9
RIGHT_WRIST = 10
LEFT_HIP = 11
RIGHT_HIP = 12
LEFT_KNEE = 13
RIGHT_KNEE = 14
LEFT_ANKLE = 15
RIGHT_ANKLE = 16

class SwingAnalysis:
    def __init__(self, landmarks_dtl_2d, landmarks_fo_2d, landmarks_dtl_3d, dtl_video_path, fo_video_path):
        """
        Initializes the analysis object with landmark data from both views.
        """
        if landmarks_dtl_2d is None or landmarks_fo_2d is None:
            raise ValueError("Both DTL and FO landmark arrays are required.")
        
        self.landmarks_dtl_2d = self._clean_landmarks(landmarks_dtl_2d)
        self.landmarks_fo_2d = self._clean_landmarks(landmarks_fo_2d)
        self.landmarks_dtl_3d = self._clean_landmarks(landmarks_dtl_3d)
        self.dtl_path = dtl_video_path
        self.fo_path = fo_video_path
        
        self.key_frames_dtl = self._find_key_frames(self.landmarks_dtl_2d, "DTL")
        self.key_frames_fo = self._find_key_frames(self.landmarks_fo_2d, "FO")

    def _extract_phase_images(self, video_path, key_frames_dict, landmarks):
        """
        Reads the video ONCE sequentially to extract the 3 key frames perfectly.
        This bypasses the OpenCV frame-skipping bugs on Windows.
        """
        if not video_path or not os.path.exists(video_path):
            return {"address": None, "top": None, "impact": None}

        # Map the frame index to its phase name (e.g., {58: 'address', 140: 'top'})
        targets = {
            key_frames_dict['address']: 'address',
            key_frames_dict['top']: 'top',
            key_frames_dict['impact']: 'impact'
        }
        max_frame_needed = max(targets.keys())
        
        extracted_images = {}
        cap = cv2.VideoCapture(video_path)
        
        current_frame = 0
        while cap.isOpened() and current_frame <= max_frame_needed:
            success, frame = cap.read()
            if not success:
                break
                
            # If the current frame is one of our key frames, draw the skeleton and save it
            if current_frame in targets:
                phase_name = targets[current_frame]
                annotated = utils.draw_skeleton(frame, landmarks[current_frame])
                
                _, buffer = cv2.imencode('.jpg', annotated)
                b64_str = base64.b64encode(buffer).decode('utf-8')
                extracted_images[phase_name] = b64_str
                
            current_frame += 1
            
        cap.release()

        for phase in ['address', 'top', 'impact']:
            if phase not in extracted_images:
                extracted_images[phase] = None
                
        return extracted_images

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
        
        debug_images = {
            "dtl": self._extract_phase_images(self.dtl_path, self.key_frames_dtl, self.landmarks_dtl_2d),
            "fo": self._extract_phase_images(self.fo_path, self.key_frames_fo, self.landmarks_fo_2d)
        }

        return {
            "key_frames": {"dtl": self.key_frames_dtl, "fo": self.key_frames_fo},
            "metrics": metrics,
            "diagnosed_faults": faults,
            "keypoints_3d": self.landmarks_dtl_3d.tolist(),
            "debug_images": debug_images
        }

    def _find_key_frames(self, landmarks_array, view_type):
        num_total_frames = len(landmarks_array)
        hand_midpoints = np.array([utils.get_midpoint(frame[:, :2], LEFT_WRIST, RIGHT_WRIST) for frame in landmarks_array])
        hand_y = hand_midpoints[:, 1]

        address_idx = 5
        # Top is the absolute highest point
        top_idx = 10 + np.argmin(hand_y[10:int(num_total_frames*0.7)])
        # Impact is when hands return to address Y-level in the downswing
        search_space = np.abs(hand_y[top_idx+5:int(num_total_frames*0.9)] - hand_y[address_idx])
        impact_idx = top_idx + 5 + np.argmin(search_space)

        return { 
            'address': int(address_idx), 
            'top': int(top_idx), 
            'impact': int(impact_idx) 
        }

    def _calculate_dtl_metrics(self):
        """Calculates metrics using DTL key frames."""
        kf = self.key_frames_dtl
        
        spine_addr = self._get_spine_angle(self.landmarks_dtl_2d[kf['address']])
        spine_impact = self._get_spine_angle(self.landmarks_dtl_2d[kf['impact']])
        knee_addr = self._get_knee_angle(self.landmarks_dtl_2d[kf['address']], LEFT_HIP, LEFT_KNEE, LEFT_ANKLE)
        knee_impact = self._get_knee_angle(self.landmarks_dtl_2d[kf['impact']], LEFT_HIP, LEFT_KNEE, LEFT_ANKLE)
        hand_path = self._get_hand_path_angle(self.landmarks_dtl_2d, kf['address'], kf['top'], kf['impact'])

        return {
            "spine_angle_change_at_impact": spine_addr - spine_impact,
            "knee_flex_change": knee_impact - knee_addr,
            "initial_hand_path_angle": hand_path
        }
    
    def _calculate_fo_metrics(self):
        """Calculates metrics using FO key frames."""
        kf = self.key_frames_fo
        
        head_sway = self._get_head_sway(self.landmarks_fo_2d, kf['address'], kf['top'])
        backswing_len = self._get_backswing_length(self.landmarks_fo_2d, kf['top'])
        impact_arm_angle = self._get_lead_arm_angle_at_impact(self.landmarks_fo_2d, kf['impact'])
        hip_slide = self._get_hip_slide(self.landmarks_fo_2d, kf['address'], kf['impact'])
        x_factor = self._get_x_factor(self.landmarks_fo_2d, kf['address'], kf['top'])
        
        return {
            "max_head_sway_cm": head_sway,
            "backswing_length_angle": backswing_len,
            "lead_arm_angle_impact": impact_arm_angle,
            "max_hip_slide_cm": hip_slide,
            "x_factor_angle": x_factor
        }

    def _diagnose_faults(self, metrics):
        """Runs the rule engine, calculates severity, and selects exactly 3 drills."""
        detected_faults = []

        thresholds = {
            "sway": 25.37, 
            "spine": 5.06, 
            "ott": 43.18, # Using handPath threshold for OTT
            "overSwing": 143.14, 
            "leadArm": 160, 
            "slide": 13.18, 
            "xFactor": 9.12, 
            "knee": 5.06
        }
        
        # 1. Early Extension
        spine_val = abs(metrics.get("spine_angle_change_at_impact", 0))
        if spine_val > thresholds["spine"]:
            detected_faults.append({
                "name": "Early Extension (Loss of Posture)",
                "severity": spine_val / thresholds["spine"],
                "detail": f"Spine angle changed by {spine_val:.1f}°."
            })
            
        # 2. Sway
        sway_val = metrics.get("max_head_sway_cm", 0)
        if sway_val > thresholds["sway"]:
            detected_faults.append({
                "name": "Sway", 
                "severity": sway_val / thresholds["sway"], 
                "detail": f"Head moved {sway_val:.1f}cm laterally."
            })
            
        # 3. Over-swinging
        backswing_angle = metrics.get("backswing_length_angle", 0)
        if backswing_angle > thresholds["overSwing"]:
            detected_faults.append({
                "name": "Over-swinging",
                "severity": backswing_angle / thresholds["overSwing"],
                "detail": f"Backswing reached {backswing_angle:.1f}° (past parallel)."
            })
            
        # 4. Chicken Wing (Lower is worse)
        arm_angle = metrics.get("lead_arm_angle_impact", 180)
        if arm_angle < thresholds["leadArm"]:
            # Severity = Threshold / Value (e.g., 160/140 = 1.14 severity)
            detected_faults.append({
                "name": "Bent Lead Arm at Impact (Chicken Wing)",
                "severity": thresholds["leadArm"] / max(arm_angle, 1), 
                "detail": f"Lead arm was bent to {arm_angle:.1f}° at impact."
            })

        # 5. Excessive Slide
        slide_val = metrics.get("max_hip_slide_cm", 0)
        if slide_val > thresholds["slide"]:
            detected_faults.append({
                "name": "Excessive Slide", 
                "severity": slide_val / thresholds["slide"],
                "detail": f"Hips slid {slide_val:.1f}cm toward target."
            })

        # 6. Poor Separation (Lower is worse)
        x_factor = metrics.get("x_factor_angle", 0)
        if x_factor < thresholds["xFactor"]:
            detected_faults.append({
                "name": "Poor Separation", 
                "severity": thresholds["xFactor"] / max(x_factor, 1),
                "detail": "Hips and shoulders turned together; needs more X-Factor."
            })

        # 7. Loss of Knee Flex
        knee_val = abs(metrics.get("knee_flex_change", 0))
        if knee_val > thresholds["knee"]:
            detected_faults.append({
                "name": "Loss of Knee Flex", 
                "severity": knee_val / thresholds["knee"],
                "detail": f"Knee angle changed by {knee_val:.1f}°."
            })

        # 8. Over the Top
        hand_angle = abs(metrics.get("initial_hand_path_angle", 0))
        if hand_angle > thresholds["ott"]:
            detected_faults.append({
                "name": "Over the Top", 
                "severity": hand_angle / thresholds["ott"],
                "detail": f"Hands moved outward at {hand_angle:.1f}° over the plane."
            })

        detected_faults = sorted(detected_faults, key=lambda x: x['severity'], reverse=True)
        
        recommended_drills = self._select_top_drills(detected_faults)
        
        return {
            "faults": detected_faults,
            "recommended_drills": recommended_drills
        }

    def _select_top_drills(self, faults):
        """Logic to select exactly 3 YouTube videos based on fault severity."""
        from .drill_db import DRILL_DATA # Your dictionary of YT links
        
        num_detected = len(faults)
        
        # Case 0: No faults found
        if num_detected == 0:
            return DRILL_DATA["General Improvement"][:3]

        # Case 1: 1 fault found -> 3 videos for that fault
        if num_detected == 1:
            return DRILL_DATA.get(faults[0]['name'], DRILL_DATA["General Improvement"])[:3]

        # Case 2: 2 faults found -> 2 for the most severe, 1 for the second
        if num_detected == 2:
            drill_1 = DRILL_DATA.get(faults[0]['name'], [])
            drill_2 = DRILL_DATA.get(faults[1]['name'], [])
            return drill_1[:2] + drill_2[:1]

        # Case 3: 3+ faults found
        if num_detected >= 3:
            # If the #1 fault is 50% more severe than the #2 fault, prioritize it
            if faults[0]['severity'] > (faults[1]['severity'] * 1.5):
                drill_1 = DRILL_DATA.get(faults[0]['name'], [])
                drill_2 = DRILL_DATA.get(faults[1]['name'], [])
                return drill_1[:2] + drill_2[:1]
            else:
                # Balanced: 1 video for each of the top 3 most severe faults
                drill_1 = DRILL_DATA.get(faults[0]['name'], [])
                drill_2 = DRILL_DATA.get(faults[1]['name'], [])
                drill_3 = DRILL_DATA.get(faults[2]['name'], [])
                return drill_1[:1] + drill_2[:1] + drill_3[:1]

    def _get_spine_angle(self, landmarks_frame):
        # Explicitly slice [:2] to ignore the confidence score
        hip_mid = utils.get_midpoint(landmarks_frame[:, :2], LEFT_HIP, RIGHT_HIP)
        shldr_mid = utils.get_midpoint(landmarks_frame[:, :2], LEFT_SHOULDER, RIGHT_SHOULDER)
        
        spine_vector = shldr_mid - hip_mid
        # In 2D, Y increases downwards. So "Up" towards the head is[0, -1]
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
        head_x_address = landmarks_array[address_idx, NOSE, 0]
        backswing_head_x = landmarks_array[address_idx:top_idx + 1, NOSE, 0]
        
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
            if width > 300: return 300.0
            if width > 20: # Valid width found
                return width
        return 40.0

    def _clean_landmarks(self, landmarks_array):
        """
        Fixes 'lost tracking' frames (where YOLO outputs [0, 0]) by 
        interpolating the position from surrounding valid frames.
        """
        if landmarks_array.size == 0 or landmarks_array.shape[0] == 0:
            return landmarks_array

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