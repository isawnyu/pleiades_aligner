#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#
"""
Work on MANTO alignments
"""

from airtight.cli import configure_commandline
import json
import logging
from pathlib import Path
from platformdirs import user_cache_dir, user_config_dir, user_documents_dir
from pleiades_aligner import configure_ingester, Aligner
import sys

DEFAULT_CONFIG_FILE_PATH = str(
    Path(user_config_dir("pleiades_aligner", "isaw_nyu")) / "script_manto_config.json"
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

def align(config: dict, ingesters: dict) -> Aligner:
    """
    perform alignment operations indicated in the config file using the ingested data
    """
    aligner = Aligner(ingesters, config["data_sources"], config["redirects"])
    aligner.align(modes=config["alignment_modes"], proximity_categories=config["proximity_categories"])
    logger = logging.getLogger(sys._getframe().f_code.co_name)
    logger.info(f"Identified {len(aligner.alignments)} alignments")
    return aligner

def configure_ingesters(config: dict) -> dict:
    """ Configure ingesters for namespaces indicated in the config file """
    ingesters = {namespace: configure_ingester(namespace, file_path) for namespace, file_path in config["data_sources"].items()}
    logger = logging.getLogger(sys._getframe().f_code.co_name)
    logger.info(f"Ingesters are configured for the following namespaces: {", ".join(list(ingesters.keys()))}")
    return ingesters


def create_config(config_path: Path):
    """
    Create default config file at config_path
    """
    logger = logging.getLogger(sys._getframe().f_code.co_name)
    logger.debug(f"Attempting to create default config file at: {config_path}.")
    d = {
        "data_sources": {
            "pleiades": f"{user_documents_dir()}/files/P/pleiades.datasets/data/json/",
            "manto": f"{user_documents_dir()}/files/P/pleiades_manto/data/raw/combined.csv",
        },
        "notes": {
            "manto": f"{user_documents_dir()}/files/P/pleiades_manto/data/alignment_notes.json"
        },
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=4, sort_keys=True)
    del f
    logger.info(f"Created default config file at: {config_path}.")


def get_config(config_path: Path) -> dict:
    """
    Read config path or if does not exist, create it
    """
    logger = logging.getLogger(sys._getframe().f_code.co_name)
    if not config_path.exists():
        logger.warning(f"Specified config path not found: {config_path}.")
        create_config(config_path)
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    del f
    return config

def group_alignments(aligner: Aligner) -> dict:
    """
    Group alignments by MANTO id
    Returns a dictionary of alignment group dictionaries
    """
    logger = logging.getLogger(sys._getframe().f_code.co_name)
    alignment_groups = dict()
    for alignment in aligner.alignments_by_authority_namespace("manto"):
        manto_id = alignment.aligned_id_for_namespace(namespace="manto")
        try:
            alignment_groups[manto_id]
        except KeyError:
            alignment_groups[manto_id] = dict()
        this_group = alignment_groups[manto_id]
        other_namespace = [ns for ns in alignment.id_namespaces if ns != "manto"][0]
        try:
            this_group[other_namespace]
        except KeyError:
            this_group[other_namespace] = dict()
        other_id = alignment.aligned_id_for_namespace(other_namespace)
        this_group[other_namespace][other_id] = alignment.asdict()
    return alignment_groups

def ingest(ingesters: dict):
    """
    Read data associated with configured ingesters
    """
    logger = logging.getLogger(sys._getframe().f_code.co_name)
    for namespace, ingester in ingesters.items():
        logger.info(f"Ingesting data for namespace '{namespace}'")
        ingester.ingest()
        logger.info(f"Successfully ingested {len(ingester.data)} places for namespace '{namespace}'")


def main(**kwargs):
    """
    main function
    """
    logger = logging.getLogger(sys._getframe().f_code.co_name)

    config_path = Path(kwargs["config"]).expanduser().resolve()
    config = get_config(config_path)
    ingesters = configure_ingesters(config)
    ingest(ingesters)
    aligner = align(config, ingesters)
    alignment_groups = group_alignments(aligner)
    print(json.dumps(alignment_groups, ensure_ascii=False, indent=4, sort_keys=True))


if __name__ == "__main__":
    main(
        **configure_commandline(
            OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL
        )
    )