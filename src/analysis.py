"""Exploratory analysis and figures for question 1 (renewable share) and 2 (negative prices).

The figures are saved in figures/. Price results are shown only in aggregated form
(see the licence note in the README).
"""

import sqlite3

import matplotlib.pyplot as plt
import pandas as pd

from database import DB_FILE, run_query
from download import PROJECT_DIR

FIGURES_DIR = PROJECT_DIR / "figures"

BLUE = "#2a78d6"
LIGHT_BLUE = "#9ec5f4"
SEASON_COLORS = {"winter": "#2a78d6", "spring": "#1baf7a", "summer": "#eda100", "autumn": "#eb6834"}
SEASON_NAMES = {"winter": "Winter", "spring": "Frühling", "summer": "Sommer", "autumn": "Herbst"}
MONTHS = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]


def set_style():
    plt.rcParams.update({
        "figure.figsize": (9, 4.5),
        "figure.dpi": 150,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#c3c2b7",
        "axes.labelcolor": "#52514e",
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": "#e1e0d9",
        "grid.linewidth": 0.6,
        "xtick.color": "#52514e",
        "ytick.color": "#52514e",
        "legend.frameon": False,
    })


def load_hourly():
    """Read the hourly view with calendar fields and derived values from the database."""
    connection = sqlite3.connect(DB_FILE)
    table = pd.read_sql_query("SELECT * FROM hourly_enriched", connection)
    connection.close()
    return table


def save(figure, name):
    figure.tight_layout()
    figure.savefig(FIGURES_DIR / f"{name}.png")
    plt.close(figure)
    print(f"Saved figures/{name}.png")


def plot_share_by_year(last_day):
    data = run_query("renewable_share_by_year")
    colors = [BLUE] * (len(data) - 1) + [LIGHT_BLUE]  # last year is incomplete
    figure, ax = plt.subplots()
    bars = ax.bar(data["year"].astype(str), data["renewable_share_pct"], color=colors, width=0.6)
    ax.bar_label(bars, fmt="%.1f %%", padding=3, color="#0b0b0b")
    ax.set_title("Anteil erneuerbarer Energien an der Netzlast")
    ax.set_ylabel("Anteil (%)")
    ax.set_ylim(0, 70)
    ax.grid(axis="x", visible=False)
    ax.annotate(f"bis {last_day}", (len(data) - 1, 3), ha="center", color="#52514e")
    save(figure, "1_anteil_erneuerbare_pro_jahr")


def plot_share_by_hour():
    data = run_query("renewable_share_by_hour")
    figure, ax = plt.subplots()
    for season, color in SEASON_COLORS.items():
        part = data[data["season"] == season]
        ax.plot(part["hour"], part["renewable_share_pct"], color=color, linewidth=2,
                label=SEASON_NAMES[season])
    ax.set_title("Anteil erneuerbarer Energien nach Uhrzeit und Jahreszeit (2020–2026)")
    ax.set_xlabel("Uhrzeit (deutsche Ortszeit)")
    ax.set_ylabel("Anteil (%)")
    ax.set_xticks(range(0, 24, 3))
    ax.set_xlim(0, 23)
    ax.legend(loc="upper left")
    save(figure, "2_anteil_erneuerbare_nach_uhrzeit")


def plot_negative_hours_by_year(last_day):
    data = run_query("negative_prices_by_year")
    colors = [BLUE] * (len(data) - 1) + [LIGHT_BLUE]
    figure, ax = plt.subplots()
    bars = ax.bar(data["year"].astype(str), data["negative_hours"], color=colors, width=0.6)
    ax.bar_label(bars, padding=3, color="#0b0b0b")
    ax.set_title("Stunden mit negativem Strompreis pro Jahr")
    ax.set_ylabel("Stunden")
    ax.grid(axis="x", visible=False)
    ax.annotate(f"bis {last_day}", (len(data) - 1, 15), ha="center", color="#52514e")
    save(figure, "3_negative_preise_pro_jahr")


