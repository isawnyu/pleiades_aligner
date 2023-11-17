#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2023 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Define common classes for ingesting different datasets
"""
import chardet
import codecs
from collections import Counter
from encoded_csv import get_csv
from logging import getLogger
import os
from pathlib import Path
from pleiades_aligner.dataset import DataSet, Place
from pprint import pformat
from shapely import Point
from textnorm import normalize_space, normalize_unicode

FIELDNAME_GUESSES = {
    "id": ["id", "Object ID", "item"],
    "latitude": ["lat", "latitude"],
    "longitude": ["lon", "long", "longitude"],
}


class IngesterBase:
    def __init__(self, namespace: str, filepath: Path):
        self.logger = getLogger(f"{namespace.capitalize()}Ingester")
        self.data = DataSet(namespace=namespace)
        self.filepath = filepath

    def _set_titles_from_properties(self, format_string: str):
        for place in self.data.places:
            try:
                place.title = format_string.format(**place.raw_properties, id=place.id)
            except KeyError as err:
                raise KeyError(pformat(place.raw_properties, indent=4)) from err

    def _norm_string(self, s: str) -> str:
        return normalize_space(normalize_unicode(s))

    def _set_names_from_properties(self, fieldnames: list):
        for place in self.data.places:
            names = set()
            for fn in fieldnames:
                raw = place.raw_properties[fn]
                if raw is None:
                    continue
                if isinstance(raw, str):
                    clean = {self._norm_string(r) for r in raw.split(",")}
                elif isinstance(raw, (list, set)):
                    clean = {self._norm_string(r) for r in raw}
                clean = {c for c in clean if c}
                if not clean:
                    continue
                clean = [
                    c for c in clean if not c.startswith("(") and not c.endswith(")")
                ]
                names.update(clean)
            place.names = names


class IngesterCSV(IngesterBase):
    def __init__(self, namespace: str, filepath: Path = None):
        IngesterBase.__init__(self, namespace, filepath)

    def ingest(self, unique_rows=True):
        raw_data, fieldnames = self._load_csv()
        if unique_rows:
            self._ingest_unique_rows(raw_data, fieldnames)
        else:
            self._ingest_nonunique_rows(raw_data, fieldnames)

    def _guess_csv_field(self, fieldnames: str, candidates: str) -> str:
        """
        Pick the field with a name from a range of candidates
        Returns the first value in fieldnames that matches a value in candidates
        Returns NONE if no match
        """
        lower_fieldnames = [f.lower() for f in fieldnames]
        lower_candidates = [c.lower() for c in candidates]
        for fn in lower_candidates:
            try:
                i = lower_fieldnames.index(fn)
            except ValueError:
                continue
            else:
                return fieldnames[i]  # sic
        return None

    def _ingest_nonunique_rows(self, raw_data: list, fieldnames: list):
        id_key = self._guess_csv_field(fieldnames, FIELDNAME_GUESSES["id"])
        lat_key = self._guess_csv_field(fieldnames, FIELDNAME_GUESSES["latitude"])
        lon_key = self._guess_csv_field(fieldnames, FIELDNAME_GUESSES["longitude"])
        other_keys = [k for k in fieldnames if k != id_key]
        places = dict()
        for datum in raw_data:
            this_pid = datum[id_key]
            try:
                place = places[this_pid]
            except KeyError:
                place = Place(id=this_pid)
            if lat_key and lon_key:
                place.add_geometries(Point([datum[lon_key], datum[lat_key]]))
                other_keys = [k for k in other_keys if k not in (lat_key, lon_key)]
            for k in other_keys:
                new_values = self._norm_string(datum[k])
                try:
                    values = place.raw_properties[k]
                except KeyError:
                    place.raw_properties[k] = new_values
                else:
                    if isinstance(values, str):
                        if values != new_values:
                            place.raw_properties[k] = {values, new_values}
                    elif isinstance(values, set):
                        place.raw_properties[k].add(new_values)
            places[this_pid] = place
        if places:
            self.data.places = list(places.values())

    def _ingest_unique_rows(self, raw_data: list, fieldnames: list):
        id_key = self._guess_csv_field(fieldnames, FIELDNAME_GUESSES["id"])
        lat_key = self._guess_csv_field(fieldnames, FIELDNAME_GUESSES["latitude"])
        lon_key = self._guess_csv_field(fieldnames, FIELDNAME_GUESSES["longitude"])
        other_keys = [k for k in fieldnames if k != id_key]
        places = list()
        for datum in raw_data:
            p = Place(id=datum[id_key])
            if lat_key and lon_key:
                p.geometries = [Point([datum[lon_key], datum[lat_key]])]
                other_keys = [k for k in other_keys if k not in (lat_key, lon_key)]
            p.raw_properties = {k: datum[k] for k in other_keys}
            places.append(p)
        if places:
            self.data.places = places

    def _load_csv(self) -> tuple:
        """
        Load data from CSV
        Attempts to guess encoding, dialect, and fieldnames of CSV file
        Returns a tuple:
        - data: list of dictionaries, one per row in row order
        - fieldnames: list of fieldnames, which are keys in the data dictionaries
        """

        fieldnames = self._detect_redundant_fieldnames(self.filepath)
        try:
            colxn = get_csv(
                str(self.filepath),
                skip_lines=1,
                fieldnames=fieldnames,
                sample_lines=1000,
            )
        except UnicodeDecodeError as err:
            self.logger.error(
                f"UnicodeDecodeError trying to read {self.filepath} with encoded_csv.get_csv"
            )
            raise err
        return (colxn["content"], colxn["fieldnames"])

    def _detect_redundant_fieldnames(self, filepath: Path) -> list:
        """
        Returns a list of fieldnames that disambiguate repeated/redundant fieldnames
        """
        whence = str(filepath)
        num_bytes = min(1024, os.path.getsize(whence))
        raw = open(whence, "rb").read(num_bytes)
        if raw.startswith(codecs.BOM_UTF8):
            file_encoding = "utf-8-sig"
        else:
            file_encoding = chardet.detect(raw)["encoding"]
        with open(whence, "r", encoding=file_encoding) as f:
            first_line = f.readline()
        del f
        headers = [h.strip() for h in first_line.split(",")]
        header_counts = Counter(headers)
        handled = set()
        if [k for k, v in header_counts.items() if v > 1]:
            fieldnames = list()
            for h in headers:
                if h in handled:
                    continue
                if header_counts[h] == 1:
                    fieldnames.append(h)
                else:
                    for i in range(0, header_counts[h]):
                        fieldnames.append(f"{h}_{i}")
                handled.add(h)
            return fieldnames
        else:
            return headers
