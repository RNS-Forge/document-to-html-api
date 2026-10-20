"""
Document-to-HTML API — Accurate Universal Document Converter
============================================================
Accepts uploads of PDF, DOCX, PPTX, XLSX, images (PNG/JPG/WEBP/BMP/TIFF),
Markdown, CSV, and plain text files and returns pixel-accurate semantic HTML.

Run:
    pip install -r requirements.txt
    uvicorn app:app --host 0.0.0.0 --port 8000 --reload

Endpoint:
    POST /convert   (multipart/form-data, field name: "file")
    Returns JSON:   { "success": true, "filename": "...", "html": "..." }
"""

import io
import os
import csv
import base64
import tempfile
import traceback
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Document-to-HTML API",
    description="Converts PDF, DOCX, PPTX, XLSX, images, Markdown, CSV, and plain text into accurate semantic HTML.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Maximum upload size: 50 MB
MAX_UPLOAD_BYTES = 50 * 1024 * 1024

# ─── Supported MIME → handler mapping ─────────────────────────────────────────

EXTENSION_MAP = {
    # PDF
    ".pdf": "pdf",
    # Microsoft Word
    ".docx": "docx",
    ".doc": "docx",
    # Microsoft PowerPoint
    ".pptx": "pptx",
    ".ppt": "pptx",
    # Microsoft Excel
    ".xlsx": "xlsx",
    ".xls": "xlsx",
    # Images (OCR + embed)
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".webp": "image",
    ".bmp": "image",
    ".tiff": "image",
    ".tif": "image",
    ".gif": "image",
    ".svg": "svg",
    # Markdown
    ".md": "markdown",
    ".markdown": "markdown",
    # CSV / TSV
    ".csv": "csv",
    ".tsv": "csv",
    # Plain text / code
    ".txt": "text",
    ".log": "text",
    ".json": "text",
    ".xml": "text",
    ".html": "passthrough",
    ".htm": "passthrough",
}


# ─── Shared CSS reset embedded in every output ────────────────────────────────

SHARED_CSS = """
<style>
  .doc-html-root {
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    color: #1a1a1a;
    background: #ffffff;
    line-height: 1.6;
    padding: 24px 32px;
    max-width: 960px;
    margin: 0 auto;
    box-sizing: border-box;
    word-wrap: break-word;
    overflow-wrap: break-word;
  }
  .doc-html-root h1 { font-size: 1.8em; margin: 0.6em 0 0.3em; font-weight: 700; color: #111; border-bottom: 2px solid #e5e7eb; padding-bottom: 6px; }
  .doc-html-root h2 { font-size: 1.4em; margin: 0.5em 0 0.25em; font-weight: 700; color: #1e293b; }
  .doc-html-root h3 { font-size: 1.15em; margin: 0.4em 0 0.2em; font-weight: 600; color: #334155; }
  .doc-html-root p  { margin: 0.4em 0; font-size: 1em; }
  .doc-html-root ul, .doc-html-root ol { margin: 0.3em 0; padding-left: 1.6em; }
  .doc-html-root li { margin-bottom: 0.2em; }
  .doc-html-root table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 0.92em; }
  .doc-html-root th, .doc-html-root td { border: 1px solid #d1d5db; padding: 8px 10px; text-align: left; vertical-align: top; }
  .doc-html-root th { background: #f1f5f9; font-weight: 700; color: #1e293b; }
  .doc-html-root tr:nth-child(even) td { background: #f8fafc; }
  .doc-html-root img { max-width: 100%; height: auto; display: block; margin: 10px 0; }
  .doc-html-root pre { background: #f8f9fa; padding: 12px 16px; border-radius: 6px; overflow-x: auto; font-size: 0.88em; line-height: 1.5; border: 1px solid #e5e7eb; }
  .doc-html-root code { font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace; }
  .doc-html-root blockquote { border-left: 4px solid #6366f1; padding: 8px 16px; margin: 12px 0; background: #f5f3ff; color: #4338ca; font-style: italic; }
  .doc-html-root hr { border: none; border-top: 1.5px solid #e5e7eb; margin: 16px 0; }
  .doc-slide { page-break-after: always; border: 1px solid #e5e7eb; border-radius: 8px; padding: 24px 28px; margin-bottom: 20px; background: #fff; }
  .doc-slide-title { font-size: 1.5em; font-weight: 700; color: #1e293b; margin-bottom: 12px; border-bottom: 2px solid #6366f1; padding-bottom: 6px; }
  .doc-slide-content { font-size: 1em; line-height: 1.55; }
  .doc-page-break { page-break-after: always; border-top: 2px dashed #cbd5e1; margin: 18px 0; }
  .ocr-text-overlay { margin-top: 12px; padding: 12px 16px; background: #fffbeb; border: 1px solid #fbbf24; border-radius: 6px; font-size: 0.92em; color: #92400e; }
</style>
""".strip()


