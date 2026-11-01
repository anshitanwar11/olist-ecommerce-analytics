
"""Power BI look-and-feel for the Insights pages: palette, CSS and small HTML helpers.

All colours were sampled by eye from the five Power BI screenshots supplied with the project.
"""
from __future__ import annotations

import base64
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
LOGO_FILE = ROOT / "assets" / "olist_logo.png"

# ---- Palette (Power BI report) -------------------------------------------------------------
NAVY = "#1B2A6B"
BG = "#777E88"
PANEL = "#E8EFFC"
CARD_BORDER = "#E1E8F6"
BLUE = "#2F7BEF"
PERIWINKLE = "#7F9CF2"
INDIGO = "#6B76F7"
PINK = "#EBA9F7"
HOME_BTN = "#5560C9"
RED = "#B00020"
GREEN = "#1E8E3E"

FONT_TITLE = "Arial Black, Arial, sans-serif"
FONT_BODY = "Segoe UI, Arial, sans-serif"

# ---- Inline SVG icons ----------------------------------------------------------------------
_ICONS = {
    "cube": '<path d="M12 2 3 7v10l9 5 9-5V7z"/><path d="M3 7l9 5 9-5M12 12v10"/>',
    "star": '<path d="m12 2.5 2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4 6.1 20.5l1.2-6.5L2.5 9.4l6.6-.9z"/>',
    "bag": '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
    "layers": '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5M3 17.5l9 5 9-5"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8 12.5 3 3 5-6"/>',
    "warn": '<path d="M12 3 2 20h20z"/><path d="M12 10v5M12 17.5v.5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "truck": '<path d="M2 6h12v10H2zM14 9h4l4 4v3h-8z"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/>',
    "smile": '<circle cx="12" cy="12" r="9"/><path d="M8 14c1 2 7 2 8 0M9 9.5v.5M15 9.5v.5"/>',
    "frown": '<circle cx="12" cy="12" r="9"/><path d="M8 16c1-2 7-2 8 0M9 9.5v.5M15 9.5v.5"/>',
    "repeat": '<path d="M17 2l4 4-4 4"/><path d="M3 11V9a3 3 0 0 1 3-3h15M7 22l-4-4 4-4"/><path d="M21 13v2a3 3 0 0 1-3 3H3"/>',
    "cart": '<circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M2 3h3l2.5 12h11L21 7H6"/>',
    "wallet": '<rect x="3" y="6" width="18" height="14" rx="3"/><path d="M3 10h18M16 15h2"/>',
    "bars": '<path d="M5 20V10M12 20V4M19 20v-7"/>',
}


