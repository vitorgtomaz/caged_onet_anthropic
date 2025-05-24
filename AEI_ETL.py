"""Generate AEI occupation level metrics.

This script merges Anthropic Economic Index (AEI) task data with the
Standard Occupational Classification (SOC) structure in order to compute
automation and augmentation ratios by SOC minor group. The resulting
tables are written to ``data/output`` for further analysis.
"""

import pandas as pd
import numpy as np


def merge_onet_soc_data() -> pd.DataFrame:
    """Merge O*NET task statements with SOC major group titles.

    The CSV paths are fixed inside the function and point to the files in
    ``data/input/aei_data``.

    Returns
    -------
    pandas.DataFrame
        DataFrame with task statements and their corresponding SOC major group
        titles.
    """

    # Read and process O*NET data
    onet_df = pd.read_csv("data/input/aei_data/onet_task_statements.csv")
    onet_df["soc_major_group"] = onet_df["O*NET-SOC Code"].str[:2]

    # Read and process SOC data
    soc_df = pd.read_csv("data/input/aei_data/SOC_Structure.csv")
    soc_df = soc_df.dropna(subset=["Major Group"])
    soc_df["soc_major_group"] = soc_df["Major Group"].str[:2]

    # Merge datasets
    merged_df = onet_df.merge(
        soc_df[["soc_major_group", "SOC or O*NET-SOC 2019 Title"]],
        on="soc_major_group",
        how="left",
    )

    return merged_df


onet_df = merge_onet_soc_data()

# Update cluster mappings to include data from the merged_df
onet_df["task_normalized"] = onet_df["Task"].str.lower().str.strip()
# Some tasks are included multiple times, so we need to count the number of occurrences per task
onet_df["n_occurrences"] = onet_df.groupby("task_normalized")["Title"].transform(
    "nunique"
)

task_mappings_df = pd.read_csv("data/input/aei_data/task_pct_v2.csv")

grouped_with_occupations = task_mappings_df.merge(
    onet_df, left_on="task_name", right_on="task_normalized", how="left"
)

grouped_with_occupations["pct_occ_scaled"] = (
    100
    * (grouped_with_occupations["pct"] / grouped_with_occupations["n_occurrences"])
    / (
        grouped_with_occupations["pct"] / grouped_with_occupations["n_occurrences"]
    ).sum()
)
grouped_with_occupations["pct_occ_scaled"].sum()

automation_vs_augmentation_by_task_df = pd.read_csv(
    "data/input/aei_data/automation_vs_augmentation_by_task.csv"
)

automation_vs_augmentation_with_occupations = grouped_with_occupations.merge(
    automation_vs_augmentation_by_task_df, on="task_name", how="left"
)
assert len(automation_vs_augmentation_with_occupations) == len(grouped_with_occupations)


import pandas as pd
import numpy as np

automation_vs_augmentation_by_task_df = pd.read_csv(
    "data/input/aei_data/automation_vs_augmentation_by_task.csv"
)

task_pct = pd.read_csv("data/input/aei_data/task_pct_v2.csv")

onet_df = pd.read_csv("data/input/aei_data/onet_task_statements.csv")
onet_df["soc_minor_group"] = onet_df["O*NET-SOC Code"].str[:4]
onet_df["task_normalized"] = onet_df["Task"].str.lower().str.strip()
onet_df = onet_df[["soc_minor_group", "task_normalized"]]
onet_df.rename({"task_normalized": "task_name"}, axis=1, inplace=True)
onet_df.drop_duplicates(inplace=True)

df = task_pct.merge(automation_vs_augmentation_by_task_df, on="task_name", how="left")
df.fillna(0, inplace=True)
df["aug"] = (df["learning"] + df["validation"]) * df["pct"]
df["aut"] = (df["feedback_loop"] + df["directive"] + df["task_iteration"]) * df["pct"]

df.drop(
    columns=["learning", "validation", "feedback_loop", "directive", "task_iteration"],
    inplace=True,
)

df = df.merge(onet_df, on="task_name", how="left")

# Sum of pct is smaller than 100% because ~1.7% belong to rows with no occupation
occ_aut_aug_lvl = (
    df.groupby(["soc_minor_group"])[["pct", "aug", "aut"]].sum().reset_index()
)
occ_aut_aug_lvl["aug_aut_ratio"] = occ_aut_aug_lvl["aug"] / occ_aut_aug_lvl["aut"]

occ_aut_aug_lvl.to_parquet("data/output/occ_aut_aug_lvl.parquet")

# Classifying jobs
## 1. Highest usage jobs
top_10_jobs = occ_aut_aug_lvl.sort_values("pct", ascending=False).head(10)
top_10_jobs["class"] = "Top 10 pct"

## 2. Lowest usage jobs
bottom_10_jobs = occ_aut_aug_lvl.sort_values("pct", ascending=True).head(10)
bottom_10_jobs["class"] = "Bottom 10 pct"

## 3. jobs with highest aut
top_10_aut_jobs = occ_aut_aug_lvl.sort_values("aut", ascending=False).head(10)
top_10_aut_jobs["class"] = "Top 10 aut"

## 4. jobs with highest aug
top_10_aug_jobs = occ_aut_aug_lvl.sort_values("aug", ascending=False).head(10)
top_10_aug_jobs["class"] = "Top 10 aug"

df = pd.concat([top_10_jobs, bottom_10_jobs, top_10_aut_jobs, top_10_aug_jobs])
df.to_parquet("data/output/occ_aut_aug_lvl_classified.parquet")

