"""Interactive dashboard. Start with:  streamlit run src/dashboard.py"""

import sqlite3

import pandas as pd
import streamlit as st

from analysis import price_by_residual_load
from database import DB_FILE
from forecast import evaluate, run_forecast

SOURCES = {
    "solar": "Photovoltaik",
    "wind_onshore": "Wind Onshore",
    "wind_offshore": "Wind Offshore",
    "biomass": "Biomasse",
    "hydro": "Wasserkraft",
    "other_renewables": "Sonstige Erneuerbare",
    "lignite": "Braunkohle",
    "hard_coal": "Steinkohle",
    "gas": "Erdgas",
    "nuclear": "Kernenergie",
    "pumped_storage": "Pumpspeicher",
    "other_conventional": "Sonstige Konventionelle",
}


# Streamlit reruns the whole script after every click; caching avoids
# reading the database and training the model again each time.
@st.cache_data
def load_hourly():
    query = """
        SELECT h.*, e.renewables, e.residual_load
        FROM hourly AS h
        JOIN hourly_enriched AS e USING (timestamp_utc)
    """
    connection = sqlite3.connect(DB_FILE)
    table = pd.read_sql_query(query, connection, parse_dates=["timestamp_local"])
    connection.close()
    return table


@st.cache_data
def load_forecast():
    _, test = run_forecast()
    return test[["timestamp_local", "load", "baseline", "model"]]


def resample_rule(days):
    """Coarser time steps for longer periods, so that the charts stay readable."""
    if days <= 31:
        return "h"
    if days <= 366:
        return "D"
    return "W"


def select_period(table):
    first = table["timestamp_local"].min().date()
    last = table["timestamp_local"].max().date()
    period = st.sidebar.date_input("Zeitraum", (first, last), min_value=first, max_value=last)
    if len(period) != 2:  # the user has picked only the start date so far
        st.stop()
    start, end = period
    in_period = table["timestamp_local"].dt.date.between(start, end)
    return table[in_period], (end - start).days + 1


def show_key_figures(data):
    with_price = data.dropna(subset=["price"])
    columns = st.columns(4)
    columns[0].metric("Anteil Erneuerbare", f"{100 * data['renewables'].sum() / data['load'].sum():.1f} %")
    columns[1].metric("Ø Netzlast", f"{data['load'].mean() / 1000:.1f} GW")
    columns[2].metric("Stunden mit negativem Preis", f"{(with_price['price'] < 0).sum()}")
    columns[3].metric("Ø Großhandelspreis", f"{with_price['price'].mean():.0f} €/MWh")


def show_generation(data, rule):
    st.subheader("Stromerzeugung nach Energieträger (GW)")
    generation = data.set_index("timestamp_local")[list(SOURCES)].rename(columns=SOURCES)
    st.area_chart(generation.resample(rule).mean() / 1000, stack=True)


def show_renewables(data, rule):
    series = data.set_index("timestamp_local")[["renewables", "load"]].resample(rule).sum()
    st.subheader("Anteil erneuerbarer Energien an der Netzlast (%)")
    st.line_chart(100 * series["renewables"] / series["load"])

    st.subheader("Anteil nach Uhrzeit (%)")
    by_hour = data.groupby(data["timestamp_local"].dt.hour)[["renewables", "load"]].sum()
    st.bar_chart(100 * by_hour["renewables"] / by_hour["load"])


def show_negative_prices(data):
    with_price = data.dropna(subset=["price"])
    st.subheader("Stunden mit negativem Preis pro Monat")
    is_negative = with_price["price"] < 0
    # Summing True/False counts the negative hours and keeps months with zero
    per_month = is_negative.groupby(with_price["timestamp_local"].dt.to_period("M")).sum()
    st.bar_chart(per_month.rename(index=str))

    st.subheader("Preis nach Residuallast (Median je 2-GW-Klasse, EUR/MWh)")
    bands = price_by_residual_load(with_price)
    st.line_chart(bands["median"].rename_axis("Residuallast (GW)"))
    st.caption("Großhandelspreise nur zusammengefasst, siehe Lizenzhinweis im README.")


def show_forecast():
    forecast = load_forecast()
    first = forecast["timestamp_local"].min().date()
    last = forecast["timestamp_local"].max().date()
    start = st.date_input("Woche ab", pd.Timestamp("2025-04-14").date(),
                          min_value=first, max_value=last)
    week = forecast[forecast["timestamp_local"].dt.date.between(start, start + pd.Timedelta(days=6))]

    chart = week.set_index("timestamp_local")[["baseline", "model", "load"]].rename(columns={
        "baseline": "Baseline", "model": "Modell", "load": "Tatsächliche Last"})
    # One fixed color per series, in the same order as the columns
    st.line_chart(chart / 1000, y_label="GW", color=["#eb6834", "#2a78d6", "#898781"])

    rows = {
        "Baseline (diese Woche)": evaluate(week["load"], week["baseline"]),
        "Modell (diese Woche)": evaluate(week["load"], week["model"]),
        "Baseline (gesamter Test ab 2025)": evaluate(forecast["load"], forecast["baseline"]),
        "Modell (gesamter Test ab 2025)": evaluate(forecast["load"], forecast["model"]),
    }
    st.dataframe(pd.DataFrame(rows).T.round(2))


def main():
    st.set_page_config(page_title="Energiewende in Daten", layout="wide")
    st.title("Energiewende in Daten")
    st.caption("Stündliche Strommarktdaten für Deutschland. Quelle: Bundesnetzagentur | SMARD.de (CC BY 4.0)")

    data, days = select_period(load_hourly())
    show_key_figures(data)
    rule = resample_rule(days)

    tabs = st.tabs(["Erzeugung", "Erneuerbare", "Negative Preise", "Prognose"])
    with tabs[0]:
        show_generation(data, rule)
    with tabs[1]:
        show_renewables(data, rule)
    with tabs[2]:
        show_negative_prices(data)
    with tabs[3]:
        show_forecast()


if __name__ == "__main__":
    main()
