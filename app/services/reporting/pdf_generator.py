"""PDF Report Generator for Content Editorial Assistant.

Produces a polished 4-page writing analytics PDF using ReportLab.
Each page is self-contained with explicit PageBreak boundaries.
Renders exclusively from metrics and issue data — no full document
text is included (Trap 3 guard).
"""

import io
import logging
import math
from datetime import datetime, timezone
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

# ── Page dimensions ──────────────────────────────────────────────────

_PAGE_W, _PAGE_H = letter
_MARGIN = 0.75 * inch
_CONTENT_W = _PAGE_W - 2 * _MARGIN

# ── Colour palette ───────────────────────────────────────────────────

_PRIMARY = colors.HexColor("#2B6CB0")
_PRIMARY_DARK = colors.HexColor("#1A365D")
_GREEN = colors.HexColor("#1A8F57")
_BLUE = colors.HexColor("#2B6CB0")
_ORANGE = colors.HexColor("#DD6B20")
_GOLD = colors.HexColor("#D69E2E")
_RED = colors.HexColor("#C9190B")
_DARK = colors.HexColor("#1A202C")
_MEDIUM = colors.HexColor("#4A5568")
_LIGHT = colors.HexColor("#718096")
_BORDER = colors.HexColor("#E2E8F0")
_LIGHT_BG = colors.HexColor("#F7FAFC")
_CALLOUT_BG = colors.HexColor("#FFFBEB")
_CALLOUT_BORDER = colors.HexColor("#F6AD55")
_BLUE_BG = colors.HexColor("#EBF8FF")
_BLUE_BORDER = colors.HexColor("#63B3ED")
_WHITE = colors.white

# Readability metric name constants
_FLESCH_RE = "Flesch Reading Ease"
_FLESCH_KG = "Flesch-Kincaid Grade"
_GUNNING_FOG = "Gunning Fog"
_COLEMAN_LIAU = "Coleman-Liau"


# ── Colour / label helpers ───────────────────────────────────────────

def _hex(c: colors.Color) -> str:
    """Return #rrggbb hex string for Paragraph markup."""
    return "#%02x%02x%02x" % (
        int(c.red * 255), int(c.green * 255), int(c.blue * 255),
    )


def _score_color(score: int) -> colors.Color:
    """Map a 0-100 score to a semantic colour."""
    if score >= 90:
        return _GREEN
    if score >= 75:
        return _BLUE
    if score >= 60:
        return _ORANGE
    return _RED


def _score_label(score: int) -> str:
    """Map a 0-100 score to an uppercase label."""
    if score >= 90:
        return "EXCELLENT"
    if score >= 75:
        return "GOOD"
    if score >= 60:
        return "NEEDS WORK"
    return "REQUIRES REVISION"


def _readability_label(flesch: float) -> str:
    """Human label for a Flesch Reading Ease score."""
    if flesch >= 90:
        return "Very Easy"
    if flesch >= 80:
        return "Easy"
    if flesch >= 70:
        return "Fairly Easy"
    if flesch >= 60:
        return "Standard"
    if flesch >= 50:
        return "Fairly Difficult"
    if flesch >= 30:
        return "Difficult"
    return "Very Difficult"


def _readability_color(flesch: float) -> colors.Color:
    """Colour for a Flesch Reading Ease score."""
    if flesch >= 60:
        return _GREEN
    if flesch >= 30:
        return _ORANGE
    return _RED


def _issue_count_color(total: int) -> colors.Color:
    """Colour for an issue count."""
    if total <= 10:
        return _GREEN
    if total <= 20:
        return _ORANGE
    return _RED


def _passive_color(pct: float) -> colors.Color:
    """Colour for a passive voice percentage."""
    if pct <= 10:
        return _GREEN
    if pct <= 15:
        return _ORANGE
    return _RED


def _grade_color(grade: float) -> colors.Color:
    """Colour for a grade level value."""
    if 9 <= grade <= 11:
        return _GREEN
    if grade <= 14:
        return _ORANGE
    return _RED


def _grade_audience(grade: float) -> str:
    """Target audience description from grade level."""
    if grade <= 8:
        return "General audience"
    if grade <= 12:
        return "Professional technical audience"
    if grade <= 16:
        return "Advanced specialists, researchers"
    return "Academic / PhD level"


def _grade_assessment(grade: float) -> str:
    """Academic level label from grade level."""
    if grade <= 6:
        return "Elementary"
    if grade <= 8:
        return "Middle School"
    if grade <= 12:
        return "High School"
    if grade <= 16:
        return "College/University"
    return "Graduate"


