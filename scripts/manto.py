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
from colorama import Fore, Back, Style
import json
import logging
from pathlib import Path
from platformdirs import user_cache_dir, user_config_dir, user_documents_dir
from pleiades_aligner import configure_ingester, Aligner
from pprint import pformat
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
    ["-z", "--fromcache", False, "load alignments from cache instead of raw data", False]
]
POSITIONAL_ARGUMENTS = [
    # each row is a list with 3 elements: name, type, help
]

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

def align(config: dict, ingesters: dict) -> Aligner:
    """
    perform alignment operations indicated in the config file using the ingested data
    """
    aligner = Aligner(ingesters, config["data_sources"], config["redirects"])
    aligner.align(modes=config["alignment_modes"], proximity_categories=config["proximity_categories"])
    logger = logging.getLogger(sys._getframe().f_code.co_name)
    logger.info(f"Identified {len(aligner.alignments)} alignments")
    return aligner

def annotate(config: dict, alignment_groups: dict):
    """
    load notes from file and incorporate into alignment groups
    """
    logger = logging.getLogger(sys._getframe().f_code.co_name)
    notes_path = Path(config["notes"])
    with open(notes_path, "r", encoding="utf-8") as f:
        notes = json.load(f)
    del f
    logger.info(f"Loaded {len(notes)} notes from {notes_path}.")
    for manto_id, note in notes.items():
        try:
            group = alignment_groups[manto_id]
        except KeyError:
            logger.error(f"notes contain manto_id {manto_id} which is not in an alignment group in the data")
            continue
        group["note"] = note

def concurrence(alignment_groups: dict):
    """ Check for concurrence """
    for manto_id, group in alignment_groups.items():
        concurrence_reciprocal(manto_id, group)
        concurrence_names(manto_id, group)
        concurrence_types(manto_id, group)

def concurrence_names(manto_id: str, group: dict):
    if not group["names"]:
        return
    else:
        manto_names = set(group["names"])
    for qualified_id in group["alignments"]:
        other_namespace, other_id = qualified_id.split(":")
        if other_namespace != "pleiades":
            continue
        try:
            pleiades_names = set(group[other_namespace][other_id]["names"])
        except KeyError:
            continue
        if manto_names.intersection(pleiades_names):
            group["name_concurrence"] = True
            return
    group["name_concurrence"] = False
    

def concurrence_reciprocal(manto_id: str, group: dict):
    for qualified_id in group["alignments"]:
        other_namespace, other_id = qualified_id.split(":")
        try:
            alignments = group[other_namespace][other_id]["alignments"]
        except KeyError:
            continue
        else:
            if f"manto:{manto_id}" in alignments:
                group["reciprocal"] = True
                return
    group["reciprocal"] = False

def concurrence_types(manto_id: str, group: dict):
    if not group["feature_types"]:
        group["type_concurrence"] = False
        return
    else:
        manto_types = set(group["feature_types"])
    for qualified_id in group["alignments"]:
        other_namespace, other_id = qualified_id.split(":")
        if other_namespace != "pleiades":
            continue
        try:
            pleiades_types = set(group[other_namespace][other_id]["feature_types"])
        except KeyError:
            continue
        if manto_types.intersection(pleiades_types):
            group["type_concurrence"] = True
            return
    group["type_concurrence"] = False


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
        "notes": f"{user_documents_dir()}/files/P/pleiades_manto/data/alignment_notes.json"
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

def group_alignments(aligner: Aligner, ingesters: dict) -> dict:
    """
    Group alignments by MANTO id
    Returns a dictionary of alignment group dictionaries
    """
    logger = logging.getLogger(sys._getframe().f_code.co_name)
    common_fields = ["title", "uri", "names", "alignments", "feature_types"]
    alignment_groups = dict()
    for alignment in aligner.alignments_by_authority_namespace("manto"):
        manto_id = alignment.aligned_id_for_namespace(namespace="manto")
        try:
            alignment_groups[manto_id]
        except KeyError:
            alignment_groups[manto_id] = dict()
            try:
                this_place = ingesters["manto"].data.get_place_by_id(manto_id)
            except KeyError as err:
                logger.error(str(err))
            else:
                for fn in common_fields:
                    try:
                        alignment_groups[manto_id][fn] = getattr(this_place, fn)
                    except AttributeError:
                        pass
        this_group = alignment_groups[manto_id]
        other_namespace = [ns for ns in alignment.id_namespaces if ns != "manto"][0]
        try:
            this_group[other_namespace]
        except KeyError:
            this_group[other_namespace] = dict()
        other_id = alignment.aligned_id_for_namespace(other_namespace)
        this_group[other_namespace][other_id] = alignment.asdict()
        try:
            other_place = ingesters[other_namespace].data.get_place_by_id(other_id)
        except KeyError as err:
            logger.error(str(err))
        else:
            for fn in common_fields:
                try:
                    this_group[other_namespace][other_id][fn] = getattr(other_place, fn)
                except AttributeError:
                    pass

    return alignment_groups

