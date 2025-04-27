import pandas as pd
import json
import unicodedata


def strip_accents(text: str) -> str:
    # 1) Decompose characters into base + combining marks (NFKD)
    #    e.g. "á" → "á"  (two code-points)
    decomposed = unicodedata.normalize("NFKD", text)
    # 2) Keep only the base characters (category != Mn = “Mark, Non-spacing”)
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


import matplotlib.pyplot as plt

df = general_trends[general_trends["date"] >= "2021-08-01"]

df["net_jobs_norm"] = df["net_jobs"] / df.groupby("class")["net_jobs"].transform("mean")

df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

classes = ["Top 10 pct", "Bottom 10 pct", "Top 10 aug", "Top 10 aut"]

# 1. plot raw series ──────────────────────────────────────────────────────
fig, ax = plt.subplots()
fig.set_size_inches(12, 6)
for cls in classes:
    subset = df.loc[df["class"] == cls]
    ax.plot(subset["date"], subset["net_jobs_norm"], label=cls)
ax.set_title("Net-jobs by class (raw)")
ax.set_ylabel("net_jobs_norm")
ax.legend()
plt.show()

# 2. estimate seasonal component (Aug-2021 … Jul-2023) ───────────────────
seasonal_dict = {}  # store one seasonal series per class
period = 12  # monthly data → period = 12

start, end = pd.Timestamp("2021-08-01"), pd.Timestamp("2024-08-31")

for cls in classes:
    mask = (df["class"] == cls) & df["date"].between(start, end)
    series = (
        df.loc[mask, ["date", "net_jobs_norm"]]
        .set_index("date")["net_jobs_norm"]
        .asfreq("MS")  # monthly start frequency
        .interpolate()  # fill any gaps
    )
    stl = STL(series, period=period)
    res = stl.fit()
    monthly_seasonal = res.seasonal.groupby(
        res.seasonal.index.month
    ).mean()  # 1 … 12 → mean across years
    seasonal_dict[cls] = monthly_seasonal  # store 12-value Series


# 3. build a de-seasonalised dataframe ────────────────────────────────────
def get_seasonal_value(cls, date):
    """Return the seasonal factor for class cls on the given date.
    If the date is outside Aug-2021 … Jul-2023 we wrap around
    (i.e. assume seasonality is stable)."""
    month_idx = date.month - 1  # 0 … 11
    seasonal_series = seasonal_dict[cls]
    # find the first entry in the stored seasonal component with that month
    value = seasonal_series[seasonal_series.index.month == date.month].iloc[0]
    return value


df["seasonal"] = df.apply(
    lambda r: seasonal_dict[r["class"]].loc[r["date"].month], axis=1
)
df["deseasonal_net_jobs"] = df["net_jobs_norm"] - df["seasonal"]

# plot de-seasonalised series ────────────────────────────────────────────
fig, ax = plt.subplots()
fig.set_size_inches(12, 6)
for cls in classes:
    subset = df.loc[df["class"] == cls]
    ax.plot(subset["date"], subset["deseasonal_net_jobs"], label=cls)
ax.set_title("Net-jobs by class (de-seasonalised)")
ax.set_ylabel("net_jobs (trend + noise)")
ax.legend()
plt.show()


import pandas as pd
import numpy as np
from statsmodels.tsa.ar_model import AutoReg
import statsmodels.api as sm
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller, acf, pacf

# ───────────────────────── 0. prep ─────────────────────────
df = df.sort_values("date")  # already done earlier
df["t"] = (df["date"] - df["date"].min()).dt.days / 30  # time in ~months
df["t_sq"] = df["t"] ** 2

classes = ["Top 10 pct", "Bottom 10 pct", "Top 10 aug", "Top 10 aut"]
results = {}  # to store model objects

for cls in classes:
    y = df.loc[df["class"] == cls, "deseasonal_net_jobs"].values
    X = df.loc[df["class"] == cls, ["t", "t_sq"]]
    X = sm.add_constant(X)  # adds β₀ column

    # ── 1. fit quadratic trend via OLS ────────────────────
    ols_res = sm.OLS(y, X).fit()
    trend_hat = ols_res.fittedvalues
    resid = ols_res.resid

    # stationarity check
    p_adf = adfuller(resid, autolag="AIC")[1]
    print(f"{cls}: ADF p-value on residuals = {p_adf:.3f}")

    # ── 2. choose AR order (AIC / PACF eyeball) ───────────
    # quick grid search up to lag 6
    best_aic, best_p, best_mod = np.inf, None, None
    for p in range(1, 7):
        mod = AutoReg(resid, lags=p, old_names=False).fit()
        if mod.aic < best_aic:
            best_aic, best_p, best_mod = mod.aic, p, mod

    print(f"{cls}: best AR({best_p}) AIC = {best_aic:.2f}")
    results[cls] = {"trend": ols_res, "ar": best_mod}

    # ── 3. diagnostics ───────────────────────────────────
    sm.graphics.tsa.plot_acf(best_mod.resid, lags=24)
    plt.title(f"ACF of AR({best_p}) residuals – {cls}")
    plt.show()

# ── 4. optional: plot fitted trend vs. data ───────────────
fig, ax = plt.subplots()
for cls in classes:
    mask = df["class"] == cls
    ax.plot(
        df.loc[mask, "date"], df.loc[mask, "deseasonal_net_jobs"], label=f"{cls} data"
    )
    ax.plot(
        df.loc[mask, "date"],
        results[cls]["trend"].fittedvalues,
        linewidth=2,
        linestyle="--",
        label=f"{cls} quad-trend",
    )
ax.legend()
ax.set_title("Quadratic trend fit on de-seasonalised series")
plt.show()
