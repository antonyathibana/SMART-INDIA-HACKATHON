# SIH26091 eligibility report

Retrieval date: 27 September 2026. Machine-readable version: `scheme_eligibility.csv`.

## How this was verified (read first)

The collection environment's network policy blocked every `.gov.in`, `.nic.in` and `cgtmse.in` host, and the archive mirrors too. So no official page or PDF could be opened, downloaded or hashed here. Each value below was confirmed in two ways:

- The search was restricted to official domains. The value had to appear in the search extract of a named official page.
- Where possible, a second official domain was checked, for example `pib.gov.in` alongside `nsfdc.nic.in`.

Statuses therefore read "SEARCH-LEVEL". Page numbers are not recorded. Run `05_SOURCE_REGISTER/fetch_scripts/download_documents.py` on an unrestricted machine to add the original files and SHA-256 hashes.

## 1. Which schemes SIH26091 is about

The problem statement comes from the Ministry of Social Justice and Empowerment (Department of Social Justice and Empowerment). It describes two tiers of concessional loans. These match NSFDC's (National Scheduled Castes Finance and Development Corporation) published schemes:

| SIH26091 name | NSFDC name | NSFDC page |
|---|---|---|
| Micro Finance Scheme | **Micro Credit Finance** | https://nsfdc.nic.in/en/micro-credit-finance |
| Term Loan Scheme | **Term Loan** | https://nsfdc.nic.in/en/term-loan |

NSFDC also has a page called `micro-finance-scheme`, but its content could not be read. Mapping the SIH "Micro Finance Scheme" to NSFDC "Micro Credit Finance" is based on identical parameters: ₹1.40 lakh, 90%, ₹1.25 lakh, 6.5%, 3 years, 3 months. **NEEDS HUMAN REVIEW** to confirm the name mapping.

## 2. The rules in plain language

### Who can apply (both schemes)
- **Community:** The applicant must belong to a Scheduled Caste, shown by a caste certificate from the competent authority.
- **Income:** Annual family income must be **up to ₹5,00,000**, in both rural and urban areas.
  - This limit applies **from 7 January 2026**. Before that date it was ₹3,00,000, from 8 March 2018.
  - Sources: the NSFDC "About" page, plus PIB release PRID 2223171, a Ministry of Social Justice and Empowerment reply saying the limit was "revised from ₹3 lakh to ₹5 lakh with effect from 07.01.2026".
  - NSFDC's own Eligibility Criteria and FAQ pages still say ₹3 lakh. These pages are stale; see `CONFLICTS.csv` C01.
- **Age:** No official NSFDC age limit was found. Some websites claim "18–50", but none of them are official, so that claim was rejected. ONEVA must not enforce an age rule.
- **How to apply:** Applications go through the State Channelizing Agency (SCA) or another NSFDC channel partner, such as public sector banks, RRBs or NBFC-MFIs.
  - NSFDC does not accept direct applications.
  - In Tamil Nadu the SCA is **TAHDCO**.
- **Documents:**
  - Application in NSFDC's format, with business details
  - Caste certificate
  - Income certificate
  - Experience details
  - Any further SCA-specific list is NOT VERIFIED.

### Micro Credit Finance ("Micro Finance Scheme")
- **Project size:** up to ₹1,40,000.
- **Loan:** up to 90% of the project cost, capped at ₹1,25,000.
- **Interest:** 6.5% a year for the beneficiary. NSFDC charges the SCA 2.5%.
- **Repayment:** quarterly instalments, all repaid within 3 years of disbursement. The 3 years include a 3-month moratorium.

### Term Loan
- **Project size:** more than ₹1,40,000 and up to ₹50,00,000.
- **Loan:** up to 90% of the project cost, capped at ₹45,00,000.
- **Interest:** 8% a year for the beneficiary. NSFDC charges the SCA 4%.
- **Repayment:** quarterly instalments within 7 years, including the moratorium.
- **Moratorium:** 6 months. For **plantation and construction activities it is 12 months**; the SIH brief does not mention this.
- PIB PRID 2223171 says the ₹50 lakh / ₹45 lakh ceiling is "considered adequate", so no increase has been announced.

### Beneficiary contribution
- NSFDC pages only say the loan covers "up to 90%". The SIH brief assumes the other 10% is the beneficiary's own margin.
- How that remaining share is split between the beneficiary, the SCA and any subsidy is **NOT VERIFIED**. The SCA (TAHDCO) is the authority on this.

### Eligible and excluded activities
- **OFFICIAL SOURCE NOT FOUND** for an activity-level list. NSFDC only says "viable income-generating activities".
- ONEVA must not hard-block any activity on NSFDC grounds.

## 3. SIH brief compared with current official figures

| Item | SIH26091 brief | Current NSFDC | Verdict |
|---|---|---|---|
| Micro Finance project cap | ₹1.40 lakh | ₹1.40 lakh | agrees |
| Micro Finance loan | 90%, max ₹1.25 lakh | same | agrees |
| Micro Finance rate / tenure / moratorium | 6.5% / 3 y / 3 m | same | agrees |
| Term Loan project range | >₹1.40 lakh to ₹50 lakh | same | agrees |
| Term Loan loan | 90%, max ₹45 lakh | same | agrees |
| Term Loan rate / tenure / moratorium | 8% / 7 y / 6 m | 8% / 7 y / 6 m (12 m for plantation/construction) | brief simplified |
| Income ceiling | not stated | ₹5 lakh from 07-01-2026 | brief silent: ONEVA must add it |
| Beneficiary category | "marginalized communities" | Scheduled Castes | brief is broader: ONEVA must restrict NSFDC routing to SC |

## 4. Arithmetic trap in the brief (CALCULATED)

The brief says Project Cost = Margin ÷ 10% and Loan = 90% of Project Cost. That formula ignores the ₹1.25 lakh cap:

- 90% of ₹1,40,000 is ₹1,26,000, which is **more than the ₹1,25,000 cap**.
- The cap starts to bind at a project cost of ₹1,25,000 ÷ 0.9 = **₹1,38,888.89**.
- For a project cost between ₹1,38,889 and ₹1,40,000:
  - the loan is ₹1,25,000;
  - the beneficiary share is (cost − ₹1,25,000), which is slightly more than 10%.

Recommended deterministic rule (for the 06-scheme-router):

```
if caste != SC or family_income > 500000: not NSFDC-eligible
if project_cost <= 140000: scheme = MCF;  loan = min(0.90*cost, 125000); rate=6.5; tenure_m=36; morat_m=3
elif project_cost <= 5000000: scheme = TL; loan = min(0.90*cost, 4500000); rate=8.0; tenure_m=84
                              morat_m = 12 if activity in {plantation, construction} else 6
else: not eligible under NSFDC MCF/TL
```

## 5. Items marked NEEDS HUMAN REVIEW
- Mapping the SIH "Micro Finance Scheme" name to NSFDC "Micro Credit Finance".
- The board circular behind the ₹5 lakh income limit, and whether TAHDCO has adopted it.
- How the remaining 10% is split.
- The NSFDC activity list.
- The official SIH26091 listing on sih.gov.in. The brief text used here comes from an unofficial GitHub mirror, stored with its SHA-256 in `source_documents/`.