def _metric_interpretation(name: str, score: float) -> str:
    """Human interpretation for a readability metric score."""
    if name == _FLESCH_RE:
        return _readability_label(score)
    if name == _FLESCH_KG:
        return f"Grade {score:.0f} level"
    if name == _GUNNING_FOG:
        if score <= 8:
            return "Easy to read"
        if score <= 12:
            return "Ideal"
        if score <= 17:
            return "Difficult"
        return "Very difficult"
    if name == _COLEMAN_LIAU:
        return f"Grade {score:.0f} level"
    return "\u2014"


def _assess_color(good: bool) -> str:
    """Return green or red hex for good/bad assessment."""
    return _hex(_GREEN) if good else _hex(_RED)


# ── Styles ───────────────────────────────────────────────────────────

def _build_styles() -> dict[str, ParagraphStyle]:
    """Create PDF paragraph styles."""
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "CEA_Title", parent=base["Title"],
            fontSize=24, leading=30, spaceAfter=2,
            textColor=_PRIMARY_DARK,
        ),
        "subtitle": ParagraphStyle(
            "CEA_Subtitle", parent=base["Normal"],
            fontSize=10, leading=14, spaceAfter=14,
            textColor=_LIGHT,
        ),
        "h1": ParagraphStyle(
            "CEA_H1", parent=base["Heading1"],
            fontSize=16, leading=20, spaceBefore=0, spaceAfter=10,
            textColor=_PRIMARY,
        ),
        "h2": ParagraphStyle(
            "CEA_H2", parent=base["Heading2"],
            fontSize=13, leading=16, spaceBefore=12, spaceAfter=6,
            textColor=_DARK,
        ),
        "body": ParagraphStyle(
            "CEA_Body", parent=base["Normal"],
            fontSize=10, leading=14, spaceAfter=6,
            textColor=_DARK,
        ),
        "body_center": ParagraphStyle(
            "CEA_BodyCenter", parent=base["Normal"],
            fontSize=10, leading=14, alignment=TA_CENTER,
            textColor=_DARK,
        ),
        "small": ParagraphStyle(
            "CEA_Small", parent=base["Normal"],
            fontSize=8, leading=10, textColor=_LIGHT,
        ),
        "score_big": ParagraphStyle(
            "CEA_ScoreBig", parent=base["Normal"],
            fontSize=42, leading=48, alignment=TA_CENTER,
        ),
        "score_label": ParagraphStyle(
            "CEA_ScoreLabel", parent=base["Normal"],
            fontSize=11, leading=14, alignment=TA_CENTER,
            textColor=_LIGHT, spaceAfter=4,
        ),
        "card_value": ParagraphStyle(
            "CEA_CardValue", parent=base["Normal"],
            fontSize=18, leading=22,
        ),
        "cell_hdr": ParagraphStyle(
            "CEA_CellHdr", parent=base["Normal"],
            fontSize=9, leading=12, textColor=_WHITE,
            fontName="Helvetica-Bold",
        ),
        "cell_hdr_c": ParagraphStyle(
            "CEA_CellHdrC", parent=base["Normal"],
            fontSize=9, leading=12, textColor=_WHITE,
            fontName="Helvetica-Bold", alignment=TA_CENTER,
        ),
        "cell": ParagraphStyle(
            "CEA_Cell", parent=base["Normal"],
            fontSize=9, leading=12, textColor=_DARK,
        ),
        "cell_c": ParagraphStyle(
            "CEA_CellC", parent=base["Normal"],
            fontSize=9, leading=12, textColor=_DARK,
            alignment=TA_CENTER,
        ),
    }


# ── Canvas callbacks ─────────────────────────────────────────────────

def _draw_footer(canvas: Any, doc: Any) -> None:
    """Draw footer and AI disclaimer on every page."""
    canvas.saveState()
    page_w = doc.pagesize[0]

    # AI disclaimer (centered, above footer line)
    canvas.setFillColor(_RED)
    cx = page_w / 2 - 80
    canvas.rect(cx, 0.58 * inch, 5, 5, fill=True, stroke=False)
    canvas.setFillColor(_ORANGE)
    canvas.rect(cx + 7, 0.58 * inch, 5, 5, fill=True, stroke=False)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(_MEDIUM)
    canvas.drawString(
        cx + 16, 0.59 * inch,
        "Always review AI-generated content prior to use.",
    )

    # Footer line
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(_LIGHT)
    canvas.drawString(
        doc.leftMargin, 0.38 * inch, "Writing Analytics Report",
    )
    canvas.drawCentredString(
        page_w / 2, 0.38 * inch,
        f"Page {canvas.getPageNumber()}",
    )
    canvas.drawRightString(
        page_w - doc.rightMargin, 0.38 * inch,
        datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    )
    canvas.restoreState()


