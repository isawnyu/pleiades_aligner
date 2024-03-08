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
    logger.info(f"Identified {len(aligner.alignments)} alignments")

    # ingest index and convert to alignments
    index_path = Path(kwargs["indexpath"]).expanduser().resolve()
    logger.info(index_path)
    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)
    del f
    index_alignments = dict()
    base_hostname = urlparse(ingester.base_uri).hostname
    base_len = len(base_hostname)
    for uri, place in index.items():
        uri_parts = urlparse(uri)
        if uri_parts.hostname != base_hostname:
            continue
        place_id = uri[base_len:].strip()
        full_place_id = ":".join((namespace, place_id))
        for a_uri in place["alignments"]:
            target_id = "pleiades:" + a_uri.split("/")[-1]
            alignment = Alignment(
                full_place_id, target_id, authority=full_place_id, mode="assertion"
            )
            a_hash = hash(alignment)
            index_alignments[a_hash] = alignment
    logger.info(f"parsed {len(index_alignments)} alignments from {index_path}")


if __name__ == "__main__":
    main(
        **configure_commandline(
            OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL
        )
    )