def plot_negative_hours_heatmap(hourly):
    """Number of negative-price hours for each month and hour of the day."""
    negative = hourly[hourly["price"] < 0]
    counts = (negative.groupby(["month", "hour"]).size()
              .unstack(fill_value=0)
              .reindex(index=range(1, 13), columns=range(24), fill_value=0))
    figure, ax = plt.subplots()
    image = ax.imshow(counts, cmap="Blues", aspect="auto")
    ax.set_title("Wann sind die Preise negativ? Stunden 2020–2026 nach Monat und Uhrzeit")
    ax.set_xlabel("Uhrzeit (deutsche Ortszeit)")
    ax.set_xticks(range(0, 24, 3))
    ax.set_yticks(range(12), MONTHS)
    ax.grid(False)
    figure.colorbar(image, ax=ax, label="Stunden mit negativem Preis")
    save(figure, "4_negative_preise_monat_uhrzeit")


def price_by_residual_load(hourly, band_gw=2):
    """Median, 10 % and 90 % quantile of the price and share of negative hours per band."""
    data = hourly.dropna(subset=["price"]).copy()
    data["band"] = (data["residual_load"] / 1000 // band_gw) * band_gw + band_gw / 2
    grouped = data.groupby("band")["price"]
    result = pd.DataFrame({
        "hours": grouped.size(),
        "median": grouped.median(),
        "q10": grouped.quantile(0.1),
        "q90": grouped.quantile(0.9),
        "negative_pct": 100 * grouped.apply(lambda price: (price < 0).mean()),
    })
    return result[result["hours"] >= 50]  # skip bands with too few hours


def plot_price_vs_residual_load(hourly):
    data = price_by_residual_load(hourly)
    figure, (top, bottom) = plt.subplots(2, 1, figsize=(9, 6.5), sharex=True,
                                         gridspec_kw={"height_ratios": [2, 1]})
    top.fill_between(data.index, data["q10"], data["q90"], color=LIGHT_BLUE, alpha=0.6,
                     linewidth=0, label="10–90 % der Stunden")
    top.plot(data.index, data["median"], color=BLUE, linewidth=2, label="Median")
    top.axhline(0, color="#52514e", linewidth=0.8)
    top.set_title("Strompreis und Residuallast (Last − Wind − PV)")
    top.set_ylabel("Preis (EUR/MWh)")
    top.legend(loc="upper left")

    bottom.bar(data.index, data["negative_pct"], width=1.6, color=BLUE)
    bottom.set_ylabel("Anteil negativ (%)")
    bottom.set_xlabel("Residuallast (GW), Klassen à 2 GW")
    bottom.grid(axis="x", visible=False)
    save(figure, "5_preis_und_residuallast")


def print_key_numbers(hourly):
    with_price = hourly.dropna(subset=["price"])
    negative = with_price[with_price["price"] < 0]
    weekend = negative["weekday"].isin([0, 6]).mean()
    midday = negative["hour"].between(10, 16).mean()
    below_10gw = (negative["residual_load"] < 10000).mean()
    print(f"\nNegative price hours: {len(negative)} of {len(with_price)}")
    print(f"  on weekends: {100 * weekend:.0f} % (weekends are 29 % of all days)")
    print(f"  between 10:00 and 16:59: {100 * midday:.0f} %")
    print(f"  with residual load below 10 GW: {100 * below_10gw:.0f} %")
    correlation = with_price["price"].corr(with_price["residual_load"], method="spearman")
    print(f"Spearman correlation price vs. residual load: {correlation:.2f}")


def main():
    set_style()
    FIGURES_DIR.mkdir(exist_ok=True)
    hourly = load_hourly()
    last_day = pd.Timestamp(hourly["day"].max()).strftime("%d.%m.")

    plot_share_by_year(last_day)
    plot_share_by_hour()
    plot_negative_hours_by_year(last_day)
    plot_negative_hours_heatmap(hourly)
    plot_price_vs_residual_load(hourly)
    print_key_numbers(hourly)


if __name__ == "__main__":
    main()
