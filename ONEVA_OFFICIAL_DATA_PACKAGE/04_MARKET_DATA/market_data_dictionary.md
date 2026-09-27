# Market data dictionary

The labels used throughout this folder:

- `OFFICIAL STATISTIC`: a published government number.
- `DERIVED`: arithmetic on official numbers.
- `Observed`: directly measured.
- `Proxy`: an indirect indicator.
- `Unavailable`: no official source.

No file here contains a demand score. None should ever be computed from these files.

## market_prices.csv
**Status: header only (0 rows).**

- The collection environment blocked `api.data.gov.in` and `agmarknet.gov.in`.
- The API also needs a personal key.
- Rows are produced by `05_SOURCE_REGISTER/fetch_scripts/fetch_agmarknet.py`, which keeps every raw JSON page in `04_MARKET_DATA/raw_agmarknet/`.

| column | type | meaning |
|---|---|---|
| commodity | text | Commodity name exactly as AGMARKNET publishes it (no renaming) |
| state, district, market | text | As published. Join through the LGD alias table, not raw text |
| date | ISO date | `arrival_date` converted from dd/mm/yyyy |
| minimum_price, maximum_price, modal_price | number ≥ 0 | Wholesale prices at that market that day. The modal price is the most common transaction price |
| unit | text | **Must be copied from the resource description on data.gov.in** (the script refuses to run without `--unit`). No conversion is applied |
| source | text | "AGMARKNET via OGD Platform India (resource 9ef84268-…)" |
| source_url | URL | data.gov.in resource page |
| retrieval_date | ISO date | Date the script ran |

- **API resource ID:** `9ef84268-d588-465a-a308-a864a43d0070`.
  - This ID comes from public GitHub client code, not from the resource page, which could not be reached.
  - Confirm it on the first live call.
- **Field names:** `state, district, market, commodity, variety, grade, arrival_date, min_price, max_price, modal_price`. These were confirmed from the same client code.
- **Licence:** expected to be the Government Open Data License – India. **Verify on the resource page**; status is NEEDS HUMAN REVIEW until then.
- **Limitations:** these are wholesale regulated-market prices, not retail prices. Coverage depends on which markets report. A missing day means "not reported", not a zero price.

## purchasing_power.csv
- Source: MoSPI Household Consumption Expenditure Survey (HCES) 2023-24.
- The indicator is MPCE (monthly per-capita consumption expenditure, ₹ per person per month).
- It is reported "with" and "without" the imputed value of free items received from welfare schemes. Store both; never mix them in one comparison.
- `geography_level` is `country` or `state`. **This is a state-level consumption indicator.** It must never be shown as village or district purchasing power.
- Tamil Nadu rows are present but empty (`NOT VERIFIED`). The official state table could not be read. A value seen on a non-official aggregator was deliberately **not** stored.

## demand_proxies.csv
This file is a catalogue of datasets. For each one it records:
- `measures_actual_demand` (YES / NO / PARTIAL);
- `classification`: PRODUCTION, CONSUMPTION, MARKET ACTIVITY, CREDIT ACTIVITY, SUPPLY/COMPETITION, POPULATION, ECONOMIC INDICATOR or UNAVAILABLE.

The few example values it holds are OFFICIAL STATISTICs, each with its source.

- **Production (BAHS) is never demand.**
- **Market arrivals are never consumer demand.**
- **Direct village-level consumer demand is `UNAVAILABLE`.**

## market_intelligence_availability_matrix.csv
This matrix implements Part J. For each business and location it lists every evidence type with:
- `status`: AVAILABLE, NOT COLLECTED or UNAVAILABLE;
- `label`: Observed, Derived, Proxy or Unavailable.

The UI should render this list as it is, for example "Evidence-based market context: 4 of 6 evidence types available", instead of a score.

## Suggested labels in the UI
| data | UI label |
|---|---|
| Udyam same-NIC count | "Registered similar enterprises (Udyam) – observed" |
| AGMARKNET modal price | "Wholesale mandi price, <market>, <date> – official" |
| HCES MPCE | "State-level consumption indicator (HCES 2023-24) – not village-specific" |
| BAHS production | "State production (not demand)" |
| Anything missing | "No official data available" |
