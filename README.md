# City Map Poster Generator

***Fork of [originalankur/maptoposter](https://github.com/originalankur/maptoposter)***

Generate beautiful map posters with an emphasis on public transportation
for any city in the world.

## Installation

NixOS users can use the provided `shell.nix` to pull in the required C++ stdlib.

## Usage

[uv](https://docs.astral.sh/uv/) is a fast Python package manager that handles dependencies and virtual environments automatically.

```bash
uv run src/maptoposter/__main__.py -l <location> -t <title> -s <subtitle> -r <radius> -T <theme>
uv run src/maptoposter/__main__.py --list-themes
uv run src/maptoposter/__main__.py --help
```

### Font

Use `-f` / `--font` to specify a font family name or path to a font file (.ttf, .otf). The default font is Roboto.

### Size

Use `-S` / `--size` to select a predefined print size, or specify custom dimensions:

```bash
# Predefined sizes
uv run src/maptoposter/__main__.py --size 4x6 ...   # 4x6" postcard
uv run src/maptoposter/__main__.py --size a4 ...    # A4 paper
uv run src/maptoposter/__main__.py --size letter ...

# Custom sizes
uv run src/maptoposter/__main__.py --size-inches 8x12 ...
uv run src/maptoposter/__main__.py --size-cm 20x30 ...

# List all predefined sizes
uv run src/maptoposter/__main__.py --list-sizes
```

**Available predefined sizes:**

| Category | Sizes |
| -------- | ----- |
| Photo/Poster | 4x6, 5x7, 8x10, 11x14, 12x16 (default), 16x20, 18x24, 24x36 |
| US Paper | letter (8.5x11), legal (8.5x14), tabloid (11x17) |
| ISO A-series | a6, a5, a4, a3, a2, a1, a0 |

Custom sizes must be portrait orientation (height > width) with an aspect ratio between 1:1 and 1:2.

### DPI

Use `--dpi` to set the output resolution (default: 300). Higher values produce larger files with more detail.

```bash
uv run src/maptoposter/__main__.py --dpi 150 ...  # draft quality
uv run src/maptoposter/__main__.py --dpi 300 ...  # print quality (default)
uv run src/maptoposter/__main__.py --dpi 600 ...  # high quality
```

### Output

Use `-o` / `--output` to specify the output path as a template string. Available placeholders:

| Placeholder | Description |
|-------------|-------------|
| `{timestamp}` | Current time (YYYY_MM_DD_HH_MM_SS) |
| `{title}` | Poster title |
| `{subtitle}` | Poster subtitle |
| `{theme}` | Theme name |
| `{size}` | Print size (e.g., 12x16) |
| `{dpi}` | Output DPI |

Default: `out/{timestamp}_{title}_{theme}.png`

```bash
uv run src/maptoposter/__main__.py -o "posters/{title}_{size}.png" ...
uv run src/maptoposter/__main__.py -o "{title}_{theme}_{dpi}dpi.png" ...
```

## Examples

| Command | Result |
| ------- | ------ |
| `uv run src/maptoposter/__main__.py -l "52.5170120, 13.3888222" -t Berlin -s Germany -r 10000 -T noir` | <img src="examples/berlin_noir.png" alt="An example of the output using the city of Berlin and the noir theme" width="250"> |
| `uv run src/maptoposter/__main__.py -l "43.2961743, 5.3699525" -t Marseille -s France -r 8000 -T ocean` | <img src="examples/marseille_ocean.png" alt="An example of the output using the city of Marseille and the ocean theme" width="250"> |
| `uv run src/maptoposter/__main__.py -l "45.50677, -73.59524" -t Montréal -s Québec -r 12000 -T autumn` | <img src="examples/montréal_autumn.png" alt="An example of the output using the city of Montréal and the autumn theme" width="250"> |
| `uv run src/maptoposter/__main__.py -l "48.8534951, 2.3483915" -t Paris -s France -r 8000 -T emerald` | <img src="examples/paris_emerald.png" alt="An example of the output using the city of Paris and the emerald theme" width="250"> |
| `uv run src/maptoposter/__main__.py -l "31.2074091, 121.4649932" -t Shanghai -s China -r 10000 -T forest` | <img src="examples/shanghai_forest.png" alt="An example of the output using the city of Shanghai and the forest theme" width="250"> |
| `uv run src/maptoposter/__main__.py -t Tokyo -s Japan -r 12000 -T japanese_ink` | <img src="examples/tokyo_japanese_ink.png" alt="An example of the output using the city of Tokyo and the japanese_ink theme" width="250"> |


### Distance Guide

| Distance | Best for |
| -------- | -------- |
| 4000-6000m | Small/dense cities (Venice, Amsterdam center) |
| 8000-12000m | Medium cities, focused downtown (Paris, Barcelona) |
| 15000-20000m | Large metros, full city view (Tokyo, Mumbai) |

