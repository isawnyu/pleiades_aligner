#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2023 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Define the aligner class
"""
from logging import getLogger


class Alignment:
    def __init__(self, id_1: str, id_2: str):
        self._aligned_ids = {id_1, id_2}
        self._namespaces = {id.split(":")[0] for id in self._aligned_ids}

    @property
    def aligned_ids(self) -> list:
        return sorted(list(self._aligned_ids))

    def has_namespace(self, namespace: str) -> bool:
        return namespace in self._namespaces

    def __hash__(self):
        return hash(repr(self))

    def __repr__(self):
        return " >< ".join(self.aligned_ids)

    def __str__(self):
        return "<Alignment: " + " >< ".join(self.aligned_ids)


class Aligner:
    def __init__(self, ingesters: dict, data_sources: dict, redirects: dict):
        self.logger = getLogger("Aligner")
        self.ingesters = ingesters
        self.data_sources = data_sources
        self.redirects = redirects
        self.alignments = dict()

    def align(self, modes: list):
        for mode in modes:
            getattr(self, f"_align_{mode}")()

    def _align_assertions(self):
        """Record all alignments asserted in ingested data items"""
        for namespace, ingester in self.ingesters.items():
            for place in ingester.data.places:
                for target_id in place.alignments:
                    alignment = Alignment(":".join((namespace, place.id)), target_id)
                    ahash = hash(alignment)
                    try:
                        self.alignments[ahash]
                    except KeyError:
                        self.alignments[ahash] = alignment
                    else:
                        self.logger.error(f"collision: {alignment}")
