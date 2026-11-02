
"""Predict the probability of a not-satisfied review for an order described by the user."""

import streamlit as st

from src import theme
from src.app_data import get_data
from src.auth import require_login
from src.predict import load_bundle, predict_review_risk

st.set_page_config(
    page_title="Predict | Olist",
    page_icon="🔮",
    layout="wide",
)

require_login()
theme.apply_theme()

st.markdown(
    theme.page_title("Customer Satisfaction Prediction", "star"),
    unsafe_allow_html=True,
)

st.caption(
    "Enter order-time details to estimate the chance that the customer "
    "will leave a 1–3 star review."
)

# ---- Load application data -------------------------------------------------

try:
    data = get_data()
except (FileNotFoundError, ConnectionError) as exc:
    st.error(str(exc))
    st.stop()

# ---- Load trained prediction model ----------------------------------------

try:
    bundle = load_bundle()
except Exception as exc:  # noqa: BLE001
    st.error(f"The model is not ready: {exc}")
    st.info(
        "Train it once from the project root with "
        "`python -m src.train_model`."
    )
    st.stop()

orders = data["order_360"]
products = data["products"]
sellers = data["seller_360"]

# ---- Dropdown values -------------------------------------------------------

states = (
    sorted(orders["customer_state"].dropna().astype(str).unique())
    if "customer_state" in orders
    else ["Unknown"]
)

categories = (
    sorted(products["category_en"].dropna().astype(str).unique())
    if "category_en" in products
    else ["Unknown"]
)

sstate_col = next(
    (c for c in ("state", "seller_state") if c in sellers),
    None,
)

seller_states = (
    sorted(sellers[sstate_col].dropna().astype(str).unique())
    if sstate_col
    else states
)

WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

# ---- Prediction input form -------------------------------------------------

with st.form("order_prediction"):

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("**When**")

        year = st.number_input(
            "Purchase year", 2016, 2035, 2018, 1
        )

        month = st.selectbox(
            "Purchase month",
            list(range(1, 13)),
            index=5,
        )

        weekday = st.selectbox(
            "Purchase weekday",
            list(range(7)),
            index=2,
            format_func=lambda i: WEEKDAYS[i],
        )

        hour = st.selectbox(
            "Purchase hour",
            list(range(24)),
            index=12,
        )

    with c2:
        st.markdown("**What & where**")

        category = st.selectbox(
            "Main product category",
            categories,
        )

        n_items = st.number_input(
            "Number of items", 1, 100, 1
        )

        n_sellers = st.number_input(
            "Number of sellers", 1, 100, 1
        )

        state = st.selectbox(
            "Customer state",
            states,
        )

        seller_state = st.selectbox(
            "Seller state",
            seller_states,
        )

    with c3:
        st.markdown("**Price & payment (BRL)**")

        price = st.number_input(
            "Total item price",
            0.0,
            value=150.0,
            step=10.0,
        )

        freight = st.number_input(
            "Total freight",
            0.0,
            value=25.0,
            step=5.0,
        )

        installments = st.number_input(
            "Maximum installments",
            0,
            48,
            1,
        )

        card = st.number_input(
            "Credit card amount",
            0.0,
            value=175.0,
            step=10.0,
        )

        boleto = st.number_input(
            "Boleto amount",
            0.0,
            value=0.0,
            step=10.0,
        )

        voucher = st.number_input(
            "Voucher amount",
            0.0,
            value=0.0,
            step=10.0,
        )

        debit = st.number_input(
            "Debit card amount",
            0.0,
            value=0.0,
            step=10.0,
        )

    submitted = st.form_submit_button(
        "Estimate satisfaction risk",
        type="primary",
    )

# ---- Run prediction --------------------------------------------------------

if submitted:

    values = {
        "purchase_year": year,
        "purchase_month_num": month,
        "purchase_weekday": weekday,
        "purchase_hour": hour,
        "n_items": n_items,
        "n_sellers": n_sellers,
        "price_sum": price,
        "freight_sum": freight,
        "freight_ratio": freight / price if price else None,
        "max_installments": installments,
        "credit_card_amt": card,
        "debit_card_amt": debit,
        "boleto_amt": boleto,
        "voucher_amt": voucher,
        "not_defined_amt": 0.0,
        "payment_rows": 1,
        "avg_weight_g": None,
        "avg_volume_cm3": None,
        "avg_photos_qty": None,
        "distinct_categories": 1,
        "customer_state": state,
        "dominant_category": category,
        "seller_state": seller_state,
        "same_state": int(state == seller_state),
    }

    try:
        r = predict_review_risk(values, model=bundle)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Prediction failed: {exc}")
        st.stop()

    p = r["probability"]

    if p < 0.25:
        level = "Low"
        msg = (
            "This order looks likely to end in a satisfied customer."
        )
    elif p < 0.5:
        level = "Moderate"
        msg = (
            "There is a noticeable chance of a lukewarm or negative review."
        )
    else:
        level = "High"
        msg = (
            "This order is more likely than not to receive a 1–3 star review."
        )

    st.subheader("Result")

    a, b, c = st.columns(3)

    a.metric(
        "Chance of a 1–3 star review",
        f"{p * 100:.1f}%",
    )

    b.metric(
        "Risk level",
        level,
    )

    if r.get("predicted_review_score") is not None:
        c.metric(
            "Expected review score",
            f"{r['predicted_review_score']:.1f} / 5",
        )

    st.progress(min(1.0, max(0.0, p)))
    st.write(msg)

    extra = st.columns(2)

    if r.get("late_probability_percent") is not None:
        extra[0].metric(
            "Chance of late delivery",
            f"{r['late_probability_percent']:.1f}%",
        )

    if r.get("predicted_delivery_days") is not None:
        extra[1].metric(
            "Expected delivery time",
            f"{r['predicted_delivery_days']:.0f} days",
        )

    st.caption(
        "A statistical estimate for the values entered, not a guarantee. "
        "Details not asked for here are filled in by the model with "
        "typical values."
    )
