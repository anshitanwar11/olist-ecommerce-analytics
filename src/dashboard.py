"""Data layer for the five Power BI report pages (pure pandas, no Streamlit/Plotly imports).

Scope note: the Power BI figures (96K orders, R$ 15.39M, 110K items, 8.1% late) are consistent with
*delivered* orders only, so every page here works on orders flagged delivered (``is_delivered`` in
order_360, falling back to status/dates). Revenue = item price + freight, as in the existing analysis layer.

Assumptions that could not be read from the screenshots are collected in the constants below.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from src.analysis import prepare_orders, _col

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
PAYMENT_TYPES = {"Credit card": "credit_card_amt", "Boleto": "boleto_amt", "Voucher": "voucher_amt", "Debit card": "debit_card_amt"}

# ---- Assumptions (documented in README "Known limitations") ---------------------------------
MIN_SELLER_ORDERS_PERFORMANCE = 10   # sellers below this are "Too few orders"
TOP_PERFORMER_MIN_RATING, TOP_PERFORMER_MAX_LATE_PCT = 4.3, 5.0
NEEDS_ATTENTION_MAX_RATING, NEEDS_ATTENTION_MIN_LATE_PCT = 3.5, 15.0
MIN_SELLER_ORDERS_LATE_RANK = 100    # minimum orders for a seller to enter "Top 10 by late rate"
MIN_CATEGORY_ORDERS = 100            # minimum orders for a category to enter %-based rankings
RATING_BANDS = ["Below 3", "3 to 4", "4 and above"]
PARTIAL_MONTH_FRACTION = 0.05        # trailing months with < 5% of the median monthly orders are ignored for MoM


# ---------------------------------------------------------------------------------------------
# Base order table + generic filters
# ---------------------------------------------------------------------------------------------
def base_orders(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Delivered orders with year / month helper columns."""
    o = prepare_orders(data)
    flag = pd.to_numeric(o["is_delivered"], errors="coerce") if "is_delivered" in o.columns else pd.Series(np.nan, index=o.index)
    scope = flag.eq(1).where(flag.notna(), o["is_delivered_std"])
    o = o[scope.astype(bool) & o["purchase_dt"].notna()].copy()
    o["year"] = o["purchase_dt"].dt.year
    o["month_num"] = o["purchase_dt"].dt.month
    o["month"] = o["month_num"].map(dict(enumerate(MONTHS, start=1)))
    o["est_days"] = (o["estimated_dt"] - o["purchase_dt"]).dt.total_seconds() / 86400
    return o


def filter_orders(o: pd.DataFrame, years=None, months=None, states=None, payments=None, delivery_status=None) -> pd.DataFrame:
    if years: o = o[o["year"].isin([int(y) for y in years])]
    if months: o = o[o["month"].isin(months)]
    if states: o = o[o["customer_state_std"].isin(states)]
    if payments:
        mask = pd.Series(False, index=o.index)
        for p in payments:
            col = PAYMENT_TYPES.get(p)
            if col in o.columns: mask |= pd.to_numeric(o[col], errors="coerce").fillna(0) > 0
        o = o[mask]
    if delivery_status:
        late = o["is_late_std"]
        keep = pd.Series(False, index=o.index)
        if "Late" in delivery_status: keep |= late.eq(1)
        if "On time" in delivery_status: keep |= late.eq(0)
        o = o[keep]
    return o


def _pct(a, b):
    return float(a / b * 100) if b else np.nan


def _mom(series_by_month: pd.DataFrame) -> dict:
    """Latest vs previous calendar month, ignoring trailing partial months."""
    empty = {"revenue": np.nan, "orders": np.nan, "aov": np.nan}
    m = series_by_month.sort_index()
    if len(m) < 2: return empty
    floor = m["orders"].median() * PARTIAL_MONTH_FRACTION
    while len(m) > 2 and m["orders"].iloc[-1] < floor: m = m.iloc[:-1]
    cur, prev = m.iloc[-1], m.iloc[-2]
    ch = lambda a, b: float((a / b - 1) * 100) if b else np.nan
    return {"revenue": ch(cur["revenue"], prev["revenue"]), "orders": ch(cur["orders"], prev["orders"]),
            "aov": ch(cur["revenue"] / cur["orders"], prev["revenue"] / prev["orders"])}


