from dataclasses import dataclass
from geopandas import GeoDataFrame
from matplotlib.axes import Axes
import matplotlib.colors as mcolors
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from maptoposter.themes import Theme
from matplotlib import pyplot
from networkx import MultiDiGraph
import numpy
import osmnx
from shapely import Point
from typing import Tuple, cast

@dataclass
class PosterData:
    parks: GeoDataFrame | None
    water: GeoDataFrame | None
    roads: MultiDiGraph
    subways: GeoDataFrame | None
    trams: GeoDataFrame | None
    light_rails: GeoDataFrame | None
    trains: GeoDataFrame | None

@dataclass
class PosterConfig:
    title: str
    subtitle: str
    point: Tuple[float, float]
    radius: int
    theme: Theme

def plot(cfg: PosterConfig, data: PosterData) -> Figure:
    print("Rendering map...")
    fig, ax = _setup_canvas(cfg.theme)
    roads_proj = osmnx.projection.project_graph(data.roads)

    print("Drawing parks/green spaces...")
    _plot_polys_only(ax, data.parks, cfg.theme.parks, zorder=0)

    print("Drawing water...")
    _plot_polys_only(ax, data.water, cfg.theme.water, zorder=1)

    print("Drawing roads...")
    _plot_roads(ax, roads_proj, cfg.theme)

    print("Drawing train tracks...")
    _plot_edges(ax, data.trains, cfg.theme.train, linewidth=2, zorder=10)

    print("Drawing tram tracks...")
    _plot_edges(ax, data.trams, cfg.theme.tram, linewidth=2.5, zorder=11)

    print("Drawing light rail tracks...")
    _plot_edges(ax, data.light_rails, cfg.theme.light_rail, linewidth=2.5, zorder=12)

    print("Drawing subway tracks...")
    _plot_edges(ax, data.subways, cfg.theme.subway, linewidth=3, zorder=13)

    _crop_to_dimensions(ax, roads_proj, fig)

    print("Drawing overlay...")
    _draw_gradient(ax, cfg.theme.gradient_color, position="bottom", zorder=20)
    _draw_gradient(ax, cfg.theme.gradient_color, position="top", zorder=20)
    _draw_text(ax, "Roboto", cfg.title, cfg.subtitle, cfg.point, cfg.theme.text, 21)

    return fig


def _setup_canvas(theme: Theme) -> Tuple[Figure, Axes]:
    fig, ax = pyplot.subplots(figsize=(12, 16), facecolor=theme.bg)
    ax.set_facecolor(theme.bg)
    ax.set_position((0.0, 0.0, 1.0, 1.0))

    return fig, ax


def _plot_polys_only(ax: Axes, gdf: GeoDataFrame | None, color: str, zorder: int):
    if gdf is None:
        return

    polys = gdf.loc[gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]
    if polys.empty:
        return

    proj = osmnx.projection.project_gdf(polys)
    proj.plot(ax=ax, facecolor=color, edgecolor='none', zorder=zorder)


def _plot_edges(ax: Axes, gdf: GeoDataFrame | None, color: str, linewidth: float, zorder: int):
    if gdf is None or gdf.empty:
        return

    proj = osmnx.projection.project_gdf(gdf)
    proj.plot(ax=ax, facecolor='none', edgecolor=color, linewidth=linewidth, zorder=zorder)


def _plot_roads(ax: Axes, roads: MultiDiGraph, theme: Theme) -> None:
    edge_widths = []
    for _, _, data in roads.edges(data=True):
        highway = data.get('highway', 'unclassified')

        if isinstance(highway, list):
            highway = highway[0] if highway else 'unclassified'

        if highway in ['motorway', 'motorway_link']:
            width = 1.2
        elif highway in ['trunk', 'trunk_link', 'primary', 'primary_link']:
            width = 1.0
        elif highway in ['secondary', 'secondary_link']:
            width = 0.8
        elif highway in ['tertiary', 'tertiary_link']:
            width = 0.6
        else:
            width = 0.4

        edge_widths.append(width)

    osmnx.plot_graph(roads, ax=ax, node_size=0, bgcolor=theme.bg,
                     edge_color=theme.road, edge_linewidth=edge_widths,
                     show=False)


