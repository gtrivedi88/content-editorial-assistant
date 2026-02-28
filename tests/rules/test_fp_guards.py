"""Tests for false-positive guards on deterministic rules.

Validates that specific guard conditions in 10 rules correctly suppress
false positives for legitimate text patterns, while still detecting real
issues. Uses a real SpaCy ``en_core_web_md`` model for rules that require
dependency parsing or POS tagging.

Guards tested:
  Phase 1: VerbsRule, ClaimsRule, ToneRule, AccessibilityRule
  Phase 2: RepeatedWordsRule, NumeralsVsWordsRule
  Phase 3: OxfordCommaRule, CommasRule, UsingRule, ConversationalStyleRule
"""

import logging
from typing import Any, Dict, List

import pytest
import spacy

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Module-scoped SpaCy fixture — loaded once, reused across all tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def nlp() -> spacy.language.Language:
    """Load the en_core_web_md SpaCy model for rules that need NLP.

    Returns:
        A loaded SpaCy Language pipeline.
    """
    return spacy.load("en_core_web_md")


# ===================================================================
# Phase 1 — VerbsRule, ClaimsRule, ToneRule, AccessibilityRule
# ===================================================================


class TestVerbsRuleFPGuards:
    """False-positive guards for the VerbsRule passive-voice detector."""

    def test_state_of_being_deploy_not_flagged(self, nlp: spacy.language.Language) -> None:
        """'is deployed' should not be flagged — 'deploy' is a state-of-being lemma."""
        from rules.language_and_grammar.verbs_rule import VerbsRule

        rule = VerbsRule()
        text = "The application is deployed on the cluster."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        passive_issues = [e for e in result if "passive" in e.get("message", "").lower()]
        assert passive_issues == [], (
            f"'is deployed' is a state-of-being pattern and should not be flagged: {passive_issues}"
        )

    def test_state_of_being_configure_not_flagged(self, nlp: spacy.language.Language) -> None:
        """'is configured' should not be flagged — 'configure' is a state-of-being lemma."""
        from rules.language_and_grammar.verbs_rule import VerbsRule

        rule = VerbsRule()
        text = "The service is configured to use TLS."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        passive_issues = [e for e in result if "passive" in e.get("message", "").lower()]
        assert passive_issues == [], (
            f"'is configured' is a state-of-being pattern and should not be flagged: {passive_issues}"
        )

    def test_state_of_being_store_not_flagged(self, nlp: spacy.language.Language) -> None:
        """'is stored' should not be flagged — 'store' is a state-of-being lemma."""
        from rules.language_and_grammar.verbs_rule import VerbsRule

        rule = VerbsRule()
        text = "The data is stored in the database."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        passive_issues = [e for e in result if "passive" in e.get("message", "").lower()]
        assert passive_issues == [], (
            f"'is stored' is a state-of-being pattern and should not be flagged: {passive_issues}"
        )

    def test_real_passive_still_flagged(self, nlp: spacy.language.Language) -> None:
        """'was deleted by the admin' should still be flagged — 'delete' is not excepted."""
        from rules.language_and_grammar.verbs_rule import VerbsRule

        rule = VerbsRule()
        text = "The file was deleted by the admin."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        passive_issues = [e for e in result if "passive" in e.get("message", "").lower()]
        assert len(passive_issues) >= 1, (
            "'was deleted by the admin' is real passive voice and should be flagged"
        )


class TestClaimsRuleFPGuards:
    """False-positive guards for the ClaimsRule unsubstantiated-claim detector."""

    def test_secure_shell_compound_not_flagged(self, nlp: spacy.language.Language) -> None:
        """'Secure Shell' is a technical compound and should not trigger the 'secure' claim."""
        from rules.legal_information.claims_rule import ClaimsRule

        rule = ClaimsRule()
        text = "Connect to the server using Secure Shell."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        secure_issues = [
            e for e in result
            if "secure" in e.get("flagged_text", "").lower()
        ]
        assert secure_issues == [], (
            f"'Secure Shell' is a technical compound and should not be flagged: {secure_issues}"
        )

    def test_modal_qualifier_not_flagged(self, nlp: spacy.language.Language) -> None:
        """'can improve performance' has a modal qualifier before any claim word."""
        from rules.legal_information.claims_rule import ClaimsRule

        rule = ClaimsRule()
        text = "Caching can improve performance."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        assert result == [], (
            f"Modal qualifier 'can' should suppress claim detection: {result}"
        )

    def test_attribution_not_flagged(self, nlp: spacy.language.Language) -> None:
        """'according to the guide, the product is best' has an attribution marker."""
        from rules.legal_information.claims_rule import ClaimsRule

        rule = ClaimsRule()
        text = "According to the guide, the product is best in its category."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        best_issues = [
            e for e in result
            if "best" in e.get("flagged_text", "").lower()
        ]
        assert best_issues == [], (
            f"Attribution marker 'According to' should suppress claim detection: {best_issues}"
        )

    def test_unqualified_superlative_still_flagged(self, nlp: spacy.language.Language) -> None:
        """'Our product is always the best' has no modal, no attribution, no compound."""
        from rules.legal_information.claims_rule import ClaimsRule

        rule = ClaimsRule()
        text = "Our product is always the best."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        assert len(result) >= 1, (
            "'Our product is always the best' contains unqualified claims "
            "and should be flagged"
        )