# ---------------------------------------------------------------------------------------------
# Page 1 - Executive Sales Overview
# ---------------------------------------------------------------------------------------------
def executive(o: pd.DataFrame) -> dict:
    orders = o["order_id"].nunique(); revenue = float(o["revenue"].sum())
    by_ym = o.groupby(o["purchase_dt"].dt.to_period("M")).agg(revenue=("revenue", "sum"), orders=("order_id", "nunique"))
    mom = _mom(by_ym)
    monthly = (o.groupby(["month_num", "month"]).agg(orders=("order_id", "nunique"), revenue=("revenue", "sum")).reset_index()
               .sort_values("orders", ascending=False))
    rows = []
    for label, col in PAYMENT_TYPES.items():
        if col in o.columns:
            n = int((pd.to_numeric(o[col], errors="coerce").fillna(0) > 0).sum())
            if n: rows.append({"payment_type": label, "orders": n})
    payments = pd.DataFrame(rows, columns=["payment_type", "orders"]).sort_values("orders", ascending=False)
    states = (o.groupby("customer_state_std").agg(revenue=("revenue", "sum")).reset_index()
              .rename(columns={"customer_state_std": "state"}).sort_values("revenue", ascending=False))
    return {"revenue": revenue, "orders": orders, "aov": revenue / orders if orders else np.nan, "mom": mom,
            "monthly": monthly, "payments": payments, "states": states}


# ---------------------------------------------------------------------------------------------
# Item-level helper shared by Product and Seller pages
# ---------------------------------------------------------------------------------------------
def scoped_items(data: dict[str, pd.DataFrame], o: pd.DataFrame) -> pd.DataFrame:
    """Order items of the filtered delivered orders, with category, revenue and order attributes."""
    items = data["items"].copy()
    items = items[items["order_id"].isin(o["order_id"])]
    items["price"] = pd.to_numeric(items["price"], errors="coerce").fillna(0)
    items["freight_value"] = pd.to_numeric(items["freight_value"], errors="coerce").fillna(0)
    items["item_revenue"] = items["price"] + items["freight_value"]
    p = data["products"]; pid = _col(p, ["product_id"]); cat = _col(p, ["category_en", "product_category_name_english", "product_category_name", "category_pt"])
    items = items.merge(p[[pid, cat]].drop_duplicates(pid).rename(columns={pid: "product_id", cat: "category"}), on="product_id", how="left")
    items["category"] = items["category"].fillna("Others").replace("", "Others")
    ocols = ["order_id", "review_score", "is_late_std", "delay_days_std"]
    return items.merge(o[ocols].drop_duplicates("order_id"), on="order_id", how="left")


# ---------------------------------------------------------------------------------------------
# Page 2 - Product and Category Analysis
# ---------------------------------------------------------------------------------------------
def product_categories(data: dict[str, pd.DataFrame], o: pd.DataFrame | None = None) -> list[str]:
    """Category options for the slicer (from the products table; missing names appear as 'Others')."""
    p = data["products"]; cat = _col(p, ["category_en", "product_category_name_english", "product_category_name", "category_pt"])
    return sorted(p[cat].fillna("Others").replace("", "Others").astype(str).unique())


def product(data: dict[str, pd.DataFrame], o: pd.DataFrame, categories=None) -> dict:
    it = scoped_items(data, o)
    if categories: it = it[it["category"].isin(categories)]
    total = float(it["item_revenue"].sum())
    cat = it.groupby("category").agg(sales=("item_revenue", "sum"), items=("order_id", "size"), orders=("order_id", "nunique"),
                                     price=("price", "sum"), freight=("freight_value", "sum")).reset_index().sort_values("sales", ascending=False)
    top10 = cat.head(10)
    # Low-review %: distinct (order, category) pairs with a review of 1-2 stars.
    pairs = it.dropna(subset=["review_score"]).drop_duplicates(["order_id", "category"])
    low = (pairs.groupby("category").agg(orders=("order_id", "size"), low=("review_score", lambda s: (s <= 2).sum())).reset_index())
    low = low[low["orders"] >= MIN_CATEGORY_ORDERS].assign(low_pct=lambda d: d["low"] / d["orders"] * 100).sort_values("low_pct", ascending=False).head(10)
    # Freight cost % = freight / item price, five highest among categories with enough volume.
    fr = cat[cat["orders"] >= MIN_CATEGORY_ORDERS].assign(freight_pct=lambda d: d["freight"] / d["price"].replace(0, np.nan)).dropna(subset=["freight_pct"])
    fr = fr.sort_values("freight_pct", ascending=False).head(5)
    overall = float(it["freight_value"].sum() / it["price"].sum()) if it["price"].sum() else np.nan
    return {"items_sold": int(len(it)), "total_sales": total,
            "top_share": _pct(cat["sales"].iloc[0], total) if len(cat) else np.nan,
            "top10_share": _pct(top10["sales"].sum(), total), "top10": top10, "low_review": low, "freight": fr, "freight_overall": overall}


