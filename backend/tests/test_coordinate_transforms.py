import numpy as np
import pytest

def test_pinhole_unprojection_roundtrip():
    """Verify exact mathematical invertibility of pinhole camera projection."""
    w, h = 1920, 1080
    fx, fy = 934.18, 934.18
    cx, cy = 960.0, 540.0

    # Known pixel test points: center, corners, arbitrary
    test_pixels = np.array([
        [960.0, 540.0],
        [100.0, 100.0],
        [1820.0, 980.0],
        [450.5, 782.3],
    ])
    test_depths = np.array([10.0, 25.5, 50.0, 120.2])

    u = test_pixels[:, 0]
    v = test_pixels[:, 1]
    z = test_depths

    # Pinhole back-projection
    x_c = (u - cx) * z / fx
    y_c = (v - cy) * z / fy
    z_c = z

    # Forward projection back to image plane
    u_proj = x_c * fx / z_c + cx
    v_proj = y_c * fy / z_c + cy

    np.testing.assert_allclose(u_proj, u, atol=1e-5)
    np.testing.assert_allclose(v_proj, v, atol=1e-5)


def test_camera_world_transformation_invertibility():
    """Verify rigid-body SE(3) transformation between camera and world frames."""
    # Arbitrary camera pose: drone looking forward-downward
    pitch = np.radians(-35)
    yaw = np.radians(20)
    R_pitch = np.array([
        [1, 0, 0],
        [0, np.cos(pitch), -np.sin(pitch)],
        [0, np.sin(pitch), np.cos(pitch)]
    ])
    R_yaw = np.array([
        [np.cos(yaw), 0, np.sin(yaw)],
        [0, 1, 0],
        [-np.sin(yaw), 0, np.cos(yaw)]
    ])
    R_w2c = R_pitch @ R_yaw
    t_w2c = np.array([12.5, -45.0, 110.0])

    # Check proper SO(3) rotation
    np.testing.assert_allclose(R_w2c @ R_w2c.T, np.eye(3), atol=1e-6)
    assert np.isclose(np.linalg.det(R_w2c), 1.0)

    # Inverses
    R_c2w = R_w2c.T
    C_w = -R_w2c.T @ t_w2c

    # Test 3D points in camera frame
    P_c = np.array([
        [0.0, 0.0, 10.0],
        [5.0, -2.0, 30.0],
        [-15.0, 8.0, 75.0],
    ])

    # Camera to World
    P_w = (R_c2w @ P_c.T).T + C_w

    # World back to Camera
    P_c_reprojected = (R_w2c @ (P_w - C_w).T).T

    np.testing.assert_allclose(P_c_reprojected, P_c, atol=1e-6)


def test_threejs_upright_orientation_convention():
    """Verify that inverted Y (+Y_three = -Y_colmap) produces upright aerial elevation."""
    # Point beneath the drone in OpenCV convention (+Y is down)
    P_c_opencv = np.array([0.0, 5.0, 20.0])  # +Y is downward below drone

    R_c2w = np.eye(3)
    C_w = np.array([0.0, -50.0, 0.0])  # Drone at altitude in OpenCV space

    P_w = R_c2w @ P_c_opencv + C_w
    # P_w[1] = -50 + 5 = -45 (ground is at -45 in OpenCV)

    # In Three.js canonical aerial orientation, invert Y:
    P_three = P_w.copy()
    P_three[1] = -P_three[1]

    # In Three.js, altitude should be +45 (positive elevation UP)
    assert P_three[1] == 45.0

