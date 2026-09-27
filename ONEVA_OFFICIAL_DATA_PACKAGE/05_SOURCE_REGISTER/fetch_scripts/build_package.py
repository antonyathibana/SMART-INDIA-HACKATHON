"""Generates the ONEVA_OFFICIAL_DATA_PACKAGE structured files (CSVs, metadata JSON, VERIFICATION_MATRIX.xlsx).

The CSVs are canonical; edit values here and re-run: python 05_SOURCE_REGISTER/fetch_scripts/build_package.py
WARNING: re-running resets metadata JSON download fields; run download_documents.py afterwards.

All values below were collected on 2026-09-27 via official-domain-restricted
web search (the session's network policy blocked direct access to every
.gov.in / .nic.in host, so original PDFs/pages could not be opened or hashed).
"""
import csv, json, hashlib, os, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # ONEVA_OFFICIAL_DATA_PACKAGE/
RD = "2026-09-27"

# Verification vocabulary (documented in DATA_COLLECTION_REPORT.md)
SV = "OFFICIAL-DOMAIN SEARCH VERIFIED"          # seen in search extract of an official-domain page; original not opened
SV2 = "TWO OFFICIAL SOURCES (SEARCH-LEVEL)"      # two independent official domains agree at search level
SINGLE = "SINGLE OFFICIAL SOURCE VERIFIED (SEARCH-LEVEL)"
NV = "NOT VERIFIED"
NHR = "NEEDS HUMAN REVIEW"
NOPAGE = "NOT RECORDED - original not opened (egress blocked)"

for d in ["01_SIH26091_ELIGIBILITY/source_documents",
          "02_SCHEME_PARAMETERS/mudra", "02_SCHEME_PARAMETERS/pmegp",
          "02_SCHEME_PARAMETERS/cgtmse", "02_SCHEME_PARAMETERS/nsfdc",
          "03_GOVERNMENT_RAG/documents", "03_GOVERNMENT_RAG/metadata",
          "04_MARKET_DATA", "05_SOURCE_REGISTER/fetch_scripts", "06_FINAL_REPORT"]:
    (ROOT / d).mkdir(parents=True, exist_ok=True)


def write_csv(path, cols, rows):
    with open(ROOT / path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="raise")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


# ---------------------------------------------------------------- URLs
U = dict(
    sih="https://sih.gov.in/sih2026PS",
    sih_mirror="https://github.com/NoBugNinja/Smart-India-Hackathon-SIH-2026-Problem-Statements/blob/ee69e2d423689f806e06c57c09e99953cebadadb/data/sih2026_ps_20260822_211225.json",
    nsfdc_tl="https://nsfdc.nic.in/en/term-loan",
    nsfdc_mcf="https://nsfdc.nic.in/en/micro-credit-finance",
    nsfdc_mfs="https://nsfdc.nic.in/en/micro-finance-scheme",
    nsfdc_elig="https://www.nsfdc.nic.in/en/eligibility-criteria",
    nsfdc_faq="https://nsfdc.nic.in/en/faq?link=out",
    nsfdc_about="https://nsfdc.nic.in/en/about-nsfdc",
    nsfdc_apply="https://nsfdc.nic.in/en/how-to-apply",
    nsfdc_scas="https://nsfdc.nic.in/channel-patrners/scas",
    nsfdc_suvidha="https://nsfdc.nic.in/en/suvidha-loan",
    nsfdc_dash="https://nsfdc.nic.in/en/schemes-dashboard",
    pib_nsfdc_income="https://www.pib.gov.in/PressReleasePage.aspx?PRID=2223171",
    mosje_nsfdc="https://socialjustice.gov.in/schemes/34",
    mosje_nsfdc_old="https://socialjustice.gov.in/writereaddata/UploadFile/About_NSFDC_08_2021.pdf",
    dfs_pmmy="https://www.financialservices.gov.in/pradhan-mantri-mudra-yojana-pmmy",
    mudra_off="https://www.mudra.org.in/offerings",
    mudra_faq="https://mudra.org.in/FAQ",
    mudra_sf="https://www.mudra.org.in/Default/DownloadFile/MudraLoan-SalientFeatures-English.pdf",
    mudra_how="https://www.mudra.org.in/Default/DownloadFile/How_and_Where_to_get_MUDRA_loan.pdf",
    pib_tarunplus="https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=2068019",
    pib_tarunplus_pdf="https://static.pib.gov.in/WriteReadData/specificdocs/documents/2024/oct/doc20241029426401.pdf",
    pib_mudra11="https://static.pib.gov.in/WriteReadData/specificdocs/documents/2026/apr/doc202648842601.pdf",
    pmegp_rev="https://msme.gov.in/sites/default/files/Revisedguidelines07.12.2023.pdf",
    pmegp_rev_kvic="https://www.kviconline.gov.in/pmegpeportal/dashboard/notification/Revised_PMEGP_Scheme_Guidelines_07122023_compressed.pdf",
    pmegp_2022="https://www.kviconline.gov.in/pmegpeportal/dashboard/notification/PMEGP_Guidelines_Certified_2022_3.pdf",
    pmegp_elig_msme="https://www.msme.gov.in/eligibility-criteria-pmegp-scheme",
    pmegp_elig_kvic="https://www.kviconline.gov.in/pmegpeportal/jsp/eligibility_criteria.jsp",
    pmegp_faq="https://www.kviconline.gov.in/pmegpeportal/jsp/FAQ.jsp",
    pmegp_2nd="https://msme.gov.in/sites/default/files/2ndloanenglishguidelines.pdf",
    pmegp_2nd_kvic="https://www.kviconline.gov.in/pmegpeportal/pmegpIILOAN/PMEGP.pdf",
    pmegp_edpfaq="https://www.kviconline.gov.in/pmegpeportal/pmegphome/EDPFAQ.pdf",
    pmegp_portal="https://pmegp.msme.gov.in/Home/HomePage",
    pib_pmegp_sc="https://www.pib.gov.in/PressReleasePage.aspx?PRID=2158990",
    cg_doc="https://www.cgtmse.in/Default/ViewFile/?id=1743176302611_CGTMSE+-+Scheme+Document+CGS+I_updated+as+on+Apr+1+2025.pdf&path=Page",
    cg_250="https://www.cgtmse.in/Default/ViewFile/?id=1742382157365_Circular+No.+2502024-25+5cr+to+10+cr.pdf&path=Circular",
    cg_251="https://cgtmse.in/Default/ViewFile/?id=1742382368090_Circular+No.2512024-25+reduction+in+AGF.pdf&path=Circular",
    cg_241="https://www.cgtmse.in/Default/ViewFile/?id=1734171815262_Circular+241-+enhancement+in+extent+of+coverage+for+women+entrepreneurs%5B90%5D.pdf&path=Circular",
    cg_220="https://cgtmse.in/Default/ViewFile/?id=1680282300234_Circular+No.+220_Increase+in+ceiling+of+Coverage.pdf&path=Circular",
    cg_elig="https://www.cgtmse.in/Home/VS/95",
    cg_fac="https://www.cgtmse.in/Home/VS/96",
    cg_agf="https://www.cgtmse.in/Home/VS/98",
    cg_cover="https://www.cgtmse.in/Home/VS/99",
    cg_circ="https://www.cgtmse.in/Circulars",
    cg_ar="https://www.cgtmse.in/Default/ViewFile/CGTMSE-AR-2024-25-english.pdf?path=AnnualReport",
    msme_cgs="https://msme.gov.in/sites/default/files/CredirGuranteeFundScheme_1.pdf",
    pib_cgs_rural="https://www.pib.gov.in/PressNoteDetails.aspx?NoteId=158608&ModuleId=3",
    pib_msme_class="https://www.pib.gov.in/PressReleasePage.aspx?PRID=2098389",
    pib_msme_class2="https://www.pib.gov.in/PressReleasePage.aspx?PRID=2220403",
    msme_class_gaz="https://www.msme.gov.in/whatsnew/new-criteria-classification-micro-small-and-medium-enterprises-gazette-notification-1st",
    msme_ar="https://www.msme.gov.in/static/uploads/2026/05/1bfda06b460e72543530b40817573495.pdf",
    hces_pn="https://www.mospi.gov.in/sites/default/files/press_release/HCES_Press_Note_2023-24_27122024_rev.pdf",
    hces_pib="https://www.pib.gov.in/PressReleasePage.aspx?PRID=2097601",
    hces_report="https://www.mospi.gov.in/sites/default/files/publication_reports/Final_Report_HCES_2023-24L.pdf",
    hces_pn2="https://mospi.gov.in/sites/default/files/press_release/HCES_Report202324_Press_Note_30012025.pdf",
    ogd_mandi="https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi",
    ogd_mandi_api="https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070",
    ogd_variety="https://www.data.gov.in/resource/variety-wise-daily-market-prices-data-commodity",
    bahs="https://dahd.gov.in/sites/default/files/2025-12/BasicAnimalHusbandryStatistics2025.pdf",
    bahs_pib="https://www.pib.gov.in/PressReleasePage.aspx?PRID=2195049",
    tn_uyegp="https://www.msmetamilnadu.tn.gov.in/uyegp.php",
    tn_aabcs="https://msmeonline.tn.gov.in/aabcs/aabcs_desc.php",
    tn_aabcs_go="https://msmeonline.tn.gov.in/aabcs/pdf/aabcs_go.pdf",
    tn_needs="https://msmeonline.tn.gov.in/needs/",
    tahdco="https://tahdco.com/schemes",
    tn_des="https://des.tn.gov.in/en/node/32",
    tn_des_income="https://des.tn.gov.in/en/node/20",
    udyam="https://udyamregistration.gov.in",
    udyamimitra="https://www.udyamimitra.in",
)

# ================================================================ PART A
EL_COLS = ["scheme", "scheme_type", "beneficiary_category", "income_limit", "income_period",
           "age_requirement", "project_cost_min", "project_cost_max", "maximum_loan",
           "beneficiary_contribution", "interest_rate", "repayment_period", "moratorium",
           "eligible_activities", "excluded_activities", "application_route", "implementing_agency",
           "required_documents", "effective_date", "source_organization", "source_title",
           "source_url", "source_document_url", "source_page", "source_section", "retrieval_date",
           "verification_status", "confidence", "notes"]

common_nsfdc = dict(
    beneficiary_category="Scheduled Caste (SC) persons",
    income_limit="500000",
    income_period="annual family income (INR), rural and urban alike",
    age_requirement="NOT VERIFIED - no official NSFDC age limit found for credit schemes (third-party sites claiming 18-50 rejected as non-official)",
    eligible_activities="Viable income-generating activities (NSFDC generic wording); activity-level list OFFICIAL SOURCE NOT FOUND",
    excluded_activities="OFFICIAL SOURCE NOT FOUND",
    application_route="Apply through the State Channelizing Agency (SCA) of the state or other NSFDC Channel Partners (PSBs, RRBs, NBFC-MFIs etc.). NSFDC does not entertain direct applications. Tamil Nadu SCA: TAHDCO.",
    implementing_agency="NSFDC (Dept. of Social Justice & Empowerment, MoSJE) via SCAs/CAs",
    required_documents="Application in NSFDC format with business details; Caste certificate (competent authority); Income certificate (competent authority); experience certificate/details. Further SCA-specific documents NOT VERIFIED.",
    source_organization="National Scheduled Castes Finance and Development Corporation (NSFDC)",
    retrieval_date=RD,
    source_page=NOPAGE,
)

