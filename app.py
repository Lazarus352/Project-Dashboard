"""
THE MARKET TERMINAL — Bloomberg-lite dashboard inspired by urbankaoberg.com
Single-file Streamlit app. Production-ready with yfinance data + placeholder macro data.
Replace placeholder macro data with FRED API calls as noted in TODO comments.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import datetime
import io
import random
import time

# ── Optional imports ──────────────────────────────────────────────────────────
try:
    import yfinance as yf
    HAS_YF = True
except ImportError:
    HAS_YF = False

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="The Market Terminal",
    page_icon="▸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS — Bloomberg terminal aesthetic
# TYPOGRAPHY FIX: Inter sans-serif, crisp #EDEDED text, 14px base, antialiased
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Google Fonts: Inter (UI body) + JetBrains Mono (data/numbers only) ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ══ DESIGN TOKENS ══════════════════════════════════════════════════════════ */
:root {
  /* Backgrounds — true dark, not pure black (easier on eyes, better contrast) */
  --bg:         #0e1117;
  --bg1:        #131720;
  --bg2:        #181d27;
  --bg3:        #1d2330;
  --border:     #242c3d;
  --border2:    #2a3347;

  /* Accent colours */
  --green:      #00e676;
  --green-dim:  #00b85a;
  --green-dark: #00230f;
  --red:        #ff4757;
  --red-dim:    #cc2233;
  --red-dark:   #2d0008;
  --amber:      #ffc107;
  --blue:       #29b6f6;

  /* ── TEXT — crisp, high-contrast hierarchy ── */
  --text-primary:   #ededed;   /* body / table values  — near-white, not glaring */
  --text-secondary: #a0aab8;   /* labels, captions     — readable mid-grey       */
  --text-muted:     #576070;   /* placeholders, dims   — subtle                  */
  --text-accent:    #ffffff;   /* hero numbers, titles — full white               */

  /* Legacy alias so existing HTML snippets still work */
  --white: #ededed;
  --dim:   #576070;
  --dim2:  #2a3347;

  /* ── TYPOGRAPHY ── */
  --font-ui:   'Inter', 'Segoe UI', 'Helvetica Neue', -apple-system, sans-serif;
  --font-data: 'JetBrains Mono', 'Menlo', 'Consolas', monospace;

  /* Sizes */
  --fs-xs:   11px;   /* tags, meta, status dots  */
  --fs-sm:   12px;   /* table cells, captions    */
  --fs-base: 14px;   /* body text default        */
  --fs-md:   15px;   /* sub-headings             */
  --fs-lg:   16px;   /* section headings         */
  --fs-xl:   22px;   /* hero numbers             */

  /* Rendering */
  --smooth: antialiased;
}

/* ══ GLOBAL RESET / BASE ════════════════════════════════════════════════════ */
html, body {
  font-family: var(--font-ui) !important;
  font-size: var(--fs-base) !important;
  background: var(--bg) !important;
  color: var(--text-primary) !important;

  /* Crisp rendering on all platforms */
  -webkit-font-smoothing: antialiased !important;
  -moz-osx-font-smoothing: grayscale !important;
  text-rendering: optimizeLegibility !important;
}

/* Catch-all for Streamlit's injected class names */
[class*="css"], [class*="st-"], .element-container,
p, div, span, li, td, th, label, input, textarea, select, button {
  font-family: var(--font-ui) !important;
  -webkit-font-smoothing: antialiased !important;
  text-rendering: optimizeLegibility !important;
  letter-spacing: 0.2px !important;
  line-height: 1.45 !important;
}

/* Numbers / data fields — use mono font */
[data-testid="stDataFrame"] *,
[data-testid="stMetric"] *,
.bb-card-val,
.font-data { font-family: var(--font-data) !important; }

.stApp { background: var(--bg) !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ══ SIDEBAR ════════════════════════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
  background: var(--bg1) !important;
  border-right: 1px solid var(--border2) !important;
}
section[data-testid="stSidebar"] > div { padding: 0.75rem 0.5rem !important; }

/* ══ TOP BAR ════════════════════════════════════════════════════════════════ */
.top-bar {
  background: var(--bg1);
  border-bottom: 1px solid var(--border2);
  padding: 0.35rem 1rem;
  display: flex; align-items: center; justify-content: space-between;
  position: sticky; top: 0; z-index: 999;
}
.top-logo {
  font-family: var(--font-ui);
  font-size: var(--fs-sm);
  font-weight: 700;
  color: var(--green);
  letter-spacing: 0.18em;
  text-transform: uppercase;
}
.top-time {
  font-family: var(--font-data);
  font-size: var(--fs-xs);
  color: var(--text-muted);
  letter-spacing: 0.06em;
}
.tick-up   { color: var(--green) !important; }
.tick-down { color: var(--red)   !important; }

/* ══ MAIN NAV TABS ══════════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
  background: var(--bg1) !important;
  border-bottom: 1px solid var(--border2) !important;
  border-top: none !important;
  gap: 0 !important;
  padding: 0 !important;
}
.stTabs [data-baseweb="tab"] {
  font-family: var(--font-ui) !important;
  font-size: var(--fs-xs) !important;
  font-weight: 600 !important;
  letter-spacing: 0.12em !important;
  color: var(--text-muted) !important;
  padding: 0.6rem 1.15rem !important;
  border-right: 1px solid var(--border) !important;
  border-radius: 0 !important;
  background: transparent !important;
  text-transform: uppercase !important;
  min-width: fit-content !important;
  -webkit-font-smoothing: antialiased !important;
}
.stTabs [aria-selected="true"] {
  background: var(--bg3) !important;
  color: var(--green) !important;
  border-top: 2px solid var(--green) !important;
}
.stTabs [data-baseweb="tab-panel"] {
  background: var(--bg) !important;
  padding: 0.75rem 0.75rem 2rem !important;
  border: none !important;
}

/* ══ RADIO — toolbar style ══════════════════════════════════════════════════ */
.stRadio > div {
  display: flex !important;
  flex-direction: row !important;
  gap: 0 !important;
  flex-wrap: wrap !important;
}
.stRadio > div > label {
  font-family: var(--font-ui) !important;
  font-size: var(--fs-xs) !important;
  font-weight: 600 !important;
  letter-spacing: 0.1em !important;
  padding: 0.28rem 0.75rem !important;
  border: 1px solid var(--border2) !important;
  color: var(--text-muted) !important;
  cursor: pointer !important;
  background: var(--bg1) !important;
  margin: 0 !important;
  text-transform: uppercase !important;
  -webkit-font-smoothing: antialiased !important;
}
.stRadio > div > label:has(input:checked) {
  color: var(--green) !important;
  border-color: var(--green) !important;
  background: var(--green-dark) !important;
}
.stRadio > div > label > div:first-child { display: none !important; }
div[data-testid="stRadio"] > label { display: none !important; }

/* ══ SELECTBOX ══════════════════════════════════════════════════════════════ */
.stSelectbox > div > div {
  background: var(--bg2) !important;
  border: 1px solid var(--border2) !important;
  color: var(--text-primary) !important;
  font-size: var(--fs-sm) !important;
  font-family: var(--font-ui) !important;
  border-radius: 0 !important;
}
.stSelectbox label { display: none !important; }

/* ══ METRIC / HERO CARDS ════════════════════════════════════════════════════ */
.bb-card {
  background: var(--bg1);
  border: 1px solid var(--border2);
  padding: 0.55rem 0.85rem;
  position: relative;
  overflow: hidden;
}
.bb-card-label {
  font-family: var(--font-ui);
  font-size: var(--fs-xs);
  font-weight: 500;
  color: var(--text-muted);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  -webkit-font-smoothing: antialiased;
}
.bb-card-val {
  font-family: var(--font-data);
  font-size: var(--fs-xl);
  font-weight: 700;
  color: var(--text-accent);
  line-height: 1.15;
  -webkit-font-smoothing: antialiased;
}
.bb-card-chg   { font-family: var(--font-data); font-size: var(--fs-sm); font-weight: 600; margin-top: 0.15rem; }
.bb-card-chg.up { color: var(--green); }
.bb-card-chg.dn { color: var(--red); }
.bb-card-chg.fl { color: var(--text-muted); }
.bb-card-bar      { position: absolute; top: 0; left: 0; right: 0; height: 2px; background: var(--green); }
.bb-card-bar.red   { background: var(--red); }
.bb-card-bar.amber { background: var(--amber); }

/* ══ SECTION LABELS ═════════════════════════════════════════════════════════ */
.bb-section {
  font-family: var(--font-ui);
  font-size: var(--fs-xs);
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--text-muted);
  border-left: 2px solid var(--green);
  padding-left: 0.5rem;
  margin: 0.85rem 0 0.45rem;
  -webkit-font-smoothing: antialiased;
}

/* ══ DATA TABLES ════════════════════════════════════════════════════════════ */
.stDataFrame { border: 1px solid var(--border2) !important; }

/* Table header */
[data-testid="stDataFrame"] th,
[data-testid="stDataFrame"] [data-testid="glideDataEditor"] .gdg-header {
  font-family: var(--font-ui) !important;
  font-size: var(--fs-xs) !important;
  font-weight: 600 !important;
  color: var(--text-muted) !important;
  background: var(--bg2) !important;
  letter-spacing: 0.08em !important;
  text-transform: uppercase !important;
}
/* Table cells */
[data-testid="stDataFrame"] td,
[data-testid="stDataFrame"] [data-testid="glideDataEditor"] .gdg-cell {
  font-family: var(--font-data) !important;
  font-size: var(--fs-sm) !important;
  color: var(--text-primary) !important;
  -webkit-font-smoothing: antialiased !important;
}
/* Broad catch for all dataframe text */
[data-testid="stDataFrame"] * {
  font-size: var(--fs-sm) !important;
  -webkit-font-smoothing: antialiased !important;
}

/* ══ BUTTONS ════════════════════════════════════════════════════════════════ */
.stButton > button {
  font-family: var(--font-ui) !important;
  font-size: var(--fs-xs) !important;
  font-weight: 600 !important;
  letter-spacing: 0.1em !important;
  text-transform: uppercase !important;
  background: var(--bg2) !important;
  color: var(--green) !important;
  border: 1px solid var(--green) !important;
  border-radius: 2px !important;
  padding: 0.32rem 0.9rem !important;
  -webkit-font-smoothing: antialiased !important;
}
.stButton > button:hover { background: var(--green-dark) !important; }

/* ══ TEXT / NUMBER INPUTS ════════════════════════════════════════════════════ */
.stTextInput > div > div {
  background: var(--bg2) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 2px !important;
  color: var(--text-primary) !important;
  font-family: var(--font-ui) !important;
  font-size: var(--fs-sm) !important;
}
.stTextInput label {
  font-family: var(--font-ui) !important;
  font-size: var(--fs-xs) !important;
  font-weight: 600 !important;
  color: var(--text-muted) !important;
  letter-spacing: 0.1em !important;
  text-transform: uppercase !important;
}

/* ══ NEWS CARDS ══════════════════════════════════════════════════════════════ */
.news-card {
  border-left: 2px solid var(--border2);
  padding: 0.45rem 0.7rem;
  margin-bottom: 0.45rem;
  background: var(--bg1);
}
.news-card:hover { border-left-color: var(--green); }
.news-headline {
  font-family: var(--font-ui);
  font-size: var(--fs-base);
  font-weight: 500;
  color: var(--text-primary);
  line-height: 1.45;
  -webkit-font-smoothing: antialiased;
}
.news-meta {
  font-family: var(--font-ui);
  font-size: var(--fs-xs);
  color: var(--text-muted);
  margin-top: 0.18rem;
  letter-spacing: 0.05em;
}
.news-tag {
  display: inline-block;
  font-family: var(--font-ui);
  font-size: 10px;
  font-weight: 600;
  padding: 0.05rem 0.35rem;
  border: 1px solid var(--border2);
  color: var(--text-muted);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-right: 0.3rem;
}

/* ══ WATCHLIST ════════════════════════════════════════════════════════════════ */
.wl-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.35rem 0.5rem;
  border-bottom: 1px solid var(--border);
  font-family: var(--font-data);
  font-size: var(--fs-sm);
}
.wl-ticker { color: var(--amber); font-weight: 700; letter-spacing: 0.05em; min-width: 60px; }
.wl-price  { color: var(--text-primary); text-align: right; min-width: 70px; }
.wl-chg    { text-align: right; min-width: 60px; font-weight: 600; }

/* ══ CHAT ════════════════════════════════════════════════════════════════════ */
.chat-wrap   { border: 1px solid var(--border2); background: var(--bg1); margin-top: 0.5rem; }
.chat-header { background: var(--bg3); border-bottom: 1px solid var(--border2); padding: 0.3rem 0.75rem; font-family: var(--font-ui); font-size: var(--fs-xs); font-weight: 600; letter-spacing: 0.15em; color: var(--green); text-transform: uppercase; }
.chat-msg-user {
  background: var(--bg3);
  border-left: 2px solid var(--amber);
  padding: 0.45rem 0.75rem;
  margin: 0.3rem;
  font-family: var(--font-ui);
  font-size: var(--fs-sm);
  color: var(--text-primary);
  line-height: 1.5;
}
.chat-msg-ai {
  background: var(--bg2);
  border-left: 2px solid var(--green);
  padding: 0.45rem 0.75rem;
  margin: 0.3rem;
  font-family: var(--font-ui);
  font-size: var(--fs-sm);
  color: var(--text-primary);
  line-height: 1.5;
}

/* ══ MISC ════════════════════════════════════════════════════════════════════ */
.hi-green { color: var(--green) !important; }
.hi-red   { color: var(--red)   !important; }

.ticker-tape {
  background: var(--bg3);
  border-top: 1px solid var(--border2);
  border-bottom: 1px solid var(--border2);
  padding: 0.28rem 1rem;
  font-family: var(--font-data);
  font-size: var(--fs-xs);
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  letter-spacing: 0.04em;
}

.hm-cell {
  text-align: center;
  font-family: var(--font-data);
  font-size: var(--fs-xs);
  padding: 0.3rem;
  border: 1px solid var(--border);
}

/* Multiselect */
.stMultiSelect > div {
  background: var(--bg2) !important;
  border-radius: 2px !important;
}
.stMultiSelect label {
  font-family: var(--font-ui) !important;
  font-size: var(--fs-xs) !important;
  color: var(--text-muted) !important;
  letter-spacing: 0.08em !important;
}

/* Number input */
.stNumberInput > div { border-radius: 2px !important; }
.stNumberInput label {
  font-family: var(--font-ui) !important;
  font-size: var(--fs-xs) !important;
  color: var(--text-muted) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
}

/* Expander */
.streamlit-expanderHeader {
  font-family: var(--font-ui) !important;
  font-size: var(--fs-sm) !important;
  font-weight: 600 !important;
  background: var(--bg2) !important;
  color: var(--text-primary) !important;
  border-radius: 0 !important;
  border: 1px solid var(--border2) !important;
  letter-spacing: 0.05em !important;
}
.streamlit-expanderContent {
  background: var(--bg1) !important;
  border: 1px solid var(--border2) !important;
  border-top: none !important;
}

/* st.caption / st.info text */
.stCaption, [data-testid="stCaptionContainer"] {
  font-family: var(--font-ui) !important;
  font-size: var(--fs-xs) !important;
  color: var(--text-muted) !important;
}

/* st.info / st.warning / st.success boxes */
.stAlert {
  font-family: var(--font-ui) !important;
  font-size: var(--fs-sm) !important;
}

/* Progress bar */
.stProgress > div > div { background: var(--green) !important; }

/* Hide Streamlit chrome */
.stDeployButton { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
defaults = {
    "watchlist": ["SPY", "QQQ", "AAPL", "MSFT", "BTC-USD", "GC=F", "CL=F", "EURUSD=X"],
    "chat_history": [],
    "uploaded_text": "",
    "custom_df": None,
    "formula_result": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
PLOTLY_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, Segoe UI, Helvetica Neue, sans-serif",
              color="#a0aab8", size=11),
    xaxis=dict(
        gridcolor="#1d2330",
        linecolor="#2a3347",
        zerolinecolor="#2a3347",
        tickfont=dict(family="JetBrains Mono, monospace", size=10, color="#a0aab8"),
        showgrid=True,
    ),
    yaxis=dict(
        gridcolor="#1d2330",
        linecolor="#2a3347",
        zerolinecolor="#2a3347",
        tickfont=dict(family="JetBrains Mono, monospace", size=10, color="#a0aab8"),
        showgrid=True,
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor="#2a3347",
        font=dict(family="Inter, sans-serif", size=10, color="#a0aab8"),
    ),
    hoverlabel=dict(
        bgcolor="#1d2330",
        bordercolor="#2a3347",
        font=dict(family="JetBrains Mono, monospace", size=11, color="#ededed"),
    ),
    margin=dict(l=40, r=20, t=32, b=30),
    hovermode="x unified",
)

EQUITY_TICKERS = {
    "EQUITIES":    ["SPY", "QQQ", "DIA", "IWM", "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "JPM"],
    "CREDIT":      ["LQD", "HYG", "TLT", "AGG", "MBB", "BKLN", "JNK", "EMB"],
    "RATES":       ["^TNX", "^FVX", "^TYX", "^IRX", "TLT", "IEF", "SHY"],
    "FX":          ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X", "USDCHF=X", "USDCNH=X"],
    "COMMODITIES": ["GC=F", "SI=F", "CL=F", "NG=F", "ZC=F", "ZW=F", "ZS=F", "HG=F", "PL=F"],
    "FUNDS":       ["SPY", "QQQ", "IVV", "VTI", "GLD", "SLV", "USO", "VNQ", "XLE", "XLF"],
    "CRYPTO":      ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "DOGE-USD"],
    "ECONOMY":     ["^GSPC", "^DJI", "^IXIC", "^VIX"],
    "GEOPOLITICS": ["^GSPC", "GC=F", "USO", "^VIX", "TLT"],
}

TIMEFRAMES = {
    "1D": ("1d", "2m"), "5D": ("5d", "15m"), "1M": ("1mo", "1h"),
    "3M": ("3mo", "1d"), "6M": ("6mo", "1d"), "1Y": ("1y", "1d"),
    "2Y": ("2y", "1wk"), "5Y": ("5y", "1wk"), "10Y": ("10y", "1mo"),
    "30Y": ("max", "1mo"),
}

# ══════════════════════════════════════════════════════════════════════════════
# DATA HELPERS
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=60, show_spinner=False)
def fetch_ohlcv(ticker: str, period: str, interval: str) -> pd.DataFrame:
    if not HAS_YF:
        return pd.DataFrame()
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna()
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=120, show_spinner=False)
def fetch_quote(ticker: str) -> dict:
    if not HAS_YF:
        return {}
    try:
        t = yf.Ticker(ticker)
        fi = t.fast_info
        price = round(float(fi.last_price), 4)
        prev  = round(float(fi.previous_close), 4) if fi.previous_close else price
        chg   = round(price - prev, 4)
        pct   = round(chg / prev * 100, 2) if prev else 0.0
        return {"price": price, "prev": prev, "chg": chg, "pct": pct}
    except Exception:
        return {}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_bulk_quotes(tickers: list) -> dict:
    results = {}
    for t in tickers:
        q = fetch_quote(t)
        if q:
            results[t] = q
    return results

def add_overlays(fig, df: pd.DataFrame, overlays: list):
    close = df["Close"] if "Close" in df.columns else df.iloc[:, 0]
    idx   = df.index
    if "SMA 20" in overlays:
        sma20 = close.rolling(20).mean()
        fig.add_trace(go.Scatter(x=idx, y=sma20, mode="lines", name="SMA20",
                                 line=dict(color="#00b8d4", width=1)))
    if "SMA 50" in overlays:
        sma50 = close.rolling(50).mean()
        fig.add_trace(go.Scatter(x=idx, y=sma50, mode="lines", name="SMA50",
                                 line=dict(color="#ffab00", width=1)))
    if "EMA 20" in overlays:
        ema20 = close.ewm(span=20).mean()
        fig.add_trace(go.Scatter(x=idx, y=ema20, mode="lines", name="EMA20",
                                 line=dict(color="#aa00ff", width=1, dash="dot")))
    if "Bollinger Bands" in overlays:
        mid = close.rolling(20).mean()
        std = close.rolling(20).std()
        fig.add_trace(go.Scatter(x=idx, y=mid + 2*std, mode="lines", name="BB+",
                                 line=dict(color="#555555", width=1, dash="dot"), showlegend=False))
        fig.add_trace(go.Scatter(x=idx, y=mid - 2*std, mode="lines", name="BB-",
                                 line=dict(color="#555555", width=1, dash="dot"),
                                 fill="tonexty", fillcolor="rgba(80,80,80,0.07)", showlegend=False))
    if "Fibonacci" in overlays and len(close) > 1:
        hi, lo = close.max(), close.min()
        levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
        colors_fib = ["#ff1744","#ff6d00","#ffab00","#00e676","#00b8d4","#aa00ff","#ff1744"]
        for lvl, col in zip(levels, colors_fib):
            price_lvl = lo + (hi - lo) * lvl
            fig.add_hline(y=price_lvl, line_dash="dot", line_color=col, line_width=0.7,
                          annotation_text=f"Fib {lvl}", annotation_font_size=8,
                          annotation_font_color=col)
    return fig

def render_chart(ticker: str, period: str, interval: str, chart_type: str, overlays: list):
    df = fetch_ohlcv(ticker, period, interval)
    if df.empty:
        st.warning(f"No data for {ticker}")
        return

    layout = dict(**PLOTLY_BASE)
    layout.update(height=480, showlegend=True)
    layout["xaxis"]["rangeslider"] = {"visible": False}

    if chart_type == "CANDLESTICK":
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
            name=ticker, increasing_line_color="#00ff41", decreasing_line_color="#ff1744",
            increasing_fillcolor="#003a0e", decreasing_fillcolor="#3a0008",
        ))
    elif chart_type == "BAR":
        colors = ["#00ff41" if r >= 0 else "#ff1744"
                  for r in (df["Close"] - df["Open"])]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df.index, y=df["Close"], name=ticker,
                             marker_color=colors, marker_line_width=0))
    else:  # LINE
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"], mode="lines", name=ticker,
            line=dict(color="#00ff41", width=1.5),
            fill="tozeroy", fillcolor="rgba(0,255,65,0.04)"
        ))

    fig = add_overlays(fig, df, overlays)

    # Volume subplot
    fig_full = make_subplots(rows=2, cols=1, shared_xaxes=True,
                             row_heights=[0.78, 0.22], vertical_spacing=0.01)
    for trace in fig.data:
        fig_full.add_trace(trace, row=1, col=1)
    vol_colors = ["#00aa2a" if c >= o else "#cc1133"
                  for c, o in zip(df["Close"], df["Open"])]
    fig_full.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume",
                              marker_color=vol_colors, marker_line_width=0,
                              showlegend=False), row=2, col=1)
    fig_full.update_layout(**layout)
    fig_full.update_xaxes(gridcolor="#0d0d0d", linecolor="#1a1a1a")
    fig_full.update_yaxes(gridcolor="#0d0d0d", linecolor="#1a1a1a")
    st.plotly_chart(fig_full, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# MACRO / ECONOMY PLACEHOLDER DATA
# ══════════════════════════════════════════════════════════════════════════════
def get_cpi_data() -> pd.DataFrame:
    # TODO: replace with FRED API here
    # from fredapi import Fred; fred = Fred(api_key='YOUR_KEY'); df = fred.get_series('CPIAUCSL')
    data = {
        "Date": pd.date_range("2023-01-01", periods=26, freq="MS"),
        "CPI (All Items)": [296.8, 298.0, 299.2, 300.3, 301.8, 303.1, 304.3, 305.7,
                             307.1, 308.4, 309.2, 310.7, 311.4, 312.0, 313.2, 314.1,
                             315.3, 316.0, 317.2, 318.5, 319.8, 320.1, 321.4, 322.7,
                             323.5, 324.2],
        "Core CPI":        [300.1, 301.3, 302.4, 303.5, 304.7, 305.8, 306.9, 308.0,
                             309.2, 310.3, 311.4, 312.5, 313.2, 313.9, 314.8, 315.6,
                             316.5, 317.2, 318.0, 318.9, 319.8, 320.5, 321.3, 322.0,
                             322.8, 323.5],
        "YoY %":           [6.4, 6.0, 5.0, 4.9, 4.0, 3.0, 3.2, 3.7, 3.7, 3.2, 3.1,
                             2.9, 3.1, 3.2, 2.8, 2.9, 3.0, 2.7, 2.6, 2.5, 2.7, 2.4,
                             2.3, 2.6, 2.8, 2.7],
        "Core YoY %":      [5.6, 5.5, 5.6, 5.5, 5.3, 4.8, 4.7, 4.3, 4.1, 4.0, 4.0,
                             3.9, 3.8, 3.7, 3.5, 3.4, 3.3, 3.2, 3.2, 3.1, 3.3, 3.2,
                             3.1, 3.0, 2.9, 2.8],
    }
    df = pd.DataFrame(data)
    df["Date"] = df["Date"].dt.strftime("%b %Y")
    return df

def get_pce_data() -> pd.DataFrame:
    # TODO: replace with FRED API here (series: PCEPI, PCEPILFE)
    months = pd.date_range("2023-01-01", periods=26, freq="MS").strftime("%b %Y").tolist()
    return pd.DataFrame({
        "Date":       months,
        "PCE YoY %":  [5.3, 5.1, 4.6, 4.4, 3.8, 3.0, 3.3, 3.5, 3.4, 3.0, 2.6, 2.4,
                       2.5, 2.4, 2.3, 2.3, 2.6, 2.5, 2.3, 2.2, 2.1, 2.3, 2.4, 2.2, 2.3, 2.2],
        "Core PCE %": [4.7, 4.7, 4.7, 4.7, 4.6, 4.1, 3.7, 3.5, 3.4, 3.2, 3.2, 2.9,
                       2.8, 2.7, 2.7, 2.7, 2.6, 2.6, 2.6, 2.5, 2.4, 2.5, 2.4, 2.3, 2.4, 2.3],
        "Fed Target": [2.0] * 26,
    })

def get_rates_table() -> pd.DataFrame:
    # TODO: replace with FRED API here (series: DFF, DFEDTARL, etc.)
    return pd.DataFrame({
        "Instrument":    ["Fed Funds Rate", "SOFR", "3M T-Bill", "2Y Treasury",
                          "5Y Treasury", "10Y Treasury", "30Y Treasury",
                          "TIPS 10Y (Real)", "Breakeven 10Y"],
        "Current %":     [4.33, 4.32, 4.28, 3.95, 3.84, 4.21, 4.52, 1.87, 2.34],
        "Prior Week %":  [4.33, 4.31, 4.25, 4.01, 3.90, 4.28, 4.57, 1.90, 2.38],
        "1M Ago %":      [4.33, 4.30, 4.22, 4.15, 4.05, 4.41, 4.68, 2.01, 2.40],
        "1Y Ago %":      [5.33, 5.31, 5.28, 4.62, 4.28, 4.27, 4.44, 1.99, 2.28],
        "Chg (bps)":     [0, +1, +3, -6, -6, -7, -5, -3, -4],
    })

def get_gdp_data() -> pd.DataFrame:
    # TODO: replace with FRED API here (series: GDP, GDPC1)
    return pd.DataFrame({
        "Quarter":      ["Q1'22","Q2'22","Q3'22","Q4'22","Q1'23","Q2'23","Q3'23",
                         "Q4'23","Q1'24","Q2'24","Q3'24","Q4'24","Q1'25","Q2'25",
                         "Q3'25","Q4'25"],
        "Real GDP QoQ Annualized %":
                        [-1.6, -0.6, 3.2, 2.6, 2.2, 2.4, 4.9, 3.4, 1.4, 3.0, 2.8,
                         2.3, 1.8, 2.1, 2.4, 2.2],
        "Nominal GDP ($T)":
                        [25.0, 24.9, 25.7, 26.1, 26.5, 27.1, 27.6, 28.1, 28.3, 28.9,
                         29.4, 29.9, 30.2, 30.6, 31.0, 31.5],
    })

def get_jobs_data() -> pd.DataFrame:
    # TODO: replace with FRED API here (series: PAYEMS, UNRATE, JOLTS)
    months = pd.date_range("2023-01-01", periods=26, freq="MS").strftime("%b %Y").tolist()
    return pd.DataFrame({
        "Date":              months,
        "NFP (000s)":        [517, 248, 236, 253, 339, 209, 187, 157, 150, 105, 208, 220,
                              186, 167, 142, 194, 175, 151, 168, 180, 143, 188, 158, 165,
                              172, 155],
        "Unemployment %":    [3.4, 3.6, 3.5, 3.4, 3.5, 3.6, 3.5, 3.8, 3.7, 3.9, 4.1,
                              4.2, 4.0, 4.1, 4.2, 4.3, 4.2, 4.3, 4.2, 4.1, 4.3, 4.2,
                              4.1, 4.2, 4.1, 4.2],
        "Participation %":   [62.4, 62.4, 62.6, 62.6, 62.5, 62.6, 62.8, 62.8, 62.7, 62.7,
                              62.7, 62.5, 62.6, 62.5, 62.4, 62.5, 62.6, 62.5, 62.5, 62.4,
                              62.5, 62.4, 62.5, 62.4, 62.5, 62.4],
        "JOLTS (M)":         [11.2, 10.6, 9.8, 9.7, 10.0, 9.6, 9.0, 8.8, 8.5, 8.2, 8.0,
                              7.7, 7.6, 7.5, 7.4, 7.6, 7.5, 7.4, 7.5, 7.4, 7.3, 7.4,
                              7.3, 7.4, 7.3, 7.2],
    })

def get_sector_heatmap() -> pd.DataFrame:
    # TODO: can use yfinance sector ETFs for live data
    sectors = ["XLK Tech","XLF Fin","XLE Energy","XLV Health","XLI Indus",
               "XLY Discr","XLP Staples","XLU Util","XLRE RE","XLB Mater","XLC Comm"]
    timeframes_hm = ["1D","5D","1M","3M","6M","YTD","1Y"]
    rng = np.random.default_rng(42)
    data = rng.normal(0.3, 2.0, (len(sectors), len(timeframes_hm)))
    data[:, 0] = rng.normal(0.1, 0.8, len(sectors))  # 1D smaller moves
    return pd.DataFrame(data.round(2), index=sectors, columns=timeframes_hm)

def get_volatility_table() -> pd.DataFrame:
    return pd.DataFrame({
        "Asset":         ["S&P 500","NASDAQ","Russell 2000","Gold","Crude Oil",
                          "10Y Treasury","EUR/USD","Bitcoin"],
        "VIX/Vol":       [18.2, 22.4, 24.1, 14.8, 32.5, 8.7, 6.4, 55.2],
        "30D HV":        [14.8, 18.9, 20.3, 11.4, 28.7, 7.2, 5.9, 48.7],
        "IV Rank %":     [42, 55, 61, 38, 72, 29, 31, 68],
        "IV Percentile": [45, 58, 63, 40, 75, 31, 33, 71],
        "Put/Call":      [0.82, 0.71, 0.95, 0.68, 1.12, 0.59, 0.74, 0.88],
    })

def get_placeholder_news(section: str) -> list:
    base_news = {
        "EQUITIES": [
            ("S&P 500 Touches Record Highs on Tech Surge", "1h", ["MARKETS", "EQUITY"]),
            ("NVIDIA Reports Blowout Earnings, Raises Guidance", "2h", ["EARNINGS", "TECH"]),
            ("Fed Officials Signal Patience on Rate Cuts", "3h", ["FED", "MACRO"]),
            ("Apple Eyes AI Partnership with OpenAI Rival", "4h", ["TECH", "AI"]),
            ("Buyback Boom: S&P 500 Repurchases Hit $1T Pace", "5h", ["CORPORATE"]),
            ("Small Caps Lag as Dollar Strength Persists", "6h", ["EQUITY", "FX"]),
        ],
        "CREDIT": [
            ("Investment Grade Spreads Tighten to Post-GFC Lows", "1h", ["CREDIT", "IG"]),
            ("High Yield Issuance Surges Amid Risk-On Mood", "2h", ["HY", "CREDIT"]),
            ("CLO Market Sees Record First-Quarter Volume", "3h", ["STRUCTURED"]),
            ("Emerging Market Debt Attracts $5B in Weekly Flows", "5h", ["EM", "CREDIT"]),
        ],
        "RATES": [
            ("10Y Yield Rises to 4.22% on Strong Jobs Data", "30m", ["RATES", "TREASURY"]),
            ("Fed's Waller: No Rush to Cut, Inflation Progress Uneven", "1h", ["FED", "RATES"]),
            ("Treasury Refunding Announcement Raises Supply Fears", "3h", ["SUPPLY", "RATES"]),
            ("TIPS Breakevens Signal Sticky Inflation Expectations", "4h", ["INFLATION"]),
        ],
        "FX": [
            ("Dollar Index Near 104 as US Exceptionalism Narrative Holds", "1h", ["DXY", "FX"]),
            ("Yen Weakens Past 150 Again, BOJ Watch Intensifies", "2h", ["JPY", "BOJ"]),
            ("Euro Tests 1.08 Support Amid Eurozone Growth Fears", "3h", ["EUR", "ECB"]),
            ("Yuan Hits Weakest Since November on PBOC Flexibility", "5h", ["CNY", "PBOC"]),
        ],
        "COMMODITIES": [
            ("Gold Surges to $2,950/oz on Safe Haven Demand", "1h", ["GOLD", "METALS"]),
            ("WTI Crude Holds $78 as OPEC+ Cuts Remain in Force", "2h", ["OIL", "OPEC"]),
            ("Natural Gas Spikes 8% on Cold Snap Forecast", "3h", ["NATGAS", "ENERGY"]),
            ("Copper Signals Global Demand Pickup, Hits 8-Month High", "4h", ["COPPER", "METALS"]),
            ("Wheat Retreats as Black Sea Grain Exports Resume", "5h", ["AGRI", "GRAINS"]),
        ],
        "CRYPTO": [
            ("Bitcoin Consolidates at $88,000 After ETF Inflow Surge", "30m", ["BTC", "CRYPTO"]),
            ("Ethereum Staking Rewards Hit Two-Year High", "2h", ["ETH", "DEFI"]),
            ("SEC Approves Options on Spot Bitcoin ETFs", "3h", ["REGULATION", "ETF"]),
            ("Solana Surpasses Ethereum in Daily Active Users", "5h", ["SOL", "LAYER1"]),
        ],
        "ECONOMY": [
            ("March CPI: +2.7% YoY, Core at +2.9%", "2h", ["CPI", "INFLATION"]),
            ("February NFP: +155K, Rate Holds at 4.1%", "1d", ["JOBS", "MACRO"]),
            ("Q4 GDP Revised Up to 2.3% Annualized", "2d", ["GDP", "GROWTH"]),
            ("Consumer Confidence Dips on Tariff Uncertainty", "1d", ["SENTIMENT"]),
            ("ISM Manufacturing Returns to Expansion Territory", "2d", ["PMI", "INDUSTRY"]),
        ],
        "GEOPOLITICS": [
            ("US-China Trade Talks Stall Over Tech Restrictions", "1h", ["TRADE", "CHINA"]),
            ("Middle East Tensions Ease; Brent Drops $2", "3h", ["GEOPOLIT", "OIL"]),
            ("NATO Summit: Defense Spending Pledges Increase", "5h", ["NATO", "DEFENSE"]),
            ("Russia Energy Exports Rerouted Through Emerging Markets", "1d", ["RUSSIA", "ENERGY"]),
            ("Taiwan Strait: Navy Exercises Raise Tensions", "1d", ["TAIWAN", "RISK"]),
        ],
        "FUNDS": [
            ("Hedge Funds Reduce Equity Net Long to 6-Month Low", "2h", ["HF", "POSITIONING"]),
            ("Vanguard Reports Record $1.2T in Annual ETF Flows", "3h", ["ETF", "PASSIVE"]),
            ("Bridgewater Increases Gold Allocation to 18%", "4h", ["HF", "GOLD"]),
            ("Private Equity Dry Powder Hits $3.9T as Deals Slow", "5h", ["PE", "CREDIT"]),
        ],
    }
    return base_news.get(section, base_news["EQUITIES"])

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Watchlist
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div style="font-size:0.65rem;color:#00ff41;letter-spacing:0.2em;padding:0.25rem 0 0.5rem;text-transform:uppercase;border-bottom:1px solid #1a1a1a;margin-bottom:0.5rem;">▸ WATCHLIST</div>', unsafe_allow_html=True)

    add_col, btn_col = st.columns([3, 1])
    with add_col:
        new_ticker = st.text_input("ADD TICKER", placeholder="e.g. TSLA", key="wl_input", label_visibility="collapsed")
    with btn_col:
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        if st.button("+", key="wl_add"):
            t = new_ticker.strip().upper()
            if t and t not in st.session_state.watchlist:
                st.session_state.watchlist.append(t)
                st.rerun()

    # Fetch all watchlist quotes
    if HAS_YF:
        wl_quotes = fetch_bulk_quotes(st.session_state.watchlist)
    else:
        wl_quotes = {}

    for ticker in st.session_state.watchlist:
        q = wl_quotes.get(ticker, {})
        price = f"{q.get('price', '—')}" if q else "—"
        pct   = q.get("pct", 0) if q else 0
        chg_str  = f"{pct:+.2f}%" if q else "—"
        chg_class = "tick-up" if pct >= 0 else "tick-down"

        c1, c2 = st.columns([3, 2])
        with c1:
            st.markdown(f'<div style="font-size:0.68rem;color:#ffab00;font-weight:700;padding:0.15rem 0;">{ticker}</div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div style="font-size:0.65rem;text-align:right;color:#ededed;padding:0.15rem 0;">{price}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:0.6rem;text-align:right;class="{chg_class}" style="color:{"#00ff41" if pct >= 0 else "#ff1744"}">{chg_str}</div>', unsafe_allow_html=True)
        st.markdown('<div style="border-bottom:1px solid #111111;margin-bottom:0.1rem;"></div>', unsafe_allow_html=True)

    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
    if st.button("↺ REFRESH WATCHLIST", key="wl_refresh"):
        st.cache_data.clear()
        st.rerun()

    # Remove ticker
    if st.session_state.watchlist:
        rm = st.selectbox("REMOVE", ["—"] + st.session_state.watchlist, key="wl_rm",
                          label_visibility="visible")
        if rm != "—":
            if st.button(f"✕ REMOVE {rm}"):
                st.session_state.watchlist.remove(rm)
                st.rerun()

    st.markdown('<div style="height:16px;border-top:1px solid #1a1a1a;margin-top:0.5rem;"></div>', unsafe_allow_html=True)

    # Quick macro numbers
    st.markdown('<div style="font-size:0.55rem;color:#576070;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:0.3rem;">MACRO SNAPSHOT</div>', unsafe_allow_html=True)
    macro_snap = [
        ("FED FUNDS", "4.25–4.50%", ""),
        ("CPI YOY", "2.8%", "up"),
        ("CORE PCE", "2.8%", "up"),
        ("UNEMPLOYMENT", "4.1%", ""),
        ("GDP (Q4)", "+2.3%", "up"),
        ("10Y YIELD", "4.21%", ""),
        ("DXY", "103.8", ""),
        ("VIX", "18.2", ""),
    ]
    for label, val, direction in macro_snap:
        color = "#00ff41" if direction == "up" else ("#ff1744" if direction == "dn" else "#e0e0e0")
        st.markdown(f'<div style="display:flex;justify-content:space-between;font-size:0.58rem;padding:0.1rem 0;border-bottom:1px solid #0d0d0d;"><span style="color:#576070;">{label}</span><span style="color:{color};font-weight:600;">{val}</span></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HEADER BAR
# ══════════════════════════════════════════════════════════════════════════════
now_str = datetime.datetime.utcnow().strftime("UTC %Y-%m-%d %H:%M")
st.markdown(f"""
<div class="top-bar">
  <div class="top-logo">▸ THE MARKET TERMINAL</div>
  <div style="font-size:0.58rem;color:#333333;letter-spacing:0.08em;flex:1;padding:0 1.5rem;overflow:hidden;white-space:nowrap;">
    S&P 500 <span style="color:#00ff41">5,614 ▲0.41%</span> &nbsp;|&nbsp;
    NASDAQ <span style="color:#00ff41">17,890 ▲0.62%</span> &nbsp;|&nbsp;
    DOW <span style="color:#ff1744">39,213 ▼0.08%</span> &nbsp;|&nbsp;
    VIX <span style="color:#ffab00">18.24</span> &nbsp;|&nbsp;
    10Y <span style="color:#ff1744">4.21%</span> &nbsp;|&nbsp;
    DXY <span style="color:#ededed">103.82</span> &nbsp;|&nbsp;
    GOLD <span style="color:#00ff41">$2,947</span> &nbsp;|&nbsp;
    WTI <span style="color:#ededed">$78.14</span> &nbsp;|&nbsp;
    BTC <span style="color:#00ff41">$88,420</span>
  </div>
  <div class="top-time">{now_str}</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN NAVIGATION TABS