def _first_page(canvas: Any, doc: Any) -> None:
    """Header bar + footer on the cover page."""
    canvas.saveState()
    page_w = doc.pagesize[0]
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(_PRIMARY)
    canvas.drawString(
        doc.leftMargin, _PAGE_H - 0.5 * inch,
        "CONTENT EDITORIAL ASSISTANT",
    )
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(_LIGHT)
    canvas.drawRightString(
        page_w - doc.rightMargin, _PAGE_H - 0.5 * inch,
        "AI-Powered Writing Analysis",
    )
    canvas.restoreState()
    _draw_footer(canvas, doc)


def _later_pages(canvas: Any, doc: Any) -> None:
    """Thin top accent bar + footer on subsequent pages."""
    canvas.saveState()
    canvas.setFillColor(_PRIMARY_DARK)
    canvas.rect(0, _PAGE_H - 4, _PAGE_W, 4, fill=True, stroke=False)
    canvas.restoreState()
    _draw_footer(canvas, doc)


# ── Reusable table / card builders ───────────────────────────────────

def _styled_table(
    data: list[list[Any]],
    col_widths: list[float],
) -> Table:
    """Build a table with blue header row and alternating stripes."""
    table = Table(data, colWidths=col_widths)
    cmds: list[tuple[Any, ...]] = [
        ("BACKGROUND", (0, 0), (-1, 0), _PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), _WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEADING", (0, 0), (-1, -1), 13),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
    ]
    for i in range(2, len(data), 2):
        cmds.append(("BACKGROUND", (0, i), (-1, i), _LIGHT_BG))
    table.setStyle(TableStyle(cmds))
    return table


def _callout_box(
    text: str,
    bg: colors.Color,
    border: colors.Color,
    styles: dict[str, ParagraphStyle],
) -> Table:
    """Build a callout box with coloured left border."""
    para = Paragraph(text, styles["body"])
    table = Table([[para]], colWidths=[_CONTENT_W])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LINEBEFORE", (0, 0), (0, -1), 3, border),
    ]))
    return table


# ── Data extraction helpers ──────────────────────────────────────────

def _extract_stats(
    report_data: dict[str, Any],
) -> dict[str, Any]:
    """Extract statistics from report data with fallbacks."""
    stats = report_data.get("statistics", {})
    return {
        "word_count": int(
            stats.get("word_count", report_data.get("word_count", 0)),
        ),
        "sentence_count": int(
            stats.get(
                "sentence_count",
                report_data.get("sentence_count", 0),
            ),
        ),
        "paragraph_count": int(
            stats.get(
                "paragraph_count",
                report_data.get("paragraph_count", 0),
            ),
        ),
        "avg_sentence_length": float(
            stats.get("avg_sentence_length", 0),
        ),
        "vocabulary_diversity": float(
            stats.get("vocabulary_diversity", 0),
        ),
        "avg_syllables_per_word": float(
            stats.get(
                "avg_syllables_per_word",
                report_data.get("avg_syllables_per_word", 0),
            ),
        ),
        "reading_time": stats.get("estimated_reading_time", "N/A"),
    }


def _extract_readability(
    report_data: dict[str, Any],
) -> tuple[float, float]:
    """Return (flesch_score, grade_level) from report data."""
    readability = report_data.get("readability", {})
    flesch = float(
        readability.get(_FLESCH_RE, {}).get("score", 0),
    )
    grade = float(
        readability.get(_FLESCH_KG, {}).get("score", 0),
    )
    return flesch, grade


def _compute_passive_pct(
    issues_data: list[dict[str, Any]],
    sentence_count: int,
) -> float:
    """Estimate passive voice percentage from issues."""
    passive = sum(
        1 for i in issues_data
        if "verbs" in i.get("rule_name", "")
    )
    return round(passive / max(sentence_count, 1) * 100, 1)


# ── Stat card grid (Page 1) ─────────────────────────────────────────

