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
from shapely import distance


class Alignment:
    def __init__(
        self,
        id_1: str,
        id_2: str,
        mode: str,
        authority: str = None,
        proximity: str = None,
    ):
        self._aligned_ids = {id_1, id_2}
        self._namespaces = {id.split(":")[0] for id in self._aligned_ids}
        if authority:
            self._authorities = {
                authority,
            }
        else:
            self._authorities = set()
        self._authority_namespaces = {a.split(":")[0] for a in self._authorities}
        self.supported_modes = ["assertion", "proximity"]
        if mode in self.supported_modes:
            self._modes = {
                mode,
            }
        else:
            raise ValueError(f"Unsupported alignment mode '{mode}'")
        if proximity:
            self._proximity = {
                proximity,
            }
        else:
            self._proximity = set()

    @property
    def aligned_ids(self) -> list:
        return sorted(list(self._aligned_ids))

    @property
    def id_namespaces(self):
        return self._namespaces

    def has_id_namespace(self, namespace: str) -> bool:
        return namespace in self._namespaces

    @property
    def authorities(self) -> set:
        return self._authorities

    def add_authority(self, authority: str):
        self._authorities.add(authority)
        self._authority_namespaces.add(authority.split(":")[0])

    @property
    def authority_namespaces(self):
        return self._authority_namespaces

    def has_authority_namespace(self, namespace: str) -> bool:
        return namespace in self._authority_namespaces

    @property
    def modes(self) -> set:
        return self._modes

    @property
    def proximity(self) -> set:
        return self._proximity

    def add_proximity(self, value: str):
        self._proximity.add(value)

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
        self._alignment_hashes_by_id_namespace = dict()
        self._alignment_hashes_by_authority_namespace = dict()
        self._alignment_hashes_by_full_id = dict()
        self._alignment_hashes_by_mode = dict()

    def align(self, modes: list, **kwargs):
        for mode in modes:
            getattr(self, f"_align_{mode}")(**kwargs)

    def alignments_by_mode(self, mode: str) -> list:
        return [
            self.alignments[ahash] for ahash in self._alignment_hashes_by_mode[mode]
        ]

    def alignments_by_full_id(self, id: str) -> list:
        return [
            self.alignments[ahash] for ahash in self._alignment_hashes_by_full_id[id]
        ]

    def alignments_by_authority_namespace(self, namespace: str) -> list:
        try:
            self._alignment_hashes_by_authority_namespace[namespace]
        except KeyError:
            return set()
        else:
            return [
                self.alignments[ahash]
                for ahash in self._alignment_hashes_by_authority_namespace[namespace]
            ]

    def alignments_by_id_namespace(self, namespace: str) -> list:
        return [
            self.alignments[ahash]
            for ahash in self._alignment_hashes_by_id_namespace[namespace]
        ]

    def _align_assertions(self):
        """Record all alignments asserted in ingested data items"""
        self._alignment_hashes_by_mode["assertion"] = set()
        for namespace, ingester in self.ingesters.items():
            for place in ingester.data.places:
                full_place_id = ":".join((namespace, place.id))
                for target_id in place.alignments:
                    alignment = Alignment(
                        full_place_id,
                        target_id,
                        authority=full_place_id,
                        mode="assertion",
                    )
                    ahash = hash(alignment)
                    try:
                        self.alignments[ahash]
                    except KeyError:
                        self.alignments[ahash] = alignment
                    else:
                        raise NotImplementedError("assertion alignment hash collision")
                    # populate indexes
                    self._alignment_hashes_by_mode["assertion"].add(ahash)
                    for id in [full_place_id, target_id]:
                        try:
                            self._alignment_hashes_by_full_id[id]
                        except KeyError:
                            self._alignment_hashes_by_full_id[id] = set()
                        finally:
                            self._alignment_hashes_by_full_id[id].add(ahash)
                    for ns in alignment.authority_namespaces:
                        try:
                            self._alignment_hashes_by_authority_namespace[ns]
                        except KeyError:
                            self._alignment_hashes_by_authority_namespace[ns] = set()
                        finally:
                            self._alignment_hashes_by_authority_namespace[ns].add(ahash)
                    for ns in alignment.id_namespaces:
                        try:
                            self._alignment_hashes_by_id_namespace[ns]
                        except KeyError:
                            self._alignment_hashes_by_id_namespace[ns] = set()
                        finally:
                            self._alignment_hashes_by_id_namespace[ns].add(ahash)

    def _align_proximity(self, proximity_categories: dict):
        """Compare all ingested places to find possible associations by proximity"""
        self._alignment_hashes_by_mode["proximity"] = set()
        # sort all places into geometric bins
        bins = dict()
        for ingester in self.ingesters.values():
            for place in ingester.data.places:
                if place.bin:
                    try:
                        bins[place.bin]
                    except KeyError:
                        bins[place.bin] = set()
                    finally:
                        bins[place.bin].add(place)

        for geom, places in bins.items():
            print(f"{geom}: {len(places)}")
            for place_a in places:
                for cat_name, cat_params in proximity_categories.items():
                    for place_b in places:
                        if place_a != place_b:
                            val_a = getattr(place_a, cat_params[0])
                            val_b = getattr(place_b, cat_params[0])
                            if distance(val_a, val_b) <= cat_params[1]:
                                print(3 * "\n" + "WOOT" + 3 * "\n")
                                alignment = Alignment(
                                    place_a.id,
                                    place_b.id,
                                    mode="proximity",
                                    proximity=cat_params[0],
                                )
                                ahash = hash(alignment)
                                try:
                                    self.alignments[ahash]
                                except KeyError:
                                    self.alignments[ahash] = alignment
                                else:
                                    raise NotImplementedError(
                                        "assertion alignment hash collision"
                                    )
