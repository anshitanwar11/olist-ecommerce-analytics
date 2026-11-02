import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path

SERVER = "localhost"

engine = create_engine(
    f"mssql+pyodbc://@{'localhost'}/PRP_OLIST_PROJECT"
    "?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
)

out = Path("data/extracts")
out.mkdir(parents=True, exist_ok=True)

for table in ["order_360", "customer_360", "seller_360", "items", "products", "reviews", "payments"]:
    df = pd.read_sql(f"SELECT * FROM clean.{table}", engine)
    df.to_csv(out / f"{table}.csv", index=False)
    print(table, "->", len(df), "rows saved")