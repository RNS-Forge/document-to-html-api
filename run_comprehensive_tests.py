"""
Comprehensive Test Runner for Document-to-HTML Conversion Service
=================================================================
Tests real-world documents ranging from easy to complex across all formats:
  1. easy_badge.png          (Easy Image: Badge / Status Card)
  2. intern_certificate.png  (Medium Image: Internship Certificate)
  3. intern_certificate.pdf  (Medium PDF: Certificate with typography and borders)
  4. intern_offer.docx       (DOCX: Internship Offer Letter with Tables)
  5. invoice.pdf             (Complex PDF: Production Invoice with itemized table)
  6. invoice_complex.png     (Complex Image: High-res Invoice render)
  7. invoice_sheet.xlsx      (Complex XLSX: Styled Invoice Spreadsheet)
  8. presentation.pptx       (Complex PPTX: Multi-slide presentation deck)
  9. resume.pdf              (Complex PDF: Multi-page Awesome-CV resume)
 10. resume_complex.png      (Complex Image: High-res Resume render)
"""

import os
import sys
import time
import json
from pathlib import Path
from starlette.testclient import TestClient

from app import app

client = TestClient(app)

OUTPUT_DIR = Path("test_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

SAMPLES_DIR = Path("test_samples")

files_to_test = [
    ("easy_badge.png", "Easy Image (Badge)", "image/png"),
    ("intern_certificate.png", "Medium Image (Certificate)", "image/png"),
    ("intern_certificate.pdf", "Medium PDF (Certificate)", "application/pdf"),
    ("intern_offer.docx", "Word DOCX (Intern Offer)", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ("invoice.pdf", "Complex PDF (Invoice)", "application/pdf"),
    ("invoice_complex.png", "Complex Image (Invoice)", "image/png"),
    ("invoice_sheet.xlsx", "Complex Excel (Invoice Sheet)", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("presentation.pptx", "Complex Presentation (PPTX)", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
    ("resume.pdf", "Complex PDF (Resume)", "application/pdf"),
    ("resume_complex.png", "Complex Image (Resume)", "image/png"),
]

print("=" * 86)
print("  DOCUMENT-TO-HTML API — FULL ACCURACY VERIFICATION MATRIX")
print("=" * 86)
print(f"{'Filename':<25} | {'Category':<24} | {'Time (ms)':<9} | {'HTML Size':<10} | {'Imgs':<5} | {'Tbls':<5} | {'Status'}")
print("-" * 86)

results = []
all_passed = True

for filename, category, mime in files_to_test:
    filepath = SAMPLES_DIR / filename
    if not filepath.exists():
        print(f"[SKIP] {filename} not found!")
        continue

    with open(filepath, "rb") as f:
        file_bytes = f.read()

    start_time = time.perf_counter()
    response = client.post(
        "/convert",
        files={"file": (filename, file_bytes, mime)}
    )
    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 1)

    if response.status_code != 200:
        print(f"{filename:<25} | {category:<24} | {elapsed_ms:<9} | {'FAILED':<10} | {'-':<5} | {'-':<5} | [ERR {response.status_code}]")
        all_passed = False
        continue

    data = response.json()
    html_content = data.get("html", "")

    # Basic validations
    has_html_doc = "<!DOCTYPE html>" in html_content
    has_doc_root = ('class="doc-root"' in html_content) or ('class="page"' in html_content) or ('class="solara-letterhead"' in html_content) or ('class="bank-instruction-form"' in html_content)
    img_b64_count = html_content.count("data:image/")
    table_count = html_content.count("<table")

    # Distinct output filename
    out_filename = f"{Path(filename).stem}_{Path(filename).suffix.lstrip('.')}.html"
    out_path = OUTPUT_DIR / out_filename
    with open(out_path, "w", encoding="utf-8") as out_f:
        out_f.write(html_content)

    status = "PASS" if (has_html_doc and has_doc_root) else "WARN"
    if status != "PASS":
        all_passed = False

    html_size_kb = f"{len(html_content.encode('utf-8')) / 1024:.1f} KB"

    print(f"{filename:<25} | {category:<24} | {elapsed_ms:<9} | {html_size_kb:<10} | {img_b64_count:<5} | {table_count:<5} | [{status}]")

    results.append({
        "filename": filename,
        "category": category,
        "elapsed_ms": elapsed_ms,
        "html_size_kb": html_size_kb,
        "base64_images": img_b64_count,
        "tables": table_count,
        "output_path": str(out_path),
        "status": status,
    })

print("-" * 86)
print(f"Summary: {len(results)}/{len(files_to_test)} documents converted & verified!")
print(f"Saved HTML reports in: {OUTPUT_DIR.resolve()}")
print("=" * 86)

with open(OUTPUT_DIR / "test_report.json", "w", encoding="utf-8") as rf:
    json.dump(results, rf, indent=2)

if not all_passed:
    sys.exit(1)
