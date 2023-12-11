#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2023 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#
"""
Run Alignments
"""

from airtight.cli import configure_commandline
from copy import deepcopy
import json
import logging
from pathlib import Path
from platformdirs import user_cache_dir, user_config_dir
import pleiades_aligner
from pprint import pformat, pprint
from shapely import to_wkt

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_FILE_PATH = str(
    Path(user_config_dir("pleiades_aligner", "isaw_nyu")) / "default.config"
)

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
    ["-c", "--config", DEFAULT_CONFIG_FILE_PATH, "path to config file", False],
]
POSITIONAL_ARGUMENTS = [
    # each row is a list with 3 elements: name, type, help
]


def main(**kwargs):
    """
    main function
    """
    logger = logging.getLogger()
    config_file_path = Path(kwargs["config"].strip()).expanduser().resolve()
    with open(config_file_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    del f

    # configure ingesters for namespaces indicated in the config file
    ingesters = dict()
    for namespace, file_path in config["data_sources"].items():
        if namespace == "chronique":
            ingesters[namespace] = pleiades_aligner.IngesterChronique(file_path)
        elif namespace == "manto":
            ingesters[namespace] = pleiades_aligner.IngesterMANTO(file_path)
        elif namespace == "pleiades":
            ingesters[namespace] = pleiades_aligner.IngesterPleiades(file_path)
        else:
            raise NotImplementedError(
                f"No supported ingester for namespace '{namespace}'"
            )
    logger.info(f"Ingesters are configured for the following namespaces: {", ".join(list(ingesters.keys()))}")

    # using the configured ingesters, ingest data from filepaths indicated in the config file
    for namespace, ingester in ingesters.items():
        logger.info(f"Ingesting data for namespace '{namespace}'")
        ingester.ingest()
        logger.info(f"Successfully ingested {len(ingester.data)} places for namespace '{namespace}'")

    # perform alignment operations indicated in the config file using the ingested data
    logger.info("Performing alignments")
    aligner = pleiades_aligner.Aligner(ingesters, config["data_sources"], config["redirects"])
    aligner.align(modes=config["alignment_modes"], proximity_categories=config["proximity_categories"])
    logger.info(f"Identified {len(aligner.alignments)} alignments")

    # >>> add second-generation alignments, if any, using inference criteria defined in the config file
    for inference_rule in config["infer"]:
        aligner.align_by_inference(**inference_rule)

    # prepare a JSON-formatted report according to the parameters defined in the config file
    logger.info(f"Preparing report")
    report = config["report"]

    # >>> ignore alignments relying only on authority namespaces explicitly excluded by the config file
    alignments = [a for a in aligner.alignments.values() if not a.authority_namespaces.intersection(report["ignore_authority_namespaces"])]
    
    # >>> further filter alignments by removing any that aren't based on the combination of alignment modes indicated in config file
    required_modes = set(report["require_modes"])
    alignments = [a for a in alignments if required_modes.issubset(a.modes)]

    # >>> convert alignments to dictionaries in anticipation of serializing to JSON
    alignments = [a.asdict() for a in alignments]

    # >>> further filter alignment dictionaries to exclude those involving places from datasets (i.e. namespaces) explicitly excluded by the config file
    filtered_alignments = list()
    for a in alignments:
        bailout = False
        pids = a["aligned_ids"]
        places = dict()
        for pid in pids:
            namespace, this_id = pid.split(":")
            if namespace in report["ignore_place_namespaces"]:
                bailout = True
                break
            try:
                places[namespace] = ingesters[namespace].data.get_place_by_id(this_id)
            except KeyError:
                pass
        if bailout:
            continue
        b = deepcopy(a)
        # >>> copy essential place information into the alignment dictionaries
        for namespace, place in places.items():
            b[namespace] = {
                "id": place.id,
                "title": place.title, 
                "names": list(place.names),
                "uri": ingesters[namespace].base_uri + place.id,
                "centroid": to_wkt(place.centroid),
                "footprint": to_wkt(place.footprint)
            }
        filtered_alignments.append(b)

    # output the report
    print(json.dumps(filtered_alignments, ensure_ascii=False, indent=4, sort_keys=True))
    logger.info(f"Reported on {len(filtered_alignments)} alignments after filtering")

if __name__ == "__main__":
    main(
        **configure_commandline(
            OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL
        )
    )