def _stat_card_grid(
    report_data: dict[str, Any],
    score_data: dict[str, Any],
    issues_data: list[dict[str, Any]],
    styles: dict[str, ParagraphStyle],
) -> Table:
    """Build the 2x4 statistics card grid for the cover page."""
    st = _extract_stats(report_data)
    flesch, grade = _extract_readability(report_data)
    total_issues = int(score_data.get("total_issues", 0))
    passive_pct = _compute_passive_pct(
        issues_data, st["sentence_count"],
    )

    r_color = _readability_color(flesch)
    i_color = _issue_count_color(total_issues)
    p_color = _passive_color(passive_pct)

    def _card(
        value: str, label: str, vc: colors.Color,
    ) -> Paragraph:
        sz = 14 if len(value) > 6 else 18
        return Paragraph(
            f'<font size="{sz}" color="{_hex(vc)}">'
            f"<b>{value}</b></font><br/>"
            f'<font size="8" color="{_hex(_LIGHT)}">{label}</font>',
            styles["card_value"],
        )

    row1 = [
        _card(f"{st['word_count']:,}", "Word Count", _PRIMARY),
        _card(f"{grade:.1f}", "Grade Level", _PRIMARY),
        _card(_readability_label(flesch), "Readability", r_color),
        _card(str(total_issues), "Issues Found", i_color),
    ]
    row2 = [
        _card(st["reading_time"] or "N/A", "Reading Time", _DARK),
        _card(str(st["sentence_count"]), "Sentences", _DARK),
        _card(str(st["paragraph_count"]), "Paragraphs", _DARK),
        _card(f"{passive_pct:.0f}%", "Passive Voice", p_color),
    ]

    card_w = _CONTENT_W / 4
    grid = Table([row1, row2], colWidths=[card_w] * 4)

    accent = [
        [_PRIMARY, _PRIMARY, r_color, i_color],
        [_DARK, _DARK, _DARK, p_color],
    ]
    cmds: list[tuple[Any, ...]] = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    for row in range(2):
        for col in range(4):
            cmds.append(("BOX", (col, row), (col, row), 0.5, _BORDER))
            cmds.append((
                "LINEBEFORE", (col, row), (col, row),
                3, accent[row][col],
            ))
    grid.setStyle(TableStyle(cmds))
    return grid


# ── Score cards row (Page 2) ─────────────────────────────────────────

def _score_cards_row(
    score_data: dict[str, Any],
    report_data: dict[str, Any],
    styles: dict[str, ParagraphStyle],
) -> Table:
    """Build the three executive score cards."""
    score = int(score_data.get("score", 0))
    sc = _score_color(score)

    llm = report_data.get("llm_consumability", {})
    llm_score = int(llm.get("score", 0))
    llm_c = _score_color(llm_score)
    llm_lbl = str(llm.get("label", "N/A"))

    _, grade = _extract_readability(report_data)
    gc = _grade_color(grade)

    def _hdr(t: str) -> Paragraph:
        return Paragraph(
            f'<font color="white"><b>{t}</b></font>',
            styles["cell_hdr_c"],
        )

    def _val(v: str, c: colors.Color) -> Paragraph:
        return Paragraph(
            f'<font size="24" color="{_hex(c)}"><b>{v}</b></font>',
            styles["body_center"],
        )

    def _lbl(t: str) -> Paragraph:
        return Paragraph(
            f'<font color="{_hex(_LIGHT)}">{t}</font>',
            styles["body_center"],
        )

    cw = (_CONTENT_W - 24) / 3
    data = [
        [_hdr("Quality Score"), "", _hdr("AI Readiness"), "",
         _hdr("Grade Level")],
        [_val(str(score), sc), "", _val(str(llm_score), llm_c), "",
         _val(f"{grade:.1f}", gc)],
        [_lbl(_score_label(score)), "", _lbl(llm_lbl), "",
         _lbl("Target: 9\u201311")],
    ]
    widths = [cw, 12, cw, 12, cw]
    table = Table(data, colWidths=widths)

    cmds: list[tuple[Any, ...]] = [
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 1), (-1, 1), 10),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 4),
        ("TOPPADDING", (0, 2), (-1, 2), 2),
        ("BOTTOMPADDING", (0, 2), (-1, 2), 8),
    ]
    for col in (0, 2, 4):
        cmds.append(("BACKGROUND", (col, 0), (col, 0), _PRIMARY))
        cmds.append(("BOX", (col, 0), (col, -1), 0.5, _BORDER))
    table.setStyle(TableStyle(cmds))
    return table


# ── Dynamic content generators ──────────────────────────────────────

def _compute_key_insights(
    report_data: dict[str, Any],
    score_data: dict[str, Any],
) -> list[str]:
    """Generate 3 key insight bullets for the cover page."""
    st = _extract_stats(report_data)
    wc = st["word_count"]
    total = int(score_data.get("total_issues", 0))
    flesch, _ = _extract_readability(report_data)

    insights: list[str] = []
    if wc < 500:
        insights.append(
            f"Concise document ({wc:,} words) - typical for "
            "focused topics.",
        )
    elif wc < 2000:
        insights.append(
            f"Medium-length document ({wc:,} words) - suitable "
            "for detailed technical content.",
        )
    else:
        insights.append(
            f"Comprehensive document ({wc:,} words) - extensive "
            "coverage of the topic.",
        )

    if flesch < 60:
        insights.append(
            "Readability could be improved to reach a wider audience.",
        )
    else:
        insights.append(
            "Good readability - accessible to most technical "
            "professionals.",
        )

    if total > 20:
        insights.append(
            f"{total} areas for improvement - systematic revision "
            "suggested.",
        )
    elif total > 0:
        insights.append(
            f"{total} areas for improvement - targeted edits "
            "recommended.",
        )
    else:
        insights.append(
            "No areas for improvement identified - excellent quality.",
        )
    return insights[:3]


