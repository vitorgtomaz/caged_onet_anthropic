import pandas as pd
import json

# Loading data
caged = pd.read_parquet("data/input/caged_national.parquet")

# Generates a random sample from caged
caged_sample = caged.sample(frac=0.1)

CW_ONET_CBO = pd.read_csv(
    "data/config/cbo_onet_crosswalks.csv", encoding="utf-8", engine="python"
)

df = caged_sample.merge(CW_ONET_CBO, how="left", on=["cbo_subgroup"])

# Calculates the sum of net_jobs by cbo_subgroup with missing onet_code
total_missing = (
    df.loc[df["onet_code"].isna(), ["cbo_subgroup", "net_jobs"]]
    .groupby(["cbo_subgroup"])
    .agg({"net_jobs": "sum"})
    .reset_index()
)
