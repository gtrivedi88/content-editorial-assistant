"""HTML parser using lxml for DOM tree-based extraction.

Walks the parsed DOM to produce Block structures, skipping script/style
elements and mapping common HTML tags to semantic block types.
"""

import copy
import logging
from typing import Optional

from lxml import html as lxml_html
from lxml.html import HtmlElement

from app.services.parsing.base import BaseParser, Block, ParseResult

logger = logging.getLogger(__name__)

# Elements whose subtree should be completely ignored
_SKIP_TAGS = frozenset({"script", "style", "noscript", "svg", "math"})

# CSS classes that indicate admonition containers in Red Hat docs HTML
_ADMONITION_CLASSES = frozenset({
    "note", "tip", "important", "warning", "caution", "admonition",
})

# Block-level tags that produce a newline in innerText — mirrors
# span-mapper.js BLOCK_TAGS for synchronized offset tracking.
_INNERTEXT_BLOCK_TAGS = frozenset({
    "p", "div", "h1", "h2", "h3", "h4", "h5", "h6",
    "li", "tr", "blockquote", "pre", "hr", "ul", "ol",
    "table", "thead", "tbody", "dt", "dd", "figcaption",
})

# Block types that can contain inline <code> elements
_INLINE_CODE_BLOCK_TYPES = frozenset({
    "paragraph", "list_item", "list_item_ordered",
    "list_item_unordered", "blockquote", "table_cell",
})

# Tag -> block_type mapping
_TAG_MAP: dict[str, str] = {
    "h1": "heading",
    "h2": "heading",
    "h3": "heading",
    "h4": "heading",
    "h5": "heading",
    "h6": "heading",
    "p": "paragraph",
    "pre": "code_block",
    "code": "code_block",
    "ul": "list",
    "ol": "list",
    "li": "list_item",
    "table": "table",
    "tr": "table_row",
    "td": "table_cell",
    "th": "table_cell",
    "blockquote": "blockquote",
    "img": "image",
    "figure": "image",
    "aside": "sidebar",
    "dt": "paragraph",
    "dd": "paragraph",
    # div, section, article are containers — _walk() recurses into them
}


