# Developer handoff: ONEVA official data package

## Before you start

- **All paths below are relative to `ONEVA_OFFICIAL_DATA_PACKAGE/`.**
- **Run the quality checks:** `python 05_SOURCE_REGISTER/fetch_scripts/quality_checks.py`. A non-zero exit means a hard failure. Warnings are pending page numbers and downloads.
- **Fill the gaps in two commands:**
  - `python 05_SOURCE_REGISTER/fetch_scripts/download_documents.py` downloads the originals, computes SHA-256 hashes and counts PDF pages.
  - `DATA_GOV_IN_API_KEY=… python 05_SOURCE_REGISTER/fetch_scripts/fetch_agmarknet.py --state "Tamil Nadu" --unit "<unit from resource page>"` fetches the mandi prices.
- **Golden rule:** use a value in deterministic code only if its `verification_status` is not `NOT VERIFIED`, `NEEDS HUMAN REVIEW` or `UNRESOLVED`. Always carry `source_url` and `effective_date` through to the UI.

---

## 1. `01_SIH26091_ELIGIBILITY/scheme_eligibility.csv`

1. **What it contains:** NSFDC Micro Credit Finance and Term Loan eligibility and terms, the general NSFDC eligibility rules, and the SIH brief's own assumptions kept as separate rows.
2. **Why ONEVA needs it:** it is the core of the SIH26091 Scheme Router (Module 2).
3. **Table:** `scheme_rule`
4. **Columns:** `scheme_code, beneficiary_category, income_limit_inr, project_cost_min_inr, project_cost_max_inr, loan_cap_inr, loan_share_pct, rate_pct, tenure_months, moratorium_months, moratorium_override_json, application_route, effective_from, effective_to, source_url, source_page, verification_status, confidence`
   - Parse the text columns: `interest_rate` "6.5% p.a." becomes 6.5; `repayment_period` "3 years" becomes 36 months.
   - Skip rows whose `scheme_type` starts with "Problem-statement assumption"; those are for display only.
5. **Update frequency:** monthly.
6. **Official source:** nsfdc.nic.in; pib.gov.in (MoSJE).
7. **Join keys:** `scheme_code`. The user's state picks the SCA (TN → TAHDCO).
8. **Known limitations:** no official age or activity rules; income-limit circular not sighted; see CONFLICTS C01.
9. **Safe for deterministic rules?** **YES** for the loan, rate, tenure, moratorium, project-range and ₹5 lakh income rows. **NO** for age, activities and the split of the remaining 10%.
10. **RAG only?** No. Also index the SIH brief as RAG evidence.

## 2. `02_SCHEME_PARAMETERS/scheme_parameters.csv` (+ per-scheme copies)

1. **What it contains:** 95 atomic parameters for PMMY, PMEGP, CGTMSE, NSFDC and the Udyam classification.
2. **Why ONEVA needs it:** the financial engine, alternative scheme routing and the MSME size classification.
3. **Table:** `scheme_parameter`
4. **Columns:** `scheme, parameter, value_numeric, value_text, unit, condition, effective_from, effective_to, source_url, source_document, source_page, verification_status, confidence, notes`
   - All INR values are plain rupees; no lakh or crore is stored.
   - Percentages are plain numbers with `unit` = `percent_*`.
   - Take the numeric prefix of `value` as `value_numeric`.
5. **Update frequency:** monthly for CGTMSE and NSFDC; after each Budget for PMMY, PMEGP and Udyam.
6. **Official sources:** financialservices.gov.in, mudra.org.in, msme.gov.in, kviconline.gov.in, cgtmse.in, nsfdc.nic.in, pib.gov.in.
7. **Join keys:** `(scheme, parameter)`. For CGTMSE, the borrower category joins to the coverage rows.
8. **Known limitations:** search-level verification; page numbers pending.
9. **Safe for deterministic rules?**
   - **YES** for rows with status `TWO OFFICIAL SOURCES` or `SINGLE OFFICIAL SOURCE` and confidence HIGH or MEDIUM-HIGH.
   - **NO** for rows with status `DERIVED`, `NOT VERIFIED` or `NEEDS HUMAN REVIEW`: `bank_finance_*`, `interest_rate` (MUDRA), `coverage_sc_st_and_other_special`, `scheme_validity_after_2025_26`.
   - **PMEGP negative list:** display it as text, and do not block dairy or poultry until reviewed.
