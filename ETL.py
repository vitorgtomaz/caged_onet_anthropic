import basedosdados as bd
from dotenv import load_dotenv
import os
import pandas as pd
import json

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


# df = bd.read_sql(query=query, billing_project_id=billing_id)
caged = pd.read_parquet("data/input/caged_national.parquet")

CW_CAGED = json.load(open("data/config/caged_crosswalks.json", encoding="utf-8"))
CW_ONET_CBO = json.load(open("data/config/CBO_ONET_crosswalks.json", encoding="utf-8"))

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
    caged.groupby(cols_to_keep)["saldo_movimentacao"]
    .sum()
    .reset_index()
    .apply(lambda col: col.str.strip() if col.dtype == "object" else col)
)

df[["onet_code", "onet_title", "reasoning", "confidence", "0"]] = (
    df["cbo_2002_descricao_subgrupo_principal"].map(CW_ONET_CBO).apply(pd.Series)
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
        "cbo_2002_descricao_subgrupo_principal": "occ_subgroup",
        "cbo_2002_descricao_grande_grupo": "occ_group",
        "grau_instrucao": "education_level",
    }
)

# remove columns 'tipo_movimentacao' and 'movement_subtype
df = df.drop(columns=["0", "tipo_movimentacao", "tipo_estabelecimento"])

df.to_parquet("data/input/caged_national.parquet")
