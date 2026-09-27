# ONEVA official data collection report (SIH26091)

- Collection date: 27 September 2026.
- Areas covered: (5) SIH26091 eligibility, (6) MUDRA / PMEGP / CGTMSE parameters, (7) government RAG library, (9) market, demand and purchasing-power data.

## 0. Collection constraint (affects everything below)

The cloud environment used for this collection has an egress policy. It returned **HTTP 403 for every government host tried**:

- nsfdc.nic.in, socialjustice.gov.in, financialservices.gov.in, mudra.org.in
- msme.gov.in, kviconline.gov.in, cgtmse.in
- data.gov.in, api.data.gov.in, mospi.gov.in, udyamregistration.gov.in
- sih.gov.in, agmarknet.gov.in, *.tn.gov.in
- also web.archive.org

The only working channels were:
- **web search restricted to official domains**;
- GitHub, used only to retrieve an *unofficial mirror* of the SIH problem statement and public API client code.

What this means:

- No official PDF or page was downloaded. So there is **no SHA-256 hash and no page number** for any official value yet.
- Every official value is labelled with one of these statuses:
  - `OFFICIAL-DOMAIN SEARCH VERIFIED`: the value appeared in the search extract of a named official page.
  - `TWO OFFICIAL SOURCES (SEARCH-LEVEL)`: two official pages or domains agree. Sometimes these are two pages of the same organisation, e.g. the KVIC FAQ and the KVIC guidelines.
  - `SINGLE OFFICIAL SOURCE VERIFIED (SEARCH-LEVEL)`.
- Search extracts are machine summaries of the page text. They can mis-group items; that is exactly why CGTMSE SC/ST coverage is marked UNRESOLVED. Treat SEARCH-LEVEL as strong but **not final**.
- `05_SOURCE_REGISTER/fetch_scripts/download_documents.py` closes the gap. On an unrestricted network it downloads all 30 official documents, checks the file type, counts PDF pages and fills in the SHA-256 in each metadata JSON.

## Section 1: What was successfully collected
| Deliverable | Content |
|---|---|
| `01/scheme_eligibility.csv` | 5 rows: NSFDC MCF, NSFDC Term Loan, NSFDC general eligibility, and both SIH-brief tiers kept as separate "assumption" rows |
| `01/source_documents/` | SIH 2026 problem-statement dataset (GitHub mirror, original file plus SHA-256) and a processed SIH26091 extract |
| `02/scheme_parameters.csv` | 95 parameters: PMMY 17, PMEGP 30, CGTMSE 22, NSFDC 20, Udyam classification 6. Split copies are in `mudra/ pmegp/ cgtmse/ nsfdc/` |
| `02/scheme_changelog.md` | 10 changed values with old and new sources |
| `03/metadata/*.json`, `rag_document_index.csv` | 31 curated documents (1 mirror file stored; 30 official, pending download) |
| `04/purchasing_power.csv` | 6 official HCES 2023-24 values (All-India and Sikkim) plus 2 Tamil Nadu placeholders marked NOT VERIFIED |
| `04/demand_proxies.csv` | 9 datasets, each classified by what it actually measures |
| `04/market_intelligence_availability_matrix.csv` | Part J evidence matrix for 4 example business/location pairs |
| `04/market_prices.csv` | header only; fetch script provided |
| `05/SOURCE_REGISTER.csv`, `CONFLICTS.csv` (12), `MISSING_DATA.csv` (18), `udyam_join_keys.csv` (8), `VERIFICATION_MATRIX.xlsx` (9 sheets) | |
| `05/fetch_scripts/` | `download_documents.py`, `fetch_agmarknet.py`, `quality_checks.py` |

## Section 2: What was verified from official primary sources (search-level)

- **NSFDC:**
  - Micro Credit Finance: ₹1.40 lakh project, 90% loan up to ₹1.25 lakh, 6.5% (2.5% to SCA), 3 years including a 3-month moratorium, quarterly repayment.
  - Term Loan: >₹1.40 lakh to ₹50 lakh project, 90% loan up to ₹45 lakh, 8% (4% to SCA), 7 years including a 6-month moratorium (12 months for plantation/construction).
  - SC-only eligibility.
  - **Income ≤ ₹5 lakh w.e.f. 07-01-2026.**
  - Applications go through SCAs only.
- **PMMY:**
  - Shishu up to ₹50k; Kishor up to ₹5 lakh; Tarun up to ₹10 lakh; Tarun Plus up to ₹20 lakh (w.e.f. 24-10-2024, only for borrowers who repaid a Tarun loan).
  - Collateral-free; CGFMU guarantee.
  - Lent through MLIs; MUDRA only refinances.
  - Non-farm plus allied-agriculture activities; term loans and working capital.
- **PMEGP:**
  - Project caps: ₹50 lakh manufacturing, ₹20 lakh service.
  - Age above 18; no income ceiling; class VIII pass needed above ₹10 lakh (manufacturing) or ₹5 lakh (service).
  - Subsidy: 15/25% general (urban/rural), 25/35% special category.
  - Own contribution: 10% general, 5% special.
  - New units only; one per family; 3-year TDR lock-in; repayment 3–7 years.
  - EDP training rules and a negative list.
  - 2nd-loan rules: ₹1 cr / ₹25 lakh project, 15% subsidy (20% NER/Hill), 10% own contribution.
