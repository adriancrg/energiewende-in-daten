import sqlite3

import pandas as pd
import pytest

from database import SQL_DIR

COLUMNS = ["load", "solar", "wind_onshore", "wind_offshore", "biomass", "hydro",
           "other_renewables", "lignite", "hard_coal", "gas", "nuclear",
           "pumped_storage", "other_conventional", "price"]


@pytest.fixture
def connection():
    """In-memory database with the real schema and two example hours."""
    connection = sqlite3.connect(":memory:")
    connection.executescript((SQL_DIR / "schema.sql").read_text())
    rows = pd.DataFrame([
        # Winter night: high load, little wind, positive price
        {"timestamp_utc": "2025-01-15 02:00:00+00:00", "timestamp_local": "2025-01-15 03:00:00",
         "load": 60000, "solar": 0, "wind_onshore": 10000, "wind_offshore": 2000,
         "biomass": 4000, "hydro": 2000, "other_renewables": 0, "price": 120.0},
        # Sunny Sunday in May: more wind and PV than load, negative price
        {"timestamp_utc": "2025-05-11 11:00:00+00:00", "timestamp_local": "2025-05-11 13:00:00",
         "load": 40000, "solar": 45000, "wind_onshore": 5000, "wind_offshore": 1000,
         "biomass": 4000, "hydro": 2000, "other_renewables": 0, "price": -20.0},
    ]).reindex(columns=["timestamp_utc", "timestamp_local"] + COLUMNS).fillna(0)
    rows.to_sql("hourly", connection, if_exists="append", index=False)
    yield connection
    connection.close()


def test_view_calculates_residual_load_and_calendar(connection):
    view = pd.read_sql_query("SELECT * FROM hourly_enriched ORDER BY timestamp_utc", connection)

    assert view["residual_load"].tolist() == [48000, -11000]
    assert view["hour"].tolist() == [3, 13]   # local time, not UTC
    assert view["weekday"].tolist() == [3, 0]  # Wednesday, Sunday
    assert view["season"].tolist() == ["winter", "spring"]


def test_renewable_share_is_energy_weighted(connection):
    result = pd.read_sql_query((SQL_DIR / "renewable_share_by_year.sql").read_text(), connection)

    # (18000 + 57000) / (60000 + 40000), not the mean of 30 % and 142.5 %
    assert result["renewable_share_pct"].iloc[0] == pytest.approx(75.0)


def test_negative_price_lies_in_negative_residual_load_band(connection):
    result = pd.read_sql_query((SQL_DIR / "price_by_residual_load.sql").read_text(), connection)
    lowest_band = result.iloc[0]

    assert lowest_band["residual_load_band"] == "< 0 GW"
    assert lowest_band["negative_hours"] == 1
