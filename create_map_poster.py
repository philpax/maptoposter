from matplotlib.figure import Figure
from networkx import MultiDiGraph
import osmnx as ox
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import matplotlib.colors as mcolors
import numpy as np
from geopy.geocoders import Nominatim
from tqdm import tqdm
import time
import json
import os
from datetime import datetime
import argparse
from pathlib import Path
from hashlib import md5
import pickle
import asyncio
import sys

class CacheError(Exception):
    """Raised when a cache operation fails."""
    pass

CACHE_DIR_PATH = os.environ.get("CACHE_DIR", "cache")
CACHE_DIR = Path(CACHE_DIR_PATH)

CACHE_DIR.mkdir(exist_ok=True)

def cache_file(key: str) -> str:
    encoded = md5(key.encode()).hexdigest()
    return f"{encoded}.pkl"

def cache_get(name: str) -> dict | None:
    path = CACHE_DIR / cache_file(name)
    if path.exists():
        with path.open("rb") as f:
            return pickle.load(f)
    return None

def cache_set(name: str, obj) -> None:
    path = CACHE_DIR / cache_file(name)
    try:
        with path.open("wb") as f:
            pickle.dump(obj, f)
    except pickle.PickleError as e:
        raise CacheError(
            f"Serialization error while saving cache for '{name}': {e}"
        ) from e
    except (OSError, IOError) as e:
        raise CacheError(
            f"File error while saving cache for '{name}': {e}"
        ) from e

THEMES_DIR = "themes"
FONTS_DIR = "fonts"
POSTERS_DIR = "out"

def load_fonts():
    """
    Load Roboto fonts from the fonts directory.
    Returns dict with font paths for different weights.
    """
    fonts = {
        'bold': os.path.join(FONTS_DIR, 'Roboto-Bold.ttf'),
        'regular': os.path.join(FONTS_DIR, 'Roboto-Regular.ttf'),
        'light': os.path.join(FONTS_DIR, 'Roboto-Light.ttf')
    }

    # Verify fonts exist
    for _, path in fonts.items():
        if not os.path.exists(path):
            print(f"⚠ Font not found: {path}")
            return None

    return fonts

FONTS = load_fonts()

