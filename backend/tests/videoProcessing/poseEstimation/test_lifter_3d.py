import os
import sys
import numpy as np
import torch
from unittest.mock import MagicMock, patch

# --- SETUP PATHS FOR VIDEOPOSE3D ---
# We need to do this BEFORE importing tasks, so lifter_3d can find 'common'
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up to project root (AIGolfCoach/)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
    # Define path to VideoPose3D
    vp3d_path = os.path.join(project_root, 'VideoPose3dRepo', 'VideoPose3D')
    
    if os.path.exists(vp3d_path):
        sys.path.append(vp3d_path)
    else:
        print(f"WARNING: VideoPose3D path not found at: {vp3d_path}")
except Exception as e:
    print(f"Error setting up paths: {e}")

from lib.python.videoProcessing.poseEstimation.lifter_3d import (
    get_lifter_model, 
    create_temporal_chunks, 
    preprocess_2d_data, 
    run_inference, 
    lift_2d_to_3d,
    RECEPTIVE_FIELD
)

# 1. Test the Lazy Loader (Singleton Pattern)
@patch('lib.python.videoProcessing.poseEstimation.lifter_3d.TemporalModel')
@patch('torch.load')
def test_get_lifter_model_singleton(mock_torch_load, mock_temporal_model):
    """Verify the 3D model is only initialized once and correctly configured."""
    # Reset the global variable for a clean test state
    with patch('lib.python.videoProcessing.poseEstimation.lifter_3d._MODEL_3D', None):
        # Mock the checkpoint dictionary
        mock_torch_load.return_value = {'model_pos': {}}
        
        model1 = get_lifter_model()
        model2 = get_lifter_model()
        
        # Check singleton behavior
        assert model1 is model2
        # Check that TemporalModel was instantiated once
        mock_temporal_model.assert_called_once()
        # Check that eval() was called
        model1.eval.assert_called()

# 2. Test Temporal Chunking and Padding
def test_create_temporal_chunks():
    """Verify that padding logic correctly increases sequence length and adds batch dimension."""
    num_frames = 10
    num_joints = 17
    # Input shape: (Frames, Joints, XY)
    fake_kps = np.random.rand(num_frames, num_joints, 2)
    
    output_tensor = create_temporal_chunks(fake_kps, RECEPTIVE_FIELD)
    
    # Padding = (27 - 1) / 2 = 13 on each side
    # Total frames = 10 + 13 + 13 = 36
    expected_frames = num_frames + (RECEPTIVE_FIELD - 1)
    
    assert isinstance(output_tensor, torch.Tensor)
    assert output_tensor.shape == (1, expected_frames, num_joints, 2)
    assert output_tensor.dtype == torch.float32

# 3. Test Pre-processing Pipeline
@patch('lib.python.utils.normalize_screen_coordinates')
def test_preprocess_2d_data(mock_normalize):
    """Verify that preprocessing calls normalization and chunking in order."""
    video_res = (1920, 1080)
    fake_kps = np.random.rand(50, 17, 3) # (F, J, XY+Conf)
    
    # Mock normalization to return just the XY parts
    mock_normalize.return_value = fake_kps[:, :, :2]
    
    result = preprocess_2d_data(fake_kps, video_res)
    
    mock_normalize.assert_called_once()
    assert result.shape[0] == 1 # Batch dimension added
    assert result.shape[2] == 17 # Joints preserved

# 4. Test Inference Execution
@patch('lib.python.videoProcessing.poseEstimation.lifter_3d.get_lifter_model')
def test_run_inference(mock_get_model):
    """Verify that inference moves data to device and removes batch dimension."""
    mock_model = MagicMock()
    # Mock model output: (1, 50, 17, 3) -> Batch, Frames, Joints, XYZ
    fake_output = torch.randn(1, 50, 17, 3)
    mock_model.return_value = fake_output
    mock_get_model.return_value = mock_model
    
    input_tensor = torch.randn(1, 76, 17, 2)
    
    prediction = run_inference(input_tensor)
    
    # Should be squeezed (remove batch dimension) and converted to numpy
    assert isinstance(prediction, np.ndarray)
    assert prediction.shape == (50, 17, 3)

# 5. Test Full Integration (The "lift_2d_to_3d" function)
@patch('lib.python.videoProcessing.poseEstimation.lifter_3d.preprocess_2d_data')
@patch('lib.python.videoProcessing.poseEstimation.lifter_3d.run_inference')
def test_lift_2d_to_3d_integration(mock_run, mock_preprocess):
    """Verify the orchestration of the full lifting pipeline."""
    mock_preprocess.return_value = torch.randn(1, 50, 17, 2)
    mock_run.return_value = np.zeros((24, 17, 3))
    
    kps_in = np.ones((24, 17, 3))
    res = (1280, 720)
    
    result = lift_2d_to_3d(kps_in, res)
    
    mock_preprocess.assert_called_with(kps_in, res)
    mock_run.assert_called_once()
    assert result.shape == (24, 17, 3)