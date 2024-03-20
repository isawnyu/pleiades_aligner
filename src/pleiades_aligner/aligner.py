#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2023 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Define the aligner class
"""
from copy import deepcopy
import functools
from haversine import haversine, Unit
from logging import getLogger
from pleiades_aligner.dataset import Place
from pprint import pformat
from shapely import distance as shapely_distance
from textnorm import normalize_space, normalize_unicode


@functools.cache
def distance(a, b):
    return shapely_distance(a, b)


class Alignment:
    def __init__(
        self,
        id_1: str,
        id_2: str,
        mode: str,
        authority: str = None,
        proximity: str = None,
        centroid_distance_dd: float = None,
        centroid_distance_m: float = None,
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
        self.supported_modes = [
            "assertion",
            "proximity",
            "inference",
            "toponymy",
            "typology",
        ]
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
        if centroid_distance_dd is not None:
            self.centroid_distance_dd = centroid_distance_dd
        if centroid_distance_m is not None:
            self.centroid_distance_m = centroid_distance_m

    @property
    def aligned_ids(self) -> list:
        return sorted(list(self._aligned_ids))

    def aligned_id_for_namespace(self, namespace: str) -> str:
        return [
            this_id.split(":")[-1]
            for this_id in self._aligned_ids
            if this_id.startswith(f"{namespace}:")
        ][0]

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

    def update_proximity(self, value: set):
        self._proximity.update(value)

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

    def asdict(self):
        d = {
            "aligned_ids": list(self.aligned_ids),
            "aligned_namespaces": list(self.id_namespaces),
            "authorities": sorted(self.authorities),
            "hash": hash(self),
            "modes": sorted(self.modes),
        }
        if "proximity" in self.modes:
            d["proximity"] = list(self.proximity)[0]
            try:
                self.centroid_distance_dd
            except AttributeError:
                pass
            else:
                d["centroid_distance_dd"] = self.centroid_distance_dd
            try:
                self.centroid_distance_m
            except AttributeError:
                pass
            else:
                d["centroid_distance_m"] = self.centroid_distance_m

        return d


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
        self._alignment_hashes_by_mode = {
            "inference": set(),
            "assertion": set(),
            "proximity": set(),
        }

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

    def _align_assertions(self, **kwargs):
        """Record all alignments asserted in ingested data items"""
        self.logger.info("Performing assertion alignments")
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
                    self._register_alignment(alignment)

    def _register_alignment(self, alignment: Alignment):
        this_alignment = alignment
        ahash = hash(this_alignment)
        try:
            self.alignments[ahash]
        except KeyError:
            self.alignments[ahash] = this_alignment
        else:
            # alignment already noted
            prior_alignment = self.alignments[ahash]
            this_alignment = deepcopy(prior_alignment)
            for authority_id in alignment.authorities:
                this_alignment.add_authority(authority_id)
            for mode in alignment.modes:
                this_alignment.add_mode(mode)
            if "proximity" in alignment.modes:
                for prox_class in alignment.proximity:
                    this_alignment.add_proximity(prox_class)
                try:
                    this_alignment.centroid_distance_dd = alignment.centroid_distance_dd
                except AttributeError:
                    self.logger.error(pformat(alignment.asdict(), indent=4))
                    self.logger.error(pformat(prior_alignment.asdict(), indent=4))
                    raise
                this_alignment.centroid_distance_m = alignment.centroid_distance_m

            self.alignments[ahash] = this_alignment

        # populate indexes
        for mode in this_alignment.modes:
            self._alignment_hashes_by_mode[mode].add(ahash)
        for id in this_alignment.aligned_ids:
            try:
                self._alignment_hashes_by_full_id[id]
            except KeyError:
                self._alignment_hashes_by_full_id[id] = set()
            finally:
                self._alignment_hashes_by_full_id[id].add(ahash)
        for ns in this_alignment.authority_namespaces:
            try:
                self._alignment_hashes_by_authority_namespace[ns]
            except KeyError:
                self._alignment_hashes_by_authority_namespace[ns] = set()
            finally:
                self._alignment_hashes_by_authority_namespace[ns].add(ahash)
        for ns in this_alignment.id_namespaces:
            try:
                self._alignment_hashes_by_id_namespace[ns]
            except KeyError:
                self._alignment_hashes_by_id_namespace[ns] = set()
            finally:
                self._alignment_hashes_by_id_namespace[ns].add(ahash)

    def _align_proximity(self, proximity_categories: dict, **kwargs):
        """Compare all ingested places to find possible associations by proximity"""
        self.logger.info("Performing proximity alignments")
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
                        bins[place.bin].add((ingester.data.namespace, place))

        for geom, places_info in bins.items():
            for place_a_namespace, place_a in places_info:
                for place_b_namespace, place_b in places_info:
                    if place_a_namespace == place_b_namespace:
                        continue
                    alignment = None
                    for cat_name, cat_params in proximity_categories.items():
                        attr_name = cat_params[0]
                        val_a = getattr(place_a, attr_name)
                        val_b = getattr(place_b, attr_name)
                        threshold = cat_params[1]
                        d = distance(val_a, val_b)
                        if d <= threshold:
                            place_a_full_id = ":".join((place_a_namespace, place_a.id))
                            place_b_full_id = ":".join((place_b_namespace, place_b.id))
                            if attr_name != "centroid":
                                d = distance(
                                    getattr(place_a, "centroid"),
                                    getattr(place_b, "centroid"),
                                )
                            alignment = Alignment(
                                place_a_full_id,
                                place_b_full_id,
                                mode="proximity",
                                proximity=cat_name,
                                centroid_distance_dd=d,
                                centroid_distance_m=self._d_centroid_meters(
                                    place_a, place_b
                                ),
                            )
                            self._register_alignment(alignment)
                            break

    def _d_centroid_meters(self, a: Place, b: Place):
        coords_a = list(list(a.centroid.coords)[0])
        coords_b = list(list(b.centroid.coords)[0])
        coords_a.reverse()
        coords_b.reverse()
        return haversine(coords_a, coords_b, unit=Unit.METERS)

    def _align_toponymy(self, apply_to_modes: list, **kwargs):
        self.logger.info(
            f"Performing toponomy alignment checks for alignment modes {apply_to_modes}"
        )
        candidate_hashes = set()
        for m in apply_to_modes:
            candidate_hashes.update(self._alignment_hashes_by_mode[m])
        places = dict()
        filtered_hashes = set()
        for chash in candidate_hashes:
            c = self.alignments[chash]
            consider = True
            for pid in c.aligned_ids:
                ns, rawid = pid.split(":")
                try:
                    i = self.ingesters[ns]
                except KeyError:
                    consider = False
                    break
                try:
                    p = i.data.get_place_by_id(rawid)
                except KeyError as err:
                    self.logger.error(f"During toponymy alignment: {str(err)}")
                    consider = False
                    break
                if not p.names:
                    consider = False
                    break
                places[pid] = p
            if consider:
                filtered_hashes.add(chash)
        for chash in filtered_hashes:
            c = self.alignments[chash]
            pid1, pid2 = c.aligned_ids
            names1 = {
                normalize_space(normalize_unicode(n)).lower()
                for n in places[pid1].names
            }
            names2 = {
                normalize_space(normalize_unicode(n)).lower()
                for n in places[pid2].names
            }
            common = names1.intersection(names2)
            if common:
                self.alignments[chash].add_mode("toponymy")

    def _align_typology(self, apply_to_modes: list, **kwargs):
        self.logger.info(
            f"Performing typology alignment checks for alignment modes {apply_to_modes}"
        )
        candidate_hashes = set()
        for m in apply_to_modes:
            candidate_hashes.update(self._alignment_hashes_by_mode[m])
        places = dict()
        filtered_hashes = set()
        for chash in candidate_hashes:
            c = self.alignments[chash]
            consider = True
            for pid in c.aligned_ids:
                ns, rawid = pid.split(":")
                try:
                    i = self.ingesters[ns]
                except KeyError:
                    consider = False
                    break
                try:
                    p = i.data.get_place_by_id(rawid)
                except KeyError as err:
                    consider = False
                    break
                if not p.feature_types:
                    consider = False
                    break
                places[pid] = p
            if consider:
                filtered_hashes.add(chash)
        for chash in filtered_hashes:
            c = self.alignments[chash]
            pid1, pid2 = c.aligned_ids
            common = places[pid1].feature_types.intersection(places[pid2].feature_types)
            if common:
                self.alignments[chash].add_mode("typology")

    def align_by_inference(
        self,
        primary_namespace: str,
        aligned_namespace: str,
        inference_namespace: str,
        **kwargs,
    ):
        """Record all alignments that can be inferred from chained assertions in ingested data items"""
        self.logger.info(
            f"Inferring alignments between {primary_namespace} and {inference_namespace} based on assertions found in {aligned_namespace} already matched with {primary_namespace}."
        )
        primary_alignments = {
            a
            for a in self.alignments_by_id_namespace(primary_namespace)
            if aligned_namespace in a.id_namespaces
        }
        candidate_alignments = {
            a
            for a in self.alignments_by_id_namespace(inference_namespace)
            if "assertion" in a.modes and aligned_namespace in a.id_namespaces
        }
        for candidate in candidate_alignments:
            aligned_id = [
                f
                for f in candidate.aligned_ids
                if not f.startswith(inference_namespace)
            ][0]
            these_primary = {
                a for a in primary_alignments if aligned_id in a.aligned_ids
            }
            if not these_primary:
                continue
            these_candidate = {
                a for a in candidate_alignments if aligned_id in a.aligned_ids
            }
            if not these_candidate:
                continue
            for this_primary in these_primary:
                primary_id = [
                    f
                    for f in this_primary.aligned_ids
                    if f.startswith(primary_namespace)
                ][0]
                for this_candidate in these_candidate:
                    inferred_id = [
                        f
                        for f in this_candidate.aligned_ids
                        if f.startswith(inference_namespace)
                    ][0]
                    new_alignment = Alignment(
                        primary_id, inferred_id, "inference", authority=aligned_id
                    )
                    self._register_alignment(new_alignment)
