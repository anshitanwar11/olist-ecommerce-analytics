"""Olist look-and-feel for every page: palette, CSS and small HTML helpers.

Soft lavender background, white rounded cards, indigo/blue accents and gradient icon badges.
All other files import names from here, so the function names below must stay the same.
"""
from __future__ import annotations

import base64
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
LOGO_FILE = ROOT / "assets" / "olist_logo.png"

# ---- Palette -------------------------------------------------------------------------------
NAVY = "#1B2A6B"          # titles and main text
BG = "#EEF3FC"            # page background (soft lavender-blue)
PANEL = "#E4ECFB"         # left slicer panel
CARD_BORDER = "#DCE5F5"
BLUE = "#2F7BEF"
PERIWINKLE = "#7F9CF2"
INDIGO = "#6B76F7"
PINK = "#EBA9F7"
HOME_BTN = "#4F5BD5"
RED = "#D92D4A"
GREEN = "#13A06F"
MUTED = "#5B6896"

FONT_TITLE = "Poppins, Segoe UI, Arial, sans-serif"
FONT_BODY = "Inter, Segoe UI, Arial, sans-serif"

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


# ---- KPI icon styles: (soft background, icon colour) --------------------------------------
ICON_STYLES = {
    "blue": ("#DCE8FF", "#2F6FE4"),
    "orange": ("#FFE6D3", "#F0802A"),
    "green": ("#D4F3E6", "#16A36B"),
    "purple": ("#E6DEFF", "#7A55E8"),
    "red": ("#FFE0D6", "#E8541E"),
}

_WAVE = (
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' "
    "viewBox='0 0 300 140' preserveAspectRatio='none'>"
    "<path d='M0 70 C60 10 140 20 200 70 S280 110 300 100 "
    "L300 140 L0 140Z' fill='%23C3D8FB'/>"
    "<path d='M0 100 C50 70 110 80 170 110 S260 135 300 125 "
    "L300 140 L0 140Z' fill='%236C8CEA'/></svg>"
)

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@600;700;800&display=swap');

html, body, [class*="css"], .stApp {{
    font-family:{FONT_BODY};
}}