# ---------------------------------------------------------------------------------------------
# Page 3 - Customer and Satisfaction
# ---------------------------------------------------------------------------------------------
DELAY_BUCKETS = ["1) 7+ days early", "2) 0-7 days early", "3) 1-3 days late", "4) 3-7 days late", "5) 7+ days late"]


def customer(data: dict[str, pd.DataFrame], o: pd.DataFrame) -> dict:
    rated = o.dropna(subset=["review_score"])
    cust_col = _col(o, ["customer_unique_id"])
    repeat = np.nan
    if cust_col:
        counts = o.dropna(subset=[cust_col]).groupby(cust_col)["order_id"].nunique()
        repeat = float((counts >= 2).mean() * 100) if len(counts) else np.nan
    by_month = rated.groupby(["month_num", "month"])["review_score"].mean().reset_index().sort_values("month_num")
    d = rated.dropna(subset=["delay_days_std"]).copy()
    d["bucket"] = pd.cut(d["delay_days_std"], bins=[-np.inf, -7, 0, 3, 7, np.inf], labels=DELAY_BUCKETS)
    by_delay = d.groupby("bucket", observed=False)["review_score"].mean().reindex(DELAY_BUCKETS).reset_index()
    # Star split comes from the reviews table when it can be linked to the filtered orders.
    rv = data.get("reviews", pd.DataFrame())
    if {"order_id", "review_score"} <= set(rv.columns):
        scores = pd.to_numeric(rv.loc[rv["order_id"].isin(o["order_id"]), "review_score"], errors="coerce").dropna().round().astype(int)
    else:
        scores = rated["review_score"].round().astype(int)
    stars = scores.value_counts().reindex([1, 2, 3, 4, 5], fill_value=0).rename_axis("stars").reset_index(name="reviews")
    return {"avg_score": float(rated["review_score"].mean()) if len(rated) else np.nan,
            "satisfied": _pct((rated["review_score"] >= 4).sum(), len(rated)), "low": _pct((rated["review_score"] <= 2).sum(), len(rated)),
            "repeat": repeat, "by_month": by_month, "by_delay": by_delay, "stars": stars,
            "four_star_count": int(stars.loc[stars["stars"] == 4, "reviews"].sum())}


# ---------------------------------------------------------------------------------------------
# Page 4 - Delivery and Logistics
# ---------------------------------------------------------------------------------------------
def delivery(o: pd.DataFrame) -> dict:
    known = o[o["is_late_std"].notna()]
    late = known[known["is_late_std"] == 1]
    by_state = (known.groupby("customer_state_std")["is_late_std"].agg(["mean", "size"]).reset_index()
                .rename(columns={"customer_state_std": "state", "mean": "late_pct"}))
    by_state = by_state[by_state["size"] >= 30].assign(late_pct=lambda d: d["late_pct"] * 100).sort_values("late_pct", ascending=False).head(10)
    late_month = known.groupby(["month_num", "month"])["is_late_std"].mean().mul(100).reset_index(name="late_pct").sort_values("month_num")
    est = o.groupby(["month_num", "month"]).agg(est_days=("est_days", "mean"), actual_days=("delivery_days_std", "mean")).reset_index().sort_values("month_num")
    low = known[known["review_score"] <= 2]
    return {"on_time": _pct((known["is_late_std"] == 0).sum(), len(known)), "late_orders": int(len(late)),
            "avg_days_late": float(late["delay_days_std"].mean()) if len(late) else np.nan,
            "avg_delivery": float(o["delivery_days_std"].mean()) if o["delivery_days_std"].notna().any() else np.nan,
            "by_state": by_state, "late_month": late_month, "est_vs_actual": est,
            "low_late": int((low["is_late_std"] == 1).sum()), "low_on_time": int((low["is_late_std"] == 0).sum())}