def icon(name: str, color: str, size: int = 22) -> str:
    body = _ICONS.get(name, "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    )


# ---- KPI icon styles -----------------------------------------------------------------------
ICON_STYLES = {
    "blue": ("#355081", "#2F6FE4"),
    "orange": ("#FFE3CF", "#F0802A"),
    "green": ("#D4F3E6", "#16A36B"),
    "purple": ("#55487E", "#7A55E8"),
    "red": ("#FFE0D6", "#E8541E"),
}

_WAVE = (
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' "
    "viewBox='0 0 300 140' preserveAspectRatio='none'>"
    "<path d='M0 70 C60 10 140 20 200 70 S280 110 300 100 "
    "L300 140 L0 140Z' fill='%23A9C8FA'/>"
    "<path d='M0 100 C50 70 110 80 170 110 S260 135 300 125 "
    "L300 140 L0 140Z' fill='%234C7DE0'/></svg>"
)

CSS = f"""
<style>
.stApp {{
    background:{BG};
    font-family:{FONT_BODY};
}}

header[data-testid="stHeader"] {{
    background:transparent;
}}

.block-container {{
    padding-top:.6rem;
    padding-bottom:1rem;
    max-width:100%;
}}

/* Left slicer panel */
.st-key-filter_panel {{
    background:{PANEL} url("{_WAVE}") no-repeat bottom left / 100% 150px;
    min-height:690px;
    padding:0 .6rem 1rem .6rem;
    border-radius:6px;
    gap:.2rem;
}}

.st-key-filter_panel label p {{
    color:{NAVY};
    font-size:1.02rem;
    font-weight:500;
}}

.st-key-filter_panel [data-baseweb="select"] > div {{
    background:#fff;
    border:1.5px solid #4A5578;
    border-radius:3px;
    min-height:30px;
}}

.st-key-filter_panel [data-baseweb="select"] * {{
    font-size:.72rem;
    font-weight:700;
    color:{NAVY};
}}

/* White cards that hold charts */
[class*="st-key-card_"] {{
    background:#fff;
    border:1px solid {CARD_BORDER};
    border-radius:10px;
    padding:.5rem .6rem;
    box-shadow:0 1px 3px rgba(40,60,120,.07);
}}

/* KPI cards */
.kpi {{
    display:flex;
    align-items:center;
    gap:.7rem;
    background:#F7F9FE;
    border:1px solid {CARD_BORDER};
    border-radius:10px;
    padding:.6rem .8rem;
    min-height:78px;
    box-shadow:0 1px 3px rgba(40,60,120,.07);
}}

.kpi-ic {{
    width:46px;
    height:46px;
    border-radius:50%;
    display:flex;
    align-items:center;
    justify-content:center;
    flex:0 0 46px;
    font-weight:700;
}}

.kpi-l {{
    color:{NAVY};
    font-weight:700;
    font-size:1.12rem;
    line-height:1.15;
}}

.kpi-v {{
    color:{NAVY};
    font-weight:700;
    font-size:1.45rem;
    line-height:1.2;
}}

.kpi-wrap {{
    background:#fff;
    border:1px solid {CARD_BORDER};
    border-radius:10px;
    overflow:hidden;
    box-shadow:0 1px 3px rgba(40,60,120,.07);
}}

.kpi-wrap .kpi {{
    border:none;
    box-shadow:none;
    background:#fff;
    border-radius:0;
}}

.kpi-wrap .kpi-v {{
    font-size:1.75rem;
}}

.kpi-sub {{
    background:#DDE6F8;
    color:{NAVY};
    font-size:.8rem;
    font-weight:600;
    text-align:center;
    padding:.22rem 0;
}}

.kpi-mom {{
    background:#fff;
    border:1px solid {CARD_BORDER};
    border-radius:10px;
    min-height:112px;
    padding:.9rem 1rem;
    box-shadow:0 1px 3px rgba(40,60,120,.07);
}}

.kpi-mom .t {{
    color:{NAVY};
    font-weight:800;
    font-size:1.45rem;
}}

.kpi-mom .v {{
    font-weight:700;
    font-size:1.5rem;
}}

/* Main custom page title */
.pg-title {{
    display:flex;
    align-items:center;
    gap:.7rem;
    color:#101B4D !important;
    font-weight:900;
    font-size:2rem;
    padding-top:.2rem;
    text-shadow:none;
}}

.pg-title span {{
    color:#101B4D !important;
    font-weight:900 !important;
}}

/* Darker Streamlit headings */
.stApp h1,
.stApp h2,
.stApp h3 {{
    color:#101B4D !important;
    font-weight:800 !important;
}}

/* Strong text and section labels */
.stApp .stMarkdown strong {{
    color:#172554 !important;
    font-weight:800 !important;
}}

/* Captions */
.stApp [data-testid="stCaptionContainer"] {{
    color:#263445 !important;
}}

/* Metric labels and values */
[data-testid="stMetricLabel"] {{
    color:#263445 !important;
    font-weight:700 !important;
}}

[data-testid="stMetricValue"] {{
    color:#172554 !important;
    font-weight:800 !important;
}}

/* Header buttons */
.st-key-btn_home button {{
    background:{HOME_BTN};
    color:#fff;
    border:none;
    border-radius:999px;
    font-weight:800;
    min-height:48px;
}}

.st-key-btn_home button p,
.st-key-btn_home button span {{
    color:#fff;
    font-size:1.1rem;
    font-weight:800;
}}

.st-key-btn_prev button,
.st-key-btn_next button {{
    background:#F4F7FE;
    color:{NAVY};
    border:1px solid #C9D3EA;
    border-radius:999px;
    min-height:48px;
}}

.st-key-btn_prev button p,
.st-key-btn_next button p {{
    color:{NAVY};
    font-weight:800;
}}

/* Home / Predict / Model helper styles */
.hero {{
    background:linear-gradient(90deg,{HOME_BTN},{INDIGO});
    color:#fff;
    border-radius:14px;
    padding:1.2rem 1.5rem;
}}

.hero h1 {{
    color:#fff !important;
    margin:0;
    font-size:2rem;
}}

.hero p {{
    margin:.2rem 0 0;
    opacity:.92;
}}

.plain-card {{
    background:#fff;
    border:1px solid {CARD_BORDER};
    border-radius:12px;
    padding:1rem 1.2rem;
    box-shadow:0 1px 3px rgba(40,60,120,.07);
}}

.plain-card h1,
.plain-card h2,
.plain-card h3,
.plain-card p {{
    color:#172554 !important;
}}
</style>
"""


def apply_theme() -> None:
    """Inject the report CSS once per script run."""
    st.markdown(CSS, unsafe_allow_html=True)


def logo(width: int = 190) -> None:
    if LOGO_FILE.exists():
        st.image(str(LOGO_FILE), width=width)
    else:
        st.markdown(
            f"<div style='font-size:2rem;font-weight:800;color:{BLUE}'>olist</div>",
            unsafe_allow_html=True,
        )


def kpi_card(label: str, value: str, ic: str, tone: str) -> str:
    bg, fg = ICON_STYLES[tone]
    return (
        f'<div class="kpi"><div class="kpi-ic" style="background:{bg}">'
        f'{icon(ic, fg)}</div><div><div class="kpi-l">{label}</div>'
        f'<div class="kpi-v">{value}</div></div></div>'
    )


def kpi_card_delta(
    label: str,
    value: str,
    ic_html: str,
    bg: str,
    delta: float | None,
    sub_label: str = "vs. last month",
) -> str:
    """Executive-page card: big value plus a 'vs. last month' strip."""
    if delta is None or delta != delta:
        strip = f"{sub_label} n/a"
    else:
        arrow, colour = ("▲", GREEN) if delta >= 0 else ("▼", RED)
        sign = "+" if delta >= 0 else ""
        strip = (
            f'{sub_label} <span style="color:{colour}">'
            f'{arrow} {sign}{delta:.1f}%</span>'
        )

    return (
        f'<div class="kpi-wrap"><div class="kpi">'
        f'<div class="kpi-ic" style="background:{bg}">{ic_html}</div>'
        f'<div><div class="kpi-l" style="font-size:1rem">{label}</div>'
        f'<div class="kpi-v">{value}</div></div></div>'
        f'<div class="kpi-sub">{strip}</div></div>'
    )


def kpi_mom_card(delta: float | None) -> str:
    if delta is None or delta != delta:
        body = '<span class="v" style="color:#555">n/a</span>'
    else:
        arrow, colour = ("▲", GREEN) if delta >= 0 else ("▼", RED)
        sign = "+" if delta >= 0 else ""
        body = (
            f'<span class="v" style="color:{colour}">'
            f'{arrow} {sign}{delta:.1f}%</span>'
        )

    return (
        f'<div class="kpi-mom"><div class="t">Revenue MOM%</div>'
        f'{body}</div>'
    )


def page_title(title: str, ic: str) -> str:
    return (
        f'<div class="pg-title">{icon(ic, "#245CC5", 30)}'
        f'<span>{title}</span></div>'
    )


def _b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()
