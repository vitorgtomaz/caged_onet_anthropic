import basedosdados as bd
from dotenv import load_dotenv
import os
import pandas as pd
import json
import unicodedata


def strip_accents(text: str) -> str:
    # 1) Decompose characters into base + combining marks (NFKD)
    #    e.g. "á" → "á"  (two code-points)
    decomposed = unicodedata.normalize("NFKD", text)
    # 2) Keep only the base characters (category != Mn = “Mark, Non-spacing”)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


load_dotenv()
LIMIT = False

# Reads .secrets.txt to biling_id
billing_id = os.getenv("BILLING_ID")

# loads caged_query_bd.SQL to query
query_file = "data/config/caged_bd_national.SQL"
with open(query_file, "r") as f:
    query = f.read()
    if LIMIT:
        query = query + f"\nLIMIT {LIMIT};"


df = bd.read_sql(query=query, billing_project_id=billing_id)
df.to_parquet("data/input/caged_national_UNTREATED.parquet")

df = pd.read_parquet("data/input/caged_national_UNTREATED.parquet")

CW_CAGED = json.load(open("data/config/caged_crosswalks.json", encoding="utf-8"))

# Data adjustments
cols_to_keep = [
    "ano",
    "mes",
    "cbo_2002_descricao_subgrupo_principal",
    "cbo_2002_descricao_grande_grupo",
    "grau_instrucao",
    "tipo_estabelecimento",
    "tipo_movimentacao",
]
df = (
    df.groupby(cols_to_keep)["saldo_movimentacao"]
    .sum()
    .reset_index()
    .apply(lambda col: col.str.strip() if col.dtype == "object" else col)
)

df["employed_by"] = df["tipo_estabelecimento"].map(CW_CAGED["tipo_estabelecimento"])
df[["movement_type", "movement_subtype"]] = (
    df["tipo_movimentacao"].map(CW_CAGED["tipo_movimentacao"]).apply(pd.Series)
)

df = df.rename(
    columns={
        "saldo_movimentacao": "net_jobs",
        "ano": "year",
        "mes": "month",
        "cbo_2002_descricao_subgrupo_principal": "cbo_subgroup",
        "cbo_2002_descricao_grande_grupo": "cbo_group",
        "grau_instrucao": "education_level",
    }
)

# remove columns 'tipo_movimentacao' and 'movement_subtype
df = df.drop(columns=["tipo_movimentacao", "tipo_estabelecimento"])

df["cbo_subgroup"] = df["cbo_subgroup"].apply(strip_accents)
df["cbo_group"] = df["cbo_group"].apply(strip_accents)
df["education_level"] = df["education_level"].apply(strip_accents)

df.to_parquet("data/input/caged_national.parquet")
