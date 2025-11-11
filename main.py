import argparse
import json
import numpy as np

# Import the main functions from our new modules
from lib.videoProcessing.pose_estimator import extract_landmarks_from_video
from lib.featureExtraction.feature_extractor import analyze_swing

def main():
    """The main entry point for the analysis pipeline."""
    parser = argparse.ArgumentParser(description='Run a full biomechanical analysis on a golf swing video.')
    parser.add_argument('video_path', type=str, help='Path to the input video file.')
    args = parser.parse_args()
    
    print(f"Starting analysis for: {args.video_path}")

    # --- Step 1: Call the Pose Estimator ---
    landmarks_array = extract_landmarks_from_video(args.video_path)
    
    # Exit if pose estimation failed
    if landmarks_array is None:
        print("Halting analysis.")
        return

    # --- Step 2: Call the Feature Extractor ---
    print("\n-> Running Biomechanical Analysis...")
    analysis_results = analyze_swing(landmarks_array)
    print("-> Analysis complete.")

    # --- Step 3: Handle Outputs (Saving and Printing) ---
    
    # Save the final, analyzed results to a file
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

    # Print a summary to the console
    print("\n--- ANALYSIS SUMMARY ---")
    print(f"Spine Angle at Address: {analysis_results['metrics']['spine_angle_address']:.1f}°")
    print(f"Spine Angle at Impact: {analysis_results['metrics']['spine_angle_impact']:.1f}°")
    print(f"Change at Impact: {analysis_results['metrics']['spine_angle_change_at_impact']:.1f}°")

if __name__ == '__main__':
    main()