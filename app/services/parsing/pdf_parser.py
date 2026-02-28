"""PDF parser using PyMuPDF (fitz) for page-by-page text extraction.

Applies a noise-removal pipeline to exclude headers, footers, watermarks,
and margin content before producing blocks for analysis.
"""

import logging
from typing import Optional

import fitz  # pymupdf

from app.config import Config
from app.services.parsing.base import BaseParser, Block, ParseResult

logger = logging.getLogger(__name__)

# Font-size threshold (pt) above which text is considered a watermark candidate
_WATERMARK_FONT_SIZE = 40.0

# Minimum ratio of text width to page width for watermark classification
_WATERMARK_WIDTH_RATIO = 0.50

# Number of consecutive pages on which a text must appear to be a header/footer
_REPEATED_TEXT_THRESHOLD = 3

# Font-size bump (relative to median) that suggests a heading
_HEADING_SIZE_RATIO = 1.3


class PdfParser(BaseParser):
    """Parser for PDF documents.

    Uses PyMuPDF to extract text blocks page-by-page, then applies a
    noise-removal pipeline (margin crop, repeated-text detection,
    watermark exclusion) and heuristic heading detection.
    """

    def parse(self, content: str, filename: Optional[str] = None) -> ParseResult:
        """Parse a PDF file and return text blocks.

        Because PDFs are binary, *content* is expected to be the file
        path (as a string) or raw bytes.  When given a file path the file
        is opened directly; when given raw bytes they are loaded in-memory.

        Args:
            content: File path to the PDF or raw PDF bytes.
            filename: Optional display filename for metadata.

        Returns:
            ParseResult with text blocks extracted from the PDF.
        """
        logger.debug("PdfParser: opening PDF %s", filename or "(in-memory)")

        if not content:
            return ParseResult(blocks=[], plain_text="")

        try:
            doc = self._open_document(content)
        except RuntimeError as exc:
            logger.warning("PdfParser: failed to open PDF: %s", exc)
            return ParseResult(
                blocks=[], plain_text="",
                metadata={"error": str(exc)},
            )
        except ValueError as exc:
            logger.warning("PdfParser: invalid PDF data: %s", exc)
            return ParseResult(
                blocks=[], plain_text="",
                metadata={"error": str(exc)},
            )

        try:
            raw_page_blocks = self._extract_raw_blocks(doc)
            cleaned = self._remove_noise(raw_page_blocks, doc)
            blocks = self._to_blocks(cleaned)
        finally:
            doc.close()

        plain_text = "\n\n".join(
            b.content for b in blocks if not b.should_skip_analysis and b.content
        )

        logger.debug("PdfParser: produced %d blocks", len(blocks))
        return ParseResult(
            blocks=blocks,
            plain_text=plain_text,
            metadata={"filename": filename, "pages": len(raw_page_blocks)},
        )

    # ------------------------------------------------------------------
    # Document opening
    # ------------------------------------------------------------------

    @staticmethod
    def _open_document(content: str) -> fitz.Document:
        """Open the PDF from a path or raw bytes."""
        if isinstance(content, bytes):
            return fitz.open(stream=content, filetype="pdf")
        return fitz.open(content)

    # ------------------------------------------------------------------
    # Raw block extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_raw_blocks(doc: fitz.Document) -> list[list[dict]]:
        """Extract text blocks from every page.

        Returns a list of pages, each page being a list of block dicts
        with keys: text, bbox, font_size, is_bold, page_num.
        """
        all_pages: list[list[dict]] = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_blocks: list[dict] = []
            text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

            for block in text_dict.get("blocks", []):
                if block.get("type") != 0:
                    continue
                block_info = _parse_text_block(block, page_num)
                if block_info is not None:
                    page_blocks.append(block_info)

            all_pages.append(page_blocks)
        return all_pages

    # ------------------------------------------------------------------
    # Noise removal pipeline
    # ------------------------------------------------------------------

    def _remove_noise(
        self,
        pages: list[list[dict]],
        doc: fitz.Document,
    ) -> list[dict]:
        """Apply margin crop, repeated-text, and watermark filters.

        Returns a flat list of cleaned block dicts.
        """
        margin_pct = Config.PDF_MARGIN_CROP_PERCENT / 100.0
        cleaned: list[dict] = []

        repeated = _detect_repeated_texts(pages)

        for page_num, page_blocks in enumerate(pages):
            page = doc[page_num]
            page_height = page.rect.height
            page_width = page.rect.width
            top_margin = page_height * margin_pct
            bottom_margin = page_height * (1.0 - margin_pct)

            for blk in page_blocks:
                bbox = blk["bbox"]

                # Margin crop
                if bbox[1] < top_margin or bbox[3] > bottom_margin:
                    logger.debug(
                        "PdfParser: margin-cropped text on page %d: %s",
                        page_num + 1, blk["text"][:60],
                    )
                    continue

                # Repeated text (headers/footers)
                text_key = (blk["text"].strip(), round(bbox[1], 1))
                if text_key in repeated:
                    logger.debug(
                        "PdfParser: repeated-text excluded on page %d: %s",
                        page_num + 1, blk["text"][:60],
                    )
                    continue

                # Watermark detection
                if _is_watermark(blk, page_width):
                    logger.debug(
                        "PdfParser: watermark excluded on page %d: %s",
                        page_num + 1, blk["text"][:60],
                    )
                    continue

                cleaned.append(blk)

        return cleaned

    # ------------------------------------------------------------------
    # Block creation
    # ------------------------------------------------------------------

    @staticmethod
    def _to_blocks(cleaned: list[dict]) -> list[Block]:
        """Convert cleaned text block dicts to Block objects."""
        blocks: list[Block] = []
        offset = 0

        for blk in cleaned:
            text = blk["text"].strip()
            if not text:
                continue

            block_type = "paragraph"
            level = 0
            if blk["is_bold"] and blk["font_size"] > 0:
                # Heuristic heading: bold + larger font
                block_type = "heading"
                level = _estimate_heading_level(blk["font_size"])

            end = offset + len(text)
            blocks.append(Block(
                block_type=block_type,
                content=text,
                raw_content=text,
                start_pos=offset,
                end_pos=end,
                level=level,
                metadata={"page": blk["page_num"] + 1},
            ))
            offset = end + 1  # +1 for implied separator

        return blocks


