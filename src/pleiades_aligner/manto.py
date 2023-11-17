#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2023 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Manage data from the MANTO project
"""
from logging import getLogger
from pathlib import Path
from pleiades_aligner.ingester import IngesterCSV
import re


class IngesterMANTO(IngesterCSV):
    def __init__(self, filepath: Path):
        IngesterCSV.__init__(self, namespace="manto", filepath=filepath)
        self.logger = getLogger("IngesterMANTO")
        self.base_uri = "https://resource.manto.unh.edu/"
        self.rx_name_symbol = re.compile(r"^([^Α-Ωα-ωA-Za-zἌἨ]).+$")
        self.feature_types = {
            "🌍": "place",
            "🏛️": "monument",
            "🏛": "monument",
            "River": "river",
            "Mount": "mountain",
            "Spring": "spring",
            "island": "island",
            "mountain": "mountain",
            "river": "river",
            "mountain range": "mountain",
            "spring": "spring",
            "harbor": "harbor",
            "city": "settlement",
            "monument": "monument",
            "lake": "lake",
            "Lake": "lake",
            "💠": "theater",
            "theater": "theater",
        }
        self.rx_name_prefix = re.compile(r"^(River|Mount|Spring) .+$")
        self.rx_name_parenthetical = re.compile(r"^.*\((island)\).*$")
        self.rx_name_substring = re.compile(
            r"^.*(mountain range|mountain|river|harbor|spring|city|monument|lake)"
        )

    def ingest(self):
        IngesterCSV.ingest(self, unique_rows=False)
        self._digest()

    def _digest(self):
        self._set_titles_from_properties("{id}: {Name_1}")
