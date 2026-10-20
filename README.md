# Document-to-HTML API

A Python FastAPI service that converts **any document** into accurate semantic HTML.

## Supported Formats

| Format | Extensions | Engine |
|--------|-----------|--------|
| PDF | `.pdf` | PyMuPDF (text + images + tables + OCR fallback) |
| Word | `.docx`, `.doc` | Mammoth (headings, lists, bold, images) |
| PowerPoint | `.pptx`, `.ppt` | python-pptx (slides → styled cards) |
| Excel | `.xlsx`, `.xls` | openpyxl (sheets → tables) |
| Images | `.png`, `.jpg`, `.webp`, `.bmp`, `.tiff`, `.gif` | Base64 embed + Tesseract OCR |
| SVG | `.svg` | Direct embed |
| Markdown | `.md` | Python-Markdown with extensions |
| CSV / TSV | `.csv`, `.tsv` | Auto-detect delimiter → table |
| Plain Text | `.txt`, `.log`, `.json`, `.xml` | Semantic paragraphs / code blocks |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Install Tesseract for image OCR
#    Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
#    Ubuntu:  sudo apt install tesseract-ocr

# 3. Run the server
python app.py
# or
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### `GET /`
Health check. Returns service status and supported formats.

### `POST /convert`
Upload a file and get the **full HTML document** (with `<html>`, `<head>`, CSS).

```bash
curl -X POST http://localhost:8000/convert \
  -F "file=@resume.pdf"
```

**Response:**
```json
{
  "success": true,
  "filename": "resume.pdf",
  "content_type": "application/pdf",
  "size_bytes": 123456,
  "html": "<!DOCTYPE html>..."
}
```

### `POST /convert/raw`
Same as `/convert` but returns **only the inner HTML body** — no wrapper. Useful for embedding into an existing page.

```bash
curl -X POST http://localhost:8000/convert/raw \
  -F "file=@resume.pdf"
```

## Interactive Docs

Once running, visit **http://localhost:8000/docs** for the Swagger UI where you can test uploads directly in the browser.

## Architecture

```
POST /convert
  → Detect file extension
  → Route to converter (pdf / docx / pptx / xlsx / image / markdown / csv / text)
  → Return { success, filename, html }
```

Each converter produces semantic, styled HTML with:
- **Headings** detected by font size (PDF) or document structure (DOCX/PPTX)
- **Tables** preserved from PDFs, DOCX, PPTX, XLSX, and CSV
- **Images** embedded as inline base64 data URIs (zero external dependencies)
- **OCR** via Tesseract for scanned PDFs and images
- **Shared CSS** for consistent, clean rendering across all formats

## License

MIT
