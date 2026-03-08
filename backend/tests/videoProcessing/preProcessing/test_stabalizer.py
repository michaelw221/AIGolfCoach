import numpy as np
from unittest.mock import patch
from lib.python.videoProcessing.preProcessing.stabilizer import stabilize_video

# Order of patches: Bottom-most decorator becomes the FIRST argument.
@patch('cv2.warpAffine')              # 7th argument
@patch('cv2.estimateAffinePartial2D') # 6th argument
@patch('cv2.calcOpticalFlowPyrLK')    # 5th argument
@patch('cv2.goodFeaturesToTrack')     # 4th argument
@patch('cv2.cvtColor')                # 3rd argument
@patch('cv2.VideoWriter')             # 2nd argument
@patch('cv2.VideoCapture')            # 1st argument
def test_stabilize_video_success(
    mock_capture,         # 1. VideoCapture
    mock_writer,          # 2. VideoWriter
    mock_cvtColor,        # 3. cvtColor
    mock_goodFeatures,    # 4. goodFeaturesToTrack
    mock_calcOpticalFlow, # 5. calcOpticalFlowPyrLK
    mock_estimateAffine,  # 6. estimateAffinePartial2D
    mock_warpAffine       # 7. warpAffine
):
    """Verify the full stabilization pipeline when features are successfully tracked."""
    
    # 1. Setup VideoCapture Mock
    mock_cap_inst = mock_capture.return_value
    
    # Provide enough .get() returns for FPS, Width, and Height
    mock_cap_inst.get.side_effect = [30.0, 1920, 1080, 1080]
    
    # Provide frames for the .read() calls. 
    # 1st read = prev_frame, 2nd read = curr_frame, 3rd read = end of video
    fake_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    mock_cap_inst.read.side_effect = [
        (True, fake_frame), 
        (True, fake_frame), 
        (False, None)       
    ]

    # 2. Setup Computer Vision Logic Mocks
    mock_cvtColor.return_value = np.zeros((1080, 1920), dtype=np.uint8)
    mock_goodFeatures.return_value = np.array([[[10, 10]]], dtype=np.float32)
    mock_calcOpticalFlow.return_value = (np.array([[[11, 11]]], dtype=np.float32), np.array([1]), None)
    
    # Mock a successful affine transformation matrix
    mock_m = np.eye(2, 3, dtype=np.float32)
    mock_estimateAffine.return_value = (mock_m, None)
    mock_warpAffine.return_value = fake_frame

    # Execute the function
    result = stabilize_video("input.mp4", "output.mp4")

    # Assertions
    assert result == "output.mp4"
    assert mock_warpAffine.called
    assert mock_cap_inst.release.called


@patch('cv2.warpAffine')              # 7th argument
@patch('cv2.estimateAffinePartial2D') # 6th argument
@patch('cv2.calcOpticalFlowPyrLK')    # 5th argument
@patch('cv2.goodFeaturesToTrack')     # 4th argument
@patch('cv2.cvtColor')                # 3rd argument
@patch('cv2.VideoWriter')             # 2nd argument
@patch('cv2.VideoCapture')            # 1st argument
def test_stabilize_video_fallback_on_no_features(
    mock_capture,         # 1. VideoCapture
    mock_writer,          # 2. VideoWriter
    mock_cvtColor,        # 3. cvtColor
    mock_goodFeatures,    # 4. goodFeaturesToTrack
    mock_calcOpticalFlow, # 5. calcOpticalFlowPyrLK
    mock_estimateAffine,  # 6. estimateAffinePartial2D
    mock_warpAffine       # 7. warpAffine
):
    """Verify fallback behavior when transformation fails (m is None)."""
    
    # 1. Setup VideoCapture Mock
    mock_cap_inst = mock_capture.return_value
    mock_cap_inst.get.side_effect = [30.0, 100, 100, 100]
    
    fake_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_cap_inst.read.side_effect = [
        (True, fake_frame), 
        (True, fake_frame), 
        (False, None)
    ]
    
    mock_goodFeatures.return_value = np.array([[[10, 10]]])
    mock_calcOpticalFlow.return_value = (np.array([[[11, 11]]]), np.array([1]), None)
    
    # 2. Simulate failure (m is None)
    mock_estimateAffine.return_value = (None, None)
    
    # Execute the function
    stabilize_video("in.mp4", "out.mp4")

    # Assertions
    # If m is None, warpAffine should NOT be called
    mock_warpAffine.assert_not_called()
    
    # VideoWriter.write should be called twice (the reference frame, and the fallback raw frame)
    assert mock_writer.return_value.write.call_count == 2