#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2023 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
top level
"""

from pathlib import Path
from pleiades_aligner.aligner import Aligner
from pleiades_aligner.chronique import IngesterChronique
from pleiades_aligner.manto import IngesterMANTO
from pleiades_aligner.pleiades import IngesterPleiades
from pleiades_aligner.topostext import IngesterTopostext


def configure_ingester(
    namespace: str, file_path: Path
) -> IngesterChronique | IngesterMANTO | IngesterPleiades | IngesterTopostext:
    if namespace == "chronique":
        ingester = IngesterChronique(file_path)
    elif namespace == "manto":
        ingester = IngesterMANTO(file_path)
    elif namespace == "pleiades":
        ingester = IngesterPleiades(file_path)
    elif namespace == "topostext":
        ingester = IngesterTopostext(file_path)
    else:
        raise NotImplementedError(f"No supported ingester for namespace '{namespace}'")
    return ingester