class TestToneRuleFPGuards:
    """False-positive guards for the ToneRule jargon/buzzword detector."""

    def test_quoted_leverage_not_flagged(self, nlp: spacy.language.Language) -> None:
        """Text inside quotes like 'leverage' should not be flagged."""
        from rules.audience_and_medium.tone_rule import ToneRule

        rule = ToneRule()
        text = "Use the term 'leverage' carefully in technical writing."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        leverage_issues = [
            e for e in result
            if "leverage" in e.get("flagged_text", "").lower()
        ]
        assert leverage_issues == [], (
            f"'leverage' inside quotes should not be flagged: {leverage_issues}"
        )

    def test_unquoted_leverage_still_flagged(self, nlp: spacy.language.Language) -> None:
        """Unquoted 'leverage' in prose should still be flagged as business jargon."""
        from rules.audience_and_medium.tone_rule import ToneRule

        rule = ToneRule()
        text = "You can leverage this feature to improve performance."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        leverage_issues = [
            e for e in result
            if "leverage" in e.get("flagged_text", "").lower()
        ]
        assert len(leverage_issues) >= 1, (
            "Unquoted 'leverage' is business jargon and should be flagged"
        )


class TestAccessibilityRuleFPGuards:
    """False-positive guards for the AccessibilityRule all-caps detector."""

    def test_rhel_acronym_not_flagged(self, nlp: spacy.language.Language) -> None:
        """'RHEL' is a known acronym and should not be flagged as all-caps."""
        from rules.audience_and_medium.accessibility_rule import AccessibilityRule

        rule = AccessibilityRule()
        text = "Install RHEL on the target machine."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        caps_issues = [
            e for e in result
            if "RHEL" in e.get("flagged_text", "")
        ]
        assert caps_issues == [], (
            f"'RHEL' is a known acronym and should not be flagged: {caps_issues}"
        )

    def test_openshift_acronym_not_flagged(self, nlp: spacy.language.Language) -> None:
        """'OPENSHIFT' is a known acronym and should not be flagged as all-caps."""
        from rules.audience_and_medium.accessibility_rule import AccessibilityRule

        rule = AccessibilityRule()
        text = "Deploy the application on OPENSHIFT."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        caps_issues = [
            e for e in result
            if "OPENSHIFT" in e.get("flagged_text", "")
        ]
        assert caps_issues == [], (
            f"'OPENSHIFT' is a known acronym and should not be flagged: {caps_issues}"
        )


# ===================================================================
# Phase 2 — RepeatedWordsRule, NumeralsVsWordsRule
# ===================================================================


class TestRepeatedWordsRuleFPGuards:
    """False-positive guards for the RepeatedWordsRule duplicate detector."""

    def test_step_by_step_not_flagged(self) -> None:
        """'step by step' is a compound repeat pattern and should not be flagged."""
        from rules.language_and_grammar.repeated_words_rule import RepeatedWordsRule

        rule = RepeatedWordsRule()
        text = "Follow the step by step instructions."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        step_issues = [
            e for e in result
            if "step" in e.get("flagged_text", "").lower()
        ]
        assert step_issues == [], (
            f"'step by step' is an idiomatic compound and should not be flagged: {step_issues}"
        )

    def test_end_to_end_not_flagged(self) -> None:
        """'end to end' is a compound repeat pattern and should not be flagged."""
        from rules.language_and_grammar.repeated_words_rule import RepeatedWordsRule

        rule = RepeatedWordsRule()
        text = "Run the end to end tests before deploying."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        end_issues = [
            e for e in result
            if "end" in e.get("flagged_text", "").lower()
        ]
        assert end_issues == [], (
            f"'end to end' is an idiomatic compound and should not be flagged: {end_issues}"
        )

    def test_actual_duplicate_still_flagged(self) -> None:
        """'document document' is a real repeated word and should be flagged."""
        from rules.language_and_grammar.repeated_words_rule import RepeatedWordsRule

        rule = RepeatedWordsRule()
        # Note: 'the' is in _ALLOWED_REPEATS so we use a word not in that set.
        text = "Review document document before submitting."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        assert len(result) >= 1, (
            "'document document' is a real repeated word and should be flagged"
        )


