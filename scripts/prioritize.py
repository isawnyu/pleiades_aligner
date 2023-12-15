#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2023 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#
"""
Prioritize and group alignments by namespace
"""

from airtight.cli import configure_commandline
import json
import logging
from pathlib import Path
from pprint import pformat

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
    ["-n", "--namespace", "pleiades", "namespace to group by", False],
]
POSITIONAL_ARGUMENTS = [
    # each row is a list with 3 elements: name, type, help
    ["jsonpath", str, "path to JSON file containing alignments"]
]


def proximity_sort_key(p: dict):
    distances = set()
    proximity_types = set()

    for ns, data in p.items():
        if ns == "pleiades":
            continue
        for pid, datum in data.items():
            if "proximity" not in datum["modes"]:
                continue
            proximity_types.add(datum["proximity"])
            distances.add(datum["centroid_distance_m"])
    type_convert = {"identical": 1, "tight": 2, "overlapping": 3, "close": 4, "near": 5}
    return (min(distances), min([type_convert[t] for t in proximity_types]))


def main(**kwargs):
    """
    main function
    """
    # logger = logging.getLogger(sys._getframe().f_code.co_name)
    inpath = Path(kwargs["jsonpath"]).expanduser().resolve()
    with open(inpath, "r", encoding="utf-8") as f:
        alignments = json.load(f)
    del f
    logger.info(f"Loaded {len(alignments)} alignments from {inpath}")

    # filter alignments for the desired namespace
    primary_namespace = kwargs["namespace"]
    alignments = {
        a["hash"]: a for a in alignments if primary_namespace in a["aligned_namespaces"]
    }
    logger.info(f"After filtering: {len(alignments)} alignments")

    # reorganize alignments by places in the primary namespace
    aligned_places = dict()
    for a in alignments.values():
        this_pid = [id for id in a["aligned_ids"] if id.startswith(primary_namespace)][
            0
        ]
        that_pid = [id for id in a["aligned_ids"] if id != this_pid][0]
        this_pid_raw = this_pid.split(":")[1]
        try:
            aligned_places[this_pid_raw]
        except KeyError:
            aligned_places[this_pid_raw] = dict()
            aligned_places[this_pid_raw][primary_namespace] = a[primary_namespace]
        that_namespace = [
            ns for ns in a["aligned_namespaces"] if ns != primary_namespace
        ][0]
        try:
            aligned_places[this_pid_raw][that_namespace]
        except KeyError:
            aligned_places[this_pid_raw][that_namespace] = dict()
        that_pid_raw = that_pid.split(":")[1]
        try:
            aligned_places[this_pid_raw][that_namespace][that_pid_raw]
        except KeyError:
            aligned_places[this_pid_raw][that_namespace][that_pid_raw] = dict()
        for k, v in a.items():
            if k in [
                primary_namespace,
                that_namespace,
                "aligned_ids",
                "aligned_namespaces",
                "hash",
            ]:
                continue
            aligned_places[this_pid_raw][that_namespace][that_pid_raw][k] = v
        try:
            a["that_namespace"]
        except KeyError:
            pass
        else:
            for k, v in a["that_namespace"].items():
                if k in ["id"]:
                    continue
                aligned_places[this_pid_raw][that_namespace][that_pid_raw][k]
    logger.info(f"{len(aligned_places)} aligned places")

    # place the aligned places into categories of interest
    categories = dict()
    for pleiades_id, data in aligned_places.items():
        modes = set()
        for ns, alignment in data.items():
            if ns == "pleiades":
                continue
            for placeid, datum in alignment.items():
                modes.add(",".join(sorted(datum["modes"])))
        logger.error(modes)
        cat = None
        if "assertion,names,proximity" in modes:
            cat = 1
        elif "assertion,proximity" in modes:
            cat = 2
        elif "names,proximity" in modes:
            cat = 3
        elif "proximity" in modes:
            cat = 4
        else:
            cat = 5
        try:
            categories[cat]
        except KeyError:
            categories[cat] = list()
        categories[cat].append(data)

    # sort each category
    for cat, pplaces in categories.items():
        if cat < 5:
            pplaces.sort(key=proximity_sort_key)

    print(json.dumps(categories, ensure_ascii=False, indent=4, sort_keys=True))
    # print(json.dumps(aligned_places, ensure_ascii=False, indent=4, sort_keys=True))


if __name__ == "__main__":
    main(
        **configure_commandline(
            OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL
        )
    )
