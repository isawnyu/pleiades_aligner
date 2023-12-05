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
