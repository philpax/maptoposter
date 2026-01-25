from typing import Tuple

from rich.console import Console
from maptoposter.poster import PosterData
import osmnx


def fetch_point(search_term: str) -> Tuple[float, float]:
    return osmnx.geocode(search_term)


def fetch_data(console: Console, point: Tuple[float, float], radius: int) -> PosterData:
    console.print("Retrieving [bold green]parks/green spaces[/bold green]")
    parks = _fetch_features(
        point,
        {"leisure": "park", "landuse": ["grass", "cemetery"], "natural": "wood"},
        radius,
    )

    console.print("Retrieving [bold blue]water[/bold blue]")
    water = _fetch_features(
        point, {"natural": ["water", "bay", "strait"], "waterway": "riverbank"}, radius
    )

    console.print("Retrieving [bold yellow]roads[/bold yellow]")
    roads = osmnx.graph_from_point(
        point,
        dist=radius,
        dist_type="bbox",
        network_type="all",
        truncate_by_edge=True,
    )

    console.print("Retrieving [bold magenta]train tracks[/bold magenta]")
    trains = _fetch_features(point, {"railway": "rail"}, radius)

    console.print("Retrieving [bold magenta]tram tracks[/bold magenta]")
    trams = _fetch_features(point, {"railway": "tram"}, radius)

    console.print("Retrieving [bold magenta]light rail tracks[/bold magenta]")
    light_rails = _fetch_features(point, {"railway": "light_rail"}, radius)

    console.print("Retrieving [bold magenta]subway tracks[/bold magenta]")
    subways = _fetch_features(point, {"railway": "subway"}, radius)

    return PosterData(parks, water, roads, subways, trams, light_rails, trains)


def _fetch_features(
    point: Tuple[float, float], tags: dict[str, bool | str | list[str]], radius: int
):
    try:
        return osmnx.features_from_point(point, tags, radius)
    except Exception:
        return None
