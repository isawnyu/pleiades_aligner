#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2023 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the pleiades_aligner.chronique module
"""

from pathlib import Path
from pprint import pformat, pprint
from pleiades_aligner.chronique import IngesterChronique
from pytest import raises
from shapely import Point

data_path = Path("tests/data")


class TestIngesterChronique:
    def test_init(self):
        with raises(TypeError):
            IngesterChronique()

    def test_load(self):
        whence = data_path / "chronique" / "chronique_example.csv"
        i = IngesterChronique(filepath=whence)
        i.ingest()
        assert len(i.data) == 14
        place = i.data.get_place_by_id("10035")
        assert place.title == "Toponym 10035: Neon Petritsion, Vetrina, Vetren"
        assert place.names == {
            "Neon Petritsion",
            "Vetrina",
            "Vetren",
            "Δ.Δ.Νέου Πετριτσίου",
        }
        assert place.alignments == {"geonames:734947"}
        assert place.feature_types == {"municipality"}

        place = i.data.get_place_by_id("1083")
        assert place.alignments == {"pleiades:589694", "geonames:264858"}
        assert place.centroid == Point([24.1, 35.216667])
