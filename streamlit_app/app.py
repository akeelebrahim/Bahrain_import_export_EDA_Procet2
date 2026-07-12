"""
Bahrain Non-Oil Foreign Trade — Interactive Dashboard
Aqeel Ebrahim · Data Science DSB-1

Run:  streamlit run streamlit_app/app.py
Reads the compact cleaned aggregates in ../data/cleaned/
"""
from pathlib import Path
import pandas as pd
import plotly.express as px  # noqa: F401  (used across tabs)
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------- config
st.set_page_config(page_title="Bahrain Non-Oil Trade", page_icon="📊", layout="wide")

C_IMPORT, C_EXPORT, C_POS, C_NEG = "#4C72B0", "#DD8452", "#55A868", "#C44E52"
DATA = Path(__file__).resolve().parent.parent / "data" / "cleaned"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


@st.cache_data
def load():
    annual = pd.read_csv(DATA / "annual_trade_clean.csv")
    country = pd.read_csv(DATA / "dash_country_year.csv")
    commodity = pd.read_csv(DATA / "dash_commodity_year.csv")
    month = pd.read_csv(DATA / "dash_month_year.csv")
    comp = pd.read_csv(DATA / "dash_export_composition_2024.csv")
    return annual, country, commodity, month, comp


annual, country, commodity, month, comp = load()

# ----------------------------------------------------------------- header
st.title("🇧🇭 Bahrain Non-Oil Foreign Trade")
st.caption("Interactive companion to the EDA project · Aqeel Ebrahim · Data Science DSB-1 · "
           "Source: [data.gov.bh](https://www.data.gov.bh/explore/?refine.theme=Foreign+Trade)")

# ----------------------------------------------------------------- sidebar
st.sidebar.header("Filters")
year = st.sidebar.radio("Year (transaction detail)", [2024, 2023], index=0)
topn = st.sidebar.slider("Top N (partners / commodities)", 5, 20, 10)
st.sidebar.markdown("---")
st.sidebar.info("All values are **non-oil** trade in **million Bahraini Dinar (BD)**.")

# ----------------------------------------------------------------- KPIs
imp = country[(country.flow == "Import") & (country.year == year)]["value_bd"].sum() / 1e6
exp = country[(country.flow == "Export") & (country.year == year)]["value_bd"].sum() / 1e6
bal = exp - imp
k1, k2, k3 = st.columns(3)
k1.metric(f"Non-oil Imports ({year})", f"{imp:,.0f} M BD")
k2.metric(f"Non-oil Exports ({year})", f"{exp:,.0f} M BD")
k3.metric("Non-oil Trade Balance", f"{bal:,.0f} M BD", "Surplus" if bal >= 0 else "Deficit",
          delta_color="normal" if bal >= 0 else "inverse")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Trends", "🌍 Partners", "📦 Commodities", "🗓️ Seasonality"])

# ----------------------------------------------------------------- Trends
with tab1:
    st.subheader("Total trade and balance, 2010–2023 (oil-inclusive)")
    fig = go.Figure()
    fig.add_bar(x=annual["year"], y=annual["Trade Balance"], name="Trade Balance",
                marker_color=[C_POS if v >= 0 else C_NEG for v in annual["Trade Balance"]], opacity=0.4)
    fig.add_scatter(x=annual["year"], y=annual["Total Imports"], name="Total Imports",
                    mode="lines+markers", line=dict(color=C_IMPORT, width=3))
    fig.add_scatter(x=annual["year"], y=annual["Total Exports"], name="Total Exports",
                    mode="lines+markers", line=dict(color=C_EXPORT, width=3))
    fig.update_layout(height=430, yaxis_title="Million BD", legend_orientation="h",
                      margin=dict(t=10, b=10), plot_bgcolor="white")
    st.plotly_chart(fig, width="stretch")
    st.markdown("**Note:** these headline totals include oil. The tabs on the right isolate the "
                "**non-oil** economy, where Bahrain runs a trade **deficit**.")

    st.subheader("2024 export composition")
    cc1, cc2 = st.columns([1, 1])
    with cc1:
        pie = px.pie(comp, names="component", values="value_bd", hole=0.5,
                     color_discrete_sequence=[C_EXPORT, "#E8B87F"])
        pie.update_layout(height=340, margin=dict(t=10, b=10))
        st.plotly_chart(pie, width="stretch")
    with cc2:
        share = comp["value_bd"].iloc[0] / comp["value_bd"].sum() * 100
        st.metric("National-origin share of exports", f"{share:.0f}%")
        st.write("Most exports are genuinely **made in Bahrain** rather than re-exported goods, "
                 "so the export base reflects real domestic production.")

