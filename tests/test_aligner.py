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
        assert (
            len(
                [
                    a
                    for a in self.aligner.alignments.values()
                    if a.has_id_namespace("pleiades")
                ]
            )
            == 19
        )
        assert (
            len(
                [
                    a
                    for a in self.aligner.alignments.values()
                    if a.has_id_namespace("chronique")
                ]
            )
            == 15
        )
        assert (
            len(
                [
                    a
                    for a in self.aligner.alignments.values()
                    if a.has_id_namespace("manto")
                ]
            )
            == 16
        )
        assert (
            len(
                [
                    a
                    for a in self.aligner.alignments.values()
                    if a.has_authority_namespace("manto")
                ]
            )
            == 16
        )
        assert (
            len(
                [
                    a
                    for a in self.aligner.alignments.values()
                    if a.has_id_namespace("geonames")
                ]
            )
            == 12
        )
        assert (
            len(
                [
                    a
                    for a in self.aligner.alignments.values()
                    if a.has_authority_namespace("chronique")
                ]
            )
            == 15
        )
