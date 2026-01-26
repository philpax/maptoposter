from dataclasses import dataclass
import os.path
from geopandas import GeoDataFrame
from matplotlib.axes import Axes
import matplotlib.colors as mcolors
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from rich.console import Console
from maptoposter.themes import Theme
from matplotlib import pyplot
from networkx import MultiDiGraph
import numpy
import osmnx
from shapely import Point
from typing import Tuple, cast

# Print sizes in portrait orientation (width x height in inches)
# Organized by category for display purposes
PRINT_SIZE_CATEGORIES = {
    "Photo/Poster sizes": {
        "4x6": (4, 6),
        "5x7": (5, 7),
        "8x10": (8, 10),
        "11x14": (11, 14),
        "12x16": (12, 16),
        "16x20": (16, 20),
        "18x24": (18, 24),
        "24x36": (24, 36),
    },
    "US paper sizes": {
        "letter": (8.5, 11),
        "legal": (8.5, 14),
        "tabloid": (11, 17),
    },
    "ISO A-series": {
        "a6": (4.1, 5.8),
        "a5": (5.8, 8.3),
        "a4": (8.3, 11.7),
        "a3": (11.7, 16.5),
        "a2": (16.5, 23.4),
        "a1": (23.4, 33.1),
        "a0": (33.1, 46.8),
    },
}

# Flattened dict for lookup
PRINT_SIZES = {
    name: size
    for sizes in PRINT_SIZE_CATEGORIES.values()
    for name, size in sizes.items()
}


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


def plot(
    console: Console,
    cfg: PosterConfig,
    data: PosterData,
    font: str,
    size: Tuple[float, float] = (12, 16),
) -> Figure:
    console.print("Setting up canvas")
    fig, ax = _setup_canvas(cfg.theme, size)
    roads_proj = osmnx.projection.project_graph(data.roads)

    console.print("Drawing [bold green]parks/green spaces[/bold green]")
    _plot_polys_only(ax, data.parks, cfg.theme.parks, zorder=0)

    console.print("Drawing [bold blue]water[/bold blue]")
    _plot_polys_only(ax, data.water, cfg.theme.water, zorder=1)

    console.print("Drawing [bold yellow]roads[/bold yellow]")
    _plot_roads(ax, roads_proj, cfg.theme)

    console.print("Drawing [bold magenta]train tracks[/bold magenta]")
    _plot_edges(ax, data.trains, cfg.theme.train, linewidth=2, zorder=10)

    console.print("Drawing [bold magenta]tram tracks[/bold magenta]")
    _plot_edges(ax, data.trams, cfg.theme.tram, linewidth=2.5, zorder=11)

    console.print("Drawing [bold magenta]light rail tracks[/bold magenta]")
    _plot_edges(ax, data.light_rails, cfg.theme.light_rail, linewidth=2.5, zorder=12)

    console.print("Drawing [bold magenta]subway tracks[/bold magenta]")
    _plot_edges(ax, data.subways, cfg.theme.subway, linewidth=3, zorder=13)

    _crop_to_dimensions(ax, cfg.point, cfg.radius, roads_proj, fig)

    console.print("Drawing [bold]overlay[/bold]")
    _draw_gradient(ax, cfg.theme.gradient_color, position="bottom", zorder=20)
    _draw_gradient(ax, cfg.theme.gradient_color, position="top", zorder=20)
    _draw_text(ax, font, cfg.title, cfg.subtitle, cfg.point, cfg.theme.text, 21, size)

    return fig


def _setup_canvas(theme: Theme, size: Tuple[float, float]) -> Tuple[Figure, Axes]:
    fig, ax = pyplot.subplots(figsize=size, facecolor=theme.bg)
    ax.set_facecolor(theme.bg)
    ax.set_position((0.0, 0.0, 1.0, 1.0))

    return fig, ax


def _plot_polys_only(ax: Axes, gdf: GeoDataFrame | None, color: str, zorder: int):
    if gdf is None:
        return

    polys = gdf.loc[gdf.geometry.type.isin(["Polygon", "MultiPolygon"])]
    if polys.empty:
        return

    proj = osmnx.projection.project_gdf(polys)
    proj.plot(ax=ax, facecolor=color, edgecolor="none", zorder=zorder)


def _plot_edges(
    ax: Axes, gdf: GeoDataFrame | None, color: str, linewidth: float, zorder: int
):
    if gdf is None or gdf.empty:
        return

    proj = osmnx.projection.project_gdf(gdf)
    proj.plot(
        ax=ax, facecolor="none", edgecolor=color, linewidth=linewidth, zorder=zorder
    )


def _plot_roads(ax: Axes, roads: MultiDiGraph, theme: Theme) -> None:
    edge_widths = []
    for _, _, data in roads.edges(data=True):
        highway = data.get("highway", "unclassified")

        if isinstance(highway, list):
            highway = highway[0] if highway else "unclassified"

        if highway in ["motorway", "motorway_link"]:
            width = 1.2
        elif highway in ["trunk", "trunk_link", "primary", "primary_link"]:
            width = 1.0
        elif highway in ["secondary", "secondary_link"]:
            width = 0.8
        elif highway in ["tertiary", "tertiary_link"]:
            width = 0.6
        else:
            width = 0.4

        edge_widths.append(width)

    osmnx.plot_graph(
        roads,
        ax=ax,
        node_size=0,
        bgcolor=theme.bg,
        edge_color=theme.road,
        edge_linewidth=edge_widths,
        show=False,
    )


