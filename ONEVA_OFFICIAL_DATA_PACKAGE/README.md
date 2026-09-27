# ONEVA official data package (SIH26091)

This package holds the official scheme rules, source documents and market data that ONEVA needs. Collected 27 September 2026.

- **Start here:** `06_FINAL_REPORT/DEVELOPER_HANDOFF.md`.
- **Read before trusting any number:** `06_FINAL_REPORT/DATA_COLLECTION_REPORT.md` §0.
  - The collection environment blocked every government host.
  - So values are verified at *official-domain search* level. No original file has been downloaded or hashed yet.
  - One exception: the SIH brief, taken from an unofficial mirror.

## Key findings
- The NSFDC income ceiling is now **₹5,00,000** (was ₹3,00,000), effective **07-01-2026**. The SIH brief does not mention any income ceiling.
- SIH26091's "Micro Finance Scheme" is NSFDC **Micro Credit Finance**. Its loan must be capped: `min(0.9 × cost, ₹1,25,000)`.
- NSFDC Term Loan terms are unchanged: 8% interest, 7 years, 6-month moratorium (12 months for plantation or construction).
- PMMY has a new **Tarun Plus** tier, up to ₹20 lakh, since 24-10-2024.
- The CGTMSE guarantee ceiling is **₹10 crore** from 01-04-2025, with a new fee table.
- New Udyam classification limits apply from 01-04-2025.

## Filling the gaps (on a machine with open network access)
```bash
pip install requests pypdf openpyxl
python 05_SOURCE_REGISTER/fetch_scripts/download_documents.py      # originals + sha256 + page counts
DATA_GOV_IN_API_KEY=... python 05_SOURCE_REGISTER/fetch_scripts/fetch_agmarknet.py --state "Tamil Nadu" --unit "<unit from resource page>"
python 05_SOURCE_REGISTER/fetch_scripts/quality_checks.py          # Part N checks; exit 1 on failure
```
