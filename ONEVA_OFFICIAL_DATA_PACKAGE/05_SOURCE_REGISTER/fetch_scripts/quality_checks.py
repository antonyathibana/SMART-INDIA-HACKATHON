"""Part N data-quality checks for the ONEVA official data package. Exit code 1 on any failure."""
import csv, json, re, sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[2]
fails, warns = [], []


def rows(p):
    with open(PKG / p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# --- scheme checks
for r in rows("02_SCHEME_PARAMETERS/scheme_parameters.csv"):
    tag = f"{r['scheme']}/{r['parameter']}"
    if not r["source_url"]:
        fails.append(f"missing source_url: {tag}")
    if r["verification_status"].startswith("OBSOLETE") and "SUPERSEDED" not in r["condition"]:
        fails.append(f"obsolete value not marked superseded: {tag}")
    if r["unit"] == "INR" and not re.fullmatch(r"\d+", r["value"].split(" ")[0]):
        fails.append(f"INR value not normalised to plain rupees: {tag} = {r['value']}")
    if "percent" in r["unit"] and not re.match(r"^\d+(\.\d+)?", r["value"]) and r["verification_status"] not in ("NOT VERIFIED", "NEEDS HUMAN REVIEW"):
        fails.append(f"percentage not numeric: {tag}")
    if re.search(r"\blakh\b|\bcrore\b", r["value"], re.I) and r["unit"] == "INR":
        fails.append(f"lakh/crore in INR value: {tag}")
    if r["source_page"].startswith("NOT RECORDED"):
        warns.append(f"page number pending: {tag}")
for r in rows("01_SIH26091_ELIGIBILITY/scheme_eligibility.csv"):
    if not r["source_url"]:
        fails.append(f"eligibility row without source: {r['scheme']}")
    for c in ("income_limit", "project_cost_max"):
        v = r[c]
        if v and v[0].isdigit() and not re.fullmatch(r"\d+", v.split(" ")[0]):
            fails.append(f"{c} not plain INR in {r['scheme']}")

# --- dates
date_re = re.compile(r"\d{4}-\d{2}-\d{2}")
for p in ("02_SCHEME_PARAMETERS/scheme_parameters.csv",):
    for r in rows(p):
        for m in date_re.findall(r["effective_date"]):
            y, mo, d = map(int, m.split("-"))
            if not (2000 <= y <= 2026 and 1 <= mo <= 12 and 1 <= d <= 31):
                fails.append(f"bad date {m} in {r['parameter']}")

# --- market prices
mp = rows("04_MARKET_DATA/market_prices.csv")
seen = set()
for r in mp:
    k = tuple(r.values())
    if k in seen:
        fails.append(f"duplicate price row {k[:5]}")
    seen.add(k)
    for c in ("minimum_price", "maximum_price", "modal_price"):
        try:
            if float(r[c]) < 0:
                fails.append(f"negative price {r}")
        except ValueError:
            fails.append(f"non-numeric price {c}={r[c]}")
    if not date_re.fullmatch(r["date"]):
        fails.append(f"malformed date {r['date']}")
    if not r["unit"]:
        fails.append("price row without unit")
if not mp:
    warns.append("market_prices.csv has no rows (fetch not yet run)")
units = {r["unit"] for r in mp}
if len(units) > 1:
    warns.append(f"multiple price units present: {units}")

# --- purchasing power labelling
for r in rows("04_MARKET_DATA/purchasing_power.csv"):
    if "village" in r["indicator"].lower():
        fails.append("purchasing power row claims village level")
    if r["value"] and r["label"] == "NOT VERIFIED":
        fails.append(f"unverified value stored: {r['state']} {r['indicator']}")

# --- demand proxies: production never called demand
for r in rows("04_MARKET_DATA/demand_proxies.csv"):
    if r["classification"].startswith("PRODUCTION") and r["measures_actual_demand"] != "NO":
        fails.append(f"production labelled as demand: {r['dataset']}")

# --- metadata completeness + URL domain sanity
for m in sorted((PKG / "03_GOVERNMENT_RAG/metadata").glob("*.json")):
    d = json.load(open(m, encoding="utf-8"))
    for k in ("document_id", "title", "organization", "source_url", "verification_status"):
        if not d.get(k):
            fails.append(f"{m.name}: empty {k}")
    if d["sha256"]:
        f = next(PKG.rglob(d["file_name"]), None)
        import hashlib
        if f is None or hashlib.sha256(f.read_bytes()).hexdigest() != d["sha256"]:
            fails.append(f"{m.name}: sha256 mismatch or file missing")
    elif d["official_source"]:
        warns.append(f"{m.name}: not yet downloaded")
    host = re.sub(r"^https?://", "", d["download_url"]).split("/")[0]
    if d["official_source"] and not re.search(r"(\.gov\.in|\.nic\.in|cgtmse\.in|mudra\.org\.in|tahdco\.com)$", host):
        fails.append(f"{m.name}: official doc on non-official host {host}")

# --- CSV well-formedness
for p in PKG.rglob("*.csv"):
    with open(p, encoding="utf-8", newline="") as f:
        rd = list(csv.reader(f))
    if rd and any(len(x) != len(rd[0]) for x in rd):
        fails.append(f"ragged CSV {p.relative_to(PKG)}")

print(f"FAIL: {len(fails)}  WARN: {len(warns)}")
for x in fails:
    print("FAIL", x)
for x in warns[:15]:
    print("WARN", x)
if len(warns) > 15:
    print(f"... {len(warns) - 15} more warnings")
sys.exit(1 if fails else 0)
