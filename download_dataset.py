import basedosdados as bd
from dotenv import load_dotenv
import os

load_dotenv()
LIMIT = False

# Reads .secrets.txt to biling_id
billing_id = os.getenv("BILLING_ID")

# lods caged_query_bd.SQL to query
query_file = "caged_bd_national.SQL"
with open(query_file, "r") as f:
    query = f.read()
    if LIMIT:
        query = query + f"\nLIMIT {LIMIT};"


# df = bd.read_sql(query=query, billing_project_id=billing_id)
# df.to_parquet('caged_national.parquet')