def _compute_key_findings(
    report_data: dict[str, Any],
    score_data: dict[str, Any],
    issues_data: list[dict[str, Any]],
) -> list[tuple[colors.Color, str]]:
    """Generate key findings with severity colours."""
    findings: list[tuple[colors.Color, str]] = []
    st = _extract_stats(report_data)
    flesch, _ = _extract_readability(report_data)
    total = int(score_data.get("total_issues", 0))
    passive_pct = _compute_passive_pct(
        issues_data, st["sentence_count"],
    )
    avg_sl = st["avg_sentence_length"]

    if flesch < 30:
        findings.append((
            _RED,
            "Readability needs improvement - content may be too "
            "complex for most readers.",
        ))
    elif flesch < 60:
        findings.append((
            _ORANGE,
            "Readability could be improved for broader "
            "accessibility.",
        ))
    else:
        findings.append((
            _GREEN,
            "Readability is strong - accessible to a broad "
            "audience.",
        ))

    if avg_sl > 20:
        findings.append((
            _GOLD,
            f"Sentence length ({avg_sl:.1f} words avg) could be "
            "adjusted.",
        ))

    if passive_pct > 15:
        findings.append((
            _RED,
            f"High passive voice usage ({passive_pct:.0f}%) impacts "
            "engagement.",
        ))

    if total > 0:
        findings.append((
            _GOLD,
            f"{total} issues found - systematic revision "
            "recommended.",
        ))
    else:
        findings.append((
            _GREEN,
            "No issues found - excellent document quality.",
        ))

    return findings[:4]


def _compute_priority_actions(
    score_data: dict[str, Any],
    issues_data: list[dict[str, Any]],
) -> list[tuple[str, str, str, str]]:
    """Generate priority action rows (severity, action, impact, effort).

    Returns up to 3 rows derived from the top issue categories.
    """
    cats = score_data.get("category_counts", {})
    sorted_cats = sorted(
        cats.items(), key=lambda x: x[1], reverse=True,
    )

    _action_map: dict[str, tuple[str, str]] = {
        "grammar": (
            "Reduce passive voice usage",
            "Creates more engaging, direct content",
        ),
        "style": (
            "Address style consistency issues",
            "Improves professional tone",
        ),
        "word_usage": (
            "Simplify word choices",
            "Enhances clarity for readers",
        ),
        "punctuation": (
            "Fix punctuation issues",
            "Enhances reading flow",
        ),
        "structure": (
            "Improve document structure",
            "Better navigation and scannability",
        ),
        "audience": (
            "Adjust audience targeting",
            "Better reader engagement",
        ),
    }

    actions: list[tuple[str, str, str, str]] = []
    for cat, count in sorted_cats:
        if count == 0 or len(actions) >= 3:
            break
        high_count = sum(
            1 for i in issues_data
            if i.get("category") == cat
            and i.get("severity") == "high"
        )
        severity = "HIGH" if high_count > 0 else "MEDIUM"
        mapped = _action_map.get(cat)
        if mapped:
            action_text, impact = mapped
        else:
            label = cat.replace("_", " ").title()
            action_text = f"Address {label.lower()} issues ({count} found)"
            impact = f"Reduces errors by {min(round(count / max(int(score_data.get('total_issues', 1)), 1) * 100), 100)}%"
        effort = "Low" if count <= 5 else "Medium"
        actions.append((severity, action_text, impact, effort))
    return actions


# ── PAGE 1: Cover ────────────────────────────────────────────────────

