import os
import sys
import numpy as np
import torch
from unittest.mock import MagicMock, patch

# --- SETUP PATHS FOR VIDEOPOSE3D ---
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
    vp3d_path = os.path.join(project_root, 'VideoPose3dRepo', 'VideoPose3D')
    if os.path.exists(vp3d_path): sys.path.append(vp3d_path)
except Exception:
    pass

from lib.python.videoProcessing.poseEstimation.lifter_3d import (
    get_lifter_model, 
    create_temporal_chunks, 
    preprocess_2d_data, 
    run_inference, 
    lift_2d_to_3d,
    RECEPTIVE_FIELD
)

@patch('lib.python.videoProcessing.poseEstimation.lifter_3d.TemporalModel')
@patch('torch.load')
def test_get_lifter_model_singleton(mock_torch_load, mock_temporal_model):
    """Verify the 3D model is only initialized once."""
    with patch('lib.python.videoProcessing.poseEstimation.lifter_3d._MODEL_3D', None):
        mock_torch_load.return_value = {'model_pos': {}}
        model1 = get_lifter_model()
        model2 = get_lifter_model()
        assert model1 is model2
        mock_temporal_model.assert_called_once()

def test_create_temporal_chunks():
    """Verify that padding logic correctly increases sequence length to meet minimum bounds."""
    num_frames = 10
    num_joints = 17
    fake_kps = np.random.rand(num_frames, num_joints, 2)
    
    output_tensor = create_temporal_chunks(fake_kps, RECEPTIVE_FIELD)
    
    # We added a REQUIRED_MIN_FRAMES = 243 constraint in the actual code
    # Plus (27-1)//2 = 13 padding on each side -> 243 + 26 = 269
    expected_frames = 243 + (RECEPTIVE_FIELD - 1)
    
    assert isinstance(output_tensor, torch.Tensor)
    assert output_tensor.shape == (1, expected_frames, num_joints, 2)

def test_preprocess_2d_data():
    """Verify normalization logic returns correct dimensions."""
    video_res = (1920, 1080)
    fake_kps = np.random.rand(50, 17, 3) 
    
    result = preprocess_2d_data(fake_kps, video_res)
    
    assert result.shape[0] == 1 
    assert result.shape[2] == 17 

def test_run_inference():
    """Verify that inference moves data to device, root-centers, and removes batch dimension."""
    mock_model = MagicMock()
    # Output shape: Batch, Frames, Joints, XYZ
    fake_output = torch.randn(1, 50, 17, 3)
    mock_model.return_value = fake_output
    
    # Patch the global model variable directly
    with patch('lib.python.videoProcessing.poseEstimation.lifter_3d._MODEL_3D', mock_model):
        input_tensor = torch.randn(1, 76, 17, 2)
        prediction = run_inference(input_tensor)
        
        assert isinstance(prediction, np.ndarray)
        assert prediction.shape == (50, 17, 3)

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