# ------------------------------------------------------------------
# Pure helper functions
# ------------------------------------------------------------------


def _parse_text_block(block: dict, page_num: int) -> Optional[dict]:
    """Extract text, bbox, and font info from a PyMuPDF block dict."""
    lines = block.get("lines", [])
    if not lines:
        return None

    texts: list[str] = []
    sizes: list[float] = []
    bold_count = 0
    total_spans = 0

    for line in lines:
        for span in line.get("spans", []):
            span_text = span.get("text", "")
            if span_text.strip():
                texts.append(span_text)
                sizes.append(span.get("size", 0.0))
                total_spans += 1
                flags = span.get("flags", 0)
                if flags & 2 ** 4:  # bold bit
                    bold_count += 1

    full_text = " ".join(texts)
    if not full_text.strip():
        return None

    avg_size = sum(sizes) / len(sizes) if sizes else 0.0
    is_bold = bold_count > total_spans / 2 if total_spans else False

    return {
        "text": full_text,
        "bbox": block.get("bbox", (0, 0, 0, 0)),
        "font_size": avg_size,
        "is_bold": is_bold,
        "page_num": page_num,
    }


def _detect_repeated_texts(
    pages: list[list[dict]],
) -> set[tuple[str, float]]:
    """Identify texts that appear in the same vertical position on 3+ pages."""
    counts: dict[tuple[str, float], int] = {}
    for page_blocks in pages:
        seen_on_page: set[tuple[str, float]] = set()
        for blk in page_blocks:
            key = (blk["text"].strip(), round(blk["bbox"][1], 1))
            if key not in seen_on_page:
                seen_on_page.add(key)
                counts[key] = counts.get(key, 0) + 1

    return {k for k, v in counts.items() if v >= _REPEATED_TEXT_THRESHOLD}


def _is_watermark(blk: dict, page_width: float) -> bool:
    """Return True if *blk* looks like a watermark."""
    if blk["font_size"] < _WATERMARK_FONT_SIZE:
        return False
    bbox = blk["bbox"]
    text_width = bbox[2] - bbox[0]
    return text_width > page_width * _WATERMARK_WIDTH_RATIO


def _estimate_heading_level(font_size: float) -> int:
    """Map font size to a heading level (1-6)."""
    if font_size >= 24:
        return 1
    if font_size >= 20:
        return 2
    if font_size >= 16:
        return 3
    if font_size >= 14:
        return 4
    if font_size >= 12:
        return 5
    return 6


