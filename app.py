"""
PROJECT DASHBOARD — Bloomberg-lite personal dashboard
Single-file Streamlit app. Replace placeholder data with your own later.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import datetime
import io
import random

# ── Optional imports (graceful fallback if not installed) ─────────────────────
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG — must be first Streamlit call
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="PROJECT · Dashboard",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS — dark Bloomberg-lite theme
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

/* ── Root variables ── */
:root {
  --bg:        #0a0c10;
  --surface:   #111318;
  --surface2:  #181b22;
  --border:    #22262f;
  --accent:    #f0b429;
  --accent2:   #3ecf8e;
  --accent3:   #e05252;
  --text:      #d4d8e1;
  --text-dim:  #6b7385;
  --mono:      'IBM Plex Mono', monospace;
  --sans:      'IBM Plex Sans', sans-serif;
}

/* ── Base ── */
html, body, [class*="css"] {
  font-family: var(--sans);
  background-color: var(--bg);
  color: var(--text);
}
.stApp { background: var(--bg); }

/* ── Hide Streamlit branding ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 3rem; max-width: 1400px; }

/* ── Top header bar ── */
.dash-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.75rem 0 1.25rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 1.5rem;
}
.dash-logo {
  font-family: var(--mono);
  font-size: 1.1rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  color: var(--accent);
}
.dash-time {
  font-family: var(--mono);
  font-size: 0.78rem;
  color: var(--text-dim);
  letter-spacing: 0.05em;
}
.dash-status {
  display: inline-flex; align-items: center; gap: 0.4rem;
  font-family: var(--mono); font-size: 0.72rem;
  color: var(--accent2); letter-spacing: 0.06em;
}
.status-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--accent2);
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%,100% { opacity:1; } 50% { opacity:0.3; }
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface);
  border-radius: 4px 4px 0 0;
  border: 1px solid var(--border);
  border-bottom: none;
  gap: 0;
  padding: 0;
}
.stTabs [data-baseweb="tab"] {
  font-family: var(--mono);
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.08em;
  color: var(--text-dim);
  padding: 0.65rem 1.3rem;
  border-right: 1px solid var(--border);
  border-radius: 0;
  background: transparent;
  text-transform: uppercase;
}
.stTabs [aria-selected="true"] {
  background: var(--bg) !important;
  color: var(--accent) !important;
  border-top: 2px solid var(--accent) !important;
  margin-top: -1px;
}
.stTabs [data-baseweb="tab-panel"] {
  background: var(--bg);
  border: 1px solid var(--border);
  border-top: none;
  padding: 1.5rem;
  border-radius: 0 0 4px 4px;
}

/* ── Metric cards ── */
.metric-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1rem 1.2rem;
  position: relative;
  overflow: hidden;
}
.metric-card::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: var(--accent);
}
.metric-card.green::before { background: var(--accent2); }
.metric-card.red::before   { background: var(--accent3); }
.metric-label {
  font-family: var(--mono);
  font-size: 0.65rem;
  letter-spacing: 0.1em;
  color: var(--text-dim);
  text-transform: uppercase;
  margin-bottom: 0.4rem;
}
.metric-value {
  font-family: var(--mono);
  font-size: 1.55rem;
  font-weight: 600;
  color: var(--text);
  line-height: 1.1;
}
.metric-delta {
  font-family: var(--mono);
  font-size: 0.72rem;
  margin-top: 0.3rem;
}
.metric-delta.up   { color: var(--accent2); }
.metric-delta.down { color: var(--accent3); }
.metric-delta.neutral { color: var(--text-dim); }

/* ── Section headers ── */
.section-label {
  font-family: var(--mono);
  font-size: 0.65rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--text-dim);
  border-left: 2px solid var(--accent);
  padding-left: 0.6rem;
  margin: 1.5rem 0 0.8rem;
}

/* ── Tables ── */
.stDataFrame { border: 1px solid var(--border) !important; }
.stDataFrame [data-testid="stDataFrameResizable"] { background: var(--surface) !important; }

/* ── Buttons ── */
.stButton > button {
  font-family: var(--mono);
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  background: transparent;
  color: var(--accent);
  border: 1px solid var(--accent);
  border-radius: 2px;
  padding: 0.5rem 1.2rem;
  transition: all 0.15s ease;
}
.stButton > button:hover {
  background: var(--accent);
  color: var(--bg);
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
  border: 1px dashed var(--border) !important;
  background: var(--surface) !important;
  border-radius: 4px;
}

/* ── Chat ── */
.chat-bubble-user {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 4px 4px 4px 0;
  padding: 0.75rem 1rem;
  margin: 0.5rem 3rem 0.5rem 0;
  font-size: 0.88rem;
}
.chat-bubble-ai {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 2px solid var(--accent);
  border-radius: 4px 4px 0 4px;
  padding: 0.75rem 1rem;
  margin: 0.5rem 0 0.5rem 3rem;
  font-size: 0.88rem;
  font-family: var(--mono);
}
.chat-label {
  font-family: var(--mono);
  font-size: 0.6rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-dim);
  margin-bottom: 0.25rem;
}

/* ── Ticker tape ── */
.ticker-wrap {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 0.5rem 1rem;
  font-family: var(--mono);
  font-size: 0.75rem;
  color: var(--text-dim);
  margin-bottom: 1rem;
  overflow: hidden;
  white-space: nowrap;
}

/* ── Selectbox / inputs ── */
.stSelectbox > div, .stTextInput > div { font-family: var(--mono) !important; font-size: 0.82rem !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE — persists across tab switches
# ══════════════════════════════════════════════════════════════════════════════
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "uploaded_text" not in st.session_state:
    st.session_state.uploaded_text = ""
if "custom_df" not in st.session_state:
    st.session_state.custom_df = None

# ══════════════════════════════════════════════════════════════════════════════
# HELPER — placeholder data generators
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def get_placeholder_timeseries():
    dates = pd.date_range(end=datetime.date.today(), periods=180, freq="D")
    base = 100
    vals = [base]
    for _ in range(179):
        vals.append(round(vals[-1] * (1 + random.gauss(0.0005, 0.012)), 2))
    df = pd.DataFrame({"Date": dates, "Value": vals})
    df["MA30"] = df["Value"].rolling(30).mean()
    return df

@st.cache_data(ttl=300)
def get_placeholder_table():
    categories = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon",
                  "Zeta", "Eta", "Theta", "Iota", "Kappa"]
    rows = []
    for c in categories:
        rev  = round(random.uniform(50_000, 500_000), 0)
        cost = round(rev * random.uniform(0.4, 0.8), 0)
        rows.append({
            "Name":     c,
            "Revenue":  rev,
            "Cost":     cost,
            "Profit":   round(rev - cost, 0),
            "Margin %": round((rev - cost) / rev * 100, 1),
            "Units":    random.randint(100, 5000),
            "Status":   random.choice(["Active", "Active", "Active", "Paused", "Review"]),
        })
    return pd.DataFrame(rows)

@st.cache_data(ttl=300)
def get_heatmap_data():
    months = ["Jan","Feb","Mar","Apr","May","Jun",
              "Jul","Aug","Sep","Oct","Nov","Dec"]
    cats   = ["Revenue","Cost","Profit","Units","Margin"]
    data   = [[round(random.uniform(-20, 40), 1) for _ in months] for _ in cats]
    return pd.DataFrame(data, index=cats, columns=months)

# ══════════════════════════════════════════════════════════════════════════════
# PLOTLY theme helper
# ══════════════════════════════════════════════════════════════════════════════
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor ="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Mono", color="#d4d8e1", size=11),
    xaxis=dict(gridcolor="#22262f", linecolor="#22262f", zerolinecolor="#22262f"),
    yaxis=dict(gridcolor="#22262f", linecolor="#22262f", zerolinecolor="#22262f"),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#22262f"),
    margin=dict(l=10, r=10, t=40, b=10),
)

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
now_str = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
st.markdown(f"""
<div class="dash-header">
  <div class="dash-logo">◈ PROJECT</div>
  <div class="dash-time">{now_str}</div>
  <div class="dash-status"><span class="status-dot"></span>LIVE</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "01 · Dashboard",
    "02 · Data Viewer",
    "03 · Charts",
    "04 · Analysis",
    "05 · Updater",
    "06 · Chat",
])

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  TAB 1 — DASHBOARD                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝
with tab1:
    df_ts  = get_placeholder_timeseries()
    df_tbl = get_placeholder_table()

    # ── Metric row ──────────────────────────────────────────────────────────
    total_rev  = df_tbl["Revenue"].sum()
    total_pnl  = df_tbl["Profit"].sum()
    avg_margin = df_tbl["Margin %"].mean()
    active_ct  = (df_tbl["Status"] == "Active").sum()

    c1, c2, c3, c4, c5 = st.columns(5)
    metrics = [
        (c1, "Total Revenue",  f"${total_rev:,.0f}",   "+12.4%", "up",      ""),
        (c2, "Total Profit",   f"${total_pnl:,.0f}",   "+8.7%",  "up",      "green"),
        (c3, "Avg Margin",     f"{avg_margin:.1f}%",   "−1.2pp", "down",    "red"),
        (c4, "Active Items",   str(active_ct),          "Steady", "neutral", ""),
        (c5, "Days Tracked",   "180",                   "6 mo",   "neutral", ""),
    ]
    for col, label, val, delta, direction, card_class in metrics:
        with col:
            st.markdown(f"""
            <div class="metric-card {card_class}">
              <div class="metric-label">{label}</div>
              <div class="metric-value">{val}</div>
              <div class="metric-delta {direction}">{delta}</div>
            </div>""", unsafe_allow_html=True)

    # ── Main chart ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Performance Overview</div>', unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_ts["Date"], y=df_ts["Value"],
        mode="lines", name="Value",
        line=dict(color="#f0b429", width=1.5),
        fill="tozeroy", fillcolor="rgba(240,180,41,0.06)"
    ))
    fig.add_trace(go.Scatter(
        x=df_ts["Date"], y=df_ts["MA30"],
        mode="lines", name="30d MA",
        line=dict(color="#3ecf8e", width=1, dash="dot")
    ))
    fig.update_layout(**PLOTLY_LAYOUT, height=280)
    st.plotly_chart(fig, use_container_width=True)

    # ── Bottom row ──────────────────────────────────────────────────────────
    col_a, col_b = st.columns([3, 2])
    with col_a:
        st.markdown('<div class="section-label">Top 5 by Revenue</div>', unsafe_allow_html=True)
        top5 = df_tbl.nlargest(5, "Revenue")[["Name","Revenue","Margin %","Status"]]
        st.dataframe(top5, use_container_width=True, hide_index=True)
    with col_b:
        st.markdown('<div class="section-label">Status Breakdown</div>', unsafe_allow_html=True)
        status_counts = df_tbl["Status"].value_counts().reset_index()
        status_counts.columns = ["Status","Count"]
        fig2 = px.pie(status_counts, names="Status", values="Count",
                      color_discrete_sequence=["#f0b429","#3ecf8e","#e05252","#4a9eff"])
        fig2.update_traces(textfont_family="IBM Plex Mono")
        fig2.update_layout(**PLOTLY_LAYOUT, height=220, showlegend=True)
        st.plotly_chart(fig2, use_container_width=True)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  TAB 2 — DATA VIEWER                                                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝
