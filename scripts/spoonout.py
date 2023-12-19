#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2023 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#
"""
change me
"""

from airtight.cli import configure_commandline
import json
import logging
from pathlib import Path
from slugify import slugify

logger = logging.getLogger(__name__)

DEFAULT_LOG_LEVEL = logging.WARNING
OPTIONAL_ARGUMENTS = [
    [
        "-l",
        "--loglevel",
        "NOTSET",
        "desired logging level ("
        + "case-insensitive string: DEBUG, INFO, WARNING, or ERROR",
        False,
    ],
    ["-v", "--verbose", False, "verbose output (logging level == INFO)", False],
    [
        "-w",
        "--veryverbose",
        False,
        "very verbose output (logging level == DEBUG)",
        False,
    ],
]
POSITIONAL_ARGUMENTS = [
    # each row is a list with 3 elements: name, type, help
    [
        "aligned_places_file",
        str,
        "path to aligned places json file as output by prioritize.py",
    ]
]


def output_pleiades(p: dict):
    print(f"Pleiades {p['id']}: {p['title']}")
    print(f"{p['uri']}")
    print(f"names: {', '.join(sorted(p['names'], key=lambda n: slugify(n)))}")


def main(**kwargs):
    """
    main function
    """
    # logger = logging.getLogger(sys._getframe().f_code.co_name)
    whence = Path(kwargs["aligned_places_file"]).expanduser().resolve()
    with open(whence, "r", encoding="utf-8") as f:
        aligned_places = json.load(f)
    del f
    w = 78
    for category, place_groups in aligned_places.items():
        for place_group in place_groups:
            print("\n" + "=" * w)
            print(f"category {category}")
            output_pleiades(place_group["pleiades"])
            others = list()
            for ns, places in place_group.items():
                if ns == "pleiades":
                    continue
                for pid, place in places.items():
                    place["pid"] = pid
                    place["namespace"] = ns
                    others.append(place)
            others.sort(key=lambda p: len(p["modes"]), reverse=True)
            for place in others:
                print("-" * w)
                print(f"{place['namespace']}:{place['pid']}")
                print(f"modes: {', '.join(place['modes'])}")
                if "assertion" in place["modes"] or "inference" in place["modes"]:
                    print(f"authorities: {', '.join(place['authorities'])}")
                try:
                    print(f"{place['title']}")
                except KeyError:
                    pass
                try:
                    print(f"{place['uri']}")
                except KeyError:
                    pass
                try:
                    print(
                        f"names: {', '.join(sorted(place['names'], key=lambda n: slugify(n)))}"
                    )
                except KeyError:
                    pass
                try:
                    d = place["centroid_distance_m"]
                except KeyError:
                    pass
                else:
                    print(f"centroid distance: {d}")

            s = input("press <ENTER> for next place group").strip()
            if s:
                if s[0].lower() == "q":
                    exit()


if __name__ == "__main__":
    main(
        **configure_commandline(
            OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL
        )
    )
