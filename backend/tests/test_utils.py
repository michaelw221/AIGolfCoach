import numpy as np
import pytest
from lib.python.utils import calculate_angle_3d

def test_calculate_angle_90_degrees():
    v1 = np.array([1, 0, 0])
    v2 = np.array([0, 1, 0])
    assert calculate_angle_3d(v1, v2) == pytest.approx(90.0)

def test_calculate_angle_0_degrees():
    v1 = np.array([0, 1, 0])
    v2 = np.array([0, 1, 0])
    assert calculate_angle_3d(v1, v2) == pytest.approx(0.0)

def test_calculate_angle_floating_point_safety():
    # Test that values slightly outside [-1, 1] don't crash the arccos
    v1 = np.array([0, 1, 0])
    v2 = np.array([0, 1.00000000001, 0]) 
    # Should not return NaN
    assert not np.isnan(calculate_angle_3d(v1, v2))