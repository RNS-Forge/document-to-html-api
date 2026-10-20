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

## Configuration (.env)

Create a `.env` file in the root directory (or copy from `.env.example`):

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `LOCAL_RUN` | `true` | **`true`**: Serves an interactive drag-and-drop web testing UI at `http://localhost:8000/`.<br>**`false`**: Runs in pure API mode (returns JSON health check at `/`). |
| `PORT` | `8000` | Port for the FastAPI server. |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure .env (optional, defaults to LOCAL_RUN=true)
# See .env.example

# 3. (Optional) Install Tesseract for image OCR
#    Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
#    Ubuntu:  sudo apt install tesseract-ocr

# 4. Run the server
python app.py
# or
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### `GET /`
- **When `LOCAL_RUN=true`**: Returns the interactive drag-and-drop test page with real-time HTML preview, source viewer, and download options.
- **When `LOCAL_RUN=false`**: Health check. Returns service status and supported formats in JSON.

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

## Architecture & Accuracy Highlights

```
POST /convert
  → Detect file extension
  → Route to converter (pdf / docx / pptx / xlsx / image / markdown / csv / json / text)
  → Process elements in visual reading order
  → Convert all images to Base64 data URIs
  → Return { success, filename, html }
```

Each converter produces pixel-accurate, self-contained semantic HTML:
- **Base64 Everywhere**: All embedded images, pictures, and graphics are converted directly into Base64 data URIs (`data:image/...;base64,...`) — zero broken images or external dependencies.
- **PDF Visual Ordering**: Elements (headings, paragraphs, tables, images) are unified and sorted top-to-bottom and left-to-right (`y0`, `x0`) matching the exact visual layout. Tables have bounding box exclusion to prevent duplicate jumbled text.
- **DOCX Fidelity**: Mammoth semantic style mapping with automatic fallback to `python-docx` for complex documents.
- **PPTX Slide Cards**: Recursive shape hierarchy (including nested groups), run-level typography, table extraction, and collapsible speaker notes.
- **XLSX Multi-Sheet**: Interactive tab navigation for workbooks, cell formatting, merged cell (`rowspan`/`colspan`) handling, background colors, and embedded graphics.
- **Images**: Crisp responsive previews with metadata badges and optional Tesseract OCR for text recognition.

## Running Tests

Run the complete test suite covering all document formats and API endpoints:

```bash
python test_converters.py
```

## License

MIT
