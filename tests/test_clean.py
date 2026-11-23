import pandas as pd

from clean import (
    complete_hourly_index,
    day_lengths,
    find_gaps,
    find_jumps,
    find_stuck_values,
    set_nuclear_after_shutdown,
    trim_to_complete_days,
)


def hourly_table(start_utc, hours, **columns):
    index = pd.date_range(start_utc, periods=hours, freq="h", tz="UTC", name="timestamp")
    return pd.DataFrame(columns, index=index)


def test_clock_change_days_have_23_and_25_hours():
    # 29 March 2025 00:00 local (UTC+1) until 27 October 2025 00:00 local (UTC+1)
    table = hourly_table("2025-03-28 23:00", 24 * 213, load=1.0)
    lengths = day_lengths(table)

    assert lengths[pd.Timestamp("2025-03-30").date()] == 23
    assert lengths[pd.Timestamp("2025-10-26").date()] == 25
    assert lengths[pd.Timestamp("2025-06-01").date()] == 24


def test_missing_hour_is_inserted_as_empty_row():
    table = hourly_table("2025-01-01", 5, load=[1.0, 2.0, 3.0, 4.0, 5.0]).drop(
        pd.Timestamp("2025-01-01 02:00", tz="UTC"))

    completed = complete_hourly_index(table)

    assert len(completed) == 5
    assert completed["load"].isna().sum() == 1


def test_incomplete_last_day_is_removed():
    # Load data ends at 10:00 local time on 3 January
    table = hourly_table("2024-12-31 23:00", 24 * 2 + 11, load=1.0)
    trimmed = trim_to_complete_days(table)

    assert trimmed.index.max() == pd.Timestamp("2025-01-02 22:00", tz="UTC")


def test_nuclear_is_zero_after_shutdown():
    table = hourly_table("2023-04-15 20:00", 4, nuclear=[100.0, 100.0, None, None])
    result = set_nuclear_after_shutdown(table)

    assert result["nuclear"].tolist() == [100.0, 100.0, 0.0, 0.0]


def test_find_gaps_returns_start_end_and_length():
    table = hourly_table("2025-01-01", 6, price=[1.0, None, None, 4.0, 5.0, None])
    gaps = find_gaps(table["price"])

    assert gaps["hours"].tolist() == [2, 1]
    assert gaps["start"].iloc[0] == pd.Timestamp("2025-01-01 01:00", tz="UTC")


def test_find_stuck_values_ignores_zeros():
    values = [0.0] * 30 + [7.0] * 30 + [1.0, 2.0]
    table = hourly_table("2025-01-01", len(values), solar=values)
    stuck = find_stuck_values(table["solar"], min_hours=24)

    assert stuck["value"].tolist() == [7.0]
    assert stuck["hours"].tolist() == [30]


def test_find_jumps_detects_a_single_spike():
    values = [50.0 + (i % 3) for i in range(100)]
    values[50] = 500.0
    table = hourly_table("2025-01-01", len(values), load=values)

    jumps = find_jumps(table["load"])

    assert pd.Timestamp("2025-01-03 02:00", tz="UTC") in jumps.index