with tab2:
    df_tbl = get_placeholder_table()

    st.markdown('<div class="section-label">Filter & Search</div>', unsafe_allow_html=True)
    col_f1, col_f2, col_f3 = st.columns([2,2,1])
    with col_f1:
        status_filter = st.multiselect(
            "Status", options=df_tbl["Status"].unique().tolist(),
            default=df_tbl["Status"].unique().tolist()
        )
    with col_f2:
        sort_col = st.selectbox("Sort by", ["Revenue","Profit","Margin %","Units"])
    with col_f3:
        sort_asc = st.selectbox("Order", ["Descending","Ascending"]) == "Ascending"

    filtered = df_tbl[df_tbl["Status"].isin(status_filter)].sort_values(sort_col, ascending=sort_asc)

    st.markdown('<div class="section-label">Data Table</div>', unsafe_allow_html=True)
    st.dataframe(
        filtered.style.format({
            "Revenue": "${:,.0f}", "Cost": "${:,.0f}",
            "Profit": "${:,.0f}", "Margin %": "{:.1f}%"
        }).background_gradient(subset=["Margin %"], cmap="RdYlGn"),
        use_container_width=True, hide_index=True, height=400
    )

    st.markdown('<div class="section-label">Summary Statistics</div>', unsafe_allow_html=True)
    st.dataframe(filtered[["Revenue","Cost","Profit","Margin %","Units"]].describe().round(1),
                 use_container_width=True)

    if st.session_state.custom_df is not None:
        st.markdown('<div class="section-label">Uploaded Data</div>', unsafe_allow_html=True)
        st.dataframe(st.session_state.custom_df, use_container_width=True, hide_index=True)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  TAB 3 — CHARTS                                                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝
