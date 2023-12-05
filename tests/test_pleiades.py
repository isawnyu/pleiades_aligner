#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2023 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the pleaides_aligner.pleiades module
"""

from pathlib import Path
from pleiades_aligner.pleiades import IngesterPleiades
from pytest import raises

data_path = Path("tests/data")


class TestIngesterPleiades:
    def test_init(self):
        with raises(TypeError):
            IngesterPleiades()

    def test_load(self):
        whence = data_path / "pleiades" / "pleiades_example"
        i = IngesterPleiades(filepath=whence)
        i.ingest()
        assert len(i.data) == 1391
        place = i.data.get_place_by_id("837")
        assert place.names == {"Asia Minor"}
        # assert place.title == "837: Asia Minor"
        place = i.data.get_place_by_id("20521")
        assert round(place.accuracy, 3) == 0.146
        cc = list(place.centroid.coords)[0]
        cc = [round(c, 6) for c in cc]
        assert cc == [18.519463, 51.893773]
        assert round(place.footprint.length, 5) == 0.91527
        place = i.data.get_place_by_id("727070")
        assert place.alignments == {"manto:11015142"}
        place = i.data.get_place_by_id("590095")
        assert place.alignments == {"chronique:16315"}
