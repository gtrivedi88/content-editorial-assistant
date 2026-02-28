"""
Integration test for false positive reduction.

Loads a realistic .adoc file of legitimate technical writing patterns
and verifies that CEA does NOT flag them as errors. Any error flagged
here is a genuine false positive that needs investigation.

NOTE: This test intentionally avoids words the IBM Style Guide legitimately
flags (e.g., "leverage", "enable", "best practice", "below", "native").
It focuses on patterns that should NEVER produce errors: URLs, emails,
inline code, file paths, global exception terms, and standard procedures.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

FIXTURE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'fixtures',
    'test_false_positives.adoc'
)


class TestFalsePositiveReduction:
    """Verify that legitimate technical writing patterns are NOT flagged."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Load the test fixture and run analysis once."""
        with open(FIXTURE_PATH, 'r', encoding='utf-8') as f:
            self.text = f.read()

        from style_analyzer.base_analyzer import StyleAnalyzer
        self.analyzer = StyleAnalyzer()
        self.result = self.analyzer.analyze(self.text)
        self.errors = self.result.get('errors', [])
        self.style_errors = [e for e in self.errors if e.get('type') != 'system_error']

    def _errors_in_section(self, section_heading: str):
        """Get errors whose sentence contains text from a given section."""
        lines = self.text.split('\n')
        in_section = False
        section_lines = []
        for line in lines:
            if line.strip().startswith('== ') and section_heading.lower() in line.lower():
                in_section = True
                continue
            elif line.strip().startswith('== ') and in_section:
                break
            elif in_section and line.strip():
                section_lines.append(line.strip().lower())

        section_errors = []
        for error in self.style_errors:
            sentence = error.get('sentence', '').lower()
            if any(sl in sentence for sl in section_lines if len(sl) > 10):
                section_errors.append(error)
        return section_errors

    def test_no_errors_on_urls_emails_paths(self):
        """URLs, emails, and file paths should not be flagged."""
        errors = self._errors_in_section('Technical URLs, emails, and file paths')
        assert len(errors) == 0, (
            f"Found {len(errors)} false positive(s) on URLs/emails/paths: "
            f"{[(e['type'], e['message'][:60]) for e in errors]}"
        )

    def test_no_errors_on_inline_code(self):
        """Inline code (backtick-wrapped) should not be flagged."""
        errors = self._errors_in_section('Inline code and commands')
        assert len(errors) == 0, (
            f"Found {len(errors)} false positive(s) on inline code: "
            f"{[(e['type'], e['message'][:60]) for e in errors]}"
        )

    def test_no_errors_on_global_exceptions(self):
        """Terms in the global exception list should never be flagged."""
        errors = self._errors_in_section('Global exception terms')
        assert len(errors) == 0, (
            f"Found {len(errors)} false positive(s) on global exception terms: "
            f"{[(e['type'], e['message'][:60]) for e in errors]}"
        )

    def test_overall_false_positive_rate_below_threshold(self):
        """Total errors should be minimal for this clean content.
        The test file contains only patterns that should NOT be flagged.
        """
        # Allow at most 2 errors across the entire document
        assert len(self.style_errors) <= 2, (
            f"Found {len(self.style_errors)} error(s) on clean content (max 2 allowed): "
            f"{[(e['type'], e['message'][:60]) for e in self.style_errors]}"
        )

    def test_confidence_threshold_applied(self):
        """All reported errors should have confidence >= 0.60."""
        for error in self.style_errors:
            confidence = error.get('confidence_score', error.get('confidence', 1.0))
            if confidence is not None and error.get('enhanced_validation_available', False):
                assert confidence >= 0.60, (
                    f"Low confidence error leaked: confidence={confidence:.2f}, "
                    f"type={error.get('type')}, msg={error.get('message', '')[:50]}"
                )

    def test_code_blocks_produce_no_errors(self):
        """Code blocks (source listings) should be completely skipped."""
        errors = self._errors_in_section('Code blocks should be completely skipped')
        assert len(errors) == 0, (
            f"Found {len(errors)} error(s) in code block section: "
            f"{[(e['type'], e['message'][:60]) for e in errors]}"
        )
