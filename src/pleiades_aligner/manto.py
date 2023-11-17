#
# This file is part of pleiades_aligner
# by Tom Elliott for the Institute for the Study of the Ancient World
# (c) Copyright 2023 by New York University
# Licensed under the AGPL-3.0; see LICENSE.txt file.
#

"""
Manage data from the MANTO project
"""
from pathlib import Path
from pleiades_aligner.ingester import IngesterCSV


class IngesterMANTO(IngesterCSV):
    def __init__(self, filepath: Path):
        IngesterCSV.__init__(self, namespace="manto", filepath=filepath)

    
