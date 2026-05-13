import argparse
from datetime import datetime
import os.path
import platform
import re
import subprocess
from typing import Callable, Tuple
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties, findfont
import matplotlib.pyplot as pyplot
from maptoposter import fetching, poster
from maptoposter.poster import PRINT_SIZES, PRINT_SIZE_CATEGORIES
from maptoposter.themes import themes
import sys
from rich.console import Console


def main():
    args, print_help = parse_args()
    console = Console()

    if args.list_themes:
        for theme_name in themes:
            console.print(f"  - {theme_name}")
        return 0

    if args.list_sizes:
        console.print("[bold]Available predefined sizes:[/bold]")
        for category, sizes in PRINT_SIZE_CATEGORIES.items():
            console.print(f"\n[bold]{category}:[/bold]")
            for name, (w, h) in sizes.items():
                console.print(f"  {name:10} {w}\" x {h}\"")
        return 0

    if not args.title or not args.subtitle:
        print_help()
        return 1

    if args.theme not in themes:
        print(f"Theme {args.theme} not found.", file=sys.stderr)
        return 1
    theme = themes[args.theme]

    if not validate_font(args.font):
        print(f"Font '{args.font}' not found.", file=sys.stderr)
        return 1

    # Parse size
    size = parse_size(args)
    if size is None:
        return 1

    location = args.location
    if not args.location:
        location = f"{args.title}, {args.subtitle}"

    console.print(f'Locating "{location}"')
    point = fetching.fetch_point(location)
    console.print(f"[green]found [bold]{point}[/bold][/green]")

    config = poster.PosterConfig(args.title, args.subtitle, point, args.radius, theme)

    with console.status("Fetching required data"):
        data = fetching.fetch_data(console, point, config.radius)
        console.print("[green]Data retrieved sucessfully![/green]")

    with console.status("Drawing poster"):
        fig = poster.plot(console, config, data, args.font, size)

    console.print("Saving poster")
    save_location = save_poster(
        fig, args.output, config.title, config.subtitle, args.theme, size, args.dpi
    )
    console.print(f"[green]Poster saved at [bold]{save_location}[/bold]![/green]")

    pyplot.close(fig)

    if args.open:
        open_file(save_location)


def validate_font(font: str) -> bool:
    """Check if the font is available (either as a file or font family)."""
    # If it has an extension, treat it as a file path
    if os.path.splitext(font)[1]:
        return os.path.isfile(font)

    # Otherwise, check if the font family is available
    # findfont returns the default font if the requested one isn't found
    default_font = findfont(FontProperties())
    requested_font = findfont(FontProperties(family=font))
    return requested_font != default_font


def open_file(path: str) -> None:
    """Open a file with the system's default application."""
    system = platform.system()
    if system == "Darwin":
        subprocess.run(["open", path])
    elif system == "Windows":
        subprocess.run(["start", "", path], shell=True)
    else:  # Linux and others
        subprocess.run(["xdg-open", path])


def parse_custom_size(size_str: str, is_cm: bool) -> Tuple[float, float] | None:
    """Parse a custom size string (WxH) and validate it."""
    match = re.match(r"(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)", size_str.lower())
    if not match:
        print(f"Invalid size format: '{size_str}'. Use WxH (e.g., 8x12).", file=sys.stderr)
        return None

    width, height = float(match.group(1)), float(match.group(2))
    if is_cm:
        width, height = width / 2.54, height / 2.54  # convert to inches

    # Validate portrait orientation
    if width >= height:
        print(f"Size must be portrait orientation (height > width). Got {width:.1f}x{height:.1f}.", file=sys.stderr)
        return None

    # Validate aspect ratio (between 1:1 and 1:2)
    ratio = height / width
    if ratio < 1.0 or ratio > 2.0:
        print(f"Aspect ratio must be between 1:1 and 1:2 (got 1:{ratio:.2f}).", file=sys.stderr)
        return None

    return (width, height)


def parse_size(args: argparse.Namespace) -> Tuple[float, float] | None:
    """Parse and validate size arguments."""
    if args.size_inches:
        return parse_custom_size(args.size_inches, is_cm=False)
    elif args.size_cm:
        return parse_custom_size(args.size_cm, is_cm=True)
    else:
        # Use predefined size (default is "12x16")
        size_name = args.size.lower()
        if size_name not in PRINT_SIZES:
            print(f"Unknown size '{args.size}'. Use --list-sizes to see available sizes.", file=sys.stderr)
            return None
        return PRINT_SIZES[size_name]


def parse_args() -> Tuple[argparse.Namespace, Callable[[], None]]:
    parser = argparse.ArgumentParser(
        prog="maptoposter",
        description="Generate beautiful map posters for any city",
    )

    parser.add_argument(
        "--location",
        "-l",
        type=str,
        help="Location (default: inferred from title and subtitle if not specified)",
    )
    parser.add_argument(
        "--radius", "-r", type=int, default=10000, help="Map radius in meters"
    )
    parser.add_argument("--title", "-t", type=str, help="Title to write on the poster")
    parser.add_argument(
        "--subtitle", "-s", type=str, help="Subtitle to write on the poster"
    )
    parser.add_argument(
        "--theme", "-T", type=str, help="Theme name (default: feature_based)"
    )
    parser.add_argument(
        "--list-themes", action="store_true", help="List all available themes"
    )
    parser.add_argument(
        "--font",
        "-f",
        type=str,
        default="Roboto",
        help="Font family name or path to a font file (default: Roboto)",
    )

    # Size options (mutually exclusive)
    size_group = parser.add_mutually_exclusive_group()
    size_group.add_argument(
        "--size",
        "-S",
        type=str,
        default="12x16",
        help="Predefined size name (default: 12x16). Use --list-sizes to see options.",
    )
    size_group.add_argument(
        "--size-inches",
        type=str,
        help="Custom size in inches (WxH, e.g., 8x12)",
    )
    size_group.add_argument(
        "--size-cm",
        type=str,
        help="Custom size in centimeters (WxH, e.g., 20x30)",
    )
    parser.add_argument(
        "--list-sizes", action="store_true", help="List all available predefined sizes"
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Output resolution in DPI (default: 300)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="out/{timestamp}_{title}_{theme}.png",
        help="Output path template. Placeholders: {timestamp}, {title}, {subtitle}, {theme}, {size}, {dpi} (default: out/{timestamp}_{title}_{theme}.png)",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the output file after saving",
    )

    return parser.parse_args(), parser.print_help


def save_poster(
    fig: Figure,
    output_template: str,
    title: str,
    subtitle: str,
    theme_name: str,
    size: Tuple[float, float],
    dpi: int,
) -> str:
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    size_str = f"{size[0]}x{size[1]}"

    save_location = output_template.format(
        timestamp=timestamp,
        title=title,
        subtitle=subtitle,
        theme=theme_name,
        size=size_str,
        dpi=dpi,
    ).lower().replace(" ", "_")

    # Create parent directories if needed
    parent_dir = os.path.dirname(save_location)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    fig.savefig(save_location, dpi=dpi)

    return save_location


if __name__ == "__main__":
    main()
