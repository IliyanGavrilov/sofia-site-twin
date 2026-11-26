"""Key performance indicators shared by the baseline and every scenario."""

import numpy as np


def compute_kpis(residents: np.ndarray, dist: np.ndarray, radius_m: float) -> dict:
    """KPIs for one state of the district. ``dist`` is (cells, facilities) in metres.

    - ``unserved_residents`` / ``unserved_pct``: residents with no facility within ``radius_m``
    - ``mean_dist_nearest_m``: resident-weighted mean distance to the nearest facility
    - ``residents_per_facility``: saturation of the district
    """
    total = float(residents.sum())
    if dist.shape[1] == 0:
        return {
            "facilities": 0,
            "unserved_residents": total,
            "unserved_pct": 100.0,
            "mean_dist_nearest_m": float("nan"),
            "residents_per_facility": float("inf"),
        }
    nearest = dist.min(axis=1)
    unserved = float(residents[nearest > radius_m].sum())
    return {
        "facilities": int(dist.shape[1]),
        "unserved_residents": unserved,
        "unserved_pct": 100.0 * unserved / total if total else 0.0,
        "mean_dist_nearest_m": float(np.average(nearest, weights=residents)) if total else 0.0,
        "residents_per_facility": total / dist.shape[1],
    }