def _crop_to_dimensions(
    ax: Axes,
    point: Tuple[float, float],
    radius: int,
    roads_proj: MultiDiGraph,
    fig: Figure,
) -> None:
    lat, lon = point

    proj, _ = osmnx.projection.project_geometry(
        Point(lon, lat), crs="EPSG:4326", to_crs=roads_proj.graph["crs"]
    )
    center = cast(Point, proj)
    center_x, center_y = center.x, center.y

    fig_width, fig_height = fig.get_size_inches()
    aspect = fig_width / fig_height

    # Start from the *requested* radius
    half_x = radius
    half_y = radius

    # Cut inward to match aspect
    if aspect > 1:  # landscape → reduce height
        half_y = half_x / aspect
    else:  # portrait → reduce width
        half_x = half_y * aspect

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(center_x - half_x, center_x + half_x)
    ax.set_ylim(center_y - half_y, center_y + half_y)


def _draw_gradient(ax: Axes, color: str, position: str, zorder: int) -> None:
    vals = numpy.linspace(0, 1, 256).reshape(-1, 1)
    gradient = numpy.hstack((vals, vals))

    rgb = mcolors.to_rgb(color)
    colors = numpy.zeros((256, 4))
    colors[:, 0] = rgb[0]
    colors[:, 1] = rgb[1]
    colors[:, 2] = rgb[2]

    if position == "bottom":
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

    ax.imshow(
        gradient,
        extent=(xlim[0], xlim[1], y_bottom, y_top),
        aspect="auto",
        cmap=custom_cmap,
        zorder=zorder,
        origin="lower",
    )


def _draw_text(
    ax: Axes,
    font: str,
    title: str,
    subtitle: str,
    point: Tuple[float, float],
    color: str,
    zorder: int,
    fig_size: Tuple[float, float],
) -> None:
    fig_width, fig_height = fig_size
    # Scale fonts based on figure height relative to 16" baseline
    scale = fig_height / 16.0
    size_main = 60 * scale
    size_sub = 22 * scale
    size_coords = 14 * scale
    size_attribution = 8 * scale
    line_width = 1 * scale

    # Check if font is a file path or a font family name
    is_font_file = os.path.splitext(font)[1] and os.path.isfile(font)
    if is_font_file:
        font_main = FontProperties(fname=font, weight="bold", size=size_main)
        font_sub = FontProperties(fname=font, weight="normal", size=size_sub)
        font_coords = FontProperties(fname=font, size=size_coords)
        font_attributions = FontProperties(fname=font, size=size_attribution)
    else:
        font_main = FontProperties(family=font, weight="bold", size=size_main)
        font_sub = FontProperties(family=font, weight="normal", size=size_sub)
        font_coords = FontProperties(family=font, size=size_coords)
        font_attributions = FontProperties(family=font, size=size_attribution)

    # Title (scale letter spacing based on aspect ratio: narrower = fewer spaces)
    # At aspect 0.75 (12x16 baseline): 2 spaces; narrower (<0.7): 1 space
    aspect = fig_width / fig_height
    num_spaces = max(1, round(4 * aspect - 1.2))
    title_spaced_letters = (" " * num_spaces).join(list(title.upper()))
    ax.text(
        x=0.5,
        y=0.14,
        s=title_spaced_letters,
        transform=ax.transAxes,
        color=color,
        ha="center",
        fontproperties=font_main,
        zorder=zorder,
    )

    # Subtitle
    ax.text(
        x=0.5,
        y=0.10,
        s=subtitle.upper(),
        transform=ax.transAxes,
        color=color,
        ha="center",
        fontproperties=font_sub,
        zorder=zorder,
    )

    # Coordinates
    lat, long = point
    lat_dir = "N" if lat >= 0 else "S"
    long_dir = "E" if long >= 0 else "W"
    coords = f"{abs(lat):.4f}° {lat_dir} / {abs(long):.4f}° {long_dir}"

    ax.text(
        x=0.5,
        y=0.07,
        s=coords,
        transform=ax.transAxes,
        color=color,
        alpha=0.7,
        ha="center",
        fontproperties=font_coords,
        zorder=zorder,
    )

    ax.plot(
        [0.4, 0.6],
        [0.125, 0.125],
        transform=ax.transAxes,
        color=color,
        linewidth=line_width,
        zorder=zorder,
    )

    ax.text(
        x=0.98,
        y=0.02,
        s="© OpenStreetMap contributors",
        transform=ax.transAxes,
        color=color,
        alpha=0.7,
        ha="right",
        va="bottom",
        fontproperties=font_attributions,
        zorder=zorder,
    )
