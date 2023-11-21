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
from shapely import (
    GeometryCollection,
    Point,
    LinearRing,
    LineString,
    Polygon,
    MultiPoint,
    MultiPolygon,
    MultiLineString,
)
from shapely.geometry import box
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

    # places
    @property
    def pids(self):
        return list(self._places.keys())

    @property
    def places(self):
        return list(self._places.values())

    @places.setter
    def places(self, values=list()):
        if not isinstance(values, list):
            raise TypeError(
                f"Expected type list for values argument, but got {type(values)}"
            )
        fails = [p for p in values if not isinstance(p, Place)]
        if fails:
            fail_types = {type(f) for f in fails}
            raise TypeError(
                "One or more items in values argument is not of type Place: {fail_types}"
            )
        self._places = {p.id: p for p in values}
        self.reindex()

    def get_place_by_id(self, id: str):
        try:
            return self._places[id]
        except KeyError as err:
            raise KeyError(
                f"Requested placeid {self.namespace}:{id}, but it has not been ingested."
            ) from err

    def reindex(self):
        for pid, p in self._places.items():
            try:
                p.names
            except AttributeError:
                pass
            else:
                for n in p.names:
                    slug = slugify(n)
                    try:
                        self._name_index[slug]
                    except KeyError:
                        self._name_index[slug] = dict()
                    finally:
                        self._name_index[slug][pid] = 1

    def __len__(self):
        return len(self.places)


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
        self.accuracy = 0.0  # assume unsigned decimal degrees
        self.feature_types = set()
        self._centroid = None  # assume signed decimal degrees WGS84
        self._footprint = None  # assume signed decimal degrees WGS84
        self._bin = None  # n x n degree bin into which the footprint fits
        self.raw_properties = dict()

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

    # Alignments
    @property
    def alignments(self) -> set:
        return self._alignments

    @alignments.deleter
    def alignments(self):
        self._alignments = set()

    @alignments.setter
    def alignments(self, values: [tuple, list, set, str, None]):
        if values is None:
            del self.alignments
        elif isinstance(values, set):
            self._alignments = values
        elif isinstance(values, str):
            if values:
                self._alignments = {
                    values,
                }
            else:
                del self.alignments
        elif isinstance(values, (tuple, list)):
            self._alignments = set(values)
        else:
            raise TypeError(
                f"Expected tuple, list, set, or str, but got {type(values)}"
            )

    def add_alignment(self, value: str):
        if value:
            self._alignments.add(value)

    # Geometries

    @property
    def geometries(self) -> GeometryCollection:
        return self._geometries

    @geometries.deleter
    def geometries(self):
        self._geometries = None

    @geometries.setter
    def geometries(
        self,
        values: [
            GeometryCollection,
            LinearRing,
            LineString,
            list,
            MultiLineString,
            MultiPoint,
            MultiPolygon,
            Point,
            Polygon,
            set,
            tuple,
            None,
        ],
    ):
        if not values or values is None:
            del self.geometries
        elif isinstance(values, GeometryCollection):
            self._geometries = values
        elif isinstance(values, list):
            self._geometries = GeometryCollection(values)
        elif isinstance(
            values,
            (
                LinearRing,
                LineString,
                MultiLineString,
                MultiPoint,
                MultiPolygon,
                Point,
                Polygon,
            ),
        ):
            self._geometries = GeometryCollection(
                [
                    values,
                ]
            )
        elif isinstance(values, (tuple, set)):
            self._geometries = GeometryCollection(list(values))
        self._recalculate_spatial_metadata()

    def add_geometries(
        self,
        values: [
            GeometryCollection,
            LinearRing,
            LineString,
            list,
            MultiLineString,
            MultiPoint,
            MultiPolygon,
            Point,
            Polygon,
            set,
            tuple,
        ],
    ):
        if not values or values is None:
            pass
        elif isinstance(values, GeometryCollection):
            gg = set(self.geometries.geoms)
            gg.update(values.geoms)
            self._geometries = GeometryCollection(list(gg))
        elif isinstance(values, (list, tuple)):
            gg = set(self.geometries.geoms)
            gg.update(values)
            self._geometries = GeometryCollection(list(gg))
        elif isinstance(
            values,
            (
                LinearRing,
                LineString,
                MultiLineString,
                MultiPoint,
                MultiPolygon,
                Point,
                Polygon,
            ),
        ):
            gg = set(self.geometries.geoms)
            gg.add(values)
            self._geometries = GeometryCollection(list(gg))
        self._recalculate_spatial_metadata()

    def remove_geometries(self):
        raise NotImplementedError

    @property
    def bin(self):
        return self._bin

    @property
    def centroid(self):
        return self._centroid

    @property
    def footprint(self):
        return self._footprint

    def _recalculate_spatial_metadata(self):
        if self._geometries is None:
            self._footprint = None
            self._centroid = None
        else:
            if self.accuracy:
                gg = GeometryCollection(
                    [g.buffer(self.accuracy) for g in self._geometries.geoms]
                )
                self._footprint = gg.convex_hull
                self._centroid = gg.centroid
            else:
                self._footprint = self._geometries.convex_hull
                self._centroid = self._geometries.centroid
        # now, bin it
        if isinstance(self._footprint, Point):
            bounds = self._footprint.buffer(0.00001).bounds
        else:
            bounds = self._footprint.bounds
        min_x, min_y, max_x, max_y = bounds
        round_bounds = [
            float(int(min_x)),
            float(int(min_y)),
            float(1 + int(max_x)),
            float(1 + int(max_y)),
        ]
        self._bin = box(*round_bounds)

    # Names

    @property
    def names(self) -> set:
        return self._names

    @names.deleter
    def names(self):
        self._names = set()

    @names.setter
    def names(self, values: [tuple, list, set, str, None]):
        if values is None:
            del self.names
        elif isinstance(values, set):
            self._names = values
        elif isinstance(values, str):
            if values:
                self._names = {
                    values,
                }
            else:
                del self.names
        elif isinstance(values, (tuple, list)):
            self._names = set(values)
        else:
            raise TypeError(
                f"Expected tuple, list, set, or str, but got {type(values)}"
            )

    def add_names(self, values: [tuple, list, set, str, None]):
        if values is None:
            return
        if values:
            if isinstance(values, (set, tuple, list)):
                self._names.update(values)
            elif isinstance(values, str):
                self._names.add(values)
            else:
                raise TypeError(
                    f"Expected tuple, list, set, or str, but got {type(values)}"
                )

    def remove_names(self, values: [tuple, list, set, str, None]):
        if values is None:
            return
        if values:
            if isinstance(values, str):
                self._names.discard(values)
            elif isinstance(values, (tuple, list, set)):
                self._names = self._names.difference(values)
            else:
                raise TypeError(
                    f"Expected tuple, list, set, or str, but got {type(values)}"
                )
