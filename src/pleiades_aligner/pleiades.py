#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2023 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Manage data from the Pleiades project
"""

from logging import getLogger
from pathlib import Path
from pleiades_aligner.dataset import DataSet, Place
from pleiades_aligner.ingester import IngesterBase
from pleiades_local.filesystem import PleiadesFilesystem


class IngesterPleiades(IngesterBase):
    def __init__(self, filepath: Path):
        IngesterBase.__init__(self, namespace="pleiades", filepath=filepath)
        self.logger = getLogger("IngesterPleiades")
        self.base_uri = "https://pleiades.stoa.org/places/"
        self._pleiades_file_system = PleiadesFilesystem(root=filepath)

    def ingest(self):
        places = list()
        for pid in self._pleiades_file_system.get_pids():
            datum = self._pleiades_file_system.get(pid)
            p = Place(id=pid)
            # alignments
            # geometries
            # names
            places.append(p)
        if places:
            self.data.places = places
        self._digest()

    def _digest(self):
        pass
