import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from lib.python.videoProcessing.poseEstimation.detector_2d import detect_2d_poses, get_model

# 1. Test the Lazy Loader
def test_get_model_singleton():
    """Verify that the model is only loaded once (Singleton pattern)."""
    with patch('lib.python.videoProcessing.poseEstimation.detector_2d.YOLO') as mock_yolo:
        # First call should initialize
        model1 = get_model()
        # Second call should return the same object without calling YOLO() again
        model2 = get_model()
        
        assert model1 is model2
        mock_yolo.assert_called_once()

# 2. Test Video Opening Failure
def test_detect_2d_poses_invalid_video():
    """Verify return values when the video file cannot be opened."""
    with patch('cv2.VideoCapture') as mock_cap:
        mock_cap.return_value.isOpened.return_value = False
        
        kps, res = detect_2d_poses("invalid_path.mp4")
        
        assert kps is None
        assert res is None

# 3. Test Successful Detection
def test_detect_2d_poses_success():
    """Verify logic when a person is detected in the frame."""
    with patch('cv2.VideoCapture') as mock_cap, \
         patch('lib.python.videoProcessing.poseEstimation.detector_2d.get_model') as mock_get_model:
        
        # Mock VideoCapture behavior (1 frame then end)
        mock_cap.return_value.isOpened.side_effect = [True, True, False]
        mock_cap.return_value.read.return_value = (True, np.zeros((100, 100, 3)))
        mock_cap.return_value.get.side_effect = [1920, 1080] # Width, Height
        
        # Mock YOLO Result structure: results[0].keypoints.data.cpu().numpy()
        mock_model = MagicMock()
        mock_keypoints = MagicMock()
        
        # Simulate (1, 17, 3) array returned by YOLO
        fake_data = np.ones((1, 17, 3)) 
        mock_keypoints.data.cpu.return_value.numpy.return_value = fake_data
        mock_keypoints.shape = [1, 17, 3] # shape[0] > 0
        
        mock_results = MagicMock()
        mock_results.keypoints = mock_keypoints
        mock_model.return_value = [mock_results]
        mock_get_model.return_value = mock_model

        kps, res = detect_2d_poses("fake_video.mp4")

        assert res == (1920, 1080)
        assert kps.shape == (1, 17, 3)
        assert np.array_equal(kps[0], fake_data[0])

# 4. Test Missing Detection (The Zero Placeholder)
def test_detect_2d_poses_no_person_found():
    """Verify that frames with no people detected are filled with zeros."""
    with patch('cv2.VideoCapture') as mock_cap, \
         patch('lib.python.videoProcessing.poseEstimation.detector_2d.get_model') as mock_get_model:
        
        mock_cap.return_value.isOpened.side_effect = [True, True, False]
        mock_cap.return_value.read.return_value = (True, np.zeros((100, 100, 3)))
        
        # Mock YOLO to return no people (shape[0] == 0)
        mock_keypoints = MagicMock()
        mock_keypoints.shape = [0, 17, 3] 
        
        mock_results = MagicMock()
        mock_results.keypoints = mock_keypoints
        
        mock_model = MagicMock()
        mock_model.return_value = [mock_results]
        mock_get_model.return_value = mock_model

        kps, _ = detect_2d_poses("fake_video.mp4")

        # Result should be a (1, 17, 3) array of all zeros
        assert kps.shape == (1, 17, 3)
        assert np.all(kps == 0)