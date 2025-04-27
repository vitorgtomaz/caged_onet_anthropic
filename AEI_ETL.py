import pandas as pd
import numpy as np


def merge_onet_soc_data() -> pd.DataFrame:
    """
    Merges O*NET task statements with SOC (Standard Occupational Classification) data
    based on major group codes.

    Args:
        onet_path (str): Path to the O*NET task statements CSV file
        soc_path (str): Path to the SOC structure CSV file

    Returns:
        pd.DataFrame: Merged DataFrame containing O*NET data with SOC major group titles
    """

    # Read and process O*NET data
    onet_df = pd.read_csv("onet_task_statements.csv")
    onet_df["soc_major_group"] = onet_df["O*NET-SOC Code"].str[:2]

    # Read and process SOC data
    soc_df = pd.read_csv("SOC_Structure.csv")
    soc_df = soc_df.dropna(subset=["Major Group"])
    soc_df["soc_major_group"] = soc_df["Major Group"].str[:2]

    # Merge datasets
    merged_df = onet_df.merge(
        soc_df[["soc_major_group", "SOC or O*NET-SOC 2019 Title"]],
        on="soc_major_group",
        how="left",
    )

    return merged_df


task_occupations_df = merge_onet_soc_data()
task_occupations_df["Title"].nunique()

# Update cluster mappings to include data from the merged_df
task_occupations_df["task_normalized"] = (
    task_occupations_df["Task"].str.lower().str.strip()
)
# Some tasks are included multiple times, so we need to count the number of occurrences per task
task_occupations_df["n_occurrences"] = task_occupations_df.groupby("task_normalized")[
    "Title"
].transform("nunique")

task_mappings_df = pd.read_csv("task_pct_v2.csv")

grouped_with_occupations = task_mappings_df.merge(
    task_occupations_df, left_on="task_name", right_on="task_normalized", how="left"
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
    "automation_vs_augmentation_by_task.csv"
)

automation_vs_augmentation_with_occupations = grouped_with_occupations.merge(
    automation_vs_augmentation_by_task_df, on="task_name", how="left"
)
assert len(automation_vs_augmentation_with_occupations) == len(grouped_with_occupations)