# ══════════════════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "EQUITIES", "CREDIT", "RATES", "FX",
    "COMMODITIES", "FUNDS", "CRYPTO", "ECONOMY", "GEOPOLITICS"
])

# ══════════════════════════════════════════════════════════════════════════════
# SHARED CHART PANEL RENDERER
# ══════════════════════════════════════════════════════════════════════════════
def render_section(section_name: str, default_tickers: list):
    """Renders the standard chart / screener / heatmap / news layout for any section."""

    sub_tabs = st.tabs(["CHARTS", "SCREENER", "HEATMAP", "VOLATILITY", "NEWS", "FORMULAS"])

    # ── CHARTS ──────────────────────────────────────────────────────────────
    with sub_tabs[0]:
        col_ctrl, col_chart = st.columns([1, 5])
        with col_ctrl:
            ticker = st.selectbox("TICKER", default_tickers, key=f"ticker_{section_name}")
            chart_type = st.radio("TYPE", ["CANDLESTICK", "LINE", "BAR"], key=f"ct_{section_name}")
            tf = st.radio("TIMEFRAME", list(TIMEFRAMES.keys()), key=f"tf_{section_name}")
            overlays = st.multiselect("OVERLAYS",
                ["SMA 20", "SMA 50", "EMA 20", "Bollinger Bands", "Fibonacci"],
                key=f"ov_{section_name}")

        with col_chart:
            period, interval = TIMEFRAMES[tf]
            # Quote strip
            q = fetch_quote(ticker)
            if q:
                pct   = q.get("pct", 0)
                price = q.get("price", "—")
                chg   = q.get("chg", 0)
                chg_color = "#00ff41" if pct >= 0 else "#ff1744"
                arrow = "▲" if pct >= 0 else "▼"
                st.markdown(f"""
                <div style="display:flex;align-items:baseline;gap:1rem;padding:0.2rem 0 0.5rem;border-bottom:1px solid #1a1a1a;margin-bottom:0.5rem;">
                  <span style="font-size:1.1rem;color:#ffab00;font-weight:700;letter-spacing:0.05em;">{ticker}</span>
                  <span style="font-family:'JetBrains Mono',monospace;font-size:1.35rem;color:#ededed;font-weight:700;">{price:,}</span>
                  <span style="font-size:0.85rem;color:{chg_color};font-weight:600;">{arrow} {chg:+.4f} &nbsp; ({pct:+.2f}%)</span>
                  <span style="font-size:0.6rem;color:#333333;margin-left:auto;">15min delay · yfinance</span>
                </div>""", unsafe_allow_html=True)
            render_chart(ticker, period, interval, chart_type, overlays)

    # ── SCREENER ──────────────────────────────────────────────────────────────
    with sub_tabs[1]:
        st.markdown('<div class="bb-section">SCREENER — TOP MOVERS</div>', unsafe_allow_html=True)
        if HAS_YF:
            screener_quotes = fetch_bulk_quotes(default_tickers[:12])
            rows = []
            for t, q in screener_quotes.items():
                rows.append({
                    "Ticker": t,
                    "Price":  q.get("price", "—"),
                    "Chg":    q.get("chg", 0),
                    "Chg %":  q.get("pct", 0),
                })
            if rows:
                df_sc = pd.DataFrame(rows).sort_values("Chg %", ascending=False)

                def color_pct(val):
                    if isinstance(val, (int, float)):
                        return "color: #00ff41" if val >= 0 else "color: #ff1744"
                    return ""

                st.dataframe(
                    df_sc.style
                        .format({"Price": "{:.4f}", "Chg": "{:+.4f}", "Chg %": "{:+.2f}%"})
                        .applymap(color_pct, subset=["Chg %", "Chg"]),
                    use_container_width=True, hide_index=True, height=400
                )
        else:
            st.info("yfinance not installed — screener unavailable")

        # Holdings table (placeholder)
        st.markdown('<div class="bb-section">TOP HOLDINGS / WEIGHTS</div>', unsafe_allow_html=True)
        holdings_data = {
            "Name":   [t.replace("=F","").replace("-USD","").replace("=X","")
                       for t in default_tickers[:8]],
            "Symbol": default_tickers[:8],
            "Weight": sorted([round(random.uniform(3, 18), 2) for _ in range(8)], reverse=True),
            "3M Ret": [round(random.gauss(3, 8), 2) for _ in range(8)],
        }
        df_hold = pd.DataFrame(holdings_data)
        st.dataframe(df_hold.style.format({"Weight":"{:.2f}%","3M Ret":"{:+.2f}%"})
                     .background_gradient(subset=["3M Ret"], cmap="RdYlGn"),
                     use_container_width=True, hide_index=True)

    # ── HEATMAP ──────────────────────────────────────────────────────────────
    with sub_tabs[2]:
        st.markdown('<div class="bb-section">SECTOR / ASSET PERFORMANCE HEATMAP</div>', unsafe_allow_html=True)
        hm_df = get_sector_heatmap()

        fig_hm = px.imshow(
            hm_df, text_auto=True,
            color_continuous_scale=[
                [0.0,  "#3a0008"], [0.35, "#ff1744"],
                [0.5,  "#111111"],
                [0.65, "#003a0e"], [1.0,  "#00ff41"]
            ],
            zmin=-8, zmax=8, aspect="auto"
        )
        fig_hm.update_traces(textfont=dict(family="JetBrains Mono", size=10),
                             texttemplate="%{z:+.1f}%")
        fig_hm.update_layout(**PLOTLY_BASE, height=360,
                             coloraxis_showscale=False)
        st.plotly_chart(fig_hm, use_container_width=True)

        # Individual sector charts
        st.markdown('<div class="bb-section">SECTOR ETF PERFORMANCE</div>', unsafe_allow_html=True)
        sector_etfs = ["XLK","XLF","XLE","XLV","XLI","XLY","XLP","XLU","XLRE","XLB","XLC"]
        if HAS_YF:
            sector_quotes = fetch_bulk_quotes(sector_etfs)
            sc_rows = [{"ETF": t, "Price": q.get("price","—"), "Chg %": q.get("pct",0)}
                       for t, q in sector_quotes.items()]
            df_sec = pd.DataFrame(sc_rows)
            colors_bar = ["#00ff41" if p >= 0 else "#ff1744" for p in df_sec["Chg %"]]
            fig_bar = go.Figure(go.Bar(x=df_sec["ETF"], y=df_sec["Chg %"],
                                       marker_color=colors_bar, marker_line_width=0))
            fig_bar.update_layout(**PLOTLY_BASE, height=220, showlegend=False,
                                  title="Sector ETFs — Daily % Change")
            fig_bar.add_hline(y=0, line_color="#333333", line_width=0.8)
            st.plotly_chart(fig_bar, use_container_width=True)

    # ── VOLATILITY ──────────────────────────────────────────────────────────
    with sub_tabs[3]:
        st.markdown('<div class="bb-section">VOLATILITY DASHBOARD</div>', unsafe_allow_html=True)
        df_vol = get_volatility_table()

        def color_vix(val):
            if isinstance(val, (int, float)):
                if val > 30: return "color: #ff1744; font-weight: 700"
                if val > 20: return "color: #ffab00"
                return "color: #00ff41"
            return ""

        st.dataframe(
            df_vol.style
                .format({"VIX/Vol": "{:.1f}", "30D HV": "{:.1f}",
                         "IV Rank %": "{:.0f}", "IV Percentile": "{:.0f}",
                         "Put/Call": "{:.2f}"})
                .applymap(color_vix, subset=["VIX/Vol"]),
            use_container_width=True, hide_index=True
        )

        # VIX historical (placeholder)
        st.markdown('<div class="bb-section">VIX TERM STRUCTURE (PLACEHOLDER)</div>', unsafe_allow_html=True)
        vix_maturities = ["Spot","1M","2M","3M","4M","5M","6M","12M"]
        vix_levels = [18.2, 19.1, 19.8, 20.3, 20.8, 21.1, 21.4, 22.0]
        fig_ts = go.Figure(go.Scatter(x=vix_maturities, y=vix_levels, mode="lines+markers",
                                       line=dict(color="#ffab00", width=1.5),
                                       marker=dict(color="#ffab00", size=6)))
        fig_ts.update_layout(**PLOTLY_BASE, height=200, title="VIX Futures Term Structure")
        st.plotly_chart(fig_ts, use_container_width=True)

    # ── NEWS ──────────────────────────────────────────────────────────────────
    with sub_tabs[4]:
        news_items = get_placeholder_news(section_name)
        st.markdown('<div class="bb-section">LATEST HEADLINES</div>', unsafe_allow_html=True)
        for headline, age, tags in news_items:
            tags_html = "".join(f'<span class="news-tag">{t}</span>' for t in tags)
            st.markdown(f"""
            <div class="news-card">
              <div class="news-headline">{headline}</div>
              <div class="news-meta">{tags_html} &nbsp;{age} ago</div>
            </div>""", unsafe_allow_html=True)

    # ── FORMULAS ──────────────────────────────────────────────────────────────
    with sub_tabs[5]:
        st.markdown('<div class="bb-section">CUSTOM FORMULA CALCULATOR</div>', unsafe_allow_html=True)
        st.caption("Build custom spreads, ratios, and derived metrics. Uses yfinance live data.")

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            formula_presets = {
                "Crack Spread (3-2-1)": ("CL=F", "RB=F", "3-2-1 Crack Spread = (2×Gasoline + 1×Heating Oil - 3×Crude) / 3"),
                "Gold/Silver Ratio":    ("GC=F", "SI=F", "Gold/Silver Ratio = Gold Price / Silver Price"),
                "S&P / Gold Ratio":     ("SPY", "GC=F", "SPY/Gold = S&P Price / Gold Price"),
                "Custom":               ("", "", ""),
            }
            preset = st.selectbox("PRESET FORMULA", list(formula_presets.keys()), key=f"formula_preset_{section_name}")
            t1_default, t2_default, desc = formula_presets[preset]
            if desc:
                st.markdown(f'<div style="font-size:0.62rem;color:#576070;padding:0.25rem 0;">{desc}</div>', unsafe_allow_html=True)

        with col_f2:
            ticker_a = st.text_input("TICKER A", value=t1_default or default_tickers[0], key=f"fa_{section_name}")
            ticker_b = st.text_input("TICKER B", value=t2_default or (default_tickers[1] if len(default_tickers) > 1 else ""), key=f"fb_{section_name}")
            formula_op = st.radio("OPERATOR", ["A / B", "A - B", "A + B", "A × B"], key=f"fop_{section_name}", horizontal=True)
            tf_f = st.radio("PERIOD", ["1M","3M","1Y","5Y"], key=f"ftf_{section_name}", horizontal=True)

        if st.button("▸ CALCULATE & CHART", key=f"fcalc_{section_name}"):
            p, i = TIMEFRAMES[tf_f]
            with st.spinner("Fetching…"):
                df_a = fetch_ohlcv(ticker_a.upper(), p, i)
                df_b = fetch_ohlcv(ticker_b.upper(), p, i) if ticker_b else pd.DataFrame()

            if df_a.empty:
                st.error(f"No data for {ticker_a}")
            elif not df_b.empty:
                close_a = df_a["Close"].rename(ticker_a)
                close_b = df_b["Close"].rename(ticker_b)
                combined = pd.concat([close_a, close_b], axis=1).dropna()

                if formula_op == "A / B":
                    result = combined.iloc[:,0] / combined.iloc[:,1]
                    label  = f"{ticker_a} / {ticker_b}"
                elif formula_op == "A - B":
                    result = combined.iloc[:,0] - combined.iloc[:,1]
                    label  = f"{ticker_a} - {ticker_b}"
                elif formula_op == "A + B":
                    result = combined.iloc[:,0] + combined.iloc[:,1]
                    label  = f"{ticker_a} + {ticker_b}"
                else:
                    result = combined.iloc[:,0] * combined.iloc[:,1]
                    label  = f"{ticker_a} × {ticker_b}"

                fig_f = go.Figure()
                fig_f.add_trace(go.Scatter(x=result.index, y=result, mode="lines",
                                            name=label, line=dict(color="#00b8d4", width=1.5),
                                            fill="tozeroy", fillcolor="rgba(0,184,212,0.05)"))
                fig_f.update_layout(**PLOTLY_BASE, height=320, title=label)
                st.plotly_chart(fig_f, use_container_width=True)

                summary = pd.DataFrame({
                    "Metric": ["Current","Min","Max","Mean","Std Dev","% from Min","% from Max"],
                    "Value": [
                        round(result.iloc[-1], 4),
                        round(result.min(), 4),
                        round(result.max(), 4),
                        round(result.mean(), 4),
                        round(result.std(), 4),
                        round((result.iloc[-1] - result.min()) / abs(result.min()) * 100, 2),
                        round((result.iloc[-1] - result.max()) / abs(result.max()) * 100, 2),
                    ]
                })
                st.dataframe(summary, use_container_width=True, hide_index=True)
            else:
                # Single ticker chart
                fig_f = go.Figure(go.Scatter(x=df_a.index, y=df_a["Close"], mode="lines",
                                              line=dict(color="#00ff41", width=1.5)))
                fig_f.update_layout(**PLOTLY_BASE, height=320, title=ticker_a)
                st.plotly_chart(fig_f, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION TABS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:  # EQUITIES
    render_section("EQUITIES", EQUITY_TICKERS["EQUITIES"])

with tabs[1]:  # CREDIT
    render_section("CREDIT", EQUITY_TICKERS["CREDIT"])

with tabs[2]:  # RATES
    st.tabs_inner = st.tabs(["CHARTS", "YIELD CURVE", "CPI / INFLATION", "FED POLICY", "NEWS", "FORMULAS"])
    with st.tabs_inner[0]:
        render_section("RATES", EQUITY_TICKERS["RATES"])
    with st.tabs_inner[1]:
        st.markdown('<div class="bb-section">US TREASURY YIELD CURVE</div>', unsafe_allow_html=True)
        maturities = ["1M","3M","6M","1Y","2Y","3Y","5Y","7Y","10Y","20Y","30Y"]
        yields_current = [4.31, 4.28, 4.18, 4.02, 3.95, 3.90, 3.84, 3.90, 4.21, 4.52, 4.52]
        yields_1y_ago  = [5.51, 5.48, 5.38, 5.02, 4.62, 4.45, 4.28, 4.35, 4.27, 4.55, 4.44]
        yields_2y_ago  = [4.51, 4.82, 5.05, 5.08, 4.86, 4.70, 4.39, 4.34, 4.00, 4.10, 3.96]
        fig_yc = go.Figure()
        for yvals, label, color, dash in [
            (yields_current, "Current",  "#00ff41", "solid"),
            (yields_1y_ago,  "1Y Ago",   "#ffab00", "dot"),
            (yields_2y_ago,  "2Y Ago",   "#555555", "dash"),
        ]:
            fig_yc.add_trace(go.Scatter(x=maturities, y=yvals, mode="lines+markers",
                                         name=label, line=dict(color=color, width=1.5, dash=dash),
                                         marker=dict(size=5)))
        fig_yc.update_layout(**PLOTLY_BASE, height=360, title="US Treasury Yield Curve")
        st.plotly_chart(fig_yc, use_container_width=True)

        st.markdown('<div class="bb-section">RATES TABLE</div>', unsafe_allow_html=True)
        df_rates = get_rates_table()

        def color_bps(val):
            if isinstance(val, (int, float)):
                if val > 0: return "color: #ff1744"
                if val < 0: return "color: #00ff41"
            return "color: #555555"

        st.dataframe(df_rates.style.applymap(color_bps, subset=["Chg (bps)"]),
                     use_container_width=True, hide_index=True)

    with st.tabs_inner[2]:
        # CPI section
        st.markdown('<div class="bb-section">CPI — CONSUMER PRICE INDEX</div>', unsafe_allow_html=True)
        df_cpi = get_cpi_data()

        fig_cpi = go.Figure()
        fig_cpi.add_trace(go.Bar(x=df_cpi["Date"], y=df_cpi["YoY %"], name="CPI YoY",
                                  marker_color=["#ff1744" if v > 3 else "#ffab00" if v > 2 else "#00ff41"
                                                for v in df_cpi["YoY %"]]))
        fig_cpi.add_trace(go.Scatter(x=df_cpi["Date"], y=df_cpi["Core YoY %"], name="Core CPI",
                                      mode="lines+markers", line=dict(color="#00b8d4", width=1.5)))
        fig_cpi.add_hline(y=2.0, line_dash="dot", line_color="#333333",
                           annotation_text="Fed 2% Target", annotation_font_color="#333333")
        fig_cpi.update_layout(**PLOTLY_BASE, height=340, title="CPI YoY % — Jan 2023 to Present")
        st.plotly_chart(fig_cpi, use_container_width=True)

        col_cpi1, col_cpi2 = st.columns(2)
        with col_cpi1:
            st.markdown('<div class="bb-section">CPI DATA TABLE</div>', unsafe_allow_html=True)
            st.dataframe(df_cpi.tail(12).style.format({"YoY %":"{:.1f}%","Core YoY %":"{:.1f}%"}),
                         use_container_width=True, hide_index=True, height=300)
        with col_cpi2:
            st.markdown('<div class="bb-section">PCE / FED PREFERRED MEASURE</div>', unsafe_allow_html=True)
            df_pce = get_pce_data()
            st.dataframe(df_pce.tail(12).style.format({"PCE YoY %":"{:.1f}%","Core PCE %":"{:.1f}%","Fed Target":"{:.1f}%"}),
                         use_container_width=True, hide_index=True, height=300)

        st.markdown('<div class="bb-section">CPI COMPONENTS (LATEST MONTH — PLACEHOLDER)</div>', unsafe_allow_html=True)
        components = pd.DataFrame({
            "Component":  ["All Items","Food","Energy","Core","Shelter","Medical","Transport","Apparel","Education","Recreation"],
            "Weight %":   [100, 13.5, 7.2, 79.3, 36.2, 6.5, 5.9, 2.5, 3.1, 5.5],
            "YoY %":      [2.8, 2.2, 3.5, 3.1, 5.8, 2.1, 6.2, 0.3, 4.5, 1.2],
            "MoM %":      [0.4, 0.2, 1.2, 0.3, 0.5, 0.1, 0.8, -0.1, 0.3, 0.1],
            "3M Ann %":   [3.1, 2.5, 4.8, 3.4, 6.1, 2.3, 8.1, 0.2, 5.0, 1.4],
        })

        def color_yoy(val):
            if isinstance(val, (int, float)):
                if val > 5: return "color: #ff1744; font-weight: 700"
                if val > 3: return "color: #ffab00"
                if val > 2: return "color: #ededed"
                return "color: #00ff41"
            return ""

        st.dataframe(components.style.applymap(color_yoy, subset=["YoY %","3M Ann %"])
                     .format({"Weight %":"{:.1f}","YoY %":"{:.1f}%","MoM %":"{:+.1f}%","3M Ann %":"{:.1f}%"}),
                     use_container_width=True, hide_index=True)

    with st.tabs_inner[3]:
        st.markdown('<div class="bb-section">FED POLICY TIMELINE</div>', unsafe_allow_html=True)
        fed_dates = ["Mar'22","May'22","Jun'22","Jul'22","Sep'22","Nov'22","Dec'22",
                     "Feb'23","Mar'23","May'23","Jun'23","Jul'23","Sep'23","Nov'23",
                     "Jan'24","Mar'24","Sep'24","Nov'24","Dec'24"]
        fed_rates = [0.25, 0.75, 1.50, 2.25, 3.00, 3.75, 4.25, 4.50, 4.75, 5.00,
                     5.00, 5.25, 5.25, 5.25, 5.25, 5.25, 4.75, 4.50, 4.25]
        fig_fed = go.Figure()
        fig_fed.add_trace(go.Scatter(x=fed_dates, y=fed_rates, mode="lines+markers",
                                      line=dict(color="#ffab00", width=2, shape="hv"),
                                      marker=dict(size=7, color="#ffab00"), name="Fed Funds Rate"))
        fig_fed.add_hline(y=2.0, line_dash="dot", line_color="#333333",
                           annotation_text="Neutral Rate Est.", annotation_font_color="#333333")
        fig_fed.update_layout(**PLOTLY_BASE, height=320, title="Federal Funds Rate Target (Upper Bound)")
        st.plotly_chart(fig_fed, use_container_width=True)

        st.markdown('<div class="bb-section">NEXT FOMC MEETING</div>', unsafe_allow_html=True)
        fomc_data = pd.DataFrame({
            "Date":    ["May 6-7, 2025","Jun 17-18, 2025","Jul 29-30, 2025","Sep 16-17, 2025","Oct 28-29, 2025","Dec 9-10, 2025"],
            "Type":    ["FOMC","FOMC","FOMC","FOMC","FOMC","FOMC"],
            "Prob Cut":["32%","51%","68%","79%","85%","90%"],
            "Consensus":["Hold","Hold/Cut","Cut","Cut","Cut","Cut"],
        })
        st.dataframe(fomc_data, use_container_width=True, hide_index=True)

    with st.tabs_inner[4]:
        for h, a, tags in get_placeholder_news("RATES"):
            tags_html = "".join(f'<span class="news-tag">{t}</span>' for t in tags)
            st.markdown(f'<div class="news-card"><div class="news-headline">{h}</div><div class="news-meta">{tags_html} {a} ago</div></div>', unsafe_allow_html=True)

    with st.tabs_inner[5]:
        st.info("See FORMULAS tab in any section's sub-navigation.")

with tabs[3]:  # FX
    render_section("FX", EQUITY_TICKERS["FX"])

with tabs[4]:  # COMMODITIES
    render_section("COMMODITIES", EQUITY_TICKERS["COMMODITIES"])

with tabs[5]:  # FUNDS
    render_section("FUNDS", EQUITY_TICKERS["FUNDS"])

with tabs[6]:  # CRYPTO
    render_section("CRYPTO", EQUITY_TICKERS["CRYPTO"])

with tabs[7]:  # ECONOMY
    econ_tabs = st.tabs(["GDP", "JOBS", "CPI OVERVIEW", "LEADING INDICATORS", "GLOBAL COMPARISON", "DATA UPLOAD"])

    with econ_tabs[0]:
        st.markdown('<div class="bb-section">GROSS DOMESTIC PRODUCT</div>', unsafe_allow_html=True)
        df_gdp = get_gdp_data()
        fig_gdp = go.Figure()
        colors_gdp = ["#00ff41" if v > 0 else "#ff1744" for v in df_gdp["Real GDP QoQ Annualized %"]]
        fig_gdp.add_trace(go.Bar(x=df_gdp["Quarter"],
                                  y=df_gdp["Real GDP QoQ Annualized %"],
                                  marker_color=colors_gdp, name="Real GDP QoQ Ann.%"))
        fig_gdp.add_hline(y=0, line_color="#222222", line_width=0.8)
        fig_gdp.update_layout(**PLOTLY_BASE, height=320, title="US Real GDP — QoQ Annualized %")
        st.plotly_chart(fig_gdp, use_container_width=True)

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.dataframe(df_gdp.style.format({"Real GDP QoQ Annualized %":"{:+.1f}%",
                                               "Nominal GDP ($T)":"${:.1f}T"}),
                         use_container_width=True, hide_index=True)
        with col_g2:
            gdp_components = pd.DataFrame({
                "Component":   ["Personal Consumption","Fixed Investment","Govt Spending","Net Exports","Inventories"],
                "Contribution": [1.67, 0.52, 0.37, -0.20, -0.03],
                "Share of GDP": [68.2, 18.4, 17.5, -3.8, 0.5],
            })
            st.dataframe(gdp_components.style.format({"Contribution":"{:+.2f}pp","Share of GDP":"{:.1f}%"})
                         .background_gradient(subset=["Contribution"], cmap="RdYlGn"),
                         use_container_width=True, hide_index=True)

    with econ_tabs[1]:
        st.markdown('<div class="bb-section">LABOR MARKET</div>', unsafe_allow_html=True)
        df_jobs = get_jobs_data()
        fig_jobs = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                  row_heights=[0.6, 0.4], vertical_spacing=0.05)
        fig_jobs.add_trace(go.Bar(x=df_jobs["Date"], y=df_jobs["NFP (000s)"],
                                   marker_color=["#00ff41" if v > 0 else "#ff1744" for v in df_jobs["NFP (000s)"]],
                                   name="NFP (000s)"), row=1, col=1)
        fig_jobs.add_trace(go.Scatter(x=df_jobs["Date"], y=df_jobs["Unemployment %"],
                                       mode="lines", line=dict(color="#ffab00", width=1.5),
                                       name="Unemployment %"), row=2, col=1)
        fig_jobs.update_layout(**PLOTLY_BASE, height=400, title="Nonfarm Payrolls & Unemployment Rate")
        fig_jobs.update_xaxes(gridcolor="#0d0d0d")
        fig_jobs.update_yaxes(gridcolor="#0d0d0d")
        st.plotly_chart(fig_jobs, use_container_width=True)
        st.dataframe(df_jobs.tail(12).style.format({"Unemployment %":"{:.1f}%","Participation %":"{:.1f}%","JOLTS (M)":"{:.1f}M"}),
                     use_container_width=True, hide_index=True)

    with econ_tabs[2]:
        st.markdown('<div class="bb-section">INFLATION OVERVIEW</div>', unsafe_allow_html=True)
        df_cpi2 = get_cpi_data()
        df_pce2 = get_pce_data()
        fig_inf = go.Figure()
        fig_inf.add_trace(go.Scatter(x=df_cpi2["Date"], y=df_cpi2["YoY %"],
                                      mode="lines", name="CPI YoY", line=dict(color="#ff1744", width=1.5)))
        fig_inf.add_trace(go.Scatter(x=df_cpi2["Date"], y=df_cpi2["Core YoY %"],
                                      mode="lines", name="Core CPI", line=dict(color="#ffab00", width=1.5)))
        fig_inf.add_trace(go.Scatter(x=df_pce2["Date"], y=df_pce2["Core PCE %"],
                                      mode="lines", name="Core PCE", line=dict(color="#00b8d4", width=1.5, dash="dot")))
        fig_inf.add_hline(y=2.0, line_dash="dot", line_color="#222222",
                           annotation_text="2%", annotation_font_color="#444444")
        fig_inf.update_layout(**PLOTLY_BASE, height=340, title="US Inflation Gauges vs Fed Target")
        st.plotly_chart(fig_inf, use_container_width=True)

    with econ_tabs[3]:
        st.markdown('<div class="bb-section">LEADING ECONOMIC INDICATORS</div>', unsafe_allow_html=True)
        lei_data = pd.DataFrame({
            "Indicator":    ["ISM Mfg PMI","ISM Services PMI","Conf. Board LEI",
                             "Philadelphia Fed","Empire State Mfg","Consumer Confidence",
                             "U. Michigan Sentiment","Building Permits (M)","Housing Starts (M)"],
            "Latest":       [50.3, 53.5, 100.2, 12.5, 5.7, 98.2, 72.5, 1.45, 1.38],
            "Prior":        [49.1, 52.8, 99.8, 8.2, -3.6, 99.7, 71.8, 1.48, 1.34],
            "Consensus":    [50.0, 53.2, 100.0, 10.0, 2.0, 100.0, 72.0, 1.46, 1.37],
            "Direction":    ["▲","▲","▲","▲","▲","▼","▲","▼","▲"],
        })
        st.dataframe(lei_data, use_container_width=True, hide_index=True)

    with econ_tabs[4]:
        st.markdown('<div class="bb-section">GLOBAL MACRO COMPARISON</div>', unsafe_allow_html=True)
        global_data = pd.DataFrame({
            "Country/Region": ["United States","Eurozone","United Kingdom","Japan",
                               "China","Canada","Australia","Brazil","India","Mexico"],
            "GDP Growth %":   [2.3, 0.9, 0.8, 0.1, 4.9, 1.2, 1.5, 3.1, 7.2, 2.8],
            "CPI YoY %":      [2.8, 2.6, 3.4, 2.8, 0.7, 2.8, 3.6, 4.8, 5.1, 4.5],
            "Policy Rate %":  [4.33, 2.50, 4.50, 0.50, 3.10, 3.00, 4.10, 10.75, 6.25, 9.00],
            "Unemployment %": [4.1, 6.2, 4.4, 2.5, 5.2, 6.7, 4.0, 6.8, 7.8, 3.2],
            "Curr Account %": [-3.2, 2.8, -3.5, 3.1, 1.5, -2.0, -1.5, -2.8, -1.9, -1.2],
        })
        st.dataframe(global_data.style.background_gradient(subset=["GDP Growth %"], cmap="RdYlGn")
                     .format({"GDP Growth %":"{:.1f}%","CPI YoY %":"{:.1f}%","Policy Rate %":"{:.2f}%",
                              "Unemployment %":"{:.1f}%","Curr Account %":"{:.1f}%"}),
                     use_container_width=True, hide_index=True)

    with econ_tabs[5]:
        st.markdown('<div class="bb-section">DATA UPLOAD</div>', unsafe_allow_html=True)
        col_up1, col_up2 = st.columns(2)
        with col_up1:
            pdf_file = st.file_uploader("UPLOAD PDF", type=["pdf"])
            if pdf_file:
                if HAS_PYPDF2:
                    try:
                        reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
                        text = "\n".join(p.extract_text() or "" for p in reader.pages)
                        st.session_state.uploaded_text = text
                        st.success(f"✓ {len(reader.pages)} pages / {len(text):,} chars")
                        with st.expander("PREVIEW"):
                            st.text(text[:1500])
                    except Exception as e:
                        st.error(str(e))
                else:
                    st.warning("PyPDF2 not installed")
        with col_up2:
            xl_file = st.file_uploader("UPLOAD EXCEL / CSV", type=["xlsx","xls","csv"])
            if xl_file:
                try:
                    df_up = pd.read_csv(xl_file) if xl_file.name.endswith(".csv") else pd.read_excel(xl_file)
                    st.session_state.custom_df = df_up
                    st.success(f"✓ {len(df_up):,} rows × {len(df_up.columns)} cols")
                    st.dataframe(df_up.head(30), use_container_width=True)
                except Exception as e:
                    st.error(str(e))

        if st.session_state.custom_df is not None:
            st.markdown('<div class="bb-section">UPLOADED DATA PREVIEW</div>', unsafe_allow_html=True)
            st.dataframe(st.session_state.custom_df, use_container_width=True)

