"""Interactive interface: explore a district, run a what-if scenario, inspect recommendations.

Run with ``streamlit run app/main.py``.
"""

import sys
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sitetwin import recommend, simulate  # noqa: E402
from sitetwin.data import DISTRICTS, FACILITY_TYPES  # noqa: E402

st.set_page_config(page_title="Sofia Site Twin", layout="wide")
st.title("Sofia Site Twin")
st.caption("Where should the next facility open? Explore demand, test a location, compare.")

with st.sidebar:
    district = st.selectbox("District", list(DISTRICTS))
    facility_type = st.selectbox("Facility type", FACILITY_TYPES)
    radius = st.slider("Service radius (m)", 200, 1000, 500, 50)
    st.subheader("Scenario")
    lat0, lon0 = DISTRICTS[district]
    lat = st.number_input("Latitude", value=lat0, format="%.5f")
    lon = st.number_input("Longitude", value=lon0, format="%.5f")
    place = st.checkbox("Place a new facility here")

recs = recommend(district, facility_type, k=3, radius_m=radius)
result = simulate(district, facility_type, add=[(lat, lon)] if place else [], radius_m=radius)
base, scen = result["baseline"], result["scenario"]

col1, col2, col3 = st.columns(3)
col1.metric(
    "Unserved residents",
    f"{scen['unserved_residents']:,.0f}",
    f"{scen['unserved_residents'] - base['unserved_residents']:,.0f}",
    delta_color="inverse",
)
col2.metric(
    "Mean distance to nearest (m)",
    f"{scen['mean_dist_nearest_m']:,.0f}",
    f"{scen['mean_dist_nearest_m'] - base['mean_dist_nearest_m']:,.0f}",
    delta_color="inverse",
)
col3.metric(
    "Market share of new facility",
    f"{100 * result['new_share'][0]:.1f}%" if result["new_share"] else "-",
)

cells = result["cells"].assign(unserved=lambda d: (d.nearest_m > radius).astype(int))
layers = [
    pdk.Layer(
        "ColumnLayer",
        cells,
        get_position="[lon, lat]",
        get_elevation="residents",
        radius=60,
        pickable=True,
        get_fill_color="[230 * unserved, 120, 200 * (1 - unserved), 160]",
    ),
    pdk.Layer(
        "ScatterplotLayer",
        result["facilities"],
        get_position="[lon, lat]",
        get_radius=60,
        get_fill_color="[20, 20, 20, 230]",
        pickable=True,
    ),
]
if recs:
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            pd.DataFrame(recs),
            get_position="[lon, lat]",
            get_radius=90,
            get_fill_color="[0, 180, 90, 220]",
        )
    )

st.pydeck_chart(
    pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(latitude=lat0, longitude=lon0, zoom=13.5, pitch=40),
        tooltip={"text": "{name}{cell_id}\nresidents: {residents}"},
    )
)
st.caption(
    "Column height = residents · red = outside the service radius · "
    "black = existing facilities · green = recommended locations"
)

st.subheader("Recommended locations")
for i, rec in enumerate(recs, 1):
    st.markdown(f"**{i}. ({rec['lat']:.5f}, {rec['lon']:.5f})** - " + "; ".join(rec["reasons"]))