.stApp {{
    background:
        radial-gradient(1100px 500px at 100% -10%, #E3E6FF 0%, rgba(227,230,255,0) 60%),
        radial-gradient(900px 480px at -10% 0%, #E1F0FF 0%, rgba(225,240,255,0) 55%),
        {BG};
    color:{NAVY};
}}

header[data-testid="stHeader"] {{
    background:transparent;
}}

footer {{ visibility:hidden; }}

.block-container {{
    padding-top:.8rem;
    padding-bottom:1.2rem;
    max-width:100%;
}}

/* Default Streamlit sidebar (page list) */
section[data-testid="stSidebar"] {{
    background:linear-gradient(180deg,#F4F7FE 0%,#E4ECFB 100%);
    border-right:1px solid {CARD_BORDER};
}}

section[data-testid="stSidebar"] a span {{
    color:{NAVY};
    font-weight:600;
}}

/* Left slicer panel */
.st-key-filter_panel {{
    background:{PANEL} url("{_WAVE}") no-repeat bottom left / 100% 150px;
    min-height:690px;
    padding:0 .7rem 1rem .7rem;
    border-radius:14px;
    border:1px solid {CARD_BORDER};
    box-shadow:0 4px 14px rgba(60,80,160,.08);
    gap:.35rem;
}}

.st-key-filter_panel label p {{
    color:{NAVY};
    font-size:.98rem;
    font-weight:600;
}}

.st-key-filter_panel [data-baseweb="select"] > div {{
    background:#fff;
    border:1.5px solid #C5D0EC;
    border-radius:10px;
    min-height:34px;
    transition:border-color .15s, box-shadow .15s;
}}

.st-key-filter_panel [data-baseweb="select"] > div:hover,
.st-key-filter_panel [data-baseweb="select"] > div:focus-within {{
    border-color:{INDIGO};
    box-shadow:0 0 0 3px rgba(107,118,247,.15);
}}

.st-key-filter_panel [data-baseweb="select"] * {{
    font-size:.78rem;
    font-weight:600;
    color:{NAVY};
}}

.st-key-filter_panel [data-baseweb="tag"] {{
    background:{INDIGO} !important;
    border-radius:8px;
}}

.st-key-filter_panel [data-baseweb="tag"] * {{
    color:#fff !important;
}}

/* White cards that hold charts */
[class*="st-key-card_"] {{
    background:#fff;
    border:1px solid {CARD_BORDER};
    border-radius:16px;
    padding:.7rem .8rem;
    box-shadow:0 6px 18px rgba(50,70,150,.08);
}}

/* KPI cards */
.kpi {{
    display:flex;
    align-items:center;
    gap:.8rem;
    background:#fff;
    border:1px solid {CARD_BORDER};
    border-radius:16px;
    padding:.75rem 1rem;
    min-height:84px;
    box-shadow:0 6px 18px rgba(50,70,150,.08);
    transition:transform .15s, box-shadow .15s;
}}

.kpi:hover {{
    transform:translateY(-2px);
    box-shadow:0 10px 22px rgba(50,70,150,.14);
}}

.kpi-ic {{
    width:48px;
    height:48px;
    border-radius:14px;
    display:flex;
    align-items:center;
    justify-content:center;
    flex:0 0 48px;
    font-weight:700;
}}

.kpi-l {{
    color:{MUTED};
    font-weight:600;
    font-size:.95rem;
    line-height:1.15;
}}

.kpi-v {{
    color:{NAVY};
    font-family:{FONT_TITLE};
    font-weight:700;
    font-size:1.55rem;
    line-height:1.25;
}}

.kpi-wrap {{
    background:#fff;
    border:1px solid {CARD_BORDER};
    border-radius:16px;
    overflow:hidden;
    box-shadow:0 6px 18px rgba(50,70,150,.08);
}}

.kpi-wrap .kpi {{
    border:none;
    box-shadow:none;
    background:#fff;
    border-radius:0;
}}

.kpi-wrap .kpi:hover {{
    transform:none;
    box-shadow:none;
}}

.kpi-wrap .kpi-v {{
    font-size:1.7rem;
}}

.kpi-sub {{
    background:linear-gradient(90deg,#E4ECFD,#EEF0FF);
    color:{NAVY};
    font-size:.8rem;
    font-weight:600;
    text-align:center;
    padding:.3rem 0;
}}

.kpi-mom {{
    background:#fff;
    border:1px solid {CARD_BORDER};
    border-radius:16px;
    min-height:112px;
    padding:.9rem 1.1rem;
    box-shadow:0 6px 18px rgba(50,70,150,.08);
}}

.kpi-mom .t {{
    color:{MUTED};
    font-weight:600;
    font-size:1rem;
}}

.kpi-mom .v {{
    font-family:{FONT_TITLE};
    font-weight:700;
    font-size:1.7rem;
}}

/* Main custom page title */
.pg-title {{
    display:flex;
    align-items:center;
    gap:.7rem;
    color:{NAVY} !important;
    font-family:{FONT_TITLE};
    font-weight:700;
    font-size:1.9rem;
    padding-top:.2rem;
    letter-spacing:-.2px;
}}

.pg-title span {{
    color:{NAVY} !important;
    font-weight:700 !important;
    background:linear-gradient(90deg,{NAVY},{HOME_BTN});
    -webkit-background-clip:text;
    background-clip:text;
    -webkit-text-fill-color:transparent;
}}

/* Headings and text */
.stApp h1, .stApp h2, .stApp h3 {{
    color:{NAVY} !important;
    font-family:{FONT_TITLE};
    font-weight:700 !important;
}}

.stApp .stMarkdown strong {{
    color:{NAVY} !important;
    font-weight:700 !important;
}}

.stApp [data-testid="stCaptionContainer"] {{
    color:{MUTED} !important;
}}

/* Metric cards (Predict and Model pages) */
[data-testid="stMetric"] {{
    background:#fff;
    border:1px solid {CARD_BORDER};
    border-radius:16px;
    padding:14px 16px;
    box-shadow:0 6px 18px rgba(50,70,150,.08);
}}

[data-testid="stMetricLabel"] {{
    color:{MUTED} !important;
    font-weight:600 !important;
}}

[data-testid="stMetricValue"] {{
    color:{NAVY} !important;
    font-family:{FONT_TITLE};
    font-weight:700 !important;
}}

/* Forms */
[data-testid="stForm"] {{
    background:#fff;
    border:1px solid {CARD_BORDER};
    border-radius:16px;
    padding:1.2rem 1.4rem;
    box-shadow:0 6px 18px rgba(50,70,150,.08);
}}

/* Header buttons */
.st-key-btn_home button {{
    background:linear-gradient(90deg,{HOME_BTN},{INDIGO});
    color:#fff;
    border:none;
    border-radius:999px;
    font-weight:700;
    min-height:46px;
    box-shadow:0 4px 12px rgba(79,91,213,.35);
}}

.st-key-btn_home button p,
.st-key-btn_home button span {{
    color:#fff;
    font-size:1.02rem;
    font-weight:700;
}}

.st-key-btn_prev button,
.st-key-btn_next button {{
    background:#fff;
    color:{NAVY};
    border:1.5px solid #C5D0EC;
    border-radius:999px;
    min-height:46px;
    transition:border-color .15s, background .15s;
}}

.st-key-btn_prev button:hover,
.st-key-btn_next button:hover {{
    border-color:{INDIGO};
    background:#F4F5FF;
}}

.st-key-btn_prev button p,
.st-key-btn_next button p {{
    color:{NAVY};
    font-weight:700;
}}

/* Main action buttons (Predict page and login) */
.stButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button[kind="primary"],
[data-testid="stBaseButton-primaryFormSubmit"] {{
    background:linear-gradient(90deg,{HOME_BTN},{INDIGO});
    border:none;
    border-radius:999px;
    color:#fff;
    font-weight:700;
    padding:.5rem 1.6rem;
    box-shadow:0 4px 12px rgba(79,91,213,.35);
}}

/* Home / Predict / Model helper styles */
.hero {{
    background:linear-gradient(110deg,{HOME_BTN} 0%,{INDIGO} 55%,#8E7BFA 100%);
    color:#fff;
    border-radius:20px;
    padding:1.4rem 1.8rem;
    box-shadow:0 10px 26px rgba(79,91,213,.30);
}}

.hero h1 {{
    color:#fff !important;
    margin:0;
    font-size:2rem;
    -webkit-text-fill-color:#fff;
}}

.hero p {{
    margin:.3rem 0 0;
    opacity:.94;
    color:#fff;
}}

.plain-card {{
    background:#fff;
    border:1px solid {CARD_BORDER};
    border-radius:16px;
    padding:1rem 1.2rem;
    box-shadow:0 6px 18px rgba(50,70,150,.08);
}}

.plain-card h1,
.plain-card h2,
.plain-card h3,
.plain-card p {{
    color:{NAVY} !important;
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
        f'<div><div class="kpi-l">{label}</div>'
        f'<div class="kpi-v">{value}</div></div></div>'
        f'<div class="kpi-sub">{strip}</div></div>'
    )


def kpi_mom_card(delta: float | None) -> str:
    if delta is None or delta != delta:
        body = f'<span class="v" style="color:{MUTED}">n/a</span>'
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
        f'<div class="pg-title">{icon(ic, HOME_BTN, 30)}'
        f'<span>{title}</span></div>'
    )


def _b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()
