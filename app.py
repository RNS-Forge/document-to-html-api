"""
Document-to-HTML API — Accurate Universal Document Converter
============================================================
Converts PDF, DOCX, PPTX, XLSX, images, Markdown, CSV, and plain text
into pixel-accurate semantic HTML.

Modes (controlled via .env):
  LOCAL_RUN=true  → Serves a beautiful drag-and-drop upload test page at GET /
  LOCAL_RUN=false  → API-only mode, GET / returns JSON health-check

Run:
    pip install -r requirements.txt
    python app.py
"""

import io
import os
import csv
import base64
import traceback
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse

# ─── Configuration ────────────────────────────────────────────────────────────

LOCAL_RUN = os.getenv("LOCAL_RUN", "false").strip().lower() == "true"
PORT = int(os.getenv("PORT", "8000"))
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB

# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Document-to-HTML API",
    description="Converts PDF, DOCX, PPTX, XLSX, images, Markdown, CSV, TXT into accurate HTML.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Extension → Handler Mapping ─────────────────────────────────────────────

EXTENSION_MAP = {
    ".pdf": "pdf",
    ".docx": "docx", ".doc": "docx",
    ".pptx": "pptx", ".ppt": "pptx",
    ".xlsx": "xlsx", ".xls": "xlsx",
    ".png": "image", ".jpg": "image", ".jpeg": "image",
    ".webp": "image", ".bmp": "image", ".tiff": "image",
    ".tif": "image", ".gif": "image",
    ".svg": "svg",
    ".md": "markdown", ".markdown": "markdown",
    ".csv": "csv", ".tsv": "csv",
    ".txt": "text", ".log": "text", ".json": "text", ".xml": "text",
    ".html": "passthrough", ".htm": "passthrough",
}

# ─── Shared CSS ───────────────────────────────────────────────────────────────

SHARED_CSS = """
<style>
  .doc-root {
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    color: #1a1a1a; background: #fff; line-height: 1.6;
    padding: 28px 36px; max-width: 960px; margin: 0 auto;
    box-sizing: border-box; word-wrap: break-word;
  }
  .doc-root h1 { font-size: 1.75em; font-weight: 700; color: #111; border-bottom: 2px solid #e5e7eb; padding-bottom: 5px; margin: 0.6em 0 0.3em; }
  .doc-root h2 { font-size: 1.35em; font-weight: 700; color: #1e293b; margin: 0.5em 0 0.25em; }
  .doc-root h3 { font-size: 1.12em; font-weight: 600; color: #334155; margin: 0.4em 0 0.2em; }
  .doc-root h4 { font-size: 1em; font-weight: 600; color: #475569; margin: 0.35em 0 0.15em; }
  .doc-root p  { margin: 0.35em 0; font-size: 1em; }
  .doc-root ul, .doc-root ol { margin: 0.3em 0; padding-left: 1.6em; }
  .doc-root li { margin-bottom: 0.2em; }
  .doc-root a { color: #2563eb; text-decoration: underline; }
  .doc-root table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 0.92em; }
  .doc-root th, .doc-root td { border: 1px solid #d1d5db; padding: 7px 10px; text-align: left; vertical-align: top; }
  .doc-root th { background: #f1f5f9; font-weight: 700; color: #1e293b; }
  .doc-root tr:nth-child(even) td { background: #f8fafc; }
  .doc-root img { max-width: 100%; height: auto; display: block; margin: 8px 0; border-radius: 4px; }
  .doc-root pre { background: #f8f9fa; padding: 12px 16px; border-radius: 6px; overflow-x: auto; font-size: 0.88em; border: 1px solid #e5e7eb; }
  .doc-root code { font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace; }
  .doc-root blockquote { border-left: 4px solid #6366f1; padding: 8px 16px; margin: 12px 0; background: #f5f3ff; color: #4338ca; }
  .doc-root hr { border: none; border-top: 1.5px solid #e5e7eb; margin: 14px 0; }
  .doc-root strong { font-weight: 700; }
  .doc-root em { font-style: italic; }
  .page-sep { border-top: 2px dashed #cbd5e1; margin: 16px 0; }
  .slide-card { border: 1px solid #e2e8f0; border-radius: 10px; padding: 22px 26px; margin-bottom: 18px; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
  .slide-title { font-size: 1.4em; font-weight: 700; color: #1e293b; margin-bottom: 10px; border-bottom: 2px solid #6366f1; padding-bottom: 5px; }
  .slide-body { font-size: 1em; line-height: 1.5; }
  .ocr-box { margin-top: 10px; padding: 12px 16px; background: #fffbeb; border: 1px solid #fbbf24; border-radius: 6px; font-size: 0.92em; color: #92400e; }
  .page-label { font-size: 0.72em; color: #94a3b8; margin-bottom: 6px; letter-spacing: 0.5px; text-transform: uppercase; }
</style>
""".strip()


