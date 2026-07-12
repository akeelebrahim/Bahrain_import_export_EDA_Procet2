"""
Data collection utility for the Bahrain Foreign Trade EDA project.

Downloads the raw non-oil foreign-trade datasets from the Kingdom of Bahrain
Open Data Portal (https://www.data.gov.bh, an OpenDataSoft platform) via its
public Explore API v2.1 CSV export endpoint, saving them to data/raw/.

Run once to (re)create the raw data locally:
    python scratch/data_download.py

Dsiclaimer: I used Ai and google search in parts on this code.
"""
import os
import time
import requests

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
RAW = os.path.abspath(RAW)
os.makedirs(RAW, exist_ok=True)

# (local_name, dataset_id, expected_rows)  -- ordered smallest -> largest
DATASETS = [
    ("annual_foreign_trade_statistics", "a-annual-foreign-trade-statistics", 168),
    ("national_exports_2024", "national-export-1-2024", 18521),
    ("re_exports_2024", "re-export-1-2024", 45647),
    ("total_exports_2023", "total-exports-2023", 59345),
    ("total_exports_2024", "total-export-1-2024", 60400),
    ("imports_2023", "01-import-non-oil-classified-by-commodity-and-country-for-2023", 321376),
    ("imports_2024", "import-2024", 322062),
]

BASE = "https://www.data.gov.bh/api/explore/v2.1/catalog/datasets/{}/exports/csv"


def download(ds_id, out_path):
    url = BASE.format(ds_id)
    with requests.get(url, stream=True, timeout=600) as r:
        r.raise_for_status()
        size = 0
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                if chunk:
                    f.write(chunk)
                    size += len(chunk)
    return size


def inspect(path):
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        first = f.readline()
        delim = ";" if first.count(";") >= first.count(",") else ","
        ncols = len(first.rstrip("\r\n").split(delim))
        nrows = sum(1 for _ in f)  # data rows (header already consumed)
    return delim, ncols, nrows


if __name__ == "__main__":
    for name, ds_id, exp in DATASETS:
        out = os.path.join(RAW, name + ".csv")
        t0 = time.time()
        try:
            size = download(ds_id, out)
            delim, ncols, nrows = inspect(out)
            dl = {";": "semicolon", ",": "comma"}[delim]
            print(f"OK  {name:34s} {size/1e6:6.1f} MB  {nrows:>7d} rows (exp {exp})  "
                  f"{ncols} cols  delim={dl}  {time.time()-t0:4.0f}s")
        except Exception as e:
            print(f"ERR {name:34s} {type(e).__name__}: {e}")