eligibility = [
    dict(common_nsfdc,
         scheme="NSFDC Micro Credit Finance (SIH26091 'Micro Finance Scheme')",
         scheme_type="Concessional loan - micro credit",
         project_cost_min="0", project_cost_max="140000",
         maximum_loan="125000 (= min(90% of project cost, 125000))",
         beneficiary_contribution="Balance of project cost not funded by NSFDC loan (>=10%; >10% when the 1.25 lakh cap binds, i.e. project cost > 138889). Split between beneficiary/SCA share/subsidy is NOT VERIFIED; SIH brief assumes all of it is beneficiary margin.",
         interest_rate="6.5% p.a. to beneficiary (NSFDC charges SCA/CA 2.5%)",
         repayment_period="Max 3 years from disbursement, quarterly instalments (includes moratorium)",
         moratorium="3 months",
         effective_date="Rates: date NOT VERIFIED (current on NSFDC site as of 2026-09-27); income limit w.e.f. 2026-01-07",
         source_title="Micro Credit Finance (NSFDC scheme page); income: About NSFDC + PIB PRID 2223171",
         source_url=U["nsfdc_mcf"],
         source_document_url=U["pib_nsfdc_income"] + " ; " + U["nsfdc_about"],
         source_section="Scheme page body: 'Loan', 'Interest', 'Repayment'",
         verification_status=SV2 + " for loan terms (nsfdc.nic.in + SIH26091 brief agree); income limit " + SV2 + " (nsfdc.nic.in About + pib.gov.in)",
         confidence="HIGH (loan terms) / MEDIUM-HIGH (income limit: internal NSFDC page conflict, see CONFLICTS.csv C01)",
         notes="NSFDC names this scheme 'Micro Credit Finance'; SIH26091 calls it 'Micro Finance Scheme'. A separate nsfdc.nic.in page 'micro-finance-scheme' exists but its content could not be read; treat name-mapping as NEEDS HUMAN REVIEW. Income limit raised 3.00->5.00 lakh w.e.f. 07.01.2026; NSFDC Eligibility/FAQ pages still show 3.00 lakh (stale)."),
    dict(common_nsfdc,
         scheme="NSFDC Term Loan",
         scheme_type="Concessional loan - term loan",
         project_cost_min="140001 (project cost 'more than 1.40 lakh')",
         project_cost_max="5000000",
         maximum_loan="4500000 (= 90% of project cost, loan 'above 1.25 lakh and up to 45 lakh')",
         beneficiary_contribution="Balance of project cost (>=10%). Official split NOT VERIFIED; SIH brief assumes 10% beneficiary margin.",
         interest_rate="8% p.a. to beneficiary (NSFDC charges SCA/CA 4%)",
         repayment_period="Max 7 years, quarterly instalments (includes moratorium)",
         moratorium="6 months (12 months for plantation and construction activities)",
         effective_date="Rates: date NOT VERIFIED (current on NSFDC site as of 2026-09-27); income limit w.e.f. 2026-01-07",
         source_title="Term Loan (NSFDC scheme page); income: About NSFDC + PIB PRID 2223171",
         source_url=U["nsfdc_tl"],
         source_document_url=U["pib_nsfdc_income"] + " ; " + U["nsfdc_about"],
         source_section="Scheme page body: 'Loan', 'Interest', 'Repayment'",
         verification_status=SV2 + " (nsfdc.nic.in + pib.gov.in for 50 lakh/45 lakh; SIH26091 brief agrees on 8%/7y/6m)",
         confidence="HIGH",
         notes="PIB PRID 2223171 (MoSJE, Parliament reply) states the Rs 50 lakh project / Rs 45 lakh loan ceiling is 'considered adequate' - i.e. no enhancement. 12-month moratorium for plantation/construction is NOT in the SIH brief."),
    dict(scheme="NSFDC - general eligibility (all credit schemes)",
         scheme_type="Eligibility rule",
         beneficiary_category="Scheduled Caste; valid caste certificate",
         income_limit="500000", income_period="annual family income (INR), rural and urban",
         age_requirement=common_nsfdc["age_requirement"],
         project_cost_min="", project_cost_max="",
         maximum_loan="Scheme-specific; NSFDC funds up to 90% of project cost (VETLS up to 100%)",
         beneficiary_contribution="Scheme-specific", interest_rate="Scheme-specific",
         repayment_period="Scheme-specific", moratorium="Scheme-specific",
         eligible_activities=common_nsfdc["eligible_activities"],
         excluded_activities="OFFICIAL SOURCE NOT FOUND",
         application_route=common_nsfdc["application_route"],
         implementing_agency=common_nsfdc["implementing_agency"],
         required_documents=common_nsfdc["required_documents"],
         effective_date="2026-01-07 (income limit 5.00 lakh). Previous: 3.00 lakh w.e.f. 2018-03-08",
         source_organization="NSFDC; Ministry of Social Justice & Empowerment (via PIB)",
         source_title="About NSFDC; Eligibility Criteria; FAQ; How to Apply; PIB 'Increase in the provision of loans to Scheduled Castes'",
         source_url=U["nsfdc_about"],
         source_document_url=U["pib_nsfdc_income"] + " ; " + U["nsfdc_elig"] + " ; " + U["nsfdc_faq"] + " ; " + U["nsfdc_apply"] + " ; " + U["mosje_nsfdc"],
         source_page=NOPAGE, source_section="About NSFDC: objective paragraph; PIB: reply text",
         retrieval_date=RD,
         verification_status=SV2 + "; " + NHR + " (stale 3.00 lakh on Eligibility/FAQ pages)",
         confidence="MEDIUM-HIGH",
         notes="socialjustice.gov.in/schemes/34 also states income 'upto Rs. 5.00 lakh'. One search extract additionally said 'annual family income of each member/applicant should not exceed Rs.3.00 lakh for credit-based schemes' - that is the pre-2026 wording; ask NSFDC/SCA to confirm whether any scheme retains 3.00 lakh."),
    dict(scheme="SIH26091 brief - Micro Finance Scheme (as stated in problem statement)",
         scheme_type="Problem-statement assumption (not a scheme rule)",
         beneficiary_category="'marginalized communities' (brief does not specify SC)",
         income_limit="NOT STATED IN BRIEF", income_period="",
         age_requirement="NOT STATED IN BRIEF",
         project_cost_min="0", project_cost_max="140000", maximum_loan="125000 (90%, max 1.25 lakh)",
         beneficiary_contribution="10% of project cost (brief's assumption)",
         interest_rate="6.5% p.a.", repayment_period="3 years", moratorium="3 months",
         eligible_activities="Examples: Dairy, Retail, Textiles", excluded_activities="NOT STATED IN BRIEF",
         application_route="SCAs / CAs", implementing_agency="'funding agency' via SCAs/CAs",
         required_documents="NOT STATED IN BRIEF", effective_date="SIH 2026 (idea deadline 20 Sep 2026)",
         source_organization="Ministry of Social Justice and Empowerment (SIH 2026 problem statement)",
         source_title="SIH26091: AI-Driven Hyper-Local Business Advisory and Financial Structuring Assistant for Rural Micro-Entrepreneurs",
         source_url=U["sih"], source_document_url=U["sih_mirror"],
         source_page="N/A (web listing); field 'description'", source_section="Background - tier 1; Module 2 Logic A",
         retrieval_date=RD,
         verification_status="UNOFFICIAL MIRROR of official listing (sih.gov.in blocked); values AGREE with nsfdc.nic.in",
         confidence="HIGH that this is the brief text; brief is NOT a scheme rule",
         notes="Brief's formula Project Cost = Margin / 10% ignores the 1.25 lakh cap: for margin 14,000 the formula gives project 1.40 lakh and loan 1.26 lakh, exceeding the cap. ONEVA must apply min(0.9*cost, 125000)."),
    dict(scheme="SIH26091 brief - Term Loan Scheme (as stated in problem statement)",
         scheme_type="Problem-statement assumption (not a scheme rule)",
         beneficiary_category="'marginalized communities'", income_limit="NOT STATED IN BRIEF",
         age_requirement="NOT STATED IN BRIEF",
         project_cost_min="140001", project_cost_max="5000000", maximum_loan="4500000 (90%, max 45 lakh)",
         beneficiary_contribution="10% of project cost (brief's assumption)",
         interest_rate="8% p.a.", repayment_period="7 years", moratorium="6 months",
         eligible_activities="Examples: Dairy, Retail, Textiles", excluded_activities="NOT STATED IN BRIEF",
         application_route="SCAs / CAs", implementing_agency="'agency' via SCAs/CAs",
         required_documents="NOT STATED IN BRIEF", effective_date="SIH 2026",
         source_organization="Ministry of Social Justice and Empowerment (SIH 2026 problem statement)",
         source_title="SIH26091 problem statement", source_url=U["sih"], source_document_url=U["sih_mirror"],
         source_page="N/A; field 'description'", source_section="Background - tier 2; Module 2 Logic B",
         retrieval_date=RD,
         verification_status="UNOFFICIAL MIRROR of official listing; values AGREE with nsfdc.nic.in",
         confidence="HIGH that this is the brief text",
         notes="Brief omits: 12-month moratorium for plantation/construction; SC-only eligibility; 5.00 lakh income ceiling. Brief's worked example contains typos ('?10,00,00')."),
]
write_csv("01_SIH26091_ELIGIBILITY/scheme_eligibility.csv", EL_COLS, eligibility)

# copy SIH mirror original + processed extract
dst = ROOT / "01_SIH26091_ELIGIBILITY/source_documents/sih2026_ps_20260822_211225.json"
src = dst  # original mirror file, stored unmodified
sih_sha = hashlib.sha256(dst.read_bytes()).hexdigest()
d = json.load(open(src))
rec = [p for p in d["problem_statements"] if p.get("ps number") == "SIH26091"][0]
with open(ROOT / "01_SIH26091_ELIGIBILITY/source_documents/SIH26091_extract.processed.json", "w", encoding="utf-8") as f:
    json.dump({"_provenance": {"original_file": dst.name, "original_sha256": sih_sha,
                               "mirror_repo": "https://github.com/NoBugNinja/Smart-India-Hackathon-SIH-2026-Problem-Statements",
                               "mirror_commit": "ee69e2d423689f806e06c57c09e99953cebadadb",
                               "mirror_scraped_from": d["source"], "mirror_scraped_at": d["scraped_at"],
                               "official": False,
                               "note": "Third-party scrape of the official SIH listing; sih.gov.in was unreachable from the collection environment. Text reproduced verbatim including encoding artefacts ('?' = rupee sign, 'â€”' = dash)."},
               "record": rec}, f, indent=1, ensure_ascii=False)

# ================================================================ PART B/C/D
P_COLS = ["scheme", "parameter", "value", "unit", "condition", "effective_date", "source_organization",
          "source_title", "source_url", "source_document", "source_page", "source_section",
          "retrieval_date", "verification_status", "confidence", "notes"]


def P(scheme, parameter, value, unit, condition, eff, org, title, url, doc, section, status, conf, notes=""):
    return dict(scheme=scheme, parameter=parameter, value=value, unit=unit, condition=condition,
                effective_date=eff, source_organization=org, source_title=title, source_url=url,
                source_document=doc, source_page=NOPAGE if doc.endswith(".pdf") or ".pdf" in doc else "N/A (web page)",
                source_section=section, retrieval_date=RD, verification_status=status,
                confidence=conf, notes=notes)


