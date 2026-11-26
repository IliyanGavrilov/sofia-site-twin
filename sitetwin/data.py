"""Data access for the model.

``load_cells`` and ``load_facilities`` are the only way the model reads data. They currently
return deterministic synthetic data for the pilot districts; the PostGIS-backed versions
return the same columns, so nothing above this module changes when real data is plugged in.
"""

import zlib

import numpy as np
import pandas as pd

DISTRICTS = {
    "Mladost": (42.650, 23.380),
    "Lozenets": (42.675, 23.325),
}
FACILITY_TYPES = ["pharmacy", "supermarket", "kindergarten"]

_GRID = 20  # 20 x 20 cells, ~150 m apart


def _rng(key: str) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32(key.encode()))


def load_cells(district: str) -> pd.DataFrame:
    """Demand cells. Columns: ``cell_id, lat, lon, residents, footfall``."""
    lat0, lon0 = DISTRICTS[district]
    rng = _rng(district)
    offsets = np.arange(_GRID) - _GRID / 2
    lat, lon = np.meshgrid(lat0 + offsets * 0.00135, lon0 + offsets * 0.00185, indexing="ij")
    dense = np.exp(-((lat - lat0 - 0.004) ** 2 + (lon - lon0 + 0.006) ** 2) / 2e-5)
    residents = np.round(80 + 900 * dense + rng.gamma(2, 40, lat.shape))
    return pd.DataFrame(
        {
            "cell_id": [f"{district.lower()}-{i}" for i in range(lat.size)],
            "lat": lat.ravel(),
            "lon": lon.ravel(),
            "residents": residents.ravel(),
            "footfall": rng.uniform(0, 1, lat.size),
        }
    )


def load_facilities(district: str, facility_type: str) -> pd.DataFrame:
    """Existing facilities (the supply). Columns: ``id, lat, lon, type, name``."""
    lat0, lon0 = DISTRICTS[district]
    rng = _rng(district + facility_type)
    k = {"pharmacy": 8, "supermarket": 5, "kindergarten": 4}.get(facility_type, 5)
    return pd.DataFrame(
        {
            "id": np.arange(k),
            "lat": lat0 + rng.uniform(-0.012, 0.012, k),
            "lon": lon0 + rng.uniform(-0.016, 0.016, k),
            "type": facility_type,
            "name": [f"{facility_type.capitalize()} {i + 1}" for i in range(k)],
        }
    )