class HtmlParser(BaseParser):
    """Parser for HTML documents using lxml.

    Skips ``<script>``, ``<style>``, and ``<noscript>`` elements. Maps
    structural HTML tags to semantic block types for downstream analysis.
    """

    def parse(self, content: str, filename: Optional[str] = None) -> ParseResult:
        """Parse an HTML document into blocks.

        Args:
            content: Raw HTML string.
            filename: Optional filename for logging.

        Returns:
            ParseResult with blocks and metadata.
        """
        logger.debug("HtmlParser: parsing %d chars", len(content) if content else 0)

        if not content or not content.strip():
            return ParseResult(blocks=[], plain_text="")

        try:
            doc = lxml_html.fromstring(content)
        except lxml_html.etree.ParserError:
            logger.warning("HtmlParser: lxml failed to parse content")
            return ParseResult(blocks=[], plain_text="")

        blocks: list[Block] = []
        self._walk(doc, blocks, offset=0)

        plain_text = "\n\n".join(
            b.content for b in blocks if not b.should_skip_analysis and b.content
        )

        logger.debug("HtmlParser: produced %d blocks", len(blocks))
        return ParseResult(
            blocks=blocks,
            plain_text=plain_text,
        )

    # ------------------------------------------------------------------
    # Recursive DOM walker
    # ------------------------------------------------------------------

    def _walk(
        self,
        element: HtmlElement,
        blocks: list[Block],
        offset: int,
    ) -> int:
        """Recursively walk *element* and append blocks.

        Args:
            element: Current DOM node.
            blocks: Accumulator for discovered blocks.
            offset: Running character offset for position tracking.

        Returns:
            Updated character offset after processing this element.
        """
        tag = _local_tag(element)

        if tag in _SKIP_TAGS:
            return offset

        # Account for innerText newline at block boundaries (mirrors span-mapper.js)
        if tag in _INNERTEXT_BLOCK_TAGS and offset > 0 and blocks:
            offset += 1

        # Admonition div/section/article — treat as terminal block
        if tag in ("div", "section", "article") and _is_admonition(element):
            block = self._element_to_block(
                element, tag, "admonition", offset,
            )
            if block is not None:
                blocks.append(block)
                offset = block.end_pos
            return offset

        block_type = _TAG_MAP.get(tag)

        if block_type is not None:
            block = self._element_to_block(element, tag, block_type, offset)
            if block is not None:
                blocks.append(block)
                offset = block.end_pos
            return offset

        # Container element — capture loose text + recurse into children
        return self._walk_container(element, blocks, offset)

    def _walk_container(
        self,
        element: HtmlElement,
        blocks: list[Block],
        offset: int,
    ) -> int:
        """Walk a container element, capturing loose text and recursing."""
        if element.text and element.text.strip():
            offset = self._emit_loose_text(element.text, offset, blocks)

        for child in element:
            offset = self._walk(child, blocks, offset)
            if child.tail and child.tail.strip():
                offset = self._emit_loose_text(child.tail, offset, blocks)

        return offset

    def _element_to_block(
        self,
        element: HtmlElement,
        tag: str,
        block_type: str,
        offset: int,
    ) -> Optional[Block]:
        """Create a Block from a single HTML element.

        Args:
            element: The HTML element node.
            tag: Normalised lower-case tag name.
            block_type: Mapped block type string.
            offset: Current character offset.

        Returns:
            A Block or None if the element has no useful content.
        """
        if _is_admonition(element):
            block_type = "admonition"

        raw_content = _outer_html(element)
        skip = block_type in ("code_block", "admonition")

        text_content, inline_content = _extract_block_text(
            element, block_type, skip,
        )
        metadata = _image_metadata(element) if block_type == "image" else {}
        if block_type == "image":
            text_content = metadata.get("alt") or metadata.get("src", "")

        if not text_content and block_type != "image":
            return None

        start_pos = offset
        end_pos = offset + len(text_content)

        children: list[Block] = []
        if block_type in ("list", "table"):
            children = self._extract_children(element, start_pos)

        char_map = _build_block_char_map(
            skip, text_content, inline_content,
        )

        return Block(
            block_type=block_type,
            content=text_content,
            raw_content=raw_content,
            start_pos=start_pos,
            end_pos=end_pos,
            inline_content=inline_content,
            level=_heading_level(tag),
            children=children,
            should_skip_analysis=skip,
            metadata=metadata,
            char_map=char_map,
        )

    def _extract_children(
        self, element: HtmlElement, parent_offset: int,
    ) -> list[Block]:
        """Extract child blocks from list or table containers."""
        children: list[Block] = []
        offset = parent_offset
        parent_tag = _local_tag(element)
        for child in element:
            tag = _local_tag(child)
            child_type = _TAG_MAP.get(tag)
            if child_type is None:
                continue
            # Typed list items based on parent
            if child_type == "list_item":
                if parent_tag == "ol":
                    child_type = "list_item_ordered"
                elif parent_tag == "ul":
                    child_type = "list_item_unordered"
            block = self._element_to_block(child, tag, child_type, offset)
            if block is not None:
                children.append(block)
                offset = block.end_pos
        return children

    def _emit_loose_text(
        self, text: str, offset: int, blocks: list[Block],
    ) -> int:
        """Create a paragraph block from loose text inside a container.

        Handles text nodes directly inside container elements (div,
        section, article) that are not wrapped in ``<p>`` tags.

        Args:
            text: The raw text string (element.text or child.tail).
            offset: Current character offset.
            blocks: Accumulator for discovered blocks.

        Returns:
            Updated character offset.
        """
        clean = text.strip()
        if not clean:
            return offset
        end = offset + len(clean)
        blocks.append(Block(
            block_type="paragraph",
            content=clean,
            raw_content=text,
            start_pos=offset,
            end_pos=end,
            inline_content=clean,
            char_map=None,
        ))
        return end


# ------------------------------------------------------------------
# Pure helper functions
# ------------------------------------------------------------------


def _local_tag(element: HtmlElement) -> str:
    """Return the lower-case local tag name of *element*."""
    tag = element.tag if isinstance(element.tag, str) else ""
    return tag.split("}")[-1].lower() if "}" in tag else tag.lower()