DFS = "Department of Financial Services, Ministry of Finance"
MUDRA = "MUDRA Ltd (Micro Units Development & Refinance Agency)"
PIB_F = "Press Information Bureau (Ministry of Finance)"
params = []
M = "PMMY/MUDRA"
params += [
    P(M, "shishu_max_loan", "50000", "INR", "loan up to", "2015-04-08 (scheme launch)", MUDRA + "; " + DFS,
      "Offerings / PMMY page", U["mudra_off"], U["dfs_pmmy"], "Loan categories", SV2, "HIGH"),
    P(M, "kishor_min_loan_exclusive", "50000", "INR", "above (exclusive)", "2015-04-08", MUDRA, "Offerings", U["mudra_off"], U["dfs_pmmy"], "Loan categories", SV2, "HIGH"),
    P(M, "kishor_max_loan", "500000", "INR", "up to", "2015-04-08", MUDRA, "Offerings", U["mudra_off"], U["dfs_pmmy"], "Loan categories", SV2, "HIGH", "Official sites spell it 'Kishore' and 'Kishor' interchangeably."),
    P(M, "tarun_min_loan_exclusive", "500000", "INR", "above (exclusive)", "2015-04-08", MUDRA, "Offerings", U["mudra_off"], U["dfs_pmmy"], "Loan categories", SV2, "HIGH"),
    P(M, "tarun_max_loan", "1000000", "INR", "up to", "2015-04-08", MUDRA, "Offerings", U["mudra_off"], U["dfs_pmmy"], "Loan categories", SV2, "HIGH"),
    P(M, "tarun_plus_min_loan_exclusive", "1000000", "INR", "above (exclusive)", "2024-10-24", PIB_F + "; " + MUDRA,
      "Loan limit under PMMY increased to Rs.20 lakh", U["pib_tarunplus"], U["pib_tarunplus_pdf"], "Press release body", SV2, "HIGH"),
    P(M, "tarun_plus_max_loan", "2000000", "INR", "up to", "2024-10-24", PIB_F + "; " + MUDRA,
      "Loan limit under PMMY increased to Rs.20 lakh", U["pib_tarunplus"], U["pib_tarunplus_pdf"], "Press release body", SV2, "HIGH",
      "Supersedes the previous PMMY overall maximum of Rs 10 lakh (see SCHEME_CHANGELOG)."),
    P(M, "tarun_plus_eligibility", "Borrower must have previously availed AND successfully repaid a loan under the Tarun category", "rule", "", "2024-10-24",
      PIB_F + "; " + MUDRA, "PIB PRID 2068019; MUDRA Offerings", U["pib_tarunplus"], U["mudra_off"], "Tarun Plus definition", SV2, "HIGH"),
    P(M, "maximum_loan_overall", "2000000", "INR", "collateral-free", "2024-10-24", DFS, "PMMY", U["dfs_pmmy"], U["pib_mudra11"], "Scheme overview", SV2, "HIGH"),
    P(M, "collateral", "Not required (collateral-free)", "rule", "", "2015-04-08", MUDRA, "Offerings / FAQ", U["mudra_off"], U["mudra_faq"], "Key features", SV2, "HIGH"),
    P(M, "credit_guarantee", "Loans covered by Credit Guarantee Fund for Micro Units (CGFMU), administered by NCGTC", "rule", "", "NOT VERIFIED", PIB_F,
      "PIB press notes on PMMY", "https://www.pib.gov.in/PressNoteDetails.aspx?NoteId=158056&ModuleId=3", U["pib_tarunplus"], "CGFMU paragraph", SINGLE, "MEDIUM-HIGH",
      "CGFMU fee/coverage parameters OFFICIAL SOURCE NOT FOUND in this collection."),
    P(M, "eligible_borrowers", "Non-corporate, non-farm small/micro enterprises (individuals, proprietorships, partnerships etc.) in manufacturing, trading and services, including activities allied to agriculture (e.g. poultry, dairy, beekeeping)", "rule", "income-generating activities", "NOT VERIFIED",
      PIB_F + "; " + MUDRA, "PIB PMMY press note; MUDRA Offerings", "https://www.pib.gov.in/PressNoteDetails.aspx?NoteId=158056&ModuleId=3", U["mudra_off"], "Eligible activities", SV2, "HIGH"),
    P(M, "loan_purpose", "Term loans and working capital for income-generating micro enterprises", "rule", "", "NOT VERIFIED", PIB_F, "PIB PMMY press note", "https://www.pib.gov.in/PressNoteDetails.aspx?NoteId=158056&ModuleId=3", U["mudra_sf"], "Purpose", SINGLE, "MEDIUM-HIGH",
      "Detailed purpose list (e.g. MUDRA card for WC) is in the Salient Features PDF - not opened."),
    P(M, "lending_institutions", "Member Lending Institutions: Scheduled Commercial Banks (PSB/private/foreign), RRBs, Small Finance Banks, Cooperative banks (NOT VERIFIED), NBFCs, MFIs/NBFC-MFIs", "rule", "", "NOT VERIFIED", MUDRA + "; " + PIB_F,
      "MUDRA site; PIB '11 Years of PMMY'", U["mudra_off"], U["pib_mudra11"], "MLIs", SV2, "HIGH", "MUDRA is a refinancing institution and does not lend directly to individuals."),
    P(M, "application_route", "Approach any MLI branch, or apply online at www.udyamimitra.in", "rule", "", "NOT VERIFIED", MUDRA, "How & where to get MUDRA loan", U["mudra_how"], U["mudra_faq"], "Procedure", SINGLE, "MEDIUM-HIGH"),
    P(M, "interest_rate", "NOT VERIFIED - set by the lending institution (no single official PMMY rate found)", "", "", "", MUDRA, "", U["mudra_faq"], "", "", NV, "N/A", "Do not show a MUDRA interest rate as official."),
    P(M, "stat_loans_sanctioned_since_inception", "52 crore+ (loans); 32.61 lakh crore (amount)", "count; INR", "since April 2015", "published April 2026", PIB_F, "11 Years of Pradhan Mantri MUDRA Yojana", U["pib_mudra11"], U["pib_mudra11"], "Headline numbers", SINGLE, "MEDIUM",
      "OFFICIAL STATISTIC, reporting date inside PDF not confirmed. Mixed units: 'crore' count vs 'lakh crore' INR; normalised: ~520,000,000 loans; INR 32,610,000,000,000."),
]

K = "PMEGP"
KORG = "Ministry of MSME / KVIC (nodal agency)"
params += [
    P(K, "objective", "Credit-linked subsidy for setting up NEW micro-enterprises in non-farm sector to generate employment in rural and urban areas", "rule", "", "2023-12-07 (revised guidelines)", KORG, "PMEGP revised guidelines 07.12.2023", U["pmegp_elig_msme"], U["pmegp_rev"], "1. The Scheme", SINGLE, "MEDIUM"),
    P(K, "max_project_cost_manufacturing", "5000000", "INR", "new unit", "2022 (revision; exact date NOT VERIFIED) - current per 07.12.2023 guidelines", KORG, "PMEGP FAQ; revised guidelines", U["pmegp_faq"], U["pmegp_rev_kvic"], "Maximum project cost", SV2, "HIGH"),
    P(K, "max_project_cost_service_business", "2000000", "INR", "new unit", "2022 (revision) - current", KORG, "PMEGP FAQ; revised guidelines", U["pmegp_faq"], U["pmegp_rev_kvic"], "Maximum project cost", SV2, "HIGH"),
    P(K, "min_age", "18", "years", "above 18 years", "current", KORG, "Eligibility criteria", U["pmegp_elig_msme"], U["pmegp_elig_kvic"], "Eligibility", SV2, "HIGH"),
    P(K, "income_ceiling", "None", "rule", "no income ceiling", "current", KORG, "Eligibility criteria", U["pmegp_elig_msme"], U["pmegp_elig_kvic"], "Eligibility", SV2, "HIGH"),
    P(K, "education_requirement", "VIII standard pass", "rule", "only if project cost > 1000000 (manufacturing) or > 500000 (service/business)", "current", KORG, "Eligibility criteria", U["pmegp_elig_msme"], U["pmegp_elig_kvic"], "Eligibility", SV2, "HIGH"),
    P(K, "new_units_only", "Only new projects; existing units (under PMRY, REGP or any GoI/State scheme) and units that already availed Government subsidy are NOT eligible", "rule", "", "current", KORG, "PMEGP guidelines", U["pmegp_elig_kvic"], U["pmegp_rev"], "Eligibility", SV2, "HIGH"),
    P(K, "one_per_family", "Only one person per family; family = self and spouse", "rule", "", "current", KORG, "PMEGP guidelines", U["pmegp_elig_kvic"], U["pmegp_rev"], "Eligibility", SINGLE, "MEDIUM",
      "Search extracts of the official guidelines state family = self and spouse; some PMEGP material uses self, spouse and unmarried children (see CONFLICTS C11). Confirm clause in 07.12.2023 PDF."),
    P(K, "subsidy_general_urban", "15", "percent_of_project_cost", "General category, urban", "current", KORG, "PMEGP FAQ; revised guidelines", U["pmegp_faq"], U["pmegp_rev_kvic"], "Margin money subsidy table", SV2, "HIGH"),
    P(K, "subsidy_general_rural", "25", "percent_of_project_cost", "General category, rural", "current", KORG, "PMEGP FAQ; revised guidelines", U["pmegp_faq"], U["pmegp_rev_kvic"], "Margin money subsidy table", SV2, "HIGH"),
    P(K, "subsidy_special_urban", "25", "percent_of_project_cost", "Special category (SC/ST/OBC/Minority/Women/Ex-servicemen/PwD/Transgender/NER/Hill/Border/Aspirational districts), urban", "current", KORG, "PMEGP FAQ; PIB PRID 2158990", U["pmegp_faq"], U["pib_pmegp_sc"], "Margin money subsidy table", SV2, "HIGH"),
    P(K, "subsidy_special_rural", "35", "percent_of_project_cost", "Special category, rural", "current", KORG, "PMEGP FAQ; PIB PRID 2158990", U["pmegp_faq"], U["pib_pmegp_sc"], "Margin money subsidy table", SV2, "HIGH"),
    P(K, "own_contribution_general", "10", "percent_of_project_cost", "General category", "current", KORG, "PMEGP FAQ; revised guidelines", U["pmegp_faq"], U["pmegp_rev_kvic"], "Beneficiary contribution", SV2, "HIGH"),
    P(K, "own_contribution_special", "5", "percent_of_project_cost", "Special category (weaker sections)", "current", KORG, "PMEGP FAQ; revised guidelines", U["pmegp_faq"], U["pmegp_rev_kvic"], "Beneficiary contribution", SV2, "HIGH"),
    P(K, "bank_finance_general", "90", "percent_of_project_cost", "General category (= 100 - own contribution)", "current", "DERIVED", "", U["pmegp_faq"], U["pmegp_rev"], "", "DERIVED", "MEDIUM", "Guidelines say balance is provided by banks as term loan + working capital; the 90/95 split is arithmetic, not quoted."),
    P(K, "bank_finance_special", "95", "percent_of_project_cost", "Special category", "current", "DERIVED", "", U["pmegp_faq"], U["pmegp_rev"], "", "DERIVED", "MEDIUM"),
    P(K, "subsidy_lock_in", "3", "years", "Margin money kept as TDR in beneficiary name; adjusted/released after 3-year lock-in subject to physical verification", "current", KORG, "PMEGP guidelines / MM claim forms", U["pmegp_rev"], U["pmegp_rev"], "Margin money", SINGLE, "MEDIUM"),
    P(K, "repayment_period", "3 to 7", "years", "after initial moratorium prescribed by the bank", "current", KORG, "PMEGP guidelines", U["pmegp_rev"], U["pmegp_2022"], "Repayment", SINGLE, "MEDIUM", "Moratorium length is bank-determined; a '6-18 months' figure was NOT found officially -> NOT VERIFIED."),
    P(K, "edp_training", "10 working days if project cost > 500000; 5 working days if up to 500000; not mandatory up to 200000", "rule", "", "NOT VERIFIED (circular date)", KORG, "EDP FAQ / exemption circular", U["pmegp_edpfaq"], "https://kviconline.gov.in/pmegpeportal/pmegphome/edpCircularExmp.pdf", "EDP", SINGLE, "MEDIUM"),
    P(K, "negative_list", "Crop cultivation/plantation (tea, coffee, rubber etc.), sericulture (cocoon rearing), horticulture, floriculture, animal husbandry; polythene carry bags <75 micron & recycled-plastic food containers; activities prohibited by local authorities", "rule", "", "current", KORG, "PMEGP guidelines - negative list", U["pmegp_rev"], U["pmegp_2022"], "Negative list", SINGLE, "MEDIUM",
      "IMPORTANT for ONEVA: 'animal husbandry' appears in PMEGP negative list, yet some allied activities (e.g. dairy/poultry with processing) may be permitted under later revisions. Verify item-by-item against the 07.12.2023 PDF before blocking dairy/poultry -> NEEDS HUMAN REVIEW."),
    P(K, "institutions_eligible", "Institutions / Production Co-operative Societies / Trusts are eligible (not as special category)", "rule", "", "current", KORG, "PMEGP guidelines", U["pmegp_2022"], U["pmegp_rev"], "Eligibility", SINGLE, "MEDIUM"),
    P(K, "second_loan_max_project_manufacturing", "10000000", "INR", "upgradation of existing PMEGP/REGP/MUDRA unit", "NOT VERIFIED", KORG, "2nd loan guidelines", U["pmegp_2nd"], U["pmegp_2nd_kvic"], "Project cost", SV2, "HIGH"),
    P(K, "second_loan_max_project_service", "2500000", "INR", "upgradation", "NOT VERIFIED", KORG, "2nd loan guidelines", U["pmegp_2nd"], U["pmegp_2nd_kvic"], "Project cost", SV2, "HIGH"),
    P(K, "second_loan_subsidy", "15 (20 for NER & Hill States)", "percent_of_project_cost", "all categories", "NOT VERIFIED", KORG, "2nd loan guidelines", U["pmegp_2nd"], U["pmegp_2nd_kvic"], "Subsidy", SV2, "HIGH"),
    P(K, "second_loan_max_subsidy_manufacturing", "1500000 (2000000 NER/Hill)", "INR", "", "NOT VERIFIED", KORG, "2nd loan guidelines", U["pmegp_2nd"], U["pmegp_2nd_kvic"], "Subsidy", SINGLE, "MEDIUM"),
    P(K, "second_loan_max_subsidy_service", "375000 (500000 NER/Hill)", "INR", "", "NOT VERIFIED", KORG, "2nd loan guidelines", U["pmegp_2nd"], U["pmegp_2nd_kvic"], "Subsidy", SINGLE, "MEDIUM"),
    P(K, "second_loan_own_contribution", "10", "percent_of_project_cost", "all categories", "NOT VERIFIED", KORG, "2nd loan guidelines", U["pmegp_2nd"], U["pmegp_2nd_kvic"], "Contribution", SINGLE, "MEDIUM"),
    P(K, "second_loan_eligibility", "Existing unit performing well (turnover, profit, repayment); profit-making in last 3 years", "rule", "", "NOT VERIFIED", KORG, "2nd loan guidelines", U["pmegp_2nd"], U["pmegp_2nd_kvic"], "Eligibility", SINGLE, "MEDIUM"),
    P(K, "application_route", "Online through PMEGP e-portal; implementing agencies KVIC / KVIB / DIC; financed by banks", "rule", "", "current", "Ministry of MSME", "PMEGP portal", U["pmegp_portal"], U["pmegp_rev"], "", SINGLE, "MEDIUM"),
    P(K, "scheme_validity_after_2025_26", "UNRESOLVED - continuation beyond FY 2025-26 not confirmed from an official approval", "", "", "", "Ministry of MSME", "", U["pmegp_elig_msme"], U["msme_ar"], "", NHR, "LOW",
      "PMEGP was approved for the 15th Finance Commission cycle ending 31-03-2026 (NOT VERIFIED in this collection). A Parliamentary Standing Committee report on MSME Demands for Grants 2026-27 (PIB PRID 2238242) discusses PMEGP, indicating it is funded in 2026-27, but no continuation approval document was located."),
]