def wrap_html(inner_html: str, title: str = "Converted Document") -> str:
    """Wrap raw inner HTML in a full document with shared CSS."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{_esc(title)}</title>
  {SHARED_CSS}
</head>
<body>
  <div class="doc-html-root">
    {inner_html}
  </div>
</body>
</html>"""


def _esc(text: str) -> str:
    """HTML-escape a string."""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CONVERTER FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


# ── 1. PDF ────────────────────────────────────────────────────────────────────

def convert_pdf(data: bytes, filename: str) -> str:
    """
    Converts a PDF to semantic HTML using PyMuPDF (fitz).
    Extracts text blocks with font metadata, images, tables, and page structure.
    Falls back to OCR for scanned/image-only PDFs.
    """
    import fitz  # PyMuPDF

    doc = fitz.open(stream=data, filetype="pdf")
    pages_html = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_parts = []

        # Extract text as structured dict for font-aware rendering
        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        blocks = text_dict.get("blocks", [])

        for block in blocks:
            if block["type"] == 0:  # Text block
                block_html = _render_text_block(block)
                if block_html.strip():
                    page_parts.append(block_html)

            elif block["type"] == 1:  # Image block
                img_data = block.get("image")
                if img_data:
                    ext = block.get("ext", "png")
                    b64 = base64.b64encode(img_data).decode("utf-8")
                    mime = f"image/{ext}" if ext != "jpg" else "image/jpeg"
                    page_parts.append(
                        f'<img src="data:{mime};base64,{b64}" alt="Embedded image from page {page_num + 1}">'
                    )

        # Extract tables if pymupdf supports it
        try:
            tables = page.find_tables()
            for table in tables:
                table_data = table.extract()
                if table_data and len(table_data) > 0:
                    page_parts.append(_render_table(table_data))
        except Exception:
            pass

        # If no text was extracted (scanned PDF), attempt OCR on the page image
        if not any(b["type"] == 0 and _block_has_text(b) for b in blocks):
            ocr_html = _ocr_page_image(page, page_num)
            if ocr_html:
                page_parts.append(ocr_html)

        if page_parts:
            page_content = "\n".join(page_parts)
            if len(doc) > 1:
                pages_html.append(
                    f'<section class="pdf-page" data-page="{page_num + 1}">\n'
                    f'  <div class="page-marker" style="font-size:0.75em;color:#94a3b8;margin-bottom:8px;">Page {page_num + 1}</div>\n'
                    f"  {page_content}\n"
                    f"</section>"
                )
                if page_num < len(doc) - 1:
                    pages_html.append('<div class="doc-page-break"></div>')
            else:
                pages_html.append(page_content)

    doc.close()
    inner = "\n".join(pages_html) if pages_html else "<p><em>No extractable content found in this PDF.</em></p>"
    return wrap_html(inner, filename)


def _block_has_text(block: dict) -> bool:
    """Check if a text block has any actual visible characters."""
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            if span.get("text", "").strip():
                return True
    return False


def _render_text_block(block: dict) -> str:
    """Render a PyMuPDF text block dict into styled HTML."""
    lines_html = []
    for line in block.get("lines", []):
        spans_html = []
        for span in line.get("spans", []):
            text = span.get("text", "")
            if not text:
                continue

            size = span.get("size", 11)
            flags = span.get("flags", 0)
            # flags: bit 0 = superscript, bit 1 = italic, bit 2 = serif, bit 4 = bold

            is_bold = bool(flags & 16)
            is_italic = bool(flags & 2)

            escaped = _esc(text)

            if is_bold and is_italic:
                escaped = f"<strong><em>{escaped}</em></strong>"
            elif is_bold:
                escaped = f"<strong>{escaped}</strong>"
            elif is_italic:
                escaped = f"<em>{escaped}</em>"

            spans_html.append(escaped)

        line_text = "".join(spans_html).strip()
        if line_text:
            lines_html.append(line_text)

    if not lines_html:
        return ""

    combined = " ".join(lines_html)

    # Determine element type based on font size of first span
    first_size = 11
    try:
        first_size = block["lines"][0]["spans"][0].get("size", 11)
    except (IndexError, KeyError):
        pass

    if first_size >= 20:
        return f"<h1>{combined}</h1>"
    elif first_size >= 16:
        return f"<h2>{combined}</h2>"
    elif first_size >= 13:
        return f"<h3>{combined}</h3>"
    else:
        return f"<p>{combined}</p>"


