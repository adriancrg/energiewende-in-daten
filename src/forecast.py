"""Day-ahead forecast of the hourly load (question 3).

Setting: the forecast for day D is made on day D-1, so only load data up to day D-2
is known. All features are therefore calendar values or load values at least
two days old (no look-ahead leakage).

Compared: a naive baseline (same hour one week earlier) and a gradient boosting model.
Training data: 2020-2024. Test data: 2025 until today (never seen during training).
"""

import sqlite3
from datetime import date, timedelta

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

from analysis import FIGURES_DIR, save, set_style
from database import DB_FILE

TEST_START = pd.Timestamp("2025-01-01")
FEATURES = ["hour", "weekday", "month", "day_of_year", "is_holiday",
            "load_2_days_ago", "load_7_days_ago", "mean_load_2_days_ago"]


def easter_sunday(year):
    """Date of Easter Sunday (Gregorian calendar, anonymous Gauss algorithm)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def national_holidays(year):
    """Public holidays that apply in all German federal states."""
    easter = easter_sunday(year)
    return {
        date(year, 1, 1),                 # Neujahr
        easter - timedelta(days=2),       # Karfreitag
        easter + timedelta(days=1),       # Ostermontag
        date(year, 5, 1),                 # Tag der Arbeit
        easter + timedelta(days=39),      # Christi Himmelfahrt
        easter + timedelta(days=50),      # Pfingstmontag
        date(year, 10, 3),                # Tag der Deutschen Einheit
        date(year, 12, 25),
        date(year, 12, 26),
    }


def load_data():
    connection = sqlite3.connect(DB_FILE)
    table = pd.read_sql_query("SELECT timestamp_local, load FROM hourly", connection,
                              parse_dates=["timestamp_local"])
    connection.close()
    return table


def load_days_ago(table, days):
    """Load at the same local clock time `days` days earlier.

    Uses local time, so that 8:00 is compared with 8:00 also across clock changes.
    """
    by_time = table.drop_duplicates("timestamp_local").set_index("timestamp_local")["load"]
    earlier = table["timestamp_local"] - pd.Timedelta(days=days)
    return by_time.reindex(earlier).to_numpy()


def add_features(table):
    table = table.copy()
    time = table["timestamp_local"]
    years = range(time.dt.year.min(), time.dt.year.max() + 1)
    holidays = set().union(*(national_holidays(year) for year in years))

    table["hour"] = time.dt.hour
    table["weekday"] = time.dt.day_of_week  # 0 = Monday
    table["month"] = time.dt.month
    table["day_of_year"] = time.dt.day_of_year
    table["is_holiday"] = time.dt.date.isin(holidays).astype(int)
    table["load_2_days_ago"] = load_days_ago(table, 2)
    table["load_7_days_ago"] = load_days_ago(table, 7)
    # Average load of the whole day two days earlier (overall level of demand)
    daily_mean = table.groupby(time.dt.date)["load"].transform("mean")
    table["mean_load_2_days_ago"] = daily_mean.shift(48)
    return table.dropna()


def evaluate(actual, predicted):
    return {
        "MAE (MW)": mean_absolute_error(actual, predicted),
        "MAPE (%)": 100 * mean_absolute_percentage_error(actual, predicted),
    }


def plot_example(test, start, end, name):
    week = test[(test["timestamp_local"] >= start) & (test["timestamp_local"] < end)]
    figure, ax = plt.subplots()
    ax.plot(week["timestamp_local"], week["load"] / 1000, color="#0b0b0b", linewidth=2,
            label="Tatsächliche Last")
    ax.plot(week["timestamp_local"], week["baseline"] / 1000, color="#eb6834", linewidth=2,
            label="Baseline (gleiche Stunde Vorwoche)")
    ax.plot(week["timestamp_local"], week["model"] / 1000, color="#2a78d6", linewidth=2,
            label="Modell (Gradient Boosting)")
    ax.set_title("Prognose der Netzlast: Beispiel Ostern 2025")
    ax.set_ylabel("Last (GW)")
    ax.set_ylim(20, None)  # free space at the bottom for the legend
    ax.legend(loc="lower left", ncol=3)
    figure.autofmt_xdate()
    save(figure, name)


def run_forecast():
    """Train on 2020-2024 and return the test period with baseline and model forecasts."""
    table = add_features(load_data())
    train = table[table["timestamp_local"] < TEST_START]
    test = table[table["timestamp_local"] >= TEST_START].copy()

    model = HistGradientBoostingRegressor(random_state=0)
    model.fit(train[FEATURES], train["load"])

    test["baseline"] = test["load_7_days_ago"]
    test["model"] = model.predict(test[FEATURES])
    return train, test


def main():
    train, test = run_forecast()
    print(f"Training: {len(train)} hours, test: {len(test)} hours "
          f"({test['timestamp_local'].min():%Y-%m-%d} to {test['timestamp_local'].max():%Y-%m-%d})")

    results = pd.DataFrame({
        "Baseline": evaluate(test["load"], test["baseline"]),
        "Modell": evaluate(test["load"], test["model"]),
    }).T.round(2)
    print("\nError on the test period:")
    print(results.to_string())

    holidays = test[test["is_holiday"] == 1]
    print("\nMAPE (%) on public holidays only:")
    print(f"  Baseline {evaluate(holidays['load'], holidays['baseline'])['MAPE (%)']:.1f}, "
          f"Modell {evaluate(holidays['load'], holidays['model'])['MAPE (%)']:.1f}")

    set_style()
    FIGURES_DIR.mkdir(exist_ok=True)
    plot_example(test, "2025-04-14", "2025-04-28", "6_prognose_beispiel_ostern")


if __name__ == "__main__":
    main()