10. **RAG only?** Rule-text rows (eligibility, exclusions) should be both rules and RAG evidence.

## 3. `02_SCHEME_PARAMETERS/scheme_changelog.md` + `05_SOURCE_REGISTER/CONFLICTS.csv`

1. **What they contain:** superseded values and open conflicts.
2. **Why ONEVA needs them:** so the app never serves an obsolete value.
3. **Table:** `scheme_parameter_history` (same columns as `scheme_parameter`, plus `superseded_by`) and `data_conflict`.
4. **Columns:** as in the CSV.
5. **Update frequency:** whenever parameters change.
6. **Sources:** as listed per row.
7. **Join keys:** `(scheme, parameter)`.
8. **Known limitations:** C06, C10 and C11 are unresolved or provisional.
9. **Safe for deterministic rules?** Use only `recommended_value` where the status is `RESOLVED`.
10. **RAG only?** RAG metadata: use `effective_to` to filter out stale documents.

## 4. `03_GOVERNMENT_RAG/` (metadata/*.json, rag_document_index.csv, documents/)

1. **What it contains:** 31 curated documents:
   - SIH: 1
   - NSFDC/MoSJE: 9
   - MUDRA: 4
   - PMEGP: 3
   - CGTMSE: 4
   - MSME/Udyam: 2
   - statistics: 4
   - Tamil Nadu: 4
2. **Why ONEVA needs it:** grounding for the 08-government-rag and 09-llm-assistant services.
3. **Table:** `gov_document` (+ `gov_document_chunk`)
4. **Columns:** every key in the metadata JSON, plus `effective_to` and `superseded`.
5. **Update frequency:** monthly re-run of `download_documents.py`. If a hash changes, the script keeps the old version and saves a timestamped new one.
6. **Official sources:** as per `download_url`. The script rejects any file whose final host is not official.
7. **Join keys:** `document_id`, referenced by `scheme_parameters.source_document`.
8. **Known limitations:** only D01 (the mirror) is stored now; D04 is stale by design.
9. **Safe for deterministic rules?** No. Rules come from the CSVs.
10. **RAG only?** **YES.** This is RAG evidence.

## 5. `04_MARKET_DATA/market_prices.csv` (via `fetch_agmarknet.py`)

1. **What it contains:** AGMARKNET wholesale min/max/modal prices by market and date.
2. **Why ONEVA needs it:** SIH Module 1 item 6, "Product Market Value": price context and seasonality.
3. **Table:** `mandi_price`, partitioned by date.
4. **Columns:** `commodity, variety, grade, state, district, market, lgd_district_code, market_lat, market_lon, arrival_date, min_price, max_price, modal_price, unit, raw_file_sha256, retrieval_date`
5. **Update frequency:** daily.
6. **Official source:** data.gov.in resource `9ef84268-d588-465a-a308-a864a43d0070`.
7. **Join keys:** state and district through the LGD alias table; market through geocoded distance; commodity through a curated commodity-to-category map.
8. **Known limitations:** wholesale, not retail; patchy coverage; the unit must be confirmed.
9. **Safe for deterministic rules?** Safe for displaying observed prices. **Not** for predicting "local market value" without the label "indicative".
10. **RAG only?** No. It is structured data.

## 6. `04_MARKET_DATA/purchasing_power.csv`

1. **What it contains:** HCES 2023-24 MPCE, All-India plus the highest state; Tamil Nadu placeholders.
2. **Why ONEVA needs it:** "regional purchasing power" context (SIH Module 1 item 6).
3. **Table:** `consumption_indicator`
4. **Columns:** as in the CSV, plus `lgd_state_code` and `with_imputation BOOLEAN`.
5. **Update frequency:** per HCES round.
6. **Official source:** mospi.gov.in; pib.gov.in.
7. **Join keys:** state (LGD code) × sector (rural/urban).
8. **Known limitations:** state level only; Tamil Nadu values not yet verified.
9. **Safe for deterministic rules?** Safe to display with the label **"state-level consumption indicator"**. Never use it to compute an affordability or demand score for a village.
10. **RAG only?** No.

