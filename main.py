import argparse
import json
import numpy as np

# Import the main functions from our new modules
from lib.videoProcessing.pose_estimator import extract_landmarks_from_video
from lib.featureExtraction.feature_extractor import SwingAnalysis

def main():
    """The main entry point for the analysis pipeline."""
    parser = argparse.ArgumentParser(description='Run a full biomechanical analysis on a golf swing video.')
    parser.add_argument('--dtl', type=str, required=True, help='Path to the Down-the-Line (DTL) video.')
    parser.add_argument('--fo', type=str, required=True, help='Path to the Face-On (FO) video.')
    args = parser.parse_args()
    
    print(f"Starting analysis for DTL: '{args.dtl}' and FO: '{args.fo}'")

    # --- Step 1: Process both videos to get landmarks ---
    landmarks_array_dtl = extract_landmarks_from_video(args.dtl)
    landmarks_array_fo = extract_landmarks_from_video(args.fo)
    
    if landmarks_array_dtl is None or landmarks_array_fo is None:
        print("Halting analysis: Pose estimation failed on one or both videos.")
        return

    # --- Step 2: Create an analysis object and run it ---
    try:
        # Create an instance of the analysis class
        swing_analyzer = SwingAnalysis(landmarks_dtl=landmarks_array_dtl, landmarks_fo=landmarks_array_fo)
        
        # Run the full analysis with a single method call
        analysis_results = swing_analyzer.run_full_analysis()
        
    except ValueError as e:
        print(f"Analysis Error: {e}")
        return

    # --- Step 3: Handle Outputs ---
    analysis_output_path = 'swing_analysis.json'
    with open(analysis_output_path, 'w') as f:
        # We need a custom way to save NumPy arrays to JSON
        # This class helps json.dump handle NumPy types
        class NpEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                if isinstance(obj, np.floating):
                    return float(obj)
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                return super(NpEncoder, self).default(obj)
        
        json.dump(analysis_results, f, indent=4, cls=NpEncoder)
    
    print(f"\nFinal analysis results saved to {analysis_output_path}")

    print("\n--- ANALYSIS SUMMARY ---")
    metrics = analysis_results['metrics']
    
    # Print Metrics
    print(f"Spine Angle Change at Impact: {metrics['spine_angle_change_at_impact']:.1f}°")
    print(f"Max Head Sway in Backswing: {metrics['max_head_sway_cm']:.1f} cm")
    print(f"Backswing Length (Arm Angle): {metrics['backswing_length_angle']:.1f}°")
    print(f"Lead Arm Angle at Impact: {metrics['lead_arm_angle_impact']:.1f}°")
    
    # Print Faults
    if analysis_results['diagnosed_faults']:
        print("\nFaults Detected:")
        for fault in analysis_results['diagnosed_faults']:
            print(f"- {fault['name']}: {fault['detail']}")
    else:
        print("\nNo major faults detected.")

if __name__ == '__main__':
    main()