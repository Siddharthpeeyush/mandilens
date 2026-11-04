#!/usr/bin/env python3
"""MandiLens interactive dashboard — Day 25 of the 30-day roadmap.

Commodity explorer for the daily mandi-price dataset.

Run locally:
    streamlit run src/dashboard.py

The app needs no API keys and no network: it reads the flat CSVs the daily
pipeline already produces (data/processed/mandi_prices_clean.csv and the
latest data/processed/forecast_table_*.csv).
"""
import glob
import os

import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_CSV = os.path.join(BASE_DIR, "data", "processed", "mandi_prices_clean.csv")
FORECAST_GLOB = os.path.join(BASE_DIR, "data", "processed", "forecast_table_*.csv")

PRIORITY_COMMODITIES = ["Onion", "Potato", "Tomato"]


@st.cache_data
def load_prices():
    df = pd.read_csv(CLEAN_CSV, parse_dates=["arrival_date"])
    df["modal_price"] = pd.to_numeric(df["modal_price"], errors="coerce")
    df = df.dropna(subset=["modal_price"])
    return df


@st.cache_data
def load_forecasts():
    paths = sorted(glob.glob(FORECAST_GLOB))
    if not paths:
        return pd.DataFrame()
    df = pd.read_csv(paths[-1], parse_dates=["forecast_date"])
    df["forecast_price"] = pd.to_numeric(df["forecast_price"], errors="coerce")
    return df


def main():
    st.set_page_config(page_title="MandiLens", page_icon="🧅", layout="wide")
    st.title("MandiLens — commodity price explorer")

    prices = load_prices()
    forecasts = load_forecasts()

    latest_date = prices["arrival_date"].max().date()
    portal_days = prices[prices["source_file"].str.contains("2026-11-0", na=False)]
    data_mode = "PORTAL (Agmarknet)" if not portal_days.empty else "sample data"

    st.caption(
        f"{len(prices):,} daily quotes · {prices['market'].nunique()} markets · "
        f"{prices['commodity'].nunique()} commodities · latest {latest_date} · "
        f"source: {data_mode}"
    )

    commodities = sorted(prices["commodity"].dropna().unique())
    ordered = PRIORITY_COMMODITIES + [c for c in commodities if c not in PRIORITY_COMMODITIES]
    commodity = st.sidebar.selectbox("Commodity", ordered)

    markets = sorted(prices.loc[prices["commodity"] == commodity, "market"].unique())
    market = st.sidebar.selectbox("Market", markets)

    series = prices[
        (prices["commodity"] == commodity) & (prices["market"] == market)
    ].sort_values("arrival_date")

    if series.empty:
        st.warning("No data for this market/commodity pair.")
        return

    latest = series.iloc[-1]
    st.metric(
        f"{commodity} in {market} — latest modal price",
        f"Rs {latest['modal_price']:,.0f}/qtl",
        f"{latest['arrival_date'].date()}",
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Price trend")
        st.line_chart(series.set_index("arrival_date")["modal_price"])

    with col2:
        st.subheader("Day-over-day change (latest 10)")
        chg = series[["arrival_date", "modal_price"]].copy().tail(10)
        chg["pct_change"] = chg["modal_price"].pct_change() * 100
        chg["modal_price"] = chg["modal_price"].round(2)
        chg["pct_change"] = chg["pct_change"].round(2)
        st.dataframe(
            chg.assign(
                arrival_date=chg["arrival_date"].dt.date.astype(str)
            )[["arrival_date", "modal_price", "pct_change"]],
            width="stretch",
        )

    st.subheader("7-day forecast (OLS champion, refit daily)")
    fc = forecasts[
        (forecasts["commodity"] == commodity) & (forecasts["market"] == market)
    ].sort_values("horizon_days")
    if fc.empty:
        st.info("No forecast rows for this market/commodity pair.")
    else:
        show = fc[["forecast_date", "horizon_days", "forecast_price", "model"]].copy()
        show["forecast_date"] = show["forecast_date"].dt.date.astype(str)
        show["forecast_price"] = show["forecast_price"].round(2)
        st.dataframe(show, width="stretch")


if __name__ == "__main__":
    main()