def _esc(text):
    """HTML-escape a string."""
    if not text:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


def wrap_html(body: str, title: str = "Converted Document") -> str:
    """Wrap inner HTML in a full document with shared CSS."""
    return (
        f"<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        f"  <meta charset=\"UTF-8\">\n"
        f"  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        f"  <title>{_esc(title)}</title>\n"
        f"  {SHARED_CSS}\n"
        f"</head>\n<body>\n"
        f"  <div class=\"doc-root\">\n{body}\n  </div>\n"
        f"</body>\n</html>"
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONVERTERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


# ── 1. PDF ────────────────────────────────────────────────────────────────────
#  Strategy (from PyMuPDF best practices):
#    1. Extract tables via page.find_tables() → tab.to_html()  (most accurate)
#    2. Extract text via page.get_text("dict") for font-aware heading detection
#    3. Extract images via page.get_images() + doc.extract_image(xref)
#    4. For scanned PDFs (no text layer), fallback to OCR via Tesseract
# ──────────────────────────────────────────────────────────────────────────────

def convert_pdf(data: bytes, filename: str) -> str:
    import fitz  # PyMuPDF

    doc = fitz.open(stream=data, filetype="pdf")
    total_pages = len(doc)
    pages_html = []

    for pg_num in range(total_pages):
        page = doc[pg_num]
        parts = []

        # ── Step 1: Collect table bounding boxes so we can exclude them from text ──
        table_rects = []
        table_html_blocks = []
        try:
            tab_finder = page.find_tables()
            for tab in tab_finder.tables:
                table_rects.append(fitz.Rect(tab.bbox))
                # Use PyMuPDF's built-in to_html() for maximum table accuracy
                try:
                    table_html_blocks.append(tab.to_html())
                except Exception:
                    # Fallback: manual table rendering
                    extracted = tab.extract()
                    table_html_blocks.append(_render_table(extracted))
        except Exception:
            pass

        # ── Step 2: Extract text blocks (dict) with font metadata ──
        text_dict = page.get_text("dict", flags=11)  # TEXT_PRESERVE_WHITESPACE + PRESERVE_IMAGES
        blocks = text_dict.get("blocks", [])

        text_found = False
        for block in blocks:
            block_rect = fitz.Rect(block["bbox"])

            # Skip blocks that overlap with detected tables
            if any(block_rect.intersects(tr) for tr in table_rects):
                continue

            if block["type"] == 0:  # Text block
                html = _render_pdf_text_block(block)
                if html.strip():
                    parts.append(html)
                    text_found = True

            elif block["type"] == 1:  # Image block
                img_bytes = block.get("image")
                if img_bytes:
                    ext = block.get("ext", "png")
                    mime = f"image/{ext}" if ext != "jpg" else "image/jpeg"
                    b64 = base64.b64encode(img_bytes).decode()
                    parts.append(f'<img src="data:{mime};base64,{b64}" alt="PDF image page {pg_num+1}">')

        # ── Step 3: Extract standalone images via get_images (catches ones dict misses) ──
        try:
            image_list = page.get_images(full=True)
            for img_info in image_list:
                xref = img_info[0]
                base_img = doc.extract_image(xref)
                if base_img:
                    img_bytes = base_img["image"]
                    img_ext = base_img.get("ext", "png")
                    mime = f"image/{img_ext}" if img_ext != "jpg" else "image/jpeg"
                    b64 = base64.b64encode(img_bytes).decode()
                    # Avoid duplicate if the block already added this image
                    img_tag = f'<img src="data:{mime};base64,{b64}" alt="Extracted image">'
                    if img_tag not in parts:
                        parts.append(img_tag)
        except Exception:
            pass

        # ── Step 4: Insert tables in page order ──
        for tbl_html in table_html_blocks:
            parts.append(tbl_html)

        # ── Step 5: OCR fallback for scanned pages ──
        if not text_found and not table_html_blocks:
            ocr_result = _ocr_pdf_page(page, pg_num, doc)
            if ocr_result:
                parts.append(ocr_result)

        # ── Assemble page ──
        if parts:
            content = "\n    ".join(parts)
            if total_pages > 1:
                pages_html.append(
                    f'<section data-page="{pg_num+1}">\n'
                    f'  <div class="page-label">Page {pg_num+1} of {total_pages}</div>\n'
                    f'  {content}\n'
                    f'</section>'
                )
                if pg_num < total_pages - 1:
                    pages_html.append('<div class="page-sep"></div>')
            else:
                pages_html.append(content)

    doc.close()
    inner = "\n".join(pages_html) if pages_html else "<p><em>No extractable content found in this PDF.</em></p>"
    return wrap_html(inner, filename)


def _render_pdf_text_block(block: dict) -> str:
    """Render a PyMuPDF dict text block into semantic HTML using font metrics."""
    lines_html = []
    max_font_size = 0

    for line in block.get("lines", []):
        spans_html = []
        for span in line.get("spans", []):
            text = span.get("text", "")
            if not text:
                continue

            size = span.get("size", 11)
            flags = span.get("flags", 0)
            color_int = span.get("color", 0)
            font_name = span.get("font", "")

            max_font_size = max(max_font_size, size)

            is_bold = bool(flags & 16) or "Bold" in font_name or "bold" in font_name
            is_italic = bool(flags & 2) or "Italic" in font_name or "italic" in font_name
            is_mono = "Mono" in font_name or "Courier" in font_name or "Code" in font_name

            escaped = _esc(text)

            if is_mono:
                escaped = f"<code>{escaped}</code>"
            if is_bold and is_italic:
                escaped = f"<strong><em>{escaped}</em></strong>"
            elif is_bold:
                escaped = f"<strong>{escaped}</strong>"
            elif is_italic:
                escaped = f"<em>{escaped}</em>"

            # Apply color if not black
            if color_int and color_int != 0:
                r = (color_int >> 16) & 0xFF
                g = (color_int >> 8) & 0xFF
                b = color_int & 0xFF
                if not (r < 30 and g < 30 and b < 30):  # skip near-black
                    escaped = f'<span style="color:rgb({r},{g},{b})">{escaped}</span>'

            spans_html.append(escaped)

        line_text = "".join(spans_html).strip()
        if line_text:
            lines_html.append(line_text)

    if not lines_html:
        return ""

    combined = " ".join(lines_html)

    # Determine semantic tag based on font size
    if max_font_size >= 22:
        return f"<h1>{combined}</h1>"
    elif max_font_size >= 17:
        return f"<h2>{combined}</h2>"
    elif max_font_size >= 14:
        return f"<h3>{combined}</h3>"
    elif max_font_size >= 12.5:
        return f"<h4>{combined}</h4>"
    else:
        # Detect bullet lines
        if combined.lstrip().startswith(("•", "●", "○", "▪", "■", "–", "—")):
            bullet_text = combined.lstrip("•●○▪■–— ").strip()
            return f"<ul><li>{bullet_text}</li></ul>"
        return f"<p>{combined}</p>"


def _render_table(table_data: list) -> str:
    """Render a 2D list into an HTML table."""
    if not table_data:
        return ""
    html = "<table>\n"
    for ri, row in enumerate(table_data):
        tag = "th" if ri == 0 else "td"
        html += "  <tr>"
        for cell in row:
            html += f"<{tag}>{_esc(str(cell) if cell is not None else '')}</{tag}>"
        html += "</tr>\n"
    html += "</table>"
    return html


def _ocr_pdf_page(page, pg_num: int, doc) -> str:
    """Render a PDF page as an image → Tesseract OCR → return HTML."""
    try:
        import pytesseract
        from PIL import Image
        import fitz

        mat = fitz.Matrix(2.0, 2.0)  # 2x resolution for better OCR
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")

        img = Image.open(io.BytesIO(img_data))
        ocr_text = pytesseract.image_to_string(img, lang="eng")

        parts = []
        b64 = base64.b64encode(img_data).decode()
        parts.append(f'<img src="data:image/png;base64,{b64}" alt="Scanned page {pg_num+1}">')

        if ocr_text.strip():
            lines = [_esc(l) for l in ocr_text.strip().split("\n") if l.strip()]
            parts.append(f'<div class="ocr-box"><strong>OCR Text:</strong><br>{"<br>".join(lines)}</div>')

        return "\n".join(parts)
    except ImportError:
        return ""
    except Exception:
        return ""


# ── 2. DOCX ──────────────────────────────────────────────────────────────────
#  Strategy (from mammoth best practices):
#    • mammoth converts semantic styles → clean HTML (headings, lists, tables)
#    • Custom style_map for common Word custom styles
#    • Images embedded as inline base64 data URIs via img_element handler
#    • Post-process: normalize empty paragraphs, fix nested lists
# ──────────────────────────────────────────────────────────────────────────────

def convert_docx(data: bytes, filename: str) -> str:
    import mammoth

    # Custom style map for common Word styles
    style_map = """
    p[style-name='Title'] => h1:fresh
    p[style-name='Subtitle'] => h2.subtitle:fresh
    p[style-name='Heading 1'] => h1:fresh
    p[style-name='Heading 2'] => h2:fresh
    p[style-name='Heading 3'] => h3:fresh
    p[style-name='Heading 4'] => h4:fresh
    p[style-name='Quote'] => blockquote > p:fresh
    p[style-name='Intense Quote'] => blockquote > p:fresh
    p[style-name='List Paragraph'] => li:fresh
    r[style-name='Strong'] => strong
    r[style-name='Emphasis'] => em
    r[style-name='Intense Emphasis'] => strong > em
    r[style-name='Subtle Reference'] => cite
    """

    result = mammoth.convert_to_html(
        io.BytesIO(data),
        style_map=style_map,
        convert_image=mammoth.images.img_element(_mammoth_img_handler),
    )

    inner_html = result.value
    warnings = result.messages

    # Post-process: clean up empty paragraphs mammoth sometimes generates
    inner_html = inner_html.replace("<p></p>", "")

    if warnings:
        items = "".join(f"<li>{_esc(str(w))}</li>" for w in warnings[:5])
        inner_html += (
            f'\n<details style="margin-top:16px;font-size:0.8em;color:#64748b;">'
            f'<summary>Conversion Notes ({len(warnings)})</summary>'
            f'<ul>{items}</ul></details>'
        )

    return wrap_html(inner_html, filename)


def _mammoth_img_handler(image):
    """Embed DOCX images as inline base64 data URIs."""
    with image.open() as stream:
        img_bytes = stream.read()
    ct = image.content_type or "image/png"
    b64 = base64.b64encode(img_bytes).decode()
    return {"src": f"data:{ct};base64,{b64}"}


# ── 3. PPTX ──────────────────────────────────────────────────────────────────
#  Strategy (from python-pptx best practices):
#    • Each slide → styled card with slide number + title
#    • Iterate shapes: text frames → styled paragraphs with run-level formatting
#    • Tables → semantic HTML tables
#    • Images → base64 embedded
#    • Preserve bold, italic, underline, font size, font color per run
# ──────────────────────────────────────────────────────────────────────────────

def convert_pptx(data: bytes, filename: str) -> str:
    from pptx import Presentation
    from pptx.util import Pt, Emu
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    prs = Presentation(io.BytesIO(data))
    slides_html = []

    for s_num, slide in enumerate(prs.slides, 1):
        parts = []
        title_text = ""

        # Sort shapes by top position then left, to approximate visual reading order
        shapes = sorted(slide.shapes, key=lambda s: (s.top or 0, s.left or 0))

        for shape in shapes:
            # ── Title shape ──
            if shape == slide.shapes.title and shape.has_text_frame:
                title_text = shape.text_frame.text.strip()
                continue

            # ── Text frames (with run-level formatting) ──
            if shape.has_text_frame:
                frame_html = _render_pptx_text_frame(shape.text_frame)
                if frame_html.strip():
                    parts.append(frame_html)

            # ── Tables ──
            if shape.has_table:
                tbl = shape.table
                rows = []
                for row in tbl.rows:
                    cells = [cell.text.strip() for cell in row.cells]
                    rows.append(cells)
                if rows:
                    parts.append(_render_table(rows))

            # ── Images ──
            try:
                if shape.shape_type == MSO_SHAPE_TYPE.PICTURE or (hasattr(shape, "image") and shape.image):
                    img_blob = shape.image.blob
                    ct = shape.image.content_type or "image/png"
                    b64 = base64.b64encode(img_blob).decode()
                    parts.append(f'<img src="data:{ct};base64,{b64}" alt="Slide {s_num} image">')
            except Exception:
                pass

        # Build slide card
        slide_title = f'<div class="slide-title">Slide {s_num}' + (f': {_esc(title_text)}' if title_text else '') + '</div>'
        body = "\n    ".join(parts) if parts else "<p><em>(Empty slide)</em></p>"
        slides_html.append(
            f'<div class="slide-card">\n  {slide_title}\n  <div class="slide-body">\n    {body}\n  </div>\n</div>'
        )

    inner = "\n".join(slides_html) if slides_html else "<p><em>No slides found.</em></p>"
    return wrap_html(inner, filename)


def _render_pptx_text_frame(text_frame) -> str:
    """Render a PPTX text frame with per-run formatting (bold, italic, underline, color, size)."""
    paras = []
    for para in text_frame.paragraphs:
        if not para.text.strip():
            continue

        runs_html = []
        for run in para.runs:
            text = _esc(run.text)
            if not text:
                continue

            styles = []
            if run.font.bold:
                text = f"<strong>{text}</strong>"
            if run.font.italic:
                text = f"<em>{text}</em>"
            if run.font.underline:
                text = f"<u>{text}</u>"

            # Font size
            if run.font.size:
                pt = run.font.size.pt
                if pt:
                    styles.append(f"font-size:{pt}pt")

            # Font color
            try:
                if run.font.color and run.font.color.rgb:
                    rgb = str(run.font.color.rgb)
                    styles.append(f"color:#{rgb}")
            except Exception:
                pass

            if styles:
                text = f'<span style="{";".join(styles)}">{text}</span>'

            runs_html.append(text)

        if runs_html:
            line = "".join(runs_html)
            # Detect list-style paragraphs by indent level
            level = para.level or 0
            if level > 0:
                paras.append(f'<li style="margin-left:{level * 24}px">{line}</li>')
            else:
                paras.append(f"<p>{line}</p>")

    return "\n".join(paras)


# ── 4. XLSX ──────────────────────────────────────────────────────────────────
#  Strategy: openpyxl with merged-cell handling, bold detection, per-sheet tables
# ──────────────────────────────────────────────────────────────────────────────

def convert_xlsx(data: bytes, filename: str) -> str:
    from openpyxl import load_workbook
    from openpyxl.utils import get_column_letter

    wb = load_workbook(io.BytesIO(data), data_only=True)
    sheets_html = []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        if ws.max_row is None or ws.max_row == 0:
            continue

        parts = [f"<h2>{_esc(sheet_name)}</h2>", "<table>"]

        # Collect merged cell ranges for proper spanning
        merged = {}
        skip_cells = set()
        for merge_range in ws.merged_cells.ranges:
            min_row, min_col = merge_range.min_row, merge_range.min_col
            max_row, max_col = merge_range.max_row, merge_range.max_col
            merged[(min_row, min_col)] = (max_row - min_row + 1, max_col - min_col + 1)
            for r in range(min_row, max_row + 1):
                for c in range(min_col, max_col + 1):
                    if (r, c) != (min_row, min_col):
                        skip_cells.add((r, c))

        for row_idx, row in enumerate(ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=ws.max_column), 1):
            tag = "th" if row_idx == 1 else "td"
            parts.append("  <tr>")
            for cell in row:
                coord = (cell.row, cell.column)
                if coord in skip_cells:
                    continue

                val = _esc(str(cell.value)) if cell.value is not None else ""

                # Bold detection
                try:
                    if cell.font and cell.font.bold:
                        val = f"<strong>{val}</strong>"
                except Exception:
                    pass

                attrs = ""
                if coord in merged:
                    rowspan, colspan = merged[coord]
                    if rowspan > 1:
                        attrs += f' rowspan="{rowspan}"'
                    if colspan > 1:
                        attrs += f' colspan="{colspan}"'

                parts.append(f"    <{tag}{attrs}>{val}</{tag}>")
            parts.append("  </tr>")

        parts.append("</table>")
        sheets_html.append("\n".join(parts))

    inner = "\n<hr>\n".join(sheets_html) if sheets_html else "<p><em>No data found.</em></p>"
    return wrap_html(inner, filename)


