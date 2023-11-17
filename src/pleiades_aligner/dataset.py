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


class DataSet:
    """
    A collection of places and related information corresponding to a single data set
    """

    def __init__(self, namespace: str, **kwargs):
        self.logger = getLogger("DataSet")

        self._namespace = namespace

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

    @property
    def namespace(self):
        return self._namespace


class Place:
    """
    A record containing information about a single Place resource in a DataSet
    """

    def __init__(self, id: str, **kwargs):
        self.logger = getLogger("Place")

        self._id = id

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

    @property
    def id(self):
        return self._id
