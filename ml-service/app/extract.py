"""Resume file upload support: extract plain text from PDF / DOCX / TXT uploads.

PDF note: pypdf reads embedded text layers only. Scanned/image-only PDFs (common with
CVs exported as images) contain no text layer - we detect that and tell the user to
paste text instead of failing silently."""
import io


def extract_text(filename: str, data: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".txt"):
        for enc in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                return data.decode(enc)
            except UnicodeDecodeError:
                continue
        return data.decode("utf-8", errors="replace")

    if name.endswith(".docx"):
        from docx import Document
        doc = Document(io.BytesIO(data))
        parts = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:                     # skills are often in tables
            for row in table.rows:
                cell_text = " | ".join(c.text.strip() for c in row.cells if c.text.strip())
                if cell_text:
                    parts.append(cell_text)
        return "\n".join(parts)

    if name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                pages.append("")                     # one broken page shouldn't kill the rest
        return "\n".join(pages)

    raise ValueError("Unsupported file type - upload a .pdf, .docx or .txt file")