C = "CGTMSE (CGS-I)"
CORG = "Credit Guarantee Fund Trust for Micro and Small Enterprises (CGTMSE)"
params += [
    P(C, "max_guarantee_ceiling", "100000000", "INR", "per borrower, CGS-I (banks)", "2025-04-01", CORG + "; Ministry of MSME (PIB)", "Circular 250/2024-25 dated 18-03-2025; CGS-I scheme document updated 01-04-2025", U["cg_250"], U["cg_doc"], "Ceiling", SV2, "HIGH", "= Rs 10 crore. Previously Rs 5 crore (from 01-04-2023) and Rs 2 crore before that (see changelog)."),
    P(C, "coverage_micro_upto_5_lakh", "85", "percent_of_amount_in_default", "Micro enterprises, credit up to 500000", "NOT VERIFIED", CORG, "CGS-I scheme document / Extent of cover", U["cg_cover"], U["cg_doc"], "Extent of guarantee", SINGLE, "MEDIUM"),
    P(C, "coverage_women", "90", "percent_of_amount_in_default", "Women entrepreneurs", "Circular 241 dated 10-12-2024 (effective date inside circular NOT VERIFIED)", CORG, "Circular 241 - enhancement in extent of coverage for women entrepreneurs", U["cg_241"], U["cg_doc"], "Extent of guarantee", SINGLE, "MEDIUM-HIGH", "Supersedes 85% set by Circular 209/2022-23 dated 30-11-2022."),
    P(C, "coverage_sc_st_and_other_special", "NOT VERIFIED (85 or 90)", "percent_of_amount_in_default", "SC/ST entrepreneurs, PwD, Agniveer-promoted MSEs etc.", "", CORG, "CGS-I scheme document", U["cg_doc"], U["cg_doc"], "Extent of guarantee", NHR, "LOW",
      "A search extract grouped SC/ST with women at 90%, but Circular 241 is titled for women only. Read scheme document page with coverage table before using."),
    P(C, "coverage_ner_jk_ladakh", "80", "percent_of_amount_in_default", "MSEs in North East Region, UT of J&K, UT of Ladakh", "NOT VERIFIED", CORG, "Extent of cover", U["cg_cover"], U["cg_doc"], "Extent of guarantee", SINGLE, "MEDIUM"),
    P(C, "coverage_others", "75", "percent_of_amount_in_default", "All other borrowers", "NOT VERIFIED", CORG, "Extent of cover", U["cg_cover"], U["cg_doc"], "Extent of guarantee", SINGLE, "MEDIUM"),
    P(C, "coverage_icdd_addon", "5", "percentage_points", "Additional coverage for MSEs in RBI-identified Credit Deficient Districts", "NOT VERIFIED", CORG, "Extent of cover", U["cg_cover"], U["cg_doc"], "Extent of guarantee", SINGLE, "MEDIUM"),
    P(C, "coverage_transgender", "85", "percent_of_amount_in_default", "MSEs promoted by transgender entrepreneurs; plus 10% concession in guarantee fee", "2025-03-01", CORG, "CGTMSE circular (via search)", U["cg_circ"], U["cg_doc"], "", SINGLE, "MEDIUM"),
    P(C, "agf_0_to_10_lakh", "0.37", "percent_per_annum", "guaranteed amount 0-1000000", "2025-04-01", CORG, "Circular 251/2024-25 dated 18-03-2025 - reduction in AGF", U["cg_agf"], U["cg_251"], "AGF table", SV, "MEDIUM-HIGH"),
    P(C, "agf_10_to_50_lakh", "0.55", "percent_per_annum", "above 1000000 to 5000000", "2025-04-01", CORG, "Circular 251", U["cg_agf"], U["cg_251"], "AGF table", SV, "MEDIUM-HIGH"),
    P(C, "agf_50_lakh_to_1_crore", "0.60", "percent_per_annum", "above 5000000 to 10000000", "2025-04-01", CORG, "Circular 251", U["cg_agf"], U["cg_251"], "AGF table", SV, "MEDIUM-HIGH"),
    P(C, "agf_1_to_2_crore", "0.85", "percent_per_annum", "above 10000000 to 20000000", "2025-04-01", CORG, "Circular 251", U["cg_agf"], U["cg_251"], "AGF table", SV, "MEDIUM-HIGH"),
    P(C, "agf_2_to_5_crore", "1.00", "percent_per_annum", "above 20000000 to 50000000", "2025-04-01", CORG, "Circular 251", U["cg_agf"], U["cg_251"], "AGF table", SV, "MEDIUM-HIGH"),
    P(C, "agf_5_to_8_crore", "1.10", "percent_per_annum", "above 50000000 to 80000000", "2025-04-01", CORG, "Circular 251", U["cg_agf"], U["cg_251"], "AGF table", SV, "MEDIUM-HIGH"),
    P(C, "agf_8_to_10_crore", "1.20", "percent_per_annum", "above 80000000 to 100000000", "2025-04-01", CORG, "Circular 251", U["cg_agf"], U["cg_251"], "AGF table", SV, "MEDIUM-HIGH"),
    P(C, "agf_basis", "Charged on guaranteed amount for first year and on outstanding amount for remaining tenure", "rule", "sanctioned/renewed on or after 01-04-2025", "2025-04-01", CORG, "Circular 251", U["cg_251"], U["cg_251"], "", SINGLE, "MEDIUM"),
    P(C, "guarantee_tenure", "Term loan/composite: agreed tenure of term credit. Working-capital-only: 5 years (or block of 5 years) or loan termination, whichever earlier", "rule", "", "NOT VERIFIED", CORG, "CGS-I scheme document", U["cg_doc"], U["cg_doc"], "Tenure of guarantee", SINGLE, "MEDIUM"),
    P(C, "eligible_borrowers", "New and existing Micro and Small Enterprises incl. MSE retail/wholesale traders and educational/training institutions (Circ. 195, 25-02-2022); Udyam Registration Number mandatory", "rule", "", "NOT VERIFIED", CORG, "Eligible Borrowers page", U["cg_elig"], U["cg_doc"], "", SINGLE, "MEDIUM"),
    P(C, "existing_facility_condition", "Existing credit facility may be covered if not restructured and not in SMA-2 in the last 1 year before application", "rule", "", "NOT VERIFIED", CORG, "Eligible Borrowers page", U["cg_elig"], U["cg_doc"], "", SINGLE, "MEDIUM"),
    P(C, "exclusions", "Agriculture; Self Help Groups (SHGs). Full ineligible list NOT VERIFIED", "rule", "", "NOT VERIFIED", CORG, "CGS-I scheme document", U["cg_doc"], U["cg_doc"], "Ineligible", SINGLE, "MEDIUM"),
    P(C, "collateral", "Collateral-free and third-party-guarantee-free credit; 'hybrid security' allows partial collateral with remainder (up to Rs 10 crore) guaranteed", "rule", "", "NOT VERIFIED", CORG + "; Ministry of MSME (PIB)", "About CGTMSE; PIB note", U["cg_elig"], U["pib_cgs_rural"], "", SV2, "MEDIUM-HIGH"),
    P(C, "lender_eligibility", "Registered Member Lending Institutions (Scheduled Commercial Banks, RRBs, SFBs, NBFCs etc. as notified)", "rule", "", "NOT VERIFIED", CORG, "MLI eligibility page", "https://www.cgtmse.in/Home/VS/94", U["cg_doc"], "", SINGLE, "MEDIUM", "Exact MLI category list not read."),
]

N = "NSFDC"
NORG = "NSFDC"
params += [
    P(N, "income_limit_current", "500000", "INR per year (family)", "rural and urban", "2026-01-07", NORG + "; MoSJE (PIB)", "About NSFDC; PIB PRID 2223171", U["nsfdc_about"], U["pib_nsfdc_income"], "Objective / reply", SV2, "HIGH"),
    P(N, "income_limit_previous", "300000", "INR per year (family)", "rural and urban; SUPERSEDED", "2018-03-08 to 2026-01-06", NORG, "Eligibility Criteria / FAQ (stale)", U["nsfdc_elig"], U["nsfdc_faq"], "", "OBSOLETE - superseded", "HIGH"),
    P(N, "mcf_max_project_cost", "140000", "INR", "Micro Credit Finance", "NOT VERIFIED", NORG, "Micro Credit Finance", U["nsfdc_mcf"], U["nsfdc_mcf"], "", SV2, "HIGH", "Second source: SIH26091 brief (MoSJE)."),
    P(N, "mcf_max_loan", "125000", "INR", "up to 90% of project cost", "NOT VERIFIED", NORG, "Micro Credit Finance", U["nsfdc_mcf"], U["nsfdc_mcf"], "", SV2, "HIGH"),
    P(N, "mcf_loan_share", "90", "percent_of_project_cost", "maximum", "NOT VERIFIED", NORG, "Micro Credit Finance", U["nsfdc_mcf"], U["mosje_nsfdc"], "", SV2, "HIGH"),
    P(N, "mcf_rate_beneficiary", "6.5", "percent_per_annum", "", "NOT VERIFIED", NORG, "Micro Credit Finance", U["nsfdc_mcf"], U["nsfdc_mcf"], "", SV2, "HIGH"),
    P(N, "mcf_rate_nsfdc_to_sca", "2.5", "percent_per_annum", "", "NOT VERIFIED", NORG, "Micro Credit Finance", U["nsfdc_mcf"], U["nsfdc_mcf"], "", SINGLE, "HIGH"),
    P(N, "mcf_repayment_max", "3", "years", "quarterly instalments incl. moratorium", "NOT VERIFIED", NORG, "Micro Credit Finance", U["nsfdc_mcf"], U["nsfdc_mcf"], "", SV2, "HIGH"),
    P(N, "mcf_moratorium", "3", "months", "", "NOT VERIFIED", NORG, "Micro Credit Finance", U["nsfdc_mcf"], U["nsfdc_mcf"], "", SV2, "HIGH"),
    P(N, "tl_min_project_cost_exclusive", "140000", "INR", "more than", "NOT VERIFIED", NORG, "Term Loan", U["nsfdc_tl"], U["nsfdc_tl"], "", SV2, "HIGH"),
    P(N, "tl_max_project_cost", "5000000", "INR", "", "NOT VERIFIED", NORG + "; MoSJE (PIB)", "Term Loan; PIB PRID 2223171", U["nsfdc_tl"], U["pib_nsfdc_income"], "", SV2, "HIGH"),
    P(N, "tl_max_loan", "4500000", "INR", "up to 90% of project cost", "NOT VERIFIED", NORG + "; MoSJE (PIB)", "Term Loan; PIB PRID 2223171", U["nsfdc_tl"], U["pib_nsfdc_income"], "", SV2, "HIGH"),
    P(N, "tl_rate_beneficiary", "8", "percent_per_annum", "", "NOT VERIFIED", NORG, "Term Loan", U["nsfdc_tl"], U["nsfdc_tl"], "", SV2, "HIGH"),
    P(N, "tl_rate_nsfdc_to_sca", "4", "percent_per_annum", "", "NOT VERIFIED", NORG, "Term Loan", U["nsfdc_tl"], U["nsfdc_tl"], "", SINGLE, "HIGH"),
    P(N, "tl_repayment_max", "7", "years", "quarterly instalments incl. moratorium", "NOT VERIFIED", NORG, "Term Loan", U["nsfdc_tl"], U["nsfdc_tl"], "", SV2, "HIGH"),
    P(N, "tl_moratorium", "6", "months", "general", "NOT VERIFIED", NORG, "Term Loan", U["nsfdc_tl"], U["nsfdc_tl"], "", SV2, "HIGH"),
    P(N, "tl_moratorium_plantation_construction", "12", "months", "plantation and construction activities", "NOT VERIFIED", NORG, "Term Loan", U["nsfdc_tl"], U["nsfdc_tl"], "", SINGLE, "HIGH"),
    P(N, "suvidha_max_loan", "900000", "INR", "Suvidha Loan; up to 90% of project cost", "NOT VERIFIED", NORG, "Suvidha Loan", U["nsfdc_suvidha"], U["nsfdc_suvidha"], "", SINGLE, "MEDIUM", "Not part of SIH26091 routing; listed for completeness."),
    P(N, "suvidha_rate_beneficiary", "8", "percent_per_annum", "Suvidha Loan", "NOT VERIFIED", NORG, "Suvidha Loan", U["nsfdc_suvidha"], U["nsfdc_suvidha"], "", SINGLE, "MEDIUM"),
    P(N, "tamil_nadu_sca", "TAHDCO (Tamil Nadu Adi Dravidar Housing & Development Corporation)", "entity", "", "", "TAHDCO; NSFDC", "TAHDCO schemes; NSFDC SCA list", U["tahdco"], U["nsfdc_scas"], "", SV, "MEDIUM-HIGH"),
]

