"""File parser registry -- auto-detection and parsing for all supported formats.

Provides :func:`get_parser` to obtain a parser instance by FileType and
:func:`detect_and_parse` to auto-detect the format and parse in one step.
"""

import logging
from typing import Optional

from app.models.enums import FileType
from app.services.parsing.base import BaseParser, Block, ParseResult
from app.services.parsing.format_detector import detect_format
from app.services.parsing.plaintext_parser import PlaintextParser
from app.services.parsing.markdown_parser import MarkdownParser
from app.services.parsing.html_parser import HtmlParser
from app.services.parsing.xml_parser import XmlParser
from app.services.parsing.dita_parser import DitaParser
from app.services.parsing.asciidoc_parser import AsciidocParser
from app.services.parsing.pdf_parser import PdfParser
from app.services.parsing.docx_parser import DocxParser

logger = logging.getLogger(__name__)

# Lazy-initialised parser singletons
_parsers: dict[FileType, BaseParser] = {}


def _get_or_create(file_type: FileType) -> BaseParser:
    """Return a cached parser instance for *file_type*, creating it on first use."""
    if file_type not in _parsers:
        _parsers[file_type] = _FACTORY_MAP[file_type]()
    return _parsers[file_type]


# FileType -> parser class mapping
_FACTORY_MAP: dict[FileType, type[BaseParser]] = {
    FileType.PLAINTEXT: PlaintextParser,
    FileType.MARKDOWN: MarkdownParser,
    FileType.HTML: HtmlParser,
    FileType.XML: XmlParser,
    FileType.DITA: DitaParser,
    FileType.ASCIIDOC: AsciidocParser,
    FileType.PDF: PdfParser,
    FileType.DOCX: DocxParser,
}


def get_parser(file_type: FileType) -> BaseParser:
    """Return the parser instance for the given file type.

    Args:
        file_type: The :class:`FileType` enum member identifying the format.

    Returns:
        A :class:`BaseParser` subclass instance capable of parsing that format.

    Raises:
        ValueError: If *file_type* has no registered parser.
    """
    if file_type not in _FACTORY_MAP:
        raise ValueError(f"No parser registered for file type: {file_type!r}")
    return _get_or_create(file_type)


def detect_and_parse(
    content: str, filename: Optional[str] = None
) -> ParseResult:
    """Auto-detect the format of *content* and parse it.

    Uses :func:`detect_format` to determine the file type, then delegates
    to the appropriate parser.

    Args:
        content: Raw document content (or file path for binary formats).
        filename: Optional filename for extension-based hints and metadata.

    Returns:
        A :class:`ParseResult` with blocks and metadata.
    """
    file_type = detect_format(content, filename)
    logger.debug("detect_and_parse: detected %s for %s", file_type.value, filename or "(no filename)")
    parser = get_parser(file_type)
    return parser.parse(content, filename)


__all__ = [
    "get_parser",
    "detect_and_parse",
    "detect_format",
    "BaseParser",
    "Block",
    "ParseResult",
    "PlaintextParser",
    "MarkdownParser",
    "HtmlParser",
    "XmlParser",
    "DitaParser",
    "AsciidocParser",
    "PdfParser",
    "DocxParser",
]