# ----------------------------------------------------------------- Partners
with tab2:
    st.subheader(f"Top {topn} partner countries — {year}")
    c1, c2 = st.columns(2)
    for col, flow, color, label in [(c1, "Import", C_IMPORT, "Import sources"),
                                    (c2, "Export", C_EXPORT, "Export destinations")]:
        d = (country[(country.flow == flow) & (country.year == year)]
             .nlargest(topn, "value_bd").assign(v=lambda x: x["value_bd"] / 1e6))
        fig = px.bar(d.sort_values("v"), x="v", y="country_name", orientation="h",
                     color_discrete_sequence=[color], labels={"v": "Million BD", "country_name": ""})
        fig.update_layout(height=460, margin=dict(t=30, b=10), title=label)
        col.plotly_chart(fig, width="stretch")
    tot_imp = country[(country.flow == "Import") & (country.year == year)]["value_bd"].sum()
    top5 = country[(country.flow == "Export") & (country.year == year)].nlargest(5, "value_bd")["value_bd"].sum()
    tote = country[(country.flow == "Export") & (country.year == year)]["value_bd"].sum()
    st.info(f"The top-5 destinations account for **{top5/tote*100:.0f}%** of non-oil exports — "
            "a concentration risk led by Saudi Arabia and the UAE.")

# ----------------------------------------------------------------- Commodities
with tab3:
    flow_sel = st.radio("Flow", ["Import", "Export"], horizontal=True, key="commflow")
    color = C_IMPORT if flow_sel == "Import" else C_EXPORT
    d = commodity[(commodity.flow == flow_sel) & (commodity.year == year)]
    st.subheader(f"Top {topn} {flow_sel.lower()} commodities — {year}")
    top = d.nlargest(topn, "value_bd").assign(v=lambda x: x["value_bd"] / 1e6)
    top["short"] = top["commodity"].str.slice(0, 40)
    fig = px.bar(top.sort_values("v"), x="v", y="short", orientation="h",
                 color_discrete_sequence=[color], labels={"v": "Million BD", "short": ""})
    fig.update_layout(height=460, margin=dict(t=10, b=10))
    st.plotly_chart(fig, width="stretch")

    st.subheader(f"Product groups (HS chapters) — {flow_sel.lower()}s {year}")
    ch = (d.groupby("hs_chapter", as_index=False)["value_bd"].sum()
          .nlargest(15, "value_bd").assign(v=lambda x: x["value_bd"] / 1e6))
    tm = px.treemap(ch, path=["hs_chapter"], values="v", color="v",
                    color_continuous_scale="Blues" if flow_sel == "Import" else "Oranges")
    tm.update_layout(height=380, margin=dict(t=10, b=10))
    st.plotly_chart(tm, width="stretch")

# ----------------------------------------------------------------- Seasonality
with tab4:
    st.subheader(f"Monthly non-oil trade — {year}")
    mi = month[(month.flow == "Import") & (month.year == year)].set_index("month_num")["value_bd"] / 1e6
    me = month[(month.flow == "Export") & (month.year == year)].set_index("month_num")["value_bd"] / 1e6
    fig = go.Figure()
    fig.add_scatter(x=MONTHS, y=[mi.get(m) for m in range(1, 13)], name="Imports",
                    mode="lines+markers", line=dict(color=C_IMPORT, width=3))
    fig.add_scatter(x=MONTHS, y=[me.get(m) for m in range(1, 13)], name="Exports",
                    mode="lines+markers", line=dict(color=C_EXPORT, width=3))
    fig.update_layout(height=440, yaxis_title="Million BD", legend_orientation="h",
                      margin=dict(t=10, b=10), plot_bgcolor="white")
    st.plotly_chart(fig, width="stretch")
    st.markdown("Non-oil trade is **structurally stable** month to month, with a mild **December peak**.")

st.markdown("---")
st.caption("Data: Kingdom of Bahrain Open Data Portal (Information & eGovernment Authority). "
           "Non-oil trade only. Built with Streamlit + Plotly.")
