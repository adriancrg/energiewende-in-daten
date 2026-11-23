"""Clean the raw SMARD table and report its data quality.

Changes: drop the incomplete last day, make the hourly index complete, set nuclear
to zero after the shutdown and add the local German time.
Gaps and outliers are only reported, not changed: extreme prices are real market
events, and filling long gaps would invent data.
"""

import pandas as pd

from download import OUTPUT_FILE as RAW_FILE
from download import PROJECT_DIR

CLEAN_FILE = PROJECT_DIR / "data" / "smard_hourly_clean.csv"
TIMEZONE = "Europe/Berlin"
# The last three nuclear plants went offline on 15 April 2023
NUCLEAR_SHUTDOWN = pd.Timestamp("2023-04-16", tz=TIMEZONE)


def load_raw():
    return pd.read_csv(RAW_FILE, index_col="timestamp", parse_dates=True)


def trim_to_complete_days(table):
    """Keep only complete local days: drop the day in which the load data ends."""
    last_hour = table["load"].last_valid_index().tz_convert(TIMEZONE)
    first_incomplete_day = (last_hour + pd.Timedelta(hours=1)).normalize()
    return table[table.index < first_incomplete_day]


def complete_hourly_index(table):
    """Insert missing hours as empty rows, so that every hour exists exactly once."""
    return table.asfreq("h")


def set_nuclear_after_shutdown(table):
    table = table.copy()
    table.loc[table.index >= NUCLEAR_SHUTDOWN, "nuclear"] = 0.0
    return table


def add_local_time(table):
    """Add the local time without UTC offset, used later for hour, weekday and season."""
    table = table.copy()
    local = table.index.tz_convert(TIMEZONE).tz_localize(None)
    table.insert(0, "timestamp_local", local)
    return table


def day_lengths(table):
    """Number of hours per local calendar day (23 or 25 on clock-change days)."""
    local_days = table.index.tz_convert(TIMEZONE).date
    return table.groupby(local_days).size()


def constant_blocks(series):
    """Split a series into blocks of consecutive equal values.

    The block id increases by one every time the value changes.
    """
    block_id = (series != series.shift()).cumsum()
    blocks = series.index.to_series().groupby(block_id).agg(["min", "max", "size"])
    blocks.columns = ["start", "end", "hours"]
    blocks["value"] = series.groupby(block_id).first()
    return blocks.reset_index(drop=True)


def find_gaps(series):
    """Return start, end and length of every block of missing values."""
    blocks = constant_blocks(series.isna())
    return blocks[blocks["value"]][["start", "end", "hours"]]


def find_stuck_values(series, min_hours=24):
    """Return blocks where a non-zero value stays exactly the same for min_hours or more."""
    blocks = constant_blocks(series)
    return blocks[(blocks["hours"] >= min_hours) & (blocks["value"] != 0)]


def find_jumps(series, threshold=6):
    """Return hours whose change to the previous hour is extreme.

    Uses a robust z-score (median and MAD instead of mean and standard deviation),
    because the standard deviation itself is inflated by outliers.
    """
    change = series.diff()
    median = change.median()
    mad = (change - median).abs().median()
    z = (change - median) / (1.4826 * mad)  # 1.4826 * MAD ~ std for normal data
    return series[z.abs() > threshold]


def residual_load_difference(table):
    """Largest difference between our residual load and SMARD's own series."""
    own = table["load"] - table["wind_onshore"] - table["wind_offshore"] - table["solar"]
    return (own - table["residual_load_smard"]).abs().max()


def local(timestamp):
    return timestamp.tz_convert(TIMEZONE).strftime("%Y-%m-%d %H:%M")


def print_day_lengths(table):
    lengths = day_lengths(table)
    for hours in (23, 25):
        days = [str(day) for day in lengths[lengths == hours].index]
        print(f"Days with {hours} hours ({len(days)}): {', '.join(days)}")


def print_quality_checks(table):
    print("\nGaps (local time):")
    found = False
    for column in table.columns:
        for gap in find_gaps(table[column]).itertuples():
            print(f"  {column}: {local(gap.start)} to {local(gap.end)} ({gap.hours} h)")
            found = True
    if not found:
        print("  none")

    negative = (table.drop(columns=["price", "residual_load_smard"]) < 0).sum().sum()
    print(f"\nNegative load or generation values: {negative}")
    print(f"Extreme hour-to-hour jumps in load: {len(find_jumps(table['load']))}")
    print(f"Residual load vs. SMARD, max difference: {residual_load_difference(table):.1f} MWh")

    print("\nValues constant for 24 h or more:")
    for column in table.columns:
        stuck = find_stuck_values(table[column])
        if len(stuck) > 0:
            print(f"  {column}: {len(stuck)} blocks, {stuck['hours'].sum()} h, "
                  f"from {local(stuck['start'].min())} to {local(stuck['end'].max())}")

    price = table["price"]
    print("\nExtreme prices (real market events, kept):")
    print(f"  min {price.min():.1f} EUR/MWh on {local(price.idxmin())}")
    print(f"  max {price.max():.1f} EUR/MWh on {local(price.idxmax())}")


def main():
    table = trim_to_complete_days(load_raw())
    rows_before = len(table)
    table = complete_hourly_index(table)
    print(f"Hours: {len(table)}, from {local(table.index.min())} to {local(table.index.max())}")
    print(f"Missing hours inserted: {len(table) - rows_before}")
    print_day_lengths(table)

    table = set_nuclear_after_shutdown(table)
    print_quality_checks(table)

    # Our own residual load matches SMARD's series, so we keep only one definition
    table = add_local_time(table).drop(columns="residual_load_smard")
    table.to_csv(CLEAN_FILE)
    print(f"\nSaved: {CLEAN_FILE.relative_to(PROJECT_DIR)}")


if __name__ == "__main__":
    main()
