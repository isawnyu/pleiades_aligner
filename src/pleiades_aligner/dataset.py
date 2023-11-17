#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2023 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Define common classes for managing ingested datasets and their place records
"""

from logging import getLogger
from slugify import slugify


class DataSet:
    """
    A collection of places and related information corresponding to a single data set
    """

    def __init__(self, namespace: str, **kwargs):
        self.logger = getLogger("DataSet")

        self._set_namespace(namespace)

        self._places = dict()
        self._name_index = dict()

        for k, arg in kwargs.items():
            try:
                getattr(self, k)
            except AttributeError as err:
                self.logger.warning(
                    f"__init__() is setting uninitialized attribute {k}='{arg}', which was passed with kwargs"
                )
            setattr(self, k, arg)

    # namespace:
    # a read-only, non-zero-length, slug-like string
    # once initialized, it can only be set or changed directly by the DataSet object itself

    def _set_namespace(self, namespace: str):
        if not isinstance(namespace, str):
            raise TypeError(
                f"Expected type str for namespace argument, but got {type(namespace)}"
            )
        slug = slugify(namespace)
        if namespace != slug or namespace == "":
            raise ValueError(
                f"Expected slugifiable string like '{slug}' for namespace, but got '{namespace}'"
            )
        self._namespace = namespace

    @property
    def namespace(self):
        return self._namespace


class Place:
    """
    A record containing information about a single Place resource in a DataSet
    """

    def __init__(self, id: str, **kwargs):
        self.logger = getLogger("Place")

        self._set_id(id)

        self._alignments = set()
        self._geometries = list()
        self._name_strings = set()
        self._accuracy = 0.0  # assume unsigned decimal degrees
        self._centroid = None  # assume signed decimal degrees WGS84
        self._footprint = None  # assume signed decimal degrees WGS84

        for k, arg in kwargs.items():
            try:
                getattr(self, k)
            except AttributeError as err:
                self.logger.warning(
                    f"__init__() is setting uninitialized attribute {k}='{arg}', which was passed with kwargs"
                )
            setattr(self, k, arg)

    # id:
    # a read-only, non-zero-length string
    # once initialized, it can only be set or changed by the Place object itself

    def _set_id(self, id: str):
        if not isinstance(id, str):
            raise TypeError(f"Expected type str for id argument, but got {type(id)}")
        slug = id.strip()
        if id != slug or id == "":
            raise ValueError(
                f"Expected non-empty string for id argument, but got '{slug}'"
            )
        self._id = id

    @property
    def id(self):
        return self._id
