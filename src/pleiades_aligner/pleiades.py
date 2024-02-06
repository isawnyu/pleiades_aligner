#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2023 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Manage data from the Pleiades project
"""

from logging import getLogger
from pathlib import Path
from pleiades_aligner.dataset import DataSet, Place
from pleiades_aligner.ingester import IngesterBase
from pleiades_local.filesystem import PleiadesFilesystem
from pprint import pformat
from shapely.geometry import shape

SUPPORTED_ALIGNMENTS = {
    "chronique toponyms": {
        "uri_base": "https://chronique.efa.gr/?kroute=topo_public&id=",
        "namespace": "chronique",
    },
    "manto": {"uri_base": "https://resource.manto.unh.edu/", "namespace": "manto"},
    "topostext": {"uri_base": "https://topostext.org/place/", "namespace": "topostext"},
    "wikidata": {"uri_base": "https://wikidata.org/wiki/", "namespace": "wikidata"},
    "geonames": {"uri_base": "https://www.geonames.org/", "namespace": "geonames"},
}


class IngesterPleiades(IngesterBase):
    def __init__(self, filepath: Path):
        IngesterBase.__init__(self, namespace="pleiades", filepath=filepath)
        self.logger = getLogger("IngesterPleiades")
        self.base_uri = "https://pleiades.stoa.org/places/"
        self._pleiades_file_system = PleiadesFilesystem(root=filepath)

    def ingest(self):
        places = list()
        for pid in self._pleiades_file_system.get_pids():
            datum = self._pleiades_file_system.get(pid)
            p = Place(id=pid)

            p.title = datum["title"].strip()
            # alignments
            alignment_ids = set()
            for p_ref in datum["references"]:
                uri = p_ref["accessURI"].strip()
                if uri:
                    for sup in SUPPORTED_ALIGNMENTS.values():
                        if uri.startswith(sup["uri_base"]):
                            alignment_ids.add(
                                ":".join(
                                    (sup["namespace"], uri[len(sup["uri_base"]) :])
                                )
                            )
            if alignment_ids:
                p.alignments = alignment_ids

            # geometries
            for p_loc in datum["locations"]:
                if p_loc["geometry"]:
                    g = shape(p_loc["geometry"])
                    p.add_geometries(g)
                    if p_loc["accuracy_value"]:
                        if isinstance(p_loc["accuracy_value"], float):
                            p.set_accuracy_if_larger(
                                g.centroid, p_loc["accuracy_value"], "meters"
                            )

            # names
            name_strings = set()
            for p_name in datum["names"]:
                if p_name["attested"]:
                    name_strings.add(p_name["attested"])
                for n in p_name["romanized"].split(","):
                    if n.strip():
                        name_strings.add(n.strip())
            if name_strings:
                p.names = name_strings

            places.append(p)

            # place types
            p.feature_types = set(datum["placeTypes"])
        if places:
            self.data.places = places
        self._digest()

    def _digest(self):
        pass