def index(alignment_groups: dict) -> dict:
    """
    determine which manto ids to work with when
    """
    idx = {
        "done": set(),
        "pending_discussion": set(),
        "ready": {
            "likely": set(),
            "probable": set(),
            "asserted": set()
        }
    }
    for manto_id, group in alignment_groups.items():
        if group["reciprocal"]:
            idx["done"].add(manto_id)
        else:
            try:
                group["note"]
            except KeyError:
                pass
            else:
                if group["note"]["discuss"]:
                    idx["pending_discussion"].add(manto_id)
                    continue
            try:
                group["type_concurrence"]
            except KeyError:
                raise RuntimeError(pformat(group, indent=4))
            if group["name_concurrence"] and group["type_concurrence"]:
                idx["ready"]["likely"].add(manto_id)
            elif group["name_concurrence"]:
                idx["ready"]["probable"].add(manto_id)
            else:
                idx["ready"]["asserted"].add(manto_id)
    return idx


def ingest(ingesters: dict):
    """
    Read data associated with configured ingesters
    """
    logger = logging.getLogger(sys._getframe().f_code.co_name)
    for namespace, ingester in ingesters.items():
        logger.info(f"Ingesting data for namespace '{namespace}'")
        ingester.ingest()
        logger.info(f"Successfully ingested {len(ingester.data)} places for namespace '{namespace}'")

def spoon_header(v: str):
    outs = f"{v}\n"
    print(
        Fore.BLUE
        + Style.BRIGHT
        + outs
        + "-" * len(outs)
        + Style.NORMAL
        + Fore.RESET
    )

def spoonout(alignment_groups: dict, idx: dict):
    logger = logging.getLogger(sys._getframe().f_code.co_name)

    wipe_terminal()
    spoon_header("MANTO alignments to Pleiades")


    done = len(idx["done"])
    print(f"Reciprocal (complete): {done}")

    discuss = len(idx["pending_discussion"])
    print(f"Pending discussion: {discuss}\n")

    print("Ready for review:")
    likely = len(idx["ready"]["likely"])
    print(f"    Likely: {likely}")

    probable = len(idx["ready"]["probable"])
    print(f"    Probable: {probable}")

    asserted = len(idx["ready"]["asserted"])
    print(f"    Asserted: {asserted}\n")

    commands = {k.lower(): k.lower() for k in idx["ready"]}
    logger.debug(f"commands: {pformat(commands, indent=4)}")
    commands = dict(commands, **{k[0]: k for k in commands.keys()})
    logger.debug(f"commands: {pformat(commands, indent=4)}")

    while True:
        try:
            s = spoonprompt("Choose a category to review ('q' to quit)").lower()
        except KeyboardInterrupt:
            s = "q"
        if s in {"q", "quit"}:
            exit()
        try:
            cmd = commands[s]
        except KeyError:
            spoonerror(f"Invalid category. Try one of: {', '.join(idx["ready"].keys())}")
            continue
        manto_ids = idx["ready"][cmd]

def spoonerror(p: str):
    v = Fore.RED + p + Fore.RESET
    print(v)

def spoonprompt(p: str) -> str:
    v = Fore.BLUE + f"{p}: " + Fore.RESET
    return input(v).strip()


def wipe_terminal():
    print("\033[H\033[2J", end="")

def main(**kwargs):
    """
    main function
    """
    logger = logging.getLogger(sys._getframe().f_code.co_name)

    config_path = Path(kwargs["config"]).expanduser().resolve()
    config = get_config(config_path)

    cache_path = Path(user_cache_dir()) / "alignments.json"
    if not kwargs["fromcache"]:
        ingesters = configure_ingesters(config)
        ingest(ingesters)
        aligner = align(config, ingesters)
        alignment_groups = group_alignments(aligner, ingesters)
        concurrence(alignment_groups)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(alignment_groups, f, ensure_ascii=False, indent=4, sort_keys=True, cls=SetEncoder)
        del f
        logger.info(f"Cached alignment data at {cache_path}")
    else:
        with open(cache_path, "r", encoding="utf-8") as f:
            alignment_groups = json.load(f)
        del f
        logger.info(f"Loaded cached alignment data from {cache_path}")

    annotate(config, alignment_groups)
    idx = index(alignment_groups)

    spoonout(alignment_groups, idx)    




if __name__ == "__main__":
    main(
        **configure_commandline(
            OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL
        )
    )