## 7. `04_MARKET_DATA/demand_proxies.csv` + `market_intelligence_availability_matrix.csv`

1. **What they contain:** a catalogue of datasets classified by what they really measure, plus the evidence-availability matrix.
2. **Why ONEVA needs them:** an honest Module 1, with no fake demand score.
3. **Tables:** `evidence_source` and `evidence_availability` (business_category, location_level, evidence_type, status, label).
4. **Columns:** as in the CSVs.
5. **Update frequency:** when datasets are added.
6. **Official sources:** as listed per row.
7. **Join keys:** business category → NIC prefix and commodity; location → LGD codes.
8. **Known limitations:** direct village-level demand is UNAVAILABLE.
9. **Safe for deterministic rules?** Use the status and label to drive what the UI shows. Do not compute scores.
10. **RAG only?** No.

## 8. `05_SOURCE_REGISTER/udyam_join_keys.csv`

1. **What it contains:** 8 join keys between ONEVA's existing Udyam tables (`locations`, `msme_enterprises`, `nic_codes`, `location_coordinates`) and the external datasets.
2. **Why ONEVA needs it:** safe integration without buying a new MSME dataset.
3. **Tables:** `geo_alias` (source, raw_name, lgd_code) and `pincode_district_bridge` (pincode, lgd_district_code, share).
4. **Columns:** as in the CSV.
5. **Update frequency:** when a new source is added or LGD changes.
6. **Official sources:** LGD; the India Post pincode directory (data.gov.in); not yet fetched.
7. **Join keys:** as listed.
8. **Known limitations:** **pincode is many-to-many with district and village.**
9. **Safe for deterministic rules?** State and district joins on LGD codes: yes. Pincode: aggregation only.
10. **RAG only?** No.

## 9. `05_SOURCE_REGISTER/SOURCE_REGISTER.csv`, `VERIFICATION_MATRIX.xlsx`, `MISSING_DATA.csv`

1. **What they contain:** provenance for everything, the 9-sheet review workbook, and 18 open gaps.
2. **Why ONEVA needs them:** audit trail and an SIH jury demo of "no fabrication".
3. **Table:** `data_source`
4. **Columns:** as in the CSV.
5. **Update frequency:** every fetch run. `VERIFICATION_MATRIX.xlsx` is regenerated from the CSVs (`05_SOURCE_REGISTER/fetch_scripts/build_package.py`).
6. **Official sources:** not applicable (these are registers).
7. **Join keys:** `source_id` / `document_id`.
8. **Known limitations:** hash and page columns are empty until the downloads run.
9. **Safe for deterministic rules?** Not applicable.
10. **RAG only?** Not applicable.

## 10. `02_SCHEME_PARAMETERS/*` Tamil Nadu notes (in MISSING_DATA)

- The Tamil Nadu schemes UYEGP, NEEDS, AABCS and the TAHDCO schemes are listed as RAG documents D28–D31.
- Only headline values were seen: UYEGP loan up to ₹15 lakh with a 25% subsidy capped at ₹3.75 lakh; age 18–35 (general) or 18–45 (special category); AABCS 6% interest subvention for up to 10 years.
- These are **SINGLE SOURCE, SEARCH-LEVEL** and not yet in `scheme_parameters.csv`. Add them after reading the G.O.s.

## Suggested minimal Postgres DDL

```sql
CREATE TABLE scheme_parameter (
  scheme text, parameter text, value_numeric numeric, value_text text, unit text,
  condition text, effective_from date, effective_to date,
  source_url text NOT NULL, source_document text, source_page text,
  verification_status text NOT NULL, confidence text, notes text,
  PRIMARY KEY (scheme, parameter, effective_from));

CREATE TABLE mandi_price (
  commodity text, variety text, grade text, state text, district text, market text,
  lgd_district_code int, arrival_date date, min_price numeric CHECK (min_price >= 0),
  max_price numeric CHECK (max_price >= 0), modal_price numeric CHECK (modal_price >= 0),
  unit text NOT NULL, raw_file_sha256 text, retrieval_date date,
  UNIQUE (commodity, variety, grade, market, arrival_date));
```
