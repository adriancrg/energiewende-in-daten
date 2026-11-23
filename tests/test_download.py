import json

import pandas as pd

from download import chunks_since, needs_download

WEEK_MS = 7 * 24 * 3600 * 1000


def test_chunks_since_keeps_the_chunk_that_contains_the_start():
    start = pd.Timestamp("2020-01-01", tz="UTC")
    monday_before = int(pd.Timestamp("2019-12-30", tz="UTC").timestamp() * 1000)
    timestamps = [monday_before - WEEK_MS, monday_before, monday_before + WEEK_MS]

    assert chunks_since(timestamps, start) == [monday_before, monday_before + WEEK_MS]


def test_missing_chunk_is_downloaded(tmp_path):
    assert needs_download(tmp_path / "missing.json")


def test_complete_chunk_is_not_downloaded_again(tmp_path):
    path = tmp_path / "complete.json"
    path.write_text(json.dumps({"series": [[1, 10.0], [2, 11.0]]}))
    assert not needs_download(path)


def test_chunk_with_empty_values_is_downloaded_again(tmp_path):
    path = tmp_path / "incomplete.json"
    path.write_text(json.dumps({"series": [[1, 10.0], [2, None]]}))
    assert needs_download(path)
