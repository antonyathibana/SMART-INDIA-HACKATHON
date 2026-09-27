"""Download every document in 03_GOVERNMENT_RAG/rag_document_index.csv, verify it,
and fill in retrieved_at / file_size / sha256 / pages in the per-document metadata JSON.

Run on a machine whose network can reach the .gov.in / .nic.in / cgtmse.in hosts:

    pip install requests pypdf
    python 05_SOURCE_REGISTER/fetch_scripts/download_documents.py

Originals are written to 03_GOVERNMENT_RAG/documents/ and never modified afterwards.
Nothing is overwritten: if a file already exists with a different hash, the new
download is saved with a timestamp suffix and the difference is reported.
"""
import csv, datetime, hashlib, json, sys
from pathlib import Path

import requests

PKG = Path(__file__).resolve().parents[2]
DOCS = PKG / "03_GOVERNMENT_RAG/documents"
META = PKG / "03_GOVERNMENT_RAG/metadata"
INDEX = PKG / "03_GOVERNMENT_RAG/rag_document_index.csv"
OFFICIAL_SUFFIXES = (".gov.in", ".nic.in", "cgtmse.in", "mudra.org.in", "tahdco.com", "udyamimitra.in")
MAGIC = {b"%PDF": "pdf", b"<!DO": "html", b"<htm": "html", b"<HTM": "html", b"PK\x03\x04": "zip/xlsx"}


def sniff(b: bytes) -> str:
    for k, v in MAGIC.items():
        if b.startswith(k):
            return v
    return "unknown"


def main():
    rows = list(csv.DictReader(open(INDEX, encoding="utf-8")))
    report = []
    for r in rows:
        doc_id, url = r["document_id"], r["download_url"]
        meta_path = META / f"{doc_id}.json"
        meta = json.load(open(meta_path, encoding="utf-8"))
        if doc_id == "D01":
            report.append((doc_id, "SKIP (mirror already stored; fetch official listing manually)"))
            continue
        host = requests.utils.urlparse(url).hostname or ""
        try:
            resp = requests.get(url, timeout=60, allow_redirects=True,
                                headers={"User-Agent": "ONEVA-data-collection/1.0"})
        except Exception as e:  # network errors are recorded, never hidden
            report.append((doc_id, f"FAILED: {e}"))
            continue
        final_host = requests.utils.urlparse(resp.url).hostname or ""
        body = resp.content
        kind = sniff(body[:8])
        ok = resp.status_code == 200 and len(body) > 0
        redirect_note = f"redirected to {resp.url}" if resp.url != url else ""
        if not final_host.endswith(OFFICIAL_SUFFIXES):
            report.append((doc_id, f"REJECTED: final host {final_host} not an expected official domain"))
            continue
        name = meta["file_name"] or f"{doc_id}.bin"
        if kind == "html" and not name.endswith(".html"):
            name = f"{doc_id}.html"
        target = DOCS / name
        sha = hashlib.sha256(body).hexdigest()
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != sha:
            stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
            target = target.with_name(f"{target.stem}.{stamp}{target.suffix}")
            redirect_note += " | CONTENT CHANGED vs earlier download"
        if ok:
            target.write_bytes(body)
        pages = 0
        if kind == "pdf" and ok:
            try:
                from pypdf import PdfReader
                reader = PdfReader(str(target))
                pages = len(reader.pages)
                _ = reader.pages[-1].extract_text()  # confirm last page readable
            except Exception as e:
                redirect_note += f" | PDF READ ERROR: {e}"
        meta.update(retrieved_at=datetime.datetime.now().isoformat(timespec="seconds"),
                    file_name=target.name, file_size=str(len(body)), sha256=sha, pages=pages,
                    verification_status=("DOWNLOADED; type=%s; http=%s" % (kind, resp.status_code)) if ok else f"FAILED http={resp.status_code}",
                    notes=(meta.get("notes", "") + " " + redirect_note).strip())
        json.dump(meta, open(meta_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        report.append((doc_id, meta["verification_status"] + (" " + redirect_note if redirect_note else "")))
    for d, s in report:
        print(d, s)
    print("\nNEXT: open every PDF, confirm title/organisation/date, and record page numbers for every"
          " value in scheme_parameters.csv (source_page column).")


if __name__ == "__main__":
    sys.exit(main())
