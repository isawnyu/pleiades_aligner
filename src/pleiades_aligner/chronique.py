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
        IngesterCSV.ingest(
            self, id_clean={"strip-prefix": 'GA_OPE_EDIT" target="_blank">'}
        )
        self._digest()

    def _digest(self):
        self._set_titles_from_properties("Toponym {id}: {Full_name}")
        name_fields = ["Greekname", "Full_name"]
        self._set_names_from_properties(name_fields)
        alignment_fields = {
            "Pleiades_id": {"namespace": "pleiades", "prefix": ""},
            "Geoname_id": {"namespace": "geonames", "prefix": ""},
        }
        self._set_alignments_from_properties(alignment_fields)
