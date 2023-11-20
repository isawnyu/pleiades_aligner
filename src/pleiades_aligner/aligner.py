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
    def __init__(self, id_1: str, id_2: str, authority: str, mode: str):
        self._aligned_ids = {id_1, id_2}
        self._namespaces = {id.split(":")[0] for id in self._aligned_ids}
        self._authorities = {
            authority,
        }
        self._authority_namespaces = {a.split(":")[0] for a in self._authorities}
        self.supported_modes = ["assertion"]
        if mode in self.supported_modes:
            self._modes = {
                mode,
            }
        else:
            raise ValueError(f"Unsupported alignment mode '{mode}'")

    @property
    def aligned_ids(self) -> list:
        return sorted(list(self._aligned_ids))

    def has_id_namespace(self, namespace: str) -> bool:
        return namespace in self._namespaces

    @property
    def authorities(self) -> set:
        return self._authorities

    def add_authority(self, authority: str):
        self._authorities.add(authority)
        self._authority_namespaces.add(authority.split(":")[0])

    def has_authority_namespace(self, namespace: str) -> bool:
        return namespace in self._authority_namespaces

    @property
    def modes(self) -> set:
        return self._modes

    def add_mode(self, mode: str):
        if mode in self.supported_modes:
            self._modes.add(mode)
        else:
            raise ValueError(f"Unsupported alignment mode '{mode}'")

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
                full_place_id = ":".join((namespace, place.id))
                for target_id in place.alignments:
                    alignment = Alignment(
                        full_place_id, target_id, full_place_id, "assertion"
                    )
                    ahash = hash(alignment)
                    try:
                        self.alignments[ahash]
                    except KeyError:
                        self.alignments[ahash] = alignment
                    else:
                        raise NotImplementedError("assertion alignment hash collision")
