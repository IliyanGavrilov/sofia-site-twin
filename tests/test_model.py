import numpy as np

from sitetwin.geo import distance_matrix
from sitetwin.huff import huff_probabilities, market_share
from sitetwin.kpi import compute_kpis


def test_distance_one_km_north():
    d = distance_matrix([42.65], [23.38], [42.65 + 1 / 111.2], [23.38])
    assert abs(d[0, 0] - 1000) < 10


def test_huff_rows_sum_to_one_and_closer_wins():
    p = huff_probabilities(np.array([[100.0, 200.0], [300.0, 50.0]]))
    assert np.allclose(p.sum(axis=1), 1)
    assert p[0, 0] > p[0, 1]
    assert p[1, 1] > p[1, 0]


def test_market_share_sums_to_one():
    p = huff_probabilities(np.array([[100.0, 200.0], [300.0, 50.0]]))
    assert np.isclose(market_share(np.array([10.0, 30.0]), p).sum(), 1)


def test_kpis_without_facilities_leave_everyone_unserved():
    k = compute_kpis(np.array([10.0, 20.0]), np.zeros((2, 0)), 500)
    assert k["unserved_residents"] == 30 and k["unserved_pct"] == 100


def test_kpis_radius():
    k = compute_kpis(np.array([10.0, 20.0]), np.array([[100.0], [900.0]]), 500)
    assert k["unserved_residents"] == 20
