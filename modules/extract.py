"""
modules/extract.py – Text extraction from PDF, TXT, and images.
"""
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_text(uploaded_file) -> str:
    """Accept a Streamlit UploadedFile (txt/pdf/png/jpg). Return plain text."""
    if uploaded_file is None:
        return ""

    name = uploaded_file.name.lower()

    if name.endswith(".txt"):
        return _extract_txt(uploaded_file)
    elif name.endswith(".pdf"):
        return _extract_pdf(uploaded_file)
    elif name.endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
        return _extract_image(uploaded_file)
    else:
        # Try as plain text
        try:
            return uploaded_file.read().decode("utf-8", errors="replace")
        except Exception:
            return ""


def extract_text_from_path(file_path: str) -> str:
    """Extract text from a file path (used for sample data loading)."""
    if file_path.lower().endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif file_path.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            logger.warning("pypdf not installed; cannot read PDF.")
            return ""
    return ""


def _extract_txt(uploaded_file) -> str:
    """Extract text from a TXT file."""
    try:
        content = uploaded_file.read()
        if isinstance(content, bytes):
            return content.decode("utf-8", errors="replace")
        return str(content)
    except Exception as e:
        logger.error("TXT extraction failed: %s", e)
        return ""


def _extract_pdf(uploaded_file) -> str:
    """Extract text from a PDF file using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(uploaded_file.read()))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)
    except ImportError:
        logger.warning("pypdf not installed; cannot read PDF.")
        return "[PDF extraction requires pypdf. Install with: pip install pypdf]"
    except Exception as e:
        logger.error("PDF extraction failed: %s", e)
        return ""


def _extract_image(uploaded_file) -> str:
    """Extract text from an image using OpenCV + Tesseract OCR."""
    try:
        import cv2
        import numpy as np
        import pytesseract

        file_bytes = np.frombuffer(uploaded_file.read(), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if img is None:
            return "[Could not decode image]"

        # Preprocess: grayscale, threshold
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        text = pytesseract.image_to_string(gray)
        return text.strip()
    except ImportError:
        logger.warning("OpenCV or pytesseract not installed; cannot do OCR.")
        return "[OCR requires opencv-python and pytesseract. Install both and ensure Tesseract is on your PATH.]"
    except Exception as e:
        logger.error("OCR failed: %s", e)
        return ""


def word_count(text: str) -> int:
    """Count words in text."""
    return len(text.split()) if text else 0