def _text_of(element: HtmlElement) -> str:
    """Extract concatenated text content from *element* and descendants."""
    return element.text_content() or ""


def _outer_html(element: HtmlElement) -> str:
    """Serialise *element* back to an HTML string."""
    try:
        return lxml_html.tostring(element, encoding="unicode")
    except (TypeError, lxml_html.etree.SerialisationError):
        return ""


def _heading_level(tag: str) -> int:
    """Return 1-6 for heading tags, 0 otherwise."""
    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        return int(tag[1])
    return 0


def _is_admonition(element: HtmlElement) -> bool:
    """Return True if *element* has CSS classes indicating an admonition."""
    classes = set((element.get("class") or "").lower().split())
    return bool(classes & _ADMONITION_CLASSES)


def _image_metadata(element: HtmlElement) -> dict:
    """Extract image metadata from an element."""
    return {
        "src": element.get("src", ""),
        "alt": element.get("alt", ""),
    }


def _extract_block_text(
    element: HtmlElement, block_type: str, skip: bool,
) -> tuple[str, str]:
    """Extract content and inline_content from an element.

    For block types that can contain inline ``<code>``, preserves code
    markers as backticks in ``inline_content`` so the orchestrator can
    compute inline code ranges.

    Returns:
        ``(content, inline_content)`` pair, both stripped.
    """
    if block_type in _INLINE_CODE_BLOCK_TYPES and not skip:
        content, inline = _extract_text_with_inline_markers(element)
        return content.strip(), inline.strip()
    return _text_of(element).strip(), ""


def _extract_text_with_inline_markers(
    element: HtmlElement,
) -> tuple[str, str]:
    """Extract plain text and inline-marked text from *element*.

    Clones the element, wraps ``<code>`` text with backticks and
    ``<b>``/``<strong>`` text with ``**`` markers in-place, then lets
    lxml's ``text_content()`` safely stitch text and tails.

    Processing order: code first (innermost), then bold (outermost),
    so ``<b><code>curl</code></b>`` produces ``**`curl`**``.

    Returns:
        ``(content, inline_content)`` where inline_content has backticks
        around code and ``**`` around bold text.
    """
    content = element.text_content() or ""

    el_copy = copy.deepcopy(element)

    # Process code elements first (innermost)
    for code_el in el_copy.xpath(".//code"):
        code_text = code_el.text_content() or ""
        code_el.text = f"`{code_text}`"
        while len(code_el):
            code_el.remove(code_el[0])

    # Process bold elements (outermost) — skip nested bolds
    for bold_el in el_copy.xpath(
        ".//b[not(ancestor::b or ancestor::strong)]"
        " | .//strong[not(ancestor::b or ancestor::strong)]"
    ):
        bold_text = bold_el.text_content() or ""
        if not bold_text.strip():
            continue
        bold_el.text = f"**{bold_text}**"
        while len(bold_el):
            bold_el.remove(bold_el[0])

    inline_content = el_copy.text_content() or ""
    return content, inline_content


def _build_inline_char_map(content: str, inline_content: str) -> list[int]:
    """Build a char_map from *content* positions to *inline_content* positions.

    The two strings differ by backtick wrappers around code terms and
    ``**`` wrappers around bold terms.  Walks both in parallel, skipping
    inserted markers in inline_content.
    """
    char_map: list[int] = []
    j = 0
    for _ in range(len(content)):
        while j < len(inline_content):
            ch = inline_content[j]
            if ch == "`":
                j += 1
            elif (
                ch == "*"
                and j + 1 < len(inline_content)
                and inline_content[j + 1] == "*"
            ):
                j += 2
            else:
                break
        if j < len(inline_content):
            char_map.append(j)
            j += 1
        else:
            char_map.append(max(0, len(inline_content) - 1))
    return char_map


def _build_block_char_map(
    skip: bool,
    text_content: str,
    inline_content: str,
) -> list[int] | None:
    """Build the appropriate char_map for a block."""
    if skip or not text_content:
        return None
    if inline_content and inline_content != text_content:
        return _build_inline_char_map(text_content, inline_content)
    return None
