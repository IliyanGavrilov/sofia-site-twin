# Sofia Site Twin

[![CI](https://github.com/IliyanGavrilov/sofia-site-twin/actions/workflows/ci.yml/badge.svg)](https://github.com/IliyanGavrilov/sofia-site-twin/actions/workflows/ci.yml)
[![CodeQL](https://github.com/IliyanGavrilov/sofia-site-twin/actions/workflows/codeql.yml/badge.svg)](https://github.com/IliyanGavrilov/sofia-site-twin/actions/workflows/codeql.yml)
[![Security](https://github.com/IliyanGavrilov/sofia-site-twin/actions/workflows/security.yml/badge.svg)](https://github.com/IliyanGavrilov/sofia-site-twin/actions/workflows/security.yml)
![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)
![OGC API - Features](https://img.shields.io/badge/OGC-API%20Features-0A66C2)

An urban digital twin of Sofia for **site selection**: given a district and a type of
facility (pharmacy, supermarket, kindergarten...), it shows where demand is under-served,
simulates what happens when a facility opens or closes, and **recommends the best
locations for a new one - with the numbers behind each pick**.

The twin models each district as a grid of demand cells (residents, footfall) and the
existing facilities as the supply. Distances drive a Huff gravity model of how residents
split between competitors; a greedy maximal-coverage search then ranks candidate
locations by how many currently unserved residents they would reach.

> **Status:** early development. The model, the app and the OGC service run end to end on
> deterministic synthetic data for two pilot districts; the ingestion pipelines for the
> real data sources below are in progress.

## Layout

| Path | Purpose |
|------|---------|
| `sitetwin/` | Pure-Python core - distances, Huff model, KPIs, simulation and recommendation (`api.py`). Depends only on NumPy and pandas, unit-testable in isolation. |
| `sitetwin/data.py` | The single data-access point: demand cells and facilities per district. Swapping synthetic data for PostGIS happens here only. |
| `ingest/` | Pipelines from the open data sources into harmonised PostGIS tables. |
| `app/` | The Streamlit + pydeck interface - map, scenario controls, KPI comparison, recommendations. |
| `ogc/` | pygeoapi configuration publishing the twin's layers as OGC API - Features. |
| `tests/` | pytest suite for the model and the public API. |
| `docker-compose.yml` | PostGIS, pygeoapi and the app as one stack. |

## Prerequisites

- **[Python](https://www.python.org/) 3.13+**
- **[Git](https://git-scm.com/)** (to clone)
- [Docker](https://www.docker.com/) only for the full stack (PostGIS + OGC API); the app
  and the tests run without it.

## Setup

```bash
# 1. Clone
git clone https://github.com/IliyanGavrilov/sofia-site-twin.git
cd sofia-site-twin

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate            # Windows (PowerShell/cmd)
# source .venv/bin/activate       # Linux / macOS

# 3. Install dependencies
pip install -r requirements-dev.txt    # app + tests
pip install -r requirements-geo.txt    # only for the ingestion pipelines
```

## Running it

```bash
streamlit run app/main.py           # app at http://localhost:8501
pytest                              # run the test suite
ruff check .                        # lint
ruff format .                       # format
```

### Full stack

```bash
cp .env.example .env                # then set a real password
docker compose up --build
```

| Service | Address |
|---------|---------|
| App | http://localhost:8501 |
| OGC API - Features | http://localhost:5000/collections |
| PostGIS | `localhost:5432` |

## How to use

1. Pick a **district** and a **facility type** in the sidebar, and set the **service
   radius** - how far a resident is willing to go.
2. The map shows every demand cell as a column: height = residents, red = no facility
   within the radius. Black points are the existing facilities.
3. The **recommended locations** (green) are ranked by how many unserved residents each
   would reach, each with its justification.
4. To test your own location, enter its coordinates and tick **Place a new facility
   here**: the KPI cards compare the scenario against the baseline - unserved residents,
   mean distance to the nearest facility, and the new facility's market share.

### From code

```python
from sitetwin import recommend, simulate

recommend("Mladost", "pharmacy", k=3, radius_m=500)
# [{"lat": 42.65405, "lon": 23.37445, "score": 22342.0,
#   "reasons": ["22,342 residents without a pharmacy within 500 m",
#               "nearest existing pharmacy is 879 m away"]}, ...]

simulate("Mladost", "pharmacy", add=[(42.65405, 23.37445)])
# {"baseline": {...KPIs}, "scenario": {...KPIs}, "cells": DataFrame,
#  "facilities": DataFrame, "new_share": [0.238]}
```

## Model

| Part | Method |
|------|--------|
| Demand | Residents per grid cell. Target: estimated from cadastre building floor area, calibrated to census population. |
| Competition | Huff model: P(i -> j) = A_j * d_ij^-beta / sum_k A_k * d_ik^-beta, with beta = 2. |
| KPIs | Unserved residents within the service radius, resident-weighted mean distance to the nearest facility, residents per facility, market share per facility. |
| Recommendation | Greedy maximal coverage over candidate cells, O(k * n^2) for n cells. |

## Data sources

| Source | Used for |
|--------|----------|
| [OpenStreetMap](https://www.openstreetmap.org/) via [OSMnx](https://osmnx.readthedocs.io/) | Existing facilities, building footprints, street network |
| [Cadastre (KAIS)](https://kais.cadastre.bg/) | Buildings - floors, area, use - for the residential demand estimate |
| [NSI population grid](https://www.nsi.bg/) / [GHS-POP](https://human-settlement.emergency.copernicus.eu/) | Population to calibrate demand |
| [Sofia Urban Data](https://urbandata.sofia.bg/) / [Sofiaplan](https://sofiaplan.bg/api/) | Municipal GIS layers and district boundaries |
| [Sofia public transport GTFS](https://www.sofiatraffic.bg/bg/info-center/gtfs-danni) | Stops as a footfall proxy |

## Tech stack

- [Python 3.13](https://www.python.org/) with [NumPy](https://numpy.org/) and
  [pandas](https://pandas.pydata.org/) - the model core.
- [GeoPandas](https://geopandas.org/), [Shapely](https://shapely.readthedocs.io/),
  [OSMnx](https://osmnx.readthedocs.io/), [H3](https://h3geo.org/) - geospatial ingestion
  and the hexagonal grid.
- [PostgreSQL](https://www.postgresql.org/) + [PostGIS](https://postgis.net/) - spatial
  storage, via [SQLAlchemy](https://www.sqlalchemy.org/) and
  [GeoAlchemy2](https://geoalchemy-2.readthedocs.io/).
- [pygeoapi](https://pygeoapi.io/) - OGC API - Features service.
- [Streamlit](https://streamlit.io/) + [pydeck](https://deckgl.readthedocs.io/) - the
  interactive interface.
- [Docker Compose](https://docs.docker.com/compose/) - the full stack.
- [GitHub Actions](https://github.com/features/actions) - CI, CodeQL, security scans,
  Dependabot.
- [pytest](https://docs.pytest.org/) and [Ruff](https://docs.astral.sh/ruff/) - tests,
  lint and format.
