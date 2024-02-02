#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2024 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Manage data from the Topostext project
"""
from logging import getLogger
from pathlib import Path
from pleiades_aligner.ingester import IngesterWHGJSON


class IngesterTopostext(IngesterWHGJSON):
    def __init__(self, filepath: Path):
        self.base_uri = "https://topostext.org/place/"
        IngesterWHGJSON.__init__(
            self, namespace="chronique", filepath=filepath, base_uri=self.base_uri
        )
        self.logger = getLogger("IngesterTopostext")

    def ingest(self):
        IngesterWHGJSON.ingest(self)
        self._digest()

    def _digest(self):
        self._set_titles_from_properties("Place {id}: {title}")
        alignment_base_uris = {
            "https://pleiades.stoa.org/places/": {
                "namespace": "pleiades",
                "prefix": "",
            },
            "http://dare.ht.lu.se/places/": {"namespace": "dare", "prefix": ""},
            "https://www.wikidata.org/wiki/": {"namespace": "wikidata", "prefix": ""},
        }
        alignment_fields = {
            "fieldname": "close_matches",
            "namespaces": [
                {
                    "namespace": "pleiades",
                    "prefix": "https://pleiades.stoa.org/places/",
                },
                {
                    "namespace": "pleiades",
                    "prefix": "http://pleiades.stoa.org/places/",
                },
                {"namespace": "dare", "prefix": "http://dare.ht.lu.se/places/"},
                {"namespace": "wikidata", "prefix": "https://www.wikidata.org/wiki/"},
            ],
        }
        self._set_alignments_from_properties(alignment_fields)
