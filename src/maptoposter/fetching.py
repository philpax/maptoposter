from typing import Tuple
from maptoposter.poster import PosterData
import osmnx


def fetch_point(search_term: str) -> Tuple[float, float]:
    return osmnx.geocode(search_term)


def fetch_data(point: Tuple[float, float], radius: int) -> PosterData:
    print("Retrieving parks/green spaces...")
    parks = osmnx.features_from_point(
        point,
        {"leisure": "park", "landuse": ["grass", "cemetery"], "natural": "wood"},
        radius,
    )

    print("Retrieving water features...")
    water = osmnx.features_from_point(
        point, {"natural": ["water", "bay"], "waterway": "riverbank"}, radius
    )

    print("Retrieving roads...")
    roads = osmnx.graph_from_point(
        point,
        dist=radius,
        dist_type="bbox",
        network_type="all",
        truncate_by_edge=True,
    )

    print("Retrieving train network...")
    trains = osmnx.features_from_point(point, {"railway": "rail"}, radius)

    print("Retrieving tram network...")
    trams = osmnx.features_from_point(point, {"railway": "tram"}, radius)

    print("Retrieving light rail network...")
    light_rails = osmnx.features_from_point(point, {"railway": "light_rail"}, radius)

    print("Retrieving subway network...")
    subways = osmnx.features_from_point(point, {"railway": "subway"}, radius)

    return PosterData(parks, water, roads, subways, trams, light_rails, trains)
