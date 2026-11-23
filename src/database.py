"""Build the SQLite database from the clean data and run the SQL queries in sql/."""

import sqlite3

import pandas as pd

from clean import CLEAN_FILE
from download import PROJECT_DIR

DB_FILE = PROJECT_DIR / "data" / "energy.db"
SQL_DIR = PROJECT_DIR / "sql"

QUERIES = [
    "quality_missing_values",
    "quality_day_lengths",
    "renewable_share_by_year",
    "renewable_share_by_weekday",
    "renewable_share_by_hour",
    "negative_prices_by_year",
    "negative_prices_by_hour",
    "price_by_residual_load",
]


def create_database():
    """Create a new database: tables from sql/schema.sql, rows from the clean CSV."""
    DB_FILE.unlink(missing_ok=True)
    table = pd.read_csv(CLEAN_FILE).rename(columns={"timestamp": "timestamp_utc"})
    connection = sqlite3.connect(DB_FILE)
    connection.executescript((SQL_DIR / "schema.sql").read_text())
    table.to_sql("hourly", connection, if_exists="append", index=False)
    connection.commit()
    connection.close()
    return len(table)


def run_query(name):
    """Run sql/<name>.sql and return the result as a DataFrame."""
    query = (SQL_DIR / f"{name}.sql").read_text()
    connection = sqlite3.connect(DB_FILE)
    result = pd.read_sql_query(query, connection)
    connection.close()
    return result


def main():
    rows = create_database()
    print(f"Database {DB_FILE.relative_to(PROJECT_DIR)} created with {rows} hours")
    for name in QUERIES:
        print(f"\n--- {name}")
        print(run_query(name).to_string(index=False, max_rows=14))


if __name__ == "__main__":
    main()
