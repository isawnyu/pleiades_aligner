#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2023 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the pleiades_aligner.aligner module
"""
from pathlib import Path
import pleiades_aligner


class TestAligner:
    @classmethod
    def setup_class(cls):
        cls.ingesters = {
            "chronique": pleiades_aligner.IngesterChronique(
                Path("tests/data/chronique/chronique_example.csv")
            ),
            "manto": pleiades_aligner.IngesterMANTO(
                Path("tests/data/manto/manto_example.csv")
            ),
        }
        for ingester in cls.ingesters.values():
            ingester.ingest()
        cls.aligner = pleiades_aligner.Aligner(
            cls.ingesters,
            {
                "chronique": "tests/data/chronique/chronique_example.csv",
                "manto": "tests/data/manto/manto_example.csv",
            },
            redirects=dict(),
        )

    def test_assertions(self):
        self.aligner.align(modes=["assertions"])

        assert len(self.aligner.alignments_by_id_namespace("pleiades")) == 20
        assert len(self.aligner.alignments_by_id_namespace("chronique")) == 15
        assert len(self.aligner.alignments_by_id_namespace("geonames")) == 12
        assert len(self.aligner.alignments_by_id_namespace("manto")) == 17

        assert len(self.aligner.alignments_by_authority_namespace("pleiades")) == 0
        assert len(self.aligner.alignments_by_authority_namespace("chronique")) == 15
        assert len(self.aligner.alignments_by_authority_namespace("geonames")) == 0
        assert len(self.aligner.alignments_by_authority_namespace("manto")) == 17

        assert len(self.aligner.alignments_by_full_id("pleiades:589704")) == 2

        assert len(self.aligner.alignments_by_mode("assertion")) == 32
