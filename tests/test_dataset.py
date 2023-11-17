#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2023 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Test the pleiades_aligner.dataset module
"""
from pleiades_aligner.dataset import DataSet, Place
from pytest import raises


class TestDataSet:
    def test_init(self):
        with raises(TypeError):
            # namespace argument for the dataset is required
            d = DataSet()

    def test_init_with_valid_namespace(self):
        ns = "test_namespace"
        d = DataSet(namespace=ns)
        assert ns == d.namespace


class TestPlace:
    def test_init(self):
        with raises(TypeError):
            # id argument for the place is required
            Place()

    def test_init_with_valid_id(self):
        valid_id = "8675309"
        p = Place(id=valid_id)
        assert valid_id == p.id