def _render_table(table_data: list) -> str:
    """Render extracted table data into an HTML table."""
    if not table_data:
        return ""

    html = '<table>\n'
    for row_idx, row in enumerate(table_data):
        tag = "th" if row_idx == 0 else "td"
        html += "  <tr>\n"
        for cell in row:
            cell_text = _esc(str(cell)) if cell is not None else ""
            html += f"    <{tag}>{cell_text}</{tag}>\n"
        html += "  </tr>\n"
    html += "</table>"
    return html


def _ocr_page_image(page, page_num: int) -> str:
    """Render a PDF page as image and run OCR to extract text."""
    try:
        import pytesseract
        from PIL import Image

        # Render page to pixmap at 2x resolution for better OCR
        mat = __import__("fitz").Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")

        img = Image.open(io.BytesIO(img_data))
        ocr_text = pytesseract.image_to_string(img, lang="eng")

        parts = []
        # Embed the page image
        b64 = base64.b64encode(img_data).decode("utf-8")
        parts.append(f'<img src="data:image/png;base64,{b64}" alt="Scanned page {page_num + 1}">')

        if ocr_text.strip():
            lines = [_esc(l) for l in ocr_text.strip().split("\n") if l.strip()]
            ocr_html = "<br>\n".join(lines)
            parts.append(f'<div class="ocr-text-overlay"><strong>OCR Extracted Text:</strong><br>{ocr_html}</div>')

        return "\n".join(parts)
    except ImportError:
        return ""
    except Exception:
        return ""


# ── 2. DOCX ──────────────────────────────────────────────────────────────────

def convert_docx(data: bytes, filename: str) -> str:
    """
    Converts a DOCX file to styled HTML using mammoth (preserves headings,
    lists, bold, italic, links, tables, and embedded images as base64).
    """
    import mammoth

    result = mammoth.convert_to_html(
        io.BytesIO(data),
        convert_image=mammoth.images.img_element(_mammoth_image_handler),
    )

    inner_html = result.value
    warnings = result.messages

    # Add conversion notes if there were warnings
    if warnings:
        warn_items = "".join(f"<li>{_esc(str(w))}</li>" for w in warnings[:5])
        inner_html += f'\n<details style="margin-top:16px;font-size:0.82em;color:#64748b;"><summary>Conversion Notes ({len(warnings)})</summary><ul>{warn_items}</ul></details>'

    return wrap_html(inner_html, filename)


def _mammoth_image_handler(image):
    """Convert embedded DOCX images to inline base64 data URIs."""
    with image.open() as img_stream:
        img_bytes = img_stream.read()
    content_type = image.content_type or "image/png"
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    return {"src": f"data:{content_type};base64,{b64}"}


# ── 3. PPTX ──────────────────────────────────────────────────────────────────

def convert_pptx(data: bytes, filename: str) -> str:
    """
    Converts a PowerPoint PPTX to HTML. Each slide becomes a styled card
    with title, text frames, tables, and embedded images.
    """
    from pptx import Presentation
    from pptx.util import Inches

    prs = Presentation(io.BytesIO(data))
    slides_html = []

    for slide_num, slide in enumerate(prs.slides, 1):
        parts = []
        title_text = ""

        for shape in slide.shapes:
            # Title
            if shape.has_text_frame:
                if shape == slide.shapes.title:
                    title_text = shape.text_frame.text.strip()
                else:
                    frame_html = _render_text_frame(shape.text_frame)
                    if frame_html.strip():
                        parts.append(frame_html)

            # Tables
            if shape.has_table:
                table = shape.table
                table_data = []
                for row in table.rows:
                    row_data = [cell.text.strip() for cell in row.cells]
                    table_data.append(row_data)
                parts.append(_render_table(table_data))

            # Images
            if hasattr(shape, "image"):
                try:
                    img_bytes = shape.image.blob
                    content_type = shape.image.content_type or "image/png"
                    b64 = base64.b64encode(img_bytes).decode("utf-8")
                    parts.append(
                        f'<img src="data:{content_type};base64,{b64}" alt="Slide {slide_num} image">'
                    )
                except Exception:
                    pass

        slide_title = f'<div class="doc-slide-title">Slide {slide_num}{": " + _esc(title_text) if title_text else ""}</div>'
        slide_body = "\n".join(parts) if parts else "<p><em>(Empty slide)</em></p>"
        slides_html.append(
            f'<div class="doc-slide">\n  {slide_title}\n  <div class="doc-slide-content">\n    {slide_body}\n  </div>\n</div>'
        )

    inner = "\n".join(slides_html) if slides_html else "<p><em>No slides found.</em></p>"
    return wrap_html(inner, filename)