def _build_cover(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    report_data: dict[str, Any],
    score_data: dict[str, Any],
    issues_data: list[dict[str, Any]],
) -> None:
    """Page 1 — title, hero score, stat grid, key insights."""
    score = int(score_data.get("score", 0))
    color = _score_color(score)
    label = _score_label(score)
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")

    story.append(Paragraph("Writing Analytics Report", styles["title"]))
    story.append(Paragraph(
        f"Comprehensive Analysis \u2022 Generated {date_str}",
        styles["subtitle"],
    ))

    # Hero score
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f'<font color="{_hex(color)}">{score}</font>',
        styles["score_big"],
    ))
    story.append(Paragraph(
        "Overall Quality Score", styles["score_label"],
    ))
    story.append(Paragraph(
        f'<font color="{_hex(color)}"><b>{label}</b></font>',
        styles["score_label"],
    ))
    story.append(Spacer(1, 16))

    # Stat grid
    story.append(_stat_card_grid(
        report_data, score_data, issues_data, styles,
    ))
    story.append(Spacer(1, 20))

    # Key Insights
    story.append(Paragraph("<b>Key Insights</b>", styles["h2"]))
    for insight in _compute_key_insights(report_data, score_data):
        story.append(Paragraph(f"\u2022 {insight}", styles["body"]))


# ── PAGE 2: Executive Summary ────────────────────────────────────────

def _build_executive(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    report_data: dict[str, Any],
    score_data: dict[str, Any],
    issues_data: list[dict[str, Any]],
) -> None:
    """Page 2 — narrative, score cards, findings, priority actions."""
    score = int(score_data.get("score", 0))
    st = _extract_stats(report_data)
    flesch, grade = _extract_readability(report_data)
    total = int(score_data.get("total_issues", 0))

    story.append(Paragraph("Executive Summary", styles["h1"]))

    # Narrative paragraph
    audience = _grade_audience(grade)
    r_lbl = _readability_label(flesch)
    s_lbl = _score_label(score)
    sc_hex = _hex(_score_color(score))
    narrative = (
        f'This report analyzes a <b>{st["word_count"]:,}-word document'
        f"</b> for writing quality, readability, and professional "
        f"effectiveness. The content achieves a grade level of "
        f"<b>{grade:.1f}</b>, making it appropriate for "
        f"<b>{audience}</b>. With a Flesch Reading Ease score of "
        f"<b>{flesch:.1f}</b> ({r_lbl}), the document receives an "
        f'overall quality grade of <b><font color="{sc_hex}">'
        f"{s_lbl}</font></b>. The analysis identified <b>{total} "
        f'area{"s" if total != 1 else ""}</b> for potential '
        "improvement."
    )
    story.append(Paragraph(narrative, styles["body"]))
    story.append(Spacer(1, 10))

    # Score cards row
    story.append(_score_cards_row(score_data, report_data, styles))
    story.append(Spacer(1, 14))

    # Key Findings
    _add_key_findings_section(
        story, styles, report_data, score_data, issues_data,
    )
    story.append(Spacer(1, 8))

    # Priority Actions
    _add_priority_actions(story, styles, score_data, issues_data)
    story.append(Spacer(1, 10))

    # Time savings callout
    _add_time_savings(story, styles, total)


def _add_key_findings_section(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    report_data: dict[str, Any],
    score_data: dict[str, Any],
    issues_data: list[dict[str, Any]],
) -> None:
    """Render coloured key findings bullets."""
    story.append(Paragraph("<b>Key Findings</b>", styles["h2"]))
    findings = _compute_key_findings(
        report_data, score_data, issues_data,
    )
    for color, text in findings:
        square = f'<font color="{_hex(color)}">\u25A0</font>'
        story.append(Paragraph(f"{square}  {text}", styles["body"]))


def _add_priority_actions(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    score_data: dict[str, Any],
    issues_data: list[dict[str, Any]],
) -> None:
    """Render priority actions table."""
    story.append(Paragraph("<b>Priority Actions</b>", styles["h2"]))
    actions = _compute_priority_actions(score_data, issues_data)
    if not actions:
        story.append(Paragraph(
            "No priority actions needed.", styles["body"],
        ))
        return

    sev_colors = {"HIGH": _hex(_RED), "MEDIUM": _hex(_ORANGE)}
    header = ["Priority", "Action", "Impact", "Effort"]
    rows: list[list[Any]] = [header]
    for sev, action, impact, effort in actions:
        sc = sev_colors.get(sev, _hex(_DARK))
        rows.append([
            Paragraph(
                f'<font color="{sc}"><b>{sev}</b></font>',
                styles["cell"],
            ),
            action, impact, effort,
        ])

    widths = [1.0 * inch, 2.5 * inch, 2.0 * inch, 1.0 * inch]
    story.append(_styled_table(rows, widths))


def _add_time_savings(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    total_issues: int,
) -> None:
    """Render time savings callout box."""
    if total_issues == 0:
        return
    manual = math.ceil(total_issues * 0.5)
    ai = math.ceil(total_issues * 0.18)
    savings = manual - ai
    gain = round(savings / max(manual, 1) * 100)
    text = (
        f"<b>Estimated Time Savings with AI-Assisted Editing</b> "
        f"Manual editing estimate: {manual} minutes \u2022 "
        f"AI-assisted: {ai} minutes "
        f'<font color="{_hex(_GREEN)}"><b>Potential savings: '
        f"{savings} minutes ({gain}% productivity gain)</b></font>"
    )
    story.append(_callout_box(text, _BLUE_BG, _BLUE_BORDER, styles))


