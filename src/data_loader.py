"""Load the cleaned Olist tables from SQL Server (Windows Authentication) or from CSV exports.

source="sql"     -> read clean.<table> from database PRP_OLIST_PROJECT
source="extract" -> read data/extracts/<table>.csv (or <table>.csv.gz)
source="auto"    -> SQL Server when a server is configured, otherwise (or if SQL fails) the CSV extracts.
No synthetic data is ever generated here.
"""
from __future__ import annotations
import pandas as pd
from src import config

_STATUS = {"mode": "uninitialized", "message": "Data has not been loaded."}

# geolocation is very large and is not used by the dashboard pages, so it may be missing.
OPTIONAL_TABLES = {"geolocation"}


def _find_file(filename: str):
    """Return the CSV path, or the compressed .gz version of it, or None."""
    for name in (filename, filename + ".gz"):
        path = config.EXTRACT_DIR / name
        if path.is_file():
            return path
    return None


def missing_extracts() -> list[str]:
    return [filename for key, filename in config.TABLES.items()
            if key not in OPTIONAL_TABLES and _find_file(filename) is None]


def data_status() -> dict[str, str]:
    return dict(_STATUS)


def sql_engine():
    """SQLAlchemy engine using Windows Authentication (Trusted_Connection)."""
    from sqlalchemy import create_engine
    from sqlalchemy.engine import URL
    cfg = config.sql_settings()
    if not cfg["server"]:
        raise ConnectionError("No SQL Server configured. Add a [sql] section to .streamlit/secrets.toml (see the .example file).")
    odbc = (f"DRIVER={{{cfg['driver']}}};SERVER={cfg['server']};DATABASE={cfg['database']};"
            "Trusted_Connection=yes;TrustServerCertificate=yes;")
    return create_engine(URL.create("mssql+pyodbc", query={"odbc_connect": odbc}))


def _load_sql() -> dict[str, pd.DataFrame]:
    engine = sql_engine()
    data = {}
    for key in config.TABLES:
        frame = pd.read_sql(f"SELECT * FROM {config.SQL_SCHEMA}.{key}", engine)
        frame.columns = [str(c).strip() for c in frame.columns]
        data[key] = frame
    return data


def _load_csv() -> dict[str, pd.DataFrame]:
    missing = missing_extracts()
    if missing:
        raise FileNotFoundError(
            "Real Olist extracts are missing from data/extracts: " + ", ".join(missing)
            + ". Configure SQL Server in .streamlit/secrets.toml or copy the clean CSV exports into that folder. "
            "Synthetic data is never used.")
    data = {}
    for key, filename in config.TABLES.items():
        path = _find_file(filename)
        if path is None:                      # optional table that was not exported
            data[key] = pd.DataFrame()
            continue
        frame = pd.read_csv(path, low_memory=False)   # .csv.gz is read directly
        frame.columns = [str(c).strip() for c in frame.columns]
        data[key] = frame
    return data


def load_all(source: str | None = None) -> dict[str, pd.DataFrame]:
    """Load all real tables or fail with an explicit message."""
    global _STATUS
    source = (source or config.DATA_SOURCE or "auto").lower()
    if source not in {"auto", "sql", "extract"}:
        raise ValueError("source must be 'auto', 'sql' or 'extract'.")
    sql_error = None
    if source in {"auto", "sql"}:
        try:
            data = _load_sql()
            _STATUS = {"mode": "sql", "message": f"Loaded the clean tables from SQL Server database {config.SQL_DATABASE}."}
            return data
        except Exception as exc:  # noqa: BLE001 - report the reason, then fall back only in auto mode
            sql_error = exc
            if source == "sql":
                raise ConnectionError(f"SQL Server load failed: {exc}") from exc
    try:
        data = _load_csv()
    except FileNotFoundError as exc:
        if sql_error is not None:
            raise FileNotFoundError(f"{exc} (SQL Server attempt failed: {sql_error})") from exc
        raise
    _STATUS = {"mode": "extract", "message": "Loaded the real Olist CSV extracts."}
    return data
