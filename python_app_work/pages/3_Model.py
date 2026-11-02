
"""Model page: genuine evaluation metrics read from the artifacts written by src.train_model."""

import json
import math

import pandas as pd
import plotly.express as px
import streamlit as st

from src import config, theme
from src.auth import require_login


# ---- Page configuration ----------------------------------------------------

st.set_page_config(
    page_title="Model | Olist",
    page_icon="🧪",
    layout="wide",
)

require_login()
theme.apply_theme()


# ---- Additional page styling ----------------------------------------------

st.markdown(
    """
    <style>
    /* Main Model page title */
    .pg-title {
        color: #101B4D !important;
        font-weight: 900 !important;
    }

    /* Model description */
    .model-description {
        color: #263445 !important;
        font-size: 1rem;
        font-weight: 600;
        margin-top: 12px;
        margin-bottom: 20px;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 12px;
        padding: 16px 14px;
        box-shadow: 0 2px 5px rgba(20, 35, 75, 0.08);
    }

    [data-testid="stMetricLabel"] {
        color: #263445 !important;
        font-weight: 800 !important;
    }

    [data-testid="stMetricValue"] {
        color: #172554 !important;
        font-weight: 900 !important;
    }

    /* Section headings */
    .stApp h2,
    .stApp h3 {
        color: #101B4D !important;
        font-weight: 800 !important;
    }

    /* Supporting model text */
    .support-model {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-left: 5px solid #5560C9;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 12px;
        color: #263445 !important;
        box-shadow: 0 2px 5px rgba(20, 35, 75, 0.06);
    }

    .support-model strong {
        color: #172554 !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ---- Page title -------------------------------------------------------------

st.markdown(
    theme.page_title("Model Performance", "bars"),
    unsafe_allow_html=True,
)


# ---- Load actual model metrics ---------------------------------------------

try:
    with open(config.METRICS_FILE, encoding="utf-8") as f:
        m = json.load(f)

except FileNotFoundError:
    st.warning(
        "No trained model found yet. Run "
        "`python -m src.train_model` from the project root."
    )
    st.stop()

except (OSError, json.JSONDecodeError) as e:
    st.error(f"Cannot read the metrics file: {e}")
    st.stop()


# ---- Formatting helper -----------------------------------------------------

def pct(x):
    try:
        x = float(x)
        return f"{x:.1%}" if math.isfinite(x) else "N/A"
    except (TypeError, ValueError):
        return "N/A"


# ---- Model description -----------------------------------------------------

st.markdown(
    f"""
    <div class="model-description">
        Logistic regression predicting
        <strong>{m.get('target', 'a not-satisfied review (score 1–3)')}</strong>.
        Scores below come from a held-out 20% test split.
    </div>
    """,
    unsafe_allow_html=True,
)


# ---- Primary evaluation metrics --------------------------------------------

cols = st.columns(5)

metric_details = [
    ("Accuracy", "accuracy"),
    ("Precision", "precision"),
    ("Recall", "recall"),
    ("F1-score", "f1"),
    ("AUC", "roc_auc"),
]

for col, (label, key) in zip(cols, metric_details):
    col.metric(
        label=label,
        value=pct(m.get(key)),
    )


# ---- Cross-validation -------------------------------------------------------

if m.get("cv_auc_mean") is not None:

    cv_std = m.get("cv_auc_std")

    try:
        cv_std_text = (
            f"{float(cv_std):.3f}"
            if cv_std is not None and math.isfinite(float(cv_std))
            else "N/A"
        )
    except (TypeError, ValueError):
        cv_std_text = "N/A"

    st.caption(
        f"{m.get('cv_folds', 5)}-fold cross-validated AUC: "
        f"{pct(m.get('cv_auc_mean'))} "
        f"(± {cv_std_text})."
    )


# ---- Confusion matrix -------------------------------------------------------

cm = m.get("confusion_matrix")

if (
    isinstance(cm, list)
    and len(cm) == 2
    and all(isinstance(row, list) and len(row) == 2 for row in cm)
):

    st.subheader("Confusion Matrix")

    fig = px.imshow(
        cm,
        text_auto=True,
        x=[
            "Predicted satisfied",
            "Predicted not satisfied",
        ],
        y=[
            "Actual satisfied",
            "Actual not satisfied",
        ],
        color_continuous_scale=[
            "#EEF3FD",
            theme.INDIGO,
        ],
    )

    fig.update_layout(
        height=380,
        margin=dict(
            l=15,
            r=15,
            t=20,
            b=20,
        ),
        coloraxis_showscale=False,
        font=dict(
            family="Segoe UI, Arial, sans-serif",
            color="#172554",
            size=13,
        ),
        xaxis=dict(
            title="Predicted class",
            tickfont=dict(color="#172554"),
        ),
        yaxis=dict(
            title="Actual class",
            tickfont=dict(color="#172554"),
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        theme=None,
    )


# ---- Supporting models -----------------------------------------------------

support = []

late = m.get("late_delivery_model", {})
days = m.get("delivery_time_model", {})

if (
    late.get("available", True) is not False
    and late.get("accuracy") is not None
):

    support.append(
        (
            "Late-delivery model",
            (
                f"Accuracy {pct(late.get('accuracy'))} · "
                f"Recall {pct(late.get('recall'))} · "
                f"AUC {pct(late.get('roc_auc'))}"
            ),
        )
    )


if (
    days.get("available", True) is not False
    and days.get("rmse") is not None
):

    support.append(
        (
            "Delivery-time model",
            (
                f"Typical error {days['rmse']:.1f} days (RMSE) · "
                f"{days.get('mae', float('nan')):.1f} days (MAE) · "
                f"R² {days.get('r2', float('nan')):.2f}"
            ),
        )
    )


if support:

    st.subheader("Supporting Models")

    for name, description in support:

        st.markdown(
            f"""
            <div class="support-model">
                <strong>{name}</strong><br>
                {description}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---- Footer ----------------------------------------------------------------

st.caption(
    "Metrics are produced by the training script on your real data. "
    "Future performance can differ from the test split."
)
