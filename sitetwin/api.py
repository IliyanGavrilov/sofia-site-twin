"""Public interface of the digital twin: what-if simulation and location recommendation."""

import numpy as np
import pandas as pd

from sitetwin.data import load_cells, load_facilities
from sitetwin.geo import distance_matrix
from sitetwin.huff import huff_probabilities, market_share
from sitetwin.kpi import compute_kpis

DEFAULT_RADIUS_M = 500


def simulate(
    district: str,
    facility_type: str,
    add: list[tuple[float, float]] | None = None,
    remove: list[int] | None = None,
    radius_m: float = DEFAULT_RADIUS_M,
) -> dict:
    """Compare the current state of a district with a scenario.

    ``add`` places new facilities at ``(lat, lon)``; ``remove`` closes existing ones by id.
    Returns ``baseline`` and ``scenario`` KPIs, the scenario's ``cells`` (with distance to the
    nearest facility) and ``facilities`` (with Huff market share), and ``new_share``: the
    market share of each added facility.
    """
    add, remove = add or [], remove or []
    cells = load_cells(district)
    residents = cells.residents.to_numpy()
    existing = load_facilities(district, facility_type)
    baseline = compute_kpis(
        residents, distance_matrix(cells.lat, cells.lon, existing.lat, existing.lon), radius_m
    )

    added = pd.DataFrame(
        {
            "id": [-(i + 1) for i in range(len(add))],
            "lat": [p[0] for p in add],
            "lon": [p[1] for p in add],
            "type": facility_type,
            "name": [f"New {facility_type} {i + 1}" for i in range(len(add))],
        }
    )
    facilities = pd.concat([existing[~existing.id.isin(remove)], added], ignore_index=True)
    dist = distance_matrix(cells.lat, cells.lon, facilities.lat, facilities.lon)
    share = market_share(residents, huff_probabilities(dist))

    return {
        "baseline": baseline,
        "scenario": compute_kpis(residents, dist, radius_m),
        "cells": cells.assign(nearest_m=dist.min(axis=1) if dist.shape[1] else np.inf),
        "facilities": facilities.assign(share=share),
        "new_share": share[len(facilities) - len(add) :].tolist(),
    }


def recommend(
    district: str, facility_type: str, k: int = 3, radius_m: float = DEFAULT_RADIUS_M
) -> list[dict]:
    """Top-``k`` locations for a new facility, by greedy maximal coverage.

    Each pick is the cell centre that brings the most currently unserved residents within
    ``radius_m``; covered residents are then marked served before the next pick. Returns
    ``[{"lat", "lon", "score", "reasons"}]`` with human-readable justifications.
    O(k * n^2) for n cells.
    """
    cells = load_cells(district)
    existing = load_facilities(district, facility_type)
    residents = cells.residents.to_numpy()
    if len(existing):
        to_existing = distance_matrix(cells.lat, cells.lon, existing.lat, existing.lon)
        served = to_existing.min(axis=1) <= radius_m
    else:
        to_existing = np.full((len(cells), 1), np.inf)
        served = np.zeros(len(cells), bool)
    covers = distance_matrix(cells.lat, cells.lon, cells.lat, cells.lon) <= radius_m

    picks = []
    for _ in range(k):
        gain = (residents[:, None] * (covers & ~served[:, None])).sum(axis=0)
        c = int(gain.argmax())
        if gain[c] <= 0:
            break
        nearest = float(to_existing[c].min())
        picks.append(
            {
                "lat": float(cells.lat[c]),
                "lon": float(cells.lon[c]),
                "score": float(gain[c]),
                "reasons": [
                    f"{int(gain[c]):,} residents without a {facility_type} within {radius_m} m",
                    f"nearest existing {facility_type} is {nearest:,.0f} m away",
                ],
            }
        )
        served |= covers[:, c]
    return picks
