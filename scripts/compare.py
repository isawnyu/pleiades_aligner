#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2023 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#
"""
compare an assertion alignment dataset to a corresponding pleiades index
"""

from airtight.cli import configure_commandline
import json
import logging
from pathlib import Path
from platformdirs import user_cache_dir, user_config_dir
import pleiades_aligner
from pleiades_aligner.aligner import Alignment
from urllib.parse import urlparse


logger = logging.getLogger(__name__)

DEFAULT_LOG_LEVEL = logging.WARNING
DEFAULT_CONFIG_FILE_PATH = str(
    Path(user_config_dir("pleiades_aligner", "isaw_nyu")) / "default.config"
)
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
    ["datasource", str, "name of datasource to use (must be defined in config file)"],
    ["indexpath", str, "path to Pleiades index file to compare"],
]


def main(**kwargs):
    """
    main function
    """
    # logger = logging.getLogger(sys._getframe().f_code.co_name)
    logger = logging.getLogger()
    config_file_path = Path(kwargs["config"].strip()).expanduser().resolve()
    with open(config_file_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    del f

    # configure ingester for namespace
    namespace = kwargs["datasource"]
    logger.info(f"Configuring ingestor for namespace '{namespace}'")
    file_path = Path(config["data_sources"][namespace])
    if namespace == "chronique":
        ingester = pleiades_aligner.IngesterChronique(file_path)
    elif namespace == "manto":
        ingester = pleiades_aligner.IngesterMANTO(file_path)
    elif namespace == "topostext":
        ingester = pleiades_aligner.IngesterTopostext(file_path)
    else:
        raise NotImplementedError(f"No supported ingester for namespace '{namespace}'")

    # using the configured ingesters, ingest data from filepaths indicated in the config file
    logger.info(f"Ingesting data for namespace '{namespace}'")
    ingester.ingest()
    logger.info(
        f"Successfully ingested {len(ingester.data)} places for namespace '{namespace}'"
    )

    # perform assertion alignments using the ingested data
    logger.info("Performing alignments")
    aligner = pleiades_aligner.Aligner(
        {namespace: ingester}, config["data_sources"], config["redirects"]
    )
    aligner.align(modes=["assertions"])
    # logger.info(f"Identified {len(aligner.alignments)} alignments")
    dataset_alignments = {
        hash(a): a for a in aligner.alignments_by_id_namespace("pleiades")
    }
    logger.info(
        f"Identified {len(dataset_alignments)} pleiades alignments in {namespace} dataset."
    )

    # ingest index and convert to alignments
    index_path = Path(kwargs["indexpath"]).expanduser().resolve()
    logger.info(index_path)
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)
    del f
    index_alignments = dict()
    base_hostname = urlparse(ingester.base_uri).hostname
    base_uri_len = len(ingester.base_uri)
    for uri, place in index.items():
        uri_parts = urlparse(uri)
        if uri_parts.hostname != base_hostname:
            continue
        if not uri.startswith(ingester.base_uri):
            continue
        if namespace == "chronique" and "kroute=report" in uri:
            continue
        place_id = uri[base_uri_len:].strip()
        full_place_id = ":".join((namespace, place_id))
        for a_uri in place["alignments"]:
            target_id = "pleiades:" + a_uri.split("/")[-1]
            alignment = Alignment(
                full_place_id, target_id, authority=target_id, mode="assertion"
            )
            a_hash = hash(alignment)
            index_alignments[a_hash] = alignment
    logger.info(f"parsed {len(index_alignments)} alignments from {index_path}")

    matching = dict()
    index_unmatched = dict()
    dataset_unmatched = dict()

    for index_hash in index_alignments.keys():
        try:
            a = dataset_alignments[index_hash]
        except KeyError:
            index_unmatched[index_hash] = index_alignments[index_hash]
        else:
            matching[index_hash] = a
            for auth in index_alignments[index_hash].authorities:
                matching[index_hash].add_authority(auth)
    for dataset_hash in dataset_alignments.keys():
        try:
            matching[dataset_hash]
        except KeyError:
            dataset_unmatched[dataset_hash] = dataset_alignments[dataset_hash]

    results = {
        "matching_alignments": [a.asdict() for a in matching.values()],
        "unmatched_in_index": [a.asdict() for a in index_unmatched.values()],
        "unmatched_in_dataset": [a.asdict() for a in dataset_unmatched.values()],
    }
    print(json.dumps(results, ensure_ascii=False, indent=4, sort_keys=True))
    logger.info(
        f"There are {len(dataset_alignments)} asserted alignments in the "
        f"{namespace} dataset. Of these, Pleiades includes {len(matching)} "
        f"matching assertions, leaving {len(dataset_unmatched)} to be "
        f"addressed. There are an additional {len(index_unmatched)} asserted "
        f"alignments in Pleiades that are not reflected in the {namespace} "
        "dataset."
    )


if __name__ == "__main__":
    main(
        **configure_commandline(
            OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL
        )
    )
