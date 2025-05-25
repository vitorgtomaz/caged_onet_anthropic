# CAGED & O*NET Data Pipeline

This repository contains a small collection of ETL scripts used to combine
Brazilian labor market data with O*NET occupational groups and task level
metrics from the Anthropic Economic Index (AEI).

The process produces time series on job movements and an occupational mapping of
automation and augmentation patterns.

## Repository Structure

- `AEI_ETL.py` – Processes AEI task data and aggregates automation/augmentation
  metrics by SOC minor group.
- `CAGED_ETL.py` – Downloads CAGED labor statistics using
  [basedosdados](https://basedosdados.org/), cleans the raw output and saves a
  parquet file.
- `ONET_ETL.py` – Builds a lookup table of O*NET minor groups from the provided
  SOC structure file.
- `main.py` – Merges the CAGED data with the crosswalks and classified
  occupation groups to generate analysis ready tables.
- `diff_diff.py` – Utilities to perform a basic difference-in-differences
  analysis on the aggregated time series in `data/output/time_series.csv`.
- `data/config/` – SQL queries and crosswalk files used by the ETL scripts.
- AEI task data is downloaded from the Hugging Face dataset
  [`Anthropic/EconomicIndex`](https://huggingface.co/datasets/Anthropic/EconomicIndex)
  when running the ETL notebook.
- `data/output/` – Generated datasets. This folder is excluded from version
  control.

## Running the Pipeline

The scripts are intended to be executed in the following order:

1. `python AEI_ETL.py`
2. `python CAGED_ETL.py`
3. `python ONET_ETL.py`
4. `python main.py`

`CAGED_ETL.py` requires a Google Cloud project ID in the environment variable
`BILLING_ID` to query BigQuery via `basedosdados`. The example SQL queries reside
in `data/config/`.

Each script reads from `data/input/` and writes its results to `data/output/`.
The analysis notebooks in the repository demonstrate how to load the generated
files for further exploration.
