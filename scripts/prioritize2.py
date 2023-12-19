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

cat_criteria = {
    "1": {
        "modes": {"assertion", "proximity", "toponymy", "typology"},
        "proximity_types": {"identical", "tight"},
        "inference_modes": {},
    },
    "2": {
        "modes": {"assertion", "proximity", "toponymy", "typology"},
        "proximity_types": {"overlapping"},
        "inference_modes": {},
    },
    "3": {
        "modes": {"assertion", "proximity", "toponymy", "typology"},
        "proximity_types": {"close"},
        "inference_modes": {},
    },
    "4": {
        "modes": {"assertion", "proximity", "toponymy"},
        "proximity_types": {"identical", "tight", "overlapping", "close"},
        "inference_modes": {},
    },
    "5": {
        "modes": {"assertion", "toponymy"},
        "proximity_types": {},
        "inference_modes": {},
    },
    "6": {
        "modes": {"proximity", "toponymy", "typology"},
        "proximity_types": {"identical", "tight"},
        "inference_modes": {},
    },
    "7": {
        "modes": {"proximity", "toponymy", "typology"},
        "proximity_types": {"overlapping"},
        "inference_modes": {},
    },
    "8": {
        "modes": {"proximity", "toponymy", "typology"},
        "proximity_types": {"close"},
        "inference_modes": {},
    },
}


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return sorted(list(obj))
        return json.JSONEncoder.default(self, obj)


def main(**kwargs):
    """
    main function
    """
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

    # group by categories and primary namespace places
    categories = {cat: dict() for cat in cat_criteria.keys()}
    count = 0
    inf_only = set("inference")
    inferred_alignments_by_pid = dict()
    for ahash, a in alignments.items():
        a_modes = set(a["modes"])
        primary_pid = [
            pid for pid in a["aligned_ids"] if pid.startswith(primary_namespace)
        ][0]
        hit = False
        for cat, criteria in cat_criteria.items():
            if a_modes == criteria["modes"]:
                if criteria["proximity_types"]:
                    try:
                        a["proximity"]
                    except KeyError:
                        continue
                    else:
                        if a["proximity"] in criteria["proximity_types"]:
                            hit = True
                else:
                    hit = True
            if hit:
                count += 1
                try:
                    categories[cat][primary_pid]
                except KeyError:
                    categories[cat][primary_pid] = set()
                categories[cat][primary_pid].add(ahash)
                break
        if not hit and "inference" in a_modes:
            try:
                inferred_alignments_by_pid[primary_pid]
            except KeyError:
                inferred_alignments_by_pid[primary_pid] = set()
            inferred_alignments_by_pid[primary_pid].add(ahash)

    # places by category
    results = {cat: dict() for cat in cat_criteria.keys()}
    for cat, hashes_by_pids in categories.items():
        for primary_pid, hashes in hashes_by_pids.items():
            for ahash in hashes:
                a = alignments[ahash]
                other_pid = [pid for pid in a["aligned_ids"] if pid != primary_pid][0]
                try:
                    results[cat][primary_pid]
                except KeyError:
                    results[cat][primary_pid] = dict()
                results[cat][primary_pid][primary_pid] = a[primary_namespace]
                other_namespace = [
                    ns for ns in a["aligned_namespaces"] if ns != primary_namespace
                ][0]
                results[cat][primary_pid][other_pid] = a[other_namespace]
                results[cat][primary_pid][other_pid]["authorities"] = a["authorities"]
                results[cat][primary_pid][other_pid]["modes"] = a["modes"]
                try:
                    results[cat][primary_pid][other_pid]["proximity"] = a["proximity"]
                    results[cat][primary_pid][other_pid]["centroid_distance_m"] = a[
                        "centroid_distance_m"
                    ]
                except KeyError:
                    results[cat][primary_pid][other_pid]["proximity"] = None
                    results[cat][primary_pid][other_pid]["centroid_distance_m"] = None
            try:
                inference_hashes = inferred_alignments_by_pid[primary_pid]
            except KeyError:
                pass
            else:
                for ahash in inference_hashes:
                    a = alignments[ahash]
                    if set(a["authorities"]).intersection(
                        results[cat][primary_pid][other_pid]["authorities"]
                    ):
                        other_pid = [
                            pid for pid in a["aligned_ids"] if pid != primary_pid
                        ][0]
                        other_namespace = [
                            ns
                            for ns in a["aligned_namespaces"]
                            if ns != primary_namespace
                        ][0]
                        try:
                            results[cat][primary_pid][other_pid] = a[other_namespace]
                        except KeyError:
                            results[cat][primary_pid][other_pid] = dict()
                        results[cat][primary_pid][other_pid]["authorities"] = a[
                            "authorities"
                        ]
                        results[cat][primary_pid][other_pid]["modes"] = a["modes"]
                        try:
                            results[cat][primary_pid][other_pid]["proximity"] = a[
                                "proximity"
                            ]
                            results[cat][primary_pid][other_pid][
                                "centroid_distance_m"
                            ] = a["centroid_distance_m"]
                        except KeyError:
                            results[cat][primary_pid][other_pid]["proximity"] = None
                            results[cat][primary_pid][other_pid][
                                "centroid_distance_m"
                            ] = None
    print(json.dumps(results, indent=4, cls=SetEncoder))
    logger.info(f"Wrote {count} categorized/ranked alignments")


if __name__ == "__main__":
    main(
        **configure_commandline(
            OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL
        )
    )
