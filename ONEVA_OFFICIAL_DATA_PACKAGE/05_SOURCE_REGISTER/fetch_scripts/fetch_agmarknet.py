"""Fetch official mandi prices from the Open Government Data Platform (AGMARKNET feed)
into 04_MARKET_DATA/market_prices.csv, preserving the raw JSON pages untouched.

    export DATA_GOV_IN_API_KEY=...        # free key from data.gov.in -> My Account
    python 05_SOURCE_REGISTER/fetch_scripts/fetch_agmarknet.py --state "Tamil Nadu" --unit "<unit from resource page>"

Resource: https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi
API id  : 9ef84268-d588-465a-a308-a864a43d0070  (confirm on the resource page on first run)

Rules enforced (ONEVA Part F/N):
  * --unit is REQUIRED and must be copied from the resource description; no unit conversion.
  * rows with non-numeric or negative prices are rejected (logged), never repaired.
  * exact duplicate records (e.g. from paging retries) are dropped and counted.
  * dates are normalised dd/mm/yyyy -> yyyy-mm-dd; unparseable dates are rejected.
"""
import argparse, csv, datetime, hashlib, json, os, sys, time
from pathlib import Path

import requests

PKG = Path(__file__).resolve().parents[2]
RAW = PKG / "04_MARKET_DATA/raw_agmarknet"
OUT = PKG / "04_MARKET_DATA/market_prices.csv"
RESOURCE = "9ef84268-d588-465a-a308-a864a43d0070"
API = f"https://api.data.gov.in/resource/{RESOURCE}"
PAGE_URL = "https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi"
COLS = ["commodity", "state", "district", "market", "date", "minimum_price", "maximum_price",
        "modal_price", "unit", "source", "source_url", "retrieval_date"]


def parse_date(s):
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.datetime.strptime(s.strip(), fmt).date().isoformat()
        except ValueError:
            pass
    return None


def num(v):
    try:
        x = float(str(v).replace(",", ""))
    except ValueError:
        return None
    return x if x >= 0 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=None)
    ap.add_argument("--district", default=None)
    ap.add_argument("--commodity", default=None)
    ap.add_argument("--unit", required=True, help="unit exactly as stated on the resource page")
    ap.add_argument("--limit", type=int, default=1000)
    a = ap.parse_args()
    key = os.environ.get("DATA_GOV_IN_API_KEY")
    if not key:
        sys.exit("DATA_GOV_IN_API_KEY not set")
    RAW.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    params = {"api-key": key, "format": "json", "limit": a.limit, "offset": 0}
    for f, v in (("state", a.state), ("district", a.district), ("commodity", a.commodity)):
        if v:
            params[f"filters[{f}]"] = v
    seen, rows, rejected, dups = set(), [], 0, 0
    while True:
        r = requests.get(API, params=params, timeout=60)
        r.raise_for_status()
        raw = r.content
        (RAW / f"{today}_offset{params['offset']}_{hashlib.sha256(raw).hexdigest()[:12]}.json").write_bytes(raw)
        data = json.loads(raw)
        recs = data.get("records", [])
        for rec in recs:
            d = parse_date(rec.get("arrival_date", ""))
            lo, hi, mo = num(rec.get("min_price")), num(rec.get("max_price")), num(rec.get("modal_price"))
            if d is None or None in (lo, hi, mo):
                rejected += 1
                continue
            row = dict(commodity=rec.get("commodity", "").strip(), state=rec.get("state", "").strip(),
                       district=rec.get("district", "").strip(), market=rec.get("market", "").strip(),
                       date=d, minimum_price=lo, maximum_price=hi, modal_price=mo, unit=a.unit,
                       source="AGMARKNET via OGD Platform India (resource %s)" % RESOURCE,
                       source_url=PAGE_URL, retrieval_date=today)
            k = tuple(row[c] for c in COLS[:8]) + (rec.get("variety", ""), rec.get("grade", ""))
            if k in seen:
                dups += 1
                continue
            seen.add(k)
            rows.append(row)
        if len(recs) < a.limit:
            break
        params["offset"] += a.limit
        time.sleep(1)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    print(f"written={len(rows)} rejected={rejected} duplicates_dropped={dups} raw_dir={RAW}")
    print("NOTE: variety/grade are kept in raw JSON; add columns if ONEVA needs them.")


if __name__ == "__main__":
    main()