class TestNumeralsVsWordsRuleFPGuards:
    """False-positive guards for the NumeralsVsWordsRule sentence-start detector."""

    def test_measurement_at_start_not_flagged(self) -> None:
        """'2 GB of memory is required' should not be flagged — has measurement unit."""
        from rules.numbers_and_measurement.numerals_vs_words_rule import NumeralsVsWordsRule

        rule = NumeralsVsWordsRule()
        text = "2 GB of memory is required."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        assert result == [], (
            f"'2 GB' has a measurement unit and should not be flagged: {result}"
        )

    def test_version_like_number_not_flagged(self) -> None:
        """'3.14 is the value' should not be flagged — version-like decimal."""
        from rules.numbers_and_measurement.numerals_vs_words_rule import NumeralsVsWordsRule

        rule = NumeralsVsWordsRule()
        text = "3.14 is the value of pi."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        assert result == [], (
            f"'3.14' looks like a version number and should not be flagged: {result}"
        )

    def test_bare_numeral_at_start_still_flagged(self) -> None:
        """'5 servers are available' should be flagged — bare numeral at sentence start."""
        from rules.numbers_and_measurement.numerals_vs_words_rule import NumeralsVsWordsRule

        rule = NumeralsVsWordsRule()
        text = "5 servers are available in the cluster."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        assert len(result) >= 1, (
            "'5 servers' starts with a bare numeral and should be flagged"
        )


# ===================================================================
# Phase 3 — OxfordCommaRule, CommasRule, UsingRule,
#            ConversationalStyleRule
# ===================================================================


class TestOxfordCommaRuleFPGuards:
    """False-positive guards for the OxfordCommaRule serial-comma detector."""

    def test_heading_block_type_not_flagged(self) -> None:
        """Headings should not be checked for Oxford comma."""
        from rules.punctuation.oxford_comma_rule import OxfordCommaRule

        rule = OxfordCommaRule()
        text = "Installing, configuring and deploying the application."
        sentences = [text]
        context: Dict[str, Any] = {"block_type": "heading"}

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, context=context,
        )

        assert result == [], (
            f"Headings should not be checked for Oxford comma: {result}"
        )

    def test_paragraph_without_oxford_comma_still_flagged(self) -> None:
        """Lists in paragraphs missing the Oxford comma should still be flagged."""
        from rules.punctuation.oxford_comma_rule import OxfordCommaRule

        rule = OxfordCommaRule()
        text = "Install servers, databases and applications."
        sentences = [text]
        context: Dict[str, Any] = {"block_type": "paragraph"}

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, context=context,
        )

        assert len(result) >= 1, (
            "Missing Oxford comma in a paragraph should be flagged"
        )


class TestCommasRuleFPGuards:
    """False-positive guards for the CommasRule 'then' clause detector."""

    def test_if_then_conditional_not_flagged(self) -> None:
        """'If you configured... then restart' should not be flagged — if...then pattern."""
        from rules.punctuation.commas_rule import CommasRule

        rule = CommasRule()
        text = "If you configured the storage backend then restart the service."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        then_issues = [
            e for e in result
            if "then" in e.get("flagged_text", "").lower()
        ]
        assert then_issues == [], (
            f"'If...then' conditional pattern should not be flagged: {then_issues}"
        )

    def test_when_then_conditional_not_flagged(self) -> None:
        """'When the process completes then exit' should not be flagged — when...then."""
        from rules.punctuation.commas_rule import CommasRule

        rule = CommasRule()
        text = "When the process completes then exit the terminal."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        then_issues = [
            e for e in result
            if "then" in e.get("flagged_text", "").lower()
        ]
        assert then_issues == [], (
            f"'When...then' conditional pattern should not be flagged: {then_issues}"
        )

    def test_bare_then_clause_still_flagged(self) -> None:
        """'Start the server then run the tests' should be flagged — no if/when/after."""
        from rules.punctuation.commas_rule import CommasRule

        rule = CommasRule()
        text = "Start the server then run the tests."
        sentences = [text]

        result: List[Dict[str, Any]] = rule.analyze(text, sentences)

        then_issues = [
            e for e in result
            if "then" in e.get("flagged_text", "").lower()
        ]
        assert len(then_issues) >= 1, (
            "'Start the server then run the tests' has bare 'then' and should be flagged"
        )


