import argparse
from datetime import datetime
from typing import Callable, Tuple
from matplotlib.figure import Figure
import matplotlib.pyplot as pyplot
from maptoposter import fetching, poster
from maptoposter.themes import themes
import sys
import os
from rich.console import Console


def main():
    args, print_help = parse_args()
    console = Console()

    if args.list_themes:
        for theme_name in themes:
            console.print(f"  - {theme_name}")
        return 0

    if not args.title or not args.subtitle:
        print_help()
        return 1

    if args.theme not in themes:
        print(f"Theme {args.theme} not found.", file=sys.stderr)
        return 1
    theme = themes[args.theme]

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
        fig = poster.plot(console, config, data)

    console.print("Saving poster")
    save_location = save_poster(fig, config.title, args.theme)
    console.print(f"[green]Poster saved at [bold]{save_location}[/bold]![/green]")

    pyplot.close(fig)


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

    return parser.parse_args(), parser.print_help


def save_poster(fig: Figure, title: str, theme_name: str) -> str:
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

    file_name = f"{timestamp}_{title}_{theme_name}.png".lower().replace(" ", " ")
    save_location = os.path.join("out", file_name)

    if not os.path.exists("out"):
        os.makedirs("out")

    fig.savefig(save_location, dpi=300)

    return save_location


if __name__ == "__main__":
    main()
