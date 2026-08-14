#!/usr/bin/env python3
"""
doc_intake.py — Multi-format document text extractor for USAP skills.

Extracts plain text from any supported document format with graceful fallbacks.
No hard external dependencies — stdlib-only for text formats; optional deps for
binary formats (pdfminer.six, PyPDF2, python-docx, PyYAML).

Usage:
  python shared/scripts/doc_intake.py --input <path>
  python shared/scripts/doc_intake.py --input document.pdf

Supported formats:
  .md .txt .rst     — stdlib read
  .json             — recursive string extraction (stdlib)
  .yaml .yml        — PyYAML if available; else line-by-line string extraction
  .pdf              — pdfminer.six → PyPDF2 → fallback error
  .docx             — python-docx → fallback error

Output (stdout):
  JSON with fields: document_type_hint, text, word_count, extraction_method
  On fallback: JSON with 'error' field instead of 'text'
"""

import argparse
import json
import sys
from pathlib import Path


def _extract_strings_from_json(obj, depth: int = 0) -> list[str]:
    """Recursively extract all string values from a JSON structure."""
    if depth > 20:
        return []
    strings = []
    if isinstance(obj, str):
        strings.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            strings.extend(_extract_strings_from_json(v, depth + 1))
    elif isinstance(obj, list):
        for item in obj:
            strings.extend(_extract_strings_from_json(item, depth + 1))
    return strings


def extract_plaintext(path: Path) -> dict:
    """Extract text from .md, .txt, .rst files using stdlib."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return {
            "document_type_hint": "markdown" if path.suffix == ".md" else "plaintext",
            "text": text,
            "word_count": len(text.split()),
            "extraction_method": "stdlib",
        }
    except OSError as exc:
        return {
            "error": f"Failed to read file: {exc}",
            "document_type_hint": "plaintext",
            "extraction_method": "stdlib",
        }


def extract_json(path: Path) -> dict:
    """Extract all string values from a JSON file using stdlib."""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
        parsed = json.loads(raw)
        strings = _extract_strings_from_json(parsed)
        text = "\n".join(strings)
        return {
            "document_type_hint": "json",
            "text": text,
            "word_count": len(text.split()),
            "extraction_method": "stdlib",
        }
    except json.JSONDecodeError as exc:
        return {
            "error": f"Invalid JSON: {exc}",
            "document_type_hint": "json",
            "extraction_method": "stdlib",
        }
    except OSError as exc:
        return {
            "error": f"Failed to read file: {exc}",
            "document_type_hint": "json",
            "extraction_method": "stdlib",
        }


def extract_yaml(path: Path) -> dict:
    """Extract text from YAML using PyYAML if available; else line-by-line fallback."""
    try:
        import yaml  # type: ignore

        raw = path.read_text(encoding="utf-8", errors="replace")
        parsed = yaml.safe_load(raw)
        strings = _extract_strings_from_json(parsed)  # same recursive logic works
        text = "\n".join(strings)
        return {
            "document_type_hint": "yaml",
            "text": text,
            "word_count": len(text.split()),
            "extraction_method": "pyyaml",
        }
    except ImportError:
        # PyYAML not available — extract non-key lines as plain text
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
            lines = []
            for line in raw.splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    # Strip YAML key prefix (key: value → take the value part)
                    if ": " in stripped:
                        _, _, value = stripped.partition(": ")
                        if value:
                            lines.append(value)
                    else:
                        lines.append(stripped)
            text = "\n".join(lines)
            return {
                "document_type_hint": "yaml",
                "text": text,
                "word_count": len(text.split()),
                "extraction_method": "stdlib-line-extraction",
            }
        except OSError as exc:
            return {
                "error": f"Failed to read file: {exc}",
                "document_type_hint": "yaml",
                "extraction_method": "stdlib-line-extraction",
            }
    except Exception as exc:  # noqa: BLE001
        return {
            "error": f"YAML parse error: {exc}",
            "document_type_hint": "yaml",
            "extraction_method": "pyyaml",
        }


def extract_pdf(path: Path) -> dict:
    """Extract text from PDF using pdfminer.six → PyPDF2 → fallback."""
    # Attempt 1: pdfminer.six
    try:
        from pdfminer.high_level import extract_text as pdfminer_extract  # type: ignore

        text = pdfminer_extract(str(path))
        if text and text.strip():
            return {
                "document_type_hint": "pdf",
                "text": text,
                "word_count": len(text.split()),
                "extraction_method": "pdfminer",
            }
    except ImportError:
        pass
    except Exception:  # noqa: BLE001
        pass

    # Attempt 2: PyPDF2
    try:
        import PyPDF2  # type: ignore

        pages = []
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pages.append(page_text)
        text = "\n".join(pages)
        if text.strip():
            return {
                "document_type_hint": "pdf",
                "text": text,
                "word_count": len(text.split()),
                "extraction_method": "PyPDF2",
            }
    except ImportError:
        pass
    except Exception:  # noqa: BLE001
        pass

    # Fallback: cannot extract
    return {
        "error": "manual extraction required — install pdfminer.six or PyPDF2: pip install pdfminer.six",
        "document_type_hint": "pdf",
        "extraction_method": "fallback",
    }


def extract_docx(path: Path) -> dict:
    """Extract text from .docx using python-docx → fallback."""
    try:
        import docx  # type: ignore

        doc = docx.Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs)
        return {
            "document_type_hint": "docx",
            "text": text,
            "word_count": len(text.split()),
            "extraction_method": "python-docx",
        }
    except ImportError:
        return {
            "error": "manual extraction required — install python-docx: pip install python-docx",
            "document_type_hint": "docx",
            "extraction_method": "fallback",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "error": f"python-docx extraction failed: {exc}",
            "document_type_hint": "docx",
            "extraction_method": "fallback",
        }


EXTRACTORS = {
    ".md": extract_plaintext,
    ".txt": extract_plaintext,
    ".rst": extract_plaintext,
    ".json": extract_json,
    ".yaml": extract_yaml,
    ".yml": extract_yaml,
    ".pdf": extract_pdf,
    ".docx": extract_docx,
}


def extract(input_path: str) -> dict:
    """Dispatch to the correct extractor based on file extension."""
    path = Path(input_path)

    if not path.exists():
        return {
            "error": f"File not found: {input_path}",
            "document_type_hint": "unknown",
            "extraction_method": "none",
        }

    ext = path.suffix.lower()
    extractor = EXTRACTORS.get(ext)

    if extractor is None:
        return {
            "error": f"Unsupported file format: {ext}. Supported: {sorted(EXTRACTORS.keys())}",
            "document_type_hint": "unknown",
            "extraction_method": "none",
        }

    return extractor(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="doc_intake.py — multi-format document text extractor"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to document file (.md, .txt, .rst, .json, .yaml, .yml, .pdf, .docx)",
    )
    args = parser.parse_args()

    result = extract(args.input)
    print(json.dumps(result, indent=2))

    # Exit 1 if extraction failed
    return 1 if "error" in result else 0


if __name__ == "__main__":
    raise SystemExit(main())
