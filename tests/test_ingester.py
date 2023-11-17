#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2023 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the pleiades_aligner.ingester module
"""
from pathlib import Path
from pprint import pformat, pprint
from pleiades_aligner.ingester import IngesterCSV
from pleiades_aligner.dataset import DataSet
from pytest import raises

data_path = Path("tests/data")


class TestIngesterCSV:
    def test_init(self):
        with raises(TypeError):
            IngesterCSV()

    def test_load_unique(self):
        whence = data_path / "chronique" / "chronique_example.csv"
        i = IngesterCSV(namespace="chronique", filepath=whence)
        i.ingest()
        assert len(i.data) == 13

    def test_load_nonunique(self):
        whence = data_path / "manto" / "manto_example.csv"
        i = IngesterCSV(namespace="manto", filepath=whence)
        i.ingest(unique_rows=False)
        assert len(i.data) == 16