def _crop_to_dimensions(ax: Axes, roads_proj: MultiDiGraph, fig: Figure) -> None:

    # Compute node extents in projected coordinates
    xs = [data['x'] for _, data in roads_proj.nodes(data=True)]
    ys = [data['y'] for _, data in roads_proj.nodes(data=True)]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    x_range = maxx - minx
    y_range = maxy - miny

    fig_width, fig_height = fig.get_size_inches()
    desired_aspect = fig_width / fig_height
    current_aspect = x_range / y_range

    center_x = (minx + maxx) / 2
    center_y = (miny + maxy) / 2

    if current_aspect > desired_aspect:
        # Too wide, need to crop horizontally
        desired_x_range = y_range * desired_aspect
        new_minx = center_x - desired_x_range / 2
        new_maxx = center_x + desired_x_range / 2
        new_miny, new_maxy = miny, maxy
        crop_xlim = (new_minx, new_maxx)
        crop_ylim = (new_miny, new_maxy)
    elif current_aspect < desired_aspect:
        # Too tall, need to crop vertically
        desired_y_range = x_range / desired_aspect
        new_miny = center_y - desired_y_range / 2
        new_maxy = center_y + desired_y_range / 2
        new_minx, new_maxx = minx, maxx
        crop_xlim = (new_minx, new_maxx)
        crop_ylim = (new_miny, new_maxy)
    else:
        # Otherwise, keep original extents (no horizontal crop)
        crop_xlim = (minx, maxx)
        crop_ylim = (miny, maxy)

    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim(crop_xlim)
    ax.set_ylim(crop_ylim)


def _draw_gradient(ax: Axes, color: str, position: str, zorder: int) -> None:
    vals = numpy.linspace(0, 1, 256).reshape(-1, 1)
    gradient = numpy.hstack((vals, vals))

    rgb = mcolors.to_rgb(color)
    colors = numpy.zeros((256, 4))
    colors[:, 0] = rgb[0]
    colors[:, 1] = rgb[1]
    colors[:, 2] = rgb[2]
  
    if position == 'bottom':
        colors[:, 3] = numpy.linspace(1, 0, 256)
        extent_y_start = 0
        extent_y_end = 0.25
    else:
        colors[:, 3] = numpy.linspace(0, 1, 256)
        extent_y_start = 0.75
        extent_y_end = 1.0

    custom_cmap = mcolors.ListedColormap(colors)

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    y_range = ylim[1] - ylim[0]

    y_bottom = ylim[0] + y_range * extent_y_start
    y_top = ylim[0] + y_range * extent_y_end

    ax.imshow(gradient, extent=(xlim[0], xlim[1], y_bottom, y_top),
              aspect='auto', cmap=custom_cmap, zorder=zorder, origin='lower')


def _draw_text(ax: Axes, font_family: str, title: str, subtitle: str,
               point: Tuple[float, float], color: str, zorder: int) -> None:
    font_main = FontProperties(family=font_family, weight='bold', size=60)
    font_sub = FontProperties(family=font_family, weight='normal', size=22)
    font_coords = FontProperties(family=font_family, size=14)
    font_attributions = FontProperties(family=font_family, size=8)

    # Title
    title_spaced_letters = "  ".join(list(title.upper()))
    ax.text(x=0.5, y=0.14, s=title_spaced_letters, transform=ax.transAxes, color=color,
            ha='center', fontproperties=font_main, zorder=zorder)

    # Subtitle
    ax.text(x=0.5, y=0.10, s=subtitle.upper(), transform=ax.transAxes, color=color,
            ha='center', fontproperties=font_sub, zorder=zorder)

    # Coordinates
    lat, long = point
    lat_dir = "N" if lat >= 0 else "S"
    long_dir = "E" if long >= 0 else "W"
    coords = f"{abs(lat):.4f}° {lat_dir} / {abs(long):.4f}° {long_dir}"

    ax.text(x=0.5, y=0.07, s=coords, transform=ax.transAxes, color=color,
            alpha=0.7, ha='center', fontproperties=font_coords, zorder=zorder)

    ax.plot([0.4, 0.6], [0.125, 0.125], transform=ax.transAxes, color=color,
            linewidth=1, zorder=zorder)

    ax.text(x=0.98, y=0.02, s="© OpenStreetMap contributors",
            transform=ax.transAxes, color=color, alpha=0.7, ha='right',
            va='bottom', fontproperties=font_attributions, zorder=zorder)