# ── 5. Image (with OCR) ──────────────────────────────────────────────────────

def convert_image(data: bytes, filename: str) -> str:
    from PIL import Image

    ext = Path(filename).suffix.lower().lstrip(".")
    mime_map = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp",
                "bmp": "bmp", "gif": "gif", "tiff": "tiff", "tif": "tiff"}
    mime = f"image/{mime_map.get(ext, 'png')}"

    b64 = base64.b64encode(data).decode()
    parts = [f'<img src="data:{mime};base64,{b64}" alt="{_esc(filename)}">']

    # OCR
    try:
        import pytesseract
        img = Image.open(io.BytesIO(data))
        if img.mode not in ("L", "RGB"):
            img = img.convert("RGB")

        ocr_text = pytesseract.image_to_string(img, lang="eng")
        if ocr_text.strip():
            lines = [_esc(l) for l in ocr_text.strip().split("\n") if l.strip()]
            parts.append(f'<div class="ocr-box"><strong>Extracted Text (OCR):</strong><br>{"<br>".join(lines)}</div>')
    except ImportError:
        parts.append('<p style="color:#94a3b8;font-size:0.85em;"><em>Tesseract not installed — OCR skipped.</em></p>')
    except Exception:
        pass

    return wrap_html("\n".join(parts), filename)


