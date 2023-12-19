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
from colorama import Fore, Back, Style
import json
import logging
import math
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


def wipe_terminal():
    print("\033[H\033[2J", end="")


def output_place(pid: str, place: dict):
    namespace = pid.split(":")[0]
    if namespace == "pleiades":
        color = Fore.BLUE
    else:
        color = Fore.RESET
    try:
        print(
            color
            + Style.BRIGHT
            + f"{pid}:\n{place['title']}"
            + Style.NORMAL
            + Fore.RESET
        )
    except KeyError:
        print(color + Style.BRIGHT + pid + ":" + Style.NORMAL + Fore.RESET)
    try:
        print(place["uri"])
    except KeyError:
        pass
    try:
        print(", ".join(sorted(place["names"], key=lambda n: slugify(n))))
    except KeyError:
        pass
    try:
        print(", ".join(sorted(place["feature_types"])))
    except KeyError:
        pass
    try:
        modes = place["modes"]
    except KeyError:
        modes = list()
    else:
        print(", ".join(sorted(modes)))
    if "proximity" in modes:
        d = place["centroid_distance_m"]
        print(f"proximity:{place['proximity']}={math.ceil(d)}")
    print()


def main(**kwargs):
    """
    main function
    """
    # logger = logging.getLogger(sys._getframe().f_code.co_name)
    whence = Path(kwargs["aligned_places_file"]).expanduser().resolve()
    with open(whence, "r", encoding="utf-8") as f:
        categorized_aligments = json.load(f)
    del f

    for cat, aligned_places in categorized_aligments.items():
        for pleiades_id, pleiades_data in aligned_places.items():
            wipe_terminal()
            output_place(pleiades_id, pleiades_data[pleiades_id])
            for other_id, other_data in pleiades_data.items():
                if other_id == pleiades_id:
                    continue
                output_place(other_id, other_data)
            s = input("> ").strip()
            if s:
                if s[0].lower() == "q":
                    exit()


if __name__ == "__main__":
    main(
        **configure_commandline(
            OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL
        )
    )
