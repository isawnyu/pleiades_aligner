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
        place_type_values = {
            "PPL": "populated place",
            "BAY": "bay",
            "DD": "municipality",
            "PASS": "pass",
            "CAPE": "cape",
            "ANS": "archaeological/prehistoric site",
            "SD": "sound",
            "STM": "stream",
            "MT": "mountain",
            "PK": "peak",
            "HLL": "hill",
            "HBR": "harbor",
            "RGN": "region",
            "PPLX": "section of populated place",
            "PT": "point",
            "RDGE": "ridge",
            "CHNM": "marine channel",
            "MTS": "mountains",
            "PPLR": "religious populated place",
            "RSTP": "railroad stop",
            "ISL": "island",
            "ADMD": "administrative division",
            "LK": "lake",
            "LBED": "lake bed",
            "ISLS": "islands",
            "MSTY": "monastery",
            "LGN": "lagoon",
            "GULF": "gulf",
            "AIRP": "airport",
            "RSTN": "railroad station",
            "PEN": "peninsula",
            "STMX": "section of stream",
            "STRT": "strait",
            "ISTH": "isthmus",
            "CNLN": "navigation canal",
            "GRGE": "gorge",
            "PPLA": "seat of a first-order administrative division",
            "ADM1": "first-order administrative division",
            "ADM2": "second-order administrative division",
            "FT": "fort",
            "VAL": "valley",
            "RSV": "reservoir",
            "SPUR": "spur",
            "CHN": "channel",
            "ADM3": "third-order administrative division",
            "LCTY": "locality",
            "RK": "rock",
            "CH": "church",
            "HLLS": "hills",
            "STMM": "stream mouth",
            "DEME": "deme",
            "FRST": "forest",
            "PPLQ": "abandoned populated place",
            "STMI": "intermittent stream",
            "PRT": "port",
            "CSTL": "castle",
            "PLN": "plain",
            "ARCH": "arch",
        }
        self._set_feature_types_from_properties(
            fieldname="Dsg", feature_types=place_type_values
        )
        alignment_fields = {
            "Pleiades_id": {"namespace": "pleiades", "prefix": ""},
            "Geoname_id": {"namespace": "geonames", "prefix": ""},
        }
        self._set_alignments_from_properties(alignment_fields)