# ── 6. SVG ────────────────────────────────────────────────────────────────────

def convert_svg(data: bytes, filename: str) -> str:
    svg = data.decode("utf-8", errors="replace")
    return wrap_html(f'<div style="text-align:center">{svg}</div>', filename)


# ── 7. Markdown ───────────────────────────────────────────────────────────────

def convert_markdown(data: bytes, filename: str) -> str:
    import markdown
    text = data.decode("utf-8", errors="replace")
    html = markdown.markdown(text, extensions=["tables", "fenced_code", "codehilite", "toc", "nl2br", "sane_lists"])
    return wrap_html(html, filename)


# ── 8. CSV / TSV ──────────────────────────────────────────────────────────────

def convert_csv(data: bytes, filename: str) -> str:
    text = data.decode("utf-8", errors="replace")
    delim = "\t" if filename.lower().endswith(".tsv") else ","
    try:
        dialect = csv.Sniffer().sniff(text[:4096])
        delim = dialect.delimiter
    except Exception:
        pass

    reader = csv.reader(io.StringIO(text), delimiter=delim)
    rows = list(reader)
    if not rows:
        return wrap_html("<p><em>Empty file.</em></p>", filename)

    parts = ["<table>"]
    for ri, row in enumerate(rows):
        tag = "th" if ri == 0 else "td"
        parts.append("  <tr>" + "".join(f"<{tag}>{_esc(c.strip())}</{tag}>" for c in row) + "</tr>")
    parts.append("</table>")
    return wrap_html("\n".join(parts), filename)


