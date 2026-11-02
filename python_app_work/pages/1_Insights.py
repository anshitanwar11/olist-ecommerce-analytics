"""Insights: the five Power BI report pages recreated in Streamlit (same pages, order, KPIs, visuals and slicers)."""
import numpy as np
import streamlit as st
from src import dashboard as dash, pbi_charts as pc, theme
from src.app_data import get_data, get_orders
from src.auth import require_login

st.set_page_config(page_title="Insights | Olist", page_icon="📈", layout="wide")
require_login()
theme.apply_theme()

try:
    data, orders_all = get_data(), get_orders()
except (FileNotFoundError, ConnectionError) as exc:
    st.error(str(exc)); st.stop()

PAGES = ["Executive Sales Overview", "Product and Category Analysis", "Customer and Satisfaction", "Delivery and logistics Analysis", "Seller Performance"]
PAGE_ICONS = ["bars", "cube", "star", "truck", "cube"]
st.session_state.setdefault("pbi_page", 0)
idx = int(st.session_state["pbi_page"])
CFG = {"displayModeBar": False}


def plot(fig):
    st.plotly_chart(fig, use_container_width=True, config=CFG, theme=None)


def fmt(v, kind):
    if v is None or (isinstance(v, float) and np.isnan(v)): return "N/A"
    return {"pct": f"{v:.1f}%", "m": f"{v / 1e6:.2f}M", "k": dash.short(v, 2, 0), "score1": f"{v:.1f}", "score2": f"{v:.2f}",
            "int": f"{v:.0f}", "brl": f"R$ {v / 1e6:.2f}M", "aov": f"R$ {v:,.2f}"}[kind]


def slicers(prefix, *fields):
    """Left slicer panel: logo + dropdown slicers. Returns the selected values by field name."""
    out = {}
    with st.container(key="filter_panel"):
        theme.logo()
        for name, label, options in fields:
            out[name] = st.multiselect(label[0], options, key=f"{prefix}_{name}", placeholder=label[1])
    return out


def header(title, ic):
    c = st.columns([5.2, 1.3, 1.6, 1.3], vertical_alignment="center")
    c[0].markdown(theme.page_title(title, ic), unsafe_allow_html=True)
    if c[1].button("⌂  Home", key="btn_home", use_container_width=True): st.switch_page("app.py")
    if c[2].button("←  Previous Page", key="btn_prev", use_container_width=True):
        if idx == 0: st.switch_page("app.py")
        st.session_state["pbi_page"] = idx - 1; st.rerun()
    if idx < len(PAGES) - 1 and c[3].button("Next Page  →", key="btn_next", use_container_width=True):
        st.session_state["pbi_page"] = idx + 1; st.rerun()


def kpis(cards):
    for col, html in zip(st.columns(len(cards)), cards): col.markdown(html, unsafe_allow_html=True)


def card(key):
    return st.container(key=f"card_{key}")


years = [str(y) for y in sorted(orders_all["year"].unique())]
shell = st.columns([1.15, 6.85], gap="small")
with shell[0]:
    if idx == 0:
        sel = slicers("exec", ("years", ("Year", "Select Year"), years), ("months", ("Month", "Select Month"), dash.MONTHS),
                      ("pay", ("Payment Type", "Select Payment Type"), list(dash.PAYMENT_TYPES)),
                      ("states", ("State", "Select customer_state"), sorted(orders_all["customer_state_std"].dropna().unique())))
    elif idx == 1:
        sel = slicers("prod", ("years", ("Year", "Select Year"), years), ("months", ("Month", "Select Month"), dash.MONTHS),
                      ("cats", ("Product Category", "Select Product Category"), dash.product_categories(data, orders_all)))
    elif idx == 2:
        sel = slicers("cust", ("years", ("Year", "Select Year"), years), ("months", ("Month", "Select Month"), dash.MONTHS),
                      ("states", ("Customer State", "Select customer_state"), sorted(orders_all["customer_state_std"].dropna().unique())))
    elif idx == 3:
        sel = slicers("deliv", ("years", ("Year", "Select Year"), years), ("months", ("Month", "Select Month"), dash.MONTHS),
                      ("status", ("Delivery Status", "Select Delivery Status"), ["On time", "Late"]))
    else:
        seller_states = sorted(data["seller_360"][next((c for c in ("state", "seller_state") if c in data["seller_360"].columns), data["seller_360"].columns[0])].dropna().astype(str).unique())
        sel = slicers("sell", ("years", ("Year", "Select Year"), years), ("months", ("Month", "Select Month"), dash.MONTHS),
                      ("states", ("Seller state", "Select state"), seller_states), ("bands", ("Rating Band", "Select Rating Band"), dash.RATING_BANDS))

