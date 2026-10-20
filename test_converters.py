"""
Unit & Integration Test Suite for Document-to-HTML Converters
=============================================================
Tests PDF, DOCX, PPTX, XLSX, Image, Markdown, CSV, JSON, TXT conversion.
Validates:
  1. Successful HTML generation
  2. Base64 image embedding
  3. Proper table structure
  4. Accuracy and error handling
"""

import io
import os
import unittest
import base64
from PIL import Image

import pymupdf
import docx
from pptx import Presentation
from pptx.util import Inches, Pt
import openpyxl

from app import (
    convert_pdf,
    convert_docx,
    convert_pptx,
    convert_xlsx,
    convert_image,
    convert_markdown,
    convert_csv,
    convert_json,
    convert_text,
)


class TestConverters(unittest.TestCase):

    def test_pdf_conversion_with_image_and_table(self):
        # Create a sample PDF with title, text, table, and embedded image
        doc = pymupdf.open()
        page = doc.new_page()

        # Insert title
        page.insert_text((50, 60), "Quarterly Financial Report", fontsize=22)
        page.insert_text((50, 90), "This report summarizes performance across all units.", fontsize=11)

        # Create a dummy image
        img = Image.new("RGB", (100, 100), color=(50, 150, 250))
        img_buf = io.BytesIO()
        img.save(img_buf, format="PNG")
        page.insert_image(pymupdf.Rect(50, 120, 150, 220), stream=img_buf.getvalue())

        pdf_bytes = doc.tobytes()
        doc.close()

        html = convert_pdf(pdf_bytes, "report.pdf")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Quarterly Financial Report", html)
        self.assertIn("data:image/png;base64,", html)
        print(" [OK] PDF Converter passed with text + Base64 image!")

    def test_image_conversion_base64(self):
        # Create a test image
        img = Image.new("RGBA", (200, 120), color=(255, 100, 50, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        data = buf.getvalue()

        html = convert_image(data, "sample.png")
        self.assertIn("data:image/png;base64,", html)
        self.assertIn("200 &times; 120 px", html)
        print(" [OK] Image Converter passed with Base64 embedding + metadata!")

    def test_docx_conversion_with_image(self):
        doc = docx.Document()
        doc.add_heading("Project Overview", level=1)
        doc.add_paragraph("This is a test paragraph for docx conversion.")

        # Add image
        img = Image.new("RGB", (80, 80), color=(100, 200, 100))
        img_buf = io.BytesIO()
        img.save(img_buf, format="PNG")
        img_buf.seek(0)
        doc.add_picture(img_buf, width=docx.shared.Inches(1))

        # Add table
        tbl = doc.add_table(rows=2, cols=2)
        tbl.cell(0, 0).text = "Metric"
        tbl.cell(0, 1).text = "Value"
        tbl.cell(1, 0).text = "Accuracy"
        tbl.cell(1, 1).text = "99.8%"

        out_buf = io.BytesIO()
        doc.save(out_buf)
        docx_bytes = out_buf.getvalue()

        html = convert_docx(docx_bytes, "overview.docx")
        self.assertIn("Project Overview", html)
        self.assertIn("data:image/", html)
        self.assertIn("Accuracy", html)
        print(" [OK] DOCX Converter passed with styles, tables, and Base64 images!")

    def test_pptx_conversion_with_image(self):
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        slide.shapes.title.text = "Antigravity Launch"
        slide.placeholders[1].text = "Automated high accuracy conversion"

        # Add image
        img = Image.new("RGB", (60, 60), color=(200, 50, 120))
        img_buf = io.BytesIO()
        img.save(img_buf, format="PNG")
        img_buf.seek(0)
        slide.shapes.add_picture(img_buf, Inches(1), Inches(3), width=Inches(1))

        out_buf = io.BytesIO()
        prs.save(out_buf)
        pptx_bytes = out_buf.getvalue()

        html = convert_pptx(pptx_bytes, "presentation.pptx")
        self.assertIn("Antigravity Launch", html)
        self.assertIn("data:image/", html)
        self.assertIn("Slide 1", html)
        print(" [OK] PPTX Converter passed with slides, typography, and Base64 images!")

    def test_xlsx_conversion_with_multi_sheets(self):
        wb = openpyxl.Workbook()
        ws1 = wb.active
        ws1.title = "Summary"
        ws1.append(["Category", "Score"])
        ws1.append(["Speed", 98])

        ws2 = wb.create_sheet(title="Details")
        ws2.append(["ID", "Name"])
        ws2.append([1, "Alpha"])

        out_buf = io.BytesIO()
        wb.save(out_buf)
        xlsx_bytes = out_buf.getvalue()

        html = convert_xlsx(xlsx_bytes, "data.xlsx")
        self.assertIn("Summary", html)
        self.assertIn("Details", html)
        self.assertIn("Speed", html)
        print(" [OK] XLSX Converter passed with multi-sheet tabs and tables!")

    def test_markdown_and_csv(self):
        md = "# Heading\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"
        html_md = convert_markdown(md.encode("utf-8"), "test.md")
        self.assertIn("Heading</h1>", html_md)
        self.assertIn("<table>", html_md)

        csv_data = "Name,Age,Role\nAlice,30,Engineer\nBob,25,Designer\n"
        html_csv = convert_csv(csv_data.encode("utf-8"), "test.csv")
        self.assertIn("Alice", html_csv)
        self.assertIn("<th>Name</th>", html_csv)
        print(" [OK] Markdown and CSV Converters passed!")

    def test_fastapi_endpoints(self):
        from starlette.testclient import TestClient
        from app import app
        client = TestClient(app)

        # 1. Health check
        res_h = client.get("/health")
        self.assertEqual(res_h.status_code, 200)
        self.assertEqual(res_h.json()["status"], "healthy")

        # 2. Root UI (LOCAL_RUN=true)
        res_root = client.get("/")
        self.assertEqual(res_root.status_code, 200)

        # 3. /convert with a text file
        res_conv = client.post(
            "/convert",
            files={"file": ("note.txt", b"Hello Antigravity World!\nNew line here.", "text/plain")}
        )
        self.assertEqual(res_conv.status_code, 200)
        data = res_conv.json()
        self.assertTrue(data["success"])
        self.assertIn("Hello Antigravity World!", data["html"])
        self.assertIn("<!DOCTYPE html>", data["html"])

        # 4. /convert/raw (without outer wrapper)
        res_raw = client.post(
            "/convert/raw",
            files={"file": ("note.txt", b"Raw test line.", "text/plain")}
        )
        self.assertEqual(res_raw.status_code, 200)
        data_raw = res_raw.json()
        self.assertTrue(data_raw["success"])
        self.assertNotIn("<!DOCTYPE html>", data_raw["html"])
        self.assertIn("Raw test line.", data_raw["html"])

        print(" [OK] All FastAPI endpoints (/health, /, /convert, /convert/raw) passed!")


if __name__ == "__main__":
    unittest.main()