UD = "Udyam/MSME classification"
UORG = "Ministry of MSME (PIB)"
params += [
    P(UD, "micro_investment_max", "25000000", "INR", "plant & machinery/equipment", "2025-04-01", UORG, "Investment and turnover limits enhanced", U["pib_msme_class"], U["msme_class_gaz"], "", SV2, "HIGH", "Rs 2.5 crore"),
    P(UD, "micro_turnover_max", "100000000", "INR", "", "2025-04-01", UORG, "same", U["pib_msme_class"], U["msme_class_gaz"], "", SV2, "HIGH", "Rs 10 crore"),
    P(UD, "small_investment_max", "250000000", "INR", "", "2025-04-01", UORG, "same", U["pib_msme_class"], U["msme_class_gaz"], "", SV2, "HIGH", "Rs 25 crore"),
    P(UD, "small_turnover_max", "1000000000", "INR", "", "2025-04-01", UORG, "same", U["pib_msme_class"], U["msme_class_gaz"], "", SV2, "HIGH", "Rs 100 crore"),
    P(UD, "medium_investment_max", "1250000000", "INR", "", "2025-04-01", UORG, "same", U["pib_msme_class2"], U["msme_class_gaz"], "", SV2, "HIGH", "Rs 125 crore"),
    P(UD, "medium_turnover_max", "5000000000", "INR", "", "2025-04-01", UORG, "same", U["pib_msme_class2"], U["msme_class_gaz"], "", SV2, "HIGH", "Rs 500 crore"),
]
write_csv("02_SCHEME_PARAMETERS/scheme_parameters.csv", P_COLS, params)
for sub, key in [("mudra", M), ("pmegp", K), ("cgtmse", C), ("nsfdc", N)]:
    write_csv(f"02_SCHEME_PARAMETERS/{sub}/{sub}_parameters.csv", P_COLS, [p for p in params if p["scheme"] == key])

# ================================================================ CONFLICTS
CF_COLS = ["conflict_id", "topic", "parameter", "source_1", "value_1", "date_1", "source_2", "value_2", "date_2",
           "which_is_newer", "supersession_evidence", "recommended_value", "confidence", "status", "notes"]
conflicts = [
    dict(conflict_id="C01", topic="NSFDC", parameter="annual family income limit",
         source_1="NSFDC Eligibility Criteria + FAQ pages (" + U["nsfdc_elig"] + ")", value_1="300000 (w.e.f. 08.03.2018)", date_1="2018-03-08",
         source_2="NSFDC About page + PIB PRID 2223171 (" + U["pib_nsfdc_income"] + ")", value_2="500000 (w.e.f. 07.01.2026)", date_2="2026-01-07",
         which_is_newer="source_2", supersession_evidence="PIB (MoSJE) states the limit 'has been revised from Rs 3 lakh to Rs 5 lakh with effect from 07.01.2026'",
         recommended_value="500000", confidence="MEDIUM-HIGH", status="RESOLVED-PROVISIONAL; NEEDS HUMAN REVIEW",
         notes="Underlying NSFDC board circular not located. Confirm with TAHDCO whether SCA-level income certificates still use 3 lakh."),
    dict(conflict_id="C02", topic="NSFDC", parameter="interest rate / repayment range",
         source_1="MoSJE NSFDC material (socialjustice.gov.in; older annexure, e.g. About_NSFDC_08_2021.pdf)", value_1="rate 3%-6%; repayment up to 10 years; loan up to 50 lakh", date_1="~2021 (NOT VERIFIED)",
         source_2="NSFDC scheme pages (MCF, Term Loan)", value_2="MCF 6.5% / 3y; TL 8% / 7y", date_2="current as of 2026-09-27",
         which_is_newer="source_2 (live scheme pages)", supersession_evidence="Implicit only (live pages vs older ministry summary); SIH26091 brief (2026) matches source_2",
         recommended_value="MCF 6.5%/3y/3m; TL 8%/7y/6m", confidence="HIGH", status="RESOLVED",
         notes="MoSJE summary covers many NSFDC schemes (education, VETLS etc.) so the ranges are not scheme-specific."),
    dict(conflict_id="C03", topic="SIH26091 brief vs NSFDC", parameter="loan arithmetic at MCF boundary",
         source_1="SIH26091 brief", value_1="Project cost = margin / 10%; loan = 90%", date_1="2026",
         source_2="NSFDC MCF page", value_2="loan = min(90% of cost, 125000)", date_2="current",
         which_is_newer="N/A", supersession_evidence="Not a supersession; brief formula ignores cap",
         recommended_value="Apply cap: for cost in (138889, 140000] beneficiary share > 10%", confidence="HIGH", status="RESOLVED (DERIVED)",
         notes="CALCULATED: 125000/0.9 = 138888.89."),
    dict(conflict_id="C04", topic="SIH26091 brief vs NSFDC", parameter="Term Loan moratorium",
         source_1="SIH26091 brief", value_1="6 months", date_1="2026",
         source_2="NSFDC Term Loan page", value_2="6 months; 12 months for plantation & construction", date_2="current",
         which_is_newer="N/A", supersession_evidence="Brief is simplified", recommended_value="6 months default; 12 for plantation/construction",
         confidence="HIGH", status="RESOLVED", notes=""),
    dict(conflict_id="C05", topic="CGTMSE", parameter="coverage - women entrepreneurs",
         source_1="CGTMSE Circular 209/2022-23", value_1="85%", date_1="2022-11-30",
         source_2="CGTMSE Circular 241", value_2="90%", date_2="2024-12-10",
         which_is_newer="source_2", supersession_evidence="Circular 241 title: 'enhancement in extent of coverage for women entrepreneurs'",
         recommended_value="90%", confidence="MEDIUM-HIGH", status="RESOLVED", notes="Effective date inside circular not read."),
    dict(conflict_id="C06", topic="CGTMSE", parameter="coverage - SC/ST entrepreneurs",
         source_1="Older CGS-I documents (search extract)", value_1="85%", date_1="NOT VERIFIED",
         source_2="Search extract of current extent-of-cover page grouping SC/ST with women", value_2="90%", date_2="NOT VERIFIED",
         which_is_newer="UNKNOWN", supersession_evidence="None found", recommended_value="DO NOT USE until scheme document table is read",
         confidence="LOW", status="UNRESOLVED", notes=""),
    dict(conflict_id="C07", topic="CGTMSE", parameter="guarantee ceiling",
         source_1="Circular 220 (31-03-2023)", value_1="5 crore", date_1="2023-04-01",
         source_2="Circular 250 (18-03-2025)", value_2="10 crore", date_2="2025-04-01",
         which_is_newer="source_2", supersession_evidence="Circular 250 title '5cr to 10 cr'; PIB MSME classification release", recommended_value="100000000 INR",
         confidence="HIGH", status="RESOLVED", notes=""),
    dict(conflict_id="C08", topic="PMMY", parameter="maximum loan",
         source_1="Original PMMY (Tarun top)", value_1="10 lakh", date_1="2015-04-08",
         source_2="PIB PRID 2068019 (Tarun Plus)", value_2="20 lakh", date_2="2024-10-24",
         which_is_newer="source_2", supersession_evidence="PIB: 'Loan limit under PMMY increased to Rs.20 lakh from the current Rs.10 lakh'",
         recommended_value="2000000 INR (Tarun Plus only for successful Tarun repayers)", confidence="HIGH", status="RESOLVED", notes=""),
    dict(conflict_id="C09", topic="Udyam", parameter="micro enterprise limits",
         source_1="2020 classification (DERIVED from PIB '2.5x and 2x')", value_1="investment 1 crore / turnover 5 crore", date_1="2020-07-01 (NOT VERIFIED)",
         source_2="PIB PRID 2098389 / gazette notification", value_2="investment 2.5 crore / turnover 10 crore", date_2="2025-04-01",
         which_is_newer="source_2", supersession_evidence="Gazette notification effective 01-04-2025", recommended_value="2.5 crore / 10 crore",
         confidence="HIGH", status="RESOLVED", notes="Old values are DERIVED by dividing new by 2.5/2; not independently verified."),
    dict(conflict_id="C10", topic="PMEGP", parameter="scheme validity beyond 31-03-2026",
         source_1="15th FC-cycle approval (NOT VERIFIED)", value_1="valid to FY 2025-26", date_1="NOT VERIFIED",
         source_2="Parliamentary Standing Committee report on MSME DFG 2026-27 (PIB PRID 2238242)", value_2="PMEGP discussed as flagship scheme in 2026-27", date_2="2026-03-11",
         which_is_newer="source_2", supersession_evidence="No continuation approval found", recommended_value="Show PMEGP as available but flag 'continuation status: verify'",
         confidence="LOW", status="UNRESOLVED", notes=""),
    dict(conflict_id="C11", topic="PMEGP", parameter="definition of family (one-per-family rule)",
         source_1="PMEGP guidelines (kviconline/msme.gov.in, search extract)", value_1="self and spouse", date_1="current",
         source_2="Other PMEGP material (search extract, document not identified)", value_2="self, spouse and unmarried children", date_2="current",
         which_is_newer="UNKNOWN", supersession_evidence="None", recommended_value="self and spouse (per guidelines); confirm clause",
         confidence="MEDIUM", status="RESOLVED-PROVISIONAL; NEEDS HUMAN REVIEW", notes="Both extracts from kviconline/pmegp domains."),
    dict(conflict_id="C12", topic="NSFDC", parameter="age requirement",
         source_1="Third-party sites (bajajfinserv, creditmantri etc.)", value_1="18-50 years", date_1="unknown",
         source_2="NSFDC FAQ", value_2="No specific age restriction stated (VET context); 'upto 50 years' only for unemployed VET trainees", date_2="current",
         which_is_newer="N/A", supersession_evidence="Third-party source rejected", recommended_value="No age rule in ONEVA; show 'check with SCA'",
         confidence="MEDIUM", status="RESOLVED (reject non-official)", notes=""),
]
write_csv("05_SOURCE_REGISTER/CONFLICTS.csv", CF_COLS, conflicts)