def generate_output_filename(city, theme_name):
    """
    Generate unique output filename with city, theme, and datetime.
    """
    if not os.path.exists(POSTERS_DIR):
        os.makedirs(POSTERS_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    city_slug = city.lower().replace(' ', '_')
    filename = f"{city_slug}_{theme_name}_{timestamp}.png"
    return os.path.join(POSTERS_DIR, filename)

def get_available_themes():
    """
    Scans the themes directory and returns a list of available theme names.
    """
    if not os.path.exists(THEMES_DIR):
        os.makedirs(THEMES_DIR)
        return []

    themes = []
    for file in sorted(os.listdir(THEMES_DIR)):
        if file.endswith('.json'):
            theme_name = file[:-5]  # Remove .json extension
            themes.append(theme_name)
    return themes

def load_theme(theme_name="feature_based"):
    """
    Load theme from JSON file in themes directory.
    """
    theme_file = os.path.join(THEMES_DIR, f"{theme_name}.json")

    if not os.path.exists(theme_file):
        print(f"⚠ Theme file '{theme_file}' not found. Using default feature_based theme.")
        # Fallback to embedded default theme
        return {
            "name": "Feature-Based Shading",
            "bg": "#FFFFFF",
            "text": "#000000",
            "gradient_color": "#FFFFFF",
            "water": "#C0C0C0",
            "parks": "#F0F0F0",
            "road_motorway": "#0A0A0A",
            "road_primary": "#1A1A1A",
            "road_secondary": "#2A2A2A",
            "road_tertiary": "#3A3A3A",
            "road_residential": "#4A4A4A",
            "road_default": "#3A3A3A"
        }

    with open(theme_file, 'r') as f:
        theme = json.load(f)
        print(f"✓ Loaded theme: {theme.get('name', theme_name)}")
        if 'description' in theme:
            print(f"  {theme['description']}")
        return theme

# Load theme (can be changed via command line or input)
THEME = dict[str, str]()  # Will be loaded later

def create_gradient_fade(ax, color, location='bottom', zorder=10):
    """
    Creates a fade effect at the top or bottom of the map.
    """
    vals = np.linspace(0, 1, 256).reshape(-1, 1)
    gradient = np.hstack((vals, vals))

    rgb = mcolors.to_rgb(color)
    my_colors = np.zeros((256, 4))
    my_colors[:, 0] = rgb[0]
    my_colors[:, 1] = rgb[1]
    my_colors[:, 2] = rgb[2]

    if location == 'bottom':
        my_colors[:, 3] = np.linspace(1, 0, 256)
        extent_y_start = 0
        extent_y_end = 0.25
    else:
        my_colors[:, 3] = np.linspace(0, 1, 256)
        extent_y_start = 0.75
        extent_y_end = 1.0

    custom_cmap = mcolors.ListedColormap(my_colors)

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    y_range = ylim[1] - ylim[0]

    y_bottom = ylim[0] + y_range * extent_y_start
    y_top = ylim[0] + y_range * extent_y_end

    ax.imshow(gradient, extent=[xlim[0], xlim[1], y_bottom, y_top], 
              aspect='auto', cmap=custom_cmap, zorder=zorder, origin='lower')

def get_edge_colors_by_type(G):
    """
    Assigns colors to edges based on road type hierarchy.
    Returns a list of colors corresponding to each edge in the graph.
    """
    edge_colors = []

    for _, _, data in G.edges(data=True):
        # Get the highway type (can be a list or string)
        highway = data.get('highway', 'unclassified')

        # Handle list of highway types (take the first one)
        if isinstance(highway, list):
            highway = highway[0] if highway else 'unclassified'

        # Assign color based on road type
        if highway in ['motorway', 'motorway_link']:
            color = THEME['road_motorway']
        elif highway in ['trunk', 'trunk_link', 'primary', 'primary_link']:
            color = THEME['road_primary']
        elif highway in ['secondary', 'secondary_link']:
            color = THEME['road_secondary']
        elif highway in ['tertiary', 'tertiary_link']:
            color = THEME['road_tertiary']
        elif highway in ['residential', 'living_street', 'unclassified']:
            color = THEME['road_residential']
        elif highway in ['cycleway']:
            color = THEME['bike_path']
        else:
            color = THEME['road_default']

        edge_colors.append(color)

    return edge_colors

def get_edge_widths_by_type(G):
    """
    Assigns line widths to edges based on road type.
    Major roads get thicker lines.
    """
    edge_widths = []

    for _, _, data in G.edges(data=True):
        highway = data.get('highway', 'unclassified')

        if isinstance(highway, list):
            highway = highway[0] if highway else 'unclassified'

        # Assign width based on road importance
        if highway in ['motorway', 'motorway_link']:
            width = 1.2
        elif highway in ['trunk', 'trunk_link', 'primary', 'primary_link', 'cycleway']:
            width = 1.0
        elif highway in ['secondary', 'secondary_link']:
            width = 0.8
        elif highway in ['tertiary', 'tertiary_link']:
            width = 0.6
        else:
            width = 0.4

        edge_widths.append(width)

    return edge_widths

def get_coordinates(search_term):
    """
    Fetches coordinates for a given city and country using geopy.
    Includes rate limiting to be respectful to the geocoding service.
    """
    coords = f"coords_{search_term}"
    cached = cache_get(coords)
    if cached:
        print(f"✓ Using cached coordinates for {search_term}")
        return cached

    print("Looking up coordinates...")
    geolocator = Nominatim(user_agent="city_map_poster")

    # Add a small delay to respect Nominatim's usage policy
    time.sleep(1)

    location = geolocator.geocode(search_term)

    # If geocode returned a coroutine in some environments, run it to get the result.
    if asyncio.iscoroutine(location):
        try:
            location = asyncio.run(location)
        except RuntimeError:
            # If an event loop is already running, try using it to complete the coroutine.
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Running event loop in the same thread; raise a clear error.
                raise RuntimeError("Geocoder returned a coroutine while an event loop is already running. Run this script in a synchronous environment.")
            location = loop.run_until_complete(location)

    if location:
        # Use getattr to safely access address (helps static analyzers)
        addr = getattr(location, "address", None)
        if addr:
            print(f"✓ Found: {addr}")
        else:
            print("✓ Found location (address not available)")
        print(f"✓ Coordinates: {location.latitude}, {location.longitude}")
        try:
            cache_set(coords, (location.latitude, location.longitude))
        except CacheError as e:
            print(e)
        return (location.latitude, location.longitude)
    else:
        raise ValueError(f"Could not find coordinates for {search_term}")

def get_crop_limits(G: MultiDiGraph, fig: Figure) -> tuple[tuple[float, float], tuple[float, float]]:
    """
    Determine cropping limits to maintain aspect ratio of the figure.

    This function calculates the extents of the graph's nodes and adjusts
    the x and y limits to match the aspect ratio of the provided figure.

    :param G: The graph to be plotted
    :type G: MultiDiGraph
    :param fig: The matplotlib figure object
    :type fig: Figure
    :return: Tuple of x and y limits for cropping
    :rtype: tuple[tuple[float, float], tuple[float, float]]
    """
    # Compute node extents in projected coordinates
    xs = [data['x'] for _, data in G.nodes(data=True)]
    ys = [data['y'] for _, data in G.nodes(data=True)]
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

    return crop_xlim, crop_ylim

def fetch_graph(point, radius):
    lat, lon = point
    graph = f"graph_{lat}_{lon}_{radius}"
    cached = cache_get(graph)
    if cached is not None:
        print("✓ Using cached street network")
        return cached

    try:
        G = ox.graph_from_point(point, dist=radius, dist_type='bbox', network_type='all')
        # Rate limit between requests
        time.sleep(0.5)
        try:
            cache_set(graph, G)
        except CacheError as e:
            print(e)
        return G
    except Exception as e:
        print(f"OSMnx error while fetching graph: {e}")
        return None

def fetch_features(point, dist, tags, name):
    lat, lon = point
    tag_str = "_".join(tags.keys())
    features = f"{name}_{lat}_{lon}_{dist}_{tag_str}"
    cached = cache_get(features)
    if cached is not None:
        print(f"✓ Using cached {name}")
        return cached

    try:
        data = ox.features_from_point(point, tags=tags, dist=dist)
        # Rate limit between requests
        time.sleep(0.3)
        try:
            cache_set(features, data)
        except CacheError as e:
            print(e)
        return data

    except Exception as e:
        print(f"OSMnx error while fetching features: {e}")
        return None

def create_poster(title, subtitle, point, radius, output_file):
    print(f"\nGenerating map for {title}, {subtitle}...")

    # Progress bar for data fetching
    with tqdm(total=3, desc="Fetching map data", unit="step", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
        # 1. Fetch Street Network
        pbar.set_description("Downloading street network")
        G = fetch_graph(point, radius)
        pbar.update(1)

        # 2. Fetch Water Features
        pbar.set_description("Downloading water features")
        water = fetch_features(point, radius, {'natural': 'water', 'waterway': 'riverbank'}, 'water')
        pbar.update(1)

        # 3. Fetch Parks
        pbar.set_description("Downloading parks/green spaces")
        parks = fetch_features(
            point,
            radius,
            {
                'leisure': 'park',
                'landuse': ['grass', 'cemetery'],
                'natural': 'wood'
            },
            'parks'
        )
        pbar.update(1)

    print("✓ All data retrieved successfully!")

    # 2. Setup Plot
    print("Rendering map...")
    fig, ax = plt.subplots(figsize=(12, 16), facecolor=THEME['bg'])
    ax.set_facecolor(THEME['bg'])
    ax.set_position((0.0, 0.0, 1.0, 1.0))

    # Project graph to a metric CRS so distances and aspect are linear (meters)
    G_proj = ox.project_graph(G)

    # 3. Plot Layers
    # Layer 1: Polygons
    if water is not None and not water.empty:
        water_polys = water[water.geometry.type.isin(['Polygon', 'MultiPolygon'])]
        if not water_polys.empty:
            try:
                # Project water features in the same CRS as the graph
                water_polys = ox.projection.project_gdf(water_polys)
            except Exception:
                water_polys = water_polys.to_crs(G_proj.graph['crs'])

            water_polys.plot(ax=ax, facecolor=THEME['water'], edgecolor='none', zorder=1)

    if parks is not None and not parks.empty:
        park_polys = parks[parks.geometry.type.isin(['Polygon', 'MultiPolygon'])]
        if not park_polys.empty:
            try:
                # Project park features in the same CRS as the graph
                park_polys = ox.projection.project_gdf(park_polys)
            except Exception:
                park_polys = park_polys.to_crs(G_proj.graph['crs'])

            park_polys.plot(ax=ax, facecolor=THEME['parks'], edgecolor='none', zorder=0)

    # Layer 2: Roads with hierarchy coloring
    print("Applying road hierarchy colors...")
    edge_colors = get_edge_colors_by_type(G_proj)
    edge_widths = get_edge_widths_by_type(G_proj)

    # Determine cropping limits to maintain the poster aspect ratio
    crop_xlim, crop_ylim = get_crop_limits(G_proj, fig)

    # Plot the projected graph and then apply the cropped limits
    ox.plot_graph(
        G_proj, ax=ax, bgcolor=THEME['bg'],
        node_size=0,
        edge_color=edge_colors,
        edge_linewidth=edge_widths,
        show=False, close=False
    )
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlim(crop_xlim)
    ax.set_ylim(crop_ylim)

    # Layer 3: Gradients (Top and Bottom)
    create_gradient_fade(ax, THEME['gradient_color'], location='bottom', zorder=10)
    create_gradient_fade(ax, THEME['gradient_color'], location='top', zorder=10)

    # 4. Typography using Roboto font
    if FONTS:
        font_main = FontProperties(fname=FONTS['bold'], size=60)
        font_sub = FontProperties(fname=FONTS['light'], size=22)
        font_coords = FontProperties(fname=FONTS['regular'], size=14)
    else:
        # Fallback to system fonts
        font_main = FontProperties(family='monospace', weight='bold', size=60)
        font_sub = FontProperties(family='monospace', weight='normal', size=22)
        font_coords = FontProperties(family='monospace', size=14)

    spaced_city = "  ".join(list(title.upper()))

    # --- BOTTOM TEXT ---
    ax.text(0.5, 0.14, spaced_city, transform=ax.transAxes,
            color=THEME['text'], ha='center', fontproperties=font_main, zorder=11)

    ax.text(0.5, 0.10, subtitle.upper(), transform=ax.transAxes,
            color=THEME['text'], ha='center', fontproperties=font_sub, zorder=11)

    lat, lon = point
    coords = f"{lat:.4f}° N / {lon:.4f}° E" if lat >= 0 else f"{abs(lat):.4f}° S / {lon:.4f}° E"
    if lon < 0:
        coords = coords.replace("E", "W")

    ax.text(0.5, 0.07, coords, transform=ax.transAxes,
            color=THEME['text'], alpha=0.7, ha='center', fontproperties=font_coords, zorder=11)

    ax.plot([0.4, 0.6], [0.125, 0.125], transform=ax.transAxes, 
            color=THEME['text'], linewidth=1, zorder=11)

    # --- ATTRIBUTION (bottom right) ---
    if FONTS:
        font_attr = FontProperties(fname=FONTS['light'], size=8)
    else:
        font_attr = FontProperties(family='monospace', size=8)

    ax.text(0.98, 0.02, "© OpenStreetMap contributors", transform=ax.transAxes,
            color=THEME['text'], alpha=0.5, ha='right', va='bottom', 
            fontproperties=font_attr, zorder=11)

    # 5. Save
    print(f"Saving to {output_file}...")
    plt.savefig(output_file, dpi=300, facecolor=THEME['bg'])
    plt.close()
    print(f"✓ Done! Poster saved as {output_file}")

def print_examples():
    """Print usage examples."""
    print("""
City Map Poster Generator
=========================

Usage:
  python create_map_poster.py --t <title> --s <subtitle> [options]

Examples:
  # Infer location from title and subtitle
  python create_map_poster.py -t "Montréal" -s "Canada" -t gruvbox-light -r 10000

  # Specify exact location
  python create_map_poster.py -l "45.50941, -73.59758" -t Québec -s Canada -t noir -r 8000

  # List themes
  python create_map_poster.py --list-themes

Options:
  --title, -t       Title to print ton the poster (required)
  --subtitle, -s    Subtitle to print on the poster (required)
  --location, -l    Location to print on the poster
  --theme, -t       Theme name (default: feature_based)
  --radius, -r      Map radius in meters (default: 10000)
  --list-themes     List all available themes

Distance guide:
  4000-6000m   Small/dense cities (Venice, Amsterdam old center)
  8000-12000m  Medium cities, focused downtown (Paris, Barcelona)
  15000-20000m Large metros, full city view (Tokyo, Mumbai)

Available themes can be found in the 'themes/' directory.
Example posters can be found in the 'posters/' directory.
Generated posters are saved to 'out/' directory.
""")

def list_themes():
    """List all available themes with descriptions."""
    available_themes = get_available_themes()
    if not available_themes:
        print("No themes found in 'themes/' directory.")
        return

    print("\nAvailable Themes:")
    print("-" * 60)
    for theme_name in available_themes:
        theme_path = os.path.join(THEMES_DIR, f"{theme_name}.json")
        try:
            with open(theme_path, 'r') as f:
                theme_data = json.load(f)
                display_name = theme_data.get('name', theme_name)
                description = theme_data.get('description', '')
        except:
            display_name = theme_name
            description = ''
        print(f"  {theme_name}")
        print(f"    {display_name}")
        if description:
            print(f"    {description}")
        print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate beautiful map posters for any city",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python create_map_poster.py -t "Montréal" -s "Canada" -t gruvbox-light -r 10000
  python create_map_poster.py -l "45.50941, -73.59758" -t Québec -s Canada -t noir -r 8000
  python create_map_poster.py --list-themes
        """
    )

    parser.add_argument('--location', '-l', type=str, help='Location (will be inferred from title and subtitle if not specified)')
    parser.add_argument('--radius', '-r', type=int, default=10000, help='Map radius in meters')
    parser.add_argument('--title', '-t', type=str, help='Title to write on the poster')
    parser.add_argument('--subtitle', '-s', type=str, help='Subtitle to write on the poster')
    parser.add_argument('--theme', '-T', type=str, default='feature_based', help='Theme name (default: feature_based)')
    parser.add_argument('--list-themes', action='store_true', help='List all available themes')

    args = parser.parse_args()

    # If no arguments provided, show examples
    if len(sys.argv) == 1:
        print_examples()
        sys.exit(0)

    # List themes if requested
    if args.list_themes:
        list_themes()
        sys.exit(0)

    # Validate required arguments
    if not args.title or not args.subtitle:
        print("Error: --title and --subtitle are required.\n")
        print_examples()
        sys.exit(1)

    location = args.location
    if not args.location:
        location = f"{args.title}, {args.subtitle}"

    # Validate theme exists
    available_themes = get_available_themes()
    if args.theme not in available_themes:
        print(f"Error: Theme '{args.theme}' not found.")
        print(f"Available themes: {', '.join(available_themes)}")
        sys.exit(1)

    print("=" * 50)
    print("City Map Poster Generator")
    print("=" * 50)

    # Load theme
    THEME = load_theme(args.theme)

    # Get coordinates and generate poster
    try:
        coords = get_coordinates(location)
        output_file = generate_output_filename(args.title, args.theme)
        create_poster(args.title, args.subtitle, coords, args.radius, output_file)

        print("\n" + "=" * 50)
        print("✓ Poster generation complete!")
        print("=" * 50)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