with tabs[8]:  # GEOPOLITICS
    geo_tabs = st.tabs(["RISK MAP", "SAFE HAVENS", "TRADE FLOWS", "NEWS"])

    with geo_tabs[0]:
        st.markdown('<div class="bb-section">GEOPOLITICAL RISK MONITOR</div>', unsafe_allow_html=True)
        geo_risks = pd.DataFrame({
            "Region":           ["Middle East","Eastern Europe","South China Sea","Korean Peninsula",
                                 "Taiwan Strait","Sahel / W. Africa","Latin America","Arctic"],
            "Risk Score (0-10)":[7.2, 6.8, 6.5, 5.0, 7.0, 5.5, 4.0, 3.5],
            "Trend":            ["→","↓","↑","→","↑","→","↓","↑"],
            "Key Asset Impact":  ["WTI, Gold","Natgas, Wheat","Semis, Shipping","Gold","TSMC, Semi ETF","Cocoa, Coffee","EM FX","LNG"],
            "Status":           ["Elevated","Elevated","Moderate","Moderate","High","Moderate","Low","Low"],
        })
        st.dataframe(geo_risks, use_container_width=True, hide_index=True)

        # Risk score bar chart
        fig_geo = go.Figure(go.Bar(
            x=geo_risks["Risk Score (0-10)"],
            y=geo_risks["Region"],
            orientation="h",
            marker_color=["#ff1744" if v > 6 else "#ffab00" if v > 4 else "#00ff41"
                          for v in geo_risks["Risk Score (0-10)"]],
        ))
        fig_geo.update_layout(**PLOTLY_BASE, height=280, title="Geopolitical Risk Scores")
        st.plotly_chart(fig_geo, use_container_width=True)

    with geo_tabs[1]:
        st.markdown('<div class="bb-section">SAFE HAVEN ASSETS — LIVE</div>', unsafe_allow_html=True)
        render_section("GEOPOLITICS", EQUITY_TICKERS["GEOPOLITICS"])

    with geo_tabs[2]:
        st.markdown('<div class="bb-section">TRADE FLOW MONITOR (PLACEHOLDER)</div>', unsafe_allow_html=True)
        # TODO: replace with WTO / Census Bureau trade data API
        trade_data = pd.DataFrame({
            "Trade Partner": ["China","EU","Mexico","Canada","Japan","South Korea","UK","India","ASEAN","Brazil"],
            "US Exports ($B)":  [148, 353, 322, 354, 75, 65, 69, 45, 118, 47],
            "US Imports ($B)":  [427, 553, 475, 420, 148, 115, 68, 87, 255, 41],
            "Trade Balance ($B)": [-279, -200, -153, -66, -73, -50, 1, -42, -137, 6],
            "Tariff Rate %":    [19.3, 3.2, 18.5, 3.4, 3.1, 3.5, 3.2, 4.8, 4.5, 3.0],
        })
        st.dataframe(trade_data.style.format({"US Exports ($B)":"${:.0f}","US Imports ($B)":"${:.0f}",
                                               "Trade Balance ($B)":"${:+.0f}","Tariff Rate %":"{:.1f}%"})
                     .background_gradient(subset=["Trade Balance ($B)"], cmap="RdYlGn"),
                     use_container_width=True, hide_index=True)

    with geo_tabs[3]:
        for h, a, tags in get_placeholder_news("GEOPOLITICS"):
            tags_html = "".join(f'<span class="news-tag">{t}</span>' for t in tags)
            st.markdown(f'<div class="news-card"><div class="news-headline">{h}</div><div class="news-meta">{tags_html} {a} ago</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CHAT ASSISTANT — bottom panel (always visible)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div style="border-top:1px solid #1a1a1a;margin-top:1.5rem;"></div>', unsafe_allow_html=True)