# ================================================================ RAG DOCUMENTS
docs = [
 # id, title, org, dept, type, pub, eff, src, dl, lang, relevant_sections, relevance, group
 ("D01", "SIH26091 problem statement: AI-Driven Hyper-Local Business Advisory and Financial Structuring Assistant for Rural Micro-Entrepreneurs", "Smart India Hackathon / Ministry of Social Justice and Empowerment", "Department of Social Justice and Empowerment", "Problem statement (web listing)", "2026 (SIH 2026 cycle)", "", U["sih"], U["sih_mirror"], "English", ["Background tiers", "Module 2 Financial Structuring", "Logic A/B"], "Defines ONEVA scope and the scheme-routing assumptions that must be checked against NSFDC", "SIH"),
 ("D02", "NSFDC - Term Loan", "NSFDC", "MoSJE", "Scheme web page", "NOT VERIFIED", "NOT VERIFIED", U["nsfdc_tl"], U["nsfdc_tl"], "English", ["Loan", "Interest", "Repayment"], "Authoritative Term Loan parameters", "NSFDC"),
 ("D03", "NSFDC - Micro Credit Finance", "NSFDC", "MoSJE", "Scheme web page", "NOT VERIFIED", "NOT VERIFIED", U["nsfdc_mcf"], U["nsfdc_mcf"], "English", ["Loan", "Interest", "Repayment"], "Authoritative micro-credit parameters", "NSFDC"),
 ("D04", "NSFDC - Eligibility Criteria", "NSFDC", "MoSJE", "Web page", "NOT VERIFIED", "2018-03-08 (stale income text)", U["nsfdc_elig"], U["nsfdc_elig"], "English", ["Eligibility"], "Eligibility; shows superseded 3 lakh limit (keep for conflict provenance)", "NSFDC"),
 ("D05", "NSFDC - FAQ", "NSFDC", "MoSJE", "FAQ web page", "NOT VERIFIED", "", U["nsfdc_faq"], U["nsfdc_faq"], "English", ["Who is eligible", "How to apply", "Documents"], "Citizen FAQ for RAG answers", "NSFDC"),
 ("D06", "About NSFDC", "NSFDC", "MoSJE", "Web page", "2026 (post 07-01-2026 edit)", "2026-01-07", U["nsfdc_about"], U["nsfdc_about"], "English", ["Objective (income limit 5 lakh)"], "Current income ceiling", "NSFDC"),
 ("D07", "NSFDC - How to Apply", "NSFDC", "MoSJE", "Web page", "NOT VERIFIED", "", U["nsfdc_apply"], U["nsfdc_apply"], "English", ["Application route"], "Application route via SCAs", "NSFDC"),
 ("D08", "NSFDC - State Channelising Agencies list", "NSFDC", "MoSJE", "Directory web page", "NOT VERIFIED", "", U["nsfdc_scas"], U["nsfdc_scas"], "English", ["SCA addresses"], "State -> SCA routing table", "NSFDC"),
 ("D09", "PIB: Increase in the provision of loans to Scheduled Castes (PRID 2223171)", "Press Information Bureau", "Ministry of Social Justice & Empowerment", "Press release (Parliament reply)", "2026 (exact date NOT VERIFIED)", "2026-01-07", U["pib_nsfdc_income"], U["pib_nsfdc_income"], "English", ["Income limit revision", "Term loan ceiling adequacy"], "Second official source for 5 lakh income limit", "NSFDC"),
 ("D10", "MoSJE - NSFDC scheme page", "Ministry of Social Justice & Empowerment", "Department of Social Justice and Empowerment", "Scheme web page", "NOT VERIFIED", "", U["mosje_nsfdc"], U["mosje_nsfdc"], "English", ["NSFDC schemes"], "Ministry-level secondary source", "NSFDC"),
 ("D11", "DFS - Pradhan Mantri MUDRA Yojana (PMMY)", "Department of Financial Services", "Ministry of Finance", "Scheme web page", "NOT VERIFIED", "", U["dfs_pmmy"], U["dfs_pmmy"], "English", ["Categories", "MLIs"], "Primary PMMY source", "MUDRA"),
 ("D12", "MUDRA Loan - Salient Features", "MUDRA Ltd", "DFS", "PDF", "NOT VERIFIED", "", U["mudra_off"], U["mudra_sf"], "English", ["Eligibility", "Purpose", "Categories"], "Detailed PMMY features", "MUDRA"),
 ("D13", "PIB: PMMY loan limit raised to Rs 20 lakh (Tarun Plus)", "Press Information Bureau", "Ministry of Finance", "Press release + PDF backgrounder", "2024-10", "2024-10-24", U["pib_tarunplus"], U["pib_tarunplus_pdf"], "English", ["Tarun Plus"], "Tarun Plus rule and effective date", "MUDRA"),
 ("D14", "PIB: 11 Years of Pradhan Mantri MUDRA Yojana", "Press Information Bureau", "Ministry of Finance", "PDF backgrounder", "2026-04", "", U["pib_mudra11"], U["pib_mudra11"], "English", ["Achievements", "State-wise disbursement"], "Current official PMMY statistics", "MUDRA"),
 ("D15", "PMEGP Revised Scheme Guidelines (07.12.2023)", "Ministry of MSME / KVIC", "Ministry of MSME", "Guidelines PDF", "2023-12-07", "2023-12-07", U["pmegp_elig_msme"], U["pmegp_rev"], "English", ["Eligibility", "Margin money", "Negative list", "Repayment"], "Latest consolidated PMEGP rules", "PMEGP"),
 ("D16", "PMEGP 2nd loan guidelines (upgradation of existing units)", "Ministry of MSME / KVIC", "Ministry of MSME", "Guidelines PDF", "NOT VERIFIED", "", U["pmegp_2nd_kvic"], U["pmegp_2nd"], "English", ["Project cost", "Subsidy", "Eligibility"], "Second-financial-assistance rules", "PMEGP"),
 ("D17", "PMEGP FAQ (KVIC e-portal)", "KVIC", "Ministry of MSME", "FAQ web page", "NOT VERIFIED", "", U["pmegp_faq"], U["pmegp_faq"], "English", ["Project cost", "Subsidy", "Contribution"], "Second source for PMEGP parameters", "PMEGP"),
 ("D18", "CGTMSE - CGS-I Scheme Document (updated as on 01-04-2025)", "CGTMSE", "Ministry of MSME / SIDBI", "Scheme document PDF", "2025-04-01", "2025-04-01", U["cg_circ"], U["cg_doc"], "English", ["Eligibility", "Extent of guarantee", "Tenure", "Fees"], "Authoritative CGTMSE rules", "CGTMSE"),
 ("D19", "CGTMSE Circular 250/2024-25 - ceiling 5 cr to 10 cr", "CGTMSE", "", "Circular PDF", "2025-03-18", "2025-04-01", U["cg_circ"], U["cg_250"], "English", ["Ceiling"], "Supersession evidence", "CGTMSE"),
 ("D20", "CGTMSE Circular 251/2024-25 - reduction in AGF", "CGTMSE", "", "Circular PDF", "2025-03-18", "2025-04-01", U["cg_circ"], U["cg_251"], "English", ["AGF table"], "Current fee table", "CGTMSE"),
 ("D21", "CGTMSE Circular 241 - coverage for women entrepreneurs", "CGTMSE", "", "Circular PDF", "2024-12-10", "NOT VERIFIED", U["cg_circ"], U["cg_241"], "English", ["Extent of cover"], "Women coverage 90%", "CGTMSE"),
 ("D22", "PIB: Investment and turnover limits for MSME classification enhanced (PRID 2098389) + MSME gazette notification page", "Press Information Bureau / Ministry of MSME", "Ministry of MSME", "Press release / notification", "2025-02", "2025-04-01", U["pib_msme_class"], U["msme_class_gaz"], "English", ["Classification limits"], "Udyam classification for ONEVA enterprise sizing", "Udyam"),
 ("D23", "Ministry of MSME Annual Report 2025-26", "Ministry of MSME", "", "Annual report PDF", "2026-05", "", U["msme_ar"], U["msme_ar"], "English", ["PMEGP", "CGTMSE", "Udyam statistics"], "Current official MSME scheme performance", "Udyam"),
 ("D24", "HCES 2023-24 Press Note / Fact sheet", "MoSPI (NSO)", "Ministry of Statistics & PI", "Press note PDF", "2024-12-27", "", U["hces_pib"], U["hces_pn"], "English", ["All-India MPCE", "State-wise MPCE tables"], "State-level consumption proxy", "Stats"),
 ("D25", "HCES 2023-24 Final Report", "MoSPI (NSO)", "Ministry of Statistics & PI", "Report PDF", "2025 (NOT VERIFIED)", "", U["hces_pn2"], U["hces_report"], "English", ["State x item-group tables"], "Item-level consumption shares for business categories", "Stats"),
 ("D26", "data.gov.in: Current Daily Price of Various Commodities from Various Markets (Mandi)", "Open Government Data Platform / AGMARKNET", "Ministry of Agriculture & Farmers Welfare", "API dataset", "daily", "", U["ogd_mandi"], U["ogd_mandi_api"], "English", ["API fields"], "Official mandi prices", "Stats"),
 ("D27", "Basic Animal Husbandry Statistics 2025", "Department of Animal Husbandry & Dairying", "Ministry of Fisheries, AH & Dairying", "Statistical publication PDF", "2025-11/12", "reference 2024-25", U["bahs_pib"], U["bahs"], "English", ["State-wise milk/egg/meat production"], "Production (NOT demand) context for dairy/poultry", "Stats"),
 ("D28", "Tamil Nadu UYEGP scheme page", "Government of Tamil Nadu - MSME Department", "Commissionerate of Industries & Commerce", "Scheme web page", "NOT VERIFIED", "", U["tn_uyegp"], U["tn_uyegp"], "English/Tamil", ["Eligibility", "Subsidy"], "State scheme complementing NSFDC/PMEGP in TN", "TamilNadu"),
 ("D29", "Tamil Nadu AABCS (Annal Ambedkar Business Champions Scheme) G.O.", "Government of Tamil Nadu - MSME Department", "", "Government Order PDF", "NOT VERIFIED", "", U["tn_aabcs"], U["tn_aabcs_go"], "Tamil/English", ["Eligibility", "Subsidy", "Interest subvention"], "SC/ST-specific state scheme in TN", "TamilNadu"),
 ("D30", "TAHDCO schemes (NSFDC SCA for Tamil Nadu)", "TAHDCO, Government of Tamil Nadu", "Adi Dravidar & Tribal Welfare Department", "Web page", "NOT VERIFIED", "", U["tahdco"], U["tahdco"], "English/Tamil", ["Schemes", "Application"], "Where TN SC applicants actually apply for NSFDC loans", "TamilNadu"),
 ("D31", "Statistical Hand Book of Tamil Nadu", "Department of Economics and Statistics, Govt of Tamil Nadu", "Planning, Development & Special Initiatives", "Statistical publication", "annual (latest edition NOT VERIFIED)", "", U["tn_des"], U["tn_des"], "English", ["District tables", "District income"], "District-level indicators for TN", "TamilNadu"),
]
DOC_COLS = ["document_id", "title", "organization", "department", "document_type", "publication_date",
            "effective_date", "source_url", "download_url", "retrieved_at", "file_name", "file_size",
            "sha256", "official_source", "language", "pages", "relevant_sections", "relevance",
            "verification_status", "notes", "group"]
