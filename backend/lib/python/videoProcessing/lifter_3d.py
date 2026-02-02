# lib/python/videoProcessing/lifter_3d.py
import numpy as np
import torch
from .. import utils

RECEPTIVE_FIELD = 27 

from common.model import TemporalModel

# ----- MODEL INITIALIZATION -----

print("Initializing VideoPose3D model...")

# --- 1. Define Model Architecture ---
# These parameters are based on the pre-trained model's architecture.
# They are typically found in the arguments or config of the original repository.
filter_widths = [3, 3, 3, 3, 3] # This is a common default (receptive field of 243 frames)
channels = 1024
dropout = 0.25
num_joints_in = 17 # Human3.6M format
in_features = 2 # x, y coordinates
num_joints_out = 17 # We are predicting 17 3D joints

MODEL_3D = TemporalModel(
    num_joints_in=num_joints_in,
    in_features=in_features,
    num_joints_out=num_joints_out,
    filter_widths=filter_widths,
    causal=False, # Use non-causal for highest accuracy
    dropout=dropout,
    channels=channels
)

# --- 2. Load the Pre-trained Weights ---
# IMPORTANT: Replace this with the actual path to the downloaded model checkpoint file.
model_path = 'C:/Users/Michael/OneDrive - Technological University Dublin/Year 4/Final year project/Repo/AIGolfCoach/VideoPose3dRepo/VideoPose3D/checkpoint/pretrained_h36m_detectron_coco.bin'

try:
    checkpoint = torch.load(model_path, map_location=lambda storage, loc: storage)
    MODEL_3D.load_state_dict(checkpoint['model_pos'])
except FileNotFoundError:
    print(f"\n\nERROR: VideoPose3D model checkpoint not found at '{model_path}'")
    print("Please download the pre-trained model and update the path in lifter_3d.py\n\n")

# --- 3. Set the model to evaluation mode and move to GPU if available ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_3D = MODEL_3D.to(device)
MODEL_3D.eval()


def create_temporal_chunks(keypoints_2d_sequence, receptive_field):
    """
    Pads and prepares the 2D keypoint sequence for a temporal model.
    """
    num_frames = keypoints_2d_sequence.shape[0]

    # Calculate the padding required on each side of the sequence
    pad = (receptive_field - 1) // 2

    # Pad the sequence. We "reflect" the start and end poses to create the padding.
    # E.g., for frame 0, we need to see frames from -13 to 13.
    # We use frame 13's pose for -13, frame 12's for -12, and so on.
    padded_sequence = np.pad(keypoints_2d_sequence, ((pad, pad), (0, 0), (0, 0)), mode='reflect')

    # The model expects a "batch" of one video. So we add a new dimension at the start.
    # Shape becomes (1, num_frames + 2*pad, num_keypoints, 2 for x,y)
    input_batch = np.expand_dims(padded_sequence, axis=0)

    # Convert to a PyTorch tensor, ready for the model
    return torch.from_numpy(input_batch.astype('float32'))

def preprocess_2d_data(keypoints_2d_sequence: np.ndarray, video_resolution: tuple):
    """
    Performs the full pre-processing pipeline on a 2D keypoint sequence.
    """
    print("-> Pre-processing 2D data for 3D lifting...")

    # --- Step 1: Normalize screen coordinates ---
    keypoints_xy = keypoints_2d_sequence[:, :, :2]
    w, h = video_resolution
    normalized_keypoints = utils.normalize_screen_coordinates(keypoints_xy, w=w, h=h)

    # --- Step 2: Create temporal chunks ---
    input_tensor = create_temporal_chunks(normalized_keypoints, RECEPTIVE_FIELD)
    
    print("-> Pre-processing complete.")
    return input_tensor

def run_inference(preprocessed_2d_tensor: torch.Tensor):
    """
    Runs the inference on the pre-trained VideoPose3D model.

    Args:
        preprocessed_2d_tensor (torch.Tensor): The output from preprocess_2d_data.

    Returns:
        np.ndarray: The predicted 3D pose sequence.
    """
    # Ensure the input tensor is on the same device as the model (CPU or GPU)
    input_tensor = preprocessed_2d_tensor.to(device)

    # Run inference inside a no_grad() block for efficiency
    with torch.no_grad():
        predicted_3d_poses = MODEL_3D(input_tensor)

    # The model's output is on the GPU, move it back to the CPU for NumPy conversion
    poses_cpu = predicted_3d_poses.cpu().numpy()
    
    # The model output is a batch of one. We remove the batch dimension.
    return poses_cpu.squeeze(0)

def lift_2d_to_3d(keypoints_2d_sequence: np.ndarray, video_resolution: tuple):
    """
    Takes a sequence of 2D keypoints from YOLOv8 and lifts them to 3D.
    """
    print("-> Lifting 2D keypoints to 3D...")
    
    # 1. Pre-process the data
    input_tensor = preprocess_2d_data(keypoints_2d_sequence, video_resolution)
    
    # 2. Run inference on the model
    predicted_3d_sequence = run_inference(input_tensor)
    
    print("-> 3D Lifting complete.")
    return predicted_3d_sequence