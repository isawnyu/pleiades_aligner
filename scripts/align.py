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
import json
import logging
from pathlib import Path
from platformdirs import user_cache_dir, user_config_dir
import pleiades_aligner
from pprint import pformat

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
    for namespace, ingester in ingesters.items():
        logger.info(f"Ingesting data for namespace '{namespace}'")
        ingester.ingest()
        logger.info(f"Successfully ingested {len(ingester.data)} places for namespace '{namespace}'")
    aligner = pleiades_aligner.Aligner(ingesters, config["data_sources"], config["redirects"])
    aligner.align(modes=config["alignment_modes"])
    logger.info(pformat(list(aligner.alignments.values()), indent=4))

if __name__ == "__main__":
    main(
        **configure_commandline(
            OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL
        )
    )
