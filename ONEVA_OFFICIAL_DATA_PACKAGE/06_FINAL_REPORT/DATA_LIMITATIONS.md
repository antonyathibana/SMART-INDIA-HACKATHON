# Data limitations

## 1. Access limitations
- The collection environment blocked all official government hosts (HTTP 403 from the egress proxy).
- Values were verified from official-domain search extracts, not from the original documents.
- Consequences:
  - no official file downloaded;
  - no SHA-256 hash;
  - no page number;
  - PDF annexures and footnotes not inspected.
- Search extracts are machine summaries. They can compress or mis-group clauses; the CGTMSE SC/ST coverage is a known example.
- The SIH26091 text comes from an **unofficial** GitHub scrape (dated 22-08-2026) of sih.gov.in. It is stored with its hash, but its official status is unconfirmed.

## 2. Scheme-data limitations
- Most NSFDC scheme pages have no publication or effective date. Rates are "current as of 27-09-2026", not "effective from".
- NSFDC's own site is internally inconsistent: ₹3 lakh on the Eligibility and FAQ pages, ₹5 lakh on the About page. PIB confirms ₹5 lakh from 07-01-2026.
- SCAs such as TAHDCO may add their own conditions: documents, activity lists, own-share rules. None of these were collected.
- PMEGP details (moratorium, collateral rules) vary by bank.
- It is unconfirmed whether PMEGP continues beyond FY 2025-26.
- MUDRA interest rates are set by each lender and are not published centrally.
- CGTMSE: only CGS-I (for banks) was covered. CGS-II (NBFCs) and the co-lending scheme (CGSCL) were not.

## 3. Statistical-data limitations
- **HCES** is a sample survey. Published tables stop at state × rural/urban level. District or village figures would need the unit-level data plus design-based estimation, and small-area estimates are statistically unreliable.
- **BAHS** gives state production figures, not consumption or demand.
- **AGMARKNET** gives wholesale prices at reporting regulated markets. Coverage is uneven, and a missing record is not a zero price.
- **Census 2011** population is 15 years old.
- **Udyam** counts registrations only. They are not active businesses, and informal enterprises are missing. Retail traders only became eligible to register in 2021.

## 4. Geography limitations
- **Pincode is not a geographic identifier.** One pincode can cover several villages, blocks or even districts, and one village can have several pincodes. Use a many-to-many bridge table.
- District names differ between datasets, and Tamil Nadu has created new districts since 2011. Join on LGD codes through an alias table.
- AGMARKNET markets are not LGD units, so use geocoded distances.
- PMEGP's "rural" definition is not the same as the Census definition of rural.

## 5. Licensing
- data.gov.in datasets are expected to fall under the Government Open Data License – India. **Verify on each resource page** (NEEDS HUMAN REVIEW).
- Government PDFs are included for reference and RAG retrieval. Show citations, and do not present the documents as ONEVA's own content.
- The SIH mirror repository has no stated licence. The problem-statement text is a public government listing.