- **CGTMSE:**
  - Ceiling ₹10 cr from 01-04-2025.
  - Annual Guarantee Fee slab table from 01-04-2025.
  - Coverage: micro ≤ ₹5 lakh 85%; women 90% (Circular 241); NER/J&K/Ladakh 80%; others 75%; +5 points in credit-deficient districts; transgender 85%.
  - Guarantee tenure rules; Udyam registration mandatory; retail traders eligible; agriculture and SHGs excluded.
- **Udyam classification (from 01-04-2025):** micro ₹2.5 cr / ₹10 cr; small ₹25 cr / ₹100 cr; medium ₹125 cr / ₹500 cr.
- **HCES 2023-24:**
  - All-India MPCE: rural ₹4,122, urban ₹6,996 (with imputation: ₹4,247 and ₹7,078).
  - Highest state, Sikkim: rural ₹9,377, urban ₹13,927.
- **BAHS 2025 (2024-25 reference period):** Tamil Nadu produces 15.63% of India's eggs; India's meat output is 10.50 million tonnes.
- **PMMY after 11 years (PIB, April 2026):** 52 crore+ loans worth ₹32.61 lakh crore.

## Section 3: What was cross-checked (two independent official sources)
- NSFDC income limit: nsfdc.nic.in (About page) and pib.gov.in (MoSJE reply). socialjustice.gov.in also states ₹5 lakh.
- NSFDC Term Loan ceiling: nsfdc.nic.in and pib.gov.in.
- NSFDC MCF/TL rates, tenure and moratorium: nsfdc.nic.in and the SIH26091 brief (MoSJE). Note that the brief was read through an unofficial mirror.
- PMMY categories and Tarun Plus: mudra.org.in, financialservices.gov.in and pib.gov.in.
- PMEGP caps, subsidy and contribution: kviconline FAQ, the revised guidelines PDF listing, and msme.gov.in. The special-category subsidy is also confirmed by PIB.
- PMEGP 2nd loan: msme.gov.in and kviconline PDFs.
- CGTMSE ceiling: CGTMSE Circular 250 and PIB.
- Udyam limits: PIB and msme.gov.in.

## Section 4: What remains uncertain
The full list is in `CONFLICTS.csv` and `MISSING_DATA.csv`. The main items:

- CGTMSE SC/ST coverage: 85% or 90% (**UNRESOLVED**).
- PMEGP continuation after FY 2025-26 (**UNRESOLVED**).
- PMEGP definition of "family" (resolved provisionally as "self and spouse").
- The circular behind NSFDC's income-limit change, and whether SCAs have adopted it.
- NSFDC: age rule (none found), activity lists, and how the remaining 10% is split.
- Tamil Nadu HCES values.
- Every page number and file hash.
- Whether PMEGP's negative list still blocks dairy and poultry (animal husbandry): **NEEDS HUMAN REVIEW** before ONEVA uses it to block those activities.

## Section 5: What should be integrated into ONEVA
1. **06-scheme-router:** the NSFDC MCF/TL rules and income ceiling (the rule pseudo-code is in `SIH26091_ELIGIBILITY_REPORT.md` §4), plus PMMY categories as an alternative route. Store `effective_date` and `source_url` with each rule.
2. **05-financial-engine:**
   - Apply the loan cap `min(0.9 × cost, cap)`.
   - Quarterly EMI over (tenure − moratorium).
   - Record which interest method is used during the moratorium. The NSFDC treatment of interest during the moratorium is NOT VERIFIED, so show it as an assumption.
3. **08-government-rag:** index the 30 official documents after download. Give D04 (the stale ₹3 lakh page) `effective_to = 2026-01-06`.
4. **03-market-intelligence:** show the availability matrix instead of any score. Fetch AGMARKNET prices daily. Show HCES values with the "state-level consumption indicator" label.
5. **PMEGP and CGTMSE:** use as informational routes, with the confidence flags from the CSV.

## Section 6: What must NOT be represented as an official fact
- Any MUDRA interest rate. Rates are set by each lender.
- NSFDC age limits, e.g. "18–50". The source is non-official.
- CGTMSE SC/ST coverage percentage.
- The split of the non-loan 10% under NSFDC, beyond "loan up to 90%".
- The PMEGP moratorium length.
- Any Tamil Nadu MPCE figure.
- Any "demand", "market size" or "purchasing power" at village or block level.
- Production (BAHS) or market arrivals presented as demand.
- DERIVED old Udyam limits, and PMEGP bank-finance shares of 90%/95%.
- The SIH brief's formula without the ₹1.25 lakh cap.
- Anything from the SIH mirror beyond "this is what the problem statement says".

## Section 7: Recommended update schedule
| Data | Frequency | Trigger |
|---|---|---|
| AGMARKNET prices | daily (or weekly, for a demo) | cron job running `fetch_agmarknet.py` |
| NSFDC scheme pages and income limit | monthly | page hash change detected by `download_documents.py` |
| CGTMSE circulars | monthly | new circular number on cgtmse.in/Circulars |
| PMMY / PMEGP | quarterly, and after each Union Budget (1 Feb) | Budget speech / PIB |
| Udyam classification | yearly, after the Budget | Gazette notification |
| HCES | when the next survey round is released | MoSPI release |
| BAHS | yearly (usually November, National Milk Day) | DAHD release |
| TN schemes (UYEGP/NEEDS/AABCS, TAHDCO) | after the TN Budget (usually Feb–Mar) | G.O. issued |