with shell[1]:
    header(PAGES[idx], PAGE_ICONS[idx])
    o = dash.filter_orders(orders_all, sel.get("years"), sel.get("months"), states=sel.get("states") if idx in (0, 2) else None,
                           payments=sel.get("pay"), delivery_status=sel.get("status"))
    if o.empty:
        st.warning("No delivered orders match the selected slicers."); st.stop()

    # ------------------------------------------------------------------ 1. Executive Sales Overview
    if idx == 0:
        e = dash.executive(o)
        kpis([theme.kpi_card_delta("Total Revenue", fmt(e["revenue"], "brl"), '<span style="color:#2F6FE4;font-weight:800">R$</span>', "#DCE8FF", e["mom"]["revenue"]),
              theme.kpi_card_delta("Orders", fmt(e["orders"], "k"), theme.icon("cart", "#7A55E8"), "#E6DEFF", e["mom"]["orders"]),
              theme.kpi_card_delta("Avg Order Value", fmt(e["aov"], "aov"), theme.icon("wallet", "#16A36B"), "#D4F3E6", e["mom"]["aov"]),
              theme.kpi_mom_card(e["mom"]["revenue"])])
        with card("exec_trend"): plot(pc.monthly_orders_revenue(e["monthly"]))
        left, right = st.columns(2)
        with left, card("exec_pay"): plot(pc.payment_methods(e["payments"]))
        with right, card("exec_state"):
            with st.container(height=330, border=False): plot(pc.revenue_by_state(e["states"]))

    # ------------------------------------------------------------------ 2. Product and Category Analysis
    elif idx == 1:
        p = dash.product(data, o, sel.get("cats"))
        kpis([theme.kpi_card("Items Sold", fmt(p["items_sold"], "k"), "cube", "blue"), theme.kpi_card("Top Category Share", fmt(p["top_share"], "pct"), "star", "orange"),
              theme.kpi_card("Total Sales", fmt(p["total_sales"], "m"), "bag", "green"), theme.kpi_card("Top 10 Categories Share", fmt(p["top10_share"], "pct"), "layers", "purple")])
        left, right = st.columns([1.95, 1.05])
        with left:
            with card("prod_top"): plot(pc.top_categories(p["top10"]))
            with card("prod_low"): plot(pc.low_review_categories(p["low_review"]))
        with right:
            st.markdown("<div style='height:105px'></div>", unsafe_allow_html=True)
            with card("prod_freight"): plot(pc.freight_donut(p["freight"], p["freight_overall"]))

    # ------------------------------------------------------------------ 3. Customer and Satisfaction
    elif idx == 2:
        c = dash.customer(data, o)
        kpis([theme.kpi_card("Average Review Score", fmt(c["avg_score"], "score1"), "star", "blue"), theme.kpi_card("Satisfied Orders (4-5 stars)", fmt(c["satisfied"], "pct"), "smile", "green"),
              theme.kpi_card("Low Reviews (1-2 stars)", fmt(c["low"], "pct"), "frown", "orange"), theme.kpi_card("Repeat Customers", fmt(c["repeat"], "pct"), "repeat", "purple")])
        with card("cust_month"): plot(pc.review_by_month(c["by_month"]))
        left, right = st.columns([1.9, 1.1])
        with left, card("cust_delay"): plot(pc.score_by_delay(c["by_delay"]))
        with right, card("cust_stars"): plot(pc.star_split(c["stars"], c["four_star_count"]))

    # ------------------------------------------------------------------ 4. Delivery and logistics Analysis
    elif idx == 3:
        d = dash.delivery(o)
        kpis([theme.kpi_card("On-Time Delivery Rate", fmt(d["on_time"], "pct"), "check", "green"), theme.kpi_card("Late Orders", fmt(d["late_orders"], "k"), "warn", "orange"),
              theme.kpi_card("Avg Days Late (late orders)", fmt(d["avg_days_late"], "score1"), "clock", "purple"), theme.kpi_card("Average Delivery Time (days)", fmt(d["avg_delivery"], "int"), "truck", "blue")])
        left, right = st.columns([1, 1.7])
        with left, card("deliv_state"): plot(pc.late_by_state(d["by_state"]))
        with right, card("deliv_est"): plot(pc.est_vs_actual(d["est_vs_actual"]))
        left, right = st.columns([1.9, 1.0])
        with left, card("deliv_month"): plot(pc.late_by_month(d["late_month"]))
        with right, card("deliv_donut"): plot(pc.late_vs_ontime(d["low_on_time"], d["low_late"], dash.short(d["low_late"], 0, 0)))

    # ------------------------------------------------------------------ 5. Seller Performance
    else:
        s = dash.seller(data, o, sel.get("states"), sel.get("bands"))
        kpis([theme.kpi_card("Total Seller Revenue", fmt(s["revenue"], "m"), "cube", "blue"), theme.kpi_card("Active Sellers", fmt(s["active"], "k"), "star", "orange"),
              theme.kpi_card("Average Seller Rating", fmt(s["avg_rating"], "score2"), "bag", "green"), theme.kpi_card("Seller Late Rate", fmt(s["late_rate"], "pct"), "layers", "purple")])
        left, right = st.columns([1.7, 1.0])
        with left, card("sell_rev"): plot(pc.top_sellers_revenue(s["top_rev"]))
        with right, card("sell_groups"): plot(pc.seller_groups(s["groups"]))
        left, _ = st.columns([3, 1.1])
        with left, card("sell_late"): plot(pc.seller_late_rank(s["late_rank"]))
