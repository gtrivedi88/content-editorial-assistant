"""Gap analysis for IBM Style Guide A-Z word list and chapter coverage.

Compares terms extracted from the IBM Style Guide PDF (A-Z word usage
section, pages 284-419) against existing YAML term configs to identify
missing entries.  Also audits chapter-to-rule coverage across all
IBM style mapping categories.

This script runs at build time only and is NOT deployed to the cluster.

Usage:
    python scripts/gap_analysis.py \
        --ibm-pdf style_guides/ibm/ibm-style-documentation.pdf \
        --output-report gap_report.md

Dependencies (build-time only):
    - PyMuPDF (fitz) for PDF text extraction
    - PyYAML for YAML parsing
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import yaml

logger = logging.getLogger(__name__)

# IBM Style Guide A-Z word usage section page range (1-based)
AZ_START_PAGE = 284
AZ_END_PAGE = 419

# Paths to term config files (relative to project root)
TERM_CONFIG_PATHS = [
    "rules/word_usage/config/word_usage_config.yaml",
    "rules/word_usage/config/do_not_use_config.yaml",
    "rules/word_usage/config/simple_words_config.yaml",
    "rules/language_and_grammar/config/terminology_config.yaml",
    "rules/word_usage/config/product_names_config.yaml",
]

# IBM style mapping path (relative to project root)
IBM_MAPPING_PATH = "style_guides/ibm/ibm_style_mapping.yaml"


def extract_az_headwords(pdf_path: Path) -> List[Dict[str, Any]]:
    """Extract headword entries from the A-Z word usage section of the PDF.

    Scans pages 284-419 for bold headword patterns that indicate term
    entries in the IBM Style Guide A-Z section.

    Args:
        pdf_path: Path to the IBM Style Guide PDF.

    Returns:
        List of dicts with 'term', 'page', and 'context' keys.
    """
    try:
        import fitz  # type: ignore[import-untyped]
    except ImportError:
        logger.error("PyMuPDF (fitz) is required: pip install PyMuPDF")
        return []

    doc = fitz.open(str(pdf_path))
    headwords: List[Dict[str, Any]] = []

    for page_num in range(AZ_START_PAGE - 1, min(AZ_END_PAGE, len(doc))):
        page = doc[page_num]
        blocks = page.get_text("dict", sort=True).get("blocks", [])
        headwords.extend(_extract_headwords_from_blocks(blocks, page_num + 1))

    doc.close()
    logger.info("Extracted %d headword entries from A-Z section", len(headwords))
    return headwords


def _extract_headwords_from_blocks(
    blocks: List[Dict[str, Any]], page_num: int,
) -> List[Dict[str, Any]]:
    """Extract bold headwords from a page's text blocks.

    Identifies headword entries by looking for bold-formatted text
    at the start of text blocks, which is the IBM Style Guide's
    convention for A-Z dictionary entries.

    Args:
        blocks: PyMuPDF dict-mode text blocks from a single page.
        page_num: 1-based page number for attribution.

    Returns:
        List of headword dicts found on this page.
    """
    headwords: List[Dict[str, Any]] = []

    for block in blocks:
        if block.get("type") != 0:  # text blocks only
            continue
        for line in block.get("lines", []):
            term = _extract_bold_term(line)
            if term and _is_valid_headword(term):
                context = _build_line_context(line)
                headwords.append({
                    "term": term,
                    "page": page_num,
                    "context": context,
                })

    return headwords


def _extract_bold_term(line: Dict[str, Any]) -> str:
    """Extract the leading bold text from a line as a potential headword.

    Args:
        line: A PyMuPDF line dict containing spans.

    Returns:
        The bold text string, or empty string if no leading bold span.
    """
    spans = line.get("spans", [])
    if not spans:
        return ""

    first_span = spans[0]
    # PyMuPDF font flags: bit 4 = bold (flags & 16)
    is_bold = bool(first_span.get("flags", 0) & 16)
    if not is_bold:
        return ""

    return first_span.get("text", "").strip()


def _is_valid_headword(term: str) -> bool:
    """Check whether a bold term looks like a valid A-Z headword.

    Filters out page headers, section labels, and other non-term
    bold text commonly found in the A-Z section.

    Args:
        term: The bold text to validate.

    Returns:
        True if the term appears to be a genuine headword entry.
    """
    if len(term) < 2 or len(term) > 60:
        return False
    # Skip page numbers, single letters (section headers), all-caps labels
    if term.isdigit() or (len(term) == 1 and term.isalpha()):
        return False
    if term.isupper() and len(term) > 3:
        return False
    # Skip common non-term headers
    skip_patterns = {"IBM Style", "Word Usage", "Index", "Table of Contents"}
    if term in skip_patterns:
        return False
    return True


def _build_line_context(line: Dict[str, Any]) -> str:
    """Build context string from all spans in a line.

    Args:
        line: A PyMuPDF line dict containing spans.

    Returns:
        Concatenated text from all spans, truncated to 200 chars.
    """
    parts = [span.get("text", "") for span in line.get("spans", [])]
    context = " ".join(parts).strip()
    return context[:200]


def load_existing_terms(project_root: Path) -> Set[str]:
    """Load all terms from existing YAML config files.

    Aggregates terms from word_usage, do_not_use, simple_words,
    terminology, and product_names configs into a single set for
    coverage comparison.

    Args:
        project_root: Root directory of the CEA project.

    Returns:
        Set of lowercase term strings found across all configs.
    """
    terms: Set[str] = set()

    for config_path in TERM_CONFIG_PATHS:
        full_path = project_root / config_path
        if not full_path.exists():
            logger.warning("Config file not found: %s", full_path)
            continue
        loaded = _load_terms_from_config(full_path)
        terms.update(loaded)
        logger.info("Loaded %d terms from %s", len(loaded), config_path)

    logger.info("Total existing terms across all configs: %d", len(terms))
    return terms


def _load_terms_from_config(config_path: Path) -> Set[str]:
    """Load terms from a single YAML config file.

    Handles the different config structures: A-Z dicts, flat dicts,
    term_map dicts, and terms-with-messages dicts.

    Args:
        config_path: Path to the YAML config file.

    Returns:
        Set of lowercase term strings from this config.
    """
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    terms: Set[str] = set()

    if "terms" in data:
        # do_not_use format: {terms: {term: {message: ...}}}
        for term in data["terms"]:
            terms.add(str(term).lower())
    elif "simple_words" in data:
        # simple_words format: {simple_words: {complex: simple}}
        for term in data["simple_words"]:
            terms.add(str(term).lower())
    elif "term_map" in data:
        # terminology format: {term_map: {wrong: right}}
        for term in data["term_map"]:
            terms.add(str(term).lower())
    elif "simple_terms" in data:
        # product_names format: {simple_terms: {...}, regex_terms: {...}}
        for term in data.get("simple_terms", {}):
            terms.add(str(term).lower())
    else:
        # word_usage format: {a: {term: replacement}, b: {...}, ...}
        terms.update(_load_az_terms(data))

    return terms


def _load_az_terms(data: Dict[str, Any]) -> Set[str]:
    """Load terms from A-Z structured config (word_usage_config).

    Args:
        data: Parsed YAML dict with single-letter keys.

    Returns:
        Set of lowercase terms from all letter sections.
    """
    terms: Set[str] = set()
    for key, value in data.items():
        if isinstance(value, dict):
            for term in value:
                terms.add(str(term).lower())
    return terms


def compute_coverage(
    headwords: List[Dict[str, Any]], existing_terms: Set[str],
) -> Dict[str, Any]:
    """Compare extracted headwords against existing term configs.

    Args:
        headwords: List of headword dicts from PDF extraction.
        existing_terms: Set of lowercase terms from YAML configs.

    Returns:
        Dict with 'covered', 'missing', 'coverage_pct', and
        'by_letter' breakdown.
    """
    covered: List[Dict[str, Any]] = []
    missing: List[Dict[str, Any]] = []

    for entry in headwords:
        term_lower = entry["term"].lower()
        if term_lower in existing_terms:
            covered.append(entry)
        else:
            missing.append(entry)

    by_letter = _compute_per_letter_coverage(headwords, existing_terms)

    total = len(headwords)
    coverage_pct = (len(covered) / total * 100) if total > 0 else 0.0

    return {
        "total_headwords": total,
        "covered": covered,
        "missing": missing,
        "covered_count": len(covered),
        "missing_count": len(missing),
        "coverage_pct": round(coverage_pct, 1),
        "by_letter": by_letter,
    }


def _compute_per_letter_coverage(
    headwords: List[Dict[str, Any]], existing_terms: Set[str],
) -> Dict[str, Dict[str, int]]:
    """Compute coverage breakdown per starting letter.

    Args:
        headwords: All extracted headwords.
        existing_terms: Set of existing lowercase terms.

    Returns:
        Dict mapping letter to {total, covered, missing} counts.
    """
    by_letter: Dict[str, Dict[str, int]] = {}

    for entry in headwords:
        letter = entry["term"][0].upper() if entry["term"] else "?"
        if letter not in by_letter:
            by_letter[letter] = {"total": 0, "covered": 0, "missing": 0}
        by_letter[letter]["total"] += 1
        if entry["term"].lower() in existing_terms:
            by_letter[letter]["covered"] += 1
        else:
            by_letter[letter]["missing"] += 1

    return dict(sorted(by_letter.items()))


def audit_chapter_coverage(project_root: Path) -> Dict[str, Any]:
    """Audit rule coverage across IBM style mapping categories.

    Loads the IBM style mapping YAML and reports which categories
    have rules, how many rules per category, and verification status.

    Args:
        project_root: Root directory of the CEA project.

    Returns:
        Dict with per-category coverage stats and overall summary.
    """
    mapping_path = project_root / IBM_MAPPING_PATH
    if not mapping_path.exists():
        logger.error("IBM mapping file not found: %s", mapping_path)
        return {}

    with open(mapping_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    categories: Dict[str, Dict[str, Any]] = {}
    skip_keys = {"version", "last_updated", "source_documents",
                 "confidence_adjustments", "verification_stats"}

    for category_key, category_data in data.items():
        if category_key in skip_keys or not isinstance(category_data, dict):
            continue
        stats = _audit_category(category_data)
        categories[category_key] = stats

    total_rules = sum(c["rule_count"] for c in categories.values())
    verified = sum(c["verified"] for c in categories.values())
    custom = sum(c["custom"] for c in categories.values())

    return {
        "categories": categories,
        "total_rules": total_rules,
        "total_verified": verified,
        "total_custom": custom,
        "category_count": len(categories),
    }


def _audit_category(category_data: Dict[str, Any]) -> Dict[str, Any]:
    """Audit a single category's rule coverage.

    Args:
        category_data: Dict of rules within a category.

    Returns:
        Dict with rule_count, verified, custom, and rule_ids.
    """
    rule_count = 0
    verified = 0
    custom = 0
    rule_ids: List[str] = []

    for rule_key, rule_data in category_data.items():
        if not isinstance(rule_data, dict) or "rule_id" not in rule_data:
            continue
        rule_count += 1
        rule_ids.append(rule_data["rule_id"])

        guide_data = rule_data.get("ibm_style", {})
        status = guide_data.get("verification_status", "unverified")
        if status == "verified":
            verified += 1
        elif status == "custom_rule":
            custom += 1

    return {
        "rule_count": rule_count,
        "verified": verified,
        "custom": custom,
        "rule_ids": rule_ids,
    }


def generate_report(
    coverage: Dict[str, Any],
    chapter_audit: Dict[str, Any],
    output_path: Path,
) -> None:
    """Generate a Markdown gap analysis report.

    Args:
        coverage: A-Z coverage analysis results.
        chapter_audit: Chapter-to-rule audit results.
        output_path: Path to write the Markdown report.
    """
    lines: List[str] = []
    lines.append("# IBM Style Guide Gap Analysis Report\n")
    lines.append(f"Generated by `scripts/gap_analysis.py`\n")

    _write_az_summary(lines, coverage)
    _write_per_letter_table(lines, coverage)
    _write_missing_terms(lines, coverage)
    _write_chapter_audit(lines, chapter_audit)

    output_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Report written to %s", output_path)


def _write_az_summary(
    lines: List[str], coverage: Dict[str, Any],
) -> None:
    """Write the A-Z coverage summary section.

    Args:
        lines: List of report lines to append to.
        coverage: Coverage analysis results.
    """
    lines.append("## A-Z Word Usage Coverage\n")
    lines.append(f"- **Total headwords extracted**: {coverage['total_headwords']}")
    lines.append(f"- **Covered in configs**: {coverage['covered_count']}")
    lines.append(f"- **Missing from configs**: {coverage['missing_count']}")
    lines.append(f"- **Coverage**: {coverage['coverage_pct']}%\n")


def _write_per_letter_table(
    lines: List[str], coverage: Dict[str, Any],
) -> None:
    """Write per-letter coverage breakdown table.

    Args:
        lines: List of report lines to append to.
        coverage: Coverage analysis results.
    """
    lines.append("### Per-Letter Coverage\n")
    lines.append("| Letter | Total | Covered | Missing | Coverage |")
    lines.append("|--------|-------|---------|---------|----------|")

    for letter, stats in coverage.get("by_letter", {}).items():
        total = stats["total"]
        covered = stats["covered"]
        missing = stats["missing"]
        pct = round(covered / total * 100, 0) if total > 0 else 0
        lines.append(f"| {letter} | {total} | {covered} | {missing} | {pct:.0f}% |")

    lines.append("")


def _write_missing_terms(
    lines: List[str], coverage: Dict[str, Any],
) -> None:
    """Write the missing terms section with auto-generated YAML snippets.

    Args:
        lines: List of report lines to append to.
        coverage: Coverage analysis results.
    """
    missing = coverage.get("missing", [])
    if not missing:
        lines.append("### Missing Terms\n")
        lines.append("No missing terms found.\n")
        return

    lines.append(f"### Missing Terms ({len(missing)} entries)\n")
    lines.append("Priority candidates (first 50):\n")

    for entry in missing[:50]:
        term = entry["term"]
        page = entry["page"]
        context = entry.get("context", "")
        lines.append(f"- **{term}** (p.{page}): {context}")

    if len(missing) > 50:
        lines.append(f"\n... and {len(missing) - 50} more terms.\n")

    # Auto-generated YAML snippet for top candidates
    lines.append("\n### Auto-Generated YAML Snippet\n")
    lines.append("```yaml")
    lines.append("# Add to word_usage_config.yaml under appropriate letter")
    for entry in missing[:20]:
        term = entry["term"]
        letter = term[0].lower() if term else "a"
        lines.append(f'# {letter}:')
        lines.append(f'#   "{term}": "TODO_REPLACEMENT"')
    lines.append("```\n")


def _write_chapter_audit(
    lines: List[str], chapter_audit: Dict[str, Any],
) -> None:
    """Write the chapter-to-rule coverage audit section.

    Args:
        lines: List of report lines to append to.
        chapter_audit: Chapter audit results.
    """
    lines.append("## Chapter-to-Rule Coverage Audit\n")

    if not chapter_audit:
        lines.append("No IBM mapping file found.\n")
        return

    lines.append(f"- **Total categories**: {chapter_audit.get('category_count', 0)}")
    lines.append(f"- **Total rules mapped**: {chapter_audit.get('total_rules', 0)}")
    lines.append(f"- **Verified rules**: {chapter_audit.get('total_verified', 0)}")
    lines.append(f"- **Custom rules**: {chapter_audit.get('total_custom', 0)}\n")

    lines.append("### Per-Category Breakdown\n")
    lines.append("| Category | Rules | Verified | Custom |")
    lines.append("|----------|-------|----------|--------|")

    categories = chapter_audit.get("categories", {})
    for cat_name, stats in sorted(categories.items()):
        rules = stats["rule_count"]
        verified = stats["verified"]
        custom = stats["custom"]
        lines.append(f"| {cat_name} | {rules} | {verified} | {custom} |")

    lines.append("")


def main() -> None:
    """Run gap analysis and generate report."""
    parser = argparse.ArgumentParser(
        description="IBM Style Guide gap analysis",
    )
    parser.add_argument(
        "--ibm-pdf",
        type=Path,
        help="Path to IBM Style Guide PDF",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=Path("gap_report.md"),
        help="Output report path (default: gap_report.md)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    project_root = args.project_root.resolve()
    existing_terms = load_existing_terms(project_root)

    coverage: Dict[str, Any] = {}
    if args.ibm_pdf and args.ibm_pdf.exists():
        headwords = extract_az_headwords(args.ibm_pdf)
        coverage = compute_coverage(headwords, existing_terms)
    else:
        logger.warning(
            "IBM PDF not provided or not found. "
            "Skipping A-Z analysis, running chapter audit only."
        )
        coverage = {
            "total_headwords": 0,
            "covered": [],
            "missing": [],
            "covered_count": 0,
            "missing_count": 0,
            "coverage_pct": 0.0,
            "by_letter": {},
        }

    chapter_audit = audit_chapter_coverage(project_root)

    generate_report(coverage, chapter_audit, args.output_report)

    _print_summary(coverage, chapter_audit)


def _print_summary(
    coverage: Dict[str, Any], chapter_audit: Dict[str, Any],
) -> None:
    """Print a summary to stdout.

    Args:
        coverage: A-Z coverage analysis results.
        chapter_audit: Chapter audit results.
    """
    logger.info("=== Gap Analysis Summary ===")
    if coverage["total_headwords"] > 0:
        logger.info(
            "A-Z Terms: %d total, %d covered (%.1f%%), %d missing",
            coverage["total_headwords"],
            coverage["covered_count"],
            coverage["coverage_pct"],
            coverage["missing_count"],
        )
    if chapter_audit:
        logger.info(
            "Rules: %d mapped across %d categories, %d verified",
            chapter_audit.get("total_rules", 0),
            chapter_audit.get("category_count", 0),
            chapter_audit.get("total_verified", 0),
        )


if __name__ == "__main__":
    main()
