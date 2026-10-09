"""Camera field-of-view checks and pinhole measurement modeling.

Part G supplies visibility, projection, and pixel covariance (docs/HUONG_DAN_KY_THUAT.md §2).
The platform differentiates projection using a chain-rule Jacobian.
"""

from __future__ import annotations

from typing import Any
from typing import Sequence

import numpy as np
from fusion_lab.workspace_support import get_tracking_params

Matrix = np.matrix | np.ndarray
params = get_tracking_params()

# vi: from fusion_lab.workspace_support import get_tracking_params


def is_in_field_of_view(x: Matrix, sensor: Any) -> bool:
    """Return True if state x is visible within the sensor horizontal field of view.

    Args:
        x: State vector (6x1) with position in vehicle frame.
        sensor: Lidar or camera adapter with ``veh_to_sens`` and ``fov``
            (radians).

    Returns:
        True if sensor coordinates are finite and the horizontal angle is within
        ``sensor.fov``. A camera additionally requires depth > 1e-6.
    """
    state = np.asarray(x, dtype=float).reshape(-1)
    transform = np.asarray(sensor.veh_to_sens, dtype=float)
    position = transform[:3, :3] @ state[:3] + transform[:3, 3]
    if not np.isfinite(position).all():
        return False
    if getattr(sensor, "name", None) == "camera":
        depth_epsilon = float(getattr(sensor, "depth_epsilon", 1e-6))
        if position[0] <= depth_epsilon:
            return False
    angle = float(np.arctan2(position[1], position[0]))
    lower, upper = sensor.fov
    return bool(np.isfinite(angle) and lower <= angle <= upper)


def camera_measurement_prediction(x: Matrix, sensor: Any) -> Matrix:
    """Predict image-plane measurement h(x) using the pinhole camera model.

    Args:
        x: State vector.
        sensor: Camera with intrinsics ``f_i, f_j, c_i, c_j``.

    Returns:
        2x1 predicted pixel coordinates as ``np.matrix``.

    Raises:
        ValueError: With coordinate context if sensor coordinates are nonfinite
            or depth is at most 1e-6.
    """
    state = np.asarray(x, dtype=float).reshape(-1)
    transform = np.asarray(sensor.veh_to_sens, dtype=float)
    position = transform[:3, :3] @ state[:3] + transform[:3, 3]
    depth_epsilon = float(getattr(sensor, "depth_epsilon", 1e-6))
    if not np.isfinite(position).all() or position[0] <= depth_epsilon:
        raise ValueError(
            "Camera projection needs finite coordinates and positive depth "
            f"> {depth_epsilon:g}; sensor position={position.tolist()}"
        )
    u = sensor.c_i - sensor.f_i * position[1] / position[0]
    v = sensor.c_j - sensor.f_j * position[2] / position[0]
    pixels = np.asarray([u, v], dtype=float)
    if not np.isfinite(pixels).all():
        raise ValueError(
            "Camera projection produced non-finite pixels; "
            f"sensor position={position.tolist()}"
        )
    return np.asmatrix(pixels).reshape(2, 1)


def build_camera_measurement(z: Sequence[float], sensor: Any) -> dict[str, Any]:
    """Build camera measurement vector z and covariance R from pixel coordinates.

    Args:
        z: Sequence ``[u, v]`` pixel coordinates.
        sensor: Camera sensor object.

    Returns:
        Dict with keys ``z``, ``R``, ``sensor``.
    """
    pixels = np.asarray(z, dtype=float).reshape(-1)
    if pixels.size != 2 or not np.isfinite(pixels).all():
        raise ValueError("Camera measurement must contain two finite pixel coordinates")
    measurement = np.asmatrix(pixels).reshape(2, 1)
    variances = np.square([params.sigma_cam_i, params.sigma_cam_j])
    covariance = np.asmatrix(np.diag(variances))
    return {"z": measurement, "R": covariance, "sensor": sensor}
