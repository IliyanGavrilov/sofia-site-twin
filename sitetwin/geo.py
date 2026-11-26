"""Distance helpers with no GIS dependency, so the core model stays light to install and test."""

import numpy as np

EARTH_RADIUS_M = 6_371_000.0


def distance_matrix(a_lat, a_lon, b_lat, b_lon) -> np.ndarray:
    """Distances in metres between every point of A and every point of B, shape (len(A), len(B)).

    Equirectangular approximation: well under 1% error at city scale, and fully vectorised.
    """
    a_lat, a_lon = np.radians(np.asarray(a_lat, float)), np.radians(np.asarray(a_lon, float))
    b_lat, b_lon = np.radians(np.asarray(b_lat, float)), np.radians(np.asarray(b_lon, float))
    mean_lat = (a_lat[:, None] + b_lat[None, :]) / 2
    dx = (b_lon[None, :] - a_lon[:, None]) * np.cos(mean_lat)
    dy = b_lat[None, :] - a_lat[:, None]
    return EARTH_RADIUS_M * np.sqrt(dx**2 + dy**2)
