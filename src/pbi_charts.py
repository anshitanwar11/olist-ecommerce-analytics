"""Plotly builders that reproduce the Power BI visuals (titles, colours, labels, axes) page by page.

Every function takes a table from ``src.dashboard`` and returns a ``plotly.graph_objects.Figure``.
Empty inputs return a titled placeholder instead of raising, so slicer combinations with no data stay usable.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from src.dashboard import short
from src.theme import NAVY, BLUE, PERIWINKLE, INDIGO, PINK, FONT_TITLE, FONT_BODY

GRID = "#E6EBF5"


def _base(title: str, height: int, style: str = "bold", legend: bool = False) -> go.Figure:
    fig = go.Figure()
    if style == "bold":
        tfont = dict(family=FONT_TITLE, size=21, color=NAVY)
        text = title
    else:  # light grey titles used by the two bottom visuals of the Executive page
        tfont = dict(family=FONT_BODY, size=20, color="#5A6270")
        text = title
    fig.update_layout(title=dict(text=text, x=0.02, xanchor="left", y=0.96, font=tfont), height=height, paper_bgcolor="white",
                      plot_bgcolor="white", font=dict(family=FONT_BODY, color=NAVY, size=11), showlegend=legend,
                      margin=dict(l=10, r=30, t=70, b=30), hoverlabel=dict(bgcolor="white", font_color=NAVY))
    return fig


def _empty(title: str, height: int, style: str = "bold") -> go.Figure:
    fig = _base(title, height, style)
    fig.add_annotation(text="No data for the selected filters", showarrow=False, x=0.5, y=0.45, xref="paper", yref="paper", font=dict(size=14, color="#8A93A8"))
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
    return fig


def _ticks(vmax: float, fmt, n: int = 5):
    vmax = float(vmax) if vmax and vmax > 0 else 1.0
    step = vmax / (n - 1)
    mag = 10 ** np.floor(np.log10(step))
    step = next(x for x in (1, 2, 2.5, 5, 10) if x >= step / mag - 1e-9) * mag  # round up to a 1/2/2.5/5 step
    vals = [step * i for i in range(n)]
    return vals, [fmt(v) for v in vals]


def _hbar(df, label, value, title, height, color, text, tick_fmt, style="bold", label_size=11, bold_labels=True, xpad=1.18, show_x=True):
    if df is None or df.empty: return _empty(title, height, style)
    d = df  # first row is drawn on top because the y axis is reversed below
    fig = _base(title, height, style)
    fig.add_bar(x=d[value], y=d[label], orientation="h", marker_color=color, text=[text(v) for v in d[value]], textposition="outside",
                textfont=dict(size=11, color=NAVY, family=FONT_BODY), cliponaxis=False, hovertemplate="%{y}: %{text}<extra></extra>")
    vals, labels = _ticks(d[value].max() * xpad, tick_fmt)
    fig.update_xaxes(tickvals=vals, ticktext=labels, range=[0, vals[-1]], gridcolor=GRID, griddash="dot", zeroline=False,
                     tickfont=dict(size=11, color=NAVY), visible=show_x)
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=label_size, color=NAVY, family=FONT_BODY), showgrid=False, automargin=True)
    fig.update_layout(bargap=0.35)
    return fig


# ---- Page 1: Executive Sales Overview --------------------------------------------------------
def monthly_orders_revenue(df) -> go.Figure:
    title = "Monthly Revenue and Orders Trend"
    if df is None or df.empty: return _empty(title, 300)
    fig = _base(title, 300, legend=True)
    fig.update_layout(title=dict(text=title, font=dict(family=FONT_TITLE, size=17, color=NAVY)))
    fig.add_bar(x=df["month"], y=df["orders"], name="Total Orders", marker_color=INDIGO, text=[f"{v/1e3:.1f}K" for v in df["orders"]],
                textposition="outside", textfont=dict(size=11, color=NAVY), cliponaxis=False, yaxis="y")
    fig.add_scatter(x=df["month"], y=df["revenue"], name="Total Revenue", mode="lines+text", line=dict(color=PINK, width=2, shape="spline"),
                    text=[f"R$ {v/1e6:.2f}M" for v in df["revenue"]], textposition="bottom center", textfont=dict(size=11, color=NAVY), yaxis="y2")
    ov, olab = _ticks(df["orders"].max() * 1.2, lambda v: short(v, 1, 0).replace("N/A", "0"))
    fig.update_layout(
        yaxis=dict(title=dict(text="<b>Total Orders</b>", font=dict(color=INDIGO)), tickvals=ov, ticktext=olab, range=[0, ov[-1]], gridcolor=GRID, griddash="dot", tickfont=dict(color=INDIGO, size=11)),
        yaxis2=dict(title=dict(text="<b>Total Revenue</b>", font=dict(color=NAVY)), overlaying="y", side="right", showgrid=False, tickprefix="R$ ",
                    tickformat=".1s", tickfont=dict(color="#F060D0", size=11), rangemode="tozero"),
        legend=dict(orientation="h", x=0.0, y=-0.18, font=dict(size=13, color=NAVY)), margin=dict(l=10, r=10, t=55, b=40))
    fig.update_xaxes(tickfont=dict(size=12, color=NAVY), showgrid=False)
    return fig


def payment_methods(df) -> go.Figure:
    return _hbar(df, "payment_type", "orders", "Payment Methods", 300, INDIGO, lambda v: f"{int(v)}", lambda v: f"{v/1e3:.0f}K", style="light")


def revenue_by_state(df) -> go.Figure:
    if df is None or df.empty: return _empty("Revenue by State", 300, "light")
    h = max(300, 26 * len(df) + 70)
    return _hbar(df, "state", "revenue", "Revenue by State", h, INDIGO, lambda v: f"R$ {v/1e6:.1f}M", lambda v: f"R$ {v/1e6:.0f}M", style="light", xpad=1.1)


# ---- Page 2: Product and Category -------------------------------------------------------------
def top_categories(df) -> go.Figure:
    return _hbar(df, "category", "sales", "Top 10 Categories by Sales", 270, BLUE, lambda v: f"{v/1e6:.2f}M", lambda v: f"{v/1e6:.1f}M")


def low_review_categories(df) -> go.Figure:
    return _hbar(df, "category", "low_pct", "Low-Review % by Category", 280, BLUE, lambda v: f"{v:.0f}%", lambda v: f"{v:.0f}%")


def _donut(labels, values, colors, title, height, center_text, title_size=21, pull_text="label+percent", legend=True, hole=0.72, center_size=22):
    fig = _base(title, height, legend=legend)
    fig.update_layout(title=dict(text=title, font=dict(family=FONT_TITLE, size=title_size, color=NAVY)), margin=dict(l=20, r=20, t=70, b=20))
    fig.add_pie(labels=list(labels), values=list(values), hole=hole, marker=dict(colors=list(colors)), sort=False, direction="clockwise",
                textinfo=pull_text, texttemplate="%{label}<br>%{percent:.2%}", textposition="outside", textfont=dict(size=12, color=NAVY),
                insidetextorientation="horizontal", showlegend=legend)
    fig.add_annotation(text=center_text, x=0.5, y=0.5, showarrow=False, xref="paper", yref="paper", font=dict(size=center_size, color="#222"))
    fig.update_layout(legend=dict(orientation="v", x=1.0, y=0.5, font=dict(size=12, color=NAVY)))
    return fig


def freight_donut(df, center_ratio) -> go.Figure:
    title = "Freight Cost % by Category"
    if df is None or df.empty: return _empty(title, 420)
    palette = ["#F3DAF3", "#FBDDF0", "#7B80F2", "#6E76EE", "#C9BEF5"]
    fig = _donut(df["category"], df["freight_pct"], palette[: len(df)], title, 420, f"{center_ratio:.2f}", title_size=17)
    fig.update_traces(texttemplate="%{label}<br>%{percent:.2%}")
    return fig


# ---- Page 3: Customer and Satisfaction --------------------------------------------------------
def review_by_month(df) -> go.Figure:
    title = "Average Review Score by Month"
    if df is None or df.empty: return _empty(title, 250)
    fig = _base(title, 250)
    fig.update_layout(title=dict(text=title, font=dict(family=FONT_TITLE, size=19, color=NAVY)), margin=dict(l=10, r=20, t=55, b=30))
    fig.add_scatter(x=df["month"], y=df["review_score"], mode="lines+text", line=dict(color=INDIGO, width=2, shape="spline"),
                    text=[f"{v:.1f}" for v in df["review_score"]], textposition="top center", textfont=dict(size=11, color=NAVY), hovertemplate="%{x}: %{y:.2f}<extra></extra>")
    lo, hi = df["review_score"].min(), df["review_score"].max()
    fig.update_yaxes(range=[lo - 0.12, hi + 0.15], gridcolor=GRID, griddash="dot", tickformat=".1f", tickfont=dict(color=NAVY, size=11), zeroline=False)
    fig.update_xaxes(showgrid=False, tickfont=dict(size=11, color=NAVY))
    return fig


def score_by_delay(df) -> go.Figure:
    title = "Average Score by Delivery Delay"
    if df is None or df["review_score"].notna().sum() == 0: return _empty(title, 330)
    fig = _base(title, 330)
    fig.update_layout(title=dict(text=title, font=dict(family=FONT_TITLE, size=19, color=NAVY)))
    fig.add_bar(x=df["bucket"].astype(str), y=df["review_score"], marker_color=BLUE, text=[("" if pd.isna(v) else f"{v:.1f}") for v in df["review_score"]],
                textposition="outside", textfont=dict(size=12, color=NAVY), cliponaxis=False)
    fig.update_yaxes(range=[0, 5], dtick=1, gridcolor=GRID, griddash="dot", tickfont=dict(color=NAVY))
    fig.update_xaxes(tickfont=dict(size=11, color=NAVY))
    fig.update_layout(bargap=0.5)
    return fig


def star_split(df, center_value) -> go.Figure:
    title = "Star Rating Split"
    if df is None or df["reviews"].sum() == 0: return _empty(title, 330)
    names = {5: "5 stars", 4: "4 stars", 1: "1 star", 3: "3 stars", 2: "2 stars"}
    colors = {5: "#7F9CF2", 4: "#C9CFFA", 1: "#FFC4E1", 3: "#F0C4F8", 2: "#FF7DB8"}
    d = df.set_index("stars").loc[[5, 4, 1, 3, 2]].reset_index()  # legend order used in the report
    fig = _donut([names[s] for s in d["stars"]], d["reviews"], [colors[s] for s in d["stars"]], title, 330, short(center_value, 0, 0), title_size=17, center_size=20)
    fig.update_traces(texttemplate="%{label} %{percent:.2%}")
    return fig


# ---- Page 4: Delivery and Logistics -----------------------------------------------------------
def late_by_state(df) -> go.Figure:
    return _hbar(df, "state", "late_pct", "Late % by State", 255, BLUE, lambda v: f"{v:.1f}%", lambda v: f"{v:.0f}%", xpad=1.12)


def est_vs_actual(df) -> go.Figure:
    title = "Estimated vs Actual Delivery Days"
    if df is None or df.empty: return _empty(title, 265)
    fig = _base(title, 265, legend=True)
    fig.update_layout(title=dict(text=title, font=dict(family=FONT_TITLE, size=19, color=NAVY)), margin=dict(l=10, r=20, t=55, b=30))
    fig.add_scatter(x=df["month"], y=df["est_days"], name="Avg Estimated Days", mode="lines+text", line=dict(color=INDIGO, width=2, shape="spline"),
                    text=[f"{v:.0f}" for v in df["est_days"]], textposition="top center", textfont=dict(size=11, color="#000"), yaxis="y")
    fig.add_scatter(x=df["month"], y=df["actual_days"], name="Avg Delivery Days", mode="lines+text", line=dict(color=PINK, width=2, shape="spline"),
                    text=[f"{v:.0f}" for v in df["actual_days"]], textposition="bottom center", textfont=dict(size=11, color="#000"), yaxis="y2")
    fig.update_layout(yaxis=dict(gridcolor=GRID, griddash="dot", tickfont=dict(color=NAVY)), yaxis2=dict(overlaying="y", side="right", showgrid=False, tickfont=dict(color="#999", size=9)),
                      legend=dict(orientation="h", x=0, y=-0.12, font=dict(size=11, color=NAVY)))
    fig.update_xaxes(showgrid=False, tickfont=dict(size=11, color=NAVY))
    return fig


def late_by_month(df) -> go.Figure:
    title = "Late % by Month"
    if df is None or df.empty: return _empty(title, 300)
    fig = _base(title, 300)
    fig.update_layout(title=dict(text=title, font=dict(family=FONT_TITLE, size=19, color=NAVY)), margin=dict(l=10, r=20, t=55, b=30))
    fig.add_scatter(x=df["month"], y=df["late_pct"], name="Late %", mode="lines+text", line=dict(color=INDIGO, width=2, shape="spline"),
                    text=[f"{v:.1f}%" for v in df["late_pct"]], textposition="top center", textfont=dict(size=11, color="#000"),
                    hovertemplate="%{x}<br>Late %  %{y:.1f}%<extra></extra>")
    vals, labs = _ticks(df["late_pct"].max() * 1.15, lambda v: f"{v:.0f}%")
    fig.update_yaxes(tickvals=vals, ticktext=labs, range=[0, vals[-1]], gridcolor=GRID, griddash="dot", tickfont=dict(color=NAVY), zeroline=False)
    fig.update_xaxes(showgrid=False, tickfont=dict(size=11, color=NAVY))
    return fig


def late_vs_ontime(on_time: int, late: int, center_text: str) -> go.Figure:
    title = "Late vs On-time among 1–2 Star Orders"
    if on_time + late == 0: return _empty(title, 300)
    fig = _donut(["On time", "Late"], [on_time, late], [INDIGO, PINK], title, 300, center_text, title_size=16, center_size=24)
    fig.update_traces(texttemplate="%{label}<br>%{percent:.2%}", rotation=0)
    return fig


# ---- Page 5: Seller Performance ---------------------------------------------------------------
def top_sellers_revenue(df) -> go.Figure:
    return _hbar(df, "label", "revenue", "TOP 10 Sellers by Revenue", 255, PERIWINKLE, lambda v: f"{v/1e3:.0f}K", lambda v: f"{v/1e3:.0f}K", xpad=1.25)


def seller_groups(df) -> go.Figure:
    title = "Sellers by Performance Group"
    if df is None or df["sellers"].sum() == 0: return _empty(title, 255)
    fig = _base(title, 255)
    fig.add_bar(x=df["group"], y=df["sellers"], marker_color=PERIWINKLE, text=df["sellers"], textposition="outside", textfont=dict(size=11, color=NAVY), cliponaxis=False)
    vals, labs = _ticks(df["sellers"].max() * 1.15, lambda v: f"{v/1e3:.0f}K")
    fig.update_yaxes(tickvals=vals, ticktext=labs, range=[0, vals[-1]], gridcolor=GRID, griddash="dot", tickfont=dict(color=NAVY, size=11))
    fig.update_xaxes(tickfont=dict(size=11, color=NAVY))
    fig.update_layout(bargap=0.55)
    return fig


def seller_late_rank(df) -> go.Figure:
    return _hbar(df, "seller_id", "late_pct", "Top 10 Sellers by Late Delivery Rate", 295, PERIWINKLE, lambda v: f"{v:.1f}%", lambda v: f"{v:.0f}%", label_size=10, xpad=1.15)