class TestUsingRuleFPGuards:
    """False-positive guards for the UsingRule 'noun using' detector."""

    def test_idiomatic_tool_not_flagged(self, nlp: spacy.language.Language) -> None:
        """'Install the package using rpm' should not be flagged — 'rpm' is idiomatic."""
        from rules.language_and_grammar.using_rule import UsingRule

        rule = UsingRule()
        text = "Install the package using rpm."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, spacy_doc=doc,
        )

        using_issues = [
            e for e in result
            if "using" in e.get("flagged_text", "").lower()
        ]
        assert using_issues == [], (
            f"'using rpm' is idiomatic tool usage and should not be flagged: {using_issues}"
        )

    def test_heading_block_type_not_flagged(self, nlp: spacy.language.Language) -> None:
        """Headings should not be checked for 'using' clarity."""
        from rules.language_and_grammar.using_rule import UsingRule

        rule = UsingRule()
        text = "Deploying applications using containers."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]
        context: Dict[str, Any] = {"block_type": "heading"}

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, context=context, spacy_doc=doc,
        )

        assert result == [], (
            f"Headings should not be checked for 'using' clarity: {result}"
        )


class TestConversationalStyleRuleFPGuards:
    """False-positive guards for the ConversationalStyleRule formality detector."""

    def test_reference_content_type_returns_empty(
        self, nlp: spacy.language.Language,
    ) -> None:
        """Reference content type uses formal language by design — should return []."""
        from rules.audience_and_medium.conversational_style_rule import ConversationalStyleRule

        rule = ConversationalStyleRule()
        text = "Utilize the API to obtain the desired output."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]
        context: Dict[str, Any] = {"content_type": "reference"}

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, context=context, spacy_doc=doc,
        )

        assert result == [], (
            f"Reference content type should suppress conversational style checks: {result}"
        )

    def test_non_reference_content_type_still_flagged(
        self, nlp: spacy.language.Language,
    ) -> None:
        """Non-reference content should still flag 'utilize' as overly formal."""
        from rules.audience_and_medium.conversational_style_rule import ConversationalStyleRule

        rule = ConversationalStyleRule()
        text = "Utilize the API to obtain the desired output."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]
        context: Dict[str, Any] = {"content_type": "concept"}

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, context=context, spacy_doc=doc,
        )

        # 'utilize' is mapped to 'use' in conversational_vocabularies.yaml,
        # so it should be flagged for non-reference content types.
        utilize_issues = [
            e for e in result
            if "utilize" in e.get("flagged_text", "").lower()
        ]
        assert len(utilize_issues) >= 1, (
            "'utilize' is overly formal for non-reference content and should be flagged"
        )


# ===================================================================
# Phase 10 — HighlightingRule bold+code detection
# ===================================================================


class TestHighlightingRuleBoldCode:
    """Check 3: bold wrapping inline code detection."""

    def test_bold_wrapping_code_flagged(self, nlp: spacy.language.Language) -> None:
        """Bold-wrapped inline code should be flagged."""
        from rules.structure_and_format.highlighting_rule import HighlightingRule

        rule = HighlightingRule()
        # In content coordinates, bold/italic markers are stripped.
        # The rule relies on bold_code_ranges from context.
        text = "Run curl to fetch the endpoint."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]
        context: Dict[str, Any] = {
            "block_type": "paragraph",
            "bold_code_ranges": [(4, 8, "bold", "curl")],
        }

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, context=context, spacy_doc=doc,
        )

        bold_issues = [
            e for e in result
            if "bold" in e.get("message", "").lower()
            and "inline code" in e.get("message", "").lower()
        ]
        assert len(bold_issues) == 1, (
            f"Bold-wrapped inline code should be flagged: {bold_issues}"
        )

    def test_plain_backtick_code_not_flagged(self, nlp: spacy.language.Language) -> None:
        """Plain backtick code (no bold/italic) should NOT be flagged by Check 3."""
        from rules.structure_and_format.highlighting_rule import HighlightingRule

        rule = HighlightingRule()
        text = "Run curl to fetch the endpoint."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]
        context: Dict[str, Any] = {
            "block_type": "paragraph",
            "bold_code_ranges": [],  # No bold wrapping
        }

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, context=context, spacy_doc=doc,
        )

        bold_issues = [
            e for e in result
            if "inline code" in e.get("message", "").lower()
        ]
        assert bold_issues == [], (
            f"Plain backtick code should not be flagged by Check 3: {bold_issues}"
        )

    def test_bold_non_code_not_flagged_by_check3(self, nlp: spacy.language.Language) -> None:
        """Bold around non-code text should NOT trigger Check 3."""
        from rules.structure_and_format.highlighting_rule import HighlightingRule

        rule = HighlightingRule()
        text = "This is important for security."
        doc = nlp(text)
        sentences = [sent.text for sent in doc.sents]
        context: Dict[str, Any] = {
            "block_type": "paragraph",
            "bold_code_ranges": [],  # No bold-wrapped code
        }

        result: List[Dict[str, Any]] = rule.analyze(
            text, sentences, nlp=nlp, context=context, spacy_doc=doc,
        )

        bold_code_issues = [
            e for e in result
            if "inline code" in e.get("message", "").lower()
        ]
        assert bold_code_issues == [], (
            f"Bold around non-code should not trigger Check 3: {bold_code_issues}"
        )
