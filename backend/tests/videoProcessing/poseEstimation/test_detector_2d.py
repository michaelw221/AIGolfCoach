import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from lib.python.videoProcessing.poseEstimation.detector_2d import detect_2d_poses, get_model

# 1. Test the Lazy Loader
def test_get_model_singleton():
    """Verify that the model is only loaded once (Singleton pattern)."""
    with patch('lib.python.videoProcessing.poseEstimation.detector_2d.YOLO') as mock_yolo:
        model1 = get_model()
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