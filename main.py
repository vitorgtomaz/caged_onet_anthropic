"""Merge CAGED job data with AEI occupation classifications."""

import pandas as pd
import json
import unicodedata


def strip_accents(text: str) -> str:
    """Return ``text`` without accent marks."""

    # 1) Decompose characters into base + combining marks (NFKD)
    #    e.g. "á" → "á"  (two code-points)
    decomposed = unicodedata.normalize("NFKD", text)
    # 2) Keep only the base characters (category != Mn = "Mark, Non-spacing")
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


# Loading data
caged = pd.read_parquet("data/input/caged_national.parquet")

CW_ONET_CBO = pd.read_csv(
    "data/config/cbo_onet_crosswalks.csv", encoding="utf-8", engine="python"
)

occ_aut_aug_class = pd.read_parquet("data/output/occ_aut_aug_lvl_classified.parquet")
occ_aut_aug_class.rename({"soc_minor_group": "onet_code"}, axis="columns", inplace=True)

CW_ONET_CBO["cbo_subgroup"] = CW_ONET_CBO["cbo_subgroup"].apply(strip_accents)

caged = caged.merge(CW_ONET_CBO, how="left", on="cbo_subgroup")
caged = caged.merge(occ_aut_aug_class, how="left", on="onet_code")


caged_f = caged[~caged["class"].isna()]

caged_f.loc["date"] = pd.to_datetime(
    caged_f["year"].astype(str) + caged_f["month"].astype(str), format="%Y%m"
)

general_trends = caged_f.groupby(["date", "class"])["net_jobs"].sum().reset_index()
general_trends.to_csv("data/output/time_series.csv", index=False)

jobs = caged_f.groupby(["cbo_subgroup", "class"])["net_jobs"].sum().reset_index()

