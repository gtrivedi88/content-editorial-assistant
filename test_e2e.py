"""End-to-end test: run deterministic + LLM analysis on test.adoc."""
import os
import sys
import logging

# Enable LLM — must be set before importing anything
os.environ["LLM_ENABLED"] = "true"

from app import create_app
from app.services.parsing import detect_and_parse
from app.services.analysis.preprocessor import preprocess
from app.services.analysis.orchestrator import (
    analyze as run_analysis,
    _run_llm_phases,
    _collect_acronyms,
)
from app.services.session.store import get_session_store


def main():
    logging.basicConfig(level=logging.INFO)

    app = create_app()

    with open("test.adoc", "r", encoding="utf-8") as f:
        content = f.read()

    with app.app_context():
        # Parse as AsciiDoc
        parse_result = detect_and_parse(content, "test.adoc")
        blocks = parse_result.blocks if parse_result.blocks else []

        print(f"\n=== Parsed {len(blocks)} blocks ===")

        # Phase 1: Deterministic via analyze()
        # analyze() also tries to schedule LLM in background via socketio,
        # but the greenlet won't execute without a running server — harmless.
        response = run_analysis(
            content,
            content_type="procedure",
            file_type="asciidoc",
            socket_sid=None,
            blocks=blocks,
        )

        det_issues = list(response.issues)
        print(f"\n=== Phase 1 — Deterministic Issues: {len(det_issues)} ===")
        for i, iss in enumerate(det_issues):
            print(f"  [{i}] {iss.rule_name}: {iss.flagged_text!r} "
                  f"span={iss.span} sev={iss.severity}")

        # Phase 2+3: Run LLM phases SYNCHRONOUSLY
        # Re-run preprocessing to get prep dict (analyze() doesn't expose it)
        print("\n=== Running LLM phases synchronously... ===")
        prep = preprocess(content, blocks=blocks, file_type="asciidoc")
        content_type = prep.get("detected_content_type") or "procedure"
        acronym_context = _collect_acronyms(prep["text"])

        # Call _run_llm_phases directly — runs granular + global + judge + merge
        # Updates the session store with partial=False when done
        _run_llm_phases(
            response.session_id,
            None,       # no socket_sid
            prep,
            det_issues,
            content_type,
            acronym_context,
        )

        # Retrieve final merged results from session store
        store = get_session_store()
        final = store.get_session(response.session_id)

        if final and hasattr(final, "issues"):
            all_issues = final.issues
        else:
            print("WARNING: No final session found, showing det-only")
            all_issues = det_issues

        print(f"\n{'='*60}")
        print(f"=== FINAL MERGED ISSUES: {len(all_issues)} ===")
        print(f"{'='*60}")

        for i, iss in enumerate(all_issues):
            src = iss.source
            print(f"\nIssue[{i}] ({src}):")
            print(f"  Rule: {iss.rule_name}")
            print(f"  Severity: {iss.severity}")
            print(f"  Flagged: {iss.flagged_text!r}")
            print(f"  Span: {iss.span}")
            print(f"  Message: {iss.message}")
            if iss.suggestions:
                print(f"  Suggestions: {iss.suggestions[:2]}")

        # Summary comparison with Gemini ground truth
        print(f"\n{'='*60}")
        print("=== GEMINI GROUND TRUTH COMPARISON ===")
        print(f"{'='*60}")
        gemini = [
            ("Grammar", '"system passes"', "Anthropomorphism"),
            ("Tone", '"You can remove"', "Be direct/imperative"),
            ("Structure", "List items missing dots", "Punctuation in lists"),
            ("Accessibility", '"placeholders below"', "Directional terms"),
            ("Formatting", "curl", "Command highlighting"),
        ]
        for cat, text, reason in gemini:
            matched = [
                iss for iss in all_issues
                if text.strip('"') in (iss.flagged_text or "")
                or text.strip('"').lower() in (iss.message or "").lower()
            ]
            status = "FOUND" if matched else "MISSING"
            if matched:
                rules = ", ".join({m.rule_name for m in matched})
                print(f"  {status}: {cat} — {text} [{rules}]")
            else:
                print(f"  {status}: {cat} — {text} ({reason})")

        # Count by source
        det_count = sum(1 for i in all_issues if i.source == "deterministic")
        llm_count = sum(1 for i in all_issues
                        if i.source and i.source.startswith("llm"))
        print(f"\n  Total: {len(all_issues)} "
              f"(deterministic={det_count}, llm={llm_count})")


if __name__ == "__main__":
    main()