with tab3:
    df_ts  = get_placeholder_timeseries()
    df_tbl = get_placeholder_table()

    st.markdown('<div class="section-label">Chart Type</div>', unsafe_allow_html=True)
    chart_type = st.radio("", ["Line / Area","Bar","Candlestick (OHLC)","Scatter","Multi-panel"],
                          horizontal=True)

    if chart_type == "Line / Area":
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_ts["Date"], y=df_ts["Value"], mode="lines", name="Series A",
            line=dict(color="#f0b429", width=2),
            fill="tozeroy", fillcolor="rgba(240,180,41,0.07)"
        ))
        fig.add_trace(go.Scatter(
            x=df_ts["Date"], y=df_ts["MA30"], mode="lines", name="30d MA",
            line=dict(color="#3ecf8e", width=1.2, dash="dot")
        ))
        fig.update_layout(**PLOTLY_LAYOUT, height=420, title="Time Series — 180 Days")

    elif chart_type == "Bar":
        fig = px.bar(df_tbl, x="Name", y="Revenue", color="Margin %",
                     color_continuous_scale=["#e05252","#f0b429","#3ecf8e"])
        fig.update_layout(**PLOTLY_LAYOUT, height=420, title="Revenue by Category")

    elif chart_type == "Candlestick (OHLC)":
        dates = df_ts["Date"]
        closes = df_ts["Value"]
        opens  = closes.shift(1).fillna(closes)
        highs  = closes * pd.Series([1 + abs(random.gauss(0, 0.008)) for _ in range(len(closes))])
        lows   = closes * pd.Series([1 - abs(random.gauss(0, 0.008)) for _ in range(len(closes))])
        fig = go.Figure(go.Candlestick(
            x=dates, open=opens, high=highs, low=lows, close=closes,
            increasing_line_color="#3ecf8e", decreasing_line_color="#e05252"
        ))
        fig.update_layout(**PLOTLY_LAYOUT, height=420, title="OHLC Candlestick", xaxis_rangeslider_visible=False)

    elif chart_type == "Scatter":
        fig = px.scatter(df_tbl, x="Revenue", y="Margin %", size="Units",
                         color="Status", text="Name",
                         color_discrete_sequence=["#f0b429","#3ecf8e","#e05252","#4a9eff"])
        fig.update_traces(textposition="top center", textfont=dict(size=9))
        fig.update_layout(**PLOTLY_LAYOUT, height=420, title="Revenue vs Margin (bubble = Units)")

    else:  # Multi-panel
        fig = make_subplots(rows=2, cols=2,
                            subplot_titles=("Revenue","Profit","Margin %","Units"),
                            vertical_spacing=0.12)
        colors = ["#f0b429","#3ecf8e","#4a9eff","#e05252"]
        cols_list = ["Revenue","Profit","Margin %","Units"]
        positions = [(1,1),(1,2),(2,1),(2,2)]
        for i, (col_name, pos, color) in enumerate(zip(cols_list, positions, colors)):
            fig.add_trace(go.Bar(x=df_tbl["Name"], y=df_tbl[col_name],
                                 marker_color=color, name=col_name,
                                 showlegend=False), row=pos[0], col=pos[1])
        fig.update_layout(**PLOTLY_LAYOUT, height=480, title="Multi-panel Overview")
        for i in range(1,5):
            r, c = positions[i-1]
            fig.update_xaxes(gridcolor="#22262f", row=r, col=c)
            fig.update_yaxes(gridcolor="#22262f", row=r, col=c)

    st.plotly_chart(fig, use_container_width=True)

    # Live price ticker (optional)
    if HAS_YFINANCE:
        st.markdown('<div class="section-label">Live Market Prices</div>', unsafe_allow_html=True)
        tickers_input = st.text_input("Tickers (comma-separated)", value="AAPL, MSFT, GOOGL, BTC-USD")
        if st.button("◈ Fetch Prices"):
            tickers = [t.strip() for t in tickers_input.split(",") if t.strip()]
            price_rows = []
            with st.spinner("Fetching…"):
                for t in tickers:
                    try:
                        info = yf.Ticker(t).fast_info
                        price_rows.append({"Ticker": t,
                                           "Price": round(info.last_price, 2),
                                           "52w High": round(info.year_high, 2),
                                           "52w Low":  round(info.year_low,  2)})
                    except Exception:
                        price_rows.append({"Ticker": t, "Price": "N/A",
                                           "52w High": "N/A", "52w Low": "N/A"})
            st.dataframe(pd.DataFrame(price_rows), use_container_width=True, hide_index=True)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  TAB 4 — ANALYSIS                                                        ║
