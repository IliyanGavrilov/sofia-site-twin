"""OpenStreetMap ingestion: existing facilities (points of interest) for a place."""

OSM_TAGS = {
    "pharmacy": {"amenity": "pharmacy"},
    "supermarket": {"shop": ["supermarket", "convenience"]},
    "kindergarten": {"amenity": "kindergarten"},
}


def fetch_facilities(place: str, facility_type: str):
    """Facilities of one type in ``place`` (e.g. ``"Mladost, Sofia, Bulgaria"``) as a
    GeoDataFrame of points in EPSG:4326 with ``type, name, source`` columns.

    Polygons (a shop mapped as a building outline) are reduced to their centroid.
    """
    import osmnx as ox  # imported lazily: the model and its tests do not need the GIS stack

    gdf = ox.features_from_place(place, tags=OSM_TAGS[facility_type])
    projected = gdf.to_crs(gdf.estimate_utm_crs())
    gdf["geometry"] = projected.geometry.centroid.to_crs(4326)
    gdf["type"] = facility_type
    gdf["name"] = gdf["name"] if "name" in gdf else None
    gdf["source"] = "osm"
    return gdf[["geometry", "type", "name", "source"]].reset_index(drop=True)
