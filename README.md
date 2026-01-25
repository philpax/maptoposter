# City Map Poster Generator

***Fork of [originalankur/maptoposter](https://github.com/originalankur/maptoposter)***

Generate beautiful map posters with an emphasis on public transportation
for any city in the world.

![An example of the output of this programm using the city of Montréal and the autumn theme](examples/montréal_autumn.png)

## Installation

```bash
python -m venv .venv
source venv/bin/activate
pip install .
```

## Usage

```bash
python -m maptoposter -l <location> -t <title> -s <subtitle> -r <radius> -T <theme>
python -m maptoposter --list-themes
```

## Examples

```bash
python -m maptoposter -l "52.5170120, 13.3888222" -t Berlin -s Germany -r 10000 -T noir
```

![An example of the output using the city of Berlin and the noir theme](examples/berlin_noir.png)

```bash
python -m maptoposter -l "43.2961743, 5.3699525" -t Marseille -s France -r 8000 -T ocean
```

![An example of the output using the city of Marseille and the ocean theme](examples/marseille_ocean.png)

```bash
python -m maptoposter -l "45.50677, -73.59524" -t Montréal -s Québec -r 12000 -T autumn
```

![An example of the output using the city of Montréal and the autumn theme](examples/montréal_autumn.png)

```bash
python -m maptoposter -l "48.8534951, 2.3483915" -t Paris -s France -r 8000 -T emerald
```

![An example of the output using the city of Paris and the emerald theme](examples/paris_emerald.png)

```bash
python -m maptoposter -l "31.2074091, 121.4649932" -t Shanghai -s China -r 10000 -T forest
```

![An example of the output using the city of Shanghai and the forest theme](examples/shanghai_forest.png)

```bash
python -m maptoposter -t Tokyo -s Japan -r 12000 -T japanese_ink 
```

![An example of the output using the city of Tokyo and the japanes_ink theme](examples/tokyo_japanese_ink.png)

### Distance Guide

| Distance | Best for |
| -------- | -------- |
| 4000-6000m | Small/dense cities (Venice, Amsterdam center) |
| 8000-12000m | Medium cities, focused downtown (Paris, Barcelona) |
| 15000-20000m | Large metros, full city view (Tokyo, Mumbai) |