# ── PAGE 3: Writing Analytics ────────────────────────────────────────

def _build_analytics(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    report_data: dict[str, Any],
) -> None:
    """Page 3 — grade level assessment and readability analysis."""
    _, grade = _extract_readability(report_data)

    story.append(Paragraph("Writing Analytics", styles["h1"]))

    # Grade Level Assessment
    _add_grade_level(story, styles, grade)
    story.append(Spacer(1, 12))

    # Readability Analysis
    _add_readability_table(story, styles, report_data)


def _add_grade_level(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    grade: float,
) -> None:
    """Render grade level assessment table + interpretation callout."""
    story.append(
        Paragraph("<b>Grade Level Assessment</b>", styles["h2"]),
    )

    assessment = _grade_assessment(grade)
    audience = _grade_audience(grade)
    in_target = 9 <= grade <= 11
    recommendation = (
        "Appropriate for professional technical writing"
        if in_target
        else "Consider simplifying for broader accessibility"
    )

    rows = [
        ["Metric", "Value", "Assessment"],
        ["Current Grade Level", f"{grade:.1f}", assessment],
        ["Target Range", "9\u201311", "Professional Technical Writing"],
        ["Target Audience", "", audience],
        ["Recommendation", "", recommendation],
    ]
    widths = [2.2 * inch, 1.5 * inch, 2.8 * inch]
    story.append(_styled_table(rows, widths))
    story.append(Spacer(1, 8))

    # Interpretation callout
    if grade > 12:
        interp = "May be challenging for general readers"
    elif grade >= 9:
        interp = "Appropriate for professional technical writing"
    else:
        interp = "Very accessible - suitable for broad audience"
    story.append(_callout_box(
        f"<b>Interpretation:</b> {interp}",
        _CALLOUT_BG, _CALLOUT_BORDER, styles,
    ))


def _add_readability_table(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    report_data: dict[str, Any],
) -> None:
    """Render 4-metric readability analysis table."""
    readability = report_data.get("readability", {})
    if not readability:
        return

    story.append(
        Paragraph("<b>Readability Analysis</b>", styles["h2"]),
    )

    targets = {
        _FLESCH_RE: "60\u201370",
        _FLESCH_KG: "9\u201311",
        _GUNNING_FOG: "< 12",
        _COLEMAN_LIAU: "10\u201314",
    }

    rows: list[list[str]] = [
        ["Metric", "Score", "Interpretation", "Target"],
    ]
    for name, data in readability.items():
        score = float(data.get("score", 0))
        interp = _metric_interpretation(name, score)
        target = targets.get(name, "\u2014")
        rows.append([name, f"{score:.1f}", interp, target])

    if len(rows) > 1:
        widths = [2.4 * inch, 0.9 * inch, 1.8 * inch, 1.4 * inch]
        story.append(_styled_table(rows, widths))


# ── PAGE 4: Quality Metrics + AI Readiness ───────────────────────────

def _build_quality(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    report_data: dict[str, Any],
    issues_data: list[dict[str, Any]],
) -> None:
    """Page 4 — writing quality metrics and LLM consumability."""
    _add_quality_metrics(
        story, styles, report_data, issues_data,
    )
    story.append(Spacer(1, 8))
    _add_llm_readiness(story, styles, report_data)


