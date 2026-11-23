from datetime import date

import pandas as pd
import pytest

from forecast import easter_sunday, evaluate, load_days_ago, national_holidays


@pytest.mark.parametrize("year, expected", [
    (2020, date(2020, 4, 12)),
    (2024, date(2024, 3, 31)),
    (2025, date(2025, 4, 20)),
    (2026, date(2026, 4, 5)),
])
def test_easter_sunday(year, expected):
    assert easter_sunday(year) == expected


def test_national_holidays_2025():
    holidays = national_holidays(2025)

    assert len(holidays) == 9
    assert date(2025, 4, 18) in holidays   # Karfreitag
    assert date(2025, 6, 9) in holidays    # Pfingstmontag
    assert date(2025, 10, 3) in holidays


def test_load_one_week_earlier_uses_local_clock_time_across_clock_change():
    utc = pd.date_range("2025-10-19 22:00", "2025-10-28 22:00", freq="h", tz="UTC")
    local = utc.tz_convert("Europe/Berlin").tz_localize(None)
    table = pd.DataFrame({"timestamp_local": local, "load": range(len(utc))})

    table["load_7_days_ago"] = load_days_ago(table, 7)

    row = table[table["timestamp_local"] == pd.Timestamp("2025-10-27 08:00")].iloc[0]
    week_before = table[table["timestamp_local"] == pd.Timestamp("2025-10-20 08:00")].iloc[0]
    assert row["load_7_days_ago"] == week_before["load"]


def test_evaluate_mae_and_mape():
    result = evaluate(pd.Series([100.0, 200.0]), pd.Series([110.0, 180.0]))

    assert result["MAE (MW)"] == pytest.approx(15.0)
    assert result["MAPE (%)"] == pytest.approx(10.0)