# ╚══════════════════════════════════════════════════════════════════════════╝
with tab4:
    df_tbl = get_placeholder_table()
    hm_df  = get_heatmap_data()

    # ── Heatmap ─────────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Month-over-Month Heatmap (% change)</div>', unsafe_allow_html=True)
    fig_hm = px.imshow(
        hm_df, text_auto=True,
        color_continuous_scale=["#e05252","#1a1d24","#3ecf8e"],
        zmin=-20, zmax=40, aspect="auto"
    )
    fig_hm.update_traces(textfont=dict(family="IBM Plex Mono", size=10))
    fig_hm.update_layout(**PLOTLY_LAYOUT, height=280, coloraxis_showscale=True)
    st.plotly_chart(fig_hm, use_container_width=True)

    # ── Profitability table ──────────────────────────────────────────────────
    st.markdown('<div class="section-label">Profitability Ranking</div>', unsafe_allow_html=True)
    ranked = df_tbl.sort_values("Margin %", ascending=False).reset_index(drop=True)
    ranked.index = ranked.index + 1
    ranked["Rank"] = ranked.index
    ranked = ranked[["Rank","Name","Revenue","Profit","Margin %","Status"]]

    def color_margin(val):
        if isinstance(val, float):
            color = "#3ecf8e" if val > 35 else ("#f0b429" if val > 20 else "#e05252")
            return f"color: {color}; font-weight: 600"
        return ""

    styled = ranked.style \
        .format({"Revenue": "${:,.0f}", "Profit": "${:,.0f}", "Margin %": "{:.1f}%"}) \
        .applymap(color_margin, subset=["Margin %"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # ── Waterfall ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">Revenue → Profit Waterfall</div>', unsafe_allow_html=True)
    total_rev  = df_tbl["Revenue"].sum()
    total_cost = df_tbl["Cost"].sum()
    total_pnl  = df_tbl["Profit"].sum()
    fig_wf = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute","relative","total"],
        x=["Revenue","Costs","Net Profit"],
        y=[total_rev, -total_cost, 0],
        connector=dict(line=dict(color="#22262f")),
        increasing=dict(marker_color="#3ecf8e"),
        decreasing=dict(marker_color="#e05252"),
        totals=dict(marker_color="#f0b429"),
        text=[f"${total_rev:,.0f}", f"−${total_cost:,.0f}", f"${total_pnl:,.0f}"],
        textposition="outside",
        textfont=dict(family="IBM Plex Mono", size=10)
    ))
    fig_wf.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False)
    st.plotly_chart(fig_wf, use_container_width=True)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  TAB 5 — UPDATER                                                         ║