def _render_text_frame(text_frame) -> str:
    """Render a PPTX text frame into HTML paragraphs with basic formatting."""
    paragraphs = []
    for para in text_frame.paragraphs:
        if not para.text.strip():
            continue

        runs_html = []
        for run in para.runs:
            text = _esc(run.text)
            if not text:
                continue
            if run.font.bold:
                text = f"<strong>{text}</strong>"
            if run.font.italic:
                text = f"<em>{text}</em>"
            if run.font.underline:
                text = f"<u>{text}</u>"
            runs_html.append(text)

        if runs_html:
            line = "".join(runs_html)
            # Detect bullet-style paragraphs
            if para.level and para.level > 0:
                paragraphs.append(f"<li style='margin-left:{para.level * 20}px;'>{line}</li>")
            else:
                paragraphs.append(f"<p>{line}</p>")

    return "\n".join(paragraphs)


# ── 4. XLSX (Excel) ──────────────────────────────────────────────────────────

def convert_xlsx(data: bytes, filename: str) -> str:
    """Converts an Excel XLSX file to HTML tables (one table per sheet)."""
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(data), data_only=True)
    sheets_html = []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        if ws.max_row is None or ws.max_row == 0:
            continue

        parts = [f"<h2>{_esc(sheet_name)}</h2>"]
        parts.append("<table>")

        for row_idx, row in enumerate(ws.iter_rows(values_only=True), 1):
            tag = "th" if row_idx == 1 else "td"
            parts.append("  <tr>")
            for cell in row:
                cell_val = _esc(str(cell)) if cell is not None else ""
                parts.append(f"    <{tag}>{cell_val}</{tag}>")
            parts.append("  </tr>")

        parts.append("</table>")
        sheets_html.append("\n".join(parts))

    inner = "\n<hr>\n".join(sheets_html) if sheets_html else "<p><em>No data found in workbook.</em></p>"
    return wrap_html(inner, filename)


# ── 5. Image (with OCR) ──────────────────────────────────────────────────────

def convert_image(data: bytes, filename: str) -> str:
    """
    Converts an image to HTML: embeds the image as base64 and extracts
    any text content via Tesseract OCR.
    """
    from PIL import Image

    # Determine MIME type from extension
    ext = Path(filename).suffix.lower().lstrip(".")
    mime_map = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp",
                "bmp": "bmp", "gif": "gif", "tiff": "tiff", "tif": "tiff"}
    mime_type = f"image/{mime_map.get(ext, 'png')}"

    b64 = base64.b64encode(data).decode("utf-8")
    parts = [f'<img src="data:{mime_type};base64,{b64}" alt="{_esc(filename)}">']

    # Attempt OCR
    try:
        import pytesseract
        img = Image.open(io.BytesIO(data))

        # Convert to RGB if needed (e.g., RGBA or palette images)
        if img.mode not in ("L", "RGB"):
            img = img.convert("RGB")

        ocr_text = pytesseract.image_to_string(img, lang="eng")
        if ocr_text.strip():
            lines = [_esc(l) for l in ocr_text.strip().split("\n") if l.strip()]
            ocr_body = "<br>\n".join(lines)
            parts.append(
                f'<div class="ocr-text-overlay">\n'
                f'  <strong>Extracted Text (OCR):</strong><br>\n'
                f'  {ocr_body}\n'
                f'</div>'
            )
    except ImportError:
        parts.append('<p style="color:#94a3b8;font-size:0.85em;"><em>Tesseract OCR not available. Install tesseract-ocr for text extraction.</em></p>')
    except Exception:
        pass

    inner = "\n".join(parts)
    return wrap_html(inner, filename)


# ── 6. SVG ────────────────────────────────────────────────────────────────────

def convert_svg(data: bytes, filename: str) -> str:
    """Embeds SVG directly into HTML (SVGs are already XML/HTML-compatible)."""
    svg_content = data.decode("utf-8", errors="replace")
    inner = f'<div class="svg-container" style="text-align:center;">\n{svg_content}\n</div>'
    return wrap_html(inner, filename)


# ── 7. Markdown ───────────────────────────────────────────────────────────────

def convert_markdown(data: bytes, filename: str) -> str:
    """Converts Markdown to HTML using the markdown library with extensions."""
    import markdown

    text = data.decode("utf-8", errors="replace")
    html_body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "codehilite", "toc", "nl2br", "sane_lists"],
    )
    return wrap_html(html_body, filename)


