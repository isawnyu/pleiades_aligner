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
from pprint import pformat


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
            "pleiades": pleiades_aligner.IngesterPleiades(
                Path("tests/data/pleiades/pleiades_example")
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

        assert len(self.aligner.alignments_by_id_namespace("pleiades")) == 60
        assert len(self.aligner.alignments_by_id_namespace("chronique")) == 34
        assert len(self.aligner.alignments_by_id_namespace("geonames")) == 12
        assert len(self.aligner.alignments_by_id_namespace("manto")) == 38

        assert len(self.aligner.alignments_by_authority_namespace("pleiades")) == 43
        assert len(self.aligner.alignments_by_authority_namespace("chronique")) == 15
        assert len(self.aligner.alignments_by_authority_namespace("geonames")) == 0
        assert len(self.aligner.alignments_by_authority_namespace("manto")) == 17

        assert len(self.aligner.alignments_by_full_id("pleiades:589704")) == 2

        assert len(self.aligner.alignments_by_mode("assertion")) == 72

        aptera_chronique = {
            a
            for a in self.aligner.alignments_by_full_id("chronique:3891")
            if "pleiades:589704" in a.aligned_ids
        }
        assert len(aptera_chronique) == 1
        aptera_pleiades = {
            a
            for a in self.aligner.alignments_by_full_id("pleiades:589704")
            if "chronique:3891" in a.aligned_ids
        }
        assert len(aptera_pleiades) == 1
        aptera_both = aptera_chronique.intersection(aptera_pleiades)
        assert len(aptera_both) == 1

    def test_proximity(self):
        self.aligner.align(
            modes=["proximity"],
            proximity_categories={
                "identical": ("centroid", 0.0),
                "tight": ("centroid", 0.001),
                "overlapping": ("footprint", 0.0),
                "close": ("centroid", 0.01),
                "near": ("footprint", 0.001),
            },
        )
        assert len(self.aligner.alignments_by_mode("proximity")) == 23

        aptera_chronique = {
            a
            for a in self.aligner.alignments_by_full_id("chronique:3891")
            if "pleiades:589704" in a.aligned_ids
        }
        assert len(aptera_chronique) == 1
        aptera_pleiades = {
            a
            for a in self.aligner.alignments_by_full_id("pleiades:589704")
            if "chronique:3891" in a.aligned_ids
        }
        assert len(aptera_pleiades) == 1
        aptera_both = aptera_chronique.intersection(aptera_pleiades)
        assert len(aptera_both) == 1

    def test_multimodal(self):
        self.aligner.align(modes=["assertions"])
        asserted = set(self.aligner.alignments_by_mode("assertion"))
        assert len(asserted) == 72
        foo = {
            a
            for a in asserted
            if "pleiades:589704" in a.aligned_ids and "chronique:3891" in a.aligned_ids
        }
        assert len(foo) == 1
        assert list(foo)[0].modes == {"assertion"}

        self.aligner.align(
            modes=["proximity"],
            proximity_categories={
                "identical": ("centroid", 0.0),
                "tight": ("centroid", 0.001),
                "overlapping": ("footprint", 0.0),
                "close": ("centroid", 0.01),
                "near": ("footprint", 0.001),
            },
        )
        proximate = set(self.aligner.alignments_by_mode("proximity"))
        assert len(proximate) == 26
        bar = {
            a
            for a in proximate
            if "pleiades:589704" in a.aligned_ids and "chronique:3891" in a.aligned_ids
        }
        assert len(bar) == 1
        assert list(bar)[0].modes == {"proximity", "assertion"}

        them = {"proximity", "assertion"}
        both = {a for a in self.aligner.alignments.values() if them.issubset(a.modes)}
        assert len(both) == 3

        # NB: asserted was first set before proximities were run, so there have been changes
        # we need to pick up before testing intersection
        asserted = set(self.aligner.alignments_by_mode("assertion"))
        both_expected = asserted.intersection(proximate)
        assert len(both_expected) == 3
        baz = {
            a
            for a in both_expected
            if "pleiades:589704" in a.aligned_ids and "chronique:3891" in a.aligned_ids
        }
        assert len(baz) == 1
        assert list(baz)[0].modes == {"proximity", "assertion"}

    def test_inferences(self):
        self.aligner.align(modes=["assertions"])
        self.aligner.align_by_inference("pleiades", "chronique", "geonames")
        geonames = self.aligner.alignments_by_id_namespace("geonames")
        assert len(geonames) == 35
        inferred_geo = {a for a in geonames if "inference" in a.modes}
        assert len(inferred_geo) == 23