def _add_quality_metrics(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    report_data: dict[str, Any],
    issues_data: list[dict[str, Any]],
) -> None:
    """Render writing quality metrics with assessments."""
    story.append(
        Paragraph("Writing Quality Metrics", styles["h1"]),
    )

    st = _extract_stats(report_data)
    passive_pct = _compute_passive_pct(
        issues_data, st["sentence_count"],
    )
    diversity = st["vocabulary_diversity"]
    avg_sl = st["avg_sentence_length"]
    avg_syl = st["avg_syllables_per_word"]

    metrics = [
        (
            "Average Sentence Length",
            f"{avg_sl:.1f} words",
            "Target: 15\u201320 words",
            avg_sl <= 20,
            "Sentences getting lengthy"
            if avg_sl > 20 else "Good sentence length",
            "Consider breaking some sentences for better clarity."
            if avg_sl > 20 else "Sentence length is appropriate.",
        ),
        (
            "Passive Voice Usage",
            f"{passive_pct:.1f}%",
            "Target: < 15%",
            passive_pct <= 15,
            "Too much passive voice"
            if passive_pct > 15 else "Good active voice usage",
            "Actively rewrite sentences for stronger, clearer "
            "communication."
            if passive_pct > 15
            else "Active voice is used effectively.",
        ),
        (
            "Vocabulary Diversity",
            f"{diversity:.2f}",
            "Target: > 0.7",
            diversity >= 0.7,
            "Limited vocabulary diversity"
            if diversity < 0.7
            else "Good vocabulary diversity",
            "Vary word choices to make content more engaging."
            if diversity < 0.7
            else "Good variety of vocabulary throughout.",
        ),
        (
            "Avg Syllables per Word",
            f"{avg_syl:.2f}",
            "Target: < 1.5",
            avg_syl <= 1.5,
            "Higher complexity vocabulary"
            if avg_syl > 1.5 else "Good word simplicity",
            "Consider simpler alternatives for non-essential "
            "technical terms."
            if avg_syl > 1.5 else "Word complexity is appropriate.",
        ),
    ]

    for name, value, target, good, assessment, recommendation in metrics:
        ac = _assess_color(good)
        story.append(Paragraph(
            f"<b>{name}</b>: {value} ({target}) "
            f'<font color="{ac}">{assessment}</font> - '
            f"{recommendation}",
            styles["body"],
        ))
        story.append(Spacer(1, 6))


def _add_llm_readiness(
    story: list[Any],
    styles: dict[str, ParagraphStyle],
    report_data: dict[str, Any],
) -> None:
    """Render AI & LLM Readiness section."""
    llm = report_data.get("llm_consumability", {})
    if not llm:
        return

    story.append(
        Paragraph("AI &amp; LLM Readiness", styles["h1"]),
    )

    llm_score = int(llm.get("score", 0))
    llm_label = str(llm.get("label", "N/A"))
    llm_color = _score_color(llm_score)

    story.append(Paragraph(
        f'<b>LLM Consumability Score:</b> '
        f'<font size="14" color="{_hex(llm_color)}">'
        f"<b>{llm_score}/100</b></font> ({llm_label})",
        styles["body"],
    ))
    story.append(Spacer(1, 8))

    # Strengths
    strengths = llm.get("strengths", [])
    if strengths:
        story.append(Paragraph("<b>Strengths:</b>", styles["body"]))
        for s in strengths[:3]:
            story.append(Paragraph(
                f'<font color="{_hex(_GREEN)}">\u2713</font>  {s}',
                styles["body"],
            ))

    # Improvements
    improvements = llm.get("improvements", [])
    if improvements:
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            "<b>Areas for Improvement:</b>", styles["body"],
        ))
        for imp in improvements[:3]:
            story.append(Paragraph(
                f'<font color="{_hex(_ORANGE)}">\u25A0</font>  {imp}',
                styles["body"],
            ))

    story.append(Spacer(1, 10))

    # Benefits callout
    story.append(_callout_box(
        "<b>Benefits of AI-Optimized Content:</b> Well-structured "
        "content with clear readability metrics processes 40-60% "
        "more effectively through LLM systems, resulting in higher "
        "quality automated improvements and more accurate content "
        "generation.",
        _BLUE_BG, _BLUE_BORDER, styles,
    ))


# ── Public API ───────────────────────────────────────────────────────

def generate_pdf_report(
    report_data: dict[str, Any],
    score_data: dict[str, Any],
    issues_data: list[dict[str, Any]],
) -> bytes:
    """Generate a PDF report as bytes.

    Produces a 4-page report:
      Page 1 — Cover with hero score, stat grid, key insights
      Page 2 — Executive summary, score cards, priority actions
      Page 3 — Writing analytics (grade level, readability)
      Page 4 — Quality metrics and AI/LLM readiness

    Args:
        report_data: Serialized ReportResponse dict.
        score_data: Serialized ScoreResponse dict.
        issues_data: Serialized list of IssueResponse dicts.

    Returns:
        PDF file content as bytes.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=_MARGIN, rightMargin=_MARGIN,
        topMargin=_MARGIN, bottomMargin=0.85 * inch,
    )

    styles = _build_styles()
    story: list[Any] = []

    _build_cover(story, styles, report_data, score_data, issues_data)
    story.append(PageBreak())
    _build_executive(
        story, styles, report_data, score_data, issues_data,
    )
    story.append(PageBreak())
    _build_analytics(story, styles, report_data)
    story.append(PageBreak())
    _build_quality(
        story, styles, report_data, issues_data,
    )

    doc.build(story, onFirstPage=_first_page, onLaterPages=_later_pages)
    return buf.getvalue()
