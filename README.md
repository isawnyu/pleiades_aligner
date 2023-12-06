# pleiades_aligner

Software tools to align external datasets with [the Pleiades gazetteer of ancient places](https://pleiades.stoa.org).

This software is being written by [Tom Elliott](https://orcid.org/0000-0002-4114-6677) for the Pleiades project and [the Institute for the Study of the Ancient World](https://isaw.nyu.edu) at New York University.   
(c) Copyright 2023 by New York University   
Use, reuse, and remixing of this software is governed by the terms of the AGPL-3.0; see LICENSE.txt file for details.

## How to run a full alignment

```bash
python scripts/align.py --config=data/default_config.json
```

Now try:

```bash
python scripts/align.py -c data/chronique2pleiades_config.json -v > ~/scratch/alignments.json
```

## Next step

- [x] add support for Pleiades ingest
- [x] test proximity alignment with Pleiades
- [x] work on getting good chronique alignments
- [ ] refactor to move inferred alignments from the align script to the actual aligner module

## Supported Datasets

### MANTO

- namespace: manto

### Chronique

- namespace: chronique
