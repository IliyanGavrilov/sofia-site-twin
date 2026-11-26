from sitetwin import recommend, simulate


def test_simulate_adding_a_facility():
    r = simulate("Mladost", "pharmacy", add=[(42.65, 23.38)])
    assert r["scenario"]["facilities"] == r["baseline"]["facilities"] + 1
    assert r["scenario"]["unserved_residents"] <= r["baseline"]["unserved_residents"]
    assert len(r["new_share"]) == 1 and 0 < r["new_share"][0] < 1


def test_simulate_removing_a_facility():
    r = simulate("Mladost", "pharmacy", remove=[0])
    assert r["scenario"]["facilities"] == r["baseline"]["facilities"] - 1
    assert r["scenario"]["unserved_residents"] >= r["baseline"]["unserved_residents"]


def test_simulate_without_changes_matches_baseline():
    r = simulate("Lozenets", "supermarket")
    assert r["scenario"] == r["baseline"]
    assert r["new_share"] == []


def test_recommend_is_ranked_and_explained():
    recs = recommend("Mladost", "pharmacy", k=3)
    assert 1 <= len(recs) <= 3
    assert all(rec["reasons"] for rec in recs)
    scores = [rec["score"] for rec in recs]
    assert scores == sorted(scores, reverse=True)


def test_recommendation_reduces_unserved():
    best = recommend("Mladost", "kindergarten", k=1)[0]
    r = simulate("Mladost", "kindergarten", add=[(best["lat"], best["lon"])])
    gain = r["baseline"]["unserved_residents"] - r["scenario"]["unserved_residents"]
    assert gain == best["score"]