# ╚══════════════════════════════════════════════════════════════════════════╝
with tab5:
    st.markdown('<div class="section-label">Upload Files</div>', unsafe_allow_html=True)
    st.caption("Drag and drop PDF or Excel files. The dashboard will update automatically.")

    col_u1, col_u2 = st.columns(2)

    with col_u1:
        st.markdown("**📄 PDF Upload**")
        pdf_file = st.file_uploader("Drop a PDF here", type=["pdf"], key="pdf_up")
        if pdf_file is not None:
            if HAS_PYPDF2:
                try:
                    reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
                    text_parts = []
                    for page in reader.pages:
                        text_parts.append(page.extract_text() or "")
                    full_text = "\n".join(text_parts)
                    st.session_state.uploaded_text = full_text
                    st.success(f"✓ Extracted {len(reader.pages)} pages, {len(full_text):,} characters")
                    with st.expander("Preview extracted text"):
                        st.text(full_text[:2000] + ("…" if len(full_text) > 2000 else ""))
                except Exception as e:
                    st.error(f"Error reading PDF: {e}")
            else:
                st.warning("PyPDF2 not installed. Add it to requirements.txt.")

    with col_u2:
        st.markdown("**📊 Excel / CSV Upload**")
        xl_file = st.file_uploader("Drop an Excel or CSV here", type=["xlsx","xls","csv"], key="xl_up")
        if xl_file is not None:
            try:
                if xl_file.name.endswith(".csv"):
                    df_up = pd.read_csv(xl_file)
                else:
                    df_up = pd.read_excel(xl_file)
                st.session_state.custom_df = df_up
                st.success(f"✓ Loaded {len(df_up):,} rows × {len(df_up.columns)} columns")
                st.dataframe(df_up.head(20), use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Error reading file: {e}")

    st.markdown('<div class="section-label">API Refresh</div>', unsafe_allow_html=True)
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        if st.button("◈ Refresh All Data"):
            st.cache_data.clear()
            st.success("Cache cleared — data will regenerate on next view.")
    with col_b2:
        if st.button("◈ Export to CSV"):
            df_tbl_exp = get_placeholder_table()
            csv_bytes = df_tbl_exp.to_csv(index=False).encode()
            st.download_button("⬇ Download CSV", csv_bytes, "project_data.csv", "text/csv")
    with col_b3:
        if st.button("◈ Reset Uploads"):
            st.session_state.custom_df   = None
            st.session_state.uploaded_text = ""
            st.success("Uploads cleared.")

    st.markdown('<div class="section-label">System Status</div>', unsafe_allow_html=True)
    status_items = {
        "yfinance":  ("✓ Installed" if HAS_YFINANCE  else "✗ Not found"),
        "PyPDF2":    ("✓ Installed" if HAS_PYPDF2    else "✗ Not found"),
        "pandas":    "✓ Installed",
        "plotly":    "✓ Installed",
        "streamlit": "✓ Installed",
    }
    cols = st.columns(len(status_items))
    for col, (lib, status) in zip(cols, status_items.items()):
        color = "#3ecf8e" if status.startswith("✓") else "#e05252"
        col.markdown(f"""
        <div style="background:#111318;border:1px solid #22262f;border-radius:4px;
                    padding:.6rem .8rem;text-align:center;">
          <div style="font-family:'IBM Plex Mono';font-size:.6rem;color:#6b7385;
                      letter-spacing:.1em;text-transform:uppercase;">{lib}</div>
          <div style="font-family:'IBM Plex Mono';font-size:.75rem;color:{color};
                      margin-top:.25rem;">{status}</div>
        </div>""", unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  TAB 6 — CHAT ASSISTANT                                                  ║
# ╚══════════════════════════════════════════════════════════════════════════╝
with tab6:
    df_tbl = get_placeholder_table()

    st.markdown('<div class="section-label">Ask About Your Data</div>', unsafe_allow_html=True)
    st.caption("No API key needed — answers are computed directly from the loaded data.")

    # ── Display history ──────────────────────────────────────────────────────
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-label">YOU</div>
            <div class="chat-bubble-user">{msg["content"]}</div>""",
            unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-label">ASSISTANT</div>
            <div class="chat-bubble-ai">{msg["content"]}</div>""",
            unsafe_allow_html=True)

    # ── Input ────────────────────────────────────────────────────────────────
    with st.form("chat_form", clear_on_submit=True):
        user_q = st.text_input("Your question…", placeholder="e.g. What is the highest margin item?")
        submitted = st.form_submit_button("◈ Send")

    def answer_question(q: str, df: pd.DataFrame, pdf_text: str) -> str:
        q_lower = q.lower()

        if any(w in q_lower for w in ["highest margin","best margin","top margin"]):
            row = df.nlargest(1, "Margin %").iloc[0]
            return f"{row['Name']} has the highest margin at {row['Margin %']:.1f}% (Revenue: ${row['Revenue']:,.0f})"

        if any(w in q_lower for w in ["lowest margin","worst margin"]):
            row = df.nsmallest(1, "Margin %").iloc[0]
            return f"{row['Name']} has the lowest margin at {row['Margin %']:.1f}%"

        if any(w in q_lower for w in ["total revenue","sum revenue"]):
            return f"Total revenue across all items: ${df['Revenue'].sum():,.0f}"

        if any(w in q_lower for w in ["total profit","net profit"]):
            return f"Total profit: ${df['Profit'].sum():,.0f}"

        if any(w in q_lower for w in ["average margin","avg margin","mean margin"]):
            return f"Average margin: {df['Margin %'].mean():.1f}%"

        if any(w in q_lower for w in ["how many","count","number of"]):
            return (f"There are {len(df)} items total — "
                    f"{(df['Status']=='Active').sum()} Active, "
                    f"{(df['Status']=='Paused').sum()} Paused, "
                    f"{(df['Status']=='Review').sum()} under Review.")

        if any(w in q_lower for w in ["top 3","top three","best 3"]):
            top3 = df.nlargest(3, "Revenue")
            lines = [f"  {i+1}. {r['Name']} — ${r['Revenue']:,.0f} (margin {r['Margin %']:.1f}%)"
                     for i, (_, r) in enumerate(top3.iterrows())]
            return "Top 3 by Revenue:\n" + "\n".join(lines)

        if any(w in q_lower for w in ["paused","inactive"]):
            paused = df[df["Status"]=="Paused"]["Name"].tolist()
            return f"Paused items: {', '.join(paused) if paused else 'None'}"

        if pdf_text and any(w in q_lower for w in ["pdf","document","uploaded"]):
            snippet = pdf_text[:500].replace("\n"," ")
            return f"Uploaded document preview:\n{snippet}..."

        # Fallback: show quick stats
        return (f"I can answer questions about the data. Quick summary:\n"
                f"  • {len(df)} items loaded\n"
                f"  • Total revenue: ${df['Revenue'].sum():,.0f}\n"
                f"  • Avg margin: {df['Margin %'].mean():.1f}%\n"
                f"  • Best performer: {df.nlargest(1,'Margin %').iloc[0]['Name']}\n\n"
                f"Try asking: 'highest margin', 'total revenue', 'top 3', 'how many items'.")

    if submitted and user_q.strip():
        answer = answer_question(user_q, df_tbl, st.session_state.uploaded_text)
        st.session_state.chat_history.append({"role": "user",    "content": user_q})
        st.session_state.chat_history.append({"role": "assistant","content": answer})
        st.rerun()

    col_cl, _ = st.columns([1, 4])
    with col_cl:
        if st.button("◈ Clear Chat") and st.session_state.chat_history:
            st.session_state.chat_history = []
            st.rerun()

    st.markdown('<div class="section-label">Suggested Questions</div>', unsafe_allow_html=True)
    suggestions = [
        "What is the highest margin item?",
        "What is the total revenue?",
        "Show me the top 3 by revenue",
        "How many items are active?",
        "What is the average margin?",
    ]
    cols_s = st.columns(len(suggestions))
    for col, sug in zip(cols_s, suggestions):
        with col:
            if st.button(sug, key=f"sug_{hash(sug) % 1000000}"):
                answer = answer_question(sug, df_tbl, st.session_state.uploaded_text)
                st.session_state.chat_history.append({"role": "user",    "content": sug})
                st.session_state.chat_history.append({"role": "assistant","content": answer})
                st.rerun()

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:3rem;padding-top:1rem;border-top:1px solid #22262f;
            font-family:'IBM Plex Mono';font-size:0.6rem;color:#6b7385;
            display:flex;justify-content:space-between;">
  <span>◈ PROJECT DASHBOARD</span>
  <span>BUILT WITH STREAMLIT + PLOTLY</span>
  <span>CUSTOMISE FOR ANY USE CASE</span>
</div>
""", unsafe_allow_html=True)
