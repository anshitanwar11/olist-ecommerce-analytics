"""Home page and login entry point for Olist Sales & Customer Analytics."""
"""Home page and login entry point for Olist Sales & Customer Analytics"""

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent          # python_app_work/
PROJECT_ROOT = APP_DIR.parent                      # repository root
for p in (str(APP_DIR), str(PROJECT_ROOT)):        # works whether src sits here or one level up
    if p not in sys.path:
        sys.path.insert(0, p)

from src import config, data_loader, theme
from src import dashboard as dash
from src.analysis import build_kris
from src.app_data import get_data, get_orders
import streamlit as st
from src.auth import require_login

st.set_page_config(page_title="Olist Sales & Customer Analytics", page_icon="📊", layout="wide")
require_login()
theme.apply_theme()

try:
    data, orders = get_data(), get_orders()
except (FileNotFoundError, ConnectionError) as exc:
    st.error(str(exc))
    st.markdown("**Required tables:** `order_360`, `customer_360`, `seller_360`, `items`, `products`, `reviews`, `payments`, `geolocation` "
                "(SQL Server schema `clean`, database `PRP_OLIST_PROJECT`, or CSV files in `data/extracts/`).")
    st.stop()

c = st.columns([1, 3], vertical_alignment="center")
with c[0]: theme.logo(200)
c[1].markdown(f'<div class="hero"><h1>Olist Sales &amp; Customer Analytics</h1><p>Welcome,— explore sales, '
              'categories, customer satisfaction, delivery and sellers, and predict review risk.</p></div>', unsafe_allow_html=True)
st.caption(data_loader.data_status()["message"])

e = dash.executive(orders)
k = st.columns(4)
k[0].markdown(theme.kpi_card("Total Revenue", f"R$ {e['revenue'] / 1e6:.2f}M", "bag", "blue"), unsafe_allow_html=True)
k[1].markdown(theme.kpi_card("Orders", dash.short(e["orders"], 2, 0), "cart", "purple"), unsafe_allow_html=True)
k[2].markdown(theme.kpi_card("Avg Order Value", f"R$ {e['aov']:,.2f}", "wallet", "green"), unsafe_allow_html=True)
cu = dash.customer(data, orders); dl = dash.delivery(orders)
k[3].markdown(theme.kpi_card("On-Time Delivery", f"{dl['on_time']:.1f}%", "check", "orange"), unsafe_allow_html=True)
k = st.columns(4)
k[0].markdown(theme.kpi_card("Average Review Score", f"{cu['avg_score']:.1f}", "star", "blue"), unsafe_allow_html=True)
k[1].markdown(theme.kpi_card("Satisfied Orders (4-5 stars)", f"{cu['satisfied']:.1f}%", "smile", "green"), unsafe_allow_html=True)
k[2].markdown(theme.kpi_card("Low Reviews (1-2 stars)", f"{cu['low']:.1f}%", "frown", "orange"), unsafe_allow_html=True)
k[3].markdown(theme.kpi_card("Repeat Customers", f"{cu['repeat']:.1f}%", "repeat", "purple"), unsafe_allow_html=True)
st.caption("All figures use delivered orders, matching the Power BI report. Revenue = item price + freight.")

st.subheader("Key risk indicators")
kris = build_kris(data)
st.dataframe(kris[["kri", "python_value", "unit"]].rename(columns={"kri": "Indicator", "python_value": "Value", "unit": "Unit"}), use_container_width=True, hide_index=True)
st.info("Use the sidebar to open **Insights** (the five Power BI report pages), **Predict** and **Model**.")
