from dataclasses import dataclass
import os
import sys
import json
from maptoposter import utils

_THEMES_DIR = "themes"

@dataclass
class Theme:
    name: str
    description: str
    bg: str
    text: str
    gradient_color: str
    water: str
    parks: str
    subway: str
    tram: str
    light_rail: str
    train: str
    road: str


def print_all() -> None:
    if not os.path.exists(_THEMES_DIR):
        utils.eprint("Could not open themes directory. Verify it exists and contains themes")
        return

    file_names = sorted(os.listdir(_THEMES_DIR))
    if not file_names:
        utils.eprint("No themes found. Make sure the themes directory is present and contains themes")

    for file_name in file_names:
        if not file_name.endswith(".json"):
            continue

        theme = load_by_name(file_name[:-5])
        if not theme:
            continue

        print(f"{theme.name}: {theme.description}")

def load_by_name(name: str) -> Theme | None:
    theme_file = os.path.join(_THEMES_DIR, f"{name}.json")

    if not os.path.exists(theme_file):
        print(f"Theme file '{theme_file}' not found. Using default feature_based theme.", file=sys.stderr)
        return None

    with open(theme_file, 'r') as f:
        json_obj = json.load(f)
        theme = Theme(**json_obj)
        return theme
