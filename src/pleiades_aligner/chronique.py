#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2023 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Manage data from the Chronique project
"""
from logging import getLogger
from pathlib import Path
from pleiades_aligner.ingester import IngesterCSV


class IngesterChronique(IngesterCSV):
    def __init__(self, filepath: Path):
        IngesterCSV.__init__(self, namespace="chronique", filepath=filepath)
        self.logger = getLogger("IngesterChronique")
        self.base_uri = "https://chronique.efa.gr/?kroute=topo_public&id="

    def ingest(self):
        IngesterCSV.ingest(self)
        self._digest()

    def _digest(self):
        pass