with st.expander("▸  MARKET TERMINAL CHAT ASSISTANT", expanded=False):
    st.markdown('<div class="bb-section">ASK ABOUT THE DATA — NO API KEY NEEDED</div>', unsafe_allow_html=True)

    # Display history
    for msg in st.session_state.chat_history[-10:]:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-msg-user"><span style="color:#576070;font-size:0.58rem;">YOU ▸ </span>{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-msg-ai"><span style="color:#333333;font-size:0.58rem;">TERMINAL ▸ </span>{msg["content"]}</div>', unsafe_allow_html=True)

    with st.form("chat_form", clear_on_submit=True):
        chat_col, btn_col = st.columns([6, 1])
        with chat_col:
            user_q = st.text_input("QUERY", placeholder="e.g. What is the Fed funds rate? What is the 10Y yield?", label_visibility="collapsed")
        with btn_col:
            submitted = st.form_submit_button("SEND ▸")

    def chat_answer(q: str) -> str:
        q = q.lower()
        if any(w in q for w in ["fed","federal reserve","fomc","rate","funds rate"]):
            return "Fed Funds Rate: 4.25–4.50%. Next FOMC: May 6-7, 2025. Market pricing ~32% probability of cut at May meeting, 51% at June meeting."
        if any(w in q for w in ["cpi","inflation","consumer price"]):
            return "CPI YoY: +2.8% (Feb 2025). Core CPI: +3.1%. Core PCE (Fed preferred): +2.8%. Shelter remains the largest contributor at 5.8% YoY."
        if any(w in q for w in ["10y","10 year","treasury yield","bond yield"]):
            return "10Y Treasury yield: 4.21%. 2Y: 3.95%. 2s10s spread: +26bps (no longer inverted as of late 2024). 30Y: 4.52%."
        if any(w in q for w in ["gdp","growth","economy"]):
            return "US Q4 2024 GDP: +2.3% QoQ annualized (revised). Q3 2024: +2.8%. US economy continues to outperform G10 peers."
        if any(w in q for w in ["jobs","unemployment","nfp","payroll"]):
            return "Feb 2025 NFP: +155K. Unemployment rate: 4.1%. Labor participation: 62.4%. JOLTS job openings: 7.3M."
        if any(w in q for w in ["gold","xau"]):
            return "Gold (XAU/USD): ~$2,947/oz. Year-to-date: +12.4%. Key drivers: central bank buying, geopolitical risk, real rate decline expectations."
        if any(w in q for w in ["oil","crude","wti","brent"]):
            return "WTI Crude: ~$78.14/bbl. Brent: ~$82.00/bbl. OPEC+ maintaining production cuts through Q2 2025. Geopolitical risk premium elevated."
        if any(w in q for w in ["bitcoin","btc","crypto"]):
            return "Bitcoin: ~$88,420. ETF flows remain strong. Spot BTC ETFs AUM >$95B. Next halving cycle effects fully priced in per analysts."
        if any(w in q for w in ["vix","volatility"]):
            return "VIX: 18.24. MOVE Index (bond vol): 98. Equity vol is moderate; rates vol elevated vs historical. No major event risk priced near-term."
        if any(w in q for w in ["dollar","dxy","usd"]):
            return "DXY (Dollar Index): 103.82. USD strength driven by US growth outperformance and delayed Fed cuts. EUR/USD: 1.082. USD/JPY: 149.3."
        if any(w in q for w in ["s&p","spx","spy","equity","stock market"]):
            return "S&P 500: ~5,614 (+12.8% YTD). Forward P/E: 21.3x. Earnings season Q4: 78% beat rate. Tech and AI remain key drivers. Concentration risk elevated (Mag 7 = 32% of index)."
        return (
            "Available data: Fed Funds Rate, CPI/inflation, GDP, Jobs/NFP, 10Y yields, "
            "Gold, WTI Oil, Bitcoin, VIX, Dollar Index, S&P 500. "
            "Try asking: 'What is the CPI?' or 'What is the Fed rate?' or 'Tell me about gold.'"
        )

    if submitted and user_q.strip():
        answer = chat_answer(user_q)
        st.session_state.chat_history.append({"role": "user", "content": user_q})
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

    chat_c1, chat_c2, _ = st.columns([1, 1, 4])
    with chat_c1:
        if st.button("CLEAR CHAT", key="chat_clear"):
            st.session_state.chat_history = []
            st.rerun()
    with chat_c2:
        quick_questions = ["Fed rate?","CPI now?","10Y yield?","Gold price?","S&P outlook?"]
        qq = st.selectbox("QUICK QUERY", ["—"] + quick_questions, key="qq", label_visibility="collapsed")
        if qq != "—":
            answer = chat_answer(qq)
            st.session_state.chat_history.append({"role": "user", "content": qq})
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.rerun()

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="border-top:1px solid #111;margin-top:1rem;padding:0.4rem 0.5rem;display:flex;justify-content:space-between;font-size:0.55rem;color:#333333;letter-spacing:0.08em;">
  <span>▸ THE MARKET TERMINAL · FOR EDUCATIONAL USE ONLY</span>
  <span>DATA: YFINANCE (15-MIN DELAY) · MACRO: PLACEHOLDER (FRED-READY)</span>
  <span>NOT FINANCIAL ADVICE</span>
</div>
""", unsafe_allow_html=True)
