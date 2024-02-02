#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the pleiades_aligner.topostext module"""

from pathlib import Path
from pleiades_aligner.topostext import IngesterTopostext
from pytest import raises
from shapely import Point

data_path = Path("tests/data")


class TestIngesterTopostext:
    def test_init(self):
        with raises(TypeError):
            IngesterTopostext()

    def test_load(self):
        whence = data_path / "topostext" / "topostext_example.json"
        i = IngesterTopostext(filepath=whence)
        i.ingest()
        assert len(i.data) == 18
        pid = i.data.pids[0]
        assert pid == "257326PThe"
        place = i.data.get_place_by_id(pid)
        assert place.title == "Place 257326PThe: Thebes (Egypt)"
        assert place.names == {"Thebes", "Θήβαι", "Θῆβαι"}
        # assert place.alignments == {"pleiades:786017", "wikidata:Q101583", "dare:21107"}
        assert place.alignments == {"pleiades:786017", "dare:21107", "wikidata:Q101583"}
        
        assert place.centroid == Point([32.641, 25.684])
