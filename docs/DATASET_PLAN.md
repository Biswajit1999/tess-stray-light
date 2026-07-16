# Dataset Plan

## Mode

**real public TESS light curves/TPFs**

## Official sources and literature seeds

- Ricker et al. 2015, DOI:10.1117/1.JATIS.1.1.014003, arXiv:1406.0151
- Jenkins et al. 2016 SPOC, DOI:10.1117/12.2233418
- MAST TESS archive documentation
- TESS quality-flag documentation
- Lightkurve official documentation/software paper

## Acquisition rules

- Prefer official mission/archive endpoints and author-maintained catalogue deposits.
- Record product identifier, query, retrieval UTC, source URL, file size, checksum and licence/terms.
- Do not commit large raw FITS, HDF5 or catalogue files.
- Store a deterministic manifest under `data/manifest.csv`.
- Store only a tiny, clearly labelled synthetic/example dataset in `data/example/`.
- Never replace inaccessible real data with fabricated values while presenting them as observations.

## Required manifest columns

`product_id, source, source_url, retrieved_utc, sha256, file_size_bytes, selection_reason, licence_or_terms`

## FAIR contract

Every derived product must point to the raw product ID, software commit, configuration hash and transformation script.
