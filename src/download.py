"""Download hourly electricity market data for Germany from SMARD.

Source: Bundesnetzagentur | SMARD.de (CC BY 4.0).
SMARD serves every series in weekly chunks. Each chunk is cached as a JSON file
in data/raw/, so a new run only downloads missing or incomplete weeks.
"""

import json
import time
import urllib.request
from pathlib import Path

import pandas as pd

BASE_URL = "https://www.smard.de/app/chart_data"
START = pd.Timestamp("2020-01-01", tz="Europe/Berlin")
PAUSE_SECONDS = 0.1  # short pause between requests to be polite to the server

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
OUTPUT_FILE = PROJECT_DIR / "data" / "smard_hourly_raw.csv"

# Column name -> (SMARD filter id, region). Energy in MWh per hour, price in EUR/MWh.
SERIES = {
    "load": (410, "DE"),
    "residual_load_smard": (4359, "DE"),
    "solar": (4068, "DE"),
    "wind_onshore": (4067, "DE"),
    "wind_offshore": (1225, "DE"),
    "biomass": (4066, "DE"),
    "hydro": (1226, "DE"),
    "other_renewables": (1228, "DE"),
    "lignite": (1223, "DE"),
    "hard_coal": (4069, "DE"),
    "gas": (4071, "DE"),
    "nuclear": (1224, "DE"),
    "pumped_storage": (4070, "DE"),
    "other_conventional": (1227, "DE"),
    "price": (4169, "DE-LU"),
}


def fetch_json(url, retries=3):
    """Return the JSON content of url, retrying a few times on network errors."""
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return json.load(response)
        except OSError as error:
            if attempt == retries:
                raise
            print(f"  attempt {attempt} failed ({error}), retrying...")
            time.sleep(5 * attempt)


def chunk_timestamps(filter_id, region):
    """Return the start times (Unix ms, UTC) of all weekly chunks of a series."""
    url = f"{BASE_URL}/{filter_id}/{region}/index_hour.json"
    return fetch_json(url)["timestamps"]


def chunks_since(timestamps, start):
    """Keep the chunk that contains `start` and all later chunks."""
    start_ms = int(start.timestamp() * 1000)
    first = max((t for t in timestamps if t <= start_ms), default=min(timestamps))
    return [t for t in timestamps if t >= first]


def chunk_path(name, timestamp):
    return RAW_DIR / name / f"{timestamp}.json"


def needs_download(path):
    """Download a chunk if it is missing or still has empty values (e.g. future hours)."""
    if not path.exists():
        return True
    values = json.loads(path.read_text())["series"]
    return any(value is None for _, value in values)


def download_series(name, filter_id, region):
    """Download all missing or incomplete weekly chunks of one series."""
    timestamps = chunks_since(chunk_timestamps(filter_id, region), START)
    downloaded = 0
    for timestamp in timestamps:
        path = chunk_path(name, timestamp)
        if not needs_download(path):
            continue
        url = f"{BASE_URL}/{filter_id}/{region}/{filter_id}_{region}_hour_{timestamp}.json"
        data = fetch_json(url)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
        downloaded += 1
        time.sleep(PAUSE_SECONDS)
    print(f"{name:<20} {len(timestamps)} chunks, {downloaded} downloaded")


def load_series(name):
    """Read all cached chunks of one series into a pandas Series indexed by UTC time."""
    rows = []
    for path in sorted((RAW_DIR / name).glob("*.json")):
        rows.extend(json.loads(path.read_text())["series"])
    frame = pd.DataFrame(rows, columns=["timestamp", name]).dropna()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
    return frame.set_index("timestamp")[name]


def build_table():
    """Combine all series into one table: one row per hour, one column per series."""
    columns = [load_series(name) for name in SERIES]
    table = pd.concat(columns, axis=1).sort_index()
    return table[table.index >= START]


def main():
    for name, (filter_id, region) in SERIES.items():
        download_series(name, filter_id, region)
    table = build_table()
    table.to_csv(OUTPUT_FILE)
    print(f"Saved {len(table)} hours ({table.index.min()} to {table.index.max()})")
    print(f"File: {OUTPUT_FILE.relative_to(PROJECT_DIR)}")


if __name__ == "__main__":
    main()