# ── 8. CSV / TSV ──────────────────────────────────────────────────────────────

def convert_csv(data: bytes, filename: str) -> str:
    """Converts CSV/TSV data into a clean HTML table."""
    text = data.decode("utf-8", errors="replace")

    # Detect delimiter
    delimiter = "\t" if filename.lower().endswith(".tsv") else ","
    try:
        dialect = csv.Sniffer().sniff(text[:4096])
        delimiter = dialect.delimiter
    except Exception:
        pass

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)

    if not rows:
        return wrap_html("<p><em>Empty CSV file.</em></p>", filename)

    parts = ["<table>"]
    for row_idx, row in enumerate(rows):
        tag = "th" if row_idx == 0 else "td"
        parts.append("  <tr>")
        for cell in row:
            parts.append(f"    <{tag}>{_esc(cell.strip())}</{tag}>")
        parts.append("  </tr>")
    parts.append("</table>")

    return wrap_html("\n".join(parts), filename)


# ── 9. Plain Text / Code ─────────────────────────────────────────────────────

def convert_text(data: bytes, filename: str) -> str:
    """Wraps plain text / code in a preformatted block."""
    text = data.decode("utf-8", errors="replace")
    ext = Path(filename).suffix.lower()

    if ext in (".json", ".xml", ".log"):
        inner = f"<pre><code>{_esc(text)}</code></pre>"
    else:
        # Convert line breaks to paragraphs for .txt
        paragraphs = []
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped:
                paragraphs.append(f"<p>{_esc(stripped)}</p>")
            else:
                paragraphs.append("<br>")
        inner = "\n".join(paragraphs)

    return wrap_html(inner, filename)


# ── 10. HTML Passthrough ─────────────────────────────────────────────────────

def convert_passthrough(data: bytes, filename: str) -> str:
    """If the uploaded file is already HTML, return it as-is."""
    return data.decode("utf-8", errors="replace")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HANDLER DISPATCH
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONVERTERS = {
    "pdf": convert_pdf,
    "docx": convert_docx,
    "pptx": convert_pptx,
    "xlsx": convert_xlsx,
    "image": convert_image,
    "svg": convert_svg,
    "markdown": convert_markdown,
    "csv": convert_csv,
    "text": convert_text,
    "passthrough": convert_passthrough,
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  API ENDPOINTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@app.get("/")
async def root():
    """Health check and documentation link."""
    return {
        "service": "Document-to-HTML API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "supported_formats": list(EXTENSION_MAP.keys()),
    }


@app.post("/convert")
async def convert_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF, DOCX, PPTX, XLSX, image, Markdown, CSV, TXT)
    and receive its HTML representation.

    Returns JSON:
        {
            "success": true,
            "filename": "resume.pdf",
            "content_type": "application/pdf",
            "size_bytes": 123456,
            "html": "<html>...</html>"
        }
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    # Read file bytes
    data = await file.read()

    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Determine file type
    ext = Path(file.filename).suffix.lower()
    handler_key = EXTENSION_MAP.get(ext)

    if not handler_key:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: '{ext}'. Supported: {', '.join(sorted(EXTENSION_MAP.keys()))}",
        )

    converter = CONVERTERS[handler_key]

    try:
        html_output = converter(data, file.filename)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Conversion failed for '{file.filename}': {str(e)}",
        )

    return JSONResponse(
        content={
            "success": True,
            "filename": file.filename,
            "content_type": file.content_type or "application/octet-stream",
            "size_bytes": len(data),
            "html": html_output,
        }
    )


@app.post("/convert/raw")
async def convert_document_raw(file: UploadFile = File(...)):
    """
    Same as /convert but returns ONLY the inner HTML body (no <html>/<head> wrapper).
    Useful when embedding the result inside an existing page.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    data = await file.read()

    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large.")
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    ext = Path(file.filename).suffix.lower()
    handler_key = EXTENSION_MAP.get(ext)
    if not handler_key:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: '{ext}'")

    converter = CONVERTERS[handler_key]

    try:
        html_output = converter(data, file.filename)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

    # Strip outer HTML wrapper — return only inner content
    # Look for doc-html-root div
    start_marker = '<div class="doc-html-root">'
    end_marker = "</div>\n</body>"
    start_idx = html_output.find(start_marker)
    end_idx = html_output.rfind(end_marker)

    if start_idx != -1 and end_idx != -1:
        inner = html_output[start_idx + len(start_marker): end_idx].strip()
    else:
        inner = html_output

    return JSONResponse(content={"success": True, "filename": file.filename, "html": inner})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
