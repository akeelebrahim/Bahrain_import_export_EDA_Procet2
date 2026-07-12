"""Generate compact aggregate tables that power the Streamlit dashboard, so the
app never has to load the ~320k-row raw files. Saves to data/cleaned/.
Run from project root:  python scratch/build_dashboard_data.py
Dsiclaimer: I used Ai and google search in parts on this code.
"""
from pathlib import Path
import pandas as pd

ROOT = Path(r"~\Aqeel_Ebrahim_EDA_Project")
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "cleaned"

RENAME = {"export_value_bd": "value_bd", "export_weight_kg": "weight_kg", "export_quantity": "quantity",
          "export_value_usa": "value_usa", "import_value_bd": "value_bd", "import_weight_kg": "weight_kg",
          "import_quantity": "quantity", "import_value_usa": "value_usa",
          "qym_lwrdt_dynr_bhryny": "value_bd", "qym_lwrdt_dwlr_mryky": "value_usa",
          "wzn_lwrdt_kjm": "weight_kg", "kmy_lwrdt": "quantity", "whd_lqys": "um"}
DROP = ["n", "lshhr", "lsl", "ldwl"]

def load_detail(fname, flow, year_default=None):
    df = pd.read_csv(RAW / f"{fname}.csv", sep=";", dtype=str)
    df = df.rename(columns=RENAME).drop(columns=[c for c in DROP if c in df.columns])
    if "year" not in df.columns:
        df["year"] = year_default
    df["month_num"] = df["month"].str.extract(r"(\d+)").astype(int)
    df["value_bd"] = pd.to_numeric(df["value_bd"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["commodity"] = df["commodity"].str.strip().str.title()
    df["country_name"] = df["country_name"].str.strip().str.title()
    df["commodity_no"] = df["commodity_no"].astype(str).str.strip()
    df["hs_chapter"] = df["commodity_no"].str[:2]
    df["flow"] = flow
    return df

imp23 = load_detail("imports_2023", "Import", 2023)
imp24 = load_detail("imports_2024", "Import", 2024)
texp23 = load_detail("total_exports_2023", "Export", 2023)
texp24 = load_detail("total_exports_2024", "Export", 2024)
nexp24 = load_detail("national_exports_2024", "National Export", 2024)
rexp24 = load_detail("re_exports_2024", "Re-export", 2024)

trade = pd.concat([imp23, imp24, texp23, texp24], ignore_index=True)

(trade.groupby(["flow", "year", "country_name"], as_index=False)["value_bd"].sum()
      .to_csv(CLEAN / "dash_country_year.csv", index=False))
(trade.groupby(["flow", "year", "commodity", "hs_chapter"], as_index=False)["value_bd"].sum()
      .to_csv(CLEAN / "dash_commodity_year.csv", index=False))
(trade.groupby(["flow", "year", "month_num"], as_index=False)["value_bd"].sum()
      .to_csv(CLEAN / "dash_month_year.csv", index=False))

comp = pd.DataFrame({
    "component": ["National-origin", "Re-export"],
    "value_bd": [nexp24["value_bd"].sum(), rexp24["value_bd"].sum()],
})
comp.to_csv(CLEAN / "dash_export_composition_2024.csv", index=False)

for f in ["dash_country_year", "dash_commodity_year", "dash_month_year", "dash_export_composition_2024"]:
    n = len(pd.read_csv(CLEAN / f"{f}.csv"))
    print(f"  {f}.csv -> {n:,} rows")
print("dashboard aggregates written to", CLEAN)