# ---------------------------------------------------------------------------------------------
# Page 5 - Seller Performance
# ---------------------------------------------------------------------------------------------
def seller_table(data: dict[str, pd.DataFrame], o: pd.DataFrame) -> pd.DataFrame:
    """One row per seller: revenue, orders, late %, average rating, city/state and performance group."""
    it = scoped_items(data, o)
    if it.empty: return pd.DataFrame(columns=["seller_id", "revenue", "orders", "late_pct", "rating", "city", "state", "group", "band"])
    per_pair = it.drop_duplicates(["order_id", "seller_id"])
    s = it.groupby("seller_id").agg(revenue=("item_revenue", "sum"), orders=("order_id", "nunique")).reset_index()
    q = per_pair.groupby("seller_id").agg(late_pct=("is_late_std", lambda x: x.mean() * 100 if x.notna().any() else np.nan),
                                          rating=("review_score", "mean")).reset_index()
    s = s.merge(q, on="seller_id", how="left")
    sl = data.get("seller_360", pd.DataFrame())
    sid, city, state = _col(sl, ["seller_id"]), _col(sl, ["city", "seller_city"]), _col(sl, ["state", "seller_state"])
    if sid:
        keep = {sid: "seller_id"}
        if city: keep[city] = "city"
        if state: keep[state] = "state"
        s = s.merge(sl[list(keep)].drop_duplicates(sid).rename(columns=keep), on="seller_id", how="left")
    for c in ("city", "state"):
        if c not in s.columns: s[c] = ""
    s["group"] = np.select(
        [s["orders"] < MIN_SELLER_ORDERS_PERFORMANCE,
         (s["rating"] >= TOP_PERFORMER_MIN_RATING) & (s["late_pct"].fillna(0) <= TOP_PERFORMER_MAX_LATE_PCT),
         (s["rating"] < NEEDS_ATTENTION_MAX_RATING) | (s["late_pct"].fillna(0) >= NEEDS_ATTENTION_MIN_LATE_PCT)],
        ["Too few orders", "Top performer", "Needs attention"], default="Average")
    s["band"] = pd.cut(s["rating"], bins=[-np.inf, 3, 4, np.inf], labels=RATING_BANDS, right=False).astype("string")
    return s


def seller(data: dict[str, pd.DataFrame], o: pd.DataFrame, states=None, bands=None) -> dict:
    s = seller_table(data, o)
    if states: s = s[s["state"].isin(states)]
    if bands: s = s[s["band"].isin(bands)]
    top_rev = s.sort_values("revenue", ascending=False).head(10).copy()
    top_rev["label"] = top_rev["seller_id"].str[:6] + " - " + top_rev["city"].astype(str)
    late = s[s["orders"] >= MIN_SELLER_ORDERS_LATE_RANK].dropna(subset=["late_pct"]).sort_values("late_pct", ascending=False).head(10)
    order = ["Too few orders", "Average", "Top performer", "Needs attention"]
    groups = s["group"].value_counts().reindex(order, fill_value=0).rename_axis("group").reset_index(name="sellers")
    pairs = scoped_items(data, o)
    pairs = pairs[pairs["seller_id"].isin(s["seller_id"])].drop_duplicates(["order_id", "seller_id"])
    return {"revenue": float(s["revenue"].sum()), "active": int(s["seller_id"].nunique()),
            "avg_rating": float(s["rating"].mean()) if s["rating"].notna().any() else np.nan,
            "late_rate": float(pairs["is_late_std"].mean() * 100) if pairs["is_late_std"].notna().any() else np.nan,
            "top_rev": top_rev, "late_rank": late, "groups": groups}


# ---------------------------------------------------------------------------------------------
# Number formatting used by KPI cards and chart labels (Power BI style)
# ---------------------------------------------------------------------------------------------
def short(v, dec_m: int = 2, dec_k: int = 0) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)): return "N/A"
    a = abs(v)
    if a >= 1e6: return f"{v / 1e6:.{dec_m}f}M"
    if a >= 1e3: return f"{v / 1e3:.{dec_k}f}K"
    return f"{v:,.0f}"
