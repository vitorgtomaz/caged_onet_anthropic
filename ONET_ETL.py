import pandas as pd

full_df = pd.read_csv("data/input/SOC_structure.csv")
full_df["minor_group"] = full_df.apply(lambda row: row.dropna().iloc[0][:4], axis=1)

# Groups by minor group, aggregating "SOC or O*NET-SOC 2019 Title" by concatenating the strings with '; '
minor_groups = (
    full_df.groupby("minor_group")
    .agg({"SOC or O*NET-SOC 2019 Title": lambda x: "; ".join(x)})
    .rename({"SOC or O*NET-SOC 2019 Title": "title"}, axis="columns")
)

minor_groups.to_csv("data/output/onet_minor_groups.csv", index=True)
