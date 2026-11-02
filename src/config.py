"""Central paths and modelling settings. No secrets are stored here."""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
EXTRACT_DIR = DATA_DIR / "extracts"
APP_DATA_DIR = ROOT_DIR / "outputs" / "app_data"
MODEL_DIR = ROOT_DIR / "models"
MODEL_FILE = MODEL_DIR / "review_model.pkl"
METRICS_FILE = MODEL_DIR / "metrics.json"
ODDS_RATIOS_FILE = MODEL_DIR / "odds_ratios.csv"
FEATURE_SCREENING_FILE = MODEL_DIR / "feature_screening.csv"
NUMERIC_VIF_FILE = MODEL_DIR / "numeric_vif.csv"
NUMERIC_CORRELATIONS_FILE = MODEL_DIR / "numeric_correlations.csv"
import os
SQL_SCHEMA = "clean"
SQL_DATABASE = "PRP_OLIST_PROJECT"
DATA_SOURCE = os.environ.get("OLIST_DATA_SOURCE", "auto").lower()  # auto | sql | extract
DISPLAY_USERNAME = "enshi"  # shown on the Home page exactly as written


def sql_settings() -> dict:
    """SQL Server settings (Windows Authentication) from env vars or .streamlit/secrets.toml [sql]."""
    cfg = {"server": "", "database": SQL_DATABASE, "driver": "ODBC Driver 17 for SQL Server"}
    secrets_path = ROOT_DIR / ".streamlit" / "secrets.toml"
    if secrets_path.is_file():
        try:
            try:
                import tomllib as _toml
            except ModuleNotFoundError:  # Python < 3.11
                import tomli as _toml
            with open(secrets_path, "rb") as fh:
                cfg.update({k: v for k, v in _toml.load(fh).get("sql", {}).items() if v})
        except Exception:
            pass
    for key in ("server", "database", "driver"):
        env = os.environ.get(f"OLIST_SQL_{key.upper()}")
        if env: cfg[key] = env
    return cfg


RANDOM_STATE = 42
TEST_SIZE = 0.20
N_CV_FOLDS = 5
LOW_REVIEW_MAX_SCORE = 3  # Scores 1–3 are not satisfied; scores 4–5 are satisfied.

TABLES = {
        "order_360": "order_360.csv.gz",
    "customer_360": "customer_360.csv",
    "seller_360": "seller_360.csv",
    "items": "items.csv",
    "products": "products.csv",
    "reviews": "reviews.csv",
    "payments": "payments.csv",
    "geolocation": "geolocation.csv",
}
REQUIRED_TABLES = set(TABLES)

# KPI and KRI definitions are implemented in src/analysis.py and intentionally
# are not hard-coded as results here.
