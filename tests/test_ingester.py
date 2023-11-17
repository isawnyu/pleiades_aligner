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
from shapely import Point

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
        pid = i.data.pids[0]
        assert pid == 'GA_OPE_EDIT" target="_blank">10006'
        place = i.data.get_place_by_id(pid)
        assert place.centroid == Point([21.45, 38.05])
        assert set(place.raw_properties.keys()) == {
            "Geoname_id",
            "Pleiades_id",
            "Bsa_irn",
            "Lau1",
            "Lau2",
            "Full_name",
            "Greekname",
            "Dsg",
            "Date_created",
            "Date_modified",
            "Fk_id_cadastres",
            "Fk_id_regions",
            "Fk_id_pays",
        }

    def test_load_nonunique(self):
        whence = data_path / "manto" / "manto_example.csv"
        i = IngesterCSV(namespace="manto", filepath=whence)
        i.ingest(unique_rows=False)
        assert len(i.data) == 16
        place = i.data.get_place_by_id("11308325")
        assert place.centroid is None
        assert set(place.raw_properties.keys()) == {
            "Name_0",
            "Name_1",
            "Minimal Disambiguation",
            "Information",
            "Name (transliteration)",
            "Name (Greek font)",
            "Name (Latinized)",
            "Name in Latin texts",
            "Alternative names",
            "Alternative name",
            "Alternative name - Object ID",
            "Pleiades",
            "In",
            "In - Object ID",
        }
        place = i.data.get_place_by_id("11310538")
        assert place.raw_properties["Alternative names"] == {
            "River Lima",
            "River Belion",
            "River Limia",
        }