rag_rows = []
for (i, t, o, dp, ty, pub, eff, s, dl, lang, secs, rel, grp) in docs:
    fn = dl.split("/")[-1].split("?")[0] if ".pdf" in dl.lower() else f"{i}_{grp}.html"
    if "ViewFile" in dl:
        fn = dl.split("id=")[1].split("&")[0].split("_", 1)[1].replace("+", "_").replace("%5B90%5D", "")
    meta = {"document_id": i, "title": t, "organization": o, "department": dp, "document_type": ty,
            "publication_date": pub, "effective_date": eff, "source_url": s, "download_url": dl,
            "retrieved_at": "", "file_name": fn, "file_size": "", "sha256": "",
            "official_source": i != "D01" or False, "language": lang, "pages": 0,
            "relevant_sections": secs, "relevance": rel,
            "verification_status": "NOT DOWNLOADED - host blocked by collection environment egress policy; content verified at search-extract level only. Run 05_SOURCE_REGISTER/fetch_scripts/download_documents.py",
            "notes": ""}
    if i == "D01":
        meta.update(official_source=False, retrieved_at=RD, file_name=dst.name,
                    file_size=str(dst.stat().st_size), sha256=sih_sha,
                    verification_status="DOWNLOADED FROM UNOFFICIAL MIRROR (GitHub, commit ee69e2d); official sih.gov.in listing not reachable",
                    notes="Original mirror file stored in 01_SIH26091_ELIGIBILITY/source_documents/ and 03_GOVERNMENT_RAG/documents/. Replace with official PDF/listing when reachable.")
        shutil.copyfile(dst, ROOT / "03_GOVERNMENT_RAG/documents" / dst.name)
    if i == "D04":
        meta["notes"] = "Shows superseded income limit (3.00 lakh). Index with effective_to=2026-01-06 to avoid RAG surfacing it as current."
    with open(ROOT / f"03_GOVERNMENT_RAG/metadata/{i}.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    r = dict(meta); r["relevant_sections"] = "; ".join(secs); r["group"] = grp
    rag_rows.append(r)
write_csv("03_GOVERNMENT_RAG/rag_document_index.csv", DOC_COLS, rag_rows)

# ================================================================ MARKET DATA
MP_COLS = ["commodity", "state", "district", "market", "date", "minimum_price", "maximum_price",
           "modal_price", "unit", "source", "source_url", "retrieval_date"]
write_csv("04_MARKET_DATA/market_prices.csv", MP_COLS, [])  # header only - see data dictionary

PP_COLS = ["state", "geography_level", "indicator", "value", "unit", "period", "source", "source_url",
           "source_document", "source_page", "retrieval_date", "limitations", "label", "verification_status"]
pp_lim = "National/State aggregate; NOT village or district purchasing power. Survey-based estimate with sampling error."
pp = [
    dict(state="All India", geography_level="country", indicator="Average MPCE - rural (excluding imputed value of free items)", value="4122", unit="INR per person per month", period="HCES 2023-24", source="MoSPI / PIB", source_url=U["hces_pib"], source_document=U["hces_pn"], source_page=NOPAGE, retrieval_date=RD, limitations=pp_lim, label="OFFICIAL STATISTIC", verification_status=SV2),
    dict(state="All India", geography_level="country", indicator="Average MPCE - urban (excluding imputed value of free items)", value="6996", unit="INR per person per month", period="HCES 2023-24", source="MoSPI / PIB", source_url=U["hces_pib"], source_document=U["hces_pn"], source_page=NOPAGE, retrieval_date=RD, limitations=pp_lim, label="OFFICIAL STATISTIC", verification_status=SV2),
    dict(state="All India", geography_level="country", indicator="Average MPCE - rural (including imputed value of free items)", value="4247", unit="INR per person per month", period="HCES 2023-24", source="MoSPI / PIB", source_url=U["hces_pib"], source_document=U["hces_pn"], source_page=NOPAGE, retrieval_date=RD, limitations=pp_lim, label="OFFICIAL STATISTIC", verification_status=SV),
    dict(state="All India", geography_level="country", indicator="Average MPCE - urban (including imputed value of free items)", value="7078", unit="INR per person per month", period="HCES 2023-24", source="MoSPI / PIB", source_url=U["hces_pib"], source_document=U["hces_pn"], source_page=NOPAGE, retrieval_date=RD, limitations=pp_lim, label="OFFICIAL STATISTIC", verification_status=SV),
    dict(state="Sikkim", geography_level="state", indicator="Average MPCE - rural (highest among states)", value="9377", unit="INR per person per month", period="HCES 2023-24", source="MoSPI / PIB", source_url=U["hces_pib"], source_document=U["hces_pn"], source_page=NOPAGE, retrieval_date=RD, limitations="state-level consumption indicator; " + pp_lim, label="OFFICIAL STATISTIC", verification_status=SV),
    dict(state="Sikkim", geography_level="state", indicator="Average MPCE - urban (highest among states)", value="13927", unit="INR per person per month", period="HCES 2023-24", source="MoSPI / PIB", source_url=U["hces_pib"], source_document=U["hces_pn"], source_page=NOPAGE, retrieval_date=RD, limitations="state-level consumption indicator; " + pp_lim, label="OFFICIAL STATISTIC", verification_status=SV),
    dict(state="Tamil Nadu", geography_level="state", indicator="Average MPCE - rural", value="", unit="INR per person per month", period="HCES 2023-24", source="MoSPI", source_url=U["hces_pn"], source_document=U["hces_pn"], source_page="State table (page NOT RECORDED)", retrieval_date=RD, limitations="state-level purchasing-power proxy only", label="NOT VERIFIED", verification_status="NOT VERIFIED - official table not readable; run fetch script / read press note state annex"),
    dict(state="Tamil Nadu", geography_level="state", indicator="Average MPCE - urban", value="", unit="INR per person per month", period="HCES 2023-24", source="MoSPI", source_url=U["hces_pn"], source_document=U["hces_pn"], source_page="State table (page NOT RECORDED)", retrieval_date=RD, limitations="state-level purchasing-power proxy only", label="NOT VERIFIED", verification_status="NOT VERIFIED - only non-official aggregator (CEIC) seen; value deliberately withheld"),
]
write_csv("04_MARKET_DATA/purchasing_power.csv", PP_COLS, pp)

DP_COLS = ["dataset_id", "dataset", "organization", "url", "geography", "period", "currency_of_data",
           "measures_actual_demand", "classification", "what_it_measures", "suitable_for_oneva", "how_to_use",
           "example_value", "example_value_label", "example_value_source", "verification_status", "limitations"]
dp = [
    dict(dataset_id="DP01", dataset="AGMARKNET mandi daily prices (data.gov.in)", organization="DMI / MoA&FW via OGD", url=U["ogd_mandi"], geography="state-district-market", period="daily, rolling", currency_of_data="current (daily)", measures_actual_demand="NO", classification="MARKET ACTIVITY (prices)", what_it_measures="Wholesale min/max/modal price at regulated markets", suitable_for_oneva="YES - price context for agri/food businesses", how_to_use="Price trend and seasonality for inputs/outputs; NOT retail consumer price", example_value="", example_value_label="", example_value_source="", verification_status="Dataset existence " + SV + "; API resource id from public client code", limitations="Coverage depends on markets reporting; wholesale, not retail; unit must be read from resource metadata"),
    dict(dataset_id="DP02", dataset="AGMARKNET market arrivals", organization="DMI / MoA&FW", url="https://agmarknet.gov.in", geography="market", period="daily", currency_of_data="current", measures_actual_demand="NO", classification="MARKET ACTIVITY (supply arriving at mandis)", what_it_measures="Quantity arriving at market", suitable_for_oneva="YES with qualification", how_to_use="Indicator of local trading volume; never label as consumer demand", example_value="", example_value_label="", example_value_source="", verification_status=NV + " (host blocked; availability of arrivals via OGD API not checked)", limitations="Arrivals != consumption"),
    dict(dataset_id="DP03", dataset="HCES 2023-24 (state x rural/urban MPCE, item-group shares)", organization="MoSPI", url=U["hces_report"], geography="state x rural/urban", period="2023-24", currency_of_data="latest available", measures_actual_demand="PARTIAL", classification="CONSUMPTION (household expenditure)", what_it_measures="Household consumption spend per capita by item group", suitable_for_oneva="YES as state-level consumption indicator", how_to_use="Spend share on item group (e.g. milk, eggs, clothing) x population = state-level spend proxy (label DERIVED)", example_value="4122 / 6996 INR (All-India rural/urban MPCE)", example_value_label="OFFICIAL STATISTIC", example_value_source=U["hces_pib"], verification_status=SV2, limitations="No district/village estimates in published tables; unit-level data needed for sub-state"),
    dict(dataset_id="DP04", dataset="Basic Animal Husbandry Statistics 2025", organization="DAHD", url=U["bahs"], geography="state", period="2024-25", currency_of_data="latest", measures_actual_demand="NO", classification="PRODUCTION", what_it_measures="Milk, egg, meat, wool production & per-capita availability", suitable_for_oneva="YES as supply-side context for dairy/poultry", how_to_use="Show state share of production; never call it demand", example_value="Tamil Nadu share of India egg production 15.63% (2024-25); India meat production 10.50 million tonnes (2024-25)", example_value_label="OFFICIAL STATISTIC", example_value_source=U["bahs_pib"], verification_status=SV, limitations="State level; production not consumption"),
    dict(dataset_id="DP05", dataset="PMMY state-wise disbursement", organization="DFS / PIB", url=U["pib_mudra11"], geography="state", period="cumulative since 2015 (to ~Mar 2026)", currency_of_data="April 2026", measures_actual_demand="NO", classification="CREDIT ACTIVITY", what_it_measures="Micro-credit disbursed", suitable_for_oneva="LIMITED - financial inclusion context", how_to_use="Context only", example_value="UP 58111 crore; Bihar 54064 crore; Maharashtra 50762 crore", example_value_label="OFFICIAL STATISTIC", example_value_source=U["pib_mudra11"], verification_status=SINGLE, limitations="Cumulative; TN figure not captured; reporting date inside PDF not read"),
    dict(dataset_id="DP06", dataset="ONEVA Udyam registrations (existing internal dataset)", organization="Ministry of MSME Udyam via data.gov.in (already in ONEVA DB)", url=U["udyam"], geography="state-district-pincode-NIC", period="as loaded by 01-udyam-data-engine", currency_of_data="per ONEVA load date", measures_actual_demand="NO", classification="SUPPLY / COMPETITION (enterprise density)", what_it_measures="Registered enterprises by NIC and location", suitable_for_oneva="YES - competitor density", how_to_use="Count of same-NIC enterprises per district/pincode", example_value="", example_value_label="", example_value_source="", verification_status="Internal", limitations="Registration != active business; informal businesses missing; pincode != unique place"),
    dict(dataset_id="DP07", dataset="Tamil Nadu District Income Estimates / Statistical Hand Book", organization="DES Tamil Nadu", url=U["tn_des_income"], geography="district (TN)", period="annual (latest year NOT VERIFIED)", currency_of_data="NOT VERIFIED", measures_actual_demand="NO", classification="ECONOMIC INDICATOR (district income)", what_it_measures="District domestic product / per-capita income", suitable_for_oneva="YES as district economic context (TN)", how_to_use="District per-capita income as context; label 'district economic indicator'", example_value="", example_value_label="", example_value_source="", verification_status=NV + " (host blocked)", limitations="Income != purchasing power of target group"),
    dict(dataset_id="DP08", dataset="Census 2011 / LGD village & town directory (population)", organization="ORGI / MoPR LGD", url="https://lgdirectory.gov.in", geography="village/town", period="2011 (Census)", currency_of_data="OUTDATED (15 years)", measures_actual_demand="NO", classification="POPULATION (market size denominator)", what_it_measures="Population and households", suitable_for_oneva="YES with explicit '2011' label", how_to_use="Population within 5-10 km radius for SIH Module 1 'market reach'", example_value="", example_value_label="", example_value_source="", verification_status=NV + " (not fetched)", limitations="Census 2011 is old; Census 2027 results not yet available (NOT VERIFIED)"),
    dict(dataset_id="DP09", dataset="Direct local consumer demand for a product", organization="-", url="", geography="village/block", period="-", currency_of_data="-", measures_actual_demand="YES (would)", classification="UNAVAILABLE", what_it_measures="-", suitable_for_oneva="N/A", how_to_use="Do not display; state 'no official source'", example_value="", example_value_label="", example_value_source="", verification_status="OFFICIAL SOURCE NOT FOUND", limitations="No official village-level demand dataset exists in this collection"),
]
write_csv("04_MARKET_DATA/demand_proxies.csv", DP_COLS, dp)

# ================================================================ UDYAM JOIN KEYS
UJ_COLS = ["join_key", "dataset_A", "dataset_B", "confidence", "known_problem", "recommended_usage"]
uj = [
    dict(join_key="state (normalised name -> LGD state code)", dataset_A="ONEVA locations.state", dataset_B="HCES state tables; BAHS; AGMARKNET state; PMMY state stats", confidence="HIGH", known_problem="Spelling variants (Tamilnadu/Tamil Nadu, Orissa/Odisha), UT reorganisations (J&K/Ladakh 2019, DNH&DD 2020)", recommended_usage="Map every source to LGD state code; join on code, never on raw text"),
    dict(join_key="district (normalised -> LGD district code)", dataset_A="ONEVA locations.district (reconciled by 03-geographic-reconciliation)", dataset_B="AGMARKNET district; TN DES district tables; NSFDC/TAHDCO district offices", confidence="MEDIUM", known_problem="New districts carved after 2011 (TN: e.g. Tenkasi, Chengalpattu, Kallakurichi, Ranipet, Tirupathur, Mayiladuthurai); AGMARKNET district names are free text", recommended_usage="Join on LGD district code; keep a manual alias table; report unmatched rows"),
    dict(join_key="market (AGMARKNET market name)", dataset_A="AGMARKNET market", dataset_B="ONEVA location_coordinates", confidence="LOW-MEDIUM", known_problem="Market names are not LGD entities; need geocoding", recommended_usage="Geocode markets once; use distance (km) from user's village rather than name joins"),
    dict(join_key="pincode", dataset_A="ONEVA msme_enterprises.pincode", dataset_B="India Post pincode directory (data.gov.in) -> district", confidence="LOW-MEDIUM", known_problem="A pincode can span multiple villages/blocks and even districts; one village can have several pincodes; not an administrative unit", recommended_usage="Use only as a fallback locator or for aggregation with a many-to-many bridge table; never as a unique geographic id"),
    dict(join_key="NIC 2008 code (2/4/5-digit)", dataset_A="ONEVA nic_codes / msme_enterprises.nic", dataset_B="ONEVA business category taxonomy; ASI/NSS tables by NIC", confidence="HIGH (code) / MEDIUM (category mapping)", known_problem="Mapping 'Dairy/Retail/Textiles' to NIC is many-to-many; Udyam activity self-declared", recommended_usage="Maintain a curated category->NIC-prefix map; version it"),
    dict(join_key="commodity (AGMARKNET) -> business category", dataset_A="AGMARKNET commodity", dataset_B="ONEVA business category (e.g. Dairy, Poultry)", confidence="MEDIUM", known_problem="Commodity names/varieties vary; many businesses use several commodities", recommended_usage="Curated mapping table; show which commodities were used"),
    dict(join_key="rural/urban sector", dataset_A="ONEVA location (village vs town)", dataset_B="HCES rural/urban; PMEGP rural/urban subsidy", confidence="MEDIUM", known_problem="PMEGP 'rural' definition (village/town population rules) not identical to Census rural", recommended_usage="Store PMEGP rural flag separately from Census flag; ask user when ambiguous"),
    dict(join_key="Udyam enterprise type (micro/small/medium)", dataset_A="ONEVA msme_enterprises.enterprise_type", dataset_B="scheme_parameters Udyam limits (01-04-2025)", confidence="HIGH", known_problem="Registrations before 01-04-2025 classified under old limits", recommended_usage="Record classification date; recompute only if investment/turnover known"),
]
write_csv("05_SOURCE_REGISTER/udyam_join_keys.csv", UJ_COLS, uj)

# ================================================================ MARKET INTELLIGENCE MATRIX
MI_COLS = ["business", "location", "evidence_type", "dataset", "geography_level", "status", "label", "note"]
mi = []
for biz, loc, items in [
    ("Poultry (egg layer)", "Coimbatore district, Tamil Nadu", [
        ("MSME density (same NIC)", "ONEVA Udyam", "district/pincode", "AVAILABLE", "Observed", "Registered units only"),
        ("Commodity prices (egg, maize feed)", "AGMARKNET via data.gov.in", "market", "AVAILABLE (after API fetch)", "Observed", "Wholesale"),
        ("Household consumption proxy (egg spend share)", "HCES 2023-24", "state", "AVAILABLE", "Proxy", "State-level consumption indicator"),
        ("Production context", "BAHS 2025", "state", "AVAILABLE", "Proxy", "Production, not demand (TN 15.63% of India's eggs)"),
        ("District economic indicator", "TN DES district income", "district", "AVAILABLE (not fetched)", "Proxy", ""),
        ("Direct consumer demand", "-", "-", "UNAVAILABLE", "Unavailable", "No official source"),
    ]),
    ("Dairy (milk collection/retail)", "Any TN block", [
        ("MSME density", "ONEVA Udyam", "district/pincode", "AVAILABLE", "Observed", ""),
        ("Milk production context", "BAHS 2025", "state", "AVAILABLE", "Proxy", "Production"),
        ("Milk spend share", "HCES 2023-24", "state", "AVAILABLE", "Proxy", ""),
        ("Milk procurement price", "Aavin/TN Co-op", "state", "NOT COLLECTED", "Unavailable", "Not an OGD dataset in this collection"),
        ("Direct consumer demand", "-", "-", "UNAVAILABLE", "Unavailable", ""),
    ]),
    ("Textiles / tailoring", "Tiruppur district, Tamil Nadu", [
        ("MSME density", "ONEVA Udyam", "district/pincode", "AVAILABLE", "Observed", ""),
        ("Clothing spend share", "HCES 2023-24", "state", "AVAILABLE", "Proxy", ""),
        ("Commodity prices (cotton)", "AGMARKNET", "market", "AVAILABLE (after API fetch)", "Observed", "Raw cotton only"),
        ("Direct consumer demand", "-", "-", "UNAVAILABLE", "Unavailable", ""),
    ]),
    ("Kirana / retail", "Any village", [
        ("MSME density (retail NIC 47xx)", "ONEVA Udyam", "pincode", "AVAILABLE", "Observed", "Retail registration under Udyam since 2021 - undercounts informal shops"),
        ("Population within 5-10 km", "Census 2011 / LGD", "village", "AVAILABLE (not fetched; 2011)", "Derived", "Outdated"),
        ("Per-capita consumption", "HCES 2023-24", "state rural/urban", "AVAILABLE", "Proxy", ""),
        ("Direct consumer demand", "-", "-", "UNAVAILABLE", "Unavailable", ""),
    ]),
]:
    for e in items:
        mi.append(dict(business=biz, location=loc, evidence_type=e[0], dataset=e[1], geography_level=e[2], status=e[3], label=e[4], note=e[5]))
write_csv("04_MARKET_DATA/market_intelligence_availability_matrix.csv", MI_COLS, mi)

# ================================================================ SOURCE REGISTER
SR_COLS = ["source_id", "dataset_or_document", "organization", "department", "source_type", "official", "url",
           "download_url", "publication_date", "effective_date", "retrieved_date", "file_name", "sha256",
           "pages_or_rows", "verification_method", "primary_source", "secondary_source", "status", "confidence", "limitations"]
sr = []
for r in rag_rows:
    sr.append(dict(source_id=r["document_id"], dataset_or_document=r["title"], organization=r["organization"],
                   department=r["department"], source_type=r["document_type"], official=str(r["official_source"]).upper(),
                   url=r["source_url"], download_url=r["download_url"], publication_date=r["publication_date"],
                   effective_date=r["effective_date"], retrieved_date=RD if r["document_id"] == "D01" else f"{RD} (search-level)",
                   file_name=r["file_name"] if r["document_id"] == "D01" else "", sha256=r["sha256"],
                   pages_or_rows="226 problem statements (JSON)" if r["document_id"] == "D01" else "",
                   verification_method="git clone of mirror; sha256" if r["document_id"] == "D01" else "Official-domain restricted web search; original not opened",
                   primary_source="YES" if r["official_source"] else "NO (mirror)",
                   secondary_source="", status="DOWNLOADED (mirror)" if r["document_id"] == "D01" else "NOT DOWNLOADED - egress blocked",
                   confidence="HIGH" if r["document_id"] == "D01" else "MEDIUM",
                   limitations="Unofficial mirror" if r["document_id"] == "D01" else "No sha256/page numbers until fetched"))
sr.append(dict(source_id="S-API-01", dataset_or_document="AGMARKNET mandi price API resource 9ef84268-d588-465a-a308-a864a43d0070", organization="OGD Platform India", department="MoA&FW", source_type="API", official="TRUE", url=U["ogd_mandi"], download_url=U["ogd_mandi_api"], publication_date="daily", effective_date="", retrieved_date="NOT RETRIEVED", file_name="", sha256="", pages_or_rows="", verification_method="Resource id taken from public GitHub client code (singhdks23/Mandi-Market-Application, kayalshri/commodityprice); field names confirmed from same code", primary_source="YES", secondary_source="", status="NOT FETCHED - api.data.gov.in blocked; requires API key", confidence="MEDIUM", limitations="Confirm id/fields on first live call"))
sr.append(dict(source_id="S-3P-01", dataset_or_document="Non-official aggregators seen and REJECTED (bajajfinserv, lendingkart, creditmantri, projectsarthi, CEIC, scribd)", organization="various", department="", source_type="rejected", official="FALSE", url="", download_url="", publication_date="", effective_date="", retrieved_date=RD, file_name="", sha256="", pages_or_rows="", verification_method="", primary_source="NO", secondary_source="", status="REJECTED - not used for any value", confidence="", limitations=""))
write_csv("05_SOURCE_REGISTER/SOURCE_REGISTER.csv", SR_COLS, sr)

# ================================================================ MISSING DATA
MS_COLS = ["item", "area", "reason", "status", "how_to_close"]
missing = [
    ("Original PDFs/pages + SHA-256 + page numbers for D02-D31", "All", "Egress policy blocked all .gov.in/.nic.in/cgtmse.in hosts", "NEEDS HUMAN REVIEW", "Run fetch_scripts/download_documents.py on an unrestricted machine; fill page numbers"),
    ("NSFDC board circular for 5 lakh income limit", "NSFDC", "Only About page + PIB reply found", "NEEDS HUMAN REVIEW", "Request from NSFDC / TAHDCO"),
    ("NSFDC age limit", "NSFDC", "No official rule found", "OFFICIAL SOURCE NOT FOUND", "Ask SCA"),
    ("NSFDC eligible/excluded activity list", "NSFDC", "Not on pages read", "OFFICIAL SOURCE NOT FOUND", "Obtain SCA/NSFDC activity list or annual action plan"),
    ("NSFDC split of remaining 10% (beneficiary vs SCA vs subsidy)", "NSFDC", "Not stated on pages read", "NOT VERIFIED", "TAHDCO scheme norms"),
    ("NSFDC 'micro-finance-scheme' page content", "NSFDC", "Page exists; content not surfaced", "NOT VERIFIED", "Fetch page"),
    ("MUDRA interest rate", "MUDRA", "Lender-determined", "NOT VERIFIED", "Do not display as official"),
    ("CGFMU fee/coverage", "MUDRA", "Not researched in depth", "NOT VERIFIED", "NCGTC website"),
    ("CGTMSE SC/ST coverage %", "CGTMSE", "Ambiguous extract", "UNRESOLVED", "Read CGS-I scheme doc coverage table"),
    ("PMEGP continuation beyond FY 2025-26", "PMEGP", "No approval document found", "UNRESOLVED", "Check msme.gov.in / Cabinet decisions"),
    ("PMEGP 'family' definition", "PMEGP", "Conflicting extracts", "UNRESOLVED", "Read guideline clause"),
    ("PMEGP moratorium length", "PMEGP", "Bank-determined; no official figure", "NOT VERIFIED", ""),
    ("Tamil Nadu HCES 2023-24 MPCE (rural/urban)", "Purchasing power", "Official table not readable; only aggregator seen", "NOT VERIFIED", "Read HCES press note state annex"),
    ("Market prices rows", "Market", "api.data.gov.in blocked; API key needed", "NOT COLLECTED", "Run fetch_agmarknet.py with DATA_GOV_IN_API_KEY"),
    ("Price unit for AGMARKNET API", "Market", "Not read from resource metadata", "NOT VERIFIED", "Read resource page; store unit per record"),
    ("TN DES district income tables", "Market", "Host blocked", "NOT COLLECTED", "Download Statistical Hand Book tables"),
    ("TN scheme (UYEGP/NEEDS/AABCS) full parameters", "Tamil Nadu", "Only headline values seen (UYEGP loan up to 15 lakh, 25% subsidy max 3.75 lakh; age 18-35/45; AABCS 6% interest subvention up to 10 years)", "SINGLE SOURCE, SEARCH-LEVEL", "Download G.O.s"),
    ("Official SIH26091 listing on sih.gov.in", "SIH", "Host blocked; mirror used", "NEEDS HUMAN REVIEW", "Save official page/PDF"),
]
write_csv("05_SOURCE_REGISTER/MISSING_DATA.csv", MS_COLS, [dict(zip(MS_COLS, m)) for m in missing])

# ================================================================ XLSX
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

def sheet_from(wb, name, cols, rows):
    ws = wb.create_sheet(name)
    ws.append(cols)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1F4E78")
        c.alignment = Alignment(wrap_text=True, vertical="top")
    for r in rows:
        ws.append([str(r.get(c, "")) if not isinstance(r.get(c, ""), (int, float)) else r.get(c) for c in cols])
    for i, c in enumerate(cols, 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = min(60, max(12, len(c) + 4))
    ws.freeze_panes = "A2"
    if not rows:
        ws.append(["(no rows - see MISSING DATA sheet)"])

wb = Workbook(); wb.remove(wb.active)
sheet_from(wb, "1 Scheme Eligibility", EL_COLS, eligibility)
sheet_from(wb, "2 Scheme Financial Params", P_COLS, params)
sheet_from(wb, "3 Government Documents", DOC_COLS, rag_rows)
sheet_from(wb, "4 Market Prices", MP_COLS, [])
sheet_from(wb, "5 Demand Proxies", DP_COLS, dp)
sheet_from(wb, "6 Purchasing Power", PP_COLS, pp)
sheet_from(wb, "7 Udyam Integration", UJ_COLS, uj)
sheet_from(wb, "8 Conflicts", CF_COLS, conflicts)
sheet_from(wb, "9 Missing Data", MS_COLS, [dict(zip(MS_COLS, m)) for m in missing])
wb.save(ROOT / "05_SOURCE_REGISTER/VERIFICATION_MATRIX.xlsx")
print("ok", len(eligibility), len(params), len(rag_rows), len(conflicts))
