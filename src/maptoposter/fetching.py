from typing import Callable, Any, Tuple
from geopandas import GeoDataFrame
from networkx import MultiDiGraph
from maptoposter import cache
from maptoposter.poster import PosterData
import osmnx

def fetch_point(search_term: str) -> Tuple[float, float]:
    return _cached_fetch(f"location_{search_term}",
                         lambda: osmnx.geocode(search_term))

def fetch_data(point: Tuple[float, float], radius: int) -> PosterData:
    print("Retrieving parks/green spaces...")
    parks = _fetch_features(
        point,
        radius,
        {
            'leisure': 'park',
            'landuse': ['grass', 'cemetery'],
            'natural': 'wood'
        },
        'parks'
    )

    print("Retrieving water features...")
    water = _fetch_features(point, radius, {'natural': 'water', 'waterway': 'riverbank'}, 'water')

    print("Retrieving roads...")
    roads = _fetch_roads(point, radius)

    print("Retrieving train network...")
    trains = _fetch_features(point, radius, {'railway': 'rail'}, 'rail')

    print("Retrieving tram network...")
    trams = _fetch_features(point, radius, {'railway': 'tram'}, 'tram')

    print("Retrieving light rail network...")
    light_rails = _fetch_features(point, radius, {'railway': 'light_rail'}, 'light_rail')

    print("Retrieving subway network...")
    subways = _fetch_features(point, radius, {'railway': 'subway'}, 'subway')

    return PosterData(parks, water, roads, subways, trams, light_rails, trains)


def _fetch_roads(point: Tuple[float, float], radius: int) -> MultiDiGraph:
    lat, lon = point
    key = f"roads_{lat}_{lon}_{radius}"
    return _cached_fetch(key, lambda: osmnx.graph_from_point(point, dist=radius,
                                                          dist_type='bbox',
                                                          network_type='all'))


def _fetch_features(point: Tuple[float, float], radius: int,
                   tags: dict[str, bool | str | list[str]],
                    name: str) -> GeoDataFrame | None :
    lat, lon = point
    key = f"{name}_{lat}_{lon}_{radius}"
    return _cached_fetch(key, lambda: osmnx.features_from_point(point, tags, radius))


def _cached_fetch(key: str, fetch_fn: Callable[[], Any]) -> Any:
    cached = cache.get(key)
    if cached is not None:
        print(f"✓ Using cached {key}")
        return cached

    try:
        result = fetch_fn()
        cache.set(key, result)
        return result
    except cache.CacheError as e:
        print(e)
        return None
    except Exception as e:
        print(f"OSMnx error while fetching {key}: {e}")
        return None
