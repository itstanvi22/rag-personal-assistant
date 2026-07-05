import pymupdf as fitz  # PyMuPDF
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def parse_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes, page by page."""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        num_pages = len(doc)  # get length BEFORE any close
        
        for page_num in range(num_pages):
            page = doc[page_num]
            page_text = page.get_text()
            if page_text.strip():
                text += f"\n[Page {page_num + 1}]\n{page_text}"
        
        doc.close()
        
        if not text.strip():
            raise ValueError("PDF appears to be empty or scanned (no extractable text)")
        
        logger.info(f"Parsed PDF: {num_pages} pages, {len(text)} characters extracted")
        return text
        
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"PDF parsing failed: {e}")
        raise ValueError(f"PDF parsing failed: {str(e)}")

def parse_txt(file_bytes: bytes) -> str:
    """Decode plain text file."""
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        # fallback encoding for files not in utf-8
        return file_bytes.decode("latin-1")

def parse_markdown(file_bytes: bytes) -> str:
    """Markdown is plain text — decode and return as-is."""
    return parse_txt(file_bytes)

def parse_document(file_bytes: bytes, filename: str) -> str:
    """
    Router function — detects file type by extension,
    calls the right parser, returns clean text.
    """
    extension = Path(filename).suffix.lower()
    
    parsers = {
        ".pdf": parse_pdf,
        ".txt": parse_txt,
        ".md":  parse_markdown,
    }
    
    if extension not in parsers:
        raise ValueError(f"Unsupported file type: {extension}. Supported: {list(parsers.keys())}")
    
    text = parsers[extension](file_bytes)
    
    if not text or not text.strip():
        raise ValueError(f"No text could be extracted from {filename}")
    
    return text