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
from haversine import haversine, Unit
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
        pids = a["aligned_ids"]
        places = dict()
        for pid in pids:
            namespace, this_id = pid.split(":")
            if namespace in report["ignore_place_namespaces"]:
                break
            places[namespace] = ingesters[namespace].data.get_place_by_id(this_id)
        if len(places) == 2:
            # >>> copy essential place information into the alignment dictionaries
            b = deepcopy(a)
            # >>> calculate a centroid distance to include in the output for further evaluation
            centroid_coords = list()
            for namespace, place in places.items():
                b[namespace] = {
                    "id": place.id,
                    "title": place.title, 
                    "names": list(place.names),
                    "uri": ingesters[namespace].base_uri + place.id,
                    "centroid": to_wkt(place.centroid),
                    "footprint": to_wkt(place.footprint)
                }
                these_coords = list(list(place.centroid.coords)[0])
                these_coords.reverse()  # haversine expects lat, lon order instead of shapely's lon, lat
                centroid_coords.append(these_coords)
            b["centroid_distance"] = haversine(*centroid_coords, unit=Unit.METERS)
            filtered_alignments.append(b)

    # >>> add second-generation alignments, if any, using inference criteria defined in the config file
    inferred_alignments = dict()
    if config["infer"]:
        for inference_rule in config["infer"]:
            primary_alignments = aligner.alignments_by_id_namespace(inference_rule["primary_namespace"])
            logger.debug(f"identified {len(primary_alignments)} primary alignments from primary namespace {inference_rule['primary_namespace']}")
            primary_alignments = {a for a in primary_alignments if inference_rule["aligned_namespace"] in a.id_namespaces}
            logger.debug(f"filtered primary alignments down to {len(primary_alignments)} involving the primary namespace {inference_rule['primary_namespace']} and the previously aligned namespace {inference_rule['aligned_namespace']}")

            candidate_alignments = aligner.alignments_by_id_namespace(inference_rule["inferred_namespace"])
            logger.debug(f"identified {len(candidate_alignments)} candidate alignments from inferred namespace {inference_rule['inferred_namespace']}")
            candidate_alignments = {a for a in candidate_alignments if "assertion" in a.modes and inference_rule["aligned_namespace"] in a.id_namespaces}
            logger.debug(f"filtered candidate alignments down to {len(candidate_alignments)} involving the inferred namespace {inference_rule['inferred_namespace']} and previously aligned namespace {inference_rule['aligned_namespace']}")

            for candidate in candidate_alignments:
                # get the already aligned full id
                aligned_id = [f for f in candidate.aligned_ids if not f.startswith(inference_rule["inferred_namespace"])][0]
                logger.debug(f">>> aligned_id: {aligned_id}")
                these_primary = {a for a in primary_alignments if aligned_id in a.aligned_ids}
                logger.debug(f">>> these_primary: {these_primary}")
                if not these_primary:
                    continue
                these_candidate = {a for a in candidate_alignments if aligned_id in a.aligned_ids}
                logger.debug(f">>> these_candidate: {these_candidate}")
                if not these_candidate:
                    continue
                for this_primary in these_primary:
                    primary_id = [f for f in this_primary.aligned_ids if f.startswith(inference_rule["primary_namespace"])][0]
                    for this_candidate in these_candidate:
                        inferred_id = [f for f in this_candidate.aligned_ids if f.startswith(inference_rule["inferred_namespace"])][0]
                        new_alignment = pleiades_aligner.aligner.Alignment(primary_id, inferred_id, "inference", authority=aligned_id)
                        logger.debug(pformat(new_alignment.asdict(), indent=4))
                        inferred_alignments[hash(new_alignment)] = new_alignment
                
            primary_alignment_dicts = [a for a in filtered_alignments if inference_rule["primary_namespace"] in a["aligned_namespaces"] and inference_rule["aligned_namespace"] in a["aligned_namespaces"]]
            logger.error(len(primary_alignment_dicts))

            # >>> >>> get a unique list of relevant place dictionaries
            primary_places = list({a[inference_rule["primary_namespace"]]["id"]: a[inference_rule["primary_namespace"]] for a in primary_alignment_dicts}.values())
            aligned_places = list({a[inference_rule["aligned_namespace"]]["id"]: a[inference_rule["aligned_namespace"]] for a in primary_alignment_dicts}.values())

            logger.error(len(primary_places))
            logger.error(len(aligned_places))
            exit()


    # >>> sort the list of alignment dictionaries using the criteria defined in the config file
    # NB: this could be more flexible
    for sort_field, sort_order in report["sort"]:
        reverse = False
        if sort_order == "reverse":
            reverse = True
        filtered_alignments = sorted(filtered_alignments, key=lambda a: a[sort_field], reverse=reverse)

    # output the report
    print(json.dumps(filtered_alignments, ensure_ascii=False, indent=4, sort_keys=True))
    logger.info(f"Reported on {len(filtered_alignments)} alignments after filtering")

if __name__ == "__main__":
    main(
        **configure_commandline(
            OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL
        )
    )
