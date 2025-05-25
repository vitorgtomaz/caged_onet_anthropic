"""Difference-in-Differences utilities for CAGED/O*NET job data."""

from __future__ import annotations

from typing import Iterable

import pandas as pd
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt



def load_time_series(path: str) -> pd.DataFrame:
    """Load aggregated job counts by date and occupation class.

    Parameters
    ----------
    path:
        Path to the ``time_series.csv`` file written by ``main.py``.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ``date``, ``class`` and ``net_jobs`` where
        ``date`` is parsed as a datetime.
    """
    df = pd.read_csv(path, parse_dates=["date"])
    return df



def assign_treatment(df: pd.DataFrame, treatment_groups: Iterable[str], start_date: str) -> pd.DataFrame:
    """Create ``treated`` and ``post`` indicators for the DiD analysis.

    Parameters
    ----------
    df:
        DataFrame returned by :func:`load_time_series`.
    treatment_groups:
        Iterable with the occupation classes that belong to the treatment
        group.
    start_date:
        Date string (``YYYY-MM-DD``) when the treatment begins.

    Returns
    -------
    pd.DataFrame
        Input DataFrame with added ``treated`` and ``post`` columns.
    """
    out = df.copy()
    out["treated"] = out["class"].isin(list(treatment_groups)).astype(int)
    start = pd.to_datetime(start_date)
    out["post"] = (out["date"] >= start).astype(int)
    return out



def plot_pre_trends(df: pd.DataFrame) -> None:
    """Visualize trends prior to the treatment date.

    The plot compares average ``net_jobs`` for treatment and control groups
    before the treatment start date.  It serves as a quick visual inspection of
    the parallel trends assumption.
    """
    avg = df.groupby(["date", "treated"])["net_jobs"].mean().reset_index()
    for treated, g in avg.groupby("treated"):
        label = "treated" if treated else "control"
        plt.plot(g["date"], g["net_jobs"], label=label)
    plt.axvline(df.loc[df["post"].diff().eq(1), "date"].min(), color="k", linestyle="--", label="treatment")
    plt.ylabel("Average Net Jobs")
    plt.legend()
    plt.tight_layout()
    plt.show()



def build_did_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Add interaction term ``treated_post`` to the DataFrame."""
    out = df.copy()
    out["treated_post"] = out["treated"] * out["post"]
    return out



def estimate_did(df: pd.DataFrame):
    """Estimate the DiD regression model.

    The model includes occupation-class and month fixed effects and returns the
    fitted ``statsmodels`` result object.
    """
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M")
    formula = "net_jobs ~ treated + post + treated_post + C(class) + C(month)"
    model = smf.ols(formula, data=df).fit(cov_type="HC1")
    return model



def run_diagnostics(df: pd.DataFrame) -> None:
    """Placeholder for robustness checks.

    Currently prints simple summary statistics for treated vs. control groups
    before and after the treatment.
    """
    summary = df.groupby(["treated", "post"])["net_jobs"].describe()[["mean", "std"]]
    print(summary)



def summarize_results(model) -> None:
    """Present key coefficients and generate post-estimation plots."""
    print(model.summary())

    coef = model.params.get("treated_post", float("nan"))
    conf_int = model.conf_int().loc["treated_post"].tolist()

    plt.errorbar(x=[0], y=[coef], yerr=[[coef - conf_int[0]], [conf_int[1] - coef]], fmt="o")
    plt.axhline(0, color="k", linestyle="--")
    plt.title("Estimated Treatment Effect")
    plt.ylabel("net_jobs")
    plt.xticks([])
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":  # pragma: no cover - manual usage
    data = load_time_series("data/output/time_series.csv")
    data = assign_treatment(data, ["Top 10 aut"], "2020-05-01")
    data = build_did_dataset(data)
    model = estimate_did(data)
    summarize_results(model)