# ── 9. Plain Text ─────────────────────────────────────────────────────────────

def convert_text(data: bytes, filename: str) -> str:
    text = data.decode("utf-8", errors="replace")
    ext = Path(filename).suffix.lower()

    if ext in (".json", ".xml", ".log"):
        return wrap_html(f"<pre><code>{_esc(text)}</code></pre>", filename)

    paras = []
    for line in text.split("\n"):
        s = line.strip()
        if s:
            paras.append(f"<p>{_esc(s)}</p>")
        else:
            paras.append("<br>")
    return wrap_html("\n".join(paras), filename)


# ── 10. HTML Passthrough ──────────────────────────────────────────────────────

def convert_passthrough(data: bytes, filename: str) -> str:
    return data.decode("utf-8", errors="replace")


# ─── Handler Dispatch ─────────────────────────────────────────────────────────

CONVERTERS = {
    "pdf": convert_pdf, "docx": convert_docx, "pptx": convert_pptx,
    "xlsx": convert_xlsx, "image": convert_image, "svg": convert_svg,
    "markdown": convert_markdown, "csv": convert_csv, "text": convert_text,
    "passthrough": convert_passthrough,
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOCAL TEST PAGE (only served when LOCAL_RUN=true in .env)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LOCAL_TEST_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Document-to-HTML Converter — Local Test</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', system-ui, sans-serif;
      background: #0f0f1a;
      color: #e2e8f0;
      min-height: 100vh;
      display: flex; flex-direction: column; align-items: center;
      padding: 40px 20px;
    }
    .header { text-align: center; margin-bottom: 32px; }
    .header h1 {
      font-size: 2.2rem; font-weight: 800;
      background: linear-gradient(135deg, #6366f1, #06b6d4);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      margin-bottom: 6px;
    }
    .header p { color: #94a3b8; font-size: 0.95rem; }
    .badge-row { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; margin-top: 14px; }
    .badge {
      font-size: 0.7rem; font-weight: 600; padding: 3px 10px;
      border-radius: 999px; background: rgba(99,102,241,0.15);
      color: #818cf8; border: 1px solid rgba(99,102,241,0.25);
      text-transform: uppercase; letter-spacing: 0.4px;
    }
    .card {
      width: 100%; max-width: 720px;
      background: rgba(30,30,50,0.7); backdrop-filter: blur(16px);
      border: 1px solid rgba(99,102,241,0.2); border-radius: 16px;
      padding: 32px; margin-bottom: 28px;
    }
    .drop-zone {
      border: 2px dashed rgba(99,102,241,0.4); border-radius: 14px;
      padding: 48px 24px; text-align: center; cursor: pointer;
      transition: all 0.3s ease; position: relative;
    }
    .drop-zone:hover, .drop-zone.active {
      border-color: #6366f1; background: rgba(99,102,241,0.08);
      box-shadow: 0 0 30px rgba(99,102,241,0.1);
    }
    .drop-zone svg { margin: 0 auto 14px; display: block; opacity: 0.7; }
    .drop-zone p { color: #94a3b8; font-size: 0.9rem; }
    .drop-zone .drop-label { font-weight: 600; color: #c7d2fe; font-size: 1rem; margin-bottom: 4px; }
    .drop-zone input[type="file"] { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
    .btn-convert {
      display: block; width: 100%; padding: 14px;
      background: linear-gradient(135deg, #6366f1, #4f46e5);
      color: #fff; font-weight: 700; font-size: 1rem;
      border: none; border-radius: 10px; cursor: pointer;
      margin-top: 18px; transition: all 0.2s ease;
    }
    .btn-convert:hover { transform: translateY(-1px); box-shadow: 0 4px 20px rgba(99,102,241,0.4); }
    .btn-convert:disabled { opacity: 0.5; cursor: not-allowed; transform: none; box-shadow: none; }
    .file-info {
      margin-top: 14px; padding: 10px 14px;
      background: rgba(99,102,241,0.1); border-radius: 8px;
      font-size: 0.82rem; color: #c7d2fe; display: none;
    }
    .file-info .fname { font-weight: 600; }
    .status {
      text-align: center; margin-top: 14px; font-size: 0.85rem; color: #94a3b8; display: none;
    }
    .status.error { color: #f87171; }
    .status.success { color: #34d399; }
    .result-card { display: none; }
    .tab-row { display: flex; gap: 0; margin-bottom: 0; }
    .tab-btn {
      flex: 1; padding: 10px; text-align: center;
      font-size: 0.82rem; font-weight: 600; cursor: pointer;
      background: rgba(30,30,50,0.5); color: #94a3b8;
      border: 1px solid rgba(99,102,241,0.15); border-bottom: none;
      transition: all 0.2s ease;
    }
    .tab-btn:first-child { border-radius: 10px 0 0 0; }
    .tab-btn:last-child { border-radius: 0 10px 0 0; }
    .tab-btn.active { background: rgba(99,102,241,0.15); color: #c7d2fe; }
    .tab-content {
      border: 1px solid rgba(99,102,241,0.15); border-radius: 0 0 10px 10px;
      min-height: 300px; max-height: 600px; overflow: auto;
      background: #fff;
    }
    .tab-content.source-tab {
      background: #1e1e2e; color: #e2e8f0;
      padding: 16px; font-family: 'Cascadia Code', monospace;
      font-size: 0.78rem; white-space: pre-wrap; word-break: break-all;
    }
    .tab-content iframe { width: 100%; height: 500px; border: none; }
    .btn-row { display: flex; gap: 10px; margin-top: 14px; }
    .btn-dl {
      flex: 1; padding: 10px; text-align: center;
      border-radius: 8px; font-weight: 600; font-size: 0.85rem;
      cursor: pointer; border: none; transition: all 0.2s ease;
    }
    .btn-dl.primary { background: #6366f1; color: #fff; }
    .btn-dl.primary:hover { background: #4f46e5; }
    .btn-dl.secondary { background: rgba(99,102,241,0.12); color: #c7d2fe; border: 1px solid rgba(99,102,241,0.25); }
    .btn-dl.secondary:hover { background: rgba(99,102,241,0.2); }
    .spinner { display: inline-block; width: 16px; height: 16px; border: 2px solid #fff4; border-top-color: #fff; border-radius: 50%; animation: spin 0.6s linear infinite; vertical-align: middle; margin-right: 6px; }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <div class="header">
    <h1>Document → HTML</h1>
    <p>Accurate universal document-to-HTML converter API — Local Test Mode</p>
    <div class="badge-row">
      <span class="badge">PDF</span><span class="badge">DOCX</span><span class="badge">PPTX</span>
      <span class="badge">XLSX</span><span class="badge">PNG / JPG</span><span class="badge">SVG</span>
      <span class="badge">Markdown</span><span class="badge">CSV</span><span class="badge">TXT</span>
    </div>
  </div>

  <div class="card">
    <div class="drop-zone" id="dropZone">
      <input type="file" id="fileInput" accept=".pdf,.docx,.doc,.pptx,.ppt,.xlsx,.xls,.png,.jpg,.jpeg,.webp,.bmp,.tiff,.tif,.gif,.svg,.md,.csv,.tsv,.txt,.log,.json,.xml,.html,.htm">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
      <p class="drop-label">Drop your file here or click to browse</p>
      <p>Supports PDF, DOCX, PPTX, XLSX, Images, Markdown, CSV, TXT</p>
    </div>
    <div class="file-info" id="fileInfo">
      Selected: <span class="fname" id="fileName"></span> — <span id="fileSize"></span>
    </div>
    <button class="btn-convert" id="btnConvert" disabled>Convert to HTML</button>
    <div class="status" id="status"></div>
  </div>

  <div class="card result-card" id="resultCard">
    <div class="tab-row">
      <div class="tab-btn active" data-tab="preview" id="tabPreview">HTML Preview</div>
      <div class="tab-btn" data-tab="source" id="tabSource">Source Code</div>
    </div>
    <div class="tab-content" id="previewPane"><iframe id="previewFrame"></iframe></div>
    <div class="tab-content source-tab" id="sourcePane" style="display:none"></div>
    <div class="btn-row">
      <button class="btn-dl primary" id="btnDownload">Download HTML</button>
      <button class="btn-dl secondary" id="btnCopy">Copy Source</button>
    </div>
  </div>

<script>
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const btnConvert = document.getElementById('btnConvert');
const status = document.getElementById('status');
const resultCard = document.getElementById('resultCard');
const previewFrame = document.getElementById('previewFrame');
const sourcePane = document.getElementById('sourcePane');

let selectedFile = null;
let resultHtml = '';

// Drag-and-drop
['dragenter','dragover'].forEach(e => dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.add('active'); }));
['dragleave','drop'].forEach(e => dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.remove('active'); }));
dropZone.addEventListener('drop', ev => { if(ev.dataTransfer.files.length) { fileInput.files = ev.dataTransfer.files; handleFile(ev.dataTransfer.files[0]); }});
fileInput.addEventListener('change', () => { if(fileInput.files.length) handleFile(fileInput.files[0]); });

function handleFile(f) {
  selectedFile = f;
  fileName.textContent = f.name;
  fileSize.textContent = (f.size / 1024).toFixed(1) + ' KB';
  fileInfo.style.display = 'block';
  btnConvert.disabled = false;
  status.style.display = 'none';
  resultCard.style.display = 'none';
}

btnConvert.addEventListener('click', async () => {
  if(!selectedFile) return;
  btnConvert.disabled = true;
  btnConvert.innerHTML = '<span class="spinner"></span>Converting...';
  status.className = 'status'; status.style.display = 'block';
  status.textContent = 'Processing ' + selectedFile.name + '...';

  const fd = new FormData();
  fd.append('file', selectedFile);

  try {
    const res = await fetch('/convert', { method: 'POST', body: fd });
    const json = await res.json();
    if(!res.ok) throw new Error(json.detail || 'Conversion failed');

    resultHtml = json.html;
    // Preview
    previewFrame.srcdoc = resultHtml;
    // Source
    sourcePane.textContent = resultHtml;
    resultCard.style.display = 'block';
    status.className = 'status success';
    status.textContent = 'Converted successfully! (' + json.size_bytes + ' bytes processed)';
  } catch(err) {
    status.className = 'status error';
    status.textContent = 'Error: ' + err.message;
  }
  btnConvert.disabled = false;
  btnConvert.textContent = 'Convert to HTML';
});

// Tabs
document.getElementById('tabPreview').addEventListener('click', () => {
  document.getElementById('tabPreview').classList.add('active');
  document.getElementById('tabSource').classList.remove('active');
  document.getElementById('previewPane').style.display = 'block';
  sourcePane.style.display = 'none';
});
document.getElementById('tabSource').addEventListener('click', () => {
  document.getElementById('tabSource').classList.add('active');
  document.getElementById('tabPreview').classList.remove('active');
  sourcePane.style.display = 'block';
  document.getElementById('previewPane').style.display = 'none';
});

// Download
document.getElementById('btnDownload').addEventListener('click', () => {
  if(!resultHtml) return;
  const blob = new Blob([resultHtml], { type: 'text/html' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = (selectedFile?.name || 'document').replace(/\\.[^.]+$/, '') + '.html';
  a.click();
});

// Copy
document.getElementById('btnCopy').addEventListener('click', () => {
  if(!resultHtml) return;
  navigator.clipboard.writeText(resultHtml).then(() => {
    const btn = document.getElementById('btnCopy');
    btn.textContent = 'Copied!';
    setTimeout(() => btn.textContent = 'Copy Source', 1500);
  });
});
</script>
</body>
</html>"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API ENDPOINTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@app.get("/")
async def root():
    """
    LOCAL_RUN=true  → serves the browser upload/test page
    LOCAL_RUN=false → returns JSON health-check
    """
    if LOCAL_RUN:
        return HTMLResponse(content=LOCAL_TEST_HTML)

    return {
        "service": "Document-to-HTML API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "mode": "api-only",
        "supported_formats": list(EXTENSION_MAP.keys()),
    }


@app.post("/convert")
async def convert_document(file: UploadFile = File(...)):
    """Upload any document and receive its accurate HTML representation."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large. Max {MAX_UPLOAD_BYTES // (1024*1024)} MB.")
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="File is empty.")

    ext = Path(file.filename).suffix.lower()
    handler_key = EXTENSION_MAP.get(ext)
    if not handler_key:
        raise HTTPException(status_code=415, detail=f"Unsupported: '{ext}'. Supported: {', '.join(sorted(EXTENSION_MAP.keys()))}")

    try:
        html = CONVERTERS[handler_key](data, file.filename)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

    return JSONResponse(content={
        "success": True,
        "filename": file.filename,
        "content_type": file.content_type or "application/octet-stream",
        "size_bytes": len(data),
        "html": html,
    })


@app.post("/convert/raw")
async def convert_raw(file: UploadFile = File(...)):
    """Same as /convert but returns only the inner HTML (no <html>/<head> wrapper)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large.")
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="File is empty.")

    ext = Path(file.filename).suffix.lower()
    handler_key = EXTENSION_MAP.get(ext)
    if not handler_key:
        raise HTTPException(status_code=415, detail=f"Unsupported: '{ext}'")

    try:
        html = CONVERTERS[handler_key](data, file.filename)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

    # Strip outer wrapper
    marker_start = '<div class="doc-root">'
    marker_end = "</div>\n</body>"
    i = html.find(marker_start)
    j = html.rfind(marker_end)
    inner = html[i + len(marker_start):j].strip() if i != -1 and j != -1 else html

    return JSONResponse(content={"success": True, "filename": file.filename, "html": inner})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    import uvicorn
    print(f"\\n  🚀 Document-to-HTML API v2.0")
    print(f"  Mode: {'LOCAL (test page at /)' if LOCAL_RUN else 'API-only'}")
    print(f"  Port: {PORT}")
    print(f"  Docs: http://localhost:{PORT}/docs\\n")
    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=True)
