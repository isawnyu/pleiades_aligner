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
        name_fields = [
            "Name_0",
            "Name_1",
            "Name (transliteration)",
            "Name (Greek font)",
            "Name (Latinized)",
            "Name in Latin texts",
            "Alternative names",
            "Alternative name",
        ]
        self._set_names_from_properties(name_fields)
        self._separate_names_and_types()

    def _separate_names_and_types(self):
        # some manto fields have embedded emojis for place type
        for p in self.data.places:
            p.feature_types = set()
            new_names = set()
            for n in p.names:
                m = self.rx_name_symbol.match(n)
                if m:
                    symbol = m.group(1)
                    try:
                        st = self.feature_types[symbol]
                    except KeyError as err:
                        raise RuntimeError(
                            f"Unrecognized MANTO symbol '{symbol}' in '{n}' for {p.uri}"
                        )
                    new_names.add(n[1:].strip())
                    p.feature_types.add(st)
                else:
                    new_names.add(n)
            if p.names != new_names:
                p.names = new_names
        # some manto fields have prefix words that indicate place type
        for p in self.data.places:
            new_names = set()
            for n in p.names:
                m = self.rx_name_prefix.match(n)
                if m:
                    p.feature_types.add(self.feature_types[m.group(1)])
                    new_names.add(self._norm_string(n[len(m.group(1)) :]))
            if new_names:
                p.add_names(new_names)
        # some manto fields have parenthetic words that indicate place type
        for p in self.data.places:
            for k, v in p.raw_properties.items():
                if k in ["Name_1", "Information", "Minimal Disambiguation"] and v:
                    m = self.rx_name_parenthetical.match(v)
                    if m:
                        p.feature_types.add(self.feature_types[m.group(1)])
        # some manto fields have plain-text substrings that indicate place type
        for p in self.data.places:
            for k, v in p.raw_properties.items():
                if k in ["Name_1", "Information", "Minimal Disambiguation"] and v:
                    m = self.rx_name_substring.match(v)
                    if m:
                        p.feature_types.add(self.feature_types[m.group(1)])
